'use strict';

const { parseFragment, serialize } = require('parse5');

// Only old HTML imports use the broken wrapper extraction. New DOM importers,
// Markdown posts, home cards and the global theme layout need no changes.
const LEGACY_SOURCE = /^_posts\/(?:es|linux|kubernetes)\//;

hexo.extend.filter.register('after_post_render', function normalizeLegacyArticle(data) {
  const source = String(data.source || '').replace(/\\/g, '/');
  if (!LEGACY_SOURCE.test(source)) return data;

  // Parse the RENDERED HTML in isolation. This matters: Markdown converts some
  // imported divs into code text, so balancing source tags alone is insufficient.
  // HTML5 tree construction discards stray closing tags and closes open formatting
  // elements before serialization, keeping them inside the article boundary.
  for (const field of ['content', 'excerpt', 'more']) {
    if (typeof data[field] === 'string' && data[field]) {
      data[field] = serialize(parseFragment(data[field]));
    }
  }
  return data;
}, 100);

