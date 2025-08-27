import hy
from hy.compiler import HyASTCompiler
from datetime import datetime
from decimal import Decimal
from typing import Any
from utms.core.time.decimal import DecimalTimeStamp, DecimalTimeLength, DecimalTimeRange


def list_to_dict(flat_list: list) -> dict:
    if isinstance(flat_list, hy.models.Dict):
        flat_list = list(flat_list)
    if not isinstance(flat_list, list):
        raise TypeError(f"Input must be a list, not {type(flat_list)}")
    return dict(zip(flat_list[::2], flat_list[1::2]))


def py_list_to_hy_expression(py_list: list) -> hy.models.Expression:
    """
    SPECIALIST CONVERSION: Python List representing CODE -> Hy Expression AST.
    """
    elements = []
    for item in py_list:
        if isinstance(item, list):
            elements.append(py_list_to_hy_expression(item))
        else:
            elements.append(converter.py_to_model(item))

    if len(elements) > 0 and isinstance(elements[0], hy.models.String):
        elements[0] = hy.models.Symbol(str(elements[0]))

    return hy.models.Expression(elements)


class HyConverter:
    def __init__(self):
        self._compiler = HyASTCompiler(hy)

    def py_to_model(self, value: Any) -> hy.models.Object:
        if isinstance(value, hy.models.Object):
            return value
        if isinstance(value, datetime):
            return hy.models.Expression(
                [
                    hy.models.Symbol("datetime"),
                    hy.models.Integer(value.year),
                    hy.models.Integer(value.month),
                    hy.models.Integer(value.day),
                    hy.models.Integer(value.hour),
                    hy.models.Integer(value.minute),
                    hy.models.Integer(value.second),
                    hy.models.Integer(value.microsecond),
                ]
            )
        if isinstance(value, Decimal):
            return hy.models.Expression([hy.models.Symbol("Decimal"), hy.models.String(str(value))])
        if isinstance(value, DecimalTimeStamp):
            return hy.models.Expression(
                [hy.models.Symbol("DecimalTimeStamp"), self.py_to_model(value.value)]
            )
        if isinstance(value, DecimalTimeLength):
            return hy.models.Expression(
                [hy.models.Symbol("DecimalTimeLength"), self.py_to_model(value.value)]
            )
        if isinstance(value, DecimalTimeRange):
            return hy.models.Expression(
                [
                    hy.models.Symbol("DecimalTimeRange"),
                    self.py_to_model(value.start),
                    self.py_to_model(value.duration),
                ]
            )
        if isinstance(value, dict):
            return hy.models.Dict(
                [
                    val
                    for pair in value.items()
                    for val in (hy.models.Keyword(str(pair[0])), self.py_to_model(pair[1]))
                ]
            )
        if isinstance(value, list):
            return hy.models.List([self.py_to_model(item) for item in value])
        if isinstance(value, bool):
            return hy.models.Symbol("True") if value else hy.models.Symbol("False")
        if isinstance(value, str):
            return hy.models.String(value)
        if isinstance(value, int):
            return hy.models.Integer(value)
        if isinstance(value, float):
            return hy.models.Float(value)
        if value is None:
            return hy.models.Symbol("None")
        return hy.models.String(str(value))

    def model_to_py(self, model: Any, *, raw: bool = False) -> Any:
        if raw:
            if isinstance(model, dict):
                return { self.model_to_py(k, raw=True): self.model_to_py(v, raw=True) for k, v in model.items() }
            if isinstance(model, (hy.models.String, hy.models.Symbol)):
                return str(model)
            if isinstance(model, hy.models.Integer):
                return int(model)
            if isinstance(model, hy.models.Float):
                return float(model)
            if isinstance(model, hy.models.Keyword):
                return str(model)[1:]
            if isinstance(model, (hy.models.List, hy.models.Expression, list, tuple)):
                return [self.model_to_py(item, raw=True) for item in model]
            if isinstance(model, hy.models.Dict):
                return [self.model_to_py(item, raw=True) for item in model]
            return model
        if isinstance(model, dict):
            return {
                self.model_to_py(k): self.model_to_py(v) 
                for k, v in model.items()
            }
        if isinstance(model, hy.models.Expression):
            if len(model) > 0:
                first_el_str = str(model[0])
                try:
                    if first_el_str == "datetime":
                        return datetime(*[self.model_to_py(arg) for arg in model[1:]])
                    if first_el_str == "Decimal":
                        return Decimal(self.model_to_py(model[1]))
                    if first_el_str == "DecimalTimeStamp":
                        return DecimalTimeStamp(self.model_to_py(model[1]))
                    if first_el_str == "DecimalTimeLength":
                        return DecimalTimeLength(self.model_to_py(model[1]))
                    if first_el_str == "DecimalTimeRange":
                        return DecimalTimeRange(
                            self.model_to_py(model[1]), self.model_to_py(model[2])
                        )
                except Exception:
                    pass
            return [self.model_to_py(item) for item in model]
        elif isinstance(model, hy.models.Dict):
            py_dict = {}
            it = iter(model)
            for key in it:
                value = next(it)
                py_dict[self.model_to_py(key)] = self.model_to_py(value)
            return py_dict
        elif isinstance(model, (hy.models.List, list, tuple)):
            return [self.model_to_py(item) for item in model]
        elif isinstance(model, hy.models.Symbol):
            s = str(model)
            if s == "True":
                return True
            if s == "False":
                return False
            if s == "None":
                return None
            return s
        elif isinstance(model, hy.models.String):
            return str(model)
        elif isinstance(model, hy.models.Integer):
            return int(model)
        elif isinstance(model, hy.models.Float):
            return float(model)
        elif isinstance(model, hy.models.Keyword):
            return str(model)[1:]
        return model

    def model_to_py_preserving_quoted_expressions(self, model: Any) -> Any:
        """
        Recursively converts a Hy model or hybrid object to a pure Python object,
        WITH ONE EXCEPTION: if it encounters a `(quote ...)` expression, it
        returns the inner expression object (`(start-occurrence...)`), preserving it as an AST node.
        """
        if isinstance(model, hy.models.Expression) and model and str(model[0]) == 'quote':
            return model[1]
        if isinstance(model, dict):
            return {
                self.model_to_py(k): self.model_to_py_preserving_quoted_expressions(v)
                for k, v in model.items()
            }
        
        if isinstance(model, (list, tuple, hy.models.List)):
            return [self.model_to_py_preserving_quoted_expressions(item) for item in model]
        return self.model_to_py(model)

    def model_to_string(self, model: hy.models.Object) -> str:
        """Renders a Hy AST model back into a clean Hy source string."""
        if isinstance(model, hy.models.String):
            return f'"{str(model)}"'
        elif isinstance(model, hy.models.Symbol):
            return str(model)
        elif isinstance(model, hy.models.Integer):
            return str(int(model))
        elif isinstance(model, hy.models.Float):
            return str(float(model))
        elif isinstance(model, hy.models.Keyword):
            return str(model)
        elif isinstance(model, hy.models.List):
            elements = [self.model_to_string(item) for item in model]
            return f"[{' '.join(elements)}]"
        elif isinstance(model, hy.models.Expression):
            elements = [self.model_to_string(item) for item in model]
            return f"({' '.join(elements)})"
        elif isinstance(model, hy.models.Dict):
            elements = []
            it = iter(model)
            for key in it:
                value = next(it)
                elements.append(self.model_to_string(key))
                elements.append(self.model_to_string(value))
            return f"{{{' '.join(elements)}}}"
        else:
            return str(model)

    def string_to_model(self, source: str) -> hy.models.Object:
        return hy.read(source)

    def py_to_string(self, value: Any) -> str:
        return self.model_to_string(self.py_to_model(value))

    def string_to_py(self, source: str, *, raw: bool = False) -> Any:
        return self.model_to_py(self.string_to_model(source), raw=raw)


converter = HyConverter()
