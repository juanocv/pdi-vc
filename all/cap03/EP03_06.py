# Código Python
from morph import mm
import numpy as np

L, C, N = int(input()), int(input()), int(input())
img = mm.readImg(L, C)
r = N // 2
out = img.copy().astype(int)
for i in range(r, L - r):
    for j in range(r, C - r):
        out[i, j] = round(img[i-r:i+r+1, j-r:j+r+1].mean())
res = out.astype('uint8')
print(mm.drawImage(res))
