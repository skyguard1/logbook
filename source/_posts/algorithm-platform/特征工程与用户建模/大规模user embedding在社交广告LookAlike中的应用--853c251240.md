---
title: "大规模user embedding在社交广告LookAlike中的应用"
date: 2022-04-15 11:44:03
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<p>抱歉，一些公式的格式我怎么调也调不好。大家细心一些根据上下文看，应该能看懂。</p>
<div>
<h1>摘要</h1>
<p>相似受众定向（LookAlike 定向，简称为LookAlike）在近年来逐渐成为各大广告系统的必备功能。通过 LookAlike，广告系统可以根据上传或指定的一个高质量人群计算出与他们相似的人群（前者称为种子，后者称为扩展人群）。考虑到新客户与现有客户具有类似特征，对扩展人群投放广告能有效帮助广告主拓展业务和发掘新客户。</p>
<p>因为篇幅原因，本文不包含过多技术和业务数据，工程上的实现和 trick 也不展开。</p>
<h1>简介</h1>
<p>我们知道，广告系统几乎都有以下定向方式：人口学，LBS/地域，兴趣，行为，再营销。那么如果没有LookAlike，广告主只能使用这些定向投放广告。这样至少有两个问题：第一，广告主可能会陷入大量的定向条件试错，才有可能找到合适的定向方式；第二，可能现有标签都不能满足广告主的需求。</p>
<p>对于广告平台也有问题，各种 KA（Key Account） 广告主总有自己的诉求，标签的定制化、个性化需求永远是无穷尽的。而标签挖掘的成本高、周期长，需要挖掘、内测、调优、开发上线等步骤。</p>
<p>LookAlike只需要广告主指定种子，系统会自动发现种子的相似人群，既省去了定向条件的试错，也规避了自定义标签的问题。</p>
<p>举个例子，如果广告主提供的种子人群是持有某种信用卡的客户，那么相似人群也在某些方面和持有这个信用卡的客户相似。如果相似人群没有持有卡，那么他们也是很有可能去开卡的。这样，显式选择定向条件和标签不够丰富的问题，LookAlike 可以简单、直接的解决。</p>
<p>LookAlike也并非完美，与显式标签相比它的直观程度低一些。</p>
<p>在不同的广告系统中，LookAlike 有不同的名字，比如 similar audiences, LookAlike audiences, behavioral targeting, 粉丝爆炸器等。业界最大的两个广告公司,  和的技术细节并没有公开，只能从产品形态上进行揣测。但总结起来，LookAlike 无外乎有这么几种做法或者它们的组合：用户分类，协同过滤，用户聚类，特征选择等。</p>
<h1>第一阶段：探索中的LookAlike</h1>
<p>广点通定向团队在2013年启动了LookAlike 技术的探索。</p>
<p>第一版LookAlike 使用了大规模分布式 LDA系统 – peacock。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/bbf1361925eb50d18337.png"/></p>
<p>通过对 user-feature矩阵分解，我们得到了user-topic 矩阵。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/adab358ffd262876e3e6.png"/></p>
<p>用户 u 和种子 S 的相似度如下定义（其中 u 是用户的topic 分布， S_i 是种子用户 i 的topic分布）：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f6bbd8a5302e99deb0cc.gif"/></p>
<p>其中 <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7dd195a8a6be0eb6b4dd.gif"/> ，即种子中每个用户的平均 topic 分布，很自然的可以认为是种子集合 S 的 topic 向量。因此，遍历全部人群，计算出每个用户与种子集合的相似度，取排e序较高的即是扩展人群。</p>
<p>这个方法的内测效果仅略好于随机定向，不能让人满意。我们又尝试了基于关系链的 LookAlike。这个方法利用共同好友信息，直觉是共同好友越多，两个人有相同兴趣、属于同一圈子的概率越大。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c1b9807836288fd5ce6d.jpg"/></p>
<p>用户 u 和种子人群 S 的相似度如下定义：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5a741bc006ad8be83bc9.gif"/></p>
<p>遍历全部人群，计算出所有用户的相似度，取 top n 即是扩展人群。</p>
<p>这种方法也没有取得好的结果。之前的直觉是禁不住推敲的。例如，我和我的某个大学同学有很多共同好友，但我们只有在所学专业上有共同点、年龄相仿，此外几乎找不到共同点。</p>
<p>通过尝试，我们也得到了一个宝贵的经验：在 LookAlike 任务上，无监督的方法效果不如有监督的好。而后面的事实也证明了这点，想到使用有监督模型，就已经离成功不远了。</p>
<h1>第二阶段：LR LookAlike</h1>
<p>2014年，我们尝试了用有监督的方法做 LookAlike。我们将种子作为正例，将随机用户进行降采样（subsampling）后作为负例，为每个种子训练一个 Logistic Regression 模型。用这个模型在全部用户上预测，我们认为预测概率值越大，越和种子相似。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/20892d4cff738292d2fd.png"/></p>
<p>用户 u 和种子 S 的相似度这样定义（其中 u 是用户特征向量，w 和 b 是 LR 模型的参数）：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/679abae9ea692da5209d.gif"/></p>
<p>遍历全部人群，计算出所有用户的相似度，取 top n 即是扩展人群。</p>
<p>有了原型算法，我们先后在购物行为定向和商业兴趣定向上做了实验，同时邀请了若干广告主进行内测，得到了大量的正向反馈。随后，LR LookAlike 很自然的完成工程开发并上线。</p>
<p>在工程实现中，一个扩展人群的形式是这样的：</p>
<div>
<pre>S1 =&gt; u1:sim, u3:sim, ...</pre>
</div>
<p> 为了在线使用，将他们系统所有的扩展人群建立倒排索引，形式如：</p>
<div>
<pre>u1 =&gt; S1:sim, S2:sim, S3:sim, ...

