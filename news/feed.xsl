<?xml version="1.0" encoding="UTF-8"?>
<!-- RSSフィードをブラウザで開いたときの見た目（購読者向けの案内ページ） -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:atom="http://www.w3.org/2005/Atom">
<xsl:output method="html" encoding="UTF-8"/>
<xsl:template match="/">
<html lang="ja">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title><xsl:value-of select="/rss/channel/title"/> | RSSフィード</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', sans-serif; background: #f4faf7; color: #1f2a28; line-height: 1.9; }
.head { background: #fff; border-bottom: 1px solid #e6efeb; padding: 14px 20px; }
.head a { font-size: 17px; font-weight: 800; color: #177083; text-decoration: none; }
.hero { background: linear-gradient(180deg, #E4F3EC 0%, #D9EEE3 100%); text-align: center; padding: 30px 20px 26px; }
.hero h1 { font-size: 21px; font-weight: 800; color: #177083; margin-bottom: 6px; }
.hero p { font-size: 13px; color: #4a5a56; }
.wrap { max-width: 680px; margin: 0 auto; padding: 24px 20px 48px; }
.note { background: #fff; border: 1px solid #e6efeb; border-radius: 14px; padding: 16px 18px; font-size: 13px; color: #444; margin-bottom: 20px; }
.note b { color: #177083; }
.note code { background: #f2f7f6; border-radius: 5px; padding: 2px 8px; font-size: 12px; word-break: break-all; }
.item { display: block; background: #fff; border: 1px solid #e6efeb; border-radius: 14px; padding: 18px; margin-bottom: 12px; text-decoration: none; color: inherit; }
.item h2 { font-size: 15px; font-weight: 800; color: #1f2a28; line-height: 1.6; margin-bottom: 6px; }
.item .date { font-size: 12px; color: #9aa8a4; margin-bottom: 6px; }
.item p { font-size: 13px; color: #5a6a66; }
.item .more { color: #E75620; font-weight: 800; font-size: 13px; }
.foot { text-align: center; font-size: 12px; color: #7a8a86; padding: 8px 16px 32px; }
.foot a { color: #177083; }
</style>
</head>
<body>
<div class="head"><a href="/index.html">まじゃすこ / majasco</a></div>
<div class="hero">
  <h1>お知らせRSSフィード</h1>
  <p><xsl:value-of select="/rss/channel/description"/></p>
</div>
<div class="wrap">
  <div class="note">
    これは<b>RSSフィード</b>のページです。お使いのRSSリーダー（Feedly など）にこのURLを登録すると、まじゃすこのアップデート情報を自動で受け取れます。<br/>
    フィードURL: <code>https://majasco.jp/news/feed.xml</code>
  </div>
  <xsl:for-each select="/rss/channel/item">
    <a class="item">
      <xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute>
      <div class="date"><xsl:value-of select="substring(pubDate, 1, 16)"/></div>
      <h2><xsl:value-of select="title"/></h2>
      <p><xsl:value-of select="description"/></p>
      <span class="more">記事を読む ▶</span>
    </a>
  </xsl:for-each>
  <div class="foot" style="padding-top:16px"><a href="/news/">お知らせ一覧へ ›</a>　<a href="/index.html">トップへ ›</a></div>
</div>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
