"""Session recorder storing replay-ready JSONL telemetry streams."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from core.telemetry_parser import TelemetryPoint

class SessionRecorder:
    def __init__(self, root: Path | str = "sessions") -> None:
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.path: Path | None = None
        self._fh = None

    @property
    def active(self) -> bool:
        return self._fh is not None

    def start(self) -> Path:
        self.stop()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.path = self.root / f"flight_{stamp}.jsonl"
        self._fh = self.path.open("w", encoding="utf-8")
        return self.path

    def record(self, point: TelemetryPoint, metadata: dict | None = None) -> None:
        if not self._fh:
            return
        row = point.as_dict(); row["metadata"] = metadata or {}
        self._fh.write(json.dumps(row) + "\n"); self._fh.flush()

    def stop(self) -> Path | None:
        if self._fh:
            self._fh.close(); self._fh = None
        return self.path
