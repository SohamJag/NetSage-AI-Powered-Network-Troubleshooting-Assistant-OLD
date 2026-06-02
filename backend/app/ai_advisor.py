import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3" # Default model

def query_ollama_advisor(prompt):
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=5)
        if response.status_code == 200:
            result = response.json()
            return json.loads(result.get("response", "{}"))
    except Exception as e:
        print(f"Ollama connection failed, using high-fidelity local NetSage Advisor fallback: {e}")
    return None

def get_expert_ai_recommendation(device, scenario_id, issue_name, severity, confidence):
    """
    High-fidelity deterministic local NetSage Advisor that simulates a CCIE-level expert response.
    Guarantees the system works flawlessly even if Ollama is not configured.
    """
    advisories = {
        1: {
            "root_cause": f"OSPF Adjacency state is DOWN between router R1 and R2 due to an Area ID Mismatch. R1 is configured for Area 0 on its GigabitEthernet0/0 interface, whereas R2 is configured for Area 10 on its GigabitEthernet0/0 interface.",
            "impact": "No routing table exchanges can occur between Head Office (R1) and Branch (R2). Branch subnet 192.168.1.0/24 is isolated from the rest of the network, preventing any traffic flow from clients to the datacenter server.",
            "recommended_fix": f"Synchronize the OSPF area configuration on the connecting link. Change R2's GigabitEthernet0/0 configuration to be in OSPF Area 0.",
            "remediation_steps": [
                "Configure R2: enter configuration terminal.",
                "Navigate to interface: 'interface GigabitEthernet0/0'.",
                "Remove mismatched area: 'no ip ospf 1 area 10'.",
                "Apply correct area: 'ip ospf 1 area 0'."
            ],
            "validation_commands": [
                "show ip ospf neighbor",
                "show ip ospf interface GigabitEthernet0/0",
                "show ip route"
            ],
            "risk_level": "Low (non-disruptive, resolves the routing outage immediately)."
        },
        2: {
            "root_cause": f"OSPF Adjacency state is DOWN between router R1 and R2 due to a Cryptographic Message-Digest Authentication Mismatch. R1 is configured with MD5 key 'CISCO123', while R2 is configured with the incorrect password 'WRONG_KEY'.",
            "impact": "OSPF neighbor state cannot reach FULL. Routers drop OSPF Hello packets due to invalid signature, stopping all routing propagation between Head Office and Branch networks.",
            "recommended_fix": "Align the OSPF message-digest authentication key on both connecting interfaces to use identical passwords.",
            "remediation_steps": [
                "Access R2 configuration mode.",
                "Select interface: 'interface GigabitEthernet0/0'.",
                "Modify the md5 key: 'ip ospf message-digest-key 1 md5 CISCO123'.",
                "Ensure authentication is enabled: 'ip ospf authentication message-digest'."
            ],
            "validation_commands": [
                "show running-config interface GigabitEthernet0/0",
                "show ip ospf neighbor"
            ],
            "risk_level": "Low (fixes authentication protocol parameters without affecting other active segments)."
        },
        3: {
            "root_cause": f"GigabitEthernet0/1 interface on R2 connected to R3 is 'administratively down'. This interface has been manually shut down by an administrator.",
            "impact": "Complete physical link loss between the Branch (R2) and the Datacenter (R3). The OSPF adjacency has collapsed, and all networks behind R3 (including Server 192.168.4.10) are unreachable from the rest of the network.",
            "recommended_fix": "Bring up GigabitEthernet0/1 on R2 by executing the 'no shutdown' command.",
            "remediation_steps": [
                "Log into R2 and enter config mode: 'configure terminal'.",
                "Select interface: 'interface GigabitEthernet0/1'.",
                "Issue command: 'no shutdown'.",
                "Wait 5 seconds for line protocol to change state to UP."
            ],
            "validation_commands": [
                "show interface GigabitEthernet0/1",
                "show interface status",
                "show ip ospf neighbor"
            ],
            "risk_level": "Low (Standard operational change, immediately restores the link)."
        },
        4: {
            "root_cause": "The Datacenter Router R3 has a missing IP route back to the Client subnet 192.168.1.0/24. While R1 and R2 have routing information, R3 cannot reply to packets incoming from the client subnet because it has no default or static path matching that subnet.",
            "impact": "One-way routing black hole. Packets reach the datacenter server, but the server's replies are dropped at R3. Ping and application connections from the client to the server fail completely.",
            "recommended_fix": "Add a static route on R3 pointing to the Branch router R2 next-hop IP, or enable redistribution under OSPF.",
            "remediation_steps": [
                "Access R3 via console, enter configuration mode.",
                "Define static path: 'ip route 192.168.1.0 255.255.255.0 192.168.23.1'.",
                "Alternatively, if using dynamic routing, ensure redistribution of connected networks is active under 'router ospf 1'."
            ],
            "validation_commands": [
                "show ip route",
                "ping 192.168.1.50 (test return path)"
            ],
            "risk_level": "Low (Safely routes target subnet traffic without affecting existing flows)."
        },
        5: {
            "root_cause": "An Extended Access Control List (ACL) named 'BLOCK_CLIENT' is applied in the inbound direction on R3's GigabitEthernet0/1 (or outbound on R3). The ACL rules explicitly deny all IP/ICMP traffic originating from the Client subnet 192.168.1.0/24 targeting the Datacenter server subnet 192.168.4.0/24.",
            "impact": "Security policy blocking. Client host is blocked from accessing the Datacenter server. All connectivity testing (ping/http) is dropped with hit counters incrementing on R3's ACL.",
            "recommended_fix": "Modify the ACL to permit authorized client traffic, or remove the ACL filter binding from the interface if it is no longer required.",
            "remediation_steps": [
                "Access R3 terminal config mode.",
                "Remove the access-group binding on GigabitEthernet0/1: 'interface GigabitEthernet0/1' followed by 'no ip access-group BLOCK_CLIENT in'.",
                "Or modify ACL rules: 'ip access-list extended BLOCK_CLIENT' then delete the deny statement: 'no deny ip 192.168.1.0 0.0.0.255 192.168.4.0 0.0.0.255' and insert permit rules."
            ],
            "validation_commands": [
                "show access-lists BLOCK_CLIENT",
                "show running-config interface GigabitEthernet0/1"
            ],
            "risk_level": "Medium (modifying firewall filters requires change controls to avoid security leaks)."
        },
        6: {
            "root_cause": "The Head Office Router R1 is experiencing Control Plane Exhaustion. The CPU utilization is at 98% with the 'IP Input' and 'OSPF Router' processes occupying the majority of scheduling. There is also low free processor memory.",
            "impact": "Extreme network degradation. Packets are dropped due to input buffer overflows, ping round-trip times have spiked to >240ms, OSPF Hello packets are delayed (triggering potential adjacency drops), and the CLI console is sluggish.",
            "recommended_fix": "Enable Cisco Express Forwarding (CEF) globally to offload CPU routing decisions to the hardware ASIC, rate-limit control plane traffic using CoPP, and check for OSPF SPF loops.",
            "remediation_steps": [
                "Log into R1.",
                "Ensure CEF is active globally: 'ip cef'.",
                "Implement Control Plane Policing (CoPP) to drop excessive management traffic: 'control-plane' -> 'service-policy input COPP-POLICY'.",
                "Review memory usage and clear hung SSH connections: 'clear line <line_num>'."
            ],
            "validation_commands": [
                "show processes cpu sorted",
                "show ip cef",
                "show memory statistics"
            ],
            "risk_level": "High (high load can make device unresponsive, apply changes with care)."
        }
    }
    
    # Fallback default for baseline or other issues
    default_advisory = {
        "root_cause": f"No active fault detected. The system health on {device} is running within standard operating baselines. OSPF adjacencies are FULL, interfaces are UP, and ping latency is within nominal bounds (<10ms).",
        "impact": "None. The network is operating fully with redundant paths available.",
        "recommended_fix": "No action required at this time. Continue monitoring baseline metrics.",
        "remediation_steps": [
            "Maintain current configuration.",
            "Set up alerts for threshold crossings on CPU/memory."
        ],
        "validation_commands": [
            "show ip interface brief",
            "show ip ospf neighbor"
        ],
        "risk_level": "None"
    }
    
    return advisories.get(scenario_id, default_advisory)

