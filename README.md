# Fish away 🐟 —— GUI 终端（v3）

对标 **Windows Terminal** 的 Windows 桌面终端：内置 **命令提示符（CMD）**、
**Windows PowerShell / PowerShell 7**、**Python**、**Node.js**、**Git Bash**、
**WSL（Linux 子系统）** 六种环境，并可通过**插件注册任意新环境/语言**；
多标签、真实终端仿真、设置中心、管理员模式、环境检测、国内镜像加速、
真实可用的 .py 插件端口，并内置一份 **20 章**超级新手教程。

## 界面布局

```
┌────────────┬──────────────────────────────────────────┐
│            │  [CMD] [PowerShell] ...      ← 标签页      │
│  🐟 Fish   │ ┌──────────────────────────────────────┐ │
│  away      │ │                                      │ │
│ [模式徽章]  │ │      中 间 大 面 板（终端输出）       │ │
│            │ │                                      │ │
│  新建会话   │ │   支持颜色 / Tab补全 / 全屏程序        │ │
│  · CMD     │ │                                      │ │
│  · PowerShell│ └──────────────────────────────────────┘ │
│  · Python  │ ┌──────────────────────────────────────┐ │
│  · Node.js │ │ >  底部输入框：输入命令，回车运行      │ │
│  · Git Bash│ └──────────────────────────────────────┘ │
│  · WSL     │                                          │
│  插件环境   │                                          │
│  插件区     │                                          │
│  设置/教程  │                                          │
└────────────┴──────────────────────────────────────────┘
```

## 快速开始

### 方式一：直接用 exe（推荐，免装 Python）

双击 **`Fish away.exe`** 即可，无需任何依赖。
- 直接双击打开 = **普通用户模式**；
- 右键「以管理员身份运行」= **管理员模式**（侧边栏徽章会显示当前模式，
  普通模式下点徽章也可一键提权重启）。

> 若双击 exe 没反应或闪退，多半是杀毒软件把单文件 exe 隔离了：到杀软
> 「保护历史记录/隔离区」还原 Fish away 并加入排除项，或改用下面的 bat
> 启动。详见内置教程第 18 章。

### 方式二：启动脚本

双击 **`启动 Fish away.bat`**，首次运行会自动安装依赖并启动。

### 方式三：源码手动启动

```powershell
# 需要 Python 3.9+（开发环境为 3.14）
pip install -r requirements.txt
pythonw fishaway.pyw      # 或 python fishaway.pyw
```

## v3 功能特性

### 六种内置终端环境
- **真实终端**：基于 `pywinpty`（ConPTY）+ `pyte` 仿真，不是简单的 subprocess
  管道——支持 ANSI 颜色、光标控制、Tab 补全、交互式程序（python REPL、vim 等）
- CMD、PowerShell（自动识别 pwsh 7）、Python、**Node.js**、**Git Bash**、
  **WSL**（可选择已安装的发行版）一键新建

### 起始目录（v3 修复）
- **CMD**：普通用户起始于用户目录（`C:\Users\你的名字`），管理员起始于
  `C:\Windows\System32`
- **PowerShell / Python / Node.js**：两种权限下都起始于用户目录

### 管理员模式
- 实时检测自身权限：普通双击显示「普通用户模式」徽章，管理员运行显示
  「管理员模式」橙色徽章
- 点徽章即可通过 UAC 提权并自动重启；「关于」中也显示当前模式

### 环境实时检测
- 启动后自动检测六种环境是否安装，侧边栏按钮追加 ✓ / ✗
- 缺失时点击该会话，会打开彩色安装指引（官方地址 + 国内镜像地址、手动设置
  路径说明），并弹出汇总提示
- 可在「设置 → 会话路径」里**手动浏览选择 exe**，或点「自动检测」重新扫描；
  WSL 可选择发行版

### 设置中心（侧边栏「设置」）
- **外观**：模糊效果开关、浓度、终端字体（等宽字体列表）、字号、光标样式
  （方块 / 竖线 / 下划线）、历史回滚行数；多数项保存后即时生效
- **会话路径**：六个工具的路径状态、浏览、自动检测
- **镜像**：国内 / 国外源选择，一键配置 pip、恢复 pip 默认
- **插件**：导入 .py、打开插件目录、启用 / 禁用列表
- 底部可直接「重启 Fish away」

### 国内镜像加速
- 默认走国内镜像；按 **Ctrl + Shift + Z** 一键在「国内 / 国外」之间切换，
  设置自动保存
- pip 默认源：清华 TUNA；npm 源：npmmirror；安装指引中 Git for Windows、
  Python、Node.js 均给出华为云镜像
- 设置中可一键执行 pip 配置 / 恢复

