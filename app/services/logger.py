import json
from pathlib import Path
from threading import Lock
from typing import Any


class InteractionLogger:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path
        self._lock = Lock()
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, item: dict[str, Any]) -> None:
        line = json.dumps(item, ensure_ascii=False)
        with self._lock:
            with self._output_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
