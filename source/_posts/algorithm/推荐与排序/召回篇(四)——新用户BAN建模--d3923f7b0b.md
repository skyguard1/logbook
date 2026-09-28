---
title: "召回篇(四)——新用户BAN建模"
date: 2022-04-01 14:52:33
categories:
  - 算法
  - 推荐与排序
---

{% raw %}

<div>
<div>
<p></p>
<ol><li>
<p>背景</p>
</li>
</ol><p>微视召回侧基于用户的行为的召回模型有很多种。比如工业界最常见的DSSM模型，基于图嵌入Graph Embedding，基于图神经网络的GNN，基于序列召回的SASRec，多兴趣召回的MIND等。但是目前大部分的模型都严重依赖用户已有的行为信息，对于新用户的召回效果并不友好。</p>
<p>冷启动问题一直是推荐系统必须面对且很难攻克的难题。团队在新用户冷启动的优化上投入了很大的精力，比如尽量丰富准确的获取用户的属性特征，比如基于规则的挖掘被系统验证过的优质内容等，同时我们也在尝试通过主动学习和迁移学习的思路来建模新用户的兴趣。假设每一个新用户都能在现有的推荐系统中找到一个或者一批与其兴趣相似的用户，如何找到这些种子用户并把其兴趣迁移到新用户兴趣中，成为我们对新用户兴趣建模的一个重要方向。本文重点介绍我们基于PreHash Network思想利用DSSM模型建模新用户兴趣的尝试。</p>
<p></p>
<ol><li>
<p>DSSM模型</p>
</li>
</ol><p>DSSM模型最早是用于query和doc的检索匹配上。如图1所示，DSSM模型通过海量的计算日志用DNN网络结构把Query和Doc表达为128维的向量，通过余弦距离建模Query与Doc之间的语义相似度。在线检索过程中，利用近似最近邻检索算法为每个query快速检索到与之距离相近的doc。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/de71521b57f430a8eb59.png"/></p>
<p>图1</p>
<p>DSSM模型的结构既充分的利用了query和doc语义特征，又避免了两者的特征交叉，同时拥有高精度和高性能的优势，从而获得工业界的广泛的青睐。同时搜索场景下Query和Doc的语义检索跟推荐场景的User和Item推荐匹配是个极其相似的问题。如图2基于推荐场景的各种行为日志，基于双塔结构建模User和Item的语义相似度，成为推荐场景下最常见的触发方式之一。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e820c3982993ba07fd08.png"/></p>
<p>图2</p>
<p>DSSM是深度模型，且我们在构造样本时，用户和物品都引入了大量稀疏特征，从而需要充足的样本以保证模型收敛。但是新用户行为少，特征少，导致模型难以准确捕捉新用户兴趣，新用户的推荐上往往有同质化，高热化的特点。如果能通过预训练的方式，加快模型捕捉新用户兴趣的速度，就可以缓解上述问题，即模型热启动。而PreHash网络则是通过anchor向量设计，对模型起到预训练的作用，实现热启动，以此来加快对新用户兴趣捕捉，降低用户兴趣探索成本。</p>
<p></p>
<ol><li>
<p>PreHash network 与 Anchor User</p>
</li>
</ol><p>prehash网络的提出是为了解决稀疏行为用户推荐问题，它通过preHash的用户向量替换掉原有网络中的用户向量，以此丰富用户的兴趣向量表达 ，其核心部分在于preHash网络的设计，整体网络架构如下图</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/19d0c75e443530ee419c.png"/></p>
<p>图3</p>
<p>网络的左侧是常规的 MF ，在推荐场景中userid的稀疏程度是远高于 itemid 的，所以在 MF 中会面临大量的计算资源开销，而如果有一种能快速得到user embedding的方式，就可以显著缓解计算复杂度。</p>
<p>网络右侧的PreHash模块也分为两部分。左部分是根据用户历史行为计算attention，加权得到用户的历史行为表达[图片未保存到本地]，其中attention计算和DIN一样是label-aware attention。PreHash模块的右侧是根据其他用户计算当前用户的兴趣表达。论文中采用的是随机选取锚点用户（anchor user），先确定N个anchor user，然后根据N计算Hierarchical Attention得到每个anchor的权重。为了降低噪音，突出高权重的anchor user，会进行一次topk的权重筛选( k &lt; n)，最后对选中的k个anchor user embedding加权融合得到 [图片未保存到本地] 。 [图片未保存到本地] 表达的是用户自身的兴趣（self-based）， [图片未保存到本地] 表达的则是协同的兴趣（others-based），最后的 [图片未保存到本地] 则是两者的融合，以替代原 MF 的user embedding。</p>
<p></p>
<ol><li>
<p>biased anchor network</p>
</li>
</ol><p>PreHash模块右侧部分，其实就是找到当前用户的相似用户以得到兴趣表达的过程，但根据原论文的实现方式，有两个问题：</p>
<ul><li>anchor user的选择</li>
</ul><p>论文中anchor user的选择是从历史行为丰富的老用户中进行随机选择，但在N比较小的情况下，很难选中和我们当前计算用户相似的anchor user，容易导致选中的anchor和我们要计算的用户相似度都不是太高 ，导致最后 [图片未保存到本地] 表达失效。</p>
<ul><li>Hierarchical Attention</li>
</ul><p>根据原论文的实现，Hierarchical Attention的主要目的是实现topk anchor的筛选，在实验中N = 1024，k = 128，这样的筛选方式在理解上远不如直接和 user 向量做内积来的直观，同时N值越大分层越多，相应的计算开销也会越大。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/5a63f3abfaeeb2847d64.png"/></p>
<p>图4</p>
<p>结合微视的新用户推荐场景，我们对网络做了如上设计。我们通过dssm模型训练出历史行为丰富的老用户向量作为author user，融合得到当前新用户向量。为了提升我们的寻找相似用户的效率，我们先根据一些基础属性特征，对老用户向量进行了聚合，聚合的过程是 anchor user -&gt; anchor group，聚合的特征包括性别，年龄，所在地域等基础属性特征。在这个过程中，含有相同特征的老用户被聚合在一个group下，并对该group内的向量做avg pooling 以得到 anchor group embedding。利用同uv内积计算得到attention的权重加权求和，得到融合后的 [图片未保存到本地] 向量。将 [图片未保存到本地] 向量与利用用户自身feature向量计算得到的 [图片未保存到本地] 进行concat，所得到的最终向量作为后续层的输入，同item侧计算相似度，以此来召回视频。</p>
<p>由于新用户没有太多历史行为，所以我们在设计上舍弃了history part。并且在计算最终 [图片未保存到本地] ，我们没有使用类似原文的route attention的加权结构，而是直接进行了concat，以保证用户自身的feature，也可以得到充分的表达。</p>
<p>我们在纯新用户上得到了如下的实验结果</p>
<div>
<p>有效人均播放时长:+2.68% ，显著;</p>
</div>
<ol><li>
<p>BAN延伸与扩展</p>
</li>
</ol><p>BAN在网络设计上的核心思想，是通过anchor embedding来补充增强已有的embedding的表达。本文中使用的anchor embedding来自于自身业务预训练的向量。同样我们结合不同的业务场景，还可以引入自身业务预训练的作者向量，标签向量等能表达相似关系的向量，以及来自于业务外的能表达先验知识的知识图谱向量或者用户端外信息的预训练向量等。相比单纯的加到feature里由模型自己学习，BAN的设计模式更好的融合了研究人员的先验知识以及业务预判，通过差异化的anchor结构设计能够对原有数据进行很好的补充增强。</p>
<ol><li>
<p>后续工作</p>
</li>
</ol><ul><li>更合理的anchor设计</li>
</ul><p>当前网络的anchor仅仅是简单的特征聚合，而特征聚合的粒度比较粗；另一方面，anchor embedding缺少和预训练模型的联动更新，虽然user 之间的相似关系相对稳定，但仍需要有合理的更新机制保证效果。</p>
<ul><li>更多类型的数据引入</li>
</ul><p>我们后续会在user侧针对多产品线数据，进行融合anchor的探索工作，期望能摆脱传统对多产品线特征直接加feature的单一使用模式，增强纯新用户端外兴趣在冷启阶段的表达。</p>
<ul><li>知识图谱结合推荐</li>
</ul><p>知识图谱如何融入到网络结构中也是我们未来主要的探索工作，例如标签语义关系的融入，能更好的帮助我们解决物品冷启问题。</p>
<p></p>
<hr/><p> </p>
<div>
<p><i>1. Huang P S, He X, Gao J, et al. Learning deep structured semantic models for web search using clickthrough data[C]//Proceedings of the 22nd ACM international conference on Information &amp; Knowledge Management. 2013: 2333-2338.</i></p>
2. <i>Shi S, Ma W, Zhang M, et al. Beyond User Embedding Matrix: Learning to Hash for Modeling Large-Scale Users in Recommendation[C]//Proceedings of the 43rd International ACM SIGIR Conference on Research and Development in Information Retrieval. 2020: 319-328.</i></div>
<h1></h1>
<p></p>
</div>
</div> 
{% endraw %}
