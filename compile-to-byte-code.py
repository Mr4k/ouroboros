import ast, dis, astpretty

with open('tail.py') as f: module_text = f.read()
module_ast = ast.parse(module_text)

astpretty.pprint(module_ast)

# for now use a simple defintion of tail recursive
# this definition is sound but not complete
# this definiton will be expanded later 
# TODO read about how Java / other pls do tail recursion
# For now the definition is:
# A function can be tail call optimized if
# all of the function calls it makes are
# 1) are the sole children of the return statements
# 2) are all calls to the parent function
def is_tail_recursive(node):
    assert isinstance(node, ast.FunctionDef)
    fname = node.name
    calls = {}
    for child in ast.walk(node):
        if isinstance(child, ast.Return):
            if isinstance(child.value, ast.Call):
                if child.value.func.id == fname:
                    calls[child.value] = 1
                else:
                    calls[child.value] = 0
        elif isinstance(child, ast.Call):
            if not child in calls:
                calls[child] = 0
    
    for call in calls.values():
        if call == 0:
            return False

    return True

for node in ast.walk(module_ast):
    if isinstance(node, ast.FunctionDef):
        print(node.name, is_tail_recursive(node))
            

module_code = compile(module_ast, 'tail.py', 'exec')
dis.show_code(module_code)

dis.dis(module_code)
