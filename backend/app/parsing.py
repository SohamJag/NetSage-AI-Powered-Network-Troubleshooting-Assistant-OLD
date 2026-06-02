import re
import json

def parse_show_ip_route(raw_text):
    routes = []
    # Match lines like: O     192.168.23.0/30 [110/2] via 192.168.12.2, 02:44:12, GigabitEthernet0/0
    # or: C        192.168.12.0/30 is directly connected, GigabitEthernet0/0
    
    # Let's write a robust parser
    lines = raw_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # OSPF route match
        ospf_match = re.match(r"^([O])\s+([\d\.\/]+)\s+\[\d+\/\d+\]\s+via\s+([\d\.]+),\s+[\d\:]+,\s+([\w\d\/]+)", line)
        if ospf_match:
            proto, network, next_hop, interface = ospf_match.groups()
            routes.append({
                "protocol": "OSPF",
                "network": network,
                "next_hop": next_hop,
                "interface": interface
            })
            continue
            
        # Connected or Local route match
        conn_match = re.match(r"^([CL])\s+([\d\.\/]+)\s+is\s+directly\s+connected,\s+([\w\d\/]+)", line)
        if conn_match:
            proto, network, interface = conn_match.groups()
            routes.append({
                "protocol": "Connected" if proto == "C" else "Local",
                "network": network,
                "next_hop": "0.0.0.0",
                "interface": interface
            })
            continue

        # Static route match
        static_match = re.match(r"^([S])\s+([\d\.\/]+)\s+via\s+([\d\.]+)", line)
        if static_match:
            proto, network, next_hop = static_match.groups()
            routes.append({
                "protocol": "Static",
                "network": network,
                "next_hop": next_hop,
                "interface": "Unknown"
            })
            continue

    return routes

def parse_show_ip_ospf_neighbor(raw_text):
    neighbors = []
    lines = raw_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Neighbor ID") or line.startswith("Syslog"):
            continue
        
        # Match e.g.: 2.2.2.2           1   FULL/DR         00:00:36    192.168.12.2    GigabitEthernet0/0
        parts = re.split(r'\s+', line)
        if len(parts) >= 6:
            neighbors.append({
                "neighbor_id": parts[0],
                "priority": parts[1],
                "state": parts[2],
                "dead_time": parts[3],
                "address": parts[4],
                "interface": parts[5]
            })
    return neighbors

def parse_show_interface(raw_text):
    interfaces = {}
    
    # We want to parse each interface's block
    # Split by interfaces which start with a line like "GigabitEthernet0/0 is up..."
    blocks = re.split(r'(?=\b[\w\d\/]+ is (?:up|down|administratively down))', raw_text)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        first_line = block.splitlines()[0]
        # Match "GigabitEthernet0/0 is up, line protocol is up" or "administratively down"
        match = re.match(r"^([\w\d\/]+) is ([^,]+),\s+line protocol is ([^\n]+)", first_line)
        if match:
            if_name, admin_state, line_state = match.groups()
            
            # Default values
            ip_addr = "unassigned"
            mtu = 1500
            bw = 1000000
            duplex = "auto"
            speed = "auto"
            input_errors = 0
            crc_errors = 0
            output_errors = 0
            
            # Find IP address: "Internet address is 192.168.12.1/30"
            ip_match = re.search(r"Internet address is ([\d\.\/\w]+)", block)
            if ip_match:
                ip_addr = ip_match.group(1)
                
            # Find MTU & BW: "MTU 1500 bytes, BW 1000000 Kbit/sec"
            mtu_match = re.search(r"MTU\s+(\d+)\s+bytes,\s+BW\s+(\d+)", block)
            if mtu_match:
                mtu = int(mtu_match.group(1))
                bw = int(mtu_match.group(2))
                
            # Find Duplex & Speed: "Full-duplex, 1000Mb/s"
            duplex_match = re.search(r"(\w+)-duplex,\s+([\w\/]+)", block)
            if duplex_match:
                duplex = duplex_match.group(1)
                speed = duplex_match.group(2)
                
            # Find Errors: "X input errors, Y CRC"
            err_match = re.search(r"(\d+)\s+input errors,\s+(\d+)\s+CRC", block)
            if err_match:
                input_errors = int(err_match.group(1))
                crc_errors = int(err_match.group(2))
                
            # Find Output Errors: "Z output errors"
            out_err_match = re.search(r"(\d+)\s+output errors", block)
            if out_err_match:
                output_errors = int(out_err_match.group(1))
                
            interfaces[if_name] = {
                "name": if_name,
                "admin_status": admin_state.strip(),
                "line_status": line_state.strip(),
                "ip_address": ip_addr,
                "mtu": mtu,
                "bandwidth": bw,
                "duplex": duplex,
                "speed": speed,
                "input_errors": input_errors,
                "crc_errors": crc_errors,
                "output_errors": output_errors
            }
            
    return interfaces

