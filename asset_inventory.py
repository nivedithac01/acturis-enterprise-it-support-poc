"""
asset_inventory.py
------------------
Hardware asset lifecycle management for enterprise IT support.
Demonstrates asset tracking skills relevant to maintaining a laptop fleet
for an insurance SaaS company like Acturis (800+ global staff).

Covers:
- Asset registration (purchase -> stock -> deployed -> decommissioned)
- Assignment and reassignment between users
- Procurement tracking and budget reporting
- Lifecycle reporting and refresh cycle planning
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional


class AssetStatus(Enum):
    IN_STOCK = "In Stock"           # Received but not deployed
    DEPLOYED = "Deployed"           # Assigned to a user
    IN_REPAIR = "In Repair"         # Sent for repair
    DECOMMISSIONED = "Decommissioned"  # End of life
    DISPOSED = "Disposed"           # Physically destroyed/recycled


class AssetType(Enum):
    LAPTOP = "Laptop"
    DESKTOP = "Desktop"
    MONITOR = "Monitor"
    KEYBOARD = "Keyboard"
    MOUSE = "Mouse"
    HEADSET = "Headset"
    DOCKING_STATION = "Docking Station"
    MOBILE = "Mobile Phone"
    TABLET = "Tablet"
    OTHER = "Other"


@dataclass
class Asset:
    """Represents a hardware asset in the inventory."""
    asset_tag: str
    asset_type: AssetType
    make_model: str
    serial_number: str
    purchase_date: date
    purchase_cost: float
    status: AssetStatus = AssetStatus.IN_STOCK
    assigned_to: Optional[str] = None
    location: str = "London HQ"
    warranty_expiry: Optional[date] = None
    notes: str = ""
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def age_years(self) -> float:
        delta = date.today() - self.purchase_date
        return round(delta.days / 365.25, 1)

    @property
    def is_warranty_active(self) -> bool:
        if self.warranty_expiry is None:
            return False
        return date.today() <= self.warranty_expiry

    def to_dict(self) -> dict:
        return {
            "asset_tag": self.asset_tag,
            "asset_type": self.asset_type.value,
            "make_model": self.make_model,
            "serial_number": self.serial_number,
            "purchase_date": str(self.purchase_date),
            "purchase_cost": self.purchase_cost,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "location": self.location,
            "warranty_expiry": str(self.warranty_expiry) if self.warranty_expiry else None,
            "age_years": self.age_years,
            "warranty_active": self.is_warranty_active,
            "notes": self.notes,
            "last_updated": self.last_updated.isoformat(),
        }


class AssetInventory:
    """
    Hardware asset lifecycle manager for enterprise IT support.

    Mirrors the asset management workflows of an IT Support Engineer
    at an insurance SaaS organisation:
    - Receive new hardware from procurement
    - Deploy to new starters with MDT build
    - Reassign on internal transfers
    - Decommission and dispose at end-of-life
    - Report on fleet age, warranty status, refresh needs
    """

    # Recommended refresh cycle in years by asset type
    REFRESH_CYCLE_YEARS: Dict[AssetType, int] = {
        AssetType.LAPTOP: 4,
        AssetType.DESKTOP: 5,
        AssetType.MONITOR: 6,
        AssetType.MOBILE: 3,
        AssetType.TABLET: 3,
        AssetType.DOCKING_STATION: 5,
        AssetType.KEYBOARD: 5,
        AssetType.MOUSE: 5,
        AssetType.HEADSET: 4,
        AssetType.OTHER: 5,
    }

    def __init__(self) -> None:
        self._assets: Dict[str, Asset] = {}
        self._audit_log: List[dict] = []

    # ------------------------------------------------------------------
    # Asset registration
    # ------------------------------------------------------------------

    def add_asset(
        self,
        asset_tag: str,
        make_model: str,
        asset_type: str = "Laptop",
        serial_number: str = "",
        purchase_date: Optional[date] = None,
        purchase_cost: float = 0.0,
        location: str = "London HQ",
        warranty_expiry: Optional[date] = None,
    ) -> Asset:
        """
        Register a new hardware asset in the inventory.

        Args:
            asset_tag: Unique asset identifier (e.g. 'LAPTOP-001')
            make_model: Make and model string (e.g. 'Dell Latitude 5540')
            asset_type: AssetType enum value string
            serial_number: Manufacturer serial number
            purchase_date: Date of purchase (defaults to today)
            purchase_cost: Cost in GBP
            location: Physical location
            warranty_expiry: Warranty expiry date

        Raises:
            ValueError: If asset_tag already exists or asset_type invalid
        """
        if asset_tag in self._assets:
            raise ValueError(f"Asset '{asset_tag}' already exists in inventory.")
        try:
            a_type = AssetType(asset_type)
        except ValueError:
            valid = [t.value for t in AssetType]
            raise ValueError(f"Invalid asset_type '{asset_type}'. Must be one of: {valid}")

        if purchase_date is None:
            purchase_date = date.today()

        asset = Asset(
            asset_tag=asset_tag,
            asset_type=a_type,
            make_model=make_model,
            serial_number=serial_number,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            location=location,
            warranty_expiry=warranty_expiry,
        )
        self._assets[asset_tag] = asset
        self._log("ADD", asset_tag, f"Asset registered: {make_model} ({a_type.value})")
        return asset

    # ------------------------------------------------------------------
    # Assignment lifecycle
    # ------------------------------------------------------------------

    def deploy_asset(self, asset_tag: str, username: str, location: Optional[str] = None) -> Asset:
        """
        Deploy an asset to a user (e.g. new starter laptop handover).

        Args:
            asset_tag: Asset to deploy
            username: AD username of the recipient
            location: Override location if different from default

        Raises:
            ValueError: If asset is not in stock or already deployed
        """
        asset = self._get_asset(asset_tag)
        if asset.status == AssetStatus.DEPLOYED:
            raise ValueError(
                f"Asset '{asset_tag}' is already deployed to '{asset.assigned_to}'."
            )
        if asset.status not in (AssetStatus.IN_STOCK,):
            raise ValueError(
                f"Asset '{asset_tag}' has status '{asset.status.value}' and cannot be deployed."
            )
        asset.assigned_to = username
        asset.status = AssetStatus.DEPLOYED
        if location:
            asset.location = location
        asset.last_updated = datetime.now()
        self._log("DEPLOY", asset_tag, f"Deployed to user '{username}'")
        return asset

    def return_asset(self, asset_tag: str, reason: str = "User return") -> Asset:
        """
        Return an asset to stock (e.g. leaver hands back laptop).
        Asset goes back to In Stock for re-imaging and redeployment.
        """
        asset = self._get_asset(asset_tag)
        previous_user = asset.assigned_to
        asset.assigned_to = None
        asset.status = AssetStatus.IN_STOCK
        asset.last_updated = datetime.now()
        self._log("RETURN", asset_tag, f"Returned from '{previous_user}': {reason}")
        return asset

    def reassign_asset(self, asset_tag: str, new_user: str) -> Asset:
        """Reassign a deployed asset directly to a new user (internal transfer)."""
        asset = self._get_asset(asset_tag)
        if asset.status != AssetStatus.DEPLOYED:
            raise ValueError(f"Asset '{asset_tag}' is not currently deployed.")
        old_user = asset.assigned_to
        asset.assigned_to = new_user
        asset.last_updated = datetime.now()
        self._log("REASSIGN", asset_tag, f"Reassigned from '{old_user}' to '{new_user}'")
        return asset

    def send_for_repair(self, asset_tag: str, fault_description: str) -> Asset:
        """Mark an asset as sent for repair."""
        asset = self._get_asset(asset_tag)
        prev_status = asset.status.value
        asset.status = AssetStatus.IN_REPAIR
        asset.notes = f"Repair: {fault_description}"
        asset.last_updated = datetime.now()
        self._log("REPAIR", asset_tag, f"Sent for repair (was {prev_status}): {fault_description}")
        return asset

    def decommission_asset(self, asset_tag: str, reason: str) -> Asset:
        """
        Mark an asset as decommissioned (end of life).
        Asset is no longer deployable but is retained for records.
        """
        asset = self._get_asset(asset_tag)
        if asset.status == AssetStatus.DISPOSED:
            raise ValueError(f"Asset '{asset_tag}' is already disposed.")
        asset.assigned_to = None
        asset.status = AssetStatus.DECOMMISSIONED
        asset.notes = f"Decommissioned: {reason}"
        asset.last_updated = datetime.now()
        self._log("DECOMMISSION", asset_tag, f"Decommissioned: {reason}")
        return asset

    def dispose_asset(self, asset_tag: str, disposal_method: str = "Certified recycling") -> Asset:
        """
        Mark an asset as physically disposed.
        Only allowed on decommissioned assets (data destruction compliance).
        """
        asset = self._get_asset(asset_tag)
        if asset.status != AssetStatus.DECOMMISSIONED:
            raise ValueError(
                f"Asset '{asset_tag}' must be Decommissioned before disposal (current: {asset.status.value})."
            )
        asset.status = AssetStatus.DISPOSED
        asset.notes += f" | Disposal: {disposal_method} on {date.today()}"
        asset.last_updated = datetime.now()
        self._log("DISPOSE", asset_tag, f"Disposed via: {disposal_method}")
        return asset

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_asset(self, asset_tag: str) -> Asset:
        return self._get_asset(asset_tag)

    def get_user_assets(self, username: str) -> List[Asset]:
        """Return all assets currently assigned to a specific user."""
        return [a for a in self._assets.values() if a.assigned_to == username]

    def list_by_status(self, status: str) -> List[Asset]:
        """Return all assets with a given status."""
        status_enum = AssetStatus(status)
        return [a for a in self._assets.values() if a.status == status_enum]

    def list_assets_needing_refresh(self) -> List[Asset]:
        """
        Identify deployed assets that have exceeded their recommended refresh cycle.
        Used for fleet refresh planning and hardware procurement budgeting.
        """
        results = []
        for asset in self._assets.values():
            if asset.status == AssetStatus.DEPLOYED:
                max_age = self.REFRESH_CYCLE_YEARS.get(asset.asset_type, 5)
                if asset.age_years >= max_age:
                    results.append(asset)
        return results

    def list_expiring_warranties(self, within_days: int = 90) -> List[Asset]:
        """Return assets whose warranty expires within the specified number of days."""
        threshold = date.today()
        cutoff = date.fromordinal(threshold.toordinal() + within_days)
        results = []
        for asset in self._assets.values():
            if asset.warranty_expiry and threshold <= asset.warranty_expiry <= cutoff:
                results.append(asset)
        return results

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def fleet_summary_report(self) -> dict:
        """
        Generate a fleet summary report for management review.
        Equivalent to the kind of reporting done in Power BI or Excel.
        """
        all_assets = list(self._assets.values())
        by_status: Dict[str, int] = {}
        for a in all_assets:
            by_status[a.status.value] = by_status.get(a.status.value, 0) + 1

        by_type: Dict[str, int] = {}
        for a in all_assets:
            by_type[a.asset_type.value] = by_type.get(a.asset_type.value, 0) + 1

        deployed = [a for a in all_assets if a.status == AssetStatus.DEPLOYED]
        total_value = sum(a.purchase_cost for a in all_assets if a.status != AssetStatus.DISPOSED)

        refresh_needed = self.list_assets_needing_refresh()
        expiring_warranty = self.list_expiring_warranties(within_days=90)

        return {
            "generated_at": datetime.now().isoformat(),
            "total_assets": len(all_assets),
            "total_fleet_value_gbp": round(total_value, 2),
            "by_status": by_status,
            "by_type": by_type,
            "deployed_count": len(deployed),
            "assets_needing_refresh": len(refresh_needed),
            "warranties_expiring_90_days": len(expiring_warranty),
            "audit_log_entries": len(self._audit_log),
        }

    def get_audit_log(self) -> List[dict]:
        return list(self._audit_log)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_asset(self, asset_tag: str) -> Asset:
        if asset_tag not in self._assets:
            raise KeyError(f"Asset '{asset_tag}' not found in inventory.")
        return self._assets[asset_tag]

    def _log(self, action: str, asset_tag: str, detail: str) -> None:
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "asset_tag": asset_tag,
            "detail": detail,
        })
