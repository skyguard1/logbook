---
title: "user embedding技术5：GraphSage在社交网络上的实践"
date: 2022-04-16 10:38:24
categories:
  - 算法平台
  - 图学习与图计算
---

{% raw %}

<h2>一、背景介绍</h2>
<p>        Network embedding算法从其学习目标角度可以分为两大类，第一类是topology driven的embedding算法，即其主要目标是表达网络的拓扑特征；第二类是feature driven的embedding算法，对节点特征和拓扑结构进行融合表达。系列前文介绍了topology driven的embedding算法（不加入节点特征信息的GAE/VGAE），本文重点介绍feature driven的embedding算法—GraphSage的算法原理。并通过实验，分析GraphSage的聚合函数、卷积层数、抽样好友数等因子对效果的影响。</p>
<h2>二、GraphSage算法简介</h2>
<p>        原始的GCN类算法有两个缺陷：（1）需要输入整幅图的邻接矩阵以及所有节点的特征向量 ，对全图进行卷积操作，而当处理像这种十亿级节点千亿级边的大规模网络的时候，难以处理。（2）是一种直推式（transductive）的学习算法，即只能学习当前输入到模型的网络节点的embedding，学习出来的模型难以应用到新增的节点或者新的图，而现实中的网络结构一般都是快速变化的，经常会出现新边或者新的节点，直推式（transductive）学习算法难以适用。</p>
<p>         斯坦福大学的JureLeskovec团队在NIPS017提出了GraphSage模型，通过以下两方面的改进来解决掉上述原始GCN的两个缺陷：（1）不是直接对全图进行卷积，而是通过对目标节点的邻居进行随机采样得到子图，再对子图进行卷积，大大降低了计算和内存的压力。（2）不是直接学习网络节点的embedding，而是学习一个聚合函数（aggregator）,这个聚合函数能够把邻居节点的特征聚合到中心节点的身上。当我们学习出聚合函数后，就可以泛化到新的节点或者新的网络上，即使是在训练过程中模型没有见过的节点也能推断出其embedding，是一种归纳式（inductive）学习算法。GraphSage的算法架构如下图所示分为三个步骤：</p>
<ol><li>对图中的每个节点采样固定数量的邻居节点作为该节点的邻居节点集合。</li>
<li>通过模型学习的聚合函数（aggregator）对步骤1中采样得到的邻居节点集合进行聚合，把邻居集合节点的特征信息聚合到中心节点上，得到新的节点Embedding。</li>
<li>由步骤2邻居聚合得到的新的节点embedding用来进行下游的预测任务。</li>
</ol><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c82a0ee46fc209163ffc.png"/></p>
<p>生成embedding向量的伪代码如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/035e969de62f72a94b93.png"/></p>
<p>其中K为图卷积的层数，表示每个节点聚合几阶邻居。在外层循环的第k次迭代中,对于每个节点v首先通过聚合函数<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/794f4c7ea36be63afb86.png"/>来对节点v的邻居节点的k-1层embedding向量<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d74ca18103cf8080566e.png"/>进行聚合，得到节点v第k层的邻居聚合embedding<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e19f68d449269b9f3159.png"/>，再把<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e19f68d449269b9f3159.png"/>和节点v的k-1层embedding<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4abca60f34b38c83c3ac.png"/>拼接起来，再接一个全连接层，最终得到节点v第k层的embedding<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5f7088597d9dbed6bd0f.png"/>。</p>
<p>        在整个GraphSage算法框架中，聚合函数是最重要的一个部分。由于节点的邻居节点集合是无序的，聚合函数不仅需要有很强的表征学习能力，还需要是对称性（symmetric）的，即函数的输出与输入聚合函数的节点顺序无关。原论文中提出了GCN aggregator、mean aggregator、pooling aggregator以及LSTM aggregator四种聚合函数。需要注意的是，LSTM aggregator虽然有更强大的表征能力，但是却不符合对称性的要求，而原论文的实验结果表明采用LSTM aggregator仍然能够取得较好的效果。</p>
<h2>三、GraphSage在公众号阅读推荐中的实践</h2>
<p>         GraphSage是以节点的特征作为原始输入，在本文的实验中，我们基于用户的阅读行为序列，利用Bert的算法，得到用户的兴趣向量特征。该特征作为节点的初始特征输入。然后我们利用Graphsage进行用户表达，最后利用用户的结果向量，计算内积进行公众号的推荐。大概的思路如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6900463d1c009e33a1ea.png"/></p>
<p>        从推荐的角度来说，BERT的物理含义主要是利用了item协同，对于行为稀疏行为的用户，其Embedding向量质量较差，因此我们进一步将BERT模型和 GraphSage模型进行融合，在Bert的基础上增加user社交协同的思想，得到user Embedding向量。</p>
<p>我们的实验总结如下：</p>
<ul><li><strong>实验数据：</strong>在社交网络中抽样实体圈用户（用户约70万），以及用户在过去一个月内阅读过的公众号序列（约50万个公众号）</li>
<li><strong>训练正负样本：</strong>用户在训练集中阅读过的公众号作为正样本，在全局公众号中随机抽取公众号作为负样本，正负样本比例为1：10。</li>
<li><strong>Loss</strong><strong>函数设计：</strong>由于我们抽取的正负样本比例为1：10，存在正负样本不平衡问题，我们采用了focal loss作为loss函数，以解决正负样本不平衡问题。</li>
<li><strong>评估方法：</strong>对每一个用户取embedding距离最近的top10公众号，评测这部分公众号在未来7天阅读数据测试集中的top10召回率</li>
<li><strong>对比算法</strong>：</li>
</ul><ol><li><strong>BERT：</strong>对用户在过去一个月内阅读过的公众号按时间顺序排列，通过BERT训练得到user embedding。</li>
<li><strong>BERT +好友平均：</strong>把BERT训练得到的user embedding做好友平均，得到user embedding。</li>
<li><strong>BERT +GCN：</strong>以BERT训练得到的user embedding作为GCN的初始化embedding向量，训练GCN模型（全图卷积），得到新的user embedding。其中GCN层数是一层，loss为focal loss。</li>
<li><strong>BERT +GraphSage：</strong>以BERT训练得到的user embedding作为GraphSage的初始化embedding向量，训练GraphSage模型，得到新的user embedding。</li>
</ol><ul><li><strong>实验结果分析：</strong></li>
</ul><p>一、整体结果分析</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/81bd9b64d431759cf0fb.png"/></p>
<p>从实验结果可以看出：</p>
<ol><li>在BERT学习item协同的基础上引入社交好友协同信息，能提升user embedding的效果。</li>
<li>即使是简单地做好友平均而不用任何模型训练也能得到一定的提升。</li>
<li>通过GCN或GraphSage的进一步训练，比原始的BERT模型要提升4个百分点。</li>
<li>在这个case中全局卷积的GCN与进行好友采样的GraphSage效果差别不大。</li>
</ol><p>二、GraphSage采样好友数的分析</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1a49e1b4ccf8915f30a2.png"/></p>
<p>实验结果可以看出：</p>
<ol><li>top10召回率随着采样好友数增大而增大，其中有采样好友数由10个增大到50个时，recall@10增大得较为明显。</li>
<li>采样好友数大于50之后recall@10的增幅较小，对模型效果的收益不大。</li>
</ol><p>三、卷积层数的分析</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6ebb6bc34061fc81776d.png"/></p>
<p>上图分别为一层卷积，好友采样数为10的结果；一层卷积，好友采样数为50的结果；两层卷积，两层卷积的好友采样数分别为10，25的结果。由实验结果可以看出：</p>
<ul><li>第一层的好友采样数相同的情况下，增加一层卷积能明显增强模型的效果。</li>
<li>模型单纯增加好友采样数的效果也能达到增加卷积层数的效果，甚至更好。</li>
</ul><p>四、聚集函数的分析</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/51ddb768cc81eee1c252.png"/></p>
<p>实验结果的结论与graphsage原论文一致，都是pool aggregator和lstm aggregator的效果要优于mean aggregator，而lstm aggragator、pool aggregator及mean aggregator的效果都要比gcn aggregator的效果好不少。</p>
<h2>五、总结</h2>
<p>        我们对GCN、GraphSage两种种经典的GNN模型在社交网络中做了实践。在小规模网络中初步的实验结果表明在用户本身已经有一个较好的特征向量时，再通过GNN模型把用户社交好友协同信息引入进来，能获得效果的提升。     </p>
<p>        GraphSage模型通过采样技术及学习聚合函数而不直接学习user embedding这两个方法很好地解决了实际落地中的一些难点，这个case的实验结果也表明GraphSage虽然在卷积时对邻居做了采样，但是模型效果跟GCN差不多，采取GraphSage的方式大规模落地GNN是很好的选择。</p>
<p>        数据中心研发的柏拉图平台提供包括node2vec、metapath2vec等传统network embedding算法组件以及GNN相关的算法组件，供业务团队根据不同需求来生成所需的embedding：</p>
<ul><li><strong>的相关数据</strong><strong>embedding</strong><strong>结果</strong>，会在<strong>笛卡尔特征库</strong>中供大家使用。</li>
<li><strong>柏拉图平台提供</strong><strong>embedding</strong><strong>相关算法组件</strong>，供业务团队生成需要的Embedding。</li>
</ul><p>如有需求，欢迎合作！</p>
<p>参考文献：</p>
<p>[1]Transformer: <a href="https://papers.nips.cc/paper/7181-attention-is-all-you-need.pdf">https://papers.nips.cc/paper/7181-attention-is-all-you-need.pdf</a></p>
<p>[2]Bert: <a href="https://arxiv.org/pdf/1810.04805.pdf%E3%80%91">https://arxiv.org/pdf/1810.04805.pdf%E3%80%91</a></p>
<p>[3]GCN：<a href="https://openreview.net/pdf?id=SJU4ayYgl">https://openreview.net/pdf?id=SJU4ayYgl</a>  </p>
<p>[4]Graphsage：<a href="https://papers.nips.cc/paper/6703-inductive-representation-learning-on-large-graphs.pdf">https://papers.nips.cc/paper/6703-inductive-representation-learning-on-large-graphs.pdf</a></p>
<p>[5] User embedding技术应用综述: [内部或本地链接已移除]</p>
<p>[6] 用户行为序列建模Bert4UserEmbedding: [内部或本地链接已移除]</p>
<p>[7] Bert大规模预训练算法:  [内部或本地链接已移除]</p>
<p>[8] SocialTrans：BERT与GNN的结合:  [内部或本地链接已移除]</p>
<p>[9] Graph Auto-Encoder在社交网络上的实践:  [内部或本地链接已移除]</p>
<p>[10] 柏拉图network embedding算法参考:  [内部或本地链接已移除]</p> 
{% endraw %}
