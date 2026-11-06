"""Run the bundled CLI without an editable install; PyYAML is still required."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skilltrim.cli import main

raise SystemExit(main())
