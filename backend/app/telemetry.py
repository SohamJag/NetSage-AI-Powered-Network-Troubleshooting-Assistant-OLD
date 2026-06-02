import os
import datetime
import json
from sqlalchemy.orm import Session
from netmiko import ConnectHandler
from .database import SessionLocal
from .models import Device, TelemetryRun, Incident, SimulationState
from .simulator import run_simulated_command, SCENARIOS
from .parsing import parse_command
from .rules import extract_facts_from_telemetry, evaluate_rules
from .ai_advisor import get_ai_recommendation

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

COMMANDS_TO_COLLECT = [
    "show version",
    "show ip route",
    "show ip ospf neighbor",
    "show interface",
    "show interface status",
    "show running-config",
    "show logging",
    "show processes cpu",
    "show memory statistics",
    "show access-lists",
    "ping 192.168.4.10"
]

def collect_device_telemetry(db: Session, device: Device, scenario_id: int = 0, real_mode: bool = False):
    """
    Collects telemetry from a device.
    If real_mode is True, attempts a live Netmiko SSH connection.
    If real_mode is False, runs simulated Cisco IOS commands from the sandbox.
    Saves outputs to data/<device>/<date>/<command>.txt
    """
    timestamp = datetime.datetime.utcnow()
    date_str = timestamp.strftime("%Y-%m-%d")
    device_data_dir = os.path.join(DATA_DIR, device.name, date_str)
    os.makedirs(device_data_dir, exist_ok=True)
    
    device_facts_parsed = {}
    collected_results = {}

    ssh_connection = None
    if real_mode:
        try:
            device_params = {
                'device_type': 'cisco_ios',
                'host': device.ip,
                'username': device.username,
                'password': device.password,
                'port': device.port,
                'timeout': 10
            }
            ssh_connection = ConnectHandler(**device_params)
        except Exception as e:
            print(f"Failed to connect to real device {device.name} via SSH: {e}. Falling back to virtual sandbox mode.")
            real_mode = False # Fall back to simulation

    for cmd in COMMANDS_TO_COLLECT:
        raw_output = ""
        if real_mode and ssh_connection:
            try:
                raw_output = ssh_connection.send_command(cmd)
            except Exception as e:
                print(f"Error executing command {cmd} on real device {device.name}: {e}")
                raw_output = f"SSH ERROR: {e}"
        else:
            # Simulated Sandbox mode
            raw_output = run_simulated_command(device.name, cmd, scenario_id)
            
        # Save raw output to file
        safe_cmd_name = cmd.replace(" ", "_").replace(".", "_").replace("/", "_")
        file_path = os.path.join(device_data_dir, f"{safe_cmd_name}.txt")
        try:
            with open(file_path, "w") as f:
                f.write(raw_output)
        except Exception as e:
            print(f"Failed to save file {file_path}: {e}")
            
        # Parse command output
        parsed_json = parse_command(cmd, raw_output)
        
        # Save to database
        run = TelemetryRun(
            timestamp=timestamp,
            device_name=device.name,
            command_name=cmd,
            raw_output=raw_output,
            parsed_output=json.dumps(parsed_json)
        )
        db.add(run)
        
        # Keep track of parsed data to build device facts
        collected_results[cmd] = parsed_json
        
        # Also store raw ping & logging for the rule evaluator
        if "ping" in cmd:
            collected_results["ping"] = raw_output
        if "show logging" in cmd:
            collected_results["show logging"] = raw_output

    if real_mode and ssh_connection:
        try:
            ssh_connection.disconnect()
        except Exception:
            pass

    # Extract facts from parsed telemetry
    facts = extract_facts_from_telemetry(device.name, collected_results, scenario_id)
    
    # Run Rule-Based Analysis Engine
    diagnoses = evaluate_rules(facts)
    
    # Update Device Health status based on findings
    device_status = "Healthy"
    highest_severity = "Low"
    cpu_val = 10.0
    mem_val = 40.0
    
    if scenario_id == 6 and device.name == "R1":
        cpu_val = 98.0
        mem_val = 95.0
    elif device.name == "R1":
        cpu_val = 8.0
        mem_val = 42.0
    elif device.name == "R2":
        cpu_val = 7.0
        mem_val = 39.0
    elif device.name == "R3":
        cpu_val = 6.0
        mem_val = 38.0

    if len(diagnoses) > 0:
        device_status = "Warning"
        for diag in diagnoses:
            sev = diag["severity"]
            if sev == "Critical" or sev == "High":
                device_status = "Critical"
                highest_severity = sev
                break
            elif sev == "Medium":
                device_status = "Warning"
                highest_severity = sev
                
    device.status = device_status
    device.cpu_usage = cpu_val
    device.memory_usage = mem_val
    device.last_checked = timestamp
    db.commit()

    # Generate incidents for matched high-severity scenarios
    for diag in diagnoses:
        if diag["confidence_score"] >= 60 and diag["severity"] in ["High", "Critical", "Medium"]:
            # Check if this incident is already open for this device
            existing_incident = db.query(Incident).filter(
                Incident.device_name == device.name,
                Incident.issue == diag["issue"],
                Incident.status == "Open"
            ).first()
            
            if not existing_incident:
                # Generate dynamic incident ID
                inc_count = db.query(Incident).count() + 1
                inc_id = f"INC-{inc_count:03d}"
                
                # Fetch AI Advisory enrichment
                ai_rec = get_ai_recommendation(
                    device=device.name,
                    scenario_id=scenario_id,
                    issue_name=diag["name"],
                    severity=diag["severity"],
                    confidence=diag["confidence_score"],
                    raw_telemetry=collected_results.get("show running-config", "")
                )
                
                res_notes = {
                    "root_cause_explanation": ai_rec.get("root_cause"),
                    "impact_analysis": ai_rec.get("impact"),
                    "recommended_fix": ai_rec.get("recommended_fix"),
                    "remediation_steps": ai_rec.get("remediation_steps", []),
                    "validation_commands": ai_rec.get("validation_commands", []),
                    "risk_level": ai_rec.get("risk_level")
                }
                
                incident = Incident(
                    incident_id=inc_id,
                    timestamp=timestamp,
                    device_name=device.name,
                    severity=diag["severity"],
                    issue=diag["issue"],
                    root_cause=diag["name"],
                    confidence_score=diag["confidence_score"],
                    status="Open",
                    resolution_notes=json.dumps(res_notes)
                )
                db.add(incident)
                db.commit()
                
    return diagnoses

