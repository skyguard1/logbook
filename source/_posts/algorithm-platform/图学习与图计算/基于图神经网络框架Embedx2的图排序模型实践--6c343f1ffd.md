---
title: "基于图神经网络框架Embedx2的图排序模型实践"
date: 2022-04-17 10:51:29
categories:
  - 算法平台
  - 图学习与内容理解
---

{% raw %}

<h2>1. 前言</h2>
<p>长期以来，排序模型主要依赖用户画像和内容画像的特征，对user-item点击概率进行建模。但是在的场景内，我们除了拥有看一看内用户-公众号点击关系，用户-视频播放关系等，还拥有很多可以刻画用户喜好的<strong>user-item</strong>关系的<strong>异构信息</strong>。这些连接关系的来源和分布差异较大，难以和现有的画像内容在同一个深度网络中共同建模。因此我们考虑在排序模型的基础上融合图模型去建模这些异构关系。下面我们将首先分别简要介绍CTR模型和GCN模型，其次介绍两阶段模型，最后介绍end2end建模框架和上线方案。 </p>
<p>本文涉及的工作均在Embedx2基础上实现，并由deepx2提供排序侧相关支持。Embedx2是算法平台组基于C++开发的分布式表示学习系统（[内部或本地链接已移除]）能够支持在<strong>十亿级别节点、千亿级别边</strong>上训练模图型。Deepx2（[内部或本地链接已移除]）是看一看团队使用的排序框架，能够支持<strong>千亿特征</strong>的大规模稀疏模型。我们的系统代码都是完全开源的。</p>
<p>本文工作由trumpyu, yuanhangzou, vinceywang, kimmyzhang, hillsu共同完成。</p>
<h2>2. 深度CTR模型简介</h2>
<p>在推荐系统中，点击率预估是一个重要的任务。CTR预估任务会根据user信息(如性别、年龄、地域、系统中的行为等)，item信息（如内容分类，标签等）和context信息（如网络、设备、时间等）来预测user的CTR。</p>
<p>典型的深度CTR模型结构为：输入、特征嵌入（feature embedding）、特征提取、输出</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/31b710073bec0d36072e.png"/></p>
<p>目前业界常用的点击模型有deepfm, deepfm2, xdeepfm, autoint, fgcnn等。其中deepfm2是当前最强的基线模型，在看一看的业务数据集上相对当前state of art的模型auc差距不到千分之一，但是训练速度上要快10倍以上。 综合性能和效果，我们选择了deepfm2作为我们后续实验的基线模型。deepfm2模型如下图所示</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a2e0452dd05b0e89d316.png"/></p>
<p></p>
<p>具体模型的介绍和业务数据实验可以参考本组前期发表的km文章——深度学习在CTR中的应用。</p>
<h2>3. GCN模型简介</h2>
<p>GCN模型是应用于图数据上的深度神经网络模型，可以自动学习节点、边、子图的低维稠密表示。目前的GCN模型基本都采用了邻居聚合的策略，而一次邻居聚合可以拆解成一次Aggregate操作（邻居特征聚合）和一次Combine操作（邻居特征与当前节点特征的融合）。选择不同的Aggregate和Combine操作就构成了不同的GCN算法。如Aggregate采用mean, combine采用concat就是graphsage算法。关于GNN，后续Embedx2会有更详细的km文章进行介绍。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f1d9fc412f140c25010e.png"/></p>
<h2>4. 传统方法——两阶段</h2>
<p>传统方法一般是分阶段，第一阶段构建图模型生成生成节点embedding, 第二阶段加入到CTR网络中进行建模。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/90d107f9ab1a166474e6.png"/></p>
<p></p>
<p>这种方法存在着很大的缺陷，第一，<strong>训练不同步</strong>，CTR模型通常会按半小时乃至分钟级别更新，而graph模型通常按天更新， 第二，<strong>学习目标不一致</strong>，graph侧的embedding通常只考虑了节点之间的相关性，和点击的有监督目标之间存在gap。离线测试也证明了我们的猜想，embedding加入后对CTR网络的影响非常小。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a8979d675a8907304a3f.png"/></p>
<h2>5. 我们的方法——end2end训练 </h2>
<p>针对两阶段方法的缺点，我们提出了一种end2end训练的GraphCTR算法框架, 如下图所示</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b8d624cdeec8366ae743.png"/></p>
<p> </p>
<p>与两阶段建模不同，这里采用了end2end的训练策略。通过graph模型和CTR模型的联合训练，可以有效克服两阶段模型的训练不同步和学习目标不一致的缺点。</p>
<p>框架主要分成两部分, Graph侧的辅助任务和CTR主任务。</p>
<p>Graph侧为辅助任务，通常采用无监督的图模型，主要使用图卷积网络来学习节点之间的相关性。CTR为主任务，主要为点击目标服务。图中的异构信息，会以图卷积网络得到的user, item表示的形式实时加入到CTR网络中, 共同学习。经由CTR的标记信息，还可以将标注节点的信息传播到周围的无标注节点，这样对冷门的长尾节点更加友好。graph模型和CTR模型共享feature层的embedding, 这样有助于保证embedding空间的一致性，同时也节省了参数的存储空间。</p>
<p> </p>
<p>目前以该套算法框架为基础，已在看一看排序业务中多次上线，取得显著效果。下面以前期上线的GerlDfm模型为例，介绍具体应用。</p>
<h3><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/45e836a55d12fef18d29.png"/></h3>
<p>首先，我们以点击关系构为基础建了二部图。</p>
<p>对于Graph侧，我们采用了基于随机游走的经典无监督算法，并融合了one-hop和two hop Graph Learning用来建模User和Item的图表示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1149112dc3a767856730.png"/></p>
<p>对于CTR侧，我们使用了Deepfm2模型。User和Item的图表示经过交叉后会在顶层和CTR模型融合，这样可以有效避免user bias。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/52fec1d64658884bf463.png"/></p>
<p>离线实验结果如下图，相对基线模型提升明显，一般离线千分之一的提升线上都可以看到效果。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/968eb42aef94b1255e61.png"/></p>
<p>针对上线，考虑到Embedx2中graph server迁移到线上涉及到的工程成本和图卷积网络增加的在线耗时，我们采用了离线缓存user, item图表示（由Deepx2支持），只上线CTR模型部分的方法。由于采用了缓存的方式，导致模型冷启动时，user,item图表示经常会缺失，我们采用了graph pretraining的策略来缓解这个问题。</p>
<h2>6. 小结</h2>
<p>近年来，图神经网络蓬勃发展，在推荐领域也有了不少应用。但是这些应用大多局限于召回和特征的使用上，本文我们聚焦图排序模型介绍了初期取得一些进展，包括首创的GraphCTR算法框架和相关具体实践。后续我们会有更多的系列文章介绍图模型在排序任务中的应用, 如graph pretraining, 长短期兴趣的建模，深度图网络的建模等。也欢迎各位讨论与合作。</p>
<h2>References</h2>
<ol><li>
<p>Embedx2: [内部或本地链接已移除]</p>
</li>
<li>
<p>Deepx2: [内部或本地链接已移除]</p>
</li>
<li>
<p>GraphSAGE: Inductive Representation Learning on Large Graphs</p>
</li>
<li>
<p>Graph Attention Networks</p>
</li>
<li>
<p>深度学习在CTR中的应用</p>
</li>
<li>
<p>图神经网络框架Embedx2中随机游走策略介绍与实现</p>
</li>
<li>大规模embedding应用套件: [内部或本地链接已移除]</li>
</ol> 
{% endraw %}
