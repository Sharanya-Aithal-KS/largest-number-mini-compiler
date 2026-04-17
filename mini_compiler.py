import re
from collections import defaultdict
from graphviz import Digraph
# NODE FOR PARSE TREE
class Node:
    def __init__(self, value):
        self.value = value
        self.children = []
# BOX TABLE
def print_box(headers, rows, title):
    print(f"\n{title}:\n")
    def format_cell(text):
        return str(text)
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i in range(len(row)):
            lines = format_cell(row[i]).split("\n")
            for line in lines:
                col_widths[i] = max(col_widths[i], len(line))
    def line():
        print("+" + "+".join("-"*(w+2) for w in col_widths) + "+")
    def row_print(row):
        cell_lines = [format_cell(cell).split("\n") for cell in row]
        max_lines = max(len(c) for c in cell_lines)
        for i in range(max_lines):
            row_out = []
            for j, cell in enumerate(cell_lines):
                if i < len(cell):
                    row_out.append(cell[i].ljust(col_widths[j]))
                else:
                    row_out.append("".ljust(col_widths[j]))
            print("| " + " | ".join(row_out) + " |")
    line()
    row_print(headers)
    line()
    for r in rows:
        row_print(r)
    line()
# LEXER
def lexer(code):
    token_spec = [
        ('KEYWORD', r'\b(int|if|begin|end|printf|main)\b'),
        ('RELOP', r'>|<|>=|<=|==|!='),
        ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('SYMBOL', r'[(),;]'),
        ('SKIP', r'[ \n\t]+')
    ]
    tok_regex = '|'.join(f'(?P<{n}>{p})' for n,p in token_spec)
    tokens=[]
    for m in re.finditer(tok_regex, code):
        if m.lastgroup!='SKIP':
            tokens.append((m.group(),m.lastgroup))
    return tokens
def print_parsing_table(steps):
    print("\nPARSING STEPS:\n")
    stack_w = 40
    input_w = 50
    action_w = 20
    def split_text(text, width):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= width:
                current += (" " + word) if current else word
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
    # header
    print("+" + "-"*(stack_w+2) + "+" + "-"*(input_w+2) + "+" + "-"*(action_w+2) + "+")
    print(f"| {'Stack'.ljust(stack_w)} | {'Input'.ljust(input_w)} | {'Action'.ljust(action_w)} |")
    print("+" + "-"*(stack_w+2) + "+" + "-"*(input_w+2) + "+" + "-"*(action_w+2) + "+")
    # rows
    for stack, inp, action in steps:
        stack_lines = split_text(stack, stack_w)
        input_lines = split_text(inp, input_w)
        max_lines = max(len(stack_lines), len(input_lines))
        for i in range(max_lines):
            s = stack_lines[i] if i < len(stack_lines) else ""
            inp_line = input_lines[i] if i < len(input_lines) else ""
            if i == 0:
                print(f"| {s.ljust(stack_w)} | {inp_line.ljust(input_w)} | {action.ljust(action_w)} |")
            else:
                print(f"| {s.ljust(stack_w)} | {inp_line.ljust(input_w)} | {' '.ljust(action_w)} |")
        print("+" + "-"*(stack_w+2) + "+" + "-"*(input_w+2) + "+" + "-"*(action_w+2) + "+")
# GRAMMAR
grammar = {
    "S'":[["Program"]],
    "Program":[["int","main","(",")","begin","Decl","Stmt","Stmt","Stmt","end"]],
    "Decl":[["int","id",",","id",",","id",";"]],
    "Stmt":[["if","(","Expr","relop","Expr",")","begin","Print","end"]],
    "Print":[["printf","(","id",")",";"]],
    "Expr":[["id"]],
    "relop":[[">"]]
}
FIRST = {
    "Program":"{ int }",
    "Decl":"{ int }",
    "Stmt":"{ if }",
    "Print":"{ printf }",
    "Expr":"{ id }",
    "relop":"{ > }"
}
FOLLOW = {
    "Program":"{ $ }",
    "Decl":"{ if }",
    "Stmt":"{ if, end }",
    "Print":"{ end }",
    "Expr":"{ relop, ) }",
    "relop":"{ id }"
}
# LR(0) DFA
def closure(items):
    closure_set=set(items)
    while True:
        new=set()
        for lhs,rhs,dot in closure_set:
            if dot<len(rhs):
                sym=rhs[dot]
                if sym in grammar:
                    for p in grammar[sym]:
                        item=(sym,tuple(p),0)
                        if item not in closure_set:
                            new.add(item)
        if not new: break
        closure_set|=new
    return closure_set
def goto(items,sym):
    moved=set()
    for lhs,rhs,dot in items:
        if dot<len(rhs) and rhs[dot]==sym:
            moved.add((lhs,rhs,dot+1))
    return closure(moved)
def build_dfa():
    start=closure({("S'",tuple(grammar["S'"][0]),0)})
    states=[start]
    trans={}
    symbols=set()
    for v in grammar.values():
        for p in v: symbols.update(p)
    while True:
        added=False
        for i,s in enumerate(states):
            for sym in symbols:
                g=goto(s,sym)
                if g:
                    if g not in states:
                        states.append(g)
                        added=True
                    trans[(i,sym)]=states.index(g)
        if not added: break
    return states,trans
