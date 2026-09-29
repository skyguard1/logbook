---
title: "基于策略梯度的TopK集合召回推荐算法"
date: 2022-04-02 13:59:56
categories:
  - 算法平台
  - 召回与向量检索
---

{% raw %}

<div>
<div>
<div>
<div>
<p></p><div><ul><li>11. 问题描述</li><li>22. 相关研究</li><li>33. 算法描述<ul><li>3.13.1 策略梯度算法：REINFORCE </li><li>3.23.2 Off-Policy</li><li>3.33.3 TopK召回</li><li>3.43.4 裁剪</li></ul></li><li>44. 奖赏的重新定义</li><li>55. 模型结构与实现</li><li>66. 未来展望</li><li>77. 参考</li></ul></div><p></p><h1>1. 问题描述</h1><p><br/>在推荐系统中，我们经常面临一次性为user展示多个item的场景。业界通常的做法是：先召回候选items，然后对每个的&lt;user, item&gt;进行打分并按照pCVR对item排序，最后经过重排层展示给user。</p><p>具体拆开来看，上述场景主要分为以下四种情况：</p><ol><li>展示多个item，user一次只能交互一个item，交互后无后续曝光（如youtube长视频推荐）；</li><li>展示多个item，user一次只能交互一个item，交互后有后续曝光（如信息流文章、短视频流推荐）；</li><li>展示多个item，user一次能交互多个item，交互后无后续曝光（如应用市场的新机必备弹窗推荐）；</li><li>展示多个item，user一次能交互多个item，交互后有后续曝光（如应用市场的详情页下了又下推荐）；</li></ol><p>举几个例子来说明：</p><ul><li>以应用宝必备弹窗推荐为例，我们假设当前场景有5个可展示槽位，pCVR打分top5的App是：淘宝、天猫、拼多多、、蘑菇街。如果按照pCVR排序去展示，很可能达不到很好的效果，因为用户不太可能同时下载多个功能相似的app；</li><li>以youtube视频推荐为例，视频的下方会推荐多个视频，但如果我们都召回源视频相同类目的视频，可能会引起用户的审美疲劳而使用户反感而降低点击率；</li><li>以应用宝必备弹窗推广“ app”为例，我们会在固定槽位帮助推广“app”，但不同的实验算法下“”的cvr差距很大，这也间接的说明了集合的推荐结果对于个体效果有很大的影响；</li></ul><p>面对这类情况，我们可以通过专家规则来控制品类的多样性，但这需要产品开发同学较强的数据敏感性和频繁的线上ab实验；当然，我们也可以通过一个集合召回算法，从用户群的历史行为中学习如何召回，从提高集合整体的点击率来提升用户体验。本文将以应用宝新机必备弹窗场景的实践为例，详细描述TopK集合召回推荐算法。</p><h1>2. 相关研究</h1><p><br/>自2016年AlphaGo问世以来，强化学习的思想已经被广泛地应用于学术界和工业界。公司在18年12月发表论文《Top-K Off-Policy Correction for a REINFORCE Recommender System》，提出的一种新的策略梯度的召回算法，用于一次性召回K个item，并在youtube视频推荐上取得了不错的效果。</p><p>论文主要有4个要点：</p><ol><li>采用REINFORCE策略梯度算法</li><li>采用离线Off-Policy进行样本分布修正</li><li>Top-K策略及其策略梯度</li><li>考虑推荐的长期奖赏和值裁剪</li></ol><p>本文主要工作是复现并改进了这篇论文：采用的随机策略梯度，结合off-policy重要性采样、值裁剪等方法，并结合业务做相应的改进。最终从候选集中一次性选取Top21个app作为必备弹窗的集合召回的结果，再经过排序层后展示给用户。下面展示了整个场景的算法流程图。<br/><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/7c1c1ea0fef38588f92a.png"/></p><p>图2.1 必备弹窗场景流程图</p><p>在应用宝新机必备弹窗业务中，对于判定为新机的用户，在第一次启动应用宝时会一次推荐最多21个App（详见右图）。如上图所示，TopK算法位于粗召回之后，会从粗召回的N个app中选择21个app，再经过精排和重排干预后最终展示给用户。由于必备弹窗场景中用户不存在连续交互性，故可以视为仅交互一次的特殊强化学习，这里使用策略梯度最大化立即奖赏；对于一些交互持续性强的场景，如相关推荐、下了又下，推荐的结果会有长期的影响和反馈，可以结合强化学习的思想去最大化长期收益。</p><h1>3. 算法描述</h1><p>从优化方法角度，强化学习可以分为策略优化和值优化两种。</p><ol><li><strong>值优化(value-based)：</strong>通过最大化值来找到最优策略，经典的Q-Learning和Sarsa等算法都是值优化方法</li><li><strong>策略优化(policy-based)：</strong>认为策略是可以直接被优化的，在每个状态都可以给出各个策略的概率（随机策略梯度）或者确定的策略（确定性策略梯度）</li><li><strong>Actor-Critic：</strong>结合了值优化和策略优化，critic网络预估value，actor网络预估action；</li></ol><p>而策略梯度，其实就是策略优化方法中直接求策略的梯度来直接优化策略的一种方法。本文不过多的叙述强化学习细节，比较陌生的同学可以网上查阅或私下交流，后期团队也会写一些入门文章。</p><h2>3.1 策略梯度算法：REINFORCE </h2><p>在推荐系统中，我们关注用户与系统的交互行为，记录推荐的动作（这里即推荐的App）和用户的反馈（点击和下载），并基于这些交互行为改善下一次动作，使用户越来越满意。我们将上述过程构建成马尔科夫决策过程
        MDP(S,A,P,R,γ,ρ0)<math><mi>M</mi><mi>D</mi><mi>P</mi><mo>(</mo><mrow><mi mathvariant="script">S</mi></mrow><mo>,</mo><mrow><mi mathvariant="script">A</mi></mrow><mo>,</mo><mrow><mi mathvariant="script">P</mi></mrow><mo>,</mo><mrow><mi mathvariant="script">R</mi></mrow><mo>,</mo><mi>γ</mi><mo>,</mo><msub><mi>ρ</mi><mn>0</mn></msub><mo>)</mo></math>
 ，其中</p><ul><li>
