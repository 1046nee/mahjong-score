# -*- coding: utf-8 -*-
"""記事の中の中国語由来の麻雀用語に、ふりがな（<ruby>）を付ける（2026-10-23〜・ユーザーの依頼「中国語由来のものには基本フリガナ」）。
- 1つの記事の中で、それぞれの言葉の**最初の1回だけ**に付ける（何度も付けると読みにくい）
- 本文（<article class="blog-post"> の中）だけ。見出し（h1・h2）、目次、図（svg）、script、すでに ruby の中、タグの属性は対象外
- 長い言葉を先に探す（「四家立直」の中の「立直」には付けない）。すぐ後ろに「（…）」で読みが書いてある所には付けない
- 読みは Wikipedia の各項目と、正式名称のページ（blog-mahjong-yougo.html）で確かめたもの
実行: python tools/add_ruby.py            （blog-*.html をまとめて。何度実行しても同じ結果）
      python tools/add_ruby.py blog-xxx.html
"""
import glob, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 「対面（ふつうの意味の“会って向かい合う”）」「平和（ふつうの意味の“へいわ”）」は記事でふつうの言葉としても使うので自動では付けない
SKIP_FILES = {"blog-mahjong-yougo.html", "blog-mahjong-yougoshu.html", "blog-mahjong-kanji.html"}  # 読み方を一覧で見せるページ（暗記モードがある・字の意味の記事は手でルビを振っている）

READ = {
 # 牌
 "萬子": "マンズ", "筒子": "ピンズ", "索子": "ソーズ", "数牌": "シュウパイ", "字牌": "ジハイ", "風牌": "フォンパイ", "三元牌": "サンゲンパイ",
 "么九牌": "ヤオチューハイ", "中張牌": "チュンチャンパイ", "役牌": "ヤクハイ", "場風": "バカゼ", "自風": "ジカゼ",
 # 山と卓
 "洗牌": "シーパイ", "砌牌": "チーパイ", "壁牌": "ピーパイ", "幢": "トン", "開門": "カイメン", "配牌": "ハイパイ", "王牌": "ワンパイ",
 "嶺上牌": "リンシャンパイ", "海底牌": "ハイテイハイ", "河底牌": "ホウテイハイ", "理牌": "リーパイ", "雀荘": "ジャンソウ", "半荘": "ハンチャン",
 "東風戦": "トンプウセン", "東場": "トンバ", "南場": "ナンバ",
 # 席
 "起家": "チーチャ", "荘家": "チャンチャ", "散家": "サンチャ", "東家": "トンチャ", "南家": "ナンチャ", "西家": "シャーチャ", "北家": "ペーチャ",
 "上家": "カミチャ", "下家": "シモチャ", "他家": "ターチャ", "連荘": "レンチャン", "輪荘": "ロンチャン",
 # 動作
 "摸打": "モウダ", "自摸": "ツモ", "打牌": "ダハイ", "和了": "ホーラ", "栄和": "ロンホー", "副露": "フーロ", "暗槓": "アンカン", "大明槓": "ダイミンカン",
 "加槓": "カカン", "明槓": "ミンカン", "立直": "リーチ", "聴牌": "テンパイ", "不聴": "ノーテン", "振聴": "フリテン", "形式聴牌": "ケイシキテンパイ",
 "搶槓": "チャンカン", "槍槓": "チャンカン",
 # 流局・反則
 "荒牌平局": "ホワンパイピンチュー", "九種九牌": "キュウシュキュウハイ", "四風連打": "スーフーレンダ", "四家立直": "スーチャリーチ",
 "四開槓": "スーカイカン", "三家和": "サンチャホー", "錯和": "チョンボ", "多牌": "ターハイ", "少牌": "ショウハイ",
 # 手の形・点数
 "面子": "メンツ", "順子": "シュンツ", "刻子": "コーツ", "槓子": "カンツ", "雀頭": "ジャントウ", "対子": "トイツ", "搭子": "ターツ",
 "多面張": "タメンチャン", "三面張": "サンメンチャン", "両面": "リャンメン", "嵌張": "カンチャン", "辺張": "ペンチャン", "単騎": "タンキ", "双碰": "シャンポン", "門前": "メンゼン",
 "翻": "ハン", "飜": "ハン", "満貫": "マンガン", "跳満": "ハネマン", "倍満": "バイマン", "三倍満": "サンバイマン", "役満": "ヤクマン",
 # 役
 "断么九": "タンヤオ", "一盃口": "イーペーコー", "二盃口": "リャンペーコー", "七対子": "チートイツ", "対々和": "トイトイホー",
 "混一色": "ホンイツ", "清一色": "チンイツ", "国士無双": "コクシムソウ", "四暗刻": "スーアンコー", "三暗刻": "サンアンコー", "大三元": "ダイサンゲン",
 "小三元": "ショウサンゲン", "一気通貫": "イッキツウカン", "三色同順": "サンショクドウジュン", "三色同刻": "サンショクドウコー",
 "混全帯么九": "ホンチャンタイヤオチュー", "純全帯么九": "ジュンチャンタイヤオチュー", "混老頭": "ホンロウトウ", "清老頭": "チンロウトウ",
 "海底摸月": "ハイテイモーユエ", "河底撈魚": "ホウテイラオユイ", "嶺上開花": "リンシャンカイホウ", "門前清自摸和": "メンゼンチンツモホー",
 "一発": "イッパツ", "字一色": "ツーイーソー", "緑一色": "リューイーソー", "小四喜": "ショウスーシー", "大四喜": "ダイスーシー",
 "四槓子": "スーカンツ", "三槓子": "サンカンツ", "九蓮宝燈": "チューレンポウトウ", "天和": "テンホー", "地和": "チーホー",
}
TERMS = sorted(READ, key=len, reverse=True)
PAT = re.compile("|".join(map(re.escape, TERMS)))
SKIP_TAGS = {"h1", "h2", "script", "style", "svg", "ruby", "title", "button", "textarea"}
TOKEN = re.compile(r"(<!--.*?-->|<[^>]+>)", re.S)


