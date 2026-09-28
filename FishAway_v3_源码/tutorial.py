# -*- coding: utf-8 -*-
"""
Fish away 内置教程 —— 终端超级新手教程（20 章）
TutorialWindow：左侧目录 + 右侧 QTextBrowser 富文本文档
插件可通过 app.add_tutorial_chapter() 动态追加章节。
"""
import html as _html
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QListWidget, QListWidgetItem,
                               QTextBrowser, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QLabel, QWidget)


# --------------------------------------------------------------------
#  小工具：代码块 / 行内代码 / 提示框
# --------------------------------------------------------------------
def pre(code):
    return f'<pre>{_html.escape(code)}</pre>'


def code(text):
    return f'<code>{_html.escape(text)}</code>'


def tip(text):
    return (f'<div style="background:#0d2b33; border-left:3px solid #22d3ee; '
            f'padding:8px 10px; border-radius:6px; margin:8px 0;">'
            f'<b style="color:#67e8f9;">小技巧：</b>{text}</div>')


def warn(text):
    return (f'<div style="background:#33220d; border-left:3px solid #f5b942; '
            f'padding:8px 10px; border-radius:6px; margin:8px 0;">'
            f'<b style="color:#f5b942;">注意：</b>{text}</div>')


def h2(t):
    return f'<h2>{t}</h2>'


def h3(t):
    return f'<h3>{t}</h3>'


def para(t):
    return f'<p>{t}</p>'


def bullets(items):
    return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'


def nums(items):
    return '<ol>' + ''.join(f'<li>{i}</li>' for i in items) + '</ol>'


def table(headers, rows):
    out = ('<table cellspacing="0" cellpadding="6">'
           '<tr>' + ''.join(f'<th bgcolor="#1b2733">{h}</th>'
                            for h in headers) + '</tr>')
    for r in rows:
        out += '<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>'
    out += '</table><p></p>'
    return out


CSS = """
<style>
body { color:#d7dce5; font-size:10.5pt; }
h2 { color:#67e8f9; font-size:15pt; margin-top:16px; }
h3 { color:#9adfe9; font-size:12pt; margin-top:14px; }
pre { background:#12151c; border:1px solid #262c38; border-radius:8px;
      padding:10px; color:#d7dce5; font-size:9.5pt; }
code { color:#7dd3fc; background:#1a212c; padding:1px 5px;
       border-radius:4px; font-size:9.5pt; }
pre code { background:transparent; color:inherit; padding:0; }
table { border-collapse:collapse; font-size:9.5pt; }
th { color:#bfeaf2; border:1px solid #2c3442; }
td { border:1px solid #2c3442; }
ul,ol { margin-left:6px; }
p { line-height:1.5; }
</style>
"""

# ====================================================================
#  章节内容
# ====================================================================
SECTIONS = []

# ---------------------------------------------------------------- 1
SECTIONS.append(("0. 欢迎与界面导览",
    h2("欢迎使用 Fish away")
    + para("Fish away 是一个对标 <b>Windows Terminal</b> 的图形化终端软件："
           "它把 <b>命令提示符（CMD）</b>、<b>PowerShell</b>、<b>Python</b>、"
           "<b>Node.js</b>、<b>Git Bash</b> 和 <b>WSL（Linux 子系统）</b> 等环境"
           "装进了一个简洁的现代深色界面里，还能通过插件加入更多语言环境。")
    + h3("界面布局")
    + bullets([
        "<b>左侧侧边栏</b>：点击六种内置环境即可新建会话标签；插件注册的"
        "环境会出现在「插件环境」区；顶部徽章显示「普通用户模式 / 管理员"
        "模式」；底部有「设置」「新手教程」「清屏」「关于」。",
        "<b>中间大面板</b>：显示命令的全部输出，这是一块<b>真正的终端</b>"
        "（基于 ConPTY + pyte 仿真），支持颜色、Tab 补全、全屏程序。",
        "<b>底部输入框</b>：在框里输入命令，按 <b>Enter</b> 就会运行。",
        "<b>顶部标签页</b>：可以同时开多个终端，标签可拖动排序、点 × 关闭。",
    ])
    + h3("两种输入方式（都可以，挑你顺手的）")
    + bullets([
        "<b>方式一（新手推荐）</b>：直接在底部输入框敲命令 → Enter。",
        "<b>方式二（进阶）</b>：用鼠标点一下中间的终端面板，让它获得焦点，"
        "之后所有按键都直接送给终端——此时 <b>Tab 补全、↑↓历史、Ctrl+C、"
        "vim 全屏操作</b>体验最完整。",
    ])
    + tip("在底部输入框里按 <b>Tab / ↑ / ↓</b>，输入框会自动把已输入内容"
          "提交给终端并把焦点转到上方面板，接着就能正常补全/翻历史。")
    + h3("实用操作速览")
    + table(["操作", "怎么做"], [
        ["新建终端", "点侧边栏的 CMD / PowerShell / Python"],
        ["运行命令", "输入命令后按 Enter"],
        ["清屏", "侧边栏「清屏」，或终端里按 Ctrl+L / 输入 cls"],
        ["中断当前命令", "终端面板里按 Ctrl+C（输入框里也是 Ctrl+C）"],
        ["字体放大/缩小", "按住 Ctrl 滚动鼠标滚轮；Ctrl+0 恢复"],
        ["关闭终端", "标签页上的 ×（会结束该终端进程）"],
    ])
    + h3("CMD、PowerShell、Python、Node.js 一句话区别")
    + bullets([
        "<b>CMD</b>：最老牌的命令解释器，命令短、历史久，简单直接。",
        "<b>PowerShell</b>：新一代 Shell，命令是“动词-名词”形式，"
        "管道里传的是<b>对象</b>，功能强大，还能兼容大部分 CMD 命令。",
        "<b>Python</b>：编程语言的交互环境（REPL），提示符是 "
        + code(">>>") + "，用来跑 Python 代码而不是系统命令。",
        "<b>Node.js</b>：JavaScript 的运行时，交互环境提示符以 "
        + code(">") + " 开头，用来跑 JavaScript。",
    ])
))

# ---------------------------------------------------------------- 2
SECTIONS.append(("1. 3 分钟跑通第一条命令",
    h2("零基础：3 分钟跑通第一条命令")
    + h3("第 1 步：看懂提示符")
    + para("打开 CMD 后，你会看到类似这样的一行，这叫<b>提示符</b>：")
    + pre("C:\\Users\\lenovo>")
    + bullets([
        code("C:\\Users\\lenovo") + " 表示<b>当前所在目录</b>（你的用户文件夹）。",
        "结尾的 " + code(">") + " 表示“计算机已准备好，等你输入命令”。",
        "PowerShell 的提示符长这样：" + code("PS C:\\Users\\lenovo>") + "。",
    ])
    + h3("第 2 步：输入第一条命令")
    + para("在输入框里输入 " + code("ver") + " 然后按 Enter，CMD 会告诉你 Windows 版本：")
    + pre("C:\\Users\\lenovo>ver\n\nMicrosoft Windows [版本 10.0.26100.9278]")
    + para("再试试这些（一次一条，敲完按 Enter）：")
    + table(["命令", "作用"], [
        ["ver", "查看 Windows 版本"],
        ["hostname", "查看电脑名"],
        ["echo 你好", "原样输出“你好”"],
        ["date /t", "查看今天日期"],
        ["time /t", "查看当前时间"],
        ["cls", "清空整个屏幕"],
    ])
    + h3("第 3 步：体验三个最常用的“保命”操作")
    + bullets([
        "<b>Tab 自动补全</b>：输入前几个字母后按 Tab，系统会自动补全"
        "文件名/命令名，多按几次循环切换。",
        "<b>↑ / ↓ 方向键</b>：翻出你之前输入过的命令，不用重新敲。",
        "<b>Ctrl + C</b>：命令停不下来时（比如一直 ping），按 Ctrl+C 立刻中断。",
    ])
    + para("来练习一下 Ctrl+C：输入下面命令并回车，它会一直 ping 下去，"
           "然后点一下终端面板按 Ctrl+C：")
    + pre("ping -t 8.8.8.8\n\n正在 Ping 8.8.8.8 具有 32 字节的数据:\n来自 8.8.8.8 的回复: 字节=32 时间=32ms TTL=117\n...\nCtrl+C\nC:\\Users\\lenovo>")
    + tip("命令不区分大小写：" + code("VER") + "、" + code("ver")
          + "、" + code("Ver") + " 效果一样（PowerShell 里也一样）。")
    + warn("如果输入命令后提示“不是内部或外部命令”，先别慌——这通常只是"
           "拼写错了或多了空格，请看最后的 FAQ 章节。")
))

