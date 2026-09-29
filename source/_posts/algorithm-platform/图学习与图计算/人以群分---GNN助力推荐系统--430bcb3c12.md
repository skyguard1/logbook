---
title: "人以群分---GNN助力推荐系统"
date: 2022-04-14 18:59:38
categories:
  - 算法平台
  - 图学习与图计算
---

{% raw %}

<div>
<p>本文由nickgu和joelzheng共同书写完成。</p>
</div>
<h2>一、背景介绍</h2>
<p>推荐系统无论是在工业界还是学术界都是非常火热，推荐系统根据用户和物品的特征来评估用户对物品的偏好，而如何从众多信息中抽取二者有用的特征，并对用户的喜好进行建模是推荐系统的主要挑战。这些信息包括用户-物品行为交互信息，用户-用户交互信息，项目属性信息等，这些信息大多可以由图结构表示，传统的神经网络方法是无法直接处理这样的数据的，需要对数据进行一定程度的转换。而使用图相关的算法可以直接处理这样的数据，充分挖掘高阶的节点交互信息，助力推荐系统；而且有别于其余的产品，这个产品本身就是建立在一个庞大的社交关系网络之上，所以从中孵化出来的各个新业务都带有强大的社交属性，从庞大的社交网络数据中抽取有用的信息和个人兴趣的融合，改善推荐结果，是一件非常重要并且很有挑战的事情。</p>
<p>本文将详细介绍笔者团队如何将现有图算法进行优化并在视频号直播推荐系统(euler)召回模块上落地、以及利用丰富的社交关系解决推荐系统中冷启动问题的过程做一个详细的介绍。主要内容包括：</p>
<ol><li>将业界已有的成熟图算法方案（metapath2vec和graphsage）在<strong>视频号直播场景上实现并上线</strong>，对视频号直播推荐系统(euler)的线上召回算法做一个补充。</li>
<li>针对直播场景作为一个新入口，新用户较多，提出了一个改善冷启动问题的GNN模型，相关工作被<strong>kdd 2021接收</strong>并成功在视频号直播业务召回模块中上线使用，在新用户指标上<strong>取得2%的提升</strong>。</li>
<li>上述的方案全部已经跟随PlatoDeep平台一起开源。</li>
</ol><h2>二、业界成熟方案使用</h2>
<p>    在推荐系统领域，使用graph embedding的方案作为召回或者是精排特征的方案已经比较普遍了。基于我们过去在大规模图网络上生成节点embedding的工作经验，我们首先的想法就是构造多源异构网络，使用基于异构图的图嵌入算法，metapath2vec来得到用户和物品的embedding向量。</p>
<h3>2.1 metapath2vec的方案</h3>
<p>Metapath2vec算法是node2vec算法在异构图上的实现，通过带权随机游走得到异构图的节点序列，用一个滑动窗口来构建正样本，窗口内的节点embedding尽可能相似，因此两个节点，只要它们的多阶邻居整体相近，即使不直接相连，它们的Embedding向量也比较相似。我们选择直接构造异构图来构造网络，一方面可以通过构造不同的metapath来丰富训练语料，另一方面又可以将我们产出的特征属性作为sideinfo加入到生成emb的过程中来，能够包含了更丰富的用户信息和用户行为信息，使得最终的Embedding向量更加有效。过程如下图所示，对于直播场景，<strong>Graph Embedding能有效学习到主播与主播之间、用户与用户之间及用户与主播之间的多阶关系，可以增强推荐主播的同质性和同构性，提升直播推荐的覆盖度和多样性</strong>。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d6decd5aa67c496b3389.png"/></p>
<p>通过metapath2vec产出用户embedding和主播embeding之后，我们利用这份数据产出一路召回上线到推荐系统上。因为直播场景是一个时效性很强的场景，每时每刻正在开播的直播间是动态变化的，所以我们借用高性能特征检索SimSvr的能力，将正在直播的直播间的emb导入simsvr中，利用用户的embedding动态去查询top N的主播。</p>
<h3><br/> 2.2 graphsage的使用</h3>
<p>    Metapath2vec的方法是一种直推式的图算法（Transductive），即在固定的图上直接学习每个节点的Embedding，每次学习只考虑当前数据，更多的是考虑局部拓扑结构的学习，这种模式的可扩展性比较低，算法的上界有限。针对这个问题，我们开始考虑使用图卷积算法--- GraphSAGE，相比较于原始的GCN算法，GraphSAGE引入了邻居抽样机制，在效率上有了极大的提升，解决了图卷积算法在工业落地的阻碍，同时提出了图上学习的新模式：归纳(inductive)学习，即学习在图上生成节点Embedding的方法而不是直接学习节点的Embedding。即通过学习聚合节点邻居生成节点Embedding的函数的方式，将GCN扩展成归纳学习任务。我们借助platoDeep的平台能力，在视频号直播全量的数据上实现了GraphSAGE算法，算法原理已经有很多文章详细介绍过了，这里就不再赘述了，主要介绍一下我们做的三个优化：</p>
<p>1. 带权重的边<br/>原始GraphSAGE并没有考虑带权图，采用随机采样的方式来采样邻居节点并将邻居节点的特征等权重的聚合在中心节点上，对于邻居节点比较多的节点（行为较多的用户），会导致有用的信息稀释，产生过平滑的现象，因此我们在<strong>输入图的边上加上权重（观看时长）</strong>，采样的时候会给观看时长更长的直播间更大的权重。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c12bbfa1a3971dca1a04.jpg"/></p>
<p>2.采用attention的聚合函数<br/>普通的GraphSAGE网络在聚合邻居信息时主要使用min-pooling，max-pooling，average，LSTM这四种方式，对邻居信息的聚合能力较弱，因此我们希望通过加入自注意力机制，来更好的聚合邻居信息。并且不同的邻居节点的在聚合的时候给到不同的权重，这是符合常识的。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b4a59713cce7c9ecb8f1.png"/></p>
<p>对比原始GraphSAGE，加入了注意力机制，邻居节点的聚合与采样顺序是无关的，并且计算可以采用并行的方式同时计算，增加的计算时间也是可以接受的。</p>
<p>3.推理时裁剪边<br/>GraphSAGE训练和推理的时候都是采用采样边的形式构成数据，在训练的过程中是比较合理的，但是在推理的时候，会因为采样节点的随机性，使得输出的emb不稳定。为了解决这个问题，<strong>我们在推理的时候对图进行裁剪，只保留了每个节点最大的TopK权重边，提升局部结构的稳定性，适当屏蔽由于抽样带来一些无用信息的干扰</strong>。</p>
<p>除此之外，原有的graphsage采用random walk+一阶卷积的方式来聚合高阶邻居信息，而我们的图更为稠密，图的直径更小，所以我们改为直接sample真实的邻居+二阶卷积的方式来聚合高阶邻居信息，在过平滑和高阶信息聚合中找到一个平衡。</p>
<h2>三、针对冷启动问题的GNN模型</h2>
<p>视频号的直播业务是一个相对较新的业务，并且由于的其余业务和视频号短视频业务的增长，会持续给直播业务带来较大数量的新用户，而对于这些新用户来说，由于缺乏行为数据，想要为其学习一个高质量的Embedding是比较困难的。基于此，为了解决新用户的召回问题，<strong>我们将推荐系统中的冷启动问题视作数据缺失问题，即缺乏用户的行为数据，设计了一种多视角的、去噪的、图编解码训练架构，来适应冷启动情况，产出高质量的 Embedding</strong>。下面详细介绍一下我们的方法：</p>
<h3>3.1 多路特征提取</h3>
<p>对于每一个User或者 Item，我们会为其设计多路特征。由此一来，<strong>即使在冷启动场景下缺乏某路特征，也能靠其他路的特征进行补充</strong>。对于每一路的特征，我们使用基于 metapath 的图卷积来提取，再将多路特征进行融合，形成信息更为全面丰富的 Embedding。基于 metapath 的图卷积基本流程为：1）采样：从中心节点出发，沿着设计好的 metapath 进行采样；2）聚合：沿着采样的反方向，进行特征聚合，一直到中心节点为止；3）不同层之间的特征拼接：将图卷积过程得到的不同层之间的特征进行拼接。结构如图1所示：</p>
<h3>3.2 Dropout 机制以适应冷启情况</h3>
<p>在 Inference 阶段，对于新用户来说，用户行为数据是缺失的，而在 Training阶段，行为数据均是完整的。如果我们继续采用常规的训练方式，会导致 Training 和 Inference 阶段产生 Gap。为了缓解这一问题，我们借鉴了去噪自编码器 (DAE, Denoising Autoencoder) 的核心思想：从受损的原始数据编码、解码之后还能恢复出原始数据，这样的特征质量更高、更为鲁棒。因此，<strong>我们在训练阶段，编码的时候会以一定概率 Mask 掉基于用户行为数据的那一路特征，而在解码的时候则要求重构出完整的基于不同类型的相似度构造的图，以此适应冷启动情况</strong>。见图1编码器中的 Dropout 机制。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1ff8fedb3e1ee5596ff8.png"/></p>
<p>图1 多视角图编码架构</p>
<h3>3.3 图解码器</h3>
<p>上述描述的过程我们视为图信息的编码过程。<strong>为了进一步增强相似用户或者Item之间的特征相似度，提高特征质量，我们除去要求模型在原有的User-Item图上构造的loss最优，还要求提取到的特征信息能够重构出对应的 User-User 图或者 Item-Item 图</strong>。以 Item 侧为例，在输入阶段，我们利用 Item-Tag-Item进行特征聚合，我们认为具有相同类别的 Item 之间是相似的。基于此，我们可以构造一个基于 Tag 连接的 Item-Item 图。而我们的解码目标，就是这些基于不同类型的相似度构造的图。构图及解码过程如图2所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7cdcb5d3cbb1f605f1c5.png"/></p>
<p>图2 图编解码架构 (Item侧)</p>
<p>这里在构图阶段有几个小 trick：</p>
<ul><li>对于不同类型的中间节点，我们会设置不同的阈值。如 User-(Item)-User、Item-(User)-Item，我们将阈值设置成3：即至少有3个共同邻居，这两个节点才相连。阈值可根据具体场景进行调节；</li>
<li>在Batch中动态构造。如上所述，我们构图时其实是基于二阶相似度，即拥有多少个共同的邻居来进行构造的。假设我们有 N 个节点，要构造出对应的图，计算复杂度为 O(N<sup>2</sup>)。当N很大时，计算代价是非常大的。由于我们是基于Batch进行训练的，因此，只需要在Batch中来动态构造即可。假设当前Batch中有 n 个节点，计算复杂度为 O(n<sup>2</sup>)，则整体的复杂度为 O(N/n * n<sup>2</sup> )=O(N*n), n&lt;&lt;N；</li>
<li>为了保证构造的User-User 图或者 Item-Item 图足够稠密，我们首先采样中间节点，再基于中间节点，去采样目标节点，以此来保证构造图的稠密。例如 Item-(Tag)-Item，我们首先采样中间节点 Tag，再基于 Tag 节点，根据Tag-&gt;Item，采样出对应的 Item 节点，以此来保证 Item-Item 图的稠密。</li>
</ul><h3>3.4 多任务学习</h3>
<p>User侧和Item侧均有多个图的重构任务。若手动地为每个任务调整权重，则需要额外增加大量的调参工作。因此，我们希望多个任务之间能通过可学习的方式自动调节。<strong>这里采用的方案为 Bayesian Task Weight Learner，为每个重构任务赋予一个可学习的权重，使其根据网络的训练自动调节，达到平衡，而无需手动调整</strong>。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b57c99b4808a178503b2.png"/></p>
<p>图3 贝叶斯权重学习器</p>
<h3>3.5 模型整体框架</h3>
<p>模型的整体架构如图4所示。具体来说，我们首先为每个 User/Item 设计多路特征聚合，每路特征采用独立的图编码器进行特征提取，再融合成信息更为全面丰富的 Embedding。为了适应冷启动情况，在训练阶段，我们在聚合各路信息的时候会以一定概率 Mask 掉基于用户行为数据的那一路信息，而在解码的时候则要求重构出完整的基于不同类型的相似度构造的图。最后采用 Bayesian Task Weight Learner 为多个重构任务赋予可学习的权重。在重构损失和 U-I 损失的联合优化中，图网络和Embedding Table不断更新，直至收敛，最终产出高质量 Embedding。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/85fc4458d0b5dbb82139.png"/></p>
<p>图4 整体模型架构图</p>
<h3>3.6 模型效果</h3>
<ul><li>公开数据集</li>
</ul><p>我们在三个公开数据集上进行实验，将测试情况分成四类（User冷启动、Item冷启动、User&amp;Item 冷启动及非冷启情况），与当前的 SOTA 模型进行对比，在MAE、RMSE及NDCG三个指标上均有显著提高。此外，<strong>我们将相关工作撰写成论文，并被数据挖掘顶会SIGKDD接收</strong>。论文链接：<a href="https://dl.acm.org/doi/pdf/10.1145/3447548.3467427">https://dl.acm.org/doi/pdf/10.1145/3447548.3467427</a></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7b7d674d454fc8b1947b.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/bc1567892b9439bbae88.png"/></p>
<p>图5 公开数据集算法效果</p>
<ul><li>业务数据集</li>
</ul><p>算法在真实业务场景数据集上同样取得了最佳的效果，具体如图5所示。以AUC作为评估指标，除去对比SOTA方法的同时，也进行了消解实验，探究模型中每一模块的作用。效果如图5所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b53add914b0861ec61c1.png"/></p>
<p>图6 业务数据集算法效果</p>
<h2>四、在线召回方案</h2>
<p>我们借助<strong>深度学习图计算引擎PlatoDeep</strong>的能力，在视频号直播场景（百亿级边、亿级节点）上实现了我们的算法，并最终采用两种方式上线了召回。其中使用u2i的方式对没有行为数据的新用户补充召回，并且使用u2i2i的方式得到实时性更强的召回内容，对线上召回进行补充。<strong>并最终在线上A/B test中新用户各项指标得到2%的提升</strong>。</p>
<h2>五、总结和感谢</h2>
<p>数据中心因为拥有Plato+PlatoDeep两大图计算平台，所以我们也一直致力于能将图算法和GNN在实际业务中去落地，本文介绍了笔者团队在推荐系统应用中推进图算法技术方案的落地过程，目前在新用户召回上取得了一定的成果，后续我们将会继续寻找GNN和推荐系统的结合，往更实时，特征规模更大、更通用的方向推进。</p>
<p>感谢healyhuang、cedricsun、powergao设计并实现的PlatoDeep，让GNN落地成为了可能，感谢irvinliu、crazyrong、windsonliu在视频号直播召回实验上的帮助，感谢jerrycgsong、danieslin、goonerding、joelzheng一起打磨GNN的算法，感谢cc、paul、chris、noah等领导的支持，使得工作能够得以完成。</p>
<h2>参考资料</h2>
<p>kdd2021 论文：<a href="https://dl.acm.org/doi/pdf/10.1145/3447548.3467427">https://dl.acm.org/doi/pdf/10.1145/3447548.3467427<br/></a>PlatoDeep开源地址：[内部或本地链接已移除]笛卡尔平台：[内部或本地链接已移除]<br/>图计算OTeam: [内部或本地链接已移除]<br/>simsvr：[内部或本地链接已移除]<a href="https://arxiv.org/pdf/1706.02216.pdf"></a>GraphSAGE: <a href="https://arxiv.org/pdf/1706.02216.pdf">https://arxiv.org/pdf/1706.02216.pdf</a></p> 
{% endraw %}
