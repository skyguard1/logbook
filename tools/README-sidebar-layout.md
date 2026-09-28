# 旧文章侧栏布局回归

## 根因与修复

部分 ES/Linux/Kubernetes 离线文章包含多余的 `</div>`、未闭合的格式标签和交错结构。
插入完整网页后，浏览器会将侧栏重新放置到 `.main-outer` 之外。
因此不是图片宽度造成的 flex 换行，扩大或限制宽度不能解决这个问题。

`scripts/legacy-article-layout.js` 在 Hexo `after_post_render` 阶段使用 HTML5 解析器 `parse5`
将旧文章的 **已渲染正文** 作为独立片段规范化，再交给主题模板。
这避免正文关闭主题容器，并将未闭合的格式标签约束在正文内部。
不能只在 Markdown 源文件中计数 div：部分 HTML 会被 Markdown 当作代码转义。

范围仅限 `_posts/es/`、`_posts/linux/`、`_posts/kubernetes/`；
不改主题 CSS、不重写原文章、不影响算法和深度学习新导入内容。
旧导入器同时修正了空元素（如 img/br）导致提取深度失准的问题。

## 自动测试

```zsh
npm ci
npm run test:layout
python3 -m unittest discover -s tools -p 'test_legacy_article_layout.py' -v
npm run clean
npm run build
```

布局浏览器测试需要本地运行 Hexo server，并安装可选的 Playwright：

```zsh
python3 -m venv /tmp/logbook-layout-venv
/tmp/logbook-layout-venv/bin/pip install playwright
# macOS 默认使用已安装的 Google Chrome；其它环境可安装 Chromium：
# /tmp/logbook-layout-venv/bin/playwright install chromium
npm run server
```

另一个终端运行：

```zsh
/tmp/logbook-layout-venv/bin/python tools/validate_sidebar_layout.py
```

验证主页和全部旧文章，在 1440px、800px 下正文/侧栏为同级且侧栏在右；
390px 下保留响应式堆叠。验证默认使用当前站点根路径 `/logbook/`。

