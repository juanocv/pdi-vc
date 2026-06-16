L = int(input())
C = int(input())
img = [list(map(int, input().split())) for _ in range(L)]
vals = [p for row in img for p in row]
N = len(vals)

hist = [0] * 256
for p in vals:
    hist[p] += 1

total_sum = sum(i * hist[i] for i in range(256))
w0 = 0
sum0 = 0
best_T = 0
best_var = -1.0

for T in range(255):
    w0 += hist[T]
    sum0 += T * hist[T]
    w1 = N - w0
    if w0 == 0 or w1 == 0:
        continue
    mu0 = sum0 / w0
    mu1 = (total_sum - sum0) / w1
    var_between = w0 * w1 * (mu0 - mu1) ** 2
    if var_between > best_var:
        best_var = var_between
        best_T = T

print(best_T)
for y in range(L):
    print(*[255 if img[y][x] > best_T else 0 for x in range(C)])