# ---------------------------------------------------------------- 3
SECTIONS.append(("2. CMD① 目录与路径",
    h2("CMD 教程①：目录（文件夹）与路径")
    + h3("打开 CMD 的几种方式")
    + bullets([
        "按 " + code("Win + R") + "，输入 " + code("cmd") + " 回车。",
        "在任意文件夹的地址栏里输入 " + code("cmd") + " 回车，会直接定位到该文件夹。",
        "在文件夹里按住 Shift 点右键 →「在此处打开命令行窗口」。",
        "当然，直接在 Fish away 侧边栏点「命令提示符 CMD」。",
    ])
    + h3("dir —— 列出目录内容")
    + pre("dir            :: 列出当前目录所有文件和文件夹\ndir /p         :: 内容太多时分页显示（按任意键翻页）\ndir /w         :: 宽屏列表，只显示名字\ndir /a         :: 连隐藏文件、系统文件一起显示\ndir /s         :: 递归列出所有子文件夹里的内容\ndir /o:n       :: 按名称排序（/o:-d 按日期倒序）\ndir *.txt      :: 只列出 .txt 文件（通配符 *）")
    + h3("cd —— 切换目录")
    + pre("cd Desktop          :: 进入当前目录下的 Desktop 子文件夹\ncd ..               :: 回到上一级文件夹\ncd \\                :: 回到当前盘的根目录\ncd /d D:\\Movies      :: 跨盘切换（关键：加 /d）\nD:                  :: 只切换当前盘符到 D 盘")
    + warn("CMD 里直接 " + code("cd D:\\xxx") + " 默认不会切换盘符！"
           "同盘切换用 " + code("cd 文件夹") + "，跨盘要么先输 " + code("D:")
           + "，要么用 " + code("cd /d D:\\xxx") + "。")
    + h3("创建和删除文件夹")
    + pre("mkdir 项目          :: 新建文件夹（可简写 md）\nmd a\\b\\c           :: 一次性建多层文件夹\nrmdir 项目          :: 删除空文件夹（可简写 rd）\nrd /s /q 项目       :: 连同里面所有文件一起删除，不询问")
    + warn("/q 是“安静模式”，删了不会再问你确认，新手用 " + code("rd /s 文件夹")
           + "（不带 /q）更安全。删除操作不进回收站，务必看清楚路径！")
    + h3("路径：绝对路径 vs 相对路径")
    + bullets([
        "<b>绝对路径</b>：从盘符开始写全，如 "
        + code("C:\\Users\\lenovo\\Desktop\\note.txt") + "。",
        "<b>相对路径</b>：相对当前目录，"
        + code(".") + " 表示当前目录，"
        + code("..") + " 表示上一级目录。",
        "路径里有空格时一定要加英文双引号："
        + code('cd "C:\\Program Files"') + "。",
    ])
    + h3("其他好用的目录命令")
    + pre("tree            :: 以树形图展示目录结构\ntree /f         :: 连文件名一起显示\npushd D:\\work   :: 切换目录并记住当前位置\npopd            :: 回到 pushd 记住的位置")
))

# ---------------------------------------------------------------- 4
SECTIONS.append(("3. CMD② 文件操作",
    h2("CMD 教程②：文件操作")
    + h3("查看文件")
    + pre("type note.txt       :: 在屏幕上显示文本文件内容\nmore note.txt       :: 内容太长时分页看（空格翻页，q 退出）")
    + h3("新建文件（用 echo + 重定向）")
    + pre("echo hello > a.txt      :: 创建 a.txt，内容为 hello\necho world >> a.txt     :: 把 world 追加到 a.txt 末尾")
    + h3("复制 / 移动")
    + pre("copy a.txt b.txt        :: 复制一份\ncopy a.txt D:\\bak\\      :: 复制到别的文件夹\ncopy /b 1.jpg+2.jpg out.jpg :: 合并文件\nxcopy src D:\\dst /e /h /y /i :: 复制整个文件夹（含子目录和隐藏文件）\nrobocopy src D:\\dst /e      :: 更强大的“可靠复制”（Win 自带）\nmove a.txt D:\\bak\\         :: 移动文件（也可用来改名）")
    + bullets([
        code("/e") + " = 连空的子文件夹一起复制；"
        + code("/h") + " = 含隐藏/系统文件；"
        + code("/y") + " = 覆盖不询问；"
        + code("/i") + " = 目标不存在时当作文件夹创建。",
    ])
    + h3("删除 / 重命名")
    + pre("del a.txt             :: 删除文件\ndel /p a.txt          :: 删除前先询问确认\ndel /s /q *.tmp       :: 递归删除所有 .tmp 临时文件\nren old.txt new.txt   :: 重命名（也写 rename）")
    + warn("del 和 rd 删除的东西<b>不进回收站</b>，配合通配符时尤其要看清楚，"
           "比如 " + code("del *.*") + " 会删掉当前目录所有文件！")
    + h3("通配符：* 和 ?")
    + bullets([
        code("*") + " 代表任意个任意字符：" + code("dir *.png")
        + " 列出所有 png 图片。",
        code("?") + " 代表单个字符：" + code("dir photo?.jpg")
        + " 匹配 photo1.jpg、photoA.jpg。",
    ])
    + h3("文件属性 attrib")
    + pre("attrib +h secret.txt   :: 设为“隐藏”\nattrib -h secret.txt   :: 取消隐藏\nattrib +r a.txt        :: 设为只读\nattrib -r a.txt        :: 取消只读")
    + h3("其他实用命令")
    + pre("where python           :: 查找某程序装在哪里\nfc a.txt b.txt         :: 比较两个文件的差异\nassoc .txt             :: 查看 .txt 关联到什么类型")
))

# ---------------------------------------------------------------- 5
SECTIONS.append(("4. CMD③ 系统、网络与任务",
    h2("CMD 教程③：系统、网络与进程")
    + h3("系统信息")
    + pre("ver                :: Windows 版本\nsysteminfo         :: 完整系统信息（补丁、内存、开机时间）\nhostname           :: 计算机名\nwhoami             :: 当前登录的用户名\nset                :: 查看所有环境变量\necho %PATH%        :: 查看 PATH 环境变量")
    + h3("网络排查（最常用）")
    + pre("ipconfig /all      :: 查看本机所有网卡 IP / MAC / DNS\nping 8.8.8.8       :: 测试网络通不通（-t 持续，-n 10 发10次）\ntracert baidu.com  :: 查看到目标经过哪些路由（排查网络断点）\npathping baidu.com  :: ping + tracert 二合一\nnetstat -ano       :: 查看所有网络连接和端口占用\nnetstat -ano | findstr :8080   :: 查 8080 端口被谁占用\nnslookup baidu.com :: 查看域名解析出的 IP\ngetmac             :: 查看网卡 MAC 地址\narp -a             :: 查看局域网 IP-MAC 对应表")
    + h3("进程管理")
    + pre("tasklist                  :: 列出所有正在运行的进程\ntasklist | findstr chrome :: 找 chrome 相关进程\ntaskkill /PID 1234 /F     :: 按进程号强制结束\ntaskkill /IM notepad.exe /F:: 按程序名结束所有同名进程")
    + h3("关机 / 重启")
    + pre("shutdown /s /t 60     :: 60 秒后关机\nshutdown /r /t 0      :: 立即重启\nshutdown /a           :: 取消刚才设定的关机/重启\nshutdown /l           :: 注销当前用户")
    + h3("需要管理员权限的命令")
    + pre("sfc /scannow         :: 扫描修复系统文件\nchkdsk C: /f          :: 检查并修复磁盘错误（通常重启后执行）")
    + warn("以管理员身份打开：按 Win + X →「终端(管理员)」；管理员窗口的"
           "提示符通常会显示 “管理员” 字样。系统级命令不要在不了解时乱执行。")
))

