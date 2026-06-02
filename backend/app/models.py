from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)  # 'router', 'switch', 'server', 'client'
    ip = Column(String)
    port = Column(Integer, default=22)
    username = Column(String, default="admin")
    password = Column(String, default="cisco")
    status = Column(String, default="Healthy")  # 'Healthy', 'Warning', 'Critical'
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    last_checked = Column(DateTime, default=datetime.datetime.utcnow)

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True, index=True)  # e.g., INC-001
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    device_name = Column(String, index=True)
    severity = Column(String)  # 'Low', 'Medium', 'High', 'Critical'
    issue = Column(String)
    root_cause = Column(String)
    confidence_score = Column(Float)
    status = Column(String, default="Open")  # 'Open', 'Resolved'
    resolution_notes = Column(Text, nullable=True)

class TelemetryRun(Base):
    __tablename__ = "telemetry_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    device_name = Column(String, index=True)
    command_name = Column(String)  # 'show ip route', etc.
    raw_output = Column(Text)
    parsed_output = Column(Text)  # Store as JSON string

class SimulationState(Base):
    __tablename__ = "simulation_state"
    
    id = Column(Integer, primary_key=True, index=True)
    current_scenario = Column(Integer, default=0)  # 0: Healthy, 1: OSPF Area, 2: OSPF Auth, etc.
    scenario_name = Column(String, default="Healthy / Baseline")
    active_since = Column(DateTime, default=datetime.datetime.utcnow)
