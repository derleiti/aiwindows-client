from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aiwindows_client import bug_reporter

class BugReporterTests(unittest.TestCase):
    def test_redaction_and_queue(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw)
            with patch.object(bug_reporter,"_state_root",return_value=root), patch.object(bug_reporter,"_post",return_value=False):
                bug_reporter._config={"app":"AIWindows Client","repo":"aiwindows-client","version":"test","channel":"test"}
                result=bug_reporter.submit_manual("password=do-not-store")
            self.assertEqual(result,{"ok":False,"queued":True})
            self.assertNotIn("do-not-store",json.dumps(json.loads((root/"pending-reports.json").read_text())))
    def test_selftest(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw)
            with patch.object(bug_reporter,"_state_root",return_value=root):
                self.assertTrue(bug_reporter.startup_selftest()["ok"])

if __name__ == "__main__": unittest.main()
