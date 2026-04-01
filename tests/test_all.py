"""
Test suite for Acturis Enterprise IT Support Toolkit.
Covers fleet_manager, ad_user_manager, and helpdesk_tracker modules.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fleet_manager import LaptopFleetManager
from ad_user_manager import ADUserManager
from helpdesk_tracker import HelpdeskTracker


# ==============================================================================
# LaptopFleetManager Tests
# ==============================================================================

class TestLaptopFleetManager:

    def setup_method(self):
        self.fm = LaptopFleetManager()

    def test_add_device_creates_record(self):
        device = self.fm.add_device("LAPTOP-001", "Dell Latitude 5540", "SN123", "alice", "IT")
        assert device["asset_tag"] == "LAPTOP-001"
        assert device["status"] == "available"
        assert device["assigned_to"] == "alice"

    def test_add_duplicate_raises_value_error(self):
        self.fm.add_device("LAPTOP-001", "Dell Latitude 5540", "SN123", "alice", "IT")
        with pytest.raises(ValueError, match="already exists"):
            self.fm.add_device("LAPTOP-001", "HP EliteBook", "SN456", "bob", "HR")

    def test_deploy_image_mdt(self):
        self.fm.add_device("LAPTOP-002", "Dell Latitude 5540", "SN200", "bob", "Finance")
        device = self.fm.deploy_image("LAPTOP-002", "Win11-22H2-Corp-v3.1", "MDT")
        assert device["status"] == "deployed"
        assert device["deployment_method"] == "MDT"
        assert device["image_version"] == "Win11-22H2-Corp-v3.1"

    def test_deploy_invalid_method_raises(self):
        self.fm.add_device("LAPTOP-003", "Lenovo ThinkPad", "SN300", "carol", "Legal")
        with pytest.raises(ValueError, match="Invalid deployment method"):
            self.fm.deploy_image("LAPTOP-003", "Win11", "pxe")

    def test_retire_device(self):
        self.fm.add_device("LAPTOP-004", "Dell Latitude", "SN400", "dave", "Sales")
        device = self.fm.retire_device("LAPTOP-004", "end-of-life")
        assert device["status"] == "retired"
        assert device["retirement_reason"] == "end-of-life"
        assert device["assigned_to"] is None

    def test_retire_already_retired_raises(self):
        self.fm.add_device("LAPTOP-005", "HP", "SN500", "eve", "HR")
        self.fm.retire_device("LAPTOP-005", "hardware fault")
        with pytest.raises(ValueError, match="already retired"):
            self.fm.retire_device("LAPTOP-005", "duplicate")

    def test_get_fleet_status(self):
        self.fm.add_device("LAPTOP-010", "Dell", "SN010", "user1", "IT")
        self.fm.add_device("LAPTOP-011", "Dell", "SN011", "user2", "IT")
        self.fm.deploy_image("LAPTOP-010", "Win11", "MDT")
        status = self.fm.get_fleet_status()
        assert status["total"] == 2
        assert status["by_status"]["deployed"] == 1
        assert status["by_status"]["available"] == 1

    def test_find_device_by_username(self):
        self.fm.add_device("LAPTOP-020", "Dell", "SN020", "niveditha", "IT")
        results = self.fm.find_device("niveditha")
        assert len(results) == 1
        assert results[0]["asset_tag"] == "LAPTOP-020"

    def test_find_device_no_match_returns_empty(self):
        self.fm.add_device("LAPTOP-030", "Dell", "SN030", "frank", "IT")
        results = self.fm.find_device("zzznomatch")
        assert results == []


# ==============================================================================
# ADUserManager Tests
# ==============================================================================

class TestADUserManager:

    def setup_method(self):
        self.ad = ADUserManager()

    def test_create_account(self):
        account = self.ad.create_account("ncherukuri", "Niveditha Cherukuri",
                                          "niveditha@acturis.com", "IT", "jsmith")
        assert account["username"] == "ncherukuri"
        assert account["enabled"] is True
        assert account["groups"] == []

    def test_create_duplicate_raises(self):
        self.ad.create_account("ncherukuri", "Niveditha Cherukuri",
                                "niveditha@acturis.com", "IT", "jsmith")
        with pytest.raises(ValueError, match="already exists"):
            self.ad.create_account("ncherukuri", "N Cherukuri",
                                   "n2@acturis.com", "HR", "jsmith")

    def test_add_to_groups(self):
        self.ad.create_account("bsmith", "Bob Smith", "b@acturis.com", "IT", "jsmith")
        account = self.ad.add_to_groups("bsmith", ["IT Support Staff", "Domain Users"])
        assert "IT Support Staff" in account["groups"]
        assert "Domain Users" in account["groups"]

    def test_add_to_groups_no_duplicates(self):
        self.ad.create_account("cjones", "Carol Jones", "c@acturis.com", "Finance", "jsmith")
        self.ad.add_to_groups("cjones", ["Finance Users"])
        account = self.ad.add_to_groups("cjones", ["Finance Users"])
        assert account["groups"].count("Finance Users") == 1

    def test_disable_account(self):
        self.ad.create_account("dwhite", "Dave White", "d@acturis.com", "Sales", "jsmith")
        self.ad.add_to_groups("dwhite", ["Sales Team"])
        account = self.ad.disable_account("dwhite", "resigned")
        assert account["enabled"] is False
        assert account["groups"] == []
        assert account["disable_reason"] == "resigned"

    def test_disable_already_disabled_raises(self):
        self.ad.create_account("eblack", "Eve Black", "e@acturis.com", "HR", "jsmith")
        self.ad.disable_account("eblack", "contract ended")
        with pytest.raises(ValueError, match="already disabled"):
            self.ad.disable_account("eblack", "duplicate")

    def test_apply_group_policy(self):
        link = self.ad.apply_group_policy("OU=IT,DC=acturis,DC=com", "IT-Security-Baseline")
        assert link["ou"] == "OU=IT,DC=acturis,DC=com"
        assert link["policy_name"] == "IT-Security-Baseline"
        assert link["enforced"] is True

    def test_audit_accounts(self):
        self.ad.create_account("u1", "User One", "u1@acturis.com", "IT", "mgr")
        self.ad.create_account("u2", "User Two", "u2@acturis.com", "IT", "mgr")
        self.ad.create_account("u3", "User Three", "u3@acturis.com", "HR", "mgr")
        self.ad.disable_account("u2", "left")
        report = self.ad.audit_accounts("IT")
        assert report["total_accounts"] == 2
        assert report["enabled_count"] == 1
        assert report["disabled_count"] == 1


# ==============================================================================
# HelpdeskTracker Tests
# ==============================================================================

class TestHelpdeskTracker:

    def setup_method(self):
        self.ht = HelpdeskTracker()

    def test_log_ticket(self):
        ticket = self.ht.log_ticket(
            "Laptop won't boot", "hardware", "alice", "Screen blank on power-on", "high"
        )
        assert ticket["ticket_id"] == "INC0001"
        assert ticket["status"] == "open"
        assert ticket["priority"] == "high"
        assert ticket["sla_due"] is not None

    def test_log_ticket_invalid_priority(self):
        with pytest.raises(ValueError, match="Invalid priority"):
            self.ht.log_ticket("Test", "hardware", "bob", "desc", "urgent")

    def test_log_ticket_invalid_category(self):
        with pytest.raises(ValueError, match="Invalid category"):
            self.ht.log_ticket("Test", "cafeteria", "bob", "desc", "low")

    def test_resolve_ticket(self):
        ticket = self.ht.log_ticket("VPN down", "vpn", "carol", "Cannot connect", "high")
        resolved = self.ht.resolve_ticket(ticket["ticket_id"], "Reinstalled GlobalProtect", "ncherukuri")
        assert resolved["status"] == "resolved"
        assert resolved["resolved_by"] == "ncherukuri"
        assert resolved["resolution"] == "Reinstalled GlobalProtect"

    def test_resolve_already_resolved_raises(self):
        ticket = self.ht.log_ticket("Printer offline", "printer", "dave", "Cannot print", "medium")
        self.ht.resolve_ticket(ticket["ticket_id"], "Restarted spooler", "ncherukuri")
        with pytest.raises(ValueError, match="already resolved"):
            self.ht.resolve_ticket(ticket["ticket_id"], "duplicate", "ncherukuri")

    def test_get_open_tickets(self):
        self.ht.log_ticket("Issue A", "software", "u1", "desc", "low")
        t2 = self.ht.log_ticket("Issue B", "network", "u2", "desc", "medium")
        self.ht.resolve_ticket(t2["ticket_id"], "fixed", "eng1")
        open_tickets = self.ht.get_open_tickets()
        assert len(open_tickets) == 1
        assert open_tickets[0]["title"] == "Issue A"

    def test_get_sla_report(self):
        t1 = self.ht.log_ticket("Critical Issue", "hardware", "u1", "desc", "critical")
        self.ht.resolve_ticket(t1["ticket_id"], "resolved fast", "eng1")
        report = self.ht.get_sla_report()
        assert "critical" in report
        assert report["critical"]["total"] == 1

    def test_search_kb_by_keyword(self):
        results = self.ht.search_kb("password")
        assert any("KB001" == r["id"] for r in results)

    def test_search_kb_vpn(self):
        results = self.ht.search_kb("vpn")
        assert any("KB002" == r["id"] for r in results)

    def test_search_kb_no_match(self):
        results = self.ht.search_kb("zzznomatch")
        assert results == []

    def test_ticket_id_increments(self):
        t1 = self.ht.log_ticket("T1", "other", "u1", "d", "low")
        t2 = self.ht.log_ticket("T2", "other", "u2", "d", "low")
        assert t1["ticket_id"] == "INC0001"
        assert t2["ticket_id"] == "INC0002"