def add_ruby(article):
    seen, stack, out = set(), [], []
    for part in TOKEN.split(article):
        if not part:
            continue
        if part.startswith("<"):
            m = re.match(r"<\s*(/)?\s*([a-zA-Z0-9]+)", part)
            if m:
                tag = m.group(2).lower()
                closing = bool(m.group(1))
                self_close = part.rstrip().endswith("/>") or tag in ("img", "br", "hr", "meta", "link", "input", "source", "image", "line", "rect", "circle", "path")
                cls = re.search(r'class="([^"]*)"', part)
                if closing:
                    if any(t == tag for t, _ in stack):
                        while stack and stack.pop()[0] != tag:
                            pass
                elif not self_close:
                    skip = tag in SKIP_TAGS or bool(cls and "post-toc" in cls.group(1))
                    stack.append((tag, skip))
            out.append(part)
            continue
        if any(sk for _, sk in stack):
            out.append(part)
            continue

        def rep(m, text=part):
            t = m.group(0)
            if t in seen:
                return t
            if text[m.end():m.end() + 1] in ("（", "("):  # すぐ後ろに「（読み）」が書いてあるところには付けない
                return t
            seen.add(t)
            return f"<ruby>{t}<rt>{READ[t]}</rt></ruby>"
        out.append(PAT.sub(rep, part))
    return "".join(out)


def process(path):
    s = io.open(path, encoding="utf-8").read()
    a = s.find('<article class="blog-post">')
    b = s.find("</article>", a)
    if a < 0 or b < 0:
        return False
    a += len('<article class="blog-post">')
    body = s[a:b]
    plain = re.sub(r"<ruby>(.*?)<rt>.*?</rt></ruby>", r"\1", body)  # いったん外して付け直す（何度実行しても同じ）
    new = add_ruby(plain)
    if new == body:
        return False
    io.open(path, "w", encoding="utf-8", newline="").write(s[:a] + new + s[b:])
    return True


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "blog-*.html")))
    n = 0
    for f in files:
        if os.path.basename(f) in SKIP_FILES:
            continue
        if process(f):
            n += 1
            print("ふりがな", os.path.basename(f))
    print(n, "ページ")
