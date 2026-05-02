import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


extractor = load_module(
    "extract_session_failures",
    ROOT / "skills" / "si:errors" / "scripts" / "extract_session_failures.py",
)


class ExtractSessionFailuresTest(unittest.TestCase):
    def test_extracts_expected_fixture_summary(self):
        result = extractor.extract(ROOT / "examples" / "session-with-friction.jsonl")

        self.assertEqual(result["total_lines"], 6)
        self.assertEqual(result["total_events"], 4)
        self.assertEqual(result["tool_failures"], 2)
        self.assertEqual(result["user_corrections"], 2)

    def test_tool_failure_includes_context_and_follow_up(self):
        result = extractor.extract(ROOT / "examples" / "session-with-friction.jsonl")
        failure = result["events"][0]

        self.assertEqual(failure["category"], "tool_failure")
        self.assertEqual(failure["kind"], "ERROR")
        self.assertEqual(failure["tool_call"]["tool"], "Bash")
        self.assertEqual(failure["tool_call"]["input"]["command"], "pytest tests/test_widget.py")
        self.assertIn("pytest: command not found", failure["error"])
        self.assertIn("python -m unittest", failure["user_follow_up"])

    def test_interruption_binds_to_preceding_tool_call(self):
        result = extractor.extract(ROOT / "examples" / "session-with-friction.jsonl")
        interrupted = [e for e in result["events"] if e["kind"] == "INTERRUPTED"][0]

        self.assertEqual(interrupted["tool_use_id"], "toolu_2")
        self.assertEqual(interrupted["tool_call"]["input"]["command"], "rm ~/.claude/CLAUDE-si.md")
        self.assertIn("reversible patch", interrupted["user_follow_up"])

    def test_ordinary_user_message_is_not_a_correction(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as fixture:
            fixture.write(
                json.dumps(
                    {
                        "type": "user",
                        "timestamp": "2026-05-02T12:00:00Z",
                        "message": {"content": "Please inspect the README and summarize it."},
                    }
                )
                + "\n"
            )
            path = fixture.name

        try:
            result = extractor.extract(path)
            self.assertEqual(result["user_corrections"], 0)
            self.assertEqual(result["total_events"], 0)
        finally:
            os.unlink(path)


class SetupStateTest(unittest.TestCase):
    def test_state_uses_temp_home_and_detects_setup(self):
        script = ROOT / "skills" / "si:setup" / "scripts" / "state.py"

        with tempfile.TemporaryDirectory() as home:
            claude = pathlib.Path(home) / ".claude"
            claude.mkdir()
            (claude / "CLAUDE.md").write_text(
                "Existing config\n<!-- SI:IMPORT:START -->\n@CLAUDE-si.md\n<!-- SI:IMPORT:END -->\n"
            )
            (claude / "CLAUDE-si.md").write_text("## Custom skills @self-improve\n")

            env = os.environ.copy()
            env["HOME"] = home
            completed = subprocess.run(
                [sys.executable, str(script), "write"],
                check=True,
                text=True,
                capture_output=True,
                env=env,
            )

            state = json.loads(completed.stdout)
            self.assertTrue(state["setup_complete"])
            self.assertTrue(state["import_wired"])
            self.assertEqual(pathlib.Path(state["claude_root"]).resolve(), claude.resolve())
            self.assertTrue((pathlib.Path(home) / ".si-state.json").exists())


class ConfigEditScriptsTest(unittest.TestCase):
    def test_register_trigger_writes_to_temp_claude_si_idempotently(self):
        script = ROOT / "skills" / "si:create" / "scripts" / "register_trigger.py"

        with tempfile.TemporaryDirectory() as home:
            claude = pathlib.Path(home) / ".claude"
            claude.mkdir()
            env = os.environ.copy()
            env["HOME"] = home

            for _ in range(2):
                subprocess.run(
                    [sys.executable, str(script), "working with release notes", "si:release-notes"],
                    check=True,
                    text=True,
                    capture_output=True,
                    env=env,
                )

            content = (claude / "CLAUDE-si.md").read_text()
            self.assertIn("## Custom skills @self-improve", content)
            self.assertIn("WHEN working with release notes, you MUST invoke `/si:release-notes`", content)
            self.assertEqual(content.count("WHEN working with release notes"), 1)

    def test_inject_import_is_idempotent(self):
        script = ROOT / "skills" / "si:create" / "scripts" / "inject_import.py"

        with tempfile.TemporaryDirectory() as home:
            claude = pathlib.Path(home) / ".claude"
            claude.mkdir()
            claude_md = claude / "CLAUDE.md"
            claude_md.write_text("Existing config\n")
            env = os.environ.copy()
            env["HOME"] = home

            for _ in range(2):
                subprocess.run(
                    [sys.executable, str(script)],
                    check=True,
                    text=True,
                    capture_output=True,
                    env=env,
                )

            content = claude_md.read_text()
            self.assertIn("Existing config", content)
            self.assertEqual(content.count("@CLAUDE-si.md"), 1)


class ManifestParityTest(unittest.TestCase):
    def test_plugin_manifest_versions_and_descriptions_match(self):
        manifests = [
            ROOT / ".claude-plugin" / "plugin.json",
            ROOT / ".cursor-plugin" / "plugin.json",
            ROOT / ".codex-plugin" / "plugin.json",
        ]
        loaded = [json.loads(path.read_text()) for path in manifests]

        versions = {manifest["version"] for manifest in loaded}
        descriptions = {manifest["description"] for manifest in loaded}

        self.assertEqual(versions, {"0.1.0"})
        self.assertEqual(len(descriptions), 1)

    def test_marketplaces_point_to_repo_root_payload(self):
        claude = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        cursor = json.loads((ROOT / ".cursor-plugin" / "marketplace.json").read_text())
        agents = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text())

        self.assertEqual(claude["plugins"][0]["source"], "./")
        self.assertEqual(cursor["plugins"][0]["source"], "./")
        self.assertEqual(agents["plugins"][0]["source"]["path"], "./")


if __name__ == "__main__":
    unittest.main()
