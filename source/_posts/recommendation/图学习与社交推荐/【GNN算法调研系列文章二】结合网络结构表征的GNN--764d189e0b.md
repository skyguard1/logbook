---
title: "【GNN算法调研系列文章二】结合网络结构表征的GNN"
date: 2022-06-14 20:48:12
categories:
  - 推荐算法
  - 图学习与社交推荐
---

{% raw %}

<h2>背景</h2>
<p>为什么网络结构对于GNN来说十分重要？我们可以参考图一的例子[1]。中间的节点是我们想要推测其分类的目标节点。假设GNN只有一层卷积，也就是从目标节点的邻居出发，我们可能会因为目标节点周围蓝色的节点较多（4个），就将其归类为蓝色（如图一左侧）。但是如果我们考虑周围节点之间的网络结构，我们会发现绿色的节点之间是相互连接的，并且他们与目标节点构成了三角形的关系，目标节点与他们的关系更加紧密，故而应该具有更大的权重，那么我们就可能会将目标节点归为绿色（图一右侧）。这个例子简单的展示了考虑和不考虑网络结构时，GNN在卷积过程中对邻居节点的侧重可能是不同的。<br/><img alt="" loading="lazy" src="/logbook/images/recommendation/1ffcd2b833ea2e06bc2e.png"/></p>
<p>图一：学术网络示例</p>
<p>在拓扑学中， Weisfeiler-Leman（WL）测试[2]可以帮助我们回答两个网络结构之间是否可以构成同构（Isomorphism）的关系：同构的两个图，一定可以通过WL测试，但是，不同构的两个图也可能可以通过WL测试。在图二的示例[3]中，人类肉眼认为非常不同的两个结构，WL测试却无法检测出他们的非同构关系。另一方面，学者们证明，传统GNN对于图结构的表征能力不超过WL测试的能力。那么显然，我们想要提高GNN的表征能力的一个重要方向就是增强其对于网络结构的表达。<br/><img alt="" loading="lazy" src="/logbook/images/recommendation/83e84102af8f199f5288.png"/></p>
<p>图二：WL测试无法分辨的非同构图</p>
<h2>调研算法</h2>
<p>笔者调研了最近2年所发表的关于增强GNN对网络结构表达的论文，研究的问题包括节点分类（Node Classification），边预测（Link Prediction）和图分类（Graph Classification）等GNN模型常常被应用到的领域。虽然我们在业务中遇到的更多是节点分类和边预测等任务，但由于GNN结构的通用性，所有的技术都具备参考的意义。我们对调研到的9篇论文一起汇总介绍，希望有可以借鉴的算法设计方案。</p>
<h3>算法总览与分类</h3>
<p>我们按照各算法对网络结构信息的应用方式分为3个类别，分别是</p>
<ul><li>Structure Convolution：根据网络结构设计新的卷积方式</li>
<li>Structure Encoding：将网络结构信息整合到连续向量中，作为特征加入模型</li>
<li>Position Encoding：将位置信息整合到连续向量中，作为特征加入模型</li>
</ul><p>按照按以上分类对调研的算法进行归纳，并逐一介绍每一个分类中的算法。</p>
<table><tbody><tr><td>Structure Convolution<br/></td>
<td>
<p>Graph Convolutional Networks with Motif-based Attention [1]<br/></p>
<p>Nested Graph Neural Networks [4]</p>
</td>
</tr><tr><td>Structure Encoding<br/></td>
<td>
<p><a href="https://www.kdd.org/kdd2020/accepted-papers/view/graph-structural-topic-neural-network">Graph Structural-topic Neural Network</a> [5]<br/></p>
<p>Improving Graph Neural Network Expressivity via Subgraph Isomorphism Counting[7]<br/></p>
</td>
</tr><tr><td>Position Encoding<br/></td>
<td>
<p>WGCN: Graph Convolutional Networks with Weighted Structural Features [8]<br/></p>
<p>Neo-GNNs: Neighborhood Overlap-aware Graph Neural Networks for Link Prediction [9]<br/></p>
<p>Distance Encoding: Design Provably More Powerful Neural Networks for Graph Representation Learning [10]<br/></p>
<p>Graph Neural Networks with Learnable Structural and Positional Representations [11]</p>
</td>
</tr></tbody></table><h3>基于结构卷积（Structure Convolution）的网络表达</h3>
<p>传统的基于消息传递（Message Passing）的GNN实际上是在以目标节点作为根节点的宽度优先搜索树上进行的，树的高度等于卷积的层数，我们将叶子节点的信息逐层向根节点传递。基于结构卷积的网络表达是希望在卷积操作时引入更多的结构信息，使得卷积的机制区别于上述树状消息传递机制。</p>
<p><strong>Graph Convolutional Networks with Motif-based Attention [1]</strong><br/></p>
<p><em><strong>[1]</strong> </em>采用的方式是用网络中的motif重新定义节点之间的相邻关系，然后在新形成的图中进行卷积。假设此时我们只考虑一种motif，比如三角形。那么区别于传统的邻接矩阵A，Aij=1表示节点i和j之间连边，基于三角形的邻接矩阵中A'中，A'ij=1表示i和j同时出现在至少一个三角形中。A'也可以是加权的，即A'ij表示节点i和j同时出现在多少个不同的三角形中。当我们考虑T种不同的 motif 的时候，那么就可以形成T个不同的邻接矩阵。与此同时，如果我们考虑通过i和j之间通过1到K个相邻的 motif 而连接，那么对于每个 motif，[1]中都定义出K个不同的矩阵，分别表示i和j之间通过1到K个 motif 到达的路径的个数。</p>
<p>基于上述描述，我们可以获得 K*T 个矩阵，要根据每一个矩阵都进行卷积的话，计算量是非常庞大的。[1]中采用了一个基于强化学习的决策机制，在每一个卷积层，为每一个节点选择其适宜选择的卷积邻居，如图三所示。图三的上半部分是我们熟悉的图卷积操作，下面是预先构建的基于 motif 定义的 K*T 个邻接矩阵。在第一层卷积时，V1决定要使用三角形定义的邻接矩阵中的一步邻居来聚合特征，所以选择了左上蓝色箭头所指的 transition vector；而在第二层卷积时，V1决定要使用四弦结构定义的一步邻居来聚合特征，于是选择了右上蓝色箭头所指的 transition vector。文中的模型将会被两个loss指导训练，一个是任务相关的loss，一个是用来训练强化学习选择器的loss。本文对于强化学习部分的 State 定义和 Reinforcement 规则不做详尽介绍。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/37d56d575688b14f1a78.png"/></p>
<p>图三：[1]中的算法示例</p>
<p><strong>Nested Graph Neural Networks [4]</strong></p>
<p><em><strong>[4]</strong></em>考虑的是在传统基于信息传递的GNN模型中，目标节点是按树状结构聚合特征的，但是这样的缺点是对于邻居的连接性是没有感知的。如图四所示，G1和G2的图结构完全不同（图四左侧），但是我们再对V1和V2进行卷积的时候，他们的树结构是一模一样的（图四右侧）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/4702e9693256716e6a07.png"/></p>
<p>图四：不同图在卷积时结构相同</p>
<p>[4]中考虑的方案则是在进行卷积时，不再采用宽度优先搜索的方式去延伸卷积的节点，而是考虑保留相邻节点之间的子图结构进行卷积，其运行方式如图五所示。在做图采样时，每一个节点除了采样出邻居节点，还会保留邻居之间的边，故而采样出的6个子图不是树状结构。在每一个子图中进行标准的GNN模型的卷积操作，每一个节点都会获得参数的更新，然后通过子图 pooling将子图中所有节点的的 embedding 聚合到目标节点上。[4]解决的是图分类问题，所以在获得每个节点的 embedding 之后还需要执行一步 graph pooling，在我们节点分类的场景中，直接使用节点的 embedding 即可。子图pooling的手段主要是mean-pooling，在子图卷积的过程中，也可以根据节点与目标节点的距离设置权重，使得子图的GNN是对目标节点有感知的。<br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/a5b2954daf7e6e616fc6.png"/></p>
<p>图五：[4]中的算法示例</p>
<p>[1]和[4]都是让图结构的信息直接改变了传统GNN进行卷积操作的方式，故而我们认为这类方法通过结构卷积的方式增加了GNN的网络表达。</p>
<h3>基于结构编码（Structure Encoding）的网络表达</h3>
<p>还有一部分论文的方案并不直接设计一个基于网络结构执行卷积操作的机制，而且将网络的结构信息encode到一个向量中，将该向量注入传统的GNN的算法框架内，然后通过设计某种针对结构信息的loss来加强对结构特征的应用。</p>
<p><strong><a href="https://www.kdd.org/kdd2020/accepted-papers/view/graph-structural-topic-neural-network">Graph Structural-topic Neural Network</a> [5]</strong><br/></p>
<p>与[1]类似，<em><strong>[5]</strong></em>也是考虑目标节点周围具备某些特定结构的motif，但是[5]认为直接将 motif 转换为邻接矩阵对计算性能影响很大，并且需要提前定义 motif 也需要人类专家对目标网络有一定程度的了解。为了解决上面的困难，[5]提出采用LDA的方式去对节点的结构topic建模。这个建模过程主要分为3步：</p>
<p>1. 先采用匿名随机游走的形式，为每个节点构建语料，使得每个节点对应一个游走结构的集合（节点类似于一个文档，每一个游走结构类似于一个单词）；匿名随机游走的含义是说，游走出的（v1，v2，v3，v1）和（v4，v5，v6，v4）是等价的结构，不会因为节点ID的不同而导致结构被区别对待。</p>
<p>2. 构建游走结果和游走结果的矩阵，矩阵中的值是对应位置的两个游走结构出现在同一个节点的次数；利用特征值分解的方式发现最重要的游走。</p>
<p>3. 去掉不重要的游走结构（类似于去掉stop words），基于全图每个节点构成的文档，应用LDA产生出每一个节点的 topic embedding，即为该节点的 structural-topic embedding。</p>
<p>卷积过程中，[5]将基于特征的卷积和基于结构embedding的卷积分别进行，然后在最后将两者的结果embedding concat在一起，再过一层MLP形成该节点的最终 embedding。假设总共有L层卷积，<img alt="" loading="lazy" src="/logbook/images/recommendation/97737d52ea6846cbe8b0.png"/>表示节点i在第L层的特征卷积，<img alt="" loading="lazy" src="/logbook/images/recommendation/86ea3c9dcc0d3cd4b412.png"/>表示节点i在第L层的结构卷积，那么最终产生的节点 embedding 则表示为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/686549670c264df078e4.png"/></p>
<p>最终的 loss 与GraphSAGE的设计一致，即随机从相邻节点抽取临边作为正样本，然后从非相邻节点中抽取负样本，如下所示。其中<img alt="" loading="lazy" src="/logbook/images/recommendation/d50f334d590de3353011.png"/>是针对节点v的 noise sampling，用于抽样负样本。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/87ed35a3717ddcb501f2.png"/></p>
<p><strong>Improving Graph Neural Network Expressivity via Subgraph Isomorphism Counting[7]</strong></p>
<p><em><strong>[7]</strong> </em>要做的事情也是将节点所处的周围的结构作为特征输入给模型。[7]中首先定义了一批重要的结构（如三角形）和位置（如3链的中间节点或者是边缘节点），假设总共D个，然后对每一个节点和边去计算他们被结构包含或者处在对应位置的数量，构成一个D维的向量，作为每一个节点和边的结构特征，如图五所示。左边的图中展示的是蓝色节点的结构特征向量。由于该节点在3个3链中位于边缘，在4个3链中位于中间，并且出现在1个三角形中，所以他的结构特征向量为[3,4,1]。相似的，右边的图中展示蓝色边的结构特征向量。由于该边在2个3链中出现和1个三角形中出现，所以他的结构特征向量为[2,1]。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/0b9d3719df7bc87d8d77.png"/></p>
<p>图五：[7]的结构特征构造示例</p>
<p>在有了节点和边的结构特征向量以后，[7]中将对应的向量拼接起来作为节点和边的特征，输入模型进行卷积，如下式所示。其中的UP函数可以是任意一个变换函数，例如MLP；M是邻居聚合的函数，例如sum pooling。这里h代表的是节点的特征，e代表边特征，而x则是前面的规则所产生的结构特征。在通过节点进行卷积时（GSN-v），目标节点V和邻居节点U的结构特征都作为输入特征；在通过边进行卷积时（GSN-e），对应边的结构特征作为输入特征。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/46819dd55527452feed1.png"/></p>
<p>值得注意的是，结构特征在每一个卷积层都以原始值输入模型，没有进行训练，后面我们介绍到的[11]则对结构的encoding也进行了训练和更新。</p>
<h3>基于位置编码（Position Encoding）的网络表达</h3>
<p>接下来我们要学习到的是通过对位置信息的编码来增加GNN的网络表达的算法。区分基于结构编码和位置编码的一个重要因素在于，基于结构编码的模型更加注重特定的 motif，如三角形，四边形，全连接子图等等，而对于是哪些节点构成了这些 motif，模型并不在意。而基于位置编码的模型更加强调目标节点与另一特定节点之间的位置关系，如最短距离或者基于随机游走的transition probability，但是对于他们之间的路径经过了什么形状的网络并不关心。</p>
<p><strong>WGCN: Graph Convolutional Networks with Weighted Structural Features [8]</strong></p>
<p><strong>[8]</strong>考虑在有向网络中，如果入度比出度小，那么入边所连接的邻居更能表征目标节点的属性，反之亦然。基于这样的假设，文章定义了一种区分入度和出度的大小的随机游走，其游走概率定义如下，其中dI代表入度，dO代表出度。在入度比出度小过某个阈值时（右侧第一行），设置入度的的权重（wI）比出度（wO）要大，反之亦然。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/ff7fe2820ad2820ced32.png"/></p>
<p>通过这样的随机游走，可以得到图六所示的随机游走矩阵。如果不区分入度和出度，那么从中间节点o到所有其他节点的概率是一样的，然而考虑出入度的差异后，由于o的入节点只有4个，所以他们获得的概率要比其他节点更高，如最右侧的矩阵所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/41507fb2474acc7971cf.png"/></p>
<p>图六：基于同一网络的随机游走结果</p>
<p>根据该规则所获得的随机游走的 transition vector 即为每个节点的位置编码，将位置编码 normalise 后与节点的原始特征拼接输入GNN模型，即可获得带有位置信息的图卷积模型。文章同时还提到应用一种 Isomap 的编码方式将多个节点聚合在一起，然后将聚合以后的超级节点作为目标节点的邻居进行卷积，可以进一步的扩大结构信息。</p>
<p><strong>Neo-GNNs: Neighborhood Overlap-aware Graph Neural Networks for Link Prediction [9]</strong></p>
<p><strong>[9]</strong>通过分析发现，在很多的边预测任务中，基于GNN这样的复杂网络进行特征传播的方法，还没有启发式的基于共同邻居数量的方法的准确性高，所以[9]考虑通过邻接矩阵去计算出节点之间的具备相似结构的邻居数量。[9]计算位置 encoding 的方法分为3个步骤，如图七蓝色框中的下半部分所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/b3d5e88072c82e1d2ba9.png"/></p>
<p>图七：[9]的算法结构</p>
<p>1. 构建一个两层的MLP用来对邻接矩阵进行处理，使得每个节点获得一个结构属性值，<img alt="" loading="lazy" src="/logbook/images/recommendation/e9daada4840f2ee2bd7a.png"/>；然后将这个值填在一个N*N的矩阵的对角线上，构成一个对角矩阵，<img alt="" loading="lazy" src="/logbook/images/recommendation/d57a65b06acdaee395e2.png"/>，其中第i行i列的元素即为节点i的结构属性值。</p>
<p>2. 将<img alt="" loading="lazy" src="/logbook/images/recommendation/d57a65b06acdaee395e2.png"/>与一阶或者高阶的邻接矩阵相乘求和，就得到了任意两个节点之间的一阶或者高阶邻居的结构相似度。</p>
<p>3. 将结构相似度输入一个MLP函数即可得到每个节点i的位置embedding，用<img alt="" loading="lazy" src="/logbook/images/recommendation/b9b3170add7098b22054.png"/>表示。</p>
<p>在有了位置 embedding 之后，该 embedding 和传统GNN算法产生的 embedding（表示为<img alt="" loading="lazy" src="/logbook/images/recommendation/150465af21aaacc57d5c.png"/>）相结合，构造预测结果，即相似度由两部分组成，且由一个超参<img alt="" loading="lazy" src="/logbook/images/recommendation/7528b7a55abc575a2db7.png"/>来控制比重。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/4fabeec19f1d5e7095b1.png"/></p>
<p>在有了预测结果之后，loss 也是如下分为三个部分。第一部分是预测结果和真实 label 的差异，第二部分是结构 encoding 相似度与真实label的差异，第三部分是传统GNN结果与真实 label 的差异，用三个<img alt="" loading="lazy" src="/logbook/images/recommendation/8c81efac93b221e0845e.png"/>超参来控制比重。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/e49bf193d082d7e18c79.png"/></p>
<p>我们可以看出，[9]的算法中其实并没有将位置encoding输入GNN模型，而仅仅是在预测阶段才对二者进行结合，该方案更多的是对位置encoding方法的介绍，而与GNN的算法设计关系不大。</p>
<p><strong>Distance Encoding: Design Provably More Powerful Neural Networks for Graph Representation Learning [10]</strong></p>
<p><strong>[10]</strong>则考虑在卷积的时候加上两个节点之间的距离信息，该距离信息是通过随机游走的 transition probability 表示的。例如如果节点u只有一个好友v，那么u通过一步随机游走到v的概率就会很大；而如果u有很多邻居，那么u到v的概率就会很小。基于此，文章定义了两个节点u和v之间的距离向量如下</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/dfb9bd595951418b62ec.png"/></p>
<p>其中，W是随机游走的 transition matrix；f3是一个变换函数，可以基于规则也可以是一个MLP。总而言之，<img alt="" loading="lazy" src="/logbook/images/recommendation/8099f5163e8912a3c83a.png"/>构成了u和v之间的位置encoding。而u到一个集合的距离向量则是u到一个集合中的每一个点的距离向量聚合而得，该聚合函数可以是 mean pooling 等简单操作：<img alt="" loading="lazy" src="/logbook/images/recommendation/4c263ab82fe627d5fb11.png"/>。当|S|=1时，我们聚合的目标是一个节点；当|S|=2时，我们聚合的目标是一条边；当|S|&gt;2时，我们聚合的目标是一个子图结构。基于不同的任务，S可以设置为不同的节点集合。</p>
<p>[10]考虑将位置encoding用在2个方面，第一个是直接作为特征，即初始特征给定为</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/399af65f7d22ffd1c62d.png"/><img alt="" loading="lazy" src="/logbook/images/recommendation/4c8126d5b020d1b673b5.png"/>，即v的原始特征与位置encoding的concat。</p>
<p>第二个是将位置encoding作为卷积的controller，即将原始卷积操作的聚合函数变换为考虑位置信息的聚合函数，如下所示</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/5dd44eb231a9b31d13a1.png"/></p>
<p>值得注意的是，[10]中是将位置encoding与卷积紧密结合的。这里的S才是目标节点或者节点集合，而u是被卷积的邻居。在[10]中，每一个邻居在被卷积时，需要根据其与目标S的距离encoding去决定传递多少/哪些特征。</p>
<p><strong>Graph Neural Networks with Learnable Structural and Positional Representations [11]</strong><br/></p>
<p><strong>[11]</strong>对于原始位置encoding的设计与[10]是接近的，即通过随机游走一步、两步，一直到k步，节点 i 从自己出发到回到自己的概率构成一个k维的位置encoding，该encoding经过一个MLP变换后就可以构成输入GNN模型的节点encoding。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/e35152de59de50c2d8aa.png"/></p>
<p>传统的基于信息传递的GNN的更新如下式，其中h是节点的特征，e是边的特征，f是非线性的转换函数。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/4e2bec750fd9f7151d46.png"/></p>
<p>如果我们直接把位置encoding当做特征加入传统的GNN，那么其更新如下式，我们发现迭代更新部分与传统GNN一模一样，唯一的差别是在第0层时，加上了<img alt="" loading="lazy" src="/logbook/images/recommendation/d10a5bc03c11de9fc943.png"/>作为输入特征。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/838df045cab72ea8c5c3.png"/></p>
<p>而[10]考虑将位置 encoding 加入迭代中，故而提出了以下的卷积方式，可以看出位置encoding（表示为<img alt="" loading="lazy" src="/logbook/images/recommendation/4b90faf2a25fb1a35376.png"/>）有自己的卷积函数，并且每一层的位置encoding都会与特征encoding拼接后去形成下一层的特征encoding。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/d66e70e0583626d12898.png"/></p>
<p>按理来说，通过对最终的特征encoding进行监督，也可以对位置encoding进行训练和更新，但是[10]更进一步的提出了基于图拓扑结构的loss，根据原图的拉普拉斯矩阵的特征向量计算得来，即</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/dfa91032204eb2c92466.png"/></p>
<h2>总结与展望</h2>
<p>至此，我们介绍了9篇利用图结构或者位置信息对GNN模型进行强化，以提升GNN的表征能力的文章。我们看到文章[1]和[4]直接根据网络结构重新定义卷积方式或者邻接矩阵的论文，而其余七篇文章都是通过encoding的方式来注入结构信息。在对结构信息进行encoding的时候，我们看到[5,8,10,11]四篇文章都借鉴了随机游走的 transition probability。</p>
<p>在业务场景中，我们的GNN网络往往是带有ID特征的，每个节点的ID都会进行encoding并作为特征进行传播。这样的操作一定程度上也相当于将位置信息带入了模型，例如[9]考虑的共同邻居的信息，在包含ID信息的 message passing 过程中就已经携带一部分邻居的身份信息，而不仅仅是邻居的特征。所以我们可能更希望借鉴结构encoding方案引入 motif 信息的算法。然而，结构encoding方案都局限在将encoding作为特征，而不参与卷积训练和参数更新，使得其与实际任务之间有一定的割裂。在调研文章中，只有基于位置encoding的文章[11]才提出对位置encoding同步进行卷积和有监督的训练。所以，最终采用什么样的方案还需要结合具体的业务分析，将调研算法融合贯通可能才会取得实际的效果。</p>
<p>笔者所在团队长期在GNN的研究和落地方面探索尝试，欢迎感兴趣的同学关注团队的技术沉淀《GNN技术研究与应用》。</p>
<h2>参考资料</h2>
<p>[1] J. B. Lee et al. Graph Convolutional Networks with Motif-based Attention. CIKM 2019.</p>
<p>[2] <a href="https://davidbieber.com/post/2019-05-10-weisfeiler-lehman-isomorphism-test/">https://davidbieber.com/post/2019-05-10-weisfeiler-lehman-isomorphism-test/</a></p>
<p>[3] B. Bevilacqua et al. Equivariant Subgraph Aggregation Networks. ICLR 2022.</p>
<p>[4] M. Zhang and P. Li. Nested Graph Neural Networks. NeuralIPS 2021.</p>
<p>[5] Q. Long et al.<a href="https://www.kdd.org/kdd2020/accepted-papers/view/graph-structural-topic-neural-network">Graph Structural-topic Neural Network. KDD 2020.</a><br/></p>
<p>[6] M. Horn et al. Topological Graph Neural Networks. ICLR 2022.<br/></p>
<p>[7] G. Bouritsas et al. Improving Graph Neural Network Expressivity via Subgraph Isomorphism Counting. ICLR 2021.</p>
<p>[8] Y. Zhao et al. WGCN: Graph Convolutional Networks with Weighted Structural Features. SIGIR 2021.</p>
<p>[9] S. Yun et al. Neo-GNNs: Neighborhood Overlap-aware Graph Neural Networks for Link Prediction. NeurIPS 2021.</p>
<p>[10] P. Li et al. Distance Encoding: Design Provably More Powerful Neural Networks for Graph Representation Learning. NeurIPS 2021.</p>
<p>[11] V. P. Dwivedi et al. Graph Neural Networks with Learnable Structural and Positional Representations. ICLR 2022.</p>
<p><br/></p>
<div>
<div>
<div>
<p><br/></p>
</div>
</div>
</div> 
{% endraw %}
