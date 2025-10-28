# Recursive Descent Parser for Mini C Compiler

from lexical import Token, tokenize

# AST Node Definitions
class ASTNode: pass

class Program(ASTNode):
    def __init__(self, functions): self.functions = functions

class Function(ASTNode):
    def __init__(self, name, params, body):
        self.name, self.params, self.body = name, params, body

class Declaration(ASTNode):
    def __init__(self, var_name, value): self.var_name, self.value = var_name, value

class Assignment(ASTNode):
    def __init__(self, var_name, value): self.var_name, self.value = var_name, value

class Return(ASTNode):
    def __init__(self, value): self.value = value

class BinOp(ASTNode):
    def __init__(self, left, op, right): self.left, self.op, self.right = left, op, right

class Number(ASTNode):
    def __init__(self, value): self.value = int(value)

class String(ASTNode):                
    def __init__(self, value):
        self.value = value.strip('"')

class Var(ASTNode):
    def __init__(self, name): self.name = name

class Print(ASTNode):
    def __init__(self, value): self.value = value

class If(ASTNode):
    def __init__(self, condition, then_body, else_body=None):
        self.condition, self.then_body, self.else_body = condition, then_body, else_body

class While(ASTNode):
    def __init__(self, condition, body): self.condition, self.body = condition, body

class FuncCall(ASTNode):
    def __init__(self, name, args): self.name, self.args = name, args


# Parser
class Parser:
    def __init__(self, tokens):
        self.tokens, self.pos = tokens, 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token("EOF", "", 0, 0)

    def peek(self, offset=1):
        i = self.pos + offset
        return self.tokens[i] if i < len(self.tokens) else Token("EOF", "", 0, 0)

    def eat(self, token_type=None):
        tok = self.current_token()
        if token_type and tok.type != token_type:
            self.error(f"Expected {token_type}, found {tok.type}")
        self.pos += 1
        return tok

    def error(self, msg):
        tok = self.current_token()
        raise SyntaxError(f"[Line {tok.line}, Col {tok.col}] {msg}")

    def parse(self):
        functions = []
        while self.current_token().type != "EOF":
            functions.append(self.function())
        return Program(functions)

    def function(self):
        self.eat("INT")
        name = self.eat("ID").value
        self.eat("LPAREN")
        params = []
        if self.current_token().type != "RPAREN":
            while True:
                if self.current_token().type == "INT": self.eat("INT")
                params.append(self.eat("ID").value)
                if self.current_token().type == "COMMA":
                    self.eat("COMMA"); continue
                break
        self.eat("RPAREN")
        self.eat("LBRACE")
        body = []
        while self.current_token().type != "RBRACE":
            body.append(self.statement())
        self.eat("RBRACE")
        return Function(name, params, body)

    def statement(self):
        t = self.current_token().type
        if t == "INT": return self.declaration()
        elif t == "ID" and self.peek().type == "LPAREN":
            node = self.func_call(); self.eat("SEMI"); return node
        elif t == "ID": return self.assignment()
        elif t == "RETURN": return self.return_stmt()
        elif t == "PRINT": return self.print_stmt()
        elif t == "IF": return self.if_stmt()
        elif t == "WHILE": return self.while_stmt()
        else: self.error(f"Unexpected token {t} in statement")

    def declaration(self):
        self.eat("INT"); name = self.eat("ID").value
        val = None
        if self.current_token().type == "ASSIGN":
            self.eat("ASSIGN"); val = self.expression()
        self.eat("SEMI"); return Declaration(name, val)

    def assignment(self):
        n = self.eat("ID").value; self.eat("ASSIGN")
        v = self.expression(); self.eat("SEMI")
        return Assignment(n, v)

    def return_stmt(self):
        self.eat("RETURN"); v = self.expression(); self.eat("SEMI"); return Return(v)

    def print_stmt(self):
        self.eat("PRINT"); self.eat("LPAREN"); expr = self.expression()
        self.eat("RPAREN"); self.eat("SEMI"); return Print(expr)

    def if_stmt(self):
        self.eat("IF"); self.eat("LPAREN")
        cond = self.expression(); self.eat("RPAREN")
        self.eat("LBRACE")
        then_b = []
        while self.current_token().type != "RBRACE":
            then_b.append(self.statement())
        self.eat("RBRACE")

        else_b = None
        if self.current_token().type == "ELSE":
            self.eat("ELSE")
            if self.current_token().type == "IF":
                else_b = [self.if_stmt()]
            else:
                self.eat("LBRACE"); else_b = []
                while self.current_token().type != "RBRACE":
                    else_b.append(self.statement())
                self.eat("RBRACE")
        return If(cond, then_b, else_b)

    def while_stmt(self):
        self.eat("WHILE"); self.eat("LPAREN")
        cond = self.expression(); self.eat("RPAREN")
        self.eat("LBRACE"); body = []
        while self.current_token().type != "RBRACE":
            body.append(self.statement())
        self.eat("RBRACE"); return While(cond, body)

    def func_call(self):
        name = self.eat("ID").value; self.eat("LPAREN")
        args = []
        if self.current_token().type != "RPAREN":
            while True:
                args.append(self.expression())
                if self.current_token().type == "COMMA":
                    self.eat("COMMA"); continue
                break
        self.eat("RPAREN"); return FuncCall(name, args)

    def expression(self): return self.relational()

    def relational(self):
        n = self.additive()
        while self.current_token().type in ("EQ","NE","GT","LT","GE","LE"):
            op = self.eat().type; r = self.additive(); n = BinOp(n, op, r)
        return n

    def additive(self):
        n = self.term()
        while self.current_token().type in ("PLUS","MINUS"):
            op = self.eat().type; r = self.term(); n = BinOp(n, op, r)
        return n

    def term(self):
        n = self.factor()
        while self.current_token().type in ("MUL","DIV"):
            op = self.eat().type; r = self.factor(); n = BinOp(n, op, r)
        return n

    def factor(self):
        tok = self.current_token()
        if tok.type == "NUMBER":
            self.eat("NUMBER"); return Number(tok.value)
        elif tok.type == "STRING":                    # <-- NEW
            self.eat("STRING"); return String(tok.value)
        elif tok.type == "ID":
            if self.peek().type == "LPAREN": return self.func_call()
            self.eat("ID"); return Var(tok.value)
        elif tok.type == "LPAREN":
            self.eat("LPAREN"); node = self.expression(); self.eat("RPAREN"); return node
        else:
            self.error(f"Unexpected token {tok.type} in expression")

