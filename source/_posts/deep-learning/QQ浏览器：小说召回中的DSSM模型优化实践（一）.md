---
title: "QQ浏览器：小说召回中的DSSM模型优化实践（一）"
date: 2022-04-18 15:20:59
categories:
  - deep-learning
---

{% raw %}

<h2>一、背景</h2>
<p>QQ浏览器小说推荐系统旨在为用户推荐可能感兴趣的小说。其主体框架与目前主流的推荐系统架构一致，主要由召回层、粗排层、精排层构成。在召回层，不同的召回路会通过不同的算法，包括兴趣、热点、协同等，召回用户感兴趣的item，然后不同召回路的item经过汇总，在粗排层进行排序截断，再经过精排层的在线打分，展控层加入人工策略等过滤出最终结果展示给用户。其中，召回层作为推荐系统的底层，需要充分考虑用户的不同特征与兴趣，召回尽可能多样的item，以供后续的粗排和精排挑选。不同路的召回应该相互配合，分别取挖掘用户不同层面可能感兴趣的item，使得最终的召回结果全面而准确。<img alt="" loading="lazy" src="/logbook/images/deep-learning/c97647fc76c237e001ca.png"/></p>
<p>DSSM作为召回层的其中一路召回，其主要目的在于挖掘用户和物品在语义空间的相关性。其核心思想是将用户与物品通过深度神经网络映射到同一个语义空间，使得特征相似的用户（物品）与用户（物品）在空间中距离相近，用户与其可能感兴趣的物品也尽可能相邻。其基于历史用户与物品的交互数据训练得出得用户向量和物品向量，还能进一步作为精排或者粗排层的特征，帮助排序层提升效果。<br/>本文将介绍我们在小说DSSM召回项目中的工程实践和特征工程两部分工作。</p>
<h2>二、系统架构</h2>
<p>整个推荐系统架构如图所示，其中重点标注了我们DSSM召回流程，主要分为离线模型训练和在线召回两个过程。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/08ab059cac7e0a11099c.png"/></p>
<p><strong>1、离线模型训练</strong>：用户行为（曝光、点击、阅读等）触发样本的收集，从特征服务获取当前user，item对应实时、离线特征，拼合上上下文信息等存储到hdfs上。离线训练到模型部署，整套流程在venus平台上完成，训练框架为无量。具体操作流程请参考无量开发文档 。</p>
<p>模型部署上线后，需要在看点推荐中台（[内部或本地链接已移除]）上注册模型和配置item向量出库，详细步骤请参考看点品类推荐平台演示，配置完成后模型将定时更新item向量到Faiss中。注意，item个数和Faiss查找范围的配置将影响召回速度。</p>
<p><strong>2、在线召回：</strong>召回服务接收到用户请求，会先解析用户携带的上下文特征，然后通过请求看点推荐中台API进行预测获得用户向量，再调用召回接口，从Faiss中获取相似度TopN的item ID以及分数。召回服务会对结果进行过滤，例如曝光退避等人工策略，最后返回给上层排序。</p>
<h2>三、特征工程</h2>
<h3>1、特征分析</h3>
<p>用户的输入包含：</p>
<ol><li>用户性别、年龄段、省份、城市、受教育程度等离散型特征</li>
<li>用户历史阅读文章的分类序列等序列型特征</li>
<li>用户历史对某个分类、tag的曝光、点击、阅读累计次数和平均转化率特征</li>
</ol><p>物品的输入包含：</p>
<ol><li> 小说一级分类、二级分类、Tag等离散型特征</li>
<li> 文章文本长度、平均阅读时长、点击数、曝光数、点击率等连续型特征</li>
<li> 书籍过去30天统计特征：UTR、有效阅读转化率等</li>
</ol><p>前期分析了特征覆盖度、准确率和重要性，作为特征筛选的参考（以下展示部分特征）：</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/b4d0087cafd2b05de193.png"/></p>
<p>对于离散特征的一般操作(异常处理、归一化、encode)不再赘叙，这里仅分享几个思路：</p>
<p>1) 初初期加入了很多经验特征，base版本表现一般，于是通过单特征剔除观察AUC变化来量化特征重要性，去除掉一些负向或者提升不大的特征后，AUC和loss没有明显变化。根据奥卡姆剃刀原则最终只保留了如上图所示的特征。</p>
<p>2) 对于统计类特征（例如：过去N天的UTR、过去N天的阅读时长等），在1中被剔除掉，但这部分信息需要利用好。小说阵地分为几个场景：书架、榜单、推荐。不同场景的转化率不可直接融合计算，实验发现分离出用户和书籍在推荐场景的转化率，并进行等频分桶，效果有明显正向提升（AUC+0.02）。特别地，其中时长类特征由于分布偏度很大需要先取log后分桶；转化率特征考虑到度量问题，需要wilson平滑处理，公式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9e0f277c7c3efb53f29a.png"/></p>
<p>p：概率，即点击的概率，也就是 CTR（以CTR为例）</p>
<p>n: 样本总数，即曝光数；</p>
<p>z：在正态分布里，μ+z*σ会有一定的置信度。例如，z=1.96就有 95% 的置信度。</p>
<h3>2、UserModel特征</h3>
<p>UM特征是用于表示用户兴趣点的，含义是用户在每个书籍分类和tag上的兴趣权重，值越大说明越感兴趣。</p>
<p>UM的生成逻辑大致如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/71a1ce4ad8288e27f416.png"/></p>
<p>样本为线上推荐曝光样本，其中点击\阅读样本 label=1，曝光未点击\阅读 label=0，用户在对应的类型A上的历史行为数据：曝光、点击、阅读、加书、阅读时长、CTR、CVR等，预测用户在该分类上的点击概率和阅读概率。预测结果经线性加权得到最终兴趣分。一条样本只有一个类别的行为。UM分数会一直累计，乘上时间衰减系数，可以刻画用户的长期兴趣。经过CE，用户top3的UM兴趣准确度有80%+，但仍有几点局限：1、用户短期内如果追一本和历史兴趣无关的书，这个信息将无法及时更新到模型中；2、新用户和浅度用户不友好，兴趣点很容易学偏。</p>
<h3>3、特征交叉</h3>
<p>在原始双塔模型中，模型并不能显式的构造高阶交叉特征，如果需要引入交叉特征，除了人工设计简单的交叉特征外，我们还在双塔模型中进行了网络结构的改造，目前在FM[2]上做了一些尝试。</p>
<p><strong>FM（Factorization Machines）</strong></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/f691e561f7e18bade967.png"/></p>
<p>展示了FM-DSSM的整体框架，其中红线标注的就是FM特征交叉的流程。FM网络由两个部分组成：其中LR模型为FM的一阶特征，Dense化的两两特征为FM的二阶特征。二阶特征即是显式的交叉特征。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/2d46056738d88aadf158.png"/></p>
<p>我们让FM网络和Deep网络共享了特征的Embedding层，最后将FM输出的高阶表征和Deep的输出拼接到一起，最终计算user和item的相似度。在离线测试集评测中，FM对AUC有0.04的提升：</p>
<table><tbody><tr><td>
<p><strong>模型</strong></p>
</td>
<td>
<p><strong>AUC</strong></p>
</td>
</tr><tr><td>
<p>Baseline</p>
</td>
<td>
<p>0.626846</p>
</td>
</tr><tr><td>
<p>DSSM + FM (仅用二阶特征)</p>
</td>
<td>
<p>0.638758</p>
</td>
</tr><tr><td>
<p>DSSM + FM (一阶、二阶特征均用上)</p>
</td>
<td>
<p>0.660813</p>
</td>
</tr></tbody></table><p>在TopK的准召率，和用户真实点击/阅读序列在召回列表中的平均位置测评中，FM+DSSM模型没有明显的提升效果，这里原因仍在追查中：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/0cf060397f8dc64e07f7.png"/></p>
<p></p>
<h2>四、小结</h2>
<p>在特征优化上，我们还有很多可以尝试的方向，一是引入更多特征，采用CNN-DSSM以及LSTM-DSSM模型，提取小说封面以及简介中的信息，通过transformer提取用户历史行为序列中的信息；二是显式的高阶特征交叉网络优化，待特征丰富后，可以尝试工业界常用的xDeepFM、DCN和AutoInt学习特征之间的信息，使模型学习更加充分。</p>
<p>本文作为“QB小说召回中的DSSM模型优化实践”系列的第一篇，抛砖引玉。后续还有模型结构、loss设计和采样优化的介绍，欢迎大家一起交流讨论！</p>
<p>本文由helenykwang和claraluo共同完成，感谢项目组同学jessiexyliu、petergong的支持，jasonyin、leevenluo的指导</p>
<p></p>
<p><strong>参考文献</strong></p>
<p>[1] <em>Huang, Po-Sen, et al. "Learning deep structured semantic models for web search using clickthrough data." Proceedings of the 22nd ACM international conference on Information &amp; Knowledge Management. 2013.</em></p>
<p>[2] <em>S. Rendle, "Factorization Machines," 2010 IEEE International Conference on Data Mining, Sydney, NSW, 2010, pp. 995-1000, doi: 10.1109/ICDM.2010.127.</em></p> 
{% endraw %}
