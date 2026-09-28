---
title: "【SIGIR'21】基于元学习的跨领域冷启动推荐【看一看】"
date: 2022-06-14 20:54:37
categories:
  - 推荐算法
  - 跨域推荐与冷启动
---

{% raw %}

<p> <img alt="" loading="lazy" src="/logbook/images/recommendation/c2ac9e7243d8ea165a87.png"/></p>
<p>本文基于SIGIR-2021论文《Transfer-Meta Framework for Cross-domain Recommendation to Cold-Start Users》，论文作者是来自中科院计算所、微信、北航的朱勇椿、葛凯凯、庄福振、谢若冰、奚冬博、张旭、林乐宇和何清。</p>
<p>论文链接：<a href="https://arxiv.org/abs/2105.04785">https://arxiv.org/abs/2105.04785</a><br/></p>
<p>本文由朱勇椿、谢若冰撰写及编辑</p>
<p>本文是看一看推荐元学习论文系列第二弹，其它文章如下：</p>
<div>看一看基于元学习的推荐冷启动预热：[内部或本地链接已移除]<br/></div>
<div>
<div>看一看基于元学习的内容定向推广：[内部或本地链接已移除]<br/></div>
</div>
<p><br/></p>
<p><br/></p>
<p><strong>一、背景介绍</strong></p>
<p>        在这个信息爆炸的时代，如何高效地从大量数据中获得有效的信息变得尤为重要。推荐系统在缓解信息过载问题中起着重要的作用。然而，推荐系统在冷启动推荐上的效果并不令人满意，比如冷启动用户和冷启动物品。</p>
<p>        跨领域推荐旨在利用一个信息丰富的辅助领域来帮助提升目标领域推荐系统的推荐效果。有一类跨领域推荐旨在提升目标领域推荐的整体效果[1,2,3,4]。另外一类跨领域推荐的方法旨在提升冷启动推荐的效果[5,6]。在这类方法中，EMCDR是一种广为使用的代表性方法。EMCDR将源领域和目标领域的用户偏好编码为向量，然后学习一个映射函数，该映射函数将源领域中的用户向量映射为目标领域上的用户向量，基于两个领域重叠的用户，使用MSE损失来进行学习。</p>
<p>        然而，这类方法基于重叠的用户直接最小化映射后的对齐的源领域用户向量和目标领域用户向量的距离，往往存在如下问题：（1）通常两个领域重叠的用户只是一小部分用户。比如在和豆瓣数据集中，源领域和目标领域中重叠的用户占比很低。因此，这样学习到的映射函数会在重叠用户上过拟合，降低模型的泛化能力；（2）使用映射导向的损失函数（MSE），对目标向量的质量有很高的要求。然而在冷启动场景中，目标向量的质量往往不尽如人意，这样会导致向量表示学习中被噪声影响。</p>
<p>        因此，我们提出了一种Transfer-Meta的框架，将跨领域推荐分为两个阶段，transfer阶段和meta阶段：</p>
<ul><li>transfer阶段：在EMCDR中，仅仅使用了重叠的用户来分别学习源领域和目标领域的模型。这里我们使用所有的数据来学习领域和目标领域的模型，然后将训练好的模型作为预训练模型，固定不动，再学习meta network。</li>
<li>meta阶段：以前的方法直接基于两个领域重叠的用户，使用映射导向的损失函数（MSE）学习映射函数。事实上，我们希望学到的映射函数在没见过的用户上有很好的效果。我们分析跨领域推荐中的冷启动问题，可以分为这样两个阶段，在已有的重叠的用户上学习知识，然后在冷启动用户上测试。因此我们将训练任务进行相应的划分，来模拟这个过程，每个训练任务分为两批，两批包含的用户是不重叠的，这两批分别来模拟在重叠用户上学习知识和在冷启动用户上测试这两个阶段，使用MAML[7]进行训练。另外我们提出了一种任务导向的优化方法，不使用MSE来优化meta network（mapping），而是直接使用任务标签来优化，比如评分数据就使用评分来进行优化。</li>
</ul><p> </p>
<p> <strong>二、</strong><strong>模型方法</strong></p>
<p>        整个框架包含两个阶段，transfer阶段和meta阶段，整个训练流程如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/8c89a3ee4fb526d04688.png"/></p>
<p>        以前的方法（例如EMCDR）采用映射导向的优化目标直接拉进映射后的用户向量和目标用户向量的距离，如下所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/5e8ff3ed328a28678ffe.png"/></p>
<p>        而我们的方法具体损失函数由最终任务优化目标确定。假设模型使用MF作为目标函数，我们的loss以MF的评分预测函数为目标进行优化。这样的好处使得模型迁移的跨领域知识能够在目标函数层级相似。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/recommendation/d1d6c11e5e744a739388.png"/></p>
<p> <strong></strong></p>
<p><strong>三、实验</strong></p>
<p>        我们使用了两个数据集：Amazon和Douban。这两个数据集被广泛地在跨领域推荐的研究中采用。我们在Amazon数据上构造了4个跨领域推荐任务，在Douban数据上构造了两个任务。具体结果如下：</p>
<p> <img alt="" loading="lazy" src="/logbook/images/recommendation/fa16605d44c64013bac3.png"/></p>
<p> <strong></strong></p>
<p><strong>四、总结</strong></p>
<p>        在这篇工作中，针对现有的跨领域推荐的方法的不足，我们提出了一种新的transfer-meta的框架。该框架分为transfer和meta两个阶段。Transfer阶段主要获取源领域和目标领域的预训练模型。在meta阶段我们采用MAML训练meta network（映射函数），这样得到的映射函数有更强的泛化能力。另外我们还提出了一种任务导向的优化方法，相比现有的映射导向的方法有更好的效果。</p>
<p> </p>
<p> </p>
<p><strong>参考文献：</strong></p>
<p>[1] Gao C, Chen X, Feng F, et al. Cross-domain recommendation without sharing user-relevant data[C]//The world wide web conference. 2019: 491-502.</p>
<p>[2] He J, Liu R, Zhuang F, et al. A general cross-domain recommendation framework via Bayesian neural network[C]//2018 IEEE International Conference on Data Mining (ICDM). IEEE, 2018: 1001-1006.</p>
<p>[3] Pan W, Xiang E, Liu N, et al. Transfer learning in collaborative filtering for sparsity reduction[C]//Proceedings of the AAAI Conference on Artificial Intelligence. 2010, 24(1).</p>
<p>[4] Singh A P, Gordon G J. Relational learning via collective matrix factorization[C]//Proceedings of the 14th ACM SIGKDD international conference on Knowledge discovery and data mining. 2008: 650-658.</p>
<p>[5] Man T, Shen H, Jin X, et al. Cross-Domain Recommendation: An Embedding and Mapping Approach[C]//IJCAI. 2017: 2464-2470.</p>
<p>[6] Kang S K, Hwang J, Lee D, et al. Semi-supervised learning for cross-domain recommendation to cold-start users[C]//Proceedings of the 28th ACM International Conference on Information and Knowledge Management. 2019: 1563-1572.</p>
<p>[7] Finn C, Abbeel P, Levine S. Model-agnostic meta-learning for fast adaptation of deep networks[C]//International Conference on Machine Learning. PMLR, 2017: 1126-1135.</p> 
{% endraw %}
