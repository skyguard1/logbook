---
title: "基于Memory Network的推荐冷启动方案"
date: 2022-03-31 10:19:18
categories:
  - 算法
  - 推荐与排序
---

{% raw %}

<div>
<ol><li>
<h1>冷启动</h1>
</li>
</ol><p>冷启动是推荐系统中常见的难题，新用户、新物品冷启动的效果不好，可能会影响产品的增长、内容生态的发展，影响业务的长期收益。</p>
<p><br/></p>
<p>常见的冷启方案包括：</p>
<h2>1.1 结合业务场景针对性处理</h2>
<p>很多业务场景有自己独特的冷启动方法。</p>
<p>（1）模型：比如有针对新用户、新物品的独立的运营策略；对新用户设计单独的模型等。</p>
<p>（2）样本：对新用户的样本加权或者上采样等。</p>
<p>（3）特征：加上区分新用户与老用户的特征，或者用户群体特征等 。</p>
<p>这些方法很多时候只在特定的业务场景内有效。</p>
<h2>1.2 跨域迁移学习</h2>
<p>使用外部场景数据，使用迁移学习的方法，帮助提升当前场景业务效果。</p>
<p>（1）联合学习：源域数据与目标域数据联合训练，将源域信息迁移到目标域，在一定程度上为目标域增加了数据。这种方法对源域的样本、特征要求比较高，很多场景不一定有合适的源域可供迁移。</p>
<p>（2）预训练：利用多个业务数据训练预训练模型，在下游业务finetune。我们组对预训练模型进行了大量探索，目前在BG内多个业务精排、召回等场景取得了显著收益。预训练方案目前面临着BG内ID体系不统一（用户ID hash方式不同，物品ID存在qimei16、qimei36等多种不同形式）等问题，还在持续探索中。</p>
<h2>1.3 Side information</h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/541ce4b2346bce308e16.png"/></p>
<div>
<div>
<p>图1 典型推荐排序模型</p>
<p>典型的推荐排序模型（图1）包括3类特征：用户特征、物品特征以及其它特征。用户（物品）特征包括用户（物品）的ID特征以及其它属性特征。在推荐模型中，用户（物品）的ID特征往往非常重要；观察多个业务模型的特征重要度[1]也印证了这个观点，有些业务的用户ID、物品ID甚至是最重要的两个特征。在冷启动场景，新用户、新物品的数据量非常少，重要的ID特征得不到充分训练，从而影响模型的整体效果。</p>
<p>用户与物品常常包括丰富的属性特征，比如用户侧的性别、年龄、地域等，物品侧的标题、类目、标签等特征。这些属性特征的数量一般远小于用户（物品）ID的数量，在模型里已经得到了充分的训练。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/8e09058a57a5d014a52c.png"/></p>
<p>图2 EGES, KDD18, 阿里</p>
<p>因此，我们可以基于用户（物品）的属性特征来加强用户（物品）ID特征的训练。比如，阿里提出的EGES模型[2]（图2），在图模型里，对表示物品的图节点加入物品的属性特征。以及MetaEmbedding[3]（图3）模型，通过元学习方法训练得到物品ID embedding的初始化生成器；输入物品的属性特征，经过生成器得到初始化的物品ID embedding，然后使用少量样本finetune得到更好的物品ID embedding。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/bdf11f743795ff2fdf1f.png"/></p>
<p>图3 MetaEmbedding, SIGIR19</p>
<p><br/></p>
</div>
</div>
<div>
<div>
<ol><li>
<h1>基于Memory Network的冷启动方案</h1>
</li>
</ol><p>推荐系统中用到了很多假设，比如协同过滤中假设相似的用户对同一个物品的兴趣相似，相似的物品对同一个用户的吸引力相似。本方案中，我们假设，属性特征相似的用户（物品），用户（物品）ID embedding也存在一定的相似性。比如地域相同、年龄相同的相同性别用户，可能有一些相似的兴趣爱好，这种隐式的共性包含在用户的ID embedding中。</p>
<h2>2.1 离线聚类</h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/567c307e47745d98187e.png"/></p>
<div>
<div>
<p>图4 离线聚类冷启方案</p>
<p>基于上面的假设，我们可以根据冷启用户的属性特征embedding来查找相似用户，以相似用户的ID embedding帮助冷启。因为属性特征组合（|性别|*|省份|*|年龄|*|受教育程度|···）数量与用户ID数量特别多，可以选择对属性特征embedding与ID embedding聚类。图4是离线聚类的冷启方案。</p>
<p>（1）离线聚类：基于业务已经训练好的模型，对属性embedding（多个属性concat）聚类；收集属性聚类中心对应的多个ID embedding，计算均值作为对应的ID embedding聚类中心。</p>
<p>（2）在线serving（作用于冷启用户）: 基于用户的属性embedding计算所在属性类簇，以对应的ID类簇的聚类中心替换模型中的ID embedding。</p>
<p><br/></p>
<p>这个方案非常直接，在QQ看点视频推荐场景离线验证有收益。但是需要业务增加一个离线聚类的流程，涉及到训练与推理流程的工程改造，有较高的接入成本。</p>
</div>
</div>
<div>
<div>
<h2>2.2 在线聚类（Memory Network）</h2>
<p>为了降低业务接入难度，可以考虑将聚类过程嵌入到模型训练里，使用“在线聚类”的方式。</p>
<p>在线聚类需要考虑如何在模型中存放、更新与使用聚类中心。经过调研，我选择使用Memory Network。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/fb41f362bc5de0f2cee9.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/e8acc0a2f6478a7d6824.png"/></p>
<p>                图5 Memory Network                                                               图6 Neural Turing Machine</p>
<p><br/></p>
</div>
</div>
<div>
<div>
<p>Memory Network[4]（图5，ICLR15，）与Neural Turing Machine[5]（图6，NeurIPS14）差不多同期提出，通过给深度学习模型增加一个较大的“外部存储”，来解决包括LSTM在内的深度学习模型“长期记忆”能力不足的问题。主体构成类似，包括主要存储单元memory，以及围绕着memory的读、写设计的功能模块。在NLP中应用较多，比如存储外部知识库，用于QA任务[6]。在推荐系统中主要被用于存储长期用户行为序列，比如阿里提出的MIMN模型[7]。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/db8d3b8cec7be061f90c.png"/></p>
<p>图7 基于规则更新的memory network冷启方案</p>
</div>
</div>
<div>
<div>
<p>如图7所示，模型中增加了两个memory，分别存储属性特征embedding聚类中心与对应的ID embedding聚类中心。为了模拟离线聚类，尽可能减少对原始模型的影响，我采用基于规则更新memory的方式，即memory的更新不回传梯度。因此，对memory先使用，再更新。</p>
<p>（1）使用memory：</p>
<p>a) 计算属性embedding与属性memory的相似度<img alt="" loading="lazy" src="/logbook/images/algorithm/afdf5bfe6b8ba52f914f.png"/></p>
<p>b) 根据相似度提取ID memory的数据，得到基于memory的ID embedding</p>
<p>c) 与原始模型中的ID emb加权融合</p>
<p>（2） 更新memory：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/6cd944a5d1861b067679.png"/></p>
<p><br/></p>
<div>
<div>
<p>该方案在视频片多多场景精排在线实验，新用户有效vv显著提升1.5%，留存涨0.09%，全部用户有效人均vv涨0.19%，留存涨0.2%。对新用户有一定的提升，整体效果不是特别明显。</p>
<p><br/></p>
<div>
<div>
<h2>2.3 可学习Memory</h2>
<p>基于规则更新memory的方案中，memory信息的增加来自于当前batch的embedding；而训练过程中可能存在一些训练不充分的embedding，这些embedding写入memory会影响memory的质量从而影响整体效果。我们做了离线实验发现，只将老用户的embedding写入memory，离线效果会有提升，进一步证明了这个猜想。但是具体哪些embedding可以写入memory是很难人工判断的，所以采用让memory的更新可学习。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f3cca160674c1f25e29e.png"/></p>
<p>图8 可学习memory network</p>
</div>
</div>
<p><br/></p>
</div>
</div>
<div>
<div>
<p>如图8所示，与Neural Turing Machine类似，模型里加入了两个控制器：写控制器与读控制器。模型中很多模块都是以属性embedding作为输入，经过控制器进行向量空间的转换。因为这里memory是可学习的，所以对memory先更新，再使用。</p>
<p>（1）更新memory</p>
<p>a)  计算属性embedding与属性memory的写相似度：<img alt="" loading="lazy" src="/logbook/images/algorithm/eb4042373453c38384dd.png"/></p>
<p>b)  使用可学习的向量erase、add来更新memory；erase用来表征memory的遗忘程度，add用来表示向memory添加的内容。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/70f18a4fe5f2961ddc0f.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/fe39aec97e0522282609.png"/></p>
<p><br/></p>
<p>（2）使用memory</p>
<p>与更新类似，计算属性embedding与属性memory的读相似度，然后提取ID memory，得到ID memory_emb。</p>
<p>得到的memory_ID_emb如何使用，我探索了多种方式，这里介绍两个比较有用的方式：</p>
<p>a) 相加融合：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/9c1491ae602ce926f478.png"/></p>
<p>阿里在Res-embedding[8]（图9）中提出，将物品ID embedding表示成物品所在类簇与物品个性化embedding之和，具有更好的泛化能力。</p>
<p>相加融合不改变业务的模型结构，适用于直接继承线上模型增量训练。在增量训练的情况下，相加融合是一个比较好的选择。</p>
</div>
</div>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/68d0dfc598b321e77d11.png"/></p>
<p>图9 Res-Embedding, DLP-KDD, 阿里</p>
<p>b) 当做新特征使用：将memory_ID_emb concat到模型里去，适合于结构方便修改的场景。</p>
<div>
<div>
<p>使用拼接的方式，在全民K歌直播精排场景在线小流量实验，uvctr+1.13%; 直播时长渗透率+0.57%, 人均时长+1.07%;人均直播关注pv+4.79%; 人均直播送礼pv+5.59%; 直播观看次数渗透率+0.66%; 直播TAB点击渗透率+1.08%; 直播送花amount渗透率+1.76%; 直播送花pv渗透率+1.80%。一些渗透率指标的提升，表示对新用户起到了很好的效果。</p>
</div>
</div>
<p><br/></p>
<div>
<div>
<h2>2.4 使用</h2>
<p>模型的demo代码参见无量ModelZoo：MemoryNetwork</p>
<div>
<div>
<p>业务使用起来非常方便，定义memory layer，传入属性embedding，就可以得到memory ID embedding，根据实际场景选择相加融合、拼接或者探索其它的使用方式。方案可以同时用于用户与物品的冷启。</p>
<div>
<pre>memory_layer = Memory(n_memory=N_MEMORY,
                      attr_memory_dim=USER_ATTR_MEMORY_DIM,
                      id_emb_dim=EMBEDDING_DIM,
                      temperature=TEMPERATURE,
                      alpha=ALPHA,
                      layer_prefix="movielens")

