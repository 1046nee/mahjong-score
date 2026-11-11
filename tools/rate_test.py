# -*- coding: utf-8 -*-
"""レート（G）の確かめ（python tools/rate_test.py）。スタブ＝本番DBに書かない。
レート（G）の表示を、チップあり／なし・レートあり／なし・途中で切る・画像・大きな数字・未参加・試合なし・チーム戦・三麻で確かめる"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from playwright.sync_api import sync_playwright
import functools, http.server, os, socketserver, tempfile, threading
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=ROOT))
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{PORT}/"

JS = r"""() => {
const R = [];
const ok = (name, cond, info) => R.push([cond ? 'PASS' : 'FAIL', name, info === undefined ? '' : String(info)]);
function mk(o) {
  const n = (o.names || ['A','B','C','D']);
  const s = Object.assign({playerNames: n, numPlayers: o.numPlayers || 4, startPoints: 25000, returnPoints: 30000, uma: o.numPlayers === 3 ? [10,0,-10] : [30,10,-10,-30], rate: 0, chipRate: 1, bonusEnabled: false, startChips: 20}, o.s || {});
  const g = {id: 'CASETESTAA', name: 'case', settings: s, rounds: []};
  (o.rounds || []).forEach(pts => { const r = {points: pts.p, members: pts.m || pts.p.map((_, i) => i)}; r.scores = calcScores(r.points, Object.assign({}, s, {numPlayers: r.points.length})); g.rounds.push(r); });
  return g;
}
const R4 = [{p: [45000, 30000, 15000, 10000]}];
const tog = g => metricToggleHtml(g.settings);
const list = (g, m) => { scoreMetric = m; const h = scoreCardsListHtml(g); return h; };
const vals = h => [...h.matchAll(/class="score-val[^"]*">([^<]*)<span[^>]*>([^<]*)<\/span>/g)].map(x => x[1] + x[2]);

// 1. レートあり・チップなし
let g = mk({s: {rate: 50}, rounds: R4});
ok('1 レートあり・チップなし: 切り替えは「スコア｜G」', tog(g).includes(">G</button>") && !tog(g).includes(">チップ</button>"));
let h = list(g, 'g');
ok('1 Gの値＝pts×50（チップは足さない）', JSON.stringify(vals(h)) === JSON.stringify(['+3,250G', '+500G', '−1,250G', '−2,500G']), vals(h));
ok('1 内訳の行は出さない（チップが無いので）', !h.includes('score-bonus'));
ok('1 設定の表示はスコアだけ', gRateLabel(g.settings) === 'スコア1pt＝50G', gRateLabel(g.settings));

// 2. レートあり・チップあり（チップの最後に入れた枚数）
g = mk({s: {rate: 50, chipRate: 100, bonusEnabled: true, finalChips: [3, -1, -2, 0]}, rounds: R4});
ok('2 切り替えは「スコア｜チップ｜G」', tog(g).includes(">チップ</button>") && tog(g).includes(">G</button>"));
h = list(g, 'g');
ok('2 G＝スコア＋チップ（合計0）', JSON.stringify(vals(h)) === JSON.stringify(['+3,550G', '+400G', '−1,450G', '−2,500G']), vals(h));
ok('2 内訳の行あり', h.includes('スコア +3,250') && h.includes('チップ +300'));

// 3. チップあり・レートなし
g = mk({s: {bonusEnabled: true, finalChips: [1, 0, 0, -1]}, rounds: R4});
ok('3 チップあり・レートなし: Gの順位は出ない', tog(g).includes(">チップ</button>") && !tog(g).includes(">G</button>"));
h = list(g, 'g');
ok('3 Gを選んでいてもスコアの順位で出す', vals(h)[0] === '+65.0pts', vals(h)[0]);

// 4. どちらもなし
g = mk({rounds: R4});
ok('4 どちらもなし: 切り替え自体を出さない', tog(g) === '');

// 5. Gを見ているあいだに他の人がレートを切った
g = mk({s: {rate: 50}, rounds: R4}); scoreMetric = 'g';
g.settings.rate = 0;
ok('5 レートを切ったらスコアの順位に戻る（中身）', vals(scoreCardsListHtml(g))[0] === '+65.0pts');
g.settings.bonusEnabled = true;
ok('5 切り替えの印もスコアに付く', /class="on"[^>]*>スコア</.test(tog(g)), tog(g).replace(/\s+/g, ' ').slice(0, 200));
// チップを切った場合
g = mk({s: {bonusEnabled: true, rate: 10}, rounds: R4}); scoreMetric = 'chips'; g.settings.bonusEnabled = false;
ok('5 チップを切ったらスコアの順位に戻る', /class="on"[^>]*>スコア</.test(tog(g)) && vals(scoreCardsListHtml(g))[0] === '+65.0pts');

// 6. 画像（総合順位・まとめ）には G を出さない・選んでいた見方は戻る
g = mk({s: {rate: 50, chipRate: 100, bonusEnabled: true, finalChips: [3, -1, -2, 0]}, rounds: R4}); scoreMetric = 'g';
const rows = imgRankingRows(g, 'score');
const flat = JSON.stringify(rows);
ok('6 画像の順位はスコア（Gの字が無い）', !/G"/.test(flat) && /pts/.test(flat), flat.slice(0, 160));
ok('6 画像を作ったあと Gの順位のまま', scoreMetric === 'g');

// 7. 大きな数字（レート1000・大差）
g = mk({s: {rate: 1000, chipRate: 5000, bonusEnabled: true, finalChips: [40, -10, -10, -20]}, rounds: [{p: [90000, 20000, 0, -10000]}, {p: [90000, 20000, 0, -10000]}]});
h = list(g, 'g');
ok('7 大きな数字も3桁区切り', /\+[0-9,]+G/.test(vals(h)[0]), vals(h));

// 8. 未参加の人がいる（5人で回す）
g = mk({names: ['A','B','C','D','E'], s: {rate: 20}, rounds: [{p: [40000, 30000, 20000, 10000], m: [0, 1, 2, 3]}]});
h = list(g, 'g');
ok('8 未参加の人は「未参加」・Gの順位に入らない', h.includes('未参加') && vals(h).length === 4, vals(h));

// 9. 試合がまだ無い
g = mk({s: {rate: 20, bonusEnabled: true}});
h = list(g, 'g');
ok('9 試合が無いとき全員0G', vals(h).every(v => v === '0G'), vals(h));

// 10. チーム戦（チーム順位は pts のまま）
g = mk({s: {rate: 20, teamMode: true, teams: [{name: 'X', members: [0, 1]}, {name: 'Y', members: [2, 3]}]}, rounds: R4});
ok('10 チーム順位はptsのまま', teamStandingsHtml(g).includes('pts') && !teamStandingsHtml(g).includes('G<'));

// 11. 三麻
g = mk({numPlayers: 3, names: ['A','B','C'], s: {rate: 30, chipRate: 50, bonusEnabled: true, finalChips: [2, 0, -2], startPoints: 35000, returnPoints: 35000}, rounds: [{p: [50000, 35000, 20000]}]});
h = list(g, 'g');
const nums = vals(h).map(v => Number(v.replace(/[G,+]/g, '').replace('−', '-')));
ok('11 三麻も合計0', nums.reduce((a, b) => a + b, 0) === 0, vals(h));

// 12. 設定の欄：レートありの試合は保存値（チップ1枚=1Gでも10にしない）
ok('12 設定の変更の欄は保存値を出す', gOptHtml('e', {rate: 50, chipRate: 1, bonusEnabled: true}).includes('id="e-g-chip" min="0" inputmode="numeric" value="1"'));
ok('12 レートなしの試合は初期値10', gOptHtml('e', {rate: 0, chipRate: 1}).includes('id="e-g-chip" min="0" inputmode="numeric" value="10"'));

// 13. 旧データ（倍率を入れていた試合・chipRate 無し）
g = mk({s: {rate: 100, chipRate: undefined, bonusEnabled: true, finalChips: [1, 0, 0, -1]}, rounds: R4});
h = list(g, 'g');
ok('13 旧データ: chipRate が無ければチップは0G', h.includes('チップ 0') && vals(h)[0] === '+6,500G', vals(h));

// 14. 変更の記録
const b0 = {name: 't', settings: {playerNames: ['A','B','C','D'], numPlayers: 4, uma: [30,10,-10,-30], rate: 0, chipRate: 1, bonusEnabled: false}};
const c14 = describeSettingsChanges({name:'t', settings: {...b0.settings, startPoints: 25000, returnPoints: 30000, rate: 50, chipRate: 10}}, {name:'t', settings: {...b0.settings, startPoints: 25000, returnPoints: 30000, rate: 50, chipRate: 20}}, null);
ok('14 チップなしでチップのGを変えたら値で記録', c14.length === 1 && c14[0] === 'レート（チップ1枚）: 10G → 20G', c14);

scoreMetric = 'score';
return R;
}"""

UI = r"""() => {
// 15. 欄：レートにチェック→0を入れて作ると止まる
const R = [];
document.getElementById('s-g').checked = true;
document.getElementById('s-g-rate').value = '0';
const r1 = readGOpt('s');
R.push([r1 === false ? 'PASS' : 'FAIL', '15 0のまま作ろうとすると止めて知らせる', JSON.stringify(r1)]);
document.getElementById('s-g-rate').value = '';
R.push([readGOpt('s') === false ? 'PASS' : 'FAIL', '15 空でも止める', '']);
document.getElementById('s-g-rate').value = '2.6';
const r3 = readGOpt('s');
R.push([r3 && r3.rate === 3 ? 'PASS' : 'FAIL', '15 小数は整数に丸める', JSON.stringify(r3)]);
document.getElementById('s-g').checked = false;
const r4 = readGOpt('s');
R.push([r4 && r4.rate === 0 ? 'PASS' : 'FAIL', '15 チェックを外せば0（レートなし）', JSON.stringify(r4)]);
return R;
}"""

SHOT = r"""(o) => {
const s = Object.assign({playerNames: o.names, numPlayers: 4, startPoints: 25000, returnPoints: 30000, uma: [30,10,-10,-30], rate: 1000, chipRate: 5000, bonusEnabled: o.chips, startChips: 20, finalChips: [40, -10, -10, -20]}, {});
const g = {id: 'CASETESTAB', name: 'x', settings: s, rounds: []};
[[90000, 20000, 0, -10000], [90000, 20000, 0, -10000]].forEach(p => { const r = {points: p, members: [0,1,2,3]}; r.scores = calcScores(p, s); g.rounds.push(r); });
scoreMetric = 'g';
const d = document.createElement('div'); d.id = 'gshot'; d.className = 'card';
d.style.cssText = 'position:fixed;left:0;top:0;width:' + o.w + 'px;z-index:99999;background:#fff;padding:14px;box-sizing:border-box';
d.innerHTML = scoreMainHtml(g); document.body.appendChild(d);
// はみ出し: 値と名前・内訳が重ならないか、カードの外に出ないか
const bad = [];
d.querySelectorAll('.score-card').forEach(c => {
  const cr = c.getBoundingClientRect();
  c.querySelectorAll('.score-val, .score-name, .score-bonus').forEach(e => { const r = e.getBoundingClientRect(); if (r.right > cr.right + 0.5 || r.left < cr.left - 0.5) bad.push(e.textContent); });
  const v = c.querySelector('.score-val').getBoundingClientRect(), info = c.querySelector('.score-info').getBoundingClientRect();
  if (info.right > v.left + 0.5) bad.push('重なり:' + c.querySelector('.score-val').textContent);
});
const seg = d.querySelector('.metric-seg'); const sr = seg.getBoundingClientRect();
if (sr.right > d.getBoundingClientRect().right) bad.push('切り替えがはみ出す');
return bad;
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 800})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(BASE); pg.wait_for_timeout(2500)
    res = pg.evaluate(JS)
    pg.evaluate("() => showView('setup')"); pg.wait_for_timeout(600)
    res += pg.evaluate(UI)
    for r in res: print(*r)
    # 幅320・360で、長い名前・大きな数字のはみ出し
    for w in (320, 360):
        for chips in (True, False):
            pg2 = b.new_page(viewport={"width": w, "height": 900}, device_scale_factor=2)
            pg2.goto(BASE); pg2.wait_for_timeout(2000)
            bad = pg2.evaluate(SHOT, {"w": w, "chips": chips, "names": ["とても長い名前のプレイヤー", "B", "C", "D"]})
            r16 = ["PASS" if not bad else "FAIL", f"16 幅{w}・チップ{'あり' if chips else 'なし'}・長い名前と大きな数字", str(bad)]
            res.append(r16); print(*r16)
            pg2.locator("#gshot").screenshot(path=f"{SP}/g_w{w}_{'c' if chips else 'n'}.png")
            pg2.close()
    print("errors", errs)
    b.close()
fails = [r for r in res if r[0] != "PASS"]
print("RATE TEST: ALL PASS" if not fails and not errs else f"RATE TEST: {len(fails)} FAIL")
sys.exit(1 if fails or errs else 0)
