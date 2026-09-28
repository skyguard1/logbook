---
title: "PlatoGL_ 主攻GNN实时推荐的新一代图深度学习框架"
date: 2022-06-14 20:52:42
categories:
  - 推荐算法
  - 图学习与社交推荐
---

{% raw %}

<div>
<div>PlatoGL项目是由微信数据中心多个团队和MKV graph技术团队联合完成:</div>
<div>
<ul><li>系统开发一组：welkinwen, cedricsun, elviske, healyhuang, ninjazhang;</li>
<li>数据应用一组：chrisyi, nickgu, drolcaqiu, jerrycgsong, danieslin;</li>
<li>MKV graph组件技术团队：flashlin, colinlyguo, lucienxian.</li>
</ul><hr/><p> 注：该项目已投稿KDD2022 (under review)</p>
</div>
</div>
<h2>一、背景</h2>
<p>近年来，图神经网络GNN算法如雨后春笋般出现，不仅在学术界掀起GNN研究浪潮，更是在工业界落地实践中获得青睐。GNN在非结构化数据上的优异表现和能够同时聚合局部信息和全局信息的能力，使得它在多类应用中表现不凡，其中包括推荐系统。在推荐系统上，用户 (user) 与商品 (item) 的历史交互行为可以定义为二部图（user-item) ，并且其他辅助信息也可以构成各种图结构，GNN在此基础上建模，学习到更好的用户表征(user embedding)和商品表征(item embedding)，从而为用户从海量商品中推荐出其兴趣更高的那些。</p>
<p>除了节点表征学习的有效果，推荐系统的另一个关键指标是能否支持实时推荐(real-time recommendation) 。这是因为在现实生活中的推荐系统，用户兴趣是随着时间动态变化的。 比如，用户在短视频应用中可能会先刷一些运动相关的视频，接着会刷到一些时事热点的视频，而这些视频是不在其长期兴趣范畴之内的。为了应对这种情况，一个优秀的推荐系统往往需要做到以下两点：</p>
<ul><li><strong>实时训练(real-time training)</strong> : 持续使用流式数据(data stream)进行训练；</li>
<li><strong>实时推理(online inference)</strong> : 以毫秒级的时间延迟快速为线上用户的推荐请求发送响应。</li>
</ul><p>在此文章中，笔者将具备这两点的推荐系统称为 <strong>实时推荐系统</strong>。然而，当要将GNN与实时推荐系统结合起来时，困难重重，挑战巨大，更别提需要应用在拥有庞大数据和用户交互行为的推荐业务中。为了解决这个问题，微信数据中心团队开发了新一代图深度学习框架<strong>PlatoGL</strong>来支持实时 GNN推荐。在此文章中，笔者将先详细介绍GNN实现实时推荐的挑战与难点，再介绍PlatoGL框架是如何支持实时GNN推荐，最后会给出对应的线上推荐效果提升。</p>
<h2>二、基于GNN实时推荐系统的挑战与难点</h2>
<p>要做一个基于GNN的实时推荐系统，并且确保它能在大数据时代真正上线使用是极具挑战的。我们将这些挑战归纳如下：</p>
<ul><li><strong>如何部署一个大型流式训练的GNN模型？</strong>具体地说，一个GNN模型的实时训练时需要使用到当前最新的图（该图能及时将用户几分钟前的交互行为记录下来），并且需要针对该图进行信息传播与邻居聚合等GNN基本操作。然而，这样的实时模型部署确实不容易的，原因在于：在实时训练中，需要能稳定地支持实时图更新。这是不容易做到的，因为在推荐场景中，用户与商品的交互行为是高频率变化的，会导致训练使用的二部图乃至更复杂的图结构进行高频更新。</li>
</ul><ul><li><strong>如何让GNN模型进行线上推理的时候满足严格的稳定需求？</strong>详细来说，为了能在毫秒级内响应用户推荐请求，GNN的线上推理的时延需要也控制在毫秒级。要做到毫秒级推理时延，需要这个系统具备非常高的图查询能力，这是因为GNN进行推理时的信息传播和邻居聚合等操作都需要对图进行邻居查询。其次，图存储的稳定在此时也变得至关重要，如果一旦图存储发生宕机或者重启，GNN线上推理必定延迟，从而也会影响线上用户体验质量。</li>
</ul><p>为了解决实时图推荐系统的这些挑战，一个优秀的图深度学习框架是至关重要的。因此，我们对图深度学习框架提出了以下4个关键要求：</p>
<ol><li><strong>毫秒级图更新</strong>(In-milliseconds Dynamically-updating) : 对一个十亿节点级别的图，能做到毫秒内完成图的动态更新。</li>
<li><strong>极高的存储稳定性</strong>(High Storage Stability) ：图存储必须具备超高的稳定来保障推荐服务。</li>
<li><strong>超快的图查询效率</strong>(Ultra-high Query Efficiency) ：在GNN训练或者推理中，它能够高效完成图查询，其中包括查找节点的邻居或者多跳邻居，从而减少时延。</li>
<li><strong>低内存消耗</strong>(Low Memory Counsumption) ：低内存消耗可以减少经济支出。</li>
</ol><p>在业界，图深度学习框架有2018年开源的Euler [1] 以及2019年提出的AliGraph [4] (未开源),  推出的DistDGL [5], 以及我司内部的EmbedX2 [3], PlatoDeep [2]等等。然而，并没有一个能满足上述的要求来支持GNN实时推荐系统的落地。笔者团队推出的PlatoGL框架是现有唯一一款能满足所有要求的图深度学习框架。</p>
<p><br/>三、PlatoGL概览</p>
<h3>1、GNN算法的基本思路</h3>
<p>在描述PlatoGL框架之前，笔者想先简单介绍一下GNN算法的基本操作。GNN算法的基本思路是，对于图上的任意节点 <em>u</em>, (1)先计算它每个邻居携带的信息，(2)接着将所有邻居的信息聚合到节点 <em>u</em>，(3)最后更新节点<em> u</em> 的表征。为了使得GNN能应用于更大规模的图，GraphSage [6] 提出了对一个节点的邻居进行采样再聚合采样到的邻居信息。因此，总结下来，GNN算法包括了三个基本操作:(1) 邻居采样 (sampling), (2) 聚合 (aggregation), (3) 更新 (updating/combination)。</p>
<h3>2、PlatoGL系统简介</h3>
<p>接下来，笔者介绍一下PlatoGL系统的概览。PlatoGL将图存储和GNN算法的基本操作分隔开来，形成两层的系统:</p>
<ol><li><strong>图存储层</strong> <em>(the graph storage layer) </em>: 用来存储图拓扑结构，节点属性信息，快速采样的索引机制，以及缓存机制。</li>
<li><strong>算子操作层</strong> <em>(the TF-based operators layer)</em> : 将GNN算法的基本操作算子融入到现有Tensorflow框架中，使得算法人员可以简单调用这些算子完成GNN算法的开发。</li>
</ol><p><img alt="" loading="lazy" src="/logbook/images/recommendation/5e696e5b155ce11eeff3.png"/></p>
<p>在PlatoGL系统中，图存储层包含了多种原生数据。为了提高图存储的稳定性以及高容灾能力，整个的图存储层是使用微信新一代大规模在线存储系统Infinity [7]。笔者在第四章中将着重描述PlatoGL的设计图存储来满足那四个关键要求。</p>
<h3>3、实时GNN推荐系统</h3>
<p>在这里，笔者简单想介绍一下如何使用PlatoGL实现一套实时GNN推荐系统，整体的工作运转如下所示。实时GNN推荐系统可以分为两个部分: (1) 实时训练 （左上方黄色部分）和 (2) 线上推理 （右上方黄色部分）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/f6bb256f5fb781226e28.png"/></p>
<ul><li><strong>实时训练</strong>：首先，用户的行为会被Logs及时记录，形成以&lt;user, item&gt; 为主的流式数据。一方面，PlatoGL系统会根据实时流式数据不断动态地更新图存储（即，mkvGraph），另一方面，这些流式数据会提供给实时GNN模型样本做训练。在实时训练过程中，这些流式数据会结合节点属性信息传播给GNN模型，GNN模型会通过PlatoGL的算子操作层调用相应的算子，比如，采样算子会向mkvGraph发送采样请求，mkvGraph完成采样再将采样到的节点返回；聚合算子会根据返回的节点进行信息聚合等操作，从而完成源点的新表征，进入传统的loss计算，更新模型网络参数。同时，持续更新的模型网络参数会被部署到线上，供线上推理使用。</li>
<li><strong>线上推理</strong>：笔者以召回为例描述线上推理。当一个用户从客户端下拉推荐请求，推荐系统首先会查询该用户的属性，然后发送用户id和属性给线上部署的模型进行实时打分，构造该用户的表征(user embedding)。在实时打分的时候，GNN模型同样需要调用PlatoGL的相关算子操作。最后，系统会将返回的用户表征与线上已有的商品表征(item embedding)进行相似度计算，找出top-k最相似的商品作为输出。</li>
</ul><h2>四、PlatoGL系统细节</h2>
<p>在此章节中，笔者着重介绍PlatoGL系统是如何存储图拓扑信息以及如何高效完成图查询。值得一提的是，PlatoGL使用<strong>key-value的数据存储格式</strong>来存储有关于图的所有数据，包括图拓扑结构、节点属性信息、索引机制和缓存机制。</p>
<h3>1、mkvGraph: 节点与边的存储</h3>
<p>此章节主要描述如何存储图拓扑结构，即节点与边的存储。在mkvGraph中，图上的节点是和边一起存储的，比如独立节点可以被看成是没有邻居的边。一般来说，最简单的边存储就是将一条边所连接的两个节点当作key，value设置为null。然而，这样的存储格式会导致超大的内存开销，假设图有m条边，这个存储开销就是O(m)。以往的工作中，为了降低存储开销，会将途上每个点当作key，该点的所有邻居当作value，这样可以将存储开销从O(m)降低到O(n)，其中 n 是图的节点个数。但这样的存储格式存在读放大(read perspiration)和写放大(write amplification)问题。简单来说就是，当一个有超多邻居个数的超级节点要更新它的邻居时，它需要将所有的邻居都load到内存来，导致读/写放大，极有可能内存爆炸，存储不稳定。</p>
<p>为了解决这些问题，mkvGraph在边存储上，设计了一款新颖的存储方案：<strong>基于块的存储 (block-based key-value storage)</strong>。它的基本思想是将图上任意节点的邻居划分为多个块，每个块存储一部分邻居节点。这个块的大小是固定的。下图表示了边存储的结构。详细来说，每个key都是一个多字节的存储，针对节点 <em>s </em>，key会保存它的节点类型(KType)、边类型(<img alt="" loading="lazy" src="/logbook/images/recommendation/8ae1676cd36b76fbfcb4.png"/>)以及邻居节点所在的块id(b)。key对应的value是一个块，主要存储两种信息：（1） header，用来存储这个块包含的邻居总数(<img alt="" loading="lazy" src="/logbook/images/recommendation/14c8389ecfa9557f8042.png"/>)、这个块所有邻居的权重总和(<img alt="" loading="lazy" src="/logbook/images/recommendation/2c25ba2321bdb696e143.png"/>)以及该块被采样的概率(<img alt="" loading="lazy" src="/logbook/images/recommendation/32c9340c61247c525c5b.png"/>); （2）units, 用来存储每个邻居节点 <em>t </em>的id和对应被采样的概率(<img alt="" loading="lazy" src="/logbook/images/recommendation/25b9b8de2d94225d13d0.png"/>)。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/e7cbc1f8cf377e9c4274.png"/></p>
<p>每个块的大小是固定，视图规模大小而定。当一个块中的邻居总数超过阈值，会触发块分裂，即变成两个块，邻居再重新分配到两个块。</p>
<p>不仅如此，PlatoGL同时设计了节点属性以及边属性的存储结构。为了区分不同应用场景，PlatoGL分别设计了稀疏属性以及稠密属性，如下图所示。因为篇幅有限，在此不做赘述。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/e2729641ce1d51ae790a.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/3b98855a7641e89ea7a9.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/99a68f8200f1685d9ad7.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/457e8c11de8cc26e56d8.png"/></p>
<h3>2、邻居采样</h3>
<p>因为边是基于块存储的，带权邻居采样的难度增大。为了快速完成采样，PlatoGL提出了一个基于Inverse Transform Sampling (ITS) [8] 的采样策略。该策略能够从理论上有效证明带权采样的准确性，并且相比于其他采样策略，理论上有效降低一半的内存开销。该策略的基本思想是，<strong>对一个节点，先从所有邻居块中按照权重分配采样一个块，再从该块中按照权重采样一个点，从而完成邻居采样</strong>。</p>
<p>为了提高采样的效率，PlatoGL同样用key-value的形式设计了采样索引。详细来说，每个节点的key会存储该节点的类型。每个key对应的value会存储两部分信息：(1) header, 用来存储信息总数； (2) 用来存储每个块id及其对应的采样概率。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/ec284080e578f91d95ec.png"/></p>
<p>同样地，为了完成节点采样和边采样，PlatoGL也设计对应的索引，因为篇幅有效，在此不做赘述。</p>
<h3>3、缓存机制</h3>
<p>在大规模图上，有些节点会被频繁访问，为了减少这些节点的查询开销，PlatoGL设计了针对节点邻居和节点属性的缓存。</p>
<p>因为缓存机制的基本思想是一致的，接下来笔者着重介绍节点属性的缓存。它的基本思想是，当一个节点属性查询请求来临时，如果该节点的属性在缓存中，就直接由缓存返回，无需和图存储做交互；否则，它会触发请求到图存储。为了保证缓存机制的稳定性，PlatoGL采用了MemC3 [9] 的缓存技术。在缓存机制中，主要有两个操作：一个是Cache-Set, 用来设置哪些节点属性可以被缓存以及哪些节点属性应该被淘汰；另一个是Cache-Get, 用来返回相应的请求结果。</p>
<p>为了保证缓存机制的更新迭代及时，设置了一个参数cache-exprie-time来记录每个节点属性缓存过期的时长；为了保证缓存的低内存开销以及线上推理的信息一致性，设置了一个参数cache-size来协调缓存的大小。</p>
<h2>五、线上推荐效果</h2>
<h3>1、数据集</h3>
<p>为了测试实时GNN推荐系统在线上的效果，我们将GNN实时模型部署在微信直播业务召回模块中。除了流式更新的用户交互数据(user-item)用来做模型训练，该模型还用到了按天更新的微信异构图 (WeChat)来增强用户与商品的表征，其中包含了5种异构关系，整个图的节点个数可达十亿级别。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/449bca3c760309cee99d.png"/></p>
<h3>2、线上召回效果</h3>
<p>为了评估实时GNN训练和推理带来的效果，我们使用PlatoDeep构造了一个按天更新的离线GNN模型，该模型使用和实时GNN模型一样的模型结构。离线GNN模型使用的是按天更新的样本，样本定于与实时GNN模型保持一致，并且离线GNN模型也使用 WeChat这张图来做增强。我们将这两个模型部署到微信直播业务的召回模块中进行线上A/B Test，覆盖了百万级别的线上用户。从下表的数据中可以看出，<strong>实时GNN模型在dau/pctr/观看时长上都比离线GNN模型更好, 因为实时GNN模型能够捕捉用户的即时交互行为（即时兴趣）</strong>。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/11aff2592f953f49435e.png"/></p>
<p>同时，为了反映出实时GNN模型真的能捕捉用户的即时兴趣，我们记录了两个模型在每小时的top100召回率。从图(a)上也可以看出，实时GNN模型的召回率比离线模型高出将近4倍。</p>
<p>最后，我们针对线上部署，记录了实时GNN模型在查询和实时推理时候的时延。从图(b)可以看到，不管是图查询还是实时推理，整体的时延都能达到毫秒级。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/a59a3e10e52a55f5704f.png"/></p>
<p>       流式GNN训练模型在直播业务上已经推全，《跨域推荐：异构GNN推荐算法》。 [内部或本地链接已移除]</p>
<h2><br/></h2>
<h2>六、参考文献</h2>
<ol><li><a href="https://github.com/alibaba/euler">https://github.com/alibaba/euler</a></li>
<li><a href="https://github.com/Tencent/plato">https://github.com//plato</a></li>
<li>[内部或本地链接已移除]</li>
<li>
<p>Zhu, Rong, et al. "AliGraph: A Comprehensive Graph Neural Network Platform." <i>Proceedings of the VLDB Endowment</i> 12.12.</p>
</li>
<li>Zheng, Da, et al. "Distdgl: distributed graph neural network training for billion-scale graphs." <i>2020 IEEE/ACM 10th Workshop on Irregular Applications: Architectures and Algorithms (IA3)</i>. IEEE, 2020.<br/></li>
<li>Hamilton, Will, Zhitao Ying, and Jure Leskovec. "Inductive representation learning on large graphs." <i>Advances in neural information processing systems</i> 30 (2017).<br/></li>
<li>Infinity：微信新一代大规模在线存储系统</li>
<li>Yang, Ke, et al. "Knightking: a fast distributed graph random walk engine." <i>Proceedings of the 27th ACM Symposium on Operating Systems Principles</i>. 2019.<br/></li>
<li>
<p>Fan, Bin, David G. Andersen, and Michael Kaminsky. "{MemC3}: Compact and Concurrent {MemCache} with Dumber Caching and Smarter Hashing." <i>10th USENIX Symposium on Networked Systems Design and Implementation (NSDI 13)</i>. 2013.</p>
</li>
</ol><p><br/></p> 
{% endraw %}
