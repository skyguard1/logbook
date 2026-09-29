# Flink 本地 HTML 导入

将 `~/Documents/flink` 导入当前 logbook 知识库的 `flink` 分类，不创建新仓库，也不自动提交或发布。

## 结果

- 5 个 HTML → 5 篇文章，4 个主题：基础原理与入门、监控与故障排查、实时数仓与工程实践、SQL与查询优化。
- 同目录的 ClickHouse SQL 优化文章一并保留。
- 正文：`source/_posts/flink/<主题>/`；图片：`source/images/flink/`。
- 103 处图片引用中，86 处保存成功（86 张去重图片），17 处无法从本地导出恢复，已标注 `[图片未保存到本地]`。
- 缺图分布：实时数仓文章 5 处，入门文章 12 处；其他三篇无缺图。
- 清单：`tools/flink-import-manifest.json`，记录完整标题、文件哈希和逐篇图片统计，不记录原始绝对路径。

## 使用

Python 3.10+，Node 使用本项目支持的版本（本次验证使用 20.19.0）。在仓库根目录运行：

```sh
python3 -m venv /tmp/logbook-flink-venv
/tmp/logbook-flink-venv/bin/pip install -r tools/requirements-import.txt
/tmp/logbook-flink-venv/bin/python tools/import_flink_html.py --dry-run
/tmp/logbook-flink-venv/bin/python tools/import_flink_html.py
/tmp/logbook-flink-venv/bin/python -m unittest discover -s tools -p 'test_import*.py'
npm run build
npm run test:layout
/tmp/logbook-flink-venv/bin/python tools/validate_flink_import.py
```

可用 `--source` 指定其他源目录；`--repo` 指定目标知识库。重复运行结果稳定，遇到手工修改的受管文件会拒绝覆盖。不要直接删除清单来绕过保护。既有分类和主题不修改，分类由 Hexo 自动生成。

可选浏览器检查（需要 Playwright 和 macOS Google Chrome）：

```sh
/tmp/logbook-flink-venv/bin/pip install playwright
npm run server -- --port 4017
# 在另一终端执行
/tmp/logbook-flink-venv/bin/python tools/validate_flink_import.py --origin http://127.0.0.1:4017
```

检查全部新文章在 1440、800、390px 下的完整标题、侧栏位置、页面溢出和图片解码。

## 内容清理与限制

复用现有 DOM 导入框架：保留正文、代码、表格与完整技术标题，移除已识别公司/部门名称、导出平台后缀、宣传元信息及内部链接；本地图片按内容识别类型并重写为站点子路径下的资源地址。不会下载内网图片或读取源目录之外的文件。

**不是完整匿名化或发布授权检查。** 截图中的公司标识、水印、姓名、业务数据没有经过 OCR 脱敏；正文中的技术示例、人员致谢和业务描述仍应人工审核。PNG 文本元数据和 SVG 中可识别文字按已有规则清理，但不保证所有格式的元数据均已移除。原始 HTML 不修改，公开发布前请确认权限并检查图片。
