#!/usr/bin/env python3
"""Build the Microsoft 365 app package for the Elfsquad agent.

Fills in the OAuth registration ID from the Teams Developer Portal and the agent instructions, copies the
plugin's skills into the package as agent skills, checks the limits Microsoft enforces, and writes
build/elfsquad-m365-<version>.zip for upload:

    ELFSQUAD_OAUTH_REGISTRATION_ID=<id> microsoft-365/build.py
"""

import json
import os
import re
import struct
import sys
import zipfile
from pathlib import Path

PACKAGE = Path(__file__).parent / "appPackage"
SKILLS = Path(__file__).parent.parent / "plugins" / "elfsquad" / "skills"
OUT = Path(__file__).parent / "build"

# Limits for agent skills in a declarative agent built from an app package.
MAX_SKILLS = 8
MAX_SKILL_FILES = 350
MAX_SKILL_DEPTH = 3
MAX_SKILL_INSTRUCTIONS = 20000
MAX_PACKAGE_BYTES = 10 * 1024 * 1024


def png_size(path: Path) -> tuple[int, int]:
    width, height = struct.unpack(">II", path.read_bytes()[16:24])
    return width, height


def fail(message: str) -> None:
    sys.exit(f"build.py: {message}")


def skill_files() -> dict[str, Path]:
    """Map each packaged path (skills/<name>/...) to its source file, after checking the skill limits."""
    files: dict[str, Path] = {}
    skill_dirs = sorted(d for d in SKILLS.iterdir() if d.is_dir())
    if not skill_dirs:
        fail(f"no skills found in {SKILLS}")
    if len(skill_dirs) > MAX_SKILLS:
        fail(f"{len(skill_dirs)} skills, the limit is {MAX_SKILLS}")
    for skill in skill_dirs:
        skill_md = skill / "SKILL.md"
        if not skill_md.is_file():
            fail(f"{skill.name} has no SKILL.md")
        text = skill_md.read_text()
        parts = text.split("---\n", 2)
        if len(parts) != 3 or parts[0].strip():
            fail(f"{skill.name}/SKILL.md must start with --- front matter ---")
        fields = dict(line.split(":", 1) for line in parts[1].splitlines() if ":" in line)
        if fields.get("name", "").strip() != skill.name:
            fail(f"{skill.name}/SKILL.md front matter must have name: {skill.name}")
        if not fields.get("description", "").strip():
            fail(f"{skill.name}/SKILL.md front matter has no description")
        body = parts[2].strip()
        if len(body) >= MAX_SKILL_INSTRUCTIONS:
            fail(f"{skill.name}/SKILL.md instructions are {len(body)} characters, the limit is {MAX_SKILL_INSTRUCTIONS}")
        for source in sorted(skill.rglob("*")):
            if not source.is_file() or source.name.startswith("."):
                continue
            relative = source.relative_to(SKILLS)
            if len(relative.parts) - 1 > MAX_SKILL_DEPTH:
                fail(f"{relative} is nested deeper than {MAX_SKILL_DEPTH} directories")
            files[f"skills/{relative.as_posix()}"] = source
    if len(files) > MAX_SKILL_FILES:
        fail(f"{len(files)} skill files, the limit is {MAX_SKILL_FILES}")
    return files


def main() -> None:
    registration_id = os.environ.get("ELFSQUAD_OAUTH_REGISTRATION_ID", "").strip()
    if not registration_id:
        fail("set ELFSQUAD_OAUTH_REGISTRATION_ID to the registration ID from the Teams Developer Portal")

    manifest = json.loads((PACKAGE / "manifest.json").read_text())
    agent = json.loads((PACKAGE / "declarativeAgent.json").read_text())
    plugin_text = (PACKAGE / "ai-plugin.json").read_text().replace("${{ELFSQUAD_OAUTH_REGISTRATION_ID}}", registration_id)
    plugin = json.loads(plugin_text)

    instructions = (PACKAGE / "instructions.md").read_text().strip()
    agent["instructions"] = instructions

    skills = skill_files()
    skill_names = sorted({path.split("/")[1] for path in skills})
    agent["agent_skills"] = [{"folder": f"./skills/{name}"} for name in skill_names]

    checks = [
        (len(instructions) <= 8000, f"instructions are {len(instructions)} characters, the limit is 8000"),
        (len(agent["name"]) <= 100, "agent name over 100 characters"),
        (len(agent["description"]) <= 1000, "agent description over 1000 characters"),
        (len(agent["conversation_starters"]) <= 12, "more than 12 conversation starters"),
        (len(manifest["name"]["short"]) <= 30, "name.short over 30 characters"),
        (len(manifest["name"]["full"]) <= 100, "name.full over 100 characters"),
        (len(manifest["description"]["short"]) <= 80, "description.short over 80 characters"),
        (len(manifest["description"]["full"]) <= 4000, "description.full over 4000 characters"),
        (len(manifest["developer"]["name"]) <= 32, "developer.name over 32 characters"),
        (len(plugin["name_for_human"]) <= 20, "name_for_human over 20 characters"),
        (len(plugin["description_for_human"]) <= 100, "description_for_human over 100 characters"),
        (len(plugin.get("description_for_model", "")) <= 2048, "description_for_model over 2048 characters"),
        (re.fullmatch(r"[A-Za-z0-9]+", plugin["namespace"]) is not None, "namespace must be letters and digits"),
        (png_size(PACKAGE / manifest["icons"]["color"]) == (192, 192), "color icon must be 192x192"),
        (png_size(PACKAGE / manifest["icons"]["outline"]) == (32, 32), "outline icon must be 32x32"),
    ]
    for ok, message in checks:
        if not ok:
            fail(message)

    OUT.mkdir(exist_ok=True)
    target = OUT / f"elfsquad-m365-{manifest['version']}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        archive.writestr("declarativeAgent.json", json.dumps(agent, indent=2))
        archive.writestr("ai-plugin.json", json.dumps(plugin, indent=2))
        archive.write(PACKAGE / manifest["icons"]["color"], manifest["icons"]["color"])
        archive.write(PACKAGE / manifest["icons"]["outline"], manifest["icons"]["outline"])
        for packaged, source in skills.items():
            archive.write(source, packaged)
    if target.stat().st_size > MAX_PACKAGE_BYTES:
        target.unlink()
        fail(f"package is over {MAX_PACKAGE_BYTES // (1024 * 1024)} MB")
    print(f"{target} ({len(skill_names)} skills: {', '.join(skill_names)})")


if __name__ == "__main__":
    main()
