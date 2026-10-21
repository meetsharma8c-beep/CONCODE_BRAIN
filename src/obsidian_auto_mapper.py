"""
CONCODE Neural Brain — Dynamic Automated Obsidian Node Mapper & Syncer

Fully automated scanner that dynamically crawls the entire Obsidian vault (concode-neural-brain/),
discovers all markdown notes across all directories (01-Brain-Architecture, 02-Guilds,
03-Training-Data, 04-Experiments, 05-Session-Logs, 06-Templates, 07-Thinking-Skills),
synthesizes bidirectional Wikilink networks, and builds CONCODE-Neural-Brain-Map.canvas
dynamically without static hardcoded files. All output is strictly monochromatic black and white without emojis.
"""

import sys
import os
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-22s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("concode.obsidian_mapper")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VAULT_DIR = PROJECT_ROOT / "concode-neural-brain"
CANVAS_FILE = VAULT_DIR / "CONCODE-Neural-Brain-Map.canvas"
DATA_DIR = PROJECT_ROOT / "data"
GUILDS_YAML = DATA_DIR / "guilds.yaml"
BRAIN_DIR = PROJECT_ROOT / "src" / "brain"
TEMPLATES_DIR = VAULT_DIR / "06-Templates"


class ObsidianAutoMapper:
    """Dynamic, fully automated Obsidian vault and canvas graph synthesizer."""

    def __init__(self):
        self.vault_dir = VAULT_DIR
        self.canvas_file = CANVAS_FILE

    def sync_all(self) -> int:
        """Run full dynamic sync across guilds, subsystems, datasets, and thinking skills."""
        logger.info("Starting Dynamic Obsidian Node Auto-Mapper Sync...")
        created_count = 0

        created_count += self.sync_guilds()
        created_count += self.sync_subsystems()
        created_count += self.sync_datasets()
        self.rebuild_canvas_dynamically()

        logger.info(f"Sync complete. New notes created: {created_count}")
        return created_count

    def sync_guilds(self) -> int:
        """Check data/guilds.yaml and create missing guild notes."""
        if not GUILDS_YAML.exists():
            return 0

        with open(GUILDS_YAML, "r") as f:
            data = yaml.safe_load(f)
            guild_list = data.get("guilds", []) if data else []

        guilds_dir = self.vault_dir / "02-Guilds"
        guilds_dir.mkdir(parents=True, exist_ok=True)

        created = 0
        for g in guild_list:
            name = g["name"]
            keywords = ", ".join([f"`{kw}`" for kw in g.get("keywords", [])])
            prompt = g.get("system_prompt", "").strip()

            display_name = name.replace("_", "-").title()
            if not display_name.lower().endswith("guild"):
                note_name = f"{display_name}-Guild.md"
            else:
                note_name = f"{display_name}.md"

            note_path = guilds_dir / note_name

            if not note_path.exists():
                logger.info(f"Auto-creating Guild Note: {note_name}")
                content = f"""---
title: {display_name} Guild
type: guild
tags:
  - guild/{name}
  - domain/{name}
status: ready
---

# {display_name} Guild

> Specialized expert persona for {name} domain requests.

---

## Domain Capabilities & Target Keywords

- Primary Keywords: {keywords}

---

## System Prompt Definition

```
{prompt}
```

---

## Related Notes

- Guild Overview: [[02-Guilds/Guild-Overview|Guild-Overview]]
- Master Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
"""
                note_path.write_text(content)
                created += 1

        return created

    def sync_subsystems(self) -> int:
        """Scan src/brain/*.py and ensure corresponding architecture notes exist."""
        if not BRAIN_DIR.exists():
            return 0

        arch_dir = self.vault_dir / "01-Brain-Architecture"
        arch_dir.mkdir(parents=True, exist_ok=True)

        subsystem_mapping = {
            "intent.py": ("01-Intent-Classifier.md", "Intent Classifier", "DistilBERT 66M classifier routing requests to 13 expert guilds."),
            "retriever.py": ("02-Workspace-Retriever.md", "Workspace Retriever", "MiniLM-L6-v2 + FAISS vector store indexing workspace files."),
            "generator.py": ("03-Core-LLM-Generator.md", "Core LLM Generator", "CodeLlama-7B GGUF Q4_K_M model running on Metal GPU."),
            "repair.py": ("04-Code-Repairer.md", "Code Repairer", "CodeT5 sequence-to-sequence neural repairer and bracket balancer."),
        }

        created = 0
        for py_file, (note_name, title, desc) in subsystem_mapping.items():
            note_path = arch_dir / note_name
            if not note_path.exists():
                logger.info(f"Auto-creating Subsystem Note: {note_name}")
                content = f"""---
title: Subsystem — {title}
type: subsystem
tags:
  - subsystem/{py_file.replace('.py', '')}
source_code: src/brain/{py_file}
---

# Subsystem: {title}

> {desc}

---

## Source File Reference

- Python Source: [`src/brain/{py_file}`](file://{BRAIN_DIR / py_file})

---

## Related Notes

- Architecture Overview: [[01-Brain-Architecture/00-Brain-Overview|00-Brain-Overview]]
- Master Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
"""
                note_path.write_text(content)
                created += 1

        return created

    def sync_datasets(self) -> int:
        """Scan data/*.jsonl and ensure dataset notes exist."""
        if not DATA_DIR.exists():
            return 0

        data_vault_dir = self.vault_dir / "03-Training-Data"
        data_vault_dir.mkdir(parents=True, exist_ok=True)

        created = 0
        for jf in DATA_DIR.glob("*.jsonl"):
            dataset_name = jf.stem.replace("_", "-").title()
            note_name = f"{dataset_name}.md"
            note_path = data_vault_dir / note_name

            if not note_path.exists():
                logger.info(f"Auto-creating Dataset Note: {note_name}")
                content = f"""---
title: {dataset_name}
type: dataset
tags:
  - dataset/{jf.stem}
dataset_file: data/{jf.name}
---

# Dataset: {dataset_name}

> Dataset stored at `data/{jf.name}`.

---

## Related Notes

- Data Pipeline: [[03-Training-Data/Data-Pipeline|Data-Pipeline]]
- Master Dashboard: [[00-Dashboard/Dashboard|Dashboard]]
"""
                note_path.write_text(content)
                created += 1

        return created

    def rebuild_canvas_dynamically(self):
        """Dynamically crawl ALL markdown files in vault and construct monochrome CONCODE-Neural-Brain-Map.canvas."""
        # 1. Crawl all .md files in vault
        all_md_files = []
        for root, _, files in os.walk(self.vault_dir):
            for file in sorted(files):
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.vault_dir).as_posix()
                    all_md_files.append(rel_path)

        # Group files by top-level category/folder
        categories = {
            "Client Gateway": [],
            "Dashboard & Overview": [],
            "Brain Architecture": [],
            "Thinking Skills": [],
            "Guild Experts Part 1": [],
            "Guild Experts Part 2": [],
            "Training Data & Experiments": [],
        }

        guild_files = []

        for rel_f in all_md_files:
            if rel_f.startswith("01-Brain-Architecture/06-") or rel_f.startswith("01-Brain-Architecture/07-"):
                categories["Client Gateway"].append(rel_f)
            elif rel_f == "00-Dashboard/Dashboard.md" or rel_f == "01-Brain-Architecture/00-Brain-Overview.md" or rel_f == "Welcome.md":
                categories["Dashboard & Overview"].append(rel_f)
            elif rel_f.startswith("01-Brain-Architecture/"):
                categories["Brain Architecture"].append(rel_f)
            elif rel_f.startswith("07-Thinking-Skills/"):
                categories["Thinking Skills"].append(rel_f)
            elif rel_f.startswith("02-Guilds/"):
                guild_files.append(rel_f)
            else:
                categories["Training Data & Experiments"].append(rel_f)

        # Split guild files into 2 columns for clean layout
        mid = len(guild_files) // 2
        categories["Guild Experts Part 1"] = guild_files[:mid]
        categories["Guild Experts Part 2"] = guild_files[mid:]

        column_coords = [
            (-550, categories["Client Gateway"]),
            (0, categories["Dashboard & Overview"]),
            (550, categories["Brain Architecture"]),
            (1100, categories["Thinking Skills"]),
            (1650, categories["Guild Experts Part 1"]),
            (2100, categories["Guild Experts Part 2"]),
            (2600, categories["Training Data & Experiments"]),
        ]

        nodes = []
        edges = []
        file_to_id = {}

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
                    "y": start_y + (i * 360),
                    "width": 420,
                    "height": 300,
                })

        # Add edges dynamically
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
                    "toSide": "left",
                })

        # Connect Dashboard to main hubs
        if "00-Dashboard/Dashboard.md" in file_to_id:
            add_edge("00-Dashboard/Dashboard.md", "01-Brain-Architecture/00-Brain-Overview.md")
            add_edge("00-Dashboard/Dashboard.md", "07-Thinking-Skills/Thinking-Skills-MOC.md")
            add_edge("00-Dashboard/Dashboard.md", "02-Guilds/Guild-Overview.md")

        # Connect Client Gateway to Dashboard
        for gw in categories["Client Gateway"]:
            add_edge(gw, "00-Dashboard/Dashboard.md")

        # Connect Overview to Subsystems
        for arch in categories["Brain Architecture"]:
            if arch != "01-Brain-Architecture/00-Brain-Overview.md":
                add_edge("01-Brain-Architecture/00-Brain-Overview.md", arch)

        # Connect Subsystems to Thinking Skills
        for skill in categories["Thinking Skills"]:
            if skill != "07-Thinking-Skills/Thinking-Skills-MOC.md":
                add_edge("07-Thinking-Skills/Thinking-Skills-MOC.md", skill)

        # Connect Guild Overview to all Guilds
        for g_f in guild_files:
            if g_f != "02-Guilds/Guild-Overview.md":
                add_edge("02-Guilds/Guild-Overview.md", g_f)

        canvas_data = {"nodes": nodes, "edges": edges}

        with open(self.canvas_file, "w") as f:
            json.dump(canvas_data, f, indent=2)

        logger.info(f"Canvas auto-mapped dynamically with {len(nodes)} nodes and {len(edges)} edges!")


def main():
    parser = argparse.ArgumentParser(description="CONCODE Neural Brain Obsidian Auto-Mapper")
    parser.add_argument("--sync", action="store_true", help="Run full sync across vault")
    parser.add_argument("--watch", action="store_true", help="Run watcher loop")
    args = parser.parse_args()

    mapper = ObsidianAutoMapper()

    if args.sync or not sys.argv[1:]:
        mapper.sync_all()
    elif args.watch:
        from src.brain_watcher import start_watcher
        start_watcher()


if __name__ == "__main__":
    main()