def parse_show_processes_cpu(raw_text):
    # Match "CPU utilization for five seconds: 98%/12%; one minute: 95%; five minutes: 92%"
    cpu_data = {"five_sec": 0, "one_min": 0, "five_min": 0, "processes": []}
    
    match = re.search(r"CPU utilization for five seconds:\s+(\d+)%.*?one minute:\s+(\d+)%.*?five minutes:\s+(\d+)%", raw_text)
    if match:
        cpu_data["five_sec"] = int(match.group(1))
        cpu_data["one_min"] = int(match.group(2))
        cpu_data["five_min"] = int(match.group(3))
        
    # Extract high CPU processes if any
    lines = raw_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or "Process" in line or "utilization" in line or "PID" in line:
            continue
        parts = re.split(r'\s+', line)
        if len(parts) >= 8:
            # PID Runtime Invoked uSecs 5Sec 1Min 5Min TTY Process
            try:
                cpu_data["processes"].append({
                    "pid": parts[0],
                    "cpu_5sec": parts[4],
                    "cpu_1min": parts[5],
                    "process_name": " ".join(parts[8:])
                })
            except Exception:
                pass
    return cpu_data

def parse_show_memory_statistics(raw_text):
    mem_data = {"total": 0, "used": 0, "free": 0}
    lines = raw_text.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("Processor"):
            parts = re.split(r'\s+', line)
            if len(parts) >= 5:
                # Processor Head Total Used Free
                try:
                    mem_data["total"] = int(parts[2])
                    mem_data["used"] = int(parts[3])
                    mem_data["free"] = int(parts[4])
                except Exception:
                    pass
    return mem_data

def parse_show_access_lists(raw_text):
    acls = {}
    current_acl = None
    lines = raw_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Extended IP access list BLOCK_CLIENT
        acl_match = re.match(r"^Extended IP access list\s+(\w+)", line)
        if acl_match:
            current_acl = acl_match.group(1)
            acls[current_acl] = []
            continue
            
        if current_acl and (line.startswith("permit") or line.startswith("deny") or re.match(r"^\d+", line)):
            # e.g., 10 deny ip 192.168.1.0 0.0.0.255 192.168.4.0 0.0.0.255 (24 matches)
            # or permit ip any any (582 matches)
            matches = 0
            match_search = re.search(r"\((\d+)\s+matches\)", line)
            if match_search:
                matches = int(match_search.group(1))
                
            acls[current_acl].append({
                "rule": line,
                "matches": matches
            })
            
    return acls

def parse_command(command, raw_text):
    cmd = command.lower().strip()
    try:
        if "show ip route" in cmd:
            return parse_show_ip_route(raw_text)
        elif "show ip ospf neighbor" in cmd:
            return parse_show_ip_ospf_neighbor(raw_text)
        elif "show interface" in cmd and "status" not in cmd:
            return parse_show_interface(raw_text)
        elif "show processes cpu" in cmd:
            return parse_show_processes_cpu(raw_text)
        elif "show memory statistics" in cmd:
            return parse_show_memory_statistics(raw_text)
        elif "show access-lists" in cmd:
            return parse_show_access_lists(raw_text)
    except Exception as e:
        print(f"Error parsing command {command}: {e}")
    return {}
