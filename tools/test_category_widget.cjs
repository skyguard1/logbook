'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ejs = require('ejs');
const Database = require('warehouse').default;
const listCategories = require('hexo/dist/plugins/helper/list_categories');
const template = fs.readFileSync(path.join(__dirname, '../themes/landscape/layout/_widget/category.ejs'), 'utf8');

async function render(rows, showCount = true) {
  const db = new Database();
  const categories = db.model('Category', new Database.Schema({
    _id: String, name: String, parent: String, path: String, length: Number
  }));
  await categories.insert(rows);
  const site = {categories: categories.find({})};
  const before = JSON.stringify(site.categories.toArray());
  const context = {site, config: {root: '/logbook/', url: 'https://example.com/logbook/'}};
  const html = ejs.render(template, {
    site, theme: {show_count: showCount}, __: () => '分类',
    list_categories: (...args) => listCategories.apply(context, args)
  });
  assert.equal(JSON.stringify(site.categories.toArray()), before, 'must not mutate categories');
  return html;
}

(async () => {
  const rows = [
    {_id: 'rec', name: '推荐算法', path: 'categories/rec/', length: 32},
    {_id: 'rec-child', name: '推荐子类', parent: 'rec', path: 'categories/rec/child/', length: 10},
    {_id: 'rec-leaf', name: '推荐三级', parent: 'rec-child', path: 'categories/rec/child/leaf/', length: 2},
    {_id: 'algo', name: '算法', path: 'categories/algo/', length: 110},
    {_id: 'algo-child', name: '算法子类', parent: 'algo', path: 'categories/algo/child/', length: 12}
  ];
  const html = await render(rows);
  assert.match(html, /href="\/logbook\/categories\/rec\/">推荐算法<\/a><span class="category-list-count">32<\/span>/);
  assert.doesNotMatch(html, /推荐子类|推荐三级/);
  assert.match(html, /category-list-child/);
  assert.match(html, /算法子类/);
  assert.doesNotMatch(await render(rows, false), /category-list-count/);
  assert.match(await render(rows.slice(3)), /算法子类/);
  assert.equal((await render([])).trim(), '');
  console.log('PASS: recommendation collapsed, counts and other branches preserved, no metadata mutation');
})().catch(error => { console.error(error); process.exitCode = 1; });