### 真实插件端口（.py，v3 大升级）
- 插件就是普通 `.py` 文件，启动时调用其 `setup(app)`，拿到宿主 API：
  - `add_sidebar_button(文字, 函数, icon=, background=)` —— 自定义按钮
  - **`register_environment(key, 标签, argv, icon=, background=, cwd=, …)`**
    —— 注册任意新环境/语言（Ruby、Go、PHP、R、Lua、JShell…），侧边栏
    「插件环境」区动态出现会话按钮
  - **`add_tutorial_chapter(标题, html)`** —— 向新手教程追加章节
  - `run_command`、`new_session`、`show_message`、`toast`、
    `get_current_terminal`、`config`
- **自定义图标**：内置图标名（cmd/ps/py/node/git/wsl/gear…）/ 图片文件
  （.png/.jpg/.ico）/ emoji 或短文字，自动绘制
- **自定义背景**：纯色 / 双色渐变 / 图片，按钮与终端会话均支持
- 使用流程：**导入插件（或放进插件目录）→ 插件列表勾选启用 → 重启软件生效**
- 单个插件出错只弹提示，不会拖垮软件
- 随包示例：`plugins/hello_demo.py`（按钮/命令）、`plugins/env_demo.py`
  （注册环境、自定义图标背景、注入教程）

### v3 性能与稳定性
- 渲染合并到约 30fps + 120ms 安全对账；历史行 runs 缓存；输出仅追加时
  走快速路径；光标选区按位置去重
- 全局异常钩子：崩溃写入 `error.log` 并弹窗，不再静默闪退
- DWM 合成检测：兼容模式/远程桌面关闭合成时自动放弃透明，避免黑屏闪退
- 关闭标签延迟销毁，规避线程/原生对象竞态

### 其他
- 多标签可拖动、可关闭；两种输入方式（底部输入框 / 点终端面板直连键盘）
- 历史回滚（默认约 5000 行）；`Ctrl + 滚轮` 字体缩放，`Ctrl + 0` 恢复
- 内置 **20 章超级教程**：CMD、PowerShell、Python、Node.js/插件注册环境、
  Git Bash、WSL、镜像加速、插件开发、FAQ、卡顿闪退排查、速查表

## 快捷键

| 快捷键 | 作用 |
|---|---|
| Enter | 运行输入框中的命令 |
| Tab | 自动补全（焦点在终端面板时） |
| ↑ / ↓ | 命令历史 |
| Ctrl + C | 中断当前命令 |
| Ctrl + L | 清屏 |
| Ctrl + Shift + Z | 一键切换国内 / 国外镜像 |
| Ctrl + 滚轮 | 终端字体缩放 |
| Ctrl + 0 | 恢复默认字号 |

## 配置与插件文件位置

| 运行方式 | 配置 / 插件目录 |
|---|---|
| exe（Fish away.exe） | `%APPDATA%\FishAway\`（config.json、error.log、plugins\） |
| 源码 / bat | 程序所在文件夹（config.json、error.log、plugins\） |

exe 首次运行会自动创建上述目录并播种示例插件 `hello_demo.py`。

## 文件说明

| 文件 | 说明 |
|---|---|
| `Fish away.exe` | 打包好的单文件可执行程序（图标、依赖全部内置） |
| `fishaway.pyw` | 主程序源码 |
| `tutorial.py` | 内置 20 章新手教程 |
| `plugins/hello_demo.py` | 示例插件：按钮与命令 |
| `plugins/env_demo.py` | 示例插件：注册环境/图标背景/注入教程 |
| `icon.ico` / `icon.png` | 应用图标 |
| `启动 Fish away.bat` | 源码模式一键启动器（自动装依赖） |
| `requirements.txt` | 源码依赖清单 |
| `test_smoke.py` / `test_v3.py` | 冒烟 / v3 集成测试脚本 |
| `shot_*.png` | 功能实测截图 |

## 常见问题

- **双击 exe 闪退/没反应**：多为杀软隔离，还原并加排除项，或用 bat 启动；
  查看 `%APPDATA%\FishAway\error.log`。
- **开兼容模式闪退**：取消 exe 属性里的兼容模式勾选；v3 已自动处理
  DWM 合成关闭的情况。
- **“不是内部或外部命令”**：拼写 / PATH 问题，见内置教程 FAQ。
- **PowerShell 禁止运行脚本**：执行
  `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`。
- **Git Bash 检测不到**：确认已装 Git for Windows；或在设置里手动选择
  Git 目录下的 `bin\bash.exe`。
- **WSL 提示没有发行版**：管理员 PowerShell 运行 `wsl --install -d Ubuntu`，
  重启后按提示初始化。
- **中文乱码**：CMD 里先执行 `chcp 65001`；脚本保存为 UTF-8。
- **插件不生效**：确认已在设置中勾选启用，并且**重启了软件**。

## 技术栈

Python · PySide6 (Qt 6) · pywinpty (ConPTY) · pyte · PyInstaller ·
Windows DWM API
