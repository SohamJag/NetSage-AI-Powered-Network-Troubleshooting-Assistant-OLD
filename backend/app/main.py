import os
import json
import datetime
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .database import engine, get_db, Base
from .models import Device, Incident, SimulationState, TelemetryRun
from .telemetry import trigger_telemetry_collection_cycle, initialize_default_devices
from .simulator import SCENARIOS
from .reporting import generate_pdf_report, generate_csv_report, generate_html_report

# Initialize database tables
Base.metadata.create_all(bind=engine)

class TerminalRequest(BaseModel):
    device: str
    command: str

app = FastAPI(title="NetSage AI Network Troubleshooting Assistant Backend")


# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    # Initialize devices if not present
    devices_count = db.query(Device).count()
    if devices_count == 0:
        initialize_default_devices(db)
        
    # Initialize simulation state if not present
    sim_count = db.query(SimulationState).count()
    if sim_count == 0:
        sim = SimulationState(current_scenario=0, scenario_name=SCENARIOS[0])
        db.add(sim)
        db.commit()
        
    # Trigger an initial baseline collection cycle
    trigger_telemetry_collection_cycle(db, real_mode=False)

@app.get("/api/devices")
def get_devices(db: Session = Depends(get_db)):
    return db.query(Device).all()

@app.get("/api/incidents")
def get_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).order_by(Incident.timestamp.desc()).all()