states,trans=build_dfa()
# LR(0) TABLE
lr_rows=[]
for i,s in enumerate(states):
    items=[]
    for lhs,rhs,dot in s:
        rhs=list(rhs)
        rhs.insert(dot,"•")
        items.append(f"{lhs}→{' '.join(rhs)}")
    lr_rows.append([f"I{i}","\n".join(items)])
dfa_rows=[[f"I{s}",sym,f"I{d}"] for (s,sym),d in trans.items()]
# SLR TABLE
ACTION={}
GOTO={}
for (s,sym),d in trans.items():
    if sym not in grammar:
        ACTION[(s,sym)]=f"S{d}"
    else:
        GOTO[(s,sym)]=d
for i,s in enumerate(states):
    for lhs,rhs,dot in s:
        if dot==len(rhs):
            if lhs=="S'":
                ACTION[(i,"$")]="ACC"
            else:
                follow = {
                    "Program":["$"],
                    "Decl":["if"],
                    "Stmt":["if","end"],
                    "Print":["end"],
                    "Expr":[">",")"],
                    "relop":["id"]
                }
                for t in follow.get(lhs,[]):
                    ACTION[(i,t)]=f"R({lhs})"
terms=["id","int","if","printf","end","$"]
nonterms=list(grammar.keys())
headers=["State"]+terms+nonterms
rows=[]
for i in range(len(states)):
    row=[f"I{i}"]
    for t in terms:
        row.append(ACTION.get((i,t),""))
    for nt in nonterms:
        row.append(GOTO.get((i,nt),""))
    rows.append(row)
# PARSER + TREE
def parse(tokens):
    stack=["0"]
    tokens.append("$")
    i=0
    steps=[]
    node_stack=[]
    accepted = False  
    while True:
        state=int(stack[-1])
        symbol=tokens[i]
        action=ACTION.get((state,symbol),"")
        stack_str=" ".join(stack)
        input_str=" ".join(tokens[i:])
        if action.startswith("S"):
            steps.append([stack_str,input_str,f"Shift {symbol}"])
            stack.append(symbol)
            stack.append(action[1:])
            node_stack.append(Node(symbol))
            i+=1
        elif action.startswith("R"):
            lhs=action.split("(")[1].split(")")[0]
            steps.append([stack_str,input_str,f"Reduce {lhs}"])
            rhs=grammar.get(lhs,[[]])[0]
            children=[]
            for _ in range(len(rhs)):
                if node_stack:
                    children.insert(0,node_stack.pop())
            new_node=Node(lhs)
            new_node.children=children
            node_stack.append(new_node)
            for _ in range(len(rhs)*2):
                if stack:
                    stack.pop()
            state=int(stack[-1])
            stack.append(lhs)
            goto_state=GOTO.get((state,lhs))
            if goto_state is not None:
                stack.append(str(goto_state))
            else:
                steps.append([stack_str,input_str,"REJECT"])
                break
        elif action=="ACC":
            steps.append([stack_str,input_str,"ACCEPT"])
            accepted = True  
            break
        else:
            steps.append([stack_str,input_str,"REJECT"])
            break
    print_parsing_table(steps)
    if accepted:
        return node_stack[0] if node_stack else None
    else:
        return None
def draw_parse_tree(root):
    dot=Digraph(format='png')
    dot.attr(rankdir='TB')
    def add(node):
        dot.node(str(id(node)),node.value)
        for child in node.children:
            dot.edge(str(id(node)),str(id(child)))
            add(child)
    add(root)
    dot.render("parse_tree",view=True)
# MAIN
code="""
int main()
begin
int n1, n2, n3;
if( expr relop expr )
begin
printf( n1);
end
if ( expr relop expr )
begin
printf( n2);
end
if( expr relop expr )
begin
printf( n3);
end
end
"""
tokens=lexer(code)
print_box(["Lexeme","Token"],tokens,"TOKEN TABLE")
print_box(["Non-Terminal","Productions"],
          [[k," | ".join(" ".join(p) for p in v)] for k,v in grammar.items()],
          "GRAMMAR")
print_box(["NON-TERMINAL","FIRST","FOLLOW"],
          [[k,FIRST.get(k,""),FOLLOW.get(k,"")] for k in grammar],
          "FIRST FOLLOW")
print_box(["State","Items"],lr_rows,"LR(0) STATES")
print_box(["From","Symbol","To"],dfa_rows,"PARSE TREE")
print_box(headers,rows,"SLR TABLE")
input_tokens=[
    "int","main","(",")",
    "int","id",",","id",",","id",";",
    "if","(","id",">","id",")","begin","printf","(","id",")",";","end",
    "if","(","id",">","id",")","begin","printf","(","id",")",";","end",
    "if","(","id",">","id",")","begin","printf","(","id",")",";","end",
    "end"   
]
root = parse(input_tokens)
if root:print("\nInput Accepted → Parse tree constructed.\n");draw_parse_tree(root)
else:print("\nInput Rejected → Parse tree not constructed.\n")