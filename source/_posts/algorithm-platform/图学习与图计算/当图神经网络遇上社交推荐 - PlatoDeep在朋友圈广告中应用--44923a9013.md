---
title: "当图神经网络遇上社交推荐 - PlatoDeep在朋友圈广告中应用"
date: 2022-04-16 10:39:16
categories:
  - 算法平台
  - 图学习与内容理解
---

{% raw %}

<h1>1. 前言</h1>
<p>         2017~2019年图神经网络（GNN）在学术界遇上了井喷式的发展。GNN提供了处理图网络的一种新思路，即图网络中的节点可以通过聚合邻居信息获得其在拓扑上的表达信息，从而提高了每个节点的表达能力。相比于学术界的繁荣，工业界上落地的GNN应用仍缺了火候，成功例子并没这么多。工业案例集中在金融风控和异常检测[1][2]、推荐系统[3]、在用户画像[4]和知识图谱[5]方面亦有所涉及。GNN的相关算法在[16]中已有所提及。在这里<strong>我们分享一个成功的例子，是</strong><strong>GNN</strong><strong>在社交广告推荐上的应用。与Baseline相比，点击或互动率平均提升8.3%。</strong></p>
<p>         工欲善其事，必先利其器。<strong>案例的成功得益于数据中心开源的深度学习图计算引擎</strong><strong>PlatoDeep</strong><strong>[6]</strong>。关系链现在已经增长到3千亿量级，在没有PlatoDeep之前，我们只能以较大计算/存储开销进行小规模的测试。现线上测试的PlatoDeep可在20分钟内完成单个广告的社交推荐需求（仍有较大的优化空间）。</p>
<p>         以下是硬广时间，有需求欢迎来撩：</p>
<ol><li>PlatoDeep提供千亿级别关系链和十亿级别节点的GNN计算平台：[内部或本地链接已移除]</li>
<li>笛卡尔[7]提供各类机器学习算法与用户画像特征库</li>
<li>提供各类社交推荐方案，帮助业务利用关系链的价值</li>
</ol><h1>2.业务介绍</h1>
<p>         朋友圈广告是公司的重要业务之一。社交广告是它有别于其他平台的重要特征之一。早在2012年的论文[8]中，就探索过显示互动好友会对广告有正向效果，以及随着显示广告的互动好友数增加，广告对用户的吸引力也会增加。的数据也有同样的结论，我们分析观察到<strong>用户点击率和互动率会随着互动好友数的增加而上升</strong>。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9d825a87cb37ab9ca32d.png"/></p>
<p>Figure 1-广告是否显示互动好友对广告影响[8]</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b8f6f6e19f928d3ebf11.png"/></p>
<p>Figure 2 社交广告互动案例</p>
<p>         可以看出，社交环境对用户是否点广告来说是十分重要的。数据中心这边在社交广告上承担了一定的流量（相关同事为jerrycgsong和jensenliao）。为了利用上述的分析结论和社交环境的优势，在这里广告的召回用户将限定在广告的互动用户好友之中。随后使用PU-learning的lookalike技术，针对每个广告，以种子用户为正样本，随机用户为负样本，学习二分类模型。产出的二分类模型会对候选用户进行排序。这里排序出来的头部候选用户，具有与互动好友相似，并且在本广告上也拥有互动好友的特点。最后为了充分考虑时效性，本计算流程会一天触发数次，实时对用户包进行更新。具体流程如下图所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f211dce5bd22d4877be7.png"/></p>
<p>         在本文中，我们<strong>优化了流程中的</strong><strong>PU-Learning</strong><strong>模块，将原有的XGB</strong><strong>模型替换成了GNN</strong><strong>的一个著名算法Graph Attention Networks (GAT)</strong>[9]。</p>
<h1>3.算法适配与改造</h1>
<h2>3.1 算法原理</h2>
<p>         GAT算法的核心原理，是利用注意力机制对图网络中的每个节点，对邻居信息进行聚合。设节点i的邻居为j，则节点i的一阶邻居拓扑聚合特征如下图所示。这里代表节点i的拓扑特征是由其邻居特征聚合并经过非线性变换而来。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/fb544d235b8e39f05696.png"/></p>
<p>         上式中\alpha_{ij}代表邻居j对节点i的权重，该权重是通过一个神经网络计算而来。神经网络的输入是节点i和节点j的特征，经过非线性变换后通过一个softmax层，将数值归一化。即\sum_j \alpha_{ij}=1。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ba9da0e993fd4984b868.png"/></p>
<p>        一般情况下，为了考虑高阶邻居的属性，模型会进行多次的上述聚合操作。代表得到的聚合特征是考虑了高阶邻居的结果。</p>
<h2>3.2 算法适配</h2>
<p>         在社交广告上，我们将用户的好友关系链当作GAT的输入图，并按照PU-Learning的流程对每个节点进行二分类，预测其是否互动用户。这里出于的考虑：</p>
<ol><li>GAT可以考虑网络中的拓扑结构，这是以往Baseline所考虑不到的。每个节点可以通过GAT的聚合公式，获得邻居的特征聚合作为其社交属性的表达。另外注意力机制，可以让节点对不同的好友有不同的关注度。比如广告兴趣相近的好友权重更高。</li>
<li>希望召回的用户包在图上互相相邻，从而更好的达到网络效应。在学术界场景中，GNN类算法表现好的一个原因是数据集中相邻节点的标签相同概率非常高[10]。在社交广告场景中这个结论也存在。利用GNN算法预测候选用户的得分时，高得分用户在网络上的聚集性会比随机用户要高。从而能达到预测用户成团的特性。</li>
</ol><p>        在对GAT进行适配的过程中，我们对原算法进行了以下的改造：1) 邻居采样; 2) 节点特征与邻居特征以concat形式拼接; 3) 关系链子图限制; 4) self labeling;</p>
<h3>3.2.1 邻居采样</h3>
<p>         GAT的原本实现[11]是对针对每个节点对所有邻居均进行信息聚合。然而，在我们的数据集中存在较多的节点拥有上千个邻居（最大好友数限制为5000）。聚合邻居数目较时，会出现运算速度稍慢的问题。在这里为了平衡速度和效果，我们最后选取了GraphSage[12]随机抽样邻居的方式。目前这个实现已整合到platoDeep[13]。</p>
<h3>3.2.2节点特征拼接</h3>
<p>         GAT的原本实现中，在整合节点自身特征和邻居特征时，采取的是“自连边”的方式。即每个节点对自己本身有边相连，在参与聚合运算时将自身特征当作邻居考虑。即</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/028ed65341e9b6c04f7b.png"/></p>
<p>         这种方式的问题是无法区分聚合的特征是邻居还是从自身而来。因此在这里我们选择了特征拼接的方式。我们对这种修改进行了离线测试，在一个广告包上PU-Learning二分类的准确率从63.4%提升至71.3%。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5145e62bbc4f726379fc.png"/></p>
<h3>3.2.3 关系链子图限制</h3>
<p>         在广告投放场景中，广告主常常会进行定向筛选。比如宝马的汽车广告，可能会选常驻地在北上广深并且年龄在25-50岁之间的人群。在刚开始使用GAT的时候，我们当时假设关系链图中所有节点都有用，因为这是代表用户本身的社交信息。但是发现其效果不如不使用图拓扑特征的LR和XGB。这里就让我们开始怀疑GAT的适用场景。在研读了ICLR2020的论文[10]后，我们发现GNN适用的场景需要有两个条件：</p>
<ol><li>相邻节点的标签应该尽量相同。</li>
<li>相邻节点的特征应该尽量不相似。</li>
</ol><p>         使用全量关系链违背了上述条件1，因为大部分节点均不会在该广告投放中出现。而条件2是满足的，我们使用了笛卡尔的用户特征库，包含用户基础属性和各行为的embedding，用户特征的描述是比较充分的。因此在这里，我们尝试了将关系链限制在广告投放的定向用户中。在离线流程上终于超越了XGB/LR的算法。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/68afd16d763c74b6596e.png"/></p>
<h3>3.2.4 self labeling</h3>
<p>         社交广告上的互动用户数常常比较少，大部分广告的互动用户数在千和万之间。有少数的广告互动用户能达到百万级别的规模。因此样本数据缺失是一个比较严重的问题。在这里，我们选取的方案是通过将模型预测得分较高或者较低的候选用户，重新放回正负样本中。扩大样本集的数目，减少过拟合的风险。最近GMNN[14]和GAM[15]也是采用类似的思路，将模型的预测结果重新放回并重新训练，由于篇幅有限，在本篇中并不展开。有兴趣的读者可以关心我们下一文章的结果，讲述的是在现有基础上如何再魔改GAT。</p>
<h1>4.业务效果</h1>
<p>        最后我们在朋友圈上对适配好的GAT进行测试，对比的Baseline是现在的线上流量。Baseline选用XGB模型，它的流程、输入特征、正负样本均与GAT对齐。<strong>特征使用的是笛卡尔平台提供的用户基础属性、广告</strong><strong>Embedding</strong><strong>、文章Embedding</strong><strong>（数据也开放给各位，欢迎大家试用笛卡尔）。</strong>在线上我们观察的核心指标是用户的点击或互动率。</p>
<p>        在我们目前所有测试过的所有广告中，<strong>点击或互动率平均提升</strong><strong>8.3%</strong>，点击率平均提升5.6%，<strong>互动率平均提升</strong><strong>22%</strong>。后续我们会考虑更多的广告进行放量测试。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/3d8d2259f7d04511b580.png"/></p>
<p>         在上述结果中，互动率有十分明显的提升。我们猜想这里的原因是，GAT推出的用户包具有成团的特性。这是以往的模型所考虑不到的，因为baseline模型只能根据个性化特征进行二分类。在这里我们选择了衡量社团结构紧密性的密度（density），来统计召回头部用户的成团情况。具体定义为：</p>
<p>密度 = 用户包中好友关系对数 / [0.5 * 用户包用户数 * (用户包用户数 – 1)]</p>
<p>         由于要对比的用户包大小是固定的，为了简化计算，在这里我们忽略分母。我们选取了广告在某天投放过程中的一个用户包进行统计。可以看出GAT算法出来的包的密度是比XGB高54%。<strong>说明了GAT投出的包具有更强的社团性</strong>，正是我们想要的！</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/0b266e6db6b7c74269ba.png"/></p>
<h1>5.总结与展望</h1>
<p>         我们探索了GNN在社交推荐场景上的应用，在多个广告上互动率有22%的提升。然而，目前PU-Learning的做法仍有一些问题，比如无法利用广告特征、样本较少、针对多个候选推荐item计算速度慢（即广告数目增多）。未来我们希望能把做法适配并推广到其他场景上，比如利用关系链进行社交内容推荐。</p>
<p>         在此感谢兄弟小组给与的支持，感谢powergao和wenqiangwu提供platoDeep系统上的支持，感谢jerrycgsong、tylerhzchen和jensenliao提供算法接入应用测试的支持。</p>
<p>         后续我们也会推出手把手教学。教大家如何在platoDeep上面玩耍千亿级别的关系链。敬请期待。</p>
<h1>引用</h1>
<p>[1] 异质图神经网络在反诈骗业务中的应用：提升对恶意卡的提前预警能力. [内部或本地链接已移除]</p>
<p>[2] Spam Review Detection with Graph Convolutional Networks. <a href="https://arxiv.org/abs/1908.10679">https://arxiv.org/abs/1908.10679</a></p>
<p>[3] Graph Convolutional Neural Networks for Web-Scale Recommender Systems. https://arxiv.org/abs/1806.01973</p>
<p>[4] 千亿图数据上的深度学习：用FastGCN预测行业. [内部或本地链接已移除]</p>
<p>[5]【游谱】基于图卷积神经网络的知识图谱实体对齐.[内部或本地链接已移除]</p>
<p>[6] PlatoDeep：Plato团队开源新一代GNN图神经网络计算框架. [内部或本地链接已移除]</p>
<p>[7] 笛卡尔：机器学习Pipeline平台. [内部或本地链接已移除]</p>
<p>[8] Social Influence in Social Advertising: Evidence from Field Experiments. <a href="https://arxiv.org/abs/1206.4327">https://arxiv.org/abs/1206.4327</a></p>
<p>[9] Graph Attention Networks. <a href="https://arxiv.org/abs/1710.10903">https://arxiv.org/abs/1710.10903</a></p>
<p>[10] Measuring and Improving the Use of Graph Information in Graph Neural Networks. <a href="https://openreview.net/pdf?id=rkeIIkHKvS">https://openreview.net/pdf?id=rkeIIkHKvS</a></p>
<p><a href="https://github.com/PetarV-/GAT">[11] https://github.com/PetarV-/GAT</a></p>
<p>[12] Inductive Representation Learning on Large Graphs. <a href="https://cs.stanford.edu/people/jure/pubs/graphsage-nips17.pdf">https://cs.stanford.edu/people/jure/pubs/graphsage-nips17.pdf</a></p>
<p>[13] GAT在PlatoDeep中的实现。[内部或本地链接已移除]</p>
<p>[14] GMNN: Graph Markov Neural Networks. <a href="https://arxiv.org/abs/1905.06214">https://arxiv.org/abs/1905.06214</a></p>
<p>[15] Graph Agreement Models for Semi-Supervised Learning. https://papers.nips.cc/paper/9076-graph-agreement-models-for-semi-supervised-learning</p>
<p>[16] GNN算法框架及其应用概述. [内部或本地链接已移除]</p> 
{% endraw %}
