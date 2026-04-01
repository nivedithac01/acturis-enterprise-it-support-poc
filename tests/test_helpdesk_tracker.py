"""Tests for helpdesk_tracker.py — ITSM help desk ticket tracking."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpdesk_tracker import HelpdeskTracker


class TestHelpdeskTracker:

    def setup_method(self):
        self.hd = HelpdeskTracker()

    def test_create_ticket_returns_dict(self):
        ticket = self.hd.log_ticket("Laptop won't start", "hardware", "john.smith", "Black screen", "high")
        assert ticket["ticket_id"] == "INC0001"
        assert ticket["status"] == "open"
        assert ticket["priority"] == "high"

    def test_create_ticket_increments_id(self):
        t1 = self.hd.log_ticket("Issue 1", "software", "user1", "Desc 1", "low")
        t2 = self.hd.log_ticket("Issue 2", "network", "user2", "Desc 2", "medium")
        assert t1["ticket_id"] == "INC0001"
        assert t2["ticket_id"] == "INC0002"

    def test_create_ticket_sets_sla_due(self):
        ticket = self.hd.log_ticket("VPN issue", "vpn", "user1", "Cannot connect", "critical")
        assert ticket["sla_due"] is not None
        assert ticket["priority"] == "critical"

    def test_create_ticket_invalid_priority_raises(self):
        with pytest.raises(ValueError, match="Invalid priority"):
            self.hd.log_ticket("Issue", "hardware", "user1", "Desc", "urgent")

    def test_create_ticket_invalid_category_raises(self):
        with pytest.raises(ValueError, match="Invalid category"):
            self.hd.log_ticket("Issue", "mainframe", "user1", "Desc", "low")

    def test_resolve_ticket(self):
        ticket = self.hd.log_ticket("Password reset", "account", "user1", "Locked out", "low")
        resolved = self.hd.resolve_ticket(ticket["ticket_id"], "Reset via AD console", "engineer.a")
        assert resolved["status"] == "resolved"
        assert resolved["resolved_at"] is not None
        assert resolved["resolved_by"] == "engineer.a"

    def test_resolve_already_resolved_raises(self):
        ticket = self.hd.log_ticket("Duplicate", "other", "user1", "Desc", "low")
        self.hd.resolve_ticket(ticket["ticket_id"], "Fixed", "engineer.a")
        with pytest.raises(ValueError, match="already resolved"):
            self.hd.resolve_ticket(ticket["ticket_id"], "Fixed again", "engineer.b")

    def test_resolve_unknown_ticket_raises(self):
        with pytest.raises(KeyError):
            self.hd.resolve_ticket("INC9999", "Fix", "engineer.a")

    def test_get_open_tickets(self):
        t1 = self.hd.log_ticket("Open issue", "software", "user1", "Desc", "low")
        t2 = self.hd.log_ticket("Resolved issue", "hardware", "user2", "Desc", "medium")
        self.hd.resolve_ticket(t2["ticket_id"], "Fixed", "engineer.a")
        open_tickets = self.hd.get_open_tickets()
        ids = [t["ticket_id"] for t in open_tickets]
        assert t1["ticket_id"] in ids
        assert t2["ticket_id"] not in ids

    def test_sla_report_structure(self):
        ticket = self.hd.log_ticket("Quick fix", "account", "user1", "Needs reset", "low")
        self.hd.resolve_ticket(ticket["ticket_id"], "Resolved immediately", "engineer.a")
        report = self.hd.get_sla_report()
        assert "low" in report
        assert "total" in report["low"]
        assert "compliance_pct" in report["low"]

    def test_search_kb_vpn(self):
        results = self.hd.search_kb("vpn")
        assert len(results) > 0
        assert any("vpn" in r["title"].lower() or any("vpn" in kw for kw in r["keywords"]) for r in results)

    def test_search_kb_password(self):
        results = self.hd.search_kb("password")
        assert len(results) > 0

    def test_search_kb_no_match(self):
        results = self.hd.search_kb("xyznonexistent123")
        assert results == []

    def test_search_kb_mdt(self):
        results = self.hd.search_kb("mdt")
        assert len(results) > 0

    def test_multiple_tickets_tracking(self):
        for i in range(5):
            self.hd.log_ticket(f"Issue {i}", "software", f"user{i}", f"Description {i}", "medium")
        open_tickets = self.hd.get_open_tickets()
        assert len(open_tickets) == 5
