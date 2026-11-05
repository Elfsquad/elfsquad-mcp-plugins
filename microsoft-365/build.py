#!/usr/bin/env python3
"""Build the Microsoft 365 app package for the Elfsquad agent.

Fills in the OAuth registration ID from the Teams Developer Portal and the agent instructions, checks
the limits Microsoft enforces, and writes build/elfsquad-m365-<version>.zip for upload:

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
OUT = Path(__file__).parent / "build"


def png_size(path: Path) -> tuple[int, int]:
    width, height = struct.unpack(">II", path.read_bytes()[16:24])
    return width, height


def fail(message: str) -> None:
    sys.exit(f"build.py: {message}")


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
    print(target)


if __name__ == "__main__":
    main()
