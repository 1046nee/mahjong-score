# -*- coding: utf-8 -*-
"""blog-naki-tejun.html を作る（鳴きの手順の記事）。ひな形は blog-kuikae.html。"""
import re, json, os
ROOT = "/home/user/mahjong-score"
tpl = open(os.path.join(ROOT, "blog-kuikae.html"), encoding="utf-8").read()

SLUG = "blog-naki-tejun"
TITLE = "【図解】ポン・チーの手順｜発声から打牌までの順番とMリーグ・プロ団体の決まりの違い"
DESC = "ポン・チーは「発声→晒す→取る→右端に並べる→打牌」。上から見た卓の図で5つの手順を1つずつ。Mリーグ・日本プロ麻雀協会・最高位戦・RMUの公式ルールで、横にする牌の位置・チーの間合い・先に切ったときの扱いがどう違うかを比べ、仲間内と雀荘での気をつけ方もまとめました。"
OGD = "鳴きの5つの手順を、上から見た卓の図で。団体ごとの決まりの違いも。"
DATE = "2026.11.11"

def T(code, x, y, w, rot=0, op=1.0):
    """卓の図の牌（まじゃすこの牌の絵）。rot=90 で横向き"""
    yoko = rot in (90, 270)
    f = f"{code}-yoko" if yoko else code
    h = w * (69 / 82 if yoko else 89 / 62)
    ww = w * (82 / 62) if yoko else w
    return f'<image href="/assets/tiles/{f}.svg" x="{x:.1f}" y="{y:.1f}" width="{ww:.1f}" height="{h:.1f}" opacity="{op}"/>'

def board(step):
    """上から見た卓。自分は下。上家（左の人）の河の最後の六萬をチーする。step=1〜5"""
    W = 320
    g = [f'<rect x="6" y="6" width="{W-12}" height="{W-12}" rx="22" fill="#E4F3EC" stroke="#9fc3bd" stroke-width="2"/>']
    tw = 20
    th = tw * 89 / 62
    # 上家の河（左。牌は上家の向き＝90度回す）。最後が六萬
    riv_left = ["z1", "m9", "p2", "s8", "z3", "m6"]
    lx, ly = 62, 52
    for i, c in enumerate(riv_left):
        hl = (i == 5)
        if hl and step >= 3:
            continue
        cx, cy = lx + th / 2, ly + i * (tw + 2) + tw / 2
        g.append(f'<g transform="rotate(90 {cx:.1f} {cy:.1f})">' + T(c, cx - tw / 2, cy - th / 2, tw, op=1 if hl else .5) + "</g>")
    hy = ly + 5 * (tw + 2)
    if step < 3:
        g.append(f'<rect x="{lx-3}" y="{hy-3}" width="{th+6:.0f}" height="{tw+6}" rx="5" fill="none" stroke="#E75620" stroke-width="3"/>')
    else:
        g.append(f'<rect x="{lx-1}" y="{hy-1}" width="{th+2:.0f}" height="{tw+2}" rx="4" fill="none" stroke="#9fc3bd" stroke-width="1.5" stroke-dasharray="3 3"/>')
    # 自分の河
    my_riv = ["z2", "m1", "p8"] + (["s3"] if step >= 5 else [])
    rx, ry = 122, 196
    for i, c in enumerate(my_riv):
        g.append(T(c, rx + i * (tw + 2), ry, tw, op=1 if (step >= 5 and i == 3) else .5))
    if step >= 5:
        g.append(f'<rect x="{rx + 3 * (tw + 2) - 3}" y="{ry - 3}" width="{tw + 6}" height="{th + 6:.0f}" rx="5" fill="none" stroke="#E75620" stroke-width="3"/>')
    # 自分の手牌
    hand = ["m4", "m5", "p3", "p4", "p6", "p7", "s3", "s5", "s6", "s7", "z7", "z7", "p9"]
    hw = 16; hx = 14; hyy = 272; k = 0
    for c in hand:
        if step >= 2 and c in ("m4", "m5"): continue
        if step >= 5 and c == "s3": continue
        g.append(T(c, hx + k * (hw + 1), hyy, hw)); k += 1
    if step == 1:
        g.append(f'<rect x="{hx-3}" y="{hyy-4}" width="{2*(hw+1)+4}" height="31" rx="5" fill="none" stroke="#177083" stroke-width="2.5" stroke-dasharray="4 3"/>')
    # 晒した牌・副露（右下の隅）
    mx, my = 246, 272
    if step >= 2:
        if step >= 3:
            g.append(T("m6", mx - 22, my + 4, hw, rot=90))
        g.append(T("m4", mx, my, hw)); g.append(T("m5", mx + hw + 1, my, hw))
        x0 = mx - (26 if step >= 3 else 4)
        g.append(f'<rect x="{x0}" y="{my-5}" width="{mx + 2*(hw+1) + 3 - x0}" height="33" rx="6" fill="none" stroke="#E75620" stroke-width="2.5" {"" if step >= 4 else 'stroke-dasharray="4 3"'}/>')
    def arrow(x1, y1, x2, y2, col="#E75620", lift=34):
        return (f'<path d="M{x1} {y1} Q {(x1+x2)/2} {min(y1,y2)-lift} {x2} {y2}" fill="none" stroke="{col}" stroke-width="3.5" stroke-linecap="round" marker-end="url(#ah{col[1:]})"/>')
    if step == 2: g.append(arrow(32, 266, 262, 264, "#177083", 40))
    if step == 3: g.append(arrow(lx + th + 6, hy + 14, mx - 12, my - 6, lift=10))
    if step == 5: g.append(arrow(120, 268, rx + 3 * (tw + 2) + 4, ry + th + 8, lift=-6))
    defs = ("<defs>" + "".join(f'<marker id="ah{c}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#{c}"/></marker>' for c in ("E75620", "177083")) + "</defs>")
    seats = ('<text x="160" y="26" text-anchor="middle" font-size="12" font-weight="800" fill="#5F6E6B">対面</text>'
             '<text x="26" y="150" text-anchor="middle" font-size="12" font-weight="800" fill="#5F6E6B">上家</text>'
             '<text x="294" y="150" text-anchor="middle" font-size="12" font-weight="800" fill="#5F6E6B">下家</text>'
             '<text x="160" y="312" text-anchor="middle" font-size="11" font-weight="800" fill="#177083">自分</text>')
    call = ('<rect x="104" y="232" width="112" height="28" rx="14" fill="#E75620"/><text x="160" y="251" text-anchor="middle" font-size="15" font-weight="900" fill="#fff">チー！</text>') if step == 1 else ""
    return f'<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg" role="img" class="nk-board">{defs}{"".join(g)}{seats}{call}</svg>'

