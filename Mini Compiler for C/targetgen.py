# targetgen.py
# ------------------------------------------------------------
# Target Code Generator for our Mini C Compiler (Python Version)
# ------------------------------------------------------------
# Converts optimized TAC into simple, assembly-like target code.
# This version improves the handling of "arithmetic -> MOV temp->var"
# patterns to:
#  - emit in-place arithmetic when safe (e.g., ADD i, 1)
#  - emit in-place arithmetic + MOV var, left when needed
#  - avoid emitting redundant MOV x, x
# ------------------------------------------------------------

from typing import List, Tuple, Optional

TACInstr = Tuple[str, Optional[str], Optional[str], Optional[str]]

class TargetCodeGenerator:
    def __init__(self, optimized_tac: List[TACInstr]):
        self.optimized_tac = optimized_tac
        self.target_code: List[str] = []

    def opmap(self, op: str) -> str:
        return {
            "PLUS": "ADD", "MINUS": "SUB", "MUL": "MUL", "DIV": "DIV",
            "EQ": "EQ", "NE": "NE", "GT": "GT", "LT": "LT", "GE": "GE", "LE": "LE"
        }.get(op, op)

    def generate(self) -> List[str]:
        # Build quick index map of definitions (not strictly required but kept for clarity)
        i = 0
        n = len(self.optimized_tac)
        while i < n:
            op, a1, a2, res = self.optimized_tac[i]

            # Function label
            if op == "FUNC":
                # print function name as label
                if a1:
                    self.target_code.append(f"{a1}:")
                else:
                    self.target_code.append("FUNC:")
                i += 1
                continue

            if op == "END_FUNC":
                # no-op for end func — keep for readability
                i += 1
                continue

            # Arithmetic producing a temp followed by MOV temp -> var
            if op in ("PLUS", "MINUS", "MUL", "DIV", "EQ", "NE", "GT", "LT", "GE", "LE") and res and res.startswith("t"):
                # Look ahead for MOV res -> var
                if i + 1 < n:
                    nop, na1, na2, nres = self.optimized_tac[i+1]
                    if nop == "MOV" and na1 == res and nres:
                        asm = self.opmap(op)
                        left = a1
                        right = a2
                        dest = nres

                        # If left operand equals the final destination, do in-place and skip MOV
                        if left == dest:
                            # emit in-place arithmetic, result lives in 'left' already
                            self.target_code.append(f"{asm} {left}, {right}")
                            # skip the following MOV entirely
                            i += 2
                            continue
                        else:
                            # Common pattern: do op in-place on left operand, then move left -> dest
                            # Emit in-place operation on left operand, then MOV dest, left
                            self.target_code.append(f"{asm} {left}, {right}")
                            # Avoid redundant MOV (dest, left) when dest == left (covered above)
                            if dest != left:
                                self.target_code.append(f"MOV {dest}, {left}")
                            i += 2
                            continue

                # No matching MOV next -> fallback: emit op to temp
                asm = self.opmap(op)
                self.target_code.append(f"{asm} {res}, {a1}, {a2}")
                i += 1
                continue

            # IFZ_GOTO -> CMP/JE sequence
            if op == "IFZ_GOTO":
                # IFZ_GOTO cond, None, label  -> CMP cond, 0 ; JE label
                self.target_code.append(f"CMP {a1}, 0")
                if res:
                    self.target_code.append(f"JE {res}")
                else:
                    self.target_code.append(f"JE __UNKNOWN_LABEL__")
                i += 1
                continue

            # GOTO -> JMP label
            if op == "GOTO":
                if a1:
                    self.target_code.append(f"JMP {a1}")
                i += 1
                continue

            # LABEL -> label:
            if op == "LABEL":
                if a1:
                    self.target_code.append(f"{a1}:")
                i += 1
                continue

            # MOV -> MOV dest, src
            if op == "MOV":
                # MOV src -> res (we store as MOV res, src)
                # Avoid redundant MOV x, x
                src = a1
                dest = res
                if src is None or dest is None:
                    i += 1
                    continue
                if src == dest:
                    # skip redundant
                    i += 1
                    continue
                self.target_code.append(f"MOV {dest}, {src}")
                i += 1
                continue

            # PRINT
            if op == "PRINT":
                self.target_code.append(f"PRINT {a1}")
                i += 1
                continue

            # RET
            if op == "RET":
                self.target_code.append(f"RET {a1}")
                i += 1
                continue

            # PARAM (push)
            if op == "PARAM":
                self.target_code.append(f"PUSH {a1}")
                i += 1
                continue

            # CALL
            if op == "CALL":
                # CALL <name>, <nargs>
                if a1:
                    self.target_code.append(f"CALL {a1}, {a2 if a2 is not None else 0}")
                else:
                    self.target_code.append("CALL __UNKNOWN__, 0")
                i += 1
                continue

            # POP
            if op == "POP":
                # POP dest
                if res:
                    self.target_code.append(f"POP {res}")
                else:
                    self.target_code.append("POP _")
                i += 1
                continue

            # PARAM_DECL (no code)
            if op == "PARAM_DECL":
                i += 1
                continue

            # Fallback unknown ops
            self.target_code.append(f"# Unsupported op: {op} {a1} {a2} {res}")
            i += 1

        return self.target_code

    def display(self):
        print("\n[TARGET CODE]")
        for line in self.target_code:
            print("  ", line)
