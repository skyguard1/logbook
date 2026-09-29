---
title: "Graph embedding在视频的实践"
date: 2022-04-08 11:19:30
categories:
  - 算法平台
  - 图学习与内容理解
---

{% raw %}

<p>当前工业界有不少公司开始将GaphEmbedding和GNN方法应用在推荐领域，如Pinterest的Pinsage、阿里EGES和GATNE等的cluster-GCN等。同时也开展了针对大规模网络的embedding开源平台，如阿里的euler, 的plato, 的PyTorch-BigGraph等。</p>
<p>将graph embedding应用视频推荐领域，也就是面向用graph embedding方法为视频中的用户和视频建模。学习到的用户embedding和视频embedding可用于召回阶段的i2i和u2i，今后也可以作为排序等模型的输入特征。</p>
<p>本文主要分享基于Random Walk和Word2Vec这类Graph Embedding上的实践。该类方法先根据原始数据生成图，然后在图上进行Random Walk生成训练序列，最后基于这些序列训练Word2Vec。常见的算法有DeepWalk、Node2Vec、Metapath2Vec等。主要步骤如下：</p>
<ul><li>
<p>STEP 1: 生成由单类/多类节点组成的图</p>
</li>
<li>
<p>STEP 2: 基于图进行Random walk</p>
</li>
<li>
<p>STEP 3: 将Random walk结果作为训练样本输入Word2vec训练得到每个节点的embedding结果</p>
</li>
</ul><p>其中单类节点单类边组成的图被称之为同构图，多类节点或多类边组成的图被称之为异构图。由此，graph embedding方法又被分为同构图embedding和异构图embedding。在之前提到的常见方法中，DeepWalk和Node2Vec属于同构图embedding方法，Metapath2Vec属于异构图embedding方法。</p>
<p></p>
<h2>1. BGE(DeepWalk)</h2>
<h3>1) 同构图</h3>
<p>2014年提出的DeepWalk首次提出将word2vec应用于graph embedding领域。我们实现了阿里EGES中的base算法（DeepWalk的一种具体实现）。具体框架如下图，图中的b, c, d对应于上述步骤1-3。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8d8ba36b868525ca7cbd.png"/></p>
<p>阿里EGES中的base算法流程（图源自阿里文章）</p>
<p>图(a)是用户观看的视频序列。由此，构建以视频作为节点的同构图，将观看视频A后观看视频B的转移概率作为节点A到节点B的边，如图(b)。此后将图中的每个节点作为start node开始长度固定的随机游走。最终将随机游走得到的序列作为训练数据进行word2vec。</p>
<p>尝试了如下不同word2vec的训练样本生成策略：</p>
<ul><li>
<p>将每个节点random walk x次，每次长度y作为训练样本</p>
</li>
<li>
<p>按当前节点的出度/频率进行random walk</p>
</li>
<li>
<p>将中低频的视频random walk后的结果和原本用户播放视频序列拼接形成训练样本</p>
</li>
</ul><p>发现第三种效果最好，比其他两种离线u2i召回的MRR提升了2.5%，Hittop5提升0.3%。通过对比高中低频视频的MRR和hittop5效果，发现deepwalk对于低中频视频相比于word2vec效果有明显的提升。第一种和第二种策略相比，增加random walk的长度比增加根据节点的出度/频率的random walk次数效果明显。</p>
<p>在i2i定性结果中同样发现算法对低频item的效果明显，如下图所示。图的左侧是deepwalk的结果，右侧是word2vec的结果。可以看出，对于低频的示例视频，deepwalk的i2i结果比word2vec有所提升。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8f7c3826a145272f3651.png"/></p>
<h3>2) 异构图</h3>
<p>图中除了原本的视频节点，也可以加入用户节点和标签节点，形成异构图。图中，用户和视频的边可以是其观看视频的完成度，视频和标签的边可以是1。由于不同节点之间的边分布相差很大，由此设计并实现了Item+Tag+User和Item+Tag的异构图BGE算法。</p>
<p>BGE是基于同构图的Network embedding方法。直接使用于异构图可能导致：图的一个部分被过多游走，而其他部分没有被游走充分。这是由于在同构图上游走的时候，只会游走到相同类型的节点。而在异构图上游走时，会通过不同类型的边游走到不同类型的节点上。然而，不同类型的边的分布可能相差很大，主要在节点出入度分布（稠密or稀疏）和边权重的值范围分布这两方面。</p>
<p>为异构图BGE方法，设计基于偏好的随机游走。不同类型的边设置各自超参数bias，使得随机游走的时候可以带bias的进行游走，从而平衡不同边之间的差异。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7f9ae6c866efc2ee9972.png"/></p>
<p>偏好bias的设定目标是<strong>让节点充分游走到不同类型的节点。</strong></p>
<ol><li>考虑出入度不同，针对不同类型的边，将每个节点与该类边的出度邻居进行L1范数归一化</li>
<li>考虑值范围不同，计算每种类型的边在图中的平均数。偏好为平均数分之一。</li>
<li>根据语义简单调参</li>
</ol><p>下面以Item+Tag+User为例，建立itugraph（由item、tag和user三类节点构成），使用BGE方法为图中的每一个Item、Tag和User学习在同一低维向量空间中的embedding。构建异构图itugraph具体如下：</p>
<ul><li>
<p>节点：item(video)和tag(先锋标签）以及user(用户)</p>
</li>
<li>
<p>边：i2i边，i2t边和u2i边</p>
<ul><li>
<p>i2i: 基于用户播放序列，当前video跳转到下一个video的转移概率</p>
</li>
<li>
<p>i2t: video拥有的先锋标签（归一化）</p>
</li>
<li>
<p>u2i: 用户观看video的完成度</p>
</li>
</ul></li>
</ul><p>Item+Tag的deepwalk的MRR提升了4.6%，Hittop5提升了3.3%。Item+Tag+User的deepwalk MRR提升了6.9%，Hittop5提升了3.5%。但后者由于在图中增加了用户节点，将会使得图的节点数量大大增加，使得模型计算量大大增加。后续线上表现发现两者差距不大。</p>
<p>将Item+Tag的DeepWalk方法应用在视频doki广场feed流的线上召回阶段，<strong>ctr提升了2.6%</strong>, <strong>播放人均vv提升8.4%</strong>, <strong>人均时长提升3.78%，曝光人均vv提升9%。</strong></p>
<p></p>
<h2>2. Node2vec</h2>
<p>2016年，斯坦福大学的Jure Leskovec教授在DeepWalk的基础上提出了Node2vec，其通过调整随机游走权重的方法使graph embedding的结果在网络的同质性（homophily）和结构性（structural equivalence）中进行权衡权衡，即Node2vec方法支持可参数配置的广度优先搜索(BFS)和深度优先搜索(DFS)的随机游走。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8a87ecb618cfcd28eb18.png"/></p>
<p>Node2vec的BFS和DFS（源自Node2vec论文）</p>
<p>Node2vec通过参数p和q调节BFS和DFS的权重。具体如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d1d0e182e9d4ae1b7e31.png"/></p>
<p>基于plato进行实验，效果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c8242d223c33f11528ef.png"/></p>
<p>通过在随机游走时增加BFS权重（增大q)，相比于deepwalk在游戏数据上MRR提升了1.9%，Hittop5提升了1%，在全量数据上MRR提升了1.1%，hittop5提升1%。</p>
<p>但随着q的增大时，运行时间变长，由几分钟(p,q=1)上升到 2-3小时(q=256 or 1024)。这是由于按照目前加权高阶随机游走的实现，随着 q的不断增大，会导致图中与 X2，X3 类似的顶点被拒绝的概率上升，加剧了重新采样的频率，从而导致运行时间的增加。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c02d9e463a4e2be78eab.png"/>Plato的node2vec原理(源自plato关于node2vec的介绍）       </p>
<p></p>
<h2>3. Metapath2vec</h2>
<p>Metapath2vec方法支持在异构网络上基于元路径(meta-path)的随机游走。在视频应用场景下，以之前的itugraph图为例，元路径有：Item-Tag-Item (I-T-I)、Item-User-Item (I-U-I) , User-Item-Item-Item (U-I-I-I) , User-Item-Tag-Item (U-I-T-I) 等。</p>
<p>该方法仅支持单条元路径，无法适应于视频下多种节点和边组成的异构网络。因此，设计实现了多条元路径的自动发现方法。该方法用新一天的用户行为数据来监督前一天的图上的元路径的发现并学习其之间的权重。此后使用plato的metapath2vec random walk对多条metapath的组合进行random walk。最终将random walk得到的序列作为word2vec的训练数据。</p>
<p>基于plato的实验效果为在游戏数据上MRR提升了3.8%，hittip5提升了1.8%。在全量数据上MRR提升了2.3%, hittop5提升了1.2%。以游戏数据上的效果最优的结果为例，其最终发现的metapath组合为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a19e1dfd6078609f9650.png"/></p>
<p>注：Plato上多条metapath进行random walk后会将不同的metapath存储在不同的多个文件上。当后续的word2vec进行读入时将会把同一个节点开头的walk序列随机读入到不同的worker上，会使得最终embedding的结果下降。建议在进行word2vec之前将random walk的结果重新partition，即将同一个节点开头的walk序列存放在同一个文件里。</p>
<h2></h2>
<h2>展望</h2>
<div>
<div>
<p>graph embedding领域从算法的角度上讲，一些可能值得关注和研究的方面：<br/>1）异构图embedding（包含不同类型节点）。现有的方法总体上embedding的不够完善，比如metapath2vec本身带有一定的局限性。而普通的同构图embedding往往难以良好的embedding不同类型的节点，可能导致不同类型节点的效果差异较大。<br/>2) 融合更多信息的graph embedding，比如节点属性。这对工业界可能会带来效果提升。<br/>3) 动态图embedding。目前的方法难以embedding到动态图的规律<br/>4) 基于graph embedding 的因果推理等<br/>5) graph embedding的多向量学习，比如item embedding在不同的角度（view)可以有不同的embedding。<br/>6) graph embedding和多模态的结合，比如用户看了文章（文本），观看了视频。<br/>7) graph embedding的理论研究</p>
<p></p>
</div>
</div>
<h2><strong>引用</strong>：</h2>
<p>1. Perozzi B, Al-Rfou R, Skiena S. Deepwalk: Online learning of social representations[C]//Proceedings of the 20th ACM SIGKDD international conference on Knowledge discovery and data mining. 2014: 701-710.</p>
<p>2. Grover A, Leskovec J. node2vec: Scalable feature learning for networks[C]//Proceedings of the 22nd ACM SIGKDD international conference on Knowledge discovery and data mining. 2016: 855-864.</p>
<p>3. Dong Y, Chawla N V, Swami A. metapath2vec: Scalable representation learning for heterogeneous networks[C]//Proceedings of the 23rd ACM SIGKDD international conference on knowledge discovery and data mining. 2017: 135-144.</p>
<p>4. [内部或本地链接已移除]</p>
<p>5. [内部或本地链接已移除]</p>
<p>6. [内部或本地链接已移除]</p>
<p>7. [内部或本地链接已移除]</p> 
{% endraw %}
