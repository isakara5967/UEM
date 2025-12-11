#!/usr/bin/env python3
"""
scripts/generate_docs.py

Proje otomatik dokumantasyon uretici.
Tum modulleri tarar, class/function/dataclass cikarir.

Kullanim:
    python scripts/generate_docs.py

Urettigi dosyalar:
    - docs/PROJECT_STRUCTURE.md
    - docs/DATA_TYPES.md
    - docs/API_REFERENCE.md

UEM v2 - Auto-documentation Generator.
"""

import ast
import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime


@dataclass
class ClassInfo:
    """Bir class hakkinda bilgi."""
    name: str
    bases: List[str]
    docstring: Optional[str]
    methods: List[str]
    is_dataclass: bool = False
    is_enum: bool = False
    enum_values: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class FunctionInfo:
    """Bir fonksiyon hakkinda bilgi."""
    name: str
    args: List[str]
    docstring: Optional[str]
    returns: Optional[str]
    is_async: bool = False
    line_number: int = 0


@dataclass
class ModuleInfo:
    """Bir Python modulu hakkinda bilgi."""
    path: str
    relative_path: str
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    imports: List[str]
    docstring: Optional[str]


def analyze_module(filepath: Path, root: Path) -> Optional[ModuleInfo]:
    """
    Tek bir Python dosyasini analiz et.

    Args:
        filepath: Dosya yolu
        root: Proje root dizini

    Returns:
        ModuleInfo veya None (hata durumunda)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        tree = ast.parse(content, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"  [!] Parse error in {filepath}: {e}")
        return None

    classes: List[ClassInfo] = []
    functions: List[FunctionInfo] = []
    imports: List[str] = []
    module_docstring = ast.get_docstring(tree)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            class_info = _analyze_class(node)
            classes.append(class_info)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_info = _analyze_function(node)
            functions.append(func_info)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")

    relative_path = str(filepath.relative_to(root))

    return ModuleInfo(
        path=str(filepath),
        relative_path=relative_path,
        classes=classes,
        functions=functions,
        imports=imports,
        docstring=module_docstring
    )


def _analyze_class(node: ast.ClassDef) -> ClassInfo:
    """Class node'unu analiz et."""
    bases = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            bases.append(base.id)
        elif isinstance(base, ast.Attribute):
            bases.append(f"{_get_attr_name(base)}")

    # Dataclass veya Enum mu?
    is_dataclass = False
    is_enum = False

    for base in bases:
        if "Enum" in base:
            is_enum = True

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
            is_dataclass = True
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name) and decorator.func.id == "dataclass":
                is_dataclass = True

    # Methods
    methods = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not item.name.startswith("_") or item.name in ["__init__", "__post_init__"]:
                methods.append(item.name)

    # Enum values
    enum_values = []
    if is_enum:
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        enum_values.append(target.id)

    return ClassInfo(
        name=node.name,
        bases=bases,
        docstring=ast.get_docstring(node),
        methods=methods,
        is_dataclass=is_dataclass,
        is_enum=is_enum,
        enum_values=enum_values,
        line_number=node.lineno
    )


def _analyze_function(node) -> FunctionInfo:
    """Function node'unu analiz et."""
    args = []
    for arg in node.args.args:
        args.append(arg.arg)

    returns = None
    if node.returns:
        returns = _get_annotation_str(node.returns)

    return FunctionInfo(
        name=node.name,
        args=args,
        docstring=ast.get_docstring(node),
        returns=returns,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        line_number=node.lineno
    )


def _get_attr_name(node: ast.Attribute) -> str:
    """Attribute node'undan tam adi al."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _get_annotation_str(node) -> str:
    """Type annotation'i string'e cevir."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return str(node.value)
    elif isinstance(node, ast.Subscript):
        return f"{_get_annotation_str(node.value)}[...]"
    elif isinstance(node, ast.Attribute):
        return _get_attr_name(node)
    return "..."


def analyze_project(root: Path, directories: List[str]) -> Dict[str, ModuleInfo]:
    """
    Proje dizinlerini tara.

    Args:
        root: Proje root
        directories: Taranacak dizinler

    Returns:
        {relative_path: ModuleInfo} sozlugu
    """
    modules: Dict[str, ModuleInfo] = {}

    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            print(f"[!] Directory not found: {dir_path}")
            continue

        print(f"[*] Scanning {dir_name}/...")

        for py_file in dir_path.rglob("*.py"):
            # __pycache__ atla
            if "__pycache__" in str(py_file):
                continue

            info = analyze_module(py_file, root)
            if info:
                modules[info.relative_path] = info

    print(f"[+] Analyzed {len(modules)} modules")
    return modules