# ---------------------------------------------------------------- 6
SECTIONS.append(("5. CMD④ 管道重定向与批处理",
    h2("CMD 教程④：管道、重定向与 .bat 批处理脚本")
    + h3("重定向：把输出存进文件")
    + pre("dir > list.txt      :: 把 dir 的输出写入 list.txt（覆盖）\ndir >> list.txt     :: 追加到文件末尾\ntype nul > a.txt    :: 清空/创建空文件\nprogram 2> err.log  :: 只把错误信息存起来\nprogram > all.txt 2>&1 :: 正常输出和错误都存进文件\ndata < input.txt    :: 让程序从文件读取输入")
    + h3("管道 | ：把上一个命令的输出交给下一个命令")
    + pre('dir | more             :: 输出分页查看\ndir | find "txt"        :: 只保留含 txt 的行\nfindstr /s /i "error" *.log :: 在所有 log 里搜 error\ntasklist | findstr java :: 找 java 进程\nsort < names.txt        :: 给文本排序\nipconfig | clip         :: 结果直接复制到剪贴板')
    + h3("命令连接符")
    + bullets([
        code("&&") + "：前一个成功了才执行后一个："
        + code("mkdir test && cd test"),
        code("||") + "：前一个失败了才执行后一个："
        + code("dir || echo 没找到"),
        code("&") + "：不管成败，依次都执行：" + code("a & b"),
        code("^") + "：行尾写 ^ 表示“命令太长，下一行继续”。",
    ])
    + h3("环境变量（系统给你准备好的快捷值）")
    + pre("echo %USERPROFILE%   :: 用户文件夹，如 C:\\Users\\lenovo\necho %TEMP%          :: 临时文件夹\necho %CD%            :: 当前目录\necho %RANDOM%        :: 随机数\nset /a x=1+2         :: 计算器，结果存进 x\nset /p name=你叫什么: :: 让用户输入内容")
    + h3("批处理脚本 .bat 入门")
    + para("批处理就是“把一堆 CMD 命令存进一个文件，一次跑完”。完整流程：")
    + nums([
        "新建文本文件，把下面代码粘进去；",
        "保存时文件名取 " + code("hello.bat") + "（注意后缀是 .bat）；",
        "在 Fish away 里输入 " + code("hello.bat") + " 回车运行。",
    ])
    + pre("""@echo off
rem  这是注释，不会显示（也可以用 ::）
echo 你好，欢迎使用 Fish away
set /p name=请输入你的名字:
echo 很高兴认识你，%name%！
echo 当前时间是 %TIME%
pause""")
    + bullets([
        code("@echo off") + "：关闭“把每条命令回显出来”，让输出干净。",
        code("rem") + " 或 " + code("::") + "：注释。",
        code("pause") + "：显示“请按任意键继续…”，防止窗口一闪而过。",
        code("%name%") + "：取变量的值。",
    ])
    + h3("批处理里的判断和循环（了解即可）")
    + pre("""if exist a.txt (
    echo 文件存在
) else (
    echo 文件不存在
)

if %errorlevel%==0 echo 上一条命令成功了

:: 循环删除当前目录及子目录所有 .tmp 文件
for /r %%f in (*.tmp) do echo 删除 %%f

choice /c yn /m 确认吗
if errorlevel 2 echo 你选了 No""")
    + tip("在 .bat 文件里循环变量写双百分号 " + code("%%f")
          + "；直接在命令行手敲时写单百分号 " + code("%f") + "。"
          + code("%~dp0") + " 表示“脚本自己所在的文件夹”，"
          + code("%1 %2") + " 表示传入的参数。")
))

# ---------------------------------------------------------------- 7
SECTIONS.append(("6. PowerShell① 基础与发现命令",
    h2("PowerShell 教程①：基础与“发现”命令")
    + h3("PowerShell 是什么")
    + para("PowerShell 是 CMD 的“超集升级版”：你在 CMD 会用的 "
           + code("dir") + "、" + code("cd") + "、" + code("cls")
           + " 在 PowerShell 里照样能用（它们是<b>别名</b>）。"
           "它真正的命令长这样：")
    + pre("Get-ChildItem     :: 列出目录（别名 ls / dir / gci）\nSet-Location ..   :: 回到上级（别名 cd / sl）\nClear-Host        :: 清屏（别名 cls / clear）\nGet-Content a.txt :: 查看文件（别名 cat / type / gc）")
    + h3("执行策略：为什么脚本第一次跑不起来")
    + para("PowerShell 默认禁止运行未签名的 .ps1 脚本（保护新手）。"
           "查看与一次性放开（只对你当前用户生效，安全）：")
    + pre("Get-ExecutionPolicy\nSet-ExecutionPolicy RemoteSigned -Scope CurrentUser")
    + bullets([
        code("RemoteSigned") + "：网上下载的脚本需签名，自己本地写的可直接跑——推荐。",
        "这是解决“无法加载文件，因为在此系统上禁止运行脚本”的标准做法。",
    ])
    + h3("不会命令？三个“发现”命令走天下")
    + pre("Get-Command *process*          :: 按关键词搜命令\nGet-Help Get-ChildItem -Full    :: 看某命令的完整帮助\nGet-Help Get-ChildItem -Examples:: 只看例子\nUpdate-Help                     :: 下载最新帮助文档")
    + tip("PowerShell 命令遵循“<b>动词-名词</b>”约定：Get（取）、Set（设）、"
          "New（新建）、Remove（删除）、Copy（复制）、Move（移动）、Start（启动）、"
          "Stop（停止）……猜都能猜个八九不离十。")
    + h3("常用别名对照表（CMD 习惯无缝迁移）")
    + table(["CMD / 熟悉的写法", "PowerShell 真身", "作用"], [
        ["dir / ls", "Get-ChildItem (gci)", "列目录"],
        ["cd", "Set-Location (sl)", "切换目录"],
        ["type / cat", "Get-Content (gc)", "看文件内容"],
        ["cls / clear", "Clear-Host", "清屏"],
        ["copy / cp", "Copy-Item (cpi)", "复制"],
        ["move / mv", "Move-Item (mi)", "移动"],
        ["del / rm", "Remove-Item (ri)", "删除"],
        ["md / mkdir", "New-Item -ItemType Directory", "建文件夹"],
        ["echo", "Write-Output", "输出"],
        ["findstr", "Select-String (sls)", "搜索文本"],
        ["tasklist / ps", "Get-Process (gps)", "看进程"],
        ["-", "Get-Service (gsv)", "看服务"],
    ])
    + pre("$PSVersionTable     :: 查看 PowerShell 版本（5.1 是自带版，7.x 是新版）")
))

# ---------------------------------------------------------------- 8
SECTIONS.append(("7. PowerShell② 对象管道（核心）",
    h2("PowerShell 教程②：对象管道——它真正的超能力")
    + h3("文本管道 vs 对象管道")
    + para("CMD 的管道传的是<b>纯文本</b>，你得用 findstr 去“抠字”；"
           "PowerShell 管道传的是<b>带属性的对象</b>，可以直接按字段筛选、排序。")
    + pre("# 找出当前目录及子目录里大于 1MB 的文件，按大小倒序，取前10个\nGet-ChildItem -Recurse -File |\n    Where-Object { $_.Length -gt 1MB } |\n    Sort-Object Length -Descending |\n    Select-Object Name, Length -First 10")
    + bullets([
        code("$_") + " 代表“管道里当前这个对象”，"
        + code("$_.Length") + " 就是它的大小属性。",
        code("1MB / 1KB / 1GB") + " 是 PowerShell 内置的数字单位。",
        "别名：" + code("?") + " = Where-Object，"
        + code("%") + " = ForEach-Object。",
    ])
    + h3("再来几个实战例子")
    + pre("# CPU 占用最高的 5 个进程\nGet-Process | Sort-Object CPU -Descending |\n    Select-Object Name, CPU -First 5\n\n# 批量重命名：给所有 .txt 加 .bak 后缀\nGet-ChildItem *.txt | Rename-Item -NewName { $_.Name + '.bak' }\n\n# 对每个对象做处理：列出所有文件名\nGet-ChildItem | ForEach-Object { '文件：' + $_.Name }\n\n# 统计当前目录有多少个文件\n(Get-ChildItem -File).Count")
    + h3("格式化输出")
    + pre("... | Format-Table -AutoSize   :: 紧凑表格（别名 ft）\n... | Format-List              :: 每个属性一行（别名 fl）\n... | Format-Wide -Column 4    :: 多列只显示名字（别名 fw）\n... | Out-GridView             :: 弹一个可筛选的图形表格窗口")
    + h3("导出数据")
    + pre("Get-Process | Export-Csv procs.csv -NoTypeInformation\nGet-ChildItem | ConvertTo-Json -Depth 3 | Set-Content files.json\nGet-ChildItem | Out-File list.txt -Encoding utf8")
    + tip("筛选条件还能直接写字段名，更短："
          + code("Get-Process | Where-Object Name -eq chrome") + "。")
))

