# Código Python
from morph import mm
L, C, B = int(input()), int(input()), int(input())
img = mm.readImg(L, C)
res = mm.equalize(img, B)
print(mm.drawImage(res))
