from decimal import Decimal

from hy.models import Expression, Integer, List, String, Symbol

from .hy_loader import evaluate_hy_expression


class HyResolver:
    def resolve(self, expr, context=None, local_names=None):
        """Main resolution method"""
        if isinstance(expr, (Integer, float, int, Decimal, complex)):
            return expr
        elif isinstance(expr, String):
            return str(expr)
        elif isinstance(expr, Symbol):
            return self._resolve_symbol(expr, context, local_names)
        elif isinstance(expr, List):
            return self._resolve_list(expr, context, local_names)
        elif isinstance(expr, Expression):
            return self._resolve_expression(expr, context, local_names)
        else:
            return expr

    def _resolve_symbol(self, expr, context, local_names=None):
        
        """Base symbol resolution - override in subclasses if needed"""
        if local_names and str(expr) in local_names:
            return local_names[str(expr)]
        return expr

    def _resolve_list(self, expr, context, local_names=None):
        return [
            (
                self.resolve(item, context, local_names)
                if isinstance(item, (Expression, Symbol, List))
                else item
            )
            for item in expr
        ]

    def _resolve_expression(self, expr, context, local_names=None):
        if local_names is None:
            local_names = {}

        resolved_subexprs = []
        for subexpr in expr:
            if isinstance(subexpr, Expression):
                resolved = self.resolve(subexpr, context, local_names)
                resolved_subexprs.append(subexpr if callable(resolved) else resolved)
            else:
                resolved_subexprs.append(subexpr)

        locals_dict = self.get_locals_dict(context, local_names)

        try:
            return evaluate_hy_expression(Expression(resolved_subexprs), locals_dict)
        except NameError:
            # Return the unresolved expression to be handled later
            return Expression(resolved_subexprs)
        except Exception as e:
            print(f"Error evaluating expression: {expr}")
            raise e

    def get_locals_dict(self, context, local_names):
        """Override this in subclasses to provide context-specific locals"""
        return local_names or {}
