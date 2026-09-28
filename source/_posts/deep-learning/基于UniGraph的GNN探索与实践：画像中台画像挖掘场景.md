---
title: "基于UniGraph的GNN探索与实践：画像中台画像挖掘场景"
date: 2022-04-22 21:39:48
categories:
  - deep-learning
---

<div class="document">
<div>
<div class="document">
<h1 class="paragraph text-align-type-justify pap-line-1.7 pap-line-rule-auto pap-spacing-before-15.6pt pap-spacing-after-15.6pt toc-enable" style="text-align:justify;line-height:1.7;margin-top:20.8px;margin-bottom:20.8px;" id="4d10fee0-e991-9c82-43ea-c50a0069e4d8"><span style="font-size:22pt;font-family:&#39;Helvetica Neue&#39;, Helvetica, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-weight:bold;font-style:normal;color:#000000;background:transparent;letter-spacing:0pt;vertical-align:baseline;">UniGraph：数据资产图谱</span><span style="font-size:24pt;font-family:SimSun, &#39;Helvetica Neue&#39;, Helvetica, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-weight:bold;font-style:normal;color:#000000;background:transparent;letter-spacing:0pt;vertical-align:baseline;"></span></h1>
</div>
</div>
<div>
<div class="document">
<div class="document">

<div style="border-left:5px solid #e2e3e4;padding-left:10px;margin-top:20px;">
<p>注：算法同学后续再Baseline的基础上添加了一系列新特征之后，16-25岁年龄段的Baseline模型的准确率提升到了76.32%，在此基础上的ResGNN进一步将模型准确率提升到79.26%（准确率+2.94%）。更进一步证明了ResGNN的有效性。</p>
</div>
<div>
<div class="document">
<p class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt">为了更全面地分析ResGNN每一个模块的作用，我们对16—25岁年龄段的用户做了比较详细的对比实验分析，包括：1）Graph选择对比；2）GNN模型选择对比；3）消融实验对比。接下来我们详细介绍这几部分。</p>
</div>
</div>
<div>
<div class="document">
<h2 class="paragraph text-align-type-justify pap-line-1.7 pap-line-rule-auto pap-spacing-before-15.6pt pap-spacing-after-15.6pt toc-enable" id="10438844-14a4-f8d3-29be-81be8cde3814">对比实验分析</h2>
</div>

<h3 class="paragraph text-align-type-left pap-line-1.7 pap-line-rule-auto pap-spacing-before-0pt pap-spacing-after-0pt toc-enable" id="1c2f92fd-e6fb-541a-65a5-c65363cc3ab2">图选择对比实验</h3>
<div>
<div class="document">
<div>
<div class="document">
<p class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt" style="text-align:justify;margin-top:19.2px;margin-bottom:19.2px;">不同Graph包含的结构信息对于具体的画像挖掘任务的作用是不一样的。为了对比不同的Graph包含的结构信息对学历预测这一任务准确度的影响，我们对比了：某图一，某图二，PNode信息，三种类型的Graph，详细的试验结果如下：<span style="font-size:12pt;font-family:SimSun, &#39;Helvetica Neue&#39;, Helvetica, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-weight:400;font-style:normal;color:#000000;background:transparent;letter-spacing:0pt;vertical-align:baseline;"></span></p>
</div>
</div>
</div>

<table><colgroup><col width="201"><col width="201"><col width="201"></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>图类型</strong></p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>准确率</strong></p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>绝对值提升</strong></p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">Baseline</p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">72.26%</p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">-</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<div>
<div class="document">
<p class="paragraph text-align-type-center pap-spacing-before-14.4pt pap-spacing-after-14.4pt">ResGNN w/ 某图一</p>
</div>
</div>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">72.92%</p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">+0.66%</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">ResGNN w/ 某图二</p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">71.45%</p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">-0.81%</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>ResGNN w/</strong> <strong>PNode</strong></p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>75.71%</strong></p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>+3.45%</strong></p>
</td>
</tr></tbody></table><div>
<div class="document">
<p class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt"><span style="text-align:justify;">从实验结果可以看出，使用</span><span style="text-align:justify;">PNode</span><span style="text-align:justify;">信息所构建的Graph所包含的信息对于学历预测这一任务所带来的的提升最显著。</span><br></p>
<div>
<div class="document">
<h3 class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt toc-enable" style="text-align:justify;margin-top:19.2px;margin-bottom:19.2px;" id="3777249e-bf4c-08eb-e510-b4f3b1acfdf5">模型选型对比实验<span style="font-size:12pt;font-family:SimSun, &#39;Helvetica Neue&#39;, Helvetica, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-weight:400;font-style:normal;color:#000000;background:transparent;letter-spacing:0pt;vertical-align:baseline;"></span></h3>
</div>
</div>
</div>
</div>
<div>
<div class="document">
<p class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt">工业界常见的GNN模型有GraphSage和GAT，为了对比不同的GNN模型对学历预测任务准确率的影响，基于PNode信息构建的图，我们对比了GraphSage（mean pooling）和GAT两种模型的效果，实验结果如下：</p>
</div>

