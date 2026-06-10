# Código Python
from morph import mm
L, C = int(input()), int(input())
alpha = float(input())
f1 = mm.readImg(L, C)
f2 = mm.readImg(L, C)
res = mm.blend(f1, f2, alpha)
print(mm.drawImage(res))
