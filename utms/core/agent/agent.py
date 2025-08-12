# utms/core/agent/agent.py

import hy
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from utms import UTMSConfig
from utms.core.components.elements.entity import EntityComponent
from utms.core.components.elements.pattern import PatternComponent
from utms.core.models.elements.entity import Entity
from utms.utms_types.field.types import FieldType, TypedValue
from utms.core.time import DecimalTimeStamp
from utms.core.services.dynamic import dynamic_resolution_service as resolution_service
from utms.core.logger import get_logger
from utms.utils.hytools.conversion import hy_to_python, python_to_hy_model, list_to_dict
from utms.core.hy.utils import get_from_hy_dict


class SchedulerAgent:
    """
    A proactive agent that scans the system for time-based triggers
    and executes their corresponding hooks. It uses an intelligent "smart sleep"
    to be both efficient and responsive to the next scheduled event.
    """
    def __init__(self, config: UTMSConfig):
        self.logger = get_logger()
        self.config = config
        
        self.entity_component: EntityComponent = self.config._component_manager.get_instance("entities")
        self.pattern_component: PatternComponent = self.config._component_manager.get_instance("patterns")
        self.resolution_service = self.entity_component._loader._dynamic_service
        
        self._is_running = True

    def run_blocking(self):
        self.logger.info("SchedulerAgent run loop initiated.")
        MAX_SLEEP_SECONDS = 60.0

        while self._is_running:
            try:
                now_for_this_tick = datetime.now(timezone.utc)
                next_event_time_utc = self._tick(now_for_this_tick)

                sleep_duration = MAX_SLEEP_SECONDS 
                
                if next_event_time_utc:
                    seconds_until_event = (next_event_time_utc - now_for_this_tick).total_seconds()
                    
                    if seconds_until_event > 0.001:
                        sleep_duration = min(seconds_until_event, MAX_SLEEP_SECONDS)
                
                sleep_duration = max(0, sleep_duration)

                self.logger.info(f"Agent sleeping for {sleep_duration:.2f} seconds.")
                end_time = time.time() + sleep_duration
                while time.time() < end_time:
                    if not self._is_running:
                        break
                    time.sleep(min(1, end_time - time.time()))

                if not self._is_running:
                    break
                
            except Exception as e:
                self.logger.error(f"SchedulerAgent tick failed: {e}", exc_info=True)
                time.sleep(MAX_SLEEP_SECONDS)

        self.logger.info("SchedulerAgent run loop has gracefully exited.")

    def stop(self):
        self.logger.info("SchedulerAgent stop signal received.")
        self._is_running = False

    def _tick(self, now_utc:datetime) -> Optional[datetime]:
        self.entity_component.sync_from_disk()
        self.logger.debug(f"Agent tick based on time: {now_utc}")

        next_event_time: Optional[datetime] = None

        def update_next_event_time(new_time: Optional[datetime]):
            nonlocal next_event_time
            if new_time:
                if next_event_time is None or new_time < next_event_time:
                    next_event_time = new_time

        try:
            update_next_event_time(self._process_timers(now_utc))
        except Exception as e:
            self.logger.error(f"Error processing timers: {e}", exc_info=True)
        
        all_entities = self.entity_component._entity_manager.get_all_entities()
        self.logger.debug(f"Scanning {len(all_entities)} entities for generic temporal triggers...")

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
                        self._process_datetime_trigger(entity, attr_name, typed_value, hook_name, now_utc)
                    )
                elif is_pattern_trigger:
                    update_next_event_time(
                        self._process_recurring_trigger(entity, attr_name, typed_value, hook_name, now_utc)
                    )

        if next_event_time:
            self.logger.debug(f"Next overall event is scheduled for: {next_event_time}")
        else:
            self.logger.debug("No upcoming events found in this tick.")
        return next_event_time

    def _process_timers(self, now_utc: datetime) -> Optional[datetime]:
        self.logger.debug("Processing timers...")
        next_timer_finish_time: Optional[datetime] = None
        for timer in self.entity_component.get_by_type("timer"):
            if timer.get_attribute_value("status") != "running":
                continue
            end_time = timer.get_attribute_value("end_time")
            if not isinstance(end_time, datetime): continue
            end_time_utc = end_time if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc)
            if now_utc >= end_time_utc:
                timer_id = timer.get_identifier()
                self.logger.info(f"Timer '{timer_id}' has finished. Processing...")
                self.entity_component.update_entity_attribute("timer", timer.category, timer.name, "status", "finished")
                self.entity_component.update_entity_attribute("timer", timer.category, timer.name, "finish-cursor", now_utc) 
                self._execute_hook(timer, "on-end-time-hook", "timer finish")
            else:
                if next_timer_finish_time is None or end_time_utc < next_timer_finish_time:
                    next_timer_finish_time = end_time_utc
        return next_timer_finish_time

    def _process_datetime_trigger(self, entity: Entity, trigger_name: str, trigger_value: TypedValue, hook_name: str, now_utc: datetime) -> Optional[datetime]:
        trigger_dt = trigger_value.value
        if not isinstance(trigger_dt, datetime): return None
        trigger_dt_utc = trigger_dt.astimezone(timezone.utc) if trigger_dt.tzinfo else trigger_dt.replace(tzinfo=timezone.utc)
    
        if now_utc >= trigger_dt_utc:
            # --- START ROBUST PARSING BLOCK ---
            agent_state_plist = hy_to_python(entity.get_attribute_value("agent-state")) or []
            state_plist = agent_state_plist[0] if agent_state_plist else []
            state_dict = list_to_dict(state_plist)
            cursors_plist = state_dict.get("cursors", [])
            cursors_dict_with_list_datetime = list_to_dict(cursors_plist)
            cursors = {}
            for key, value in cursors_dict_with_list_datetime.items():
                if isinstance(value, list) and len(value) > 1 and value[0] == 'datetime':
                    try:
                        cursors[key] = datetime(*value[1:])
                    except (TypeError, ValueError):
                        cursors[key] = value 
                else:
                    cursors[key] = value
            # --- END ROBUST PARSING BLOCK ---

            # The key for the cursor map is the name of the trigger attribute itself.
            cursor_key = trigger_name 
            
            # Try to get from agent-state first, then fall back to dedicated cursor attribute.
            raw_cursor_value = cursors.get(cursor_key)
            if raw_cursor_value is None:
                dedicated_cursor_attr_name = f"{trigger_name}-cursor"
                raw_cursor_value = entity.get_attribute_value(dedicated_cursor_attr_name)

            cursor_dt_utc: Optional[datetime] = None
            if isinstance(raw_cursor_value, datetime):
                cursor_dt_utc = raw_cursor_value.astimezone(timezone.utc) if raw_cursor_value.tzinfo else raw_cursor_value.replace(tzinfo=timezone.utc)

            if cursor_dt_utc is None or cursor_dt_utc < trigger_dt_utc:
                self.logger.info(f"        !!!! TRIGGERING '{hook_name}' on '{entity.get_identifier()}' !!!!")
                self._execute_hook(entity, hook_name, "datetime trigger")

                cursors[cursor_key] = now_utc
                
                # Create a fresh, correctly typed TypedValue for the agent state.
                new_state_py_dict = {'cursors': cursors} 
                new_state_hy_model = python_to_hy_model(new_state_py_dict)
                new_agent_state_tv = TypedValue(
                    value=[new_state_hy_model],
                    field_type=FieldType.LIST,
                    item_schema_type="AGENT_STATE"
                )
                entity.set_attribute_typed("agent-state", new_agent_state_tv)
                self.entity_component._save_entities_in_category(entity.entity_type, entity.category)
            
            return None
        else:
            return trigger_dt_utc

    def _process_recurring_trigger(self, entity: Entity, trigger_name: str, trigger_value: TypedValue, hook_name: str, now_utc: datetime) -> Optional[datetime]:

        pattern_label = trigger_value.value
        if not isinstance(pattern_label, str): return None

        simple_label = pattern_label.split(':')[-1]
        pattern = self.pattern_component.get_pattern(simple_label)
        if not pattern: return None

        # --- START ROBUST PARSING BLOCK ---
        agent_state_plist = hy_to_python(entity.get_attribute_value("agent-state")) or []
        state_plist = agent_state_plist[0] if agent_state_plist else []
        state_dict = list_to_dict(state_plist)
        cursors_plist = state_dict.get("cursors", [])
        cursors_dict_with_list_datetime = list_to_dict(cursors_plist)
        cursors = {}
        for key, value in cursors_dict_with_list_datetime.items():
            if isinstance(value, list) and len(value) > 1 and value[0] == 'datetime':
                try:
                    cursors[key] = datetime(*value[1:])
                except (TypeError, ValueError):
                    cursors[key] = value
            else:
                cursors[key] = value
        # --- END ROBUST PARSING BLOCK ---

        cursor_key = trigger_name
        raw_cursor_value = cursors.get(cursor_key)
        if raw_cursor_value is None:
            dedicated_cursor_attr_name = f"{trigger_name}-cursor"
            raw_cursor_value = entity.get_attribute_value(dedicated_cursor_attr_name)

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

        # --- CATCH-UP LOGIC: "RUN ONCE, THEN ALIGN TO THE FUTURE" ---
        self.logger.info(f"        !!!! CATCH-UP TRIGGERING '{hook_name}' on '{entity.get_identifier()}' for missed event at {next_scheduled_dt} !!!!")
        self._execute_hook(entity, hook_name, "pattern trigger catch-up")

        # **THE CRITICAL FIX IS HERE**
        # The new cursor must be the current time to signify we are caught up.
        new_cursor_target = now_utc
        self.logger.info(f"        -> Catch-up complete. Aligning cursor for '{entity.get_identifier()}' to current time: {new_cursor_target}")

        cursors[cursor_key] = new_cursor_target

        new_state_py_dict = {'cursors': cursors}
        new_state_hy_model = python_to_hy_model(new_state_py_dict)
        new_agent_state_tv = TypedValue(
            value=[new_state_hy_model],
            field_type=FieldType.LIST,
            item_schema_type="AGENT_STATE"
        )
        entity.set_attribute_typed("agent-state", new_agent_state_tv)
        self.entity_component._save_entities_in_category(entity.entity_type, entity.category)

        # Calculate the *next* event starting from our newly aligned cursor.
        # This will GUARANTEE a time in the future.
        final_next_event_dt = pattern.next_occurrence(from_time=DecimalTimeStamp(new_cursor_target)).to_gregorian().replace(tzinfo=timezone.utc)
        self.logger.info(f"        -> Next future event for '{entity.get_identifier()}' scheduled for: {final_next_event_dt}")

        return final_next_event_dt
    
    def _execute_hook(self, entity: Entity, hook_name: str, event_type: str):
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
            self.resolution_service.evaluate(
                expression=code_to_run,
                context={"self": entity},
                component_label=entity.get_identifier(),
                component_type="agent_hook",
                attribute=hook_name
            )
            self.logger.info(f"Successfully executed hook for '{entity.get_identifier()}'.")
        except Exception as e:
            self.logger.error(f"Error executing hook for '{entity.get_identifier()}': {e}", exc_info=True)
