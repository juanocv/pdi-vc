def vizinhos(H, W, B, y, x):
    HB, WB = len(B), len(B[0])
    oy = -HB / 2 + 0.5
    ox = -WB / 2 + 0.5
    for by in range(HB):
        for bx in range(WB):
            vy = int(y + by + oy)
            vx = int(x + bx + ox)
            if 0 <= vy < H and 0 <= vx < W and B[by][bx] == 1:
                yield vy, vx

def erosao(f, B):
    H, W = len(f), len(f[0])
    return [[min(f[vy][vx] for vy, vx in vizinhos(H, W, B, y, x)) for x in range(W)] for y in range(H)]

def dilatacao(f, B):
    H, W = len(f), len(f[0])
    Bref = [row[::-1] for row in B[::-1]]
    return [[max(f[vy][vx] for vy, vx in vizinhos(H, W, Bref, y, x)) for x in range(W)] for y in range(H)]

L = int(input())
C = int(input())
HB = int(input())
WB = int(input())
B = [list(map(int, input().split())) for _ in range(HB)]
f = [list(map(int, input().split())) for _ in range(L)]

g = dilatacao(erosao(f, B), B)
for row in g:
    print(*row)
