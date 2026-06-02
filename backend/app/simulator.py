import datetime
import random

# Virtual Toplogy:
# Client (192.168.1.50) -> Switch1 -> [Gi0/1] R1 [Gi0/0] (192.168.12.1)
#                                             |
#                                             | (OSPF Area 0, Net 192.168.12.0/30)
#                                             v
#                                  [Gi0/0] R2 [Gi0/1] (192.168.23.2)
#                                             |
#                                             | (OSPF Area 0, Net 192.168.23.0/30)
#                                             v
#                                  [Gi0/0] R3 [Gi0/1] -> Switch2 -> Server (192.168.4.10)

SCENARIOS = {
    0: "Healthy / Baseline Operational State",
    1: "OSPF Area Mismatch on R1-R2 Link",
    2: "OSPF MD5 Authentication Mismatch on R1-R2 Link",
    3: "R2-R3 Link Interface Shutdown (Gi0/1 on R2)",
    4: "Missing Static Route on R3 for Client Network",
    5: "ACL BLOCK_CLIENT Enabled on R3 blocking Client traffic",
    6: "Control Plane Exhaustion: High CPU & Memory on R1"
}

def get_base_ip_route(device, scenario):
    if device == "R1":
        if scenario == 3: # R2-R3 link is down, OSPF neighbor down, missing route to R3 and Server
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 
       N1 - OSPF NSSA external 1, N2 - OSPF NSSA external 2
       E1 - OSPF external 1, E2 - OSPF external 2
       i - IS-IS, L1 - IS-IS level-1, L2 - IS-IS level-2, ia - IS-IS inter area
       * - candidate default, U - per-user static route, o - ODR
       P - periodic downloaded static route, H - NHRP, l - LISP
       a - application route
       + - replicated route, % - next hop override, p - overrides from PfR

Gateway of last resort is not set

      192.168.1.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.1.0/24 is directly connected, GigabitEthernet0/1
L        192.168.1.1/32 is directly connected, GigabitEthernet0/1
      192.168.12.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.12.0/30 is directly connected, GigabitEthernet0/0
L        192.168.12.1/32 is directly connected, GigabitEthernet0/0
O     192.168.23.0/30 [110/2] via 192.168.12.2, 00:04:12, GigabitEthernet0/0
"""
        elif scenario in [1, 2]: # OSPF is down between R1 and R2
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 
       N1 - OSPF NSSA external 1, N2 - OSPF NSSA external 2
       E1 - OSPF external 1, E2 - OSPF external 2

Gateway of last resort is not set

      192.168.1.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.1.0/24 is directly connected, GigabitEthernet0/1
L        192.168.1.1/32 is directly connected, GigabitEthernet0/1
      192.168.12.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.12.0/30 is directly connected, GigabitEthernet0/0
L        192.168.12.1/32 is directly connected, GigabitEthernet0/0
"""
        else: # Healthy / default
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 
       N1 - OSPF NSSA external 1, N2 - OSPF NSSA external 2
       E1 - OSPF external 1, E2 - OSPF external 2

Gateway of last resort is not set

      192.168.1.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.1.0/24 is directly connected, GigabitEthernet0/1
L        192.168.1.1/32 is directly connected, GigabitEthernet0/1
      192.168.12.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.12.0/30 is directly connected, GigabitEthernet0/0
L        192.168.12.1/32 is directly connected, GigabitEthernet0/0
O     192.168.23.0/30 [110/2] via 192.168.12.2, 02:44:12, GigabitEthernet0/0
O     192.168.4.0/24 [110/3] via 192.168.12.2, 02:44:12, GigabitEthernet0/0
"""
    elif device == "R2":
        if scenario == 3: # Gi0/1 down
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 

Gateway of last resort is not set

      192.168.1.0/24 is variably subnetted, 1 subnets, 1 masks
O        192.168.1.0/24 [110/2] via 192.168.12.1, 00:04:15, GigabitEthernet0/0
      192.168.12.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.12.0/30 is directly connected, GigabitEthernet0/0
L        192.168.12.2/32 is directly connected, GigabitEthernet0/0
"""
        elif scenario in [1, 2]: # R1-R2 link down OSPF
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 

Gateway of last resort is not set

      192.168.12.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.12.0/30 is directly connected, GigabitEthernet0/0
