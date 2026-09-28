# -*- coding: utf-8 -*-
"""
====================================================================
   Fish away  v3  ——  对标 Windows Terminal 的 GUI 终端
--------------------------------------------------------------------
  · 左侧侧边栏：CMD / PowerShell / Python / Node.js / Git Bash / WSL
  · 中间大面板：pywinpty(ConPTY) + pyte 真实终端仿真
  · 底部输入框：回车运行；也可直接点击终端面板操作
  · 设置中心、管理员模式徽章、环境实时检测、国内镜像(Ctrl+Shift+Z)
  · 插件 v3：自定义按钮/图标/背景、注册全新环境与语言、
    向新手教程注入新章节；插件列表启用后重启生效
  · v3：性能优化、起始目录修复、崩溃与兼容性加固
====================================================================
"""
import sys
import os
import glob
import json
import queue
import threading
import ctypes
import difflib
import shutil
import time
import ast
import subprocess
from collections import deque

import pyte
from winpty import PtyProcess
from PySide6.QtCore import (Qt, QTimer, Signal, QObject, QPoint, QProcess,
                            QEvent)
from PySide6.QtGui import (QFont, QColor, QTextCharFormat, QTextCursor,
                           QPixmap, QIcon, QPainter, QLinearGradient, QPen,
                           QShortcut, QKeySequence)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame,
                               QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QLineEdit, QTabWidget, QPlainTextEdit, QTextEdit,
                               QDialog, QFileDialog, QMessageBox, QComboBox,
                               QCheckBox, QSpinBox, QSlider, QFormLayout,
                               QScrollArea)

from tutorial import TutorialWindow

APP_NAME = "Fish away"
APP_VERSION = "3.0"

TERM_FAMILIES = ["Cascadia Mono", "Cascadia Code", "Consolas", "Courier New"]
UI_FAMILIES = ["Segoe UI Variable Text", "Segoe UI", "Microsoft YaHei UI"]

ACCENT = "#22d3ee"
ACCENT_DIM = "#0e7490"

NAMED_COLORS = {
    "black": "#000000", "red": "#cd3131", "green": "#0dbc79",
    "brown": "#e5e510", "yellow": "#e5e510", "blue": "#2472c8",
    "magenta": "#bc3fbc", "cyan": "#11a8cd", "white": "#e5e5e5",
    "brightblack": "#666666", "gray": "#666666",
    "brightred": "#f14c4c", "brightgreen": "#23d18b",
    "brightbrown": "#f5f543", "brightyellow": "#f5f543",
    "brightblue": "#3b8eea", "brightmagenta": "#d670d6",
    "brightcyan": "#29b8db", "brightwhite": "#ffffff",
}

# ====================================================================
#  路径 / 配置
# ====================================================================
def app_dir():
    """用户数据目录（配置、插件）。打包后放 %APPDATA%，脚本模式放程序旁。"""
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        d = os.path.join(base, "FishAway")
    else:
        d = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(d, exist_ok=True)
    return d


def resource_path(name):
    """打包资源路径（PyInstaller onefile 解压目录）。"""
    base = getattr(sys, "_MEIPASS",
                   os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


APP_DIR = app_dir()
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
PLUGINS_DIR = os.path.join(APP_DIR, "plugins")

CONFIG_DEFAULTS = {
    "acrylic": True,
    "acrylic_alpha": 110,
    "term_font_family": "auto",
    "term_font_size": 11,
    "cursor_style": "block",         # block / bar / underline
    "scrollback": 5000,
    "default_profile": "cmd",
    "mirror": "china",               # china / global
    "paths": {"cmd": "", "ps": "", "python": "", "node": "",
              "gitbash": "", "wsl": ""},
    "wsl_distro": "",
    "plugins_enabled": [],
}


def load_config():
    cfg = json.loads(json.dumps(CONFIG_DEFAULTS))   # 深拷贝默认值
    try:
        # utf-8-sig 可兼容带 BOM 的配置（某些编辑器会写 BOM）
        with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
            user = json.load(f)
        for k, v in user.items():
            if k == "paths" and isinstance(v, dict):
                cfg["paths"].update(v)
            else:
                cfg[k] = v
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


CONFIG = load_config()

# 镜像源
MIRRORS = {
    "china": {
        "label": "国内镜像（清华 TUNA）",
        "pip": "https://pypi.tuna.tsinghua.edu.cn/simple",
    },
    "global": {
        "label": "国外官方源（PyPI）",
        "pip": "https://pypi.org/simple",
    },
}

# ====================================================================
#  管理员模式检测
# ====================================================================
def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


ADMIN = is_admin()

# ====================================================================
#  起始目录
# ====================================================================
HOME_DIR = os.path.expanduser("~")
SYSTEM32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                        "System32")


def default_cwd(key):
    """各会话的起始目录。
    CMD：普通用户=用户目录，管理员=C:\\Windows\\System32；
    PowerShell / Python / Node.js：一律用户目录；
    Git Bash：用户目录；WSL：Linux 家目录（Windows 侧 cwd 不影响它）。"""
    if key == "cmd":
        return SYSTEM32 if ADMIN else HOME_DIR
    if key in ("ps", "python", "node", "gitbash"):
        return HOME_DIR
    return None

# ====================================================================
#  字体
# ====================================================================
def ui_font():
    f = QFont()
    f.setFamilies(UI_FAMILIES)
    f.setPointSize(10)
    return f


def term_font(point_size=None, family=None):
    f = QFont()
    families = list(TERM_FAMILIES)
    fam = family or CONFIG.get("term_font_family", "auto")
    if fam and fam != "auto":
        families = [fam] + families
    f.setFamilies(families)
    f.setPointSize(int(point_size or CONFIG.get("term_font_size", 11)))
    f.setStyleHint(QFont.StyleHint.Monospace)
    return f


# ====================================================================
#  亚克力
# ====================================================================
class _AccentPolicy(ctypes.Structure):
    _fields_ = [("state", ctypes.c_int), ("flags", ctypes.c_int),
                ("color", ctypes.c_int), ("anim", ctypes.c_int)]


class _CompAttrData(ctypes.Structure):
    _fields_ = [("attrib", ctypes.c_int), ("data", ctypes.c_void_p),
                ("size", ctypes.c_size_t)]


def _set_acrylic(hwnd, state, alpha=110, tint_bgr=0x141110):
    accent = _AccentPolicy()
    accent.state = state
    accent.flags = 2
    accent.color = (alpha << 24) | tint_bgr
    data = _CompAttrData()
    data.attrib = 19
    data.data = ctypes.cast(ctypes.byref(accent), ctypes.c_void_p)
    data.size = ctypes.sizeof(accent)
    ctypes.windll.user32.SetWindowCompositionAttribute(
        hwnd, ctypes.byref(data))


def enable_acrylic(hwnd):
    # 深色标题栏
    try:
        v = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(v), ctypes.sizeof(v))
    except Exception:
        pass
    if not dwm_composition_enabled():
        # DWM 合成被关闭（常见于兼容模式/远程桌面）：放弃一切透明效果
        return
    if CONFIG.get("acrylic", True):
        _set_acrylic(hwnd, 4, int(CONFIG.get("acrylic_alpha", 110)))
    else:
        # 不透明纯色（视觉上关闭亚克力，避免窗口变全透明）
        _set_acrylic(hwnd, 4, 255)


def dwm_composition_enabled():
    """DwmIsCompositionEnabled：返回 False 时透明窗口会黑屏或闪退。"""
    try:
        val = ctypes.c_int(0)
        ctypes.windll.dwmapi.DwmIsCompositionEnabled(ctypes.byref(val))
        return bool(val.value)
    except Exception:
        return True


# ====================================================================
#  工具注册表 / 环境检测
# ====================================================================
def _env(path):
    return os.path.expandvars(path)


TOOL_META = {
    "cmd": {"label": "命令提示符 CMD", "icon": "cmd"},
    "ps": {"label": "PowerShell", "icon": "ps"},
    "python": {"label": "Python", "icon": "py",
               "home": "https://www.python.org/downloads/",
               "china": "https://mirrors.huaweicloud.com/python/",
               "advice": "安装时务必勾选 “Add Python to PATH”"},
    "node": {"label": "Node.js", "icon": "node",
             "home": "https://nodejs.org/",
             "china": "https://mirrors.huaweicloud.com/nodejs/",
             "advice": "安装 LTS 长期支持版，安装后自带 npm"},
    "gitbash": {"label": "Git Bash", "icon": "git",
                "home": "https://git-scm.com/download/win",
                "china": "https://mirrors.huaweicloud.com/git-for-windows/",
                "advice": "安装 Git for Windows 即自带 Git Bash"},
    "wsl": {"label": "WSL（Linux 子系统）", "icon": "wsl",
            "advice": "以管理员身份打开 PowerShell，运行 "
                      "wsl --install -d Ubuntu，然后重启电脑"},
}
SESSION_ORDER = ["cmd", "ps", "python", "node", "gitbash", "wsl"]

# 插件注册的额外环境：key -> {"label","argv","icon","background","cwd","advice"}
EXTRA_ENVIRONMENTS = {}

# 检测结果：key -> {"found": bool, "path": str, "note": str}
DETECTION = {}
WSL_DISTROS = []


def _candidates(key):
    pf = _env(r"%ProgramFiles%")
    pf86 = _env(r"%ProgramFiles(x86)%")
    lad = _env(r"%LOCALAPPDATA%")
    if key == "cmd":
        return [_env(r"%SystemRoot%\System32\cmd.exe")]
    if key == "ps":
        pwsh = shutil.which("pwsh")
        pwsh_dirs = glob.glob(os.path.join(pf, "PowerShell", "7*",
                                           "pwsh.exe"))
        pwsh_dirs += glob.glob(os.path.join(pf86, "PowerShell", "7*",
                                            "pwsh.exe"))
        return ([pwsh] if pwsh else []) + pwsh_dirs + [
            _env(r"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe")]
    if key == "python":
        c = []
        # 打包后 sys.executable 是 Fish away.exe 自己，绝不能当作 Python
        if not getattr(sys, "frozen", False):
            c.append(sys.executable)
        c += [shutil.which("python"), shutil.which("python3")]
        c += glob.glob(os.path.join(lad, "Programs", "Python",
                                    "Python3*", "python.exe"))
        c += glob.glob(os.path.join(pf, "Python3*", "python.exe"))
        return c
    if key == "node":
        c = [shutil.which("node")]
        c += [os.path.join(pf, "nodejs", "node.exe"),
              os.path.join(pf86, "nodejs", "node.exe")]
        c += glob.glob(os.path.join(lad, "Programs", "nodejs", "node.exe"))
        return c
    if key == "gitbash":
        return [os.path.join(pf, "Git", "bin", "bash.exe"),
                os.path.join(pf86, "Git", "bin", "bash.exe"),
                os.path.join(lad, "Programs", "Git", "bin", "bash.exe")]
    if key == "wsl":
        return [_env(r"%SystemRoot%\System32\wsl.exe"),
                shutil.which("wsl")]
    return []


