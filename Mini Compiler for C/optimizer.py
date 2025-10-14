# Optimizer for Mini C Compiler
# ------------------------------------------------------------
# Simple passes:
#   - Constant folding when both operands numeric
#   - Propagate MOV temporaries (tX -> literal or expression) where safe
#   - Do not collapse control-flow instructions (LABEL, IFZ_GOTO, GOTO, FUNC, CALL, PARAM, POP)
# ------------------------------------------------------------

class Optimizer:
    def __init__(self, tac):
        self.tac = tac

    def optimize(self):
        # Keep control-flow ops and structured arithmetic as separate ops
        optimized = []
        temp_map = {}  # map temp -> value (literal or expression string)

        def resolve(x):
            return temp_map.get(x, x)

        for op, a1, a2, res in self.tac:
            # keep these ops unchanged (but resolve their args if mapped)
            if op in ("LABEL", "GOTO", "IFZ_GOTO", "FUNC", "END_FUNC", "PARAM", "CALL", "POP", "PARAM_DECL"):
                if a1 is not None and isinstance(a1, str):
                    a1 = resolve(a1)
                if a2 is not None and isinstance(a2, str):
                    a2 = resolve(a2)
                optimized.append((op, a1, a2, res))
                continue

            if op == "MOV":
                src = resolve(a1) if isinstance(a1, str) else a1
                if res and res.startswith("t"):
                    # map temp to src (keep structured)
                    temp_map[res] = src
                else:
                    optimized.append(("MOV", src, None, res))
                continue

            if op in ("PLUS", "MINUS", "MUL", "DIV", "EQ", "NE", "GT", "LT", "GE", "LE"):
                left = resolve(a1) if isinstance(a1, str) else a1
                right = resolve(a2) if isinstance(a2, str) else a2
                # constant folding
                if isinstance(left, str) and left.isdigit() and isinstance(right, str) and right.isdigit():
                    # safely compute numeric result
                    sym = self.symbol(op)
                    folded = str(eval(f"{left}{sym}{right}"))
                    if res and res.startswith("t"):
                        temp_map[res] = folded
                    else:
                        optimized.append(("MOV", folded, None, res))
                else:
                    optimized.append((op, left, right, res))
                continue

            if op == "RET":
                v = resolve(a1) if isinstance(a1, str) else a1
                optimized.append(("RET", v, None, None))
                continue

            if op == "PRINT":
                v = resolve(a1) if isinstance(a1, str) else a1
                optimized.append(("PRINT", v, None, None))
                continue

            # fallback
            optimized.append((op, a1, a2, res))

        # Second pass: replace MOV temp->var where temp mapped to expression
        final = []
        for op, a1, a2, res in optimized:
            if op == "MOV" and isinstance(a1, str) and a1 in temp_map:
                final.append(("MOV", temp_map[a1], None, res))
            else:
                final.append((op, a1, a2, res))
        return final

    def symbol(self, op):
        return {
            "PLUS": "+", "MINUS": "-", "MUL": "*", "DIV": "/",
            "EQ": "==", "NE": "!=", "GT": ">", "LT": "<", "GE": ">=", "LE": "<="
        }[op]



