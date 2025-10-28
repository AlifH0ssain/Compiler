# codegen.py
# Intermediate Code Generator (TAC) for Mini C Compiler

from parser import (
    Program, Function, Declaration, Assignment, Return,
    Print, If, While, FuncCall, Var, Number, BinOp, String
)


class CodeGenerator:
    def __init__(self, ast):
        self.ast = ast
        self.code = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self, base="L"):
        self.label_count += 1
        return f"{base}{self.label_count}"

    def emit(self, op, a1=None, a2=None, res=None):
        self.code.append((op, a1, a2, res))

    def generate(self):
        for func in self.ast.functions:
            self.emit("FUNC", func.name, None, None)
            # Declare parameters
            for p in func.params:
                self.emit("PARAM_DECL", p, None, None)
            for stmt in func.body:
                self.generate_statement(stmt)
            self.emit("END_FUNC", func.name, None, None)
        return self.code

    def generate_statement(self, stmt):
        if isinstance(stmt, Declaration):
            if stmt.value:
                val = self.generate_expression(stmt.value)
                self.emit("MOV", val, None, stmt.var_name)

        elif isinstance(stmt, Assignment):
            val = self.generate_expression(stmt.value)
            self.emit("MOV", val, None, stmt.var_name)

        elif isinstance(stmt, Return):
            val = self.generate_expression(stmt.value)
            self.emit("RET", val, None, None)

        elif isinstance(stmt, Print):
            val = self.generate_expression(stmt.value)
            self.emit("PRINT", val, None, None)

        elif isinstance(stmt, If):
            cond = self.generate_expression(stmt.condition)
            else_label = self.new_label("ELSE")
            end_label = self.new_label("ENDIF")
            self.emit("IFZ_GOTO", cond, None, else_label)
            for s in stmt.then_body:
                self.generate_statement(s)
            self.emit("GOTO", end_label, None, None)
            self.emit("LABEL", else_label, None, None)
            if stmt.else_body:
                for s in stmt.else_body:
                    self.generate_statement(s)
            self.emit("LABEL", end_label, None, None)

        elif isinstance(stmt, While):
            start_label = self.new_label("WHILE_START")
            end_label = self.new_label("WHILE_END")
            self.emit("LABEL", start_label, None, None)
            cond = self.generate_expression(stmt.condition)
            self.emit("IFZ_GOTO", cond, None, end_label)
            for s in stmt.body:
                self.generate_statement(s)
            self.emit("GOTO", start_label, None, None)
            self.emit("LABEL", end_label, None, None)

        elif isinstance(stmt, FuncCall):
            self.generate_expression(stmt)  # for standalone calls

        else:
            raise Exception(f"Unknown statement type: {type(stmt).__name__}")

    def generate_expression(self, expr):
        if isinstance(expr, Number):
            t = self.new_temp()
            self.emit("MOV", expr.value, None, t)
            return t

        elif isinstance(expr, String):  
            t = self.new_temp()
            self.emit("MOV", f'"{expr.value}"', None, t)
            return t

        elif isinstance(expr, Var):
            return expr.name

        elif isinstance(expr, BinOp):
            left = self.generate_expression(expr.left)
            right = self.generate_expression(expr.right)
            t = self.new_temp()
            self.emit(expr.op, left, right, t)
            return t

        elif isinstance(expr, FuncCall):
            # evaluate arguments in order
            for arg in expr.args:
                arg_val = self.generate_expression(arg)
                self.emit("PARAM", arg_val, None, None)
            self.emit("CALL", expr.name, len(expr.args), None)
            t = self.new_temp()
            self.emit("POP", None, None, t)
            return t

        else:
            raise Exception(f"Unknown expression type: {type(expr).__name__}")
