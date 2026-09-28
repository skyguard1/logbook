# 深度学习与算法：图片恢复与验证

## 已确认的原因

- 深度学习旧文章有 98 篇，但正文中 `<img>` 数量和本地图片数量均为 0。旧导入器在路径解析前改写组织名称，破坏了含组织后缀的 `_files` 路径；跨段清理正则也会删除正文。
- 算法分类的图片在本地存在，但未提交的文件不会被 GitHub Actions 构建，因此本地验证不代表线上已发布。
- 部分 SVG 不能用 HTML 方式重新序列化；现按 XML 处理。PNG 的文本/EXIF 附加块剥离，不更改像素、透明度、调色板等图像数据。

## 修复范围

| 分类 | 文章 | 有效图片引用 | 去重图片 | 原资源缺失引用 |
| --- | ---: | ---: | ---: | ---: |
| 深度学习 | 96 篇正文恢复；2 篇文档预览说明保留 | 1,366 | 1,313 | 3 |
| 算法 | 110 | 1,963 | 1,877 | 64 |

深度学习文章文件名、日期、分类和访问链接保持原样，不引入之前未导入的其它页面。
首次迁移要求现有深度学习文章已经提交且没有本地改动；原文章 ZIP 备份保存在 `.git/import-backups/`，不会推送。

## 安装及重复运行

```zsh
python3 -m venv /tmp/logbook-import-venv
/tmp/logbook-import-venv/bin/python -m pip install -r tools/requirements-import.txt
/tmp/logbook-import-venv/bin/python tools/repair_deep_learning_images.py
/tmp/logbook-import-venv/bin/python tools/import_algorithm_html.py
/tmp/logbook-import-venv/bin/python -m unittest discover -s tools -p 'test_*.py' -v
```

只有首次迁移旧版文章、且尚无 `tools/deep-learning-import-manifest.json` 时才使用 `--adopt-legacy`。
后续重跑依据清单校验；手工编辑过的文章不会被覆盖。
旧 `import_km_html.py --only deep-learning` 入口遇到迁移标记会退出，不会删除恢复的资源。

## 验证与预览

```zsh
nvm use 20.19.0
npm run clean
npm run build
/tmp/logbook-import-venv/bin/python tools/validate_imported_images.py
npm run server
```

在另一个终端执行：

```zsh
/tmp/logbook-import-venv/bin/python tools/validate_imported_images.py --base-url http://127.0.0.1:4000
```

该检查覆盖两类文章及全部图片 URL，确保本地文件、生成的 HTML、HTTP 200 和 `image/*` MIME 对应一致。
本地浏览器入口为 `http://localhost:4000/logbook/`。不能用 `file://` 直接打开 `public/*.html` 检验以 `/logbook/` 开头的站点绝对路径。

这次修复已额外使用 Chrome 验证 3,190 个 HTTP 图片 URL 全部可解码，并在两类代表性文章中确认图片有实际显示尺寸。

## 发布与内容审核

GitHub Pages 只构建已提交并推送到工作流触发分支的文件；仅本地存在的算法文章或图片不会自动上线。
请同时提交正文、`source/images/` 下的图片、清单及脚本，等待 Pages 工作流部署成功后再检查线上。
截图中的公司标识、水印、个人信息和业务数据仍需人工确认；脚本的文本清理不能代替截图审核和发布授权。

