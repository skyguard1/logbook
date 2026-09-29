---
title: "KBQA_ 知识图谱助力问答系统升级"
date: 2022-04-17 10:47:50
categories:
  - 算法平台
  - 多模态与内容理解
---

{% raw %}

<p>写在前面：文章初衷是帮助问答初学者们快速系统地了解KBQA并共同探讨KBQA技术进展。第一部分构建问答系统和知识图谱的概念认知，第二部分简单梳理KBQA技术体系和应用挑战，第三部分探讨前沿技术。不足之处，欢迎大家交流指正。</p>
<h2>一、知识背景</h2>
<h3>1.1  问答系统</h3>
<p><strong><b>    问答系统(</b></strong><strong><b>QA</b></strong><strong><b>)</b></strong>是对人类提出的自然语言问题进行回答的系统。我们首先来了解其相关变迁历史，早在1950年，《计算机器与智能》一文中提出的“图灵测试”就是通过问答方式检验机器智能。1960年起陆续出现一系列限定领域的问答系统，比如BASEBALL和LUNAR，它们大多基于专家领域知识构建专家系统，但由于知识获取的困难并未得到广泛使用。九十年代后检索技术(Information Retrieval，IR)的蓬勃发展，为问答系统的研究带来了突破，显露了问答系统在商业领域的应用价值。自2011年计算机Watson挑战Jeopardy竞赛史上胜率最高的两位人类选手获胜，到苹果Siri诞生，再到2014年Cortana和Alexa，问答系统飞速发展并愈加贴近人们的生活，成为人工智能时代的研究热点。现如今，不同领域场景下问答系统会以不同的产品形态与用户见面，其亮点在于将硬件设备与智能交互系统融合，赋予设备“感官”与“智慧”，比如：智能音箱、智能车载、智能家居、穿戴设备、手机、机器人等。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/832e1b953cd535c18d6d.png"/></p>
<p>                            图1. AI问答的变迁史 [图片来自亚研院Nan Duan]</p>
<p>    特别引人关注的是，2018年5月，Alphabet董事长John Hennessy表示： Duplex（全双工）技术在预约领域已经通过图灵测试，这是否代表机器已经拥有了人类智慧？事实并非如此。骗过人类和像人一样思考，前者难度远远小于后者， Duplex的演示过程或许混淆了接线员的判断，但语音干扰、领域限制、提问方角色设定等trick降低了测试的难度。图灵测试以机器骗过人类为标准判断机器的智能，但无法判别机器能否像人一样思考，这就催生了维诺格拉德测试。</p>
<p>    例：市政府拒绝给示威者提交游行许可证，因为他们[担心/鼓吹]暴力事件。</p>
<p>    问题：谁[担心/鼓吹]暴力事件？</p>
<p>    答案：市政府/示威者</p>
<p>上述例子涉及的模糊指代单纯靠语法知识是不能解决的，还需要大量的生活常识作为补充，才能理解这句话的意思是：市政府会担心，示威者会鼓吹。关于维诺格拉德测试的2019年上半年，OpenAI发布了《Language Models are Unsupervised Multitask Learners》，Alec Radford等人公布GPT-2模型赶超BERT模型在维诺格拉德模式挑战获得了70.7%的准确率（2016年只有58%），下半年这一指标又被Bert超过了，ACL2019发表《A Surprisingly Robust Trick for the Winograd Schema Challenge》达到72.5%（参见3.3节），但仍未达到人类水平，想要超过大赛设定的人类标准90%还存在不少困难。联想《武林外传》里吕秀才和姬无命的一段经典台词：</p>
<p>    吕秀才：是谁杀了我，而我又杀了谁？</p>
<p>    姬无命：是我杀了我。</p>
<p>戏剧化的演绎表象下，令人不禁反思其背后隐藏的危机。维诺格拉德测试检验着机器的<strong><b>常识推理</b></strong>能力，其发展或许会在一定程度上避免人工智能像姬无命一样出现 “自己杀了自己”的情况。</p>
<p>    目前，业界主要关注三类问答系统应用情景：（1）闲聊型对话 （2）任务型对话 （3）知识问答。图2-1展示了<strong><b></b></strong><strong><b>叮当</b></strong>在三种应用情景下的典型实例。本篇关注的知识问答通常为三类：KBQA(基于知识图谱的问答)、IRQA(基于问答对检索的问答，包含FAQ)、DocQA(基于文档阅读理解的问答)。KBQA将文本表示成结构化的语义表示，并且将该问题的语义表示转化成SPARQL或者SQL等结构化查询语言，该方法具有语义推理的能力，但是对语义解析工具的性能要求较高。IRQA通过问答对的形式存储知识，检索与当前输入语句最相近的问答对，将问答对答案作为系统答案自动生成问题的回复。DocQA针对问题从文章中寻找一段文字作为答案，对于线上未回答问题能够及时进行答案抽取，生成高质量问答对。三项技术置信排序KBQA&gt;IRQA&gt;DocQA，覆盖能力排序与之相反。总体地，任何一项技术都有其天花板和适用范围，优秀的问答系统需要多引擎的协同作战。(参见图2-2智能机器人问答系统框架)</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8d6ded6dd3393d8ebdc3.png"/></p>
<p>                  图2-1.常见问答与对话类型【图片来自@曹云波】</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/3bc895d55501b6333c49.png"/></p>
<p>                                               图2-2.智能机器人问答系统框架</p>
<h3>1.2  知识图谱</h3>
<p>    知识图谱(Knowledge Graph)，又称知识库，它以结构化的形式描述客观世界的概念、实体及其之间的关系，将互联信息表达成更接近人类认知世界的形式，以便更好地组织、管理互联网的海量信息，方便计算机理解和计算语义信息。2012年提出知识图谱概念的初衷是提高搜索引擎的能力，改善用户的搜索质量以及搜索体验。图3展示使用搜索“中国人民大会堂”，搜索结果被分为左右两部分，左侧是传统的搜索结果，而右侧则是知识图谱提供的相关信息。知识图谱自提出来一直受到工业届和学术界的追捧，各大互联网公司纷纷布局自建知识图谱，比如Probase、TopBase、知立方、知心、大脑等。与此同时，金融、医疗、教育、司法等领域都在探索建立垂直领域知识图谱以助力行业智慧能力升级。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4df022b64aaacdda1117.png"/></p>
<p>                               图3.搜索人民大会堂，右侧会出现其相关信息</p>
<p>    从组织形式上看，知识图谱是用图数据结构表示的知识载体，描述着客观世界的事物及其互相关系，节点代表客观世界的事物，边代表事物间的关系；在具体实现时，知识图谱用语义网(Semantic Web)中的资源描述框架(RDF)对知识体系和实例数据两个层面的内容进行统一表示，共同构建一个完整的知识系统。在语义网络中的<strong><b>一条知识通过一个三元组SPO表示</b></strong>&lt;Subject，Predicate，Object&gt;，无数个三元组联结形成大规模知识图谱。大数据时代知识图谱的优势可以总结为三点：<strong><b>大体量、高质量、知识结构化</b></strong>，现已被广泛应用于智能搜索、智能问答、个性化推荐、内容分发等领域。</p>
<p>    图谱中的每一个<strong><b>三元组</b></strong>代表一个事实，图4给出了一个知识图谱的示例，SPO =&lt;张艺兴，出生地，湖南省长沙市&gt;表示事实“张艺兴的出生地是湖南省长沙市”。知识搜索引擎会将关键词“张艺兴”理解为一个实体，基于图知识结构展示中文名、身高、血型等基本信息，关联“功夫瑜伽”、“好先生”等相关实体，从而让用户更便捷的获取新知识。图5查询知识图谱发现存在多个“张艺兴”，EID=407507291只指代明星“张艺兴”。这里说明<strong><b>实体名称</b></strong>在图谱中有多样性，但<strong><b>实体ID</b></strong>(EID)是唯一的。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a119da7566d78496d34d.png"/></p>
<p>                            图4.实体关系图谱查询示例【来自AILAB知识图谱】</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d3a83a261a83d310eeca.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/923f42a6942162368df7.png"/></p>
<p>              图5.实体名称的多样性和实体ID的唯一性【来自QQ浏览器知识图谱】</p>
<p>    整个知识图谱的生命周期涉及<strong><b>知识建模、知识构建、知识融合、存储、检索、知识推理以及知识服务</b></strong>等环节，基于知识图谱的问答把研究重点聚焦于流程的后半段，紧密联系自然语言处理、知识工程、语义网、机器学习等多个研究方向，为智能问答系统建设提供精准有力的知识支持。目前，得益于知识图谱以实体为核心的结构化保存方式，其<strong><b>数据更新敏捷、方便</b></strong>，因此基于知识图谱的问答能很好的解决<strong><b>事实性问题</b></strong>，但知识还有其他形态，如常识知识、场景知识、情感知识等，这些知识的表示、构建和应用需要研究者们的不断探索。</p>
<h2>二、 KBQA初探</h2>
<p>    KBQA是问答系统中把知识图谱作为答案来源的技术方法，问答系统对用户使用自然语言提出的问题进行分析，与知识图谱进行交互检索相关知识点，通过知识推理得出准确答案，并完成回复语的配置。知识图谱为问答系统提供了结构化、关联化、高质量的知识来源，也为高效地问题回答提供了知识基础。</p>
<p>    我们将线上问题依据其复杂程度划分为<strong><b>简单问题</b></strong>和<strong><b>复杂问题</b></strong>。简单问题属于单属性问题，通过一个三元组即可实现答案的查询，而复杂问题涉及单个或多个属性，需要处理判断、递归、计算推理等特殊情况，是研究中的难点。据统计，<strong><b>线上数据问答</b></strong><strong><b>query中87%为简单问题</b></strong>，可见简单问题的支持能够快速满足用户的基本需求，复杂问题的延展则能帮助系统更加智能。线上的KBQA有<strong><b>垂直领域KBQA</b></strong>和<strong><b>通用KBQA</b></strong>之分，前者保障专项领域或行业的高准确率，后者提高用户问题的召回率。</p>
<ul><li>单属性简单问题
<ul><li>鹿晗的生日              人物领域</li>
<li>中国有多少人口       地理领域</li>
</ul></li>
<li>单属性复杂问题
<ul><li>土豆是马铃薯的别名吗                  植物领域，判断</li>
<li>赵丽颖结婚了吗                             人物领域，推理</li>
<li>谁和杨幂同一个星座                      共性</li>
<li>张学友和周杰伦谁的年龄大           比较</li>
</ul></li>
<li>多属性复杂问题
<ul><li>孙俪老公的前女友叫什么               人物领域，递归</li>
<li>四川省会的面积多大                      地理领域，递归</li>
<li>孙俪和邓超是什么关系                   关系       </li>
</ul></li>
<li>......</li>
</ul><h3>主要问题与挑战</h3>
<p>当前KBQA技术进行语义理解时，围绕<strong><b>数据</b></strong>和<strong><b>语义</b></strong>两个核心。</p>
<ul><li>数据层面：问题表示是语义理解的基石，图谱中存在大量谓词(Predicate)关系，我们需要收集具有代表性的问法来帮助识别相同谓词指向的问题，同时也要尽可能地提供丰富的问法。例，谓词=丈夫，问法有“赵丽颖的丈夫是谁”、“赵丽颖嫁给了谁”、“谁的老婆是赵丽颖”等。此外，知识图谱虽然体量很大，仍然不可能覆盖所有的知识，KBQA仍然会面临回答低频问题时部分或者全部知识缺失的问题。例，“陕南有什么好玩的地方”、“某罕见病的治疗方法”，因为知识图谱没有相关知识，所以不能回答。</li>
<li>语义层面：语义解析的关键是对谓词的识别，需要完成问题表示向结构化查询的转化。做好问题表示能削弱谓词隐性表达带来的问题，而谓词识别的效果则直接影响着问答系统性能的优劣。</li>
</ul><p>    工业界项目冷启动阶段，数据的缺失对构建<strong><b>语义模型</b></strong>是一个极大的挑战，所谓巧妇难为无米之炊。前期挖掘头部query优先通过<strong><b>规则模板</b></strong>和<strong><b>语料匹配</b></strong>两种方法实现语义理解。规则模板的准确率高、用户可控且操作性强，语料匹配能对高频问题快速反应，这两种方法学习使用门槛相对较低，标注人员能快速上手，但缺点也很明显：a.昂贵的人工标注成本 b.穷举式的数据扩充，有限的泛化能力。为了弥补了规则模板和语料匹配的不足，进一步提高问答系统的泛化能力和召回率，语义模型的引入必不可少。</p>
<h2>三、主流技术方案</h2>
<p>    KBQA主流技术方案有两种：<strong><b>基于语义解析(</b></strong><strong><b>Semantic Parsing</b></strong><strong><b>)的知识图谱问答</b></strong>将自然语言问题转化为计算机能理解的逻辑表达，再进行知识图谱的结构化查询，其核心模块就是两部分：语义理解、知识推理及查询。<strong><b>基于答案检索(</b></strong><strong><b>Answering Ranking</b></strong><strong><b>)的知识图谱问答</b></strong>访问知识图谱获取问题相关子图作为候选集，通过构建特征或分布式表示的方式计算候选集与问题之间的匹配得分，从而得出最终答案。该类方法我们可以定义为排序或分类问题，即对所有候选答案的排序问题，或这对单个候选答案的二分类问题。考虑到知识图谱建设初期数据完备性不高，工业界大多选择前种技术方案。</p>
<h3>3.1《KBQA: Learning Question Answering over QA Corpora and Knowledge Bases》</h3>
<p>本篇论文主要面向<strong><b>简单问题</b></strong>，采用<strong><b>基于语义解析的知识图谱问答</b></strong>的技术方案。（2017年）</p>
<ul><li>算法概述</li>
</ul><p>    本文给出了KBQA系统的体系结构，主要包括两个过程：离线预处理部分和在线QA部分。离线过程学习templates到属性的映射。在线部分，系统将问题解析和分解为一组二元事实型问题，使用概率推断来寻找它的值。这个推断是基于给定模板的属性分布来得到的。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/70d68ebf0fe951c6cc70.png"/></p>
<ul><li>算法模型</li>
</ul><p>    论文基于亿级知识库和百万级QA语料设计了新颖的问句表示方法：templates（句子级模板）。举例：针对城市人口的问题，可以学到类似What’s the population of $city?、 How many people are there in $city?的templates。论文中为2,782个意图学到了2,700万个模板，大量的数据保证基于templates的KBQA问答系统可以理解各式各样的问题。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ac9fbaa08f1993ea6150.png"/></p>
<p>    论文利用概率图模型进行问题求解，将问句表示为q，其相关实体表示为e，定义e对q的概率分布为P(e|q)。利用q和e可以生成t(即templates)，概率分布表示为P(t|q,e)。属性p仅仅依赖于t，可以表示为P(p,t)。最终可以根据给的的属性p和实体e生成答案概率P(v|e,p)。这种方法完成了从一个自然语言问题到生成答案的整个过程。基于这个生成模型，可以得到一个联合概率分布，进而用来解决给定其他变量求最大v的条件概率问题。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/aeb9995b29194609b839.png"/></p>
<ul><li>实验结果</li>
</ul><p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2b10036f0722f2c096ee.png"/></p>
<p>    图表展示了算法在QALD-5上的结果表现，KBQA方法表现最高准确度。由于该论文提出的KBQA方法针对二元事实型问题，因此算法召回率相对较低。若只考虑二元事实型问答，召回率能上升到0.67。论文中也提到面对复杂问题时，可以采用分治算法，将问题分解为一系列的二元事实型问题，然后依次回答，通过动态规划算法找到最优分解。</p>
<p>原文：<a href="http://gdm.fudan.edu.cn/GDMWiki/attach/By%20Year/KBQA.pdf?skin=raw"><u>http://gdm.fudan.edu.cn/GDMWiki/attach/By%20Year/KBQA.pdf?skin=raw</u></a></p>
<ul><li>技术分解与实践</li>
</ul><p>基于语义解析的知识图谱问答的技术要点可以做如下分解(图6)：</p>
<p>    (1)分词、词性标注(POS)、命名实体识别(NER)       (2)实体链接</p>
<p>    (3)关系提取    (4)关系校验    (5)语义解析    (6)图谱查询    (7)回复生成</p>
<p>    提高问答系统识别实体和属性的能力可以启用等价实体/属性库，例如，刘德华的等价别名包括华仔、刘福荣，别名扩展机制使得问答系统更具兼容性。提高问答系统的相关度可以建立领域意图库，例如，省长属性可以划分到地理领域-人物关系查询意图下，属性细化到具体的领域意图使得知识问答的query更加精准。</p>
<p>    我们用一个实例回顾下基于语义解析的知识图谱问答技术的工作流程：（1）用户向问答系统提问“华仔的老婆是谁？”，系统接收Query；（2）NLU对Query进行分析-分词、POS、NER；（3）实体链接技术将含义模糊的实体映射到知识图谱对应准确实体位置，S:华仔-刘德华-EID；（4）关系提取和关系校验，P:老婆；（5）语义解析组合，识别主语“刘德华”和属性“配偶”&lt;S:刘德华，P:配偶，O:？&gt;；（6）图谱查询答案O:朱丽倩；（7）生成回复语：“刘德华的老婆是朱丽倩。”，返回给用户。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/24fec5394918c61679f0.png"/></p>
<p>                                                图6 KBQA技术实践</p>
<h3>3.2《Question Answering over Freebase via Attentive RNN with Similarity Matrix based CNN》</h3>
<p>本篇论文面向<strong><b>简单问题</b></strong>，采用<strong><b>基于答案检索的知识图谱问答</b></strong>的技术方案。（2018年）</p>
<ul><li>算法概述</li>
</ul><p>    算法将KBAQ拆解成两个模块：Entity detection 和 Relation detection（Relation等同上文Predicate），首先提取<strong><b>主题词</b></strong>形成候选实体集(Entity candidates)，然后通过知识图谱查询得到候选实体集的所有候选关系(Relation candidates)，建立模型对Relation candidates和Question pattern评分，从而获得最终答案。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/94a7b1370dbe4e33327f.png"/></p>
<ul><li>AR-SMCNN模型</li>
</ul><p>    Entity detection模块中主题词的提取涉及NER模型，这里不做过多论述，我们主要关注下Relation detection模块的设计。该模块衡量候选关系集中每一个关系与Question pattern之间的匹配得分得到最匹配关系。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/025785c0bee125510db5.png"/></p>
<p>    论文首次提出的Attentive RNN with Similarity Matrix based CNN（AR-SMCNN）模型:</p>
<p>    (1)RNN(attentive BiGRU)获取<strong><b>semantic-level</b></strong>的语义相关性，这里关系被分割成两个部分分别进行向量表示，Question pattern则被送入双向GRU网络输出表示向量，通过问题和关系间相似度计算获得semantic-level的最终特征；</p>
<p>    (2)基于相似矩阵的CNN实现<strong><b>literal-level</b></strong>字词匹配。在实现传统<strong><b>en</b></strong><strong><b>coder-compare</b></strong>框架的基础上，CNN更多地记录了原始问题词序、表达方式等信息，我们构造相似性矩阵(如图7灰度越深两个词之间的相似度越高)，利用卷积层进行特征提取，通过双向最大池化层保留最大匹配特征，经由全连接层获得literal-level的最终特征；</p>
<p>    (3)组合两种方法的结果，通过线性层得到最后的score。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/0178e928923f98313e0b.png"/></p>
<p>                                                     图7.相似矩阵示例</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6b49f766ac96082246bc.png"/></p>
<ul><li>实验结果</li>
</ul><p>论文基于SimpleQuestion数据集与近些年六个优秀算法工作进行了对比，最终AR-SMCNN模型在FB2M 和 FB5M两个数据集上分别获得77.9%和76.8%的优异表现。算法有较好的效率表现，训练过程中AR-SMCNN在GTX1080上完成20次epoch只耗费1小时。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/860826dbcb5bf384d257.png"/></p>
<p>原文: <a href="https://arxiv.org/vc/arxiv/papers/1804/1804.03317v1.pdf"><u>https://arxiv.org/vc/arxiv/papers/1804/1804.03317v1.pdf</u></a></p>
<p>源码：<a href="https://github.com/quyingqi/kbqa-ar-smcnn"><u>https://github.com/quyingqi/kbqa-ar-smcnn</u></a></p>
<ul><li>技术分解与实践</li>
</ul><p>将图4作为基于答案检索的知识图谱问答技术的参考实例图，回顾下该方法的工作流程（1）用户向问答系统提问“张艺兴在哪出生的？”，系统接收Query；（2）NLU对Query进行分析-分词、POS、NER，找到主题词“张艺兴”；（3）链接到知识图谱相关实体上，并将该主题实体在知识图谱中通过关系或者路径链接的实体提出来作为候选答案；（4）构建特征分布式表示，训练模型进行排序分类，获得属性“出生地”以及答案“湖南省长沙市”；（5）生成回复语：“张艺兴的出生地是湖南省长沙市。”，返回给用户。</p>
<h3>3.3  Winograd Schema Challenge</h3>
<p>《A Surprisingly Robust Trick for the Winograd Schema Challenge》--ACL2019新突破</p>
<p>    在本篇文章的工作中，作者首先证明对WSCR上现有的LMs（language model）进行调参有助于提供LM处理WSC273和WNLI的能力（WSC273包含pronoun disambiguation problem的273个instances，WNLI和WSC273相似，但加了限定）。其次，作者介绍了一种大规模生成类WSC样本的方法，并利用英文wikipedia构建了2.4M的数据集。该数据集和WSCR被一起用来做<strong><b>Bert LM</b></strong>的预训练调参。</p>
<p>原文：<a href="https://arxiv.org/abs/1905.06290"><u>https://arxiv.org/abs/1905.06290</u></a></p>
<p>代码：<a href="https://github.com/vid-koci/bert-commonsense"><u>https://github.com/vid-koci/bert-commonsense</u></a></p>
<p>数据：<a href="https://ora.ox.ac.uk/objects/uuid:9b34602b-c982-4b49-b4f4-6555b5a82c3d"><u>https://ora.ox.ac.uk/objects/uuid:9b34602b-c982-4b49-b4f4-6555b5a82c3d</u></a></p>
<p>    本篇文章在WSC273和WNLI分别获得了72.5%和74.7%的准确率。</p>
<h2>四、结束语</h2>
<p>    回顾两类KBQA的技术方案，基于语义解析的方法核心思想是“先解析后查询”，基于答案检索的方法核心思想是“先编码后比较”。结合近年研究热点和toB转型的趋势，KBQA应用正在<strong><b>从大规模简单应用场景向小规模复杂应用场景转变</b></strong>，除此外重要关注点还有：</p>
<p>    (1)深度的知识应用、密集的专家知识，复杂问题、推理问题等亟待突破；</p>
<p>    (2)利用互联网数据动态更新和补全知识图谱，发展低成本知识获取方法；</p>
<p>    (3)利用知识图谱完成回复语生成，更灵活的进行知识互动；</p>
<p>    (4)随着BERT、ELMo、GPT-2等方法的工程应用SOTA将会进一步提升。</p>
<p>    问答系统作为人类感知人工智能发展进度的窗口，其最先发挥作用的必然是在特定领域或垂直行业的应用。硬件设备与智能交互系统的融合，问答系统将化身万物为人类提供更加智能地服务。</p>
<p> </p>
<p>参考文献及KM传送门：</p>
<p>[1] <a href="http://ws.nju.edu.cn/conf/keqa2018/resources/%E5%9F%BA%E4%BA%8E%E7%9F%A5%E8%AF%86%E5%9B%BE%E8%B0%B1%E7%9A%84%E9%97%AE%E7%AD%94%E7%B3%BB%E7%BB%9F%E5%85%B3%E9%94%AE%E6%8A%80%E6%9C%AF.pdf">肖仰华：基于知识图谱的问答系统</a></p>
<p>[2] <a href="https://mp.weixin.qq.com/s/xAvRl6FK9ZJjpuU_odBEPw">肖仰华：知识图谱下半场-机遇与挑战</a></p>
<p>[3] <a href="https://blog.csdn.net/gjmvvv/article/details/100767856/">王昊奋：基于KG的认知智能中台思考及产业化实践</a></p>
<p>[4] 王昊奋 / 漆桂林 / 陈华钧：《知识图谱：方法、实践与应用》</p>
<p>[5] 手机QQ浏览器知识图谱系列(一) — 简介</p>
<p>[6] 手机QQ浏览器知识图谱系列(三) — KBQA，通往知识图谱的桥梁</p>
<p>[7]浅谈知识图谱型问答系统</p>
<p>[8]我们需要怎样的问答系统</p>
<p>[9] <a href="https://cs.nyu.edu/faculty/davise/papers/WinogradSchemas/WS.html">维诺格拉德模式挑战赛</a></p>
<p>[10] Berant, Jonathan, et al. "Semantic parsing on freebase from question-answer pairs." Proceedings of the 2013 Conference on Empirical Methods in Natural Language Processing. 2013.</p>
<p>[11] Yao, Xuchen, and Benjamin Van Durme. "Information extraction over structured data: Question answering with freebase." Proceedings of the 52nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). Vol. 1. 2014.</p>
<p>[12] Bordes, Antoine, Sumit Chopra, and Jason Weston. "Question answering with subgraph embeddings." arXiv preprint arXiv:1406.3676 (2014).</p>
<p>[13]Xiong, Wayne, et al. "The  2017 conversational speech recognition system." 2018 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP). IEEE, 2018.</p>
<p>[14]Qu, Yingqi, et al. "Question answering over freebase via attentive RNN with similarity matrix based CNN." arXiv preprint arXiv:1804.03317 (2018).</p>
<p>[15]Cui, Wanyun, et al. "KBQA: learning question answering over QA corpora and knowledge bases." Proceedings of the VLDB Endowment 10.5 (2017): 565-576.</p>
<p><a href="https://cs.nyu.edu/faculty/davise/papers/WinogradSchemas/WS.html"></a></p> 
{% endraw %}
