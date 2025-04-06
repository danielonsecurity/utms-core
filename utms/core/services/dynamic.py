from typing import Any, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field


from utms.core.hy.resolvers.base import HyResolver
from utms.utms_types import DynamicExpressionInfo
from utms.core.mixins.service import ServiceMixin

@dataclass
class DynamicRegistry:
    _data: Dict[str, Dict[str, Dict[str, DynamicExpressionInfo]]] = field(default_factory=dict)
    
    def add(
        self,
        component_type: str,
        component_label: str,
        attribute: str,
        dynamic_info: DynamicExpressionInfo
    ) -> None:
        """Register a dynamic expression"""
        if component_type not in self._data:
            self._data[component_type] = {}
        if component_label not in self._data[component_type]:
            self._data[component_type][component_label] = {}
        self._data[component_type][component_label][attribute] = dynamic_info
    
    def get(
        self,
        component_type: str,
        component_label: str,
        attribute: str
    ) -> Optional[DynamicExpressionInfo]:
        """Retrieve a specific dynamic expression"""
        try:
            return self._data[component_type][component_label][attribute]
        except KeyError:
            return None
    
    def get_component(
        self,
        component_type: str,
        component_label: str
    ) -> Dict[str, DynamicExpressionInfo]:
        """Get all dynamic expressions for an component"""
        try:
            return self._data[component_type][component_label]
        except KeyError:
            return {}
    
    def get_type(
        self,
        component_type: str
    ) -> Dict[str, Dict[str, DynamicExpressionInfo]]:
        """Get all dynamic expressions for an component type"""
        return self._data.get(component_type, {})
    
    def clear(
        self,
        component_type: Optional[str] = None,
        component_label: Optional[str] = None,
        attribute: Optional[str] = None
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
        context: Optional[Dict[str, Any]] = None
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
        self.logger.debug(
            "Evaluating expression for %s.%s.%s: %s",
            component_type, component_label, attribute, expression
        )
        locals_dict = self.resolver.get_locals_dict(context)
        if context:
            locals_dict.update(context)
        resolved_value, dynamic_info = self.resolver.resolve(expression,
                                                             context=context,
                                                             local_names=locals_dict)
        self.logger.debug(f"Resolved to: {resolved_value}")

        self.registry.add(component_type, component_label, attribute, dynamic_info)
        return resolved_value, dynamic_info

    def get_dynamic_info(
        self,
        component_type: str,
        component_label: str,
        attribute: str
    ) -> Optional[DynamicExpressionInfo]:
        """
        Retrieve dynamic expression information for a specific attribute
        """
        try:
            return self._registry[component_type][component_label][attribute]
        except KeyError:
            return None

    def get_component_dynamic_info(
        self,
        component_type: str,
        component_label: str
    ) -> Dict[str, DynamicExpressionInfo]:
        """
        Get all dynamic expressions for an component
        """
        try:
            return self._registry[component_type][component_label]
        except KeyError:
            return {}

    def get_type_dynamic_info(
        self,
        component_type: str
    ) -> Dict[str, Dict[str, DynamicExpressionInfo]]:
        """
        Get all dynamic expressions for an component type
        """
        return self._registry.get(component_type, {})

    def evaluate_all(
        self,
        component_type: Optional[str] = None,
        component_label: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Re-evaluate all dynamic expressions, optionally filtered by component type and/or id
        
        Returns:
            Dictionary of updated values
        """
        results = {}
        
        # Determine which entities to process
        if component_type:
            types_to_process = [component_type]
        else:
            types_to_process = list(self._registry.keys())
            
        for type_name in types_to_process:
            results[type_name] = {}
            
            if component_label:
                labels_to_process = [component_label]
            else:
                labels_to_process = list(self._registry[type_name].keys())
                
            for ent_label in labels_to_process:
                results[type_name][ent_label] = {}
                
                for attr, dynamic_info in self._registry[type_name][ent_label].items():
                    try:
                        value, _ = self.resolver.resolve(
                            dynamic_info.original,
                            context
                        )
                        results[type_name][ent_label][attr] = value
                    except Exception as e:
                        self.logger.error(
                            "Error evaluating %s.%s.%s: %s",
                            type_name, ent_label, attr, str(e)
                        )
                        results[type_name][ent_label][attr] = f"Error: {str(e)}"
        
        return results

    def clear_history(
        self,
        component_type: Optional[str] = None,
        component_label: Optional[str] = None,
        attribute: Optional[str] = None,
        before: Optional[datetime] = None
    ) -> None:
        """
        Clear evaluation history, optionally filtered by component type, id, and/or attribute
        If before is provided, only clears history before that timestamp
        """
        if component_type and component_label and attribute:
            # Clear specific attribute
            dynamic_info = self.get_dynamic_info(component_type, component_label, attribute)
            if dynamic_info and dynamic_info.history:
                if before:
                    dynamic_info.history = [
                        record for record in dynamic_info.history 
                        if record.timestamp >= before
                    ]
                else:
                    dynamic_info.history.clear()
        elif component_type and component_label:
            # Clear all attributes for an component
            for dynamic_info in self.get_component_dynamic_info(component_type, component_label).values():
                if before:
                    dynamic_info.history = [
                        record for record in dynamic_info.history 
                        if record.timestamp >= before
                    ]
                else:
                    dynamic_info.history.clear()
        elif component_type:
            # Clear all entities of a type
            for component_dict in self.get_type_dynamic_info(component_type).values():
                for dynamic_info in component_dict.values():
                    if before:
                        dynamic_info.history = [
                            record for record in dynamic_info.history 
                            if record.timestamp >= before
                        ]
                    else:
                        dynamic_info.history.clear()

# Global service instance
dynamic_resolution_service = DynamicResolutionService()
