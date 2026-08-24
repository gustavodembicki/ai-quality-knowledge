import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_adapters import (
    BEGIN_MARKER,
    END_MARKER,
    MigrationError,
    apply_knowledge,
    check_knowledge,
    resolve_targets,
)


MODULES = (
    "context.md",
    "output.md",
    "coding.md",
    "testing.md",
    "reviewing.md",
    "github.md",
    "grill-me.md",
)


class KnowledgeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "source"
        self.home = self.root / "home"
        self.project = self.root / "project"
        self.home.mkdir()
        self.project.mkdir()
        routes = "\n".join(f"- `knowledge/{module}`" for module in MODULES)
        self.write(self.source / "AGENTS.md", f"# Router\n\n{routes}\n")
        for module in MODULES:
            self.write(
                self.source / "knowledge" / module,
                f"# {module.removesuffix('.md').title()}\n\nOriginal guidance.\n",
            )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def apply(self, tools=("codex",), scope="user", **options):
        return apply_knowledge(
            self.source,
            tools,
            scope,
            home=self.home,
            project=self.project,
            environment={},
            **options,
        )

    def check(self, tools=("codex",), scope="user"):
        return check_knowledge(
            self.source,
            tools,
            scope,
            home=self.home,
            project=self.project,
            environment={},
        )

    def test_user_targets_use_native_instruction_files(self):
        targets = resolve_targets(
            ("codex", "claude", "devin"),
            "user",
            home=self.home,
            project=self.project,
            environment={},
        )
        by_tool = {target.tools[0]: target for target in targets}

        self.assertEqual(by_tool["codex"].instruction_file, self.home / ".codex/AGENTS.md")
        self.assertEqual(by_tool["claude"].instruction_file, self.home / ".claude/CLAUDE.md")
        self.assertEqual(
            by_tool["devin"].instruction_file,
            self.home / ".config/devin/AGENTS.md",
        )

    def test_user_targets_honor_codex_and_xdg_homes(self):
        environment = {
            "CODEX_HOME": str(self.root / "codex-home"),
            "XDG_CONFIG_HOME": str(self.root / "xdg"),
        }
        targets = resolve_targets(
            ("codex", "devin"),
            "user",
            home=self.home,
            project=self.project,
            environment=environment,
        )
        by_tool = {target.tools[0]: target for target in targets}

        self.assertEqual(
            by_tool["codex"].instruction_file,
            self.root / "codex-home/AGENTS.md",
        )
        self.assertEqual(
            by_tool["devin"].instruction_file,
            self.root / "xdg/devin/AGENTS.md",
        )

    def test_user_target_honors_windows_appdata(self):
        targets = resolve_targets(
            ("devin",),
            "user",
            home=self.home,
            project=self.project,
            environment={"APPDATA": str(self.root / "appdata")},
        )

        self.assertEqual(
            targets[0].instruction_file,
            self.root / "appdata/devin/AGENTS.md",
        )

    def test_project_targets_share_codex_and_devin_installation(self):
        targets = resolve_targets(
            ("codex", "claude", "devin"),
            "project",
            home=self.home,
            project=self.project,
            environment={},
        )

        self.assertEqual(len(targets), 2)
        shared = next(target for target in targets if target.instruction_file.name == "AGENTS.md")
        claude = next(target for target in targets if target.instruction_file.name == "CLAUDE.md")
        self.assertEqual(shared.tools, ("codex", "devin"))
        self.assertEqual(claude.tools, ("claude",))
        self.assertEqual(shared.payload_directory, self.project / ".ai-quality-knowledge")
        self.assertEqual(claude.payload_directory, shared.payload_directory)

    def test_project_install_preserves_both_instruction_files_and_checks_cleanly(self):
        self.write(self.project / "AGENTS.md", "# Existing agents\n")
        self.write(self.project / "CLAUDE.md", "# Existing Claude\n")
        tools = ("codex", "claude", "devin")

        self.apply(tools=tools, scope="project")

        self.assertEqual(self.check(tools=tools, scope="project"), [])
        self.assertIn(
            "# Existing agents",
            (self.project / "AGENTS.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "# Existing Claude",
            (self.project / "CLAUDE.md").read_text(encoding="utf-8"),
        )
        self.assertTrue((self.project / ".ai-quality-knowledge/manifest.json").is_file())

    def test_apply_preserves_existing_instructions_and_creates_backup(self):
        instruction_file = self.home / ".codex/AGENTS.md"
        self.write(instruction_file, "# Existing instructions\n")

        self.apply()

        content = instruction_file.read_text(encoding="utf-8")
        self.assertIn("# Existing instructions", content)
        self.assertIn(BEGIN_MARKER, content)
        self.assertIn(END_MARKER, content)
        self.assertEqual(content.count(BEGIN_MARKER), 1)
        self.assertEqual(
            instruction_file.with_name("AGENTS.md.ai-quality-knowledge.bak").read_text(
                encoding="utf-8"
            ),
            "# Existing instructions\n",
        )
        self.assertEqual(self.check(), [])

    def test_apply_is_idempotent(self):
        self.apply()
        instruction_file = self.home / ".codex/AGENTS.md"
        original = instruction_file.read_text(encoding="utf-8")

        changes = self.apply()

        self.assertEqual(changes, [])
        self.assertEqual(instruction_file.read_text(encoding="utf-8"), original)
        self.assertEqual(original.count(BEGIN_MARKER), 1)

    def test_original_backup_is_preserved_after_managed_updates(self):
        instruction_file = self.home / ".codex/AGENTS.md"
        backup_file = self.home / ".codex/AGENTS.md.ai-quality-knowledge.bak"
        self.write(instruction_file, "# Original user instructions\n")
        self.apply()
        self.write(
            self.source / "knowledge/context.md",
            "# Context\n\nUpdated guidance.\n",
        )

        self.apply()

        self.assertEqual(
            backup_file.read_text(encoding="utf-8"),
            "# Original user instructions\n",
        )

    def test_dry_run_does_not_write(self):
        changes = self.apply(dry_run=True)

        self.assertTrue(changes)
        self.assertFalse((self.home / ".codex/AGENTS.md").exists())
        self.assertFalse((self.home / ".codex/ai-quality-knowledge").exists())

    def test_apply_updates_managed_content_without_changing_user_content(self):
        instruction_file = self.home / ".codex/AGENTS.md"
        self.write(instruction_file, "# User content\n")
        self.apply()
        self.write(
            self.source / "knowledge/context.md",
            "# Context\n\nUpdated guidance.\n",
        )

        self.apply()

        self.assertIn("# User content", instruction_file.read_text(encoding="utf-8"))
        self.assertEqual(
            (self.home / ".codex/ai-quality-knowledge/knowledge/context.md").read_text(
                encoding="utf-8"
            ),
            "# Context\n\nUpdated guidance.\n",
        )
        self.assertEqual(self.check(), [])

    def test_check_detects_payload_drift(self):
        self.apply()
        self.write(
            self.home / ".codex/ai-quality-knowledge/knowledge/context.md",
            "# Drifted\n",
        )

        errors = self.check()

        self.assertTrue(any("payload drift" in error.lower() for error in errors))

    def test_check_detects_managed_router_drift(self):
        instruction_file = self.home / ".codex/AGENTS.md"
        self.apply()
        content = instruction_file.read_text(encoding="utf-8")
        instruction_file.write_text(
            content.replace("Resolve bare module references", "Changed managed router"),
            encoding="utf-8",
        )

        self.assertTrue(
            any("managed router drift" in error.lower() for error in self.check())
        )

    def test_check_detects_manifest_drift(self):
        manifest_file = self.home / ".codex/ai-quality-knowledge/manifest.json"
        self.apply()
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest["schema_version"] = 999
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")

        self.assertTrue(any("manifest drift" in error.lower() for error in self.check()))

    def test_check_detects_invalid_manifest(self):
        manifest_file = self.home / ".codex/ai-quality-knowledge/manifest.json"
        self.apply()
        manifest_file.write_text("{invalid", encoding="utf-8")

        self.assertTrue(any("invalid manifest" in error.lower() for error in self.check()))

    def test_check_detects_missing_instruction_file(self):
        instruction_file = self.home / ".codex/AGENTS.md"
        self.apply()
        instruction_file.unlink()

        self.assertTrue(
            any("missing instruction file" in error.lower() for error in self.check())
        )

    def test_malformed_managed_block_is_rejected(self):
        self.write(self.home / ".codex/AGENTS.md", f"# Existing\n\n{BEGIN_MARKER}\n")

        with self.assertRaises(MigrationError):
            self.apply()

    def test_unmanaged_payload_requires_force(self):
        self.write(self.home / ".codex/ai-quality-knowledge/unknown.txt", "user data\n")

        with self.assertRaises(MigrationError):
            self.apply()

        self.apply(force=True)
        self.assertEqual(
            (self.home / ".codex/ai-quality-knowledge/unknown.txt").read_text(
                encoding="utf-8"
            ),
            "user data\n",
        )
        self.assertEqual(self.check(), [])

    def test_all_user_installations_are_independently_valid(self):
        tools = ("codex", "claude", "devin")

        self.apply(tools=tools)

        self.assertEqual(self.check(tools=tools), [])
        self.assertTrue((self.home / ".codex/AGENTS.md").is_file())
        self.assertTrue((self.home / ".claude/CLAUDE.md").is_file())
        self.assertTrue((self.home / ".config/devin/AGENTS.md").is_file())

    def test_apply_and_check_clis_work_with_isolated_home(self):
        repository = Path(__file__).resolve().parents[1]
        environment = os.environ.copy()
        for variable in ("CODEX_HOME", "XDG_CONFIG_HOME", "APPDATA"):
            environment.pop(variable, None)
        common_arguments = [
            "--tool",
            "all",
            "--scope",
            "user",
            "--source",
            str(self.source),
            "--home",
            str(self.home),
            "--project",
            str(self.project),
        ]

        apply_result = subprocess.run(
            [sys.executable, str(repository / "scripts/apply_knowledge.py"), *common_arguments],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        check_result = subprocess.run(
            [sys.executable, str(repository / "scripts/check_knowledge.py"), *common_arguments],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )

        self.assertEqual(apply_result.returncode, 0, apply_result.stderr)
        self.assertEqual(check_result.returncode, 0, check_result.stdout + check_result.stderr)


if __name__ == "__main__":
    unittest.main()
