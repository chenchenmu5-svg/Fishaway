# -*- coding: utf-8 -*-
"""
====================================================================
  Fish away v3 插件示例：环境注册 / 自定义图标背景 / 教程注入
--------------------------------------------------------------------
  启用本插件并重启后：
  1. 侧边栏「插件环境」区出现「演示：深海 CMD」，点击打开一个带
     渐变背景、🐟 图标的真实 CMD 会话；
  2. 侧边栏「插件」区出现一个自定义样式的按钮；
  3. 新手教程末尾追加一个《插件注入的示例章节》。
  可把本文件复制后改成你自己的环境（Ruby/Go/PHP/R ...）。
====================================================================
"""
import os
import shutil

PLUGIN_NAME = "v3 能力演示：环境/图标/教程"
PLUGIN_VERSION = "1.0"
PLUGIN_DESCRIPTION = "演示注册新环境、自定义图标背景、向教程注入章节"
PLUGIN_AUTHOR = "Fish away"


def _find_cmd():
    p = shutil.which("cmd")
    if p:
        return [p]
    sysroot = os.environ.get("SystemRoot", r"C:\Windows")
    return [os.path.join(sysroot, "System32", "cmd.exe")]


def setup(app):
    # 1) 注册一个自定义环境：本质是 CMD，但带专属图标、渐变背景与起始目录
    app.register_environment(
        key="demo_deepsea",
        label="演示：深海 CMD",
        argv=_find_cmd,                 # 函数形式：每次打开时动态查找
        icon="🐟",                      # emoji 图标（也可用图片路径）
        background=["#0b2a3a", "#101a33"],   # 斜向渐变背景
        cwd=os.path.expanduser("~"),
        home="https://learn.microsoft.com/windows-server/administration/windows-commands/cmd",
        advice="这是插件注册的演示环境，无需额外安装任何东西。",
    )

    # 2) 自定义图标与背景的侧边栏按钮
    app.add_sidebar_button(
        "演示按钮",
        lambda: app.run_command("echo Hello from env_demo plugin!"),
        icon="🐳",
        background=["#2b1430", "#1a1020"],
    )

    # 3) 向新手教程注入一个章节
    app.add_tutorial_chapter(
        "插件注入的示例章节",
        "<h2>这是插件注入的章节</h2>"
        "<p>如果你在目录末尾看到本章，说明 <code>add_tutorial_chapter"
        "</code> 工作正常。</p>"
        "<p>插件还可以：注册新环境、自定义图标与背景、执行命令、弹出"
        "提示。详见第 16 章《插件开发指南》。</p>"
        '<div style="background:#0d2b33; border-left:3px solid #22d3ee; '
        'padding:8px 10px; border-radius:6px;">本章节由 env_demo.py '
        "动态追加，禁用该插件并重启后消失。</div>",
    )

    app.toast("v3 演示插件已加载：新环境、按钮与教程章节已就绪")
