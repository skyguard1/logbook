---
title: "超越 PeterRec！自研迁移学习推荐算法架构 UDARec"
date: 2022-04-14 16:07:53
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<p>本文所涉及的技术方案及实验，由<strong></strong> <strong>nickcliu(刘冲) </strong>与<strong></strong>内容业务部 <strong>leonezheng(郑荣钦</strong>) 于2020年11月-2021年1月共同完成，本文的撰写是共同完成。项目源码：[内部或本地链接已移除]<br/></p>
<h2>出发点及问题</h2>
<p>PeterRec [<em>Yuan et al.,</em> 2020] 是看点团队在 SIGIR2020 会议上提出的基于迁移学习的推荐算法架构，论文中的多组实验证明了迁移学习在推荐领域里的有效性。本文在 PeterRec 的思想上进行了优化，提出了新的迁移学习框架——UDARec，大幅度地超越了 PeterRec 的效果。</p>
<p>PeterRec算法深入研究了通过学习单一用户表征用户各种不同的下游任务，包括跨域推荐和用户画像预测，优化一个大型Pre-train网络并将其适配到下游任务是解决此类问题的有效方法。通过注入一些的的小型但是极具表达力的神经网络，以及借助Pre-train Fine Tune的训练模式，PeterRec可以快速地将在Source域训练好的模型，Fine Tune 成可以作用于Target域任务的新模型，是一种参数高效的迁移学习架构。关于PeterRec的详细介绍，可以参见原作者发表的KM文章：用户画像中台建设探索之PeterRec</p>
<p>PeterRec发表之后，引起了我和 leonezheng同学的极大兴趣，在PeterRec原作者的热心帮助和指导下，进行了复现和调优，并在多个数据集上进行了尝试，达到了预期的效果。但随着对PeterRec更深入的探索，我们发现了它的一些没有解决的问题，所以希望在PeterRec的基础上进行改进，以求达到更好的效果。</p>
<p>首先，PeterRec的Pre-train模型采用了作者于19年提出的NextItNet [<em>Yuan et al.,</em> 2019] 作为主题结构，此模型结构以Dilated Convolution为特征提取子结构，通过叠加空洞卷积层达到可视域指数级的增加，在减小计算量的同时扩大模型感受野，以求在长序列数据中达到更好的效果。但是Dilated Convolution 用来做特征提取的效果有限，而且无论是实际应用、还是作者给出的实验中，序列的长度都没有特别长，“长序列建模”这个问题的优先级在目前来看可能并没有那么高。其次，PeterRec在Pre-train的时候，不停地去预测下一个点击，但是Fine Tune的时候其实并不能满足这个时间上的假设，向原作者请教之后发现Target域上的行为数据有一部分在时间上是发生在Source域点击序列之前的。最后，PeterRec在Fine Tune的时候使用序列的最后一个点击ID的embedding作为用户的整体向量表达，这是一种常规的做法，但是对用户整体行为的拟合和表达能力不够。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c4e59d79a32f9c94d18d.png"/></p>
<p>图1: NextItNet 中的 Dilated CNN 结构</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/bb2fd083b23bdc05c25a.png"/></p>
<p>                   图2: PeterRec中的Pre-train Fine Tune模式</p>
<h2>解决方案</h2>
<p>为了解决这两个问题，首先我们决定使用现在业界更为通用的Transformer作为Pre-train时的特征提取结构，来获得更好的向量表达。并且在Pre-train过程中，借鉴Bert的训练模式——mask掉序列中的一部分，用未mask的部分来预测被mask的部分，这样可以将Pre-train和FIne Tune时的目标的时间假设性做到一致。在Fine Tune时，引入了Adapter模块来防止过拟合及尽可能多地保留Source域知识。最后，我们引入了一种非监督的对比学习表达模块，来获取更好的用户 embedding。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f828359a8ea3ac0090a5.png"/></p>
<p>图3: 我们的Pre-train模型主体结构</p>
<p>在Fine Tune的过程中，传统的Fine Tune一般有两种模式，一是对整个Pre-train模型进行更行，这样的话计算量大速度慢，且Target域一般数据较少，容易过拟合；二是只Fine Tune最后一个全连接层，这样的话表达性差，Transformer的参数被完全固定住，模型学习到的Target域信息较少。为了减少计算量的同时，尽可能多地保留模型在Source域中学到的知识，我们借鉴了NLP领域的Adapter结构 [<em>Houlsby et al.,</em> 2019]  ，相较于更新整个Pre-train模型，只更新Transformer里的Adapter结构仅需训练约0.5%的参数量；且泛化能力强，既能最大限度地保留source域中的旧信息，又能捕捉到Target域的新知识。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1d0abfd006f1755fad6a.png"/></p>
<p>图4: Transformer + Adapter 结构</p>
<p>最后，在获得最终的用户表达向量问题上，业界一般有两种做法，第一种是对Pre-train模型中序列所有ID的的Embedding取avg池化，另一种是取最后一个点击ID的Embedding作为用户整体的表达。但是无论是哪种方式，都会对用户行为的整体表达有所损失。因此，我们借鉴了 Unsupervised Representation Learning 中的 Mutual Information Maximization 方法，该方法可以最大化表达向量与原始数据之间的信息相关性。在高维连续型数据中很难精确计算 MI，一般使用近似估量的方法，在这里，采用一种基于深度学习的估计方式 [Belghazi et al., 2018] ，基于KL-divergence 的 Donsker-Varadhan representation [Donsker and Varadhan, 1983] ，实现了MI的下界：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f95d5cc21ffe46a3d794.png"/></p>
<p>基于MI-Maximization，我们设计了一个新的用户向量表达模块。如图5所示，首先将Pre-train模型的最终结果，也就是图5中的 Click ID Embeddings 通过CNN，来生成用户的 Local Representation，然后将Local Embedding 通过 Pooling 融合成 User Representation，最后借鉴对比学习的思想，将User Representation 分别与自己和其他用户的 Local 向量做比较，训练判别器。这一段的描述可能不太清晰，有疑惑的读者可以看我们的源码。判别器的loss：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8ac824d7b36525ea4e42.png"/></p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1afa8f95d0b8e0004d6d.png"/></p>
<p>图5:  User Representation Module</p>
<p><br/></p>
<h2>实验效果</h2>
<p>在这里列出来我们的UDARec在两个公开数据集（由PeterRec所公开，数据来自于看点的真实业务数据）中的实验效果，评价指标 HR@5。可以看到，在PeterRec所提出的两个公开数据集上，我们的模型有着大幅度的提升。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/0c9e395deba587554fb6.png"/></p>
<p>表1: 实验效果</p>
<p>为了验证Adapter的效果，我们对比了在Fine Tune时进行全部Fine Tune 和加入Adapter Fine Tune的效果，从下图可以明显看出，Fine Tune All 模式会陷入过拟合。</p>
<div>
<div>
<div>
<div>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9a2daaae45ad8e5b2e58.png"/></p>
</div>
</div>
<p>     图6: Adapter 拟合效果</p>
<p><br/></p>
<h2>总结及展望</h2>
<p>UDARec 在PeterRec的启发之下，通过改进特征提取子模块、引入Adapter和非监督的对比学习模块，大幅度地提升了迁移学习在推荐领域的效果。当时（21年1月）是想投一下 SIGIR21的，思虑再三，效果虽然有大幅度的提升，但是大部分提升来自于将 NextItNet 换成了 Transformer-based Model，非监督性对比学习模块的作用有限，故而始终觉得 novelty 不太够，还是希望能有更扎实的成果之后再投出去。后来由于团队业务的调整，没有在迁移学习这个方向上继续深入下去，这个工作也就停在了21年1月份，也没来得及在团队业务上做更大规模的应用。现在略微整理一下，发在KM上，抛砖引玉，希望对正在做相关工作的同学能有些启发和帮助。</p>
<p>现在回过头来反思一下当时的工作，其实是在对比学习的爆发前夕就踩中了点，但是对学术界最新进展的调研不到位，过于专注在自己脑海中已有的知识中挖掘解决方案，没能多看看大佬们的最新工作。如果当时能更多地进行调研，参考下Hinton大佬的SimCLR [<em>Chen et al.,</em> 2020]，那么在对比学习这个点上一定可以做更深入的探索。</p>
</div>
</div>
<h2>参考文献：</h2>
<p>[<em>Yuan et al.,</em> 2019] Fajie Yuan, Alexandros Karatzoglou, Ioannis Arapakis, Joemon M Jose, and Xi- angnan He. 2019. A Simple Convolutional Generative Network for Next Item Recommendation. In Proceedings of the Twelfth ACM International Conference on Web Search and Data Mining. ACM, 582–590.</p>
<p><em>[Belghazi et al.,</em> 2018] Mohamed Ishmael Belghazi, Aristide Baratin, Sai Rajeshwar, Sherjil Ozair, Yoshua Bengio, De- von Hjelm, and Aaron Courville. Mutual information neu-ral estimation. In ICML, pages 530–539, 2018.</p>
<p>[<em>Donsker and Varadhan</em>, 1983] Monroe D Donsker and SR Srinivasa Varadhan. Asymptotic evaluation of certain markov process expectations for large time. iv. Communications on Pure and Applied Mathematics, 36(2):183–212, 1983.</p>
<p>[<em>Yuan et al.,</em> 2020]  Fajie Yuan, Xiangnan He, Alexandros Karatzoglou, Liguang Zhan. 2020 Parameter-Efficient Transfer from Sequential Behaviors for User Modeling and Recommendation. SIGIR, 1469–1478.</p>
<p>[<em>Houlsby et al.,</em> 2019]  Neil Houlsby, Andrei Giurgiu, Stanislaw Jastrzebski, Bruna Morrone, Quentin De Laroussilhe, Andrea Gesmundo, Mona Attariyan, and Sylvain Gelly. 2019. Parameter-Efficient Transfer Learning for NLP. arXiv preprint arXiv:1902.00751 (2019).</p>
<p>[<em>Chen et al.,</em> 2020] Ting Chen, Simon Kornblith, Mohammad Norouzi, and Geoffrey Hinton. 2020. A simple framework for contrastive learning of visual representations. In International Conference on Machine Learning (ICML), pages 1597–1607.</p>
<p><br/></p>
<p><br/></p> 
{% endraw %}