def generate_project_structure_md(modules: Dict[str, ModuleInfo], root: Path) -> str:
    """docs/PROJECT_STRUCTURE.md icerigi uret."""
    lines = []

    lines.append("# UEM v2 Project Structure")
    lines.append("")
    lines.append(f"_Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")

    # Module istatistikleri
    total_classes = sum(len(m.classes) for m in modules.values())
    total_functions = sum(len(m.functions) for m in modules.values())
    dataclasses = sum(1 for m in modules.values() for c in m.classes if c.is_dataclass)
    enums = sum(1 for m in modules.values() for c in m.classes if c.is_enum)

    lines.append("## Overview")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Modules | {len(modules)} |")
    lines.append(f"| Total Classes | {total_classes} |")
    lines.append(f"| Dataclasses | {dataclasses} |")
    lines.append(f"| Enums | {enums} |")
    lines.append(f"| Functions | {total_functions} |")
    lines.append("")

    # Dizin yapisi (gruplu)
    lines.append("## Directory Tree")
    lines.append("")
    lines.append("```")

    # Dizinleri grupla
    dirs: Dict[str, List[str]] = {}
    for path in sorted(modules.keys()):
        parts = path.split("/")
        if len(parts) > 1:
            top_dir = parts[0]
            if top_dir not in dirs:
                dirs[top_dir] = []
            dirs[top_dir].append(path)

    for top_dir in sorted(dirs.keys()):
        lines.append(f"{top_dir}/")
        for path in sorted(dirs[top_dir]):
            indent = "  " * (path.count("/"))
            filename = path.split("/")[-1]
            lines.append(f"{indent}{filename}")

    lines.append("```")
    lines.append("")

    # Her dizin icin detay
    lines.append("## Module Details")
    lines.append("")

    current_top = ""
    for path in sorted(modules.keys()):
        module = modules[path]
        top_dir = path.split("/")[0]

        if top_dir != current_top:
            current_top = top_dir
            lines.append(f"### {top_dir}/")
            lines.append("")

        # Module header
        lines.append(f"#### `{path}`")
        lines.append("")

        if module.docstring:
            # İlk satiri al
            first_line = module.docstring.split("\n")[0].strip()
            if first_line:
                lines.append(f"_{first_line}_")
                lines.append("")

        # Classes
        if module.classes:
            lines.append("**Classes:**")
            for cls in module.classes:
                marker = ""
                if cls.is_dataclass:
                    marker = " (dataclass)"
                elif cls.is_enum:
                    marker = " (enum)"
                lines.append(f"- `{cls.name}`{marker}")
            lines.append("")

        # Functions
        if module.functions:
            public_funcs = [f for f in module.functions if not f.name.startswith("_")]
            if public_funcs:
                lines.append("**Functions:**")
                for func in public_funcs[:10]:  # Max 10
                    lines.append(f"- `{func.name}()`")
                if len(public_funcs) > 10:
                    lines.append(f"- _... and {len(public_funcs) - 10} more_")
                lines.append("")

    return "\n".join(lines)


def generate_data_types_md(modules: Dict[str, ModuleInfo]) -> str:
    """docs/DATA_TYPES.md icerigi uret."""
    lines = []

    lines.append("# UEM v2 Data Types Reference")
    lines.append("")
    lines.append(f"_Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")
    lines.append("Complete reference of all dataclasses and enums in the UEM v2 codebase.")
    lines.append("")

    # Dataclass'lari topla
    dataclasses: List[tuple] = []
    enums: List[tuple] = []

    for path, module in modules.items():
        for cls in module.classes:
            if cls.is_dataclass:
                dataclasses.append((path, cls))
            elif cls.is_enum:
                enums.append((path, cls))

    # Enums
    lines.append("## Enums")
    lines.append("")
    lines.append(f"Total: {len(enums)} enums")
    lines.append("")

    lines.append("| Enum | File | Values |")
    lines.append("|------|------|--------|")

    for path, cls in sorted(enums, key=lambda x: x[1].name):
        values = ", ".join(cls.enum_values[:5])
        if len(cls.enum_values) > 5:
            values += f", ... (+{len(cls.enum_values) - 5})"
        lines.append(f"| `{cls.name}` | {path} | {values} |")

    lines.append("")

    # Detailed Enums
    lines.append("### Enum Details")
    lines.append("")

    for path, cls in sorted(enums, key=lambda x: x[1].name):
        lines.append(f"#### `{cls.name}`")
        lines.append("")
        lines.append(f"**File:** `{path}:{cls.line_number}`")
        lines.append("")

        if cls.docstring:
            first_para = cls.docstring.split("\n\n")[0]
            lines.append(f"_{first_para}_")
            lines.append("")

        lines.append("**Values:**")
        for value in cls.enum_values:
            lines.append(f"- `{value}`")
        lines.append("")

    # Dataclasses
    lines.append("## Dataclasses")
    lines.append("")
    lines.append(f"Total: {len(dataclasses)} dataclasses")
    lines.append("")

    lines.append("| Dataclass | File | Purpose |")
    lines.append("|-----------|------|---------|")

    for path, cls in sorted(dataclasses, key=lambda x: x[1].name):
        purpose = ""
        if cls.docstring:
            purpose = cls.docstring.split("\n")[0][:50]
            if len(cls.docstring.split("\n")[0]) > 50:
                purpose += "..."
        lines.append(f"| `{cls.name}` | {path} | {purpose} |")

    lines.append("")

    # Detailed Dataclasses
    lines.append("### Dataclass Details")
    lines.append("")

    for path, cls in sorted(dataclasses, key=lambda x: x[1].name):
        lines.append(f"#### `{cls.name}`")
        lines.append("")
        lines.append(f"**File:** `{path}:{cls.line_number}`")
        lines.append("")

        if cls.docstring:
            # İlk paragraf
            paragraphs = cls.docstring.split("\n\n")
            if paragraphs:
                lines.append(f"_{paragraphs[0]}_")
                lines.append("")

        # Methods
        public_methods = [m for m in cls.methods if not m.startswith("_") or m == "__post_init__"]
        if public_methods:
            lines.append("**Methods:**")
            for method in public_methods:
                lines.append(f"- `{method}()`")
            lines.append("")

    return "\n".join(lines)


