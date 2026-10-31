/* ==========================================================
   一覧4ページ（blog.html / mahjong/ / news/ / blog/）の
   <main class="post-list"> に記事カードを静的HTMLとして書き出す。

   実行: node tools/build_post_lists.js

   なぜ必要か: 一覧をJSレンダリングだけに頼ると、クローラーには
   「本文ゼロの空ページ」に見える（AdSense「有用性の低いコンテンツ」の一因）。
   静的HTMLに同じカードを書き出しておき、JS有効環境では blog-site.js が
   同一内容で再描画する（正はあくまで BLOG_POSTS ひとつ）。

   新しい記事を公開したら:
   1. assets/blog-site.js の BLOG_POSTS に1件追加
   2. node tools/build_post_lists.js を実行
   3. 変わった4ページも一緒にコミット
   ========================================================== */
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');

const src = fs.readFileSync(path.join(root, 'assets', 'blog-site.js'), 'utf8');
const catsMatch = src.match(/const BLOG_CATS = (\{[\s\S]*?\});/);
const postsMatch = src.match(/const BLOG_POSTS = (\[[\s\S]*?\]);/);
if (!catsMatch || !postsMatch) throw new Error('blog-site.js から BLOG_CATS / BLOG_POSTS を抽出できません');
const cats = eval('(' + catsMatch[1] + ')');
const posts = eval(postsMatch[1]);

// blog-site.js の cardHtml() と同一のマークアップを出力すること（差があるとJS再描画でちらつく）
const escHtml = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const byDateDesc = (a, b) => b.date.localeCompare(a.date);
const thumb = p => '/assets/thumbs/' + p.url.split('/').pop().replace('.html', '') + '.svg';
// 題名は「｜」の前を太字の見出し、後ろを次の行に細く小さく（blog-site.js の titleHtml と同じ）
const titleHtml = t => { const [m, ...r] = t.split('｜'); return escHtml(m) + (r.length ? `<span class="pc-sub">${escHtml(r.join('｜'))}</span>` : ''); };
const cardHtml = p => `<a class="post-card has-thumb cat-${p.cat}" href="${p.url}">
      <span class="pc-thumb"><img src="${thumb(p)}" alt="" width="320" height="240" loading="lazy" decoding="async"></span>
      <div class="pc-body"><span class="pc-meta"><span class="pc-cat">${cats[p.cat].name}</span><span class="date">${p.date}</span></span>
      <h2>${titleHtml(p.title)}</h2></div>
    </a>`;
// 絵が無い記事があれば止める（新しい記事は tools/make_thumbs.py に1行足す）
for (const p of posts) if (!fs.existsSync(path.join(root, thumb(p).slice(1)))) throw new Error('記事の絵がありません: ' + thumb(p) + '（python tools/make_thumbs.py に足す）');
// blog-site.js の catNavHtml() と同じ（タブを先にHTMLに書いておくと、ページを移るときに画面が跳ねない）
const catNavHtml = active => {
  const items = [['all', 'すべて', '/blog.html']].concat(Object.keys(cats).map(k => [k, cats[k].name, cats[k].url]));
  const count = k => posts.filter(p => k === 'all' || p.cat === k).length;
  return '<div class="cat-nav-inner">' + items.map(([k, label, url]) =>
    `<a class="cat-tab cat-${k}${k === active ? ' on' : ''}" href="${url}"${k === active ? ' aria-current="page"' : ''}>${label}<span class="cnt">${count(k)}</span></a>`).join('') + '</div>';
};

// 一覧ページ: すべて・麻雀の記事の入口（/mahjong/＝6テーマをまとめて）・カテゴリごと（2026-10-28〜。テーマのページは tools/blog_cats.py が作る）
const pages = [['blog.html', 'all'], [path.join('mahjong', 'index.html'), 'mahjong']]
  .concat(Object.keys(cats).map(k => [path.join(cats[k].url.replace(/^\/|\/$/g, ''), 'index.html'), k]));
const inCat = (p, cat) => cat === 'all' || p.cat === cat || (cat === 'mahjong' && cats[p.cat] && cats[p.cat].group === 'mahjong');

for (const [file, cat] of pages) {
  const fp = path.join(root, file);
  let html = fs.readFileSync(fp, 'utf8');
  const list = posts.filter(p => inCat(p, cat)).sort(byDateDesc);
  const cards = list.map(cardHtml).join('\n    ');
  const re = new RegExp(`(<main class="post-list" data-post-list="${cat}">)[\\s\\S]*?(</main>)`);
  if (!re.test(html)) throw new Error(`アンカーが見つかりません: ${file}`);
  html = html.replace(re, `$1\n    ${cards}\n  $2`);
  // 紹介文（.cat-intro）は一覧の上に置かない＝最初の画面は題名と絵だけ（2026-10-31 ユーザーの依頼「引き算で」）。
  // 検索のために文は残し、ページの下（アプリの案内の前）に小さく置く。何度実行しても同じ
  const introM = html.match(/\n?<p class="cat-intro"[^>]*>[\s\S]*?<\/p>\n?/);
  if (introM && html.indexOf(introM[0]) < html.indexOf('<div class="post-layout">')) {
    const foot = introM[0].trim().replace(/ style="[^"]*"/, ' style="max-width:960px;margin:4px auto 26px;padding:0 20px;font-size:12.5px;line-height:1.8;color:#6B7A77"');
    html = html.replace(introM[0], '\n').replace('<div class="app-banner">', foot + '\n<div class="app-banner">');
  }
  const nre = new RegExp(`(<nav class="cat-nav" data-cat-nav="${cat}">)[\\s\\S]*?(</nav>)`);
  if (!nre.test(html)) throw new Error(`タブのアンカーが見つかりません: ${file}`);
  html = html.replace(nre, `$1${catNavHtml(cat)}$2`);
  fs.writeFileSync(fp, html);
  console.log(`${file}: ${list.length} cards written`);
}
