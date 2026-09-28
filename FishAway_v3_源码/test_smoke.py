# -*- coding: utf-8 -*-
"""Fish away 冒烟测试：自动开 CMD/PowerShell/Python，跑命令，开教程，截图校验"""
import importlib.machinery
import sys
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication

fa = importlib.machinery.SourceFileLoader(
    "fishaway", "fishaway.pyw").load_module()

results = []


def view_text(view):
    if not view or view.screen is None:
        return ""
    lines = []
    hist = list(view.screen.hist)
    for line in hist + [[view.screen.buffer[y][x]
                         for x in range(view.screen.columns)]
                        for y in range(view.screen.lines)]:
            lines.append("".join(c.data for c in line))
    return "\n".join(lines)


def grab_widget(widget, path):
    g = widget.frameGeometry()
    screen = QApplication.primaryScreen()
    screen.grabWindow(0, g.x(), g.y(), g.width(), g.height()).save(path)


app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setFont(fa.ui_font())
win = fa.MainWindow()
win.setWindowFlags(win.windowFlags() | Qt.WindowStaysOnTopHint)
win.show()
win.raise_()
win.activateWindow()

cmd_view = win.tabs.widget(0)


def step1():
    # CMD 已启动，跑 ver
    print("step1: cmd output lines =", len(cmd_view.old_runs),
          "alive =", cmd_view.pty.isalive())
    win.submit_line("ver")


def step2():
    win.new_session("ps")
    ps = win.current_view()

    def cmd():
        win.submit_line("echo PS-WORKS")
    QTimer.singleShot(900, cmd)


def step3():
    win.new_session("python")

    def cmd():
        win.submit_line("print('PY-WORKS')")
    QTimer.singleShot(900, cmd)


def step4():
    # 校验三个会话输出
    t_cmd = view_text(cmd_view)
    t_ps = view_text(win.tabs.widget(1))
    t_py = view_text(win.tabs.widget(2))
    results.append(("CMD 执行 ver", "Microsoft Windows" in t_cmd))
    results.append(("PowerShell echo", "PS-WORKS" in t_ps))
    results.append(("Python print", "PY-WORKS" in t_py))
    results.append(("CMD 进程存活", cmd_view.pty.isalive()))
    print("CMD has 版本:", "Microsoft Windows" in t_cmd)
    print("PS  has PS-WORKS:", "PS-WORKS" in t_ps)
    print("PY  has PY-WORKS:", "PY-WORKS" in t_py)
    # 打开教程并截图
    win.show_tutorial()
    win.tutorial_window.setWindowFlags(
        win.tutorial_window.windowFlags() | Qt.WindowStaysOnTopHint)
    win.tutorial_window.show(); win.tutorial_window.raise_()


def step5():
    grab_widget(win.tutorial_window, "shot_tutorial.png")
    # 教程翻到对照表
    win.tutorial_window.toc.setCurrentRow(11)
    print("tutorial sections:", len(fa_tutorial_sections()))


def fa_tutorial_sections():
    import tutorial
    return tutorial.SECTIONS


def step6():
    win.tutorial_window.close()
    win.tabs.setCurrentIndex(1)
    win.raise_()
    grab_widget(win, "shot_main.png")


def finish():
    for name, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    passed = all(ok for _, ok in results)
    print("SMOKE TEST:", "ALL PASS" if passed else "HAS FAILURES")
    app.quit()


QTimer.singleShot(1500, step1)
QTimer.singleShot(2800, step2)
QTimer.singleShot(4600, step3)
QTimer.singleShot(6400, step4)
QTimer.singleShot(7400, step5)
QTimer.singleShot(8200, step6)
QTimer.singleShot(9000, finish)

sys.exit(app.exec())
