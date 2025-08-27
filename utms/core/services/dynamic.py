from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import hy
from hy.models import Expression, Symbol

from utms.core.hy import evaluate_hy_expression
from utms.core.hy.resolvers.base import HyResolver
from utms.core.hy.resolvers.elements.variable import VariableResolver
from utms.core.mixins.service import ServiceMixin
from utms.utms_types import DynamicExpressionInfo, HyExpression


@dataclass
class DynamicRegistry:
    _data: Dict[str, Dict[str, Dict[str, DynamicExpressionInfo]]] = field(default_factory=dict)

    def add(
        self,
        component_type: str,
        component_label: str,
        attribute: str,
        dynamic_info: DynamicExpressionInfo,
    ) -> None:
        """Register a dynamic expression"""
        if component_type not in self._data:
            self._data[component_type] = {}
        if component_label not in self._data[component_type]:
            self._data[component_type][component_label] = {}
        self._data[component_type][component_label][attribute] = dynamic_info

    def get(
        self, component_type: str, component_label: str, attribute: str
    ) -> Optional[DynamicExpressionInfo]:
        """Retrieve a specific dynamic expression"""
        try:
            return self._data[component_type][component_label][attribute]
        except KeyError:
            return None

    def get_component(
        self, component_type: str, component_label: str
    ) -> Dict[str, DynamicExpressionInfo]:
        """Get all dynamic expressions for an component"""
        try:
            return self._data[component_type][component_label]
        except KeyError:
            return {}

    def get_type(self, component_type: str) -> Dict[str, Dict[str, DynamicExpressionInfo]]:
        """Get all dynamic expressions for an component type"""
        return self._data.get(component_type, {})

    def clear(
        self,
        component_type: Optional[str] = None,
        component_label: Optional[str] = None,
        attribute: Optional[str] = None,
    ) -> None:
        """Clear registry entries"""
        if component_type and component_label and attribute:
            if self.get(component_type, component_label, attribute):
                del self._data[component_type][component_label][attribute]
        elif component_type and component_label:
            if component_label in self._data.get(component_type, {}):
                del self._data[component_type][component_label]
        elif component_type:
            if component_type in self._data:
                del self._data[component_type]
        else:
            self._data.clear()

    def __iter__(self):
        """Iterate over all entries"""
        for component_type, entities in self._data.items():
            for component_label, attributes in entities.items():
                for attribute, dynamic_info in attributes.items():
                    yield component_type, component_label, attribute, dynamic_info


