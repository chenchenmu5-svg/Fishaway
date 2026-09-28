# -*- coding: utf-8 -*-
"""
====================================================================
  Fish away 示例插件：快捷工具箱
--------------------------------------------------------------------
  演示真实可用的插件端口。启用并重启 Fish away 后，
  侧边栏会多出三个“示例”按钮。
====================================================================
"""
import datetime

PLUGIN_NAME = "示例：快捷工具箱"
PLUGIN_VERSION = "1.0"
PLUGIN_DESCRIPTION = (
    "Fish away 官方示例插件：演示添加侧边栏按钮、在终端执行命令、"
    "弹出消息和轻提示。可复制本文件作为你自己插件的模板。")


def setup(app):
    # 1) 在当前终端执行一条命令
    app.add_sidebar_button(
        "示例：问候",
        lambda: app.run_command("echo Hello from Fish away plugin!"))

    # 2) 轻提示（Toast）显示当前时间
    def show_time():
        now = datetime.datetime.now().strftime("%H:%M:%S")
        app.toast(f"现在是 {now}")

    app.add_sidebar_button("示例：当前时间", show_time)

    # 3) 弹出消息框
    app.add_sidebar_button(
        "示例：弹消息",
        lambda: app.show_message(
            "插件真的可以用！\n\n把你的 .py 文件放进插件目录，"
            "在设置 → 插件中启用并重启即可。"))
