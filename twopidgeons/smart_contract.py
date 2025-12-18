import ast
import operator
import functools
import struct

# OpCodes mapping for C VM
OP_HALT = 0x00
OP_PUSH = 0x01
OP_LOAD = 0x02
OP_ADD  = 0x10
OP_SUB  = 0x11
OP_MUL  = 0x12
OP_DIV  = 0x13
OP_EQ   = 0x20
OP_GT   = 0x21
OP_LT   = 0x22
OP_AND  = 0x30
OP_OR   = 0x31
OP_NOT  = 0x32

class Compiler(ast.NodeVisitor):
    def __init__(self):
        self.bytecode = bytearray()
        self.variables = []

    def compile(self, expr: str):
        tree = ast.parse(expr, mode='eval')
        self.visit(tree.body)
        self.bytecode.append(OP_HALT)
        return bytes(self.bytecode), self.variables

    def visit_Constant(self, node):
        self.bytecode.append(OP_PUSH)
        # Pack as double (8 bytes)
        try:
            val = float(node.value)
            self.bytecode.extend(struct.pack("d", val))
        except ValueError:
            # Handle strings or other types? VM only supports doubles for now.
            # For simplicity, we treat strings as 0.0 or raise error
            raise ValueError(f"Only numeric constants supported in C VM. Got: {node.value}")

    def visit_Name(self, node):
        if node.id not in self.variables:
            self.variables.append(node.id)
        idx = self.variables.index(node.id)
        self.bytecode.append(OP_LOAD)
        self.bytecode.append(idx)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        if isinstance(node.op, ast.Add): self.bytecode.append(OP_ADD)
        elif isinstance(node.op, ast.Sub): self.bytecode.append(OP_SUB)
        elif isinstance(node.op, ast.Mult): self.bytecode.append(OP_MUL)
        elif isinstance(node.op, ast.Div): self.bytecode.append(OP_DIV)
        else: raise ValueError("Unknown op")

    def visit_Compare(self, node):
        # Simplified: only supports single comparison for now (a > b)
        self.visit(node.left)
        self.visit(node.comparators[0])
        op = node.ops[0]
        if isinstance(op, ast.Eq): self.bytecode.append(OP_EQ)
        elif isinstance(op, ast.Gt): self.bytecode.append(OP_GT)
        elif isinstance(op, ast.Lt): self.bytecode.append(OP_LT)
        else: raise ValueError("Unknown comparison op")

    def visit_BoolOp(self, node):
        # Handle AND/OR
        # For simplicity, we just visit all values and apply op sequentially
        # This is not short-circuiting like Python, but works for logic
        self.visit(node.values[0])
        for val in node.values[1:]:
            self.visit(val)
            if isinstance(node.op, ast.And): self.bytecode.append(OP_AND)
            elif isinstance(node.op, ast.Or): self.bytecode.append(OP_OR)

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
            
        # Try to use C VM first
        try:
            from . import vm_module
            compiler = Compiler()
            bytecode, vars_needed = compiler.compile(condition_script)
            
            # Prepare values list
            values = []
            for var_name in vars_needed:
                val = context.get(var_name)
                if val is None: raise ValueError(f"Missing var {var_name}")
                # Convert strings to numbers if possible, or fail
                # The VM currently only supports doubles.
                # If the script uses strings (recipient == 'bob'), the compiler will fail
                # and we fall back to Python interpreter.
                values.append(float(val))
                
            return vm_module.execute(bytecode, values)
            
        except (ImportError, ValueError, Exception) as e:
            # Fallback to Python interpreter if C VM fails (e.g. string operations)
            # print(f"VM fallback to Python: {e}")
            pass

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
