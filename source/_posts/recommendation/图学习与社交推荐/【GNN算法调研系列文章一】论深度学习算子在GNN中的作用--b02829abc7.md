---
title: "【GNN算法调研系列文章一】论深度学习算子在GNN中的作用"
date: 2022-06-14 20:47:20
categories:
  - 推荐算法
  - 图学习与社交推荐
---

{% raw %}

<h2>一、背景</h2>
<p>近年来，图神经网络GNN进入快速发展期，针对不同应用或者不同优化目的，GNN算法百花齐放，在学术界开辟出一片欣欣向荣之景。然而，GNN算法数量之多，则眼花缭乱，诸多算法研究员时常在如何将GNN算法落地到相关业务中产生迷茫，在对GNN算法进行局部优化的时候也毫无章法。然而，试图解决这些问题，也只能从GNN算法解剖中窥探一二。因此，基于近期各大顶会上GNN算法的调研，本文将探讨各种DNN深度学习算子在GNN中发挥的作用，希望能对GNN算法人员有所启发。</p>
<h2>二、GNN算法解剖</h2>
<p>GNN算法层出不穷，也有不同分类方式。在此文章中，笔者以信息传播方式(propagation step)来进行分类。传播方式可以划分为5个大方向: 卷积聚合 (Convolutional Aggregator)、注意力机制聚合 (Attention Aggregator)、门控更新(Gate Updater)、Skip Connection 、多层图传播(Hierarchical Graph)。在每一种传播方式，笔者标注了比较典型的GNN算法。值得一提的是，针对卷积聚合方式，还可以再细分为谱域传播(spectral)和空域传播(spatial), 两者的代表做分别是大家所熟识的GCN [2] 和 GraphSAGE [7]。 由于本文的主要目的是分析深度学习算子或者结构在GNN中的作用，详细的GNN算法就不在此赘述。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/10f80cb3887ea5314aaf.png"/></p>
<p>注：该分类方式参考了[1]</p>
<p>现有的诸多GNN算法可以被看作是 GCN [2], GraphSAGE [7] 和 GAT [4]的变种。在此，我们简单总结一下这三个典型GNN算法的基本操作。</p>
<ul><li><strong>GCN</strong> [2] : 通过<strong>图拉普拉斯矩阵</strong>来迭代式地聚合一个节点的所有邻居，引入了self-loop的概念，解决了自传递的问题。具体来说， 对图上任意节点 <em>v</em>, GCN按照以下方式来聚合邻居信息以及更新节点 <em>v</em> 的表达:</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/recommendation/8bff35378ad9558bfbb6.png"/></p>
<p>其中，<img alt="" loading="lazy" src="/logbook/images/recommendation/1fef590312f0084c6457.png"/>是点 <em>v </em>的邻接矩阵，<img alt="" loading="lazy" src="/logbook/images/recommendation/a5d9620782d9c46393fc.png"/>是邻接矩阵的对角矩阵的第 <em>j </em>行, <img alt="" loading="lazy" src="/logbook/images/recommendation/5d15c4d8dc3ef05c9f3e.png"/>是节点 <em>v</em> 在第<em> (l+1)</em> 层的表征， <img alt="" loading="lazy" src="/logbook/images/recommendation/2fb3ed9a9c910fa71e93.png"/>是非线性激活函数，<img alt="" loading="lazy" src="/logbook/images/recommendation/a5769997113b29488ef2.png"/>是第<em> l</em> 层可学习的参数矩阵来做特征转换。</p>
<ul><li><strong>GraphSAGE</strong> [7] : 通过对图上每个点采样固定个数的邻居，再通过 mean/sum/max-pooling等聚合方式来聚合采样到的邻居信息，最后将节点在上一层的表征和 邻居聚合的表征进行concat操作来更新节点的表征:</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/recommendation/b2fafe1f526b50c07856.png"/></p>
<p>其中，[图片未保存到本地]是节点 <em>v</em> 的邻居集合。</p>
<ul><li><strong>GAT</strong> [4] : 该算法假设对于每个邻居对源点的影响是不一样的，也无法通过图结构来预先设定的。因此他利用注意力机制来对邻居的影响力做区分，最后根据每个邻居得到的attention score来聚合邻居信息。attention score大的邻居，那么它的信息就会更多地被聚合，反之亦然。</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/recommendation/e800305eb6e752e57987.png"/></p>
<p>其中，<img alt="" loading="lazy" src="/logbook/images/recommendation/66689f8c6481d7b13e6d.png"/>是一个注意力函数，典型的注意力函数是 <img alt="" loading="lazy" src="/logbook/images/recommendation/0cf8210a2b5fce3fbfbc.png"/>。</p>
<p>从上述三种典型的算法中，我们可以看到 GNN算法在模型结构上要解决的问题可以归结为：<strong> 如何通过深度学习的算子来更好地聚合节点邻居信息? </strong>因此，在后续调研中，我们会更多聚焦在深度算子的作用。</p>
<h2>三、深度学习算子的作用</h2>
<p>通过调研，笔者发现了三篇有意思的论文，分别聚焦在非线性激活或者特征转换、注意力机制以及图池化(graph pooling)。针对每个问题，提出了一个比较新颖的角度来深刻剖析这些随处可见的深度学习算子在GNN中发挥的作用。</p>
<h3>1、非线性特征转换是否有必要？</h3>
<p>在诸多GNN算法中，特征转换(feature transformation)和非线性激活(nonlinear activation)是必然存在的，这也是现代神经网络成功的关键之一。然而，这两个操作在GNN中，是否对任何数据集或者应用都起作用？2020年，中国科技大学何向南团队[8]首次针对这个问题作出回答，他们通过实验认为，在<strong>基于协同过滤的推荐场景下，如果图上节点user和item只有one-hot ID 且没有其他属性，那么特征转换或者非线性激活并不能带来收益</strong>。</p>
<p>具体地说，该团队针对NGCF [9]算法做了实验解剖。NGCF算法是基于GNN的新型协同过滤，在推荐数据集上取得不错的效果，比以往基于矩阵分解(Matrix Factorization)的协同过滤算法效果更佳。NGCF的基本思想是，在user-item构成的二部图，每个节点的表征可以通过多跳邻居聚合，从而聚合到 相似用户购买的商品序列以及购买相似商品的用户序列。</p>
<p>[图片未保存到本地]</p>
<p>其中，用户表征与商品表征的更新计算如下：</p>
<p>[图片未保存到本地]</p>
<p>在这里，[图片未保存到本地]和[图片未保存到本地]分别是通过 <em>k</em> 层传播后的用户 <em>u</em> 和商品 <em>i</em> 的标准，[图片未保存到本地]是非线性激活函数，[图片未保存到本地]  是用户 <em>u</em> 交互过的商品集合，<img alt="" loading="lazy" src="/logbook/images/recommendation/585e8ae9204716bb40e6.png"/>是和商品 i 交互过的用户集合，[图片未保存到本地]和[图片未保存到本地]是用来做特征转换的可学习参数矩阵。</p>
<p>针对这个模型，他们分别去除了NGCF当中的特征转换和非线性激活，并在两个学术界广泛使用的推荐数据集Gowalla 和 -Book上做实验。注意，这些数据上，每个节点只有one-hot ID且没有其他属性。实验效果如下：</p>
<p>[图片未保存到本地]</p>
<p>其中，NGCF-n是去除了非线性激活函数的模型，NGCF-f是去除了两个特征转换的可学习参数矩阵的模型，NGCF-fn是同时去除了非线性激活函数和特征转换的模型。从实验结果中，可以看到，当去除了非线性激活函数和特征转换之后，模型在top20的召回率表现更加，比NGCF约有 9.57%的相对效果提升。并且，该团队认为，之所以增加特征转换和非线性激活函数会有较差的效果表现，是因为这两者增加了训练的难度，特别是当节点没有其他具有语义的属性来区分。</p>
<p>针对这个发现，他们提出了LightGCN [8]算法，该算法只采用了简单的带权sum aggregator，摒弃了特征转换和非线性激活函数的使用。在实验中发现，<strong>LightGN可以比NGCF更快地降低训练loss，取得更低的loss，从而提升最终的推荐效果</strong>。<br/></p>
<p>[图片未保存到本地]</p>
<p>[图片未保存到本地]</p>
<p><br/></p>
<h3>2、注意力机制有多大作用？</h3>
<p>GAT算法 [4] 提出的注意力机制已经被广泛应用到多种GNN算法中。在GAT中，通过注意力机制，每个节点更倾向于与自己表征更相似的邻居节点。但，近期有研究认为，GAT只是计算了一种非常局限的注意力机制。该研究 [10] 由以色列理工学院和CMU联合发表在ICLR2022。在研究中，他们发现，<strong>GAT中的注意力机制计算出来的attention score 对图上所有源点(query node) 都是一样的，对不同源点(query node) 产生的attention score都是差不多的</strong>。为了验证这一点，他们在一个完全二部图上做了实验。注意，在完全二部图上，每个节点都有相同的邻居节点。首先，针对图上10个节点，每个节点依次作为源点{q0, ..., q9}，GAT会计算每个源点和图上所有其他节点之间{k0, ..., k9}的attention score，效果如下图所示。</p>
<p>[图片未保存到本地]</p>
<p>通过左边的图，我们可以从具体的attention score数值上看到，对于第一列数据，同一个邻居节点，所有源点的attention score都是相差无几的。将左边的矩阵数值，可视化为右边的二维图，以每个节点{k0, ...k0}为横轴，画出每个源点相对于一个节点的attention score。从可视化的内容，我们可以看到，对于同一个邻居节点，所有源点的数值分布都是类似的曲线或者相同的数值，<strong>GAT的注意力机制无法为不同的源点计算出不同的数值</strong>。</p>
<p>不仅如此，该团队从理论上证明了GAT的注意力机制确实只有有限的表达能力。为了解决这个问题，该团队调整了注意力机制的算子顺序，并且证明新版注意力机制是可以将不同源点之间的attention score加以区分。</p>
<p>[图片未保存到本地]</p>
<p>在节点分类的任务上，新版注意力机制在所有数据集上均表现出了更好的效果。</p>
<p>[图片未保存到本地]</p>
<h3>3、图池化是否重要？</h3>
<p>在传统卷积神经网络中有局部池化(local pooling)的操作，部分研究将池化操作也迁移到GNN中，并且将图池化(graph pooling)问题转化成了图簇(graph clustering)问题。为了系统研究图池化在 GNN中发挥的作用，Aalto大学有团队对诸多池化方式进行了实验剖析，从而查看有无图池化是否对GNN效果有影响 [11]。</p>
<ul><li><strong>离线图池化GRACLUS [12]</strong>: 作者在这个实验中，规定了如下所示的卷积层和图池化层：</li>
</ul><p>卷积层： [图片未保存到本地]</p>
<p>其中，A是邻接矩阵，X是属性举证，通过传统卷积的方式获得每个节点卷积后的embedding。接着，通过GRACLUS算法计算图上每个节点所属的图簇(clutser), 使用max-pooling的方式将同个簇里的节点特征进行池化，从而进一步池化图的邻接矩阵.</p>
<p>图池化层：, [图片未保存到本地]</p>
<p>[图片未保存到本地]</p>
<p>[图片未保存到本地]</p>
<p>为了验证这样的图池化是否有作用，作者做了一个反例：将所有不相似的节点放在一个图簇里，其他的操作保持一致。作者将这个反例称作COMPLEMENT。通过在4个数据集上做实验，可以发现，<strong>GRACLUS和COMPLEMENT两个方法的效果是相似的，相似点进行图池化并没有带来效果上的提升</strong>。</p>
<p>[图片未保存到本地]</p>
<ul><li><strong>DIFFPOOL [14]</strong>: 这个方法是用GNN 来学习图簇分配问题，从而将学到的图簇用来做图池化：</li>
</ul><p>[图片未保存到本地]</p>
<p>接着，它利用学到的图簇分配矩阵[图片未保存到本地]和第二个GNN模型来计算节点表征:</p>
<p>[图片未保存到本地]</p>
<p>在实验中，为了控制DIFFPOOL当中图簇分配对结果的影响力，他们将使用几个随机图簇分配函数来替换GNN学到的图簇分配矩阵:</p>
<p>[图片未保存到本地]</p>
<p>从实验效果上来看，在所有数据集上，至少有一个随机图簇分配模型的accurcy比DIFFPOOL高。并且随机的图池化并不会带来更大的方差。这些实验结果都表明，<strong>通过学习得到的图池化方法不会提升DIFFPOOL的性能</strong>。</p>
<p>[图片未保存到本地]</p>
<p>[图片未保存到本地]</p>
<p> </p>
<ul><li><strong>图记忆网络GMN [15]</strong>: GMN算法是在GNN模型上包含了一系列的记忆层(memory layer)，模型结构如下：</li>
</ul><p>[图片未保存到本地]<br/></p>
<p>为了做图池化，在记忆层会计算相应的分配</p>
<p>[图片未保存到本地]</p>
<p>最后，根据分配计算节点的表征</p>
<p>[图片未保存到本地]</p>
<p>注意，这里的[图片未保存到本地]就是此文章前面所讲的节点表征矩阵。</p>
<p>在实验中，为了反应这个池化操作是否起作用，作者也提出了两个变体。一个是将记忆层的分配方式换成了欧式距离，使得每个query节点和key节点距离最远，该方法称作DISTANCE；另一个是均匀采样得到分配好的矩阵<strong>S</strong>， 该方法称作RANDOM。</p>
<p>[图片未保存到本地]</p>
<p>从实验结果中，我们可以看到通过<strong>不相似的点来做池化并不会给最后的性能带来负面影响</strong>。</p>
<h3>结论分析：</h3>
<ul><li>大部分GNN模型结构应用了卷积层，使得节点表征快速平滑。因此，图池化层并不会因为特定的图簇分配算法而产生不同的影响，相反，选择相似节点作为一簇，还是选择不相似节点作为一簇，或者是随机选择，对模型效果不会带来较大影响。</li>
</ul><h2>四、总结</h2>
<p>在GNN算法中，传统深度学习的算子或者网络构造方式在GNN发挥的作用并不一定和传统深度学习算法保持一致。一个有效的深度学习算子（或者操作）是需要针对数据集或者应用进行量身定做。本文章有以下三点发现：(1)当节点并不存在属性的时候，非线性特征转换的操作有可能对结果带来负面影响。(2) GAT当中的注意力机制无法深刻反映节点之间的attention score, 如何将不同节点对不同源点的相关性进行最大化区别，是未来可行的方向。(3) 图池化操作对GNN的效果影响甚微，如何更好地应用池化概念和操作也是一个有意思且有发展前景的方向。在未来GNN研究发展路上，希望我们能在业务中加深对GNN结构的理解，从而获得对自身业务更加有效的GNN算法。</p>
<h2>五、参考文献</h2>
<ol><li><a href="https://zhuanlan.zhihu.com/p/89503068">https://zhuanlan.zhihu.com/p/89503068</a></li>
<li>Thomas N Kipf and Max Welling. 2017. Semi-supervised classification with graph convolutional networks. In International Conference on Learning Representations. 2873–2879.</li>
<li>William L. Hamilton, Rex Ying, and Jure Leskovec. 2017. Inductive Representation Learning on Large Graphs. In Advances in Neural Information Processing Systems. 1025–1035.<br/></li>
<li>Petar Veličković, Guillem Cucurull, Arantxa Casanova, Adriana Romero, Pietro Lio, and Yoshua Bengio. 2017. Graph attention networks. arXiv preprint arXiv:1710.10903 (2017).<br/></li>
<li>Li, Yujia, et al. "Gated graph sequence neural networks." <i>arXiv preprint arXiv:1511.05493</i> (2015).<br/></li>
<li>Xu, Keyulu, et al. "Representation learning on graphs with jumping knowledge networks." <i>International Conference on Machine Learning</i>. PMLR, 2018.<br/></li>
<li>Hamilton, Will, Zhitao Ying, and Jure Leskovec. "Inductive representation learning on large graphs." <i>Advances in neural information processing systems</i> 30 (2017).<br/></li>
<li>He, Xiangnan, et al. "Lightgcn: Simplifying and powering graph convolution network for recommendation." <i>Proceedings of the 43rd International ACM SIGIR conference on research and development in Information Retrieval</i>. 2020.</li>
<li>Xiang Wang, Xiangnan He, Meng Wang, Fuli Feng, and Tat-Seng Chua. 2019. Neural Graph Collaborative Filtering. In SIGIR. 165–174.<br/></li>
<li>Brody, Shaked, Uri Alon, and Eran Yahav. "How attentive are graph attention networks?." <i>ICLR</i> (2022).<br/></li>
<li>Mesquita, Diego, Amauri Souza, and Samuel Kaski. "Rethinking pooling in graph neural networks." <i>Advances in Neural Information Processing Systems</i> 33 (2020): 2220-2231.<br/></li>
<li>Dhillon, Inderjit S., Yuqiang Guan, and Brian Kulis. "Weighted graph cuts without eigenvectors a multilevel approach." <i>IEEE transactions on pattern analysis and machine intelligence</i> 29.11 (2007): 1944-1957.<br/></li>
<li>Ying, Zhitao, et al. "Hierarchical graph representation learning with differentiable pooling." <i>Advances in neural information processing systems</i> 31 (2018).</li>
<li>Hosein Khasahmadi, Amir, et al. "Memory-Based Graph Networks." <i>ICLR (2020)</i>.<br/></li>
</ol> 
{% endraw %}
