import time
from datetime import datetime, timedelta
from decimal import Decimal

from utms import UTMSConfig
from utms.core.components.elements.entity import EntityComponent
from utms.core.components.elements.pattern import PatternComponent
from utms.core.models.elements.entity import Entity
from utms.utms_types.field.types import FieldType, TypedValue
from utms.core.time import DecimalTimeStamp, DecimalTimeLength
from utms.core.services.dynamic import dynamic_resolution_service as resolution_service
from utms.core.logger import get_logger

class SchedulerAgent:
    """
    A proactive agent that scans the system for time-based triggers
    and executes their corresponding hooks. Designed to be run as a blocking process.
    """
    def __init__(self, config: UTMSConfig):
        self.logger = get_logger("agent")
        self.config = config
        
        self.entity_component: EntityComponent = self.config._component_manager.get_instance("entities")
        self.pattern_component: PatternComponent = self.config._component_manager.get_instance("patterns")
        self.resolution_service = self.entity_component._loader._dynamic_service
        
        self.lookahead_duration = DecimalTimeLength(86400) 
        self._is_running = True

    def run_blocking(self):
        self.logger.info("SchedulerAgent run loop initiated.")
        while self._is_running:
            try:
                self._tick()
            except Exception as e:
                self.logger.error(f"SchedulerAgent tick failed: {e}", exc_info=True)
            for _ in range(60):
                if not self._is_running:
                    break
                time.sleep(1)
        self.logger.info("SchedulerAgent run loop has gracefully exited.")


    def stop(self):
        self.logger.info("SchedulerAgent stop signal received.")
        self._is_running = False

    def _tick(self):
        """A single, generalized pass of the agent's scheduling logic."""
        self.logger.debug("Agent tick...")
        
        now_dts = DecimalTimeStamp.now()
        lookahead_until_dts = now_dts + self.lookahead_duration
        self.logger.debug(f"Time window: now={now_dts}, lookahead_until={lookahead_until_dts}")

        all_entities = self.entity_component._entity_manager.get_all_entities()
        if not all_entities:
            return

        self.logger.debug(f"Scanning {len(all_entities)} entities for temporal triggers...")

        for entity in list(all_entities):
            for attr_name, typed_value in list(entity.get_all_attributes_typed().items()):
                is_datetime_trigger = (typed_value.field_type == FieldType.DATETIME)
                is_pattern_trigger = (
                    typed_value.field_type == FieldType.ENTITY_REFERENCE and
                    typed_value.referenced_entity_type == "pattern"
                )

                if not (is_datetime_trigger or is_pattern_trigger):
                    continue # Not a temporal attribute, move to the next one
                
                # We found a potential trigger. Check for its hook by convention.
                self.logger.debug(f"    -> Discovered potential trigger on {entity.get_identifier()}: '{attr_name}'")
                hook_name = f"on_{attr_name}_hook"

                if not entity.has_attribute(hook_name):
                    self.logger.debug(f"       - SKIPPING: Corresponding hook '{hook_name}' not found.")
                    continue

                if is_datetime_trigger:
                    self._process_datetime_trigger(
                        entity, 
                        trigger_name=attr_name,
                        trigger_value=typed_value,
                        hook_name=hook_name,
                        lookahead_until_dts=lookahead_until_dts
                    )
                elif is_pattern_trigger:
                    self._process_recurring_trigger(
                        entity,
                        trigger_name=attr_name,
                        trigger_value=typed_value,
                        hook_name=hook_name,
                        lookahead_until_dts=lookahead_until_dts
                    )

    def _process_datetime_trigger(self, entity: Entity, trigger_name:str, trigger_value: TypedValue, hook_name: str, lookahead_until_dts: DecimalTimeStamp):
        trigger_name = "deadline" # We know this for now
        self.logger.debug(f"      -> Processing trigger '{trigger_name}' for '{entity.get_identifier()}'")

        status = entity.get_attribute_value("status")
        if status in ["completed", "done", "archived", "cancelled"]:
            self.logger.debug(f"         - SKIPPING: Entity status is '{status}'.")
            return

        deadline_dt = trigger_value.value
        if not isinstance(deadline_dt, datetime):
            self.logger.debug(f"         - SKIPPING: Deadline attribute is not a valid datetime object. Got: {type(deadline_dt)}")
            return
            
        self.logger.debug(f"         - Found deadline datetime: {deadline_dt}")
        
        cursor_name = f"{trigger_name}_cursor"
        raw_cursor_value = entity.get_attribute_value(cursor_name)
        
        cursor_dts = None
        if raw_cursor_value is None:
            cursor_dts = DecimalTimeStamp(0) # First run, cursor is at the beginning of time
        elif isinstance(raw_cursor_value, (datetime, DecimalTimeStamp)):
            cursor_dts = DecimalTimeStamp(raw_cursor_value) # Convert if needed
        elif isinstance(raw_cursor_value, (int, float, Decimal)):
            cursor_dts = DecimalTimeStamp(raw_cursor_value)
            
        if cursor_dts is None:
            self.logger.error(f"         - CRITICAL: Could not process cursor value. Raw value was '{raw_cursor_value}'. Skipping.")
            return

        self.logger.debug(f"         - Found cursor timestamp: {cursor_dts}")

        deadline_dts = DecimalTimeStamp(deadline_dt)

        if cursor_dts < deadline_dts <= lookahead_until_dts:
            self.logger.info(f"        !!!! TRIGGERING '{hook_name}' on '{entity.get_identifier()}' for deadline: {deadline_dt} !!!!")
            
            hook_code = entity.get_attribute_value(hook_name)
            if hook_code:
                try:
                    self.resolution_service.evaluate(
                        expression=hook_code, context={"self": entity}, component_label=entity.get_identifier(),
                        component_type="agent_hook", attribute=hook_name
                    )
                except Exception as e:
                    self.logger.error(f"Error executing hook '{hook_name}': {e}", exc_info=True)

            try:
                self.entity_component.update_entity_attribute(
                    entity_type=entity.entity_type, category=entity.category, name=entity.name, 
                    attr_name=cursor_name, 
                    new_raw_value_from_api=deadline_dt # Pass the standard datetime object
                )
                self.logger.info(f"        -> Successfully updated '{cursor_name}' for '{entity.get_identifier()}'.")
            except Exception as e:
                self.logger.error(f"CRITICAL: Failed to update cursor for '{entity.get_identifier()}': {e}", exc_info=True)
        else:
            self.logger.debug(f"         - SKIPPING: Condition not met. [cursor < deadline <= lookahead] -> [{cursor_dts} < {deadline_dts} <= {lookahead_until_dts}]")

    def _process_recurring_trigger(self, entity: Entity, trigger_name: str, trigger_value: TypedValue, hook_name: str, lookahead_until_dts: DecimalTimeStamp):
        self.logger.debug(f"      -> Processing recurring trigger '{trigger_name}' for '{entity.get_identifier()}'")
        # The trigger_value holds the reference to the pattern, e.g., "daily-9am"
        pattern_label = trigger_value.value
        if not isinstance(pattern_label, str) or not pattern_label:
            self.logger.debug(f"         - SKIPPING: Pattern reference for '{trigger_name}' is not a valid string. Got: {pattern_label}")
            return

        self.logger.debug(f"         - Found fully qualified pattern label: '{pattern_label}'")

        simple_label = pattern_label.split(':')[-1]

        pattern = self.pattern_component.get_pattern(simple_label)
        if not pattern:
            self.logger.warning(f"         - SKIPPING: Pattern '{simple_label}' (from '{pattern_label}') not found in PatternComponent.")
            return

        # For recurring events, the cursor is essential.
        cursor_name = f"{trigger_name}_cursor"
        raw_cursor_value = entity.get_attribute_value(cursor_name)
        
        cursor_dts = None
        if raw_cursor_value is None:
            self.logger.info(f"         - No cursor found for '{cursor_name}'. Initializing from current time.")
            cursor_dts = DecimalTimeStamp.now() 
            try:
                self.entity_component.update_entity_attribute(
                    entity.entity_type, entity.category, entity.name, 
                    cursor_name, cursor_dts.to_gregorian()
                )
                self.logger.info(f"         - Initialized and saved new cursor for '{cursor_name}'.")
            except Exception as e:
                self.logger.error(f"CRITICAL: Failed to save initial cursor for '{entity.get_identifier()}': {e}", exc_info=True)
                return
        elif isinstance(raw_cursor_value, (datetime, DecimalTimeStamp)):
            cursor_dts = DecimalTimeStamp(raw_cursor_value)
        elif isinstance(raw_cursor_value, (int, float, Decimal)):
            cursor_dts = DecimalTimeStamp(raw_cursor_value)

        if cursor_dts is None:
            self.logger.error(f"         - CRITICAL: Could not process cursor value for recurring trigger. Raw value was '{raw_cursor_value}'. Skipping.")
            return

        self.logger.debug(f"         - Using cursor: {cursor_dts}")

        # Calculate the next scheduled event time based on our last run (the cursor).
        next_event_dts = pattern.next_occurrence(from_time=cursor_dts)
        self.logger.debug(f"         - Calculated next occurrence: {next_event_dts}")

        if next_event_dts <= lookahead_until_dts:
            self.logger.info(f"        !!!! TRIGGERING '{hook_name}' on '{entity.get_identifier()}' for pattern '{pattern_label}' at {next_event_dts} !!!!")
            
            hook_code = entity.get_attribute_value(hook_name)
            if hook_code:
                try:
                    self.resolution_service.evaluate(
                        expression=hook_code, context={"self": entity}, component_label=entity.get_identifier(),
                        component_type="agent_hook", attribute=hook_name
                    )
                except Exception as e:
                    self.logger.error(f"Error executing hook '{hook_name}': {e}", exc_info=True)

            try:
                # CRITICAL: Update the cursor to the time of the event we just processed.
                # This ensures we look for the *next* event on the next tick.
                self.entity_component.update_entity_attribute(
                    entity_type=entity.entity_type, category=entity.category, name=entity.name, 
                    attr_name=cursor_name, 
                    new_raw_value_from_api=next_event_dts.to_gregorian() # Pass a standard datetime
                )
                self.logger.info(f"        -> Successfully updated '{cursor_name}' to {next_event_dts}.")
            except Exception as e:
                self.logger.error(f"CRITICAL: Failed to update cursor for '{entity.get_identifier()}': {e}", exc_info=True)
        else:
             self.logger.debug(f"         - SKIPPING: Next occurrence {next_event_dts} is outside lookahead window {lookahead_until_dts}.")
            
