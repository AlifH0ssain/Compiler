# semantic.py
# Semantic Analyzer for Mini C Compiler


from parser import (
    Program, Function, Declaration, Assignment, Return,
    Print, If, While, FuncCall, Var, Number, BinOp, String   
)
from lexical import tokenize
from parser import Parser


class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.functions = {}   # name → Function node
        self.symbol_table = {}  # for current function

    def analyze(self):
        """Entry point for semantic analysis."""
        # Collect all function definitions
        for func in self.ast.functions:
            if func.name in self.functions:
                self.error(f"Duplicate function '{func.name}'")
            self.functions[func.name] = func

        # Analyze each function individually
        for func in self.ast.functions:
            self.visit_function(func)

    # Function-level analysis
    def visit_function(self, func):
        print(f"\nAnalyzing function: {func.name}")
        self.symbol_table = {}
        # Parameters are implicitly declared
        for p in func.params:
            if p in self.symbol_table:
                self.error(f"Duplicate parameter '{p}' in function '{func.name}'")
            self.symbol_table[p] = "int"
            print(f"Declared parameter: {p}")

        for stmt in func.body:
            self.visit_statement(stmt)

    # Statement visitors
    def visit_statement(self, stmt):
        if isinstance(stmt, Declaration):
            self.visit_declaration(stmt)
        elif isinstance(stmt, Assignment):
            self.visit_assignment(stmt)
        elif isinstance(stmt, Return):
            self.visit_return(stmt)
        elif isinstance(stmt, Print):
            self.visit_print(stmt)
        elif isinstance(stmt, If):
            self.visit_if(stmt)
        elif isinstance(stmt, While):
            self.visit_while(stmt)
        elif isinstance(stmt, FuncCall):
            self.visit_funccall(stmt)
        else:
            self.error(f"Unknown statement type: {type(stmt).__name__}")

    def visit_declaration(self, decl):
        name = decl.var_name
        if name in self.symbol_table:
            self.error(f"Variable '{name}' redeclared")
        self.symbol_table[name] = "int"
        print(f"Declared variable: {name}")
        if decl.value:
            self.visit_expression(decl.value)

    def visit_assignment(self, assign):
        name = assign.var_name
        if name not in self.symbol_table:
            self.error(f"Variable '{name}' used before declaration")
        self.visit_expression(assign.value)

    def visit_return(self, ret):
        self.visit_expression(ret.value)

    def visit_print(self, p):
        val_type = self.visit_expression(p.value)
        if val_type not in ("int", "string"):
            self.error(f"Cannot print type '{val_type}'")

    def visit_if(self, node):
        self.visit_expression(node.condition)
        saved_scope = dict(self.symbol_table)
        for stmt in node.then_body:
            self.visit_statement(stmt)
        self.symbol_table = dict(saved_scope)
        if node.else_body:
            for stmt in node.else_body:
                self.visit_statement(stmt)
            self.symbol_table = dict(saved_scope)

    def visit_while(self, node):
        self.visit_expression(node.condition)
        saved_scope = dict(self.symbol_table)
        for stmt in node.body:
            self.visit_statement(stmt)
        self.symbol_table = dict(saved_scope)

    def visit_funccall(self, call):
        if call.name not in self.functions:
            self.error(f"Call to undeclared function '{call.name}'")
        func = self.functions[call.name]
        if len(call.args) != len(func.params):
            self.error(f"Function '{call.name}' expects {len(func.params)} args, got {len(call.args)}")
        for arg in call.args:
            self.visit_expression(arg)

    # Expression visitors
    def visit_expression(self, expr):
        if isinstance(expr, Number):
            return "int"

        elif isinstance(expr, String):  
            return "string"

        elif isinstance(expr, Var):
            if expr.name not in self.symbol_table:
                self.error(f"Use of undeclared variable '{expr.name}'")
            return "int"

        elif isinstance(expr, BinOp):
            left_type = self.visit_expression(expr.left)
            right_type = self.visit_expression(expr.right)
            if left_type != "int" or right_type != "int":
                self.error(f"Incompatible types in operation '{expr.op}'")
            return "int"

        elif isinstance(expr, FuncCall):
            self.visit_funccall(expr)
            return "int"

        else:
            self.error(f"Unknown expression: {expr}")

    def error(self, message):
        raise Exception(f"Semantic Error: {message}")

