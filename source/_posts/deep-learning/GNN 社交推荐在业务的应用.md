---
title: "GNN 社交推荐在业务的应用"
date: 2022-04-27 18:37:46
categories:
  - deep-learning
---

{% raw %}

<div>
<div>
<div>
<p>撰写人:chrisyi，jerrycgsong </p>
<div>
<div>
<div>
<h1>一、学界研究: GNN 社交推荐模型 </h1>
<p>  我们考虑的社交关系进行兴趣建模，以希望提高推荐的效果。这里隐含这 2 个社交常 识假设:其一是好友同质性，同质性是社交网络结构性的基本外部原因，即我们认为物以 类聚人以群分，好友之间大概率有相同的兴趣。其二是社交影响力，这是指社交个体的行 为、思想、态度、情绪、习惯乃至价值观会受到其所在社群的其他人的影响。这两个基础 的想法也是人们在设计 GNN 网络算法框架的指南针。 </p>
<p>  好友同质性，即好友之间的兴趣表征应该相对接近。一部分研究会直接用好友关系作 为监督信息对用户最终的兴趣表征进行更新，即直接用好友关系构建 loss 拉近好友之间的 user embedding 的距离，如图一(a)所示。这种方法也许存在一个问题，即直接利用好 友关系作为监督信息过强，在推荐的目标域上，并不是所有的好友在该域的行为都一致。 另一部分研究是把社交图和行为图组成一个异构网络，即利用好友关系作为特征输入，利 用好友关系来强化用户的兴趣表征，如图一(b)所示。这种方法利用好友关系进行特征 传递，GNN block 承担了重要的特征选择的功能，而 loss 主要还是聚焦在行为域的 user 和 item 的交互信息。这种整合方式的优势在于社交关系和行为数据是可以同时纳入训练，模 型可以兼顾两个域的信息，通过自学习的方式去分配权重，而不需要人工规则参与和调整. GraphRec 算法的框架也可以归纳为图一(a)的类型。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/48014489abc288399995.png"/></p>
<p>图 1: GNN 社交推荐算法框架 </p>
</div>
</div>
</div>
<div>
<div>
<div>
<p>  好友影响力在整个社交网络传播的，有一部分论文会考虑社交网络的这个特质，设计 GNN 的算法框架，以达到对用户更好的 embedding 表征的目标。Diffnet 设 计了一个层级的影响传播结构(layer-wise influence propagation structure )，建模用 户的潜在嵌入表示是如何随着社交传播过程的持续而改变的。Diffnet 基于 GNN 模拟社 交影响力传播过程，从而能更好的表征 User 和 Item。其主要思想是为用户设计了影响 传播结构，建模在社交传播过程中，用户的潜在表示是如何演变的。这个过程也可以 认为是更好地表征了网络拓扑结构。整个算法框架分为四部分:1嵌入层;2融合 层;3层级影响传播层;4预测层;具体来说，传播过程首先是在每个用户的特征融 合和用户隐向量(描述用户潜在行为偏好)的基础上，为每个用户初始化嵌入表示; 在 item 端，由于 item 不会在社交网络中传播，故每个 item 嵌入表示是由自由的 item 隐向量和其本身特征融合得到的。随着影响力传播到事先定义好的第 K 步，第 K 层的 用户兴趣表示也就得到了，即也可以认为这相对于图一的建模框架，更多地考虑到了 高阶信息。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1960967b09a72bf3a85a.png"/></p>
<p>图 2:Diffnet 模型框架(来自原论文) </p>
<p>  作者在 Diffnet 的基础上提出了改进版本的 Diffnet++，Diffnet++沿袭了社交影响力传播的思路，并追加了在用户-物品二分图上兴趣传播的建模。DiffNet++用了两层 的注意力网络分别对社交影响力和社交兴趣进行建模。在模型的第一层，它先通过注 意力机制分别对社交图的好友特征和二分图的邻居特征进行整合，在模型的第二层， 考虑用户的兴趣扩散建模。 </p>
<p>  我们知道，社交网络好友存在同质性是指在某些方面相同，即并不是所有好友感 兴趣的所有东西我都感兴趣，即对于推荐目标域来说，社交数据可能存在噪声，值得 一提的是，模型 ESRF[11]认为社交关系是不可靠的，既可能包含噪声，也可能不够完 整。故而 ESRF 采用 auto-encoder 机制将噪声社交关系过滤掉，然后增加潜在的高影 响力的连边。类似的，DiffNetLG[12]也通过本地网络结构对连边先进行预测，然后在 补充完连边以后的图网络上进行卷积。 </p>
<h1>二、GNN 社交推荐在微信业务上的应用 </h1>
<p>  在微信生态内，直播广场、订阅号文章的推荐流场景都是新的业务场景，在这两个业 务场景我们接入了 GNN 社交推荐算法来提高新用户/冷用户的推荐效果，在业务的召回环 节生效。如上文所述，社交推荐两个基本假设是社交同质性和社交影响力，这两个基本思 想也贯穿到模型落地的全流程 PPL, 从 GNN 底图构造到 GNN 算法的设计。 </p>
</div>
</div>
</div>
<div>
<div>
<h3>1、GNN 社交召回建模的动机 </h3>
</div>
<div>
<div>
<p>  在直播业务和订阅号的推荐流业务中，都有最基础的社交召回，即多个好友在看的规 则召回，为了降低好友带来的噪声，规则召回会限制大于 N 个好友在看的内容才会进行推 荐，以保证准确性。但这带来的问题就是覆盖率低、召回数量少。GNN 社交召回模型利用 端对端的训练来提纯社交信息，以提高召回的准确率和覆盖率。 </p>
<h3>2、GNN 底图构造 </h3>
<p>  GNN 模型的需要处理的原始图是由社交关系网络和用户行为网络构造成的异构图。这 里微信社交关系量级千亿，用户人均关系链几百，这不但给工程带来了很大的压力，也给 模型带来了噪声。因此，我们对原始图进行了适当的裁剪，从而形成 GNN 模型的直接输 入。这个步骤我们称为 GNN 底图的构造。 </p>
<p>  在底图构造时，对于社交召回 GNN, 我们基于社交影响力和社交同质性进行了裁剪。 我们以直播业务举例进行说明:原始图是由社交关系和直播行为构成的异构图，我们计算 网络结构中的三角形关系，进行边的裁剪。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/aa280b8cbbf6fadf2ca0.png"/></p>
图 3: GNN 社交召回底图构造 </div>
<p>如上图所示，对每个中心节点用户，社交好友的裁剪，对于每个好友，我们会计算他 和中心节点用户组成的两类三角形的个数，这个三角形个数即为好友裁剪的标准，其中行 为图三角形的个数的权重高于社交三角形的结构。进行裁剪后，我们对社交图，每个中心 节点用户最多保留 100 个好友。 </p>
<h3>3. GNN 社交召回双塔模型迭代 </h3>
<p>  GNN 社交召回模型历经几次模型结构迭代，我们在直播双流推荐场景和订阅号推 荐流这两个场景都取得不错的收益。其次我们在直播双流场景上进行了时效性的迭 代，由天更新模型迭代为流式模型，进一步取得了收益。</p>
<h3>3.1 模型结构的迭代 </h3>
</div>
</div>
<div>
<div>
<div>  (1)构图完成后，我们从原图中定义 metapath，并基于 metapath 进行多路卷积，然 后多路卷积进行 concat 后连接 dense 层，行为 GNN 双塔召回模型。模型框架图如图4所示。原始图是由社交关系和直播行为构成的异构图。</div>
<div><img alt="" loading="lazy" src="/logbook/images/deep-learning/2ae6df22af6219465748.png"/></div>
<div>图4: 社交GNN模型结构</div>
</div>
<div>
<div>
<p>  这一版模型刚上线时，线上 ABtest 效果持平，然后我们进行模型埋点分析发现，社 交的 metapath 对用户的 embedding 表达贡献的作用非常小。主要原因是模型的训练 样本都是由高活用户贡献，直播的行为 metapath 对 embedding 的表达起了关键的作 用，因此导致低活用户的 embedding 学习的不充分。 </p>
<p> (2)基于(1)的分析结论，我们对低活用户的 embedding 学习问题进行了两个针对性的优化，一是整体模型追加 AE loss ，二是在训练阶段对高活用户的 U-I metapath 进行一定比例的随机性 drop out。模型的框架如图5所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9e3ae7116aa33e0c4dae.png"/></p>
<p>图5: 社交GNN优化版的模型结构</p>
</div>
</div>
</div>
<div>
<div>
<div>
<p>  这里 AEloss 的构造 UU 对，也是采用了在裁剪图相同的策略生成的 UU 对，考虑社交同质性，主要抽取有相同主播的用户对、有三角形社交关系的用户对进行学习。 使得低活用户的 user embedding 能更多地直接参与 loss 的计算，得到更充分的学 习。我们第二版本的 GNN 社交召回模型在直播业务和订阅号推荐流业务均已上线并 推全。 </p>
<p>  在直播业务上，实验方式:在原有的 DSSM 主流量召回上，追加 GNN 社交召 回。实验结果:在 0.01 显著性水平下, 在非高活用户指标上，pctr 显著正向 0.653%， uctr 显著正向 0.464%，uctr-30s 显著正向 0.472%，其余指标不显著正向。X 实验平台 链接(B4 实验组): [内部链接已移除] </p>
<p>在订阅号推荐流业务上，实验方式:在原来的好友在看召回、好友关注召回的基 础上追加 GNN 社交召回。实验结果:在 0.01 显著性水平下，图文点击率显著正向 1.5%，人均阅读文章数显著正向 2.2%，人均点击文章数显著正向 2.3%，人均互动(关 注、分享)显著正向 8.3%，其余指标不显著正向。X 实验平台链接(B5 实验组): [内部链接已移除] </p>
<p>另外，我们的这个工作也被 KDD2021 接受为 <a href="https://dl.acm.org/doi/10.1145/3447548.3467427">Multi-view Denoising Graph Auto-Encoders on Heterogeneous Information Networks for Cold-start Recommendation</a>，对应的KM文章也会在随后发出。</p>
<h3>3.2 模型时效性的迭代 </h3>
<p>对于直播场景，主播开播即生成新的直播间，内容也在流式地变化着，因此我们打通 了 GNN 模型流式训练的 PPL, 将上述模型升级为流式训练的模型，其效果得到进一步的提 升。实验方式:将天模型 GNN 替换为流式训练 GNN。实验结果:在 0.05 显著性水平下, pctr 不显著正向 0.432%，uctr 显著正向 0.492%，uctr-30s 显著正向 0.737%，其余指标不显 著正向。X 实验平台链接(B2 实验组) [内部链接已移除] </p>
GNN 天模型和流式训练模型都是基于 PlatoDeep 开发，详细的 PPL 介绍见团队的 KM 文章PlatoGL和PlatoGL on DKR。
<h1>三、 小结与后续 </h1>
<p>在社交推荐的问题上，指导我们建模的基本思想是好友同质性和好友影响力。目前在底图构造和模型追加 loss 的部分我们都使用到了传统网络科学中对网络结构的认知分析结果，这些思路都在提现在好友同质性和影响力的挖掘结果上，而学界直接利 用模型对社交影响力传播进行直接建模，我们目前还没有拿到收益。后续，我们在 GNN 社交推荐的模型中我们会考虑更多的高阶结构，比如更多类型的 motif，以及社群结构表达，来增强模型对社交关系的拓扑表达，提高社交推荐的精度。 </p>
<p>声明:本文的工作包含多位团队成员(nickgu，joelzheng，danieslin，drolcaqiu)的工作 产出，由 chrisyi 和 jerrycgsong 整理成文。同事们对文中细节有疑问，欢迎交流。 </p>
<p>参考资料 </p>
</div>
</div>
</div>
<div>
<div>
<div>
<pre>[1] C. Gao et al. Graph Neural Networks for Recommender Systems: Chanllenges, Methods, and Directions. TIS 2021.
</pre>
<pre>[2] S. Wu et al. Graph Neural Networks in Recommender Systems: A Survey. J. ACM 2021.
</pre>
<pre>[3]  https://github.com/wusw14/GNN-in-RS
[4]  https://github.com/tsinghua-fib-lab/GNN-Recommender-Systems
</pre>
<pre>[5]  T. Kipf and M. Welling. Semi-supervised classification with graph convolutional networks. ICLR 2017.
</pre>
<pre>[6]  W. L. Hamilton et al. Inductive representation learning on large graphs. NeurIPS 2017.
</pre>
<p>[7] P. Veličković et al. Graph attention networks. ICLR 2018. [8] J. Sun et al. Multi-graph Convolution Collaborative Filtering. CIKM 2020.</p>
<pre>[9] X. Wang et al.  Disentangled Graph Collaborative Filtering. SIGIR 2020.
</pre>
<pre>[10] R. Ying et al.  Graph Convolutional Neural Networks for Web-Scale Recommender Systems. KDD 2018.
</pre>
<pre>[11]  J. Yu et al. Enhance Social Recommendation with Adversarial Graph Convolutional Networks. 2020.
</pre>
<pre>[12] C. Song et al.  Social Recommendation with Implicit Social Influence. SIGIR 2021.
</pre>
<pre>[13] L. Wu et al.  A Neural Influence Diffusion Model for Social Recommendation. SIGIR 2019.
</pre>
<pre>[14] Q. Wu et al.  Dual Graph Attention Networks for Deep Latent Representation of Multifaceted Social Effects in Recommender Systems. WWW 2019.
</pre>
<pre>[15] L. Wu et al.  Diffnet++: A neural influence and interest diffusion network for social recommendation. TKDE 2020.
</pre>
<pre>[16] C. Ma et al. Memory Augmented Graph  Neural Networks for Sequential Recommendation. AAAI 2020.
</pre>
</div>
</div>
</div>
<div>
<div>
<div>
<pre>[17] Z. Pan et al.  Star Graph Neural Networks for Session-Based Recommendation. CIKM 2020.
</pre>
<pre>[18] J. Wang et al.  Session-based Recommendation with Hypergraph Attention Networks. ICDM 2021.
</pre>
<pre>[19]  https://en.wikipedia.org/wiki/Gated_recurrent_unit
[20] X. Wang et al.  KGAT: Knowledge Graph Attention Network for Recommendation. KDD 2019.</pre>
<pre>[21] R. Sun et al.  Multi-Modal Knowledge Graphs for Recommender Systems. CIKM 2020.
</pre>
<pre>[22] H. Wang et al.  Knowledge Graph Convolutional Networks for Recommender Systems. WWW 2019.
</pre>
</div>
</div>
</div>
<p><br/></p>
</div>
</div>
</div> 
{% endraw %}