L        192.168.12.2/32 is directly connected, GigabitEthernet0/0
      192.168.23.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.23.0/30 is directly connected, GigabitEthernet0/1
L        192.168.23.1/32 is directly connected, GigabitEthernet0/1
O     192.168.4.0/24 [110/2] via 192.168.23.2, 00:15:33, GigabitEthernet0/1
"""
        else: # Healthy / default
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 

Gateway of last resort is not set

      192.168.1.0/24 is variably subnetted, 1 subnets, 1 masks
O        192.168.1.0/24 [110/2] via 192.168.12.1, 02:44:18, GigabitEthernet0/0
      192.168.12.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.12.0/30 is directly connected, GigabitEthernet0/0
L        192.168.12.2/32 is directly connected, GigabitEthernet0/0
      192.168.23.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.23.0/30 is directly connected, GigabitEthernet0/1
L        192.168.23.1/32 is directly connected, GigabitEthernet0/1
O     192.168.4.0/24 [110/2] via 192.168.23.2, 02:44:18, GigabitEthernet0/1
"""
    elif device == "R3":
        if scenario == 3: # Link to R2 is down, OSPF down
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 

Gateway of last resort is not set

      192.168.4.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.4.0/24 is directly connected, GigabitEthernet0/1
L        192.168.4.1/32 is directly connected, GigabitEthernet0/1
      192.168.23.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.23.0/30 is directly connected, GigabitEthernet0/0
L        192.168.23.2/32 is directly connected, GigabitEthernet0/0
"""
        elif scenario in [1, 2]: # R1-R2 OSPF down
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 

Gateway of last resort is not set

      192.168.4.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.4.0/24 is directly connected, GigabitEthernet0/1
L        192.168.4.1/32 is directly connected, GigabitEthernet0/1
      192.168.23.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.23.0/30 is directly connected, GigabitEthernet0/0
L        192.168.23.2/32 is directly connected, GigabitEthernet0/0
O     192.168.12.0/30 [110/2] via 192.168.23.1, 00:15:35, GigabitEthernet0/0
"""
        elif scenario == 4: # Missing Route on R3 back to Client 192.168.1.0/24
            # OSPF routes exist except 192.168.1.0/24, or static routes are missing
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 

Gateway of last resort is not set

      192.168.4.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.4.0/24 is directly connected, GigabitEthernet0/1
L        192.168.4.1/32 is directly connected, GigabitEthernet0/1
      192.168.23.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.23.0/30 is directly connected, GigabitEthernet0/0
L        192.168.23.2/32 is directly connected, GigabitEthernet0/0
O     192.168.12.0/30 [110/2] via 192.168.23.1, 02:44:22, GigabitEthernet0/0
"""
        else: # Healthy / default
            return """Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 

Gateway of last resort is not set

      192.168.1.0/24 is variably subnetted, 1 subnets, 1 masks
O        192.168.1.0/24 [110/3] via 192.168.23.1, 02:44:22, GigabitEthernet0/0
      192.168.4.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.4.0/24 is directly connected, GigabitEthernet0/1
L        192.168.4.1/32 is directly connected, GigabitEthernet0/1
      192.168.23.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.23.0/30 is directly connected, GigabitEthernet0/0
L        192.168.23.2/32 is directly connected, GigabitEthernet0/0
O     192.168.12.0/30 [110/2] via 192.168.23.1, 02:44:22, GigabitEthernet0/0
"""
    return "Command not supported or empty output"

def generate_show_ip_ospf_neighbor(device, scenario):
    if device == "R1":
        if scenario in [1, 2]:
            return "" # Neighbor R2 is down
        else:
            return """Neighbor ID     Pri   State           Dead Time   Address         Interface
2.2.2.2           1   FULL/DR         00:00:36    192.168.12.2    GigabitEthernet0/0
"""
    elif device == "R2":
        if scenario in [1, 2]: # Neighbor R1 is down, R3 is up
            return """Neighbor ID     Pri   State           Dead Time   Address         Interface
3.3.3.3           1   FULL/BDR        00:00:38    192.168.23.2    GigabitEthernet0/1
"""
        elif scenario == 3: # Link to R3 down
            return """Neighbor ID     Pri   State           Dead Time   Address         Interface