STEPS = [
    ("声を出す", "「チー」「ポン」と、卓の全員に聞こえる声で言う。上家の牌に「チー」は、ポンやロンがないか一拍待ってから"),
    ("手の牌を晒す", "鳴くのに使う手の中の2枚（チーなら四萬・五萬）を、表にして見せる"),
    ("相手の牌を取る", "相手の河から、鳴いた牌（六萬）を取ってきて、晒した2枚と組にする"),
    ("右端に並べる", "できた組を、自分の前の右の隅に置く。鳴いた牌は横向きにして、誰から鳴いたかを示す"),
    ("1枚切る", "最後に手牌から1枚を河に切る。この打牌で鳴きが完了する"),
]

def tiles_row(codes, w=26):
    out = ""
    for c in codes:
        yoko = c.endswith("-yoko")
        ww = round(w * 82 / 62) if yoko else w
        out += f'<img src="/assets/tiles/{c}.svg" alt="" width="{ww}" class="nk-t{" y" if yoko else ""}" loading="lazy" decoding="async">'
    return f'<span class="nk-row">{out}</span>'

steps_fig = '<figure class="fg nk-steps" id="fg-naki-steps"><p class="fg-ttl">上から見た卓で、チーの5つの手順</p><ol class="nk-grid">' + "".join(
    f'<li><div class="nk-num">{i + 1}</div><b>{t}</b>{board(i + 1)}<small>{d}</small></li>' for i, (t, d) in enumerate(STEPS)) + \
    '</ol><figcaption>自分は下の席。上家（左の人）が切った六萬を、手の四萬・五萬でチーする例。オレンジの枠が、その手順で動く牌</figcaption></figure>'

