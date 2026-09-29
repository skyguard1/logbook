---
title: "搜索中的排序(二)—Learning to Rank"
date: 2022-04-18 14:27:15
categories:
  - deep-learning
---

{% raw %}

<div>
<p>Learning to Rank（以下简称LTR）是搜索排序中经典的机器学习算法。</p>
<h2><b>LTR</b><b>训练数据获取</b></h2>
<p>       LTR数据获取的方式主要有两种：人工标注和日志文件挖掘。</p>
<p>       人工标注：随机抽取query，并对返回的结果按照相关性进行分档标注，一般会分为5挡左右(perfect、excellent、good、fail、bad)。这种方式标注的label是较为准确的，但是费时费力。</p>
<p>       日志挖掘：搜索引擎有大量的用户行为日志可供挖掘，可以通过一定的规则来获取训练数据标签，最常见的规则就是点击与否。这种方式获取数据较为容易，但是人工拍规则会引入噪声导致label不准确。</p>
<p>       两种方式对query的抽取都需要保证随机，既要保证有热门query也要有长尾query。由于热门query的点击行为较丰富，容易构造数据，因此如果从日志挖掘的话，一定要兼顾长尾query数据。LTR模型主要解决的是相关性的排序，因此模型中大多是query和文档的相关性系列特征，这些特征是与点击无关的，这和CTR模型不同，没有ID特征用来做记忆，所以LTR模型作用在于泛化，能够优化长尾query的排序效果。</p>
<h2><b>LTR</b><b>算法类型</b></h2>
<p>       LTR算法主要包括三种类别：PointWise，PairWise，ListWise。</p>
<p><b>1.       </b><b>PointWise</b></p>
<p>PointWise方法只考虑给定query下，单个文档的绝对相关程度。这种方法将排序问题直接转化成了经典的分类或者回归问题，不考虑到其他文档和query的相关度，看重的是对象的绝对准确性，然而排序问题更看重对象的相对准确性。</p>
<p><b>2.       </b><b>PairWise</b></p>
<p>PairWise方法是考虑给定query下，两个文档之间的相对相关度，也即将任意两个相关性不同的文档构造出pair对，学习出偏序关系。这种方法相比于pointwise方法有一定改进，但是和真正衡量排序效果的一些指标可能存在很大差异。</p>
<p><b>3.       </b><b>ListWise</b></p>
<p>ListWise方法直接考虑给定query下优化文档集合的整体序列，较好的克服了上面两种方法的缺陷。</p>
<p>几种经典的LTR算法包括：RankSVM、GBRank、IRSVM、RankNet、LambdaRank、AdaRank、LambdaMART。其中LambdaMART是性能较好的listwise类型的LTR算法，它基于LambdaRank和MART算法，而LambdaRank又是基于RankNet改进的，所以介绍LambdaMART之前先了解下该算法如何从RankNet和LambdaRank演进而来。</p>
<h2><b>RankNet</b></h2>
<p>       上一篇文章中提到搜索排序模型的常见评价指标都无法求梯度，RankNet将不适宜用梯度下降求解的Ranking问题转化为对概率的交叉熵损失函数的优化问题，从而适用梯度下降方法。</p>
<p>       假设有一个带参数的打分函数：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/f3db06b5a1bc3e10ee91.png"/></p>
<p>根据打分函数，可以计算文档<img alt="" loading="lazy" src="/logbook/images/deep-learning/9c44e8818dbc66b8d37a.png"/>和<img alt="" loading="lazy" src="/logbook/images/deep-learning/28c1d15c0d00bfe2bc2b.png"/>的得分(<img alt="" loading="lazy" src="/logbook/images/deep-learning/576a19015214181a1555.png"/>的label应不同)：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/c73aaa7515cddc21590c.png"/></p>
<p>那么二者的偏序概率为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/3072c82fd7c2213d4160.png"/></p>
<p>其中<img alt="" loading="lazy" src="/logbook/images/deep-learning/fa55b92690186d31da4b.png"/>表示文档<img alt="" loading="lazy" src="/logbook/images/deep-learning/9c44e8818dbc66b8d37a.png"/>应该排在文档<img alt="" loading="lazy" src="/logbook/images/deep-learning/28c1d15c0d00bfe2bc2b.png"/>前面，从公式可以看出，如果<img alt="" loading="lazy" src="/logbook/images/deep-learning/0d4548b51bfb408b7a1f.png"/>越大，<img alt="" loading="lazy" src="/logbook/images/deep-learning/1a5b532902d847b6170e.png"/>越大，也即<img alt="" loading="lazy" src="/logbook/images/deep-learning/f501b3bcc00d3627c223.png"/>比<img alt="" loading="lazy" src="/logbook/images/deep-learning/099f5bb7010843286ad7.png"/>分越高，<img alt="" loading="lazy" src="/logbook/images/deep-learning/9c44e8818dbc66b8d37a.png"/>越应该排在<img alt="" loading="lazy" src="/logbook/images/deep-learning/28c1d15c0d00bfe2bc2b.png"/>前面。于是交叉熵损失函数定义为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/0fd190b6e1b71bff2a39.png"/></p>
<p>记<img alt="" loading="lazy" src="/logbook/images/deep-learning/4f41b9b3da5916c8778c.png"/>，1表示文档i比文档j更相关，-1表示文档j比文档i更相关，0表示两者相关程度一样，那么<img alt="" loading="lazy" src="/logbook/images/deep-learning/e382cf5109b5235c778a.png"/>，于是损失函数可以表示为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/69a7ff5689f1796efc39.png"/></p>
<p>求导：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/8464bf37c270953dee89.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/f622a3907c9cccc32a46.png"/></p>
<p>于是梯度下降更新参数：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/6610058d2ac097f855a8.png"/></p>
<p>注意上面<img alt="" loading="lazy" src="/logbook/images/deep-learning/608e982439087ae10c48.png"/>的更新是针对一个样本对<img alt="" loading="lazy" src="/logbook/images/deep-learning/976096a35a151ff6a87a.png"/>计算的，也即用SGD更新权重，每计算一个pair对则会更新一次参数，而RankNet实际上采用的是mini-batch更新的方式。</p>
<h3><img alt="" loading="lazy" src="/logbook/images/deep-learning/ba798c58a989c3282d42.png"/><b>的定义</b></h3>
<p>       对上述<img alt="" loading="lazy" src="/logbook/images/deep-learning/608e982439087ae10c48.png"/>的梯度公式，我们引入：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/0fdebf6af6c2bc2d7929.png"/></p>
<p>这里<img alt="" loading="lazy" src="/logbook/images/deep-learning/04421017aef338b66e15.png"/>可以理解为损失函数关于<img alt="" loading="lazy" src="/logbook/images/deep-learning/3fa5195fbeb3e788b2c2.png"/>的梯度，于是：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/8b17d240ce7ad5b8e9fa.png"/></p>
<p>进一步的，<img alt="" loading="lazy" src="/logbook/images/deep-learning/608e982439087ae10c48.png"/>在整个数据集上的损失函数梯度为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/ecbaf6fff48aaa99df6e.png"/></p>
<p>公式中<img alt="" loading="lazy" src="/logbook/images/deep-learning/d22bee9eb2bd4ff3d726.png"/>表示所有不同label的文档对的集合，而<img alt="" loading="lazy" src="/logbook/images/deep-learning/17b9baf02ce2f4c3f112.png"/>表示包含文档i的所有pair对的<img alt="" loading="lazy" src="/logbook/images/deep-learning/04421017aef338b66e15.png"/>之和，即：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1aaccef6f1c97f7333eb.png"/></p>
<p>公式拆成了两项，<img alt="" loading="lazy" src="/logbook/images/deep-learning/47707dce335903ff36aa.png"/>表示与文档i构成pair对且文档i排在前的集合，而<img alt="" loading="lazy" src="/logbook/images/deep-learning/d5ae30f6e10d4a487400.png"/>表示与文档i构成pair对且文档i排在后的集合。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/17b9baf02ce2f4c3f112.png"/>可以理解为文档i在列表中需要调序的强弱与方向，其值取决于文档i与列表中其他文档的相对相关程度，如果文档i相关度高，那么与文档i构成pair的集合中i排在前的pair对偏多，<img alt="" loading="lazy" src="/logbook/images/deep-learning/17b9baf02ce2f4c3f112.png"/>越大，越需要往前调序，相反则越需要向后调序。</p>
<p>引入<img alt="" loading="lazy" src="/logbook/images/deep-learning/17b9baf02ce2f4c3f112.png"/>后，参数更新的方式变成了计算每个文档的<img alt="" loading="lazy" src="/logbook/images/deep-learning/17b9baf02ce2f4c3f112.png"/>值并累计，一次更新完，而传统的SGD方法是每计算一个pair对的梯度就更新一次参数。</p>
<p>至此RankNet介绍完了，它可以理解为一个排序方法的框架，定义了偏序学习的方法，告诉我们如何绕开NDCG等无法求导的评价指标得到一个可用的梯度，梯度反映了某条结果需要调序的强弱和方向，但是它不关心具体的模型是什么，即<img alt="" loading="lazy" src="/logbook/images/deep-learning/f3db06b5a1bc3e10ee91.png"/>可以自行定义。</p>
<h2><b>LambdaRank</b></h2>
<p>       不难发现RankNet实质是在优化pair对的error数量，使其尽可能减少，但对于NDCG这样的评价指标来说，error数量减少并不一定是最优的优化方向。</p>
<p>       下图中每条横线代表一个文档，蓝色的表示相关的文档，灰色表示不相关。在一次迭代后，RankNet将文档的顺序从左边调整到了右边，于是优化的结果是逆序对从13降到了11，下一次迭代两个相关文档的移动趋势如黑色箭头所示，但是这真的是最优的优化方向吗？在搜索中我们通常更关注前几条结果的相关性，这在NDCG等指标中也有所体现，所以左边调整到右边的优化并不是我们所希望的，红色箭头的调整趋势才是我们希望的。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1bb202528704e1d58b5e.png"/></p>
<p>       LambdaRank巧妙地将指标（例如NDCG）直接加到了梯度中，即：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9bc12985d19a6abb4bb8.png"/></p>
<p>其中<img alt="" loading="lazy" src="/logbook/images/deep-learning/14cb7370ef4bb8a5220e.png"/>表示只交换文档i和j的位置前后，列表的NDCG值的变化。</p>
<p>       对于pair对<img alt="" loading="lazy" src="/logbook/images/deep-learning/5f9d4b75bda16250edad.png"/>，有<img alt="" loading="lazy" src="/logbook/images/deep-learning/523427c3a642d86dcbd1.png"/>，则：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/043baa3ab8e967520d38.png"/></p>
<p>       对于pair对<img alt="" loading="lazy" src="/logbook/images/deep-learning/d6846dd13e5a1e3e1ab0.png"/>，有<img alt="" loading="lazy" src="/logbook/images/deep-learning/de39e55a59e3570efae0.png"/>，则：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/dbadbbe927b8524fa0ec.png"/></p>
<p>       于是<img alt="" loading="lazy" src="/logbook/images/deep-learning/17b9baf02ce2f4c3f112.png"/>也可以方便的计算出来。</p>
<p>       由于模型训练的关键不是损失函数而是梯度，因此LambdaRank绕开了损失函数，直接定义梯度，反推下LambdaRank的损失函数：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/8daba9097f8cc8e4cb7d.png"/></p>
<p>实际上LambdaRank也可以将任意评价指标加入到梯度中。</p>
<h2><b>LambdaMART</b></h2>
<p>       LambdaMART顾名思义是将LambdaRank和MART结合在一起，我们知道MART是一个框架，定义了模型，但是缺少损失函数，缺少梯度，只要损失函数可导（XGBOOST中要求一二阶可导）；而LambdaRank也是一个框架，定义了损失函数，定义了梯度，但缺少模型；二者正好完美互补，结合在一起便是LambdaMART。下图是LambdaMART算法流程：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/a2edb56d3598cf004995.png"/></p>
<h2><b>LambdaMART</b><b>使用</b></h2>
<p>       XGBOOST中实现了排序学习的解决方案。在使用中将配置文件定义好Objective、树的相关参数以及评价指标，除了提供训练数据之外还需要定义group文件，group文件指明了每个query下的列表长度。</p>
<p>由于XGBOOST中优化还用到了二阶导信息，而<img alt="" loading="lazy" src="/logbook/images/deep-learning/04421017aef338b66e15.png"/>只是一阶导，我们来求下二阶导。这里假设对pair对<img alt="" loading="lazy" src="/logbook/images/deep-learning/5f9d4b75bda16250edad.png"/>求导，此时<img alt="" loading="lazy" src="/logbook/images/deep-learning/523427c3a642d86dcbd1.png"/>，于是：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/62645f5e0c358dd7cad8.png"/></p>
<p>其中：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/c824d828d0daecff30b4.png"/></p>
<p>那么：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/64007f5ac282ab21a247.png"/></p>
<p>二阶可导，于是LambdaMART成功植入XGBOOST。</p>
<h2><b>参考文献</b></h2>
<p>[1] Burges, Christopher JC. "From ranknet to lambdarank to lambdamart: An overview." Learning 11.23-581 (2010): 81.</p>
</div> 
{% endraw %}
