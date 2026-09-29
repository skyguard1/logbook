# 推荐算法资料导入

来源：`~/Documents/推荐算法`。输出位于当前 `logbook` 知识库，而非另建 Git 仓库。

## 内容与分类

- 文章：`source/_posts/recommendation/<技术主题>/<完整标题>--<稳定标识>.md`
- 图片：`source/images/recommendation/<内容摘要>.<实际图片格式>`
- 清单：`tools/recommendation-import-manifest.json`，含逐篇标题、来源/输出字数、图片统计、文件校验值和跳过原因。
- Hexo 分类：**推荐算法 → 技术主题**。

主题包括图学习与社交推荐、跨域推荐与冷启动、多任务与多目标优化、召回排序与匹配、多模态与用户画像、训练平台与实时工程、推荐算法基础。
正文基于 DOM 提取；本地保存的 iframe 正文也会检查，资源目录中的 HTML 不会重复作为文章导入。
会议名称、年份和技术系列名称保留，标题连字符不作为 YAML 分隔符处理。

本批资料共 35 个源 HTML：32 篇正文已导入；3 个产品介绍/白皮书导出只有预览页，列入清单，不生成空文章。
有效图片引用 687 处，去重后 682 个图像文件。71 处原始图片引用没有可用本地资源，正文使用缺图提示。

## 执行导入

Python 3.10+，在知识库根目录执行：

```zsh
python3 -m venv /tmp/logbook-import-venv
/tmp/logbook-import-venv/bin/python -m pip install -r tools/requirements-import.txt
/tmp/logbook-import-venv/bin/python tools/import_recommendation_html.py --dry-run
/tmp/logbook-import-venv/bin/python tools/import_recommendation_html.py
```

可用 `--source /路径/推荐算法` 指定来源，`--repo /路径/logbook` 指定知识库。
导入只管理推荐算法清单内的文件；如果生成文件有手工改动，拒绝覆盖。
原始 HTML 不修改，不下载内网资源，不执行原网页脚本。
算法、深度学习、ES/Linux/Kubernetes 分类及各自导入清单不变。

## 验证

```zsh
/tmp/logbook-import-venv/bin/python -m unittest discover -s tools -p 'test_*.py' -v
nvm use 20.19.0
npm run clean
npm run build
/tmp/logbook-import-venv/bin/python tools/validate_recommendation_import.py
npm run server
```

本地打开 `http://localhost:4000/logbook/`，在分类栏选择“推荐算法”。
可选浏览器测试（需要安装 Playwright；macOS 优先使用已安装的 Chrome）：

```zsh
/tmp/logbook-import-venv/bin/python -m pip install playwright
# 没有 Chrome 时：/tmp/logbook-import-venv/bin/python -m playwright install chromium
/tmp/logbook-import-venv/bin/python tools/validate_recommendation_import.py --origin http://127.0.0.1:4000
```

## 脱敏与发布

文本清理覆盖已知公司名、部门名称、平台归属后缀及内部链接/组织邮箱。
公开技术引用与会议名称不是公司归属标签，不冒充个人原创。
自动文本处理不保证截图中的水印、姓名或业务数据已经脱敏，发布前仍需人工审核图片及资料使用权限。
本工具不会自动提交或推送 Git；本地生成不等于 GitHub Pages 已部署。