memory_user_id_emb = memory_layer(user_attr_embs)</pre>
</div>
<div>
<div>
<p>已有一些业务接入使用，并且取得了离线收益。</p>
<p>该方法还需要在更多场景验证并完善。还有很多优化空间，比如memory有没有更好的构建与更新方式，一些更好的基于属性embedding加强ID embedding的模型比如图能不能同样便捷地嵌入进来。</p>
</div>
</div>
</div>
</div>
<div>
<div>
<ol><li>
<h1>总结</h1>
</li>
</ol><p>本文提出了基于memory network的冷启动方案，基于训练充分的属性embedding，来加强训练不够充分的ID embedding。方案可以同时用于用户、物品的冷启动，直接嵌入模型不改变已有的模型结构，具有良好的通用性。方案还在持续演进中，希望可以便捷、有效地在一定程度上帮助用户、物品的冷启动。</p>
<p><br/></p>
<p>感谢ppan、gracelyang、robertyuan、hemingwei等大佬的指导，感谢lianzhitan、waferzhang、mermaidliu、weilonghu、symonwang的讨论与帮助，感谢aidenpan、nikkowang、fivenwu、graywang、xlingzhang、weitaotang、yuezhouli、haichaoyang、colinliang、fabriszhou等业务同学的支持与帮助。</p>
<p><br/></p>
<div>
<div>
<ol><li>
<h1>参考文献</h1>
</li>
</ol><ol><li>
<p>（KM文章）特征重要度算法介绍</p>
</li>
<li>
<p>Wang J, Huang P, Zhao H, et al. Billion-scale commodity embedding for e-commerce recommendation in alibaba[C]//Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery &amp; Data Mining. 2018: 839-848.</p>
</li>
<li>
<p>Pan F, Li S, Ao X, et al. Warm up cold-start advertisements: Improving ctr predictions via learning to learn id embeddings[C]//Proceedings of the 42nd International ACM SIGIR Conference on Research and Development in Information Retrieval. 2019: 695-704.</p>
</li>
<li>
<p>Weston, Jason, Sumit Chopra, and Antoine Bordes. "Memory networks." arXiv preprint arXiv:1410.3916 (2014).</p>
</li>
<li>
<p>Graves, Alex, Greg Wayne, and Ivo Danihelka. "Neural turing machines." arXiv preprint arXiv:1410.5401 (2014).</p>
</li>
<li>
<p>Miller, Alexander, et al. "Key-value memory networks for directly reading documents." arXiv preprint arXiv:1606.03126 (2016).</p>
</li>
<li>
<p>Pi Q, Bian W, Zhou G, et al. Practice on long sequential user behavior modeling for click-through rate prediction[C]//Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery &amp; Data Mining. 2019: 2671-2679.</p>
</li>
<li>
<p>Zhou, Guorui, et al. "Res-embedding for deep learning based click-through rate prediction modeling." Proceedings of the 1st International Workshop on Deep Learning Practice for High-Dimensional Sparse Data. 2019.</p>
</li>
</ol></div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div> 
{% endraw %}
