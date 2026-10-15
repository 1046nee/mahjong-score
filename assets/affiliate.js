/* ==========================================================
   まじゃすこ アフィリエイト枠（/assets/affiliate.js）2026-10-15
   記事の中の <div class="aff-box" data-aff="キー"></div> に、紹介する道具のカードを描く。
   - 下の AMAZON_TAG（Amazonアソシエイトのトラッキングid。例 xxxx-22）と RAKUTEN_ID（楽天アフィリエイトID）を
     入れると、その店のボタンだけ出る。両方とも空なら枠ごと出さない（審査中も見た目に影響なし）
   - リンクは各店の「検索結果」へ飛ばす（商品の入れ替え・在庫切れの手入れが要らない）
   - ステマ規制（2023-10〜）: 枠に「PR」を必ず出す。Amazonを使うときは決められた一文を枠の下に出す
   - 用語ルール（CLAUDE.md）: 値段・金額は書かない。賭けを連想させる道具は載せない
   ========================================================== */
const AMAZON_TAG = '';
const RAKUTEN_ID = '';

const AFF_SETS = {
  // 記事「麻雀の準備とマナー」の持ち物
  starter: {
    title: 'この記事で紹介した道具',
    items: [
      { name: '麻雀牌（家庭用・136枚）', note: '4人打ちの基本セット。点棒・サイコロが付いているものが多い', q: '麻雀牌 セット 家庭用' },
      { name: '麻雀マット', note: 'テーブルに敷くだけで牌が滑りにくく、音も静かに', q: '麻雀マット' },
      { name: '麻雀のサイコロ', note: '親決め・配牌の位置決めに。2つあると便利', q: '麻雀 サイコロ' }
    ]
  }
};

(function () {
  const amazon = q => `https://www.amazon.co.jp/s?k=${encodeURIComponent(q)}&tag=${encodeURIComponent(AMAZON_TAG)}`;
  const rakuten = q => `https://hb.afl.rakuten.co.jp/hgc/${encodeURIComponent(RAKUTEN_ID)}/?pc=${encodeURIComponent('https://search.rakuten.co.jp/search/mall/' + encodeURIComponent(q) + '/')}`;
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  function render() {
    document.querySelectorAll('.aff-box[data-aff]').forEach(el => {
      const set = AFF_SETS[el.getAttribute('data-aff')];
      if (!set || (!AMAZON_TAG && !RAKUTEN_ID)) { el.style.display = 'none'; return; }
      const btn = (href, label) => `<a class="aff-btn" href="${esc(href)}" target="_blank" rel="sponsored noopener">${label}</a>`;
      el.innerHTML = `<div class="aff-head"><span class="aff-pr">PR</span><b>${esc(set.title)}</b></div>`
        + set.items.map(it => `<div class="aff-item"><div class="aff-txt"><b>${esc(it.name)}</b><small>${esc(it.note)}</small></div>`
          + `<div class="aff-btns">${AMAZON_TAG ? btn(amazon(it.q), 'Amazon') : ''}${RAKUTEN_ID ? btn(rakuten(it.q), '楽天') : ''}</div></div>`).join('')
        + `<div class="aff-note">リンク先の購入で、まじゃすこに紹介料が入ることがあります。${AMAZON_TAG ? 'Amazonのアソシエイトとして、まじゃすこは適格販売により収入を得ています。' : ''}</div>`;
      el.style.display = '';
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render); else render();
})();