S:<math><mrow><mi mathvariant="script">S</mi></mrow><mo>:</mo></math>
描述当前用户状态的特征空间：如用户年龄性别、已安装/删除app等；</li><li>
A:<math><mrow><mi mathvariant="script">A</mi></mrow><mo>:</mo></math>
离散的动作空间，每一个动作表示一个候选app被选择的概率；</li><li>
P:<math><mrow><mi mathvariant="script">P</mi></mrow><mo>:</mo></math>
状态转移概率函数</li><li>
R:<math><mrow><mi mathvariant="script">R</mi></mrow><mo>:</mo></math>
采用动作后的环境反馈的奖赏值</li><li>
γ:<math><mi>γ</mi><mo>:</mo></math>
长期奖赏折扣系数</li><li>
ρ0:<math><msub><mi>ρ</mi><mn>0</mn></msub><mo>:</mo></math>
初始状态</li></ul><p>我们的目标是寻找到一个策略
        πθ(s,a)<math><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></math>
 ，使得给出一个用户状态 
        S<math><mrow><mi mathvariant="script">S</mi></mrow></math>
 ，策略
        πθ(s,a)<math><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></math>
 来输出各个动作
        a∈A<math><mi>a</mi><mo>∈</mo><mrow><mi mathvariant="script">A</mi></mrow></math>
 被选择的概率。策略
        πθ(s,a)<math><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></math>
的优化方向是最大化长期奖赏，长期奖赏可以用很多种方法表示，如start value、average value等，这里我们使用average reward per time-step来表示，则长期奖赏的期望表示如下：</p><p>
J(θ)=Eπθ[r]=∑sdπθ(s)∑aπθ(s,a)Ras<math><mi>J</mi><mo>(</mo><mi>θ</mi><mo>)</mo><mo>=</mo><msub><mi>E</mi><mrow><msub><mi>π</mi><mi>θ</mi></msub></mrow></msub><mo>[</mo><mi>r</mi><mo>]</mo><mo>=</mo><munder><mo>∑</mo><mi>s</mi></munder><msup><mi>d</mi><mrow><msub><mi>π</mi><mi>θ</mi></msub></mrow></msup><mo>(</mo><mi>s</mi><mo>)</mo><munder><mo>∑</mo><mi>a</mi></munder><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msubsup><mi>R</mi><mi>s</mi><mi>a</mi></msubsup></math>
</p><p>策略的梯度表示为
        ∇θπθ(s,a)<math><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></math>
