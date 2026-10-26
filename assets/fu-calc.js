/* 符と点数の計算ツール（点数早見表の記事 blog-score-table.html・2026-10-26〜）
   符＝副底20＋あがり方＋待ち＋雀頭＋面子 → 10の位に切り上げ。点数＝基本点（符×2^(翻+2)、2,000で満貫）から。
   点数は tools/score_sheet.py（早見表の画像）と同じ式。node tools/fu_calc_test.js で早見表のデータと突き合わせる */
(function () {
  'use strict';
  var up100 = function (x) { return Math.ceil(x / 100) * 100; };

  var MELDS = [
    ['順子（123など）', 0],
    ['明刻（鳴いた・ロンで完成）2〜8', 2], ['明刻 1・9・字牌', 4],
    ['暗刻（自分でそろえた）2〜8', 4], ['暗刻 1・9・字牌', 8],
    ['明槓 2〜8', 8], ['明槓 1・9・字牌', 16],
    ['暗槓 2〜8', 16], ['暗槓 1・9・字牌', 32],
  ];
  var WAITS = [['両面・双碰（シャンポン）', 0], ['嵌張・辺張・単騎', 2]];
  var HEADS = [['数牌・役にならない風牌', 0], ['役牌（三元牌・場風・自風）', 2], ['連風牌（場風と自風が同じ）', 4]];

  /* o = { tsumo, menzen, form: 'normal'|'pinfu'|'chitoi', wait, head, melds: [4つ] } */
  function fuOf(o) {
    if (o.form === 'chitoi') return { fu: 25, raw: 25, parts: [['七対子は25符で固定', 25]] };
    if (o.form === 'pinfu' && o.menzen) {
      return o.tsumo ? { fu: 20, raw: 20, parts: [['平和のツモは20符で固定', 20]] }
                     : { fu: 30, raw: 30, parts: [['平和のロンは30符で固定', 30]] };
    }
    var parts = [['副底（フーテイ）', 20]];
    if (o.menzen && !o.tsumo) parts.push(['門前でロン', 10]);
    if (o.tsumo) parts.push(['ツモ', 2]);
    if (o.wait) parts.push(['待ち（嵌張・辺張・単騎）', o.wait]);
    if (o.head) parts.push(['雀頭（' + (o.head === 4 ? '連風牌' : '役牌') + '）', o.head]);
    o.melds.forEach(function (m, i) { if (m) parts.push(['面子' + (i + 1), m]); });
    var raw = parts.reduce(function (a, p) { return a + p[1]; }, 0);
    var fu = Math.ceil(raw / 10) * 10;
    if (!o.menzen && raw === 20) { parts.push(['鳴いた手で符が副底だけのときは30符', 10]); raw = 30; fu = 30; }
    return { fu: fu, raw: raw, parts: parts };
  }

  var LIMITS = [[13, '役満', 8000], [11, '三倍満', 6000], [8, '倍満', 4000], [6, '跳満', 3000], [5, '満貫', 2000]];
  function points(fu, han, kiriage) {
    var name = '', base = 0;
    for (var i = 0; i < LIMITS.length; i++) if (han >= LIMITS[i][0]) { name = LIMITS[i][1]; base = LIMITS[i][2]; break; }
    if (!name) {
      base = fu * Math.pow(2, han + 2);
      if (base > 2000 || (kiriage && base === 1920)) { base = 2000; name = '満貫'; }
    }
    return {
      name: name, base: base,
      ko_ron: up100(base * 4), ko_tsumo: [up100(base), up100(base * 2)],
      oya_ron: up100(base * 6), oya_tsumo: up100(base * 2),
    };
  }

  var api = { fuOf: fuOf, points: points, MELDS: MELDS };
  if (typeof module !== 'undefined') { module.exports = api; return; }

  // ---------------- 画面 ----------------
  var root = document.getElementById('fu-calc');
  if (!root) return;
  var n = function (x) { return x.toLocaleString('ja-JP'); };
  var opt = function (list) { return list.map(function (o) { return '<option value="' + o[1] + '">' + o[0] + '</option>'; }).join(''); };
  var seg = function (name, items) {
    return '<div class="fc-seg" role="radiogroup">' + items.map(function (it, i) {
      return '<label><input type="radio" name="' + name + '" value="' + it[1] + '"' + (i === 0 ? ' checked' : '') + '><span>' + it[0] + '</span></label>';
    }).join('') + '</div>';
  };
  var hanOpts = '';
  for (var h = 1; h <= 13; h++) hanOpts += '<option value="' + h + '"' + (h === 2 ? ' selected' : '') + '>' + (h === 13 ? '13翻以上' : h + '翻') + '</option>';
  root.innerHTML =
    '<div class="fc-row"><span class="fc-l">あがった人</span>' + seg('fc-who', [['子', 'ko'], ['親', 'oya']]) + '</div>' +
    '<div class="fc-row"><span class="fc-l">あがり方</span>' + seg('fc-how', [['ロン', 'ron'], ['ツモ', 'tsumo']]) + '</div>' +
    '<div class="fc-row"><span class="fc-l">鳴き</span>' + seg('fc-naki', [['門前（鳴きなし）', '1'], ['鳴きあり', '0']]) + '</div>' +
    '<div class="fc-row"><span class="fc-l">手の形</span>' + seg('fc-form', [['ふつう', 'normal'], ['平和', 'pinfu'], ['七対子', 'chitoi']]) + '</div>' +
    '<div class="fc-detail">' +
    '<label class="fc-sel"><span>待ち</span><select id="fc-wait">' + opt(WAITS) + '</select></label>' +
    '<label class="fc-sel"><span>雀頭</span><select id="fc-head">' + opt(HEADS) + '</select></label>' +
    [1, 2, 3, 4].map(function (i) { return '<label class="fc-sel"><span>面子' + i + '</span><select class="fc-meld">' + opt(MELDS) + '</select></label>'; }).join('') +
    '</div>' +
    '<label class="fc-sel fc-han"><span>翻（役＋ドラ）</span><select id="fc-han">' + hanOpts + '</select></label>' +
    '<label class="fc-chk"><input type="checkbox" id="fc-kiri"> 切り上げ満貫あり（30符4翻・60符3翻を満貫に）</label>' +
    '<div class="fc-out" aria-live="polite"></div>';

  var val = function (name) { var e = root.querySelector('input[name="' + name + '"]:checked'); return e ? e.value : ''; };
  function update() {
    var form = val('fc-form'), menzen = val('fc-naki') === '1', tsumo = val('fc-how') === 'tsumo', oya = val('fc-who') === 'oya';
    root.querySelector('.fc-detail').style.display = (form === 'normal' || (form === 'pinfu' && !menzen)) ? '' : 'none';
    var o = {
      tsumo: tsumo, menzen: menzen, form: form,
      wait: +root.querySelector('#fc-wait').value, head: +root.querySelector('#fc-head').value,
      melds: [].map.call(root.querySelectorAll('.fc-meld'), function (s) { return +s.value; }),
    };
    var han = +root.querySelector('#fc-han').value;
    var f = fuOf(o), p = points(f.fu, han, root.querySelector('#fc-kiri').checked);
    var warn = '';
    if (form === 'pinfu' && !menzen) warn = '平和は門前（鳴きなし）だけの役です。鳴いた手として数えました。';
    else if (form === 'chitoi' && !menzen) warn = '七対子は門前だけの形です。';
    else if (form === 'chitoi' && (han < 2 || (tsumo && han < 3))) warn = '七対子は2翻（ツモなら門前ツモがついて3翻）以上です。';
    else if (form === 'pinfu' && tsumo && han < 2) warn = '平和のツモは、平和＋門前ツモで2翻以上です。';
    var pay = oya ? (tsumo ? n(p.oya_tsumo) + '点オール（ALL）<small>子の3人が' + n(p.oya_tsumo) + '点ずつ・合計' + n(p.oya_tsumo * 3) + '点</small>'
                           : n(p.oya_ron) + '点<small>ロンされた人が払う</small>')
                  : (tsumo ? n(p.ko_tsumo[0]) + '・' + n(p.ko_tsumo[1]) + '点<small>子が' + n(p.ko_tsumo[0]) + '点ずつ、親が' + n(p.ko_tsumo[1]) + '点・合計' + n(p.ko_tsumo[0] * 2 + p.ko_tsumo[1]) + '点</small>'
                           : n(p.ko_ron) + '点<small>ロンされた人が払う</small>');
    var fuLine = p.name && han >= 5 ? '<p class="fc-fu">' + han + '翻以上は符に関係なく' + p.name + '</p>'
      : '<p class="fc-fu"><b>' + f.fu + '符</b>' + (f.raw !== f.fu ? '（' + f.raw + '符を切り上げ）' : '') + '</p>' +
        '<ul class="fc-parts">' + f.parts.map(function (q) { return '<li><span>' + q[0] + '</span><b>' + (q[1] > 0 && f.parts.length > 1 ? '+' : '') + q[1] + '符</b></li>'; }).join('') + '</ul>';
    root.querySelector('.fc-out').innerHTML = fuLine +
      '<p class="fc-pt"><span>' + (oya ? '親' : '子') + 'の' + (tsumo ? 'ツモ' : 'ロン') + '・' + (han === 13 ? '役満' : han + '翻') + (p.name && han < 5 ? '（' + p.name + '）' : '') + '</span><b>' + pay + '</b></p>' +
      (warn ? '<p class="fc-warn">' + warn + '</p>' : '');
  }
  root.addEventListener('change', update);
  update();
})();
