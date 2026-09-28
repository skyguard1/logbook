---
title: "QQ浏览器：小说召回中的DSSM模型优化实践（三）"
date: 2022-04-18 15:23:18
categories:
  - deep-learning
---

{% raw %}

<h2><img alt="" loading="lazy" src="/logbook/images/deep-learning/c97647fc76c237e001ca.png"/></h2>
<h2>一. 背景介绍</h2>
<p>在上一篇文章《QQ浏览器：小说召回中的DSSM模型优化实践（二）》里我们已经详细讲解了以点击为目标的DSSM召回模型，但是在小说推荐场景，点击其实只是用户很浅的小说行为，我们更关注的是如何让用户产生真正的阅读。在这样的背景下，我们希望可以搭建一个以阅读为目标的模型，无奈现实是骨感的，用户真实阅读的样本数远远小于推荐系统展现给用户的数量，同时有真实阅读的用户也仅占全量用户的一小部分，即存在数据稀疏问题（data sparsity,DS）。由此，我们考虑将点击和阅读相结合，用点击数据帮助训练阅读指标，多目标召回模型也就应运而生。</p>
<h2>二. 多目标召回模型的演进</h2>
<h3>1. 初版模型：添加辅助loss</h3>
<p>当我们要同时考虑点击和阅读效果时，最直观易行的方式就是先保持DSSM双塔结构不变，在原有的点击单目标loss基础上，加入阅读的辅助loss，希望模型在训练用户与点击书籍的向量相似度的同时，提升用户与阅读书籍的相似度。具体loss公式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/438262ad19029ad92f59.png"/></p>
<p>这样做的优点比较明显，操作简单易行，同时可以有效的防止过拟合。但模型的问题也显而易见，因为两者的embedding是完全共享的，我们的美好预期是一个embedding就可以既表达点击又表达阅读，但是实际由于点击和阅读向量本身会存在一定差异，强行用一个embedding表示，可能会同时折损两方信息，最后事倍功半。从离线效果评估来看，这版的指标也确实没有明显的效果，由此说明，还是要对模型结构做出一定调整，来适配多目标的需求。</p>
<p>离线指标：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/ac42aca1f9b612ccc116.png"/></p>
<p></p>
<h3>2. 基于多塔结构的多目标召回模型：</h3>
<p>由前面的离线验证效果可知，双塔结构一定程度会束缚模型对user和item的表达，这时很自然的就想到，需要用多塔来进行user和item的表征，但如何在“互相掣肘”和“互不干预”之间找到平衡，是多目标模型一直在力求解决的问题。我们这里同时尝试了多种模型构造方式。</p>
<p>1）四塔结构：这里是借鉴ESSM的思想，只共享底层embedding look-up table，上层用两个塔分别训练两个label对应的embedding向量。这里是希望在embedding层面完全将两个label的训练分开，只在计算loss的时候做两者的聚合，优点是不会再出现上面提到的“相互掣肘”的情况，缺点是没有解决阅读label样本稀疏问题，会导致对应user embedding的过拟合问题。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/24c67b903dfd4983c6ed.png"/></p>
<p>2）三塔结构：在上面四塔结构的基础上，将user合并为一个塔训练，item用两个塔分别训练两个label对应的embedding。这里的考虑还是阅读label的样本稀疏问题，所以user tower选择将两个目标合并训练，而相对来讲书籍的稀疏性并不明显，所以可以保留书籍侧的双塔双目标结构。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/d3cbc810115cea61fa50.png"/></p>
<p>下面是两个结构的离线指标，可以看出两者在点击和阅读的hit ratio（即召回率指标）都有小幅的提升，但也都不显著。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9f5f85f5792e3eefb07b.png"/></p>
<h3>3.基于MMOE的多目标召回模型</h3>
<p>到目前为止，我们其实只是在“互相掣肘”和“互不干预”之间相互摇摆，还远没有达到“相辅相成”的程度。不论是Share Bottom Model的模型结构，还是soft参数共享的相关结构，都或多或少也存在现在的问题。那么该如何让两个目标既能相互作用，又能保留自己的独特信息呢？这时MMOE模型进入了我们的视野。</p>
<p>MMOE结构如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/5ecc34cd0c05b024d3fb.png"/></p>
<p>由于很多文章都已经介绍过MMOE模型，在此我就不再赘述了，对我们的场景进行MMOE的适配后，离线实验效果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/2f3ebcca8613cdda2a4a.png"/></p>
<p>可以看到借鉴mmoe结构的离线效果最好，于是我们选取这版模型上线实验，实验效果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/718464f2fb698f6f9907.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/7408defe7432e58605a5.png"/></p>
<h2>三. 后续优化</h2>
<p>1. 多目标loss的不同组合方式：目前我们只采用了简单的线性加权，在确定模型结构后对权重值做微调，但其实这里的花样是很多的，比如用时长作为label的加权，或者ESSM一样的乘积方式等等，这里我们后续也会做更多的尝试。</p>
<p>2.模型结构的尝试：我们现有的优化逻辑，都是基于最初的单目标版本层层改进，但其实很多其他类型的模型结构都没有尝试过，比如阿里从MIND到ComiRec的Capsule网络系列等。</p>
<p>多目标召回领域还有很多东西可以实践探索，非常欢迎感兴趣的朋友们一起交流共同进步。</p>
<p></p>
<p>参考文献：</p>
<p><em>[1] Huang, Po-Sen, et al. "Learning deep structured semantic models for web search using clickthrough data." Proceedings of the 22nd ACM international conference on Information &amp; Knowledge Management. 2013.</em></p>
<p><em>[2] Ma, Jiaqi, et al. "Modeling task relationships in multi-task learning with multi-gate mixture-of-experts." Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery &amp; Data Mining. 2018.</em></p>
<p><em>[3] Ma, Xiao, et al. "Entire space multi-task model: An effective approach for estimating post-click conversion rate." The 41st International ACM SIGIR Conference on Research &amp; Development in Information Retrieval. 2018.</em></p> 
{% endraw %}