：</p><p>
∇θπθ(s,a)=πθ(s,a)∇θπθ(s,a)πθ(s,a)=πθ(s,a)∇θlogπθ(s,a)<math><mtable columnalign="right left" columnspacing="0em" displaystyle="true" rowspacing="3pt"><mtr><mtd><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mtd><mtd><mi></mi><mo>=</mo><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mfrac><mrow><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow><mrow><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow></mfrac></mtd></mtr><mtr><mtd></mtd></mtr><mtr><mtd></mtd><mtd><mi></mi><mo>=</mo><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mtd></mtr></mtable></math>
</p><p>其中
        ∇θlogπθ(s,a)<math><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></math>
又被称为score function。</p><p>有了策略的梯度，就可以计算
        ∇θJ(θ)<math><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>J</mi><mo>(</mo><mi>θ</mi><mo>)</mo></math>
:</p><p>
∇θJ(θ)=∑sdπθ(s)∑aπθ(s,a)∇θlogπθ(s,a)Ras=Es∼dπ,a∼πθ[∇θlogπθ(s,a)r]=Eπθ[∇θlogπθ(s,a)r]<math><mtable columnalign="right left" columnspacing="0em" displaystyle="true" rowspacing="3pt"><mtr><mtd><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>J</mi><mo>(</mo><mi>θ</mi><mo>)</mo></mtd><mtd><mi></mi><mo>=</mo><munder><mo>∑</mo><mi>s</mi></munder><msup><mi>d</mi><mrow><msub><mi>π</mi><mi>θ</mi></msub></mrow></msup><mo>(</mo><mi>s</mi><mo>)</mo><munder><mo>∑</mo><mi>a</mi></munder><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msubsup><mi>R</mi><mi>s</mi><mi>a</mi></msubsup></mtd></mtr><mtr><mtd></mtd></mtr><mtr><mtd></mtd><mtd><mi></mi><mo>=</mo><msub><mi>E</mi><mrow><mi>s</mi><mo>∼</mo><msup><mi>d</mi><mi>π</mi></msup><mo>,</mo><mi>a</mi><mo>∼</mo><msub><mi>π</mi><mi>θ</mi></msub></mrow></msub><mo>[</mo><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mi>r</mi><mo>]</mo></mtd></mtr><mtr><mtd></mtd></mtr><mtr><mtd></mtd><mtd><mi></mi><mo>=</mo><msub><mi>E</mi><mrow><msub><mi>π</mi><mi>θ</mi></msub></mrow></msub><mo>[</mo><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mi>r</mi><mo>]</mo></mtd></mtr></mtable></math>
</p><p>有了
        J(θ)<math><mi>J</mi><mo>(</mo><mi>θ</mi><mo>)</mo></math>
，我们就可以设计一个神经网络来最大化
        J(θ)<math><mi>J</mi><mo>(</mo><mi>θ</mi><mo>)</mo></math>
，在这个神经网络中，输入是当前agent获得的状态s，输出是策略
        πθ(s,a)<math><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></math>
，目标是最大化损失函数
        J(θ)<math><mi>J</mi><mo>(</mo><mi>θ</mi><mo>)</mo></math>
，参数
        θ<math><mi>θ</mi></math>
