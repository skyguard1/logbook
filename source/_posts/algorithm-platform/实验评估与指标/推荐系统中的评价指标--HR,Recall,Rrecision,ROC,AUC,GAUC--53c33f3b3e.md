---
title: "推荐系统中的评价指标--HR,Recall,Rrecision,ROC,AUC,GAUC"
date: 2022-04-15 15:28:01
categories:
  - 算法平台
  - 平台工程与评估
---

{% raw %}

<p>推荐系统中离线评价指标抽象总结为三大类：<br/>评分评估指标：用于对预测的评分进行评估，适用于评分推荐任务，如mse，mae等<br/>集合评估指标：用于对推荐的item集合进行评估，适用于Top-N任务，如HR等<br/>排名评估指标：按排名列表对推荐效果进行加权评估，既适用于评分推荐任务也可用于Top-N任务， 如NDCG等<br/>三大类之间并无严格的界限，本文关注于常用的几个指标及概念，包括：HR,Recall,Rrecision,ROC,AUC,GAUC</p>
<p>推荐系统常包含召回、精排等部分，其中召回部分常用HR@k作为评价指标，下面就先介绍HR</p>
<h1>Hit Ratio(HR)</h1>
<article><div>
<h2>用户粒度：</h2>
</div>
<div>如果推荐列表中有这个用户点击过的物品，那么我们记一次 ， 就是 占所有用户的比例。另外，这个指标也会结合leave one out测试场景。例如用户u点击过n个物品，则取前n-1个物品作为训练集，最后1个用于测试。模型在测试中将给出一个长度为k的推荐列表，当列表中有测试集中对应的物品时，则说明预测成功，但hit rate + leave one out测试会比较困难。那么hit rate就定义为这种测试方法下测试成功的用户个数 除以 用户总数。具体公式如下：</div>
<div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/71d549ac3568f80da801.png"/></div>
<div>where #hits is the number of users whose test item appears in the recommended list。分母#users是测试集中全体用户的个数。</div>
<div>
<h2>item粒度：</h2>
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/46ba19184839858a0ae2.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6caafc4f238bb3d2d694.png"/></div>
</article></div>
<div>
<h2>在top-K推荐中的另一种表示方式：</h2>
</div>
<div>
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9a4403bfd13fe374fcc0.png"/><br/></div>
</article></div>
<div>分母是所有的测试集合，分子表示每个用户top-K列表中属于测试集合的个数的总和。</div>
<div>例如：三个用户在测试集中的商品个数分别是10，12，8，模型得到的top-10推荐列表中，分别有6个，5个，4个在测试集中，那么此时HR的值是</div>
<div>(6+5+4)/(10+12+8) = 0.5。</div>
<div>
<h1>准确率和召回率</h1>
</div>
<div>这两个指标一般来多用于二分类任务，先说大家较熟悉的混淆矩阵，</div>
<div>
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/0bbd983dc1d00792452c.png"/><br/></div>
</article></div>
<div>Precision = TP/(TP+FP)</div>
<div>Recall = TP/(TP+FN)</div>
<div>Precision有时也被称为精度，Recall这个通常叫召回，这个很容易让人和“召回算法”联系起来。Precision和Recall的直观理解如下：</div>
<div>
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b8093596a2780dc39ee3.png"/><br/></div>
</article></div>
<div>对比item粒度的HR，其实这里分子是相同的，都是命中的item数量；分子也是相同的，即全部的相关的item数量。所以，两者本质是相等的。只不过，HR@k会有一个k的问题，在top-K推荐中。<br/></div>
<div>换个角度对比，HR是直接从集合的角度来评估效果；Recall值是从二分类的角度，对每一个item的打标结果评分；经过加和汇总可以发现，两个算的是一个东西。</div>
<div>
<h1>ROC和AUC</h1>
</div>
<div>还是基于上面的混淆矩阵，仔细观察Precision和recall的公式可以发现，混淆矩阵中的TN没有被用到。存在即合理，所以没用到就有点不合理，是否有更合理的用法。所以，有了下面两个概念：</div>
<div>TPR = TP/(TP+FN)</div>
<div>纵坐标是真阳性率（True Positive Rate, TPR），TP+FN是真实正样本的个数，也就是混淆矩阵第一行。换句话说是：正样本被预测对的概率</div>
<div>FPR = FP/(FP+TN)</div>
<div>假阳性率（False Positive Rate, FPR），FP+TN是真实负样本的个数，也就是混淆矩阵第二行。换句话说是：负样本被预测错的概率</div>
<div>
<h2>ROC曲线</h2>
</div>
<div>ROC曲线（Receiver operating characteristic curve）这个曲线的名字乍一看比较奇怪，给人的感觉就不像是纯正的数学统计名词；</div>
<div>ROC曲线首先是由二战中的电子工程师和雷达工程师发明的，用来侦测战场上的敌军载具（飞机、船舰），也就是信号检测理论。之后很快就被引入了心理学来进行信号的知觉检测。数十年来，ROC分析被用于医学、无线电、生物学、犯罪心理学领域中，而且最近在机器学习（machine learning）和数据挖掘（data mining）领域也得到了很好的发展。</div>
<div>ROC在绘制过程中是由多个点连接而成，其中横坐标是负样本中被预测为正样本的概率，纵坐标是正样本中被预测为正样本的概率，因此图上的点横坐标越小越好，纵坐标越大越好，换句话说 每个点越靠近左上角越好。示例图像如下：
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2bc6b5c139ba7addc1c4.png"/><br/></div>
</article></div>
<div>对于二分类问题，分类模型往往在最后给出一个0~1的概率值，因此我们要手动设定一个阈值，当模型的输出概率大于这个阈值时，预测为正样本，否则预测为负样本；设定不同的阈值，我们就会得到多个点，最后将得到的电连接起来就得到了ROC曲线，曲线上的点离对角线（虚线）越远，表示此阈值下FPR越大于TPR，进而表明在此阈值下所有被模型预测为正样本的样本本身是正样本的概率越大，也就表明模型的预测效果越好。当所有点距离对角线的距离</div>
<div>越远无疑由这些点连成线下的面积也就越大，而这个面积就是AUC</div>
<div>根据上面的推到可知，AUC越大，一个被模型预测为正样本的样本，真正属于正样本概率越大</div>
<div>
<h2>AUC的计算：<a href="https://zhuanlan.zhihu.com/p/84350940"></a></h2>
</div>
<div>实际上，这可以理解为一种积分过程，积分的内容是啥呢：每个预测为正的样本，能比多少个负样本大；积分所在的区域是啥呢？实际是正样本和负样本的交叉，也即：正样本数∗负样本数。
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/af79b993b3e4f316f216.png"/><br/></div>
</article></div>
<div>如上图，正样本和负样本是两个互不纠缠的正态分布，其中有M个正样本，N个负样本。阈值如果遍历所有正样本，则每个正样本都比N个负样本大，因此，积分下来，就是N+N+N+…+N = M * N，而积分的区域是M * N，因此，这种理想状态下，得到了AUC为：
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c688252a63dcdb149dd0.png"/><br/></div>
</article></div>
<div>相应的一般情况下的计算公式类似，举例如下：
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1612cdf5d17e39f4196a.png"/><br/></div>
</article></div>
<div>p=0.9的真实正样本，它在所有5个负样本前面，因此记为5</div>
<div>p=0.8的真实正样本，它在所有5个负样本前面，因此记为5</div>
<div>p=0.7的真实正样本，它在所有5个负样本前面，因此记为5</div>
<div>p=0.6的真实正样本，它在4个负样本前面，因此记为4</div>
<div>p=0.4的真实正样本，它在3个负样本前面，因此记为3</div>
<div>交叉区域记为5*5=25</div>
<div>因此最终的AUC记为：
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/92f19ad6828bdb301be8.png"/><br/></div>
</article></div>
<div>
<h2>AUC的问题与GAUC：</h2>
</div>
<div>传统的AUC可以评判二分类，但是推荐领域要算的是对于每个人的二分类结果；而每个人的预测分相对独立，互相比较没有太多意义。例如：</div>
<div>
<table><colgroup><col/><col/><col/></colgroup><tbody><tr><td></td>
<td>
<div>商品1（正）</div>
</td>
<td>
<div>商品2（负）</div>
</td>
</tr><tr><td>
<div>用户a</div>
</td>
<td>
<div>0.6</div>
</td>
<td>
<div>0.5</div>
</td>
</tr><tr><td>
<div>用户b</div>
</td>
<td>
<div>0.4</div>
</td>
<td>
<div>0.3</div>
</td>
</tr></tbody></table></div>
<div>从每个用户的角度（单行的看）：正样本预测值都大于负样本预测值，即0.6&gt;0.5且0.4&gt;0.3，所以模型推荐是没问题的。</div>
<div>但从AUC的整体二分类角度（所有数据放一起看）：存在负样本预测值大于正样本（0.5&gt;0.4）的情况，所有计算得到的auc的值并不是1，也就是模型并不完美。</div>
<div>基于这个问题，人们提出了GAUC指标，计算公式如下：
<article><div><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/92441e3550d044d3c992.png"/><br/></div>
</article></div>
<div>GAUC（group auc）实际是计算每个用户的auc，然后加权平均，最后得到group auc，这样就能减少不同用户间的排序结果不太好比较这一影响。</div>
<div><br/></div>
<div><br/></div>
<div><br/></div>
<div>参考资料：</div>
<div>[内部或本地链接已移除]</div>
<div>
<div><a href="https://blog.csdn.net/rebecca1809/article/details/122202234?spm=1001.2101.3001.6650.7&amp;utm_medium=distribute.pc_relevant.none-task-blog-2~default~BlogCommendFromBaidu~Rate-7.pc_relevant_default&amp;depth_1-utm_source=distribute.pc_relevant.none-task-blog-2~default~BlogCommendFromBaidu~Rate-7.pc_relevant_default&amp;utm_relevant_index=12">https://blog.csdn.net/rebecca1809/article/details/122202234</a></div>
<div><a href="https://www.modb.pro/db/103248">https://www.modb.pro/db/103248</a></div>
<div><a href="https://zhuanlan.zhihu.com/p/355343322">https://zhuanlan.zhihu.com/p/355343322</a></div>
<div><a href="https://zhuanlan.zhihu.com/p/84350940%20https://mp.weixin.qq.com/s?__biz=MzUzMTQ4MTU3OA==&amp;mid=2247484156&amp;idx=1&amp;sn=e1e0d541411b8147d3b2775ae3adfcf0">https://zhuanlan.zhihu.com/p/84350940 https://mp.weixin.qq.com/s?__biz=MzUzMTQ4MTU3OA==&amp;mid=2247484156&amp;idx=1&amp;sn=e1e0d541411b8147d3b2775ae3adfcf0</a></div>
<br/></div>
<div><br/></div>
<div><br/></div>
<div><br/></div>
</article><p><br/></p>
<p><br/></p> 
{% endraw %}
