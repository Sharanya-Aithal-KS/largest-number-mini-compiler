# -------------------------------
# 1. SAMPLE INPUT PROGRAM
# -------------------------------
source_code = """
int main()
begin
int n1, n2, n3;
if (n1 > n2)
begin
    if (n1 > n3)
    begin
        printf(n1);
    end
end
if (n2 > n1)
begin
    if (n2 > n3)
    begin
        printf(n2);
    end
end
if (n3 > n1)
begin
    if (n3 > n2)
    begin
        printf(n3);
    end
end
end
"""

# -------------------------------
# 2. LEXICAL ANALYZER
# -------------------------------
import re
from graphviz import Digraph

KEYWORDS = {"int", "main", "begin", "end", "if", "printf"}

token_specification = [
    ('NUMBER',   r'\d+'),
    ('ID',       r'[A-Za-z_]\w*'),
    ('OP',       r'==|>|<'),
    ('SYMBOL',   r'[(),;]'),
    ('SKIP',     r'[ \t\n]+'),
    ('MISMATCH', r'.'),
]

def tokenize(code):
    tokens = []
    regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)

    for match in re.finditer(regex, code):
        kind = match.lastgroup
        value = match.group()

        if kind == 'ID' and value in KEYWORDS:
            tokens.append(("KEYWORD", value))
        elif kind == 'ID':
            tokens.append(("IDENTIFIER", value))
        elif kind == 'NUMBER':
            tokens.append(("NUMBER", value))
        elif kind == 'OP':
            tokens.append(("OPERATOR", value))
        elif kind == 'SYMBOL':
            tokens.append(("SYMBOL", value))
        elif kind == 'SKIP':
            continue
        else:
            raise RuntimeError(f"Unexpected token: {value}")

    return tokens


# -------------------------------
# 3. AST NODE
# -------------------------------
class ASTNode:
    def __init__(self, type, value=None, children=None):
        self.type = type
        self.value = value
        self.children = children if children else []


# -------------------------------
# 4. PARSER WITH AST
# -------------------------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "")

    def match(self, expected_type, expected_value=None):
        tok_type, tok_val = self.current()

        if tok_type == expected_type and (expected_value is None or tok_val == expected_value):
            self.pos += 1
            return tok_val
        else:
            raise SyntaxError(f"Unexpected token: {tok_type}, {tok_val}")

    def program(self):
        self.match("KEYWORD", "int")
        self.match("KEYWORD", "main")
        self.match("SYMBOL", "(")
        self.match("SYMBOL", ")")
        self.match("KEYWORD", "begin")

        decl_node = self.decl()
        stmt_node = self.stmt_list()

        self.match("KEYWORD", "end")

        return ASTNode("PROGRAM", children=[decl_node, stmt_node])

    def decl(self):
        self.match("KEYWORD", "int")
        ids = self.id_list()
        self.match("SYMBOL", ";")
        return ASTNode("DECL", children=ids)

    def id_list(self):
        ids = []
        ids.append(ASTNode("ID", self.match("IDENTIFIER")))
        while self.current()[1] == ",":
            self.match("SYMBOL", ",")
            ids.append(ASTNode("ID", self.match("IDENTIFIER")))
        return ids

    def stmt_list(self):
        stmts = []
        while self.current()[1] in ("if", "printf"):
            if self.current()[1] == "if":
                stmts.append(self.if_stmt())
            elif self.current()[1] == "printf":
                stmts.append(self.print_stmt())
        return ASTNode("STMT_LIST", children=stmts)

    def if_stmt(self):
        self.match("KEYWORD", "if")
        self.match("SYMBOL", "(")

        left = self.expr()
        op = self.match("OPERATOR")
        right = self.expr()

        self.match("SYMBOL", ")")
        self.match("KEYWORD", "begin")

        body = self.stmt_list()

        self.match("KEYWORD", "end")

        return ASTNode("IF", value=op, children=[left, right, body])

    def print_stmt(self):
        self.match("KEYWORD", "printf")
        self.match("SYMBOL", "(")

        expr_node = self.expr()

        self.match("SYMBOL", ")")
        self.match("SYMBOL", ";")

        return ASTNode("PRINT", children=[expr_node])

    def expr(self):
        tok_type, tok_val = self.current()

        if tok_type == "IDENTIFIER":
            return ASTNode("ID", self.match("IDENTIFIER"))
        elif tok_type == "NUMBER":
            return ASTNode("NUM", self.match("NUMBER"))
        else:
            raise SyntaxError("Invalid expression")