的更新方式是梯度上升。</p><p>策略优化方法必须等一个episode完整结束，才能获得reward去更新，这种更新方式属于Monte-Carlo Policy Gradient，又叫REINFORCE算法。完整的REINFORCE算法如下：</p><p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/9e4fbf6f00c153d82484.png"/><br/>参数的更新公式如下：</p><p>
Δθt=α∇θlogπθ(st,at)vt<math><mi mathvariant="normal">Δ</mi><msub><mi>θ</mi><mi>t</mi></msub><mo>=</mo><mi>α</mi><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><msub><mi>s</mi><mi>t</mi></msub><mo>,</mo><msub><mi>a</mi><mi>t</mi></msub><mo>)</mo><msub><mi>v</mi><mi>t</mi></msub></math>
</p><p>
vt=Rt+1+γRt+2+...+γT−1Rt+2<math><msub><mi>v</mi><mi>t</mi></msub><mo>=</mo><msub><mi>R</mi><mrow><mi>t</mi><mo>+</mo><mn>1</mn></mrow></msub><mo>+</mo><mi>γ</mi><msub><mi>R</mi><mrow><mi>t</mi><mo>+</mo><mn>2</mn></mrow></msub><mo>+</mo><mo>.</mo><mo>.</mo><mo>.</mo><mo>+</mo><msup><mi>γ</mi><mrow><mi>T</mi><mo>−</mo><mn>1</mn></mrow></msup><msub><mi>R</mi><mrow><mi>t</mi><mo>+</mo><mn>2</mn></mrow></msub></math>
<br/></p><p>对于我们的业务，由于我们仅考虑瞬时奖赏最大化，故状态转移函数
        P<math><mrow><mi mathvariant="script">P</mi></mrow></math>
和长期折扣系数
        γ<math><mi>γ</mi></math>
都会被忽略不计。</p><h2>3.2 Off-Policy</h2><p>我们将模型要优化的策略称为目标策略
        πθ<math><msub><mi>π</mi><mi>θ</mi></msub></math>
，把实际产生行为的策略成为行为策略
        βθ<math><msub><mi>β</mi><mi>θ</mi></msub></math>
。很明显，我们的行为策略可能是由几十上百种线上的实验和配置组成，与目标策略有很大差别。根据目标策略和行为策略的异同，强化学习又分为On-Policy和Off-Policy。</p><ul><li>On-Policy中，目标策略
        πθ<math><msub><mi>π</mi><mi>θ</mi></msub></math>
和行为策略
        βθ<math><msub><mi>β</mi><mi>θ</mi></msub></math>
是同一个策略，即产生样本的策略与评估改进的策略是同一个策略。On-Policy通过在线交互学习，采取动作后得到环境的反馈后立即更新目标策略，训练和预测的样本分布式一致的。</li><li>Off-Policy中，目标策略
        πθ<math><msub><mi>π</mi><mi>θ</mi></msub></math>
和行为策略
        βθ<math><msub><mi>β</mi><mi>θ</mi></msub></math>
是不同的策略，即产生样本的策略与评估改进的策略是不同的策略。它通过Importance Sampling等方法，根据目标和行为策略的概率来动态调节样本的权重，从而保证对于状态分布和长期奖赏的拟合。</li></ul><p>对于to C业务来说，我们并不能像传统的强化学习（如游戏ai等）一样实时交互学习，因为成本太高且学习的过程不稳定会伤害用户体验；此外，线上的各种实验流量和干预逻辑复杂，也完全无法保证样本和目标网络动作分布的一致性，所以这里我们采用基于重要性采样的Off-Policy。Off-Policy策略梯度公式如下：</p><p>
∇θJβ(πθ)=Es∼ρβ,a∼πθ[∇θlogπθ(s,a)Qπ(s,a)]=Es∼ρβ,a∼β[πθ(s,a)βθ(s,a)∇θlogπθ(s,a)Qπ(s,a)]<math><mtable columnalign="right left" columnspacing="0em" displaystyle="true" rowspacing="3pt"><mtr><mtd><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><msub><mi>J</mi><mi>β</mi></msub><mo>(</mo><msub><mi>π</mi><mi>θ</mi></msub><mo>)</mo></mtd><mtd><mi></mi><mo>=</mo><msub><mi>E</mi><mrow><mi>s</mi><mo>∼</mo><msup><mi>ρ</mi><mi>β</mi></msup><mo>,</mo><mi>a</mi><mo>∼</mo><msub><mi>π</mi><mi>θ</mi></msub></mrow></msub><mo>[</mo><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msup><mi>Q</mi><mi>π</mi></msup><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mo>]</mo></mtd></mtr><mtr><mtd></mtd></mtr><mtr><mtd></mtd><mtd><mi></mi><mo>=</mo><msub><mi>E</mi><mrow><mi>s</mi><mo>∼</mo><msup><mi>ρ</mi><mi>β</mi></msup><mo>,</mo><mi>a</mi><mo>∼</mo><mi>β</mi></mrow></msub><mo>[</mo><mfrac><mrow><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow><mrow><msub><mi>β</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow></mfrac><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msup><mi>Q</mi><mi>π</mi></msup><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mo>]</mo></mtd></mtr></mtable></math>
 <br/>其中，
        πθ(s,a)βθ(s,a)<math><mfrac><mrow><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow><mrow><msub><mi>β</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow></mfrac></math>
 是重要性采样（
        βθ<math><msub><mi>β</mi><mi>θ</mi></msub></math>