class DynamicResolutionService(ServiceMixin):
    """
    Central service for managing dynamic expression resolution

    Responsibilities:
    - Coordinate dynamic expression resolution across different component types
    - Provide a unified interface for re-evaluation
    - Track and manage dynamic expressions
    """

    def __init__(self, resolver: Optional[HyResolver] = None):
        """
        Initialize the dynamic resolution service

        Args:
            resolver: Optional custom resolver, defaults to base HyResolver
        """
        self.resolver = resolver or HyResolver()
        self.registry = DynamicRegistry()

    def evaluate(
        self,
        component_type: str,
        component_label: str,
        attribute: str,
        expression: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, DynamicExpressionInfo]:
        """
        Evaluate an expression and track its result

        Args:
            component_type: Type of component (e.g., 'anchor', 'config')
            component_label: Identifier of the component (e.g., 'MONTHSTART', 'random-number')
            attribute: Name of the attribute being evaluated (e.g., 'start', 'value')
            expression: The expression to evaluate
            context: Optional context for evaluation

        Returns:
            Tuple of (resolved_value, dynamic_expression_info)
        """
        try:
            expr_str = hy.repr(expression)
        except Exception:
            expr_str = str(expression)
        self.logger.info(
            f"\n"
            f"--- [AUDIT] DYNAMIC EVALUATION TRIGGERED ---\n"
            f"    WHAT: {expr_str}\n"
            f"    FOR:  {component_type} -> {component_label}\n"
            f"    ATTR: {attribute}\n"
            f"--------------------------------------------\n"
        )
        self.logger.debug(
            "DynamicResolutionService: Evaluating for %s.%s.%s: EXPR=%s, CONTEXT_KEYS=%s",
            component_type,
            component_label,
            attribute,
            expression,
            list(context.keys()) if context else "None",
        )
        hy_expr_to_resolve: Any  # Can be Hy object or already Python native
        if isinstance(expression, str):
            try:
                hy_expr_to_resolve = hy.read(expression)
            except Exception as e:
                self.logger.error(
                    f"Failed to hy.read string expression '{expression}' for {component_label}.{attribute}: {e}"
                )
                # Create and register error info
                error_info = DynamicExpressionInfo(original=expression, is_dynamic=True)
                error_info.add_evaluation(
                    None,
                    metadata={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "component_type": component_type,
                        "component_label": component_label,
                        "attribute": attribute,
                        "context_keys": list(context.keys()) if context else None,
                    },
                )
                self.registry.add(component_type, component_label, attribute, error_info)
                raise
        else:
            hy_expr_to_resolve = expression

        try:
            resolved_value, dynamic_info_from_resolver = self.resolver.resolve(
                expr=hy_expr_to_resolve, local_names=context, context=None
            )
            self.logger.debug(
                f"DynamicResolutionService: Resolved value for {component_label}.{attribute}: {resolved_value}"
            )
            self.registry.add(
                component_type, component_label, attribute, dynamic_info_from_resolver
            )
            return resolved_value, dynamic_info_from_resolver

        except Exception as e:
            self.logger.error(
                f"Error during resolver.resolve for {component_label}.{attribute} (expr: {expression}): {e}",
                exc_info=True,
            )
            dynamic_info = self.registry.get(component_type, component_label, attribute)
            if not dynamic_info:
                is_dynamic_flag = isinstance(hy_expr_to_resolve, (Expression, Symbol))
                dynamic_info = DynamicExpressionInfo(
                    original=hy_expr_to_resolve, is_dynamic=is_dynamic_flag
                )

            dynamic_info.add_evaluation(
                None,
                original_expr=hy_expr_to_resolve,  # Record the expression that caused error
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "component_type": component_type,
                    "component_label": component_label,
                    "attribute": attribute,
                    "context_keys": list(context.keys()) if context else None,
                },
            )
            self.registry.add(component_type, component_label, attribute, dynamic_info)
            raise

    def get_dynamic_info(
        self, component_type: str, component_label: str, attribute: str
    ) -> Optional[DynamicExpressionInfo]:
        """
        Retrieve dynamic expression information for a specific attribute
        """
        try:
            return self._registry[component_type][component_label][attribute]
        except KeyError:
            return None

    def get_component_dynamic_info(
        self, component_type: str, component_label: str
    ) -> Dict[str, DynamicExpressionInfo]:
        """
        Get all dynamic expressions for an component
        """
        try:
            return self._registry[component_type][component_label]
        except KeyError:
            return {}

    def get_type_dynamic_info(
        self, component_type: str
    ) -> Dict[str, Dict[str, DynamicExpressionInfo]]:
        """
        Get all dynamic expressions for an component type
        """
        return self._registry.get(component_type, {})

    def evaluate_all(
        self,
        component_type: Optional[str] = None,
        component_label: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Re-evaluate all dynamic expressions, optionally filtered by component type and/or id

        Returns:
            Dictionary of updated values
        """
        results = {}

        for reg_comp_type, reg_comp_label, reg_attr, dynamic_info in self.registry:
            if component_type and reg_comp_type != component_type:
                continue
            if component_label and reg_comp_label != component_label:
                continue

            try:
                value, updated_dynamic_info = self.evaluate(
                    component_type=reg_comp_type,
                    component_label=reg_comp_label,
                    attribute=reg_attr,
                    expression=dynamic_info.original,
                    context=context,
                )
                # Store result
                if reg_comp_type not in results:
                    results[reg_comp_type] = {}
                if reg_comp_label not in results[reg_comp_type]:
                    results[reg_comp_type][reg_comp_label] = {}
                results[reg_comp_type][reg_comp_label][reg_attr] = value

            except Exception as e:
                self.logger.error(
                    "Error re-evaluating %s.%s.%s: %s",
                    reg_comp_type,
                    reg_comp_label,
                    reg_attr,
                    str(e),
                )
                if reg_comp_type not in results:
                    results[reg_comp_type] = {}
                if reg_comp_label not in results[reg_comp_type]:
                    results[reg_comp_type][reg_comp_label] = {}
                results[reg_comp_type][reg_comp_label][reg_attr] = f"Error: {str(e)}"
        return results

    def clear_history(
        self,
        component_type: Optional[str] = None,
        component_label: Optional[str] = None,
        attribute: Optional[str] = None,
        before: Optional[datetime] = None,
    ) -> None:
        """
        Clear evaluation history, optionally filtered by component type, id, and/or attribute
        If before is provided, only clears history before that timestamp
        """
        for reg_comp_type, reg_comp_label, reg_attr, dynamic_info in self.registry:
            if component_type and reg_comp_type != component_type:
                continue
            if component_label and reg_comp_label != component_label:
                continue
            if attribute and reg_attr != attribute:
                continue

            if dynamic_info and dynamic_info.history:
                if before:
                    dynamic_info.history = [
                        record for record in dynamic_info.history if record.timestamp >= before
                    ]
                else:
                    dynamic_info.history.clear()


# Global service instance
dynamic_resolution_service = DynamicResolutionService(resolver=VariableResolver())