<table><colgroup><col width="201"><col width="201"><col width="201"></colgroup><tbody><tr><td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>模型</strong></p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>准确率</strong></p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>绝对值提升</strong></p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">Baseline<br></p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">72.26%</p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">-</p>
</td>
</tr><tr><td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">ResGNN w/ GraphSage<br></p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">73.75%</p>
</td>
<td colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">+1.49%</p>
</td>
</tr><tr><td>
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>ResGNN w/ GAT</strong></p>
</td>
<td>
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>75.71%</strong><br></p>
</td>
<td>
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>+3.45%</strong><br></p>
</td>
</tr></tbody></table><div>
<div class="document">
<p class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt">实验结果表明，带有Attention的GAT模型能通过attention机制在聚合图信息方面更能有的放矢的挖掘到有用的邻居信息，取得了更好的效果。</p>
</div>

<h3 class="paragraph text-align-type-left pap-line-1.7 pap-line-rule-auto pap-spacing-before-0pt pap-spacing-after-0pt toc-enable" id="7ee0567e-dafb-26f8-adc5-e16c9984745e">消融实验</h3>
<p class="paragraph text-align-type-justify pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">由于加入了PNode图的过程中不可避免的带入了PNode id，为了排除PNode id引入的额外信息的影响，我们做了一个简单的消融实验以验证GNN结构能有效地抽取图结构特征，从而证明ResGNN框架结构的有效性。于是我们将PNode特征作为user特征加入到原模型当中作为multi-hot 特征，做了如下对比实验。</p>
<table><colgroup><col width="201"><col width="201"><col width="201"></colgroup><tbody><tr><td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>模型</strong></p>
</td>
<td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>准确率</strong></p>
</td>
<td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>绝对值提升</strong></p>
</td>
</tr><tr><td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">Baseline</p>
</td>
<td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">72.26%</p>
</td>
<td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">-</p>
</td>
</tr><tr><td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">baseline w/ PNode特征</p>
</td>
<td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">72.56%</p>
</td>
<td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">+0.30%</p>
</td>
</tr><tr><td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>Res GNN w/ PNode</strong></p>
</td>
<td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>75.71%</strong></p>
</td>
<td width="201" colspan="1" rowspan="1">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><strong>+3.45%</strong></p>
</td>
</tr></tbody></table><p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">从实验结果可以看出，在Baseline的特征上加入PNode的特征后，只取得了略优于Baselin模型的效果。但是使用了ResGNN的网络架构，却显著提升了模型的准确率。也就是说，相较于直接将异构图中其他的节点特征作为原模型的输入特征，ResGNN模型能更好的抽取图结构特征得到更有意义的信息，也更进一步地证明了ResGNN的有效性。</p>
<div>
<div class="document">
<h1 class="paragraph text-align-type-left pap-line-1.7 pap-line-rule-auto pap-spacing-before-12pt pap-spacing-after-12pt toc-enable" style="text-align:left;line-height:1.7;margin-top:16px;margin-bottom:16px;" id="69ab491b-c9d0-3e8a-8d3a-0c3879458df7">总结<span style="font-size:22pt;font-family:&#39;Helvetica Neue&#39;, Helvetica, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-weight:bold;font-style:normal;color:#000000;background:transparent;letter-spacing:0pt;vertical-align:baseline;"></span></h1>
</div>
</div>
<div>
<div class="document">
<div>
<div class="document">
<p class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt">立足于UniGraph这一规模最大、数据质量最高的跨端异质数据图谱，我们提出了基于GNN的画像挖掘新范式ResGNN，基于该范式算法同学只需要对自己原有的Baseline模型稍加改动就能融入图数据的结构信息，取得更好的预测准确率。同时，我们也将提出的ResGNN画像挖掘新范式应用于画像中台的学历画像预测任务中，显著地提升了该任务的预测准确率，从而也实际验证了ResGNN框架的有效性。</p>
<p class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt" style="text-align:justify;margin-top:19.2px;margin-bottom:19.2px;">除了画像挖掘，UniGraph在支持搜索、广告、推荐、PUSH、反作弊等业务场景上同样可以发挥巨大的作用，如果你希望利用丰富的数据建模非欧式空间中的结构化信息，以此提升业务指标，那么UniGraph一定是你不可错过的宝贵资源。欢迎你随时联系@boristan，@mochigao，@answerzhong了解UniGraph以及已有的成功落地经验。</p>
</div>
</div>
</div>
</div>
<div>
<div class="document">
<div class="document">
<div>
<div class="document">
<div>
<div class="document">
<h1 class="paragraph text-align-type-justify pap-line-1.7 pap-line-rule-auto pap-spacing-before-15.6pt pap-spacing-after-15.6pt toc-enable" id="21511050-ccc8-6dea-56c1-c65cfec37cd7">鸣谢</h1>
<p class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt">感谢团队@mochigao，@boristan，@jasonmliu，@harryyfhu，@felixzhuo， @gxgxzhang等小伙伴和老板们的给力支持，也感谢画像挖掘组的小伙伴@sigmayang，@echokong, @raycheng的大力配合与支持。</p>
<p class="paragraph text-align-type-justify pap-spacing-before-14.4pt pap-spacing-after-14.4pt" style="text-align:justify;margin-top:19.2px;margin-bottom:19.2px;">本文中的算法实现基于公司开源图框架Platodeep2进行开发，感谢PlatoDeep2团队的@healyhuang大佬的支持指导。<span style="font-size:12pt;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-weight:400;font-style:normal;color:#000000;background:transparent;letter-spacing:0pt;vertical-align:baseline;"></span></p>
