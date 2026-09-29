# 算法 HTML 知识库导入

独立导入 `~/Documents/算法`，不修改 ES、Linux、Kubernetes、深度学习等已有文章。
使用 DOM 提取正文，不使用跨段正则删正文。保留代码、表格、公式及已保存到本地的图像。

## 安装与运行

要求 Python 3.10+。依赖在隔离环境安装，Hexo 的 npm 依赖不受影响。

```zsh
python3 -m venv /tmp/logbook-import-venv
/tmp/logbook-import-venv/bin/python -m pip install -r tools/requirements-import.txt
/tmp/logbook-import-venv/bin/python tools/import_algorithm_html.py --dry-run
/tmp/logbook-import-venv/bin/python tools/import_algorithm_html.py
/tmp/logbook-import-venv/bin/python -m unittest discover -s tools -p 'test_import_algorithm_html.py' -v
```

`--source /绝对路径/算法` 可更换来源；`--repo /绝对路径/知识库` 可更换输出根目录。
脚本只读取源 HTML 和其目录内本地资源；不访问内网，不下载远程资源，不执行页面脚本，不修改原文件。

## 输出结构

- 文章：`source/_posts/algorithm/<主题>/<标题>--<稳定标识>.md`
- 图片：`source/images/algorithm/<内容摘要>.<实际格式>`，跨文章去重。
- 导入清单：`tools/algorithm-import-manifest.json`，包含主题统计、跳过原因、每篇图片缺失数与生成文件校验值。
- Hexo 分类层级：**算法 → 技术主题**，可在分类侧栏逐级浏览。

主题包含图学习与知识图谱、强化学习与决策、数据科学与评估、特征工程、模型训练与推理、多模态与自然语言处理、推荐与排序、广告算法、数据工程与系统实践、综合实践。
分类按标题关键词确定，可在脚本的 `TOPICS` 中维护规则。


## 正文与图片

- 支持 KM、文本内容页、保存在本地 iframe 中的 iWiki 正文。
- 资源目录中的 HTML 不作为独立文章导入。
- 仅有 PDF/PPT 预览而没有可提取正文的页面会报告为跳过，不生成占位文章。
- 没有保存到本地的图片显示“图片未保存到本地”；不会保留失效内网图片地址，也不会假装全部图片可用。
- 文章内代码被还原为文本；移除平台 CSS/事件属性，避免影响主题布局。
- 公式中被导出为 SVG/MathML 的部分保留其图形或数学结构。

## 重复导入与安全边界

只覆盖清单中由本工具生成且校验值未变的文件；如果手工改过文章或存在同路径的未管理文件，导入会拒绝覆盖。
清单先于写入用于核验所有目标。解析在临时目录完成；没有有效源文件时不会清空已有分类。
同标题文章通过来源相对路径的稳定摘要区分。其它分类不会被重新生成。

文本清理包括来源标题后的组织后缀、已知公司/部门名称、内部链接和组织邮箱；公开论文引用及个人作者署名不冒充个人原创。
**自动脱敏不是公开发布授权，也不保证截图已经脱敏。图片内的公司标识、水印、姓名、业务指标和架构信息需要人工审核。**
本次导入不执行 Git commit/push。发布前请确认资料使用权限及剩余敏感信息。

## 本地预览

站点当前依赖需要 Node 20.19+。在项目根目录执行：

```zsh
nvm use 20.19.0
npm run build
/tmp/logbook-import-venv/bin/python tools/validate_algorithm_import.py
npm run server
```

根据 `_config.yml` 的站点根路径访问（当前为 `http://localhost:4000/logbook/`），打开“算法”分类。
