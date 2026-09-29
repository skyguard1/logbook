---
title: "OneRec1_AWD： 视频推荐ctr模型演进"
date: 2022-04-06 09:54:38
categories:
  - 算法平台
  - 排序与预估模型
---

{% raw %}

<div><p>作者：刘誉臻 肖玄基</p>
</div><div><p>OneRec系列算法目前已经发布的算法：</p>
</div><div><p>0）OneRec总纲：整体算法的设计思路，[内部或本地链接已移除]</p>
</div><div><p>1） OneRec1_AWN 行为数据的增强使用。在 dlrm模型增加attenton结构进行调优。</p>
</div><div><p>相关文章：[内部或本地链接已移除]</p>
</div><div><p>2） OneRec2_NeighbourEnhancedDNN 行为和内容两种信号的强化建模。增强用户/item的表达和他们的交互.</p>
</div><div><p>相关文章：[内部或本地链接已移除] 相关论文：投递中</p>
</div><div><p>3） OneRec3_Social4Rec 行为/内容之外使用social interest信息。增强用户的表达，有效融合行为，内容，社交兴趣三种信号。</p>
</div><div><p>相关文章：[内部或本地链接已移除]  相关论文：投递中，</p>
</div><div><p>4） OneRec4_SparseSharing 如何更好的利用点击信号和转化信号。通过彩票理论实现神经元级别的多任务学习，进一步优化cvr的效果。</p>
</div><div><p>相关文章：[内部或本地链接已移除] 相关论文：<a href="https://arxiv.org/abs/2008.09872">https://arxiv.org/abs/2008.09872</a></p>
</div><div><p>OneRec代码：[内部或本地链接已移除]</p>
</div><div><h3>1. 简介</h3>
</div><div><p>基于DNN的推荐系统ctr预估模型在学术界和业界一直以来都是研究热点，其中不乏对于特征工程、模型结构、场景特性挖掘等方向的优秀工作。推荐场景中往往含有大量id类稀疏特征，因此对特征的低维dense embedding representation学习和高效充分的特征交叉能起到显著的提升作用。经典的工作包括Wide&amp;Deep、DeepFM、DCN、FNN等。本文中我们结合了视频短视频底层页推荐feed流场景的特殊性，对模型做了进一步探索和优化，取得了持续的效果提升。</p>
</div><div><h3>2. 模型演进</h3>
</div><div><h4>2.1 基线模型DLRM</h4>
</div><div><p> <strong>底层页场景是对当前播放短视频根据用户行为历史推荐个性化的相关视频feed流，因此这里包含四大特征域&lt;SrcItem, User, TargetItem&gt;</strong>。我们在2020年上半年采用DLRM网络替换了线上的双塔DSSM模型，并取得一定收益。DLRM网络结构，对所有输入特征embedding进行了两两内积交叉（all cross部分），并与原始embedding一起concate后进入MLP结构。该结构充分体现出了CTR模型领域的“暴力美学”思想，<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/89f29521abff21556c71.png"/></p>
</div><div><h4>2.2 Attention建模长序列特征</h4>
</div><div><p>首先，我们针对DLRM中对多值特征只做简单的avg pooling，无法对序列特征分重要性做不同处理可能会损失信息，我们借鉴阿里DIN模型中提到用户历史记录与target item交叉过程中使用attention weighting思想，在模型网络中对用户行为历史进行了attention处理。其中ucate（用户播放过的视频所属category）、utag（用户播放过的视频所包含的tag）等特征，与当前待打分target item的cate、tag特征分别做attention交叉，随后得到的ucate、utag多值特征中各个值的attentive weighting做加权pooling。</p>
</div><div><p>其次，我们利用attentive weighted后的ucate、utag等特征再对target item的cate、tags特征做交叉，不同于all cross中的特征交叉，我们称之为attentive cross，并将其与all cross一起拼接在了所有输入特征之后。</p>
</div><div><p>第三，在相关推荐中src item的stags与target item的tags有着很强的相关性，与utags类似地我们尝试与利用attention结构来提取stags的加权pooling。实验发现模型离线效果有所下降，分析原因为stag序列长度较短（utags最大长度20，stags最大长度仅为6），因此stags每个tag都应有所贡献，attention后反而该特征效果被削弱了。初步结论为attention操作比较适合较长的多值特征提取关键信息。<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e2794272c4a055eabdc4.png"/></p>
</div><div><h4>2.3 wide提升“强特征”表达</h4>
</div><div><p>借鉴wide&amp;deep网络结构，我们将系统中的“强特征”提升到wide侧，用于直接对输出结果产生影响。这里强特征除了显示的特征交叉all cross和attentive cross外，还加入了一些后验统计特征ctr、cvr、src-target tag similarity、user-target tag similarity等。其中tag similarity作为人工特征工程部分，可通过svid和vid的tag列表计算Jaccard积并做离散化得到：<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f998e4ec37191e2f3ba3.png"/><br/>
另外还加入了自拟合子网络NN-Similarity，输入为需要显示建立关联的src特征与target特征，通过OurProduct+Minus的操作进行充分特征交叉:<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/67def80b7a7bf801757e.png"/></p>
</div><div><p>同时我们对这类强特征放在wide侧还是deep侧、放哪些特征在wide侧都进行了离线对比实验，最终选择了最佳经验结构。<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/722d447ff794af4662a1.png"/></p>
</div><div><h4>2.4 transfer learning</h4>
</div><div><p>通过加入attention、wide塔，我们得到了DLRM模型的改进版AWD（Attention Weighted DLRM），并在离线训练评估中，同样利用一个月的日志样本数据从头开始进行训练，用最新一小时的样本数据进行模型评估，观察AUC及FAUC（Flush AUC，这里我们采用的刷AUC是对每一刷求算AUC后根据本刷曝光数求加权平均，类似于DIN的GAUC）都取得了显著提升。<br/>
由于线上base已经在线几个月时间，经过了非常充分的训练，我们发现用新训练的AWD与线上base模型对比，离线效果仍有FAUC约1个百分点的差距。为了能够快速追平并超越线上base，我们分析了base DLRM与AWD模型结构与特征配置的差异，尝试采用base模型中与AWD共同特征的embedding作AWD特征embedding的初始化，进行热启动训练。训练启动时，AWD中只有部分共同特征能够利用初始化，其余特征embedding和网络结构仍采用随机初始化并进行梯度下降拟合。虽然观察到初始阶段模型的valid AUC、FAUC等有较大的波动，但其收敛速度及后续稳定状态后的值都有显著提升。</p>
</div><div><h3>3. 实验结果</h3>
</div><div><h4>3.1 离线效果</h4>
</div><div><p>如下图可见freshbase采用与online base完全相同的配置，冷启动进行训练，AWD采用迁移学习热启动训练，最终取得了高于online base的FAUC（图中GAUC）指标，稳定后<strong>FAUC平均提升0.7~0.9个百分点，AUC平均提升0.5个百分点</strong>。<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2ce235a7d391802379c5.png"/></p>
</div><div><h4>3.2 线上效果</h4>
</div><div><p>在经过严格的AA对比实验验证样本均衡后，取得显著效果提升：场景内用户<strong>曝光人均时长显著提升1.70%，曝光人均vv显著提升1.14%，CTR显著提升1.57%，完成度显著提升1.09%</strong>；</p>
</div><div><h3>4. 创新点</h3>
</div><div><ul>
<li>我们将attention与DLRM结构进行结合，更充分地利用用户行为历史，更好的起到了特征交叉的作用，同时将attention后的序列特征与其他特征交叉产出attentive cross部分；</li>
<li>加入“强特征”，并将这类“强特征”放入wide侧浅层网络，能够更加直接地影响模型预测输出，增强模型对强特征的“记忆性”，并最终提出AWD（Attention Weighted DLRM）模型；</li>
<li>利用迁移学习，使用线上模型特规模稀疏特征embedding对我们提出的新模型进行热启动训练，离线指标效果非常显著；</li>
</ul>
</div><div><h3>5. 结论&amp;展望</h3>
</div><div><p>DLRM已经对模型有全面的交叉，但对于较长的序列特征信息捕捉能力不足；DIN提出了行为序列attention的子结构能够显著提升用户兴趣提取效率，我们进一步地在attention计算后得到attentive cross，将其与其他”强特征“进行有效结合，最终提出了AWD模型。另外，我们通过迁移学习大大缩小了新模型追赶线上模型指标的时间代价，并验证了模型结构差异较大的情况下只利用部分特征进行embedding热启动的有效性。</p>
</div><div><p>我们认为这是一个很有前景的方向，所以非常欢迎任何业务团队的同学和我们进一步共建OneRec系列算法。我们的相关算法代码会开放公司内网平台上，欢迎大家使用/讨论。</p>
</div><div><p>git地址：[内部或本地链接已移除]</p>
</div><div><h3>6. 致谢</h3>
</div><div><p>此处感谢我们的领导王峰，刘培，范朝盛对于我们工作的指导，和对我们技术创新的巨大支持。<br/>
感谢工程邹鑫团队所有同学一如既往的支持，感谢孙星海、甘如饴，詹志征提供的tfdnn基础训练框架。<br/>
同时感谢我们中心所有参与讨论并给予无私支持的同学，此处不一一赘述。</p>
</div> 
{% endraw %}