# Printer for AST
def op_symbol(op):
    return {
        "PLUS": "+", "MINUS": "-", "MUL": "*", "DIV": "/",
        "EQ": "==", "NE": "!=", "GT": ">", "LT": "<", "GE": ">=", "LE": "<="
    }.get(op, op)


def pretty_print_ast(node, indent="", is_last=True):
    from parser import Program, Declaration, Assignment, Return, Print, If, While, BinOp, Var, Number, FuncCall
    out = ""

    if isinstance(node, Program):
        for i, func in enumerate(node.functions):
            out += f"Program({func.name})\n"
            for j, stmt in enumerate(func.body):
                last = (j == len(func.body) - 1)
                branch = "└── " if last else "├── "
                out += indent + branch + pretty_print_ast(stmt, indent + ("    " if last else "│   "), is_last=last)
        return out

    if isinstance(node, Declaration):
        val = pretty_print_ast(node.value, indent + "    ", True).strip() if node.value else "None"
        return f"VarDecl({node.var_name}, {val})\n"

    if isinstance(node, Assignment):
        val = pretty_print_ast(node.value, indent + "    ", True).strip()
        return f"Assign({node.var_name}, {val})\n"

    if isinstance(node, Return):
        val = pretty_print_ast(node.value, indent + "    ", True).strip()
        return f"Return({val})\n"

    if isinstance(node, Print):
        val = pretty_print_ast(node.value, indent + "    ", True).strip()
        return f"Print({val})\n"

    if isinstance(node, If):
        cond = pretty_print_ast(node.condition, indent + "    ", True).strip()
        s = f"If({cond})\n"
        for i, stmt in enumerate(node.then_body):
            last = (i == len(node.then_body) - 1 and not node.else_body)
            branch = "└── " if last else "├── "
            s += indent + branch + pretty_print_ast(stmt, indent + ("    " if last else "│   "), is_last=last)
        if node.else_body:
            s += indent + "├── Else\n"
            for i, stmt in enumerate(node.else_body):
                last = (i == len(node.else_body) - 1)
                branch = "└── " if last else "├── "
                s += indent + branch + pretty_print_ast(stmt, indent + ("    " if last else "│   "), is_last=last)
        return s

    if isinstance(node, While):
        cond = pretty_print_ast(node.condition, indent + "    ", True).strip()
        s = f"While({cond})\n"
        for i, stmt in enumerate(node.body):
            last = (i == len(node.body) - 1)
            branch = "└── " if last else "├── "
            s += indent + branch + pretty_print_ast(stmt, indent + ("    " if last else "│   "), is_last=last)
        return s

    if isinstance(node, BinOp):
        left = pretty_print_ast(node.left, indent + "    ", False).strip()
        right = pretty_print_ast(node.right, indent + "    ", True).strip()
        return f"({left} {op_symbol(node.op)} {right})"

    if isinstance(node, Var):
        return node.name

    if isinstance(node, Number):
        return str(node.value)

    if isinstance(node, FuncCall):
        args = ", ".join(pretty_print_ast(a, indent + "    ", True).strip() for a in node.args)
        return f"{node.name}({args})"

    return str(node)
