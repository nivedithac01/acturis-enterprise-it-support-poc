# Acturis Enterprise IT Support Toolkit

A Python toolkit demonstrating enterprise IT support fundamentals aligned with the Graduate Enterprise IT Support Engineer role at Acturis.

## Overview

This project simulates three core IT support workflows:

1. **Laptop Fleet Management** (`fleet_manager.py`) — MDT-style deployment tracking, asset lifecycle, fleet status reporting
2. **Active Directory User Lifecycle** (`ad_user_manager.py`) — account provisioning, group membership, Group Policy simulation, offboarding, departmental auditing
3. **Helpdesk Ticketing with SLA** (`helpdesk_tracker.py`) — incident logging, ticket resolution, SLA compliance reporting, knowledge base search

## Relevance to Acturis

Acturis provides insurance SaaS software to 800+ global staff. This toolkit directly demonstrates the core IT support skills required:

- MDT-based Windows laptop fleet build and maintenance
- Active Directory user provisioning and onboarding workflows
- First-line ITSM ticketing with SLA management
- Python scripting applied to IT operations automation

## Project Structure

```
acturis-enterprise-it-support-poc/
├── fleet_manager.py        # Laptop fleet management with MDT deployment simulation
├── ad_user_manager.py      # Active Directory user lifecycle management
├── helpdesk_tracker.py     # ITSM helpdesk ticketing with SLA reporting
├── tests/
│   └── test_all.py         # Pytest test suite (25+ tests)
├── requirements.txt
├── .gitignore
└── README.md
```

## Quick Start

```bash
pip install pytest
python -m pytest tests/ -v
```

## Example Usage

```python
from fleet_manager import LaptopFleetManager
from ad_user_manager import ADUserManager
from helpdesk_tracker import HelpdeskTracker

# Fleet management
fm = LaptopFleetManager()
fm.add_device("LAPTOP-001", "Dell Latitude 5540", "SN12345", "ncherukuri", "IT")
fm.deploy_image("LAPTOP-001", "Win11-22H2-Corp-v3.1", "MDT")
print(fm.get_fleet_status())

# Active Directory
ad = ADUserManager()
ad.create_account("ncherukuri", "Niveditha Cherukuri", "n@acturis.com", "IT", "jsmith")
ad.add_to_groups("ncherukuri", ["IT Support Staff", "Domain Users"])
ad.apply_group_policy("OU=IT,DC=acturis,DC=com", "IT-Security-Baseline")

# Helpdesk ticketing
ht = HelpdeskTracker()
ticket = ht.log_ticket("VPN not connecting", "vpn", "bsmith", "GlobalProtect error", "high")
ht.resolve_ticket(ticket["ticket_id"], "Reinstalled client and reconfigured profile", "ncherukuri")
print(ht.get_sla_report())
```

## Author

Niveditha Cherukuri — [GitHub](https://github.com/nivedithac01) | [LinkedIn](https://www.linkedin.com/in/niveditha-cherukuri-8440033b5)
