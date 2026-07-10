/* ==========================================================
   まじゃすこ ブログ共通スクリプト（/assets/blog-site.js）
   記事のメタ情報（カテゴリ・公開日・おすすめフラグ）はこのファイルの
   BLOG_POSTS だけで管理する。新しい記事を公開したら、
   ここに1件追加するだけで一覧・カテゴリページ・サイドバーに反映される。
   （お知らせ記事の場合は /news/feed.xml にも <item> を1件追加すること）

   使い方（HTML側）:
   - 一覧を出す場所:      <div class="post-list" data-post-list="all|mahjong|news|blog"></div>
   - カテゴリナビ:        <nav class="cat-nav" data-cat-nav="現在のカテゴリkey"></nav>
   - サイドバー:          <aside class="side" data-sidebar></aside>
   ========================================================== */

const BLOG_CATS = {
  mahjong: { name: '麻雀攻略', url: '/mahjong/' },
  news:    { name: 'お知らせ', url: '/news/' },
  blog:    { name: '雑記',     url: '/blog/' }
};

// 新しい順に並べる。recommended: true の記事が「今月のおすすめ記事」に出る（3〜4件を目安に手動で付け替える）
const BLOG_POSTS = [
  { url: '/news/update-2026-07.html', cat: 'news', date: '2026.07.10', tag: 'アップデート',
    title: '大型アップデートのお知らせ｜チーム戦・チップ収支・最大40人の回し打ちに対応しました',
    desc: 'チーム戦モード、チップの収支計算、メンバー3〜40人の回し打ち対応など、まじゃすこの大型アップデート内容を紹介します。' },
  { url: '/blog-naki.html', cat: 'mahjong', date: '2026.07.10', tag: 'ルール解説', recommended: true,
    title: '麻雀の鳴き（ポン・チー・カン）とは？基本ルールと使いどころを解説',
    desc: 'ポン・チー・カンの違い、誰から鳴けるのか、鳴きのメリット・デメリットと「鳴いていい場面」の考え方を初心者向けに整理します。' },
  { url: '/blog-dora.html', cat: 'mahjong', date: '2026.07.10', tag: 'ルール解説', recommended: true,
    title: '麻雀のドラとは？裏ドラ・カンドラ・赤ドラの仕組みをやさしく解説',
    desc: 'ドラ表示牌の見方から、裏ドラ・カンドラ・赤ドラの違い、「ドラは役ではない」の意味まで、点数が伸びる仕組みを解説します。' },
  { url: '/blog-starter-kit.html', cat: 'mahjong', date: '2026.07.08', tag: '準備ガイド', tagStyle: 'orange',
    title: '友人と麻雀を始めるのに必要な持ち物リスト｜初心者向け準備ガイド',
    desc: '麻雀卓・牌・点棒など最低限必要なものから、スコア記録の悩みを解決する方法まで紹介します。' },
  { url: '/blog-manner.html', cat: 'mahjong', date: '2026.07.08', tag: 'ルール解説',
    title: '麻雀のマナーと見落としがちなルール｜チョンボ・途中流局とは',
    desc: 'チョンボ、途中流局、発声のタイミングなど、対面麻雀で知っておきたい基本のマナーをまとめました。' },
  { url: '/blog-riichi.html', cat: 'mahjong', date: '2026.07.08', tag: '役一覧',
    title: '麻雀のリーチとは？ルールとメリット・デメリットをやさしく解説',
    desc: 'リーチのルール、かけるメリット・デメリット、リーチ後の注意点まで初心者向けに解説します。' },
  { url: '/blog-rule-basics.html', cat: 'mahjong', date: '2026.07.08', tag: 'ルール解説',
    title: '麻雀のルール基本の基本｜半荘・東風戦とは？初心者向け入門',
    desc: '半荘・東風戦の違い、局・親・本場・流局といった対局の流れを理解するための基本用語を解説します。' },
  { url: '/blog-hai-types.html', cat: 'mahjong', date: '2026.07.08', tag: '牌の基礎',
    title: '麻雀牌の種類と名前一覧｜萬子・索子・筒子・字牌をやさしく解説',
    desc: '数牌（萬子・索子・筒子）と字牌（風牌・三元牌）の違いを、見分け方のコツつきで初心者向けに紹介します。' },
  { url: '/blog-app-guide.html', cat: 'mahjong', date: '2026.07.07', tag: 'アプリの選び方', tagStyle: 'orange', recommended: true,
    title: '麻雀のスコア管理アプリの選び方｜チェックすべき5つのポイント',
    desc: '共有できるか、ウマ・オカを自由に設定できるか、サンマに対応しているかなど、比較すべき5つの軸をまとめました。' },
  { url: '/blog-sanma-yonma.html', cat: 'mahjong', date: '2026.07.07', tag: 'ルール解説',
    title: '3人麻雀（サンマ）と4人麻雀の違いとは？ルール・点数の変更点を解説',
    desc: '牌の構成、持ち点・返し点、ウマの設定まで、3人麻雀ならではの違いを4人麻雀と比較しながら解説します。' },
  { url: '/blog-fu-han.html', cat: 'mahjong', date: '2026.07.07', tag: 'スコア計算入門',
    title: '麻雀の点数計算はなぜ難しい？符と翻の仕組みをやさしく解説',
    desc: '点数計算がわかりにくく感じる理由と、符・翻それぞれの考え方をゼロからやさしく説明します。' },
  { url: '/blog-yaku-list.html', cat: 'mahjong', date: '2026.07.07', tag: '役一覧',
    title: '麻雀の役一覧｜初心者がまず覚えるべき基本の役10選',
    desc: 'リーチ・タンヤオ・ピンフなど、実戦でよく出てくる基本の役だけに絞って、成立条件と翻数を紹介します。' },
  { url: '/blog-score-table.html', cat: 'mahjong', date: '2026.07.07', tag: '点数表',
    title: '麻雀の点数表（翻・符）完全早見表｜初心者向けにやさしく解説',
    desc: '子・親、ロン・ツモ別の点数一覧と、符の数え方、覚え方のコツまで一気にまとめました。' },
  { url: '/blog-uma-oka.html', cat: 'mahjong', date: '2026.07.06', tag: 'スコア計算入門', recommended: true,
    title: '麻雀のウマ・オカとは？初心者向けスコア計算入門',
    desc: 'ウマ・オカ・返し点・素点とは何かを、具体的な数字の例つきで初心者向けに解説します。' },
  { url: '/blog-why-majasco.html', cat: 'blog', date: '2026.07.06', tag: '開発ストーリー', tagStyle: 'orange',
    title: '麻雀のスコア計算がめんどうで『まじゃすこ』を作った話',
    desc: '対局後の計算が面倒、紙のスコアシートは読みにくい……。そんな不満から無料の麻雀スコア集計・共有アプリを作りました。' }
];