@app.get("/api/incidents/{incident_id}")
def get_incident_detail(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Try parsing resolution notes if they are JSON
    notes = {}
    if inc.resolution_notes:
        try:
            notes = json.loads(inc.resolution_notes)
        except Exception:
            notes = {"custom_notes": inc.resolution_notes}
            
    return {
        "id": inc.id,
        "incident_id": inc.incident_id,
        "timestamp": inc.timestamp,
        "device_name": inc.device_name,
        "severity": inc.severity,
        "issue": inc.issue,
        "root_cause": inc.root_cause,
        "confidence_score": inc.confidence_score,
        "status": inc.status,
        "resolution_details": notes
    }

@app.post("/api/telemetry/collect")
def collect_telemetry(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Run the collection cycle
    try:
        diagnoses = trigger_telemetry_collection_cycle(db, real_mode=False)
        return {"status": "success", "message": "Telemetry collection cycle executed successfully", "diagnoses": diagnoses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute telemetry collection: {str(e)}")

@app.get("/api/simulation/state")
def get_simulation_state(db: Session = Depends(get_db)):
    state = db.query(SimulationState).first()
    if not state:
        return {"current_scenario": 0, "scenario_name": SCENARIOS[0]}
    return {
        "current_scenario": state.current_scenario,
        "scenario_name": state.scenario_name,
        "active_since": state.active_since
    }

@app.post("/api/simulation/scenario/{scenario_id}")
def trigger_simulation_scenario(scenario_id: int, db: Session = Depends(get_db)):
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=400, detail="Invalid scenario ID")
        
    state = db.query(SimulationState).first()
    if not state:
        state = SimulationState(current_scenario=scenario_id, scenario_name=SCENARIOS[scenario_id])
        db.add(state)
    else:
        state.current_scenario = scenario_id
        state.scenario_name = SCENARIOS[scenario_id]
        state.active_since = datetime.datetime.utcnow()
        
    db.commit()
    
    # Run a telemetry collection cycle immediately so that database models
    # update reflecting the failure state!
    trigger_telemetry_collection_cycle(db, real_mode=False)
    
    return {
        "status": "success", 
        "message": f"Simulation scenario triggered: {SCENARIOS[scenario_id]}",
        "current_scenario": scenario_id
    }

@app.get("/api/topology")
def get_topology(db: Session = Depends(get_db)):
    # Topology endpoints details nodes and links states
    sim_state = db.query(SimulationState).first()
    scenario_id = sim_state.current_scenario if sim_state else 0
    
    # Create network layout nodes
    nodes = [
        {"id": "Client01", "label": "Client Host", "type": "client", "ip": "192.168.1.50", "status": "Healthy"},
        {"id": "Switch1", "label": "HO Switch", "type": "switch", "ip": "192.168.1.2", "status": "Healthy"},
        {"id": "R1", "label": "HO Router (R1)", "type": "router", "ip": "192.168.12.1", "status": "Healthy"},
        {"id": "R2", "label": "Branch Router (R2)", "type": "router", "ip": "192.168.12.2", "status": "Healthy"},
        {"id": "R3", "label": "DC Router (R3)", "type": "router", "ip": "192.168.23.2", "status": "Healthy"},
        {"id": "Switch2", "label": "DC Switch", "type": "switch", "ip": "192.168.4.2", "status": "Healthy"},
        {"id": "Server01", "label": "Application Server", "type": "server", "ip": "192.168.4.10", "status": "Healthy"}
    ]
    
    # Base links (Default green / active)
    links = [
        {"source": "Client01", "target": "Switch1", "status": "active"},
        {"source": "Switch1", "target": "R1", "status": "active"},
        {"source": "R1", "target": "R2", "status": "active", "label": "OSPF Area 0"},
        {"source": "R2", "target": "R3", "status": "active", "label": "OSPF Area 0"},
        {"source": "R3", "target": "Switch2", "status": "active"},
        {"source": "Switch2", "target": "Server01", "status": "active"}
    ]
    
    # Apply scenario effects
    affected_networks = []
    affected_devices = []
    
    # Fetch device models to sync state
    devices = db.query(Device).all()
    dev_statuses = {d.name: d.status for d in devices}
    for n in nodes:
        if n["id"] in dev_statuses:
            n["status"] = dev_statuses[n["id"]]
            
    if scenario_id in [1, 2]: # OSPF R1-R2 neighbor down
        # Link R1 to R2 is down/mismatched
        for link in links:
            if link["source"] == "R1" and link["target"] == "R2":
                link["status"] = "broken"
                link["error_message"] = "OSPF Neighbor Down / Area Mismatch" if scenario_id == 1 else "OSPF Authentication Mismatch"
        
        # Isolated paths
        affected_networks = ["192.168.4.0/24 (Server Subnet)", "192.168.23.0/30"]
        affected_devices = ["Server01", "DC Switch", "DC Router (R3)"]
        for n in nodes:
            if n["id"] in ["Server01"]:
                n["status"] = "Warning"
                
    elif scenario_id == 3: # Link R2-R3 interface shutdown
        for link in links:
            if link["source"] == "R2" and link["target"] == "R3":
                link["status"] = "broken"
                link["error_message"] = "Interface Gi0/1 administratively down"
                
        affected_networks = ["192.168.4.0/24 (Server Subnet)"]
        affected_devices = ["Server01", "Switch2", "R3"]
        for n in nodes:
            if n["id"] in ["Server01"]:
                n["status"] = "Warning"
                
    elif scenario_id == 4: # Missing Route on R3 back to Client 192.168.1.0/24
        # Link state is active physically, but path routing is affected
        for link in links:
            if link["source"] == "R2" and link["target"] == "R3":
                link["status"] = "degraded"
                link["error_message"] = "Missing Route on R3 back to Client"
                
        affected_networks = ["192.168.1.0/24 (Client Subnet - return path)"]
        affected_devices = ["Client01"]
        for n in nodes:
            if n["id"] in ["Server01"]:
                n["status"] = "Warning"
                
    elif scenario_id == 5: # ACL blocking on R3
        for link in links:
            if link["source"] == "R3" and link["target"] == "Switch2":
                link["status"] = "degraded"
                link["error_message"] = "ACL BLOCK_CLIENT denys ICMP/IP traffic"
                
        affected_networks = ["Client-Server communication (192.168.1.0/24 -> 192.168.4.10)"]
        affected_devices = ["Server01", "Client01"]
        for n in nodes:
            if n["id"] in ["Server01"]:
                n["status"] = "Warning"
                
    elif scenario_id == 6: # High CPU R1
        for n in nodes:
            if n["id"] == "R1":
                n["status"] = "Critical"
        for link in links:
            if link["source"] == "Switch1" and link["target"] == "R1":
                link["status"] = "degraded"
                link["error_message"] = "High Latency & Buffer drops (CPU 98%)"
                
    return {
        "scenario_id": scenario_id,
        "scenario_name": SCENARIOS[scenario_id],
        "nodes": nodes,
        "links": links,
        "impact_analysis": {
            "affected_networks": affected_networks,
            "affected_devices": affected_devices
        }
    }

@app.get("/api/reports/generate/{report_format}")
def download_reports(report_format: str, db: Session = Depends(get_db)):
    if report_format == "pdf":
        file_path = generate_pdf_report(db)
        return FileResponse(file_path, media_type="application/pdf", filename="netsage_monthly_report.pdf")
    elif report_format == "csv":
        file_path = generate_csv_report(db)
        return FileResponse(file_path, media_type="text/csv", filename="netsage_incident_history.csv")
    elif report_format == "html":
        file_path = generate_html_report(db)
        return FileResponse(file_path, media_type="text/html", filename="netsage_executive_report.html")
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats: pdf, csv, html")

@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    incidents = db.query(Incident).all()
    
    # 1. Most frequent issues
    issue_counts = {}
    for inc in incidents:
        issue_counts[inc.root_cause] = issue_counts.get(inc.root_cause, 0) + 1
    most_frequent_issues = [{"issue": k, "count": v} for k, v in issue_counts.items()]
    most_frequent_issues.sort(key=lambda x: x["count"], reverse=True)
    
    # 2. Most unstable devices
    device_counts = {}
    for inc in incidents:
        device_counts[inc.device_name] = device_counts.get(inc.device_name, 0) + 1
    most_unstable_devices = [{"device": k, "count": v} for k, v in device_counts.items()]
    most_unstable_devices.sort(key=lambda x: x["count"], reverse=True)
    
    # 3. Incident trends
    # Mock some historical trends if data is sparse to make the graphs look stunning
    trends = [
        {"month": "Jan", "incidents": 2},
        {"month": "Feb", "incidents": 5},
        {"month": "Mar", "incidents": 4},
        {"month": "Apr", "incidents": len([i for i in incidents if i.timestamp.month == 4]) or 8},
        {"month": "May", "incidents": len([i for i in incidents if i.timestamp.month == 5]) or 12},
        {"month": "Jun", "incidents": len(incidents) or 15}
    ]
    
    # 4. Mean Time to Detect (MTTD) & Resolve (MTTR)
    # Simple simulated metrics
    mttd = "4.2 minutes" # MTTD
    mttr = "14.5 minutes" # MTTR
    
    return {
        "most_frequent_issues": most_frequent_issues[:5],
        "most_unstable_devices": most_unstable_devices[:5],
        "incident_trends": trends,
        "mttd": mttd,
        "mttr": mttr
    }

@app.post("/api/terminal/run")
def run_terminal_command(req: TerminalRequest, db: Session = Depends(get_db)):
    from .simulator import run_simulated_command
    sim_state = db.query(SimulationState).first()
    scenario_id = sim_state.current_scenario if sim_state else 0
    
    # Check if device is valid
    if req.device not in ["R1", "R2", "R3"]:
        if req.device in ["Client01", "Server01"]:
            if "ping" in req.command.lower():
                from .simulator import run_simulated_ping
                output = run_simulated_ping(scenario_id, req.device, "192.168.4.10")
                return {"output": output}
            return {"output": f"{req.device}:~$ {req.command}\nCommand not found"}
        raise HTTPException(status_code=400, detail="Invalid device name")
        
    output = run_simulated_command(req.device, req.command, scenario_id)
    return {"output": output}

