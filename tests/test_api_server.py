"""Integration and unit tests for the Agent_Banca FastAPI backend server functions."""

import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from src.api_server import (
    PDFGenerationRequest,
    generate_pdf,
    get_sample_fixtures,
    health_check,
    reconcile_samples,
    set_copilot_backend,
    get_auth_status,
    list_sessions,
)
from src.copilot_backend import CopilotAuthStatus, CopilotSessionInfo


class ApiServerTests(unittest.TestCase):
    def setUp(self):
        self.mock_backend = MagicMock()
        self.mock_backend.get_auth_status.return_value = CopilotAuthStatus(
            is_authenticated=True,
            login="testuser",
            auth_type="user",
            status_message="OK",
        )
        self.mock_backend.list_sessions.return_value = [
            CopilotSessionInfo(
                session_id="test-session-123",
                summary="Test Session",
                start_time=datetime.now(timezone.utc),
                modified_time=datetime.now(timezone.utc),
            )
        ]
        set_copilot_backend(self.mock_backend)

    def tearDown(self):
        set_copilot_backend(None)

    def test_health_check(self):
        res = health_check()
        self.assertEqual(res.status, "healthy")
        self.assertTrue(res.local_fixtures_available)

    def test_get_sample_fixtures(self):
        fixtures = get_sample_fixtures()
        self.assertIn("poc_bank", fixtures)
        self.assertIn("poc_gateway", fixtures)
        self.assertIn("poc_ledger", fixtures)
        self.assertIn("records", fixtures["poc_bank"])

    def test_reconcile_samples_deterministic(self):
        result = reconcile_samples()
        self.assertTrue(result["success"])
        self.assertIn("report", result)
        summary = result["report"]["summary"]
        self.assertIn("exact_matches", summary)
        self.assertIn("reconciliation_exceptions", summary)

    def test_generate_pdf_from_report(self):
        result = reconcile_samples()
        report = result["report"]
        sources = result["sources"]
        req = PDFGenerationRequest(report=report, sources=sources)
        pdf_response = generate_pdf(req)
        self.assertEqual(pdf_response.media_type, "application/pdf")
        self.assertTrue(pdf_response.body.startswith(b"%PDF"))

    def test_copilot_auth_and_sessions(self):
        auth = get_auth_status()
        self.assertTrue(auth["is_authenticated"])
        self.assertEqual(auth["login"], "testuser")

        sessions = list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].session_id, "test-session-123")


if __name__ == "__main__":
    unittest.main()
