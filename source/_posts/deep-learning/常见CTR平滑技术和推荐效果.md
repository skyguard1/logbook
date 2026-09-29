---
title: "常见CTR平滑技术和推荐效果"
date: 2022-05-08 08:40:10
categories:
  - deep-learning
---

{% raw %}

<p></p>
<div>
<p>在推荐的点击场景中，CTR特征属于关键特征。对于曝光量小会导致CTR 置信度不足，低置信和高置信的CTR特征加入到模型中，会导致模型对低置信的item过度泛化、高置信的item不够泛化，影响推荐效果。本文介绍几种常见的CTR平滑技术，同时给出在业务上的实验效果，供同事参考。</p>
<h1>问题描述</h1>
<p>在我们的业务场景中，item 的ctr 在曝光量置信（大于1k曝光）后，平均ctr 随着曝光量的增大而降低。如果对ctr 不做任何处理，直接加入到推荐中，会导致系统对低置信的item过度泛化、高置信的item不够泛化。而item 的质量并不会因为曝光量的增加而下降。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/6630b9f327ccc55be02a.png"/></p>
<p>一般ctr 的计算方式：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/53c1ad97321b8553ebba.png"/></p>
<p>也就是 </p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/ac11581da1a8e0f469ce.png"/></p>
<p>对于系统来说，应该推荐CTR高的item. 但是，CTR置信不置信，取决于曝光的次数。如果曝光量很小，那么这个高CTR就不可信。系统需要在考虑ctr 特征的同时兼顾曝光置信。</p>
<h1>平滑技术一：手工平滑</h1>
<p>从上图可以看出，被大量推的item 量小，而ctr 会降低。针对系统曝光item的特点，将曝光分为不同的层级，不同曝光层级的item，取最近24小时的数据，利用min_max方式进行归一化后，再加入到系统中进行推荐。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/d7b5202ca00a373a6fd0.png"/></p>
<h1>平滑技术二：指数平滑</h1>
<p>手工平滑的缺点是，需要手动的根据系统的特点，设计出适应系统的曝光分段。并且曝光分段难以自动增长，难以考虑item 整个生命周期中的曝光情况。而单纯的对item的历史表现进行累积，又会使系统对item的最近表现不敏感. 因此，可以对item 的历史曝光和点击进行平滑：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/35c1d1128ac2dbe25811.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/199bf5ca26089888d9ea.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9f460fa2ba62ec8bc16e.png"/>表示item N 个小时的曝光数据，<img alt="" loading="lazy" src="/logbook/images/deep-learning/cb7d52d81b43606d2313.png"/>表示item N 个小时的点击数据。计算item N 个小时平滑曝光点击数据：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/06536cdc58355c7ceb22.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/091a9d60c016da36cb1b.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/102cce9ef0b9546c0f1d.png"/></p>
<p>同理可得：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/ec46d1131a7c35350ab2.png"/></p>
<p>这样就可以得到平滑后的CTR：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/a5c28982296a1d6e94d3.png"/></p>
<p>实际系统在使用时，为了过滤掉低置信item的影响，对<img alt="" loading="lazy" src="/logbook/images/deep-learning/ebd95a01bd5b88aee4b6.png"/>的item不进行召回。（1000 是经验值）</p>
<h1>平滑技术三：威尔逊平滑</h1>
<p>从前面可以看到，无论是手工平滑还是指数平滑，都需要按照经验值去掉一些低置信的item. 而1927 年美国数学家Edwin Bidwell Wilson 提出的威尔逊区间，可以解决小样本准确性的问题。它的计算公式为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9471849a427c7dbfe282.png"/> </p>
<p>其中，表示item的CTR, n表示曝光次数，一般情况下，在95% 的置信水平下，z 统计量的值为1.96。计算CTR的时候，我们取下限值。当n比较大的时候，下限值会趋近于，而当n比较小，这个下限值会小于。</p>
<h1>平滑技术四：贝叶斯平滑</h1>
<h2>贝叶斯平滑原理</h2>
<p>CTR的贝叶斯平滑算法是雅虎的工程师发明的[1]。贝叶斯估计的基本过程为：先验分布+ 数据的知识= 后验分布，预测的CTR不仅与C和I有关，也跟超参数α、β 有关。预测的CTR计算公式为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/a6a8052c9208ab550223.png"/></p>
<h2>贝叶斯平滑解法</h2>
<p>参数α、β的估计方法有矩估计、Fixed-point iteration、EM, 我们直接利用了矩估计的计算公式计算超参数α、β：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/2b1ca46c5d0c282f81b8.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/b1a5aa9c8eebab537160.png"/></p>
<p>其中，<img alt="" loading="lazy" src="/logbook/images/deep-learning/107ad65000b783fd066c.png"/>表示CTR均值，<img alt="" loading="lazy" src="/logbook/images/deep-learning/ee00e64b2bb0e697948f.png"/>表示CTR方差。在实现过程中，我们将指数平滑和贝叶斯平滑结合起来计算平滑后的CTR.</p>
<h1>业务效果比较</h1>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/7b91be80982f3af88a45.png"/></p>
<p>其中，6306是按照曝光平滑进行特征处理，6317是按照威尔逊平滑进行特征处理，6320是按照贝叶斯平滑进行特征处理。</p>
<p>可以看出，效果上威尔逊平滑&gt;曝光平滑&gt;贝叶斯平滑。</p>
<h1>结论和展望</h1>
<p>虽然从最后的效果上来看，在我的实现中，威尔逊平滑比贝叶斯平滑的效果好，这并不能代表威尔逊平滑的效果比所有贝叶斯平滑的效果都要优秀。因为在计算贝叶斯平滑特征时，这个业务场景的item 曝光分布及其长尾，头部item获得了大量曝光，使得计算参数α、β需要去掉一些无曝光、低曝光的item，获得合理的参数值。而却掉超低置信的item是个手工调节的过程，最终的效果可能会受到手工调节的影响。但这也是威尔逊平滑的便捷之处，无需调节更多的参数，就可以平滑特征在低曝光时的效果。从热播这个业务场景看，只需要曝光&gt;10, 威尔逊特征平滑最后的得分已经make sence.</p>
<h1>参考资料</h1>
<p>[1] Wang, Xuerui, et al. "Click-through rate estimation for rare events in online advertising." <i>Online multimedia advertising: Techniques and technologies</i>. IGI Global, 2011. 1-12.</p>
<p>[2] <a href="https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval">https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval</a></p>
</div> 
{% endraw %}
