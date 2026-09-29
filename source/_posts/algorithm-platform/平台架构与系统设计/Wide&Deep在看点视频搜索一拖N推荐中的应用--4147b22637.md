---
title: "Wide&Deep在看点视频搜索一拖N推荐中的应用"
date: 2022-04-06 10:33:45
categories:
  - 算法平台
  - 平台架构与系统设计
---

{% raw %}

<h2><strong>一、前言</strong></h2>
<p>最近两年小视频类APP的流行，使用户的视频消费方式发生了很大的改变。根据我们的统计，在看点搜索里，有80%以上的视频vv是由一拖N贡献的，而有80%以上的用户会观看一拖N视频。看点搜索一拖N的原推荐策略主要基于首点击视频进行相关和热门及个性化的推荐，并没有针对搜索的场景做专门的优化。因此，我们希望通过优化一拖N视频推荐算法来提升搜索视频的总体vv，同时提升用户的连续浏览体验，提升长尾视频的分发效率。</p>
<p> </p>
<h2><strong>二、模型</strong></h2>
<p>在我们的推荐场景中，需要根据用户输入的搜索query及上下文条件，预测用户是否会有效观看一个视频，可以建模为point-wise的ctr预估问题。工业界比较常用的ctr预估模型有LR、FM&amp;FFM、XGBoost等。</p>
<h3><strong>LR</strong></h3>
<p>LR是几年前工业界使用最为广泛的ctr预估模型，可以视作单层的神经网络，是一种wide的结构。LR模型的优点是简单、易理解，但是需要非常庞大的特征工程，要求开发者对业务非常熟悉。</p>
<h3><strong>FM&amp;FFM</strong></h3>
<p>FM可以看做带特征交叉功能的LR，它能够自动做特征交叉，增加了模型的非线性，能够捕捉到更多的数据信息，弥补了LR模型完全依赖人工特征的不足。FFM模型在FM中引入field概念，把n个特征划分到f个field里，模型参数相比FM增加了f倍，模型表达能力比FM模型更强。FM类算法的缺点是模型只能通过内积的方式对特征进行二阶交叉，对于更高阶的特征无法捕捉到。</p>
<h3><strong>XGBoost</strong></h3>
<p>XGBoost是GBDT的一种高效实现，它采用了多线程来加速树的构建，使训练速度显著高于GBDT。XGBoost拥有树类模型的优点，可以自动选择和组合特征，特征工程比较简单。缺点是缺少对大规模离散特征的刻画。</p>
<h3><strong>Wide&amp;Deep</strong></h3>
<p>Wide&amp;Deep模型是提出的一个经典模型，Wide&amp;Deep模型的结构如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/26623cd8391e45f38404.png"/></p>
<p>如图所示，Wide&amp;Deep模型包含Wide和Deep两个部分，它对Wide模型和Deep模型进行联合训练，并将两个模型的结果加权作为最终的预测结果。 之所以Wide&amp;Deep能取得优于Wide-only和Deep-only模型的效果，是因为它结合了Wide-only模型的记忆（Memorization）能力和Deep-only模型的泛化（Generalization）能力。</p>
<ul><li><strong>Memorization</strong></li>
</ul><p>Memorization即模型的记忆能力。Wide部分的线性模型直接学习特征的权重，即对于出现过的特征，模型能记住它们与预测结果之间的相关性。因此Wide部分的模型倾向于推荐之前有过行为的视频。但是线形模型无法对特征进行高阶抽象，因此对于没有出现过的ID类特征，模型学习能力较差。 </p>
<ul><li><strong>Generalization</strong></li>
</ul><p>Generalization即模型的泛化能力。Deep部分通过深层的网络对稀疏特征进行embedding，学习出稀疏特征之间的相关性，从而使模型具备较强的泛化能力。相较于Memorization，Generalization尝试去提高推荐视频的多样性。在我们的线上灰度对比中认证了这一点， Wide&amp;Deep相对于LR模型，视频的覆盖量提升了32%。</p>
<p> </p>
<p>在对比了各个模型在特征工程的效率、特征表达能力以及训练和预测性能，同时参考了业界在CTR预估上的最新实践经验后，我们最终选择了提出的Wide&amp;Deep模型。我们将Wide-only（LR）和Deep-only（DNN）模型与Wide&amp;Deep模型做了对比，验证了Wide&amp;Deep模型的效果要优于LR和DNN。下图是实验对比图，纵轴为AUC，横轴为迭代轮次。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/aa296348b8e7ac5b2b7b.png"/></p>
<p></p>
<h2><strong>三、数据</strong></h2>
<p>原始的上报特征中存在脏数据，将其直接送入模型会导致模型预测精度下降甚至训练出错。因此前期的数据整理是非常重要的。在数据准备中，我们主要做了以下工作：</p>
<ol><li> 根据用户是否完整播放视频构造样本label，完整播放则为正样本，未完整播放则为负样本。</li>
<li> 对各特征进行类型判断与转换，抛弃类型错误的特征。同时，对于明显不在数值范围内的特征或缺失特征用众数代替或直接丢弃。</li>
<li> 去除过短与过长的视频。过短的视频，如低于3s的用户还没来得及看就已经播放完了，会被误认为正样本。过长的视频用户很难全部播放完，并且很有可能是错误的上报值。</li>
<li> 每个用户-视频对，只保留观看时长最长的记录。用户有时候会回头重新看某个看过的视频，这时候曾经被观看过的视频会重复上报一次播放时长特别短的行为，需要去掉这些由于用户重看某个视频而出现的无效播放行为。</li>
<li> 负样本按照一定比率进行下采样。正样本按照播放时长进行采样，较长的视频更容易被采样到，这样是为了减小视频时长对于样本标签的影响，防止模型推荐过多时长较短的视频。</li>
</ol><p> </p>
<h2><strong>四、场景与特征</strong></h2>
<p>到达我们的消费场景，用户需要经过如下步骤：</p>
<ol><li> 在看点搜索内输入query进行搜索</li>
<li> 点击搜索出来的首视频</li>
<li> 向上拖动首视频，消费一拖N视频数据</li>
</ol><p>结合上述过程，我们围绕几个主体抽取了以下四类基础特征：</p>
<ul><li><strong>用户特征</strong></li>
</ul><p>基本属性：用户年龄、性别、所在城市等</p>
<ul><li><strong>视频特征</strong></li>
</ul><p>基本属性：ID、类别、时长、标签、召回来源、视频文档分、视频实效性等</p>
<p>统计属性：播放量、评论数、点赞数、历史有效播放率等</p>
<p>二次特征：vgg网络提取视频封面embedding</p>
<ul><li><strong>上下文特征</strong></li>
</ul><p>query属性：query值、分类、实效性</p>
<p>首视频属性：ID、类型、标签</p>
<p>其他属性：时间、位置</p>
<ul><li><strong>实时特征</strong></li>
</ul><p>为了捕捉用户的实时兴趣，提升用户实时体验，同时使视频推荐更加个性化，我们增加了实时个性化召回模块，可以根据用户最近有效观看的视频召回相关视频和相关标签的视频。在这个过程中，我们对用户兴趣进行累计与衰减，生成用户的实时兴趣画像。</p>
<p>实时属性：用户实时兴趣标签、用户实时兴趣视频ID。</p>
<p></p>
<p>围绕四类基础特征，结合业务场景，我们分别对Wide和Deep部分特征做了进一步处理：</p>
<h3><strong>4.1 Wide部分特征处理</strong></h3>
<p>Wide部分为LR模型，需要对特征进行离散和交叉。对于离散化后的特征根据取值范围，我们再进行multi-hot、one-hot、hash等不同处理。</p>
<ul><li><strong>特征离散</strong></li>
</ul><p>我们根据特征的数据分布对特征进行离散：</p>
<p>年龄：小初高大/青/中/老</p>
<p>时间：高低峰</p>
<p>城市：省/片区</p>
<p>播放量、点赞数、评论数：log平滑后取整</p>
<p>其余不存在明显分布的连续特征进行等频离散。对于离散后的特征，如果取值个数不多，我们直接用one-hot/multi-hot处理，对于取值个数过多的特征，为了加快训练速度及防止过拟合，我们选取特征中的高频部分做one-hot，长尾部分做hash。</p>
<ul><li><strong>特征交叉</strong></li>
</ul><p><strong>基础交叉</strong>：用户（年龄/性别）x视频（标签/召回源/类别）、上下文（query/位置）x视频（标签/召回源/类别）、实时特征（兴趣标签/兴趣ID）x视频（标签/召回源/类别）</p>
<p><strong>统计交叉</strong>：一定时间段（七天/一天）内query x ID 的播放数/有效播放数/播放率、一定时间段（七天/一天）内query x 召回源的播放数/有效播放数/播放率</p>
<p>Wide部分结构如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b698730328dff8a95742.png"/></p>
<p></p>
<h3><strong>4.2 Deep部分特征处理</strong></h3>
<p>Deep部分具有抽象与交叉特征的能力，不需要太多的特征工程，但仍需要对部分特征进行离散和归一化，来减少数据噪声。同时，我们在某些特征后面添加embedding层，使模型能够抽象出更合理的高级语义，再通过神经网络进行信息融合和表达。</p>
<p><strong>离散化</strong>：历史有效播放率、query实效性、视频文档分、视频时长、视频实效性</p>
<p><strong>归一化</strong>：评论数、点赞数、播放数</p>
<p><strong>embedding</strong>：query、视频ID、首视频ID、视频标签、首视频ID</p>
<p>Deep部分的结构如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/95ac38a5d1667fdb1876.png"/></p>
<p></p>
<h2><strong>五、优化</strong></h2>
<h3><strong>5.1超参数调优</strong></h3>
<p>在实际的调参过程中，我们使用控制变量法对单个超参进行调优，即固定住其他超参数，对需要调整的参数进行调优实验，逐次迭代直至完成所有超参数的选择。不同超参的实验结果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9b2642867d34a4cc61fc.png"/></p>
<p></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/69de1fdbd892cb0e7388.png"/></p>
<p></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/bef9f3f41a986eb5747e.png"/></p>
<p></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e433f9e6f8df7ca047ac.png"/></p>
<p></p>
<h3><strong>5.2其他优化</strong></h3>
<p>随着数据量的增大，加快训练速度变得尤为重要，为此我们做了如下的优化：</p>
<p> <strong>剥离预处理流程</strong></p>
<p>前期为了快速迭代，我们直接将原始数据下载到本地进行预处理。后期随着数据量增大，单机处理的速度有限，并且原始未处理过的数据体量庞大，占用大量磁盘空间。因此，我们将预处理流程与训练代码分离开，在tesla上利用集群进行快速处理，将结果保存到HDFS上，本地直接从HDFS上拉取预处理后的数据。</p>
<p><strong>最大化GPU效率</strong></p>
<p>一开始我们的GPU利用率只有3%～4%，经过排查，发现GPU大部分时间在等待IO操作，从而使GPU没有得到充分利用。因此我们修改了数据读取的方式，对数据进行预读取，增加 CPU和GPU的利用率，减少GPU的等待时间。此外，在IO操作上我们使用多线程，通过增加IO操作的并行度来加快数据读取速度。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/072c101230a8e2def4f9.png"/></p>
<p></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/14bd9a126e5f3280b328.png"/></p>
<p></p>
<p>通过增加数据预读取策略，以及设置多线程IO，最终的GPU利用率从3%提高到了20%，训练速度从6000条/秒提升到了15000条/秒。</p>
<p></p>
<h2><strong>六、结语</strong></h2>
<p>我们使用tensorflow serving搭建了线上预测服务，并挑选了部分流量与原策略进行对比，各线上指标对比结果显示，基于Wide&amp;Deep框架的优化方案能够有效提升用户的视频消费体验。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/986ae2a973d5cbcf7786.png"/></p>
<p>总的来说，Wide&amp;Deep模型在视频推荐任务上具有一定的优势，模型本身的结构兼顾了记忆与泛化能力，预测性能较好，其中Deep部分可以抽象高阶关系，弥补了Wide部分人工特征的不足。但是Wide&amp;Deep的Wide部分依赖人工设计交叉特征，处理的不好的话会影响整体模型的效果。因此，我们还尝试了具有自动交叉特征能力的DCN模型和DeepFM模型。这两个模型本质上都是借鉴了Wide&amp;Deep的框架，将模型分为两个部分，Deep部分进行特征泛化，另一部分负责交叉特征。</p>
<h3><strong>DCN</strong><strong>模型</strong></h3>
<p>DCN模型全称Deep&amp;Cross Network，它的网络由Cross network和Deep Network组成，其中Cross Network负责进行特征交叉，Cross Network的层数越多，可以生成的交叉特征阶数也越高。它的结构如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/90589926760fc7175504.png"/></p>
<h3><strong>DeepFM</strong></h3>
<p>DeepFM将Wide&amp;Deep模型的Wide部分用FM代替，从而避免了人工的特征交叉。和DCN的Cross Network部分相比，DeepFM的FM部分只能进行二阶的特征交叉。DeepFM的结构如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7023d553d228e835c3e9.png"/></p>
<h3><strong>模型效果</strong></h3>
<p>我们在线下对Wide&amp;Deep、DCN和DeepFM三个模型进行了对比，并且上线了Wide&amp;Deep和DCN模型，以下是各模型在线上线下具体的效果对比：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/686e3f32775d7f2fc8b3.png"/></p>
<h3><strong>后续工作</strong></h3>
<p>在后面的工作中，我们将继续尝试其他优化的方式。</p>
<ul><li><strong>模型方面</strong></li>
</ul><p>    ৹尝试更多前沿的模型和方法。</p>
<p>    ৹尝试其他建模方式，综合考虑视频播放率、视频观看时长和视频时长。</p>
<ul><li><strong>特征方面</strong></li>
</ul><p>    ৹丰富特征：利用外部模型对特征主体进行抽象，得到特征主体到embedding的表示。</p>
<p>    ৹细化特征：对特征进行更细致的分析，有针对性地对不同的特征采取不同处理方式。</p>
<p><strong> </strong></p> 
{% endraw %}
