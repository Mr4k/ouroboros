import ast, dis, astpretty
import inspect
import struct
from types import CodeType

with open('no_tail.py') as f: module_text = f.read()
module_ast = ast.parse(module_text)

astpretty.pprint(module_ast)

# For now use a simple defintion of tail recursive.
# This definition is sound but not complete.
# There is a lot of room for improvement.
#
# TODO read more about how other PLs do tail recursion.
# See this explanation of tail recursion in js:
# https://2ality.com/2015/06/tail-call-optimization.html
#
# For now the definition is:
# A sub function call can be tail call optimized if
# 1) it is the sole child of a return statements
# 2) it calls to the parent function
# 3) the sub function call and return statment must both all be on the same line
# 4) the sub function call and return statements be the only things their line
#   - Note that rules 3/4 only exists for now because python does not provide 
#   - a simple way to precisely identify function calls from the bytecode
#   - It seems like it can only do line number which could be ambiguous
#   - for multiline statments or statements such as the following: 
#   -   def f(arg):
#   -       ... 
#   -       return f(a) if f(c) else f(b)
#   - In the above example f(a) and f(b) are tail recursive while f(c) is not.
#   - Unfortunately they are all on the same line
#   - If we had a way to do precise identification we could mark only f(a) and f(b)
#   - as tail recursive. TODO investigate possible ways of marking functions precisely.
#   - perhaps we could append unique indentifiers in the ast but I'm unclear on the impact
#   - That would have on the rest of the compilation process (especially regarding optimizations)

# Does not work with line splits!! (TODO improve this)
def _get_num_children_with_lines(node, lineno):
    num = 0
    for child in ast.walk(node):
        if hasattr(child, 'lineno') and child.lineno == lineno:
            num += 1
    return num

# Does not work with line splits!! (TODO improve this)
def get_tail_recursive_calls(node):
    assert isinstance(node, ast.FunctionDef)
    fname = node.name
    possible_calls_lines = []
    nodes_at_line = {}
    for child in ast.walk(node):
        if hasattr(child, 'lineno'):
            if child.lineno in nodes_at_line:
                nodes_at_line[child.lineno] += 1
            else:
                nodes_at_line[child.lineno] = 1

    for child in ast.walk(node):
        if isinstance(child, ast.Return):
            if isinstance(child.value, ast.Call):
                if child.value.func.id == fname:
                    possible_calls_lines.append(child.lineno)
                    expr_nodes_on_lines = _get_num_children_with_lines(child, child.lineno)
                    nodes_at_line[child.lineno] -= expr_nodes_on_lines

    return list(filter(lambda lineno: nodes_at_line[lineno] == 0, possible_calls_lines))

# We will use this list to find them in the bytecode later
# TODO namespaces/scopes need to be handled here
# This is pretty fragile right now
tail_recursive_function_calls = {}
for node in ast.walk(module_ast):
    if isinstance(node, ast.FunctionDef):
        print(node.name, get_tail_recursive_calls(node))
        tail_recursive_function_calls[node.name] = get_tail_recursive_calls(node)

module_code = compile(module_ast, 'tail.py', 'exec')

def edit_function_code(fn_code, payload, new_consts):
    return CodeType(fn_code.co_argcount,
            fn_code.co_kwonlyargcount,
            fn_code.co_nlocals,
            fn_code.co_stacksize,
            fn_code.co_flags,
            payload,
            new_consts,
            fn_code.co_names,
            fn_code.co_varnames,
            fn_code.co_filename,
            fn_code.co_name,
            fn_code.co_firstlineno,
            fn_code.co_lnotab,
            fn_code.co_freevars,
            fn_code.co_cellvars,
            )

def pack_op(opcode_str, arg):
    return struct.pack('BB', dis.opmap[opcode_str], arg)

def replace_tail_calls(function_code, tail_call_line_locations):
    payload = function_code.co_code
    current_line = None

    # this iterator will always lag one behind so we can peek ahead
    instr = None
    for future_instr in dis.get_instructions(function_code):
        if instr == None:
            instr = future_instr 
            continue

        if instr.starts_line:
            current_line = instr.starts_line

        if instr.opname == 'CALL_FUNCTION' and future_instr.opname == 'RETURN_VALUE' and current_line in tail_call_line_locations:
            pos = instr.offset
            nargs = instr.arg
            # in this case 0 jumps to the beginning of the function
            jump = pack_op('JUMP_ABSOLUTE', 0)

            store_args = []
            for arg_n in reversed(range(nargs)):
                store_args.append(pack_op('STORE_FAST', arg_n))

            # we pop the function handle off the top of the stack
            # TODO it's probably more efficient to remove the instruction
            # which loads in onto the stack in the first place
            pop_top = pack_op('POP_TOP', 0)

            # certainly not the most efficient method of byte str concat
            # but this is fine for now
            before = payload[:pos]
            for store in store_args:
                before += store
            before += pop_top
            before += jump
            after = payload[pos+2:]
            payload = before + after
        instr = future_instr  

    return payload

def optimize_tail_calls(code, tail_recursive_function_calls):
    new_consts = []
    for const in code.co_consts:
        if inspect.iscode(const):
            new_consts.append(optimize_tail_calls(const, tail_recursive_function_calls))
        else:
            new_consts.append(const)
    payload = code.co_code
    if code.co_name in tail_recursive_function_calls:
        payload = replace_tail_calls(code, tail_recursive_function_calls[code.co_name])
    return edit_function_code(code, payload, tuple(new_consts))

print(tail_recursive_function_calls)
new_code = optimize_tail_calls(module_code, tail_recursive_function_calls)

print('!!!new code!!!')
dis.dis(new_code)

exec(new_code)
