# Código Python
from morph import mm
L, C, N = int(input()), int(input()), int(input())
img = mm.readImg(L, C)
print(mm.drawImage(mm.blur0(img, N)))
