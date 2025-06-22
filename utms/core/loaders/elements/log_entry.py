from typing import Any, Dict, List

from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.log_entry import LogEntryManager
from utms.core.models.elements.log_entry import LogEntry
from utms.utms_types import HyNode


# The loader's job is to turn HyNodes into LogEntry objects
class LogEntryLoader(ComponentLoader[LogEntry, LogEntryManager]):
    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        defs = {}
        for i, node in enumerate(nodes):
            if node.type == "log-context":
                # Use index as a unique key for the definition
                key = f"entry-{i}"
                defs[key] = {
                    "name": node.value,
                    "attributes_typed": getattr(node, "attributes_typed", {}),
                }
        return defs

    def create_object(self, label: str, properties: Dict[str, Any]) -> LogEntry:
        entry = LogEntry(
            context_name=properties.get("name"), attributes=properties.get("attributes_typed")
        )
        # We don't need to add it to the manager for this use case,
        # we will just return the list of created objects.
        return entry
