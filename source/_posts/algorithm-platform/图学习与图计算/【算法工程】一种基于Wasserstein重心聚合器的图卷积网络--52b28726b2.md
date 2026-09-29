---
title: "【算法工程】一种基于Wasserstein重心聚合器的图卷积网络"
date: 2022-04-07 18:52:45
categories:
  - 算法平台
  - 图学习与内容理解
---

{% raw %}

<div>
<p>()：由公共运营，主要目的为展示最新游戏数据科学动态，分享前沿数据知识，秉承开源协同的理念，利用 KM 平台沉淀输出核心技术和游戏增长方法论，打造专业权威的游戏数据科学技术分享 K 吧，助力游戏持续增长。更多精彩请点击</p>
</div>
<h1>一、背景</h1>
<p>图是一种广泛使用的表示数据间关系的结构。近年来，随着深度学习的广泛应用，图神经网络引起了极大的关注。目前图神经网络已经被广泛用在了推荐系统，计算机视觉等领域。在传统图神经网络中，一个图网络节点通常被表示为嵌入式空间中的一个点。然而空间中的一个节点在表达多样性上有局限，最近研究者提出利用一个概率分布来表示一个图网络节点。本文将介绍一种新的基于Wasserstein重心聚合器的图卷积网络，并探索如何将这种网络用于道具推荐场景。</p>
<h1>二、相关工作</h1>
<p>论文[1]提出了GraphSage的图卷积网络。图网络中每一个节点可以表示成嵌入式空中的一个点。每一个嵌入式空间中的节点，由一个嵌入向量表示，可以由它的近邻节点聚合表示。具体可表示为图示的三个步骤：</p>
<ul><li>先对邻居随机采样，根据计算复杂度决定邻居采样数目（图中一跳邻居采样数=3，二跳邻居采样数=5）</li>
<li>通过聚合器（aggregator）生成目标节点embedding：先聚合2跳邻居特征，生成一跳邻居embedding，再聚合一跳邻居embedding，生成目标节点embedding，从而获得二跳邻居信息。</li>
<li>将embedding作为全连接层的输入，预测目标节点的标签。</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6ddc334e06bd3daa292f.png"/></p>
<p>算法的伪代码如下，</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/946c84d88ad9002ec63d.png"/></p>
<p>GraphSage定义了一种通用的图表示学习框架，包含邻居采样，聚合，节点预测三步，但是这种节点表示法将每一个节点限制为嵌入空间的一个点，不利于表示节点的多样性。在现实网络中，比如movielens数据集中，人观看电影构成的二分图中，一个人的偏好可能是多样的，既爱看科幻片也爱看喜剧片。在这种情况下，单一的嵌入式向量表示具有一定的局限性。</p>
<p>为了表达网络中节点的多样性，论文[2]提出了一种利用高斯分布来表示节点的方法，改进现有图表示学习中单点表示的缺陷。 此时，网络中的一个节点不是用一个嵌入式向量决定，而是由一个高斯分布产生，网络中相邻节点的相似性由节点分布的KL距离决定，而不是节点向量的内积计算。进一步地，论文[3]对论文[2]进行了改进，使用Wasserstein距离，而非KL距离来表示分布间的关系，提出了如下框架。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9e16b0114b22cfb7daab.png"/></p>
<p>论文[2，3]研究应用于通用图表示学习，并不强调图网络中节点间编码关系，如果将论文[3]中的表示方法，应用于GraphSage的图卷积网络结构。图网络中，每一个节点由它的近邻节点聚合表示而成，表示而成的近邻节点再利用一个非线性变化分别表示一个高斯结构的平均值和方差，最后通过这个高斯分布生成一个节点的最终表示，最终节点向量可以用如下结构表示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1180914f455b65a75e59.png"/></p>
<p><br/></p>
<p><br/></p>
<h1>三、模型介绍</h1>
<p>论文[1]中提供的方案，将图节点表示为嵌入空间中一个点，损失了节点物理意义上的多样性。论文[2，3[虽然使用了概率分布来表示节点来实现表达多样性，节点之间的相似性可以应用节点分布的差异性（KL距离或者Wasserstein距离）衡量。但是，每一个节点在图网络中传播信息时，仍是嵌入空间中的一个点即一个向量表示，图网络节点的聚合仍是基于向量的聚合，没有获取节点分布间的关系，这种方式容易导致节点信息在图网络中传播时丢失信息。</p>
<p>针对以上方案的缺陷，本文提出了一种新的基于Wasserstein重心聚合器的图卷积网络系统。类似的，本文也是用高斯分布来表示节点的多样性，但是在图网络中每个节点用高斯分布的均值和方差表示，在图网络的信息传播时，节点与节点间传播完整的高斯分布（均值和方差），而非一个分布产生的嵌入式向量，避免丢失信息。</p>
<h2>1. WGCN</h2>
<p>本文提出了一种基于Wasserstein重心聚合器的图卷积网络（WGCN）。WGCN 使用一个高斯分布的参数均值和方差来表示图网络中的节点，并在图中传播高斯分布的参数。图卷积网络学习中，聚合器起到了节点信息传播的作用，针对这种新的节点表示方法，WGCN一种新的Wasserstein重心聚合器（WB-AGG），下图展示了基于WB-AGG的图表示方法。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2f0bc10d40679f04c64a.png"/></p>
<p>WGCN定义了一套学习流程如下，</p>
<p><strong>1) 初始化网络节点模块</strong>，对图网络G(V, E)每一个节点使用h表示其嵌入式向量，即<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2306b2bd5ce1a75d5292.png"/>。</p>
<p><strong>2) 生成节点高斯分布参数模块</strong>，使用h表示节点高斯分布参数，均值和方差。对于第k层迭代时，节点v的高斯分布均值和方差表示为<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/27a9312a9642fadcedf3.png"/></p>
<p><strong>3) 基于WB-AGG</strong><strong>的聚合器模块</strong>，对于每一个节点v，给定其邻居节点集合N(v), 使用Wasserstein重心聚合器（WB-AGG）可以聚合网络中邻接点的信息，生成节点v的高斯分布表示，即图中橙色框所表示的模块，</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8717741c99720a7658ec.png"/></p>
<p>。</p>
<p><strong>4) 生成节点向量表示模块</strong>，对于给定每个节点的高斯分布参数，生成该节点的一个嵌入式表示，<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/dbce55190f1a083e093c.png"/></p>
<p>。接下来，本系统使用聚合节点上一层的表示和当前生成的嵌入式向量，生成最终的节点表示，<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/631ed4d874230385772c.png"/></p>
<p>，</p>
<p>其中，W为网络参数，为sigmoid函数。</p>
<p>综上，WGCN的图网络节点嵌入式学习算法流程如下图所示,</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6286de2da5e9ae7cb0b5.png"/></p>
<h2>2. WB-AGG模块</h2>
<p>Wasserstein重心聚合器（WB-AGG）模块实现了图拓扑中节点分布间的信息聚合过程，是WGCN的一个核心模块。在之前的图表示学习中，聚合器函数的输入都是节点的向量表示，常用的聚合函数如求向量均值，明显不适用于高斯分布的聚合。此处，为了聚合邻近节点的分布信息，WGCN定义了一个Wasserstein重心。物理上，所有邻近节点的Wasserstein重心表示一个距离邻近节点概率分布的Wasserstein距离最小的那个概率分布。假设每个节点可以用一个高斯分布表示，那么聚合后的Wasserstein重心也一定可以用一个高斯分布表示。那么聚合后的高斯分布的均值和方差可以用如下方法求得，</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/33068a5a2dfd1f99d494.png"/></p>
<h1>四、实验结果</h1>
<p>本文在图节点分类任务上进行了实验，实验包含了三个数据集，数据集概况如下。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/278fe6f87773de5e6e14.png"/></p>
<p>Cora、PubMed、Citeseer是三个论文引用数据集，由论文和他们的关系构成的网络，这些关系包括例如引用关系、共同的作者等，具有天然的图结构，数据集的任务一般是论文的分类和连接的预测。 每个样本点都是一篇科学论文，所有样本点被分为多个类别，每篇论文都由一个高维的词向量表示，作为节点特征。词向量的每个元素都对应一个词，且该元素只有0或1两个取值。</p>
<p>具体的，Cora包含2708个论文节点，词向量特征为1433维，论文包含7个类别，分别是1）基于案例；2）遗传算法；3）神经网络；4）概率方法；5）强化学习；6）规则学习；7）理论。论文间的引用关系构成了5429条边。这些信息都包含在上述表格中。Citeseer，Pubmed也具有相似的图网络结构信息，详细数值在上述表格中展示。</p>
<p>我们提取80%的节点构成的图作为训练，20%的节点作为测试，预测节点的分类。实验结果如下图，报告的值为各个模型的节点分类的准确率。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/90008a8600fea35aff52.png"/></p>
<h1>五、推荐应用场景</h1>
<p>图神经网络可以直接用于图协同过滤架构，在图协同过滤框架中，我们可以对用户和游戏内道具构建一个二分图，然后利用图卷积神经网络学习用户和道具的图嵌入式表达，最后利用一个得分函数衡量用户和道具的链接可能性，根据这个得分预测用户可能喜欢的道具。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/3ff2bde436bbd4b52b67.png"/></p>
<p>对于图协同推荐，每一个用户和道具可以看做图网络中的一个节点。当用户和道具之间有交互（比如下载，购买，使用等行为）的时候，就在这两个节点之间构成一条边。同样的，当用户和用户之间有交互(比如加为好友或者组成战队)时，可以在用户节点之间构成边；当道具和道具交互（比如分享某些共同特性）时，可以在道具节点间构成边。下图以用户在乐高游戏中，与使用地图的交互为例，阐述图构建流程。此例只考虑玩家和地图的交互信息，可构成一个交互二部图，左侧蓝色节点为玩家，右侧橙色节点为地图。当一个用户使用过该地图时，在两个节点间构成一条边。相比于协同过滤方法，图协同过滤方法在学习网络节点表示过程中，可以学习玩家-地图的高阶关系，更好的预测玩家的偏好。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a9897351a199cdf3ffef.png"/></p>
<h1>参考文献</h1>
<p>[1] W. Hamilton, Z. Ying, J. Leskovec, Inductive representation learning on large graphs, in: Advances in Neural Information Processing Systems, 2017, pp. 1024~1034</p>
<p>[2] Bojchevski A, Günnemann S. Deep gaussian embedding of graphs: Unsupervised inductive learning via ranking[J]. arXiv preprint arXiv:1707.03815, 2017.</p>
<p>[3] Zhu D, Cui P, Wang D, et al. Deep variational network embedding in wasserstein space[C]//Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery &amp; Data Mining. 2018: 2827-2836.</p>
<p><br/></p>
<p><br/></p>
<p>欢迎大家加入<strong></strong> ，解锁更多游戏数据科学核心技术和游戏增长方法论！<br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/937c2a614f865b84eb3f.jpg"/></p> 
{% endraw %}
