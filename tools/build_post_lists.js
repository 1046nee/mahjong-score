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
const cardHtml = p => `<a class="post-card cat-${p.cat}" href="${p.url}">
      <span class="pc-meta"><span class="pc-cat">${cats[p.cat].name}</span>${p.tag ? `<span class="post-tag">${escHtml(p.tag)}</span>` : ''}<span class="date">${p.date}</span></span>
      <h2>${escHtml(p.title)}</h2>
      <p class="excerpt">${escHtml(p.desc)}</p>
    </a>`;
// blog-site.js の catNavHtml() と同じ（タブを先にHTMLに書いておくと、ページを移るときに画面が跳ねない）
const catNavHtml = active => {
  const items = [['all', 'すべて', '/blog.html']].concat(Object.keys(cats).map(k => [k, cats[k].name, cats[k].url]));
  const count = k => posts.filter(p => k === 'all' || p.cat === k).length;
  return '<div class="cat-nav-inner">' + items.map(([k, label, url]) =>
    `<a class="cat-tab cat-${k}${k === active ? ' on' : ''}" href="${url}"${k === active ? ' aria-current="page"' : ''}>${label}<span class="cnt">${count(k)}</span></a>`).join('') + '</div>';
};

const pages = [
  ['blog.html', 'all'],
  [path.join('mahjong', 'index.html'), 'mahjong'],
  [path.join('news', 'index.html'), 'news'],
  [path.join('blog', 'index.html'), 'blog'],
];

for (const [file, cat] of pages) {
  const fp = path.join(root, file);
  let html = fs.readFileSync(fp, 'utf8');
  const list = posts.filter(p => cat === 'all' || p.cat === cat).sort(byDateDesc);
  const cards = list.map(cardHtml).join('\n    ');
  const re = new RegExp(`(<main class="post-list" data-post-list="${cat}">)[\\s\\S]*?(</main>)`);
  if (!re.test(html)) throw new Error(`アンカーが見つかりません: ${file}`);
  html = html.replace(re, `$1\n    ${cards}\n  $2`);
  const nre = new RegExp(`(<nav class="cat-nav" data-cat-nav="${cat}">)[\\s\\S]*?(</nav>)`);
  if (!nre.test(html)) throw new Error(`タブのアンカーが見つかりません: ${file}`);
  html = html.replace(nre, `$1${catNavHtml(cat)}$2`);
  fs.writeFileSync(fp, html);
  console.log(`${file}: ${list.length} cards written`);
}