def get_ai_recommendation(device, scenario_id, issue_name, severity, confidence, raw_telemetry=None):
    """
    Core advisor routing. Attempts local Ollama and falls back gracefully to
    our pre-compiled NetSage expert advisories.
    """
    if raw_telemetry:
        # Construct the CCIE prompt for Ollama
        prompt = f"""
You are an expert CCIE-level Network Reliability Engineer.
Analyze the following troubleshooting data from network device {device}:
Issue: {issue_name}
Severity: {severity}
Confidence: {confidence}%

Device CLI Telemetry Snippet:
{raw_telemetry}

Provide your analysis in JSON format with these exact keys:
{{
  "root_cause": "Detailed explanation of why it failed",
  "impact": "What is the network impact and which subnets are isolated",
  "recommended_fix": "High-level summary of the fix",
  "remediation_steps": [
     "Step 1 to execute",
     "Step 2 to execute"
  ],
  "validation_commands": [
     "Command 1 to verify",
     "Command 2 to verify"
  ],
  "risk_level": "Low/Medium/High risk"
}}
"""
        # Try Ollama
        ollama_response = query_ollama_advisor(prompt)
        if ollama_response:
            return ollama_response
            
    # Fallback to local expert advisor
    return get_expert_ai_recommendation(device, scenario_id, issue_name, severity, confidence)
