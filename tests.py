import math
import pytest

def assert_call_will_fail(call, arg):
    failed = False
    try:
        call(arg)
    except Exception as e:
        failed = True
    assert failed == True

def f1(n, acc = 0):
    if n == 0:
        return acc
    return f1(n - 1, acc + n)

assert f1(1000000) == 500000500000

def f2(n, acc = 0):
    if n == 0:
        return acc
    a = f2(n - 1, acc + n)
    return a

assert_call_will_fail(f2, 1000000)

def f3(n):
    if n == 0:
        return 0
    return f3(n - 1) + 1

assert_call_will_fail(f3, 1000000)

def f4(n):
    def f4_1(n, acc=0):
        if n == 0:
            return acc
        return f4_1(n - 1, acc + n)
    return f4_1(n)

assert f4(1000000) == 500000500000

def _f5_helper(n):
    return n - 1

def f5(n):
    if n == 1:
        return 0
    return f5(_f5_helper(n))

assert f5(1000000) == 0

def f6(n, acc = 0):
    if n <= 0:
        return acc
    if n % 2 == 0:
        return f6(n - 1, acc + 1)
    else:
        return f6(n - 3, acc + 3)

assert f6(1000000) == 1000000