# ---------------------------------------------------------------- 9
SECTIONS.append(("8. PowerShell③ 变量、运算符与脚本",
    h2("PowerShell 教程③：变量、运算符与 .ps1 脚本")
    + h3("变量：用 $ 开头")
    + pre("$x = 10\n$name = 'Fish'\n\"你好，$name，x=$x\"    :: 双引号会插值替换\n'你好，$name'         :: 单引号原样输出，不替换\n$nums = 1..5           :: 数组，包含 1,2,3,4,5\n$map = @{ a=1; b=2 }   :: 哈希表（键值对）\n[int]'42'              :: 把字符串转成整数\n$env:PATH              :: 读环境变量\n$env:MY_VAR = 'hi'     :: 设置环境变量")
    + h3("比较和逻辑运算符（不是 > < ==）")
    + table(["PowerShell", "含义", "例子"], [
        ["-eq / -ne", "等于 / 不等于", "$x -eq 10"],
        ["-gt / -lt", "大于 / 小于", "$x -gt 5"],
        ["-ge / -le", "大于等于 / 小于等于", "$x -ge 10"],
        ["-like", "通配符匹配", "$f -like '*.txt'"],
        ["-match", "正则匹配", "$s -match '\\d+'"],
        ["-and / -or / -not", "与 / 或 / 非", "($a) -and ($b)"],
    ])
    + warn("PowerShell 里 " + code("=") + " 是赋值，比较相等要用 "
           + code("-eq") + "！另外 " + code(">") + " 是重定向，不是大于。")
    + h3("if / foreach 语法")
    + pre("if ($x -gt 5) {\n    Write-Output 'x 很大'\n} else {\n    Write-Output 'x 很小'\n}\n\nforeach ($i in 1..5) {\n    Write-Output \"第 $i 次\"\n}\n\nforeach ($f in Get-ChildItem *.txt) {\n    Write-Output $f.Name\n}")
    + h3("函数和脚本参数")
    + pre("function Add($a, $b) {\n    return $a + $b\n}\nAdd 2 3        :: 调用，得到 5\n\n# 脚本开头声明参数\nparam(\n    [string]$Name = 'world',\n    [int]$Count = 1\n)\n\"Hello $Name x$Count\"")
    + h3("异常处理与注释")
    + pre("# 这是单行注释\n<# 这是\n   多行注释 #>\ntry {\n    $r = 1 / 0\n} catch {\n    Write-Output ('出错了：' + $_.Exception.Message)\n}")
    + h3("写并运行一个 .ps1 脚本（完整流程）")
    + nums([
        "新建 " + code("hello.ps1") + "，写入下面内容并保存（UTF-8）；",
        "若提示禁止运行，先执行 "
        + code("Set-ExecutionPolicy RemoteSigned -Scope CurrentUser") + "；",
        "运行时要带路径前缀：" + code("./hello.ps1 -Name 小明") + "。",
    ])
    + pre("param([string]$Name = 'world')\n$files = Get-ChildItem -File\n\"你好 $Name，当前目录有 $($files.Count) 个文件\"")
    + tip("写脚本推荐用 VS Code 加 PowerShell 扩展，有自动补全和调试；"
          "PowerShell 7（pwsh）跨平台、默认 UTF-8，体验比自带的 5.1 更好。")
))

# ---------------------------------------------------------------- 10
SECTIONS.append(("9. PowerShell④ 文件与系统实战",
    h2("PowerShell 教程④：文件、进程与服务实战")
    + h3("文件 / 文件夹（一套 *-Item 命令）")
    + pre("New-Item -ItemType Directory -Path 项目 -Force   :: 建文件夹\nNew-Item -ItemType File -Path a.txt -Force  :: 建文件\nSet-Content a.txt '第一行'        :: 写入内容（覆盖）\nAdd-Content a.txt '第二行'        :: 追加内容\nGet-Content a.txt -Tail 20        :: 只看最后20行（-Wait 实时跟踪）\nCopy-Item src D:\\dst -Recurse -Force :: 复制整个文件夹\nMove-Item a.txt D:\\bak\\          :: 移动\nRename-Item a.txt b.txt          :: 重命名\nRemove-Item 项目 -Recurse -Force :: 删除文件夹及内容\nTest-Path a.txt                  :: 判断是否存在（True/False）")
    + h3("进程")
    + pre("Get-Process                       :: 所有进程（别名 ps / gps）\nGet-Process chrome                :: 指定程序\nStart-Process notepad             :: 启动程序\nStopProcess -Name notepad -Force  :: 结束程序（别名 kill）\nStart-Process powershell -Verb RunAs :: 以管理员身份新开")
    + h3("服务")
    + pre("Get-Service                       :: 列出所有服务\nGet-Service -Name w32time          :: 查看某服务\nStart-Service w32time              :: 启动（需管理员）\nStop-Service w32time               :: 停止\nRestart-Service w32time            :: 重启")
    + h3("网络 / 下载 / 其他")
    + pre("Invoke-WebRequest https://xxx/f.zip -OutFile f.zip  :: 下载（别名 iwr / curl）\nInvoke-RestMethod https://api.github.uk :: 取 JSON 并自动解析（别名 irm）\nGet-NetIPAddress                    :: 查看 IP（比 ipconfig 更结构化）\nResolve-DnsName baidu.com           :: DNS 查询\nGet-Location                        :: 当前目录（别名 pwd）")
    + warn("PowerShell 里的 " + code("curl") + " 是 Invoke-WebRequest 的别名，"
           "参数和真正的 curl 不一样；想用真 curl 请写 " + code("curl.exe") + "。")
))

# ---------------------------------------------------------------- 11
SECTIONS.append(("10. CMD ↔ PowerShell 对照表",
    h2("CMD ↔ PowerShell 命令对照表")
    + h3("文件与目录")
    + table(["要做的事", "CMD", "PowerShell"], [
        ["列目录", "dir", "Get-ChildItem（dir / ls）"],
        ["切换目录", "cd / d:", "Set-Location（cd）"],
        ["看文件内容", "type f", "Get-Content f（cat）"],
        ["建文件夹", "md 文件夹", "New-Item -ItemType Directory"],
        ["删除文件", "del f", "Remove-Item f（rm）"],
        ["删除文件夹", "rd /s /q 文件夹", "Remove-Item 文件夹 -Recurse -Force"],
        ["复制", "copy / xcopy", "Copy-Item -Recurse"],
        ["移动", "move", "Move-Item"],
        ["重命名", "ren old new", "Rename-Item"],
        ["搜文件内容", 'findstr /s /i "x" *.txt', "Select-String -Path *.txt -Pattern x"],
        ["判断文件存在", "if exist f (...)", "Test-Path f"],
    ])
    + h3("系统与网络")
    + table(["要做的事", "CMD", "PowerShell"], [
        ["系统信息", "systeminfo", "Get-ComputerInfo"],
        ["当前用户", "whoami", "whoami（相同）"],
        ["看 IP", "ipconfig /all", "Get-NetIPAddress"],
        ["测试连通", "ping host", "Test-Connection host"],
        ["端口连接", "netstat -ano", "Get-NetTCPConnection"],
        ["看进程", "tasklist", "Get-Process"],
        ["结束进程", "taskkill /PID n /F", "Stop-Process -Id n -Force"],
        ["关机/重启", "shutdown /r /t 0", "Stop-Computer / Restart-Computer"],
        ["下载文件", "(无内置)", "Invoke-WebRequest -OutFile"],
    ])
    + h3("脚本概念对照")
    + table(["概念", "CMD/.bat", "PowerShell/.ps1"], [
        ["变量", "set x=1 → %x%", "$x = 1 → $x"],
        ["注释", "rem 或 ::", "# 注释"],
        ["输出", "echo 文本", "Write-Output 文本"],
        ["条件", "if %errorlevel%==0", "if ($?) { }"],
        ["循环", "for /r %%f ...", "foreach ($f in ...) { }"],
        ["用户输入", "set /p x=提示", "Read-Host 提示"],
        ["脚本参数", "%1 %2", "param($x)；调用 .\\a.ps1 -x 1"],
        ["管道", "传文本", "传对象"],
    ])
))

