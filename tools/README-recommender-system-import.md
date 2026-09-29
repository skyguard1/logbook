# 推荐系统 HTML 导入

将 `~/Documents/推荐系统` 的离线 HTML 导入当前 `logbook` 知识库的 **推荐系统** 分类，不新建 Git 仓库，不合并/覆盖已有“推荐算法”分类。

## 运行

在仓库根目录执行（Python 3.10+）：

```zsh
python3 -m venv /tmp/logbook-html-venv
/tmp/logbook-html-venv/bin/pip install --index-url https://pypi.org/simple -r tools/requirements-import.txt
/tmp/logbook-html-venv/bin/python tools/import_recommender_system_html.py --dry-run
/tmp/logbook-html-venv/bin/python tools/import_recommender_system_html.py
```

可通过 `--source /绝对路径` 指定另一份本地导出，通过 `--repo /仓库路径` 指定目标（需有 `_config.yml`）。不请求远程图片或读取源目录以外的资源。

## 输出

- 文章：`source/_posts/recommender-system/<主题>/`
- 图片：`source/images/recommender-system/`
- 清单：`tools/recommender-system-import-manifest.json`
- 分类：推荐系统 → 知识图谱与图学习、特征工程、召回与匹配、排序与全链路优化、系统架构与工程实践、大数据基础、推荐系统基础与架构。

本次 39 个 HTML 中有 37 篇正文、818 张去重图片（827 处成功图片引用），12 处图片引用缺少本地资源。缺图位置显示 `[图片未保存到本地]`，不伪造图片。视频知识图谱 CNCC2021、通用知识图谱构建与应用两篇仅有预览壳，已跳过，未自动导入附件 PDF/PPTX。

标题保留技术系列、编号、会议与年份；从标题/正文中清理识别出的公司、部门、平台后缀、组织邮箱及内部链接。代码、表格、可提取公式和本地图片尽量保留。移除正文脚本、内联样式及页面外围导航，使用主题样式，避免导出 HTML 影响主页和侧栏。资源路径按 `_config.yml` 的站点根路径生成，兼容 `/logbook/` 部署。

清单以哈希管理输出。重复导入结果保持一致；如果手工修改了已管理文章/图片，下次导入会报错而不是覆盖。请先备份并人工合并，不要绕过保护。源 HTML 和其他分类不受影响；本工具不执行 Git 提交或推送。

## 验证

```zsh
PYTHONDONTWRITEBYTECODE=1 /tmp/logbook-html-venv/bin/python -m unittest discover -s tools -p 'test_import*html.py'
# 使用与项目兼容的 Node（本次验证为 Node 20.19.0）
npm run clean
npm run build
/tmp/logbook-html-venv/bin/python tools/validate_recommender_system_import.py
```

可选浏览器验证（macOS，已安装 Google Chrome）：

```zsh
/tmp/logbook-html-venv/bin/pip install --index-url https://pypi.org/simple playwright==1.63.0
npm run server -- --port 4017
# 另一个终端运行：
/tmp/logbook-html-venv/bin/python tools/validate_recommender_system_import.py --origin http://127.0.0.1:4017
```

验证器检查清单完整性、全部生成图片、标题、分类与正文脱敏；浏览器模式检查 1440/800/390px 布局、标题截断、侧栏位置和图片解码。

## 脱敏与使用限制

自动清理针对可识别的文本节点及 SVG 文本。**未对位图中的公司标识、水印、姓名、业务数据进行 OCR 或人工逐图审核**，也不保证所有未列入规则的组织名称都已移除。PNG 文本元数据会清理，但不代表所有格式的元数据均已清理。公开发布前仍需审核截图和文章内容，并确认转载许可、引用与署名要求；个人本地保存不等于有权公开发布。
