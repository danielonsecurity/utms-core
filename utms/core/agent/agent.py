import hy
import time
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from utms import UTMSConfig
from utms.core.components.elements.entity import EntityComponent
from utms.core.components.elements.pattern import PatternComponent
from utms.core.models.elements.entity import Entity
from utms.utms_types.field.types import FieldType, TypedValue
from utms.core.time import DecimalTimeStamp
from utms.core.logger import get_logger
from utms.core.hy.converter import converter
from utms.utils.hytools.conversion import list_to_dict

class SchedulerAgent:
    """
    A proactive, multi-user agent that scans the system for time-based triggers
    and executes their corresponding hooks. It processes each user's data in isolation.
    """
    def __init__(self, config: UTMSConfig):
        self.logger = get_logger()
        self.config = config
        self._is_running = True

    def _discover_users(self) -> List[str]:
        """Scans the config directory to find all user subdirectories."""
        users_dir = os.path.join(self.config.utms_dir, "users")
        try:
            if os.path.isdir(users_dir):
                return [name for name in os.listdir(users_dir) if os.path.isdir(os.path.join(users_dir, name))]
        except FileNotFoundError:
            self.logger.warning(f"Users directory not found at: {users_dir}")
        return []

    def run_blocking(self):
        self.logger.info("SchedulerAgent run loop initiated.")
        MAX_SLEEP_SECONDS = 60.0

        while self._is_running:
            try:
                now_for_this_tick = datetime.now(timezone.utc)
                
                all_users = self._discover_users()
                if not all_users:
                    self.logger.info("No users found to process. Sleeping.")
                    time.sleep(MAX_SLEEP_SECONDS)
                    continue

                self.logger.info(f"Processing tasks for users: {all_users}")
                
                earliest_next_event_utc: Optional[datetime] = None

                for username in all_users:
                    self.logger.debug(f"--- Starting tick for user: {username} ---")
                    try:
                        user_entity_component = EntityComponent(
                            config_dir=self.config.utms_dir,
                            component_manager=self.config._component_manager,
                            username=username
                        )
                        user_entity_component.load()
                        
                        user_pattern_component = PatternComponent(
                            config_dir=self.config.utms_dir,
                            component_manager=self.config._component_manager,
                            username=username
                        )
                        user_pattern_component.load()

                        user_next_event_time = self._tick_for_user(
                            now_utc=now_for_this_tick,
                            entity_component=user_entity_component,
                            pattern_component=user_pattern_component
                        )

                        if user_next_event_time:
                            if earliest_next_event_utc is None or user_next_event_time < earliest_next_event_utc:
                                earliest_next_event_utc = user_next_event_time

                    except Exception as user_e:
                        self.logger.error(f"Failed to process tick for user '{username}': {user_e}", exc_info=True)
                
                sleep_duration = MAX_SLEEP_SECONDS
                if earliest_next_event_utc:
                    seconds_until_event = (earliest_next_event_utc - now_for_this_tick).total_seconds()
                    if seconds_until_event > 0.001:
                        sleep_duration = min(seconds_until_event, MAX_SLEEP_SECONDS)
                
                sleep_duration = max(0, sleep_duration)

                self.logger.info(f"Agent sleeping for {sleep_duration:.2f} seconds until next event.")
                end_time = time.time() + sleep_duration
                while time.time() < end_time:
                    if not self._is_running:
                        break
                    time.sleep(min(1, end_time - time.time()))

                if not self._is_running:
                    break
                
            except Exception as e:
                self.logger.error(f"SchedulerAgent main loop failed: {e}", exc_info=True)
                time.sleep(MAX_SLEEP_SECONDS)

        self.logger.info("SchedulerAgent run loop has gracefully exited.")

    def stop(self):
        self.logger.info("SchedulerAgent stop signal received.")
        self._is_running = False

    def _tick_for_user(self, now_utc: datetime, entity_component: EntityComponent, pattern_component: PatternComponent) -> Optional[datetime]:
        self.logger.debug(f"Agent tick for user '{entity_component.username}' based on time: {now_utc}")

        next_event_time: Optional[datetime] = None

        def update_next_event_time(new_time: Optional[datetime]):
            nonlocal next_event_time
            if new_time:
                if next_event_time is None or new_time < next_event_time:
                    next_event_time = new_time

        try:
            update_next_event_time(self._process_timers(now_utc, entity_component))
        except Exception as e:
            self.logger.error(f"Error processing timers for user '{entity_component.username}': {e}", exc_info=True)
        
        all_entities = entity_component._entity_manager.get_all_entities()
        self.logger.debug(f"Scanning {len(all_entities)} entities for '{entity_component.username}'...")

        for entity in all_entities:
            if entity.entity_type == "timer":
                continue

            for attr_name, typed_value in list(entity.get_all_attributes_typed().items()):
                is_datetime_trigger = (typed_value.field_type == FieldType.DATETIME)
                is_pattern_trigger = (
                    typed_value.field_type == FieldType.ENTITY_REFERENCE and
                    typed_value.referenced_entity_type == "pattern"
                )

                if not (is_datetime_trigger or is_pattern_trigger):
                    continue
                    
                hook_name = f"on-{attr_name.replace('_', '-')}-hook"
                if not entity.has_attribute(hook_name):
                    continue

                if is_datetime_trigger:
                    update_next_event_time(
                        self._process_datetime_trigger(entity, attr_name, typed_value, hook_name, now_utc, entity_component)
                    )
                elif is_pattern_trigger:
                    update_next_event_time(
                        self._process_recurring_trigger(entity, attr_name, typed_value, hook_name, now_utc, entity_component, pattern_component)
                    )

        if next_event_time:
            self.logger.debug(f"Next event for user '{entity_component.username}' is scheduled for: {next_event_time}")
        else:
            self.logger.debug(f"No upcoming events found for user '{entity_component.username}' in this tick.")
        return next_event_time

    def _process_timers(self, now_utc: datetime, entity_component: EntityComponent) -> Optional[datetime]:
        self.logger.debug(f"Processing timers for user '{entity_component.username}'...")
        next_timer_finish_time: Optional[datetime] = None
        for timer in entity_component.get_by_type("timer"):
            if timer.get_attribute_value("status") != "running":
                continue
            end_time = timer.get_attribute_value("end_time")
            if not isinstance(end_time, datetime): continue
            end_time_utc = end_time if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc)
            if now_utc >= end_time_utc:
                timer_id = timer.get_identifier()
                self.logger.info(f"Timer '{timer_id}' has finished. Processing...")
                entity_component.update_entity_attribute("timer", timer.category, timer.name, "status", "finished")
                entity_component.update_entity_attribute("timer", timer.category, timer.name, "finish-cursor", now_utc) 
                self._execute_hook(timer, "on-end-time-hook", "timer finish", entity_component)
            else:
                if next_timer_finish_time is None or end_time_utc < next_timer_finish_time:
                    next_timer_finish_time = end_time_utc
        return next_timer_finish_time

    def _execute_hook(self, entity: Entity, hook_name: str, event_type: str, entity_component: EntityComponent):
        hook_tv = entity.get_attribute_typed(hook_name)
        if not (hook_tv and hook_tv.value and isinstance(hook_tv.value, hy.models.Expression)):
            self.logger.debug(f"Entity '{entity.get_identifier()}' has no valid hook for event '{event_type}'.")
            return

        if not (len(hook_tv.value) > 1 and str(hook_tv.value[0]) == "quote"):
            self.logger.warning(f"Hook '{hook_name}' on '{entity.get_identifier()}' is not a valid quoted expression. Skipping.")
            return

        code_to_run = hook_tv.value[1]
        self.logger.info(f"Executing '{event_type}' hook for '{entity.get_identifier()}': {hy.repr(code_to_run)}")
        try:
            resolution_service = entity_component._loader._dynamic_service
            resolution_service.evaluate(
                expression=code_to_run,
                context={"self": entity},
                component_label=entity.get_identifier(),
                component_type="agent_hook",
                attribute=hook_name
            )
            self.logger.info(f"Successfully executed hook for '{entity.get_identifier()}'.")
        except Exception as e:
            self.logger.error(f"Error executing hook for '{entity.get_identifier()}': {e}", exc_info=True)


    def _process_datetime_trigger(self, entity: Entity, trigger_name: str, trigger_value: TypedValue, hook_name: str, now_utc: datetime, entity_component: EntityComponent) -> Optional[datetime]:
        trigger_dt = trigger_value.value
        if not isinstance(trigger_dt, datetime): return None
        trigger_dt_utc = trigger_dt.astimezone(timezone.utc) if trigger_dt.tzinfo else trigger_dt.replace(tzinfo=timezone.utc)

        if now_utc >= trigger_dt_utc:
            agent_state_list = converter.model_to_py(entity.get_attribute_value("agent-state"), raw=True) or []
            state_dict = agent_state_list[0] if agent_state_list else {}

            raw_cursors_data = state_dict.get("cursors", [])
            cursors = {}
            if isinstance(raw_cursors_data, dict):
                cursors = raw_cursors_data
            elif isinstance(raw_cursors_data, list):
                cursors = list_to_dict(raw_cursors_data)

            for key, value in cursors.items():
                if isinstance(value, list) and len(value) > 1 and value[0] == 'datetime':
                    try:
                        cursors[key] = datetime(*value[1:])
                    except (TypeError, ValueError):
                        pass

            cursor_key = trigger_name
            raw_cursor_value = cursors.get(cursor_key)

            cursor_dt_utc: Optional[datetime] = None
            if isinstance(raw_cursor_value, datetime):
                cursor_dt_utc = raw_cursor_value.astimezone(timezone.utc) if raw_cursor_value.tzinfo else raw_cursor_value.replace(tzinfo=timezone.utc)

            if cursor_dt_utc is None or cursor_dt_utc < trigger_dt_utc:
                self.logger.info(f"        !!!! TRIGGERING '{hook_name}' on '{entity.get_identifier()}' !!!!")
                self._execute_hook(entity, hook_name, "datetime trigger", entity_component)

                cursors[cursor_key] = now_utc

                py_structure_to_save = [{'cursors': cursors}]
                hy_model_to_save = converter.py_to_model(py_structure_to_save)
                new_agent_state_tv = TypedValue(
                    value=hy_model_to_save,
                    field_type=FieldType.LIST,
                    item_schema_type="AGENT_STATE"
                )
                entity.set_attribute_typed("agent-state", new_agent_state_tv)
                entity_component._save_entities_in_category(entity.entity_type, entity.category)

            return None
        else:
            return trigger_dt_utc

    def _process_recurring_trigger(self, entity: Entity, trigger_name: str, trigger_value: TypedValue, hook_name: str, now_utc: datetime, entity_component: EntityComponent, pattern_component: PatternComponent) -> Optional[datetime]:
        pattern_label = trigger_value.value
        if not isinstance(pattern_label, str): return None

        simple_label = pattern_label.split(':')[-1]
        pattern = pattern_component.get_pattern(simple_label)
        if not pattern:
            self.logger.warning(f"Pattern '{simple_label}' not found for user '{entity_component.username}'. Skipping trigger for '{entity.get_identifier()}'.")
            return None

        agent_state_list = converter.model_to_py(entity.get_attribute_value("agent-state"), raw=True) or []
        state_dict = agent_state_list[0] if agent_state_list else {}

        raw_cursors_data = state_dict.get("cursors", [])
        cursors = {}
        if isinstance(raw_cursors_data, dict):
            cursors = raw_cursors_data
        elif isinstance(raw_cursors_data, list):
            cursors = list_to_dict(raw_cursors_data)

        for key, value in cursors.items():
            if isinstance(value, list) and len(value) > 1 and value[0] == 'datetime':
                try:
                    cursors[key] = datetime(*value[1:])
                except (TypeError, ValueError):
                    pass

        cursor_key = trigger_name
        raw_cursor_value = cursors.get(cursor_key)
        
        last_processed_time = None
        if isinstance(raw_cursor_value, datetime):
            last_processed_time = raw_cursor_value.astimezone(timezone.utc) if raw_cursor_value.tzinfo else raw_cursor_value.replace(tzinfo=timezone.utc)
        else:
            interval_delta = pattern.spec.interval.to_timedelta() if pattern.spec.interval else timedelta(minutes=1)
            last_processed_time = now_utc - interval_delta
            self.logger.debug(f"No cursor found for '{entity.get_identifier()}'. Starting check from a past point: {last_processed_time}")

        next_scheduled_dt = pattern.next_occurrence(from_time=DecimalTimeStamp(last_processed_time)).to_gregorian().replace(tzinfo=timezone.utc)
        if next_scheduled_dt > now_utc:
            return next_scheduled_dt

        self.logger.info(f"        !!!! CATCH-UP TRIGGERING '{hook_name}' on '{entity.get_identifier()}' for missed event at {next_scheduled_dt} !!!!")
        self._execute_hook(entity, hook_name, "pattern trigger catch-up", entity_component)

        new_cursor_target = now_utc
        self.logger.info(f"        -> Catch-up complete. Aligning cursor for '{entity.get_identifier()}' to current time: {new_cursor_target}")

        cursors[cursor_key] = new_cursor_target

        py_structure_to_save = [{'cursors': cursors}]

        hy_model_to_save = converter.py_to_model(py_structure_to_save)
        new_agent_state_tv = TypedValue(
            value=hy_model_to_save,
            field_type=FieldType.LIST,
            item_schema_type="AGENT_STATE"
        )
        entity.set_attribute_typed("agent-state", new_agent_state_tv)
        entity_component._save_entities_in_category(entity.entity_type, entity.category)

        final_next_event_dt = pattern.next_occurrence(from_time=DecimalTimeStamp(new_cursor_target)).to_gregorian().replace(tzinfo=timezone.utc)
        self.logger.info(f"        -> Next future event for '{entity.get_identifier()}' scheduled for: {final_next_event_dt}")

        return final_next_event_dt
