from time import time
import os

os.system("meson builddir --wipe")
st1 = time()
os.system("ninja -C builddir")
endt1 = time()
st2 = time()
os.system("python builder.py")
endt2 = time()
print("ninja: " + str(endt1-st1), "builder.py:", endt2-st2)