def generate_api_reference_md(modules: Dict[str, ModuleInfo]) -> str:
    """docs/API_REFERENCE.md icerigi uret."""
    lines = []

    lines.append("# UEM v2 API Reference")
    lines.append("")
    lines.append(f"_Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")
    lines.append("Function and class API reference for UEM v2.")
    lines.append("")

    # Moduller bazinda grupla
    core_modules = {p: m for p, m in modules.items() if p.startswith("core/")}
    engine_modules = {p: m for p, m in modules.items() if p.startswith("engine/")}
    interface_modules = {p: m for p, m in modules.items() if p.startswith("interface/")}
    meta_modules = {p: m for p, m in modules.items() if p.startswith("meta/")}

    def _write_module_section(title: str, mods: Dict[str, ModuleInfo]):
        lines.append(f"## {title}")
        lines.append("")

        for path in sorted(mods.keys()):
            module = mods[path]

            # Public classes ve functions
            public_classes = [c for c in module.classes if not c.name.startswith("_")]
            public_funcs = [f for f in module.functions if not f.name.startswith("_")]

            if not public_classes and not public_funcs:
                continue

            lines.append(f"### `{path}`")
            lines.append("")

            # Classes
            for cls in public_classes:
                marker = ""
                if cls.is_dataclass:
                    marker = " `@dataclass`"
                elif cls.is_enum:
                    marker = " `(Enum)`"

                lines.append(f"#### class `{cls.name}`{marker}")
                lines.append("")

                if cls.docstring:
                    first_line = cls.docstring.split("\n")[0]
                    lines.append(f"_{first_line}_")
                    lines.append("")

                # Public methods
                public_methods = [m for m in cls.methods
                                 if not m.startswith("_") or m in ["__init__", "__post_init__"]]
                if public_methods:
                    lines.append("Methods:")
                    for method in public_methods:
                        lines.append(f"- `{method}()`")
                    lines.append("")

            # Functions
            for func in public_funcs:
                args_str = ", ".join(func.args[:3])
                if len(func.args) > 3:
                    args_str += ", ..."

                ret_str = f" -> {func.returns}" if func.returns else ""
                async_mark = "async " if func.is_async else ""

                lines.append(f"#### `{async_mark}{func.name}({args_str}){ret_str}`")
                lines.append("")

                if func.docstring:
                    first_line = func.docstring.split("\n")[0]
                    lines.append(f"_{first_line}_")
                    lines.append("")

    _write_module_section("Core Modules", core_modules)
    _write_module_section("Engine Modules", engine_modules)
    _write_module_section("Meta Modules", meta_modules)
    _write_module_section("Interface Modules", interface_modules)

    return "\n".join(lines)


def main():
    """Ana giris noktasi."""
    print("=" * 60)
    print("  UEM v2 Auto-Documentation Generator")
    print("=" * 60)
    print()

    # Root dizini bul
    script_dir = Path(__file__).parent
    root = script_dir.parent

    print(f"[*] Project root: {root}")

    # Taranacak dizinler
    directories = [
        "core",
        "engine",
        "interface",
        "meta",
        "foundation",
        "infra",
        "scripts",
    ]

    # Analiz et
    modules = analyze_project(root, directories)

    if not modules:
        print("[!] No modules found!")
        sys.exit(1)

    # docs/ dizini olustur
    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)

    # PROJECT_STRUCTURE.md
    print("\n[*] Generating docs/PROJECT_STRUCTURE.md...")
    content = generate_project_structure_md(modules, root)
    (docs_dir / "PROJECT_STRUCTURE.md").write_text(content, encoding="utf-8")
    print(f"    -> {len(content)} bytes written")

    # DATA_TYPES.md
    print("[*] Generating docs/DATA_TYPES.md...")
    content = generate_data_types_md(modules)
    (docs_dir / "DATA_TYPES.md").write_text(content, encoding="utf-8")
    print(f"    -> {len(content)} bytes written")

    # API_REFERENCE.md
    print("[*] Generating docs/API_REFERENCE.md...")
    content = generate_api_reference_md(modules)
    (docs_dir / "API_REFERENCE.md").write_text(content, encoding="utf-8")
    print(f"    -> {len(content)} bytes written")

    print()
    print("[+] Documentation generation complete!")
    print()
    print("Generated files:")
    print("  - docs/PROJECT_STRUCTURE.md")
    print("  - docs/DATA_TYPES.md")
    print("  - docs/API_REFERENCE.md")


if __name__ == "__main__":
    main()