的预估见第5节）。</p><h2>3.3 TopK召回</h2><p><br/>当我们需要推荐一个集合而不是单个item的时候，我们需要一个新的策略
        αθ(s,A)<math><msub><mi>α</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>A</mi><mo>)</mo></math>
，这里
        A<math><mi>A</mi></math>
表示选择k个item，我们的期望也就变成了
        EαΘ[∑s,aRas]<math><msub><mi>E</mi><mrow><msub><mi>α</mi><mrow><mi mathvariant="normal">Θ</mi></mrow></msub></mrow></msub><mo>[</mo><munder><mo>∑</mo><mrow><mi>s</mi><mo>,</mo><mi>a</mi></mrow></munder><msubsup><mi>R</mi><mi>s</mi><mi>a</mi></msubsup><mo>]</mo></math>
。我们假设集合的奖赏等于每个item的奖赏之和，则REINFORCE算法的策略梯度为如下形式：</p><p>
∇θlogαθ(s,a)Ras<math><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>α</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msubsup><mi>R</mi><mi>s</mi><mi>a</mi></msubsup></math>
，</p><p>其中
        αθ(a,s)=1−(1−πθ(a,s))k<math><msub><mi>α</mi><mi>θ</mi></msub><mo>(</mo><mi>a</mi><mo>,</mo><mi>s</mi><mo>)</mo><mo>=</mo><mn>1</mn><mo>−</mo><mo>(</mo><mn>1</mn><mo>−</mo><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>a</mi><mo>,</mo><mi>s</mi><mo>)</mo><msup><mo>)</mo><mi>k</mi></msup></math>
，表示app 出现在最终结果集合的概率</p><p>我们用新行为策略
        αθ(s,A)<math><msub><mi>α</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>A</mi><mo>)</mo></math>
代替旧行为策略
        πθ<math><msub><mi>π</mi><mi>θ</mi></msub></math>
，那么TopK Off-Policy Gradient便改写为</p><p>
Es∼ρβ,a∼β[αθ(s,a)βθ(s,a)∇θlogαθ(s,a)Qπ(s,a)]=Es∼ρβ,a∼β[πθ(s,a)βθ(s,a)∂αθ(s,a)∂πθ(s,a)∇θlogπθ(s,a)Qπ(s,a)]<math><mtable columnalign="right left" columnspacing="0em" displaystyle="true" rowspacing="3pt"><mtr><mtd></mtd><mtd><msub><mi>E</mi><mrow><mi>s</mi><mo>∼</mo><msup><mi>ρ</mi><mi>β</mi></msup><mo>,</mo><mi>a</mi><mo>∼</mo><mi>β</mi></mrow></msub><mo>[</mo><mfrac><mrow><msub><mi>α</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow><mrow><msub><mi>β</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow></mfrac><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>α</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msup><mi>Q</mi><mi>π</mi></msup><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mo>]</mo></mtd></mtr><mtr><mtd><mo>=</mo></mtd><mtd><msub><mi>E</mi><mrow><mi>s</mi><mo>∼</mo><msup><mi>ρ</mi><mi>β</mi></msup><mo>,</mo><mi>a</mi><mo>∼</mo><mi>β</mi></mrow></msub><mo>[</mo><mfrac><mrow><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow><mrow><msub><mi>β</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow></mfrac><mfrac><mrow><mi mathvariant="normal">∂</mi><msub><mi>α</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow><mrow><mi mathvariant="normal">∂</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow></mfrac><msub><mi mathvariant="normal">∇</mi><mi>θ</mi></msub><mi>l</mi><mi>o</mi><mi>g</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msup><mi>Q</mi><mi>π</mi></msup><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mo>]</mo></mtd></mtr></mtable></math>
</p><p>TopK Off-Policy Gradient 相比 Off-Policy Gradient，多了一项 
        λK(s,a)=∂αθ(s,a)∂πθ(s,a)=K(1−πθ(s,a))K−1<math><msub><mi>λ</mi><mi>K</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mo>=</mo><mfrac><mrow><mi mathvariant="normal">∂</mi><msub><mi>α</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow><mrow><mi mathvariant="normal">∂</mi><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow></mfrac><mo>=</mo><mi>K</mi><mo>(</mo><mn>1</mn><mo>−</mo><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><msup><mo>)</mo><mrow><mi>K</mi><mo>−</mo><mn>1</mn></mrow></msup></math>
