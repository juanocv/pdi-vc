def vizinhos(H, W, B, y, x):
    HB, WB = len(B), len(B[0])
    oy = -HB / 2 + 0.5
    ox = -WB / 2 + 0.5
    for by in range(HB):
        for bx in range(WB):
            vy = int(y + by + oy)
            vx = int(x + bx + ox)
            if 0 <= vy < H and 0 <= vx < W:
                yield vy, vx, B[by][bx]

L = int(input())
C = int(input())
HB = int(input())
WB = int(input())
b = [list(map(int, input().split())) for _ in range(HB)]
f = [list(map(int, input().split())) for _ in range(L)]

for y in range(L):
    row = []
    for x in range(C):
        row.append(max(f[vy][vx] + peso for vy, vx, peso in vizinhos(L, C, b, y, x)))
    print(*row)