pon_fig = ('<figure class="fg nk-pon" id="fg-naki-pon"><p class="fg-ttl">ポンは「誰から鳴いたか」で横にする牌が変わる（Mリーグ）</p><ul class="nk-list">'
           f'<li><span class="nk-who">上家から</span>{tiles_row(["p5-yoko", "p5", "p5"])}<span class="nk-why">左の牌を横に</span></li>'
           f'<li><span class="nk-who">対面から</span>{tiles_row(["p5", "p5-yoko", "p5"])}<span class="nk-why">真ん中を横に</span></li>'
           f'<li><span class="nk-who">下家から</span>{tiles_row(["p5", "p5", "p5-yoko"])}<span class="nk-why">右の牌を横に</span></li>'
           '</ul><figcaption>横にした牌が、鳴いた相手の方向を指す。チーは上家からしかできないので、横向きの牌はいつも左</figcaption></figure>')

chi_fig = ('<figure class="fg nk-chi" id="fg-naki-chi"><p class="fg-ttl">チーの並べ方は、団体で書き方が少し違う</p><ul class="nk-list">'
           f'<li><span class="nk-who">Mリーグ</span>{tiles_row(["m6-yoko", "m4", "m5"])}<span class="nk-why">鳴いた牌を横にして、晒した2枚の左に</span></li>'
           f'<li><span class="nk-who">最高位戦</span>{tiles_row(["m6-yoko", "m5", "m4"])}<span class="nk-why">鳴いた牌を左に横向き。晒した2枚の順序は問わない</span></li>'
           '</ul><figcaption>どちらも「鳴いた牌は左・横向き」は同じ。最高位戦は、晒した2枚の並び順までは決めていない</figcaption></figure>')

order_fig = ('<figure class="fg nk-order" id="fg-naki-order"><p class="fg-ttl">2回鳴いたら、どこに置く？</p><div class="nk-two">'
             f'<div class="nk-stack"><span class="nk-lab">2回目</span>{tiles_row(["z7", "z7-yoko", "z7"])}<span class="nk-lab">1回目</span>{tiles_row(["m6-yoko", "m4", "m5"])}</div>'
             '<p>右の隅に、<b>鳴いた順に手前から奥へ</b>縦に並べる（Mリーグ・日本プロ麻雀協会）。最高位戦は「右側の縁に沿って下から上へ」と書いていて、置き方は同じ</p></div></figure>')

CMP = [
    ("Mリーグ", "発声 → 晒す → 右側へ副露 → 打牌", "（優先はアガリ＞ポン・カン＞チー。遅い発声は審判の裁定）", "鳴いた牌を横にして、晒した2枚の左", "右の隅に、手前から奥へ縦に", "指示牌の間違いは全員の同意で訂正"),
    ("日本プロ麻雀協会", "発声 → 晒す → 右側へ副露 → 打牌", "ポン・カン・ロンがないのを確かめて「チー」", "チーした牌を横向き", "右の隅に、手前から奥へ縦に", "空チー・錯チー（晒し間違い）はアガリ放棄"),
    ("最高位戦", "発声 → 晒す → 右端に並べる → 打牌", "ツモを始めるのと同じタイミングで「チー」", "鳴いた牌を左に横向き（2枚の順序は問わない）", "右の縁に沿って、下から上へ縦に", "晒す前に打牌・晒し間違えたまま打牌は和了放棄"),
    ("RMU", "発声 → 晒す → 河から持ってくる → 打牌", "1拍おいてから「チー」", "（ルールのページに書かれていない）", "（ルールのページに書かれていない）", "誤った牌を晒して打牌・発声だけで打牌しないはアガリ放棄"),
]
cmp_tbl = ('<table class="nk-cmp"><thead><tr><th>決まり</th><th>手順の順番</th><th>チーを言うとき</th><th>チーの横向きの牌</th><th>並べる場所</th><th>まちがえたら</th></tr></thead><tbody>'
           + "".join(f"<tr><th>{a}</th><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td><td>{f}</td></tr>" for a, b, c, d, e, f in CMP) + "</tbody></table>")

