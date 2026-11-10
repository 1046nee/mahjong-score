# -*- coding: utf-8 -*-
"""この手の待ちは？（14本・w-01〜14）。blog-machi-dojo.html の練習問題から自動で作る（2026-11-10）。
問題 → 5秒考える → 答え（待ちの牌と残り枚数）→ それぞれの牌が来たときの分け方 → 記事へ
"""
import io, os, re
from video_topics import esc, head, stage, hook, tile, article_end, MJ, _chunks
import video_topics3  # noqa
from video_topics_yougo import tiles, note

TOPICS = {}
LV = {}

def _codes(x):
    return re.findall(r"/assets/tiles/([a-z0-9-]+)\.svg", x)

def _problems():
    s = io.open(os.path.join(MJ, "blog-machi-dojo.html"), encoding="utf-8").read()
    out = []
    lv = ""
    for m in re.finditer(r'<h3 class="dj-lv">(.*?)</h3>|<div class="dj-q" id="q(\d+)">(.*?)</details>', s, re.S):
        if m.group(1):
            lv = re.sub(r"<[^>]+>", "", m.group(1)); continue
        blk = m.group(3)
        hand = _codes(re.search(r'<div class="dj-hand".*?</div>', blk, re.S).group(0))
        waits = _codes(re.search(r'<span class="dj-wt">(.*?)</span>', blk, re.S).group(1))
        summ = re.sub(r"<[^>]+>", "", re.search(r'<p class="dj-w">.*?</span>(.*?)</p>', blk, re.S).group(1)).strip()
        paras = re.findall(r"<p>(.*?)</p>", blk, re.S)
        expl = re.sub(r"<rt>.*?</rt>|<[^>]+>", "", paras[0]).strip() if paras else ""
        splits = []
        for li in re.findall(r"<li>(.*?)</li>", blk, re.S):
            name = re.sub(r"<[^>]+>", "", re.search(r"<b>(.*?)</b>", li).group(1))
            groups = []
            for g in re.findall(r'<span class="dj-grp[^"]*">(.*?)</span>(?=<span class="dj-grp|$)', li + "", re.S):
                win = _codes("".join(re.findall(r'<span class="w">(.*?)</span>', g, re.S)))
                groups.append((_codes(g), win[0] if win else None))
            splits.append((name, groups))
        out.append(dict(no=int(m.group(2)), lv=lv, hand=hand, waits=waits, summ=summ, expl=expl, splits=splits))
    return out

def _split_row(name, groups, w=46):
    out = ""
    for cs, win in groups:
        out += '<span style="display:inline-flex;gap:2px;margin-right:12px">'
        used = False
        for c in cs:
            if win and c == win and not used:
                out += f'<span style="display:inline-block;background:#E75620;border-radius:8px;padding:3px">{tile(c, w)}</span>'; used = True
            else:
                out += tile(c, w)
        out += "</span>"
    return (f'<div style="display:flex;align-items:center;gap:14px;height:{round(w * 1.6)}px;border-top:2px solid #E3E9E7">'
            f'<span style="width:110px;font-size:34px;font-weight:900;color:#E75620;white-space:nowrap">{esc(name)}</span><span style="display:flex;align-items:flex-end">{out}</span></div>')

def _say_tiles(s):
    return s.replace("・", "、")

def _quiz(p, n):
    hand = tiles(p["hand"], 66)
    cnt = re.search(r"（(.*?)）", p["summ"])
    kinds = cnt.group(1) if cnt else ""
    names = re.sub(r"（.*?）", "", p["summ"])
    def think(a, b):
        return [head(a, b, f"第{p['no']}問　{p['lv']}"), stage(a + .1, b, hand, top=420),
                stage(a + .4, b, f'<div class="mid"><div class="big" data-nums="{a + .5},{b - .2},5,0,0" data-post="秒">5秒</div></div>', top=640),
                stage(a + .6, b, note("待ちの牌を<b>全部</b>答えてください"), top=900)]
    def ans(a, b):
        return [head(a, b, "答え"), stage(a + .1, b, hand, top=380),
                stage(a + .4, b, '<div class="mid">' + "".join(f'<span style="display:inline-block;margin:0 8px;outline:7px solid #E75620;outline-offset:3px;border-radius:10px">{tile(c, min(96, 860 // len(p["waits"]) - 20))}</span>' for c in p["waits"]) + "</div>", top=580, anim="pop"),
                stage(a + 1.0, b, f'<div class="note">{esc(names)}<br><b>{esc(kinds)}</b></div>', top=820)]
    def why(a, b):
        rows = "".join(_split_row(nm, gs, 44 if max(sum(len(c) for c, _ in gs) for _, gs in p["splits"]) > 10 else 50) for nm, gs in p["splits"])
        return [head(a, b, "分け方"), stage(a + .1, b, f'<div class="tbl" style="padding:10px 26px">{rows}</div>', top=360),
                stage(a + .6, b, note("オレンジが<b>あがり牌</b>"), top=380 + len(p["splits"]) * 84 + 60)]
    expl = _chunks(p["expl"])[:5]
    return [(["この手の待ち、", "全部わかる？", f"第{p['no']}問です。"], hook(f"待ち当て {p['no']}/{n}", "この手の待ちは？", hand, g=False)),
            (["待ちの牌を、全部答えてください。", "5秒で考えてみましょう。"], think),
            ([f"答えは、{_say_tiles(names)}。", f"{kinds.replace('・', '、')}です。"], ans),
            (expl, why),
            (["14問の練習問題は、", "まじゃすこの記事で。"], article_end("blog-machi-dojo", "14問は記事で"))]

_P = _problems()
for _p in _P:
    TOPICS[f"w-{_p['no']:02d}"] = (lambda p=_p: _quiz(p, len(_P)))
