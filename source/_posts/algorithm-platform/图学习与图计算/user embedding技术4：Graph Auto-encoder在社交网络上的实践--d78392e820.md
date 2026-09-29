---
title: "user embedding技术4：Graph Auto-encoder在社交网络上的实践"
date: 2022-04-16 10:35:36
categories:
  - 算法平台
  - 图学习与内容理解
---

{% raw %}

<h2>一、背景介绍</h2>
<p>        Network embedding算法从其学习目标角度可以分为两大类，第一类是topology driven的embedding算法，即其主要目标是表达网络的拓扑特征，比如以Deepwalk/Node2vec/LINE为代表是表达局部拓扑结构，以structure2vec为代表是表达全局拓扑结构相似。第二类是feature driven的embedding算法，它以图的拓扑结构作为辅助信息，对节点自身特征进行feature smoothing生成embedding, 相当于是节点特征和拓扑结构进行融合表达。这类算法以加入节点自身特征向量的GNN算法为主。而在Graph Auto-encoder的框架下，不加入节点特征，利用GCN作为编码器学习节点的embedding，其本质也是表达网络的拓扑特征。本文主要是对Graph Auto-encoder算法进行阐述，并且在社交网络和行为网络上进行实验，并与Node2vec等算法进行对比分析。</p>
<h2>二、<strong>Graph Auto-Encoders/Variational Graph Auto-Encoders简介</strong></h2>
<p>        GAE/VGAE是Thoms N. Kipf在NIPS 2016 Bayesian Deep Learning Workshop中提出的两个模型，其主要思路是把自编码器（Auto-Encoders）/变分自编码器（Variational Graph Auto-Encoders）迁移到图领域，以GCN作为编码器，把输入的图通过编码器学习节点的向量表示（GAE）或学习节点向量的分布并从分布中采样得到节点的向量表示（VGAE），再通过对不同节点之间做inner product预测是否有连边作为解码器来重构图（重构邻接矩阵）。本文先简述传统的自编码器及变分自编码器然后介绍如何把自编码器和变分自编码器引入到图结构数据中。</p>
<h3>自编码器</h3>
<p>        传统的自编码器是一种包含编码器和解码器的神经网络架构。其思想是通过编码器（encoder）把输入X压缩成低维空间表示向量Z，然后再通过解码器（decoder）去重构输入X，即生成与输入X尽可能相近的输出<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/499f688e7d6de1759f8f.png"/>。自编码器的目的是希望通过训练出能够重构输入的自编码器来学习出能够表征输入数据的低维向量表示（embedding）。常见的编码器和解码器可以是MLP、CNN、LSTM、transformer等。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f73305055e81ed7891ea.png"/></p>
<h3>变分自编码器</h3>
<p>        与自编码器不同的是，变分自编码器不是直接通过编码器去学习输入数据的低维表示向量，而是学习其分布，假设每一个输入样本都服从一个正态分布，通过编码器来学习该分布的均值<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/92203d36eb9cd2983d5c.png"/>和方差<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/971433f423afd8b8db0b.png"/>，然后从该分布中采样得到该输入样本的低维向量表示：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/da5bd0f60fecf78c08c3.png"/>，其中ε服从标准正态分布。再通过解码器生成来重构输入X。与自编码器相比，变分自编码器的优点是能够从原始输入数据中学习其数据分布，并生成新的数据样本，而不是仅仅去逼近原始的输入数据。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/78c2c79a46c6f3861e42.png"/></p>
<h3>图自编码器</h3>
<p>        图自编码器是把自编码器的思想应用到图数据中，学习图节点的向量表征。由于图数据通常都是不规则的非欧几里得结构数据（Non-Euclidean Structure Data）,常用的编码器如MLP、CNN等难以对图数据进行处理，需要用图卷积神经网络（GCN）作为编码器，对图的节点进行编码。图卷积神经网络在内外网有很多更丰富详细的资料介绍，这里不再赘述，简单来说就是通过神经网络学习如何把邻居节点的特征信息聚合到节点自己身上，从而得到节点新的向量表征，一层GCN仅聚合一阶邻居的特征信息，通过叠加多层GCN可以实现多阶邻居的信息传递。其输入是邻接矩阵A，节点的向量表示X，输出节点新的向量表示Z。得到节点新的向量表示Z后，再以Inner Product作为解码器来重构邻接矩阵A，即通过节点与节点之间的向量表示作内积来计算节点之间的相似度，从而预测节点之间是否有连边。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4bc349513e88741b44fe.png"/></p>
<h3>变分图自编码器</h3>
<p>        变分图自编码器与图自编码器类似，都是通过GCN来作为编码器，Inner Product作为解码器来学习节点的embedding。不一样的是，变分图自编码器通过GCN来学习输入数据分布的均值<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/92203d36eb9cd2983d5c.png"/>和方差的对数<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ff6cba23ec2dd8ea6c6e.png"/>(之所以不直接学习方差是因为总是非负的，需要加激活函数处理，而<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ff6cba23ec2dd8ea6c6e.png"/>不需要，更好学习)，而最终生成节点的embedding为<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5911db08afb918580978.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d3cd067f893fe78e6f64.png"/></p>
<h2>三、Graph Auto-Encoders/Variational Auto-Encoders在社交网络中的实践</h2>
<p> 我们在真实的社交网络中抽样了一个子网络以测试GAE/VGAE的效果：</p>
<ul><li>实验数据：抽样社交网络，得到一个实体子网络；</li>
<li>预测目标：预测用户之间是否有好友连边；</li>
<li>评估方法：在网络中随机移除20%的边作为测试集</li>
<li>评估指标：AU-ROC和AU-PR</li>
<li>对比算法：Node2vec、GAE、VGAE三种算法</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/569a4435c6396ecd5348.png"/></p>
<p></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/dece15f650f2fb5252cb.png"/></p>
<p>从上图实验结果可以看出， GAE和VGAE模型生成的节点embedding在Link Prediction任务中的效果比Node2vec稍高，GAE和VGAE之间效果相差不大。</p>
<p> 我们还对比了不同GAE和VGAE中不同GCN层数的效果差异：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4929b332e06f58a75b44.png"/></p>
<p>由上图可以看出，在抽样网络中对GAE和VGAE增大GCN层数后效果变化也不大，这与许多论文中的结论类似，一层或两层GCN就已经能取得很不错的效果，增大GCN层数并不能明显提升模型效果，盲目增大GCN层数甚至会出现over-smooth现象（即由于叠加太多层GCN，同一连通分量内的节点表征向量趋向于收敛到同一值）而使模型效果变差。而在本文实验中，我们发现两层GCN相比一层GCN没有明显提升，推测其原因是抽样网络的边非常稠密导致。</p>
<h2>四、Graph Auto-Encoders在user-item异构网络中的实践</h2>
<p>我们把GAE从同构网络中迁移到用户-公众号阅读异构网络中，用GCN作为encoder来学习用户和公众号的embedding，用inner product作为decoder，预测用户及公众号之间是否有连边。</p>
<ul><li>实验数据：抽样行为网络，抽取十万级用户，月百万级的阅读边，构成用户的阅读网络，是一个user-item的异构网络</li>
<li>评测指标：预测用户阅读边，评测标准是用户在未来7天内新建立的公众号阅读边， Top K命中率。</li>
<li>对比算法:  Bi-GAE(Bipartite Graph Auto-Encoder) VS Metapath2vec</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c3b5b042e933f20e1993.png"/></p>
<p></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/03baf9c6fbe479a07bc5.png"/></p>
<p>从上图可以看出，Bi-GAE的效果是稍差于metapath2vec的，我们分析推测其主要原因是当前的Bi-GAE是基于user-item的二分图进行特征表达，算法无法利用边上的权重（用户对不同公众号有不同的偏好）；而metapath2vec在游走的时候，根据边的权重进行了采样。因此，我们也是建议使用更为进阶的GNN模型进行学习，比如说可以使用到边特征的GAT模型等。</p>
<h2>五、总结与展望</h2>
<p>        本文分别在抽样的同构好友网络和异构网络中对比了不加入节点特征信息的GAE/VGAE算法和node2vec、metapath2vec算法。实验表明在该抽样网络中，GAE/VGAE算法在学习图的拓扑结构信息方面对比node2vec、metapath2vec算法没有优势，可能是要加入节点自身特征信息才能发挥出GNN算法的优势。当然，针对不同性质的网络或者不同的任务也可能会得出不同的实验结果。后续文章将会继续分享加入预训练的user embedding的GNN模型的实践。</p>
<p>        数据中心研发的<strong>柏拉图平台</strong>提供包括node2vec、metapath2vec等传统network embedding算法组件以及GNN相关的算法组件，供业务团队根据不同需求来生成所需的embedding：</p>
<ul><li><strong>的相关数据</strong><strong>embedding</strong><strong>结果</strong>，会在<strong>笛卡尔特征库</strong>中供大家使用。</li>
<li><strong>柏拉图平台提供</strong><strong>embedding</strong><strong>相关算法组件</strong>，供业务团队生成需要的Embedding。</li>
</ul><p>如有需求，欢迎合作！</p>
<p>参考文献：</p>
<p>[1]Transformer: <a href="https://papers.nips.cc/paper/7181-attention-is-all-you-need.pdf">https://papers.nips.cc/paper/7181-attention-is-all-you-need.pdf</a></p>
<p>[2]Bert: <a href="https://arxiv.org/pdf/1810.04805.pdf%E3%80%91">https://arxiv.org/pdf/1810.04805.pdf%E3%80%91</a></p>
<p>[3]Node2vec: <a href="https://www-cs.stanford.edu/~jure/pubs/node2vec-kdd16.pdf">https://www-cs.stanford.edu/~jure/pubs/node2vec-kdd16.pdf</a></p>
<p>[4]Metapath2vec: <a href="http://library.usc.edu.ph/ACM/KKD%202017/pdfs/p135.pdf">http://library.usc.edu.ph/ACM/KKD%202017/pdfs/p135.pdf</a></p>
<p>[5]Structure2vec: <a href="https://arxiv.org/pdf/1603.05629.pdf">https://arxiv.org/pdf/1603.05629.pdf</a></p>
<p>[6]GAE&amp;VGAE <a href="https://arxiv.org/pdf/1611.07308.pdf">https://arxiv.org/pdf/1611.07308.pdf</a></p>
<p>[7] User embedding技术应用综述: [内部或本地链接已移除]</p>
<p>[8] 用户行为序列建模Bert4UserEmbedding: [内部或本地链接已移除]</p>
<p>[9] Bert大规模预训练算法:  [内部或本地链接已移除]</p>
<p>[10] SocialTrans：BERT与GNN的结合:  [内部或本地链接已移除]</p>
<p>[11] 柏拉图network embedding算法参考:  [内部或本地链接已移除]</p> 
{% endraw %}
