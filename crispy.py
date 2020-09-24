from types import CodeType
import dis
import struct

def n_sum(n, acc = 0):
    if n == 0:
        return acc
    return n_sum(n - 1, acc + n)

def test():
    i = 0
    i += 1
    print(i)
    i -= 1

target = n_sum

def fix_function(func, payload):
    fn_code = func.__code__
    func.__code__ = CodeType(fn_code.co_argcount,
                             fn_code.co_kwonlyargcount,
                             fn_code.co_nlocals,
                             fn_code.co_stacksize,
                             fn_code.co_flags,
                             payload,
                             fn_code.co_consts,
                             fn_code.co_names,
                             fn_code.co_varnames,
                             fn_code.co_filename,
                             fn_code.co_name,
                             fn_code.co_firstlineno,
                             fn_code.co_lnotab,
                             fn_code.co_freevars,
                             fn_code.co_cellvars,
                             )
print(dis.dis(target))
payload = target.__code__.co_code

# replace FUNCTION_CALL WITH JUMP_ABSOLUTE
jump_opcode = dis.opmap['JUMP_ABSOLUTE']#.to_bytes(1, byteorder='little')
jump_address = 0
op = struct.pack('BB', jump_opcode, jump_address)

payload = payload[0:26] + op + payload[28:]

print(target(5))  # The result is: 64
# Now it's (x - y) instead of (x+y)
fix_function(target, payload)
print('try again')
print(target(5))  # The result is: 8
