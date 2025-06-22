import subprocess
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Union

from utms.core.hy.resolvers.base import HyResolver
from utms.core.managers.elements.entity import EntityManager
from utms.core.models.elements.entity import Entity
from utms.core.services.dynamic import (  # For resolving attributes from get-attr
    dynamic_resolution_service,
)
from utms.utils import hy_to_python  # For converting resolved values
from utms.utils import get_ntp_date, get_timezone_from_seconds
from utms.utms_types import (
    Context,
    DynamicExpressionInfo,
    HyExpression,
    HyNode,
    HyString,
    HySymbol,
    LocalsDict,
    ResolvedValue,
    is_expression,
)


class EntityResolver(HyResolver):
    """Resolver for entity expressions in Hy code."""

    def __init__(self, entity_manager: EntityManager) -> None:
        super().__init__()
        self._entity_manager = entity_manager
        self.default_globals.update(
            {
                "entity-ref": self._hy_entity_ref,
                "get-attr": self._hy_get_attr,
                "shell": lambda *args, **kwargs: self._hy_shell(*args, **kwargs),
            }
        )

    def get_locals_dict(self, context: Context, local_names: LocalsDict = None) -> LocalsDict:
        """Provide entity-specific context for Hy evaluation"""
        locals_dict = super().get_locals_dict(context, local_names)

        utility_functions = {
            "get_ntp_date": get_ntp_date,
            "get_timezone": get_timezone_from_seconds,
        }

        for k, v in utility_functions.items():
            if k not in locals_dict:
                locals_dict[k] = v

        self.logger.debug("EntityResolver locals_dict keys: %s", list(locals_dict.keys()))
        return locals_dict

    def _hy_entity_ref(self, entity_type_str: str, category_str: str, name_str: str) -> str:
        """
        Implementation of the (entity-ref type category name) Hy function.
        Args are Python native strings because HyResolver._resolve_expression resolved them.
        Returns the unique entity key string.
        """
        self.logger.debug(
            f"EntityResolver._hy_entity_ref: type='{entity_type_str}', category='{category_str}', name='{name_str}'"
        )

        if not all(isinstance(arg, str) for arg in [entity_type_str, category_str, name_str]):
            raise TypeError(
                f"entity-ref arguments must resolve to strings. "
                f"Got: type({type(entity_type_str)}), cat({type(category_str)}), name({type(name_str)})"
            )

        ref_key = self._entity_manager._generate_key(entity_type_str, category_str, name_str)
        self.logger.debug(f"EntityResolver: entity-ref resolved to key string: '{ref_key}'")
        return ref_key

    def _resolve_target_entity_for_get_attr(
        self,
        target_expr: Any,
        current_self_context: Optional[SimpleNamespace],  # 'self' of the calling entity
        current_global_vars: LocalsDict,
    ) -> Optional[Entity]:
        """
        Helper for _hy_get_attr to resolve the target entity expression.
        target_expr could be:
        - Symbol 'self'
        - An (entity-ref ...) expression
        - A string (entity key)
        - Potentially a direct Entity object if passed around (less common from Hy)
        """
        resolved_target = target_expr

        if isinstance(target_expr, HySymbol) and str(target_expr) == "self":
            if isinstance(current_self_context, SimpleNamespace):  # Or your Entity proxy object
                self.logger.warning(
                    "get-attr on 'self' needs the Entity object, not just its attribute dict/SimpleNamespace. This might require context adjustments."
                )

                if isinstance(
                    current_self_context, Entity
                ):  # Ideal case for (get-attr self "attr")
                    return current_self_context
                return None  # Cannot get Entity object from SimpleNamespace directly here
            else:  # If self is not what we expect for get-attr
                self.logger.error(
                    f"get-attr: 'self' was not a SimpleNamespace or Entity. Got: {type(current_self_context)}"
                )
                return None

        elif (
            isinstance(target_expr, HyExpression)
            and target_expr
            and str(target_expr[0]) == "entity-ref"
        ):
            entity_key = self._resolve_value(target_expr, current_self_context, current_global_vars)
            if isinstance(entity_key, str):
                return self._entity_manager.get(entity_key)
            else:
                self.logger.error(
                    f"get-attr: (entity-ref ...) did not resolve to a string key. Got: {entity_key}"
                )
                return None
        elif isinstance(target_expr, (str, HyString)):  # Assumed to be an entity key string
            entity_key = str(target_expr)
            return self._entity_manager.get(entity_key)
        elif isinstance(target_expr, Entity):  # Already an entity object
            return target_expr

        self.logger.warning(f"get-attr: Cannot determine entity from target_expr: {target_expr}")
        return None

    def _hy_get_attr(self, target_entity_expr: Any, attribute_name_expr: Any) -> Any:
        """
        Implementation of (get-attr <target-entity-or-ref> <attribute-name-string>)
        <target-entity-or-ref> is resolved by the main resolver first.
        <attribute-name-string> is also resolved.
        `context` (for `self`) and `local_names` (for global vars) are implicitly available
        via how `_resolve_expression` calls this Python function (they become part of closure).
        However, to resolve the target_entity_expr or dynamic attributes of the target,
        we need to call back into the resolution mechanism carefully.

        This function is called AFTER its arguments `target_entity_expr` and `attribute_name_expr`
        have been resolved to Python native values by the main HyResolver._resolve_expression loop.
        So, target_entity_expr would be a Python string (key from entity-ref) or a SimpleNamespace (for self).
        attribute_name_expr would be a Python string.
        """
        # Arguments received here are already Python native values
        target_entity_val = (
            target_entity_expr  # e.g. "task:default:foo" or SimpleNamespace for self
        )
        attribute_name_str = str(attribute_name_expr)  # e.g. "description"

        self.logger.debug(
            f"EntityResolver: get-attr called. Target='{target_entity_val}', Attr='{attribute_name_str}'"
        )

        actual_entity_object: Optional[Entity] = None
        if isinstance(target_entity_val, SimpleNamespace):
            self.logger.error(
                "get-attr with 'self' as SimpleNamespace target is not fully supported yet without direct Entity access. Need to refine 'self' context in EntityLoader for get-attr."
            )
            if hasattr(target_entity_val, "__utms_entity_instance__"):
                actual_entity_object = getattr(target_entity_val, "__utms_entity_instance__")
            else:  # Attempt to look up self by its presumed key if 'self' has name, type, category
                if (
                    hasattr(target_entity_val, "name")
                    and hasattr(target_entity_val, "entity_type")
                    and hasattr(target_entity_val, "category")
                ):
                    self_key = self._entity_manager._generate_key(
                        target_entity_val.entity_type,
                        target_entity_val.category,
                        target_entity_val.name,
                    )
                    actual_entity_object = self._entity_manager.get(self_key)
                    if not actual_entity_object:
                        self.logger.error(
                            f"get-attr: Could not re-fetch 'self' entity for key {self_key}"
                        )
                        raise ValueError(
                            f"get-attr: 'self' entity could not be re-fetched for attribute access."
                        )
                else:
                    raise ValueError(
                        "get-attr: 'self' target does not provide enough info to fetch Entity object."
                    )

        elif isinstance(target_entity_val, str):  # An entity key from (entity-ref ...)
            actual_entity_object = self._entity_manager.get(target_entity_val)
        elif isinstance(target_entity_val, Entity):  # Direct entity object
            actual_entity_object = target_entity_val

        if not actual_entity_object:
            raise ValueError(
                f"get-attr: Could not find or resolve target entity: {target_entity_val}"
            )

        typed_value_attr = actual_entity_object.get_attribute_typed(attribute_name_str)
        if not typed_value_attr:
            # Check with hyphen replaced by underscore for attribute name
            typed_value_attr = actual_entity_object.get_attribute_typed(
                attribute_name_str.replace("-", "_")
            )
            if not typed_value_attr:
                raise AttributeError(
                    f"Attribute '{attribute_name_str}' not found on entity '{actual_entity_object.name}'."
                )

        if typed_value_attr.is_dynamic:
            self.logger.debug(
                f"get-attr: Attribute '{attribute_name_str}' of '{actual_entity_object.name}' is dynamic ('{typed_value_attr.original}'). Resolving..."
            )
            resolved_attr_val_raw, _ = dynamic_resolution_service.evaluate(
                expression=typed_value_attr._raw_value,  # The HyObject of the attribute
                # Pass the actual entity object as the 'self' context for its own attribute's resolution
                context={
                    "self": SimpleNamespace(
                        **{k: v.value for k, v in actual_entity_object.attributes.items()}
                    )
                },
                component_type=actual_entity_object.entity_type,
                component_label=f"{actual_entity_object.category}:{actual_entity_object.name}",
                attribute=attribute_name_str,
            )
            return hy_to_python(resolved_attr_val_raw)
        else:
            return typed_value_attr.value  # Already resolved Python value

    def _hy_shell(self, command_string: str, bg: bool = False): # Add the bg keyword argument
        """
        Implementation for the (shell "...") Hy function.
        Executes the given string as a shell command.
        
        Args:
            command_string: The command to execute.
            bg: If True, run the command in the background and return immediately.
        """
        if not isinstance(command_string, str):
            raise TypeError(f"The 'shell' function requires a string argument, but got {type(command_string)}")

        if bg:
            self.logger.info(f"Executing shell command in background: {command_string}")
            subprocess.Popen(command_string, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "Started background process." # Return a useful string instead of None
        else:
            self.logger.info(f"Executing shell command: {command_string}")
            try:
                result = subprocess.run(
                    command_string,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                if result.stdout:
                    self.logger.info(f"Shell command stdout: {result.stdout.strip()}")
                if result.stderr:
                    self.logger.warning(f"Shell command stderr: {result.stderr.strip()}")

                return result.stdout

            except subprocess.CalledProcessError as e:
                self.logger.error(f"Shell command failed with exit code {e.returncode}: {command_string}")
                self.logger.error(f"Stderr: {e.stderr.strip()}")
                raise e
