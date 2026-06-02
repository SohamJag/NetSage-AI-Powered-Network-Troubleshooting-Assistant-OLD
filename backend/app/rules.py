import os
import json

KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.json")

def load_knowledge_base():
    try:
        with open(KNOWLEDGE_BASE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        return []

def evaluate_rules(facts):
    """
    Evaluates parsed facts against the knowledge base and returns matched scenarios with confidence scores.
    Facts structure example:
    {
       "ospf_neighbor_down": True,
       "log_contains_area_mismatch": True,
       "interface_admin_down": False,
       "cpu_usage_high": False,
       ...
    }
    """
    kb = load_knowledge_base()
    results = []
    
    for scenario in kb:
        conditions = scenario.get("conditions", {})
        total_conditions = len(conditions)
        if total_conditions == 0:
            continue
            
        matched_count = 0
        for cond_key, cond_val in conditions.items():
            # Check if fact matches the condition value
            if facts.get(cond_key) == cond_val:
                matched_count += 1
                
        if matched_count > 0:
            confidence = int((matched_count / total_conditions) * 100)
            
            results.append({
                "id": scenario["id"],
                "category": scenario["category"],
                "name": scenario["name"],
                "severity": scenario["severity"],
                "issue": scenario["issue"],
                "possible_causes": scenario["possible_causes"],
                "remediation": scenario["remediation"],
                "validation_commands": scenario["validation_commands"],
                "confidence_score": confidence,
                "priority": scenario.get("priority", 3)
            })
            
    # Sort by priority (lower is higher priority, e.g., 1 is first) and then by confidence score (descending)
    results.sort(key=lambda x: (x["priority"], -x["confidence_score"]))
    return results

def extract_facts_from_telemetry(device_name, telemetry_data, scenario_id=0):
    """
    Analyzes telemetry runs (raw and parsed) for a device and returns a flattened facts dictionary.
    telemetry_data is a dictionary mapping command_name -> parsed_content.
    """
    facts = {
        "ospf_neighbor_down": False,
        "log_contains_area_mismatch": False,
        "log_contains_auth_mismatch": False,
        "interface_admin_down": False,
        "missing_route_to_target": False,
        "ping_fails": False,
        "acl_hit_incrementing": False,
        "ping_blocked_by_acl": False,
        "cpu_usage_high": False,
        "memory_usage_high": False,
        "ospf_state_exstart": False,
        "ospf_timer_mismatch": False,
        "interface_crc_errors_high": False,
        "interface_collisions_high": False,
        "interface_input_drops": False,
        "traceroute_loop": False,
        "vlan_missing": False,
        "nat_pool_exhausted": False,
        "optical_rx_low": False,
        "next_hop_unreachable": False,
        "bgp_neighbor_down": False,
        "dhcp_pool_exhausted": False,
        "ssh_brute_force_detected": False
    }
    
    # 1. Analyze OSPF neighbors
    ospf_neighbors = telemetry_data.get("show ip ospf neighbor", [])
    if isinstance(ospf_neighbors, list):
        # In our simulated R1-R2 link, OSPF neighbors should exist.
        # If we expect neighbors (e.g. for R1, R2, R3) and neighbor count is 0, set down
        if device_name in ["R1", "R3"] and len(ospf_neighbors) == 0:
            facts["ospf_neighbor_down"] = True
        elif device_name == "R2" and len(ospf_neighbors) < 2:
            # R2 connects to R1 and R3, so should have 2 neighbors
            facts["ospf_neighbor_down"] = True
            
        # check states
        for nbr in ospf_neighbors:
            state = nbr.get("state", "").upper()
            if "EXSTART" in state or "EXCHANGE" in state:
                facts["ospf_state_exstart"] = True
            if "DOWN" in state:
                facts["ospf_neighbor_down"] = True

    # 2. Analyze logging
    logs = telemetry_data.get("show logging", "")
    if isinstance(logs, str):
        if "Area ID mismatch" in logs:
            facts["log_contains_area_mismatch"] = True
        if "Mismatched Authentication Key" in logs:
            facts["log_contains_auth_mismatch"] = True
        if "SYS-2-MALLOCFAIL" in logs:
            facts["memory_usage_high"] = True
        if "PROCESS-3-CPU_EXCEEDED" in logs:
            facts["cpu_usage_high"] = True
            
    # 3. Analyze interface status
    interfaces = telemetry_data.get("show interface", {})
    if isinstance(interfaces, dict):
        for if_name, if_info in interfaces.items():
            admin_status = if_info.get("admin_status", "").lower()
            line_status = if_info.get("line_status", "").lower()
            if "down" in admin_status and "administratively" in admin_status:
                facts["interface_admin_down"] = True
            if if_info.get("crc_errors", 0) > 10:
                facts["interface_crc_errors_high"] = True
            if if_info.get("input_errors", 0) > 50:
                facts["interface_input_drops"] = True

    # 4. Analyze CPU and Memory
    cpu = telemetry_data.get("show processes cpu", {})
    if isinstance(cpu, dict):
        five_sec = cpu.get("five_sec", 0)
        if five_sec > 80:
            facts["cpu_usage_high"] = True
            
    mem = telemetry_data.get("show memory statistics", {})
    if isinstance(mem, dict):
        used = mem.get("used", 0)
        total = mem.get("total", 0)
        if total > 0 and (used / total) > 0.9:
            facts["memory_usage_high"] = True

    # 5. Analyze Access Lists
    acls = telemetry_data.get("show access-lists", {})
    if isinstance(acls, dict) and len(acls) > 0:
        if "BLOCK_CLIENT" in acls:
            for rule in acls["BLOCK_CLIENT"]:
                if "deny" in rule.get("rule", "").lower() and rule.get("matches", 0) > 0:
                    facts["acl_hit_incrementing"] = True
                    facts["ping_blocked_by_acl"] = True

    # 6. Pings / Routing Tables
    routes = telemetry_data.get("show ip route", [])
    has_target_route = False
    if isinstance(routes, list):
        for route in routes:
            net = route.get("network", "")
            if "192.168.4.0" in net or "192.168.1.0" in net:
                has_target_route = True
        
        # Scenario 4 missing route on R3 back to client (192.168.1.0/24)
        if device_name == "R3" and scenario_id == 4:
            # Check if 192.168.1.0/24 is explicitly in routes
            route_1_exists = any("192.168.1.0" in r.get("network", "") for r in routes)
            if not route_1_exists:
                facts["missing_route_to_target"] = True
                facts["ping_fails"] = True

    # 7. Ping Command Outputs
    ping_out = telemetry_data.get("ping", "")
    if isinstance(ping_out, str):
        if "Success rate is 0 percent" in ping_out:
            facts["ping_fails"] = True
            if "Access-List" in ping_out:
                facts["ping_blocked_by_acl"] = True

    return facts
