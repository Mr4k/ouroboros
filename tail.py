def n_sum(n, acc = 0):
    if n == 0:
        return acc
    return n_sum(n - 1, acc + n)

print(n_sum(100))
