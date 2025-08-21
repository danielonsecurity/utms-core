from typing import Any, Dict, List, Optional

import hy
from hy.models import Expression, Symbol

from utms.core.hy.resolvers.elements.variable import VariableResolver
from utms.core.loaders.base import ComponentLoader, LoaderContext
from utms.core.managers.elements.variable import VariableManager
from utms.core.models import Variable
from utms.core.services.dynamic import DynamicResolutionService
from utms.core.hy.converter import converter
from utms.utms_types import HyNode
from utms.utms_types.field.types import FieldType, TypedValue, infer_type
from utms.core.hy.converter import converter


class VariableLoader(ComponentLoader[Variable, VariableManager]):
    """Loader for Variable components."""

    def __init__(self, manager: VariableManager):
        super().__init__(manager)
        self._resolver = VariableResolver()
        self._dynamic_service = DynamicResolutionService(resolver=self._resolver)

    def parse_definitions(self, nodes: List[HyNode]) -> Dict[str, dict]:
        """
        Parse HyNodes into variable definitions.
        The 'initial_typed_value' stored here is the TypedValue created by the plugin,
        containing the raw Hy value and the original string from the .hy file.
        """
        definitions = {}
        for node in nodes:
            if not self.validate_node(node, "def-var"):
                continue

            node_value_data: Optional[Dict[str, Any]] = node.value
            if (
                not isinstance(node_value_data, dict)
                or "name" not in node_value_data
                or "typed_value_for_var_value" not in node_value_data
            ):
                self.logger.warning(
                    f"Variable node value '{node.value}' has invalid data structure. Skipping."
                )
                continue

            var_name = node_value_data["name"]
            typed_value_from_plugin: TypedValue = node_value_data["typed_value_for_var_value"]

            definition_props = {
                "key": var_name,
                "initial_typed_value": typed_value_from_plugin,
            }
            definitions[var_name] = definition_props
            self.logger.debug(
                f"Parsed definition for '{var_name}', initial_typed_value: {repr(typed_value_from_plugin)}"
            )
        return definitions

    def create_object(self, key: str, properties: Dict[str, Any]) -> Variable:
        initial_typed_value_from_plugin: TypedValue = properties["initial_typed_value"]

        self.logger.debug(
            f"Creating variable '{key}'. Initial TypedValue from plugin: {repr(initial_typed_value_from_plugin)}"
        )

        self.logger.debug(
            f"Variable '{key}' value will be resolved. Original Hy string: '{initial_typed_value_from_plugin.original}'"
        )

        evaluation_context_for_resolver = properties["evaluation_context_for_resolver"]

        expression_to_evaluate = None
        if initial_typed_value_from_plugin.is_dynamic and initial_typed_value_from_plugin.original:
            expression_to_evaluate = converter.string_to_model(initial_typed_value_from_plugin.original)
        else:
            expression_to_evaluate = initial_typed_value_from_plugin.value

        resolved_val_raw, dynamic_info_from_eval = self._dynamic_service.evaluate(
            component_type="variable_load",
            component_label=key,
            attribute="value_load",
            expression=expression_to_evaluate,
            context=evaluation_context_for_resolver,
        )
        resolved_value_for_model = converter.model_to_py(resolved_val_raw, raw=True)
        self.logger.debug(
            f"Variable '{key}' resolved during load to: {resolved_value_for_model} (type: {type(resolved_value_for_model)})"
        )

        final_field_type = infer_type(resolved_value_for_model)
        final_is_dynamic = dynamic_info_from_eval.is_dynamic

        if initial_typed_value_from_plugin.original:
            final_original_expression_str = initial_typed_value_from_plugin.original
        elif dynamic_info_from_eval.original is not None:
            if isinstance(dynamic_info_from_eval.original, (Expression, Symbol)):
                final_original_expression_str = hy.repr(dynamic_info_from_eval.original)
            else:
                final_original_expression_str = str(dynamic_info_from_eval.original)
        else:
            final_original_expression_str = None

        typed_value_for_model = TypedValue(
            value=resolved_value_for_model,
            field_type=final_field_type,
            is_dynamic=final_is_dynamic,
            original=final_original_expression_str,
            item_type=initial_typed_value_from_plugin.item_type,
            enum_choices=initial_typed_value_from_plugin.enum_choices,
            item_schema_type=initial_typed_value_from_plugin.item_schema_type,
            referenced_entity_type=initial_typed_value_from_plugin.referenced_entity_type,
            referenced_entity_category=initial_typed_value_from_plugin.referenced_entity_category,
        )

        self.logger.debug(
            f"Variable '{key}' storing TypedValue in model: {repr(typed_value_for_model)}"
        )

        return self._manager.create(
            key=key,
            value=typed_value_for_model,
        )

    def process(self, nodes: List[HyNode], context: LoaderContext) -> Dict[str, Variable]:
        """
        Process variable nodes into Variable objects sequentially, updating the context
        with resolved variables as they are processed, to handle dependencies.
        """
        self.logger.debug("Starting VariableLoader processing with context: %s", context)
        self.context = context  # Set the loader's context

        if not context or context.variables is None:
            self.logger.warning(
                "LoaderContext or its variables is None. Initializing to empty dict."
            )
            context = LoaderContext(
                config_dir=self.context.config_dir if self.context else "", variables={}
            )

        definitions_by_label = self.parse_definitions(nodes)
        self.logger.debug("Parsed definitions for variables: %s", list(definitions_by_label.keys()))

        created_objects: Dict[str, Variable] = {}

        for node in nodes:
            if not self.validate_node(node, "def-var"):
                continue

            node_value_data = node.value
            if not isinstance(node_value_data, dict) or "name" not in node_value_data:
                self.logger.error(f"Invalid node value data for variable: {node_value_data}")
                continue

            var_name = node_value_data["name"]

            if var_name not in definitions_by_label:
                self.logger.warning(
                    f"Variable '{var_name}' from node list not found in parsed definitions. Skipping."
                )
                continue

            properties = definitions_by_label[var_name]  # Get properties (including TypedValue)

            try:
                current_evaluation_context_snapshot = context.variables.copy()
                properties["evaluation_context_for_resolver"] = current_evaluation_context_snapshot
                obj = self.create_object(var_name, properties)
                created_objects[var_name] = obj
                if obj.value.field_type == FieldType.CODE and isinstance(
                    obj.value.value, (Expression, Symbol)
                ):
                    context.variables[var_name] = obj.value.value
                else:
                    context.variables[var_name] = obj.value.value
                if "-" in var_name:
                    if obj.value.field_type == FieldType.CODE and isinstance(
                        obj.value.value, (Expression, Symbol)
                    ):
                        context.variables[var_name.replace("-", "_")] = obj.value.value
                    else:
                        context.variables[var_name.replace("-", "_")] = obj.value.value

                self.logger.debug(
                    f"Added '{var_name}' (value: {repr(obj.value.value)}) to context.variables for subsequent evaluations."
                )

            except Exception as e:
                self.logger.error(
                    f"Error creating object for variable '{var_name}': {e}", exc_info=True
                )
                raise

        self.logger.debug(
            f"VariableLoader processing finished. {len(created_objects)} objects processed/created via manager."
        )
        return created_objects
