import ast
import operator
import functools

class SmartContract:
    """
    A safe, lightweight interpreter for validating transaction conditions.
    Supports basic arithmetic, comparisons, and logical operators.
    """
    
    def __init__(self):
        self.allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.BitXor: operator.xor,
            ast.USub: operator.neg,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            # Logical operators are handled differently in AST but we map them for concept
        }

    def validate(self, condition_script: str, context: dict) -> bool:
        """
        Evaluates a condition script against a context.
        Example script: "amount >= 5 and recipient == 'bob'"
        """
        if not condition_script:
            return True
            
        try:
            tree = ast.parse(condition_script, mode='eval')
            return bool(self._eval_node(tree.body, context))
        except Exception as e:
            print(f"Smart Contract Execution Error: {e}")
            return False

    def _eval_node(self, node, context):
        if isinstance(node, ast.Constant): # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num): # Python < 3.8
            return node.n
        elif isinstance(node, ast.Str): # Python < 3.8
            return node.s
        elif isinstance(node, ast.Name):
            val = context.get(node.id)
            if val is None:
                raise ValueError(f"Variable '{node.id}' not found in context")
            return val
        elif isinstance(node, ast.BinOp):
            op = self.allowed_operators.get(type(node.op))
            if not op:
                raise ValueError(f"Operator {type(node.op)} not supported")
            return op(self._eval_node(node.left, context), self._eval_node(node.right, context))
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                op_func = self.allowed_operators.get(type(op))
                if not op_func:
                    raise ValueError(f"Comparator {type(op)} not supported")
                right = self._eval_node(comparator, context)
                if not op_func(left, right):
                    return False
                left = right
            return True
        elif isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, context) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)
        elif isinstance(node, ast.UnaryOp):
            op = self.allowed_operators.get(type(node.op))
            if not op:
                raise ValueError(f"Unary operator {type(node.op)} not supported")
            return op(self._eval_node(node.operand, context))
            
        raise ValueError(f"Syntax not supported: {type(node)}")
