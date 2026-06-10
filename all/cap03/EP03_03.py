# Código Python
from morph import mm
L, C = int(input()), int(input())
img = mm.readImg(L, C)
res = mm.bnot(img)
print(mm.drawImage(res))
