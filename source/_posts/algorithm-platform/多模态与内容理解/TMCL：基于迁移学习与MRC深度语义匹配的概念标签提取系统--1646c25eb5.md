---
title: "TMCL：基于迁移学习与MRC深度语义匹配的概念标签提取系统"
date: 2022-04-16 13:32:48
categories:
  - 算法平台
  - 图学习与内容理解
---

{% raw %}

<div>
<div>
<p>       作为移动互联网时代的重要应用，信息流是以解决信息过载问题而提出的，简单概括为：互联网经过持续发展积累了海量的数据和内容，这些信息如果不加筛选、甄别、匹配而直接推给用户，必然导致用户无法有效处理和利用。有别于传统的搜索引擎和RSS，信息流希望实现一种自动的个性化智能分发机制，即通过收集和分析用户消费内容时的各种隐式或半显示反馈信号，构建用户兴趣画像，并使用推荐算法对用户和内容进行智能匹配。因此，对内容的理解至关重要，目前比较常见的内容特征是分类和标签，但是当前以实体为主的标签体系在内容刻画的精准度、抽象概念的提取能力上都存在一定的缺陷，本文主要介绍我们在图文概念标签提取上的实践。</p>
<p>       目前，博通内容理解平台已集成该概念标签提取系统TMCL（Transfer learning and MRC semantic matching for concept-label extraction），欢迎大家体验和接入。博通是一个专注于信息流推荐场景的多模态内容理解平台，由 NLP技术中心打造。</p>
<p>       博通技术系列文章：</p>
<p>基于Labeled LDA的层次细粒度主题挖掘</p>
<p>基于先验和弱后验融合的多目标文章影响力预估</p>
<p>MMCN: 基于多模态协同的视频分类网络</p>
<p>       下面，本文将对博通平台所纳入的概念标签挖掘技术进行详细介绍。</p>
<p><strong>1. 任务背景</strong></p>
<p>       精准性和泛化性作为推荐系统的两个核心问题，离不开对内容的深入理解。其中精准性需要对内容进行全面精准的刻画，抽取出语义聚焦的标签。如图1-1所示，这两篇文章在传统的标签系统中可能都会提取出“机场”，但是用户消费的真实关注点天差地别：第一篇“机场”是文章主体，大概率也是用户关注焦点；而第二篇的“机场”更多是一个辅助限定词，理想情况下应该抽取出类似“明星机场照”的概念标签。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f16d05780b4a282aaec3.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ff35cc49f1b8f506e013.png"/></p>
<p>图1-1 “机场”相关内容</p>
<p>       而泛化性主要解决信息茧房的问题，如图1-2所示，若对这两篇文章的理解都只停留在表面的实体标签上（“羊肉汤”、“萝卜”），可能会导致推荐引擎给用户推送其他偏重复的内容，进而无法获取更广泛的信息；而如果能提取出两者共性的概念性标签“冬季进补”，则让系统具备了兴趣拓展的可能性。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/999277cf9a61301c62d6.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/bf2a4b248ab9594639bb.png"/></p>
<p>图1-2 “冬季进补”相关内容</p>
<p>2. 整体技术框架</p>
<p>       概念标签提取主要分为概念标签离线挖掘与在线语义匹配两大部分，离线挖掘部分主要负责构建高质量和高覆盖的概念标签库；在线语义匹配部分主要负责从概念标签库中匹配得到文章高相关度的概念标签。整体技术框架如图2-1所示：</p>
<div>
<div>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8a26a0b005cf49f9bfec.png"/></p>
</div>
</div>
<p>图2-1 整体技术框架</p>
<p>       离线挖掘部分我们采用了模版挖掘与算法挖掘相结合的方式去构建高质量的概念标签库；在线部分我们采用了基于机器阅读理解（MRC）的框架完成文章与候选概念标签的语义匹配，并通过领域相关数据进行多阶段的迁移学习以优化匹配效果。接下来分别详细介绍这两部分的方法和演进。</p>
<h2>3. 概念标签挖掘</h2>
<div>
<div>
<p>       我们在概念标签挖掘方面尝试了模板挖掘和算法挖掘两种方法。接下来将分别介绍：</p>
<p><strong>3.1 模板挖掘方法</strong></p>
<p>       概念标签一般是由中心词+属性词组合的短语形式。其中中心词主要是实体标签词，属性词是使得中心词语义更加聚焦的相关词语。比如概念短语是【白血病症状】，其中心词为【白血病】，属性词为【症状】。我们目前可用的数据资源如下：</p>
<div>
<div>
<div>
<div>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p></p>
<p>数据类型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>数据量</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>举例</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>用户query数据</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>2.3亿+</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>白血病有哪些症状？</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>实体+术语库</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>200W+</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>甘草、带鱼、白血病</p>
</td>
</tr></tbody></table></div>
</div>
<p>表3-1 数据资源</p>
<p>       选择用户在浏览器上的query数据作为挖掘数据来源的理由：</p>
<ol><li>
<p>用户检索query跟我们要挖掘的概念标签相近，方便进行挖掘。</p>
</li>
<li>
<p>用户在浏览器上的检索行为可体现其真实关注和需求，且实时性强，可以迁移到信息流的概念标签提取任务上。</p>
</li>
</ol><p>       接下来介绍我们在模板挖掘上的工作和演进：</p>
<p><strong>3.1.1 基于词性挖掘方法</strong></p>
<p>       观察概念标签的中心词与属性词一般为名词或动词，因此我们可以用qqseg分词工具对输入query的词性进行标注，将名词和动词两两组合得到候选短语，再通过统计特征进行筛选过滤，方法如下所示：</p>
<div>
<div>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/05b198712f2d907a3399.png"/></p>
<p>图3-1 基于词性挖掘方法</p>
<p>       该方法受限于分词工具的效果，准确率不高。</p>
<p><strong>3.1.2 基于pattern挖掘方法</strong></p>
<p>       尝试使用模板（pattern）挖掘方法，该方法的核心是需要挖掘一批高质量的pattern，例如：(.*)的(.*)有哪些。pattern挖掘的过程可以分为【回标-&gt;替换-&gt;过滤】三步，以财经领域为例：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/27fb3a158d75babedc98.png"/></p>
<div>
<div>
<p>图3-2 基于pattern挖掘方法</p>
<ol><li>
<p>利用已有的实体+术语库回标query文件得到样本。</p>
</li>
<li>
<p>将样本里命中实体/术语的部分替换为(.*)，作为候选pattern。</p>
</li>
<li>
<p>人工对TOP-N的候选pattern进行审核过滤，得到最终pattern。</p>
</li>
<li>
<p>用最终pattern在新的query中挖掘概念短语。</p>
</li>
</ol><p>       该方法需谨慎设置过滤条件，泛化性和灵活性较差。</p>
<div>
<div>
<p><strong>3.1.3 基于句法分析挖掘方法</strong></p>
<p>       观察概念标签是有一定组合模式：中心词+属性词，而且二者可以分开处理。我们从现有的实体库可以得到中心词，那么挖掘重点落到了属性词上。在属性词挖掘上我们选择句法分析方法，如下图所示：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/fe4765e0ebd9fb091223.png"/></p>
<p>图3-3 基于句法分析方法</p>
<ol><li>
<p>将query内的实体词（中心词）替换为root。</p>
</li>
<li>
<p>句法分析得到【HED、HED-VOB、HED-IOB、HED-FOB】指向的名词和动词，例如"上市"可看做是属性词。</p>
</li>
<li>
<p>拼接中心词和属性词，作为概念短语。例如“茅台公司”+ "上市"="茅台公司上市"。</p>
</li>
</ol><p>       该方法受限于句法分析工具的效果，同时依赖高覆盖的实体词库。</p>
<div>
<div>
<p><strong>3.2 算法挖掘及演进</strong></p>
<p>       基于模板挖掘概念标签的方法，可移植性差、可扩展性不高、泛化性不强。为了增加挖掘泛化性，我们尝试使用模型来挖掘。考虑到概念标签挖掘类似于摘要生成，所以我们选择摘要生成任务的常用模型--生成模型（seq2seq+attn），这里我们使用指针生成网络（pointer-generator Networks）来离线自动挖掘概念短语。指针生成网络的原理是在传统seq2seq+attn模型上引入了pointer机制解决未登录词（OOV）问题。模型结构如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/20951493a9e69815b5e4.png"/></p>
<p>图3-4 指针生成网络结构</p>
<p>       在模型敲定情况下，概念标签挖掘任务要求有大规模的标注数据，显然人工标注是不现实的。考虑到用户在浏览器上搜索的内容可以看做其对应点击标题的概括，具有总结性。所以我们使用用户的搜索query和点击title作为训练数据，其中Encoder为点击title，Decoder为搜索query，如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4655c2be032ace166de8.png"/></p>
<p>图3-5 用户搜索query-title pair</p>
<p>       接下来介绍我们在模型挖掘上的工作和演进：</p>
<div>
<div>
<p><strong>3.2.1 初始版本</strong></p>
<p>       我们使用原始query log数据训练指针生成网络，模型生成效果如下列所示：</p>
<div>
<p>输入：痔疮严重的话会有什么危害？</p>
<p>输出：痔疮严重的话会怎么样</p>
</div>
<p>       从case可以看出，模型生成内容是非短语形式，更像是输入句子的改写，这不符合我们的要求。我们对训练数据进行评估：发现其中大量句子式的query数据，导致生成结果不符合短语要求。</p>
<p><strong>3.2.2 数据优化</strong></p>
<p>       我们定义的概念标签需满足精简的语法形式，避免过于口语化的表达，保证得到标签的概括性和规整性，例如：丙肝治疗、仙人掌功效。对不满足该条件的query-title数据进行过滤，包括：</p>
<ul><li>剔除非短语式query：对不满足&lt;名词+动词&gt;、&lt;动词+名词&gt;、&lt;人名+动词&gt;等词性组合的query进行过滤</li>
</ul><div>
<div>
<div>
<p>query：仙人掌能治烫伤吗</p>
click title：为什么仙人掌能治疗烫伤？</div>
<ul><li>剔除IP类实体：Encoder输入（点击标题）直接为一个实体，跟我们任务不符</li>
</ul><div>
<p>query：僵尸倾城</p>
click title：重生僵尸道长</div>
<ul><li>剔除不通顺、不完整的query</li>
</ul><div>
<p>query：天秤喜欢</p>
click title：十二星座会用什么奇葩理由拒绝不喜欢的人？天秤：我配不上你</div>
<ul><li>剔除相似度较低的query-title pair</li>
</ul><div>
<p>query：揩油女星</p>
<p>click title：国内一线女星的片酬</p>
</div>
<p>用清洗后的数据重训指针生成网络，生成结果满足短语形式，如下例所示：</p>
<div>
<p>输入：痔疮严重的话会有什么危害？</p>
<p>输出：痔疮危害</p>
</div>
<p>人工评估生成概念短语的准确率为80%。但是通过分析case，发现模型存在对较长的实体词边界学习不准的问题：</p>
<div>
<p>输入：小伙自制布加迪威龙，拥有豪车不是梦，成本只花了1万！</p>
<p>输出：自制迪威龙</p>
</div>
<div>
<div>
<p><strong>3.2.3 实体匿名化</strong></p>
<p>       针对模型对实体边界学习不准问题，我们对实体词进行匿名化处理，来减小模型学习难度。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f85ade4636c8ea6f3619.png"/></p>
<p>图3-6 实体匿名化</p>
<p>       以汽车垂类为例，我们将Encoder输入里的实体词用符号[entity]替换，然后把Decoder输出中的[entity]映射回实体词，从而保证模型生成的实体词是完整准确的，人工评价准确率提升7%。</p>
<h2>4. 概念标签语义匹配</h2>
<div>
<div>
<p>       给定文章，匹配任务的目标是从大量的概念标签库中得到能表达文章中心主旨的概念标签，图4-1给出了概念标签“鸡爪吃法”匹配的示例过程：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/79833cdca7fac3be4652.png"/></p>
<p>图4-1 概念标签匹配</p>
<p>       针对该任务的特点，我们尝试了从传统匹配方法到深度匹配模型的探索，整体技术演进方案如图4-2所示：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/33bc883d0ed2dbad4eb7.png"/></p>
<p>图4-2 概念标签匹配技术演进</p>
<p><strong>4.1 传统匹配方法</strong></p>
<p>       为了便于快速迭代，我们首先尝试了传统方法完成概念标签匹配任务，主要包括无监督策略排序的方法与基于GBDT模型的分类方法。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b58cabe91af3a4a55f1e.png"/></p>
<p>图4-3 传统匹配方法</p>
<p>       给定一篇文章，我们首先将文中高频的中心词和属性词进行组合，并通过概念标签库进行筛选，得到候选概念标签。对于无监督排序方法，我们通过人工设定的打分策略对候选概念标签进行打分排序，并选取高分的候选作为文章的概念标签。</p>
<p>       由于策略泛化性有限且难以人工设定阈值，我们设计了基于GBDT的二分类模型。给定文章与候选标签，我们对每个候选标签进行特征抽取，在此基础上通过GBDT分类模型确定该候选是否为文章的概念标签，模型的训练样本来源于高置信的策略标注数据。</p>
<p>       两者效果对比如表4-1所示：</p>
<div>
<div>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p></p>
<p>模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>覆盖率</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>准确率</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>无监督策略</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.401</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.673</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>GBDT分类模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.476</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.714</p>
</td>
</tr></tbody></table></div>
</div>
<p>表4-1 传统匹配方法效果对比</p>
<p>       对比两者效果可发现使用GBDT分类模型要比策略方法更具有泛化性，但传统机器学习方法仍然存在特征难以人工设计等问题。因此，我们进一步探索了深度模型在概念标签匹配任务上的应用。</p>
<div>
<div>
<p><strong>4.2 双塔匹配模型</strong></p>
<p>       文章和概念标签语义匹配实际上可以看作一个排序问题，给定文章，对所有候选概念标签打分排序。在GBDT模型当中，我们将概念标签匹配问题建模为对输入文本对（文章、标签）的一个分类问题，即point-wise的排序。进一步，我们将标签匹配问题视为一个pair-wise排序任务，使用双塔模型分别编码文章和短语，其中每个样本是一个三元组（文章、正例短语、负例短语）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/61c52c4b5040a40f5e36.png"/></p>
<p>图4-4 双塔匹配模型</p>
<p>       如图4-4所示，正负例短语共享一个短语编码器，使用margin triplet loss作为损失函数[5]，希望模型学习到正负例短语之间的偏序关系，从而间接完成对所有候选短语的打分：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/431f1634189b215aaea9.png"/></p>
<p>       我们分别尝试了textcnn和bert作为编码器，最终效果相比GBDT有一定提升（+2.3%）。但在进一步迭代模型时，我们发现双塔模型存在诸多不足：</p>
<ul><li>
<p>匹配开销大：双塔同GBDT一样，训练与预测均需要对所有候选短语进行逐一匹配，随着模型建模越来越复杂，逐一匹配的开销较大。</p>
</li>
<li>
<p>语义表示不对称：与常规语义匹配不同，概念标签(平均长度约为4个字)和文章(平均长度约为200个字)两部分的信息量差异大，分别编码难以编码到一个可比的向量空间。</p>
</li>
<li>
<p>文章与短语间缺乏交互：匹配任务中文章与概念短语的交互是不可或缺的，而双塔结构难以显式体现交互过程。</p>
</li>
<li>
<p>候选短语之间缺乏交互：在实际训练中，每次只能有一对正负例标签交互，难以学习到短语间细粒度的区分，从而导致大部分候选的分数很接近，如图4-5所示：</p>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f75d058ec5f0f3b874f8.png"/></p>
<p>图4-5 双塔模型打分结果</p>
<div>
<div>
<p><strong>4.3 基于MRC的匹配模型</strong></p>
<p>       因此我们意识到，需要一种新的建模方式完成更进一步的模型优化，这种方式能够满足：</p>
<ul><li>
<p>比较充分的建模概念标签与文章之间、概念标签与概念标签之间的关系。</p>
</li>
<li>
<p>一次性完成所有候选概念标签的匹配。</p>
</li>
</ul><p>       最终受机器阅读理解任务（Machine Reading Comprehension，MRC）[6]的启发，我们提出了基于MRC的概念标签匹配模型，模型结构如图4-6所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/de2d5e44dcac16033a4c.png"/></p>
<p>图4-6 基于MRC的概念标签匹配模型</p>
<p>       常规的MRC任务为：给定上下文和问题作为输入，模型需要根据问题，在上下文中找出答案。在概念标签匹配场景下，我们将文章作为问题，所有的候选概念标签的拼接作为上下文，答案即为正确的概念标签。基于MRC的建模方法能够解决我们在双塔模型中遇到的缺乏交互，无法一次完成所有匹配等问题。</p>
<p>       具体的，我们使用了基于BERT的阅读理解模型。常规的BERT解决MRC是通过span标注形式实现的[4]，即标注出候选概念标签的开始和结束位置，该方法的问题是只能提取出一个概念标签。因此，我们引入了基于序列标注的MRC模型，使用BIO标签在候选短语序列中找出所有正确的概念标签。</p>
<p>       此外，我们还在输入文章序列之前拼接了该文章的一些先验信息，例如文章的分类信息等。通过显式加入先验知识，我们希望能帮助模型更好学习得到文章的语义表示。实验发现加入先验知识能对模型带来1.38%的提升。</p>
<p>       最终MRC模型性能的对比结果如下：</p>
<div>
<div>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p></p>
<p>模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>覆盖率</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>准确率</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>无监督策略</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.401</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.673</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>GBDT分类模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.476</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.714</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>MRC匹配模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.485</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.752</p>
</td>
</tr></tbody></table></div>
</div>
<p>表4-2 基于MRC的匹配模型效果对比</p>
<p>       根据上述结果可以看出MRC匹配模型具有明显的优势。</p>
<div>
<div>
<p><strong>4.4 基于迁移学习的模型训练优化</strong></p>
<p>       除了模型结构优化之外，我们面临的另外一大挑战就是缺乏标注数据（上述模型的训练数据仅有少量来自高置信的策略标注数据）。为缓解该问题，参考论文[2]的经验，我们利用了不同形式的多个数据源，采用了多阶段微调，根据任务相关性从远到近进行迁移学习，让模型充分学习所有数据中隐含的文本匹配模式。如图4-7所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/abeff5f2ff788d3fd6b8.png"/></p>
<p>图4-7 基于多领域数据迁移的模型训练优化</p>
<p>       首先我们从QQ浏览器的搜索日志中挖掘搜索query和对应点击文章，将query作为正例短语。query数据包含了来自用户点击的监督信号，且数据规模较大，其缺点在于query和真正的概念标签形态存在一定差距。因此我们尝试进一步使用更接近的数据源。</p>
<p>       第二阶段微调的数据源则来自博通平台用于层次分类训练的大规模高质量的人工标注数据。通过观察我们发现许多概念标签与二三级分类语义比较相近，如图4-8所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f77f4348bdac251e3681.png"/></p>
<p>图4-8 层级分类体系</p>
<p>       我们将层次分类任务转换为标签匹配任务来利用分类任务的训练数据。具体而言，将文章所属父类下的所有子类作为候选，文章所属的子类作为匹配结果。通过该阶段的微调，模型能够学习到细粒度的语义区分。</p>
<p>       最终的效果也验证了我们多阶段多数据源微调的有效性，结果如表4-3所示：</p>
<div>
<div>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p></p>
<p>模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>覆盖率</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>准确率</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>无监督策略</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.401</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.673</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>GBDT分类模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.476</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.714</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>MRC匹配模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.485</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.752</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>+query数据预训练</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.489</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.812</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>+分类数据预训练</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.531</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.845</p>
</td>
</tr></tbody></table></div>
</div>
<p>表4-3 基于多领域数据迁移的模型训练效果对比</p>
</div>
</div>
<div>
<div>
<p>       除了模型和数据上的优化尝试，我们也借鉴了[3]的思路，希望在任务层面能引入与概念标签匹配相关的任务联合训练以改进模型的性能。与上述引入分类数据预训练不同的是，此处是在任务层面将分类作为辅助任务进行多任务学习。值得注意的是，在多任务学习中我们显式引入了任务标识以区分两个任务。如图4-9所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/fec9f931aad22585cec1.png"/></p>
<p>图4-9 基于多任务迁移的模型优化</p>
<p>       引入分类辅助任务后模型的覆盖率与准确率评估结果如表4-4所示，通过结果对比可知这种引入外部任务进行多任务学习的方法可以有效提升模型的性能。</p>
<div>
<div>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p></p>
<p>模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>覆盖率</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>准确率</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>无监督策略</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.401</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.673</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>GBDT分类模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.476</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.714</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>MRC匹配模型</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.485</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.752</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>+query数据预训练</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.489</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.812</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>+分类数据预训练</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.531</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.845</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>+分类辅助任务</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.541</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>0.856</p>
</td>
</tr></tbody></table></div>
</div>
<p>表4-4 基于多任务迁移的模型训练优化效果对比</p>
<p>5. 总结</p>
<p>       本文介绍了图文概念标签提取系统的背景和具体实现，包括离线挖掘以及在线深度语义匹配。目前所做的工作主要服务于看点信息流，特别感谢weidongguo(郭伟东)、danielmchen(陈立玮) 在项目推进过程中给予的帮助和指导。整个系统还在不断的迭代优化中，部分功能已整合到博通平台中，demo地址：[内部或本地链接已移除]</p>
<p><b>6. </b>引用</p>
<ol><li>
<p><a href="https://arxiv.org/pdf/1704.04368.pdf">Get To The Point: Summarization with Pointer-Generator Networks</a></p>
</li>
<li>
<p><a href="http://arxiv.org/pdf/2004.10964.pdf">Don’t Stop Pretraining: Adapt Language Models to Domains and Task</a></p>
</li>
<li>
<p><a href="https://arxiv.org/abs/1910.10683">Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer</a></p>
</li>
<li>
<p><a href="https://arxiv.org/abs/1810.04805">BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding</a></p>
</li>
<li>
<p><a href="https://arxiv.org/abs/1908.10084">Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks</a></p>
</li>
<li>
<p><a href="https://arxiv.org/abs/1907.01118">Neural Machine Reading Comprehension: Methods and Trends</a></p>
</li>
<li>
<p><a href="https://www.aclweb.org/anthology/N10-1108.pdf">Extracting Phrase Patterns with Minimum Redundancy for Unsupervised Speaker Role Classification</a></p>
</li>
<li>
<p><a href="https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&amp;arnumber=6457440">Learning Phrase Patterns for Text Classification</a></p>
</li>
<li>
<p><a href="https://www.microsoft.com/en-us/research/wp-content/uploads/2014/09/is2014.AlexMarin.pdf">Learning Phrase Patterns for Text Classification Using a Knowledge Graph and Unlabeled Data</a></p>
</li>
</ol></div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
<p></p> 
{% endraw %}
