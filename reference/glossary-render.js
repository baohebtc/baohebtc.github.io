// glossary-render.js —— 术语六层卡片渲染（F45 · ADR-0026）
// 数据：glossary-data.js（window/const GLOSSARY）
// 形态：正解 → 比喻 → ✅像 → ⚠️不像（视觉权重最高）→ 多视角 → 站内延伸
(function () {
  'use strict';
  var host = document.getElementById('glossary-cards');
  if (!host || typeof GLOSSARY === 'undefined') return;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  // 本页在 reference/ 下，数据里存的是站点根相对路径
  function up(href) {
    return href.replace(/^\/+/, '').replace(/^(?!\.\.)/, '../');
  }

  GLOSSARY.forEach(function (t, i) {
    var el = document.createElement('article');
    el.className = 'term-card';
    el.id = 'term-' + encodeURIComponent(t.term);

    var views = (t.views || []).map(function (v) {
      var m = /^(机制|使用者|历史|反面)\s*[:：]\s*([\s\S]+)$/.exec(v);
      if (!m) return '<li class="term-view"><span class="vk">视角</span><p>' + esc(v) + '</p></li>';
      return '<li class="term-view vk-' + m[1] + '"><span class="vk">' + m[1] + '</span><p>' +
        esc(m[2]) + '</p></li>';
    }).join('');

    var links = (t.links || []).map(function (l) {
      return '<a href="' + esc(up(l.href)) + '">' + esc(l.label) + ' →</a>';
    }).join('');

    el.innerHTML =
      '<div class="term-head">' +
        '<h3>' + esc(t.term) + ' <span class="term-en">' + esc(t.term_en) + '</span></h3>' +
        '<span class="term-src">比喻出处 · ' + esc(t.source || '—') + '</span>' +
      '</div>' +
      '<div class="term-layer t-correct"><span class="tl">正解</span><p>' + esc(t.correct) + '</p></div>' +
      '<div class="term-layer t-metaphor"><span class="tl">比喻</span><p>' + esc(t.metaphor) + '</p></div>' +
      '<div class="term-pair">' +
        '<div class="term-like"><span class="tl">✅ 像的地方</span><p>' + esc(t.like) + '</p></div>' +
        '<div class="term-unlike"><span class="tl">⚠️ 不一样的地方</span><p>' + esc(t.unlike) + '</p></div>' +
      '</div>' +
      '<details class="term-more"><summary>多视角(' + (t.views || []).length + ') 与延伸阅读</summary>' +
        '<ul class="term-views">' + views + '</ul>' +
        (links ? '<div class="term-links"><span class="tl">站内延伸</span>' + links + '</div>' : '') +
      '</details>';

    host.appendChild(el);
  });

  var n = document.getElementById('glossary-count');
  if (n) n.textContent = GLOSSARY.length;
})();
