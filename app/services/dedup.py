from threading import Lock


class MessageDeduplicator:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._lock = Lock()

    def is_duplicate(self, message_key: str) -> bool:
        with self._lock:
            if message_key in self._seen:
                return True
            self._seen.add(message_key)
            return False