1.1.1.1           1   FULL/BDR        00:00:35    192.168.12.1    GigabitEthernet0/0
"""
        else: # Both up
            return """Neighbor ID     Pri   State           Dead Time   Address         Interface
1.1.1.1           1   FULL/BDR        00:00:35    192.168.12.1    GigabitEthernet0/0
3.3.3.3           1   FULL/DR         00:00:39    192.168.23.2    GigabitEthernet0/1
"""
    elif device == "R3":
        if scenario == 3: # Neighbor R2 down
            return ""
        else: # Neighbor R2 up
            return """Neighbor ID     Pri   State           Dead Time   Address         Interface
2.2.2.2           1   FULL/BDR        00:00:34    192.168.23.1    GigabitEthernet0/0
"""
    return ""

def generate_show_interface(device, scenario):
    if device == "R1":
        cpu_err = "  0 input errors, 0 CRC, 0 frame, 0 overrun, 0 ignored"
        if scenario == 6:
            cpu_err = "  248 input errors, 12 CRC, 0 frame, 0 overrun, 192 ignored"
        return f"""GigabitEthernet0/0 is up, line protocol is up 
  Hardware is GE, address is 5000.0001.0000 (bia 5000.0001.0000)
  Internet address is 192.168.12.1/30
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec, 
     reliability 255/255, txload 1/255, rxload 1/255
  Encapsulation ARPA, loopback not set
  Keepalive set (10 sec)
  Full-duplex, 1000Mb/s, link type is auto, media type is RJ45
  output flow-control is unsupported, input flow-control is unsupported
  ARP type: ARPA, ARP Timeout 04:00:00
  Last input 00:00:02, output 00:00:00, output hang never
  Last clearing of "show interface" counters never
  Input queue: 0/75/0/0 (size/max/drops/flushes); Total output drops: 0
  Queueing strategy: fifo
  Output queue: 0/40 (size/max)
  5 minute input rate 1000 bits/sec, 2 packets/sec
  5 minute output rate 2000 bits/sec, 3 packets/sec
     28491 packets input, 3819201 bytes, 0 no buffer
     Received 244 broadcasts (0 IP multicasts)
     0 runts, 0 giants, 0 throttles
{cpu_err}
     0 abort, 0 watchdog, 0 multicast, 0 pause input
     29812 packets output, 3918201 bytes, 0 underruns
     0 output errors, 0 collisions, 1 interface resets
     0 unknown protocol drops
     0 babbles, 0 late collision, 0 deferred
     0 lost carrier, 0 no carrier, 0 pause output
     0 output buffer failures, 0 output buffers swapped out

GigabitEthernet0/1 is up, line protocol is up 
  Hardware is GE, address is 5000.0001.0001 (bia 5000.0001.0001)
  Internet address is 192.168.1.1/24
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec
  Encapsulation ARPA
  Full-duplex, 1000Mb/s
"""
    elif device == "R2":
        gi0_1_status = "up, line protocol is up"
        gi0_1_notes = "Internet address is 192.168.23.1/30"
        if scenario == 3:
            gi0_1_status = "administratively down, line protocol is down"
            gi0_1_notes = "Internet address is 192.168.23.1/30 (disabled)"
            
        return f"""GigabitEthernet0/0 is up, line protocol is up 
  Hardware is GE, address is 5000.0002.0000 (bia 5000.0002.0000)
  Internet address is 192.168.12.2/30
  Full-duplex, 1000Mb/s

GigabitEthernet0/1 is {gi0_1_status}
  Hardware is GE, address is 5000.0002.0001 (bia 5000.0002.0001)
  {gi0_1_notes}
  Full-duplex, 1000Mb/s
"""
    elif device == "R3":
        return """GigabitEthernet0/0 is up, line protocol is up 
  Hardware is GE, address is 5000.0003.0000 (bia 5000.0003.0000)
  Internet address is 192.168.23.2/30
  Full-duplex, 1000Mb/s

GigabitEthernet0/1 is up, line protocol is up 
  Hardware is GE, address is 5000.0003.0001 (bia 5000.0003.0001)
  Internet address is 192.168.4.1/24
  Full-duplex, 1000Mb/s