BODY = f'''
  <h1>{TITLE}</h1>
  <p class="post-meta">{DATE}</p>

  <figure class="eyecatch"><img src="/assets/thumbs/{SLUG}.webp" alt="上から見た卓で、チーの手順を示した図" width="320" height="240" fetchpriority="high"></figure>

  <div class="post-ans"><p class="pa-h">この記事の結論</p><ul><li>ポン・チーは<strong>「声を出す → 手の牌を晒す → 相手の牌を取る → 右端に並べる → 1枚切る」</strong>の順。Mリーグもプロ団体も、公式ルールの順番は同じ</li><li>違うのは<strong>横にする牌の位置・チーを言う間合い・先に切ったときの罰</strong>。最高位戦は「晒す前の打牌」をはっきり反則にしている</li><li>仲間内なら気楽でいいが、<strong>雀荘や大会では、その場の決まりに合わせる</strong></li></ul></div>
  <div class="post-toc"><b>この記事でわかること</b><a href="#tejun">5つの手順</a><a href="#hikaku">団体の違い</a><a href="#narabe">並べ方</a><a href="#machigai">よくある間違い</a><a href="#janso">雀荘では</a><a href="#nakama">仲間内では</a></div>

  <p>ポンやチーをするとき、声を出してから、手の牌を見せて、相手の牌を取って、右に寄せて、1枚切る。毎回やっている動きですが、<strong>順番を説明して</strong>と言われると、意外と迷います。「先に切ってから牌を取る人」「声と同時に牌を倒す人」など、仲間内では人によってやり方がばらばらです。</p>
  <p>この記事では、まず<strong>上から見た卓の図で5つの手順</strong>を1つずつ追い、そのあと<strong>Mリーグとプロ団体の公式ルールが何を決めているか</strong>を比べます。最後に、雀荘や大会など「外で打つとき」に気をつけたいことをまとめました。</p>

  <div class="ad-slot" data-ad="article_top"></div>

  <h2 id="tejun">鳴きの5つの手順</h2>
  <p>例は、自分の上家（左に座っている人）が切った六萬を、手の中の四萬・五萬で<strong>チー</strong>する場面です。ポンや大明槓でも、流れは同じです。</p>
  {steps_fig}
  <h3>1. 声を出す</h3>
  <p>「チー」「ポン」「カン」は、<strong>卓の全員に聞こえる声</strong>で言います。日本プロ麻雀協会と最高位戦の規定は「明確に」「同卓者全員が聞き取れる」ことを求めています。チーは上家の牌にしかできず、しかも<strong>ポン・カン・ロンより優先順位が低い</strong>ので、ほかの人の声がないかを一拍待ってから言うのが基本です。RMUのルールは「1拍おいて発声する」と書いています。</p>
  <h3>2. 手の牌を晒す</h3>
  <p>次に、鳴くのに使う<strong>手の中の牌を表にして見せます</strong>。チーなら2枚、ポンなら2枚、大明槓なら3枚です。ここで、どの組で鳴いたのかが全員に分かります。Mリーグと日本プロ麻雀協会のルールは、どちらも「発声のあと、手中の搭子（対子）を開示し」と、声のすぐあとに晒すことを書いています。</p>
  <h3>3. 相手の牌を取る</h3>
  <p>相手の河から、鳴いた牌を取ってきます。RMUのルールは「発声の後に関連する手牌をさらし、<strong>河から牌を持ってきた後</strong>打牌を行う」と、晒す→取る→切るの順番をそのまま書いています。</p>
  <h3>4. 右端に並べる</h3>
  <p>晒した牌と取った牌を組にして、<strong>自分の前の右の隅</strong>に置きます。鳴いた牌は横向きにして、誰から鳴いたかが分かるようにします。横向きの位置は、次の章の図で説明します。</p>
  <h3>5. 1枚切る</h3>
  <p>最後に、手牌から1枚を河に切ります。Mリーグのルールは、打を「チー・ポン・カンの行為完了後に任意の牌を1枚捨てる行為」と書いていて、<strong>鳴きの動作がすべて終わってから切る</strong>のが正式な順番です。最高位戦の規定は、この打牌で「吃（碰）の成立とする」としています。</p>

  <h2 id="hikaku">Mリーグと団体の決まりを比べる</h2>
  <p>公式ルールで鳴きの手順まで書いているのは、Mリーグ・日本プロ麻雀協会・最高位戦・RMUです（2026年11月に各公式サイトで確認）。<strong>手順の順番そのものは4つとも同じ</strong>で、違いは細かいところに出ます。</p>
  <div class="table-scroll">{cmp_tbl}</div>
  <p>日本プロ麻雀連盟は、公式サイトの「競技ルール」のページに本文が表示されず、文章では確かめられませんでした。麻将連合も、公式サイトで鳴きの手順の決まりを確かめられていません。確かめられたら、この表に足します。</p>
  <h3>違い1：チーを言う間合い</h3>
  <p>同じ牌にポンとチーの声が重なったら、どのルールでも<strong>ポンが優先</strong>です。そのため、チーを言うタイミングに決まりを置いている団体があります。日本プロ麻雀協会は「ポン・カン・ロンがないことを確認」してから、RMUは「1拍おいて」、最高位戦は「ツモを始めるのと同じタイミングで」チーと言う、と書いています。最高位戦の規定は、ポンにも「上家の打牌に対しては間をおいても良い」と書いており、上家の牌は少し考えてよい、という扱いです。</p>
  <h3>違い2：先に切ってしまったときの扱い</h3>
  <p>いちばん差が出るのがここです。最高位戦の規定は、罰則の一覧に<strong>「副露時、開示前の打牌」</strong>と<strong>「晒し間違えたまま打牌」</strong>をはっきり挙げ、どちらも和了放棄（その局はあがれない）にしています。つまり<strong>晒す前に切ると反則</strong>です。RMUと日本プロ麻雀協会は、晒し間違えて打牌した場合（錯行為）をアガリ放棄にしています。</p>
  <p>仲間内でよく見る「声を出して、先に1枚切ってから、相手の牌を取って右に寄せる」流れは、この順番から外れています。最後の形は同じに見えても、<strong>プロのルールでは手順の順番まで見られている</strong>ということです。</p>

  <h2 id="narabe">横にする牌と、並べ方</h2>
  {pon_fig}
  <p>ポンは、上家から鳴いたら左、対面からなら真ん中、下家からなら右の牌を横にします（Mリーグ）。横にした牌が、鳴いた相手の方向を指す、と覚えると迷いません。大明槓は、Mリーグでは対面からのとき「左から2番目」を横にします。</p>
  {chi_fig}
  {order_fig}
  <p>鳴いた組は、2つ目からは<strong>1つ目の奥</strong>に置きます。手前に置くと、あとから見たときに鳴いた順番が分からなくなります。</p>

  <h2 id="machigai">よくある間違い</h2>
  <ul class="fg-check">
    <li><strong>声と同時に手牌を倒してしまう</strong>：ポンの声が重なったときに、晒した牌を戻すことになり、手の中が見えてしまう。声を出してから晒す</li>
    <li><strong>先に切ってから牌を取る</strong>：最高位戦では「開示前の打牌」で和了放棄。晒す→取る→切るの順に</li>
    <li><strong>横向きの位置がちがう</strong>：Mリーグは、間違えたまま進んでも、その局のうちに全員の同意があれば直せる</li>
    <li><strong>鳴いた組を手牌の近くに置く</strong>：手牌と混ざって見える。右の隅に、少し離して置く</li>
    <li><strong>喰い替えになる牌を切る</strong>：鳴いた直後に、鳴いた牌とつながる牌は切れない（<a href="/blog-kuikae.html">喰い替え</a>）</li>
  </ul>

  <h2 id="janso">雀荘や大会で打つときは</h2>
  <p>雀荘や大会には、<strong>そのお店・その大会の決まり</strong>があります。鳴きの手順や、まちがえたときの扱い（アガリ放棄か、チョンボか、注意だけか）は、お店のルール表や受付の説明で決まっていることが多いので、初めてのお店では<strong>打つ前に一度目を通しておく</strong>と安心です。</p>
  <ul>
    <li><strong>声ははっきり</strong>：知らない人と打つときほど、聞き取れない発声はトラブルのもとになる</li>
    <li><strong>順番どおりに、ゆっくり</strong>：声 → 晒す → 取る → 右に並べる → 切る。急いで崩すより、1つずつ見せるほうが相手も確認しやすい</li>
    <li><strong>まちがえたら、すぐ言う</strong>：直せる範囲はお店の決まり次第。自分で直さず、店員さんを呼ぶ</li>
  </ul>
  <p>マナー全体は「<a href="/blog-manner.html">麻雀のマナー</a>」にまとめています。</p>

  <h2 id="nakama">仲間内で打つときは</h2>
  <p>いつもの仲間と打つなら、プロと同じ厳しさは要りません。順番が少し前後しても、<strong>全員が何を鳴いたか分かれば十分</strong>です。初心者がいる卓で「晒す前に切ったからアガリ放棄」とすると、麻雀そのものが楽しくなくなってしまいます。</p>
  <p>ただし、<strong>外で打つ予定がある人は、ふだんから正しい順番で鳴いておく</strong>のがおすすめです。手が覚えた順番は、緊張する場面でもそのまま出ます。決めておくと揉めない細かいルールは「<a href="/blog-house-rules.html">打つ前に決める10項目</a>」「<a href="/blog-rule-wakareme.html">麻雀ルールの分かれ目</a>」にあります。</p>

  <h2 id="shukei">集計係の目線</h2>
  <p>鳴きの手順をまちがえてアガリ放棄になっても、その局で点数のやり取りが起きるわけではありません。<ruby>半荘<rt>ハンチャン</rt></ruby>のスコアは最後の持ち点で決まるので、まじゃすこには<strong>いつもどおり最後の持ち点を入れるだけ</strong>です。チョンボにする決まりのときだけ、チョンボの罰（スコアから引く）を入れます。仲間内でどちらにするかは、打つ前に決めておきましょう。</p>

  <h2>よくある質問</h2>
  <h3>Q. 声を出したあと、やっぱり鳴くのをやめてもいいですか？</h3>
  <p>A. 多くのルールでは、声だけ出して鳴かないのは「空ポン・空チー」という反則です。日本プロ麻雀協会・RMUはアガリ放棄にしています。ただし、同時に声が出て、優先されなかったチーは空チーになりません（Mリーグ・日本プロ麻雀協会）。</p>
  <h3>Q. 取った牌を手牌に入れてしまったら？</h3>
  <p>A. 鳴いた牌は、晒した牌と一緒に右端に並べるのが決まりです。手に入れてしまうと、どの牌で鳴いたのか分からなくなります。気づいたらすぐに申し出て、その場の決まりに従いましょう。</p>
  <h3>Q. 右端に並べるとき、どれくらい手牌から離せばいいですか？</h3>
  <p>A. 決まった距離はありませんが、手牌と混ざって見えない程度に離します。2つ目からは1つ目の奥に縦に並べるので、右の隅に少し余裕を取っておくと置きやすくなります。</p>

  <h2>まとめ</h2>
  <ul>
    <li>鳴きの順番は「声を出す → 手の牌を晒す → 相手の牌を取る → 右端に並べる → 1枚切る」</li>
    <li>Mリーグ・日本プロ麻雀協会・最高位戦・RMUの公式ルールで、順番は同じ</li>
    <li>違いはチーを言う間合い・横向きの牌の書き方・まちがえたときの罰。最高位戦は晒す前の打牌を反則にしている</li>
    <li>仲間内は気楽に。雀荘や大会では、その場の決まりに合わせる</li>
  </ul>
  <p style="font-size:13px;color:#5F6E6B">出典：<a href="https://m-league.jp/about/" target="_blank" rel="noopener">Mリーグ 公式戦ルール</a>（第4章 競技の詳細）／<a href="https://npm2001.com/about/regulations/" target="_blank" rel="noopener">日本プロ麻雀協会 競技規定</a>／<a href="https://saikouisen.com/pdf/saikouisen_regulation.pdf" target="_blank" rel="noopener">最高位戦日本プロ麻雀協会 競技規定</a>（2024年12月5日改定）／<a href="https://rmu.jp/rule" target="_blank" rel="noopener">RMU ルール</a>／Wikipedia「<a href="https://ja.wikipedia.org/wiki/副露" target="_blank" rel="noopener">副露</a>」。2026年11月に確認した内容です。</p>
'''

