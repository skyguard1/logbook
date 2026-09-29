---
title: "【看点】小流量ABTest优化——CUPED-Plus方法"
date: 2022-04-11 08:19:05
categories:
  - 算法平台
  - 平台工程与评估
---

{% raw %}

<div><h2>1.背景</h2>
</div><div><p>AB-test在互联网中的应用已经有20逾年的历史，其早已成为各互联网大厂验证新feature合理与否的标配，因此，为了能尽快地将新的行之有效的feature应用于全量用户，更快、更准的实验结果显得至关重要。</p>
</div><div><p>但真实工作中，往往会出现以下场景：<br/>
a.本身是新产品，用户量不足，实验结果难以保证<br/>
b.实验中的每个桶本身就是小部分用户，若该实验真正能够触达的用户（triggered user）又仅占桶中一小部分，同样会导致参与到实验的用户不足，即算法无法准确检测此种被稀释的treatment effect<br/>
c.当希望探查的实验组和对照组的差异（<math><semantics><mrow><mi mathvariant="normal">Δ</mi></mrow><annotation>\Delta</annotation></semantics></math>Δ）较小时，实验所需的用户量呈平方项增加</p>
</div><div><p>因此，在样本量稀缺的情况下，如何仍然保持实验的准确性，是所有实验平台共同的难题。在2013年，发表一篇名为《Improving the Sensitivity of Online Controlled Experiments by Utilizing Pre-Experiment Data》的论文，简称CUPED，主要通过用户分层（Statification）和控制变量（Control variates）的方法，实现了样本方差的缩减，提升了实验精度和效率。为检测该方法在实际产品数据中的效果，本文选取了看点阿拉丁实验平台中的某个小流量实验的数据来进行验证，最后提出了一些自身的思考和对CUPED算法的优化方案。</p>
</div><div><h2>2.一般情况下实验检测方案</h2>
</div><div><p>以最简单的独立样本t-test为例：<br/>
<math><semantics><mrow><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup></mrow><annotation>\bar{Y}^{(t)}</annotation></semantics></math>Yˉ(t)为实验组的均值，<math><semantics><mrow><msup><msub><mi>s</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msub><mn>2</mn></msup></mrow><annotation>&#123;{s}_{(t)}}^{2}</annotation></semantics></math>s(t)​2为实验组样本方差，<math><semantics><mrow><msub><mi>n</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msub></mrow><annotation>n_{(t)}</annotation></semantics></math>n(t)​为实验组样本量，<br/>
<math><semantics><mrow><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><annotation>\bar{Y}^{(c)}</annotation></semantics></math>Yˉ(c)为对照组的均值，<math><semantics><mrow><msup><msub><mi>s</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msub><mn>2</mn></msup></mrow><annotation>&#123;{s}_{(c)}}^{2}</annotation></semantics></math>s(c)​2为对照组样本方差，<math><semantics><mrow><msub><mi>n</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msub></mrow><annotation>n_{(c)}</annotation></semantics></math>n(c)​为对照组样本量，<br/>
原假设（null hypothesis）：<math><semantics><mrow><msub><mi>H</mi><mn>0</mn></msub><mo>:</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>=</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><annotation>H_0:\bar{Y}^{(t)} = \bar{Y}^{(c)}</annotation></semantics></math>H0​:Yˉ(t)=Yˉ(c)<br/>
备择假设（alternative hypothesis）：<math><semantics><mrow><msub><mi>H</mi><mn>1</mn></msub><mo>:</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo mathvariant="normal">≠</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><annotation>H_1:\bar{Y}^{(t)} \neq \bar{Y}^{(c)}</annotation></semantics></math>H1​:Yˉ(t)​=Yˉ(c)<br/>
则实验的t-statistic为：<br/>
<math><semantics><mtable><mtr><mtd></mtd><mtd><mrow><mfrac><mrow><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>−</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><msqrt><mrow><mi mathvariant="normal">var</mi><mo>⁡</mo><mrow><mo>(</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>−</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup><mo>)</mo></mrow></mrow></msqrt></mfrac><mo>=</mo><mfrac><mrow><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>−</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><msqrt><mrow><mfrac><msup><msub><mi>s</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msub><mn>2</mn></msup><msub><mi>n</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msub></mfrac><mo>+</mo><mfrac><msup><msub><mi>s</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msub><mn>2</mn></msup><msub><mi>n</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msub></mfrac></mrow></msqrt></mfrac></mrow></mtd><mtd></mtd><mtd><mtext>(1)</mtext></mtd></mtr></mtable><annotation>
\frac{\bar{Y}^{(t)}-\bar{Y}^{(c)}}{\sqrt{\operatorname{var}\left(\bar{Y}^{(t)}-\bar{Y}^{(c)}\right)}} = \frac{\bar{Y}^{(t)}-\bar{Y}^{(c)}}{\sqrt{\frac&#123;{{s}_{(t)}}^{2}}{n_{(t)}}+\frac&#123;{{s}_{(c)}}^{2}}{n_{(c)}}}}\tag {1}
</annotation></semantics></math>var(Yˉ(t)−Yˉ(c))<svg height="1.8800000000000001em" preserveAspectRatio="xMinYMin slice" viewBox="0 0 400000 1944" width="400em"><path d="M983 90
l0 -0
c4,-6.7,10,-10,18,-10 H400000v40
H1013.1s-83.4,268,-264.1,840c-180.7,572,-277,876.3,-289,913c-4.7,4.7,-12.7,7,-24,7
s-12,0,-12,0c-1.3,-3.3,-3.7,-11.7,-7,-25c-35.3,-125.3,-106.7,-373.3,-214,-744
c-10,12,-21,25,-33,39s-32,39,-32,39c-6,-5.3,-15,-14,-27,-26s25,-30,25,-30
c26.7,-32.7,52,-63,76,-91s52,-60,52,-60s208,722,208,722
c56,-175.3,126.3,-397.3,211,-666c84.7,-268.7,153.8,-488.2,207.5,-658.5
c53.7,-170.3,84.5,-266.8,92.5,-289.5z
M1001 80h400000v40h-400000z"></path></svg>​Yˉ(t)−Yˉ(c)​=n(t)​s(t)​2​+n(c)​s(c)​2​<svg height="1.8800000000000001em" preserveAspectRatio="xMinYMin slice" viewBox="0 0 400000 1944" width="400em"><path d="M983 90
l0 -0
c4,-6.7,10,-10,18,-10 H400000v40
H1013.1s-83.4,268,-264.1,840c-180.7,572,-277,876.3,-289,913c-4.7,4.7,-12.7,7,-24,7
s-12,0,-12,0c-1.3,-3.3,-3.7,-11.7,-7,-25c-35.3,-125.3,-106.7,-373.3,-214,-744
c-10,12,-21,25,-33,39s-32,39,-32,39c-6,-5.3,-15,-14,-27,-26s25,-30,25,-30
c26.7,-32.7,52,-63,76,-91s52,-60,52,-60s208,722,208,722
c56,-175.3,126.3,-397.3,211,-666c84.7,-268.7,153.8,-488.2,207.5,-658.5
c53.7,-170.3,84.5,-266.8,92.5,-289.5z
M1001 80h400000v40h-400000z"></path></svg>​Yˉ(t)−Yˉ(c)​(1)<br/>
其中<math><semantics><mrow><mi mathvariant="normal">Δ</mi><mo>=</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>−</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><annotation>\Delta=\bar{Y}^{(t)}-\bar{Y}^{(c)}</annotation></semantics></math>Δ=Yˉ(t)−Yˉ(c)为实验组和对照组的绝对差异。</p>
</div><div><p>一般来说，对于双侧检验，在95%的置信水平（<math><semantics><mrow><msub><mi>P</mi><mrow><mo>(</mo><mi>t</mi><mi>y</mi><mi>p</mi><mi>e</mi><mi>I</mi><mi>e</mi><mi>r</mi><mi>r</mi><mi>o</mi><mi>r</mi><mo>)</mo></mrow></msub><mo>=</mo><mi>α</mi><mo>=</mo><mn>5</mn><mi mathvariant="normal">%</mi></mrow><annotation>P_{(type I error)} = \alpha = 5\%</annotation></semantics></math>P(typeIerror)​=α=5%）情况下，当t-statistic &gt; 1.96或者对应的p_value &lt; 0.05时，我们就可以认为实验组和对照组在统计学上存在显著差异。</p>
</div><div><h2>3.CUPED原理介绍</h2>
</div><div><p>我们做AB-test的目的，就是希望AB两组（统计量）的差异在统计学上是显著，即获得大于1.96的<math><semantics><mrow><mi>t</mi></mrow><annotation>t</annotation></semantics></math>t值（或者小于0.05的<math><semantics><mrow><mi>p</mi></mrow><annotation>p</annotation></semantics></math>p值）。从上面可以看出，在<math><semantics><mrow><mi mathvariant="normal">Δ</mi></mrow><annotation>\Delta</annotation></semantics></math>Δ一定的情况下，<math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo></mrow><annotation>var(\Delta)</annotation></semantics></math>var(Δ)越小，获得的<math><semantics><mrow><mi>t</mi></mrow><annotation>t</annotation></semantics></math>t值越大，越容易获得“显著”。进一步地，<math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo></mrow><annotation>var(\Delta)</annotation></semantics></math>var(Δ)越小即<math><semantics><mrow><mfrac><msup><msub><mi>s</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msub><mn>2</mn></msup><msub><mi>n</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msub></mfrac><mo>+</mo><mfrac><msup><msub><mi>s</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msub><mn>2</mn></msup><msub><mi>n</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msub></mfrac></mrow><annotation>\frac&#123;{{s}_{(t)}}^{2}}{n_{(t)}}+\frac&#123;{{s}_{(c)}}^{2}}{n_{(c)}}</annotation></semantics></math>n(t)​s(t)​2​+n(c)​s(c)​2​越小，而<math><semantics><mrow><mi>n</mi></mrow><annotation>n</annotation></semantics></math>n在实验分桶的时候已经固定，因此，要想提升灵敏度，获得更大的<math><semantics><mrow><mi>t</mi></mrow><annotation>t</annotation></semantics></math>t值，只能考虑从<math><semantics><mrow><mi>s</mi></mrow><annotation>s</annotation></semantics></math>s入手，对其进行缩减。</p>
</div><div><p><strong><strong>所以整个CUPED的原理是：</strong><br/>
<strong>a.找到<math><semantics><mrow><mi mathvariant="normal">Δ</mi></mrow><annotation>\Delta</annotation></semantics></math>Δ的无偏估计量<math><semantics><mrow><msup><mi mathvariant="normal">Δ</mi><mo>∗</mo></msup></mrow><annotation>\Delta^*</annotation></semantics></math>Δ∗</strong><br/>
<strong>b.<math><semantics><mrow><msup><mi mathvariant="normal">Δ</mi><mo>∗</mo></msup></mrow><annotation>\Delta^*</annotation></semantics></math>Δ∗拥有比原本的<math><semantics><mrow><mi mathvariant="normal">Δ</mi></mrow><annotation>\Delta</annotation></semantics></math>Δ更小的方差</strong></strong></p>
</div><div><h3>3.1分层（组）(Stratification)</h3>
</div><div><p>按照实验单元（一般是用户）某一特性进行分组，如下图所示，可将用户按年龄分成如下组别，假设有<math><semantics><mrow><mi>K</mi></mrow><annotation>K</annotation></semantics></math>K组，<math><semantics><mrow><msub><mi>n</mi><mi>k</mi></msub></mrow><annotation>n_k</annotation></semantics></math>nk​为第<math><semantics><mrow><mi>k</mi></mrow><annotation>k</annotation></semantics></math>k组的样本量，则第<math><semantics><mrow><mi>k</mi></mrow><annotation>k</annotation></semantics></math>k组样本量占比为<math><semantics><mrow><msub><mi>w</mi><mi>k</mi></msub><mo>=</mo><mfrac><msub><mi>n</mi><mi>k</mi></msub><mi>n</mi></mfrac></mrow><annotation>w_{k} =\frac{n_{k}}{n}</annotation></semantics></math>wk​=nnk​​，第<math><semantics><mrow><mi>k</mi></mrow><annotation>k</annotation></semantics></math>k组的样本均值<math><semantics><mrow><msub><mover><mi>Y</mi><mo>ˉ</mo></mover><mi>k</mi></msub></mrow><annotation>\bar{Y}_{k}</annotation></semantics></math>Yˉk​，则有如下等式：<br/>
<math><semantics><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mtext>strat</mtext></msub><mo>=</mo><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>K</mi></munderover><msub><mi>w</mi><mi>k</mi></msub><msub><mover><mi>Y</mi><mo>ˉ</mo></mover><mi>k</mi></msub><mo>=</mo><mover><mi>Y</mi><mo>ˉ</mo></mover><mspace></mspace><mrow><mo>(</mo><msub><mi>w</mi><mi>k</mi></msub><mo>=</mo><mfrac><msub><mi>n</mi><mi>k</mi></msub><mi>n</mi></mfrac><mo>)</mo></mrow></mrow><annotation>
\hat{Y}_{\text {strat}}=\sum_{k=1}^{K} w_{k} \bar{Y}_{k}=\bar{Y} \quad\left(w_{k}=\frac{n_{k}}{n}\right)
</annotation></semantics></math>Y^strat​=k=1∑K​wk​Yˉk​=Yˉ(wk​=nnk​​)<br/>
此处用分层后的<math><semantics><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mtext>strat</mtext></msub></mrow><annotation>\hat{Y}_{\text {strat}}</annotation></semantics></math>Y^strat​作为原始的样本均值的<math><semantics><mrow><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\bar{Y}</annotation></semantics></math>Yˉ的无偏估计。<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/22da722cea6db1823ae7.png"/></p>
</div><div><p>现对<math><semantics><mrow><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\bar{Y}</annotation></semantics></math>Yˉ求方差，具体如下，此处将<math><semantics><mrow><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\bar{Y}</annotation></semantics></math>Yˉ的方差分为等式右边第一部分的组内方差和第二部分的组间方差，正好第一部分的组内方差等于<math><semantics><mrow><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\bar{Y}</annotation></semantics></math>Yˉ的无偏估计量<math><semantics><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mtext>strat</mtext></msub></mrow><annotation>\hat{Y}_{\text {strat}}</annotation></semantics></math>Y^strat​的方差。<br/>
<math><semantics><mtable columnalign="right left" columnspacing="0em" rowspacing="0.24999999999999992em"><mtr><mtd><mstyle displaystyle="true"><mrow><mi mathvariant="normal">var</mi><mo>⁡</mo><mo>(</mo><mover><mi>Y</mi><mo>ˉ</mo></mover><mo>)</mo></mrow></mstyle></mtd><mtd><mstyle displaystyle="true"><mrow><mrow></mrow><mo>=</mo><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>K</mi></munderover><mfrac><msub><mi>w</mi><mi>k</mi></msub><mi>n</mi></mfrac><msubsup><mi>σ</mi><mi>k</mi><mn>2</mn></msubsup><mo>+</mo><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>K</mi></munderover><mfrac><msub><mi>w</mi><mi>k</mi></msub><mi>n</mi></mfrac><msup><mrow><mo>(</mo><msub><mi>μ</mi><mi>k</mi></msub><mo>−</mo><mi>μ</mi><mo>)</mo></mrow><mn>2</mn></msup></mrow></mstyle></mtd></mtr><mtr><mtd><mstyle displaystyle="true"><mrow></mrow></mstyle></mtd><mtd><mstyle displaystyle="true"><mrow><mrow></mrow><mo>≥</mo><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>K</mi></munderover><mfrac><msub><mi>w</mi><mi>k</mi></msub><mi>n</mi></mfrac><msubsup><mi>σ</mi><mi>k</mi><mn>2</mn></msubsup><mo>=</mo><mi mathvariant="normal">var</mi><mo>⁡</mo><mrow><mo>(</mo><msub><mover><mi>Y</mi><mo>^</mo></mover><mtext>strat</mtext></msub><mo>)</mo></mrow></mrow></mstyle></mtd></mtr></mtable><annotation>
\begin{aligned}
\operatorname{var}(\bar{Y}) &amp;=\sum_{k=1}^{K} \frac{w_{k}}{n} \sigma_{k}^{2}+\sum_{k=1}^{K} \frac{w_{k}}{n}\left(\mu_{k}-\mu\right)^{2} \\
&amp; \geq \sum_{k=1}^{K} \frac{w_{k}}{n} \sigma_{k}^{2}=\operatorname{var}\left(\widehat{Y}_{\text {strat}}\right)
\end{aligned}
</annotation></semantics></math>var(Yˉ)​=k=1∑K​nwk​​σk2​+k=1∑K​nwk​​(μk​−μ)2≥k=1∑K​nwk​​σk2​=var(Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>strat​)​<br/>
由此可见，通过Stratification，可获得原始统计量的无偏估计量，同时具有更小的方差。<br/>
应用在AB-test中，具体计算方式如下：<br/>
<math><semantics><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>s</mi><mi>t</mi><mi>r</mi><mi>a</mi><mi>t</mi></mrow></msub><mo>=</mo><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>K</mi></munderover><msub><mi>w</mi><mi>k</mi></msub><msub><mover><mi>Y</mi><mo>ˉ</mo></mover><mi>k</mi></msub><mo>=</mo><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>K</mi></munderover><msub><mi>w</mi><mi>k</mi></msub><mrow><mo>(</mo><mfrac><mn>1</mn><msub><mi>n</mi><mi>k</mi></msub></mfrac><munder><mo>∑</mo><mrow><mi>i</mi><mo>:</mo><msub><mi>X</mi><mi>i</mi></msub><mo>=</mo><mi>k</mi></mrow></munder><msub><mi>Y</mi><mi>i</mi></msub><mo>)</mo></mrow></mrow><annotation>\hat{Y}_{strat} = \sum_{k=1}^{K}w_{k} \bar{Y}_{k}=\sum_{k=1}^{K} w_{k}\left(\frac{1}{n_{k}} \sum_{i: X_{i}=k} Y_{i}\right)</annotation></semantics></math>Y^strat​=k=1∑K​wk​Yˉk​=k=1∑K​wk​(nk​1​i:Xi​=k∑​Yi​)<br/>
<math><semantics><mrow><msub><mi mathvariant="normal">Δ</mi><mtext>strat</mtext></msub><mo>=</mo><msubsup><mover><mi>Y</mi><mo>^</mo></mover><mtext>strat</mtext><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msubsup><mo>−</mo><msubsup><mover><mi>Y</mi><mo>^</mo></mover><mtext>strat</mtext><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msubsup><mo>=</mo><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>K</mi></munderover><msub><mi>w</mi><mi>k</mi></msub><mrow><mo>(</mo><msubsup><mover><mi>Y</mi><mo>ˉ</mo></mover><mi>k</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msubsup><mo>−</mo><msubsup><mover><mi>Y</mi><mo>ˉ</mo></mover><mi>k</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msubsup><mo>)</mo></mrow></mrow><annotation>\Delta_{\text {strat}}=\hat{Y}_{\text {strat}}^{(t)}-\hat{Y}_{\text {strat}}^{(c)}=\sum_{k=1}^{K} w_{k}\left(\bar{Y}_{k}^{(t)}-\bar{Y}_{k}^{(c)}\right)</annotation></semantics></math>Δstrat​=Y^strat(t)​−Y^strat(c)​=k=1∑K​wk​(Yˉk(t)​−Yˉk(c)​)</p>
</div><div><h3>3.2控制变量(Control Variates)</h3>
</div><div><p>和上述思想一样，控制变量法同样是试图找到<math><semantics><mrow><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\bar{Y}</annotation></semantics></math>Yˉ的无偏且方差更小的估计量。但与分层不同的是，这里是找一个协变量（covariate）来构建一个以估计量为因变量的回归方程，具体如下，其中<math><semantics><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub></mrow><annotation>\widehat{Y}_{c v}</annotation></semantics></math>Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​是<math><semantics><mrow><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\bar{Y}</annotation></semantics></math>Yˉ的无偏估计量，<math><semantics><mrow><mi>θ</mi></mrow><annotation>\theta</annotation></semantics></math>θ为常数，<math><semantics><mrow><mi>X</mi></mrow><annotation>X</annotation></semantics></math>X为协变量。<br/>
<math><semantics><mtable><mtr><mtd></mtd><mtd><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>=</mo><mover><mi>Y</mi><mo>ˉ</mo></mover><mo>−</mo><mi>θ</mi><mover><mi>X</mi><mo>ˉ</mo></mover><mo>+</mo><mi>θ</mi><mi mathvariant="double-struck">E</mi><mi>X</mi></mrow></mtd><mtd></mtd><mtd><mtext>(2)</mtext></mtd></mtr></mtable><annotation>\widehat{Y}_{c v}=\bar{Y}-\theta \bar{X}+\theta \mathbb{E} X \tag {2}</annotation></semantics></math>Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​=Yˉ−θXˉ+θEX(2)<br/>
为何说<math><semantics><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub></mrow><annotation>\widehat{Y}_{c v}</annotation></semantics></math>Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​是<math><semantics><mrow><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\bar{Y}</annotation></semantics></math>Yˉ的无偏估计量呢？在等式(2)左右两边同时取期望得到：<br/>
<math><semantics><mtable><mtr><mtd></mtd><mtd><mrow><mi mathvariant="double-struck">E</mi><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>=</mo><mi mathvariant="double-struck">E</mi><mover><mi>Y</mi><mo>ˉ</mo></mover><mo>−</mo><mi>θ</mi><mi mathvariant="double-struck">E</mi><mover><mi>X</mi><mo>ˉ</mo></mover><mo>+</mo><mi>θ</mi><mi mathvariant="double-struck">E</mi><mi>X</mi></mrow></mtd><mtd></mtd><mtd><mtext>(3)</mtext></mtd></mtr></mtable><annotation>\mathbb{E}\widehat{Y}_{c v}=\mathbb{E}\bar{Y}-\theta \mathbb{E}\bar{X}+\theta \mathbb{E} X \tag {3}</annotation></semantics></math>EY<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​=EYˉ−θEXˉ+θEX(3)<br/>
因为<math><semantics><mrow><mi>θ</mi><mi mathvariant="double-struck">E</mi><mover><mi>X</mi><mo>ˉ</mo></mover><mo>=</mo><mi>θ</mi><mi mathvariant="double-struck">E</mi><mi>X</mi></mrow><annotation>\theta \mathbb{E}\bar{X}=\theta \mathbb{E} X</annotation></semantics></math>θEXˉ=θEX,所以(3)式化简得到：<br/>
<math><semantics><mrow><mi mathvariant="double-struck">E</mi><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>=</mo><mi mathvariant="double-struck">E</mi><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\mathbb{E}\widehat{Y}_{c v}=\mathbb{E}\bar{Y}</annotation></semantics></math>EY<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​=EYˉ<br/>
即<math><semantics><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub></mrow><annotation>\widehat{Y}_{c v}</annotation></semantics></math>Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​是<math><semantics><mrow><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\bar{Y}</annotation></semantics></math>Yˉ的无偏估计量。</p>
</div><div><p>接下来看看上面得到的无偏估计量<math><semantics><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub></mrow><annotation>\widehat{Y}_{c v}</annotation></semantics></math>Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​的方差：<br/>
<math><semantics><mtable><mtr><mtd></mtd><mtd><mtable columnalign="right left" columnspacing="0em" rowspacing="0.24999999999999992em"><mtr><mtd><mstyle displaystyle="true"><mrow><mi mathvariant="normal">var</mi><mo>⁡</mo><mrow><mo>(</mo><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>)</mo></mrow></mrow></mstyle></mtd><mtd><mstyle displaystyle="true"><mrow><mrow></mrow><mo>=</mo><mi mathvariant="normal">var</mi><mo>⁡</mo><mo>(</mo><mover><mi>Y</mi><mo>ˉ</mo></mover><mo>−</mo><mi>θ</mi><mover><mi>X</mi><mo>ˉ</mo></mover><mo>)</mo><mo>=</mo><mi mathvariant="normal">var</mi><mo>⁡</mo><mo>(</mo><mi>Y</mi><mo>−</mo><mi>θ</mi><mi>X</mi><mo>)</mo><mi mathvariant="normal">/</mi><mi>n</mi></mrow></mstyle></mtd></mtr><mtr><mtd><mstyle displaystyle="true"><mrow></mrow></mstyle></mtd><mtd><mstyle displaystyle="true"><mrow><mrow></mrow><mo>=</mo><mfrac><mn>1</mn><mi>n</mi></mfrac><mrow><mo>(</mo><mi mathvariant="normal">var</mi><mo>⁡</mo><mo>(</mo><mi>Y</mi><mo>)</mo><mo>+</mo><msup><mi>θ</mi><mn>2</mn></msup><mi mathvariant="normal">var</mi><mo>⁡</mo><mo>(</mo><mi>X</mi><mo>)</mo><mo>−</mo><mn>2</mn><mi>θ</mi><mi mathvariant="normal">cov</mi><mo>⁡</mo><mo>(</mo><mi>Y</mi><mo>,</mo><mi>X</mi><mo>)</mo><mo>)</mo></mrow></mrow></mstyle></mtd></mtr></mtable></mtd><mtd></mtd><mtd><mtext>(4)</mtext></mtd></mtr></mtable><annotation>
\begin{aligned}
\operatorname{var}\left(\widehat{Y}_{c v}\right) &amp;=\operatorname{var}(\bar{Y}-\theta \bar{X})=\operatorname{var}(Y-\theta X) / n \\
&amp;=\frac{1}{n}\left(\operatorname{var}(Y)+\theta^{2} \operatorname{var}(X)-2 \theta \operatorname{cov}(Y, X)\right)
\end{aligned} \tag {4}
</annotation></semantics></math>var(Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​)​=var(Yˉ−θXˉ)=var(Y−θX)/n=n1​(var(Y)+θ2var(X)−2θcov(Y,X))​(4)<br/>
我们的目的是让<math><semantics><mrow><mi mathvariant="normal">var</mi><mo>⁡</mo><mrow><mo>(</mo><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>)</mo></mrow></mrow><annotation>\operatorname{var}\left(\widehat{Y}_{c v}\right)</annotation></semantics></math>var(Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​)尽可能的小，此时可对<math><semantics><mrow><mi>θ</mi></mrow><annotation>\theta</annotation></semantics></math>θ求偏导，当偏导数等于0时，得到<br/>
<math><semantics><mtable><mtr><mtd></mtd><mtd><mrow><mi>θ</mi><mo>=</mo><mi mathvariant="normal">cov</mi><mo>⁡</mo><mo>(</mo><mi>Y</mi><mo>,</mo><mi>X</mi><mo>)</mo><mi mathvariant="normal">/</mi><mi mathvariant="normal">var</mi><mo>⁡</mo><mo>(</mo><mi>X</mi><mo>)</mo></mrow></mtd><mtd></mtd><mtd><mtext>(5)</mtext></mtd></mtr></mtable><annotation>\theta=\operatorname{cov}(Y, X) / \operatorname{var}(X)\tag {5}</annotation></semantics></math>θ=cov(Y,X)/var(X)(5)<br/>
也就是说，当<math><semantics><mrow><mi>θ</mi></mrow><annotation>\theta</annotation></semantics></math>θ满足上面条件时，<math><semantics><mrow><mi mathvariant="normal">var</mi><mo>⁡</mo><mrow><mo>(</mo><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>)</mo></mrow></mrow><annotation>\operatorname{var}\left(\widehat{Y}_{c v}\right)</annotation></semantics></math>var(Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​)可取得极小值。<br/>
再将(5)代入(4)化简可得到：<br/>
<math><semantics><mtable><mtr><mtd></mtd><mtd><mrow><mi mathvariant="normal">var</mi><mo>⁡</mo><mrow><mo>(</mo><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>)</mo></mrow><mo>=</mo><mi mathvariant="normal">var</mi><mo>⁡</mo><mo>(</mo><mover><mi>Y</mi><mo>ˉ</mo></mover><mo>)</mo><mrow><mo>(</mo><mn>1</mn><mo>−</mo><msup><mi>ρ</mi><mn>2</mn></msup><mo>)</mo></mrow></mrow></mtd><mtd></mtd><mtd><mtext>(6)</mtext></mtd></mtr></mtable><annotation>\operatorname{var}\left(\widehat{Y}_{c v}\right)=\operatorname{var}(\bar{Y})\left(1-\rho^{2}\right)\tag {6}</annotation></semantics></math>var(Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​)=var(Yˉ)(1−ρ2)(6)<br/>
其中<math><semantics><mrow><mi>ρ</mi><mo>=</mo><mi mathvariant="normal">cor</mi><mo>⁡</mo><mo>(</mo><mi>Y</mi><mo>,</mo><mi>X</mi><mo>)</mo></mrow><annotation>\rho=\operatorname{cor}(Y, X)</annotation></semantics></math>ρ=cor(Y,X)，即<math><semantics><mrow><mi>ρ</mi></mrow><annotation>\rho</annotation></semantics></math>ρ是<math><semantics><mrow><mi>Y</mi></mrow><annotation>Y</annotation></semantics></math>Y和<math><semantics><mrow><mi>X</mi></mrow><annotation>X</annotation></semantics></math>X的相关系数。因为<math><semantics><mrow><mo>−</mo><mn>1</mn><mo>≤</mo><mi>ρ</mi><mo>≤</mo><mn>1</mn></mrow><annotation>-1\leq\rho\leq1</annotation></semantics></math>−1≤ρ≤1，所以<math><semantics><mrow><mn>0</mn><mo>≤</mo><mrow><mo>(</mo><mn>1</mn><mo>−</mo><msup><mi>ρ</mi><mn>2</mn></msup><mo>)</mo></mrow><mo>≤</mo><mn>1</mn></mrow><annotation>0\leq\left(1-\rho^{2}\right)\leq1</annotation></semantics></math>0≤(1−ρ2)≤1，由此可以看出<br/>
<math><semantics><mrow><mi mathvariant="normal">var</mi><mo>⁡</mo><mrow><mo>(</mo><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>)</mo></mrow><mo>≤</mo><mi mathvariant="normal">var</mi><mo>⁡</mo><mo>(</mo><mover><mi>Y</mi><mo>ˉ</mo></mover><mo>)</mo></mrow><annotation>\operatorname{var}\left(\widehat{Y}_{c v}\right)\leq\operatorname{var}(\bar{Y})</annotation></semantics></math>var(Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​)≤var(Yˉ)<br/>
至此，我们就通过控制变量的方式，获得了<math><semantics><mrow><mover><mi>Y</mi><mo>ˉ</mo></mover></mrow><annotation>\bar{Y}</annotation></semantics></math>Yˉ的无偏且方差更小的估计量<math><semantics><mrow><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub></mrow><annotation>\widehat{Y}_{c v}</annotation></semantics></math>Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​，<strong><strong>且当<math><semantics><mrow><mi>Y</mi></mrow><annotation>Y</annotation></semantics></math>Y与<math><semantics><mrow><mi>X</mi></mrow><annotation>X</annotation></semantics></math>X相关性越强，<math><semantics><mrow><mi>ρ</mi></mrow><annotation>\rho</annotation></semantics></math>ρ越大，获得的无偏估计量的方差<math><semantics><mrow><mi mathvariant="normal">var</mi><mo>⁡</mo><mrow><mo>(</mo><msub><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>)</mo></mrow></mrow><annotation>\operatorname{var}\left(\widehat{Y}_{c v}\right)</annotation></semantics></math>var(Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv​)也越小。</strong></strong></p>
</div><div><h3>3.3控制变量在AB-test中具体的应用</h3>
</div><div><p>在AB-test中应用控制变量法会与上面稍有区别。现在我们返回到（1）中，我们试图找到<math><semantics><mrow><mi mathvariant="normal">Δ</mi></mrow><annotation>\Delta</annotation></semantics></math>Δ = <math><semantics><mrow><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>−</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><annotation>\bar{Y}^{(t)}-\bar{Y}^{(c)}</annotation></semantics></math>Yˉ(t)−Yˉ(c)的无偏估计<math><semantics><mrow><msub><mi mathvariant="normal">Δ</mi><mrow><mi>c</mi><mi>v</mi></mrow></msub><mo>=</mo><msubsup><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msubsup><mo>−</mo><msubsup><mover><mi>Y</mi><mo>^</mo></mover><mrow><mi>c</mi><mi>v</mi></mrow><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msubsup></mrow><annotation>\Delta_{c v}=\widehat{Y}_{c v}^{(t)}-\widehat{Y}_{c v}^{(c)}</annotation></semantics></math>Δcv​=Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv(t)​−Y<svg height="0.24em" preserveAspectRatio="none" viewBox="0 0 1062 239" width="100%"><path d="M529 0h5l519 115c5 1 9 5 9 10 0 1-1 2-1 3l-4 22
c-1 5-5 9-11 9h-2L532 67 19 159h-2c-5 0-9-4-11-9l-5-22c-1-6 2-12 8-13z"></path></svg>cv(c)​，为保证无偏，此时需要满足以下两个条件：<br/>
<strong><strong>a.<math><semantics><mrow><mi mathvariant="double-struck">E</mi><msup><mi>X</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>−</mo><mi mathvariant="double-struck">E</mi><msup><mi>X</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup><mo>=</mo><mn>0</mn></mrow><annotation>\mathbb{E} X^{(t)}-\mathbb{E} X^{(c)}=0</annotation></semantics></math>EX(t)−EX(c)=0，即实验组和对照组的协变量<math><semantics><mrow><mi>X</mi></mrow><annotation>X</annotation></semantics></math>X的期望相等。<br/>
b.(2)中实验组和对照组的<math><semantics><mrow><mi>θ</mi></mrow><annotation>\theta</annotation></semantics></math>θ是相同的。</strong></strong></p>
</div><div><p>为满足条件a，该论文认为效果比较好的是采用实验单元在实验前对应指标的数据作为协变量，例如，我们现在研究的是某个实验对用户人均时长的影响，以单个用户为例，<math><semantics><mrow><msub><mi>Y</mi><mi>i</mi></msub></mrow><annotation>{Y}_i</annotation></semantics></math>Yi​为实验期用户<math><semantics><mrow><mi>i</mi></mrow><annotation>i</annotation></semantics></math>i的时长，则用户<math><semantics><mrow><mi>i</mi></mrow><annotation>i</annotation></semantics></math>i的协变量<math><semantics><mrow><msub><mi>X</mi><mi>i</mi></msub></mrow><annotation>{X}_i</annotation></semantics></math>Xi​为该用户在实验前（空跑期）的时长，这样一方面保证了同一个用户<math><semantics><mrow><mi>Y</mi></mrow><annotation>Y</annotation></semantics></math>Y和<math><semantics><mrow><mi>X</mi></mrow><annotation>X</annotation></semantics></math>X之间的高度相关性，另一方面由于<math><semantics><mrow><msup><mi>X</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup></mrow><annotation>{X}^{(t)}</annotation></semantics></math>X(t)和<math><semantics><mrow><msup><mi>X</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><annotation>{X}^{(c)}</annotation></semantics></math>X(c)同属空跑期，未受实验treatment的影响，排除工程方面的异常，理论上<math><semantics><mrow><mi mathvariant="double-struck">E</mi><msup><mi>X</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup></mrow><annotation>\mathbb{E} X^{(t)}</annotation></semantics></math>EX(t)和<math><semantics><mrow><mi mathvariant="double-struck">E</mi><msup><mi>X</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><annotation>\mathbb{E} X^{(c)}</annotation></semantics></math>EX(c)是相等的。同时可以看到，文章的标题中的“Utilizing Pre-Experiment Data”就是来源于此。</p>
</div><div><p>为满足条件b，一个简单的方法是用pooled population进行计算，即将实验组和对照组的数据合在一起计算<math><semantics><mrow><mi>θ</mi></mrow><annotation>\theta</annotation></semantics></math>θ。同时文中还提到，这样的处理方式，对方差缩减的影响几乎可以忽略（但是没有相关的理论证明）</p>
</div><div><p>目前为止，为了公式(2)能够被顺利计算出来，我们已经知道可以用实验单元（user）实验前的数据作为协变量<math><semantics><mrow><mi>X</mi></mrow><annotation>X</annotation></semantics></math>X，同时可以用pooled population计算<math><semantics><mrow><mi>θ</mi></mrow><annotation>\theta</annotation></semantics></math>θ，一切问题都看似迎刃而解，但同时又出现了新的问题，很多实验中的用户，在实验前的空跑期并未出现，将这部分用户定义为实验的“新用户”，我们无法在空跑期获得这部分用户的相关数据，即部分<math><semantics><mrow><mi>X</mi></mrow><annotation>X</annotation></semantics></math>X是缺失的。</p>
</div><div><p>此处可结合3.1中的分层的思想，<strong><strong>即将用户按照实验之前(空跑期)出现与否分成新、老用户，新用户就按照普通方式计算方差，老用户可以采用控制变量法对方差进行缩减。</strong></strong></p>
</div><div><h2>4.CUPED的应用</h2>
</div><div><h3>4.1 CUPED在实际实验中的效果</h3>
</div><div><p>为了验证CUPED算法在实际实验中的效果，现从看点阿拉丁实验平台上获取了看点快报某一实验的真实数据，对算法进行复现。该实验是在实验桶用户中引入了视频的用户画像，希望对比对照桶中的用户，实验桶中用户的主TL视频人均时长等核心指标有所增长。</p>
</div><div><p>现以主TL视频人均时长为例，取该实验开始后连续9天的数据，具体如下表。可以看到经过CUPED算法处理后，实验组和对照组均值方差之和<math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo></mrow><annotation>var(\Delta)</annotation></semantics></math>var(Δ)较未处理的均值方差之和缩减了60%左右，另一方面，原本9天都不见显著差异的实验，经过CUPED处理之后，在第5天<math><semantics><mrow><mi>p</mi></mrow><annotation>p</annotation></semantics></math>p值小于0.05，即实验组和对照组出现显著差异，实验时间得以大大缩短。</p>
</div><div><div><table>
<thead>
<tr>
<th>主TL视频人均时长</th>
<th>day1</th>
<th>day2</th>
<th>day3</th>
<th>day4</th>
<th>day5</th>
<th>day6</th>
<th>day7</th>
<th>day8</th>
<th>day9</th>
</tr>
</thead>
<tbody>
<tr>
<td>对照桶新用户数</td>
<td>44781</td>
<td>78503</td>
<td>109849</td>
<td>138709</td>
<td>167669</td>
<td>197596</td>
<td>226783</td>
<td>251585</td>
<td>278556</td>
</tr>
<tr>
<td>对照桶老用户数</td>
<td>184842</td>
<td>239549</td>
<td>266680</td>
<td>286548</td>
<td>300231</td>
<td>312113</td>
<td>321788</td>
<td>329995</td>
<td>336941</td>
</tr>
<tr>
<td>对照桶新用户占比</td>
<td>19.5%</td>
<td>24.7%</td>
<td>29.2%</td>
<td>32.6%</td>
<td>35.8%</td>
<td>38.8%</td>
<td>41.3%</td>
<td>43.3%</td>
<td>45.3%</td>
</tr>
<tr>
<td><math><semantics><mrow><mi mathvariant="normal">Δ</mi><mo>=</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>−</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup></mrow><annotation>\Delta=\bar{Y}^{(t)}-\bar{Y}^{(c)}</annotation></semantics></math>Δ=Yˉ(t)−Yˉ(c)</td>
<td>1.4</td>
<td>1.4</td>
<td>1.8</td>
<td>2.3</td>
<td>2.8</td>
<td>2.9</td>
<td>3.1</td>
<td>3.9</td>
<td>4.1</td>
</tr>
<tr>
<td><math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo></mrow><annotation>var(\Delta)</annotation></semantics></math>var(Δ)</td>
<td>1.1</td>
<td>1.9</td>
<td>2.7</td>
<td>3.6</td>
<td>4.5</td>
<td>5.5</td>
<td>6.4</td>
<td>7.4</td>
<td>8.3</td>
</tr>
<tr>
<td><math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo></mrow><annotation>var(\Delta)</annotation></semantics></math>var(Δ)（CUPED）</td>
<td>0.6</td>
<td>0.9</td>
<td>1.2</td>
<td>1.5</td>
<td>1.8</td>
<td>2.1</td>
<td>2.4</td>
<td>2.7</td>
<td>3.0</td>
</tr>
<tr>
<td><math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo></mrow><annotation>var(\Delta)</annotation></semantics></math>var(Δ)_diff%</td>
<td>-42.0%</td>
<td>-51.3%</td>
<td>-56.4%</td>
<td>-59.1%</td>
<td>-60.9%</td>
<td>-62.1%</td>
<td>-62.9%</td>
<td>-63.4%</td>
<td>-63.8%</td>
</tr>
<tr>
<td>P-Value</td>
<td>18.9%</td>
<td>29.2%</td>
<td>27.8%</td>
<td>21.3%</td>
<td>18.1%</td>
<td>21.3%</td>
<td>21.5%</td>
<td>14.8%</td>
<td>15.8%</td>
</tr>
<tr>
<td>P-Value (CUPED)</td>
<td>8.5%</td>
<td>13.1%</td>
<td>10.1%</td>
<td>5.2%</td>
<td>3.2%</td>
<td>4.3%</td>
<td>4.2%</td>
<td>1.7%</td>
<td>1.9%</td>
</tr>
</tbody>
</table>
</div></div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/90ededd9288cb71e309f.png"/></p>
</div><div><h3>4.2 CUPED对实验效率的改善</h3>
</div><div><p>上面的<math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo></mrow><annotation>var(\Delta)</annotation></semantics></math>var(Δ)是实验组和对照组均值方差之和，假定实验组和对照组人数完全相等，都等于<math><semantics><mrow><mi>n</mi></mrow><annotation>n</annotation></semantics></math>n，我们可以倒推得到实验组和对照组方差之和为<math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo><mo>∗</mo><mi>n</mi></mrow><annotation>var(\Delta)*n</annotation></semantics></math>var(Δ)∗n，上面提到使用CUPED之后<math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo></mrow><annotation>var(\Delta)</annotation></semantics></math>var(Δ)会降低60%左右，即实验组和对照组方差之和<math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi mathvariant="normal">Δ</mi><mo>)</mo><mo>∗</mo><mi>n</mi></mrow><annotation>var(\Delta)*n</annotation></semantics></math>var(Δ)∗n也会降低60%。<br/>
在<math><semantics><mrow><mi>α</mi><mo>=</mo><mn>0.05</mn></mrow><annotation>\alpha = 0.05</annotation></semantics></math>α=0.05，<math><semantics><mrow><mi>β</mi><mo>=</mo><mn>0.20</mn></mrow><annotation>\beta = 0.20</annotation></semantics></math>β=0.20时，实验所需最小样本量为（具体证明过程请见Statistical Rules of Thumb, 2nd Edition By Gerald van Belle，page27）：<br/>
<math><semantics><mrow><mi>n</mi><mo>=</mo><mfrac><mrow><mn>16</mn><msup><mi>σ</mi><mn>2</mn></msup></mrow><msup><mi mathvariant="normal">Δ</mi><mn>2</mn></msup></mfrac><mo>=</mo><mfrac><mrow><mn>16</mn><msup><mi>σ</mi><mn>2</mn></msup></mrow><mrow><mo>(</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>−</mo><msup><mover><mi>Y</mi><mo>ˉ</mo></mover><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup><msup><mo>)</mo><mn>2</mn></msup></mrow></mfrac></mrow><annotation>n = \dfrac{16\sigma^2}{\Delta^2} = \dfrac{16\sigma^2}{(\bar{Y}^{(t)} - \bar{Y}^{(c)})^2}</annotation></semantics></math>n=Δ216σ2​=(Yˉ(t)−Yˉ(c))216σ2​<br/>
所以在<math><semantics><mrow><mi mathvariant="normal">Δ</mi></mrow><annotation>\Delta</annotation></semantics></math>Δ一定时，<math><semantics><mrow><mi>n</mi><mo>∝</mo><msup><mi>σ</mi><mn>2</mn></msup></mrow><annotation>n\propto\sigma^2</annotation></semantics></math>n∝σ2，即最小样本量和方差成正比。因此，使用CUPED方法，方差降低60%，则实验所需样本也降低60%，如之前需要10万人的实验，使用CUPED之后，仅需4万人。</p>
</div><div><p><strong>可粗略的有如下估算，假设某个实验分层有100个桶，实验组、对照组各50个桶，因此同一时间最多可执行50个实验。每个桶10万用户，且10万≥每个实验所需的最小样本量，使用CUPED之后，可将每个桶人数缩减为4万人，则可分为250个桶。并行能力从原本的同时执行50个实验提升至同时执行125个实验，提升了150%。</strong></p>
</div><div><p><strong>另外也可以从实验耗时的层面来考虑，具体如下表所示。未做任何处理时，实验的方差是1545656，在希望检测的delta为5s时，所需要的样本量为99万人，累积该数量的用户大致需要19天（用户需去重）；当使用CUPED进行处理后，方差缩减至645633，方差变化为-58%，在同样检测delta为5s的情况下，所需样本量为41万，仅需5天左右就能达到该用户量，实验时长得到大大缩短。这也从某种程度上解释了，为何上面的实验在第9天为何仍未出现显著差异。</strong></p>
</div><div><div><table>
<thead>
<tr>
<th></th>
<th>方差</th>
<th>方差变化</th>
<th>希望检测delta</th>
<th>所需样本量</th>
<th>所需天数</th>
</tr>
</thead>
<tbody>
<tr>
<td>未处理</td>
<td>1545656</td>
<td></td>
<td>5s</td>
<td>989219</td>
<td>19天</td>
</tr>
<tr>
<td>CUPED</td>
<td>645633</td>
<td>-58%</td>
<td>5s</td>
<td>413205</td>
<td>5天</td>
</tr>
</tbody>
</table>
</div></div><div><p>综上，CUPED算法对实验所需样本量的缩减或者实验加速方面，都有较为明显的效果，即实验效率得到大大提升。</p>
</div><div><h2>5.CUPED不足与改进方案（CUPED-Plus)</h2>
</div><div><p>从上面可以看到，CUPED方法对样本方差，或者说实验效率的改善都有很大的提升，但是同样CUPED仍是有可改进的空间的，因为其仅仅对实验期和空跑期都出现的用户（即老用户）做了方差的缩减，而新用户由于缺乏空跑期的数据，而找不到一个很好的协变量来缩减方差。但从上面的例子，我们可以看到，随着实验时间的拉长，新用户占比越来越多，在第9天时，将近一半的用户都是新用户，即一半的用户的方差无法得到缩减，因此，考虑新用户的方差缩减，在很多实验中显得尤为重要。</p>
</div><div><p>如果我们考虑从实验期的数据中找新用户的协变量，可能会违背3.3中的条件(<math><semantics><mrow><mi mathvariant="double-struck">E</mi><msup><mi>X</mi><mrow><mo>(</mo><mi>t</mi><mo>)</mo></mrow></msup><mo>−</mo><mi mathvariant="double-struck">E</mi><msup><mi>X</mi><mrow><mo>(</mo><mi>c</mi><mo>)</mo></mrow></msup><mo>=</mo><mn>0</mn></mrow><annotation>\mathbb{E} X^{(t)}-\mathbb{E} X^{(c)}=0</annotation></semantics></math>EX(t)−EX(c)=0)，因为在实验期，实验组受到了某种treatment，很多指标都会受到影响，使得实验组和对照组的该指标的期望不相等，进而不能作为一个良好的协变量来缩减方差。</p>
</div><div><h3>5.1 CUPED-Plus算法</h3>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4a080b97e3ea459b7898.png"/></p>
</div><div><p>上图左侧为CUPED算法流程，此处不做赘述；右侧为在此基础之上改进的CUPED-Plus算法，具体以手Q看点为例进行讲解:</p>
</div><div><h4>1) 数据源获取</h4>
</div><div><p>此处以手Q看点为例，手Q看点是嵌入在手Q中的一款产品，即若该用户是看点的用户，则他一定也是手Q的用户，另一方面，手Q的本质是一款社交产品，而看点则是信息流产品，在功能上，两者又有一定的独立性。因此，当我们在看点做实验时，可以考虑从手Q的数据中，获取新用户的协变量，对应上图中的<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mn>2</mn></mrow><annotation>X\_new\_2</annotation></semantics></math>X_new_2，但仍需注意看点中的实验，是否会引起用户在手Q中行为的变化，即数据源对实验的安全性有待商榷。进一步地，我们可以把协变量数据源再向外扩展，即考虑实验产品所属app以外的其他app，如考虑，对应上图中的<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mn>3</mn></mrow><annotation>X\_new\_3</annotation></semantics></math>X_new_3。若选择作为协变量的来源，优点在于可以覆盖绝大多数的新用户，同时可以忽略看点中实验，对用户在中行为的影响，安全性较高，即可以认为<math><semantics><mrow><mi>E</mi><mo>(</mo><mi>X</mi><mi mathvariant="normal">_</mi><mi>t</mi><mo>)</mo><mo>=</mo><mi>E</mi><mo>(</mo><mi>X</mi><mi mathvariant="normal">_</mi><mi>c</mi><mo>)</mo></mrow><annotation>E(X\_t) = E(X\_c)</annotation></semantics></math>E(X_t)=E(X_c)也是成立，但此种方法，也存在一定的障碍，即数据获取困难，以及难以做到完全覆盖全量新用户。最后，实验期看点自身的数据仍值得作为备选，对应上图中的<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mn>1</mn></mrow><annotation>X\_new\_1</annotation></semantics></math>X_new_1，尽管其安全性较低，但它对全量新用户的覆盖度以及数据获取的容易程度仍是其最明显的优势。三种数据源优劣如下：</p>
</div><div><div><table>
<thead>
<tr>
<th>协变量来源</th>
<th>X_new_1(看点)</th>
<th>X_new_2(手Q)</th>
<th>X_new_3()</th>
</tr>
</thead>
<tbody>
<tr>
<td>1.是否可获得全量新用户数据</td>
<td>可</td>
<td>可</td>
<td>否</td>
</tr>
<tr>
<td>2.数据获取难度/工程复杂度</td>
<td>低</td>
<td>中</td>
<td>高</td>
</tr>
<tr>
<td>3.使用该数据源安全性</td>
<td>低</td>
<td>中</td>
<td>高</td>
</tr>
</tbody>
</table>
</div></div><div><p>即无论是手Q看点这样的嵌套式产品，抑或是独立的产品，都可以考虑从产品内部或者外部关联产品获取数据，作为新用户的协变量，具体数据源的选择，可根据产品自身情况，同时考虑上述三方面来决定。</p>
</div><div><h4>2) 安全性验证</h4>
</div><div><p>从上述数据源获得协变量<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi><mo>(</mo><mi>i</mi><mo>=</mo><mn>1</mn><mo>,</mo><mn>2</mn><mo>,</mo><mn>3</mn><mo>)</mo></mrow><annotation>X\_new\_i(i=1,2,3)</annotation></semantics></math>X_new_i(i=1,2,3)之后，需进行安全性验证，即用AA-test验证实验组和对照组的<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi></mrow><annotation>X\_new\_i</annotation></semantics></math>X_new_i期望是否相等，即<math><semantics><mrow><mi>E</mi><mo>(</mo><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi><mo>)</mo><mi mathvariant="normal">_</mi><mi>t</mi><mo>=</mo><mi>E</mi><mo>(</mo><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi><mo>)</mo><mi mathvariant="normal">_</mi><mi>c</mi></mrow><annotation>E(X\_new\_i)\_t = E(X\_new\_i)\_c</annotation></semantics></math>E(X_new_i)_t=E(X_new_i)_c。当该等式不成立时，放弃将<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi></mrow><annotation>X\_new\_i</annotation></semantics></math>X_new_i作为协变量，当等式成立时，可初步获得该协变量<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi></mrow><annotation>X\_new\_i</annotation></semantics></math>X_new_i。</p>
</div><div><h4>3) 最终协变量的获取</h4>
</div><div><p>通过安全性验证的<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi></mrow><annotation>X\_new\_i</annotation></semantics></math>X_new_i可能有多个，需进行进一步的筛选。由于X与Y的相关性越大时，方差缩减的效果越好，因此依次计算新用户实验期数据<math><semantics><mrow><mi>Y</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi></mrow><annotation>Y\_new</annotation></semantics></math>Y_new与<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi><mo>(</mo><mi>i</mi><mo>=</mo><mn>1</mn><mo>,</mo><mn>2</mn><mo>,</mo><mn>3</mn><mo>)</mo></mrow><annotation>X\_new\_i(i=1,2,3)</annotation></semantics></math>X_new_i(i=1,2,3)的相关系数，取相关系数最大的<math><semantics><mrow><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi></mrow><annotation>X\_new\_i</annotation></semantics></math>X_new_i作为最终的协变量。</p>
</div><div><h4>4) 新用户方差缩减</h4>
</div><div><p>与前述CUPED类似，通过<math><semantics><mrow><mi>θ</mi><mo>=</mo><mi>c</mi><mi>o</mi><mi>v</mi><mo>(</mo><mi>Y</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mo>,</mo><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi><mo>)</mo><mi mathvariant="normal">/</mi><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi><mo>)</mo></mrow><annotation>θ = cov(Y\_new,X\_new\_i)/var(X\_new\_i)</annotation></semantics></math>θ=cov(Y_new,X_new_i)/var(X_new_i)和<math><semantics><mrow><mi>Y</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>c</mi><mi>v</mi><mo>=</mo><mi>Y</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mo>−</mo><mi>θ</mi><mi>m</mi><mi>e</mi><mi>a</mi><mi>n</mi><mo>(</mo><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi><mo>)</mo><mo>+</mo><mi>θ</mi><mi>E</mi><mo>(</mo><mi>X</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>i</mi><mo>)</mo></mrow><annotation>Y\_new\_cv = Y\_new - θmean(X\_new\_i) + θE(X\_new\_i)</annotation></semantics></math>Y_new_cv=Y_new−θmean(X_new_i)+θE(X_new_i)可得到<math><semantics><mrow><mi>v</mi><mi>a</mi><mi>r</mi><mo>(</mo><mi>Y</mi><mi mathvariant="normal">_</mi><mi>n</mi><mi>e</mi><mi>w</mi><mi mathvariant="normal">_</mi><mi>c</mi><mi>v</mi><mo>)</mo></mrow><annotation>var(Y\_new\_cv)</annotation></semantics></math>var(Y_new_cv)，即新用户的方差得以缩减。</p>
</div><div><h4>5) 新用户方差缩减</h4>
</div><div><p>使用Stratification方法整合新、老用户方差，实现全量用户方差缩减。</p>
</div><div><p><strong>综上，通过CUPED-Plus的方法，我们可以获得较为安全的新用户的协变量，从而降低新用户的方差，最后，再结合Stratification的思想，对新、老用户各自处理的结果进行组合，使得全量用户的方差得以缩减，实验效率亦能得到更进一步的提升。</strong></p>
</div><div><h3>5.2 CUPED-Plus算法在看点阿拉丁实验平台的实践</h3>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ed0e1d716a60b05e6b23.png"/><br/>
CUPED-Plus算法已经在看点阿拉丁实验平台上线，具体交互界面如图所示，其中算法计算结果显示在最右侧的“显著性”列。</p>
</div><div><p>当电池格满格时，表示使用CUPED-Plus对原始数据方差缩减后，假设检验的计算结果为 “实验组和对照组差异显著”，再结合差异的正负，实验者可判断该实验的treatment是否可以应用于全量用户。</p>
</div><div><p>当电池格为空时，表示使用CUPED-Plus对原始数据方差缩减后，假设检验的计算结果为 “实验组和对照组不存在差异显著”，即实验对用户不存在明显的影响，实验者会放弃将此实验的treatment应用于全量用户。</p>
</div><div><p>当电池格裂开时，说明数据不适合假设检验计算，无法判断实验组和对照组是否存在差异。</p>
</div><div><p>另外，在阿拉丁中，同时还会展示实验组与对照组差异的变化情况。其中黄色折线为实验组与对照组，从实验开始至之后某一天的累计值的绝对差异，在如下实验中，实验组和对照组的累计差异是随实验时间递增的；垂直的绿色线段表示绝对差异delta的置信区间，当该置信区间包含0时，表示差异不显著，当该置信区间中，不包含0时，表示实验组和对照组存在统计学显著差异，在如下实验中，到7月3号时，0在置信区间之外，说明实验存在显著差异。<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/053f3891f12c55e89959.png"/></p>
</div><div><p>最后，附上看点阿拉丁实验平台整体界面，具体如下：<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6617e689e122f566f6ab.png"/></p>
</div><div><h2>6.后续工作</h2>
</div><div><p>如上如述，在组内小伙伴的通力合作之下，CUPED-Plus算法已成功上线至看点阿拉丁实验平台，为小流量实验提供了一个良好的解决方案，并且该算法已提交至公司的专利电子平台，希望能早日通过。同时，希望有机会和TAB等实验中台合作，深入地交流探讨，并协力为更多产品的小流量实验的评估提供更行之有效的落地方案。</p>
</div><div><p>参考文献：</p>
</div><div><ol>
<li><a href="https://exp-platform.com/Documents/2013-02-CUPED-ImprovingSensitivityOfControlledExperiments.pdf">Improving the Sensitivity of Online Controlled Experimentsby Utilizing Pre-Experiment Data</a></li>
<li><a href="https://booking.ai/how-booking-com-increases-the-power-of-online-experiments-with-cuped-995d186fff1d">How Booking.com increases the power of online experiments with CUPED</a></li>
<li><a href="https://www.slideshare.net/tushuhei/improving-the-sensitivity-of-online-controlled-experiments-by-utilizing-preexperiment-data">Improving the Sensitivity of Online Controlled Experiments by Utilizing Pre-Experiment Data-PPT_version</a></li>
<li>Statistical Rules of Thumb, 2nd Edition By Gerald van Belle</li>
<li>Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing by Ron Kohavi, Diane Tang, Ya Xu</li>
</ol>
</div> 
{% endraw %}
