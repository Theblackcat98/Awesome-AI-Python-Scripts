from typing import Any, Dict
import math
import ast
import operator
from .base_tool import BaseTool

class CalculatorTool(BaseTool):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Safe operators for evaluation
        self.safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.Mod: operator.mod,
        }

        # Safe functions and constants
        self.safe_functions = {
            'abs': abs,
            'round': round,
            'max': max,
            'min': min,
            'sum': sum,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
        }

    @property
    def name(self) -> str:
        return "calculate"

    @property
    def description(self) -> str:
        return "Perform mathematical calculations and evaluations using a safe interpreter. Supports basic arithmetic, powers, square roots, trigonometric functions, logarithms, and constants like pi and e."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)', 'log(100)')."
                }
            },
            "required": ["expression"]
        }

    def _safe_eval(self, node: ast.expr):
        """Safely evaluate an AST node, restricting operations and functions."""
        if isinstance(node, ast.Constant):
            # Only allow numeric constants (int, float)
            if isinstance(node.value, (int, float)):
                return node.value
            else:
                raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.Name):
            # Check for allowed safe functions/constants (e.g., pi, e)
            if node.id in self.safe_functions:
                return self.safe_functions[node.id]
            else:
                raise ValueError(f"Unknown or disallowed identifier: {node.id}")
        elif isinstance(node, ast.BinOp):
            # Evaluate left and right operands, then apply safe binary operator
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            op_type = type(node.op)
            if op_type in self.safe_operators:
                return self.safe_operators[op_type](left, right)
            else:
                raise ValueError(f"Unsupported binary operation: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            # Evaluate operand, then apply safe unary operator
            operand = self._safe_eval(node.operand)
            op_type = type(node.op)
            if op_type in self.safe_operators:
                return self.safe_operators[op_type](operand)
            else:
                raise ValueError(f"Unsupported unary operation: {op_type.__name__}")
        elif isinstance(node, ast.Call):
            # Evaluate function, then its arguments, then call it
            func = self._safe_eval(node.func)
            if not callable(func):
                raise ValueError(f"Attempted to call non-callable object: {func}")
            if func not in self.safe_functions.values(): # Ensure only registered safe functions are called
                 raise ValueError(f"Attempted to call disallowed function: {func.__name__}")

            args = [self._safe_eval(arg) for arg in node.args]
            return func(*args)
        elif isinstance(node, ast.Expr): # Top-level expression node
            return self._safe_eval(node.value)
        else:
            raise ValueError(f"Unsupported or unsafe expression type: {type(node).__name__}")

    def execute(self, expression: str) -> Dict[str, Any]:
        """
        Executes a mathematical calculation safely.

        Args:
            expression: The mathematical expression string to evaluate.

        Returns:
            A dictionary containing the result or an error message.
        """
        try:
            # Parse the expression into an Abstract Syntax Tree (AST)
            # 'mode='eval'' ensures it's a single expression, not arbitrary code.
            tree = ast.parse(expression, mode='eval')

            # Safely evaluate the AST
            result = self._safe_eval(tree.body)

            return {
                "expression": expression,
                "result": result,
                "success": True
            }

        except ValueError as ve:
            # Catch errors from _safe_eval for disallowed operations/variables
            return {
                "expression": expression,
                "error": f"Evaluation error: {str(ve)}",
                "success": False
            }
        except SyntaxError as se:
            # Catch syntax errors in the expression
            return {
                "expression": expression,
                "error": f"Syntax error in expression: {str(se)}",
                "success": False
            }
        except Exception as e:
            # Catch any other unexpected errors during evaluation
            return {
                "expression": expression,
                "error": f"An unexpected error occurred: {type(e).__name__}: {str(e)}",
                "success": False
            }