"""
    return ""

def generate_show_running_config(device, scenario):
    if device == "R1":
        area = "0"
        auth = ""
        if scenario == 1:
            area = "0"  # R1 stays in Area 0
        elif scenario == 2:
            auth = "ip ospf message-digest-key 1 md5 CISCO123\n ip ospf authentication message-digest"
            
        return f"""Building configuration...
Current configuration : 1582 bytes
!
version 15.6
!
hostname R1
!
interface GigabitEthernet0/0
 description Link to R2
 ip address 192.168.12.1 255.255.255.252
 ip ospf 1 area {area}
 {auth}
 duplex full
 speed 1000
!
interface GigabitEthernet0/1
 description Link to HO Switch
 ip address 192.168.1.1 255.255.255.0
 duplex full
 speed 1000
!
router ospf 1
 router-id 1.1.1.1
 log-adjacency-changes
!
end
"""
    elif device == "R2":
        area = "0"
        auth = ""
        if scenario == 1:
            area = "10" # Mismatch! R2 configures Gi0/0 in Area 10
        elif scenario == 2:
            auth = "ip ospf message-digest-key 1 md5 WRONG_KEY\n ip ospf authentication message-digest"
            
        return f"""Building configuration...
Current configuration : 1624 bytes
!
version 15.6
!
hostname R2
!
interface GigabitEthernet0/0
 description Link to R1
 ip address 192.168.12.2 255.255.255.252
 ip ospf 1 area {area}
 {auth}
 duplex full
 speed 1000
!
interface GigabitEthernet0/1
 description Link to R3
 ip address 192.168.23.1 255.255.255.252
 ip ospf 1 area 0
 duplex full
 speed 1000
{" shutdown" if scenario == 3 else ""}
!
router ospf 1
 router-id 2.2.2.2
 log-adjacency-changes
!
end
"""
    elif device == "R3":
        acl_line = ""
        acl_def = ""
        if scenario == 5:
            acl_line = " ip access-group BLOCK_CLIENT in"
            acl_def = """ip access-list extended BLOCK_CLIENT
 deny ip 192.168.1.0 0.0.0.255 192.168.4.0 0.0.0.255
 permit ip any any
"""
        return f"""Building configuration...
hostname R3
!
{acl_def}!
interface GigabitEthernet0/0
 description Link to R2
 ip address 192.168.23.2 255.255.255.252
 ip ospf 1 area 0
 duplex full
 speed 1000
!
interface GigabitEthernet0/1
 description Link to DC Switch
 ip address 192.168.4.1 255.255.255.0
{acl_line}
 duplex full
 speed 1000
!
router ospf 1
 router-id 3.3.3.3
 log-adjacency-changes
!
{"! No static routes configured" if scenario == 4 else "ip route 192.168.1.0 255.255.255.0 192.168.23.1"}
!
end
"""
    return ""

def generate_show_logging(device, scenario):
    now = datetime.datetime.now().strftime("%b %d %H:%M:%S")
    if device == "R1":
        if scenario == 1:
            return f"""Syslog logging: enabled (0 messages dropped, 0 messages rate-limited)
    Console logging: level debugging, 38 messages logged
    Monitor logging: level debugging, 0 messages logged
    Buffer logging: level debugging, 42 messages logged

*Jun  2 12:01:22.418: %OSPF-4-ERRRCV: Received invalid packet: Area ID mismatch from 2.2.2.2 on GigabitEthernet0/0
*Jun  2 12:01:32.420: %OSPF-4-ERRRCV: Received invalid packet: Area ID mismatch from 2.2.2.2 on GigabitEthernet0/0
*Jun  2 12:01:42.424: %OSPF-4-ERRRCV: Received invalid packet: Area ID mismatch from 2.2.2.2 on GigabitEthernet0/0
"""
        elif scenario == 2:
            return f"""Syslog logging: enabled
*Jun  2 12:04:11.192: %OSPF-4-ERRRCV: Mismatched Authentication Key: Key 1 from 2.2.2.2 on GigabitEthernet0/0
*Jun  2 12:04:21.195: %OSPF-4-ERRRCV: Mismatched Authentication Key: Key 1 from 2.2.2.2 on GigabitEthernet0/0
"""
        elif scenario == 6:
            return f"""Syslog logging: enabled
