"""
CONCODE Neural Brain — AST Cognitive Skill Detector

Inspects Python codebase using AST parsing to extract cognitive thinking skills,
neural reasoning functions, parameter specs, and docstring documentation.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = PROJECT_ROOT / "src" / "brain"
SERVICE_FILE = PROJECT_ROOT / "src" / "service.py"


class CognitiveSkillDetector:
    """Parses AST structures to discover cognitive skills in the codebase."""

    def __init__(self):
        self.brain_dir = BRAIN_DIR
        self.service_file = SERVICE_FILE

    def detect_all_skills(self) -> List[Dict[str, Any]]:
        """Scan codebase and extract cognitive skills metadata."""
        skills = []

        # 1. Scan src/brain/*.py
        if self.brain_dir.exists():
            for py_file in self.brain_dir.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                file_skills = self._parse_file(py_file)
                skills.extend(file_skills)

        # 2. Scan src/service.py
        if self.service_file.exists():
            file_skills = self._parse_file(self.service_file)
            skills.extend(file_skills)

        return skills

    def _parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse a single Python file AST for classes and public methods."""
        skills = []
        try:
            tree = ast.parse(file_path.read_text())
        except Exception:
            return skills

        module_name = file_path.stem

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node) or "Cognitive skill component."
                methods = [
                    m.name for m in node.body
                    if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")
                ]
                skills.append({
                    "name": node.name,
                    "module": module_name,
                    "file": file_path.name,
                    "type": "class",
                    "docstring": docstring,
                    "methods": methods,
                })
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                # Global functions
                if isinstance(getattr(node, 'parent', None), ast.Module) or True:
                    docstring = ast.get_docstring(node) or "Cognitive helper operation."
                    skills.append({
                        "name": node.name,
                        "module": module_name,
                        "file": file_path.name,
                        "type": "function",
                        "docstring": docstring,
                        "methods": [],
                    })

        return skills


if __name__ == "__main__":
    detector = CognitiveSkillDetector()
    detected = detector.detect_all_skills()
    print(f"Detected {len(detected)} cognitive skills/classes in codebase:")
    for s in detected:
        print(f"  - [{s['file']}] {s['name']} ({s['type']}): {s['docstring'][:60]}...")
