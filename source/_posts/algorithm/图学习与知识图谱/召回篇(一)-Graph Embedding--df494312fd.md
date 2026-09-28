---
title: "召回篇(一)-Graph Embedding"
date: 2022-04-01 14:42:20
categories:
  - 算法
  - 图学习与知识图谱
---

{% raw %}

<p>    微视是沉浸式播放场景，用户使用微视时通过不断上滑视频触发新视频的推荐，包含视频的播放时长、播放完整度、点赞、转发、分享、评论、关注、快划等多种丰富的行为。推荐召回的目标，是通过建模用户和视频之间的关联，从视频库中（千万级）找出用户可能感兴趣的视频（千级）。本文主要总结了我们在Graph Embedding上的一些尝试和探索。</p>
<h1>1. 随机游走类</h1>
<p>    随机游走类模型通过一定的游走策略，游走出随机游走序列，这些序列使得非结构化的图数据变得结构化，进一步基于skip-gram等模型训练，得到序列中各节点的embedding。</p>
<h2>1. 1 Node2vec</h2>
<div>  Node2vec模型可以看作是引入了权重调整参数的deepwalk模型，可以灵活调整游走策略。在进行随机游走时，节点的跳转概率分为两部分，一部分由参数p,q来决定，这部分参数主要控制是偏向bfs还是dfs的游走策略，另一部分由图中边的权重来决定。</div>
<div><img alt="" loading="lazy" src="/logbook/images/algorithm/d01eaba40c75cd2de549.png"/></div>
<div>图一：Node2vec跳转概率</div>
<div>    Node2vec的整个过程如图二所示，首先是获取用户的正向行为序列，然后构建user-item异构图，进行随机游走，再把游走出来的序列送入skip gram得到Embedding用于召回。</div>
<div><img alt="" loading="lazy" src="/logbook/images/algorithm/032a347b10ec299d6df3.png"/></div>
<div> 图二：Node2vec</div>
<div>
<div>    Node2vec可以通过随机游走去生成一些原始数据中不存在的序列来丰富训练样本，一定程度上也增加了低频item的出现次数，使得item相关性的建模效果更好。</div>
<div>Node2vec模型相关实验上线效果如下表所示：</div>
<div><img alt="" loading="lazy" src="/logbook/images/algorithm/449e7680ac51cdf4866d.png"/></div>
<h2>1. 2 Metapath2vec</h2>
<p>    前面所述Node2vec的建模方式，本质上是直接将item id作为特征去描述item节点，使得item之间的相关性完全依赖于共现关系来学习，对于低频item不够友好，所以我们希望引入item侧的sideinfo特征来辅助学习item相关性。游走类算法一般是将sideinfo直接作为节点加入构图，而Node2vec实际上还是将user和item节点当成同质节点来处理的，并不能很好地用于包含多种顶点类型和边类型的复杂关系网络。<br/>    Metapath2vec是一个非常好的解决方案，能够区分不同的异质结点，然后用基于meta-path的随机游走获取异构网络中不同类型顶点的异构邻域，从而学习不同类型顶点的Embedding表达。</p>
<h3>1. 2. 1 Metapath2vec增加Sideinfo</h3>
<p>    Sideinfo的选择上，我们从一级类目、二级类目、tags、bgmid等特征中选择了作者（Author）与二级类目（cate2）拼接的方式来构建新节点AC，利用AC节点引入item及作者的类别特征。在设计元路径时，为了发挥AC节点对item的约束性，我们将元路径设计为U-I-AC-I-U的对称格式。具体实现过程如图三所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a3b00ef7f1f02d8efc60.png"/></p>
<h3>1. 2. 2 Metapath2vec泛化性改进</h3>
<p>    在进行了上文的各种改进之后， MetaPath2Vec模型召回的相关性得到了提升，但以上游走路径中AC节点的约束能力过于强大，使得召回的视频（item）缺乏泛化性。而实际召回业务中，我们致力于提供给用户多元化的视频，满足用户多方面的兴趣。</p>
<p>    为了提高模型结果的泛化性，我们的解决方案是放宽中间节点AC的约束能力，建立新的中间节点。经统计发现，有一部分视频作者的发文会存在集中性，即他的发文类别绝大部分集中在1-3个类目下，抽取这些类目作为节点标签，可以使得发文相似的作者聚集在一起，为模型带来泛化性。<br/>    根据上面的思想，我们引入由二级类目构成的新节点CCC，具体构成如下：统计作者一段时间以来发文的各二级类目（cate2）所占比重，将发文占比前三的二级类目（cate2-0，cate2-1，cate2-2）的总和大于一定比例（如0.8）的作者视为发文垂直的作者，然后使用</p>
<p>    二级类目拼接作为新的中间节点cate2-0_cate2-1_cate2-2（CCC），具体如图四所示。在进行了这一步改进之后，线下测评item的embedding发现，有少量emb达到了召回相关性强且泛化到了其他作者，但大部分召回虽泛化到了其他作者的发文，但相关性却下降了。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/53e6065523e1d3fe435b.png"/></p>
<p>    为了提高泛化性的同时保证准确性，我们进一步提高了泛化节点CCC的垂直度。通过实验发现，虽然原始的三个二级类目拼接的中间节点会为数据带来泛化性，但每个归入当前cate2-0_cate2-1_cate2-2节点的作者在各二级类目下的发文比重是不同的，所以我们加入了作者在各二级类目下的发文权重重新构建了用于泛化的中间节点CCC——cate2-0-weight0_cate2-1-weight1_cate2-2weight2。这种构建节点的方式使得中间节点更加细化的同时又具有一定泛化性。同时，在构建异构图时，我们同时保留了CCC节点与原始的AC（author_cate2）节点，当item的二级类目在泛化节点CCC下时则优先与该泛化节点连接，否则则与原始的AC节点连接。离线检查发现调整后的模型相关性与泛化性都有一定提升，实验也在进行中。</p>
<p>    Metapath2vec模型相关实验上线效果如下表所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/55e448edaac3c0de6a1a.png"/></p>
<h1>2. 图神经网络类</h1>
<p>    Metapath2vec等随机游走类模型虽然能够通过添加新节点的方式引入一部分Sideinfo，但无法利用更多的节点特征信息，基于近邻聚合的图神经网络模型GraphSAGE与DGI模型可以很好地解决这个问题。与随机游走类算法不同，聚合类算法通过对目标节点的邻居节点进行固定数量采样的方式使得图数据结构化，减少了计算量，图中节点的各种特征可以参与到训练中。</p>
<h2>2. 1 GraphSAGE模型</h2>
<p>    GraphSAGE是一种深度图神经网络模型，在大规模图中因其可伸缩、可采样、同时支持监督学习和非监督学习的特性而得以广泛应用。现存的方法需要图中所有的顶点在训练embedding的时候都出现；这些前人的方法本质上是transductive，不能自然地泛化到未见过的顶点。而GraphSAGE是一个inductive的框架，可以利用顶点特征信息来高效地为新顶点生成embedding。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/3a779041b0833bf9f431.png"/></p>
<p>    在推荐召回的场景中，我们使用user正向行为序列来构建item同构图来反映用户兴趣，通过GraphSAGE的K层aggregation，从周边K阶邻居节点中提取高维抽象特征，来表达起始节点的item embedding。如图五，在进行中央红色节点的表达时，GraphSAGE会先以该节点为起点，游走出K阶邻居，然后逐层聚合各阶邻居节点，最终得到目标节点的embdedding。</p>
<h3>    2. 1. 1 Mean pooling GraphSAGE模型</h3>
<p>    GraphSAGE模型的图数据是item-item同构图，在训练中，我们筛选使用了如视频的一级类目，二级类目，作者等节点特征。并使用了mean pooling聚合函数代替原始的mean聚合函数，对比如图六所示，即在邻居节点的embedding聚合之前加入MLP，提高网络对邻居节点的特征抽取能力。为了解决了线上资源消耗较多，且超时风险大的问题，降低了embedding的维数，同时为了保证模型学习效果不被减弱，我们增加了邻居节点的采样个数跟采样阶数。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/aedc295c914aaa34ec95.png"/></p>
<h3>2. 1. 2 引入Attention的GraphSAGE模型</h3>
<p>    Meanpooling GraphSAGE模型虽然能够通过邻居节点聚合信息，但其在进行聚合时把所有邻居节点视为权重相同的，忽略了对不同结点间重要程度的区分。为了在聚合节点信息时，赋予不同的结点不同的权重，达到区分不同结点重要性的目地，我们引入了Attention机制。</p>
<p>    Attention机制能够区分不同节点的重要程度，多头Attention善于捕捉多种不同的关键信息，使得邻居节点聚合得到更优质的embedding，其原理如图七所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4c47f9e3a6f0a7c07fa7.png"/></p>
<h3>2. 1. 3 引入负向图的GraphSAGE模型</h3>
<p>    短视频平台的沉浸式的播放体验使得用户的决策成本非常低，用户不喜欢划走即可，所以我们拥有大量的快划样本，而工业界都是只使用正向行为，暂时还没有使用负向行为建模的解决方案和探索。<br/>    为了利用微视场景特有的大量负向行为，我们构建了包含负向item节点与正向item节点的i2i图，拆分成正图与负图两张图，如下图所示。正图中包含的边是正节点指向正节点，负节点指向负节点的，而负图中的边是正节点指向负节点，负节点指向正节点的。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/276eabdc0373d44c4377.png"/></p>
<p>    对于来自正负两张图的节点，我们分别送入一个GraphSAGE模型进行训练，然后将得到的两个embedding进行拼接，并送入BPWR损失函数进行训练。我们的目的是通过这种Pair-wise Ranking的方式，使得正边相连的节点embedding距离尽可能小，负边相连的节点embedding距离尽可能大。</p>
<p>    Graphsage模型相关实验上线效果如下表所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/9b69ed51b32a27f94718.png"/></p>
<h2>2. 2 DGI模型</h2>
<p>    DGI模型延续了GraphSAGE模型对目标节点的局部结构信息的关注，又通过对比学习的方式引入了其他模型所欠缺的对图全局信息建模的能力。本文DGI模型使用与GraphSAGE模型相同的i2i同构无向图，通过目标节点的邻居节点来得到目标节点embedding，以非监督的方式进行训练，并构建基于互信息的无监督学习loss。<br/>    DGI模型的关键思想在于通过区分true graph（G）与 corrupted graph（H）两张图里的点来进行模型的训练。训练过程中，DGI模型通过打乱真实节点的特征来构造corrupted graph（H）；然后通过GCN层获得每张图中节点的embedding（v）；真实图G的节点embedding（v）通过平均或加和得到表征图全局信息的embedding（s）；打分器对来自图G与图H的节点embedding（v）分别打分得到D(v,s)；最后的Loss方程中，如果v来自真实图G，则最大化D(v,s)，如果v来自假图H，则最小化D(v,s)。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/25aa539a377b3258fccb.png"/></p>
<p>    具体流程如图九所示，其中：<br/>(1) 扰乱生成器C：输入真实的图G，然后生成扰乱后的corrupted graph：H=C(G);<br/>(2) 编码器E：获取输入图G并为每个节点计算嵌入向量v；<br/>(3) 读出器R：将图中每个节点的独立embedding转变成象征整个图的向量s；<br/>(4) 打分器D：将节点embedding（v）与graph summary vector（s）进行比较，从而为每个节点embedding产生0到1之间的“分数”。</p>
<h3>2. 2. 1 基于Mean pooling聚合函数的DGI模型</h3>
<p>    为了充分利用目标节点的信息，我们将原始DGI模型中使用的GCN聚合层替换为在前面GraphSAGE模型上表现优秀的Mean pooling聚合层。DGI原始论文中使用的GCN聚合层没有利用到目标节点自身的特征信息，而Mean pooling聚合层可以弥补GCN层的这一缺点，为目标节点的embedding引入自身特征信息。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/d217be8750d91a25a429.png"/></p>
<p>    我们对DGI模型进行了以下改进：</p>
<p>1) 添加了针对类别型特征的处理：图中节点的特征为5种类别型特征，而原始DGI模型中使用的数据节点特征为连续型，因此我们对类别型特征使用Wide&amp;Deep编码器进行编码；<br/>2) 通过随机打乱节点特征向量来构造负样本，考虑样本之间的相对顺序，如图十所示。</p>
<p>DGI模型收益如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f9c6980ae1bf0f66bf39.png"/></p>
<h1>3. 总结与未来工作</h1>
<p>    Graph embedding目前已经广泛应用在推荐、知识图谱等各种场景中，其中，MetaPath2Vec算法的引入使得模型可以在异构图上进行训练，充分利用了图结构数据中user与item两种节点的信息。GraphSAGE模型与DGI模型是两种图神经网络算法，我们在将这些方法引入到推荐召回工作中时，进行了多方面的改进与创新：我们通过实验制定了有效的数据选取规则以及权重规则来构建i2i，u2i图。MetaPath2Vec算法的引入使得模型可以在异构图上进行训练，充分利用了图结构数据中user与item两种节点的信息。我们通过实验迭代出最优的元路径游走序列u-i-ac/ccc-i-u，在充分利用用户行为信息的同时为模型结果提供了泛化性。我们通过实验对GraphSAGE模型与DGI模型的聚合层进行改进，提高模型表征图结构信息的能力，为DGI模型的目标节点引入自身特征信息；改进DGI模型的采样方式，使得真图与假图更难区分，提高模型学习能力。</p>
<h1>4. 鸣谢</h1>
<p>    本文中的算法均基于公司开源框架Platodeep进行开发，感谢@drolcaqiu、@healyhuang、@powergao等Plato平台各位大佬的支持，期待下一个更强大的Plato版本。<br/>[内部链接已移除]</p>
</div> 
{% endraw %}
