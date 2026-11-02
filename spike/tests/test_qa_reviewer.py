"""The line QA's reviewer is the Claude Code line-reviewer subagent (ADR 051):
the request it is given carries the same checklist Gemini was sent, its reply
is filed only when it matches the findings schema, and a filed review costs
nothing. No lesson folder and no API call."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import qa_narration as qn                                       # noqa: E402


def prep(out: Path, label: str = "pass1") -> dict:
    return {"data": {"ids": ["t1.s1.u1", "t1.s1.u2"], "boards": [], "exercise": []},
            "text": "THE LESSON, board by board: (two utterances)", "label": label,
            "n_pass": 1, "pages": [101], "out": out}


class RequestText(unittest.TestCase):
    def test_the_default_reviewer_is_the_subagent(self):
        self.assertEqual(qn.DEFAULT_REVIEWER, "claude")
        self.assertIn("gemini", qn.REVIEWERS)

    def test_the_request_carries_the_checklist_the_material_and_the_schema(self):
        text = qn.request_text(prep(Path("unused")))
        self.assertIn(qn.SYSTEM, text)                     # the same words Gemini is sent
        self.assertIn("(two utterances)", text)
        for check in qn.CHECKS:
            self.assertIn(f'"{check}"', text)              # the schema's enum, verbatim
        self.assertIn("Read nothing else", text)

    def test_the_agent_definition_exists_and_reads_only(self):
        agent = Path(__file__).resolve().parents[2] / ".claude" / "agents" / "line-reviewer.md"
        head = agent.read_text(encoding="utf-8").split("---")[1]
        self.assertIn("name: line-reviewer", head)
        self.assertIn("tools: Read", head)


class Ingest(unittest.TestCase):
    def filed(self, reply: str, label: str = "pass1") -> dict:
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "qa"
            r = Path(d) / "reply.json"
            r.write_text(reply, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                path = qn.ingest(prep(out, label), r)
            self.assertEqual(path, out / f"qa_{label}.json")
            self.assertTrue((out / f"raw_response_{label}.json").exists())
            return json.loads(path.read_text(encoding="utf-8"))

    def test_a_fenced_reply_is_filed_in_the_review_shape_at_no_cost(self):
        finding = {"utterance_id": "t1.s1.u2", "severity": "minor", "check": "student-level",
                   "issue": "'utilise' where 'use' would do", "proposed_fix": "use",
                   "confidence": "high"}
        filed = self.filed("```json\n" + json.dumps({"findings": [finding]}) + "\n```")
        self.assertEqual(filed["findings"], [finding])
        m = filed["meta"]
        self.assertEqual(m["reviewer"], "claude")
        self.assertEqual(m["cost_usd"], 0)
        self.assertEqual(m["mode"], "subagent")
        self.assertEqual(m["reviewed_utterances"], 2)
        self.assertEqual(m["unknown_ids"], [])
        self.assertIn("fresh subagent", m["independent_of"])

    def test_an_empty_findings_list_is_a_valid_review(self):
        filed = self.filed('{"findings": []}', label="decisions")
        self.assertEqual(filed["findings"], [])

    def test_a_finding_on_an_unknown_utterance_is_reported(self):
        finding = {"utterance_id": "t9.s9.u9", "severity": "major", "check": "grammar-rule",
                   "issue": "x", "proposed_fix": "y", "confidence": "low"}
        filed = self.filed(json.dumps({"findings": [finding]}))
        self.assertEqual(filed["meta"]["unknown_ids"], ["t9.s9.u9"])

    def test_a_reply_outside_the_schema_is_refused_and_nothing_is_filed(self):
        bad = {"findings": [{"utterance_id": "t1.s1.u1", "severity": "huge", "check": "grammar-rule",
                             "issue": "x", "proposed_fix": "y", "confidence": "high"}]}
        for reply in (json.dumps(bad), "no json here", '{"findings": [{"issue": "x"}]}',
                      '{"findings": [], "rewrite": "a whole new narration"}'):
            with tempfile.TemporaryDirectory() as d:
                r = Path(d) / "reply.json"
                r.write_text(reply, encoding="utf-8")
                with self.assertRaises(SystemExit) as cm:
                    qn.ingest(prep(Path(d) / "qa"), r)
                self.assertIn("REFUSED", str(cm.exception))
                self.assertFalse((Path(d) / "qa").exists())

    def test_the_request_is_written_where_asked_and_the_call_is_pending(self):
        with tempfile.TemporaryDirectory() as d:
            with redirect_stdout(io.StringIO()) as buf:
                path = qn.write_request(prep(Path(d) / "qa"), Path(d) / "elsewhere")
            self.assertEqual(path, Path(d) / "elsewhere" / "request_pass1.md")
            self.assertIn(qn.SYSTEM, path.read_text(encoding="utf-8"))
            self.assertIn("REVIEW PENDING", buf.getvalue())
            self.assertFalse((Path(d) / "qa").exists())
            self.assertEqual(qn.PENDING_EXIT, 3)


if __name__ == "__main__":
    unittest.main()