# ---------------------------------------------------------------- 12
SECTIONS.append(("11. Python 交互环境",
    h2("在 Fish away 里使用 Python")
    + h3("打开 Python")
    + para("点侧边栏「Python」，会启动 Python 交互环境（REPL），提示符是 "
           + code(">>>") + "：")
    + pre("Python 3.14.7 ...\nType \"help\", \"copyright\" ... for more information.\n>>>")
    + h3("把它当计算器 / 跑代码")
    + pre(">>> 1 + 2\n3\n>>> print('你好 Fish away')\n你好 Fish away\n>>> x = 10\n>>> x * 2\n20\n>>> for i in range(3):\n...     print('第', i)\n...\n第 0\n第 1\n第 2\n>>> import math\n>>> math.sqrt(16)\n4.0")
    + bullets([
        "以 " + code(">>>") + " 开头是普通行；以 " + code("...")
        + " 开头表示代码块还没写完（缩进后再按一次回车结束）。",
        "不知道对象有什么：" + code("dir('')") + "；查帮助："
        + code("help(print))") + "。",
    ])
    + h3("退出 Python")
    + bullets([
        "输入 " + code("exit()") + " 或 " + code("quit()") + " 回车。",
        "或者按 " + code("Ctrl + Z") + " 再按 Enter（Windows 方式）。",
    ])
    + h3("安装第三方库 & 运行脚本（在 CMD / PowerShell 标签里做）")
    + pre("pip install requests        :: 安装第三方库\npython script.py            :: 运行一个 .py 脚本\npython -m pip --version     :: 查看 pip")
    + warn("pip 命令要在 <b>CMD 或 PowerShell</b> 里运行，不是在 "
           + code(">>>") + " Python 提示符里；在 >>> 里敲 pip 会报 NameError。")
))

# ---------------------------------------------------------------- 13
SECTIONS.append(("12. 更多语言环境：Node.js 与插件注册新环境",
    h2("更多语言环境：Node.js 与插件注册新环境")
    + para("除了内置的六种环境，Fish away 还内置了 <b>Node.js</b> 支持，"
           "并且允许<b>插件注册任意新的环境/语言</b>——Ruby、Go、PHP、R、"
           "Perl、Lua、Java（JShell）……只要本机装了、能在命令行启动，就能"
           "像内置环境一样在侧边栏一键打开。")
    + h3("一、Node.js 是什么 / 怎么装")
    + bullets([
        "Node.js 是一个让 <b>JavaScript 可以脱离浏览器运行</b>的环境，"
        "做网页后端、前端工程化（npm）、写小工具都用它。",
        "官方下载：" + code("https://nodejs.org/")
        + "，选 <b>LTS（长期支持版）</b>；",
        "国内镜像（更快）：" + code("https://mirrors.huaweicloud.com/nodejs/")
        + "，选最新的 LTS 版本文件夹，下载对应 Windows x64 的 .msi 安装。",
        "安装后自带 <b>npm</b>（包管理器），在 CMD/PowerShell 里运行 "
        + code("node -v") + " 和 " + code("npm -v") + " 能看到版本号即成功。",
    ])
    + h3("二、在 Fish away 里使用 Node.js")
    + para("点侧边栏「Node.js」即进入交互环境（REPL）：")
    + pre("Welcome to Node.js v22.x.x.\nType \".help\" for more information.\n> 1 + 2\n3\n> console.log('你好 Fish away')\n你好 Fish away\nundefined\n> .exit")
    + bullets([
        "提示符 " + code(">") + " 后直接输入 JavaScript 表达式，回车即出结果。",
        "多行输入（如函数）会自动出现 " + code("...") + " 续行提示。",
        "退出：输入 " + code(".exit") + " 回车，或连按两次 Ctrl+C。",
        "运行脚本文件（在 CMD/PowerShell 标签里）：" + code("node app.js") + "。",
    ])
    + h3("三、npm 下载加速（国内镜像）")
    + pre("npm config get registry\nnpm config set registry https://registry.npmmirror.com\nnpm config delete registry   :: 恢复官方源")
    + tip("npmmirror（淘宝 NPM 镜像）是国内最常用的 npm 镜像，设置后 "
          + code("npm install") + " 速度会快很多。")
    + h3("四、用插件注册一个全新环境（核心能力）")
    + para("插件在 setup(app) 里调用 " + code("app.register_environment(...)")
           + " 即可把任意命令行程序注册成侧边栏里的新会话。参数：")
    + table(["参数", "含义"], [
        ["key", "唯一英文标识，如 'ruby'、'go'"],
        ["label", "侧边栏显示的中文名"],
        ["argv", "启动命令：字符串 / 命令行列表 / 返回列表的函数"],
        ["icon", "图标：内置名 / 图片路径 / emoji，可省略"],
        ["background", "背景：颜色字符串或 [颜色1,颜色2] 渐变，可省略"],
        ["cwd", "该环境启动时的起始目录，可省略"],
        ["home / china / advice", "缺失时安装指引里显示的官网/镜像/建议"],
    ])
    + para("示例：注册 Ruby 环境（需本机已装 Ruby，https://rubyinstaller.org/）：")
    + pre('''PLUGIN_NAME = "Ruby 环境"
PLUGIN_VERSION = "1.0"
PLUGIN_DESCRIPTION = "给 Fish away 添加 Ruby 会话"

def setup(app):
    app.register_environment(
        key="ruby",
        label="Ruby",
        argv=["ruby", "irb"] if False else "ruby",   # 直接进 irb 可写 ["ruby","-S","irb"]
        icon="💎",
        background=["#2b1430", "#1a1020"],
        advice="到 https://rubyinstaller.org/ 下载安装，勾选 Add to PATH")''')
    + para("再比如注册 Go（安装包见 https://go.dev/dl/ 或国内 "
           + code("https://golang.google.cn/") + "）：")
    + pre('''def setup(app):
    app.register_environment(
        "go", "Go 语言", ["go", "tool", "compile"] and "go",
        icon="🐹", background=["#0d2a33", "#101820"],
        advice="Go 安装后自带命令行，REPL 需配合 gore 等第三方工具")''')
    + warn("注册成功后，新按钮立即出现在侧边栏「插件环境」区；"
           "若 argv 指向的程序没装，点击后会显示彩色安装指引（和内置环境一致）。")
    + tip("argv 写成<b>函数</b>可以在每次打开会话时动态查找路径，例如："
          + code("argv=lambda: [shutil.which('php'), '-a']") + "。")
))

