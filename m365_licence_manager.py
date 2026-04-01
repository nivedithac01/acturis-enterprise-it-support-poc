"""
m365_licence_manager.py
-----------------------
Microsoft 365 licence allocation and audit tool.
Demonstrates M365 administration skills relevant to enterprise IT support
at an insurance SaaS company (Acturis).

Covers:
- Licence pool management (Exchange, Teams, SharePoint, etc.)
- User licence assignment and deallocation
- Audit reporting and over-allocation detection
- Licence utilisation dashboards
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set


# Available M365 licence plans
LICENCE_PLANS = {
    "M365_E3": ["Exchange", "Teams", "SharePoint", "OneDrive", "Intune"],
    "M365_E1": ["Exchange", "Teams", "SharePoint", "OneDrive"],
    "M365_F3": ["Exchange", "Teams", "SharePoint"],
    "EXCHANGE_ONLINE": ["Exchange"],
    "TEAMS_ESSENTIALS": ["Teams"],
}


@dataclass
class LicencePool:
    """Represents an M365 licence pool."""
    plan_name: str
    total_licences: int
    services: List[str]
    assigned_to: Set[str] = field(default_factory=set)

    @property
    def available(self) -> int:
        return self.total_licences - len(self.assigned_to)

    @property
    def utilisation_pct(self) -> float:
        if self.total_licences == 0:
            return 0.0
        return round(len(self.assigned_to) / self.total_licences * 100, 1)


@dataclass
class UserLicence:
    """Records which licences and services a user has."""
    username: str
    licences: List[str] = field(default_factory=list)
    services: Set[str] = field(default_factory=set)
    assigned_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

    def has_service(self, service: str) -> bool:
        return service in self.services


class M365LicenceManager:
    """
    Microsoft 365 licence management for enterprise IT support.

    Typical use cases:
    - New starter: assign M365_E3 on day one
    - Leaver: deallocate all licences on last day
    - Audit: identify users without Exchange, flag over-provisioning
    - Reporting: utilisation per plan, cost optimisation
    """

    def __init__(self) -> None:
        self._pools: Dict[str, LicencePool] = {}
        self._users: Dict[str, UserLicence] = {}
        self._audit_log: List[dict] = []

    # ------------------------------------------------------------------
    # Pool management
    # ------------------------------------------------------------------

    def add_licence_pool(self, plan_name: str, total_licences: int) -> LicencePool:
        """
        Add or update a licence pool.

        Args:
            plan_name: e.g. 'M365_E3'
            total_licences: Number of licences purchased

        Raises:
            ValueError: If plan_name is not recognised
        """
        if plan_name not in LICENCE_PLANS:
            raise ValueError(
                f"Unknown plan '{plan_name}'. Valid plans: {list(LICENCE_PLANS.keys())}"
            )
        services = LICENCE_PLANS[plan_name]
        existing = self._pools.get(plan_name)
        if existing:
            existing.total_licences = total_licences
            pool = existing
        else:
            pool = LicencePool(
                plan_name=plan_name,
                total_licences=total_licences,
                services=services,
            )
            self._pools[plan_name] = pool
        self._log("POOL_UPDATE", plan_name, f"Pool set to {total_licences} licences")
        return pool

    # ------------------------------------------------------------------
    # User licence operations
    # ------------------------------------------------------------------

    def assign_licence(self, username: str, plan_name: str) -> UserLicence:
        """
        Assign an M365 licence plan to a user.

        Args:
            username: AD username
            plan_name: Licence plan to assign (e.g. 'M365_E3')

        Raises:
            ValueError: If no licences available or plan unknown
            KeyError: If pool not configured
        """
        if plan_name not in LICENCE_PLANS:
            raise ValueError(f"Unknown plan '{plan_name}'.")
        if plan_name not in self._pools:
            raise KeyError(
                f"Licence pool '{plan_name}' not configured. Add it first with add_licence_pool()."
            )
        pool = self._pools[plan_name]
        if pool.available <= 0:
            raise ValueError(
                f"No available licences in pool '{plan_name}' "
                f"({len(pool.assigned_to)}/{pool.total_licences} assigned)."
            )
        if username in pool.assigned_to:
            raise ValueError(f"User '{username}' already has licence '{plan_name}'.")

        pool.assigned_to.add(username)

        if username not in self._users:
            self._users[username] = UserLicence(username=username)
        user_lic = self._users[username]
        if plan_name not in user_lic.licences:
            user_lic.licences.append(plan_name)
        for svc in LICENCE_PLANS[plan_name]:
            user_lic.services.add(svc)
        user_lic.last_modified = datetime.now()

        self._log("ASSIGN", username, f"Assigned {plan_name}; services: {LICENCE_PLANS[plan_name]}")
        return user_lic

    def deallocate_licence(self, username: str, plan_name: str) -> UserLicence:
        """
        Remove a specific licence plan from a user.

        Used during offboarding or licence downgrade.
        """
        if plan_name not in self._pools:
            raise KeyError(f"Licence pool '{plan_name}' not configured.")
        pool = self._pools[plan_name]
        if username not in pool.assigned_to:
            raise ValueError(f"User '{username}' does not have licence '{plan_name}'.")

        pool.assigned_to.discard(username)

        user_lic = self._users.get(username)
        if user_lic:
            if plan_name in user_lic.licences:
                user_lic.licences.remove(plan_name)
            # Rebuild services from remaining licences
            user_lic.services = set()
            for remaining_plan in user_lic.licences:
                for svc in LICENCE_PLANS.get(remaining_plan, []):
                    user_lic.services.add(svc)
            user_lic.last_modified = datetime.now()

        self._log("DEALLOCATE", username, f"Removed licence: {plan_name}")
        return user_lic or UserLicence(username=username)

    def offboard_user(self, username: str) -> List[str]:
        """
        Remove ALL M365 licences from a user (leaver offboarding).
        Returns list of licences that were removed.
        """
        removed = []
        for plan_name, pool in self._pools.items():
            if username in pool.assigned_to:
                pool.assigned_to.discard(username)
                removed.append(plan_name)

        if username in self._users:
            self._users[username].licences = []
            self._users[username].services = set()
            self._users[username].last_modified = datetime.now()

        self._log("OFFBOARD", username, f"All licences removed: {removed}")
        return removed

    # ------------------------------------------------------------------
    # Queries and reporting
    # ------------------------------------------------------------------

    def get_user_licences(self, username: str) -> Optional[UserLicence]:
        """Return licence details for a user, or None if not found."""
        return self._users.get(username)

    def users_without_service(self, service: str) -> List[str]:
        """
        Identify users who do NOT have a specific service.
        Useful for compliance checks (e.g. who doesn't have Exchange?).
        """
        return [
            u.username for u in self._users.values()
            if not u.has_service(service) and u.licences
        ]

    def pool_utilisation_report(self) -> List[dict]:
        """Return utilisation stats for all configured licence pools."""
        report = []
        for plan_name, pool in self._pools.items():
            report.append({
                "plan": plan_name,
                "total": pool.total_licences,
                "assigned": len(pool.assigned_to),
                "available": pool.available,
                "utilisation_pct": pool.utilisation_pct,
                "services_included": pool.services,
            })
        return report

    def full_audit_report(self) -> dict:
        """Generate a comprehensive M365 licence audit report."""
        total_assigned = sum(len(p.assigned_to) for p in self._pools.values())
        total_available = sum(p.available for p in self._pools.values())
        return {
            "generated_at": datetime.now().isoformat(),
            "total_users_with_licences": len(self._users),
            "total_licences_assigned": total_assigned,
            "total_licences_available": total_available,
            "pool_breakdown": self.pool_utilisation_report(),
            "audit_log_entries": len(self._audit_log),
        }

    def get_audit_log(self) -> List[dict]:
        return list(self._audit_log)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, action: str, subject: str, detail: str) -> None:
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "subject": subject,
            "detail": detail,
        })