:</p><ol><li>当
        πθ→0<math><msub><mi>π</mi><mi>θ</mi></msub><mo>→</mo><mn>0</mn></math>
时，
        λK(s,a)→K<math><msub><mi>λ</mi><mi>K</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mo>→</mo><mi>K</mi></math>
</li><li>当
        πθ→1<math><msub><mi>π</mi><mi>θ</mi></msub><mo>→</mo><mn>1</mn></math>
时，
        λK(s,a)→0<math><msub><mi>λ</mi><mi>K</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mo>→</mo><mn>0</mn></math>
</li></ol><p>我们可以发现，当softmax结果较小时，TopK Off-Policy策略相比原策略会更加激进的更新梯度；相反，一旦softmax结果达到一个较大的合理的值（为了保证结果可能出现在TopK中），此时TopK Off-Policy策略会大幅降低梯度更新的幅度，甚至为0，从而保证其他item更新。</p><p>为了更好的理解TopK Off Policy和Off-Policy的却别，论文中设计了一组模拟实验。在模拟环境中，我们的候选集有10个，K=2。r(a1)=10，r(a2)=9，其他r=1。我们可以清楚的看到两个策略的区别：TopK Off Policy策略再保证序的同时，保证了</p><p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/30dc5c8dc7f1b394abd4.png"/></p><p><br/></p><p>在线上，我们会根据输出action概率，使用轮盘赌注有放回的选取21个不同app。若遇到重复选取，则再额外增加一次轮盘赌注。轮盘赌注的方法同时保证了探索和利用，如果不能接受线上探索行为，亦可以用值排序的方法代替轮盘赌注。</p><h2>3.4 裁剪</h2><p>我们仔细看重要性采样公式会发现，如果目标策略
        πθ<math><msub><mi>π</mi><mi>θ</mi></msub></math>
和行为策略
        βθ<math><msub><mi>β</mi><mi>θ</mi></msub></math>
的比值过大，那么会导致梯度的过大而过早拟合无法收敛，这显然是我们不能接受的。梯度权重裁剪是一个比较大的话题，业界有很多种方法在做，如PPO，NIS等，本文采用最简单的Weight Capping方法来防止梯度更新权重过大而导致的过早收敛和方差过大等问题。具体参数如下：</p><p>
wc(s,a)=min(πθ(s,a)βθ(s,a),c)<math><msub><mi>w</mi><mi>c</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo><mo>=</mo><mi>m</mi><mi>i</mi><mi>n</mi><mo>(</mo><mfrac><mrow><msub><mi>π</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow><mrow><msub><mi>β</mi><mi>θ</mi></msub><mo>(</mo><mi>s</mi><mo>,</mo><mi>a</mi><mo>)</mo></mrow></mfrac><mo>,</mo><mi>c</mi><mo>)</mo></math>
</p><p>通过设置一个常数
        c<math><mi>c</mi></math>
