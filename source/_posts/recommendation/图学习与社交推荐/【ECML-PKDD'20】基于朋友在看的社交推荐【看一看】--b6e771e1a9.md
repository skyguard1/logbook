---
title: "【ECML-PKDD'20】基于朋友在看的社交推荐【看一看】"
date: 2022-06-14 20:55:45
categories:
  - 推荐算法
  - 图学习与社交推荐
---

{% raw %}

<p> </p>
<p>本文基于ECML-PKDD-2020论文《Social Influence Attentive Neural Network for Friend-Enhanced Recommendation》，论文作者是北京邮电大学、微信、新加坡管理大学的陆元福、谢若冰、石川、方元、王伟、张旭和林乐宇。</p>
<p>本文由陆元福、谢若冰撰写及编辑。</p>
<p><br/></p>
<p><strong>一、</strong><strong>背景简介</strong></p>
<p>当下，随着在线社交网络的兴起，人们更愿意在社交平台上表达自己的观点并与好友共享信息。好友成为重要的信息来源和高质量的信息过滤器。好友互动过的商品（共享的，喜欢的等）会对用户产生重大影响，这很可能会成为用户未来的兴趣所在。工业界，也有许多推荐系统专注于好友的社交影响，例如，关注 YouTube中的信息流和微信中的“看一看”文章推荐。</p>
<p>在本文中，作者基于微信“看一看”文章推荐场景，形式化了一个全新的推荐场景，叫做好友增强的推荐系统（Friend-Enhanced Recommendation，FER），其大大增强了推荐系统中好友对用户行为的影响力。相较于传统的社交化推荐，好友增强推荐有两个主要区别：（1）鉴于好友可以看作高质量信息过滤器为用户提供高质量的商品，好友增强推荐只为用户推荐好友交互过的商品（读过的文章）；（2）与某一商品交互过的所有好友都会显式的展示给当前用户，即当前用户已知哪些好友与当前物品有过交互。这一特点重点强调了显式的社交影响力对用户行为的影响，这也有益于用户行为的可解释性。</p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/b58f272ffb541dfeddb5.jpg"/></p>
<p>图1. 好友增强性型推荐场景。左侧显示了推荐给 Jerry 的两篇文章的场景，下面是与两篇文章互动（共享，喜欢等）的朋友（如 Tom）。右侧显示了好友增强推荐问题的形式化，其中仅推荐朋友交互过的文章，并且与该项目进行交互的朋友被明确暴露给用户 Jerry。</p>
<p><br/></p>
<p>图 1 展示了微信“看一看”场景下的一个形式化示例。对于每一个用户-物品对，好友增强型推荐显式地展示已经和当前物品交互过的好友集合，这个集合被定义为：针对当前商品，当前用户的好友推荐圈（Friend Referral Circle, FRC）。举例来说，对于关于 AirPods 的文章， Jerry 的好友推荐圈是{Tom, Lily, Jack}。 在传统社交推荐中，好友推荐圈对于 Jerry 是不可见的（不会展示给 Jerry），因此 Jerry 可能会基于自身的兴趣阅读某一篇文章。然而，在好友增强型推荐场景中，好友推荐圈对用户 Jerry 是显式可见的，因此他阅读这篇关于 AirPods 的文章，更可能是因为科技专家 Tom 读过这篇文章。而 Jerry 阅读一篇关于 Disneyland 的文章，完全有可能是因为他的妻子 Lily 读过这篇文章。更进一步地，当文章与科技相关时，相较于妻子和科技文章，专家和文章的同时出现对 Jerry 的耦合影响力更大，而在娱乐方面，可能是完全相反的情况。</p>
<p>因此，在好友增强型推荐场景中，多个因素导致了用户的行为。用户阅读/点击一篇文章的原因可能来自：（1）其自身对文章的兴趣（文章本身）（2）专家的推荐（文章-好友的组合）（3）对某一好友的关注（好友）。可以看到，在好友增强型推荐场景中，用户有关注好友在看的内容的倾向，而非仅仅看自己本身感兴趣的内容。甚至可以说，传统社交推荐关注于结合社交信息去推荐物品，而好友增强的推荐旨在推荐物品和好友的组合。</p>
<p>作为好友增强型推荐的关键特性，显式的好友推荐圈为该推荐场景带来两个挑战：（1）<strong>如何从多方面的异质因素中提取关键信息？</strong>好友增强的推荐场景涉及多个异质目标，例如物品内容，好友推荐圈及用户-物品交互行为等。在用户，物品和朋友推荐圈的不同组合下，这些因素的影响甚至也有所不同。因此好友增强的 推荐场景更具挑战性，因为它不仅需要学习用户对商品的偏好，还需要预测不同 因素对好友的影响。（2）<strong>如何利用显式的好友推荐圈信息？</strong>显式的好友推荐圈推荐极大地强调了推荐中社交信息的重要性，这在好友增强的推荐场景中是至关重要。但是，很少有工作在实际推荐中探索好友推荐圈的影响和特性。因此需要一种精心设计的策略，以充分利用好友增强的推荐场景中的显式的好友推荐圈信息。</p>
<p>为了解决这些问题，作者提出了一种新颖的社交影响力专注的神经网络（SIAN）。具体来说， SIAN将好友增强推荐定义为异质社交图上的用户-物品交互预测任务，该任务将丰富的异质信息灵活地集成到异质对象及其交互连接中。首先，作者设计了一个注意力特征聚合器，它同时考虑节点级和类型级的特征聚合，以学习用户和物品的表示向量。接下来，作者实现了一个社交影响力耦合器，以建模通过显式好友推荐圈传播的耦合影响力，该耦合器利用注意力机制将多种因素（例如，朋友和物品）的影响力耦合在一起。总体而言，SIAN 模型捕获了好友增强的推荐场景中有价值的多方面因素，从而成功地从异质信息网络和显式好友推荐圈中提取了用户的最基本偏好。</p>
<p> <strong></strong></p>
<p><strong>二、模型结构</strong></p>
<p>如图 2 所示， SIAN 利用异质社交网络建模好友增强型推荐场景。除了用户和物品的向量表示，SIAN 还通过耦合有影响力的好友与物品来学习社交影响力的低维向量表示。通过学习用户、物品和耦合的社交影响力的向量表示，最终 SIAN 预测用户𝑢和物品𝑖之间交互的概率。</p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/fb8ef7b73bdc0d815c49.jpg"/></p>
<p>图2. SIAN模型总览</p>
<p><br/></p>
<p>首先，考虑到相同类型的不同邻居可能对特征聚合的贡献是不同的，并且不同类型包含多方面的信息，因此作者设计了分层的节点级和类型级的注意力特征聚合器。在每个级别，注意力机制区分和捕获邻居和类型的潜在关联性，使得 SIAN 模型能够更细粒度地编码多方面的异质信息。与之前的一些工作不同的是， SIAN 不需要基于任何先验知识手动选择元路径。</p>
<p>其次，作者设计了一个社交影响力耦合器，其用来捕获一个有影响力好友（例如 Tom）和一个物品（例如 Disneyland 相关文章）的耦合影响力， 从而量化它们的耦合影响力程度。最后，带有注意力地融合来自好友推荐圈内的多个耦合影响力，以表示整个好友推荐圈对当前用户和物品的影响。</p>
<p>最后，基于用户、物品以及耦合的影响力表示，作者将三者拼接并送入两层神经网络中，并通过一个回归层，预测得到用户-物品的交互概率 。最终，通过优化交叉熵损失函数训练优化模型。</p>
<p> <strong></strong></p>
<p><strong>三、实验分析</strong></p>
<p>基于两个公开数据集（Yelp和Douban）以及微信看一看数据（FWD），作者进行了丰富的实验评估和分析。数据集统计信息见下表1。</p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/29fe00783af405a92206.jpg"/></p>
<p>表1. 数据集统计</p>
<p><br/></p>
<p>在主实验中，作者对比了四类代表性的方法，并报告了在不同表示维下的模型表现，结果可以见表2。可以看到，在多个数据集上，提出的SIAN模型明显优于对比方法。特别是，和传统社会化推荐方法相比，SIAN模型依然表现突出，这得益于社交影响力耦合器在为好友增强推荐场景编码各种社交因素时的能力，也这进一步证实了社交影响力在好友增强推荐中的重要性。</p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/1f252343de76ed332410.jpg"/></p>
<p>表2. 用户行为预测实验结果</p>
<p><br/></p>
<p>其次，作者分析了多方面异质信息的影响。在注意力特征聚合器中，每个节点的向量表示都是从其具有不同权重的各种类型的异质邻居聚合而来的，作者分析发现：SIAN模型学习得到的好友类型的平均注意力权重值显著大于物品类型的平均注意力权重。这表明了SIAN模型更加关注用户的社交关系，这种关注甚至超过了内容本身。这同时也验证了好友推荐圈是好友增强推荐中最重要的因素。实验结果如图3所示。</p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/ddd072f1db7559778657.jpg"/></p>
<p>图3. 好友、内容、公众号等信息影响分析</p>
<p><br/></p>
<p>更进一步地，在微信看一看数据集上，作者分析了不同的用户属性如何通过社交影响力耦合器的影响力强度来影响好友增强推荐场景中的用户行为，并得出了一些有趣的发现。例如，在图 4(a)中，可以观察到用户行为受到更具权威性的朋友的影响， 而与用户自己的权威度无关。同时，高权威朋友对中等权威用户具有更大的影响力。用户通常更容易受到权威人士的影响，这和我们的常识也是相符的。因此，在好友增强推荐场景中，可能存在一个有趣的现象，即有时用户会更多地关注权威人士的喜好（或者仅仅是关注权威人士本身），而不是他们自己的实际喜好。我们也观察到其它用户基础属性对于好友增强推荐场景中的用户行为产生影响。</p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/1895775bf53b513c0505.jpg"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/785cb9d3b66150abe518.jpg"/></p>
<p>图4. 社交影响力分析</p>
<p> <strong></strong></p>
<p><strong>四、总结</strong></p>
<p>在这一工作中，作者首次形式化定义了微信看一看中的朋友在看推荐场景，即好友增强型推荐，其显式地展示已经和当前物品交互过的好友。针对这一新型且应用广泛的推荐场景，作者提出了社交影响力注意的神经网络SIAN，SIAN模型通过一个两级注意力聚合器学习user和item的表示，并设计了一个社交影响力耦合器的用于提取朋友推荐圈中的影响力信息。 实验结果表明，在三个真实的数据集上，SIAN的性能明显优于最新基准，丰富的模型分析揭示出有趣的社会学模式。</p>
<p>我们认为未来以微信看一看朋友在看为代表的好友增强型推荐将会成为人们获取信息的重要方式，通过推荐连接用户与世界。现在对好友增强型推荐的研究仅仅处于初级阶段，我们希望未来能有更多新的研究工作与分析。</p>
<p> </p>
<p><strong>参考文献：</strong></p>
<p>[1] Chen, Chong, et al. "Efficient Heterogeneous Collaborative Filtering without Negative Sampling for Recommendation." Proceedings of the AAAI Conference on Artificial Intelligence. Vol. 34. No. 01. 2020.</p>
<p>[2] Dong, Yuxiao, Nitesh V. Chawla, and Ananthram Swami. "metapath2vec: Scalable representation learning for heterogeneous networks." Proceedings of the 23rd ACM SIGKDD international conference on knowledge discovery and data mining. 2017.</p>
<p>[3] Fan, Wenqi, et al. "Graph neural networks for social recommendation." The World Wide Web Conference. 2019.</p>
<p>[4] Grover, Aditya, and Jure Leskovec. "node2vec: Scalable feature learning for networks." Proceedings of the 22nd ACM SIGKDD international conference on Knowledge discovery and data mining. 2016.</p>
<p>[5] Kipf, Thomas N., and Max Welling. "Semi-supervised classification with graph convolutional networks." arXiv preprint arXiv:1609.02907 (2016).</p>
<p>[6] Perozzi, Bryan, Rami Al-Rfou, and Steven Skiena. "Deepwalk: Online learning of social representations." Proceedings of the 20th ACM SIGKDD international conference on Knowledge discovery and data mining. 2014.</p>
<p>[7] Shi, Chuan, et al. "Heterogeneous information network embedding for recommendation." IEEE Transactions on Knowledge and Data Engineering 31.2 (2018): 357-370.</p>
<p>[8] Veličković, Petar, et al. "Graph attention networks." arXiv preprint arXiv:1710.10903 (2017).</p>
<p>[9] Wang, Xiao, et al. "Heterogeneous graph attention network." The World Wide Web Conference. 2019</p>
<p>[10] Wu, Le, et al. "A neural influence diffusion model for social recommendation." Proceedings of the 42nd international ACM SIGIR conference on research and development in information retrieval. 2019.</p>
<p>[11] Xiao, Wenyi, et al. "Beyond personalization: Social content recommendation for creator equality and consumer satisfaction." Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery &amp; Data Mining. 2019.</p>
<p><br/></p> 
{% endraw %}