(function () {
  const escHtml = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const byDateDesc = (a, b) => b.date.localeCompare(a.date);

  function cardHtml(p) {
    return `<a class="post-card" href="${p.url}">
      <span class="post-tag${p.tagStyle === 'orange' ? ' orange' : ''}">${escHtml(p.tag || BLOG_CATS[p.cat].name)}</span>
      <h2>${escHtml(p.title)}</h2>
      <p class="excerpt">${escHtml(p.desc)}</p>
      <div class="foot"><span class="date">${p.date}</span><span class="read-more">記事を読む ▶</span></div>
    </a>`;
  }
  function sideItem(p) {
    return `<li><a class="sb-link" href="${p.url}">${escHtml(p.title)}</a><span class="sb-date">${p.date}・${BLOG_CATS[p.cat].name}</span></li>`;
  }

  document.addEventListener('DOMContentLoaded', () => {
    // 記事一覧（カテゴリ別・新しい順）
    document.querySelectorAll('[data-post-list]').forEach(el => {
      const cat = el.getAttribute('data-post-list');
      const posts = BLOG_POSTS.filter(p => cat === 'all' || p.cat === cat).sort(byDateDesc);
      el.innerHTML = posts.map(cardHtml).join('') || '<p class="bs-empty">このカテゴリの記事はまだありません。</p>';
    });

    // カテゴリナビ（すべて / 麻雀攻略 / お知らせ / 雑記）
    document.querySelectorAll('[data-cat-nav]').forEach(el => {
      const active = el.getAttribute('data-cat-nav');
      const items = [['all', 'すべて', '/blog.html']].concat(Object.keys(BLOG_CATS).map(k => [k, BLOG_CATS[k].name, BLOG_CATS[k].url]));
      el.innerHTML = items.map(([k, label, url]) => `<a class="cat-chip${k === active ? ' on' : ''}" href="${url}">${label}</a>`).join('');
    });

    // サイドバー: 今月のおすすめ記事 ＋ 最新のアップデート（/news/の新着）
    document.querySelectorAll('[data-sidebar]').forEach(el => {
      const here = location.pathname;
      const rec = BLOG_POSTS.filter(p => p.recommended && p.url !== here).sort(byDateDesc).slice(0, 4);
      const news = BLOG_POSTS.filter(p => p.cat === 'news' && p.url !== here).sort(byDateDesc).slice(0, 3);
      let html = '';
      if (rec.length) {
        html += `<div class="side-box"><h2>今月のおすすめ記事</h2><ul>${rec.map(sideItem).join('')}</ul></div>`;
      }
      html += `<div class="side-box"><h2>最新のアップデート</h2>`
        + (news.length ? `<ul>${news.map(sideItem).join('')}</ul>` : '<p class="bs-empty">お知らせは準備中です。</p>')
        + `<a class="sb-more" href="/news/">お知らせ一覧 ›</a>　<a class="sb-more" href="/news/feed.xml">RSS</a></div>`;
      el.innerHTML = html;
    });
  });
})();
