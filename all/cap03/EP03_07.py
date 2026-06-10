# Código Python
from morph import mm
L, C = int(input()), int(input())
img = mm.readImg(L, C)
print(mm.drawImage(mm.laplacian(img)))