# -------------------------------
# 5. TREE PRINT (TEXT)
# -------------------------------
def print_tree(node, indent="", last=True):
    print(indent, end="")
    if last:
        print("└── ", end="")
        indent += "    "
    else:
        print("├── ", end="")
        indent += "│   "

    print(f"{node.type}: {node.value if node.value else ''}")

    for i, child in enumerate(node.children):
        is_last = i == len(node.children) - 1
        if isinstance(child, list):
            for j, c in enumerate(child):
                print_tree(c, indent, j == len(child) - 1)
        else:
            print_tree(child, indent, is_last)


# -------------------------------
# 6. GRAPHVIZ AST VISUALIZATION
# -------------------------------
def visualize_ast(node):
    dot = Digraph(comment="AST")

    def add_nodes(n, parent=None):
        node_id = str(id(n))
        label = f"{n.type}\n{n.value if n.value else ''}"

        dot.node(node_id, label)

        if parent:
            dot.edge(parent, node_id)

        for child in n.children:
            if isinstance(child, list):
                for c in child:
                    add_nodes(c, node_id)
            else:
                add_nodes(child, node_id)

    add_nodes(node)
    dot.render("AST_Output", format="png", view=True)


# -------------------------------
# 7. SEMANTIC ANALYZER
# -------------------------------
class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}

    def analyze(self, node):
        if node.type == "PROGRAM":
            for child in node.children:
                self.analyze(child)

        elif node.type == "DECL":
            for var in node.children:
                self.symbol_table[var.value] = "int"

        elif node.type == "IF":
            left, right, body = node.children

            if self.get_type(left) != self.get_type(right):
                raise TypeError("Type mismatch")

            self.analyze(body)

        elif node.type == "STMT_LIST":
            for stmt in node.children:
                self.analyze(stmt)

        elif node.type == "PRINT":
            self.get_type(node.children[0])

    def get_type(self, node):
        if node.type == "NUM":
            return "int"
        elif node.type == "ID":
            if node.value not in self.symbol_table:
                raise NameError(f"Undeclared variable: {node.value}")
            return self.symbol_table[node.value]


# -------------------------------
# 8. INTERPRETER
# -------------------------------
class Interpreter:
    def __init__(self, symbol_table):
        self.env = {var: 0 for var in symbol_table}

    def set_values(self, values):
        self.env.update(values)

    def eval_expr(self, node):
        if node.type == "NUM":
            return int(node.value)
        elif node.type == "ID":
            return self.env[node.value]

    def exec(self, node):
        if node.type == "PROGRAM":
            for child in node.children:
                self.exec(child)

        elif node.type == "STMT_LIST":
            for stmt in node.children:
                self.exec(stmt)

        elif node.type == "IF":
            left, right, body = node.children
            op = node.value

            lval = self.eval_expr(left)
            rval = self.eval_expr(right)

            condition = False
            if op == ">":
                condition = lval > rval
            elif op == "<":
                condition = lval < rval
            elif op == "==":
                condition = lval == rval

            if condition:
                self.exec(body)

        elif node.type == "PRINT":
            value = self.eval_expr(node.children[0])
            print("LARGEST VALUE IS :", value)


# -------------------------------
# 9. RUN EVERYTHING
# -------------------------------
tokens = tokenize(source_code)

parser = Parser(tokens)
ast = parser.program()

print("\nPARSE TREE:")
print_tree(ast)

#  GRAPHICAL AST
visualize_ast(ast)

semantic = SemanticAnalyzer()
semantic.analyze(ast)

print("\nSYMBOL TABLE:")
print(semantic.symbol_table)

interpreter = Interpreter(semantic.symbol_table)

values = {}

for var in semantic.symbol_table:
    val = int(input(f"Enter value for {var}: "))
    values[var] = val

interpreter.set_values(values)

print("\nEXECUTION:")
interpreter.exec(ast)