def detect_tool(key):
    """返回可执行文件路径或 None。"""
    cfgp = CONFIG.get("paths", {}).get(key, "")
    if cfgp and os.path.isfile(cfgp):
        return cfgp
    for c in _candidates(key):
        if c and os.path.isfile(c):
            return c
    return None


def list_wsl_distros(wsl_path):
    try:
        out = subprocess.run([wsl_path, "-l", "-q"],
                             capture_output=True, timeout=12)
        text = out.stdout.decode("utf-16-le", errors="ignore").replace(
            "\x00", "")
        names = [ln.strip() for ln in text.splitlines() if ln.strip()]
        # 过滤错误提示行
        return [n for n in names if "Windows" not in n and "子系统" not in n
                and "适用于" not in n]
    except Exception:
        return []


def run_full_detection():
    results = {}
    for key in SESSION_ORDER:
        p = detect_tool(key)
        note = ""
        if key == "wsl" and p:
            global WSL_DISTROS
            WSL_DISTROS = list_wsl_distros(p)
            if not WSL_DISTROS:
                note = "no-distro"
        results[key] = {"found": p is not None and note != "no-distro",
                        "path": p or "", "note": note}
    return results


# 后台检测线程 + Qt 信号桥
class _Bridge(QObject):
    detected = Signal(object)


BRIDGE = _Bridge()


# ====================================================================
#  会话 argv 构造
# ====================================================================
def prepare_session(key):
    """返回 (argv, short_name)；不可用时返回 (None, short)。"""
    # ---- 插件注册的额外环境 ----
    if key in EXTRA_ENVIRONMENTS:
        env = EXTRA_ENVIRONMENTS[key]
        short = env.get("label", key)
        argv = env.get("argv")
        if callable(argv):
            try:
                argv = argv()
            except Exception:
                argv = None
        if isinstance(argv, str):
            argv = [argv]
        if argv:
            return list(argv), short
        return None, short

    meta = TOOL_META[key]
    short = meta["label"]
    info = DETECTION.get(key)
    path = None
    if info and info.get("path"):
        path = info["path"]
    else:
        path = detect_tool(key)
    if key == "wsl":
        if path:
            distros = WSL_DISTROS or list_wsl_distros(path)
            if not distros:
                return None, short
            d = CONFIG.get("wsl_distro", "")
            argv = [path] + (["-d", d] if d and d in distros else [])
            return argv, short
        return None, short
    if not path:
        return None, short
    if key == "cmd":
        return [path], short
    if key == "ps":
        is_pwsh = os.path.basename(path).lower().startswith("pwsh")
        return [path, "-NoLogo"], ("PowerShell 7" if is_pwsh else "PowerShell")
    if key == "python":
        return [path], "Python"
    if key == "node":
        return [path], "Node.js"
    if key == "gitbash":
        return [path, "--login", "-i"], "Git Bash"
    return [path], short


def build_notice(key):
    """生成缺失环境的 ANSI 彩色提示文本。"""
    if key in EXTRA_ENVIRONMENTS:
        env = EXTRA_ENVIRONMENTS[key]
        meta = {"label": env.get("label", key),
                "home": env.get("home", ""),
                "china": env.get("china", ""),
                "advice": env.get("advice", "")}
    else:
        meta = TOOL_META[key]
    m = MIRRORS[CONFIG.get("mirror", "china")]
    L = []
    L.append("\x1b[1;36m  ╔══════════════════════════════════════════╗")
    L.append("  ║        Fish away 环境检测 / 安装指引       ║")
    L.append("  ╚══════════════════════════════════════════╝\x1b[0m")
    L.append("")
    L.append(f"\x1b[1;31m  ✗ 未在本机检测到：{meta['label']}\x1b[0m")
    L.append("")
    if key == "wsl":
        L.append("  已找到 wsl.exe，但没有已安装的 Linux 发行版。")
        L.append("  请以管理员身份打开 PowerShell，运行：")
        L.append("\x1b[1;33m      wsl --install -d Ubuntu\x1b[0m")
        L.append("  安装完成后重启电脑，再回到 Fish away 打开 WSL。")
    else:
        if meta.get("advice"):
            L.append(f"  提示：{meta['advice']}")
        L.append("  官方下载地址：")
        L.append(f"\x1b[1;32m      {meta.get('home','')}\x1b[0m")
        if CONFIG.get("mirror") == "china" and meta.get("china"):
            L.append("  国内镜像（下载更快）：")
            L.append(f"\x1b[1;32m      {meta['china']}\x1b[0m")
    L.append("")
    L.append("\x1b[0;37m  如果你已经安装，但 Fish away 没检测到：\x1b[0m")
    L.append("  打开左下角「设置」→「会话路径」，可手动选择安装目录，")
    L.append("  或点击「自动检测」让软件重新扫描。")
    L.append("")
    L.append(f"\x1b[0;90m  当前下载源：{m['label']}（Ctrl+Shift+Z 一键切换）\x1b[0m")
    L.append("")
    return "\r\n".join(L)


# ====================================================================
#  带历史回滚的 pyte 屏幕
# ====================================================================
class HistoryScreen(pyte.Screen):
    def __init__(self, cols, rows, hist_limit=5000):
        self.hist = deque(maxlen=hist_limit)
        super().__init__(cols, rows)

    def index(self):
        top, bottom = self.margins or (0, self.lines - 1)
        if self.cursor.y == bottom:
            self.hist.append([self.buffer[top][x]
                              for x in range(self.columns)])
        super().index()

    def reset(self):
        super().reset()
        self.hist.clear()


RENDER_HIST = 200


# ====================================================================
#  终端视图
# ====================================================================
class CursorOverlay(QWidget):
    """覆盖在终端 viewport 上的透明层（不拦截鼠标），用于画 bar/underline
    光标。注意：不能用 setViewport 替换原 viewport，会导致 Qt 原生崩溃。"""

    def __init__(self, view):
        self.view = view
        super().__init__(view.viewport())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setGeometry(view.viewport().rect())
        view.viewport().installEventFilter(self)
        self.show()

    def eventFilter(self, obj, event):
        if obj is self.view.viewport():
            if event.type() == QEvent.Type.Resize:
                self.setGeometry(self.view.viewport().rect())
            elif event.type() == QEvent.Type.Paint:
                self.update()
        return False

    def paintEvent(self, event):
        self.view._paint_cursor_overlay()