CSS = '''
.nk-grid { list-style: none; padding: 0 !important; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 14px; }
.nk-grid li { margin: 0 !important; background: #FAFCFB; border-radius: 12px; padding: 10px 10px 12px; position: relative; }
.nk-grid li b { display: block; font-size: 15px; color: #177083; margin: 0 0 4px 34px; line-height: 26px; }
.nk-num { position: absolute; left: 10px; top: 10px; width: 26px; height: 26px; border-radius: 50%; background: #E75620; color: #fff; font-weight: 900; font-size: 14px; line-height: 1; display: grid; place-items: center; }
.nk-board { display: block; width: 100%; height: auto; }
.nk-grid li small { display: block; font-size: 12.5px; color: #333; line-height: 1.7; margin-top: 4px; }
.nk-list { list-style: none; padding: 0 !important; margin: 0; }
.nk-list li { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; padding: 8px 4px; border-top: 1px solid #E6EEEB; margin: 0 !important; }
.nk-list li:first-child { border-top: 0; }
.nk-who { font-weight: 800; color: #177083; font-size: 14px; min-width: 5.5em; }
.nk-why { font-size: 13px; color: #333; flex: 1 1 12em; }
.nk-row { display: inline-flex; align-items: flex-end; gap: 2px; }
.nk-t { flex: none; height: auto; display: block; }
.nk-two { display: flex; flex-wrap: wrap; gap: 14px; align-items: center; }
.nk-two p { flex: 1 1 14em; margin: 0 !important; font-size: 14px; }
.nk-stack { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; background: #E4F3EC; border-radius: 10px; padding: 10px 14px; }
.nk-lab { font-size: 11px; font-weight: 800; color: #5F6E6B; }
'''