*Jun  2 12:45:00.010: %SYS-5-CONFIG_I: Configured from console by console
*Jun  2 12:46:12.441: %SYS-2-MALLOCFAIL: Memory allocation of 1048576 bytes failed from 0x41E9D7C
*Jun  2 12:47:05.105: %PROCESS-3-CPU_EXCEEDED: Process "IP Input" exceeded its runtime slice
"""
    elif device == "R2":
        if scenario == 3:
            return f"""Syslog logging: enabled
*Jun  2 12:12:02.103: %LINK-5-CHANGED: Interface GigabitEthernet0/1, changed state to administratively down
*Jun  2 12:12:03.103: %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/1, changed state to down
*Jun  2 12:12:13.204: %OSPF-5-ADJCHG: Process 1, Nbr 3.3.3.3 on GigabitEthernet0/1 from FULL to DOWN, Neighbor Down: Interface down or detached
"""
    return f"Log Buffer: Log tail at {now}\nNo alerts or errors logged."

def generate_show_processes_cpu(device, scenario):
    if device == "R1" and scenario == 6:
        return """CPU utilization for five seconds: 98%/12%; one minute: 95%; five minutes: 92%
 PID Runtime(ms)     Invoked      uSecs   5Sec   1Min   5Min TTY Process 
   1          12          92        130  0.00%  0.00%  0.00%   0 Chunk Manager    
  84     8109204     1048192       7736 78.42% 76.10% 72.10%   0 IP Input         
  92      102812       49201       2089  7.10%  6.20%  5.90%   0 OSPF Router      
 104       12841       10294       1247  0.42%  0.30%  0.20%   0 SSH Process      
"""
    return """CPU utilization for five seconds: 8%/1%; one minute: 6%; five minutes: 5%
 PID Runtime(ms)     Invoked      uSecs   5Sec   1Min   5Min TTY Process 
   1           8          42        190  0.00%  0.00%  0.00%   0 Chunk Manager    
  84       48201       10294       4682  1.12%  1.10%  1.00%   0 IP Input         
  92       18291        4182       4373  0.22%  0.18%  0.15%   0 OSPF Router      
"""

def generate_show_memory_statistics(device, scenario):
    if device == "R1" and scenario == 6:
        return """                Head    Total(b)     Used(b)     Free(b)   Lowest(b)  Largest(b)
Processor   31E00000   134217728   129482012     4735716     1024920     1849201
      I/O    E000000    33554432    12904812    20649620    20182410    19820124
"""
    return """                Head    Total(b)     Used(b)     Free(b)   Lowest(b)  Largest(b)
Processor   31E00000   134217728    52819201    81398527    79482018    78492018
      I/O    E000000    33554432     6201822    27352610    26982010    26820124
"""

def generate_show_access_lists(device, scenario):
    if device == "R3" and scenario == 5:
        return """Extended IP access list BLOCK_CLIENT
    10 deny ip 192.168.1.0 0.0.0.255 192.168.4.0 0.0.0.255 (24 matches)
    20 permit ip any any (582 matches)
"""
    return ""

def run_simulated_ping(scenario, source, target):
    # Source is usually Client (192.168.1.50) or R1
    # Target is Server (192.168.4.10)
    latency = random.randint(2, 8)
    if scenario == 6:
        latency = random.randint(180, 260)
        
    if scenario in [1, 2]: # OSPF R1-R2 is down, R1 cannot reach Server
        if target == "192.168.4.10":
            return """Sending 5, 100-byte ICMP Echos to 192.168.4.10, timeout is 2 seconds:
.....
Success rate is 0 percent (0/5)"""
    elif scenario == 3: # Link R2-R3 down
        if target == "192.168.4.10":
            return """Sending 5, 100-byte ICMP Echos to 192.168.4.10, timeout is 2 seconds:
U.U.U
Success rate is 0 percent (0/5)"""
    elif scenario == 4: # Missing Route on R3 back to 192.168.1.0/24
        # R1 ping to Server will fail because R3 drops/can't route reply back
        return """Sending 5, 100-byte ICMP Echos to 192.168.4.10, timeout is 2 seconds:
.....
Success rate is 0 percent (0/5)"""
    elif scenario == 5: # ACL blocking
        return """Sending 5, 100-byte ICMP Echos to 192.168.4.10, timeout is 2 seconds:
U.U.U
Success rate is 0 percent (0/5) (Traffic blocked by Access-List)"""
        
    # Healthy / default
    return f"""Sending 5, 100-byte ICMP Echos to 192.168.4.10, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = {latency-1}/{latency}/{latency+2} ms"""

def run_simulated_command(device, command, scenario):
    cmd = command.lower().strip()
    if "show ip route" in cmd:
        return get_base_ip_route(device, scenario)
    elif "show ip ospf neighbor" in cmd:
        return generate_show_ip_ospf_neighbor(device, scenario)
    elif "show interface" in cmd and "status" not in cmd:
        return generate_show_interface(device, scenario)
    elif "show interface status" in cmd:
        # Simple status output
        if device == "R2" and scenario == 3:
            return """Port      Name               Status       Vlan       Duplex  Speed Type
Gi0/0     Link to R1         connected    routed     full    1000  10/100/1000-TX
Gi0/1     Link to R3         disabled     routed     full    1000  10/100/1000-TX"""
        return """Port      Name               Status       Vlan       Duplex  Speed Type
Gi0/0     Link               connected    routed     full    1000  10/100/1000-TX
Gi0/1     Link               connected    routed     full    1000  10/100/1000-TX"""
    elif "show running-config" in cmd:
        return generate_show_running_config(device, scenario)
    elif "show logging" in cmd:
        return generate_show_logging(device, scenario)
    elif "show processes cpu" in cmd:
        return generate_show_processes_cpu(device, scenario)
    elif "show memory statistics" in cmd:
        return generate_show_memory_statistics(device, scenario)
    elif "show access-lists" in cmd:
        return generate_show_access_lists(device, scenario)
    elif "ping" in cmd:
        # extract target
        target = "192.168.4.10"
        if "192.168.4.10" in cmd:
            target = "192.168.4.10"
        return run_simulated_ping(scenario, device, target)
    elif "show ip protocols" in cmd:
        return f"""Routing Protocol is "ospf 1"
  Outgoing update filter list for all interfaces is not set
  Incoming update filter list for all interfaces is not set
  Router ID 1.1.1.1 (simulated)
  Number of areas in this router is 1. 1 normal 0 stub 0 nssa
  Maximum path: 4
  Routing for Networks:
    192.168.12.0 0.0.0.3 area 0
  Routing Information Sources:
    Gateway         Distance      Last Update
    2.2.2.2              110      02:45:10
  Distance: (default is 110)"""
    elif "show version" in cmd:
        return f"""Cisco IOS Software, IOSv Software (VIOS-ADVENTERPRISEK9-M), Version 15.6(2)T, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2016 by Cisco Systems, Inc.
Compiled Tue 22-Mar-16 16:19 by prod_rel_team

ROM: Bootstrap program is IOSv

{device} uptime is {random.randint(12, 48)} hours, 12 minutes
System returned to ROM by reload
System image file is "flash0:/vios-adventerprisek9-m.vmdk"
Last reload reason: PowerOn

This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use.

Cisco IOSv (revision 1.0) with 524288K bytes of memory.
Processor board ID VIOS1000001
2 Gigabit Ethernet interfaces
DRAM configuration is 72 bits wide with parity disabled.
256K bytes of non-volatile configuration memory.
2097152K bytes of physical flash disk at slot 0

Configuration register is 0x2102"""
    elif "show ip arp" in cmd:
        return f"""Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.12.1            -   5000.0001.0000  ARPA   GigabitEthernet0/0
Internet  192.168.12.2            3   5000.0002.0000  ARPA   GigabitEthernet0/0"""
    elif "show cdp neighbors" in cmd:
        if device == "R1":
            return """Capability Codes: R - Router, T - Trans Bridge, B - Source Route Bridge
                  S - Switch, H - Host, I - IGMP, r - Repeater, P - Phone, 
                  D - Remote Source Route Bridge, Y - MOP Device

Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID
R2               Gig0/0            176             R B             Gig0/0
Switch1          Gig0/1            125              S              Gig0/1
"""
        elif device == "R2":
            return """Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID
R1               Gig0/0            174             R B             Gig0/0
R3               Gig0/1            142             R B             Gig0/0
"""
        elif device == "R3":
            return """Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID
R2               Gig0/0            179             R B             Gig0/1
Switch2          Gig0/1            134              S              Gig0/1
"""
    return "Command not supported or empty output"
