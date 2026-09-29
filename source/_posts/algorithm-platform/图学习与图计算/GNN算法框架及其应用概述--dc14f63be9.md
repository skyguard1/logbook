---
title: "GNN算法框架及其应用概述"
date: 2022-04-16 10:37:57
categories:
  - 算法平台
  - 图学习与图计算
---

{% raw %}

<p>        图神经网络（Graph Neural Networks，GNN）是应用于图数据上的深度神经网络模型，是一种可以自动学习图特征的学习机制。目前GNN算法应用到了很多领域，包括推荐系统、计算机视觉、自然语言处理等。从应用目标对象来说，图算法的应用可以分为三大类：一是预测节点的标签，比如节点的分类任务等。第二类是预测边的分类（link prediction），比如推荐系统中，User和Item之间是否有交互（浏览、点击等）行为，即为预测user和item之间是否存在连边。第三类是预测整个图的标签，比如说预测化学分子的类别。在我们的业务中，主要以前两种应用场景为主。本文不涉及GNN算法原理，主要介绍GNN算法的基本框架以及PlatoDeep对GNN算法的支持，最后分享GNN在应用任务中的实践经验。</p>
<p><strong>一、GNN算法框架</strong></p>
<p>       本小节主要介绍GNN算法框架，以及PlatoDeep对GNN算法框架的支持。</p>
<p><strong>1、GNN算法框架</strong></p>
<p>        斯坦福的Jure Leskovec教授在ICLR2019 发表的论文【1】中他将GNN的算法框架归纳为以下三步关键：，第一步是Aggregate：如何整合邻居节点的特征，第二步是Combine：邻居的特征和当前节点的特征如何整合，第三步Readout：整合将图中的所有节点的特征，用户表达整张图。论文提出“只要Aggreate/Combine/READOUT能够区别不同图的结构，那么这样的GNN算法和WL-test（验证两幅图是否同构的算法）同等强大的。” 这里第三步Readout只有在预测整个图的标签任务中才需要做。因此，基于Jure大牛的论文，及其我们的应用经验，本人将应用于节点标签或者边标签预测任务的GNN算法框架提炼为四个步骤：</p>
<ul><li>图构造：根据业务构造计算的图</li>
<li>Aggregate：邻居特征聚合</li>
<li>Combine：融合邻居特征和当前节点的特征，再做非线性变换</li>
<li>Predict：根据目标任务定义正负样本，设计LOSS函数</li>
</ul><p>         以节点标签预测任务为例，GNN算法框架的示意图如下：</p>
<p>            <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2a1266b18568bcc5c547.png"/></p>
<p>       首先，基于业务的理解构造图。而第二和第三步，基于应用业务的需求，设计算法Aggregate函数和combine函数。这里，们需要了解Aggregate函数的物理含义，并结合实际业务场景并进行相应的算法选择和设计（当然如果时间充足，可以对所有的算子进行评测），这里总结几个主流GNN算法的聚合函数及其物理含义如下：</p>
<p>                          <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/aabc03eab2dd23491e99.png"/></p>
<p>       第四步，在输出层，根据目标任务定义正负样本，设计LOSS函数，基本上在所有的机器学习算法框架都十分重要，在GNN算法for节点分类任务比较常用交叉熵LOSS，在Link Prediction中可以尝试BPR LOSS。有时候也会使用word2vec里面的负采样技术进行训练加速。</p>
<p>       以上算法框架主要是同构GNN算法的框架，对于异构GNN算法框架，需要增加一步，即基于Metapath-Aggregate或者叫语义级别的Aggregate。异构图含有不同类型的节点和不同类型的连边，我们一般会定义不同的Metapath以区分连边的物理含义。下图北邮石川老师的团队的论文【5】的框架图。论文提出的算法HAN先针对异构图首先定义不同的Metapath；其次，对每一类的metapath，对相同Metapath内的邻居节点分别进行Attention的Aggregate（Node-level聚合），得到节点在每一类metapath的embedding；再次，对不同metapath的embedding进行attention（Metapath-level聚合）学习，得出最终的embedding。最后，根据节点的embedding进行预测任务。</p>
<p>                               <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/26ea18166ea06d15101d.png"/></p>
<p>      异构GNN算法框架可以总结为（1）构造异构图（2）Node-Level的聚合（3）Metapath-Level的融合（4）预测任务。在论文【10】HetGNN算法在Node-Level使用了LSTM聚合，而Metapath-Level也是采用了注意力机制。</p>
<p><strong>2、大规模GNN算法：</strong></p>
<p>       GNN算法在工业界落地应用时，我们就需要进一步考虑算法模型大规模实现的效率。学术界也有不少论文来解决这个问题。GraphSage、FastGCN、Cluster-GCN、AS-GCN分别从图采样的角度优化计算效率。而S-GCN简化GCN非线性计算以提高训练速度。详细的几个论文及其思路整理如下，欢迎讨论交流。</p>
<p>                       <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/303a0b8271e439472aef.png"/></p>
<p><strong>3、PlatoDeep for GNN算法框架</strong></p>
<p>       基于对GNN算法理论框架的基础理解，以及对计算平台的调研。Plato团队开发了PlatoDeep。PlatoDeep提供千亿级别关系链和十亿级别节点的GNN算法。详细系统设计可参考KM文章《PlatoDeep：Plato团队开源新一代GNN图神经网络计算框架》。PlatoDeep开源代码：[内部或本地链接已移除]</p>
<p>       在PlatoDeep上，目前已经实现了包括GraphSAGE、GAT、GCN、SGC、DGI在内的6个算法同构图GNN算法，算法在PlatoDeep上以minibatch方式实现，在公开数据集的效果均能达到原论文中公布的效果。对于，异构GNN算法，Plato团队正在开发中，不久的将来即可以开放使用。另外，在PlatoDeep上，算法工程师还可以基于上文中GNN的算法框架在PlatoDeep上设计和开发实现新的GNN算法，为业务定制GNN算法。</p>
<p>                 <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/939ba1d83e7807d68be2.png"/></p>
<p><strong> 二、GNN算法应用</strong></p>
<p>        本小节主要介绍GNN算在在节点标签预测任务和点预测任务上的落地应用。并介绍我们在落地应用过程中，根据业务数据特性和数据需求对GNN算法的优化思路。</p>
<p><strong>1、节点标签预测任务</strong></p>
<p>       节点标签预测任务可以简单地用下图表示，在图中，部分节点的标签是已知的，需要去预测其他未知节点的标签。</p>
<p>                  <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/aec8ba9ed698cadf7743.png"/></p>
<p>          基于社交大数据，有很多业务任务都可以抽象为这个问题。第一类任务是社交画像，利用用户的社交关系推测用户年龄、用户兴趣爱好。第二类任务是社交召回，比如在朋友圈广告的社交lookalike，根据种子包用户去召回相似用户。</p>
<p>        朋友圈广告社交lookalike是数据中心长期支持的业务，围绕着对社交数据的理解和分析，进行了三个版本的技术迭代。2015年年底上线的第一版版本以人工统计社交特征为主，预测以GBDT+LR模型作为预测模型。自2017年团队研发Network embedding技术，Network embedding输出的结果表达社交特征，再将embedding特征用到预测模型中去。2019年起，我们尝试GNN模型端对端的模型，基于社交数据，用GNN进行社交特征自动表达，并进行端对端的训练和打分。</p>
<p>      我们在社交lookalike任务上有三个递进优化的GNN方案。首先，我们基于全网构造了一个和业务相关的社交关系图，并进行GAT模型的训练和预测，相比network embedding+XGB两阶段的模型，其效果得到不错的提升（点击互动率提升5%到10%不等）。其次，因为GNN类模型中缺少了特征之间的Cross模块，对于推荐场景特征cross非常重要，因此我们基于GAT设计了新模型CrossGAT模型。另外，对于节点标签预测任务，我们将原始的无监督标签传播的思想和GNN算法进行融合，参考了Mila实验室的论文【参考文献11】改造设计了新的模型，相对GAT模型，效果有10%以上的提升。这一块的工作我们将进行详细的分享。</p>
<p><strong>2、边标签预测任务</strong></p>
<p>在推荐系统中，预测user-item之间是否有连边，即为边标签的预测任务。平台的很多业务推荐都可以抽象为一个网络中边的标签预测问题。阿里有一篇比较好的实践论文，【参考文献12】是一篇用异构GNN用于用户搜索意图推荐的文章。业务场景是推荐淘宝首页搜索框里面默认搜索词。整个模型框架是user和query embedding组成的双塔GNN。（1）根据用户的行为构造异质图，图的节点包括user，item和query，定义UQI、UIQ两种metapath。（2）根据metapath分别对user和query进行在Node-Level的特征聚合。对于user，user的邻居节点是item、query，根据行为时间进行排序，用LSTM聚合到user上； 而对于query，query的邻居节点是无序的user或item，使用了CNN聚合（3）Metapath-Level使用了Concatenation。（4）输出层采用了MLP,这里首先输入了user和query的静态特征，和embedding特征进行拼接，一起进行任务预测。另外，为了减少参数量，作者在最开始的输入层加了term embedding层，即query和item的题目都是由几个term组成的，只为每个term学习到唯一的嵌入表示，再将其组合（直接用的mean）得到对应的query和item的embedding，这大大减少了参数量，增加了应用落地的可行性。目前PlatoDeep对异构GNN算法正在评测阶段，后续我们会分享异构GNN在社交推荐场景下的实践经验。</p>
<p><strong> 三、PlatoDeep的后续展望</strong></p>
<p>      PlatoDeep旨在为算法工程师提供高性能的GNN算法计算平台。一方面，我们会基于业务需求探索新的GNN算法方案，并在PlatoDeep上沉淀state-of-art的方案。另一方面，我们在加强对算法理论的分析理解，在图采样技术、训练性能等方面取得更好的效果。欢迎各位算法工程师使用PlatoDeep，一起讨论GNN算法，一起建设PlatoDeep！</p>
<p><strong>四、参考文献：    </strong></p>
<p>【1】ICLR2019论文 GIN: https://openreview.net/pdf?id=ryGs6iA5Km<br/>【2】ICLR2017论文 GCN https://openreview.net/pdf?id=SJU4ayYgl<br/>【3】ICLR2018论文 GAT: https://arxiv.org/pdf/1710.10903.pdf<br/>【4】NIP2017论文Graphsage：https://arxiv.org/abs/1706.02216<br/>【5】HAN论文：https://arxiv.org/pdf/1903.07293.pdf <br/>【6】ICLR2018论文 FastGCN: https://arxiv.org/pdf/1801.10247.pdf<br/>【7】KDD2019论文Cluster-GCN：https://arxiv.org/pdf/1905.07953.pdf <br/>【8】NIPS2018论文（AILAB出品）AS-GCN：https://arxiv.org/pdf/1809.05343.pdf<br/>【9】ICML2019论文S-GCN：https://arxiv.org/pdf/1902.07153.pdf <br/>【10】KDD2019论文HetGNN<br/>http://www.shichuan.org/hin/time/2019.KDD%202019%20Heterogeneous%20Graph%20Neural%20Network.pdf<br/>【11】ICML2019论文GMNN算法：https://arxiv.org/abs/1905.06214<br/>【12】KDD2019论文MEIec 算法http://www.shichuan.org/doc/67.pdf<br/>【13】PlatoDeep：Plato团队开源新一代GNN图神经网络计算框架. http://[内部链接已移除]<br/>【14】笛卡尔：机器学习Pipeline平台. http://[内部链接已移除]<strong><br/></strong></p> 
{% endraw %}