class TerminalView(QPlainTextEdit):
    def __init__(self, argv, short_name, profile_key=None, notice=None,
                 background=None):
        super().__init__()
        self.argv = argv
        self.short_name = short_name
        self.profile_key = profile_key
        self.background = background      # 颜色/渐变/图片路径
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setCursorWidth(0)
        self.font_size = int(CONFIG.get("term_font_size", 11))
        self.setFont(term_font(self.font_size))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(self._build_stylesheet())
        self._cursor_overlay = None

        self.q = queue.Queue()
        self.pty = None
        self.screen = None
        self.stream = None
        self.exited = False
        self.exit_handler = None
        self._closing = False

        self.cols = 80
        self.rows = 24
        self._shown_hist = 0

        self.old_runs = []
        self.fmt_cache = {}
        self._run_cache = {}              # 行快照 id -> runs
        self._boot_time = 0.0
        self._handshake_replied = set()
        self._tail = ""                   # 跨 chunk 的查询缓冲
        self._last_render = 0.0
        self._render_pending = False
        self._last_cursor = None

        self._pump_timer = QTimer(self)
        self._pump_timer.setInterval(16)
        self._pump_timer.timeout.connect(self._pump)

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._apply_geometry)

        if notice is not None:
            self.show_notice(notice)

        self._cursor_overlay = CursorOverlay(self)

    # ---------------- 背景 / 样式表 ----------------
    def _bg_css(self):
        """把背景规格转成 Qt 样式表 background 片段。"""
        bg = self.background
        if not bg:
            return "rgba(26, 28, 34, 236)"
        if isinstance(bg, (list, tuple)) and len(bg) >= 2:
            # 渐变：[颜色1, 颜色2]
            return (f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                    f"stop:0 {bg[0]}, stop:1 {bg[1]})")
        if isinstance(bg, str) and os.path.isfile(bg):
            return f"url({bg_path(bg)})"
        return bg

    def _build_stylesheet(self):
        return f"""
            QPlainTextEdit {{
                background: {self._bg_css()};
                color: #dfe4ec;
                border: none;
                border-radius: 10px;
            }}
        """

    def apply_background(self, background):
        self.background = background
        self.setStyleSheet(self._build_stylesheet())

    # ---------------- 生命周期 ----------------
    def start(self):
        self._calc_grid()
        self._boot_time = time.monotonic()
        self._handshake_replied = set()
        limit = int(CONFIG.get("scrollback", 5000))
        self.screen = HistoryScreen(self.cols, self.rows, hist_limit=limit)
        self.stream = pyte.Stream(self.screen)
        cwd = self._session_cwd()
        pty_debug("SPAWN", f"id={id(self)} argv={self.argv} cwd={cwd} "
                           f"dims=({self.rows},{self.cols})")
        try:
            self.pty = PtyProcess.spawn(
                self.argv, cwd=cwd, dimensions=(self.rows, self.cols))
        except Exception as exc:
            self.append_fatal(f"[Fish away] 无法启动 {self.argv}: {exc}")
            self._on_exit()
            return
        threading.Thread(target=self._reader, daemon=True).start()
        self._pump_timer.start()
        # 安全网：无论合并渲染是否漏帧，每 120ms 强制对账一次，
        # 保证文档最终与屏幕一致（内容未变时 diff 为空，开销极小）
        self._safety_timer = QTimer(self)
        self._safety_timer.setInterval(120)
        self._safety_timer.timeout.connect(self._render)
        self._safety_timer.start()

    def _session_cwd(self):
        """插件环境优先用自带 cwd，否则按内置规则；目录不存在则回退用户目录。"""
        cwd = None
        k = self.profile_key
        if k in EXTRA_ENVIRONMENTS:
            cwd = EXTRA_ENVIRONMENTS[k].get("cwd")
        cwd = cwd or default_cwd(k)
        if cwd and not os.path.isdir(cwd):
            cwd = HOME_DIR
        return cwd

    def terminate(self):
        self._closing = True
        self._pump_timer.stop()
        try:
            self._safety_timer.stop()
        except Exception:
            pass
        try:
            if self.pty and self.pty.isalive():
                self.pty.terminate()
        except Exception:
            pass

    def append_fatal(self, text):
        if self.screen is None:
            self.screen = HistoryScreen(80, 24)
        self.screen.draw(text + "\r\n")

    def show_notice(self, ansi_text):
        """无 pty：仅展示环境检测/安装指引。"""
        self._calc_grid()
        self.screen = HistoryScreen(self.cols, self.rows)
        self.stream = pyte.Stream(self.screen)
        self.stream.feed(ansi_text)
        self.exited = True
        self._render()

    # ---------------- 读取线程 ----------------
    def _reader(self):
        while not self._closing:
            try:
                data = self.pty.read(8192)
            except Exception:
                break
            if data and not self._closing:
                pty_debug("RECV", data)
                self.q.put(data)
            try:
                alive = self.pty.isalive()
            except Exception:
                alive = False
            if not alive:
                break
        if not self._closing:
            self.q.put(None)

    # ---------------- pump ----------------
    def _pump(self):
        changed = False
        sentinel = False
        batch = []
        while True:
            try:
                item = self.q.get_nowait()
            except queue.Empty:
                break
            if item is None:
                sentinel = True
            else:
                batch.append(item)
                try:
                    self.stream.feed(item)
                    changed = True
                except Exception:
                    pass
        # 终端查询应答（DA / DA3 / CPR），跨 chunk 拼接检测
        if batch:
            self._answer_queries("".join(batch))
        now = time.monotonic()
        if changed:
            # 合并渲染：距上次渲染 >=28ms 立即渲染，否则延后一次
            if now - self._last_render >= 0.028:
                self._render()
                self._last_render = now
                self._render_pending = False
            elif not self._render_pending:
                self._render_pending = True
                QTimer.singleShot(18, self._deferred_render)
        if sentinel:
            self._on_exit()

    def _deferred_render(self):
        if self._render_pending:
            self._render_pending = False
            self._last_render = time.monotonic()
            self._render()

    def _answer_queries(self, text):
        # 保留尾部最多 16 字节，防止查询被切断
        blob = self._tail + text
        self._tail = blob[-16:]
        pty_debug("BLOB", blob)
        early = time.monotonic() - self._boot_time < 2.5
        if early and "\x1b[>c" in blob \
                and "da3" not in self._handshake_replied:
            self._handshake_replied.add("da3")
            self._write("\x1b[>0;0;0c")
        if early and "\x1b[c" in blob \
                and "da" not in self._handshake_replied:
            self._handshake_replied.add("da")
            self._write("\x1b[?1;0c")
        if "\x1b[6n" in blob and "cpr" not in self._handshake_replied:
            # 光标位置报告；节流标记，避免全屏程序高频查询时刷屏
            self._handshake_replied.add("cpr")
            if self.screen is not None:
                y = self.screen.cursor.y + 1
                x = self.screen.cursor.x + 1
                self._write(f"\x1b[{y};{x}R")
            QTimer.singleShot(120, self._reset_cpr_flag)

    def _reset_cpr_flag(self):
        self._handshake_replied.discard("cpr")

    def _on_exit(self):
        if self.exited:
            return
        self.exited = True
        self._render()
        self.setExtraSelections([])
        if self.exit_handler:
            self.exit_handler()

    # ---------------- 抽取行 ----------------
    def _line_runs(self, line):
        runs = []
        text = ""
        key = None
        for ch in line:
            k = (ch.fg, ch.bg, ch.bold, ch.italics, ch.underscore,
                 ch.strikethrough, ch.reverse)
            if key is not None and k != key:
                runs.append((text, key))
                text = ""
            key = k
            text += ch.data
        if text:
            runs.append((text, key))
        return runs

    def _runs_cached(self, snapshot):
        """历史快照不可变，按对象 id 缓存 runs，避免逐字符重算。"""
        sid = id(snapshot)
        runs = self._run_cache.get(sid)
        if runs is None:
            runs = self._line_runs(snapshot)
            self._run_cache[sid] = runs
        return runs

    def _collect(self):
        hist = list(self.screen.hist)
        shown = hist[-RENDER_HIST:]
        body = [[self.screen.buffer[y][x]
                 for x in range(self.screen.columns)]
                for y in range(self.screen.lines)]
        self._shown_hist = len(shown)
        out = [self._runs_cached(ln) for ln in shown]
        out += [self._line_runs(ln) for ln in body]
        # 缓存过大（快照已滚出 deque）时按当前快照清理
        cap = int(CONFIG.get("scrollback", 5000)) * 2 + 400
        if len(self._run_cache) > cap:
            live = {id(s) for s in self.screen.hist}
            self._run_cache = {
                k: v for k, v in self._run_cache.items() if k in live}
        return out

    # ---------------- 样式 ----------------
    def _resolve_color(self, value):
        if not value or value == "default":
            return None
        if value in NAMED_COLORS:
            return QColor(NAMED_COLORS[value])
        if len(value) == 6:
            c = QColor("#" + value)
            return c if c.isValid() else None
        return None

    def _char_format(self, key):
        if key in self.fmt_cache:
            return self.fmt_cache[key]
        fg, bg, bold, ital, under, strike, rev = key
        if rev:
            fg, bg = bg, fg
        fmt = QTextCharFormat()
        fmt.setFontFamilies(self.font().families())
        c = self._resolve_color(fg)
        if c:
            fmt.setForeground(c)
        c = self._resolve_color(bg)
        if c:
            fmt.setBackground(c)
        if bold:
            fmt.setFontWeight(700)
        if ital:
            fmt.setFontItalic(True)
        if under:
            fmt.setFontUnderline(True)
        if strike:
            fmt.setFontStrikeOut(True)
        self.fmt_cache[key] = fmt
        return fmt

    # ---------------- 增量渲染 ----------------
    @staticmethod
    def _line_key(runs):
        return tuple((text, key) for text, key in runs)

    def _doc_delete(self, i1, i2):
        doc = self.document()
        cur = QTextCursor(doc.findBlockByNumber(i1))
        if i2 >= doc.blockCount():
            cur.movePosition(QTextCursor.MoveOperation.End,
                             QTextCursor.MoveMode.KeepAnchor)
        else:
            cur.setPosition(doc.findBlockByNumber(i2).position(),
                            QTextCursor.MoveMode.KeepAnchor)
        cur.removeSelectedText()

    def _insert_line(self, cur, runs):
        for text, key in runs:
            cur.insertText(text, self._char_format(key))

    def _doc_insert(self, index, lines):
        doc = self.document()
        base = QTextCharFormat()
        base.setFontFamilies(self.font().families())
        if index >= doc.blockCount():
            cur = QTextCursor(doc)
            cur.movePosition(QTextCursor.MoveOperation.End)
            for line in lines:
                cur.insertText("\n", base)
                self._insert_line(cur, line)
        else:
            cur = QTextCursor(doc.findBlockByNumber(index))
            for line in lines:
                self._insert_line(cur, line)
                cur.insertText("\n", base)

    def _render(self):
        if self.screen is None:
            return
        new_runs = self._collect()
        new_keys = [self._line_key(r) for r in new_runs]
        old_keys = [self._line_key(r) for r in self.old_runs]

        sb = self.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 2

        pty_debug("RENDER", f"id={id(self)} new={len(new_keys)} "
                            f"old={len(old_keys)} "
                            f"diff={new_keys != old_keys} "
                            f"blocks={self.document().blockCount()} "
                            f"visible={self.isVisible()} "
                            f"cur=({self.screen.cursor.y},{self.screen.cursor.x}) "
                            f"sample={new_keys[0][0][0][:40] if new_keys and new_keys[0] else ''}")
        if new_keys != old_keys:
            n_old, n_new = len(old_keys), len(new_keys)
            prefix = (n_new > n_old and new_keys[:n_old] == old_keys)
            if prefix:
                # 快路径：旧内容完全是新内容的前缀，仅插入新增尾部
                self._doc_insert(n_old, new_runs[n_old:])
            else:
                matcher = difflib.SequenceMatcher(a=old_keys, b=new_keys,
                                                  autojunk=False)
                for tag, i1, i2, j1, j2 in reversed(matcher.get_opcodes()):
                    if tag in ("delete", "replace"):
                        self._doc_delete(i1, i2)
                    if tag in ("insert", "replace"):
                        self._doc_insert(i1, new_runs[j1:j2])
            self.old_runs = new_runs

        if at_bottom:
            sb.setValue(sb.maximum())

        self._update_cursor()

    def _update_cursor(self):
        style = CONFIG.get("cursor_style", "block")
        if self.exited or self.screen is None or style != "block":
            if self._last_cursor is not None:
                self._last_cursor = None
                self.setExtraSelections([])
            return
        y = self._shown_hist + self.screen.cursor.y
        x = min(self.screen.cursor.x, self.screen.columns - 1)
        if self._last_cursor == (y, x):
            return
        self._last_cursor = (y, x)
        block = self.document().findBlockByNumber(y)
        if not block.isValid():
            return
        p1 = block.position() + x
        p2 = min(p1 + 1, block.position() + block.length() - 1)
        cur = QTextCursor(block)
        cur.setPosition(p1)
        cur.setPosition(p2, QTextCursor.MoveMode.KeepAnchor)
        sel = QTextEdit.ExtraSelection()
        sel.cursor = cur
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(ACCENT))
        fmt.setForeground(QColor("#052329"))
        sel.format = fmt
        self.setExtraSelections([sel])

    def _cursor_rect(self):
        if self.screen is None:
            return None
        y = self._shown_hist + self.screen.cursor.y
        x = min(self.screen.cursor.x, self.screen.columns - 1)
        block = self.document().findBlockByNumber(y)
        if not block.isValid():
            return None
        layout = block.layout()
        line = layout.lineAt(0)
        cx = line.cursorToX(x)
        yp = layout.position().y() + line.y()
        off = self.contentOffset()
        cw = self.fontMetrics().horizontalAdvance("M")
        ch = max(line.rect().height(), self.fontMetrics().lineSpacing())
        return QRectF_like(cx + off.x(), yp + off.y(), cw, ch)

    def _paint_cursor_overlay(self):
        style = CONFIG.get("cursor_style", "block")
        if self.exited or self.screen is None or style not in ("bar",
                                                               "underline"):
            return
        r = self._cursor_rect()
        if r is None:
            return
        p = QPainter(self._cursor_overlay)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(ACCENT))
        if style == "bar":
            p.drawRect(QRectF_like(r.x(), r.y() + 1, 2.2, r.height() - 2))
        else:
            p.drawRect(QRectF_like(r.x(), r.y() + r.height() - 2.2,
                                   r.width(), 2.2))
        p.end()

    # ---------------- 尺寸 ----------------
    def _calc_grid(self):
        fm = self.fontMetrics()
        cw = fm.horizontalAdvance("M")
        ch = fm.lineSpacing()
        if cw <= 0 or ch <= 0:
            return False
        vw, vh = self.viewport().width(), self.viewport().height()
        if vw <= cw or vh <= ch:
            # 视口尚未布局完成：保持当前（默认 80x24），不要算出 1x1
            return False
        cols = vw // cw
        rows = vh // ch
        changed = (cols, rows) != (self.cols, self.rows)
        self.cols, self.rows = cols, rows
        return changed

    def _apply_geometry(self):
        if not self._calc_grid():
            return
        if self.pty:
            # 启动后 400ms 内不重设尺寸，避免 ConPTY 在初始化阶段被
            # 连续 setwinsize 打乱导致输出停滞
            if time.monotonic() - self._boot_time >= 0.4:
                try:
                    self.pty.setwinsize(self.cols, self.rows)
                except Exception:
                    pass
                try:
                    self.screen.resize(lines=self.rows, columns=self.cols)
                except Exception:
                    pass
        self._render()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(60)

    # ---------------- 按键 ----------------
    _SIMPLE_KEYS = {
        Qt.Key.Key_Return: "\r", Qt.Key.Key_Enter: "\r",
        Qt.Key.Key_Backspace: "\x7f", Qt.Key.Key_Tab: "\t",
        Qt.Key.Key_Escape: "\x1b", Qt.Key.Key_Delete: "\x1b[3~",
        Qt.Key.Key_Insert: "\x1b[2~", Qt.Key.Key_Home: "\x1b[H",
        Qt.Key.Key_End: "\x1b[F", Qt.Key.Key_Up: "\x1b[A",
        Qt.Key.Key_Down: "\x1b[B", Qt.Key.Key_Right: "\x1b[C",
        Qt.Key.Key_Left: "\x1b[D", Qt.Key.Key_PageUp: "\x1b[5~",
        Qt.Key.Key_PageDown: "\x1b[6~",
    }
    _FUNCTION_KEYS = {
        Qt.Key.Key_F1: "\x1bOP", Qt.Key.Key_F2: "\x1bOQ",
        Qt.Key.Key_F3: "\x1bOR", Qt.Key.Key_F4: "\x1bOS",
        Qt.Key.Key_F5: "\x1b[15~", Qt.Key.Key_F6: "\x1b[17~",
        Qt.Key.Key_F7: "\x1b[18~", Qt.Key.Key_F8: "\x1b[19~",
        Qt.Key.Key_F9: "\x1b[20~", Qt.Key.Key_F10: "\x1b[21~",
        Qt.Key.Key_F11: "\x1b[23~", Qt.Key.Key_F12: "\x1b[24~",
    }

    def _write(self, data):
        pty_debug("SEND", data)
        if self.pty and not self.exited:
            try:
                self.pty.write(data)
            except Exception:
                pass

    def keyPressEvent(self, event):
        if self.exited:
            return
        mods = event.modifiers()
        k = event.key()

        if mods & Qt.KeyboardModifier.ControlModifier:
            if k in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self._zoom(1); return
            if k == Qt.Key.Key_Minus:
                self._zoom(-1); return
            if k == Qt.Key.Key_0:
                self._zoom(0); return

        if mods & Qt.KeyboardModifier.ControlModifier \
                and not (mods & Qt.KeyboardModifier.AltModifier):
            b = None
            if Qt.Key.Key_A <= k <= Qt.Key.Key_Z:
                b = chr(ord("a") + k - Qt.Key.Key_A)
            elif k == Qt.Key.Key_BracketLeft:
                b = "\x1b"
            elif k == Qt.Key.Key_BracketRight:
                b = "\x1d"
            elif k == Qt.Key.Key_Backslash:
                b = "\x1c"
            elif k == Qt.Key.Key_Underscore:
                b = "\x1f"
            elif k == Qt.Key.Key_Space:
                b = "\x00"
            if b is not None:
                self._write(b)
                return

        if k == Qt.Key.Key_Backtab:
            self._write("\x1b[Z")
            return
        if k in self._SIMPLE_KEYS:
            self._write(self._SIMPLE_KEYS[k])
            return
        if k in self._FUNCTION_KEYS:
            self._write(self._FUNCTION_KEYS[k])
            return
        if mods & Qt.KeyboardModifier.AltModifier and event.text():
            self._write("\x1b" + event.text())
            return
        text = event.text()
        if text:
            self._write(text)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._zoom(1 if event.angleDelta().y() > 0 else -1)
        else:
            super().wheelEvent(event)

    def _zoom(self, direction):
        if direction == 0:
            self.font_size = int(CONFIG.get("term_font_size", 11))
        else:
            self.font_size = max(7, min(20,
                                        self.font_size + direction * 0.5))
        self.apply_font()

    def apply_font(self):
        self.setFont(term_font(self.font_size))
        self.fmt_cache.clear()
        self._apply_geometry()

    # ---------------- 对外接口 ----------------
    def send_line(self, text):
        self.scroll_to_bottom()
        self._write(text + "\r")

    def send_special(self, prefix, seq):
        if prefix:
            self._write(prefix)
        self._write(seq)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum())


