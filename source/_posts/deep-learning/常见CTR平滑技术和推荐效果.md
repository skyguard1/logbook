---
title: "常见CTR平滑技术和推荐效果"
date: 2022-05-08 08:40:10
categories:
  - deep-learning
---

<p><span style=""></span></p>
<p><span>一般</span>ctr 的计算方式：</p>
<p><span style=""></span></p>
<p><span>也就是</span>&nbsp;</p>
<p><span style=""></span></p>
<p>对于系统来说，应该推荐<span>CTR</span><span>高的</span>item. <span>但是，</span><span>CTR</span>置信不置信，取决于曝光的次数。如果曝光量很小，那么这个高<span>CTR</span>就不可信。系统需要在考虑ctr 特征的同时兼顾曝光置信。</p>
<h1>平滑技术一：手工平滑</h1>
<p>从上图可以看出，被大量推的<span>item </span><span>量小，而</span>ctr 会降低。针对系统曝光<span>item</span>的特点，将曝光分为不同的层级，不同曝光层级的<span>item</span>，取最近24小时的数据，利用<span>min_max</span>方式进行归一化后，再加入到系统中进行推荐。</p>
<p><span style=""></span></p>
<h1>平滑技术二：指数平滑</h1>
<p>手工平滑的缺点是，需要手动的根据系统的特点，设计出适应系统的曝光分段。并且曝光分段难以自动增长，难以考虑<span>item </span>整个生命周期中的曝光情况。而单纯的对<span>item</span>的历史表现进行累积，又会使系统对<span>item</span>的最近表现不敏感. 因此，可以对<span>item </span>的历史曝光和点击进行平滑：</p>
<p><span style=""></span></p>
<p><span style=""></span></p>
<p><span style=""></span>表示<span>item N </span>个小时的曝光数据，<span style=""></span>表示<span>item N </span>个小时的点击数据。计算<span>item N </span>个小时平滑曝光点击数据：</p>
<p><span style=""></span></p>
<p><span style=""></span></p>
<p><span style=""></span></p>
<p><span>同理可得：</span></p>
<p><span style=""></span></p>
<p>这样就可以得到平滑后的<span>CTR</span>：</p>
<p><span style=""></span></p>
<p>实际系统在使用时，为了过滤掉低置信<span>item</span>的影响，对<span style=""></span><span>的</span><span>item</span>不进行召回。（1000 是经验值）</p>
<h1>平滑技术三：威尔逊平滑</h1>
<p>从前面可以看到，无论是手工平滑还是指数平滑，都需要按照经验值去掉一些低置信的item. <span>而</span>1927 年美国数学家<span>Edwin Bidwell Wilson </span>提出的威尔逊区间，可以解决小样本准确性的问题。它的计算公式为：</p>
<p style="">&nbsp;</p>
<p>其中，表示<span>item</span><span>的</span><span>CTR, n</span>表示曝光次数，一般情况下，在95% 的置信水平下，z 统计量的值为1.96。计算<span>CTR</span>的时候，我们取下限值。当n比较大的时候，下限值会趋近于，而当n比较小，这个下限值会小于。</p>
<h1>平滑技术四：贝叶斯平滑</h1>
<h2>贝叶斯平滑原理</h2>
<p><span>CTR</span>的贝叶斯平滑算法是雅虎的工程师发明的[1]。贝叶斯估计的基本过程为：先验分布+ 数据的知识= 后验分布，预测的<span>CTR</span>不仅与C和I有关，也跟超参数α、β 有关。预测的<span>CTR</span>计算公式为：</p>
<p><span style=""></span></p>
<h2>贝叶斯平滑解法</h2>
<p><span>参数</span>α、β的估计方法有矩估计、<span>Fixed-point iteration</span>、EM, 我们直接利用了矩估计的计算公式计算超参数α、β：</p>
<p><span style=""></span></p>
<p><span style=""></span></p>
<p>其中，<span style=""></span>表示<span>CTR</span>均值，<span style=""></span>表示<span>CTR</span>方差。在实现过程中，我们将指数平滑和贝叶斯平滑结合起来计算平滑后的<span>CTR.</span></p>
<h1>业务效果比较</h1>
<p><span style=""></span></p>
<p>其中，6306是按照曝光平滑进行特征处理，6317是按照威尔逊平滑进行特征处理，6320是按照贝叶斯平滑进行特征处理。</p>
<p><span>可以看出，效果上</span>威尔逊平滑&gt;曝光平滑&gt;贝叶斯平滑。</p>
<h1>结论和展望</h1>
<p>虽然从最后的效果上来看，在我的实现中，威尔逊平滑比贝叶斯平滑的效果好，这并不能代表威尔逊平滑的效果比所有贝叶斯平滑的效果都要优秀。因为在计算贝叶斯平滑特征时，这个业务场景的<span>item </span>曝光分布及其长尾，头部<span>item</span>获得了大量曝光，使得计算参数α、β需要去掉一些无曝光、低曝光的<span>item</span>，获得合理的参数值。而却掉超低置信的<span>item</span>是个手工调节的过程，最终的效果可能会受到手工调节的影响。但这也是威尔逊平滑的便捷之处，无需调节更多的参数，就可以平滑特征在低曝光时的效果。从热播这个业务场景看，只需要曝光&gt;10, 威尔逊特征平滑最后的得分已经<span>make sence.</span></p>
<h1>参考资料</h1>
<p>[1]&nbsp;<span>Wang, Xuerui, et al. "Click-through rate estimation for rare events in online advertising."</span>&nbsp;<i><span>Online multimedia advertising: Techniques and technologies</span></i>. IGI Global, 2011. 1-12.</p>
<p><span>[2]</span>&nbsp;<a href="https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval"><span>https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#Wilson_score_interval</span></a></p>