，可以有效的保证沿着梯度下降方向小步更新，避免出现大的波动。</p><h1>4. 奖赏的重新定义</h1><p>前文提到，我们以单个item的奖赏之和当做集合的奖赏当，我们也确实这样做了，但发现效果并不及预期。于是我们拆分实验组和对照组的曝光app来看，发现一个很有趣的问题：</p><p>在对照组中，”Taptap“获得了最多的曝光和最高的后验cvr。但在实验组中，Taptap的曝光量却排在了10名以外。这不符合我们的理解，于是我们统计分别下载”Taptap“的用户和下载”极速版“的用户的下载分布情况，结果发现，下载”Taptap“的用户仅下载1个app的比例为8.6%，而下载”极速版“的用户下载仅下载1个app的比例仅为1.3%。在应用宝必备弹窗场景，人均下载app约为7个，下载用户中下载个数&lt;=3的用户占比达52.3%，下载个数&gt;=10个的用户占比32.1%，一键全下载用户占比达9.6%。</p><p>至此我们明白，并不是所有的用户都有集合下载的需求，部分用户更倾向于挑选少量app去下载。如果粗暴的以单个item的奖赏之和当做集合的奖赏当，那类似仅下载Taptap这样的App的行为就会只拿到很低的奖赏，从而导致这部分用户的需求无法被准确满足。我们根据这个思路调整了奖赏的定义，给下载&lt;=3个app的用户行为同样赋予最高的奖赏，这样我们既满足了精选小众下载的需求，又最大化了有集合下载愿意用户的下载能力，上线后达到了预期的效果，在忽略曝光结构的情况下（游戏、广告、自然量的比列），整体分发系数（即人均下载个数）提升20%。</p><h1>5. 模型结构与实现</h1><p>在模型选择上，我们尝试过WND结构、DIN结构、MLP结构，效果差异不大。在特征方面，User特征主要考虑用户的年龄性别等属性特征，以及用户的旧机安装列表，新机已安装app列表等行为特征。具体的模型结构如下：</p><p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/eb4895a451bf56c8ab9f.png"/><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/bf43ccd6f795a86f8e79.png"/></p><p>                                图5.1 包含attention的名网络结构                                                                                   图5.2 无Attention的模型网络结构</p><p><br/></p><p>其中，softmax层是softmax net，有参数更新；label action是输出的动作维度。</p><p>这里，我们对于
        πθ<math><msub><mi>π</mi><mi>θ</mi></msub></math>
和
        βθ<math><msub><mi>β</mi><mi>θ</mi></msub></math>
也尊重原文的方式，采用相同的训练结构和共享的底层网络参数，区别仅在于：</p><ol><li>
πθ<math><msub><mi>π</mi><mi>θ</mi></msub></math>
网络会反向传播回底层网络而
        βθ<math><msub><mi>β</mi><mi>θ</mi></msub></math>
不会；</li><li>
πθ<math><msub><mi>π</mi><mi>θ</mi></msub></math>
网络的样本采用全样本和奖赏训练，而
βθ<math><msub><mi>β</mi><mi>θ</mi></msub></math>
仅采用有下载行为的样本做训练且无奖赏。这是因为
πθ<math><msub><mi>π</mi><mi>θ</mi></msub></math>
需要最大化长期回报，而
βθ<math><msub><mi>β</mi><mi>θ</mi></msub></math>
只需要学习实际样本的分布；</li></ol><h1>6. 未来展望</h1><p>最近伯克利发表了一遍新的论文SMiRL，其核心思想是以最小化（熵混乱最小化）不确定性为奖赏进行学习，思想很有意思也许可以一试；此外，我们奖赏设置还是过于人工经验和业务经验，或许通过逆强化学习等方法会取得更好的收益；另外，未来会尝试在整个推荐交互场景上加入critic网络来拟合用户行为的长期奖赏，通过更好的刻画和服务用户来提升场景的收益。</p><h1>7. 参考</h1><p><br/>1. Top-K Off-Policy Correction for a REINFORCE Recommender System.</p><p>2. Mastering the game of Go with deep neural networks and tree search.</p><p>3. Deep Reinforcement Learning for Page-wise Recommendations.</p><p>4. SMiRL: Surprise Minimizing RL in Entropic Environments.</p><p>5. Playing Atari with Deep Reinforcement Learning.</p><p>6. Human-level control through deep reinforcement learning.</p><p>7. Trust Region Policy Optimization.</p><p>8. Deterministic Policy Gradient Algorithms.</p><p>9. State of the Art Control of Atari Games using shallow reinforcement learning.</p><p>10. Deep Reinforcement Learning in Parameterized Action Space.</p><p><br/></p><p>感谢@kelvincai，@nianhuaxie和推荐算法组同学的意见建议，以及@zemianxu，@lyleliao等架构组同学提供的工程侧的指导协助，有不足的地方请大家指正。</p><p><br/></p></div>
</div>
<div>
<div>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/61c38ec114664f596e99.png"/></p></div>
</div>
</div>
</div>

{% endraw %}
