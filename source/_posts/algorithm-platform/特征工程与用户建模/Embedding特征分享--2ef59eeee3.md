---
title: "Embedding特征分享"
date: 2022-04-06 17:29:27
categories:
  - 算法平台
  - 特征工程与用户建模
---

{% raw %}

<p>最近，在短视频排序模型中，用到了基于side information的视频embedding，side information指的是视频的一级目录，视频的二级类目，视频的标签。在排序模型中增加基于side information的embedding特征之后，离线的AUC和线上的拉新率，拉活率，渗透率等指标都有明显的提升。用户点击的视频有上下文承接关系，利用用户的点击视频序列训练出来的embedding有很好的聚类效果，相同类目下的视频聚类在一起，相似类目的视频在空间中很接近。这篇文章简单地介绍我们是如何利用side information构造视频的embedding,主要包括以下内容：</p>
<ol><li><b>基于side information 的视频embedding</b></li>
<li><b>基于side information 的用户和作者embedding</b></li>
<li><b>Incremental Skip-Gram Leaning</b></li>
<li><b>总结</b></li>
</ol><h3>1. 基于side information的视频embedding</h3>
<p>使用side infomation embedding主要是为了解决新视频的问题。如果简单的对视频ID使用skip-gram学习它的embedding特征，当新视频来的时候，无法获得新视频的embedding。在我们短视频中，视频的一级类目有几十个，视频的标签有几万个，在很长的一段时间内，视频的类目标签都是不会变化的，训练好视频的类目标签的embedding之后，可以长时间地使用。</p>
<p>我们先是学习了视频ID的embedding，之后转化为类目标签的embedding。没有直接对类目标签使用skip-gram模型来训练他们的embedding特征，主要是因为视频的类目太少，直接使用类目可能无法充分地训练。将一段时间内，一个用户点击过的视频组成这个用户的句子，这个句子中的token就是视频的ID，将所有用户的句子组成一个训练的数据集，之后使用skip-gram模型训练得到视频ID的embedding特征，embedding size的大小为8。下图是构造一个用户的句子的示意图，user_id为用户的编码，item_id为视频的编码，label为1表示用户点击了视频。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8639847f227905b19391.png"/></p>
<p>Fig1. 构造训练数据</p>
<p>从上面这个用户的sentence中选择出几个视频ID，观察用户点击的视频之间是否存在上下文关系：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e65299af33a40fb080ee.png"/></p>
<p>根据视频的ID，我们通过找到了对应的视频看，可以看到用户点击的视频存在前后承接的关系，两个相邻视频的内容很相似。用户在一个小的点击session中，表现出来了对“李现or杨紫”的强烈兴趣。在我们的推荐算法中，利用用户最近点击过的视频的平均embedding来进行召回，效果也是有提升的。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/cef7404d842a63a3e248.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6bc6a6e919453684c06b.png"/></p>
<p>Fig.2 用户点击的视频序列</p>
<p>使用TSNE对视频embedding进行降维可视化。从可视化的结果来看，同一个类目下的视频是聚在一起的；相似的类目，如“猫”和“狗”，“亲子互动”和“亲情”在空间中很接近；差异较大的类目离得较远，如“旅行Vlog”和“猫”。这还是很符合预期的，一个用户的兴趣可能就几种，有的用户喜欢“猫”，那这个用户可能看了很多个关于“猫”的视频，那我们学习出来关于猫的视频的“embedding”就会很相似，表现出来在空间中聚类在一起。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1d9e135dbfe9d36221fe.png"/></p>
<p>Fig.3 TSNE可视化视频Embedding</p>
<p>得到视频的embedding之后，需要转化为类目标签的embedding，这样，当有新的视频加入的时候，利用类目标签就可以计算出新视频的embedding。举个栗子，一段时间内，“生活”这个一级类目下有许多的视频，取这些视频的平均embedding向量作为“生活”这个类目的embedding向量。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6f7790891504437e6617.png"/></p>
<p>Fig.4 视频embedding转化为类目标签embedding</p>
<p>这样做的好处是在同一个语义空间做的加减运算，embedding的空间是不会变化，FM模型不需要重新学习embedding的空间分布。这个基于side information的视频embedding在推荐的手机QQ的公众号【手Q公众号】场景下做了A/B test实验，点击率提升+2%左右，其他指标也提升明显。</p>
<h3>2. 基于side infomation的用户和作者embedding</h3>
<p>利用视频的embedding(通过视频的类目标签计算得到），计算用户的embedding。将一段时间内一个用户点击过的视频平均embedding作为一个用户的embedding。时间段取长一点，用户的覆盖率会高一些，表达的主要是用户的一个比较长期的兴趣。时间段取短一点，用户的覆盖率会低一些，表达的主要是用户的一个近期的兴趣。例如用户最近一周内主要点击的都是关于“猫”的视频，那取一周内点击过的平均向量之后得到的用户的向量就在就和“猫”的向量很相似。这个特征在手Q公众号上了一个A/B test实验，实验效果提升明显。</p>
<p>也可以取作者近一个月内发布的视频的embedding的平均向量，作为作者的embedding。这样做的直觉是这样的，如果两个用户发布的视频相似，那么这两个作者的embedding也会相似，如果一个用户喜欢作者A，那么我们可以试着把与作者A相似的作者B推荐给该用户。这个还没有上实验，但是从离线的AUC指标来看，效果很好。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7bb1d12e5ef05a66944b.png"/></p>
<p>Fig.5 不同特征的离线AUC指标</p>
<p>”+“表示同时加入特征，例如”feed+user“表示同时加入视频embedding特征和用户embedding特征。我们将基于side information的视频embedding加到了公众号的召回中，在召回已经有了FM, word2vec的embedding的情况下还有明显的提升。</p>
<h3>3. Incremental Skip-Gram Embedding</h3>
<p>以上部分介绍的embedding，都是利用视频的类目标签的embedding。如果有新的类目标签加入怎么办？基于side information计算的视频embedding会丢失掉这一个信息。另外，如果不同视频的类目标签相同，这些视频的embedding将会完全一样，基于side information 计算出来的视频embedding区分能力有限。同时，基于side information计算出来的视频embedding很“稳定”，不管是一个月前计算这个视频的embedding，还是一个月以后计算这个视频的embedding，只有这个视频的类目标签没有发生过变化，计算出来的embedding特征就不会变化。出于这些方面的考虑，尝试用incremental skip-gram模型来直接训练视频ID的embedding，有新视频加入的时候，利用新的数据继续训练。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a6547783695ceefcada4.png"/></p>
<p>Fig.6 增量式训练embedding特征</p>
<p>Incremental skip-gram模型和传统的skip-gram模型的不同之处在于incremental skip-gram需要动态更新”单词“的分布，传统的skip-gram模型只需要在训练之前计算好”单词“的分布时候就不需要再更新，感兴趣的同学可以参考论文：<a href="https://aclweb.org/anthology/D17-1037">Incremental Skip-gram Model with Negative Sampling</a>。在利用该特征训练模型之前，分析过embedding的空间分布变化，如Fig.7和Fig.8所示。embedding的空间分布发生了变化，同一个视频在不同天之间的相似度很高。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6d4c04a9ddf8f00bf348.png"/></p>
<p>Fig.7 不同时期embedding空间分布</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/125e652b8e311d097543.png"/></p>
<p>Fig.8 视频相似度分布</p>
<p>这个特征主要是为了弥补基于side information计算的视频embedding的不足。在手Q公众号上了一个实验，实验结果正向，相对基于side information构造的一系列特征来说，这个特征的提升相对较小。</p>
<h3>4. 总结:</h3>
<p>基于side information 的视频embedding特征，直接对用户点击过的视频进行无监督训练，得到各个视频ID的embedding特征，能够很好的学习到视频之间的相似度。在手机QQ公众号场景下，线下提升了模型的AUC，线上明显地提升了各项核心消费指标。之后还可以尝试将用户点赞过的视频作为global context，训练embedding，为用户点赞过的视频提权。感谢lilillzhao的建议，metric learning也是一种新的思路，后续可以尝试。</p>
<p>以上就是我们推荐算法团队关于embedding特征的干货分享，非常感谢以下各位同事在embedding特征构造过程中提供的帮助：</p>
<p><strong>samuelqiu/menglaiwang/edisonwei/yueyanrong/sinohuang</strong></p>
<p>参考资料：</p>
<ol><li><a href="https://arxiv.org/pdf/1301.3781.pdf">Efficient Estimation of Word Representations in Vector Space</a> (original word2vec model)</li>
<li><a href="http://papers.nips.cc/paper/5021-distributed-representations-of-words-and-phrases-and-their-compositionality.pdf">Distributed Representations of Words and Phrases and their Compositionality</a></li>
<li><a href="https://arxiv.org/ftp/arxiv/papers/1603/1603.04259.pdf">Item2Vec: Neural Item Embedding for Collaborative Filtering</a></li>
<li><a href="https://www.kdd.org/kdd2018/accepted-papers/view/real-time-personalization-using-embeddings-for-search-ranking-at-airbnb">Real-time Personalization using Embeddings for Search Ranking at Airbnb</a></li>
<li><a href="https://nlp.stanford.edu/pubs/glove.pdf">GloVe: Global Vectors for Word Representation</a></li>
<li><a href="http://mccormickml.com/2016/04/19/word2vec-tutorial-the-skip-gram-model/">Word2Vec Tutorial - The Skip-Gram Model</a></li>
<li><a href="https://papers.nips.cc/paper/7368-on-the-dimensionality-of-word-embedding.pdf">On the Dimensionality of Word Embedding</a></li>
<li><a href="https://www.aclweb.org/anthology/D15-1036">Evaluation methods for unsupervised word embeddings</a></li>
</ol><p></p> 
{% endraw %}
