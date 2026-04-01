"""Tests for m365_licence_manager.py — Microsoft 365 licence management."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m365_licence_manager import M365LicenceManager


class TestM365LicenceManager:

    def setup_method(self):
        self.mgr = M365LicenceManager()
        self.mgr.add_licence_pool("M365_E3", total_licences=50)

    def test_add_licence_pool(self):
        pool_report = self.mgr.pool_utilisation_report()
        assert any(p["plan"] == "M365_E3" for p in pool_report)

    def test_assign_licence(self):
        user_lic = self.mgr.assign_licence("alice.jones", "M365_E3")
        assert "M365_E3" in user_lic.licences
        assert "Exchange" in user_lic.services
        assert "Teams" in user_lic.services

    def test_assign_reduces_available(self):
        self.mgr.assign_licence("bob.smith", "M365_E3")
        report = self.mgr.pool_utilisation_report()
        e3 = next(p for p in report if p["plan"] == "M365_E3")
        assert e3["assigned"] == 1
        assert e3["available"] == 49

    def test_assign_duplicate_raises(self):
        self.mgr.assign_licence("carol.white", "M365_E3")
        with pytest.raises(ValueError, match="already has licence"):
            self.mgr.assign_licence("carol.white", "M365_E3")

    def test_assign_unknown_plan_raises(self):
        with pytest.raises(ValueError, match="Unknown plan"):
            self.mgr.assign_licence("dave.green", "M365_FAKE")

    def test_assign_unconfigured_pool_raises(self):
        with pytest.raises(KeyError):
            self.mgr.assign_licence("eve.black", "M365_F3")

    def test_deallocate_licence(self):
        self.mgr.assign_licence("frank.jones", "M365_E3")
        user_lic = self.mgr.deallocate_licence("frank.jones", "M365_E3")
        assert "M365_E3" not in user_lic.licences

    def test_offboard_user_removes_all_licences(self):
        self.mgr.add_licence_pool("M365_E1", total_licences=20)
        self.mgr.assign_licence("grace.hill", "M365_E3")
        self.mgr.assign_licence("grace.hill", "M365_E1")
        removed = self.mgr.offboard_user("grace.hill")
        assert "M365_E3" in removed
        assert "M365_E1" in removed
        user_lic = self.mgr.get_user_licences("grace.hill")
        assert user_lic.licences == []

    def test_pool_exhaustion_raises(self):
        small_mgr = M365LicenceManager()
        small_mgr.add_licence_pool("M365_E3", total_licences=1)
        small_mgr.assign_licence("user1", "M365_E3")
        with pytest.raises(ValueError, match="No available licences"):
            small_mgr.assign_licence("user2", "M365_E3")

    def test_users_without_service(self):
        self.mgr.add_licence_pool("TEAMS_ESSENTIALS", total_licences=10)
        self.mgr.assign_licence("teams.only", "TEAMS_ESSENTIALS")
        no_exchange = self.mgr.users_without_service("Exchange")
        assert "teams.only" in no_exchange

    def test_full_audit_report_structure(self):
        self.mgr.assign_licence("report.user", "M365_E3")
        report = self.mgr.full_audit_report()
        assert "total_users_with_licences" in report
        assert "pool_breakdown" in report
        assert report["total_users_with_licences"] == 1
