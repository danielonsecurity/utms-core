import hy
from typing import Dict, Any
from ..utils import get_logger
from ..utms_types import HyExpression, Context, LocalsDict, ResolvedValue, is_expression

from .hy_resolver import HyResolver

logger = get_logger("resolvers.fixed_unit_resolver")

class FixedUnitResolver:
    def resolve(self, expr: hy.models.Expression) -> Dict[str, Dict[str, Any]]:
        if not isinstance(expr, hy.models.Expression):
            return {}

        try:
            if str(expr[0]) == "def-fixed-unit":
                unit_label = str(expr[1])
                unit_data = {"name": "", "value": "", "groups": []}
                
                # Process each property (name, value, groups)
                for prop in expr[2:]:
                    if isinstance(prop, hy.models.Expression):
                        prop_name = str(prop[0])
                        if prop_name == "name":
                            unit_data["name"] = str(prop[1])
                        elif prop_name == "value":
                            unit_data["value"] = str(prop[1])
                        elif prop_name == "groups":
                            # Convert Hy list of strings to Python list
                            unit_data["groups"] = [
                                str(g) for g in prop[1]
                            ]

                return {unit_label: unit_data}
                
        except Exception as e:
            print(f"Error resolving unit expression: {e}")
            
        return {}

