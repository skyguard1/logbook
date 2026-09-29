'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const { JSDOM } = require('jsdom');
let filter;
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../scripts/legacy-article-layout.js'), 'utf8'), {
  require,
  hexo: { extend: { filter: { register(name, fn) {
    assert.equal(name, 'after_post_render');
    filter = fn;
  } } } }
});

for (const content of [
  '<p>text<img src="/logbook/images/a.png" alt="Test diagram"></p></div>',
  '<div><p>open wrapper</p>',
  '<pre>&lt;div&gt;sample&lt;/div&gt;</pre></div></div>',
  '<div><code>unclosed code</div>',
  '<table><div>foster-parented text</div><tr><td>cell</td></tr></table></footer>',
]) {
  const post = filter({source: '_posts/linux/example.md', content, excerpt:content, more:content});
  for (const field of ['content','excerpt','more']) {
    const dom = new JSDOM(`<div class="main-outer"><section id="main"><article><div class="entry">${post[field]}</div></article></section><aside id="sidebar">sidebar</aside></div>`);
    const doc = dom.window.document;
    assert.equal(doc.querySelector('#sidebar').parentElement, doc.querySelector('.main-outer'));
    assert.equal(doc.querySelector('#main').parentElement, doc.querySelector('.main-outer'));
    assert.equal(doc.querySelector('.entry').textContent, new JSDOM(content).window.document.body.textContent);
    assert.deepEqual([...doc.querySelectorAll('.entry img')].map(img => img.getAttribute('src')),
      [...new JSDOM(content).window.document.querySelectorAll('img')].map(img => img.getAttribute('src')));
  }
  assert.equal(filter({...post}).content, post.content, 'normalization must be idempotent');
}
for (const source of ['_posts/algorithm/a.md', '_posts/deep-learning/a.md', '_posts/hello.md', 'index.md']) {
  const post = {source,content:'<p>unchanged</p></div>'};
  assert.equal(filter({...post}).content,post.content);
}
console.log('PASS: rendered HTML remains inside article; code/text/images preserved; unrelated sources unchanged');