def QRectF_like(x, y, w, h):
    from PySide6.QtCore import QRectF
    return QRectF(float(x), float(y), float(w), float(h))


def bg_path(p):
    """Qt 样式表 url() 使用正斜杠。"""
    return str(p).replace("\\", "/")


def pty_debug(tag, text):
    if not os.environ.get("FISHDEBUG"):
        return
    try:
        with open(os.path.join(APP_DIR, "pty_debug.log"), "a",
                  encoding="utf-8") as f:
            f.write(tag + " " + repr(text[:240]) + "\n")
    except Exception:
        pass


# ====================================================================
#  底部输入框
# ====================================================================
class CommandInput(QLineEdit):
    lineSubmitted = Signal(str)
    specialRequested = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setPlaceholderText(
            "在这里输入命令，按 Enter 运行……（Tab 补全 / ↑↓历史 / Ctrl+C 中断，"
            "也可直接点击上方终端面板操作）")
        self.setFrame(False)
        self.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: #e8edf4;
                font-size: 11pt;
                selection-background-color: rgba(34, 211, 238, 90);
                padding: 2px 6px;
            }
        """)

    def keyPressEvent(self, event):
        k = event.key()
        mods = event.modifiers()
        if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.lineSubmitted.emit(self.text())
            self.clear(); return
        if mods & Qt.KeyboardModifier.ControlModifier:
            if k == Qt.Key.Key_C:
                self.specialRequested.emit(self.text(), "\x03")
                self.clear(); return
            if k == Qt.Key.Key_L:
                self.specialRequested.emit(self.text(), "\x0c")
                self.clear(); return
        if k in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Tab):
            seq = {Qt.Key.Key_Up: "\x1b[A", Qt.Key.Key_Down: "\x1b[B",
                   Qt.Key.Key_Tab: "\t"}[k]
            self.specialRequested.emit(self.text(), seq)
            self.clear(); return
        if k == Qt.Key.Key_Escape:
            self.clear(); return
        super().keyPressEvent(event)


# ====================================================================
#  鱼形 Logo
# ====================================================================
class FishLogo(QWidget):
    def __init__(self, size=54, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, int(size * 0.78))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor("#67e8f9"))
        g.setColorAt(1, QColor("#0891b2"))
        p.setBrush(g)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon([QPoint(11, self.height() // 2), QPoint(0, 2),
                       QPoint(0, self.height() - 2)])
        p.drawEllipse(8, 4, self.width() - 14, self.height() - 10)
        p.drawPolygon([
            QPoint(int(self.width() * 0.5), self.height() - 8),
            QPoint(int(self.width() * 0.62), self.height() - 8),
            QPoint(int(self.width() * 0.52), self.height() - 1)])
        p.setBrush(QColor("white"))
        ex = self.width() - 13
        p.drawEllipse(ex, int(self.height() * 0.28), 7, 7)
        p.setBrush(QColor("#0b2b33"))
        p.drawEllipse(ex + 3, int(self.height() * 0.28) + 2, 3, 3)


# ====================================================================
#  小图标
# ====================================================================
def make_icon(kind, size=22):
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)

    if kind == "cmd":
        p.setBrush(QColor("#d9d9d9"))
        p.drawRoundedRect(1, 1, size - 2, size - 2, 5, 5)
        p.setPen(QColor("#111111"))
        f = p.font(); f.setBold(True); f.setPointSize(8); p.setFont(f)
        p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "C")
    elif kind == "ps":
        p.setBrush(QColor("#0a6dca"))
        p.drawRoundedRect(1, 1, size - 2, size - 2, 5, 5)
        p.setPen(QColor("white"))
        f = p.font(); f.setBold(True); f.setPointSize(7); p.setFont(f)
        p.drawText(pix.rect().adjusted(0, 1, 0, 0),
                   Qt.AlignmentFlag.AlignCenter, ">_")
    elif kind == "py":
        p.setBrush(QColor("#3776ab"))
        p.drawRoundedRect(1, 1, size - 2, size - 2, 5, 5)
        p.setPen(QColor("white"))
        f = p.font(); f.setBold(True); f.setPointSize(7); p.setFont(f)
        p.drawText(pix.rect().adjusted(0, 1, 0, 0),
                   Qt.AlignmentFlag.AlignCenter, "Py")
    elif kind == "node":
        p.setBrush(QColor("#3c873a"))
        p.drawRoundedRect(1, 1, size - 2, size - 2, 5, 5)
        p.setPen(QColor("white"))
        f = p.font(); f.setBold(True); f.setPointSize(7); p.setFont(f)
        p.drawText(pix.rect().adjusted(0, 1, 0, 0),
                   Qt.AlignmentFlag.AlignCenter, "JS")
    elif kind == "git":
        p.setBrush(QColor("#f05133"))
        p.drawRoundedRect(1, 1, size - 2, size - 2, 5, 5)
        p.setBrush(QColor("white"))
        p.drawEllipse(6, 5, 4, 4); p.drawEllipse(12, 11, 4, 4)
        p.drawEllipse(6, 13, 4, 4)
        p.drawRect(7, 8, 2, 6); p.drawRect(9, 12, 4, 2)
    elif kind == "wsl":
        p.setBrush(QColor("#22272e"))
        p.drawRoundedRect(1, 1, size - 2, size - 2, 5, 5)
        # 小企鹅
        p.setBrush(QColor("#f2f2f2"))
        p.drawEllipse(7, 6, 8, 12)
        p.drawEllipse(7, 4, 3, 3); p.drawEllipse(12, 4, 3, 3)
        p.setBrush(QColor("#111418"))
        p.drawEllipse(9, 14, 4, 4)
    elif kind == "gear":
        p.setPen(QPen(QColor("#9aa3b2"), 1.5))
        p.setBrush(QColor("#2b3038"))
        p.drawEllipse(5, 5, 12, 12)
        for a in range(0, 360, 45):
            import math
            x = 11 + 8 * math.cos(math.radians(a))
            y = 11 + 8 * math.sin(math.radians(a))
            p.drawEllipse(QPoint(int(x), int(y)), 2, 2)
        p.setBrush(QColor("#9aa3b2"))
        p.drawEllipse(8, 8, 6, 6)
    elif kind == "shield":
        p.setBrush(QColor("#9aa3b2"))
        p.drawPolygon([QPoint(11, 2), QPoint(19, 5), QPoint(19, 11),
                       QPoint(11, 20), QPoint(3, 11), QPoint(3, 5)])
        p.setPen(QColor("#111418"))
        f = p.font(); f.setBold(True); f.setPointSize(8); p.setFont(f)
        p.drawText(pix.rect().adjusted(0, 1, 0, 0),
                   Qt.AlignmentFlag.AlignCenter, "!")
    elif kind == "plug":
        p.setPen(QPen(QColor("#9aa3b2"), 1.6))
        p.setBrush(QColor("#2b3038"))
        p.drawRoundedRect(5, 8, 12, 9, 3, 3)
        p.drawLine(9, 8, 9, 4); p.drawLine(13, 8, 13, 4)
        p.drawLine(17, 12, 20, 12)
    elif kind == "book":
        p.setBrush(QColor(ACCENT))
        p.drawRoundedRect(2, 1, size - 4, size - 2, 3, 3)
        p.setPen(QColor("#052329"))
        f = p.font(); f.setBold(True); f.setPointSize(9); p.setFont(f)
        p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "?")
    elif kind == "broom":
        p.setBrush(QColor("#9aa3b2"))
        p.drawRect(4, 3, 3, 10)
        p.setBrush(QColor("#e5c07b"))
        p.drawPolygon([QPoint(2, 13), QPoint(9, 13), QPoint(11, 20),
                       QPoint(0, 20)])
    elif kind == "info":
        p.setPen(QPen(QColor("#9aa3b2"), 1.6))
        p.drawEllipse(2, 2, size - 5, size - 5)
        f = p.font(); f.setBold(True); f.setPointSize(8); p.setFont(f)
        p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "i")
    p.end()
    return QIcon(pix)


_BUILTIN_ICONS = {"cmd", "ps", "py", "node", "git", "wsl", "gear",
                  "shield", "plug", "book", "broom", "info"}


def text_icon(text, size=22, tile="#2b3038", color="#e8edf4"):
    """把 emoji 或 1~3 个字符画成圆角方块图标。"""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(tile))
    p.drawRoundedRect(1, 1, size - 2, size - 2, 5, 5)
    p.setPen(QColor(color))
    f = p.font(); f.setBold(True)
    f.setPointSize(9 if len(text) <= 1 else 7)
    p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, text[:3])
    p.end()
    return QIcon(pix)


def resolve_icon(spec, fallback="plug", size=22, tile="#2b3038"):
    """统一图标解析：
    · QIcon/QPixmap 直接用；
    · 内置图标名（cmd/ps/py/node/git/wsl/gear…）走 make_icon；
    · 存在的图片文件（.ico/.png/.jpg）按文件加载；
    · 其它字符串当作 emoji/短文字绘制。"""
    if isinstance(spec, QIcon):
        return spec
    if isinstance(spec, QPixmap):
        return QIcon(spec)
    if not spec:
        return make_icon(fallback)
    if isinstance(spec, str):
        if spec in _BUILTIN_ICONS:
            return make_icon(spec)
        if os.path.isfile(spec):
            ic = QIcon(spec)
            if not ic.isNull():
                return ic
        return text_icon(spec, size=size, tile=tile)
    return make_icon(fallback)


# ====================================================================
#  Toast 轻提示
# ====================================================================
class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""
            QLabel {
                background: rgba(18, 22, 28, 240);
                color: #eafcfe;
                border: 1px solid rgba(34,211,238,120);
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 10pt;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_text(self, text, ms=2400):
        self.setText(text)
        self.adjustSize()
        p = self.parentWidget()
        self.move((p.width() - self.width()) // 2,
                  p.height() - self.height() - 90)
        self.show(); self.raise_()
        self._timer.start(ms)


# ====================================================================
#  侧边栏
# ====================================================================
class Sidebar(QFrame):
    newSession = Signal(str)
    openTutorial = Signal()
    openAbout = Signal()
    openSettings = Signal()
    clearScreen = Signal()
    elevate = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(196)
        self.setStyleSheet("""
            QFrame { background: rgba(17, 19, 25, 215); border-radius: 12px; }
        """)
        box = QVBoxLayout(self)
        box.setContentsMargins(12, 16, 12, 14)
        box.setSpacing(8)

        logo_row = QHBoxLayout()
        logo_row.addWidget(FishLogo(50))
        title = QVBoxLayout()
        t1 = QLabel("Fish away")
        t1.setStyleSheet("color:#f2f6fa; font-size:14pt; font-weight:700;")
        title.addWidget(t1)
        logo_row.addLayout(title)
        logo_w = QWidget(); logo_w.setLayout(logo_row)
        logo_w.setStyleSheet("background: transparent;")
        box.addWidget(logo_w)

        # 管理员模式徽章
        self.admin_badge = QPushButton()
        self.admin_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self.admin_badge.setFixedHeight(30)
        self.admin_badge.setIcon(make_icon("shield"))
        self._render_badge()
        self.admin_badge.clicked.connect(self._badge_clicked)
        box.addWidget(self.admin_badge)
        box.addSpacing(4)

        cap = QLabel("新建会话")
        cap.setStyleSheet("color:#6b7482; font-size:9pt; "
                          "background:transparent; padding-left:6px;")
        box.addWidget(cap)

        self.session_buttons = {}
        for key in SESSION_ORDER:
            meta = TOOL_META[key]
            btn = QPushButton("  " + meta["label"])
            btn.setIcon(make_icon(meta["icon"]))
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._btn_qss())
            btn.clicked.connect(lambda _=False, k=key: self.newSession.emit(k))
            self.session_buttons[key] = btn
            box.addWidget(btn)

        # 插件注册的额外环境（动态）
        self.extra_caption = QLabel("插件环境")
        self.extra_caption.setStyleSheet(
            "color:#6b7482; font-size:9pt; background:transparent;"
            "padding-left:6px;")
        self.extra_caption.hide()
        box.addWidget(self.extra_caption)
        self.extra_session_buttons = {}
        self.extra_box = QVBoxLayout()
        self.extra_box.setSpacing(4)
        ew = QWidget(); ew.setStyleSheet("background:transparent;")
        ew.setLayout(self.extra_box)
        box.addWidget(ew)

        # 插件按钮区
        self.plugin_caption = QLabel("插件")
        self.plugin_caption.setStyleSheet(
            "color:#6b7482; font-size:9pt; background:transparent;"
            "padding-left:6px;")
        self.plugin_caption.hide()
        box.addWidget(self.plugin_caption)
        self.plugin_box = QVBoxLayout()
        self.plugin_box.setSpacing(4)
        pw = QWidget(); pw.setStyleSheet("background:transparent;")
        pw.setLayout(self.plugin_box)
        box.addWidget(pw)

        box.addStretch(1)

        clear_btn = QPushButton("  清屏 (Ctrl+L)")
        clear_btn.setIcon(make_icon("broom"))
        clear_btn.setFixedHeight(36)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(self._btn_qss(dim=True))
        clear_btn.clicked.connect(self.clearScreen.emit)
        box.addWidget(clear_btn)

        settings_btn = QPushButton("  设置")
        settings_btn.setIcon(make_icon("gear"))
        settings_btn.setFixedHeight(36)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet(self._btn_qss(dim=True))
        settings_btn.clicked.connect(self.openSettings.emit)
        box.addWidget(settings_btn)

        tut_btn = QPushButton("  新手教程（20 章）")
        tut_btn.setIcon(make_icon("book"))
        tut_btn.setFixedHeight(52)
        tut_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tut_btn.setStyleSheet("""
            QPushButton {
                text-align:left; color:#042026;
                background: rgba(34,211,238,235);
                border:none; border-radius:10px;
                padding-left:10px; font-weight:700; font-size:10pt;
            }
            QPushButton:hover { background: rgba(103,232,249,245); }
        """)
        tut_btn.clicked.connect(self.openTutorial.emit)
        box.addWidget(tut_btn)

        about_btn = QPushButton("  关于 Fish away")
        about_btn.setIcon(make_icon("info"))
        about_btn.setFixedHeight(34)
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        about_btn.setStyleSheet(self._btn_qss(dim=True, h=12))
        about_btn.clicked.connect(self.openAbout.emit)
        box.addWidget(about_btn)

    @staticmethod
    def _btn_qss(dim=False, h=16):
        color = "#c6ccd8" if dim else "#d5dbe6"
        return f"""
            QPushButton {{
                text-align: left; color: {color}; background: transparent;
                border: none; border-radius: 8px; padding-left: 10px;
                font-size: 10pt;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,{h}); }}
            QPushButton:pressed {{ background: rgba(255,255,255,26); }}
        """

    def _render_badge(self):
        if ADMIN:
            text = "  管理员模式"
            qss = """
                QPushButton { text-align:left; color:#ffd9a0;
                    background: rgba(245,158,11,45); border:1px solid
                    rgba(245,158,11,120); border-radius:8px; font-size:9pt; }
                QPushButton:hover { background: rgba(245,158,11,70); }
            """
        else:
            text = "  普通用户模式（点击提权）"
            qss = """
                QPushButton { text-align:left; color:#9fb4c0;
                    background: rgba(255,255,255,12); border:1px solid
                    rgba(255,255,255,22); border-radius:8px; font-size:9pt; }
                QPushButton:hover { background: rgba(255,255,255,24); }
            """
        self.admin_badge.setText(text)
        self.admin_badge.setStyleSheet(qss)

    def _badge_clicked(self):
        if not ADMIN:
            self.elevate.emit()

    @staticmethod
    def _custom_btn_qss(bg):
        if isinstance(bg, (list, tuple)):
            bg = (f"qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                  f"stop:0 {bg[0]}, stop:1 {bg[1]})")
        return f"""
            QPushButton {{
                text-align:left; color:#e8edf4; background: {bg};
                border:none; border-radius:8px; padding-left:10px;
                font-size:10pt;
            }}
            QPushButton:hover {{ border:1px solid rgba(34,211,238,160); }}
            QPushButton:pressed {{ border:1px solid rgba(34,211,238,220); }}
        """

    def add_plugin_button(self, label, callback, icon=None, background=None):
        self.plugin_caption.show()
        btn = QPushButton("  " + label)
        btn.setIcon(resolve_icon(icon, fallback="plug"))
        btn.setFixedHeight(36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(self._custom_btn_qss(background or "#242b36"))
        btn.clicked.connect(lambda _=False: callback())
        self.plugin_box.addWidget(btn)

    def add_session_button(self, key, label, icon=None, background=None):
        """插件注册新环境后，在“插件环境”区动态加一个会话按钮。"""
        if key in self.extra_session_buttons:
            return
        btn = QPushButton("  " + label)
        btn.setIcon(resolve_icon(icon, fallback="plug"))
        btn.setFixedHeight(36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(self._custom_btn_qss(background or "#20262f"))
        btn.clicked.connect(lambda _=False, k=key: self.newSession.emit(k))
        self.extra_box.addWidget(btn)
        self.extra_session_buttons[key] = btn
        self.extra_caption.show()

    def update_status_dots(self):
        for key, btn in self.session_buttons.items():
            info = DETECTION.get(key)
            meta = TOOL_META[key]
            if info is None:
                btn.setText("  " + meta["label"])
            elif info.get("found"):
                btn.setText("  " + meta["label"] + "  ✓")
            else:
                btn.setText("  " + meta["label"] + "  ✗")


# ====================================================================
#  插件系统：发现 / 加载
# ====================================================================
def ensure_plugins_dir():
    os.makedirs(PLUGINS_DIR, exist_ok=True)
    # 打包后首次运行：把随包示例插件复制到用户插件目录
    if getattr(sys, "frozen", False):
        for name in ("hello_demo.py", "env_demo.py"):
            bundled = resource_path(os.path.join("plugins", name))
            target = os.path.join(PLUGINS_DIR, name)
            try:
                if os.path.isfile(bundled) and not os.path.isfile(target):
                    shutil.copyfile(bundled, target)
            except Exception:
                pass


def scan_plugins():
    ensure_plugins_dir()
    out = []
    for path in sorted(glob.glob(os.path.join(PLUGINS_DIR, "*.py"))):
        file = os.path.basename(path)
        if file.startswith("_"):
            continue
        meta = {"file": file, "name": file[:-3], "version": "",
                "description": ""}
        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name) and t.id in (
                                "PLUGIN_NAME", "PLUGIN_VERSION",
                                "PLUGIN_DESCRIPTION") and isinstance(
                                node.value, ast.Constant):
                            k = t.id.replace("PLUGIN_", "").lower()
                            meta[k] = str(node.value.value)
        except Exception:
            meta["description"] = "（无法解析该插件）"
        out.append(meta)
    return out


class PluginHost:
    """传给插件 setup(app) 的宿主 API。"""

    def __init__(self, window):
        self.win = window
        self.config = CONFIG

    def add_sidebar_button(self, label, callback, icon=None, background=None):
        """在侧边栏添加一个按钮，点击时执行 callback。
        icon：内置图标名 / 图片路径 / emoji；background：颜色 / [c1,c2] 渐变。"""
        self.win.sidebar.add_plugin_button(
            label, callback, icon=icon, background=background)

    def register_environment(self, key, label, argv, icon=None,
                             background=None, cwd=None, home="", china="",
                             advice=""):
        """注册一个全新的终端环境/语言（例如 Ruby、Go、PHP、R 等）。
        注册后侧边栏“插件环境”区会出现按钮，点击即开新会话。
        argv：可执行文件路径 / 命令行列表 / 返回列表的函数。"""
        if key in TOOL_META:
            raise ValueError(f"{key} 是内置环境，不能重复注册")
        EXTRA_ENVIRONMENTS[key] = {
            "label": label, "argv": argv, "icon": icon,
            "background": background, "cwd": cwd,
            "home": home, "china": china, "advice": advice,
        }
        self.win.sidebar.add_session_button(
            key, label, icon=icon, background=background)

    def add_tutorial_chapter(self, title, html):
        """向新手教程追加一个章节（HTML 片段），重启后依然生效。"""
        import tutorial as _tut
        _tut.SECTIONS.append((title, html))
        tw = getattr(self.win, "tutorial_window", None)
        if tw is not None:
            tw.refresh()

    def new_session(self, profile_key):
        """新建终端会话：内置 cmd/ps/python/node/gitbash/wsl 或插件环境。"""
        self.win.new_session(profile_key)

    def run_command(self, command):
        """在当前终端执行一行命令。"""
        view = self.win.current_view()
        if view and not view.exited:
            view.send_line(command)
        else:
            self.show_message("当前没有可用的终端，请先新建一个会话。")

    def show_message(self, text, title="Fish away 插件"):
        QMessageBox.information(self.win, title, text)

    def toast(self, text):
        self.win.toast.show_text(text)

    def get_current_terminal(self):
        return self.win.current_view()


def load_enabled_plugins(window):
    host = PluginHost(window)
    plugins = {p["file"]: p for p in scan_plugins()}
    for file in list(CONFIG.get("plugins_enabled", [])):
        if file not in plugins:
            continue
        path = os.path.join(PLUGINS_DIR, file)
        mod_name = "fishaway_plugin_" + file[:-3]
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(mod_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            setup = getattr(module, "setup", None)
            if not callable(setup):
                host.toast(f"插件 {file} 没有 setup(app) 入口，已跳过")
                continue
            setup(host)
        except Exception as exc:
            host.toast(f"插件 {file} 加载出错：{exc}")


# ====================================================================
#  设置中心
# ====================================================================
class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("设置 · Fish away")
        self.setFixedSize(760, 580)
        self.setStyleSheet("""
            QDialog { background: #14161c; }
            QLabel { color:#d5dbe6; background:transparent; }
            QPushButton { background:#232833; color:#dfe4ec; border:none;
                          border-radius:7px; padding:7px 14px; }
            QPushButton:hover { background:#2e3542; }
            QLineEdit, QComboBox, QSpinBox {
                background:#1c1f27; color:#e5eaf1; border:1px solid #303642;
                border-radius:6px; padding:5px 8px;
            }
            QTabWidget::pane { border:1px solid #2a2f3a; border-radius:8px; }
            QTabBar::tab { background:transparent; color:#9aa3b2;
                           padding:8px 16px; }
            QTabBar::tab:selected { color:#67e8f9;
                                    border-bottom:2px solid #22d3ee; }
            QCheckBox { color:#d5dbe6; }
            QSlider::groove:horizontal { height:4px; background:#2a2f3a;
                                         border-radius:2px; }
            QSlider::handle:horizontal { background:#22d3ee; width:14px;
                                        margin:-6px 0; border-radius:7px; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 12)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._page_appearance(), "外观")
        self.tabs.addTab(self._page_sessions(), "会话路径 / 环境检测")
        self.tabs.addTab(self._page_mirror(), "镜像 / 下载加速")
        self.tabs.addTab(self._page_plugins(), "插件")
        lay.addWidget(self.tabs, 1)

        btn_row = QHBoxLayout()
        restart = QPushButton("重启 Fish away")
        restart.clicked.connect(self._restart)
        btn_row.addWidget(restart)
        btn_row.addStretch(1)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        save = QPushButton("保存")
        save.setDefault(True)
        save.setStyleSheet("background:#0891b2; color:white; padding:8px 26px;")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel); btn_row.addWidget(save)
        lay.addLayout(btn_row)

        self.path_edits = {}
        self.status_labels = {}
        self._populate_sessions()
        self._populate_plugins()

    # ---------- 外观 ----------
    def _page_appearance(self):
        w = QWidget(); form = QFormLayout(w)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(14)

        self.chk_acrylic = QCheckBox("启用亚克力（Acrylic）模糊效果")
        self.chk_acrylic.setChecked(CONFIG.get("acrylic", True))
        form.addRow(self.chk_acrylic)

        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setRange(60, 200)
        self.slider_alpha.setValue(int(CONFIG.get("acrylic_alpha", 110)))
        self.lbl_alpha = QLabel(f"亚克力浓度：{self.slider_alpha.value()}")
        self.slider_alpha.valueChanged.connect(
            lambda v: self.lbl_alpha.setText(f"亚克力浓度：{v}"))
        form.addRow(self.lbl_alpha, self.slider_alpha)

        self.combo_family = QComboBox()
        self.combo_family.addItem("自动（推荐）", "auto")
        from PySide6.QtGui import QFontDatabase
        for fam in QFontDatabase.families():
            if any(k in fam.lower() for k in
                   ("cascadia", "consolas", "courier", "mono", "jetbrains",
                    "fira code", "sarasa")):
                self.combo_family.addItem(fam, fam)
        cur = CONFIG.get("term_font_family", "auto")
        for i in range(self.combo_family.count()):
            if self.combo_family.itemData(i) == cur:
                self.combo_family.setCurrentIndex(i)
        form.addRow("终端字体", self.combo_family)

        self.spin_size = QSpinBox()
        self.spin_size.setRange(8, 20)
        self.spin_size.setValue(int(CONFIG.get("term_font_size", 11)))
        form.addRow("终端字号", self.spin_size)

        self.combo_cursor = QComboBox()
        self.combo_cursor.addItem("方块", "block")
        self.combo_cursor.addItem("竖线", "bar")
        self.combo_cursor.addItem("下划线", "underline")
        cur = CONFIG.get("cursor_style", "block")
        for i in range(self.combo_cursor.count()):
            if self.combo_cursor.itemData(i) == cur:
                self.combo_cursor.setCurrentIndex(i)
        form.addRow("光标样式", self.combo_cursor)

        self.spin_scroll = QSpinBox()
        self.spin_scroll.setRange(500, 50000)
        self.spin_scroll.setSingleStep(500)
        self.spin_scroll.setValue(int(CONFIG.get("scrollback", 5000)))
        form.addRow("历史回滚行数", self.spin_scroll)
        return w

    # ---------- 会话路径 ----------
    def _page_sessions(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        w = QWidget()
        self.sessions_form = QFormLayout(w)
        self.sessions_form.setContentsMargins(16, 16, 16, 16)
        self.sessions_form.setSpacing(10)
        scroll.setWidget(w)
        return scroll

    def _populate_sessions(self):
        for key in SESSION_ORDER:
            meta = TOOL_META[key]
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)

            status = QLabel("检测中…")
            status.setFixedWidth(88)
            edit = QLineEdit(CONFIG.get("paths", {}).get(key, ""))
            edit.setPlaceholderText("自动检测（也可手动填写或浏览）")
            browse = QPushButton("浏览…")
            auto = QPushButton("自动检测")

            def do_browse(_=False, e=edit):
                fp, _ = QFileDialog.getOpenFileName(
                    self, f"选择 {meta['label']} 的可执行文件",
                    "", "可执行文件 (*.exe);;所有文件 (*.*)")
                if fp:
                    e.setText(fp)

            def do_auto(_=False, k=key, e=edit, s=status):
                p = detect_tool(k)
                if p:
                    e.setText(p); s.setText("✓ 已找到")
                    s.setStyleSheet("color:#3ddc84;")
                else:
                    s.setText("✗ 未安装")
                    s.setStyleSheet("color:#f87171;")

            browse.clicked.connect(do_browse)
            auto.clicked.connect(do_auto)
            h.addWidget(status); h.addWidget(edit, 1)
            h.addWidget(browse); h.addWidget(auto)

            info = DETECTION.get(key)
            if info is not None:
                if info.get("found"):
                    status.setText("✓ 已安装")
                    status.setStyleSheet("color:#3ddc84;")
                    if not edit.text() and info.get("path"):
                        edit.setPlaceholderText("自动：" + info["path"])
                else:
                    status.setText("✗ 未安装")
                    status.setStyleSheet("color:#f87171;")
            cap = QLabel(meta["label"])
            cap.setStyleSheet("font-weight:700;")
            self.sessions_form.addRow(cap, row)
            self.path_edits[key] = edit
            self.status_labels[key] = status

        # WSL 发行版
        self.combo_distro = QComboBox()
        self.combo_distro.addItem("默认发行版", "")
        for d in WSL_DISTROS:
            self.combo_distro.addItem(d, d)
        cur = CONFIG.get("wsl_distro", "")
        for i in range(self.combo_distro.count()):
            if self.combo_distro.itemData(i) == cur:
                self.combo_distro.setCurrentIndex(i)
        self.sessions_form.addRow("WSL 发行版", self.combo_distro)

    # ---------- 镜像 ----------
    def _page_mirror(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 20, 20, 20)
        v.setSpacing(12)
        tip = QLabel("需要联网下载资源时（pip 安装包、安装工具等），"
                     "默认使用国内镜像，速度更快。\n"
                     "也可以随时按快捷键 Ctrl+Shift+Z 一键切换。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#9aa3b2;")
        v.addWidget(tip)

        self.chk_mirror_cn = QCheckBox("使用国内镜像（清华 TUNA pip 源）")
        self.chk_mirror_gl = QCheckBox("使用国外官方源（PyPI）")
        cur = CONFIG.get("mirror", "china")
        self.chk_mirror_cn.setChecked(cur == "china")
        self.chk_mirror_gl.setChecked(cur == "global")
        self.chk_mirror_cn.clicked.connect(
            lambda: self.chk_mirror_gl.setChecked(
                not self.chk_mirror_cn.isChecked()))
        self.chk_mirror_gl.clicked.connect(
            lambda: self.chk_mirror_cn.setChecked(
                not self.chk_mirror_gl.isChecked()))
        v.addWidget(self.chk_mirror_cn)
        v.addWidget(self.chk_mirror_gl)

        self.lbl_pip = QLabel()
        self.lbl_pip.setWordWrap(True)
        v.addWidget(self.lbl_pip)
        self.chk_mirror_cn.toggled.connect(self._update_pip_label)
        self._update_pip_label()

        row = QHBoxLayout()
        apply_pip = QPushButton("一键配置 pip 使用所选源")
        restore = QPushButton("恢复 pip 默认设置")

        def do_apply():
            url = (MIRRORS["china"]["pip"]
                   if self.chk_mirror_cn.isChecked()
                   else MIRRORS["global"]["pip"])
            ok, msg = self._pip_config(["global.index-url", url])
            QMessageBox.information(self, "pip 镜像", msg)

        def do_restore():
            ok, msg = self._pip_config(["global.index-url"], unset=True)
            QMessageBox.information(self, "pip 镜像", msg)

        apply_pip.clicked.connect(do_apply)
        restore.clicked.connect(do_restore)
        row.addWidget(apply_pip); row.addWidget(restore); row.addStretch(1)
        v.addLayout(row)
        v.addStretch(1)
        return w

    def _update_pip_label(self):
        cn = self.chk_mirror_cn.isChecked()
        url = MIRRORS["china"]["pip"] if cn else MIRRORS["global"]["pip"]
        self.lbl_pip.setText("当前 pip 源地址：" + url)

    @staticmethod
    def _pip_config(args, unset=False):
        py = detect_tool("python") or sys.executable
        cmd = [py, "-m", "pip", "config"]
        cmd += (["unset"] + args if unset else ["set"] + args)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                return True, "配置成功：\n" + (r.stdout or "已写入 pip 配置。")
            return False, "配置失败：\n" + (r.stderr or "未知错误")
        except Exception as exc:
            return False, f"执行出错：{exc}"

    # ---------- 插件 ----------
    def _page_plugins(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(10)
        tip = QLabel("插件为 .py 文件。把插件放入插件目录，在下方勾选启用，"
                     "重启 Fish away 后生效。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#9aa3b2;")
        v.addWidget(tip)

        row = QHBoxLayout()
        import_btn = QPushButton("导入插件（.py）…")
        folder_btn = QPushButton("打开插件目录")
        import_btn.clicked.connect(self._import_plugin)
        folder_btn.clicked.connect(
            lambda: (ensure_plugins_dir(),
                     os.startfile(PLUGINS_DIR)))
        row.addWidget(import_btn); row.addWidget(folder_btn)
        row.addStretch(1)
        v.addLayout(row)

        self.plugin_scroll = QScrollArea()
        self.plugin_scroll.setWidgetResizable(True)
        self.plugin_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.plugin_list_w = QWidget()
        self.plugin_list_lay = QVBoxLayout(self.plugin_list_w)
        self.plugin_list_lay.setContentsMargins(2, 6, 2, 6)
        self.plugin_list_lay.setSpacing(6)
        self.plugin_scroll.setWidget(self.plugin_list_w)
        v.addWidget(self.plugin_scroll, 1)
        return w

    def _populate_plugins(self):
        enabled = set(CONFIG.get("plugins_enabled", []))
        plugins = scan_plugins()
        self.plugin_checks = {}
        if not plugins:
            empty = QLabel("（插件目录中还没有插件，可先试试随包的示例插件）")
            empty.setStyleSheet("color:#6b7482;")
            self.plugin_list_lay.addWidget(empty)
        for p in plugins:
            chk = QCheckBox()
            chk.setChecked(p["file"] in enabled)
            ver = f" v{p['version']}" if p.get("version") else ""
            chk.setText(f"{p['name']}{ver}")
            desc = QLabel("    " + (p.get("description") or ""))
            desc.setWordWrap(True)
            desc.setStyleSheet("color:#8b95a5;")
            self.plugin_list_lay.addWidget(chk)
            self.plugin_list_lay.addWidget(desc)
            self.plugin_checks[p["file"]] = chk
        self.plugin_list_lay.addStretch(1)

    def _import_plugin(self):
        ensure_plugins_dir()
        fp, _ = QFileDialog.getOpenFileName(
            self, "选择插件文件", "", "Python 插件 (*.py)")
        if not fp:
            return
        target = os.path.join(PLUGINS_DIR, os.path.basename(fp))
        try:
            shutil.copyfile(fp, target)
            QMessageBox.information(
                self, "导入插件",
                f"已导入：{os.path.basename(fp)}\n"
                "在下方列表勾选启用，然后重启 Fish away。")
            self._rebuild_plugin_list()
        except Exception as exc:
            QMessageBox.warning(self, "导入失败", str(exc))

    def _rebuild_plugin_list(self):
        while self.plugin_list_lay.count():
            item = self.plugin_list_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._populate_plugins()

    def _restart(self):
        self._save(close=False)
        relaunch_app()
        self.accept()

    # ---------- 保存 ----------
    def _save(self, close=True):
        CONFIG["acrylic"] = self.chk_acrylic.isChecked()
        CONFIG["acrylic_alpha"] = int(self.slider_alpha.value())
        CONFIG["term_font_family"] = self.combo_family.currentData()
        CONFIG["term_font_size"] = int(self.spin_size.value())
        CONFIG["cursor_style"] = self.combo_cursor.currentData()
        CONFIG["scrollback"] = int(self.spin_scroll.value())
        CONFIG["wsl_distro"] = self.combo_distro.currentData() or ""
        CONFIG["mirror"] = ("china" if self.chk_mirror_cn.isChecked()
                            else "global")
        for key, edit in self.path_edits.items():
            CONFIG["paths"][key] = edit.text().strip()
        CONFIG["plugins_enabled"] = [
            f for f, chk in getattr(self, "plugin_checks", {}).items()
            if chk.isChecked()]
        save_config(CONFIG)

        # 实时生效
        win = self.parent()
        if isinstance(win, MainWindow):
            win.apply_settings_live()
        if close:
            self.accept()


# ====================================================================
#  关于
# ====================================================================
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"关于 {APP_NAME}")
        self.setFixedSize(440, 380)
        self.setStyleSheet("""
            QDialog { background: rgba(22,24,31,245); border-radius:12px; }
            QLabel { color:#dfe4ec; background:transparent; }
            QPushButton { background:#0a6dca; color:white; border:none;
                          border-radius:8px; padding:8px 22px; }
            QPushButton:hover { background:#1a82e0; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 18)
        row = QHBoxLayout()
        row.addWidget(FishLogo(64))
        col = QVBoxLayout()
        n = QLabel(f"<span style='font-size:16pt;font-weight:700;'>{APP_NAME}</span>"
                   f"<span style='color:#8b95a5;'>  v{APP_VERSION}</span>")
        mode = "管理员模式" if ADMIN else "普通用户模式"
        d = QLabel(f"对标 Windows Terminal 的图形化终端\n当前：{mode}")
        d.setStyleSheet("color:#9aa3b2;")
        col.addWidget(n); col.addWidget(d)
        row.addLayout(col)
        lay.addLayout(row)
        lay.addSpacing(10)
        info = QLabel(
            "· CMD、Windows PowerShell / PowerShell 7、Python、Node.js、"
            "Git Bash、WSL\n"
            "· ConPTY(pywinpty) 真实终端 · pyte 仿真 · PySide6/Qt\n"
            "· 设置中心、环境检测、国内镜像(Ctrl+Shift+Z)\n"
            "· 插件可注册新环境、自定义图标背景、扩充教程；多标签、历史回滚")
        info.setStyleSheet("color:#c6ccd8; font-size:10pt;")
        lay.addWidget(info)
        lay.addStretch(1)
        close = QPushButton("知道了")
        close.clicked.connect(self.accept)
        crow = QHBoxLayout(); crow.addStretch(1); crow.addWidget(close)
        lay.addLayout(crow)


# ====================================================================
#  重启 / 提权
# ====================================================================
def relaunch_app():
    import traceback
    pty_debug("RELAUNCH", "".join(traceback.format_stack()))
    if getattr(sys, "frozen", False):
        QProcess.startDetached(sys.executable, [])
    else:
        d = os.path.dirname(sys.executable)
        pyw = os.path.join(d, "pythonw.exe")
        exe = pyw if os.path.isfile(pyw) else sys.executable
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "fishaway.pyw")
        QProcess.startDetached(exe, [script])


def elevate_and_restart(parent):
    try:
        if getattr(sys, "frozen", False):
            target = sys.executable
            args = ""
        else:
            d = os.path.dirname(sys.executable)
            target = os.path.join(d, "pythonw.exe")
            if not os.path.isfile(target):
                target = sys.executable
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "fishaway.pyw")
            args = f'"{script}"'
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", target, args, None, 1)
        if rc <= 32:
            QMessageBox.warning(parent, "提权失败",
                                "无法以管理员身份启动（可能被取消）。")
            return
        QApplication.quit()
    except Exception as exc:
        QMessageBox.warning(parent, "提权失败", str(exc))


# ====================================================================
#  主窗口
# ====================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        icon_path = resource_path("icon.ico")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1180, 720)
        self.setMinimumSize(780, 500)
        self.translucent = dwm_composition_enabled()
        if self.translucent:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.counters = {k: 0 for k in SESSION_ORDER}
        self.tutorial_window = None

        central = QWidget()
        central.setStyleSheet(
            "background: transparent;" if self.translucent
            else "background:#14161c; border-radius:12px;")
        root = QHBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        self.sidebar = Sidebar()
        self.sidebar.newSession.connect(self.new_session)
        self.sidebar.openTutorial.connect(self.show_tutorial)
        self.sidebar.openAbout.connect(self.show_about)
        self.sidebar.openSettings.connect(self.show_settings)
        self.sidebar.clearScreen.connect(self.clear_screen)
        self.sidebar.elevate.connect(lambda: elevate_and_restart(self))
        root.addWidget(self.sidebar)

        right = QWidget()
        right.setStyleSheet("background: transparent;")
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
        rlay.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none; border-radius: 12px;
                background: rgba(24, 26, 33, 120); top: -1px;
            }
            QTabBar { background: transparent; qproperty-drawBase:0; }
            QTabBar::tab {
                background: rgba(255,255,255,14); color: #9aa3b2;
                padding: 7px 16px; margin: 2px 2px 0 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px; font-size: 10pt;
            }
            QTabBar::tab:selected { background: rgba(34,211,238,45);
                                    color: #eafcfe; }
            QTabBar::tab:hover:!selected { background: rgba(255,255,255,26); }
            QTabBar::close-button { image: none; }
        """)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(lambda _i: self.input.setFocus())
        self.tabs.currentChanged.connect(self._on_tab_changed)
        rlay.addWidget(self.tabs, 1)

        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame { background: rgba(13, 15, 21, 220);
                     border-radius: 10px; }
        """)
        ilay = QHBoxLayout(input_frame)
        ilay.setContentsMargins(12, 6, 12, 6)
        prompt = QLabel(">")
        prompt.setStyleSheet("color:#22d3ee; font-size:13pt; font-weight:700;"
                             "background:transparent;")
        ilay.addWidget(prompt)
        self.input = CommandInput()
        self.input.lineSubmitted.connect(self.submit_line)
        self.input.specialRequested.connect(self.submit_special)
        ilay.addWidget(self.input, 1)
        rlay.addWidget(input_frame)

        root.addWidget(right, 1)
        self.setCentralWidget(central)

        self.toast = Toast(self)

        # Ctrl+Shift+Z：一键切换镜像
        sc = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        sc.activated.connect(self.toggle_mirror)

        # 默认标签
        self.new_session(CONFIG.get("default_profile", "cmd"))

        # 后台环境检测
        BRIDGE.detected.connect(self._on_detected)

        def worker():
            BRIDGE.detected.emit(run_full_detection())

        threading.Thread(target=worker, daemon=True).start()

    # ---------------- 会话 ----------------
    def new_session(self, profile_key):
        argv, short = prepare_session(profile_key)
        self.counters[profile_key] = self.counters.get(profile_key, 0) + 1
        n = self.counters[profile_key]
        title = short if n == 1 else f"{short} {n}"
        bg, icon_spec = self._env_style(profile_key)
        if argv is None:
            view = TerminalView(None, short, profile_key,
                                notice=build_notice(profile_key),
                                background=bg)
        else:
            view = TerminalView(argv, short, profile_key, background=bg)
        view.exit_handler = lambda v=view, t=title: self._mark_exited(v, t)
        idx = self.tabs.addTab(view, title)
        if icon_spec:
            self.tabs.setTabIcon(idx, resolve_icon(icon_spec, fallback="plug"))
        self.tabs.setCurrentIndex(idx)
        if self.isVisible() and argv is not None:
            view.start()
            self.input.setFocus()
        # 新建标签后多次强制刷新，规避透明窗口下新视口不绘制的问题
        for delay in (60, 180, 450):
            QTimer.singleShot(delay, lambda v=view: self._refresh_view(v))

    @staticmethod
    def _refresh_view(v):
        try:
            v._render()
            v.viewport().update()
            if v._cursor_overlay is not None:
                v._cursor_overlay.update()
        except Exception:
            pass

    def _on_tab_changed(self, _idx):
        w = self.tabs.currentWidget()
        if isinstance(w, TerminalView):
            for delay in (0, 40, 160):
                QTimer.singleShot(delay, lambda v=w: self._refresh_view(v))

    @staticmethod
    def _env_style(profile_key):
        """返回 (背景规格, 图标规格)。"""
        if profile_key in EXTRA_ENVIRONMENTS:
            e = EXTRA_ENVIRONMENTS[profile_key]
            return e.get("background"), e.get("icon")
        if profile_key in TOOL_META:
            return None, TOOL_META[profile_key].get("icon")
        return None, None

    def _mark_exited(self, view, title):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            self.tabs.setTabText(idx, title + "（已退出）")

    def close_tab(self, idx):
        view = self.tabs.widget(idx)
        if isinstance(view, TerminalView):
            view.terminate()
        self.tabs.removeTab(idx)
        # 延迟销毁，等读取线程退出，避免原生对象竞态崩溃
        QTimer.singleShot(400, view.deleteLater)

    def current_view(self):
        view = self.tabs.currentWidget()
        return view if isinstance(view, TerminalView) else None

    def submit_line(self, text):
        view = self.current_view()
        if view:
            view.send_line(text)

    def submit_special(self, prefix, seq):
        view = self.current_view()
        if view:
            view.send_special(prefix, seq)
            view.setFocus()

    def clear_screen(self):
        view = self.current_view()
        if view:
            view.send_special("", "\x0c")

    # ---------------- 检测结果 ----------------
    def _on_detected(self, results):
        DETECTION.update(results)
        self.sidebar.update_status_dots()
        missing = [TOOL_META[k]["label"] for k, v in results.items()
                   if k in TOOL_META and not v.get("found")]
        if missing:
            self.toast.show_text(
                "环境检测：未检测到 " + "、".join(missing) +
                "，点击侧边栏对应项查看安装指引")

    # ---------------- 镜像 ----------------
    def toggle_mirror(self):
        new = "global" if CONFIG.get("mirror") == "china" else "china"
        CONFIG["mirror"] = new
        save_config(CONFIG)
        self.toast.show_text("已切换为：" + MIRRORS[new]["label"])

    # ---------------- 设置实时生效 ----------------
    def apply_settings_live(self):
        hwnd = int(self.winId())
        if CONFIG.get("acrylic", True):
            _set_acrylic(hwnd, 4, int(CONFIG.get("acrylic_alpha", 110)))
        else:
            _set_acrylic(hwnd, 4, 255)
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if isinstance(view, TerminalView):
                view.font_size = int(CONFIG.get("term_font_size", 11))
                view.apply_font()
                n = int(CONFIG.get("scrollback", 5000))
                if view.screen is not None:
                    view.screen.hist = deque(view.screen.hist, maxlen=n)
                view.viewport().update()

    # ---------------- 教程 / 关于 / 设置 ----------------
    def show_tutorial(self):
        if self.tutorial_window is None:
            self.tutorial_window = TutorialWindow(self)
        self.tutorial_window.show()
        self.tutorial_window.raise_()
        self.tutorial_window.activateWindow()

    def show_about(self):
        AboutDialog(self).exec()

    def show_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    # ---------------- show ----------------
    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        enable_acrylic(hwnd)
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if isinstance(view, TerminalView) and view.pty is None \
                    and view.argv is not None:
                # 等布局/几何稳定后再 spawn，避免尺寸抖动卡住 ConPTY
                QTimer.singleShot(150, view.start)
        QTimer.singleShot(0, self.input.setFocus)
        # 加载已启用插件
        QTimer.singleShot(300, lambda: load_enabled_plugins(self))


# ====================================================================
def install_crash_hooks():
    """全局异常钩子：任何未捕获异常都写入 error.log，主线程同时弹窗。
    这样程序不会再“悄无声息地闪退”，用户能拿到具体原因。"""
    log_path = os.path.join(APP_DIR, "error.log")

    def _write(exc_type, exc, tb):
        import traceback
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("==== " + time.strftime("%Y-%m-%d %H:%M:%S")
                        + "  v" + APP_VERSION + " ====\n")
                f.write("".join(traceback.format_exception(
                    exc_type, exc, tb)) + "\n")
        except Exception:
            pass

    def _gui_hook(exc_type, exc, tb):
        _write(exc_type, exc, tb)
        try:
            QMessageBox.critical(
                None, "Fish away 遇到问题",
                "程序出现一个未处理的错误，详细信息已写入：\n\n"
                + log_path + "\n\n可把该文件发给开发者，或查看新手教程"
                "第 19 章《卡顿、闪退与兼容性排查》。")
        except Exception:
            pass

    def _thread_hook(args):
        _write(args.exc_type, args.exc_value, args.exc_traceback)

    sys.excepthook = _gui_hook
    threading.excepthook = _thread_hook


def run_selftest():
    """打包后确定性自检：逐个打开内置会话并执行标记命令，
    结果写入 APP_DIR/selftest_report.txt。用法：Fish away.exe --selftest"""
    report = []

    def log(s):
        report.append(s)

    log("Fish away self-test  v" + APP_VERSION + "  "
        + time.strftime("%Y-%m-%d %H:%M:%S"))
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ensure_plugins_dir()
    DETECTION.update(run_full_detection())
    win = MainWindow()
    win.show()

    def view_text(view):
        lines = []
        hist = list(view.screen.hist)
        grids = [[view.screen.buffer[y][x]
                  for x in range(view.screen.columns)]
                 for y in range(view.screen.lines)]
        for line in hist + grids:
            lines.append("".join(c.data for c in line))
        return "\n".join(lines)

    def pump(sec):
        end = time.time() + sec
        while time.time() < end:
            app.processEvents()
            time.sleep(0.02)

    pump(1.0)
    markers = {"cmd": "SELFTEST-CMD", "ps": "SELFTEST-PS",
               "python": "SELFTEST-PY", "node": "SELFTEST-NODE"}
    commands = {"cmd": "echo {m}", "ps": "echo {m}",
                "python": "print('{m}')", "node": "console.log('{m}')"}
    results = {}
    for env, marker in markers.items():
        det = DETECTION.get(env)
        if not (det and det.get("found")):
            results[env] = "SKIP(not installed)"
            log(f"[{env}] SKIP (not installed)")
            continue
        try:
            win.new_session(env)
            view = win.current_view()
            pump(2.5)
            view.send_line(commands[env].format(m=marker))
            pump(2.0)
            text = view_text(view)
            ok = marker in text
            results[env] = "PASS" if ok else "FAIL"
            log(f"[{env}] {'PASS' if ok else 'FAIL'}  "
                f"alive={view.pty.isalive() if view.pty else None}")
            if not ok:
                snippet = [l for l in text.split("\n") if l.strip()][-4:]
                for l in snippet:
                    log("    > " + l[:80])
        except Exception as exc:
            results[env] = "ERROR"
            log(f"[{env}] ERROR {exc!r}")

    # 起始目录检查
    win.new_session("cmd")
    pump(2.5)
    cmd_text = view_text(win.current_view())
    home_ok = HOME_DIR in cmd_text
    log(f"[cwd cmd normal] {'PASS' if home_ok else 'FAIL'} "
        f"home={HOME_DIR}")

    # 插件自检：env_demo
    try:
        CONFIG["plugins_enabled"] = ["env_demo.py"]
        load_enabled_plugins(win)
        pump(0.8)
        has_btn = "demo_deepsea" in win.sidebar.extra_session_buttons
        log(f"[plugin env_demo register] {'PASS' if has_btn else 'FAIL'}")
        if has_btn:
            win.new_session("demo_deepsea")
            view = win.current_view()
            pump(2.5)
            view.send_line("echo SELFTEST-PLUGIN")
            pump(2.0)
            ok = "SELFTEST-PLUGIN" in view_text(view)
            log(f"[plugin env run] {'PASS' if ok else 'FAIL'}")
    except Exception as exc:
        log(f"[plugin] ERROR {exc!r}")

    out = os.path.join(APP_DIR, "selftest_report.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    log("report written: " + out)
    return results


def main():
    install_crash_hooks()
    if "--selftest" in sys.argv:
        run_selftest()
        sys.exit(0)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "fishaway.terminal.2")
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setFont(ui_font())
    icon_path = resource_path("icon.ico")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    ensure_plugins_dir()
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