html = tpl
# head
html = re.sub(r"<title>.*?</title>", f"<title>{TITLE} | まじゃすこ</title>", html, count=1)
html = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{DESC}">', html, count=1)
html = html.replace("https://majasco.jp/blog-kuikae.html", f"https://majasco.jp/{SLUG}.html")
html = re.sub(r'(<meta property="og:title" content=")[^"]*', r"\g<1>" + TITLE, html)
html = re.sub(r'(<meta name="twitter:title" content=")[^"]*', r"\g<1>" + TITLE, html)
html = re.sub(r'(<meta property="og:description" content=")[^"]*', r"\g<1>" + OGD, html)
html = re.sub(r'(<meta name="twitter:description" content=")[^"]*', r"\g<1>" + OGD, html)
html = html.replace("/assets/og/blog-kuikae-2.png", f"/assets/og/{SLUG}.png")
ld = {"@context": "https://schema.org", "@type": "Article", "headline": TITLE, "description": DESC, "image": f"https://majasco.jp/assets/og/{SLUG}.png",
      "datePublished": "2026-11-11", "dateModified": "2026-11-11", "author": {"@type": "Person", "name": "むにぃ", "url": "https://majasco.jp/about.html"},
      "publisher": {"@type": "Organization", "name": "まじゃすこ / majasco", "logo": {"@type": "ImageObject", "url": "https://majasco.jp/assets/favicon.png"}}, "mainEntityOfPage": f"https://majasco.jp/{SLUG}.html"}
html = re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "Article".*?</script>', '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>", html, count=1, flags=re.S)
assert html.count("</style>\n<link rel=\"stylesheet\" href=\"/assets/blog.css\">") == 1
html = html.replace("</style>\n<link rel=\"stylesheet\" href=\"/assets/blog.css\">", CSS + "</style>\n<link rel=\"stylesheet\" href=\"/assets/blog.css\">")
html = html.replace("＞ 喰い替え</nav>", "＞ 鳴きの手順</nav>")
# body: h1 から 出典の段落まで差しかえ
a = html.index("  <h1>"); b = html.index('<div class="post-illust small"')
html = html[:a] + BODY.strip("\n") + "\n\n" + html[b:]
# 記事のあとに付いていた喰い替え専用の <style>（.kq）は外す
html = re.sub(r"<style>\.kq\{.*?</style>\n", "", html, count=1, flags=re.S)
html = html.replace("<p>鳴きのルールも決めたら、仲間と打ったスコアを記録しよう。</p>", "<p>鳴きの順番を覚えたら、仲間と打ったスコアを記録しよう。</p>")
open(os.path.join(ROOT, SLUG + ".html"), "w", encoding="utf-8").write(html)
print("ok", len(re.sub(r"<[^>]+>", "", BODY)))
