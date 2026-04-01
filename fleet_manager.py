"""
Laptop Fleet Manager
Simulates enterprise laptop fleet management including MDT-style deployment,
asset lifecycle tracking, and fleet status reporting.
"""

from datetime import datetime
from typing import Optional


class LaptopFleetManager:
    """Manages an enterprise laptop fleet including deployment, tracking, and retirement."""

    VALID_STATUSES = {"available", "deployed", "imaging", "repair", "retired"}
    VALID_METHODS = {"MDT", "manual", "autopilot"}

    def __init__(self):
        self._fleet: dict[str, dict] = {}

    def add_device(
        self,
        asset_tag: str,
        model: str,
        serial: str,
        assigned_to: str,
        department: str,
    ) -> dict:
        """
        Add a new device to the fleet inventory.

        Args:
            asset_tag: Unique asset identifier (e.g. 'LAPTOP-001')
            model: Hardware model (e.g. 'Dell Latitude 5540')
            serial: Serial number
            assigned_to: Username or employee name
            department: Business department

        Returns:
            The newly created device record.

        Raises:
            ValueError: If asset_tag already exists.
        """
        if asset_tag in self._fleet:
            raise ValueError(f"Asset tag '{asset_tag}' already exists in fleet.")

        device = {
            "asset_tag": asset_tag,
            "model": model,
            "serial": serial,
            "assigned_to": assigned_to,
            "department": department,
            "status": "available",
            "deployment_method": None,
            "image_version": None,
            "deployed_at": None,
            "retired_at": None,
            "retirement_reason": None,
            "added_at": datetime.utcnow().isoformat(),
        }
        self._fleet[asset_tag] = device
        return device

    def deploy_image(
        self,
        asset_tag: str,
        image_version: str,
        method: str,
    ) -> dict:
        """
        Record an OS image deployment on a device.

        Args:
            asset_tag: Target device asset tag.
            image_version: Image version string (e.g. 'Win11-22H2-Corp-v3.1').
            method: Deployment method — one of 'MDT', 'manual', 'autopilot'.

        Returns:
            Updated device record.

        Raises:
            KeyError: If asset_tag not found.
            ValueError: If method is invalid or device is retired.
        """
        device = self._get_device(asset_tag)
        if device["status"] == "retired":
            raise ValueError(f"Cannot deploy image to retired device '{asset_tag}'.")
        if method not in self.VALID_METHODS:
            raise ValueError(
                f"Invalid deployment method '{method}'. Choose from {self.VALID_METHODS}."
            )

        device["status"] = "deployed"
        device["image_version"] = image_version
        device["deployment_method"] = method
        device["deployed_at"] = datetime.utcnow().isoformat()
        return device

    def get_fleet_status(self) -> dict:
        """
        Return aggregated fleet counts by status, department, and deployment method.

        Returns:
            Dict with keys 'total', 'by_status', 'by_department', 'by_deployment_method'.
        """
        by_status: dict[str, int] = {}
        by_department: dict[str, int] = {}
        by_method: dict[str, int] = {}

        for device in self._fleet.values():
            status = device["status"]
            dept = device["department"]
            method = device["deployment_method"] or "undeployed"

            by_status[status] = by_status.get(status, 0) + 1
            by_department[dept] = by_department.get(dept, 0) + 1
            by_method[method] = by_method.get(method, 0) + 1

        return {
            "total": len(self._fleet),
            "by_status": by_status,
            "by_department": by_department,
            "by_deployment_method": by_method,
        }

    def retire_device(self, asset_tag: str, reason: str) -> dict:
        """
        Decommission a device from active fleet use.

        Args:
            asset_tag: Target device asset tag.
            reason: Reason for retirement (e.g. 'end-of-life', 'hardware fault').

        Returns:
            Updated device record.

        Raises:
            KeyError: If asset_tag not found.
            ValueError: If device is already retired.
        """
        device = self._get_device(asset_tag)
        if device["status"] == "retired":
            raise ValueError(f"Device '{asset_tag}' is already retired.")

        device["status"] = "retired"
        device["retirement_reason"] = reason
        device["retired_at"] = datetime.utcnow().isoformat()
        device["assigned_to"] = None
        return device

    def find_device(self, query: str) -> list[dict]:
        """
        Search fleet by username or asset tag (case-insensitive partial match).

        Args:
            query: Search string matched against asset_tag and assigned_to fields.

        Returns:
            List of matching device records.
        """
        query_lower = query.lower()
        results = []
        for device in self._fleet.values():
            assigned = (device["assigned_to"] or "").lower()
            if query_lower in device["asset_tag"].lower() or query_lower in assigned:
                results.append(device)
        return results

    def _get_device(self, asset_tag: str) -> dict:
        if asset_tag not in self._fleet:
            raise KeyError(f"Device '{asset_tag}' not found in fleet.")
        return self._fleet[asset_tag]
