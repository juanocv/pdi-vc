# Código Python
from morph import mm
import numpy as np

L, C = int(input()), int(input())
img = mm.readImg(L, C)
out = np.zeros((L, C), dtype='uint8')
for i in range(1, L - 1):
    for j in range(1, C - 1):
        gx = (int(img[i-1,j+1]) + 2*int(img[i,j+1]) + int(img[i+1,j+1])) - \
             (int(img[i-1,j-1]) + 2*int(img[i,j-1]) + int(img[i+1,j-1]))
        gy = (int(img[i+1,j-1]) + 2*int(img[i+1,j]) + int(img[i+1,j+1])) - \
             (int(img[i-1,j-1]) + 2*int(img[i-1,j]) + int(img[i-1,j+1]))
        out[i,j] = max(0, min(255, round((gx**2 + gy**2)**0.5)))
print(mm.drawImage(out))
