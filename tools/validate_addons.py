"""Lightweight repository checks that do not require a running Odoo server."""

from __future__ import annotations

import ast
import csv
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


def collect_xml_record_ids(addons: list[Path]) -> set[str]:
    record_ids = set()
    for addon in addons:
        for path in sorted(addon.rglob("*.xml")):
            root = ET.parse(path).getroot()
            for record in root.findall(".//record"):
                record_id = record.attrib.get("id")
                if record_id:
                    record_ids.add(record_id)
                    record_ids.add(f"{addon.name}.{record_id}")
    return record_ids


def validate_access_group_refs(addons: list[Path]) -> None:
    known_groups = {
        "base.group_portal",
        "base.group_system",
        "base.group_user",
        "group_campus_administrator",
        "group_campus_lecturer",
    }
    known_groups.update(collect_xml_record_ids(addons))

    for addon in addons:
        for path in sorted(addon.glob("security/ir.model.access.csv")):
            with path.open(newline="", encoding="utf-8") as access_file:
                for row in csv.DictReader(access_file):
                    group_id = row.get("group_id:id", "")
                    if group_id and group_id not in known_groups:
                        raise ValueError(
                            f"{path.relative_to(ROOT)} references unknown group_id:id {group_id!r}"
                        )
            print(f"ACCESS OK {path.relative_to(ROOT)}")


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def collect_python_model_fields(addons: list[Path]) -> dict[str, set[str]]:
    models: dict[str, set[str]] = {}
    inherited_models: dict[str, set[str]] = {}

    for addon in addons:
        for path in sorted((addon / "models").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                model_name = None
                inherited_model = None
                fields = set()

                for stmt in class_node.body:
                    if not isinstance(stmt, ast.Assign):
                        continue

                    for target in stmt.targets:
                        if not isinstance(target, ast.Name):
                            continue

                        if target.id == "_name":
                            model_name = literal_string(stmt.value)
                        elif target.id == "_inherit":
                            inherited_model = literal_string(stmt.value)
                        elif isinstance(stmt.value, ast.Call):
                            func = stmt.value.func
                            if (
                                isinstance(func, ast.Attribute)
                                and isinstance(func.value, ast.Name)
                                and func.value.id == "fields"
                            ):
                                fields.add(target.id)

                if model_name:
                    models.setdefault(model_name, set()).update(fields)
                elif inherited_model:
                    inherited_models.setdefault(inherited_model, set()).update(fields)

    for model_name, fields in inherited_models.items():
        models.setdefault(model_name, set()).update(fields)

    return models


def validate_view_fields(addons: list[Path]) -> None:
    model_fields = collect_python_model_fields(addons)
    builtin_view_fields = {
        "activity_ids",
        "display_name",
        "message_follower_ids",
        "message_ids",
    }

    for addon in addons:
        for path in sorted(addon.glob("views/*.xml")):
            root = ET.parse(path).getroot()
            for record in root.findall(".//record[@model='ir.ui.view']"):
                model_field = record.find("./field[@name='model']")
                arch_field = record.find("./field[@name='arch']")
                model_name = model_field.text if model_field is not None else None
                if not model_name or arch_field is None or model_name not in model_fields:
                    continue

                valid_fields = model_fields[model_name] | builtin_view_fields

                def validate_arch_node(node: ET.Element, inside_relational_field: bool = False) -> None:
                    if node.tag == "field":
                        field_name = node.attrib.get("name")
                        if not inside_relational_field and field_name and field_name not in valid_fields:
                            raise ValueError(
                                f"{path.relative_to(ROOT)} view for {model_name} references "
                                f"unknown field {field_name!r}"
                            )
                        inside_relational_field = True

                    for child in node:
                        validate_arch_node(child, inside_relational_field)

                for arch_child in arch_field:
                    validate_arch_node(arch_child)
            print(f"VIEW OK {path.relative_to(ROOT)}")


def main() -> None:
    addons = iter_addons()
    if not addons:
        raise RuntimeError("No campus addons were found.")

    compile_python(addons)
    parse_xml(addons)
    validate_manifest_data(addons)
    validate_access_group_refs(addons)
    validate_view_fields(addons)


if __name__ == "__main__":
    main()
