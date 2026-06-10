# Código Python
from morph import mm
L, C = int(input()), int(input())
k = int(input())
img = mm.readImg(L, C)
res = mm.addm(img, k)
print(mm.drawImage(res))
