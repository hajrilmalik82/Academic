"""Lightweight repository checks that do not require a running Odoo server."""

from __future__ import annotations

import ast
import py_compile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ADDON_PREFIX = "campus_"


def iter_addons() -> list[Path]:
    return sorted(
        path
        for path in ROOT.iterdir()
        if path.is_dir() and path.name.startswith(ADDON_PREFIX) and (path / "__manifest__.py").exists()
    )


def compile_python(addons: list[Path]) -> None:
    for addon in addons:
        for path in sorted(addon.rglob("*.py")):
            py_compile.compile(path, doraise=True)
            print(f"PY OK {path.relative_to(ROOT)}")


def parse_xml(addons: list[Path]) -> None:
    for addon in addons:
        for path in sorted(addon.rglob("*.xml")):
            ET.parse(path)
            print(f"XML OK {path.relative_to(ROOT)}")


def load_manifest(addon: Path) -> dict:
    manifest_path = addon / "__manifest__.py"
    return ast.literal_eval(manifest_path.read_text(encoding="utf-8"))


def validate_manifest_data(addons: list[Path]) -> None:
    for addon in addons:
        manifest = load_manifest(addon)
        for rel_path in manifest.get("data", []):
            full_path = addon / rel_path
            if not full_path.exists():
                raise FileNotFoundError(
                    f"{addon.name} manifest references missing data file: {rel_path}"
                )
            print(f"DATA OK {full_path.relative_to(ROOT)}")


def main() -> None:
    addons = iter_addons()
    if not addons:
        raise RuntimeError("No campus addons were found.")

    compile_python(addons)
    parse_xml(addons)
    validate_manifest_data(addons)


if __name__ == "__main__":
    main()
