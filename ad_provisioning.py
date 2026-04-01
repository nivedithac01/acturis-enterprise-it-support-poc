"""
ad_provisioning.py
------------------
Active Directory user provisioning simulator for enterprise IT support.
Demonstrates Windows AD account lifecycle management:
- Create, update, deactivate, delete user accounts
- Assign users to groups (role-based access)
- Audit and report on account status
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional


@dataclass
class ADUser:
    """Represents an Active Directory user account."""
    username: str
    display_name: str
    job_title: str
    department: str
    email: str
    enabled: bool = True
    groups: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    password_last_set: Optional[date] = None

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "display_name": self.display_name,
            "job_title": self.job_title,
            "department": self.department,
            "email": self.email,
            "enabled": self.enabled,
            "groups": self.groups,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "password_last_set": str(self.password_last_set) if self.password_last_set else None,
        }


class ADProvisioner:
    """
    Simulates Active Directory provisioning operations for enterprise IT support.

    Covers:
    - New starter onboarding (create user, assign groups)
    - Leaver offboarding (disable, remove groups)
    - Account updates (title changes, department moves)
    - Audit reporting (disabled accounts, group membership)
    """

    # Default department-to-group mappings (mirrors typical enterprise AD structure)
    DEPARTMENT_GROUPS: Dict[str, List[str]] = {
        "IT": ["IT-Staff", "VPN-Access", "Admin-Tools"],
        "Finance": ["Finance-Staff", "Finance-Shared-Drive"],
        "HR": ["HR-Staff", "HR-Confidential"],
        "Engineering": ["Engineering-Staff", "Dev-Tools", "VPN-Access"],
        "Sales": ["Sales-Staff", "CRM-Access"],
        "Operations": ["Operations-Staff", "Operations-Shared"],
    }

    def __init__(self) -> None:
        self._users: Dict[str, ADUser] = {}
        self._audit_log: List[dict] = []

    # ------------------------------------------------------------------
    # User lifecycle
    # ------------------------------------------------------------------

    def create_user(
        self,
        username: str,
        display_name: str,
        job_title: str,
        department: str,
        email: Optional[str] = None,
        additional_groups: Optional[List[str]] = None,
    ) -> ADUser:
        """
        Provision a new AD user account.

        Args:
            username: SAMAccountName (e.g. 'john.smith')
            display_name: Full name (e.g. 'John Smith')
            job_title: Job title (e.g. 'IT Support Engineer')
            department: Department name — used to auto-assign default groups
            email: Optional email override; defaults to username@company.local
            additional_groups: Extra groups beyond department defaults

        Returns:
            ADUser instance

        Raises:
            ValueError: If username already exists
        """
        if username in self._users:
            raise ValueError(f"User '{username}' already exists in Active Directory.")

        if email is None:
            email = f"{username}@company.local"

        groups = list(self.DEPARTMENT_GROUPS.get(department, []))
        if additional_groups:
            for g in additional_groups:
                if g not in groups:
                    groups.append(g)

        user = ADUser(
            username=username,
            display_name=display_name,
            job_title=job_title,
            department=department,
            email=email,
            enabled=True,
            groups=groups,
            password_last_set=date.today(),
        )
        self._users[username] = user
        self._log_action("CREATE", username, f"Account created for {display_name} in {department}")
        return user

    def deactivate_user(self, username: str) -> ADUser:
        """
        Disable a user account (leaver offboarding step 1).
        Removes all group memberships.

        Raises:
            KeyError: If user not found
        """
        user = self._get_user(username)
        if not user.enabled:
            raise ValueError(f"User '{username}' is already disabled.")
        removed_groups = list(user.groups)
        user.groups = []
        user.enabled = False
        user.last_modified = datetime.now()
        self._log_action(
            "DEACTIVATE", username,
            f"Account disabled; removed from groups: {removed_groups}"
        )
        return user

    def reactivate_user(self, username: str, department: Optional[str] = None) -> ADUser:
        """Re-enable a disabled user account (e.g. return from leave)."""
        user = self._get_user(username)
        if user.enabled:
            raise ValueError(f"User '{username}' is already active.")
        if department:
            user.department = department
        user.groups = list(self.DEPARTMENT_GROUPS.get(user.department, []))
        user.enabled = True
        user.last_modified = datetime.now()
        user.password_last_set = date.today()
        self._log_action("REACTIVATE", username, "Account re-enabled and groups restored")
        return user

    def delete_user(self, username: str) -> None:
        """
        Permanently delete a user account (irreversible).
        Only allowed on already-disabled accounts.
        """
        user = self._get_user(username)
        if user.enabled:
            raise ValueError(
                f"Cannot delete active user '{username}'. Deactivate first."
            )
        del self._users[username]
        self._log_action("DELETE", username, "Account permanently deleted")

    # ------------------------------------------------------------------
    # Account updates
    # ------------------------------------------------------------------

    def update_job_title(self, username: str, new_title: str) -> ADUser:
        """Update a user's job title (e.g. after promotion)."""
        user = self._get_user(username)
        old_title = user.job_title
        user.job_title = new_title
        user.last_modified = datetime.now()
        self._log_action("UPDATE", username, f"Job title changed: '{old_title}' -> '{new_title}'")
        return user

    def transfer_department(self, username: str, new_department: str) -> ADUser:
        """
        Move a user to a new department.
        Updates group memberships to reflect new department defaults.
        """
        user = self._get_user(username)
        old_dept = user.department
        old_groups = list(user.groups)
        user.department = new_department
        user.groups = list(self.DEPARTMENT_GROUPS.get(new_department, []))
        user.last_modified = datetime.now()
        self._log_action(
            "TRANSFER", username,
            f"Dept: '{old_dept}' -> '{new_department}'; groups updated from {old_groups} to {user.groups}"
        )
        return user

    def add_to_group(self, username: str, group_name: str) -> ADUser:
        """Add a user to an AD security group."""
        user = self._get_user(username)
        if group_name in user.groups:
            raise ValueError(f"User '{username}' is already in group '{group_name}'.")
        user.groups.append(group_name)
        user.last_modified = datetime.now()
        self._log_action("GROUP_ADD", username, f"Added to group: {group_name}")
        return user

    def remove_from_group(self, username: str, group_name: str) -> ADUser:
        """Remove a user from an AD security group."""
        user = self._get_user(username)
        if group_name not in user.groups:
            raise ValueError(f"User '{username}' is not in group '{group_name}'.")
        user.groups.remove(group_name)
        user.last_modified = datetime.now()
        self._log_action("GROUP_REMOVE", username, f"Removed from group: {group_name}")
        return user

    def reset_password(self, username: str) -> str:
        """
        Simulate a password reset. Returns a placeholder temporary password.
        In production this would call Set-ADAccountPassword via PowerShell.
        """
        user = self._get_user(username)
        temp_hash = hashlib.sha256(f"{username}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        temp_password = f"Tmp!{temp_hash[:8]}"
        user.password_last_set = date.today()
        user.last_modified = datetime.now()
        self._log_action("PASSWORD_RESET", username, "Password reset performed")
        return temp_password

    # ------------------------------------------------------------------
    # Queries and reporting
    # ------------------------------------------------------------------

    def get_user(self, username: str) -> ADUser:
        """Retrieve a user by username."""
        return self._get_user(username)

    def list_all_users(self, enabled_only: bool = False) -> List[ADUser]:
        """Return all users, optionally filtered to enabled accounts only."""
        users = list(self._users.values())
        if enabled_only:
            users = [u for u in users if u.enabled]
        return users

    def list_users_in_group(self, group_name: str) -> List[ADUser]:
        """Return all users who are members of a given group."""
        return [u for u in self._users.values() if group_name in u.groups]

    def list_disabled_accounts(self) -> List[ADUser]:
        """Return all disabled user accounts (useful for cleanup audit)."""
        return [u for u in self._users.values() if not u.enabled]

    def audit_report(self) -> dict:
        """Generate a summary audit report."""
        all_users = list(self._users.values())
        enabled = [u for u in all_users if u.enabled]
        disabled = [u for u in all_users if not u.enabled]
        dept_counts: Dict[str, int] = {}
        for u in enabled:
            dept_counts[u.department] = dept_counts.get(u.department, 0) + 1
        return {
            "total_accounts": len(all_users),
            "enabled_accounts": len(enabled),
            "disabled_accounts": len(disabled),
            "accounts_by_department": dept_counts,
            "audit_log_entries": len(self._audit_log),
            "generated_at": datetime.now().isoformat(),
        }

    def get_audit_log(self) -> List[dict]:
        """Return the full audit log."""
        return list(self._audit_log)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_user(self, username: str) -> ADUser:
        if username not in self._users:
            raise KeyError(f"User '{username}' not found in Active Directory.")
        return self._users[username]

    def _log_action(self, action: str, username: str, detail: str) -> None:
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "username": username,
            "detail": detail,
        })
