---
title: "基于UniGraph的GNN探索与实践：画像中台画像挖掘场景"
date: 2022-04-22 21:39:48
categories:
  - deep-learning
---

{% raw %}

<div>
<div>
<div>
<h1>UniGraph：数据资产图谱</h1>
</div>
</div>
<div>
<div>
<div>
<p>在过去的几年中，深度神经网络（Deep Neural Networks, DNN）的兴起与应用成功推动了模式识别和数据挖掘的研究。许多曾经严重依赖于手工提取特征的机器学习任务（如目标检测、机器翻译和语音识别），如今都已被各种端到端的深度学习范式彻底改变了，例如：CNN、LSTM和Transformer。</p>
</div>
</div>
</div>
<div>
<div>
<p>虽然深度神经网络（DNN）被证明在建模欧式空间信息上非常有效，但是在实际应用场景中，大量数据是从非欧式空间（e.g., 社交网络、生物网络、交通网络、能源网络等等）生成的，这些数据没法无损的映射到欧式空间，使得传统的深度学习方法在处理类似的数据上的表现难以使人满意。为了更好地从非欧式空间中学习数据特征，研究者们通过引入图论中抽象意义上的图（Graph）来表示非欧几里得结构化数据，并利用图神经网络（Graph Neural Networks, GNN）来对图数据进行处理，以深入发掘其特征和规律。沿着这个思路诞生了一系列基于图的算法，例如node2vec, metapath2vec, gcn, graphsage, gat等，这类算法通过更进一步地提取图上的结构化信息，弥补了传统DNN算法的不足，在搜广推增长、反作弊等众多领域取得了非常不错的成绩。</p>
</div>
</div>
<div>
<div>
<p>大数据平台沉淀了丰富的跨业务数据资产（如行为流水、兴趣画像等），通过清洗梳理这些数据资产，进行必要的数据标准化之后将它们组织成跨域超级异构数据图谱（UniGraph）的形式，以期望借助图中节点之间不同种类的关系表达节点之间的相似或者依赖关系，更好地建模数据的真实情况，从而服务于搜索、广告、推荐、PUSH、反作弊、画像挖掘等众多业务场景。</p>
</div>
</div>
<div>
<div>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9cda02989732d7987165.png"/></p>
</div>
</div>
<div>
<div>
<p><strong>经过长时间的资产建设，目前UniGraph包含了设备、视频、作者、标签等在内的10+种实体类型，数十种节点和节点之间的关系类型，总共包含数十亿的节点，千亿级别的边。作为规模最大、数据质量最高的跨端异质数据图谱，UniGraph在支持业务方提升业务指标上发挥了重要的作用</strong>。例如，基于UniGraph中的多端视频流水，ovbu @timchang，@albertxwang，@yuchenglin，@starmieli等同学开发的跨端视频图表征服务目前接入了微视、小世界、QB等多个业务线的多个场景推荐召回。</p>
</div>
</div>
<div>
<div>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/7e7b3576f3e85cf12a4c.png"/></p>
</div>
</div>
<div>
<div>
<div>
<div>
<div>
<div>
<h1>ResGNN：基于GNN的端对端画像挖掘新范式</h1>
</div>
</div>
<div>
<div>
<p>致力于打通多源数据构建多实体关系，全面准确刻画用户/内容，挖掘众多的用户画像。目前画像挖掘这一领域的普遍情况是：对于某一个特定的画像挖掘任务，经过算法同学不断地添加更丰富的特征以及不断地对模型（通常是树模型或者DNN）进行迭代优化，挖掘模型已经达到了较高的预测准确率，一时难以继续提升。正因为如此，在画像挖掘模型中引入传统DNN模型不能很好建模的非欧式空间的图谱结构化信息是一个非常值得尝试的方向。</p>
</div>
</div>
<div>
<div>
<p>这里，我们立足于UniGraph这一最大的跨域异质数据图谱：1）提出了一套基于GNN的画像挖掘新范式，升级传统画像挖掘流程，<strong>使得画像挖掘同学只需要对原有DNN模型进行微小的修改就能融入非欧式空间的的结构化信息，取得至少不比原模型差的准确率</strong>；2）使用我们提出的画像挖掘新范式在某一个具体的画像挖掘任务上取得了比原模型更好的效果，从而验证我们提出的方法的有效性；</p>
</div>
</div>
<p>为此，我们借鉴了在CV领域大获成功的<a href="https://arxiv.org/abs/1512.03385">ResNet</a>的经典网络架构，提出一种基于GNN的端对端画像挖掘新范式，简称ResGNN框架，如下：</p>
</div>
</div>
</div>
</div>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/327897459d3210452146.png"/></p>
<p><br/></p>
<p>具体而言，原模型的输入特征（即图中的Input Feature: x）既作为原始特征输入DNN，也作为Graph（既可以是异构图也可以是同构图）中的节点属性特征用于GNN建模。我们通过GNN算法提取Graph中的结构化信息（即GNN(G,x)部分），再拼接原始的特征值作为新的输入特征输入进原有的模型，最终通过原有模型输出最终的预测结果。整体框架可以简单表示成如下公式：</p>
<p>y = ResGNN( G , x )= OriginalModel( CONCAT( x , GNN( G , x ) )</p>
<div>
<div>
<p>由于ResGNN框架结构简单，不需要对原模型做太多改动，所以十分方便算法同学快速搭建进行实验与应用。其次，ResGNN框架对原模型结构并没有进行修改，且是在保证了原输入特征不变的情况下融合了GNN算法提取的图结构信息。ResGNN将两部分模型（原模型和GNN模型）结合在一起进行端对端训练，相当于在原有模型的基础上额外增加了GNN提取到的结构化信息，这样的特性保证了最终模型可以获得大于等于原模型的效果。换句话说，即使GNN算法并没有学习到对目标任务有用的图结构信息，模型也能通过图中的左侧通路（即走原模型的训练流程）完成训练，确保整体模型效果至少等于原模型的效果。</p>
<div>
<div>
<h1>基于ResGNN的学历预测</h1>
</div>
</div>
<div>
<div>
<p>通过在学历预测任务上应用ResGNN框架，我们显著的提升了学历预测的准确率，验证了ResGNN框架的有效性。</p>
</div>
</div>
</div>
</div>
<div>
<div>
<h2>学历预测任务介绍</h2>
</div>
</div>
<p>的学历标签主要分为高中及以下，大专，本科，硕士及以上4个类别，每种类别具体的含义如下：</p>
<ul><li>
<p>高中及以下：含小学、初中、高中、职高、中专、技校等</p>
</li>
<li>
<p>大专：含全日制大专、成人高等教育（大专学历）等</p>
</li>
<li>
<p>本科：含全日制本科、专升本、成人高等教育（本科学历）等</p>
</li>
<li>
<p>硕士及以上：含全日制硕士、非全日制硕士、全日制博士、在职博士等</p>
</li>
</ul><div>
<div>
<p>经过数据分析发现16-25岁人群特征多、学历变化较快，所以画像中台将人群分为16-25岁和26-35岁两个年龄段分别进行训练，两类人群所使用的的DNN模型网络结构是相同的，模型网络结构如下：</p>
</div>
</div>
<div>
<div>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9c13b9a35114921bbc2b.png"/></p>
</div>
</div>
<div>
<div>
<h2>ResGNN学历预测</h2>
</div>
</div>
<p>我们将ResGNN的最佳实现分别应用于16-25年龄组和26-35年龄组得到如下结果，在16-25年龄组中从72.26%提升至75.71%（绝对值提升+3.45%），在26-35年龄组中从60.53%提升至63.08%（绝对值提升+2.55%），具体数据如下：</p>
<table><tbody><tr><td><strong>模型</strong></td>
<td><strong>16-25年龄组准确率</strong></td>
<td><strong>26-35年龄组准确率</strong></td>
</tr><tr><td>Baseline</td>
<td>72.26%<br/></td>
<td>60.53%<br/></td>
</tr><tr><td>ResGNN<br/></td>
<td>75.71%<br/></td>
<td>63.08%<br/></td>
</tr><tr><td><strong>准确率提升（绝对值）</strong></td>
<td><strong>+3.45%</strong><br/></td>
<td><strong>+2.55%</strong><br/></td>
</tr></tbody></table><p>目前该结果已在中台落地推全，具体推全结果可以参考学历V3版本介绍-Q36口径 。<strong></strong></p>
<div>
<p>注：算法同学后续再Baseline的基础上添加了一系列新特征之后，16-25岁年龄段的Baseline模型的准确率提升到了76.32%，在此基础上的ResGNN进一步将模型准确率提升到79.26%（准确率+2.94%）。更进一步证明了ResGNN的有效性。</p>
</div>
<div>
<div>
<p>为了更全面地分析ResGNN每一个模块的作用，我们对16—25岁年龄段的用户做了比较详细的对比实验分析，包括：1）Graph选择对比；2）GNN模型选择对比；3）消融实验对比。接下来我们详细介绍这几部分。</p>
</div>
</div>
<div>
<div>
<h2>对比实验分析</h2>
</div>
</div>
<h3>图选择对比实验</h3>
<div>
<div>
<div>
<div>
<p>不同Graph包含的结构信息对于具体的画像挖掘任务的作用是不一样的。为了对比不同的Graph包含的结构信息对学历预测这一任务准确度的影响，我们对比了：某图一，某图二，PNode信息，三种类型的Graph，详细的试验结果如下：</p>
</div>
</div>
</div>
</div>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p><strong>图类型</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>准确率</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>绝对值提升</strong></p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>Baseline</p>
</td>
<td colspan="1" rowspan="1">
<p>72.26%</p>
</td>
<td colspan="1" rowspan="1">
<p>-</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<div>
<div>
<p>ResGNN w/ 某图一</p>
</div>
</div>
</td>
<td colspan="1" rowspan="1">
<p>72.92%</p>
</td>
<td colspan="1" rowspan="1">
<p>+0.66%</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>ResGNN w/ 某图二</p>
</td>
<td colspan="1" rowspan="1">
<p>71.45%</p>
</td>
<td colspan="1" rowspan="1">
<p>-0.81%</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p><strong>ResGNN w/</strong> <strong>PNode</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>75.71%</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>+3.45%</strong></p>
</td>
</tr></tbody></table><div>
<div>
<p>从实验结果可以看出，使用PNode信息所构建的Graph所包含的信息对于学历预测这一任务所带来的的提升最显著。<br/></p>
<div>
<div>
<h3>模型选型对比实验</h3>
</div>
</div>
</div>
</div>
<div>
<div>
<p>工业界常见的GNN模型有GraphSage和GAT，为了对比不同的GNN模型对学历预测任务准确率的影响，基于PNode信息构建的图，我们对比了GraphSage（mean pooling）和GAT两种模型的效果，实验结果如下：</p>
</div>
</div>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p><strong>模型</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>准确率</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>绝对值提升</strong></p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>Baseline<br/></p>
</td>
<td colspan="1" rowspan="1">
<p>72.26%</p>
</td>
<td colspan="1" rowspan="1">
<p>-</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>ResGNN w/ GraphSage<br/></p>
</td>
<td colspan="1" rowspan="1">
<p>73.75%</p>
</td>
<td colspan="1" rowspan="1">
<p>+1.49%</p>
</td>
</tr><tr><td>
<p><strong>ResGNN w/ GAT</strong></p>
</td>
<td>
<p><strong>75.71%</strong><br/></p>
</td>
<td>
<p><strong>+3.45%</strong><br/></p>
</td>
</tr></tbody></table><div>
<div>
<p>实验结果表明，带有Attention的GAT模型能通过attention机制在聚合图信息方面更能有的放矢的挖掘到有用的邻居信息，取得了更好的效果。</p>
</div>
</div>
<h3>消融实验</h3>
<p>由于加入了PNode图的过程中不可避免的带入了PNode id，为了排除PNode id引入的额外信息的影响，我们做了一个简单的消融实验以验证GNN结构能有效地抽取图结构特征，从而证明ResGNN框架结构的有效性。于是我们将PNode特征作为user特征加入到原模型当中作为multi-hot 特征，做了如下对比实验。</p>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p><strong>模型</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>准确率</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>绝对值提升</strong></p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>Baseline</p>
</td>
<td colspan="1" rowspan="1">
<p>72.26%</p>
</td>
<td colspan="1" rowspan="1">
<p>-</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p>baseline w/ PNode特征</p>
</td>
<td colspan="1" rowspan="1">
<p>72.56%</p>
</td>
<td colspan="1" rowspan="1">
<p>+0.30%</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p><strong>Res GNN w/ PNode</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>75.71%</strong></p>
</td>
<td colspan="1" rowspan="1">
<p><strong>+3.45%</strong></p>
</td>
</tr></tbody></table><p>从实验结果可以看出，在Baseline的特征上加入PNode的特征后，只取得了略优于Baselin模型的效果。但是使用了ResGNN的网络架构，却显著提升了模型的准确率。也就是说，相较于直接将异构图中其他的节点特征作为原模型的输入特征，ResGNN模型能更好的抽取图结构特征得到更有意义的信息，也更进一步地证明了ResGNN的有效性。</p>
<div>
<div>
<h1>总结</h1>
</div>
</div>
<div>
<div>
<div>
<div>
<p>立足于UniGraph这一规模最大、数据质量最高的跨端异质数据图谱，我们提出了基于GNN的画像挖掘新范式ResGNN，基于该范式算法同学只需要对自己原有的Baseline模型稍加改动就能融入图数据的结构信息，取得更好的预测准确率。同时，我们也将提出的ResGNN画像挖掘新范式应用于画像中台的学历画像预测任务中，显著地提升了该任务的预测准确率，从而也实际验证了ResGNN框架的有效性。</p>
<p>除了画像挖掘，UniGraph在支持搜索、广告、推荐、PUSH、反作弊等业务场景上同样可以发挥巨大的作用，如果你希望利用丰富的数据建模非欧式空间中的结构化信息，以此提升业务指标，那么UniGraph一定是你不可错过的宝贵资源。欢迎你随时联系@boristan，@mochigao，@answerzhong了解UniGraph以及已有的成功落地经验。</p>
</div>
</div>
</div>
</div>
<div>
<div>
<div>
<div>
<div>
<div>
<div>
<h1>鸣谢</h1>
<p>感谢团队@mochigao，@boristan，@jasonmliu，@harryyfhu，@felixzhuo， @gxgxzhang等小伙伴和老板们的给力支持，也感谢画像挖掘组的小伙伴@sigmayang，@echokong, @raycheng的大力配合与支持。</p>
<p>本文中的算法实现基于公司开源图框架Platodeep2进行开发，感谢PlatoDeep2团队的@healyhuang大佬的支持指导。</p>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div> 
{% endraw %}
