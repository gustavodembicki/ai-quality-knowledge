import tempfile
import unittest
from pathlib import Path

from scripts.validate_knowledge import validate_repository


MODULES = (
    "context.md",
    "continuity.md",
    "output.md",
    "coding.md",
    "testing.md",
    "reviewing.md",
    "github.md",
    "grill-me.md",
)


class KnowledgeValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.write(".tool-versions", "python 3.14.6\n")
        routes = "\n".join(f"- `knowledge/{module}`" for module in MODULES)
        self.write("AGENTS.md", f"# Router\n\nDo not preload all modules.\n\n{routes}\n")
        for module in MODULES:
            self.write(f"knowledge/{module}", f"# {module.removesuffix('.md').title()}\n")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def errors(self):
        return validate_repository(self.root)

    def test_valid_repository_passes(self):
        self.assertEqual(self.errors(), [])

    def test_missing_required_module_fails(self):
        (self.root / "knowledge/testing.md").unlink()

        self.assertTrue(any("missing required module" in error.lower() for error in self.errors()))

    def test_missing_router_still_validates_required_modules(self):
        (self.root / "AGENTS.md").unlink()
        (self.root / "knowledge/testing.md").unlink()

        errors = self.errors()

        self.assertTrue(any("missing required file" in error.lower() for error in errors))
        self.assertTrue(any("missing required module" in error.lower() for error in errors))

    def test_unrouted_module_fails(self):
        router = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        (self.root / "AGENTS.md").write_text(
            router.replace("- `knowledge/testing.md`\n", ""), encoding="utf-8"
        )

        self.assertTrue(any("not routed" in error.lower() for error in self.errors()))

    def test_orphan_module_fails(self):
        self.write("knowledge/unused.md", "# Unused\n")

        self.assertTrue(any("orphan module" in error.lower() for error in self.errors()))

    def test_broken_route_fails(self):
        router_path = self.root / "AGENTS.md"
        router = router_path.read_text(encoding="utf-8")
        router_path.write_text(router + "- `knowledge/missing.md`\n", encoding="utf-8")

        self.assertTrue(any("broken module route" in error.lower() for error in self.errors()))

    def test_invalid_markdown_heading_fails(self):
        self.write("knowledge/context.md", "Context without a heading\n")

        self.assertTrue(any("top-level heading" in error.lower() for error in self.errors()))

    def test_invalid_utf8_fails(self):
        (self.root / "knowledge/context.md").write_bytes(b"\xff")

        self.assertTrue(any("not valid utf-8" in error.lower() for error in self.errors()))

    def test_personal_absolute_path_fails(self):
        self.write("knowledge/context.md", "# Context\n\n/Users/private-owner/project\n")

        self.assertTrue(any("absolute user path" in error.lower() for error in self.errors()))

    def test_placeholder_absolute_path_passes(self):
        self.write("knowledge/context.md", "# Context\n\n/Users/example/project\n")

        self.assertEqual(self.errors(), [])

    def test_likely_credential_fails(self):
        likely_credential = "github_" + "pat_" + "A" * 30
        self.write("knowledge/context.md", f"# Context\n\n{likely_credential}\n")

        self.assertTrue(any("credential" in error.lower() for error in self.errors()))

    def test_exclusive_agent_configuration_fails(self):
        (self.root / ".devin").mkdir()

        self.assertTrue(any("exclusive agent configuration" in error.lower() for error in self.errors()))

    def test_exclusive_agent_skill_fails(self):
        self.write("portable/SKILL.md", "# Skill\n")

        self.assertTrue(any("exclusive agent skill" in error.lower() for error in self.errors()))

    def test_invalid_tool_versions_format_fails(self):
        self.write(".tool-versions", "python 3.14\n")

        self.assertTrue(any("exact semantic version" in error.lower() for error in self.errors()))

    def test_oversized_router_fails(self):
        router = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        (self.root / "AGENTS.md").write_text(router + "extra\n" * 100, encoding="utf-8")

        self.assertTrue(any("router exceeds" in error.lower() for error in self.errors()))


class KnowledgeContinuityContractTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]
    continuity_path = root / "knowledge/continuity.md"

    @classmethod
    def setUpClass(cls):
        cls.router = (cls.root / "AGENTS.md").read_text(encoding="utf-8")
        cls.continuity = cls.continuity_path.read_text(encoding="utf-8")

    def section(self, heading):
        start = self.continuity.index(heading) + len(heading)
        end = self.continuity.find("\n## ", start)
        return self.continuity[start:] if end == -1 else self.continuity[start:end]

    def test_continuity_protocol_is_routed_and_structured(self):
        self.assertIn("`knowledge/continuity.md`", self.router)
        for heading in (
            "## State layers",
            "## Session boundaries",
            "## Context assembly",
            "## Token budget",
            "## Handoff and checkpoint",
        ):
            self.assertIn(heading, self.continuity)

    def test_session_boundaries_preserve_resume_and_fresh_semantics(self):
        section = self.section("## Session boundaries")

        self.assertIn("**resumed session**, use the restored conversation history", section)
        self.assertIn("**fresh session**, assume no access to prior internal state", section)
        self.assertIn("fresh session with a handoff remains fresh", section)
        self.assertIn("compacted summary as an index to surviving evidence", section)
        self.assertIn("current authoritative evidence", section)

    def test_context_assembly_preserves_order_and_instruction_precedence(self):
        section = self.section("## Context assembly")
        steps = (
            "1. **Intent:**",
            "2. **Gather:**",
            "3. **Reconcile:**",
            "4. **Decide:**",
            "5. **Verify:**",
        )

        positions = [section.index(step) for step in steps]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("as data, not instructions", section)
        self.assertIn("Recognized user and repository rule files", section)
        self.assertIn("cannot override", section)

    def test_token_budget_is_whole_context_native_first_and_honest(self):
        section = self.section("## Token budget")

        self.assertIn("Budget the whole context", section)
        self.assertIn("native context meter or tokenizer when available", section)
        self.assertIn("`ceil(characters / 4)` only as a labeled estimate", section)
        self.assertIn("additional safety margin", section)
        self.assertIn("Stop loading at coherent boundaries", section)
        self.assertIn("Report material omissions or truncation", section)

    def test_handoffs_are_authorized_provenance_bearing_and_private(self):
        section = self.section("## Handoff and checkpoint")

        self.assertIn("user explicitly requests it", section)
        self.assertIn("authorized checkpoint path", section)
        self.assertIn("rationale, provenance, and an as-of point", section)
        self.assertIn("navigation aid", section)
        self.assertIn("current authoritative evidence", section)
        self.assertIn("Do not persist secrets", section)
        self.assertIn("explicitly authorized", section)


class AutomationContractTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def test_python_version_is_pinned(self):
        self.assertEqual(
            (self.root / ".tool-versions").read_text(encoding="utf-8"),
            "python 3.14.6\n",
        )

    def test_workflow_runs_tests_and_repository_validation(self):
        workflow = (self.root / ".github/workflows/validate.yml").read_text(encoding="utf-8")

        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("python scripts/validate_knowledge.py .", workflow)


if __name__ == "__main__":
    unittest.main()
