// 記事ごとの共有用の画像（og:image・1200×630 PNG）を、記事の絵（assets/thumbs/blog-*.svg）から作る（2026-10-31〜）。
// SNS（X・LINE・Facebook）は SVG を使えないので PNG にする。絵を真ん中に大きく置き、左右は絵の地の色で広げる。右下に小さくロゴ。
// X は横2:1に切るので、大事なものは上下15pxより内側に（絵は上下に余白があるので切れない）。
// 実行: リポジトリで python3 -m http.server 8765 を起こしてから node tools/make_og_images.js [blog-xxx ...]
// 画像を作り直したら、ファイル名を変えないとXが前の画像を出し続ける（docs/image-tools.md）。そのときは記事の og:image も書き換える
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const ROOT = path.join(__dirname, '..');
const BASE = 'http://localhost:8765';
(async () => {
  const want = process.argv.slice(2);
  const files = fs.readdirSync(path.join(ROOT, 'assets/thumbs')).filter(f => /^blog-.*\.svg$/.test(f))
    .filter(f => !want.length || want.includes(f.replace('.svg', '')))
    .filter(f => fs.existsSync(path.join(ROOT, f.replace('.svg', '.html'))));
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  await p.goto(BASE + '/404.html');
  for (const f of files) {
    const svg = fs.readFileSync(path.join(ROOT, 'assets/thumbs', f), 'utf8');
    const bg = (svg.match(/<rect width="320" height="240" fill="([^"]+)"/) || [])[1] || '#177083';
    await p.setContent(`<!doctype html><html><head><base href="${BASE}/"><style>
      html,body{margin:0;width:1200px;height:630px;overflow:hidden;background:${bg}}
      .art{position:absolute;left:50%;top:0;width:840px;height:630px;transform:translateX(-50%)}
      .art > svg{width:840px;height:630px;display:block;overflow:visible}
      .logo{position:absolute;right:26px;bottom:24px;background:#fff;border-radius:16px;padding:9px 16px;line-height:0;box-shadow:0 2px 8px rgba(0,0,0,.12)}
      .logo img{height:40px;width:auto}
    </style></head><body><div class="art">${svg}</div><div class="logo"><img src="/assets/logo.png"></div></body></html>`, { waitUntil: 'networkidle' });
    await p.waitForTimeout(150);
    await p.screenshot({ path: path.join(ROOT, 'assets/og', f.replace('.svg', '.png')) });
  }
  await b.close();
  console.log('made', files.length);
})();