u2 =&gt; S3:sim, S5:sim, S6:sim, ... 

u3 =&gt; S5:sim, S1:sim, S6:sim, ...</pre>
</div>
<p>LR LookAlike 系统从2015年服务到了2017年中。随着广告主使用增加，系统的弊端逐渐暴露出来：倒排索引占用空间不断上涨，导致索引更新周期过长，每个用户身上的LookAlike ID 也不得不按照相似度截断，而这种截断会加剧马太效应，对广告主扩展新用户不利。同时，离线模型训练和预测的机器也在不断增加。</p>
<p>LR LookAlike 系统可以支撑至万级别的广告（! 2016年的公开资料表明，他们的 LookAlike只支撑了3000+ 广告）。若要支持10万级别广告，倒排索引存储、离线训练和预测的机器使用不可接受。</p>
<p>因此，LR LookAlike 本身的缺陷阻碍它进一步推广。</p>
<h1>第三阶段：OnlineLookAlike</h1>
<p>了解到了LR LookAlike 扩展性差的原因，我们尝试着抛弃完整的倒排索引，抛弃每个种子一个模型的思路。</p>
<p>在考虑离线模型训练扩展性，倒排索引容量和性能等因素的前提下，我们经过反复推敲，反复思考与实验检测各个模块的可行性，提出了第三代的LookAlike – Online LookAlike。</p>
<p>首先，直接上干货，我们的模型网络结构是这样的：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6d4b58a7254440230bd0.png"/></p>
<p>与 LR LookAlike 不同的是，上图的模型将对所有种子建模。每条训练样本由3部分组成：</p>
<ol><li>用户特征 x</li>
<li>LookAlike ID</li>
<li>标签 y （+1/-1）</li>
</ol><p>用户特征 x 经过feature embedding lookup table 后，将 x 中的非零项对应的feature embedding 取出求平均，得到user embedding。LookAlike ID 只有一个，直接从 LookAlike embedding lookup table 中取出对应 embedding。得到 user embedding 和 LookAlike embedding 后，对这两个embedding求内积，继续通过 sigmoid 函数向前传播，最后使用label y和输出概率之间的logistic loss 作为损失函数。</p>
<p>有了feature embedding，我们可以计算出全量用户的 user embedding，将这些数据写入正排索引供线上查询。注意到user embedding 的规模和用户数量成正比，和种子数量无关。</p>
<p>有了 LookAlike embedding，将他们加载到定向服务器（10万个embedding 只有几十 MB）。</p>
<p>在线召回广告的过程如下：从正排索引取到 user embedding；LookAlike embedding 矩阵– user embedding 向量做乘法，得到 user 和每个广告的相似度；根据每个广告扩展倍数的阈值截断；随机保留 n 个LookAlike ID，将它们对应的广告召回。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b850d82b81fc7c7b6e37.png"/></p>
<p>当 embedding 维度为32，广告为10万时，使用高性能 BLAS 计算库，第一步矩阵-向量乘法的性能没有任何问题。随机保留广告的过程，可以缓解马太效应，提升推荐的时间多样性，提升广告主的收益。由于整个召回过程是在服务器实时计算得到，所以我们叫它 Online LookAlike。</p>
<p>2017年9月，我们完成了Online LookAlike 对 LR LookAlike 的全量替换。</p>
<h1>未来工作</h1>
<p>模型。刻画用户特征的子网络可以走的更深：加入多层全连接，捕捉非线性关系。同时 LookAlike embedding 的子网络可以加入种子的信息（图中未画出）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6b6d73b497a7909b6dba.png"/></p>
<p>特征。加入更具有区分度的特征。</p>
<p>模型训练。随着 LookAlike 广告的增加，训练系统需要超强的能力来处理上百TB 的训练数据。潜在的方案是：分布式训练；online learning；正负例共享等。</p>
<p>在线召回。当LookAlike 广告超过10万后，目前的性能满足不了要求时，可以使用若干方法：LookAlike embedding 矩阵分 shard；使用GPU；使用LSH 或 faiss 近似快速计算向量相似度。</p>
<h1>总结</h1>
<p>Online LookAlike 使用一个神经网络将用户和广告均压缩到了一个低维 embedding 向量空间，使得在线计算成为了可能。在线计算相似度并扩展，只需要存储常量容量的user embedding 和 少量的LookAlike embedding。“所有种子一个模型”比“每个种子一个模型”更具有扩展性。“在线随机截断”比“离线按概率截断”，缓解了马太效应，提升了广告主的收益。Online LookAlike 支持10万级别广告，是目前已知最具有扩展性的LookAlike 构架。</p>
<h1><strong>项目成员</strong></h1>
<p>alanwyyu</p>
<p>elisabeth</p>
<p>kexinhu</p>
<p>kimmyzhang</p>
<p>patrickyao</p>
<p>richardsun(ex.)</p>
<p>roycexu(ex.)</p>
<p>stephengao</p>
<p>wenhanhuang</p>
<p>xueminzhao(ex.)</p>
<p>xinyanlu</p>
<p>yuanhangzou(ex.)</p>
</div> 
{% endraw %}