def trigger_telemetry_collection_cycle(db: Session, real_mode: bool = False):
    """
    Executes a complete telemetry collection cycle across all monitored devices
    based on the current active simulation state.
    """
    # Get active simulation scenario
    sim_state = db.query(SimulationState).first()
    if not sim_state:
        sim_state = SimulationState(current_scenario=0, scenario_name=SCENARIOS[0])
        db.add(sim_state)
        db.commit()
        
    scenario_id = sim_state.current_scenario
    devices = db.query(Device).all()
    
    # If no devices exist, initialize defaults
    if not devices:
        initialize_default_devices(db)
        devices = db.query(Device).all()
        
    all_diagnoses = {}
    for device in devices:
        # switches, servers, and clients are not polled via complex CLI, we only poll routers (R1, R2, R3)
        # switches are updated dynamically based on scenario status
        if device.type == "router":
            diags = collect_device_telemetry(db, device, scenario_id, real_mode)
            all_diagnoses[device.name] = diags
        else:
            # Update switch/server/client health based on scenario state
            timestamp = datetime.datetime.utcnow()
            device.last_checked = timestamp
            
            if scenario_id == 3 and device.name == "Server01":
                device.status = "Warning" # Isolated
            elif scenario_id == 4 and device.name == "Server01":
                device.status = "Warning" # One way routing
            elif scenario_id == 5 and device.name == "Server01":
                device.status = "Warning" # Blocked by ACL
            else:
                device.status = "Healthy"
                
            db.commit()
            
    # Auto-resolve incidents if scenario is 0 (Healthy)
    if scenario_id == 0:
        open_incidents = db.query(Incident).filter(Incident.status == "Open").all()
        for inc in open_incidents:
            inc.status = "Resolved"
            inc.resolution_notes = inc.resolution_notes or ""
            # Append resolution message
            try:
                notes = json.loads(inc.resolution_notes) if inc.resolution_notes else {}
                notes["resolution_summary"] = "Automatically resolved during baseline telemetry collection cycle. No active fault detected."
                inc.resolution_notes = json.dumps(notes)
            except Exception:
                inc.resolution_notes = json.dumps({"resolution_summary": "Resolved by Baseline check."})
        db.commit()
            
    return all_diagnoses

def initialize_default_devices(db: Session):
    default_devices = [
        Device(name="R1", type="router", ip="192.168.12.1", port=22, username="admin", password="cisco", status="Healthy"),
        Device(name="R2", type="router", ip="192.168.12.2", port=22, username="admin", password="cisco", status="Healthy"),
        Device(name="R3", type="router", ip="192.168.23.2", port=22, username="admin", password="cisco", status="Healthy"),
        Device(name="Switch1", type="switch", ip="192.168.1.2", port=22, username="admin", password="cisco", status="Healthy"),
        Device(name="Switch2", type="switch", ip="192.168.4.2", port=22, username="admin", password="cisco", status="Healthy"),
        Device(name="Server01", type="server", ip="192.168.4.10", port=80, username="webadmin", password="admin", status="Healthy"),
        Device(name="Client01", type="client", ip="192.168.1.50", port=22, username="client", password="password", status="Healthy"),
    ]
    for d in default_devices:
        db.add(d)
    db.commit()
