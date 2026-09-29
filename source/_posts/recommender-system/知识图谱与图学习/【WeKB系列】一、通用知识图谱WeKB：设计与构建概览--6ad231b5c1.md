---
title: "【WeKB系列】一、通用知识图谱WeKB：设计与构建概览"
date: 2022-03-16 14:18:17
categories:
  - 推荐系统
  - 知识图谱与图学习
---

{% raw %}

<h1><strong>▌一、知识图谱简介</strong></h1>
<h2><strong>▌1.1 知识图谱的概念</strong></h2>
<p>知识图谱（Knowledge Graph, KG），又名知识库（Knowledge Base, KB），是结构化的实体、关系、属性的数据集。知识图谱包含了大量结构化、高质量的知识，能为自然语言处理应用提供丰富的知识支持。</p>
<p>我们可以用图的结构去看待KB这样一种数据形式，也就是KG。“Knowledge Graph”的概念最早由在2012年提出，用于其搜索右侧的信息展示框（Infoboxes）。今天的 KG包含十亿级别实体，作为一个基础能力服务于内部方方面面。很多企业也都有其自建的知识库，主要依托于一些通用知识图谱，并采用一系列信息抽取技术挖掘其自有的结构化、半结构化数据，进行知识的抽取。</p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/68a9e5ec7e9d1892d191.png"/></p>
<p>图一：KG与文本世界的关系</p>
<p> </p>
<p>KG与文本的关系是什么呢？在上图中，“甲壳虫”这个词汇是<strong>文本层面的表示</strong>，在知识库中，它会映射到<strong>实体（语义）层面的表示</strong>，例如词汇“甲壳虫”既有可能是一种昆虫，又有可能是一种汽车，也有可能是一种乐队。</p>
<p>KG中有几个主要概念：</p>
<ol><li><strong>实体（Entity</strong><strong>）。</strong>如上图的蓝色标记，“大众新甲壳虫”、“大众汽车”、“The_Beatles”等，每个对应一个真实世界的实体。</li>
<li><strong>实体之间的关系（Relation</strong><strong>）</strong>，如上图的黄色标记。例如“大众新甲壳虫”和“大众汽车”之间有一种“生产商”的关系。</li>
<li><strong>实体的类别（Types</strong><strong>）</strong>，如上图的绿色标记。例如“大众新甲壳虫”可能是一种“汽车型号”；“The_Beatles”可能是一个“乐队”。类别的本质还是实体与关系：“乐队”也是一个通用实体，但他是一个上位概念实体，两个实体之间可以有一种“类别”的特殊关系。</li>
<li><strong>其他属性（Properties</strong><strong>）</strong>，如实体的文本属性、别名、描述、出现过的文本（mentions） 等；关系的起止时间属性等。这些属性也是一种广义的关系（实体与非实体之间的关系）。</li>
</ol><p>总之，知识图谱是一种异构的，有多种实体与关系的图结构。“甲壳虫”是在文本世界（Text World）中的一种表示；实体、关系、类型、属性是在语义世界（Semantic World）中的表示。知识图谱应用的一个核心工作就是将文本世界与语义世界进行打通——实体链接（Entity Linking）。</p>
<p>常见的公开的知识图谱有Wikidata（包含2千万左右的实体）、DBpedia、Freebase等，以及中文的CN-DBpedia、Ownthink、大词林等等。</p>
<p><strong> </strong></p>
<h2><strong>▌</strong><strong>1.2 知识图谱的应用</strong> </h2>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/d81c8b580318e53f1338.png"/></p>
<p>图二：知识图谱的一些应用</p>
<p> </p>
<p>为什么说知识图谱是有用的呢？<strong>知识图谱中涵盖的高质量的知识可以帮助我们进行理解与推理</strong>。如上图，我们举了几个例子：</p>
<p>在<strong>智能问答</strong>（Question Answering）方面，一般用户会有一个问题（query），例如《哈利波特》一书的作者是谁（Author of Harry Potter）？我们首先将这个问题解析成一个结构化的查询语句（Semantic Parsing等方法）。然后将这个查询在知识库上执行，我们会发现J.K.Rawling这个节点和Harry Potter这个节点之间存在作者关系（author），因此返回J.K.Rawling就是这个问题的答案。</p>
<p>在<strong>结构化搜索</strong>（Faceted Search）中，用户可能有一些查询语句，如“我要去买300元以下的皮包”，把它解析为一个限定话的搜索：查询商品，满足材质是皮、商品种类是包，价格是300元以下。之后在商品的知识库中进行搜索，返回给用户一些最满足上述条件的商品。</p>
<p>在<strong>语义理解</strong>，包括查询、文档的理解（Query and Document Understanding）中： 比如用户的一个问题 “Ball Animal at Target”，是什么意思呢？如果有了知识图谱来辅助理解，就可以发现“Ball Animal”是一个戴森吸尘器的型号，“Target”是美国的一个连锁商场。这些词其实都是有歧义的，但是只要能和知识图谱进行准确的关联，那么我们就会得知：其实用户是想要在Target这个商场购买吸尘器。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/f04bd55f9521c42a6355.png"/></p>
<p>图三：知识图谱用于推荐系统 </p>
<p>知识图谱在<strong>推荐系统</strong>中也有应用。传统的推荐系统一般会基于用户与物品的交互，因此对于一些<strong>尾部的、缺乏交互的物品</strong>效果可能不是太好。我们如何基于知识图谱与内容理解的方法去提升尾部物品推荐的效果呢？如上图所示，用户点赞了一个视频，如果我们把视频的文本信息（发布者、描述、弹幕、OCR文本等）用知识图谱进行辅助理解，就能发现视频里的“霉霉”指泰勒·斯威夫特（女歌手）（/person/Taylor_Swift），“世界巡回演唱会”指的是1989年的World_Tour（/event/The_1989_World_Tour），“Love Story”是她的一首歌（/song/Love_Story_(Taylor_Swift)）等等。如果能够发现这些文本与实体之间的关联，那么我们就能在相应的知识图谱上做一定的扩展，例如我们可以给用户推荐泰勒·斯威夫特的其它演唱会的视频，以及与她相似的其它歌手的视频等，以及通过视频的核心表意实体构造用户的兴趣画像。如此就可以基于内容提升这个推荐系统的多样性与可解释性。当然，这只是一个简单的应用思路，近期也有很多论文探索KG在推荐中的应用，大家感兴趣的话可以去阅读。KG实际在推荐应用的场景中也会有很多新问题，我们在之后的系列文章中会娓娓道来。</p>
<p>在以上几个应用中，我们都看到了一个通用的步骤，即<strong>如何将文本映射到知识库中的实体</strong>。该问题被称为实体链接（Entity Linking），它是“连接文本与语义世界的桥梁”，在实际应用中发挥着重要的作用。我们会在后续的系列文章中，带领大家探索实体链接的研究进展与我们的部署经验。</p>
<p> </p>
<h1><strong>▌二、知识图谱的构建框架</strong></h1>
<h2><strong>▌2.1 关键模块一览</strong> </h2>
<p>知识库构建（Knowledge Base Construction, KBC）是构建一个知识图谱的整体技术。构建知识图谱WeKB的整体工作中，包括但不限于以下技术点：</p>
<ul><li>基础知识图谱和Ontology的选取</li>
<li>数据源的选取，包括多个结构化、半结构化、无结构化数据源</li>
<li>知识库构建的主要模块：
<ul><li>实体词抽取 (mention extraction)</li>
<li>关系抽取 (relation extraction)</li>
<li>实体链接 (entity linking)</li>
<li>指代消解 (coref resolution)</li>
<li>实体对齐 (entity alignment)</li>
<li>链路预测 (link prediction)</li>
<li>知识融合 (knowledge fusion)</li>
<li>新实体发现 (entity discovery)</li>
</ul></li>
<li>模块设计中的核心技术思路：
<ul><li>训练数据：基于KG的远程监督、基于语境模板的远程监督、结合标注数据</li>
<li>模型和特征的选择</li>
<li>错误分析、迭代工具</li>
<li>可视化工具</li>
</ul></li>
<li>知识库构建系统上线，需要考虑：
<ul><li>知识运营，实时修正关键事实</li>
<li>知识的更新频率</li>
<li>基于WeKB的查询、文本理解、推理与联想、实体Embedding等服务支持</li>
<li>在多个下游应用中持续验证效果</li>
</ul></li>
</ul><p> </p>
<p>WeKB构建的技术模块可以用以下矩阵展示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/44659c707ec0ef07705d.png"/></p>
<p>图四：WeKB构建的技术矩阵</p>
<p> </p>
<h2><strong>▌2.2 知识库构建的简单流程</strong></h2>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/c106c333c121d74028d6.png"/></p>
<p>图五：知识库构建的一般流程</p>
<p>我们用一个基本的流程来说明知识库构建的要点，如上图。 </p>
<p>首先我们获取若干个已有的KB （Existing KB_1..n），进行<strong>实体和关系的对齐</strong>（Entity and Relation Alignment），这个对齐可以使用一系列基于模型的匹配方法或一些业务规则。</p>
<p>图中右侧是从文本构建KG的步骤，自底向上：第一步是<strong>实体词和关系的抽取</strong>（Entity and Relation Extraction）。如“苹果CEO库克谈iphone13 pro max功能”，这句无结构文本中，我们可以抽取出“库克”、“苹果”、“iphone 13 pro max” 三个词语片段，作为“实体词”，以及实体词之间的关系，如“owner_of”和 “ has_product”的关系。</p>
<p>第二步是<strong>实体链接</strong>（Entity Linking）。在这一步中，我们把上述抽取的实体词解析为知识库中已有的实体，如 库克指代“Tim_Cook”而不是其他同名实体, “苹果”指代 “Apple_Inc”而不是水果。</p>
<p>第三步是<strong>新实体的发现</strong>（Entity Discovery）：对于未能被链接到已知实体的 “iphone 13 pro max”，通过一系列实体分类、关系抽取、跨文本聚合等模型，我们可以生成一个新的实体，如 iPhone13_Pro_Max, 品牌是苹果，类别是手机，以及描述信息和其他属性若干。 最后，我们用这些抽取出来的新实体、新关系来扩充已知的KB。以上就是知识图谱WeKB构建的一个精简流程。</p>
<p> </p>
<h2><strong>▌</strong>2.3 构建效果——WeKB的现状</h2>
<p><strong>如今的WeKB包括1亿多实体，7亿多关系</strong>，从多语言开放知识图谱Wikidata, Wikipedia等数据源，以及自有文章数据中抽取、融合而成。具体规模在下表中展示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/2686a7d60a70ffd27e37.png"/> </p>
<p>我们还在进一步扩大WeKB的规模，完善技术模块、增加准确率、添加更多数据源、优化实时性，以及探索更多的应用方向。</p>
<p><br/></p>
<p>我们也搭建了WeKB的可视化工具，效果如图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/ee874b1f36b202f70d6f.png"/></p>
<p>图六：WeKB的可视化效果<br/></p>
<p><br/></p>
<p> </p>
<h1><strong>▌三、WeKB的应用概览</strong></h1>
<p>WeKB的构建初见成效后，我们在内部数个业务场景下探索WeKB的应用方法，取得了不错的效果。</p>
<p>主要应用场景包括：</p>
<ul><li>构建MeKB——<strong>个人兴趣图谱</strong></li>
<li>通过实体链接、NER等方法，支持<strong>文章、视频的内容理解</strong></li>
<li>通过实体扩展与联想，支持<strong>视频号红点投放</strong>场景</li>
<li>知识指导的<strong>多模态</strong>表示学习</li>
<li>知识辅助的文本摘要</li>
<li>垂直领域知识图谱的挖掘等</li>
</ul><p>以下是几个应用场景的简单介绍。关于实现细节，敬请期待后续的系列文章。</p>
<p> </p>
<h2><strong>▌</strong>3.1 MeKB个人兴趣图谱的构建 </h2>
<p>MeKB是我们使用知识图谱技术对<strong>用户画像</strong>进行的一次全面升级。 其灵感来源于在2019年提出的一篇proposal： Personal Knowledge Graph （PKG）。 传统的用户画像往往是用户的<strong>独立兴趣标签的集合</strong>，兴趣之间互相割裂，缺乏兴趣点之间的整体关系。我们使用知识图谱技术，对用户不同来源、不同模态的正例内容进行综合的理解，产生实体粒度的兴趣标签，聚合为每个用户的一整张个人兴趣图谱。这是我们已知的PKG的唯一一个大规模业界落地工作。</p>
<p>个人兴趣图谱MeKB有着可扩展、可推理、易用、兴趣点全面等优势，在视频号投放等应用中显著优于baseline的画像方法。MeKB的具体构建和应用细节，可以参考 [内部或本地链接已移除] 及我们后续发布的系列文章。</p>
<p> </p>
<h2><strong>▌</strong>3.2 WeKB辅助内容理解 </h2>
<p>我们通过基于WeKB的实体链接、NER、实体检索等技术，给文章、视频等内容打上不同粒度的内容标签，从而提供内容特征给推荐场景用于内容匹配，以及MeKB的构建等工作。在视频号场景中，比起传统的关键词匹配方法，基于WeKB的方法内容覆盖率达到原始方法的2.7x，且1k个样本上的抽样准确率高于92%。</p>
<p>未来我们也计划逐步发布我们的NER和实体链接等内容理解服务与预训练模型，从而赋能公司内的其他内容理解场景，敬请期待。</p>
<p> </p>
<h2><strong>▌</strong>3.3 通过关键词扩展支持视频号红点投放等业务</h2>
<p>通过WeKB的多模态实体表示学习，我们获取了高质量、强语义性、通用的entity embedding，为实体之间的联想和扩散提供了有效的帮助。我们基于WeKB的关系结构与多模态实体Embedding，提供关键词扩散服务支持视频号红点投放，通过扩展取得了更高的覆盖和更精确的用户兴趣定向效果。在近期的投放项目上，该方法获取了相对于基础画像方法3倍的pctr提升，覆盖3.5x用户数，在活跃用户和新用户上表现均高于baseline。</p>
<p>该关键词扩展方法正在被应用到更多的场景中，关于应用详情也敬请期待未来的系列文章。</p>
<p> </p>
<h1><strong>▌总结</strong></h1>
<p>WeKB是数据中心建设的大规模通用知识图谱。本文作为WeKB系列文章的第一期，总结了知识图谱的概要、知识图谱构建中的一系列基础方法、关键模块，也展示了我们的一些应用效果。在未来的WeKB系列文章中，会与大家分享具体部分的模块设计、研究进展、应用实战等。</p>
<p> </p>
<p> </p>
<h1><strong>▌部分</strong>参考文献 </h1>
<p>[1] <a href="https://krisztianbalog.com/files/ictir2019-pkg.pdf">https://krisztianbalog.com/files/ictir2019-pkg.pdf</a>  Personal Knowledge Graphs: A Research Agenda</p>
<p>[2][内部或本地链接已移除] Feature Engineering for Knowledge Base Construction</p>
<p>[3] <a href="https://arxiv.org/abs/2001.03765">https://arxiv.org/abs/2001.03765</a> Learning Cross-Context Entity Representations from Text</p>
<p>[4] <a href="https://arxiv.org/abs/1906.03158">https://arxiv.org/abs/1906.03158</a> Matching the Blanks: Distributional Similarity for Relation Learning</p>
<p>[5] <a href="https://arxiv.org/abs/1802.01021">https://arxiv.org/abs/1802.01021</a>  DeepType: Multilingual Entity Linking by Neural Type System Evolution</p>
<p>[6] <u><a href="https://arxiv.org/abs/2011.02690">https://arxiv.org/abs/2011.02690</a></u> Entity Linking in 100 Languages</p>
<p>[7] <u><a href="https://arxiv.org/abs/2103.12528">https://arxiv.org/abs/2103.12528</a></u> Multilingual Autoregressive Entity Linking</p> 
{% endraw %}
