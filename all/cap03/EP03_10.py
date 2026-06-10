# Código Python%%writefile EP03_10.py
# Código Python
from morph import mm
L, C = int(input()), int(input())
k = float(input())
img = mm.readImg(L, C)
print(mm.drawImage(mm.usm0(img, k)))
