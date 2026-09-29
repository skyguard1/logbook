---
title: "当画像遇上GNN，更好地进行CF建模"
date: 2022-05-10 18:51:53
categories:
  - deep-learning
---

{% raw %}

<h1>一、    背景介绍</h1>
<p>用户兴趣画像是对用户行为序列的高度抽象。相比用户行为序列之间的相似性（如共同点赞了一个视频），用户在画像之间的相似性（如有一个相同的兴趣tag/cate）会更强。在内，各个业务均有自己的画像积累，但是业务间缺少互通。一个用户在一个业务内的兴趣画像只能代表用户的部分兴趣，而站在中台多端画像的角度，融合多端画像可以让用户的兴趣表达更充分，且各个业务在画像层面可以互为补充（如图1所示）。</p>
<p>    因此本文提出了一种将多端画像融入到具体某一目标业务深度模型的用户embedding生成算法，通过将Graph与我们设计的基于tag共现的无监督信号相结合，使模型能充分利用多端画像信息，学习到更好的适配于目标业务的用户表征，以服务于推荐召回侧。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/2f891db84cc7d506bc7a.png"/></p>
<p>图1. 用户多端画像可以让用户兴趣表达更加充分</p>
<h1>二、    方案选型与Graph方法构图介绍</h1>
<p>我们整理目前所拥有的数据主要分为两大块：目标业务的用户行为流水数据与用户的多端画像信息（如图2所示）。前者代表了用户在目标业务的兴趣偏好，后者则通过画像提供额外的知识，以加深对用户之间偏好关联的建模。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/66a2cd766e828051ca3d.png"/></p>
<p>图2 目标业务的用户行为流水数据提供训练数据，用户多端画像提供额外知识补充用户相似关系 </p>
<p>在进行具体的模型介绍前，我们先解释下，为什么用Graph来进行画像价值挖掘，而不是直接把画像当做特征送给普通的DNN模型，如双塔模型。以微视端push场景作为目标端业务为例，我们统计了以微视用户为主体，其用户在其他各端的画像覆盖度，见表1。由结果可以看出覆盖度不是很高，如果直接将画像信息当作特征用于双塔模型建模，会出现特征缺失严重的问题，会干扰双塔模型的建模。</p>
<p>表1 其他业务标签在微视近10天用户的覆盖度</p>
<table><tbody><tr><td>
<p>微视视角</p>
</td>
<td>
<p>微视Cate</p>
</td>
<td>
<p>QQ浏览器Tag</p>
</td>
</tr><tr><td>
<p>100%</p>
</td>
<td>
<p>93.93%</p>
</td>
<td>
<p>7.35%</p>
</td>
</tr><tr><td>
<p>QQ浏览器Cate</p>
</td>
<td>
<p>App类目画像</p>
</td>
<td>
<p>看点Tag</p>
</td>
</tr><tr><td>
<p>6.99%</p>
</td>
<td>
<p>81.87%</p>
</td>
<td>
<p>17.04%</p>
</td>
</tr><tr><td>
<p>看点图文Tag</p>
</td>
<td>
<p>QQ音乐Tag</p>
</td>
<td></td>
</tr><tr><td>
<p>43.14%</p>
</td>
<td>
<p>6.96%</p>
</td>
<td></td>
</tr></tbody></table><p> </p>
<p>图的构建是Graph模型训练的基础。在构图中，首先是用户侧，以用户和多端tag/cate分别作为节点，用户与多端tag/cate画像的关系作为边，来充分挖掘用户在多端画像层面呈现的相似关系。此外，具体到某一目标业务，我们也可以纳入目标业务自己的二级分类画像以及tag画像。在item侧，我们也类似地融入item的二级分类、tag，这样用户画像就与用户所看的视频通过标签关联了起来。此外，用户在目标业务对item的正负向行为是我们最重要的监督信号，用以传递用户在目标业务的明确喜好。在具体图构建过程中，我们以近10天的微视push用户行为流水信息来建模用户在目标端业务的明确喜好，并针对用户的各端画像，过滤掉绝大部分用户都有的过热tag，因为过热tag不能很好的表征用户的个性化兴趣。</p>
<h1>三、    方案设计</h1>
<p>在图构建好后，针对如何挖掘多端画像信息,我们进行了调研与探索，提出了以下三种Graph建模方案。</p>
<h2>3.1基于多端画像的MetaPath2vec方案</h2>
<p>为了高效的进行项目迭代，源于游走类算法组件相对成熟，我们首先采用Metapath2vec[6]的方案。Metapath2vec算法是node2vec算法在异构图上的实现，通过带权随机游走得到异构图的节点序列，用一个滑动窗口来构建正样本，窗口内的节点embedding尽可能相似，因此两个节点，只要它们的多阶邻居整体相近，即使不直接相连，它们的Embedding向量也比较相似。</p>
<p>针对微视端push，我们设计了如表2的2条Metapath，其传递出的语义也整理进了表格。得益于对多端画像的充分挖掘，以及当时线上缺少User CF相关召回，我们收获了非常不错的线上效果，效果的具体数据可见表7。</p>
<p>表2 Metapath2vec设计与思考</p>
<table><tbody><tr><td>
<p><strong>MetaPath设计</strong><br/></p>
</td>
<td colspan="2">
<p><strong>传递语义</strong></p>
</td>
</tr><tr><td>
<p>User → 多端Tag → User → Item → 微视Tag → User</p>
</td>
<td colspan="2" rowspan="2">
<p>1. User-&gt;Item为强监督信号，用以传递用户喜好</p>
<p>2. 带有相似Tag的User应该对带有相似Tag的Item有相似的兴趣喜好</p>
</td>
</tr><tr><td>
<p>User → 多端Tag → User → Item → 微视Tag → Item</p>
</td>
</tr></tbody></table><h2>3.2基于多端画像的跨域GNN方案</h2>
<p>首先不同业务的画像可以看成不同的domain，而我们的目标是将多端画像的知识迁移到具体某一目标业务，这可以看做是将源域的知识迁移到目标域，算是一种迁移学习。因此我们对迁移学习的基本方法进行了调研，现有的认可度较高的分类是分为四类，具体的每一类的方法概要如表3所示。由于我们任务所具有的特点1. 存在大量source domain画像信息2. 无source domain标签 3. source domain仅提供额外知识，与这四种方式不是特别吻合，我们尚未发现完全match我们场景的成熟方案。</p>
<p>表3 迁移学习类别</p>
<table><tbody><tr><td>
<p><strong>方法分类</strong></p>
</td>
<td>
<p><strong>方法概要</strong></p>
</td>
</tr><tr><td>
<p>基于样本的迁移方法</p>
</td>
<td>
<p>通过调整样本权重，减少源域和目标域的样例的分布差异从而进行迁移。</p>
</td>
</tr><tr><td>
<p>基于特征的迁移方法</p>
</td>
<td>
<p>对特征进行变换到一个高维空间中，在高维空间中特征分布相似，从而完成迁移学习。</p>
</td>
</tr><tr><td>
<p>基于模型的迁移方法</p>
</td>
<td>
<p>本质是参数共享的模型，在源域上训练模型，然后基于目标域调整</p>
</td>
</tr><tr><td>
<p>基于关系的迁移方法</p>
</td>
<td>
<p>挖掘和利用关系进行类比迁移。</p>
</td>
</tr></tbody></table><p>之后我们又调研了GNN的一些论文，我们从KDD2021的一篇微信的Paper[1][2]（MvDGAE）获得了启发，他们除去U-I双塔建模外，还以auto-encoder的方式重建了U-U/I-I间的相似度(见图3)，U-U相似度是基于两个用户共现的标签数和视频数决定的。这对我们将多端画像定位在沟通用户与用户的媒介具有重大参考意义.</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/e8e704e1f009fb8b7820.png"/></p>
<p>图3. MvDGAE利用auto-encoder的方式建模了I-I(U-U)间的相似度</p>
<p>MvDGAE提出使用User/Item层面的属性共现并结合Auto-encoder来增强User/Item的表达，而共现关系在画像层面普遍存在，我们在用户多端画像共现层面建立额外监督信号：如果某两个用户在任一端画像有K个画像共现，那这两个用户相似。针对多端画像中的每一路画像，通过设置K个画像共现来构造U-U相似度矩阵，若batch内用户pair对不足K个画像共现，设为负例，并以Auto-encoder的方式学习U-U相似度矩阵。而在用户的embedding生成方面，我们通过设计的多条元路径user -&gt; tag -&gt; user,user -&gt; tag -&gt; item,user -&gt; category对原始图进行采样，之后通过类似GraphSage[3]的方式对每一条采样路径聚合得到用户的embedding，并求均值获取最终的用户embedding。具体的模型如图4所示。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/b41af62aaae9d1acd7c1.png"/></p>
<p>图4. 基于多端画像适配MvDGAE方案 </p>
<p>    但是我们也发现了一个重要问题：在构建U-U相似度矩阵时，如果仅通过使用&gt;或者&lt;K个画像共现条件限制太严格了（hard）,在K的临近值处存在模棱两可的情况，我们不能明确的认为在K的临近值处两用户是否相似。因此我们借鉴计算机视觉detection领域定义正负例的经验，使用ignore mask来缓解这个现象，使得K临界处的pair对最终的损失不产生贡献。并且也通过离线评估验证了这种设置的有效性，见表4。</p>
<p>表4 使用Ignore mask提升MvDGAE方案离线效果</p>
<table><tbody><tr><td></td>
<td>
<p>Precision@10</p>
</td>
<td>
<p>NDCG@10</p>
</td>
<td>
<p>Recall@20</p>
</td>
<td>
<p>Recall@50</p>
</td>
</tr><tr><td>
<p>MvDGAE<br/></p>
</td>
<td>
<p>0.2609%</p>
</td>
<td>
<p>0.6909%</p>
</td>
<td>
<p>2.6093%</p>
</td>
<td>
<p>7.0051%</p>
</td>
</tr><tr><td>
<p>+ignore</p>
<p>mask</p>
</td>
<td>
<p>0.2955%</p>
</td>
<td>
<p>0.7377%</p>
</td>
<td>
<p>2.6813%</p>
</td>
<td>
<p>7.2420%</p>
</td>
</tr><tr><td><strong>相对提升</strong></td>
<td>
<p><strong>+13.26%</strong></p>
</td>
<td>
<p><strong>+6.77%</strong></p>
</td>
<td>
<p><strong>+2.76%</strong></p>
</td>
<td>
<p><strong>+3.38%</strong></p>
</td>
</tr></tbody></table><p> </p>
<h2>3.3 基于对比学习的跨域GNN方案</h2>
<p>    我们通过数据分析来思考进一步优化方向。我们统计了人均tag数量的1/4分位数，发现对于低活/新用户，画像信息并不完善（如用户不够活跃）。加上由于推荐偏差的存在（用户在某一端的画像表达可能并不充分），通过设定阈值来构建U-U相似度不鲁邦。我们重新审视了MvDGAE的方案，发现他们是以pairwise方式使用Auto-encoder来学习U-U相似度，相比之下，我们提出一种triplet的方式来提升对U-U关系的挖掘。针对三个用户U1,U2,U3，如果U1相较于U3，与U2更为相似，那么我们可以直观的认为U1与U2的Tag共现个数相比于U1与U3的更多，进而拉近U1与U2距离，推开U1与U3距离，这与对比学习的思想相契合（见图5）。由此针对多端画像的每一端画像，我们均添加上述U-U间的无监督信号，通过构建正负例三元组，通过BPR损失来进行建模，其计算公式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1f180830494a5b62a1cd.png"/></p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/3e3f8c04c9ada10d6e22.png"/></p>
<p>图5. 基于多端画像进行对比监督的GNN方案</p>
<p>而多端画像存在多个无监督信号，为了平衡他们的作用，我们借鉴MvDGAE方案，使用Bayesian Task Weight Learner自动调权。</p>
<p>在有监督信号方面，我们通过采样用户的正负样本并通过交叉熵损失进行建模</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/23d1a408b9bcb2149cab.png"/></p>
<p>最终将有监督损失与无监督损失求和来完成模型的最终训练。</p>
<p>我们通过离线实验验证了使用对比学习方式相比使用auto-encoder方式的优越性，结果如表5所示。</p>
<p>表5 基于多端画像进行对比监督的GNN方案离线效果</p>
<table><tbody><tr><td></td>
<td>
<p>Precision@10</p>
</td>
<td>
<p>NDCG@10</p>
</td>
<td>
<p>Recall@20</p>
</td>
<td>
<p>Recall@50</p>
</td>
</tr><tr><td>
<p>+ignore</p>
<p>mask</p>
</td>
<td>
<p>0.2955%</p>
</td>
<td>
<p>0.7377%</p>
</td>
<td>
<p>2.6813%</p>
</td>
<td>
<p>7.2420%</p>
</td>
</tr><tr><td>
<p>Triplet</p>
</td>
<td>
<p>0.4129%</p>
</td>
<td>
<p>1.1405%</p>
</td>
<td>
<p>3.4986%</p>
</td>
<td>
<p>7.6797%</p>
</td>
</tr><tr><td><strong>相对提升</strong></td>
<td>
<p>+39.70%</p>
</td>
<td>
<p>+54.60%</p>
</td>
<td>
<p>+30.48%</p>
</td>
<td>
<p>+6.04%</p>
</td>
</tr></tbody></table><p> </p>
<p>    此外，negative transfer是迁移学习里需要重视的问题，我们也通过离线实验验证了引入多端画像信息对模型效果的持续提升。限于现阶段的资源，以及高效迭代实验，我们目前只融入了看点视频tag和app类目信息，在未来会尝试融入更多端画像。</p>
<p>表6 验证是否存在negative transfer</p>
<table><tbody><tr><td></td>
<td>
<p>Precision@10</p>
</td>
<td>
<p>NDCG@10</p>
</td>
<td>
<p>Recall@20</p>
</td>
<td>
<p>Recall@50</p>
</td>
</tr><tr><td>
<p>Triplet</p>
</td>
<td>
<p>0.4129%</p>
</td>
<td>
<p>1.1405%</p>
</td>
<td>
<p>3.4986%</p>
</td>
<td>
<p>7.6797%</p>
</td>
</tr><tr><td>
<p>w/o App类目Tag</p>
</td>
<td>
<p>0.2762%</p>
</td>
<td>
<p>0.6837%</p>
</td>
<td>
<p>2.7528%</p>
</td>
<td>
<p>7.3257%</p>
</td>
</tr><tr><td>
<p>w/o 看点Tag</p>
</td>
<td>
<p>0.3791%</p>
</td>
<td>
<p>0.9955%</p>
</td>
<td>
<p>3.1699%</p>
</td>
<td>
<p>7.1833%</p>
</td>
</tr><tr><td>
<p>w/o Both</p>
</td>
<td>
<p>0.2378%</p>
</td>
<td>
<p>0.6102%</p>
</td>
<td>
<p>2.3924%</p>
</td>
<td>
<p>6.4452%</p>
</td>
</tr><tr><td>
<p>w/o App类目Tag</p>
</td>
<td>
<p>-33.11%</p>
</td>
<td>
<p>-40.06%</p>
</td>
<td>
<p>-21.32%</p>
</td>
<td>
<p>-4.61%</p>
</td>
</tr><tr><td>
<p>w/o 看点Tag</p>
</td>
<td>
<p>-8.18%</p>
</td>
<td>
<p>-12.72%</p>
</td>
<td>
<p>-9.39%</p>
</td>
<td>
<p>-6.46%</p>
</td>
</tr><tr><td>
<p>w/o Both</p>
</td>
<td>
<p>-42.40%</p>
</td>
<td>
<p>-46.50%</p>
</td>
<td>
<p>-31.62%</p>
</td>
<td>
<p>-16.08%</p>
</td>
</tr></tbody></table><p> </p>
<h1>四、    落地应用</h1>
<p>我们在微视端push场景进行了模型落地，我们相继落地了增加一路metapath2vec User CF召回，增加一路GNN User CF召回，增加一路GNN Item CF召回，获得了不错的业务收益，三次实验的线上AB结果如表7-9所示：</p>
<p>表7 微视端push增加一路metapath2vec UCF召回实验效果</p>
<table><tbody><tr><td>
<p><strong>微视端Push AB效果</strong></p>
</td>
<td>
<p><strong>+MetaPath2vec</strong></p>
</td>
</tr><tr><td>
<p>PCTR点击率</p>
</td>
<td>
<p>+5.81%</p>
</td>
</tr><tr><td>
<p>UCTR点击率</p>
</td>
<td>
<p>+3.74%</p>
</td>
</tr><tr><td>
<p>人均push有启活跃天</p>
</td>
<td>
<p>+4.91%</p>
</td>
</tr><tr><td>
<p>人均push首启活跃天</p>
</td>
<td>
<p>+4.94%</p>
</td>
</tr></tbody></table><p>表8 微视端push增加一路GNN UCF召回实验效果</p>
<table><tbody><tr><td>
<p><strong>微视端Push AB效果</strong></p>
</td>
<td>
<p><strong>+Triplet</strong></p>
</td>
</tr><tr><td>
<p>PCTR点击率</p>
</td>
<td>
<p>+0.97%</p>
</td>
</tr><tr><td>
<p>UCTR点击率</p>
</td>
<td>
<p>+0.91%</p>
</td>
</tr><tr><td>
<p>人均push有启活跃天</p>
</td>
<td>
<p>+1.12%</p>
</td>
</tr><tr><td>
<p>人均push首启活跃天</p>
</td>
<td>
<p>+1.39%</p>
</td>
</tr></tbody></table><p>表9 微视端push增加一路GNN ICF召回实验效果</p>
<table><tbody><tr><td>
<p><strong>微视端Push AB效果</strong></p>
</td>
<td>
<p><strong>+Triplet</strong></p>
</td>
</tr><tr><td>
<p>PCTR点击率</p>
</td>
<td>
<p>+0.68%</p>
</td>
</tr><tr><td>
<p>UCTR点击率</p>
</td>
<td>
<p>+0.40%</p>
</td>
</tr><tr><td>
<p>人均push有启活跃天</p>
</td>
<td>
<p>+0.88%</p>
</td>
</tr><tr><td>
<p>人均push首启活跃天</p>
</td>
<td>
<p>+0.55%</p>
</td>
</tr></tbody></table><p> </p>
<h1>五、    未来工作与展望</h1>
<ul><li>我们基于标签名称一致来判定跨业务标签是否为同一个标签，这会在标签映射歧义和映射覆盖率上有一些损失，后续可以考虑和画像中台<a href="https://doc.weixin.qq.com/doc/w3_ACYAmQa_AFUzYkEyW0kR3e5edrHga?scode=AJEAIQdfAAoEhRVeixANgALgZbACo">UniTag</a>进行合作，得到更准确的跨业务标签映射结果</li>
<li>目前我们仅仅融入了看点和两端的用户画像，之后将会尝试融入更多的画像，并在更多的场景进行落地实验。</li>
<li>可以通过进一步挖掘如挖掘attention机制，增强U-U关系与U-I关系，对embedding的融合采用attention加权求和。</li>
<li>短视频推荐对用户短期兴趣要求高，我们也在联合画像工程团队、画像中台Uni-Graph团队以及 Turing团队进行实时GNN建设，期待能够收获更多收益。</li>
</ul><h1>六、鸣谢</h1>
<p>感谢业务侧@sprizhang、@haijunliu等合作伙伴在方案适配及推广落地上的大力配合。感谢@yuchenglin、@danikachen、@timchang等小伙伴、老师对算法方案实施提出的一些建设性建议。感谢画像中台@raycheng、@boristan、@ganggangliu、@mochigao等伙伴对中台数据的支持。感谢团队@dylanhong、@bevisjiang、@felixzhuo、@gavinzli等小伙伴和老板们的给力支持。</p>
<p>本文中的算法实现基于公司开源图框架Platodeep2进行开发，感谢PlatoDeep2团队的@healyhuang、@cedricsun等各位大佬的支持指导</p>
<p> </p>
<p>参考资料：</p>
<ol><li> 人以群分---GNN助力推荐系统：[内部链接已移除]</li>
<li> 【KDD 2021】针对冷启动问题的GNN模型 ：[内部或本地链接已移除]</li>
<li> Hamilton, Will, Zhitao Ying, and Jure Leskovec. "Inductive representation learning on large graphs." Advances in neural information processing systems 30 (2017).</li>
<li> 图技术探索与应用（一）：语义多视角图对比学习方法与应用[内部或本地链接已移除]</li>
<li> 基于UniGraph的GNN探索与实践：画像挖掘场景 [内部或本地链接已移除]</li>
<li> Dong Y, Chawla N V, Swami A. metapath2vec: Scalable representation learning for heterogeneous networks[C]//Proceedings of the 23rd ACM SIGKDD international conference on knowledge discovery and data mining. 2017: 135-144.</li>
</ol><p> </p> 
{% endraw %}
