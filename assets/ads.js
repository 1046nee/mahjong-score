/* ==========================================================
   まじゃすこ AdSense広告枠（/assets/ads.js）
   AdSense管理画面で「ディスプレイ広告」ユニットを作成し、
   下のAD_SLOTSにスロットID（数字）を設定すると、その枠だけ配信が始まる。
   空文字のままの枠は非表示（レイアウトへの影響なし）。

   配置ルール（CLAUDE.md参照）:
   - 記事: 導入文の直後（article_top）と末尾CTAの上（article_bottom）
   - ブログ一覧・カテゴリページ: リストの下（list_bottom）
   - LP: 解説セクションの間（lp_bottom）
   - スコア入力シート・ゲーム画面・設定モーダル周辺には置かない（誤クリック防止）
   ========================================================== */

const AD_CLIENT = 'ca-pub-9998035509478799';
const AD_SLOTS = {
  article_top: '',    // 記事の導入文直後
  article_bottom: '', // 記事の末尾（CTAの上）
  list_bottom: '',    // 一覧ページのリスト下
  lp_bottom: ''       // LPの解説セクション間
};

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-ad]').forEach(el => {
    const slot = AD_SLOTS[el.getAttribute('data-ad')];
    if (!slot) { el.style.display = 'none'; return; }
    // CLS対策: 広告読み込み前から高さを確保しておく
    el.style.minHeight = '280px';
    el.innerHTML = '<div style="font-size:10px;color:#aaa;text-align:center;margin-bottom:4px">スポンサーリンク</div>'
      + `<ins class="adsbygoogle" style="display:block" data-ad-client="${AD_CLIENT}" data-ad-slot="${slot}" data-ad-format="auto" data-full-width-responsive="true"></ins>`;
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) {}
  });
});
