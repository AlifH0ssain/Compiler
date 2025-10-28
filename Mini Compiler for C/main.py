# main.py
# Mini C Compiler + TAC Interpreter (with string literal support)

from lexical import tokenize
from parser import Parser, pretty_print_ast
from semantic import SemanticAnalyzer
from codegen import CodeGenerator
from optimizer import Optimizer
from targetgen import TargetCodeGenerator

def read_source(filename="test.c"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[ERROR] File '{filename}' not found!")
        return ""

def format_tac(tac):
    lines = []
    for instr in tac:
        op, a1, a2, res = instr
        if op == "FUNC":
            lines.append(f"{a1}:")
        elif op == "END_FUNC":
            lines.append(f"END {a1}")
        elif op == "PARAM_DECL":
            lines.append(f"  PARAM_DECL {a1}")
        elif op == "MOV":
            lines.append(f"  {res} = {a1}")
        elif op in ("PLUS", "MINUS", "MUL", "DIV", "EQ", "NE", "GT", "LT", "GE", "LE"):
            sym = {
                "PLUS": "+", "MINUS": "-", "MUL": "*", "DIV": "/",
                "EQ": "==", "NE": "!=", "GT": ">", "LT": "<", "GE": ">=", "LE": "<="
            }[op]
            lines.append(f"  {res} = {a1} {sym} {a2}")
        elif op == "RET":
            lines.append(f"  return {a1}")
        elif op == "PRINT":
            lines.append(f"  print {a1}")
        elif op == "IFZ_GOTO":
            lines.append(f"  IFZ {a1} -> {res}")
        elif op == "GOTO":
            lines.append(f"  GOTO {a1}")
        elif op == "LABEL":
            lines.append(f"{a1}:")
        elif op == "PARAM":
            lines.append(f"  PARAM {a1}")
        elif op == "CALL":
            lines.append(f"  CALL {a1}, {a2}")
        elif op == "POP":
            lines.append(f"  POP {res}")
        else:
            lines.append("  " + " ".join(str(x) for x in instr))
    return "\n".join(lines)

# TAC Interpreter (supports strings and numbers)
class TACInterpreter:
    def __init__(self, tac):
        self.tac = tac
        self.labels = {}      # label -> index
        self.functions = {}   # func_name -> FUNC index
        self.env_stack = []   # stack of env dicts for nested function executions
        self.params = []      # global param stack (flat)
        self.output = []
        self.return_value = 0

    def build_indices(self):
        for idx, (op, a1, a2, res) in enumerate(self.tac):
            if op == "LABEL" and a1:
                self.labels[a1] = idx
            if op == "FUNC" and a1:
                self.functions[a1] = idx

    def _is_string_literal(self, token_value):
        
        if token_value is None:
            return False
        return isinstance(token_value, str) and len(token_value) >= 2 and token_value[0] == '"' and token_value[-1] == '"'

    def get_val_from_env(self, env, val):

        if val is None:
            return 0
        
        if isinstance(val, int) or isinstance(val, str) and not val:
            pass

        if self._is_string_literal(val):
            return val[1:-1]  
        
        try:
            return int(val)
        except (ValueError, TypeError):

            if not self.env_stack:
                return 0

            for env in reversed(self.env_stack):
                if val in env:
                    return env[val]

            return 0

    def _ensure_int(self, v, op_name):
        if isinstance(v, str):
            # attempt to convert numeric-looking strings
            try:
                return int(v)
            except ValueError:
                raise RuntimeError(f"[Runtime] Cannot use string value '{v}' in numeric operation '{op_name}'")
        return v

    def run_func(self, func_name, args):

        if func_name not in self.functions:
            raise RuntimeError(f"[Runtime] Function '{func_name}' not found")

        # Create local environment and bind PARAM_DECL entries to args
        env = {}
        f_start = self.functions[func_name]
        pc = f_start + 1

        # Bind parameters according to PARAM_DECL entries in function prologue
        param_idx = 0
        while pc < len(self.tac) and self.tac[pc][0] == "PARAM_DECL":
            _, pname, _, _ = self.tac[pc]
            if param_idx < len(args):
                env[pname] = args[param_idx]
            else:
                env[pname] = 0
            param_idx += 1
            pc += 1

        # push env
        self.env_stack.append(env)

        ret_val = 0
        # execute until END_FUNC
        while pc < len(self.tac):
            op, a1, a2, res = self.tac[pc]

            if op == "END_FUNC":
                break

            if op == "MOV":
                val = self.get_val_from_env(env, a1)
                env[res] = val

            elif op in ("PLUS", "MINUS", "MUL", "DIV", "EQ", "NE", "GT", "LT", "GE", "LE"):
                left_raw = self.get_val_from_env(env, a1)
                right_raw = self.get_val_from_env(env, a2)

                if op in ("EQ", "NE"):

                    if isinstance(left_raw, str) or isinstance(right_raw, str):
                        result = int(str(left_raw) == str(right_raw)) if op == "EQ" else int(str(left_raw) != str(right_raw))
                    else:
                        left = self._ensure_int(left_raw, op)
                        right = self._ensure_int(right_raw, op)
                        result = int(left == right) if op == "EQ" else int(left != right)
                else:
                    left = self._ensure_int(left_raw, op)
                    right = self._ensure_int(right_raw, op)
                    if op == "PLUS":
                        result = left + right
                    elif op == "MINUS":
                        result = left - right
                    elif op == "MUL":
                        result = left * right
                    elif op == "DIV":
                        result = left // right if right != 0 else 0
                    elif op == "GT":
                        result = int(left > right)
                    elif op == "LT":
                        result = int(left < right)
                    elif op == "GE":
                        result = int(left >= right)
                    elif op == "LE":
                        result = int(left <= right)
                env[res] = result

            elif op == "PARAM":
                val = self.get_val_from_env(env, a1)
                self.params.append(val)

            elif op == "CALL":
                argc = int(a2) if a2 is not None else 0
                args_for_call = []

                if argc:
                    args_for_call = self.params[-argc:]
                    del self.params[-argc:]

                nested_ret = self.run_func(a1, args_for_call)
                env["ret"] = nested_ret

            elif op == "POP":
                env[res] = env.get("ret", 0)

            elif op == "PRINT":
                v = self.get_val_from_env(env, a1)

                if isinstance(v, str):
                    print(v)
                    self.output.append(v)
                else:
                    print(v)
                    self.output.append(str(v))

            elif op == "IFZ_GOTO":
                cond = self.get_val_from_env(env, a1)
                cond_int = self._ensure_int(cond, "IFZ_GOTO")

                if cond_int == 0:
                    pc = self.labels.get(res, pc)
                    continue

            elif op == "GOTO":
                pc = self.labels.get(a1, pc)
                continue

            elif op == "LABEL":
                pass

            elif op == "RET":
                ret_val = self.get_val_from_env(env, a1)
                self.env_stack.pop()
                return ret_val

            pc += 1

        # end function, pop env
        self.env_stack.pop()
        return ret_val

    def execute(self):
        self.build_indices()

        if "main" not in self.functions:
            raise RuntimeError("[Runtime] main() not found")

        # Call main with no args
        ret = self.run_func("main", [])
        self.return_value = ret
        return self.output, self.return_value


# Compiler pipeline + runtime execution 
def compile_source(filename="test.c"):
    print("===============================================")
    print("        MINI C COMPILER (Python")
    print("===============================================\n")

    src = read_source(filename)
    if not src:
        return

    print("[SOURCE CODE]")
    print(src.strip())
    print("-----------------------------------------------")

    # Lexical
    tokens = tokenize(src)
    print("[TOKENS]")
    for t in tokens:
        print("   ", t)
    print("-----------------------------------------------")

    # Parse
    parser = Parser(tokens)
    ast = parser.parse()
    print("[SYNTAX TREE / PARSE RESULT]")
    print(pretty_print_ast(ast))
    print("-----------------------------------------------")

    # Semantic
    analyzer = SemanticAnalyzer(ast)
    analyzer.analyze()
    print("[SEMANTIC CHECKS COMPLETED]")
    print("-----------------------------------------------")

    # CodeGen
    codegen = CodeGenerator(ast)
    tac = codegen.generate()
    print("[INTERMEDIATE CODE (TAC)]")
    print(format_tac(tac))
    print("-----------------------------------------------")

    # Optimize
    optimizer = Optimizer(tac)
    opt = optimizer.optimize()
    print("[OPTIMIZED TAC]")
    print(format_tac(opt))
    print("-----------------------------------------------")

    # Target generation (for inspection)
    targetgen = TargetCodeGenerator(opt)
    target = targetgen.generate()
    print("[TARGET CODE]")
    for line in target:
        print("   ", line)
    print("-----------------------------------------------")

    # Execute program
    print("[PROGRAM OUTPUT]")
    vm = TACInterpreter(opt)
    outputs, ret_val = vm.execute()
    print("-----------------------------------------------")
    print(f"Program exited with return value: {ret_val}")
    print("Compilation and Execution Successful!")


if __name__ == "__main__":
    compile_source("test.c")
