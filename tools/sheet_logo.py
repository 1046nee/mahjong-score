# -*- coding: utf-8 -*-
"""1枚の表（点数早見表・役一覧・確認リストなど）の見出しの右上に置く、まじゃすこのロゴ（2026-11-12〜・ユーザーの指定）。
白い角丸の札に assets/logo.png をのせる。新しく1枚の表を作るときも、見出しに logo_html() を入れる"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_CSS = (".logo-pill { background: #fff; border-radius: 10px; padding: 5px 10px; line-height: 0; flex-shrink: 0; }"
            " .logo-pill img { height: 38px; width: auto; }"
            " header .legend { margin-left: auto; margin-right: 10px; }")


def logo_html(h=None):
    src = "file:///" + os.path.join(ROOT, "assets", "logo.png").replace("\\", "/")
    st = f' style="height:{h}px"' if h else ""
    return f'<span class="logo-pill"><img src="{src}" alt="まじゃすこ"{st}></span>'