# ---------------------------------------------------------------- 14
SECTIONS.append(("13. Git Bash 入门",
    h2("认识 Git Bash")
    + para("<b>Git Bash</b> 是安装 <b>Git for Windows</b> 时附带的一个命令行环境："
           "它把 Linux/Mac 上常用的 <b>Bash</b> 外壳和一大堆 Unix 工具（ls、grep、"
           "ssh、vim 等）搬到了 Windows 上。做开发、连服务器、用 Git，"
           "几乎都会用到它。")
    + h3("安装 Git Bash")
    + nums([
        "官方地址：" + code("https://git-scm.com/download/win") + "；"
        "国内下载更快：" + code("https://mirrors.huaweicloud.com/git-for-windows/"),
        "下载安装包一路下一步即可（默认选项就很好），安装完就有了 Git Bash。",
        "回到 Fish away 点侧边栏「Git Bash」；如果仍提示没检测到，"
        "到「设置 → 会话路径」里手动选择 Git 安装目录下的 "
        + code("bin\\bash.exe") + "。",
    ])
    + tip("Git Bash 的可执行文件一般在 "
           + code("C:\\Program Files\\Git\\bin\\bash.exe") + "。")
    + h3("第一批命令（打开 Git Bash 跟着敲）")
    + pre("pwd                 我现在在哪个目录（print working directory）\nls                  列出当前目录的文件\nls -la              连隐藏文件、权限、大小一起列出\ncd 文件夹            进入某个文件夹\ncd ..               回到上一级\ncd ~                回到家目录（C:\\Users\\你的名字）\nclear               清屏")
    + h3("文件与目录")
    + pre("mkdir 项目           新建文件夹\ntouch a.txt          新建空文件\ncp a.txt b.txt       复制\nmv a.txt docs/       移动（也能改名）\nrm a.txt             删除文件\nrm -r 文件夹          删除文件夹（小心，不进回收站）\ncat a.txt            查看文件全部内容\nless a.txt           分页查看（按 q 退出）\nhead -n 5 a.txt      只看前 5 行\nfind . -name '*.py'  在当前目录树下找 .py 文件")
    + h3("搜索、管道与重定向")
    + pre("grep 关键词 a.txt           在文件里找包含关键词的行\ngrep -rn 关键词 .            递归搜索当前整个目录\nls | grep doc               把 ls 的结果交给 grep 筛选\nls > list.txt               把输出写进文件（覆盖）\necho hello >> list.txt      把输出追加到文件末尾")
    + h3("权限与远程连接")
    + pre("chmod +x script.sh     给脚本加上可执行权限\nssh user@服务器地址     用 SSH 登录远程服务器\nscp a.txt user@主机:~/   上传文件到远程主机")
    + h3("Git 最基础五连")
    + pre("git clone 仓库地址       下载一个远程仓库\ngit status              看当前改了什么\ngit add .               把所有改动加入暂存\ngit commit -m '说明'     提交一次\ngit push                推送到远程（git pull 拉取更新）")
    + h3("Bash 和 CMD 的关键区别（新手最容易懵的地方）")
    + bullets([
        "路径写法不同：Bash 里是 " + code("/c/Users/你的名字")
        + "，用正斜杠 /，没有盘符冒号。",
        "大小写敏感：" + code("ls") + " 可以，" + code("LS") + " 不行。",
        "运行当前目录的程序要加 ./ ：" + code("./script.sh") + "。",
        "隐藏文件以点开头，比如 " + code(".gitconfig") + "。",
    ])
    + h3("CMD ↔ Bash 速查")
    + table(["想做的事", "CMD", "Git Bash"], [
        ["列文件", "dir", "ls -la"],
        ["清屏", "cls", "clear"],
        ["复制", "copy", "cp"],
        ["移动/改名", "move / ren", "mv"],
        ["删除文件", "del", "rm"],
        ["删除文件夹", "rd /s", "rm -r"],
        ["看文件内容", "type", "cat"],
        ["找文件", "dir /s /p", "find"],
        ["文本搜索", "findstr", "grep"],
    ])
))

# ---------------------------------------------------------------- 13
SECTIONS.append(("14. WSL（Linux 子系统）入门",
    h2("认识 WSL")
    + para("<b>WSL</b>（Windows Subsystem for Linux）让你在 Windows 里直接跑一个"
           "真正的 <b>Linux</b> 系统：不用装虚拟机、不用双系统，Linux 的命令、"
           "开发环境、服务都能直接用，而且和 Windows 文件互通。")
    + h3("安装 WSL（需要管理员权限 + 重启一次）")
    + nums([
        "在 Fish away 侧边栏点「普通用户模式」徽章，选择以管理员身份重启；"
        "或手动用管理员打开 PowerShell。",
        "运行：" + pre("wsl --install -d Ubuntu"),
        "按提示重启电脑，开始菜单会出现 “Ubuntu”，首次启动设置 Linux 的"
        "用户名和密码（输入密码时屏幕不显示，正常现象）。",
        "回到 Fish away 点侧边栏「WSL」即可进入。装了多个发行版时，"
        "可在「设置 → 会话路径 → WSL 发行版」里选择。",
    ])
    + warn("只运行 wsl.exe 但没装任何发行版时，Fish away 会提示"
           "“没有已安装的 Linux 发行版”，这就是上面的安装步骤没做完。")
    + h3("Linux 命令速览（和 Git Bash 几乎一样）")
    + pre("ls -la              列文件\ncd / cd ..           切换目录\npwd                  在哪\nmkdir / touch        建文件夹/文件\nrm / rm -r           删除\ncp / mv              复制/移动\ncat / less           看文件\ngrep / find          搜索\nclear                清屏")
    + h3("用 apt 安装软件（Ubuntu/Debian）")
    + pre("sudo apt update                更新软件列表（sudo = 临时用管理员）\nsudo apt install python3       安装软件（示例：python3）\nsudo apt install git curl vim  一次装多个\npython3 --version              验证")
    + tip("Linux 里 Python 通常叫 " + code("python3") + "，包管理用 "
           + code("apt") + "，这和 Windows 上的 pip 是两回事。")
    + h3("Windows 与 Linux 的文件互通")
    + bullets([
        "在 Linux 里访问 Windows 文件：" + code("/mnt/c/...")
        + "，例如 " + code("cd /mnt/c/Users/你的名字") + "。",
        "在 Linux 里打开 Windows 资源管理器：" + code("explorer.exe .") + "。",
        "在 Windows 里访问 Linux 文件：资源管理器地址栏输入 "
        + code("\\\\wsl$") + "（或 \\\\wsl.localhost）。",
        "日常开发的代码建议放在 Linux 家目录里（~），速度更快。",
    ])
    + h3("WSL 管理命令（在 Windows 的 PowerShell/CMD 里运行）")
    + pre("wsl -l -v             查看已安装的发行版与版本\nwsl                   进入默认发行版\nwsl -d Ubuntu         指定进入 Ubuntu\nwsl --shutdown        关闭所有 WSL 实例\nwsl --update         更新 WSL 内核")
))

# ---------------------------------------------------------------- 14
SECTIONS.append(("15. 国内镜像与下载加速",
    h2("为什么要切换镜像")
    + para("很多开发资源的官方服务器在国外，国内直连慢甚至超时。"
           "<b>镜像（Mirror）</b>就是国内服务器同步的一份完整副本，内容一样、"
           "下载快得多。Fish away 默认就走国内镜像。")
    + h3("一键切换：Ctrl + Shift + Z")
    + bullets([
        "在 Fish away 任意界面按 " + code("Ctrl+Shift+Z")
        + "，即可在「国内镜像 / 国外官方源」之间切换。",
        "切换后会弹出轻提示告诉你当前用的是哪个；设置会自动保存。",
        "也可以在「设置 → 镜像 / 下载加速」里勾选。",
    ])
    + h3("pip 下载 Python 库加速")
    + bullets([
        "最简单：设置 → 镜像页点「一键配置 pip 使用所选源」，以后所有 "
        + code("pip install") + " 自动加速。",
        "临时单次使用镜像："
        + pre("pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple"),
        "常用国内 pip 源：",
    ])
    + pre("清华 TUNA : https://pypi.tuna.tsinghua.edu.cn/simple\n阿里云   : https://mirrors.aliyun.com/pypi/simple/")
    + h3("安装包下载加速")
    + table(["要下载的东西", "国内镜像地址"], [
        ["Git for Windows", "https://mirrors.huaweicloud.com/git-for-windows/"],
        ["Python 安装包", "https://mirrors.huaweicloud.com/python/"],
        ["Node.js 安装包", "https://mirrors.huaweicloud.com/nodejs/"],
    ])
    + h3("npm（Node.js 包管理器）加速")
    + pre("npm config set registry https://registry.npmmirror.com")
    + h3("WSL 里的 Ubuntu 也能换源（可选，进阶）")
    + para("Ubuntu 的软件源同样有国内镜像，可参考清华镜像站的 Ubuntu 帮助："
           + code("https://mirrors.tuna.tsinghua.edu.cn/help/ubuntu/")
           + "，按页面说明替换 /etc/apt/sources.list 后再 "
           + code("sudo apt update") + "。")
    + tip("想恢复官方源：设置 → 镜像页点「恢复 pip 默认设置」，"
          "或再按一次 Ctrl+Shift+Z 切回去。")
))

