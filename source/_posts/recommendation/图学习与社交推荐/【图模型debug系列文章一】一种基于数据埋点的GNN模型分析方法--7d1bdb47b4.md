---
title: "【图模型debug系列文章一】一种基于数据埋点的GNN模型分析方法"
date: 2022-06-14 20:51:20
categories:
  - 推荐算法
  - 图学习与社交推荐
---

{% raw %}

<div>
<p><br/></p>
该方法是由本组Danieslin(林丹丹), Jerrycgsong(宋重钢) 及 Chrisyi(易玲玲)共同设计。</div>
<h2>一、背景</h2>
<p>在微信生态内，微信用户有着丰富的多种行为数据，比如公众号文章阅读、视频号短视频浏览、视频号直播观看等等。然而，在单一推荐场景内（比如直播推荐），往往存在冷启动问题：<strong>新用户或者低活用户在推荐场景内行为稀少，模型无法得到充分的学习，从而导致冷用户的推荐效果不佳</strong>。最近，笔者团队以GNN为技术基点，利用图的结构对微信用户在多个场景的交互行为（包括社交行为/短视频/公众号文章等等）进行描述，为多个业务场景提升了冷用户推荐效果。对于不同推荐场景，其模型细节可以参考GNN应用系列文章一】跨域推荐：异构GNN推荐算法。</p>
<p>然而，我们团队在GNN算法落地开发的时候，也面临着一个常见的问题：<strong>如何验证模型设计能够促进冷用户的推荐效果？</strong>一个简单粗暴的方法就是通过线上A/B test查看对应的指标，如果指标提升，那么就是有效果，反之亦然。比如，在推荐场景下，A/B测试后的指标有UCTR/PCTR等点击类指标，如果这些指标显著正向，算法设计者则认为算法有效，如果这些指标显著下降或者没有显著效果，算法设计者则认为算法无效，转而进行新一轮的模型开发。然而，这种验证方式是高成本的。有数据表明，业内100个A/B测试往往95个是没有效果的。然而，模型上线没有效果，并不代表模型的设计是不合理的，如果直接抛弃该算法，对算法工程师来说，技术收益非常低，不利于做技术沉淀。</p>
<p>本文主要分享一种GNN模型分析方法——<strong>埋点分析法</strong>，该方法着重于验证模型设计是否达到了跨域推荐的目标，即，模型设计是否提升了冷用户的推荐效果。该方法已在团队中实践，并助力了GNN跨域模型的推全。</p>
<h2>二、问题描述</h2>
<p>在此章节中，笔者将以团队在微信视频号直播业务（以下简称“直播”）中落地跨域GNN算法为例，展开详解。</p>
<p>在直播业务中，用户(user)对直播间(item)的交互行为，可以构造一张二分图，进行GNN算法计算。基于用户在其他微信业务场景内的交互数据（例如视频号短视频/公众号文章），我们设计了跨域GNN模型，模型设计的主要思路如下：</p>
<ul><li><b>两个用户如果在其他场景有相似的兴趣，那么他们在直播域内也有相似的兴趣。</b></li>
</ul><p>举个例子，在直播推荐中，对于一个冷用户U来说，U在直播域内的行为非常稀少，我们引入了视频号短视频的交互数据，模型设计的主要目的是<strong>希望能找到和U在视频号有相似兴趣的直播高活用户，再通过高活用户在直播域内的交互行为，增强冷用户U的学习</strong>。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/6fedd226ea06f2fe9658.png"/></p>
<p>为了加强域外信息在最终user embedding的表达，我们通常会通过多种手段来加强域外信息在user embedding的表达，比如追加对比loss或者追加AEloss【KDD 2021】针对冷启动问题的GNN模型。</p>
<p>为了查看这些模型结构的设计是否加强了域外信息的表达，是否对冷用户推荐起到了促进作用，我们设计了一种分析方式——埋点分析。</p>
<h2>三、埋点分析</h2>
<h3>1、基本思路</h3>
<p>为了验证模型是否达到了上述的设计目的，我们希望在直播域找到一对用户&lt;高活用户U1，冷用户U2&gt;，这两个用户在域外（即，视频号）有相似的兴趣，查看这两个用户的embedding是否靠近。然而，冷用户往往会有稀疏的直播域内行为，并且两个用户在域外的兴趣很难完全一致，可能对最终结果产生干扰。为了避免这种干扰，我们虚拟构造冷用户，<strong>保证这些冷用户在域内完全没有行为，并且域外行为与高活用户保持完全一致</strong>。</p>
<h3>2、具体做法</h3>
<p>详细地说，我们从直播域内的高活用户中抽取了1000个，这1000个用户有个共性：<strong>既有丰富的域内数据，又有丰富的域外数据</strong>。并且，为了保证这些用户在域内和域外均具有较多的数据，我们只选择在每个域的交互数据多于20条的用户。我们将这类用户标记为U1用户。接着，我们虚拟构造了1000个冷用户：</p>
<ul><li>U2: <strong>具有和域内1000个高活用户一样的域外数据和社交数据。</strong></li>
</ul><p>这1000对&lt;高活用户U1，冷用户U2&gt;，user embedding的metapath如下所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/ecbba690e1353e1594df.png"/></p>
<p>注意，我们这边所构造的1000个冷用户，均是使用了全新的user id。这样做的目的是为了避免了user id这个属性特征带来的模型训练偏差，更加地贴合实际场景。</p>
<p>最后，我们将这些冷用户加入模型参与训练，保证用户的数据都得到了充分的学习。</p>
<p>虚拟构造的冷用户个数设置得较少，是为了不大规模地影响原本模型的学习，另外在第五章节，我们会讨论一下如何设置冷用户个数。</p>
<h2>四、实验</h2>
<p>我们拿在直播业务中的三个GNN模型来阐述这个分析如何验证冷用户推荐效果。这三个GNN模型都使用了视频号域外信息，user embedding的设计如上所示，但模型结构上对加强域外信息有着不同设计。为了方便阐述，我们简单将这三个模型标记为：模型1， 模型2， 模型3. 三个模型的主要设计差异如下所示：</p>
<ul><li>模型1: 直接采用基本GAT框架，同时加入了用户在域内交互行为的AEloss来刻画冷用户</li>
<li>模型2: 和模型1基本结构一致，但增加了用户域外行为的AELoss</li>
<li>模型3: 和模型1基本结构一致，但将用户在域内行为的AELoss 和在域外行为的AEloss 区分开</li>
</ul><h3>1、离线评估指标</h3>
<p>离线评估的指标是：<strong>冷用户和其对应的高活用户在离线跨天召回表现上的相似度</strong>。具体来讲，对每一种用户，我们离线召回top100 items；接着，计算每对&lt;高活用户U1，冷用户U2&gt;的推荐结果交并比，<img alt="" loading="lazy" src="/logbook/images/recommendation/ecbb2c31ba62cdb8eeb1.png"/></p>
<p>最后，计算所有用户的重叠率均值，本文称作“<strong>重叠率_pv</strong>”。</p>
<p>另外，我们也设置了一种指标“<strong>重叠率_uv</strong>”：有至少一个item和其对应高活用户重叠的冷用户个数占所有冷用户总数的占比。</p>
<h3>2、离线评估数据</h3>
<p>评估数据如下：</p>
<table><tbody><tr><td>
<p>用户类型</p>
</td>
<td>
<p>模型</p>
</td>
<td>
<p>重叠率_pv</p>
</td>
<td>
<p>重叠率_uv</p>
</td>
</tr><tr><td>
<p>U2</p>
</td>
<td>
<p>模型1</p>
</td>
<td>
<p>8.49%</p>
</td>
<td>
<p>66.10%</p>
</td>
</tr><tr><td>
<p>U2</p>
</td>
<td>模型2</td>
<td>
<p>17.45%<br/></p>
</td>
<td>
<p>87.20%<br/></p>
</td>
</tr><tr><td>
<p>U2</p>
</td>
<td>
<p>模型3</p>
</td>
<td>
<p>18.78%</p>
</td>
<td>
<p>86.50%</p>
</td>
</tr></tbody></table><p><br/></p>
<p>从数据上，我们可以看到，不同的模型结构对冷用户的推荐效果是不同的。比如，模型1的重叠率不管是pv还是uv均远远低于模型2和模型3，说明模型2和模型3在域外信息的增强是起到更好的作用，增强了冷用户的学习。其次，模型2和模型3的效果是相差无几的，在重叠率_pv的表现上，模型3的效果稍好，但在重叠率_uv的表现上，模型2的效果稍好。这个现象说明模型2和模型3对域外信息增强的作用是差不多，大概率上线无法区分。</p>
<h3>2、线上A/B test</h3>
<p>接着，我们进行了线上小流量A/B test。</p>
<p>我们先将模型1作为对照组，模型2作为实验组，实验只覆盖非高活用户，实验数据如下：</p>
<table><tbody><tr><td>pctr</td>
<td>uctr</td>
<td>dau</td>
</tr><tr><td>+0.691%</td>
<td>+0.701%</td>
<td>+0.339%<br/></td>
</tr></tbody></table><p>实验数据表明，模型2在pctr/uctr/dau均有显著正向。这个实验结果说明，<strong>模型2的设计更能将两个有相似域外行为的用户embedding距离拉近，从而达到了使用域外数据解决冷启动的问题，与离线评估效果一致</strong>。具体的实验可以在X平台上找到：[内部或本地链接已移除]</p>
<p>接下来，我们将模型2作为对照组，模型3作为实验组，实验只覆盖非高活用户，实验数据没有显著指标。这个实验可以认为，<strong>模型2和模型3在实验效果上是持平的，这个和离线评估的数据也是对齐的</strong>。具体的实验可以在X平台上找到：[内部或本地链接已移除]</p>
<h2>五、结论及未来扩展</h2>
<p>本文介绍了一种GNN模型分析方法——埋点分析法。该方法以模型优化目标为主，详细阐述了如何针对跨域场景进行数据的虚拟构造。我们的方法在离线评估和线上A/B test取得了一致的结论，说明我们的分析方法是奏效的。目前这个方法可以适用于任何跨域GNN模型。</p>
<p>目前，我们这个分析方式有一个潜在的问题：没有严谨的统计学从理论上来验证“虚拟构造的冷用户既不会影响模型的训练又具备较高置信度的统计学意义”。主要原因有两个：一个是虚拟构造的冷用户会参与训练，如果虚拟的数据太多，可能会影响模型；另一个是在离线评估的时候，&lt;高活用户U1，冷用户U2&gt;的数量会影响评估质量，如果数量太少，可能统计结果置信度不高。因为评估质量是根据所有冷用户的平均交并比计算出来的，可以近似为正态分布，所以我们可以计算出预计置信度所需的虚拟构造用户。感兴趣的同学可以详细参考【微信x实验平台】假设检验方法</p>
<p>如果有任何问题和更好的分析方式，欢迎大家一起交流。</p>
<h2>六、参考文献</h2>
<ol><li>Fu, Xinyu, et al. "Magnn: Metapath aggregated graph neural network for heterogeneous graph embedding." <i>Proceedings of The Web Conference 2020</i>. 2020.<br/></li>
<li>Thomas N Kipf and Max Welling. 2017. Semi-supervised classification with graph convolutional networks. In International Conference on Learning Representations. 2873–2879.</li>
<li>William L. Hamilton, Rex Ying, and Jure Leskovec. 2017. Inductive Representation Learning on Large Graphs. In Advances in Neural Information Processing Systems. 1025–1035.<br/></li>
<li>Petar Veličković, Guillem Cucurull, Arantxa Casanova, Adriana Romero, Pietro Lio, and Yoshua Bengio. 2017. Graph attention networks. arXiv preprint arXiv:1710.10903 (2017).</li>
<li>Ying, Rex, et al. "Graph convolutional neural networks for web-scale recommender systems." <i>Proceedings of the 24th ACM SIGKDD international conference on knowledge discovery &amp; data mining</i>. 2018.<br/></li>
<li>Dong, Yuxiao, Nitesh V. Chawla, and Ananthram Swami. "metapath2vec: Scalable representation learning for heterogeneous networks." <i>Proceedings of the 23rd ACM SIGKDD international conference on knowledge discovery and data mining</i>. 2017.<br/></li>
<li>跨域推荐：异构GNN推荐算法</li>
</ol> 
{% endraw %}
