from collections import deque

L = int(input())
C = int(input())
K = int(input())
f = [list(map(int, input().split())) for _ in range(L)]

if K == 4:
    dirs = [(-1, 0), (0, -1), (0, 1), (1, 0)]
else:
    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

labels = [[0] * C for _ in range(L)]
desc = []
current = 0

for y in range(L):
    for x in range(C):
        if f[y][x] == 1 and labels[y][x] == 0:
            current += 1
            q = deque([(y, x)])
            labels[y][x] = current
            area = 0
            min_y = max_y = y
            min_x = max_x = x
            while q:
                cy, cx = q.popleft()
                area += 1
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                for dy, dx in dirs:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < L and 0 <= nx < C:
                        if f[ny][nx] == 1 and labels[ny][nx] == 0:
                            labels[ny][nx] = current
                            q.append((ny, nx))
            desc.append((current, area, min_y, min_x, max_y, max_x))

print(len(desc))
for item in desc:
    print(*item)