# ---------------------------------------------------------------- 15
SECTIONS.append(("16. 插件开发指南",
    h2("Fish away 插件端口（真的能用）")
    + para("Fish away 内置了一个真实的插件系统：插件就是普通的 "
           + code(".py") + " 文件，软件启动时会调用插件里的 "
           + code("setup(app)") + " 函数，把一组<b>宿主 API</b> 交给插件，"
           "插件借此添加按钮、执行命令、新建终端、弹提示、<b>注册全新的"
           "语言环境</b>、<b>自定义图标与背景</b>，甚至<b>给本教程追加新"
           "章节</b>。")
    + h3("三步使用插件")
    + nums([
        "把插件 .py 文件放进<b>插件目录</b>（设置 → 插件 → 打开插件目录；"
        "也可以点「导入插件」直接选文件）。",
        "在插件列表里<b>勾选启用</b>，保存。",
        "<b>重启 Fish away</b>（设置里有重启按钮），插件就生效了。",
    ])
    + h3("插件文件长什么样（最小可用示例）")
    + pre('''PLUGIN_NAME = "我的第一个插件"
PLUGIN_VERSION = "1.0"
PLUGIN_DESCRIPTION = "点按钮在终端里打个招呼"

def setup(app):
    app.add_sidebar_button("打招呼", say_hello)

def say_hello():
    app.run_command("echo 你好，我是插件！")''')
    + h3("宿主 API 一览（setup(app) 里的 app）")
    + table(["API", "作用"], [
        ["app.add_sidebar_button(文字, 函数, icon=, background=)",
         "在侧边栏「插件」区添加按钮，可自定义图标与背景"],
        ["app.register_environment(key, 标签, argv, icon=, background=, …)",
         "注册全新环境/语言，侧边栏「插件环境」区出现会话按钮"],
        ["app.add_tutorial_chapter(标题, html)",
         "向新手教程追加一个章节（重启后仍在）"],
        ["app.run_command(命令字符串)",
         "在当前终端执行一行命令（如 echo、ls）"],
        ["app.new_session(会话key)",
         "新建终端：cmd / ps / python / node / gitbash / wsl 或插件环境"],
        ["app.show_message(文字)",
         "弹出一个消息框"],
        ["app.toast(文字)",
         "在窗口底部显示一条轻提示（几秒后消失）"],
        ["app.get_current_terminal()",
         "拿到当前终端视图对象（进阶用法）"],
        ["app.config",
         "读取当前软件配置字典"],
    ])
    + h3("自定义图标（三种写法都支持）")
    + bullets([
        "<b>内置图标名</b>：" + code('icon="node"')
        + "，可选 cmd / ps / py / node / git / wsl / gear / shield / plug / "
        "book / broom / info。",
        "<b>图片文件</b>：" + code('icon=r"C:\\imgs\\my.png"')
        + "，支持 .png / .jpg / .ico，建议正方形。",
        "<b>emoji 或短文字</b>：" + code('icon="🐳"')
        + "，软件会自动画成圆角方块。",
    ])
    + h3("自定义背景（按钮与终端会话都能用）")
    + pre('''# 纯色
background="#1e2b3a"
# 渐变（两种颜色，自动斜向渐变）
background=["#2b1430", "#101a2a"]
# 图片背景（终端会话）
background=r"C:\\imgs\\wallpaper.jpg"''')
    + tip("注册环境时给的 background 会作为该会话终端的默认背景；"
          "建议选<b>偏暗</b>的图片，文字才看得清。")
    + h3("给新手教程注入章节")
    + pre('''def setup(app):
    app.add_tutorial_chapter(
        "我的插件使用说明",
        "<h2>使用说明</h2><p>点击侧边栏按钮即可……</p>")''')
    + para("注入的章节会追加到目录末尾；若教程窗口正开着会自动刷新。")
    + h3("更完整的例子（随包示例插件的写法）")
    + pre('''import datetime

PLUGIN_NAME = "快捷工具箱"
PLUGIN_VERSION = "1.0"
PLUGIN_DESCRIPTION = "执行命令、弹时间、弹消息"

def setup(app):
    app.add_sidebar_button("问候",
        lambda: app.run_command("echo Hello!"))
    app.add_sidebar_button("当前时间", show_time)
    app.add_sidebar_button("关于",
        lambda: app.show_message("这是我的插件"))

def show_time():
    now = datetime.datetime.now().strftime("%H:%M:%S")
    app.toast(f"现在是 {now}")''')
    + bullets([
        "某个插件出错不会拖垮软件：错误会以轻提示显示，其它插件照常加载。",
        "插件可以安装第三方库，在自己的代码里正常 import 使用。",
        "改了插件代码也要重启才会重新加载。",
        "随包的「示例：快捷工具箱」就是最好的模板，可复制后改成你自己的。",
    ])
    + warn("插件拥有和 Fish away 相同的权限，请只启用你信任来源的插件。")
))

# ---------------------------------------------------------------- 16
SECTIONS.append(("17. 常见错误与新手 FAQ",
    h2("常见错误与新手 FAQ")
    + h3("Q1：提示“'xxx' 不是内部或外部命令，也不是可运行的程序”")
    + bullets([
        "90% 是<b>拼写错误</b>或多了空格/中文符号，重新核对。",
        "程序没加入 PATH：用完整路径运行，或把程序目录加进环境变量 PATH。",
        "当前目录下的程序，CMD 里要写 " + code(".\程序名")
        + "（PowerShell 同理，安全设计）。",
    ])
    + h3("Q2：PowerShell“无法加载文件……因为在此系统上禁止运行脚本”")
    + pre("Set-ExecutionPolicy RemoteSigned -Scope CurrentUser")
    + h3("Q3：路径/文件名里有空格")
    + bullets([
        "用英文双引号包起来：" + code('cd "C:\\Program Files"') + "。",
        "多利用 Tab 补全，系统会自动帮你加好引号。",
    ])
    + h3("Q4：中文乱码 / 方框")
    + bullets([
        "CMD 临时切到 UTF-8：" + code("chcp 65001") + " 再运行。",
        "保存脚本时选 <b>UTF-8</b> 编码；PowerShell 7 默认就是 UTF-8。",
        "Windows PowerShell 5.1 对无 BOM 的脚本可能按系统编码读，"
        "可在 VS Code 里选“UTF-8 with BOM”。",
    ])
    + h3("Q5：命令卡住不动了")
    + bullets([
        "按 " + code("Ctrl + C") + " 中断；",
        "如果是 more/less 类分页器，按 " + code("q") + " 退出；",
        "可能在等你输入（脚本里有 set /p 或 Read-Host），按提示输入后回车。",
    ])
    + h3("Q6：红色的报错怎么读")
    + bullets([
        "先看最后一行：通常写明错误类型（找不到文件、权限不足、语法错误）。",
        "“拒绝访问/权限”→ 用管理员身份开终端再试。",
        "“系统找不到指定的路径/文件”→ 用 dir 核对路径和文件名，"
        "注意资源管理器里可能隐藏了扩展名（.txt.txt 的坑）："
        "查看 → 勾选「文件扩展名」。",
    ])
    + h3("Q7：CMD 和 PowerShell 该用哪个？")
    + bullets([
        "照着老教程/老脚本走 → CMD；",
        "想学新东西、处理文件和数据、写自动化脚本 → PowerShell；",
        "在 Fish away 里随时可以两个都开，标签页并排用。",
    ])
))

