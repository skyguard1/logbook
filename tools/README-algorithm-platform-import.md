# 算法平台知识库导入

将 `~/Documents/算法平台` 中的离线 HTML 导入当前 `logbook` 的 **算法平台** 分类，不创建新 Git 仓库，也不覆盖“算法”“推荐算法”“推荐系统”等已有分类。

## 执行

在仓库根目录执行，使用 Python 3.10+：

```zsh
python3 -m venv /tmp/logbook-html-venv
/tmp/logbook-html-venv/bin/pip install --index-url https://pypi.org/simple -r tools/requirements-import.txt
PYTHONDONTWRITEBYTECODE=1 /tmp/logbook-html-venv/bin/python tools/import_algorithm_platform_html.py --dry-run
PYTHONDONTWRITEBYTECODE=1 /tmp/logbook-html-venv/bin/python tools/import_algorithm_platform_html.py
```

支持 `--source /绝对路径` 和 `--repo /目标仓库`。目标仓库须有 `_config.yml`。仅读取本地源目录内的资源，不访问公司内网或下载远程图片。

## 本次结果与输出

- 139 个 HTML → **133 篇正文**、8 个主题。
- 文章：`source/_posts/algorithm-platform/<主题>/`
- 图片：`source/images/algorithm-platform/`，**1,692 张去重图片**，1,791 处成功引用。
- 清单：`tools/algorithm-platform-import-manifest.json`，包含输出哈希、缺图计数及跳过原因。
- 主题：平台架构与系统设计、图学习与图计算、多模态与内容理解、特征工程与用户建模、召回与向量检索、排序与预估模型、训练与工程优化、实验评估与指标。
- 67 处引用没有本地资源，正文显示 `[图片未保存到本地]`；不会生成虚假图片地址。
- 6 个文件只有预览内容、无可提取正文，已跳过：实时推荐系统 PDF、OGB 比赛 PDF、Plato 分享 PDF、推荐思考与实践 PDF、智能推荐产品方案、精准推荐系统架构 PPTX。原文件及附件保持不变。

iWiki 的 Markdown/Cherry 宏会展开已经保存的本地预览 HTML，并重定位图片路径；不会把外层的 Base64 编辑器数据当作代码块写入文章。若宏预览未保存，导入会停止并报错，避免无声丢失正文。少量文章正文只有标题和架构图，按原内容保留，不凭空补写。

保留技术系列、编号及真正的技术副标题，不把所有 ` - ` 后的文字都视作部门信息。输出统一使用主题样式，不修改主页或文章 CSS。资源链接按照站点根路径生成，支持 GitHub Pages 的 `/logbook/` 前缀。

## 验证

```zsh
PYTHONDONTWRITEBYTECODE=1 /tmp/logbook-html-venv/bin/python -m unittest discover -s tools -p 'test_import*html.py'
# 本次构建验证使用 Node 20.19.0
npm run build
PYTHONDONTWRITEBYTECODE=1 /tmp/logbook-html-venv/bin/python tools/validate_algorithm_platform_import.py
```

macOS 已安装 Google Chrome 时可选浏览器检查：

```zsh
/tmp/logbook-html-venv/bin/pip install --index-url https://pypi.org/simple playwright==1.63.0
npm run server -- --port 4017
# 在另一个终端运行：
PYTHONDONTWRITEBYTECODE=1 /tmp/logbook-html-venv/bin/python tools/validate_algorithm_platform_import.py --origin http://127.0.0.1:4017
```

静态验证检查文章标题、分类、正文组织信息、全部生成图片及 HTML 容器关系。浏览器验证检查 1440/800/390px 下的标题、侧栏、页面溢出和所有正文图片解码。

## 重复导入与安全边界

- 导入清单只管理本分类的文章和图片，重复运行结果保持一致。
- 已管理文件被手工修改后，导入会拒绝覆盖；需先备份并人工合并，勿删除清单绕过保护。
- 文本层清理已识别的公司/部门名称、平台后缀、组织邮箱、内部 URL（包括部分无协议头或畸形地址）。公开开源项目引用、技术模型名、代码包名与学术引用尽量保留，不能将它们等同于组织归属信息。
- **位图中的水印、姓名、组织标识和业务数据未做 OCR 或逐图人工审核**；自动文本清理也不能保证所有未识别的名称被移除。公开前仍须审核截图、链接、代码和业务信息，并确认转载许可与署名要求。
- 工具不提交、不推送、不改变远程分支。
