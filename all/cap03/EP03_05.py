# Código Python
from morph import mm
L, C = int(input()), int(input())
f = mm.readImg(L, C)
m = mm.readImg(L, C)
res = mm.band(f, m)
print(mm.drawImage(res))
