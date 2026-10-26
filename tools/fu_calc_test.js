// 符と点数の計算ツール（assets/fu-calc.js）を、早見表のデータ（assets/score/score_table.json＝tools/score_sheet.py）と例で確かめる
// 実行: node tools/fu_calc_test.js
const path = require('path');
const C = require(path.join(__dirname, '..', 'assets', 'fu-calc.js'));
const T = require(path.join(__dirname, '..', 'assets', 'score', 'score_table.json'));
let bad = 0;
const eq = (a, b, msg) => { if (JSON.stringify(a) !== JSON.stringify(b)) { bad++; console.log('NG', msg, a, b); } };
const HANS = [1, 2, 3, 4];
T.rows.forEach(r => r.cells.forEach((c, i) => {
  const p = C.points(r.fu, HANS[i], false);
  ['ko_ron', 'ko_tsumo', 'oya_ron', 'oya_tsumo'].forEach(k => eq(p[k], c[k], `${r.fu}符${HANS[i]}翻 ${k}`));
}));
const LH = { '満貫': 5, '跳満': 6, '倍満': 8, '三倍満': 11, '役満': 13 };
T.limits.forEach(l => { const p = C.points(30, LH[l.name], false); ['ko_ron', 'ko_tsumo', 'oya_ron', 'oya_tsumo'].forEach(k => eq(p[k], l[k], `${l.name} ${k}`)); });
eq(C.points(30, 4, true).ko_ron, 8000, '切り上げ満貫 30符4翻');
eq(C.points(60, 3, true).oya_ron, 12000, '切り上げ満貫 60符3翻 親');
// 符の例（記事の実例：門前ロン・両面・中の暗刻 → 38符→40符）
const base = { tsumo: false, menzen: true, form: 'normal', wait: 0, head: 0, melds: [0, 0, 0, 0] };
eq(C.fuOf({ ...base, melds: [8, 0, 0, 0] }).fu, 40, '門前ロン＋中の暗刻');
eq(C.fuOf({ ...base, form: 'pinfu', tsumo: true }).fu, 20, '平和ツモ');
eq(C.fuOf({ ...base, form: 'pinfu' }).fu, 30, '平和ロン');
eq(C.fuOf({ ...base, form: 'chitoi' }).fu, 25, '七対子');
eq(C.fuOf({ ...base, menzen: false }).fu, 30, '鳴いて副底だけ→30符');
eq(C.fuOf({ ...base, tsumo: true, wait: 2 }).fu, 30, '門前ツモ・単騎 20+2+2=24→30');
eq(C.fuOf({ ...base, menzen: false, melds: [32, 0, 0, 0] }).fu, 60, '鳴き・暗槓么九 52→60');
eq(C.fuOf({ ...base, head: 4, wait: 2, melds: [8, 8, 0, 0] }).fu, 60, '門前ロン 20+10+2+4+16=52→60');
console.log(bad ? `${bad} 件ちがう` : 'すべてOK');
process.exit(bad ? 1 : 0);
