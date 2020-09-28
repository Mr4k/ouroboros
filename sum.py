def sum(n, acc = 0):
    if n == 0:
        return acc
    return sum(n - 1, acc + n)

print(sum(10000000))
