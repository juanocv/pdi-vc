L = int(input())
C = int(input())
T = int(input())

img = [list(map(int, input().split())) for _ in range(L)]

for y in range(L):
    row = [255 if img[y][x] >= T else 0 for x in range(C)]
    print(*row)
