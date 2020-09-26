import ast, dis, astpretty
import inspect
import struct
from types import CodeType

with open('no_tail.py') as f: module_text = f.read()
module_ast = ast.parse(module_text)

astpretty.pprint(module_ast)

# for now use a simple defintion of tail recursive
# this definition is sound but not complete
# this definiton will be expanded later 
# TODO read about how Java / other pls do tail recursion
# For now the definition is:
# A sub function call can be tail call optimized if
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

# we will use this list to find them in the bytecode later
tail_recursive_function_ids = {}
for node in ast.walk(module_ast):
    if isinstance(node, ast.FunctionDef):
        if is_tail_recursive(node):
            tail_recursive_function_ids[node.name] = 1
            print(node.name, is_tail_recursive(node))

module_code = compile(module_ast, 'tail.py', 'exec')

# let's find our functions
dis.show_code(module_code)

dis.dis(module_code)

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

def surgery(function_code):
    payload = function_code.co_code
    for instr in dis.get_instructions(function_code):
        if instr.opname == 'CALL_FUNCTION':
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
            
    return payload

def optimize_tail_calls(code, tail_recursive_function_ids):
    new_consts = []
    for const in code.co_consts:
        if inspect.iscode(const):
            new_consts.append(optimize_tail_calls(const, tail_recursive_function_ids))
            #functions_by_id[instr.argval.co_name] = const.
            #sub_functions = optimized_tail_calls(instr.argval)
            # TODO note scopes will be a problem here
            # sub functions maybe can have identical names to existing functions
            # see if the AST already does something about this
            """for key in sub_functions.keys():
                functions_by_id[key] = sub_functions[key]"""
        else:
            new_consts.append(const)
    payload = code.co_code
    if code.co_name in tail_recursive_function_ids:
        payload = surgery(code)
    return edit_function_code(code, payload, tuple(new_consts))

new_code = optimize_tail_calls(module_code, tail_recursive_function_ids)

print('!!!new code!!!')
exec(new_code)
