"""
Helpdesk Tracker
Simulates an ITSM help desk ticketing system with SLA tracking, knowledge base
search, and incident lifecycle management.
"""

from datetime import datetime, timedelta

# SLA resolution targets in hours per priority
SLA_TARGETS_HOURS = {
    "critical": 1,
    "high": 4,
    "medium": 8,
    "low": 24,
}

KNOWLEDGE_BASE = [
    {
        "id": "KB001",
        "title": "Password Reset Procedure",
        "keywords": ["password", "reset", "login", "locked", "account"],
        "solution": "Use the self-service portal at https://password.acturis.internal or contact IT support.",
    },
    {
        "id": "KB002",
        "title": "VPN Connection Troubleshooting",
        "keywords": ["vpn", "remote", "access", "connect", "tunnel"],
        "solution": "Ensure the GlobalProtect client is installed. Try disconnecting and reconnecting. Check firewall rules.",
    },
    {
        "id": "KB003",
        "title": "Printer Not Printing",
        "keywords": ["printer", "print", "printing", "offline", "queue"],
        "solution": "Check printer status, clear print queue, restart print spooler service via services.msc.",
    },
    {
        "id": "KB004",
        "title": "Laptop Imaging with MDT",
        "keywords": ["mdt", "image", "imaging", "deploy", "windows", "build"],
        "solution": "Boot from network (PXE), select MDT deployment share, choose image and task sequence.",
    },
    {
        "id": "KB005",
        "title": "Microsoft 365 Licence Assignment",
        "keywords": ["m365", "office", "licence", "license", "teams", "outlook"],
        "solution": "Assign via M365 Admin Centre > Users > Active Users > Licences and Apps.",
    },
]


class HelpdeskTracker:
    """ITSM helpdesk ticket tracker with SLA monitoring and knowledge base."""

    VALID_PRIORITIES = {"critical", "high", "medium", "low"}
    VALID_CATEGORIES = {
        "hardware", "software", "network", "account", "access",
        "email", "printer", "vpn", "other"
    }

    def __init__(self):
        self._tickets: dict = {}
        self._counter = 1

    def log_ticket(self, title: str, category: str, user: str, description: str, priority: str) -> dict:
        """
        Log a new helpdesk incident ticket.

        Raises:
            ValueError: If priority or category is invalid.
        """
        if priority.lower() not in self.VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{priority}'. Choose from {self.VALID_PRIORITIES}."
            )
        if category.lower() not in self.VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Choose from {self.VALID_CATEGORIES}."
            )

        ticket_id = f"INC{self._counter:04d}"
        self._counter += 1

        created_at = datetime.utcnow()
        sla_hours = SLA_TARGETS_HOURS[priority.lower()]
        sla_due = created_at + timedelta(hours=sla_hours)

        ticket = {
            "ticket_id": ticket_id,
            "title": title,
            "category": category.lower(),
            "user": user,
            "description": description,
            "priority": priority.lower(),
            "status": "open",
            "assigned_to": None,
            "resolution": None,
            "resolved_by": None,
            "created_at": created_at.isoformat(),
            "resolved_at": None,
            "sla_due": sla_due.isoformat(),
            "sla_breached": False,
        }
        self._tickets[ticket_id] = ticket
        return ticket

    def resolve_ticket(self, ticket_id: str, resolution: str, resolved_by: str) -> dict:
        """
        Mark a ticket as resolved with a resolution note.

        Raises:
            KeyError: If ticket not found.
            ValueError: If ticket is already resolved.
        """
        ticket = self._get_ticket(ticket_id)
        if ticket["status"] == "resolved":
            raise ValueError(f"Ticket '{ticket_id}' is already resolved.")

        resolved_at = datetime.utcnow()
        sla_due = datetime.fromisoformat(ticket["sla_due"])
        sla_breached = resolved_at > sla_due

        ticket["status"] = "resolved"
        ticket["resolution"] = resolution
        ticket["resolved_by"] = resolved_by
        ticket["resolved_at"] = resolved_at.isoformat()
        ticket["sla_breached"] = sla_breached
        return ticket

    def get_open_tickets(self) -> list:
        """Return all open (unresolved) tickets."""
        return [t for t in self._tickets.values() if t["status"] == "open"]

    def get_sla_report(self) -> dict:
        """Generate an SLA compliance report grouped by priority."""
        report: dict = {}

        for ticket in self._tickets.values():
            if ticket["status"] != "resolved":
                continue
            priority = ticket["priority"]
            if priority not in report:
                report[priority] = {"total": 0, "within_sla": 0, "breached": 0}

            report[priority]["total"] += 1
            if ticket["sla_breached"]:
                report[priority]["breached"] += 1
            else:
                report[priority]["within_sla"] += 1

        for priority, stats in report.items():
            if stats["total"] > 0:
                stats["compliance_pct"] = round(
                    (stats["within_sla"] / stats["total"]) * 100, 1
                )
            else:
                stats["compliance_pct"] = 0.0

        return report

    def search_kb(self, keyword: str) -> list:
        """Simulate a knowledge base search by keyword."""
        keyword_lower = keyword.lower()
        results = []
        for article in KNOWLEDGE_BASE:
            if (keyword_lower in article["title"].lower()
                    or any(keyword_lower in kw for kw in article["keywords"])):
                results.append(article)
        return results

    def _get_ticket(self, ticket_id: str) -> dict:
        if ticket_id not in self._tickets:
            raise KeyError(f"Ticket '{ticket_id}' not found.")
        return self._tickets[ticket_id]
