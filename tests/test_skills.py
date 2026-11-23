"""The skills are instructions only. The main skill names the pipeline release it was tested with."""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "sbci-pipeline" / "SKILL.md"
REFERENCES = sorted((REPO / "sbci-pipeline" / "references").glob("*.md"))
FOCUSED = sorted((REPO / "sbci-focused-skills").glob("*/SKILL.md"))


class SkillTests(unittest.TestCase):
    def test_main_skill_names_one_pipeline_release(self) -> None:
        text = MAIN.read_text(encoding="utf-8")
        main = re.search(r"\*\*Pipeline release: SBCI_Pipeline_Py3 `([^`]+)` \(commit `([0-9a-f]{7})`\)\.\*\*", text)
        self.assertIsNotNone(main)
        release, commit = main.groups()
        self.assertIn(f"~/.cyberbench/SBCI_Pipeline_Py3-{release}", text)
        self.assertRegex(text, rf"checkout --detach {commit}[0-9a-f]{{33}}\n")
        self.assertIn(f"must start with {commit}", text)
        walkthrough = (REPO / "sbci-pipeline" / "references" / "running_one_subject_on_wanda.md").read_text(encoding="utf-8")
        self.assertIn(f"SBCI_Pipeline_Py3-{release}", walkthrough)
        self.assertRegex(walkthrough, rf"checkout --detach {commit}[0-9a-f]{{33}}\n")

    def test_skills_hold_no_code(self) -> None:
        files = {p.relative_to(REPO).as_posix() for p in (REPO / "sbci-pipeline").rglob("*") if p.is_file()}
        files |= {p.relative_to(REPO).as_posix() for p in (REPO / "sbci-focused-skills").rglob("*") if p.is_file()}
        self.assertEqual(set(), {f for f in files if not f.endswith(".md")})

    def test_main_skill_uses_the_current_layout(self) -> None:
        """Paths of the earlier layout (scripts/, examples/, vendor/, the per-cluster job script) are gone."""
        old = ("<skill>", "uploaded-skills/sbci-pipeline", "longleaf_run_subject.sbatch", "scripts/submit.sh",
               "examples/sbci_config", "vendor/sbci", "ADNI_example", "get_synb0", "sbci-workflow",
               "sbci-runtime", "scripts/hpc_probe.py", "install_preprocessing_runtime.sh")
        for path in [MAIN, *REFERENCES]:
            if path.name == "upstream_provenance.md":  # a historical record, kept as written
                continue
            text = path.read_text(encoding="utf-8")
            for term in old:
                self.assertNotIn(term, text, f"{path.name}: {term}")

    def test_main_skill_starts_jobs_through_submit_sh(self) -> None:
        """A bare sbatch fails on Wanda's Lab Server and Desktop, which have no Slurm."""
        text = MAIN.read_text(encoding="utf-8")
        self.assertIn("workflow/submit.sh", text)
        self.assertIn("workflow/run_subject.sbatch", text)
        self.assertNotRegex(text, r"(?m)^\s*`?sbatch ")

    def test_each_focused_skill_names_itself(self) -> None:
        """The focused skills are not updated to the current layout (README.md); only their names are checked."""
        if not FOCUSED:
            self.skipTest("the focused skills are not part of this tree")
        self.assertEqual(8, len(FOCUSED))
        for path in FOCUSED:
            front = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", path.read_text(encoding="utf-8"))
            self.assertIsNotNone(front, path.parent.name)
            self.assertEqual(path.parent.name, front.group(1))


if __name__ == "__main__":
    unittest.main()
