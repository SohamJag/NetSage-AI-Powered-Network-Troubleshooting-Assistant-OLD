# Implementation Plan: NetSage – AI-Powered Network Troubleshooting Assistant

NetSage is a full-stack, enterprise-grade Network Reliability Engineering (NRE) platform designed to automate network telemetry collection, analyze device health, detect network faults, identify root causes, calculate confidence scores, and provide AI-driven remediation recommendations.

This plan details the full implementation, combining a robust Python/FastAPI backend with a state-of-the-art React frontend. To make the project instantly demoable and self-contained without physical hardware, we will implement a dual-mode **Telemetry Engine** that supports both actual SSH connections via Netmiko/Paramiko and a **High-Fidelity Virtual Sandbox Simulator** that simulates Cisco IOS device responses under various failure scenarios.

---

## 1. Directory Structure

```text
NetSage-AI-Troubleshooting/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI Application entry point
│   │   ├── database.py             # SQLite DB setup with SQLAlchemy
│   │   ├── models.py               # SQLAlchemy Database Models (incidents, devices, telemetry)
│   │   ├── telemetry.py            # Telemetry collection (Netmiko & Simulated Sandbox)
│   │   ├── parsing.py              # Parsing engine (Genie/TextFSM + Regex)
│   │   ├── rules.py                # Rule-based analysis engine & confidence scoring
│   │   ├── ai_advisor.py           # Local LLM (Ollama) & fallbacks
│   │   ├── simulator.py            # Failure simulation engine (scenarios 1-6)
│   │   └── reporting.py            # PDF/HTML/CSV reporting engine
│   ├── data/                       # Telemetry raw outputs storage
│   ├── database.db                 # SQLite database
│   ├── requirements.txt            # Python dependencies
│   └── run.py                      # Backend startup script
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/             # Reusable UI Components
│   │   │   ├── Dashboard.jsx       # Main Dashboard view
│   │   │   ├── NetworkTopology.jsx # Dynamic Topology Map (D3.js or custom interactive SVG)
│   │   │   ├── IncidentList.jsx    # Active and Historical Incidents
│   │   │   ├── DeviceHealth.jsx    # CPU, memory, and interface metrics
│   │   │   ├── SimulationLab.jsx   # Interactive failure simulation controls
│   │   │   └── AIRecommendations.jsx # AI-powered troubleshooting advice
│   │   ├── App.jsx
│   │   ├── index.css               # Design system & styles
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js          # Tailwind CSS config
│   └── vite.config.js
└── README.md                       # Comprehensive guide
```

---

## 2. Component Design & Technical Specs

### A. Dual-Mode Telemetry Collection Module (`telemetry.py` & `simulator.py`)
- **Real SSH Mode**: Connects to Cisco/FRR devices using Netmiko, executes commands (`show ip route`, `show ip ospf neighbor`, `show interface`, etc.), and saves them to `backend/data/<device>/<date>/<command>.txt`.
- **Sandbox Simulator Mode**: Emulates Cisco IOS command line outputs. When a user activates a scenario in the UI, the simulator alters the state of the virtual topology. Subsequent collection runs read simulated router CLI outputs matching the failure state.
- **Scenarios Supported**:
  1. *OSPF Area Mismatch*: `show ip ospf neighbor` shows neighbor down; `show running-config` reveals mismatched areas on link.
  2. *OSPF Authentication Mismatch*: Neighbor down; `show ip ospf neighbor` empty; config reveals authentication mismatch.
  3. *Interface Shutdown*: `show interface` reports `administratively down, line protocol is down`.
  4. *Missing Static Route*: Router misses route to 192.168.3.0/24; ping/traceroute tests fail.
  5. *ACL Blocking Traffic*: Traffic from Client hits an ACL and gets dropped; ACL hit counters increase.
  6. *High CPU/Memory Exhaustion*: CPU processes spike in `show processes cpu`.

### B. Parsing & Rule Engine (`parsing.py` & `rules.py`)
- **Parsing**: Translates raw text CLI commands into clean structured JSON. We use Python patterns (or light Genie/TextFSM wrappers) to return parsed interfaces, routing tables, OSPF neighbors, and processes.
- **Rule Engine**: Evaluates JSON facts against pre-defined rules.
  - Matches multi-condition criteria.
  - Computes a deterministic **Confidence Score** based on the matching density formula: $\text{Confidence} = (\text{Matched Conditions} / \text{Total Conditions}) \times 100$.
  - Includes a comprehensive network knowledge base (50+ scenarios) stored as a local JSON file.

### C. AI Advisory Layer (`ai_advisor.py`)
- Interfaces with a local **Ollama** instance (running Llama 3 or Mistral) or falls back to a high-quality local LLM heuristic client if Ollama is not reachable.
- Combines the structured output of the Rule Engine with the raw CLI data to provide:
  1. Root cause summary.
  2. Step-by-step human remediation guide.
  3. Precise validation commands to run.
  4. Risk level analysis.

### D. Topology Visualization (`NetworkTopology.jsx`)
- Built using an interactive, custom React SVG graph or Pyvis/NetworkX. It dynamically renders the network nodes (R1, R2, R3, Switches, Server, Client).
- Shows link status (Green = Active, Red = Broken) and path trace.
- Under simulation failures, it performs **Impact Analysis**, highlighting affected paths, servers, and subnets.

### E. Frontend Design System (`index.css`)
- Fully custom, high-end design using deep dark theme, glassmorphism card layouts (`backdrop-filter: blur`), smooth neon ambient glows, and intuitive status micro-animations.
- Modern fonts (e.g., Outfit or Inter) loaded via Google Fonts.

---

## 3. Implementation Steps

1. **Phase 1: Backend Architecture & SQLite Database**
   - Define database models for `Device`, `Incident`, `TelemetryRun`, and `SimulationState`.
   - Setup SQLite tables.

2. **Phase 2: Simulation Sandbox & Commands Output Generator**
   - Write standard CLI output templates for the 6 target failure states.
   - Develop the logic that reads/writes actual files in the `data/` structure just as a Netmiko collector would.

3. **Phase 3: Parsing & Rule Engine**
   - Write robust parsers for CLI text (e.g. `show ip route`, `show ip ospf neighbor`, etc.).
   - Define the Rule Engine with priority sorting, multi-condition matching, and confidence scores.

4. **Phase 4: AI Advisor API**
   - Build API for Ollama integration and an intelligent deterministic fallback helper that acts as a NetDevOps advisor.

5. **Phase 5: React + Tailwind CSS Dashboard**
   - Setup Vite React frontend.
   - Build custom SVG network topology map showing live failures.
   - Connect frontend to backend REST APIs.

6. **Phase 6: Failure Simulation Lab & Reporting**
   - Add dashboard controls to trigger scenarios and watch the topology instantly degrade, alerts fire, and AI recommend fixes.
   - Implement PDF/HTML/CSV reporting downloads.

---

## 4. Feedback Request
Before proceeding, please verify:
1. **Tailwind CSS Version**: Do you want us to proceed with **Tailwind CSS v3** or **Tailwind CSS v4**?
2. **AI Engine Integration**: Do you have a local Ollama instance running, or should we focus heavily on our robust local fallback AI model so it runs instantly without setup?
3. **Any specific GNS3/EVE-NG integration**: Shall we implement the virtual simulation engine as the default sandbox, with a config file that supports real Cisco IOS SSH connections if you plug in your credentials later?
