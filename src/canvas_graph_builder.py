"""
CONCODE Neural Brain — Monochrome Canvas Graph Builder

Generates and rebuilds CONCODE-Neural-Brain-Map.canvas using a 6-column
auto-layout grid algorithm with strict black-and-white monochromatic styling (no colors).
"""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VAULT_DIR = PROJECT_ROOT / "concode-neural-brain"
CANVAS_FILE = VAULT_DIR / "CONCODE-Neural-Brain-Map.canvas"


class CanvasGraphBuilder:
    """Builds and lays out CONCODE-Neural-Brain-Map.canvas in 6 monochrome columns."""

    def __init__(self):
        self.vault_dir = VAULT_DIR
        self.canvas_file = CANVAS_FILE

    def build_canvas(self) -> str:
        """Rebuild canvas layout from vault files with black and white styling."""
        nodes = []
        edges = []

        # ── Column Definitions (Monochrome) ───────────────────────────
        c0_files = [
            "01-Brain-Architecture/07-Client-Integration.md",
            "01-Brain-Architecture/06-FastAPI-Service.md",
        ]

        c1_files = [
            "00-Dashboard/Dashboard.md",
            "01-Brain-Architecture/00-Brain-Overview.md",
            "Welcome.md",
        ]

        c2_files = [
            "01-Brain-Architecture/01-Intent-Classifier.md",
            "01-Brain-Architecture/02-Workspace-Retriever.md",
            "01-Brain-Architecture/03-Core-LLM-Generator.md",
            "01-Brain-Architecture/04-Code-Repairer.md",
            "01-Brain-Architecture/05-Session-Memory.md",
        ]

        c3_files = [
            "07-Thinking-Skills/Thinking-Skills-MOC.md",
            "07-Thinking-Skills/01-Intent-Classification-Routing.md",
            "07-Thinking-Skills/02-Dense-Vector-Similarity-Search.md",
            "07-Thinking-Skills/03-Autoregressive-Code-Generation.md",
            "07-Thinking-Skills/04-Seq2Seq-Neural-Code-Repair.md",
            "07-Thinking-Skills/05-Regex-Bracket-Typo-Fixing.md",
            "07-Thinking-Skills/06-Multi-Turn-Session-Memory.md",
            "07-Thinking-Skills/07-QLoRA-Adapter-Pathway-Modulation.md",
            "07-Thinking-Skills/08-Prompt-Deconstruction-And-Tagging.md",
            "07-Thinking-Skills/09-Sub-Graph-Execution-Orchestration.md",
            "07-Thinking-Skills/10-Context-Window-Pruning-Strategy.md",
            "07-Thinking-Skills/11-Confidence-Scoring-And-Fallback-Routing.md",
            "07-Thinking-Skills/12-AST-Syntax-Tree-Balancing.md",
        ]

        c4_files = [
            "02-Guilds/Guild-Overview.md",
            "02-Guilds/Debugger-Guild.md",
            "02-Guilds/WebGL-Guild.md",
            "02-Guilds/AI-ML-Guild.md",
            "02-Guilds/QA-Guild.md",
            "02-Guilds/Security-Guild.md",
            "02-Guilds/Performance-Guild.md",
            "02-Guilds/Database-Guild.md",
            "02-Guilds/UI-UX-Guild.md",
            "02-Guilds/DevOps-Guild.md",
            "02-Guilds/API-Guild.md",
            "02-Guilds/Fullstack-Guild.md",
            "02-Guilds/Mobile-Guild.md",
            "02-Guilds/Blockchain-Guild.md",
        ]

        c5_files = [
            "03-Training-Data/Data-Pipeline.md",
            "03-Training-Data/Intent-Dataset.md",
            "03-Training-Data/Multi-Guild-Train.md",
            "03-Training-Data/Repair-Dataset.md",
            "04-Experiments/QLoRA-FineTuning.md",
            "04-Experiments/GGUF-Quantization.md",
            "05-Session-Logs/Session-Tracking.md",
        ]

        columns = [
            (-550, c0_files),
            (0, c1_files),
            (550, c2_files),
            (1100, c3_files),
            (1650, c4_files[:7]),
            (2100, c4_files[7:]),
            (2600, c5_files),
        ]

        file_to_id = {}

        categories = {
            "Client Gateway": [],
            "Dashboard & Overview": [],
            "Brain Architecture": [],
            "Thinking Skills MOC": [],
            "Guilds": [],
            "Infrastructure & Experiments": []
        }

        for root, dirs, files in os.walk(self.vault_dir):
            for f in sorted(files):
                if f.endswith(".md"):
                    rel_p = os.path.relpath(os.path.join(root, f), self.vault_dir)
                    if rel_p.startswith("01-Brain-Architecture/06-") or rel_p.startswith("01-Brain-Architecture/07-"):
                        categories["Client Gateway"].append(rel_p)
                    elif rel_p in ["00-Dashboard/Dashboard.md", "01-Brain-Architecture/00-Brain-Overview.md", "Welcome.md"]:
                        categories["Dashboard & Overview"].append(rel_p)
                    elif rel_p.startswith("01-Brain-Architecture/"):
                        categories["Brain Architecture"].append(rel_p)
                    elif rel_p == "07-Thinking-Skills/Thinking-Skills-MOC.md":
                        categories["Thinking Skills MOC"].append(rel_p)
                    elif rel_p.startswith("02-Guilds/"):
                        categories["Guilds"].append(rel_p)
                    else:
                        categories["Infrastructure & Experiments"].append(rel_p)

        column_coords = [
            (-600, categories["Client Gateway"]),
            (0, categories["Dashboard & Overview"]),
            (600, categories["Brain Architecture"]),
            (1200, categories["Thinking Skills MOC"]),
            (1800, categories["Guilds"][:7]),
            (2400, categories["Guilds"][7:]),
            (3000, categories["Infrastructure & Experiments"]),
        ]

        for col_x, files_list in column_coords:
            start_y = -300
            for i, rel_path in enumerate(files_list):
                node_id = f"node_{rel_path.replace('/', '_').replace('.', '_').replace('-', '_')}"
                file_to_id[rel_path] = node_id
                nodes.append({
                    "id": node_id,
                    "type": "file",
                    "file": rel_path,
                    "x": col_x,
                    "y": start_y + (i * 340),
                    "width": 450,
                    "height": 280
                })

        edge_counter = 0

        def add_edge(from_f, to_f):
            nonlocal edge_counter
            from_id = file_to_id.get(from_f)
            to_id = file_to_id.get(to_f)
            if from_id and to_id:
                edge_counter += 1
                edges.append({
                    "id": f"edge_{edge_counter}",
                    "fromNode": from_id,
                    "fromSide": "right",
                    "toNode": to_id,
                    "toSide": "left"
                })

        if "00-Dashboard/Dashboard.md" in file_to_id:
            add_edge("00-Dashboard/Dashboard.md", "01-Brain-Architecture/00-Brain-Overview.md")
            add_edge("00-Dashboard/Dashboard.md", "07-Thinking-Skills/Thinking-Skills-MOC.md")
            add_edge("00-Dashboard/Dashboard.md", "02-Guilds/Guild-Overview.md")

        for gw in categories["Client Gateway"]:
            add_edge(gw, "00-Dashboard/Dashboard.md")

        for arch in categories["Brain Architecture"]:
            if arch != "01-Brain-Architecture/00-Brain-Overview.md":
                add_edge("01-Brain-Architecture/00-Brain-Overview.md", arch)

        for g_f in categories["Guilds"]:
            if g_f != "02-Guilds/Guild-Overview.md":
                add_edge("02-Guilds/Guild-Overview.md", g_f)

        canvas_data = {"nodes": nodes, "edges": edges}

        with open(self.canvas_file, "w") as f:
            json.dump(canvas_data, f, indent=2)

        return f"Successfully generated black and white CONCODE-Neural-Brain-Map.canvas with {len(nodes)} nodes and {len(edges)} edges."


if __name__ == "__main__":
    builder = CanvasGraphBuilder()
    msg = builder.build_canvas()
    print(msg)
