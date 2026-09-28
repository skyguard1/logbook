---
title: "CPM合约广告算法系统系列（五）：在线分配"
date: 2022-03-23 16:40:31
categories:
  - 算法
  - 广告算法
---

{% raw %}

<div>
<ul>
<li>第一章：概述</li>
<li>第二章：库存预估</li>
<li>第三章：库存模型</li>
<li>第四章：售卖分配</li>
<li>第五章：在线分配</li>
<li>第六章：频次模型</li>
</ul>
<h1>1       问题与背景</h1>
<p>通过之前介绍有关CPM合约广告算法系统的《概述》、《库存预估》、《库存模型》、《售卖分配》系列文章，想必大家对整个CPM合约广告算法系统有了一定的了解。本文作为系列文章的收官之作，将介绍广平CPM合约广告算法系统的《在线分配》是如何实现的。</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/21d11a0a0a0dececcac1.png"/></p>
<p>图1 广平CPM合约广告系统</p>
<p>       如图1所示，在线分配的输入主要分三部分：订单实时播放信息（Storm提供）、订单的属性信息（订单系统提供）、库存结构信息（“库存模型”提供）。</p>
<p>       在线分配的输出是给投放引擎提供订单的播放优先级以及订单的播放概率。当一个曝光到达的时候：</p>
<p>（1）       投放引擎对订单列表进行定向条件（静态）过滤、频次（动态）过滤。</p>
<p>（2）       投放引擎根据优先级将可用订单排序。</p>
<p>（3）       选取前n个订单。n的取值规则是，前n-1个订单概率和小于1，前n个订单概率和大于等于1。</p>
<p>（4）       将第n个订单的概率设为“1 - 前n-1个订单概率和”。如果所有订单概率和小于1，增加“空单”填满剩余概率。</p>
<p>（5）       根据概率选择订单投放。</p>
<h2>1.1   什么是在线分配问题</h2>
<p>在Yahoo计算广告学经典论文“Ad Serving Using a Compact Allocation Plan”中<sup>[1]</sup>，认为在线分配问题：A central problem facing online advertising systems is ad serving, i.e., deciding how to rapidly match supply (user visits) and demand (ads) in a way that meets an overall objective。</p>
<p>《计算广告》作者刘鹏在书中写到：在线分配问题指的是在通过对每一次广告展示进行实时在线决策，从而达到在满足某些量的约束的前提下，优化广告产品整体收益的过程。</p>
<p>最后，从系统实现的角度出发，本人认为在线分配问题就是：针对每一个曝光，如何决定候选订单的播放顺序以及播放概率，从而使得所有曝光的收益最大化。</p>
<p>面对在线分配问题，我们要做的就是：在<strong>某一时刻</strong>，获取<strong>剩余时间</strong>的库存结构（供应量及供给约束）以及订单信息（需求量及需求约束）；然后生成二部图<sup>[2]</sup>匹配问题以及相应约束条件的参数；最后求解得出针对每一个曝光，各订单的播放顺序和播放概率。</p>
<p>在线分配的供给与需求二部图匹配问题示意：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/f533285f79cbd8e7017c.png"/></p>
<p>图2 供给与需求二部图</p>
<p>求解图2所示供给与需求二部图匹配问题相当于求解以下最优化问题：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/06658a5f42dcffc7152f.png"/></p>
<p>s.t. <img alt="图示" loading="lazy" src="/logbook/images/algorithm/fc7c54e27af451aaf4d3.png"/> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/104db48a03af063e9f93.png"/>  </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/87a5225b5381ece17473.png"/> </p>
<p>上述二部图与最优化问题公式的具体介绍可以参考《售卖分配》中的问题背景。</p>
<h2>1.2   HWM算法的不足</h2>
<p>此前广平CPM合约广告系统采用的就是类似HWM算法的广平第二代投放算法。它的优先级是根据定向条件规则排序，比如定向地域内容的订单的优先级高于只定向地域的订单；“订单的概率”等于“订单需求量”除以“订单定向的可用库存”。但HWM算法无法很好的解决下述在线分配问题。</p>
<p>问题描述如下：</p>
<p><i>订单A</i><i>：需要400CPM </i><i>综艺频道库存。</i></p>
<p><i>订单B</i><i>：需要1000CPM </i><i>上海库存。</i></p>
<p><i>订单A</i><i>的优先级高于订单B</i><i>的优先级。</i></p>
<p><i>库存结构如图3</i><i>所示：</i></p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/c5018620f336011a395c.png"/></p>
<p>图3 库存结构示意图</p>
<p>按照HWM算法，订单A的400CPM需求量会均匀分配在上海北京，而定向了上海1000CPM的订单B只能得到800CPM库存，从而造成200CPM缺量。HWM分配结果如图4所示（浅绿色代表订单A，浅红色代表订单B）：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/74422198fee473526990.png"/></p>
<p>图4 HWM分配结果示意图</p>
<p>而在线分配的目标是使收益最大化，当各订单的惩罚因子相同时，就等同于缺量最小化。而上述在线分配问题处于图5所示的分配结果时，缺量为0。</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/5c684c77f55104bd5b5f.png"/></p>
<p>图5 最优分配结果示意图</p>
<p>为了实现图5的效果，就必须要打破高优先级订单的均匀分配，使优先级高的订单减少在拥挤维度的播放量。HWM算法无法解决这个问题，但Yahoo于2012年发表的SHALE算法<sup>[3]</sup>通过提出了维度优先级这个概念，使订单在不同维度有不同播放概率从而完美的解决此问题。</p>
<h1>2       基于SHALE的在线分配算法</h1>
<h2>2.1   算法特点</h2>
<p>相较之前的在线分配算法，SHALE算法率先提出了维度优先级的概念，使订单在不同维度的播放概率不同。从而解决拥挤维度的“超订”问题，减少总体缺量。</p>
<p>SHALE算法的订单优先级是根据<b>订单的需求量</b>除以<b>订单定向的可用库存</b>排序，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/22d27497592071598e95.png"/>越大，优先级越高。</p>
<p>SHALE算法的订单播放概率（<img alt="图示" loading="lazy" src="/logbook/images/algorithm/cf897044dcefdf920022.png"/>)是由公式<img alt="图示" loading="lazy" src="/logbook/images/algorithm/85be2cff2603faedad5f.png"/>决定，其中<img alt="图示" loading="lazy" src="/logbook/images/algorithm/4f0a79ae8f65258ca798.png"/>为订单平均播放概率，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/4839f4b95d65d991b24b.png"/><b>订单优先参数</b>，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c56b4d1d3af1d9fc145f.png"/>为<b>维度优先参数</b>，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c6e6dbb4bbccd57cc0d8.png"/>为相对订单价值（已知参数）。SHALE算法通过订单的需求量以及库存各维度的供给量进行迭代计算，求解<img alt="图示" loading="lazy" src="/logbook/images/algorithm/4839f4b95d65d991b24b.png"/>、<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c56b4d1d3af1d9fc145f.png"/>。经过多轮迭代，算法一般情况能够收敛，从而得到或接近最优解。</p>
<p>从以上算法简述中，可以看出为了求出优先级和概率，关键点在于<b>订单优先级</b>、<b>订单优先参数<img alt="图示" loading="lazy" src="/logbook/images/algorithm/fd8783dfcabc2e3446bd.png"/></b>、<b>维度优先参数<img alt="图示" loading="lazy" src="/logbook/images/algorithm/17abc1be8d26d02c932e.png"/></b>的计算。</p>
<p>（1）       <b>订单优先级</b>是根据<b>订单的需求量</b>除以<b>订单定向的可用库存</b>排序。</p>
<p>（2）       <b>维度优先参数<img alt="图示" loading="lazy" src="/logbook/images/algorithm/17abc1be8d26d02c932e.png"/></b>表示维度的拥挤程度，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/17abc1be8d26d02c932e.png"/>值越大代表维度越拥挤。</p>
<p>（3）       <b>订单优先参数<img alt="图示" loading="lazy" src="/logbook/images/algorithm/fd8783dfcabc2e3446bd.png"/></b>表示订单的挤占能力，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/fd8783dfcabc2e3446bd.png"/>值越大代表挤占能力越强。</p>
<p>关于<img alt="图示" loading="lazy" src="/logbook/images/algorithm/fd8783dfcabc2e3446bd.png"/>、<img alt="图示" loading="lazy" src="/logbook/images/algorithm/17abc1be8d26d02c932e.png"/>的意义举个简单例子，有在线分配问题如下：</p>
<p><i>订单A</i><i>定向上海100CPM</i><i>。</i></p>
<p><i>订单B</i><i>定向上海北京50CPM</i><i>。</i></p>
<p><i>上海库存100CPM</i><i>，北京库存100CPM</i><i>。</i></p>
<p>此时，上海维度超订，预订率150%，北京预订率25%；上海的<b>维度优先参数</b>大于北京。（“超订”原因可能是库存波动造成的库存预估误差）</p>
<p>而由于订单A的定向条件更严格，所以一般情况下订单A的<b>订单优先参数</b>大于订单B。</p>
<p>为了满足缺量最小化，经过迭代计算<img alt="图示" loading="lazy" src="/logbook/images/algorithm/fd8783dfcabc2e3446bd.png"/>、<img alt="图示" loading="lazy" src="/logbook/images/algorithm/17abc1be8d26d02c932e.png"/>，订单B在上海维度的<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a696780c13227f779920.png"/>将小于等于0（播放概率为0），即订单B被挤出了上海维度。</p>
<h2>2.2   算法模型</h2>
<p>SHALE算法是为了解决以下最优化问题而提出来的：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/e9eb96ed9c99c867512f.png"/></p>
<p>s.t. <img alt="图示" loading="lazy" src="/logbook/images/algorithm/fc7c54e27af451aaf4d3.png"/></p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/104db48a03af063e9f93.png"/> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/87a5225b5381ece17473.png"/></p>
<p>其中，i表示各库存维度的编号，j表示各订单的编号；<img alt="图示" loading="lazy" src="/logbook/images/algorithm/22bc21d335f9b40e604b.png"/>表示维度i的供应量，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c6e6dbb4bbccd57cc0d8.png"/>表示订单j的相对价值（已知参数），<img alt="图示" loading="lazy" src="/logbook/images/algorithm/4f0a79ae8f65258ca798.png"/>表示在一个曝光i到达后，订单j的播放概率<img alt="图示" loading="lazy" src="/logbook/images/algorithm/d4286ae3beadb4665eff.png"/>，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c0a72a43022e744b8838.png"/>；<img alt="图示" loading="lazy" src="/logbook/images/algorithm/6a57e6b9c34dc5dd09e5.png"/>表示订单j的缺量，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/6a57e6b9c34dc5dd09e5.png"/>表示订单j缺量后的惩罚因子；<img alt="图示" loading="lazy" src="/logbook/images/algorithm/cf897044dcefdf920022.png"/>表示维度i给订单j的库存比例，即我们要求的概率。</p>
<p>传统的最优化算法求解上述问题太慢，而HWM启发式算法虽然快但牺牲了准确性。SHALE算法综合两者的优点，经过多次迭代，就能逼近最优解，如果不进行迭代，则SHALE算法退化为HWM算法。</p>
<p>SHALE算法基于求解对偶变量，求解的任意对偶变量都是原始问题（primal problem）的一组最优解。论文作者对求解对偶变量的步骤进行了优化，采用原始对偶方法迭代进行求解，每次迭代的过程中改善对偶解。其中，对偶变量即为<img alt="图示" loading="lazy" src="/logbook/images/algorithm/4839f4b95d65d991b24b.png"/>订单优先参数，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c56b4d1d3af1d9fc145f.png"/>维度优先参数。</p>
<p>SHALE算法是从HWM算法发展而来，分为2部分：第一部分计算合适的对偶变量（<img alt="图示" loading="lazy" src="/logbook/images/algorithm/4839f4b95d65d991b24b.png"/>，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c56b4d1d3af1d9fc145f.png"/>）；第二部分将对偶变量带入原问题求解（<img alt="图示" loading="lazy" src="/logbook/images/algorithm/cf897044dcefdf920022.png"/>）。</p>
<p>以下是算法伪代码，其中<img alt="图示" loading="lazy" src="/logbook/images/algorithm/f7986e74576c3de568f7.png"/>：</p>
<p>步骤一：迭代计算对偶变量（<img alt="图示" loading="lazy" src="/logbook/images/algorithm/4839f4b95d65d991b24b.png"/>，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c56b4d1d3af1d9fc145f.png"/>）</p>
<p>迭代计算直到超过迭代次数:</p>
<p>1.       循环每一个维度i，找到<img alt="图示" loading="lazy" src="/logbook/images/algorithm/4839f4b95d65d991b24b.png"/>满足：</p>
<p>                <img alt="图示" loading="lazy" src="/logbook/images/algorithm/46ec7b8b9c07f8a512ea.png"/></p>
<p> 如果<img alt="图示" loading="lazy" src="/logbook/images/algorithm/117985e2a9f34ad6c346.png"/>或者解不存在，则设<img alt="图示" loading="lazy" src="/logbook/images/algorithm/6e96145bf52a1a1402d0.png"/></p>
<p>2.       循环每一个订单j，找到<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c56b4d1d3af1d9fc145f.png"/>满足：</p>
<p>                 <img alt="图示" loading="lazy" src="/logbook/images/algorithm/ce60d0d2f26332fb102e.png"/></p>
<p>                     如果<img alt="图示" loading="lazy" src="/logbook/images/algorithm/5c108deabda81235f5fe.png"/>或者解不存在，则设<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a4a27293fff1aaf18f2e.png"/></p>
<p>步骤二：</p>
<p>1.       设每个维度初始供应量剩余比例<img alt="图示" loading="lazy" src="/logbook/images/algorithm/6ba8299f3eb6b34a52f1.png"/>=1（100%)</p>
<p>2.       循环每一个维度i，找到<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c56b4d1d3af1d9fc145f.png"/>满足：</p>
<p>                 <img alt="图示" loading="lazy" src="/logbook/images/algorithm/46ec7b8b9c07f8a512ea.png"/></p>
<p> 如果<img alt="图示" loading="lazy" src="/logbook/images/algorithm/117985e2a9f34ad6c346.png"/>或者解不存在，则设<img alt="图示" loading="lazy" src="/logbook/images/algorithm/6e96145bf52a1a1402d0.png"/></p>
<p>3.       按优先级顺序循环每一个订单j：</p>
<p>a)         找到<img alt="图示" loading="lazy" src="/logbook/images/algorithm/8fa2aa1c4f1ac4fc28a9.png"/>满足：</p>
<p>                 <img alt="图示" loading="lazy" src="/logbook/images/algorithm/3ffff81a7e313ec70549.png"/></p>
<p> 如果解不存在，则设<img alt="图示" loading="lazy" src="/logbook/images/algorithm/8fa2aa1c4f1ac4fc28a9.png"/>等于无穷大</p>
<p>b)        循环每一个订单j定向的维度i，更新：</p>
<p>                 <img alt="图示" loading="lazy" src="/logbook/images/algorithm/fd2d68b0964d8bd2817e.png"/></p>
<p>步骤三：</p>
<p>       输出每个订单的<img alt="图示" loading="lazy" src="/logbook/images/algorithm/4839f4b95d65d991b24b.png"/>，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/8fa2aa1c4f1ac4fc28a9.png"/>以及每个维度的<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c56b4d1d3af1d9fc145f.png"/>       </p>
<h1>3       算法与广平业务的结合</h1>
<h2>3.1   核心思想</h2>
<p>SHALE是一个理论上快速求解在线分配问题的算法。但在实际应用中，我们面对的要求远远比论文中描绘的复杂。比如更多更复杂的库存维度、播放控制上广告主的各种细致需求。</p>
<p>因此，我们在SHALE算法基础上结合广平业务需求设计并实现了广平第三代投放算法。广平的第三代投放算法作为业内领先的在线分配系统，基本满足了广告主的各种需求，例如：广告位的联合投放、人群定向、投放周期内各天的播放曲线、每天各小时的播放曲线、单用户观看次数（频次）、贴片定向、多贴不重复、CPD包段、人工优先级、白金客户等。</p>
<p>上述需求主要分两部分：</p>
<p>（1）       <b>订单定向的可用库存的精确计算</b>：包括频次、人群定向、贴片定向、多贴不重复、CPD包段、广告位的联合投放等。</p>
<p>（2）       <b>订单播放曲线的控制</b>：包括投放周期内各天的播放曲线、每天各小时的播放曲线等。</p>
<h2>3.2   解决方案</h2>
<p>针对<b>（</b><b>1</b><b>）订单定向的可用库存的精确计算</b>，在线分配使用的方法与售卖分配相同，为了减少维度数量，采用了基础维度进行<b>属性合并</b>、特殊维度（频次，多贴不重复，人群包定向等）乘以<b>相关衰减系数</b>。具体见《库存结构》、《售卖分配》，此处不再赘述。</p>
<p>在线分配算法对<b>（</b><b>2</b><b>）订单播放曲线的控制</b>主要在于优先级的分层，即优先层级：</p>
<p>（1）       <b>优先层级</b>的含义：处于高优先层级的订单的优先级一定高于处于低优先层级的订单。订单优先层级的划分是根据订单的需求量来的，订单的需求量分为保底量、多播量、提量、冲高量；不同量对应不同的优先层级。处于保底播放阶段订单的优先级一定高于处于多播播放阶段订单的优先级，依次类推。</p>
<p>（2）       由于售卖分配询量下单是针对一段时间，不同订单的排期区别和排期交叉会导致每天预订率的不同。<b>冲高保底策略</b>就是为了解决订单投放周期内“天与天之间”的挤占以及“各天之间”的播放曲线提出的。简言之，订单每天有最小播放量（保底量），最大播放量（冲高量）；保底量是每天必须完成的量，冲高量就是如果该天预订率低，仍有多余的库存，就继续播冲高量。</p>
<p>（3）       此外，为了满足“订单在一天内各小时均匀播放”的需求，在线分配算法计算了两种<b>播放曲线</b>（平滑播，尽快播）以及每个小时的最大可播量。当某一时刻订单的播放量超过该时间段的最大可播量，订单将会临时停单。</p>
<h1>4       效果验证</h1>
<h2>4.1   效果指标</h2>
<p>在线分配的目标是使收益最大化，目前各订单保价保量，惩罚因子相同，收益最大化就等同于缺量最小化。因为保量原则，缺量又称为需补偿量，简称补量。因此、在线分配算法的<b>补量率</b>就是业务的关键指标。</p>
<p>广平第三代投放算法以SHALE算法为核心，以<b>维度挤占</b>为特色，所以拥挤维度中“通投订单”所占比例的变化也是重要的评价指标。</p>
<h2>4.1  效果展示</h2>
<p>4月初，广平第三代广告投放算法全流量上线。通过在视频广告投放问题中反复试验优化，新算法大幅提高了库存利用效率，降低了补量率，明显提升了变现效率。上线前后2个月的对比数据如表1所示，上线后在售卖率提升的条件下，无论是CPM补量率还是订单补量率都大幅下降。整体CPM补量率由9.8%下降至6.1%，重点城市CPM补量率由18.3%下降至9.1%。</p>
<div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/69f0fe8997e5d7078958.png"/></div>
<p>表1 广平第三代广告投放算法上线效果表</p>
<p>如图6所示，新算法上线后，内容定向订单在重点城市的播放比例明显下降，在北上广的播放比例相对下降约50%，新算法将内容定向订单尽量分配到了其它非重点城市投放。</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/e5a3f824245d85b02b54.png"/></p>
<p>图6 内容定向订单（地域通投）在地域维度播放比例</p>
<p>同样，地域定向订单在稀缺内容纬度的播放比例下降，在综艺、电影、电视剧纬度的播放比例相对下降约15%，算法将地域定向订单尽量分配到了非稀缺内容纬度投放。如图7所示：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/2fb4d33a70f68176d602.png"/></p>
<p>图7 重点城市定向订单（内容通投）在内容维度播放比例</p>
<h1>参考文献<o:p></o:p></h1>
<p>[1] P. Chen, W. Ma, S. Manalapu, C. Nagarajan, S. Vassilvitskii, E. Vee, M. Yu, and J. Zien. Ad serving using a compact allocation plan. Proceedings of the 13th ACM Conference on Electronic Commerce. 2012, 1(212): 319-336.<br/>[2] zh.wikipedia.org/wiki/二分图<br/>[3] V. Bharadwaj, P. Chen, W. Ma, C. Nagarajan, J. Tomlin, S. Vassilvitskii, E. Vee, and J. Yang. Shale: an efficient algorithm for allocation of guaranteed display advertising. In KDD, 2012.</p>
</div> 
{% endraw %}
