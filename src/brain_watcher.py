"""
CONCODE Neural Brain — Real-Time Brain Watcher Daemon

Monitors source code changes in src/brain/, data/guilds.yaml, and src/service.py.
Automatically invokes AST skill detection and updates Obsidian notes & canvas graph.

Usage:
  python src/brain_watcher.py
"""

import sys
import time
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.obsidian_auto_mapper import ObsidianAutoMapper
from src.canvas_graph_builder import CanvasGraphBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-22s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("concode.brain_watcher")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = PROJECT_ROOT / "src" / "brain"
GUILDS_YAML = PROJECT_ROOT / "data" / "guilds.yaml"
SERVICE_FILE = PROJECT_ROOT / "src" / "service.py"


def get_latest_mtime() -> float:
    """Find maximum mtime across monitored files."""
    mtimes = []
    if GUILDS_YAML.exists():
        mtimes.append(GUILDS_YAML.stat().st_mtime)
    if SERVICE_FILE.exists():
        mtimes.append(SERVICE_FILE.stat().st_mtime)
    if BRAIN_DIR.exists():
        mtimes.extend([f.stat().st_mtime for f in BRAIN_DIR.glob("*.py")])
    return max(mtimes) if mtimes else 0.0


def start_watcher(interval: int = 3):
    """Run real-time watching loop."""
    logger.info("Starting Real-Time Brain Watcher Daemon...")
    logger.info("  Monitored: src/brain/*.py, data/guilds.yaml, src/service.py")

    mapper = ObsidianAutoMapper()
    builder = CanvasGraphBuilder()

    last_mtime = get_latest_mtime()

    try:
        while True:
            current_mtime = get_latest_mtime()
            if current_mtime > last_mtime:
                logger.info("Detected codebase update. Auto-mapping thinking skills & canvas graph...")
                mapper.sync_all()
                msg = builder.build_canvas()
                logger.info(f"{msg}")
                last_mtime = current_mtime
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Watcher daemon stopped.")


if __name__ == "__main__":
    start_watcher()
