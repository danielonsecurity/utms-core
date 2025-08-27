import os
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

import hy

from utms.core.components.base import SystemComponent
from utms.core.hy.ast import HyAST
from utms.core.hy.resolvers.elements.variable import VariableResolver
from utms.core.loaders.base import LoaderContext
from utms.core.loaders.elements.log_entry import LogEntryLoader
from utms.core.managers.elements.log_entry import LogEntryManager
from utms.core.models.elements.log_entry import LogEntry
from utms.core.plugins.elements.log_context import LogContextNodePlugin
from utms.core.services.dynamic import DynamicResolutionService
from utms.utms_types import HyNode
from utms.utms_types.field.types import TypedValue


class DailyLogComponent(SystemComponent):
    """
    Manages daily log files containing context switches and other timed events.
    """

    def __init__(self, config_dir: str, component_manager=None):
        super().__init__(config_dir, component_manager)
        self._ast_manager = HyAST()
        config_component = self.get_component("config")
        if not config_component.is_loaded(): config_component.load()
        active_user_config = config_component.get_config("active-user")

        self._log_dir = None
        if active_user_config and (active_user := active_user_config.get_value()):
            user_root = os.path.join(self._config_dir, "users", active_user)
            self._log_dir = os.path.join(user_root, "daily_logs")
        else:
            self.logger.error("DailyLogComponent cannot operate without an active user.")
        self._loader = LogEntryLoader(LogEntryManager())
        self._resolver = VariableResolver()
        self._dynamic_service = DynamicResolutionService(resolver=self._resolver)
        self._formatter_plugin = LogContextNodePlugin()

    def load(self) -> None:
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)
        self._loaded = True
        self.logger.info("DailyLogComponent initialized. Logs will be loaded on demand.")

    def get_log_for_day(self, log_date: date) -> List[LogEntry]:
        """
        Reads the log file for a specific date, resolves any dynamic values,
        and returns a list of resolved LogEntry objects.
        """
        filename = f"{log_date.isoformat()}.hy"
        filepath = os.path.join(self._log_dir, filename)

        if not os.path.exists(filepath):
            return []

        try:
            nodes = self._ast_manager.parse_file(filepath)
            raw_log_entries = list(
                self._loader.process(nodes, LoaderContext(config_dir=self._config_dir)).values()
            )

            variables_component = self.get_component("variables")
            eval_context = variables_component.get_all_values() if variables_component else {}
            if "datetime" not in eval_context:
                from datetime import datetime

                eval_context["datetime"] = datetime

            resolved_entries = []
            for entry in raw_log_entries:
                resolved_attrs = {}
                for attr_name, tv in entry.attributes.items():
                    if tv.is_dynamic:
                        resolved_raw, _ = self._dynamic_service.evaluate(
                            expression=tv.value, 
                            context=eval_context,
                            component_type="daily_log",
                            component_label=f"{log_date.isoformat()}:{entry.context_name}",
                            attribute=attr_name,
                        )
                        unwrapped_val = resolved_raw
                        while (
                            isinstance(unwrapped_val, hy.models.Expression)
                            and len(unwrapped_val) == 2
                            and str(unwrapped_val[0]) == "quote"
                        ):
                            unwrapped_val = unwrapped_val[1]
                        if isinstance(unwrapped_val, hy.models.Object):
                            try:
                                resolved_py_val = hy.eval(unwrapped_val, locals=eval_context)
                            except Exception as eval_err:
                                self.logger.error(
                                    f"Final hy.eval failed for {unwrapped_val}: {eval_err}"
                                )
                                resolved_py_val = None
                        else:
                            resolved_py_val = unwrapped_val
                        resolved_attrs[attr_name] = TypedValue(
                            value=resolved_py_val,
                            field_type=tv.field_type,
                            is_dynamic=tv.is_dynamic,
                            original=tv.original,
                        )
                    else:
                        resolved_attrs[attr_name] = tv

                resolved_entries.append(
                    LogEntry(context_name=entry.context_name, attributes=resolved_attrs)
                )

            return resolved_entries

        except Exception as e:
            self.logger.error(f"Error processing daily log file '{filepath}': {e}", exc_info=True)
            return []

    def switch_context(self, new_context_name: str, color: Optional[str] = None) -> List[LogEntry]:
        """
        Ends the current ongoing context and starts a new one.
        This is the core logic for the context switcher widget.
        """
        now_utc = datetime.now(timezone.utc)
        today_date = now_utc.date()

        self._end_latest_ongoing_context(end_time=now_utc)
        todays_entries = self._load_unresolved_log_entries(today_date)
        new_entry = self._create_new_log_entry(
            context_name=new_context_name, start_time=now_utc, color=color
        )
        todays_entries.append(new_entry)
        self._save_log_file(today_date, todays_entries)

        self.logger.info(f"Switched context to '{new_context_name}'.")
        return self.get_log_for_day(today_date)

    def _end_latest_ongoing_context(self, end_time: datetime) -> None:
        """
        Finds the last ongoing LogEntry (which could be in yesterday's file),
        sets its end_time, and saves the file.
        """
        for i in range(2):
            date_to_check = end_time.date() - timedelta(days=i)

            try:
                entries = self._load_unresolved_log_entries(date_to_check)
                if not entries:
                    continue

                ongoing_entry = None
                for entry in reversed(entries):
                    if "end_time" not in entry.attributes:
                        ongoing_entry = entry
                        break

                if ongoing_entry:
                    self.logger.debug(
                        f"Found ongoing context '{ongoing_entry.context_name}' in log for {date_to_check}."
                    )

                    ongoing_entry.attributes["end_time"] = TypedValue(
                        value=end_time,
                        field_type="datetime",
                        is_dynamic=True,
                    )
                    self._save_log_file(date_to_check, entries)
                    return

            except FileNotFoundError:
                continue

    def _load_unresolved_log_entries(self, log_date: date) -> List[LogEntry]:
        """
        Loads a log file and returns a list of raw, unresolved LogEntry objects.
        This is used for modification, preserving the original Hy expressions.
        """
        filename = f"{log_date.isoformat()}.hy"
        filepath = os.path.join(self._log_dir, filename)

        if not os.path.exists(filepath):
            return []

        try:
            nodes = self._ast_manager.parse_file(filepath)
            raw_log_entries = list(
                self._loader.process(nodes, LoaderContext(config_dir=self._config_dir)).values()
            )
            return raw_log_entries
        except Exception as e:
            self.logger.error(f"Error loading raw daily log file '{filepath}': {e}", exc_info=True)
            return []

    def _save_log_file(self, log_date: date, entries: List[LogEntry]) -> None:
        """
        Regenerates and saves a daily log file from a list of in-memory
        LogEntry objects, upholding Chronoiconicity.
        """
        filename = f"{log_date.isoformat()}.hy"
        filepath = os.path.join(self._log_dir, filename)

        self.logger.debug(f"Saving {len(entries)} entries to '{filepath}'")

        with open(filepath, "w", encoding="utf-8") as f:
            for entry in entries:
                node_to_format = HyNode(
                    type="log-context",
                    value=entry.context_name,
                    original="",  
                )
                setattr(node_to_format, "attributes_typed", entry.attributes)

                formatted_lines = self._formatter_plugin.format(node_to_format)
                for line in formatted_lines:
                    f.write(line + "\n")

    def _create_new_log_entry(
        self, context_name: str, start_time: datetime, color: Optional[str]
    ) -> LogEntry:
        """Creates a new LogEntry object for an ongoing context."""
        attributes = {
            "start_time": TypedValue(value=start_time, field_type="datetime", is_dynamic=True)
        }
        if color:
            attributes["color"] = TypedValue(
                value=color, field_type="string", is_dynamic=False
            )

        return LogEntry(context_name=context_name, attributes=attributes)
