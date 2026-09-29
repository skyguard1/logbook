---
title: "MMTL：Multimodal Topic Learning for Video Recommendation--多模态视频主题挖掘技术详解"
date: 2022-04-19 10:17:35
categories:
  - deep-learning
---

{% raw %}

<div>
<p>        随着信息流产品近几年的发展，短视频的消费占比逐年增大。用户对短视频喜好受多种因素影响，其中短视频的内容信息往往决定了用户的消费。因此，对于推荐引擎来说，短视频内容特征就显得尤为重要。</p>
<p>       目前比较常见的短视频内容特征是标签，通过为视频打上多个标签来指代视频的主要内容。标签大体分为两种：实体标签和语义标签，其中语义标签识别的挑战非常大，集中在标签体系制定和模型识别两个方面。在语义标签的体系制定方面，现有的标签识别方案主要依赖人工定义，由于信息流场景下新颖的视频层出不穷，导致语义标签的体系相对滞后；另外，人工定义的语义标签体系不能全面覆盖不同用户对视频内容的语义关注点。在语义标签识别方面，现有的方案依赖大量的人工标注数据集，对模型的更新和优化带来了极大的不便。</p>
<p>       针对上述问题我们开展了视频主题挖掘的相关工作，目标是在不依赖人工定义语义标签体系和不依赖人工标注训练数据的情况下，通过算法模型自动挖掘出视频的语义信息。这里提出了两种方案，分别是“基于视频内容的主题挖掘方法”和“用户行为与视频内容相结合的主题挖掘方法”，均在信息流产品中上线使用，在用户人均主TL视频时长合计提升<strong>4.9%</strong>。</p>
<p>       目前视频主题挖掘能力已经上线集成到「博通」内容理解平台（[内部链接已移除] NLP技术中心打造。</p>
<p>        博通技术系列文章：</p>
<p>【博通技术干货】低俗短文本识别：AI深度理解，禁止超速“开车”</p>
<p>【博通技术干货】图卷积+多模态融合解决不适图片识别难题</p>
<p>【博通技术干货】万字详解：博通低俗图片识别技术演进</p>
<h1>一、基于视频内容的主题挖掘方法</h1>
<ol><li>
<h2>任务背景及分析</h2>
</li>
</ol><p>       以下地震相关的例子（图1-1-1和表1-1-1），用户可能对于视频的兴趣点为自然灾难的科普，所以我们尝试从视频分布上获取视频topic的信息来补全现有tag的不足。因为视频量级较大且视频封面图代表性较强，为了能够较快的迭代模型，在视频模态暂时只使用了视频的封面图。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/da8361af94596b10105f.png"/></p>
<p>图1-1-1 地震科普视频封面图</p>
<p>表1-1-1 地震科普视频分类以及标签</p>
<table><colgroup><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p>体系</p>
</td>
<td colspan="1" rowspan="1">
<p>属性</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>一级分类</p>
</td>
<td colspan="1" rowspan="1">
<p>科学</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>二级分类</p>
</td>
<td colspan="1" rowspan="1">
<p>科普</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>Tag</p>
</td>
<td colspan="1" rowspan="1">
<p>地震、建筑物、趣味科普</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>潜在语义层次</p>
</td>
<td colspan="1" rowspan="1">
<p>自然灾难科普</p>
</td>
</tr></tbody></table><p></p>
<ol><li>
<h2>技术方案及其迭代</h2>
</li>
</ol><h4>2.1 视频内容主题基本框架</h4>
<p>       目前视频的体系有视频一级分类体系、二级分类体系和标签体系，通过已有的标题和封面图构造一个多输入多目标的学习框架，其中在文本侧模型使用了bert，图像侧模型使用了inception-v3，然后将各自提取的特征映射到同一语义空间。将得到的视频封面图和标题融合语义空间通过一个MMoe学习一级分类、二级分类和标签，其中一级分类和二级分类为单标签分类，标签为多标签分类。</p>
<p>       主要框架如图1-2-1主要使用多模态输入映射到同一语义空间进行多任务的方案来获取融合特征，多模态输入能够提升特征表达能力，多任务学习可以尽可能发挥输入特征的能力，当特征能力足够时可以同时学到多个任务，能力欠缺时也能完成一部分的任务。</p>
<p>      在损失收敛后，根据得到的封面图标题特征进行Kmeans聚类，从而得到视频的topic表示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/a45e7abd8aef23d857cd.png"/></p>
<p>图1-2-1 base版本框架</p>
<h4>2.2 添加标签信息</h4>
<p>       在完成了base版本后，通过观察case会发现由于视频的标题过于短小而仅凭封面图又较难准确描述视频语义。如表1-2-1所示，英雄联盟和王者荣耀会因此被划分到同一个topic内部，由此考虑继续加入标签来帮助准确定位视频topic。</p>
<p>表1-2-1 base版本bad case</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/a86bb89b3d388bc97337.png"/></p>
<p><br/>       在之前的框架中加入标签很自然的方式就是增加一路tag的输入如图1-2-2所示就得到了V2版本，当输入模态增加了标签后损失下降十分明显，分析主要原因为标签为三个体系中最细的体系具备轻松推导一级分类和二级分类的能力，但是直接加入标签后由于标签特征太强会让生成的特征忽视掉标题和封面图特征，如表1-2-2所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9dffafb6946e378480eb.png"/></p>
<p>图1-2-2 V2版本框架</p>
<p>表1-2-2 V2版本bad case</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/0cb2643f9ccd6795e9a6.png"/><br/></p>
<p>       由此考虑标签部分只能通过自我表示学习的方式后拼接加入到特征中，主要考虑到了链接预测方案和图表示学习方案，链接预测主要预测不同的两个标签是否在同一个视频中共现过，如果存在共现则为正例，反之为负例。实验发现链接预测存在一个标签别名或者多层次标签不会同时标注的问题（泛化性较差），例如图1-2-3例子中吃播跟韩国吃播有较相近的关系，但是由于标注人员通常只会标注其中一个，所以会导致其中一些较为相近的标签成为负例。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/0371b3b27f45833fad35.png"/></p>
<p>图1-2-3 链接预测问题</p>
<p>       图表示方案将每个标签视为图中的一个结点，然后通过在视频中的共现次数构建边，归一化后就构建了一个无向有权图，使用node2vec的方式在标签上游走得到序列再使用skpi-gram的方式训练标签结点的embedding，表1-2-3为训练的结点检索结果展示。</p>
<p>表1-2-3 标签embedding召回case展示</p>
<table><colgroup><col/><col/><col/><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p></p>
<p>Tag种子</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>top1</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>top2</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>top3</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>top4</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>top5</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>栀子花开</p>
<p></p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>同桌的你</p>
<p></p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p> 匆匆那年</p>
<p></p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>可惜不是你</p>
<p></p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>左耳</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>睡在我上铺的兄弟</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>自杀小队</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>超级英雄电影</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>神奇女侠</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>克里斯蒂安</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>托尼·斯塔克</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>蝙蝠侠：黑暗骑士</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>柴油发动机</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>发动机</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>机械原理</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>机械展示</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>柴油机</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>引擎</p>
</td>
</tr></tbody></table><p></p>
<h4>2.3 特征距离一致化</h4>
<div>
<div>
<p> V2版本concat了训练好的标签embedding后再进行聚类就得到了topic表示。分别用封面图标题特征embedding和标签embedding测试召回case时发现，封面图标题特征embedding更适合于欧式距离，标签embedding更适合于余弦距离，分析主要与各自训练的方式有关。在concat前直接为封面图标题特征embedding做l2-norm会减弱特征能力，参照人脸分类中的cosface的方式直接在feature后面限制单层输入和参数的l2范数为1，因为在训练中就加入了限制所以在concat后方便在同一空间下进行聚类。图1-2-4为线上使用版本，表1-2-5为离线内容topic展示。</p>
</div>
</div>
<p>       由于topic本身是基于正排数据分布生成的，所以随着时间的推移会出现新的topic以及老的topic不再出现。由于topic计算是独立基于簇中心的cos相似度，所以新增和删除并不会干扰到已有的结果，仅需要在字段中增加topic id即可。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/7972fe79b528a11de00b.png"/><br/></p>
<p>图1-2-4 线上版本</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/93b2c15abddb71006b2c.png"/><br/></p>
<p>图1-2-5 内容topic展示</p>
<h2>3. 线上效果</h2>
<p>       分别从内容topic优质占比和线上效果来看视频topic的优势，改进后的版本短视频-6000的优质topic占比提升了18%，小视频-2000提升了21%，如表1-3-1所示。</p>
<p>表1-3-1 优质topic占比对比</p>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p></p>
<p>优质Topic占比</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>短视频-6000</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>小视频-2000</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>优化前</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>57%</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>65%</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p></p>
<p>优化后</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>75%</p>
</td>
<td colspan="1" rowspan="1">
<p></p>
<p>86%</p>
</td>
</tr></tbody></table><p></p>
<p>在快报推荐上实验取得了以下效果</p>
<ol><li>
<p>短视频召回增加一路topic召回后，人均主TL视频时长(秒)0.57%；</p>
</li>
<li>
<p>小视频排序模型加入小视频Topic特征后AUC提升，分拆短小视频推荐模型时直接上线；</p>
</li>
<li>
<p>短视频排序模型加入短视频Topic特征后，人均主TL视频时长(秒) 增长3.01%；</p>
</li>
<li>
<p>短视频NN召回模型优化同时也引入了短视频Topic特征，人均主TL视频时长(秒) 0.93%（老用户），人均主TL视频时长(秒) 2.61%（新用户）。</p>
</li>
</ol><p>完成论文《<a href="https://arxiv.org/abs/2010.13373">Multimodal Topic Learning for Video Recommendation</a>》目前在投中</p>
<p></p>
<p></p>
<p></p>
<h1>二、用户行为与视频内容相结合的主题挖掘方法</h1>
<h2>1. 任务背景及分析</h2>
<p>       在推荐系统通过观察，我们发现仅仅使用内容构建视频的主题还存在一些问题，主要有以下几点：</p>
<ol><li>
<p>在推荐系统的用户表现上，我们发现同属一个内容topic视频有的在内容上表现非常接近，但是在推荐上的表现差异会比较大</p>
</li>
<li>
<p>完全基于内容的主题挖掘会由于体系交叉等问题导致内容主题与用户的兴趣点存在一定差异</p>
</li>
<li>
<p>平铺方案的主题构建topic粒度不可控且多样性不够</p>
</li>
</ol><p>       由此我们实验了多种融合用户行为和内容的主题挖掘方案，分别为风格topic、兴趣topic和层次topic。</p>
<h2>2. 风格topic</h2>
<p>       在推荐系统中，我们观察到存在一些视频即使在标题、封面图、标签这些已有内容特征上极为相近，但是在给同样具有该类兴趣的用户推荐时，在均具有较大曝光的情况下用户的表现依旧存在较大差异（如表2-2-1所示）。</p>
<p>表2-2-1 内容相似推荐差异大case</p>
<table><colgroup><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p>视频标题</p>
</td>
<td colspan="1" rowspan="1">
<p>推荐表现（ctr）</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>没本事又学美国挑事？瑞典将5G排除后，称希望中企加大投资</p>
</td>
<td colspan="1" rowspan="1">
<p>低</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>别以为中国不敢还手！瑞典执意挑事，不料中方已亮出“王牌”</p>
</td>
<td colspan="1" rowspan="1">
<p>高</p>
</td>
</tr></tbody></table><p></p>
<p>       通过对比case发现，视频除了在已有的内容上的特征会影响推荐效果，视频的其他方面比如清晰度，优美度，基调等，在影响用户行为中起着不可忽略的作用，我们称之为视频的风格，于是考虑区别于之前的做法跳出已有的内容特征从风格topic入手完善推荐。</p>
<h3>2.1 视频的两个属性：内容和风格</h3>
<p>       我们把在视频侧影响用户行为的要素粗略的分为内容和风格两个要素（如图2.2.1），内容描述了视频中有什么，风格描述了视频怎么样。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/7e552424b079281c9002.png"/></p>
<p>图2-2-1 视频内容和风格分析</p>
<p>       当一个用户对视频产生一个行为时，我们很难确定这个行为的起因是内容还是风格甚或是兼而有之。因此，引出以下风格topic挖掘的思路，对拿到的用户行为数据，我们尝试剔除内容的原因，只剩下风格原因，然后通过筛选后的数据来训练一个风格topic的model。</p>
<h3>2.2 风格topic挖掘思路</h3>
<p>       根据以上分析，我们通过剔除行为中内容的影响，来筛选出只有风格影响的行为数据。</p>
<p>       具体而言，假设以下场景，当我们同时曝光两个相似的视频（指内容相似，比如相同的电视剧，同一演员，同一类小品等）给用户时，如果点击视频A而不点击视频B的用户远远大于点击视频B而不点击视频A的用户，那我们说着两个视频蕴含着明显的风格差异（由于是相似内容，因此排除内容因素的影响，如图2-2-2所示）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/d515416e06675de7bff5.png"/></p>
<p>图2-2-1 分析用户行为与内容还是风格相关</p>
<p>       那么，如何表征内容相似的视频呢？我们使用视频embedding向量（以标题模态和封面图模态作为encoder的输入，embedding向量使用视频的tag作为监督信号习得）来表征视频，由于监督信号tag多为实体（影视剧名/人名/组织名/），因此可以使用视频embedding来衡量视频之间的内容相似度。把embedding向量聚类后，每个簇可以看做一个内容topic，当两个视频具有相同的内容topic时，视为具有相似内容。</p>
<h3>2.3 风格topic训练语料挖掘方法</h3>
<p>       依赖得到的内容topic，可以挖掘出大量的风格差异性比较明显的视频pair，这些视频pair作为训练风格topic的语料。以下为挖掘风格topic训练语料的步骤。</p>
<ol><li>挖掘具有相同内容topic的视频pair</li>
<li>该pair中的两个视频需共同曝光给用户</li>
<li>有大量的用户选择了其中一个视频，而未选择另外一个视频</li>
<li>其中一个用户群体是另一个用户群体的2倍以上，视为两个视频有显著的风格差异</li>
</ol></div>
<div>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/2bbe6a3c3f1c3cc74dd3.png"/></p>
<p>图2-2-2 挖掘风格topic训练样本</p>
<p>       图2-2-2为挖掘的图示过程。其中，共同曝光排除了推荐理由对A和B的曝光偏好，相似内容排除不同内容对用户行为的影响。熟悉因果推理的同学容易看出，以上两个条件本质是对两个变量做了变量控制。</p>
<p>通过这种方式在140W用户的行为上挖掘了96W个风格差异比较大的视频pair。</p>
<h3>2.4 风格topic学习过程</h3>
<p>       在得到训练语料之后，我们使用这些视频pair学习到每一个视频的风格向量，我们期望这个向量只蕴含了视频的风格特征，而剔除了内容特征。最终，我们会得到一个视频的风格encoder，使用这个encoder，我们能算出每一个视频的风格向量。风格向量的聚类，即是风格topic。</p>
<p>       以下为风格向量的模型架构与风格encoder的结构。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/d0217ffb9fa566e4ea48.png"/></p>
<p>图2-2-3 风格向量模型架构</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/5c2d5aed1d5b92e9cdc7.png"/></p>
<p>图2-2-4 风格向量encoder架构</p>
<p>       使用用户的播放上下文作为anchor，该用户的点击视频作为正例，未点击视频作为负例，通过triplet loss来引导style encoder的学习。这样的方法其实蕴含了一个弱假设，即假设用户的历史播放视频的风格与pair中的点击视频的风格一致，当然这个假设比较粗略，也可以选择其它的学习方法。由于A和B同属于一个内容topic，因此在学习两者差异的过程中，得到的风格向量自动剔除了内容的特征。</p>
<p>       图2-2-5为最终聚类得到的风格topic例子：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/63f83280fd64049d8bb0.png"/></p>
<p>图2-2-5 风格topic展示例子</p>
<h3>2.5 召回策略与线上效果</h3>
<p>       线上使用时，我们拿到用户的最近3天的行为日志，把用户的点击视频映射为它对应的风格topic id，然后统计批次最高的3个风格topic，召回其下面的视频即可。</p>
<p>      在快报推荐上进行ab test实验取得了以下效果：</p>
<p>       在老用户上实验人均主TL视频时长1.44%，人均主TL刷数0.58%，人均App时长0.81%。</p>
<p></p>
<h2>3 兴趣topic</h2>
<p>       为了让挖掘的主题更加符合用户的兴趣点，我们考虑将内容和用户的行为结合，从内容出发，使用用户的行为去指导内容生成符合用户兴趣倾向的topic，我们称之为兴趣topic。</p>
<h3>3.1 视频内容的多模态表征</h3>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/5e6571712bccfe713a26.png"/></p>
<p>图2-3-1 视频内容表征模型</p>
<p>       如图2-3-1所示，对于视频的表征，我们使用了视频的封面图、标题、tag和分类信息。其中，封面图使用BiT提取embedding，标题使用Bert提取embedding，tag使用node2vec的方法获取每个tag的embedding，然后同一个视频下的所有tag对应的embedding进行平均池化得到整个视频的tag embedding。对于上述得到的封面图、标题和tag的embedding，我们又分别接入了多层全连接，从而使每个模态的表征可以根据训练进行调整。由于一二级分类维度较低且相对固定，我们直接使用了embedding层来作为分类的表征。在得到视频各个模态的表征之后，我们通过拼接加全连接将多模态进行融合从而得到视频的整体表征。</p>
<h3>3.2 视频内容和用户行为的结合</h3>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/d1ee6a1da03bf7ce95ce.png"/></p>
<p>图2-3-2 兴趣topic模型结构</p>
<p>       如图2-3-2所示，在得到每个视频的表征之后，我们通过一个用户历史点击视频和候选视频之间的attention网络，将用户的历史行为序列融合成一个向量。其中，历史视频和候选视频的表征模型是共享的，这样也保证了attention网络的有效性。</p>
<p>      最后，整个网络以CTR为目标进行训练。对于训练数据，我们采用了用户近40次点击序列，并且根据用户观看时长进行了过滤，从而去除那些用户误点或标题党等非用户真正感兴趣的视频，提升了训练数据的质量。训练完成之后，我们就可以得到上图右侧这样的一个融合了内容和用户行为的视频embedding模型。通过对该embedding进行聚类，我们就得到了兴趣topic。</p>
<h3>3.3 兴趣topic效果</h3>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/de39eea0d1ef753bd50d.png"/> <img alt="" loading="lazy" src="/logbook/images/deep-learning/c3a37175ff264f894760.png"/></p>
<p>图 2-3-3 兴趣topic展示</p>
<p>       图2-3-3左侧是兴趣topic学习到的夫妻或者一家人一起吃饭的一个topic，这样的topic信息在原来的内容体系中是不存在的。另外，在信息流真实的数据上进行测试，使用兴趣topic模型进行ctr预估得到的AUC指标为0.74，说明兴趣topic模型能够捕获到用户真正的兴趣，生成的topic能够对内容起到较好的补充作用。</p>
<h2>4 层次topic</h2>
<p>       基于内容的Topic存在粒度不可控的问题，因为内容Topic产生自正排的内容分布而不是基于用户的兴趣且较难同时描述出由泛到准的用户兴趣。</p>
<p>       针对普通视频topic的难点问题，我们提出了基于层次结构的用户topic模型。在层次topic中借鉴TDM模型，以树的结构承载层次topic（如图2-4-1所示），树中自顶向下topic粒度由粗到细逐层细化，这样可解决普通topic方法中由于topic数量固定导致的Topic杂糅和分裂，topic粒度控制以及topic之间关联的问题，同时，应用中树的结构还能够提供快速的检索。用户topic模型由两部分组成：用户兴趣模型和层次topic模型，两模块在结构上相互独立，用户兴趣模型中深度网络可任意选择。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1db9e5ce465565f0202e.png"/></p>
<p>图2-4-1 层次topic模型基本框架</p>
<h4>4.1 树的构建与学习</h4>
<p>       我们采用平衡二叉树来建模层次topic，将视频存储在树的叶子结点中，自顶向下对应兴趣的由粗粒度到细粒度的细化过程，树结构如图2-4-2所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/09e4dc673f85fc9627ba.png"/></p>
<p>图2-4-2 层次topic平衡二叉树</p>
<p>       构建了这样一棵树后，如何保证自上而下是兴趣粒度细化的过程呢？要想保证这种性质，需要上下层之间具有兴趣偏序关系，即：用户对节点的兴趣正比于对这个节点子节点兴趣的最大值。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/e9638c24c490b9f17a08.png"/></p>
<p>       在兴趣最大堆树上，只要保证用户对节点的兴趣正比于对这个节点子节点兴趣的最大值。只要满足这一点，则可保证且自上而下的兴趣细化过程，这样的树也是一颗兴趣最大堆树。</p>
<p>      既然要求层次树具有兴趣偏序关系，那么我们如何学习能使层次topic模型学习到这种偏序关系呢？</p>
<p>       在叶子层，可以直接由用户行为学习；而非叶子结点则可以采用其他的方法：比如构建正则化规则的方法，或通过样本牵引模型使树逼近最大堆性质；相对于第二种方法，由于树结构复杂，正则化的方法难以实现，因此我们采用了通过样本牵引层次结构学习的方法。</p>
<p>       样本生成中，叶子层采用用户的隐式反馈行为对节点建模。中间层正样本采用自底向上上溯的方法生成，儿子节点是正例，则父亲也是正例；对于负样本，在每层中，检索top k得到偏序负例样本。</p>
<p>      通过以上学习方法，我们可建立一个具有兴趣最大堆性质的层次topic模型如图2-4-3。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/c1132f76d88c55c71915.png"/></p>
<p>图2-4-3 层次topic正负例选取</p>
<h4>4.2 用户兴趣模型与层次Topic模型联合训练</h4>
<p>       已知用户对兴趣树上部分结点感兴趣，那么我们可以引进深度模型学习用户对树上每层结点的兴趣分布。层次topic模型和用户兴趣模型没有结构上的关联，因此，用户兴趣模型可以灵活选择。目前常用的兴趣建模方法有多种，如DIN，DIEN，BST等，同时也可采用当前流行的序列建模模型，如：BERT，RNN系列，NMT系列。考虑到时效性和模型效果，我们采用了BST模型作为用户兴趣模型的Baseline；BST模型，由一层tansformer组成，模型简单，训练速度快；模型整体架构图2-4-4所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/83eca87eceee5a8e7cf1.png"/></p>
<p>图2-4-4 用户兴趣模型架构图</p>
<p>模型训练基于topic树采用自顶向下的方向逐层训练节点。采用用户点击日志生成训练数据，训练数据生成如下：</p>
<p>设定：</p>
<p>视频集：SET（ITEM1,ITEM2, … ,ITEM8)</p>
<p>用户点击序列: LIST(ITEM5,ITEM7,ITEM8,ITEM6)</p>
<p>样本生成：</p>
<ol><li>
<p>基于用户历史行为，在树上生成正例节点；</p>
</li>
<li>
<p>将点击序列序列节点映射到每层的，生成巡练样本集正例节点；</p>
</li>
<li>
<p>在同一层选取负例节点，可采用随机采样等方法；</p>
</li>
</ol><p>基于生成样本在BST模型中预测正例的点击概率；</p>
<p>当前点击为ITEM6的采样流程和训练流程如图2-4-5所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/459ff760ff2d44513ed3.png"/></p>
<p>图2-4-5 模型联合训练示意图</p>
<h4>4.3 基于样本优化</h4>
<p>       Baseline模型中采用随机采样的方法生成，生成的负例质量较低。模型召回结果中统计发现：目标位置很发散，没有集中在头部位置。</p>
<p>      针对这个数据质量低的问题，我们探索了困难负例样本挖掘方法，提出了一种基于树结构的动态负例样本生成方法：自顶向下训练过程中动态筛选困难负例样本</p>
<ol><li>
<p>初始层全部节点参与训练，正例及头部负例节点的子节点参与下轮训练；</p>
</li>
<li>
<p>预测本层候选的概率，筛选top k，将其孩子节点做下层训练的负样本；</p>
</li>
<li>
<p>重复上部, 直到叶子节点；</p>
</li>
</ol><p>      同时，训练时将batch内本样本的正例作为其他样本负例，通过采用动态样本生成方法，模型的召回提高了9.8%。  </p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/0d724a5d517b4d154d4c.png"/>     </p>
<p>图2-4-6 困难样本挖掘示例</p>
<h4>4.4 基于模型结构优化</h4>
<p>       BST模型仅由单层transformer组成，模型结构较为简单，可以尝试使用更复杂的模型。采用了较为复杂的BERT模型进行训练，对比模型效果并没有提升且令训练速度降低较大。</p>
<p>       训练中仅预测目标样本的点击概率，训练任务较为简单。尝试在训练中添加辅助任务来提升模型的学习能力。我们在模型训练中添加了词向量训练的辅助任务，网络结构如图2-4-7所示。同时辅助任务参考BERT的预训练任务进行了改进，在训练中添加了item的mask。通过添加辅助任务，模型的召回提高了3.3%。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1c9c07d7e8c742aa9ae4.png"/></p>
<p> 图2-4-7 添加辅助任务整体框架图</p>
<h4>4.5 召回策略与线上效果</h4>
<p>基于层次树的Topic召回同样采用自顶向下的方向进行，具体召回方法如下：</p>
<ol><li>选初始层全部节点作为本层召回结果，将其孩子节点作为下层候选；</li>
<li>预测本层候选节点与用户兴趣的相关性，选top K个节点，将其子节点做为下层候选；</li>
<li>自上而下重复步骤2, 直至选出叶子层top K个节点，将其作为召回结果；</li>
</ol></div>
<div>
<p></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/27567d3355e633ff5878.png"/></p>
<p>图2-4-8 模型联合训练示意图</p>
<p>在快报短视频推荐上进行实验，在老用户上人均主TL视频时长+0.56%，主TL-短视频曝光占比+1.32%，人均App时长+0.75%。</p>
<p></p>
<h1>未来展望</h1>
<ol><li>
<h2>基于内容侧</h2>
</li>
</ol><ul><li>
<p>在视频模态引入视频帧，在引入更多的信息的同时保持关注到视频最主体的部分</p>
</li>
<li>
<p>在一个框架中同时引入无监督方案和有监督方案优化特征，有监督方案能够保证我们的主题模型贴近业务，无监督方案能够引入额外的信息</p>
</li>
</ul><ol><li>
<h2>基于结合内容和用户侧</h2>
</li>
</ol><ul><li>
<p>尝试更多的结合内容和用户侧信息的方案</p>
</li>
<li>
<p>探索不同样本采样方案对模型的影响</p>
</li>
</ul><p></p>
<p></p>
<p></p>
<p></p>
</div> 
{% endraw %}