# ---------------------------------------------------------------- 19
SECTIONS.append(("18. 卡顿、闪退与兼容性排查",
    h2("卡顿、闪退与兼容性排查")
    + para("本章汇总 Fish away 在各种电脑环境下可能出现的性能与稳定性"
           "问题，按“现象 → 原因 → 解决办法”排列，照着做即可。")
    + h3("一、界面卡顿、输出一卡一卡")
    + bullets([
        "<b>v3 已优化</b>：渲染合并到约每秒 30 次、历史行缓存、输出只"
        "追加时走快速路径。若仍卡，继续往下看。",
        "<b>调小历史回滚行数</b>：设置 → 外观 → 历史回滚行数，从 5000 "
        "调到 2000，内存占用和渲染压力会明显下降。",
        "<b>关闭模糊效果</b>：设置 → 外观，取消勾选亚克力；透明窗口的"
        "实时模糊在性能较弱的核显上很耗性能。",
        "<b>少开标签</b>：每个终端标签都有独立线程，十几个标签同时跑"
        "（尤其编译、npm install）会占满 CPU。",
        "任务管理器（Ctrl+Shift+Esc）看一下是 CPU 满还是磁盘 100%："
        "磁盘 100% 时终端本身也会被拖慢，等磁盘操作结束。",
    ])
    + h3("二、双击后闪退 / 窗口一闪就没了")
    + bullets([
        "<b>先看错误日志</b>：打开用户数据目录（在地址栏输入 "
        + code("%APPDATA%\\FishAway")
        + "），里面的 " + code("error.log")
        + " 记录了崩溃的完整原因；v3 起崩溃时也会弹窗提示该路径。",
        "<b>杀毒软件误删（最常见）</b>：PyInstaller 打包的单文件 exe "
        "经常被部分杀毒软件（含 Windows Defender）误判并直接隔离，"
        "表现为“双击没反应/闪退”。到杀毒软件的「保护历史记录/隔离区」"
        "里查看是否有 Fish away，选择「允许/还原」，并把 Fish away "
        "加入「排除项/白名单」。",
        "<b>改用源码启动（最稳）</b>：双击文件夹里的 "
        + code("启动 Fish away.bat")
        + "，不依赖 exe，几乎不会被误杀。",
        "<b>配置损坏</b>：删除用户数据目录里的 config.json（可先备份"
        "插件），软件会重建默认配置。",
    ])
    + h3("三、开了 Windows 兼容模式反而闪退")
    + bullets([
        "兼容模式（尤其勾选“以兼容模式运行”）可能<b>关闭桌面窗口管理器"
        "（DWM）合成</b>，而透明窗口依赖 DWM，关闭后会黑屏或崩溃。",
        "<b>v3 已自动处理</b>：检测到 DWM 合成关闭时，软件会自动放弃"
        "透明效果、使用不透明窗口。建议同时<b>取消 exe 属性里的所有"
        "兼容模式勾选</b>（右键 exe → 属性 → 兼容性 → 更改所有用户的"
        "设置 → 全部取消勾选）。",
        "“以管理员身份运行此程序”这一项也不建议长期勾选，用侧边栏"
        "徽章按需提权即可。",
    ])
    + h3("四、某个终端打不开 / 一直转圈")
    + bullets([
        "先看侧边栏该环境后面是 ✓ 还是 ✗：✗ 表示本机没装，点击后"
        "控制台会给出彩色安装指引，按指引安装即可。",
        "装了仍检测不到：设置 → 会话路径，点「自动检测」，或「浏览」"
        "手动选择可执行文件。",
        "PowerShell 首次启动会初始化配置文件，较慢属正常；若卡住，"
        "新开一个 CMD 标签输入 " + code("powershell -NoProfile")
        + " 对比，判断是不是配置文件（$PROFILE）里有脚本卡住。",
        "WSL 标签打不开多半是没装发行版（运行 wsl --install -d "
        "Ubuntu）或 WSL 服务异常，试 " + code("wsl --shutdown") + " 再开。",
    ])
    + h3("五、显示异常 / 花屏 / 黑块")
    + bullets([
        "更新显卡驱动；远程桌面下建议关闭透明效果。",
        "换终端字体：设置 → 外观 → 终端字体选 Consolas，排除字体"
        "缺失导致的方块。",
        "缩放比例异常：注销重新登录，或在显示设置里把缩放设为 100% "
        "后再改回。",
    ])
    + h3("六、收集信息，方便排查")
    + bullets([
        "error.log 的最后一段；",
        "Windows 版本（" + code("winver") + "）；",
        "出问题的是哪个环境、做了什么操作后出现；",
        "是否开了兼容模式、用的什么杀毒软件。",
    ])
    + tip("最稳妥的使用组合：<b>关闭兼容模式 + 源码 bat 启动或把 exe "
          "加入杀软白名单 + 按需用管理员徽章提权</b>。")
))

# ---------------------------------------------------------------- 20
SECTIONS.append(("19. 一页速查表 Cheat Sheet",
    h2("一页速查表（建议截图保存）")
    + h3("最通用（CMD / PowerShell 都能用）")
    + pre("cls / clear        清屏\nTab                自动补全\n↑ ↓                历史命令\nCtrl + C           中断\nCtrl + L           清屏\ncd ..              上一级\ncd \\               根目录\ndir                列文件\nipconfig           看 IP\nping 域名          测网络\nwhere 程序         找程序位置")
    + h3("CMD 高频")
    + pre("md 文件夹          新建文件夹\nrd /s 文件夹        删除文件夹\ntype f             看文件\ncopy a b           复制\nmove a b           移动\ndel f              删除\nren old new        重命名\ntasklist           看进程\ntaskkill /PID n /F 杀进程\nshutdown /r /t 0   立即重启\nnetstat -ano        看端口")
    + h3("PowerShell 高频")
    + pre("Get-ChildItem              列文件（ls）\nGet-Help 命令               查帮助\nGet-Command 关键词          搜命令\n$x = 10                     赋值\n... | Where-Object {...}    筛选\n... | Select-Object -First n 取前n\nNew-Item -ItemType Directory 建文件夹\nRemove-Item x -Recurse -Force 删除\nGet-Process                 看进程\nStop-Process -Name x -Force  杀进程\nGet-Service                 看服务\nInvoke-WebRequest -OutFile f 下载")
    + tip("学会“<b>查帮助 + Tab 补全 + Ctrl+C</b>”三件套，你就已经超过"
          "绝大多数新手了。剩下的命令随用随查，不用死记硬背。")
    + para("<b>祝玩得开心！—— Fish away</b>")
))


# ====================================================================
#  教程窗口
# ====================================================================
class TutorialWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fish away · 终端超级新手教程")
        self.resize(1000, 700)
        self.setStyleSheet("""
            QDialog { background: rgba(20,22,29,248); border-radius:12px; }
            QListWidget {
                background: rgba(13,15,20,220); color:#c6ccd8;
                border:none; border-radius:10px; padding:8px; outline:none;
            }
            QListWidget::item { padding:8px 10px; border-radius:7px; }
            QListWidget::item:selected {
                background: rgba(34,211,238,55); color:#eafcfe;
            }
            QListWidget::item:hover { background: rgba(255,255,255,12); }
            QTextBrowser {
                background: rgba(23,25,32,235); color:#d7dce5;
                border:none; border-radius:10px; padding:12px;
            }
            QLineEdit {
                background: rgba(13,15,20,220); border:none;
                border-radius:8px; padding:7px 10px; color:#dfe4ec;
            }
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # 左：搜索 + 目录
        left = QVBoxLayout()
        left.setSpacing(8)
        search = QLineEdit()
        search.setPlaceholderText("搜索章节标题，如“管道”……")
        left.addWidget(search)

        self.toc = QListWidget()
        for title, _ in SECTIONS:
            QListWidgetItem(title, self.toc)
        left.addWidget(self.toc, 1)

        lw = QWidget(); lw.setLayout(left)
        lw.setFixedWidth(248)
        lw.setStyleSheet("background:transparent;")
        root.addWidget(lw)

        # 右：文档
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        root.addWidget(self.browser, 1)

        self.toc.currentRowChanged.connect(self._show)
        search.textChanged.connect(self._filter)
        self.toc.setCurrentRow(0)

    def _show(self, row):
        if 0 <= row < len(SECTIONS):
            self.browser.setHtml(CSS + SECTIONS[row][1])

    def _filter(self, text):
        text = text.strip().lower()
        for i in range(self.toc.count()):
            item = self.toc.item(i)
            item.setHidden(bool(text) and text not in item.text().lower())

    def refresh(self):
        """插件注入新章节后重建目录，并尽量保持当前章节。"""
        row = self.toc.currentRow()
        self.toc.blockSignals(True)
        self.toc.clear()
        for title, _ in SECTIONS:
            QListWidgetItem(title, self.toc)
        self.toc.blockSignals(False)
        target = row if 0 <= row < len(SECTIONS) else 0
        self.toc.setCurrentRow(target)
        self._show(target)
