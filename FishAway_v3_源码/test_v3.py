# -*- coding: utf-8 -*-
"""Fish away v3 集成测试（offscreen Qt）。"""
import os, sys, time
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import fishaway as fa
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
fa.DETECTION.update(fa.run_full_detection())
win = fa.MainWindow()
win.show()

# 模拟启用 env_demo
fa.CONFIG["plugins_enabled"] = ["env_demo.py"]
fa.load_enabled_plugins(win)

results = []

def check(name, cond):
    results.append((name, cond))
    print(("[PASS] " if cond else "[FAIL] ") + name)

def screen_text(view):
    if not view or view.screen is None:
        return ""
    lines = []
    hist = list(view.screen.hist)
    for line in hist + [[view.screen.buffer[y][x]
                         for x in range(view.screen.columns)]
                        for y in range(view.screen.lines)]:
        lines.append("".join(c.data for c in line))
    return "\n".join(lines)

def pump(sec):
    end = time.time() + sec
    while time.time() < end:
        app.processEvents(); time.sleep(0.02)

# 1. 环境注册
check("插件注册了 demo_deepsea 环境", "demo_deepsea" in fa.EXTRA_ENVIRONMENTS)
sb = win.sidebar
check("侧边栏出现插件环境按钮", "demo_deepsea" in sb.extra_session_buttons)
check("侧边栏出现插件按钮", sb.plugin_box.count() >= 1)

# 2. 教程注入
import tutorial
check("教程被注入新章节", tutorial.SECTIONS[-1][0] == "插件注入的示例章节")

# 3. 真实打开插件环境会话（本质是 cmd）
win.new_session("demo_deepsea")
view = win.current_view()
check("插件环境会话已创建", view is not None and view.profile_key == "demo_deepsea")
check("插件环境带渐变背景", isinstance(view.background, (list, tuple)))

# 等待 ConPTY 启动
pump(2.0)
view.send_line("echo PLUGINENV-WORKS")
pump(1.5)
stext = screen_text(view)
check("插件环境真实执行命令", "PLUGINENV-WORKS" in stext)

# 4. 起始目录检查：新开 cmd（普通用户），提示符应在用户目录
win.new_session("cmd")
cv = win.current_view()
pump(2.5)
stext = screen_text(cv)
home = os.path.expanduser("~")
check("CMD(普通) 起始于用户目录", home in stext)

# 5. 关闭标签不崩溃
idx = win.tabs.indexOf(view)
win.close_tab(idx)
app.processEvents()
check("关闭插件环境标签无异常", True)

ok = all(c for _, c in results)
print("V3 TEST:", "ALL PASS" if ok else "HAS FAILURES")
sys.exit(0 if ok else 1)
