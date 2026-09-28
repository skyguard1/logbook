---
title: "CPM合约广告算法系统系列（四）：售卖分配"
date: 2022-03-23 16:38:58
categories:
  - 算法
  - 广告算法
---

{% raw %}

<ul>
<li>第一章：概述</li>
<li>第二章：库存预估</li>
<li>第三章：库存模型</li>
<li>第四章：售卖分配</li>
<li>第五章：在线分配</li>
<li>第六章：频次模型</li>
</ul>
<h1>1　 售卖分配背景与问题</h1>
<h2>1.1　什么是售卖分配系统</h2>
<p>在CPM广告系统中，带有各种属性标签的曝光流量即为系统的库存。在有了多维度流量库存的预估及其精确描述后（见同系列文章：库存预估和库存模型），售卖分配系统主要基于该库存描述进行库存的管理，并根据库存的应用类型建立相应的事务进行处理，保持系统的库存分配情况维持在一个最佳的状态。在功能层面，售卖分配系统提供了订单分配、下单以及订单询量等功能，保障了CPM合约广告从预订、询量到下单等多个投放前流程的顺利运行；在业务层面，通过分析订单定向、库存利用情况等系统数据为优化CPM合约广告变现业务决策提供数据支撑。作为衔接CPM合约广告售卖侧和投放侧的关键系统，售卖分配系统从优化库存利用效率、辅助定价、提高分配和投放一致性等多个层面为合约广告系统的发展提供了技术支撑。<o:p></o:p></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/30403fc8be9a27880b7d.jpg"/></p>
<p>图1　CPM合约广告系统系统架构</p>
<h2>1.2　售卖分配面临的问题</h2>
<p>　　售卖分配系统主要解决的问题是对于一组具有合约量和受众定向约束的订单在给定的预估库存下，对每个订单按照其定向条件和需求量分配展示库存，并在此基础上不断优化系统的整体利润。对于合约广告库存分配问题，我们可以使用如下供需二部图<sup>[2]</sup>进行描述：       </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm/41805f9f66cb3d3970d5.png"/></p>
<p>图2　售卖分配供需二部图</p>
<p>　　上图描绘出了广告活动中的三个参与主体：广告（a）、用户（u）和媒体环境（c）在担保式（GD：Guarantee Delivery）系统中的所处位置。其中：Supply侧节点<img alt="图示" loading="lazy" src="/logbook/images/algorithm/9d6ffcee46a763d71636.png"/>点表示供应节点，代表某类定向下的广告曝光，Demand节点<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a366b5c8331ed7bf001b.png"/>表示需求节点，代表某类订单需求。对于需求节点<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a366b5c8331ed7bf001b.png"/>，若<img alt="图示" loading="lazy" src="/logbook/images/algorithm/9d6ffcee46a763d71636.png"/>节点代表的受众标签满足其定向需求，则在<img alt="图示" loading="lazy" src="/logbook/images/algorithm/9d6ffcee46a763d71636.png"/>和<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a366b5c8331ed7bf001b.png"/>之间建立连线。因此，整个二部图我们可以用<img alt="图示" loading="lazy" src="/logbook/images/algorithm/ef964a74eeff8a167b97.png"/>表示，其中<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c3c62c8f6a62b6fe5324.png"/>为所有供应节点<img alt="图示" loading="lazy" src="/logbook/images/algorithm/9d6ffcee46a763d71636.png"/>与需求节点<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a366b5c8331ed7bf001b.png"/>之间的供求关系集合。对于售卖库存分配系统而言，其主要任务就是求解<img alt="图示" loading="lazy" src="/logbook/images/algorithm/1c75c6ea0579bdcd500d.png"/>到<img alt="图示" loading="lazy" src="/logbook/images/algorithm/b46d7e447ccc313477e2.png"/>的分配比例，使得满足供给方和需求约束的同时，系统整体的收益函数目标值最大：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/8b94299af3e65902eb3a.jpg"/></p>
<p>其中<img alt="图示" loading="lazy" src="/logbook/images/algorithm/babde5a33a25656f3b2f.png"/>表示<img alt="图示" loading="lazy" src="/logbook/images/algorithm/9d6ffcee46a763d71636.png"/>节点分配给订单<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a366b5c8331ed7bf001b.png"/>的库存比例，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/2e5e7b0d00622ceea4eb.png"/>表示将展示<img alt="图示" loading="lazy" src="/logbook/images/algorithm/9d6ffcee46a763d71636.png"/>按照<img alt="图示" loading="lazy" src="/logbook/images/algorithm/babde5a33a25656f3b2f.png"/>给的比例分配给订单<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a366b5c8331ed7bf001b.png"/>所带来的收益。对于单个订单<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a366b5c8331ed7bf001b.png"/>而言，我们把Supply侧所有满足<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a366b5c8331ed7bf001b.png"/>需求的供给节点<img alt="图示" loading="lazy" src="/logbook/images/algorithm/1c75c6ea0579bdcd500d.png"/>的集合用<img alt="图示" loading="lazy" src="/logbook/images/algorithm/7101da969604b4c64d80.png"/>表示，用<img alt="图示" loading="lazy" src="/logbook/images/algorithm/379700876c948e147262.png"/>代表Demand侧所有和供给节点<img alt="图示" loading="lazy" src="/logbook/images/algorithm/9d6ffcee46a763d71636.png"/>存在供需关系的需求节点<img alt="图示" loading="lazy" src="/logbook/images/algorithm/b46d7e447ccc313477e2.png"/>的集合。</p>
<p>　　由公式（1.1）我们可知库存分配问题的本质目标是优化一组流量上的利润，由于存在需求量的限制，因此该问题是一个带约束的最优化问题。最优化问题主要解决如何在众多可行的方案中找出最优的方案，其问题一般包含两部分内容: 1）既定的目标函数和 2）针对该目标函数自变量的一组约束条件：                                          </p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/77a492636fc91ca9056f.jpg"/></p>
<p>　　对于最优化问题来说，无约束优化问题的求解是最优化问题求解的基础。通常，带约束条件的最优化问题在一定条件下可以转化为无约束条件的优化问题来求解，其中最常用的转换方法是拉格朗日法<sup>[3]</sup>：拉格朗日算法根据约束条件的类型，通过使用拉格朗日乘子和KKT条件，可以将一个带约束的优化问题转化为一个不带约束的基本优化问题,再利用无约束优化中的一些经典算法如梯度下降法、牛顿法等，最终得到问题的最优解。</p>
<h1>２　 基于HWM的库存分配与询量算法</h1>
<p>本文讨论的合约广告售卖分配问题属于带约束最优化框架下分配问题，但由于进一步引入了订单需求量的约束，使得其相对一般的最优化问题而言更为复杂。在讨论具体的算法之前我们先简单介绍下售卖分配系统所面临解决的主要问题：<o:p></o:p></p>
<p>1)     已下单库存分配扣减：对所有已下GD订单，按照当天预估库存以及订单定向条件，将订单预定库存分配到具体的库存结构上，使得已下单整体缺量最小。<o:p></o:p></p>
<p>2)     带定向订单询量最大可用库存：为新订单计算在其定向条件下的剩余最大可用库存量，并引导客户在该最大可用库存值范围内下单。<o:p></o:p></p>
<p>本章将从上述两个问题出发，简述售卖分配系统在上述两个模块的实现。</p>
<h2>2.１　解决订单库存分配问题  </h2>
<p>　　由于合约广告按照约定的Cpm价格结算，当所有订单的需求量已知时，系统的整体收益（<img alt="图示" loading="lazy" src="/logbook/images/algorithm/7b27f2b0667def960406.png"/>）是固定的，那么上述售卖分配面临问题转化为在目标函数值固定的条件下求解可行解的问题，其公式化描述如下式：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7880c0cd03ceb4886447.jpg"/></p>
<p>　　上述问题是一个典型的带线性约束的最优化问题。根据第一节介绍的最优化知识，我们可以应用拉格朗日乘子法等方法来求解。然而在CPM合约广告系统中，由于支持订单定向的条件较为复杂（已支持地域、内容、平台、性别、年龄、时间、场景等7个维度的交叉定向，人群、渠道等多个附加维度的非交叉定向），订单数量长期保持在千级别，使得系统中摊平后的供给节点的数目达到十亿级别，边<img alt="图示" loading="lazy" src="/logbook/images/algorithm/df748b5bef935239d31d.png"/>的量级在百亿级以上，这就使得分配问题变得过于复杂而不能直接利用相关经典算法快速的得到有效解，因此需要一种快速高效的分配算法解决方案。</p>
<p>　　为了解决订单已知需求量情况下求解有效分配解的问题，我们引入了HWM（High Water Mark）算法<sup>[1]</sup>。HWM算法最初由Yahoo！的工程师们于2012年提出，是针对计算广告领域的一种启发式的、轻量快速的合约广告在线分配算法。该算法对于上述二部图描述的分配问题提出了两点关键性的启发规则：</p>
<p>1)     根据需求订单定向下可用库存的紧缺程度，确定订单之间的分配优先级，高优先级订单优先进行分配。<o:p></o:p></p>
<p>2)     计算每个需求订单<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a366b5c8331ed7bf001b.png"/>提供在其优先级下的播放比例值<img alt="图示" loading="lazy" src="/logbook/images/algorithm/98f65174c2e3dcd6dd77.png"/>，在投放时可以仅凭该播放比例<img alt="图示" loading="lazy" src="/logbook/images/algorithm/98f65174c2e3dcd6dd77.png"/>即可确定所有供给节点在该订单上的分配量。</p>
<p>即对于给定的分配场景，只要大致确定订单之间分配的相对优先级并给出基于订单优先级计算得到的播放比例值<img alt="图示" loading="lazy" src="/logbook/images/algorithm/d7bbc478acb0e25a33d8.png"/>，即可给出一种效果比较好的分配方案，是一种兼顾效果和效率的较为理想的分配算法。HWM算法包含离线分配和在线分配两部分，其离线分配算法的关键步骤如下：</p>
<p>1)     初始化每个流量供应节点的剩余库存(<img alt="图示" loading="lazy" src="/logbook/images/algorithm/c9504d27a1f254449260.png"/>)为预估库存值(<img alt="图示" loading="lazy" src="/logbook/images/algorithm/9d6ffcee46a763d71636.png"/>):<img alt="图示" loading="lazy" src="/logbook/images/algorithm/2a971c4401191a704341.png"/>。</p>
<p>2)     对于每个合约订单j，按照优先级顺序求解：<o:p></o:p></p>
<p>a)     解<img alt="图示" loading="lazy" src="/logbook/images/algorithm/e3f4b7635eee27cb4394.png"/>，得到订单播放概率<img alt="图示" loading="lazy" src="/logbook/images/algorithm/98f65174c2e3dcd6dd77.png"/>，若无解则设置<img alt="图示" loading="lazy" src="/logbook/images/algorithm/57675fa2fbbb337fef05.png"/>。</p>
<p>b)     更新订单j对应的所有流量供应节点的剩余库存：<img alt="图示" loading="lazy" src="/logbook/images/algorithm/186438a59b0bafdf02fd.png"/>。</p>
<p>　　通过上述步骤，HWM离线分配提供了一种快速的、紧凑型（compact）的库存分配方案，经过离线分配后的每个订单仅需要附加携带其播放比例<img alt="图示" loading="lazy" src="/logbook/images/algorithm/98f65174c2e3dcd6dd77.png"/>，即可很方便的在线上服务中对每次展示做出和HWM离线分配时一致的分配决策。若不考虑订单询量最大可用库存问题，售卖分配系统面临的问题和HWM离线分配问题是相同的，因此我们使用HWM离线分配算法作为售卖分配系统的算法基础。</p>
<h2>2.2　解决订单询量问题      </h2>
<p>　　利用HWM在线分配算法可以有效的解决CPM库存售卖分配过程中面临的基于已下单预定量的流量分配问题。然而，售卖分配系统还需要定向订单在预估库存下的最大可用库存询量的问题：即对于系统来说，在订单询量时其面临的最优化问题的目标函数将不再是固定的，而是和当前询量订单<img alt="图示" loading="lazy" src="/logbook/images/algorithm/5b95057e3f8d871a396d.png"/>属性（可用量，价格）相关的一个函数，其公式化描述如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/1cb0a599766e135189c0.jpg"/></p>
<p>上式中<img alt="图示" loading="lazy" src="/logbook/images/algorithm/1a587a4d63ebe720e81f.png"/>为订单eCPM价格，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/a528f3c19e7ae1d47868.png"/>为订单最大可用库存量。同公式（2.1）中的<img alt="图示" loading="lazy" src="/logbook/images/algorithm/7b27f2b0667def960406.png"/>为历史订单在担保式投放（GD）的情况下系统能够获取的总体收益，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/74eda6d9e0469928fdb9.png"/>代表了引入当前询量单后系统能够获取的总收益，当询量单带价格询量时，系统能够提供个可用库存越大则系统的总收益也越高，这正符合了售卖分配系统的系统收益最大化的目标。上述问题是一个标准的二次规划问题，整体上还是在HWM的算法框架内的。</p>
<p><b>　　</b>从合约广告售卖的系统层面来看，由于CPM售卖分配系统引入了订单价格和最大可用量的参数，使得CPM的离线售卖分配和在线投放系统的目标区分开来，并且相比投放面临的最优化问题更加复杂。因此我们基于HWM的算法模型进行参数调整，在其原有算法流程的基础上引入价格和需求量作为HWM询量算法的参数，并对原算法的相关策略进行优化，最终获得我们实践应用中的系统。其中的主要改进点如下：</p>
<p>1)     基于订单定向对流量标签进行合并：通过合并，减少订单定向的流量标签个数，降低系统面临的供需二部图的问题规模，最终降低系统的整体复杂性。<o:p></o:p></p>
<p>2)     细化库存频次到地域*内容级别，同时基于VV库存结构进行分配，提高系统库存分配结果的精确性。<o:p></o:p></p>
<p>3)     在确保已下单需求量情况下，引入时间队列和二分查找进行算法迭代，求解询量订单最大可用库存量：<o:p></o:p></p>
<p>a)     询量单在优先级位置F_pos处的可用库存f_remain为不考虑所有低优先级订单需求量时的剩余库存，作为该订单询量的可用库存上限<o:p></o:p></p>
<p>b)     询量单在优先级末尾S_pos处的可用库存s_remain为考虑了所有已下订单的需求量后的剩余库存，代表了该订单询量的可用库存的下限。<o:p></o:p></p>
<p>c)      通过对[f_remain, s_remain]区间进行二分迭代，作为询量单分配的需求量，带入HWM分配算法计算是否存在可用解，则使得HWM分配算法存在可用解的最大迭代值即为该单的询量结果：<o:p></o:p></p>
<p>d)     整个订单询量流程图如下：<o:p></o:p></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/002178dea6f42d0b6421.jpg"/></p>
<p>图3　订单询量流程图</p>
<h1>3　分配与售卖一体化</h1>
<p><b>　　</b>上部分中，我们利用HWM解决了固定价格下的订单询量问题，即将需求量参数引入到售卖分配系统中去。但是，其中并没有考虑到价格这一影响系统整体收入的关键因素对于订单询量最大可用库存的影响，而这一影响在现实的生产环境中是普遍存在的。同时，我们通过对历史长期的下单数据分析发现，大部分订单的下单时间主要集中在订单的投放期3周前，因此需要客户提前规划其广告预算，增加了客户接入系统的成本。为了反应价格因素对于订单询量可用库存的影响以及提高客户投放期前可以灵活调整预定库存量，我们在基于系统收入最大化的目标框架下，引入了锁量和客情优先级两套系统优化机制。</p>
<h2>3.1　锁量机制</h2>
<p>　　锁量机制是一种对于系统库存提供提前预约功能的机制：用户可根据其广告预算对系统库存进行提前预约，由于预约时并不生成具体售卖合同，客户可在投放期开始前对其预定量进行灵活调整，直至订单合同的达成。锁量机制增强了系统对于未来较长时间窗口期库存预定管理的灵活性，同时将系统中的历史订单按照其是否锁量分成了两种类型：1）正式已下单，即已达成库存预定正式合同，需要GD订单需求量的订单；2）锁量订单，即并未达成正式合同，但对未来流量带有明确的预定意向，由于这些订单有可能转化为正式订单，其需求量应尽量得到满足而非必须满足。锁量机制降低了客户接入系统的门槛，给予了用户更大的调整的空间，有利于吸引新广告主用户接入。</p>
<h2>3.2　客情优先级机制</h2>
<p>　　对于广告系统来说，最关心的目标是系统的整体收入<img alt="图示" loading="lazy" src="/logbook/images/algorithm/08eaca28c96d774acef3.png"/>，而系统的收入有两部分构成：<img alt="图示" loading="lazy" src="/logbook/images/algorithm/69f5364ecf4b0e26ecee.png"/>，其中<img alt="图示" loading="lazy" src="/logbook/images/algorithm/1fead0942280c48d3ed8.png"/>为售卖库存，<img alt="图示" loading="lazy" src="/logbook/images/algorithm/b01bc7cdf8a0d8176fec.png"/>为价格。只有让更多的锁量单转化为正式已下订单才能真正将客户的广告需求转化为系统的收入，即增大已售库存因子<img alt="图示" loading="lazy" src="/logbook/images/algorithm/1fead0942280c48d3ed8.png"/>；同时若能在提高库存的单位价格或者某些热门维度的库存单位价格，则提高了系统收入中的价格因子<img alt="图示" loading="lazy" src="/logbook/images/algorithm/b01bc7cdf8a0d8176fec.png"/>，则系统的整体收入会有显著的提升。基于上述目的，我们设计了一种基于订单询量价格和历史单状态的询量机制--客情优先级机制，其核心逻辑有以下两点：</p>
<p>1)     为每个订单分配一个客情优先级，其值由订单对应广告主以及订单价格等因素综合决定，值越小优先级越高，该值可以定量的反应订单预定库存所带来的单位收益。<o:p></o:p></p>
<p>2)     高优先级订单可以在GD历史已下正式单预定量的前提下挤占低于自身的低客情优先级的锁量订单。高客情优先级订单询量时，其需要Guarantee的历史单只有两类：客情优先级高于自身的锁量单以及历史已下正式单。对于当前询量订单来说，其客情优先级越高，可用库存量越大。<o:p></o:p></p>
<p>　　引入了锁量和客情优先级机制的订单询量流程如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f8d2ec01cdd6ef20c6ab.jpg"/></p>
<p>图4 订单按照客情优先级顺序询量示意图</p>
<p>　　通过引入上述两点规则，对于相同的历史订单情况下的订单询量，有如下优点：</p>
<p>1） 客户给出不同的库存单价所能够得到的可用库存量是不一样的，有助于提高订单定向下单位库存的溢价能力。<o:p></o:p></p>
<p>2） 处于锁量状态订单被高客情优先级订单挤占，使得自身需求库存被其他订单占用，有利于促进锁量订单向正式合同订单的快速转化。<o:p></o:p></p>
<p>　　此外，由于锁量单会影响其他订单的可用库存量，一般会为锁量订单设置一个锁量的过期时间窗口，以避免系统库存被长期锁量，影响其他订单的预定。</p>
<h1>４　衡量标准</h1>
<p>对于一个广告系统而言，有售卖就有投放，由于售卖分配系统本质上是为系统提供一种高性价比的库存售卖方案，并且合约广告的结算方式一般是按照实际投放过程中约定流量的实际达成情况进行结算，这决定了衡量售卖系统分配结果的好坏应和投放系统的实际投放结果结合起来。我们认为可以从两个指标来对售卖库存分配系统的整体性能进行衡量：<o:p></o:p></p>
<p>1)     极限下单量：即在给定一组订单定向的情况下，系统能够分配的总库存量。该指标的描述类似组合优化问题中的背包问题，其最终解方案的优劣一定程度上体现了系统能够达到的总体收益的期望水平。<o:p></o:p></p>
<p>2)     分配方案与在线投放结果匹配度：由于cpm广告按照实际播放的曝光量进行结算，保证分配方案与系统最终的投放结果保持一致对于保障系统收益来说十分重要。我们可以通过对比一段时间内的多组真实订单在售卖分配系统和在真实线上环境的分配量，来评价售卖库存分配系统分配结果的整体效果。 </p>
<h1><strong>５</strong>　<strong>参考文献</strong></h1>
<p>[1]    P. Chen, W. Ma, S. Manalapu, C. Nagarajan, S. Vassilvitskii, E. Vee, M. Yu, and J. Zien. Ad serving using a compact allocation plan. Proceedings of the 13th ACM Conference on Electronic Commerce. 2012, 1(212): 319-336.<o:p></o:p></p>
<p>[2]    zh.wikipedia.org/wiki/二分图<o:p></o:p></p>
<p>[3]    https://zh.wikipedia.org/wiki/拉格朗日乘数</p> 
{% endraw %}
