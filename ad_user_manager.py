"""
Active Directory User Manager
Simulates AD user lifecycle operations including account creation, group membership,
Group Policy application, offboarding, and departmental auditing.
"""

from datetime import datetime
from typing import Optional


class ADUserManager:
    """Simulates Active Directory user account lifecycle management."""

    def __init__(self):
        self._accounts: dict[str, dict] = {}
        self._gpo_links: list[dict] = []

    def create_account(
        self,
        username: str,
        full_name: str,
        email: str,
        department: str,
        manager: str,
    ) -> dict:
        """
        Create a new AD user account.

        Args:
            username: sAMAccountName / login username (must be unique).
            full_name: Display name.
            email: Primary SMTP address.
            department: OU/department the user belongs to.
            manager: Manager's username.

        Returns:
            Newly created account record.

        Raises:
            ValueError: If username already exists.
        """
        if username in self._accounts:
            raise ValueError(f"Account '{username}' already exists.")

        account = {
            "username": username,
            "full_name": full_name,
            "email": email,
            "department": department,
            "manager": manager,
            "groups": [],
            "enabled": True,
            "disabled_at": None,
            "disable_reason": None,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._accounts[username] = account
        return account

    def add_to_groups(self, username: str, groups: list[str]) -> dict:
        """
        Add a user to one or more AD security/distribution groups.

        Args:
            username: Target user's sAMAccountName.
            groups: List of group names to add the user to.

        Returns:
            Updated account record.

        Raises:
            KeyError: If user not found.
            ValueError: If user account is disabled.
        """
        account = self._get_account(username)
        if not account["enabled"]:
            raise ValueError(f"Cannot add disabled account '{username}' to groups.")

        for group in groups:
            if group not in account["groups"]:
                account["groups"].append(group)
        return account

    def disable_account(self, username: str, reason: str) -> dict:
        """
        Disable a user account as part of the offboarding workflow.

        Args:
            username: Target user's sAMAccountName.
            reason: Reason for disabling (e.g. 'resigned', 'contract ended').

        Returns:
            Updated account record.

        Raises:
            KeyError: If user not found.
            ValueError: If account is already disabled.
        """
        account = self._get_account(username)
        if not account["enabled"]:
            raise ValueError(f"Account '{username}' is already disabled.")

        account["enabled"] = False
        account["disabled_at"] = datetime.utcnow().isoformat()
        account["disable_reason"] = reason
        # Remove all group memberships on offboarding
        account["groups"] = []
        return account

    def apply_group_policy(self, ou: str, policy_name: str) -> dict:
        """
        Simulate linking a Group Policy Object (GPO) to an Organisational Unit (OU).

        Args:
            ou: Target Organisational Unit distinguished name (e.g. 'OU=IT,DC=acturis,DC=com').
            policy_name: Name of the GPO to link (e.g. 'IT-Security-Baseline').

        Returns:
            GPO link record.
        """
        link = {
            "ou": ou,
            "policy_name": policy_name,
            "linked_at": datetime.utcnow().isoformat(),
            "enforced": True,
        }
        self._gpo_links.append(link)
        return link

    def audit_accounts(self, department: str) -> dict:
        """
        Generate an audit report for all accounts in a given department.

        Args:
            department: Department name to audit.

        Returns:
            Audit report with counts and account details.
        """
        dept_accounts = [
            acc for acc in self._accounts.values()
            if acc["department"].lower() == department.lower()
        ]
        enabled = [a for a in dept_accounts if a["enabled"]]
        disabled = [a for a in dept_accounts if not a["enabled"]]

        return {
            "department": department,
            "total_accounts": len(dept_accounts),
            "enabled_count": len(enabled),
            "disabled_count": len(disabled),
            "accounts": dept_accounts,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _get_account(self, username: str) -> dict:
        if username not in self._accounts:
            raise KeyError(f"User '{username}' not found in AD.")
        return self._accounts[username]
