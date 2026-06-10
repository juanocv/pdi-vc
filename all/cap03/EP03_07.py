# Código Python
from morph import mm
import numpy as np

L, C = int(input()), int(input())
img = mm.readImg(L, C)
out = img.copy().astype(int)
for i in range(1, L - 1):
    for j in range(1, C - 1):
        lap = (int(img[i-1,j]) + int(img[i+1,j]) +
               int(img[i,j-1]) + int(img[i,j+1]) - 4*int(img[i,j]))
        out[i,j] = max(0, min(255, int(img[i,j]) - lap))
res = out.astype('uint8')
print(mm.drawImage(res))
