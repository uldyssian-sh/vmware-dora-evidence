# DORA Evidence Collector for VMware vSphere 8

**Author:** LT  
**Version:** 1.0  

---

## License for This Repository
This repository’s own content (README, file list, structure) is licensed under the MIT License. See LICENSE for details.

---

Disclaimer

This script is provided "as is", without any warranty of any kind. Use it at your own risk. You are solely responsible for reviewing, testing, and implementing it in your own environment.

---

## Overview

This repository contains a **read-only PowerCLI script** (`dora-evidence.ps1`) that collects **technical evidence** to support compliance with the **EU Digital Operational Resilience Act (DORA)**.  

The script **does not change any settings** – it only queries configuration and operational data from vCenter, ESXi hosts, clusters, datastores, portgroups, and VMs.  
The output is presented in the **PowerCLI console**, and an optional export to CSV/JSON can be enabled.

At the end of execution, a **Compliance Summary** is shown.

---

## Compliance Summary Example

Example output after running the script:

=== Evidence (overview) ===
Timestamp Category Scope Ref Key Value Severity
2025-08-21T19:32:01 Inventory vCenter - vCenter Version 8.0.2 build 223555 Info
2025-08-21T19:32:03 Control esx01.lab 9.2 NTP configured & running Servers=[ntp1.local]; Running=True Pass
2025-08-21T19:32:03 Control esx01.lab 11.8 Persistent log dir [datastore1]/scratch/log Pass
2025-08-21T19:32:04 Control esx01.lab 9.4.c SSH disabled (stopped/not auto) Running=False; Policy=off Pass
2025-08-21T19:32:04 Control esx01.lab 9.4.c ESXi Shell disabled Running=False; Policy=off Pass
2025-08-21T19:32:05 Control esx01.lab 9.4.c Firewall enabled True Info
2025-08-21T19:32:05 Control esx01.lab 9.3.a SSH protocol is v2 2 Pass
2025-08-21T19:32:06 Control esx01.lab 9.3.b TPS settings Mem.ShareForceSalting=2; pshare.enable=0 Info
2025-08-21T19:32:06 Control esx01.lab 9.3.b ESX Admins AD group Not set Pass
2025-08-21T19:32:07 Control VM01 9.4.c CD/DVD connected Connected=True; Start=True; ISO=win.iso Warn

=== Evidence Summary (last 30 day(s)) ===
Total records : 142
Pass : 87
Info : 39
Warnings : 15
Fails : 1


---

## Features

- **Read-only auditor** (safe to run with auditor/readonly account).
- Collects evidence mapped to **DORA requirements**, including:
  - **ICT Risk Management**: Inventory, NTP, Syslog, Firewall, VIB acceptance, Core dump.
  - **ICT Incident & Logging**: Syslog targets, Events, Failed login attempts.
  - **Operational Resilience**: Cluster HA/DRS, Datastore capacity, Snapshots.
  - **Third-Party Risk**: vCenter Extensions, NetFlow collectors.
  - **Security Controls**: ESXi Shell/SSH, DCUI.Access, MOB disabled, TPS, vSwitch security, VM device connections.
- Displays results in a formatted table.
- Provides **Compliance Summary** at the end.
- Optional export to **CSV/JSON** for audit evidence.

---

## Requirements

- **VMware PowerCLI** module installed.  
- PowerShell 5.1+ or PowerShell 7.x.  
- Access to **vCenter Server** (and associated ESXi hosts) with at least **read-only permissions**.  

---

## Usage

1. Clone the repository or download the script:

   ```powershell
   git clone https://github.com/<your-org>/vsphere-dora-auditor.git
   cd vsphere-dora-auditor

2. Import PowerCLI if not already loaded:
   Import-Module VMware.PowerCLI

3. Run the script:
   .\dora-evidence.ps1 -VCenter vcenter.company.local

If you want to specify credentials explicitly:
$secPass = Read-Host "Enter Password" -AsSecureString
.\dora-evidence.ps1 -VCenter vcenter.company.local -Username "auditor@vsphere.local" -Password $secPass

4. The script will connect, run all evidence collection checks, print a detailed table of results, and finally show the Compliance Summary.
5. To export results to CSV and JSON:
   .\dora-evidence.ps1 -VCenter vcenter.company.local -Export -OutFolder .\evidence

---

Notes
* The script is non-intrusive – it does not modify any settings.
* Controls are annotated with DORA references (e.g., 9.2, 9.4.c, 11.8).
* Some controls (e.g., NetFlow collector authorization, password policies) must be validated manually.
* Output can be archived as audit evidence.
