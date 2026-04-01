"""Tests for ad_provisioning.py — Active Directory user management."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ad_provisioning import ADProvisioner, ADUser


class TestADProvisioner:

    def setup_method(self):
        self.ad = ADProvisioner()

    def test_create_user_basic(self):
        user = self.ad.create_user("jane.doe", "Jane Doe", "IT Support Engineer", "IT")
        assert user.username == "jane.doe"
        assert user.display_name == "Jane Doe"
        assert user.job_title == "IT Support Engineer"
        assert user.department == "IT"
        assert user.enabled is True

    def test_create_user_default_email(self):
        user = self.ad.create_user("bob.smith", "Bob Smith", "Analyst", "Finance")
        assert user.email == "bob.smith@company.local"

    def test_create_user_department_groups_assigned(self):
        user = self.ad.create_user("alice.jones", "Alice Jones", "Engineer", "IT")
        assert "IT-Staff" in user.groups
        assert "VPN-Access" in user.groups
        assert "Admin-Tools" in user.groups

    def test_create_user_duplicate_raises(self):
        self.ad.create_user("john.smith", "John Smith", "Support", "IT")
        with pytest.raises(ValueError, match="already exists"):
            self.ad.create_user("john.smith", "John Smith", "Support", "IT")

    def test_create_user_additional_groups(self):
        user = self.ad.create_user(
            "tom.jones", "Tom Jones", "Manager", "Engineering",
            additional_groups=["Project-X"]
        )
        assert "Project-X" in user.groups

    def test_deactivate_user(self):
        self.ad.create_user("leaverA", "Leaver A", "Analyst", "Finance")
        user = self.ad.deactivate_user("leaverA")
        assert user.enabled is False
        assert user.groups == []

    def test_deactivate_already_disabled_raises(self):
        self.ad.create_user("leaverB", "Leaver B", "Analyst", "HR")
        self.ad.deactivate_user("leaverB")
        with pytest.raises(ValueError, match="already disabled"):
            self.ad.deactivate_user("leaverB")

    def test_reactivate_user(self):
        self.ad.create_user("returnee", "Return User", "Engineer", "Engineering")
        self.ad.deactivate_user("returnee")
        user = self.ad.reactivate_user("returnee")
        assert user.enabled is True
        assert "Engineering-Staff" in user.groups

    def test_update_job_title(self):
        self.ad.create_user("promo.user", "Promo User", "Junior Analyst", "Finance")
        user = self.ad.update_job_title("promo.user", "Senior Analyst")
        assert user.job_title == "Senior Analyst"

    def test_transfer_department(self):
        self.ad.create_user("mover.user", "Mover User", "Engineer", "Engineering")
        user = self.ad.transfer_department("mover.user", "IT")
        assert user.department == "IT"
        assert "IT-Staff" in user.groups
        assert "Engineering-Staff" not in user.groups

    def test_add_to_group(self):
        self.ad.create_user("group.user", "Group User", "Analyst", "Sales")
        user = self.ad.add_to_group("group.user", "Special-Project")
        assert "Special-Project" in user.groups

    def test_remove_from_group(self):
        self.ad.create_user("rm.user", "Remove User", "Analyst", "Sales")
        self.ad.add_to_group("rm.user", "Temp-Group")
        user = self.ad.remove_from_group("rm.user", "Temp-Group")
        assert "Temp-Group" not in user.groups

    def test_reset_password_returns_string(self):
        self.ad.create_user("pwd.user", "Pwd User", "Support", "IT")
        temp_pw = self.ad.reset_password("pwd.user")
        assert isinstance(temp_pw, str)
        assert len(temp_pw) > 0

    def test_audit_report_counts(self):
        self.ad.create_user("u1", "User 1", "Role", "IT")
        self.ad.create_user("u2", "User 2", "Role", "Finance")
        self.ad.deactivate_user("u2")
        report = self.ad.audit_report()
        assert report["total_accounts"] == 2
        assert report["enabled_accounts"] == 1
        assert report["disabled_accounts"] == 1

    def test_get_user_not_found_raises(self):
        with pytest.raises(KeyError):
            self.ad.get_user("nonexistent.user")

    def test_delete_active_user_raises(self):
        self.ad.create_user("active.user", "Active User", "Role", "IT")
        with pytest.raises(ValueError, match="Deactivate first"):
            self.ad.delete_user("active.user")

    def test_delete_disabled_user_succeeds(self):
        self.ad.create_user("del.user", "Del User", "Role", "HR")
        self.ad.deactivate_user("del.user")
        self.ad.delete_user("del.user")
        with pytest.raises(KeyError):
            self.ad.get_user("del.user")

    def test_audit_log_populated(self):
        self.ad.create_user("log.user", "Log User", "Role", "IT")
        log = self.ad.get_audit_log()
        assert len(log) >= 1
        assert log[0]["action"] == "CREATE"
        assert log[0]["username"] == "log.user"

    def test_list_users_in_group(self):
        self.ad.create_user("g1.user", "G1 User", "Role", "IT")
        self.ad.create_user("g2.user", "G2 User", "Role", "Finance")
        it_users = self.ad.list_users_in_group("IT-Staff")
        assert any(u.username == "g1.user" for u in it_users)
        assert all(u.username != "g2.user" for u in it_users)
