"""Tests for asset_inventory.py — Hardware asset lifecycle management."""

import pytest
import sys
import os
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asset_inventory import AssetInventory, AssetStatus, AssetType


class TestAssetInventory:

    def setup_method(self):
        self.inv = AssetInventory()

    def test_add_asset_basic(self):
        asset = self.inv.add_asset("LAPTOP-001", "Dell Latitude 5540")
        assert asset.asset_tag == "LAPTOP-001"
        assert asset.make_model == "Dell Latitude 5540"
        assert asset.status == AssetStatus.IN_STOCK

    def test_add_asset_default_type_is_laptop(self):
        asset = self.inv.add_asset("LAPTOP-002", "HP EliteBook 840")
        assert asset.asset_type == AssetType.LAPTOP

    def test_add_asset_duplicate_raises(self):
        self.inv.add_asset("LAPTOP-003", "Lenovo ThinkPad")
        with pytest.raises(ValueError, match="already exists"):
            self.inv.add_asset("LAPTOP-003", "Another Laptop")

    def test_add_asset_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid asset_type"):
            self.inv.add_asset("X001", "Unknown Device", asset_type="Mainframe")

    def test_deploy_asset(self):
        self.inv.add_asset("LAPTOP-010", "Dell Latitude 5540")
        asset = self.inv.deploy_asset("LAPTOP-010", "alice.jones")
        assert asset.status == AssetStatus.DEPLOYED
        assert asset.assigned_to == "alice.jones"

    def test_deploy_already_deployed_raises(self):
        self.inv.add_asset("LAPTOP-011", "HP EliteBook")
        self.inv.deploy_asset("LAPTOP-011", "bob.smith")
        with pytest.raises(ValueError, match="already deployed"):
            self.inv.deploy_asset("LAPTOP-011", "carol.white")

    def test_return_asset(self):
        self.inv.add_asset("LAPTOP-020", "Dell Latitude")
        self.inv.deploy_asset("LAPTOP-020", "dave.jones")
        asset = self.inv.return_asset("LAPTOP-020")
        assert asset.status == AssetStatus.IN_STOCK
        assert asset.assigned_to is None

    def test_reassign_asset(self):
        self.inv.add_asset("LAPTOP-030", "Lenovo X1 Carbon")
        self.inv.deploy_asset("LAPTOP-030", "user.one")
        asset = self.inv.reassign_asset("LAPTOP-030", "user.two")
        assert asset.assigned_to == "user.two"
        assert asset.status == AssetStatus.DEPLOYED

    def test_send_for_repair(self):
        self.inv.add_asset("LAPTOP-040", "Dell Precision")
        self.inv.deploy_asset("LAPTOP-040", "eve.black")
        self.inv.return_asset("LAPTOP-040")
        asset = self.inv.send_for_repair("LAPTOP-040", "Screen cracked")
        assert asset.status == AssetStatus.IN_REPAIR

    def test_decommission_asset(self):
        self.inv.add_asset("LAPTOP-050", "Old Dell", purchase_date=date(2018, 1, 1))
        asset = self.inv.decommission_asset("LAPTOP-050", "End of 5-year lifecycle")
        assert asset.status == AssetStatus.DECOMMISSIONED

    def test_dispose_asset_requires_decommission(self):
        self.inv.add_asset("LAPTOP-060", "Active Laptop")
        with pytest.raises(ValueError, match="must be Decommissioned"):
            self.inv.dispose_asset("LAPTOP-060")

    def test_dispose_asset_after_decommission(self):
        self.inv.add_asset("LAPTOP-070", "Old Laptop", purchase_date=date(2018, 6, 1))
        self.inv.decommission_asset("LAPTOP-070", "Lifecycle complete")
        asset = self.inv.dispose_asset("LAPTOP-070", "Certified recycling")
        assert asset.status == AssetStatus.DISPOSED

    def test_get_user_assets(self):
        self.inv.add_asset("L-001", "Dell Latitude", asset_type="Laptop")
        self.inv.add_asset("M-001", "Dell Monitor", asset_type="Monitor")
        self.inv.deploy_asset("L-001", "frank.jones")
        self.inv.deploy_asset("M-001", "frank.jones")
        assets = self.inv.get_user_assets("frank.jones")
        tags = [a.asset_tag for a in assets]
        assert "L-001" in tags
        assert "M-001" in tags

    def test_list_by_status(self):
        self.inv.add_asset("S-001", "Stock Laptop")
        self.inv.add_asset("D-001", "Deployed Laptop")
        self.inv.deploy_asset("D-001", "grace.hill")
        in_stock = self.inv.list_by_status("In Stock")
        assert any(a.asset_tag == "S-001" for a in in_stock)
        assert all(a.asset_tag != "D-001" for a in in_stock)

    def test_fleet_summary_report(self):
        self.inv.add_asset("FR-001", "Dell Latitude", purchase_cost=1200.0)
        self.inv.add_asset("FR-002", "HP EliteBook", purchase_cost=1100.0)
        report = self.inv.fleet_summary_report()
        assert report["total_assets"] == 2
        assert report["total_fleet_value_gbp"] == 2300.0

    def test_get_asset_not_found_raises(self):
        with pytest.raises(KeyError):
            self.inv.get_asset("NONEXISTENT-999")

    def test_assets_needing_refresh_old_laptop(self):
        old_date = date.today() - timedelta(days=365 * 5)  # 5 years old
        self.inv.add_asset("OLD-001", "Aging Laptop", purchase_date=old_date)
        self.inv.deploy_asset("OLD-001", "henry.brown")
        refresh_list = self.inv.list_assets_needing_refresh()
        assert any(a.asset_tag == "OLD-001" for a in refresh_list)

    def test_expiring_warranties(self):
        expiry = date.today() + timedelta(days=30)
        self.inv.add_asset("W-001", "Warranty Laptop", warranty_expiry=expiry)
        expiring = self.inv.list_expiring_warranties(within_days=90)
        assert any(a.asset_tag == "W-001" for a in expiring)

    def test_audit_log_populated(self):
        self.inv.add_asset("LOG-001", "Log Test Laptop")
        log = self.inv.get_audit_log()
        assert len(log) >= 1
        assert log[0]["action"] == "ADD"
