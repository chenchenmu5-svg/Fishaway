# -*- coding: utf-8 -*-
"""下载生成的图标 -> 裁紧 -> 输出 icon.png 与多尺寸 icon.ico"""
import subprocess
from PIL import Image

URL = "https://aka.doubaocdn.com/s/Gy5dU0HMJJ"
subprocess.run(["curl", "-L", "-sS", "-o", "icon_src.png", URL], check=True)

img = Image.open("icon_src.png").convert("RGBA")

# 找到圆角方块的边界（外部背景 g~35，方块内部暗色区 g~57+，鱼更亮）
px = img.load()
w, h = img.size
minx, miny, maxx, maxy = w, h, 0, 0
for y in range(0, h, 2):
    for x in range(0, w, 2):
        r, g, b, a = px[x, y]
        if g > 47 or r > 40:
            minx = min(minx, x); maxx = max(maxx, x)
            miny = min(miny, y); maxy = max(maxy, y)

# 留一点点边
pad = 14
minx = max(0, minx - pad); miny = max(0, miny - pad)
maxx = min(w, maxx + pad); maxy = min(h, maxy + pad)
side = max(maxx - minx, maxy - miny)
cx, cy = (minx + maxx) // 2, (miny + maxy) // 2
half = side // 2
box = (max(0, cx - half), max(0, cy - half),
       min(w, cx + half), min(h, cy + half))
icon = img.crop(box).resize((256, 256), Image.LANCZOS)
icon.save("FishAway/icon.png")

sizes = [16, 24, 32, 48, 64, 128, 256]
icons = {s: icon.resize((s, s), Image.LANCZOS) for s in sizes}
icons[256].save("FishAway/icon.ico", format="ICO",
                sizes=[(s, s) for s in sizes])
print("icon.ico / icon.png written, crop box:", box)
