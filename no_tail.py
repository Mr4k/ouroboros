# should return yes
def test1(n, acc = 0):
    if n == 0:
        return acc
    return test1(n - 1, acc + n)

# should current return no even though it maybe could be
def test2(n, acc = 0):
    if n == 0:
        return acc
    a = test2(n - 1, acc + n)
    return a

# not tail call optimizable
def test3(n):
    if n == 0:
        return 0
    return test3(n - 1) + 1

def test4(n):
    def test4_1(n, acc=0):
        if n == 0:
            return acc
        return test4_1(n - 1, acc + n)
    return test4_1(10)

def ouroboros():
    return ouroboros()

ouroboros()
