from typing import Any, Dict, List

from utms.core.managers.base import BaseManager
from utms.core.models.elements.log_entry import LogEntry


class LogEntryManager(BaseManager[LogEntry]):
    def create(self, label: str, **kwargs) -> LogEntry:
        # We won't use this manager in the same way as entities,
        # but it needs to satisfy the base class contract.
        entry = LogEntry(context_name=label, attributes=kwargs.get("attributes", {}))
        self.add(label, entry)  # The key can just be the context name for now
        return entry

    def deserialize(self, data: Dict[str, Any]) -> None:
        pass

    def serialize(self) -> Dict[str, Any]:
        return {}
