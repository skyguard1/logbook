---
title: "QQ浏览器：小说召回中的DSSM模型优化实践（一）"
date: 2022-04-18 15:20:59
categories:
  - deep-learning
---

<h2><span>一、背景</span></h2>

<p><strong>2、在线召回：</strong>召回服务接收到用户请求，会先解析用户携带的上下文特征，然后通过请求看点推荐中台<span>API</span>进行预测获得用户向量，再调用召回接口，从<span>Faiss</span>中获取相似度<span>TopN</span>的<span>item ID</span>以及分数。召回服务会对结果进行过滤，例如曝光退避等人工策略，最后返回给上层排序。</p>
<h2>三、特征工程</h2>
<h3><span>1</span>、特征分析</h3>
<p>用户的输入包含：</p>
<ol><li>用户性别、年龄段、省份、城市、受教育程度等离散型特征</li>
<li>用户历史阅读文章的分类序列等序列型特征</li>
<li>用户历史对某个分类、<span>tag</span>的曝光、点击、阅读累计次数和平均转化率特征</li>
</ol><p>物品的输入包含：</p>
<ol><li><span> </span>小说一级分类、二级分类、<span>Tag</span>等离散型特征</li>
<li><span> </span>文章文本长度、平均阅读时长、点击数、曝光数、点击率等连续型特征</li>
<li><span> </span>书籍过去<span>30</span>天统计特征：<span>UTR</span>、有效阅读转化率等</li>
</ol><p>前期分析了特征覆盖度、准确率和重要性，作为特征筛选的参考（以下展示部分特征）：</p>
<p><span style="">&nbsp;</span></p>
<p>对于离散特征的一般操作<span>(</span>异常处理、归一化、<span>encode)</span>不再赘叙，这里仅分享几个思路：</p>
<p><span>1) </span>初初期加入了很多经验特征，<span>base</span>版本表现一般，于是通过单特征剔除观察<span>AUC</span>变化来量化特征重要性，去除掉一些负向或者提升不大的特征后，<span>AUC</span>和<span>loss</span>没有明显变化。根据奥卡姆剃刀原则最终只保留了如上图所示的特征。</p>
<p><span>2) </span>对于统计类特征（例如：过去<span>N</span>天的<span>UTR</span>、过去<span>N</span>天的阅读时长等），在<span>1</span>中被剔除掉，但这部分信息需要利用好。小说阵地分为几个场景：书架、榜单、推荐。不同场景的转化率不可直接融合计算，实验发现分离出用户和书籍在推荐场景的转化率，并进行等频分桶，效果有明显正向提升（AUC+0.02）。特别地，其中时长类特征由于分布偏度很大需要先取<span>log</span>后分桶；转化率特征考虑到度量问题，需要<span>wilson</span>平滑处理，公式如下：</p>
<p style=""></p>
<p><span>p</span>：概率，即点击的概率，也就是<span> CTR</span>（以<span>CTR</span>为例）</p>
<p><span>n: </span>样本总数，即曝光数；</p>
<p><span>z</span>：在正态分布里，μ+z*σ会有一定的置信度。例如，z=1.96就有<span> 95% </span>的置信度。</p>
<h3><span>2</span>、<span>UserModel</span>特征</h3>
<p><span>UM</span>特征是用于表示用户兴趣点的，含义是用户在每个书籍分类和<span>tag</span>上的兴趣权重，值越大说明越感兴趣。</p>
<p><span>UM</span>的生成逻辑大致如下：</p>
<p style=""></p>
<p>样本为线上推荐曝光样本，其中点击<span>\</span>阅读样本<span> label=1</span>，曝光未点击<span>\</span>阅读<span> label=0</span>，用户在对应的类型<span>A</span>上的历史行为数据：曝光、点击、阅读、加书、阅读时长、<span>CTR</span>、<span>CVR</span>等，预测用户在该分类上的点击概率和阅读概率。预测结果经线性加权得到最终兴趣分。一条样本只有一个类别的行为。<span>UM</span>分数会一直累计，乘上时间衰减系数，可以刻画用户的长期兴趣。经过CE，用户top3的UM兴趣准确度有80%+，但仍有几点局限：1、用户短期内如果追一本和历史兴趣无关的书，这个信息将无法及时更新到模型中；2、新用户和浅度用户不友好，兴趣点很容易学偏。</p>
<h3><span>3</span>、特征交叉</h3>
<p>在原始双塔模型中，模型并不能显式的构造高阶交叉特征，如果需要引入交叉特征，除了人工设计简单的交叉特征外，我们还在双塔模型中进行了网络结构的改造，目前在<span>FM[2]</span>上做了一些尝试。</p>
<p><strong><span>FM</span>（<span>Factorization Machines</span>）</strong></p>
<p style=""></p>
<p>展示了<span>FM-DSSM</span>的整体框架，其中红线标注的就是<span>FM</span>特征交叉的流程。<span>FM</span>网络由两个部分组成：其中<span>LR</span>模型为<span>FM</span>的一阶特征，<span>Dense</span>化的两两特征为<span>FM</span>的二阶特征。二阶特征即是显式的交叉特征。</p>
<p style=""></p>
<p>我们让<span>FM</span>网络和<span>Deep</span>网络共享了特征的<span>Embedding</span>层，最后将<span>FM</span>输出的高阶表征和<span>Deep</span>的输出拼接到一起，最终计算<span>user</span>和<span>item</span>的相似度。在离线测试集评测中，<span>FM</span>对<span>AUC</span>有<span>0.04</span>的提升：</p>
<table style="width:385px;height:10px;"><tbody><tr style="height:42px;"><td style="width:223px;height:42px;">
<p><strong>模型</strong></p>
</td>
<td style="width:107px;height:42px;">
<p><strong>AUC</strong></p>
</td>
</tr><tr style="height:42px;"><td style="width:223px;height:42px;">
<p>Baseline</p>
</td>
<td style="width:107px;height:42px;">
<p>0.626846</p>
</td>
</tr><tr style="height:42px;"><td style="width:223px;height:42px;">
<p>DSSM + FM (仅用二阶特征<span>)</span></p>
</td>
<td style="width:107px;height:42px;">
<p>0.638758</p>
</td>
</tr><tr style="height:21px;"><td style="width:223px;height:21px;">
<p>DSSM + FM (一阶、二阶特征均用上<span>)</span></p>
</td>
<td style="width:107px;height:21px;">
<p>0.660813</p>
</td>
</tr></tbody></table><p>在<span>TopK</span>的准召率，和用户真实点击<span>/</span>阅读序列在召回列表中的平均位置测评中，<span>FM+DSSM</span>模型没有明显的提升效果，这里原因仍在追查中：</p>
<p style=""></p>
<p></p>
<h2>四、小结</h2>
<p>在特征优化上，我们还有很多可以尝试的方向，一是引入更多特征，采用<span>CNN-DSSM</span>以及<span>LSTM-DSSM</span>模型，提取小说封面以及简介中的信息，通过<span>transformer</span>提取用户历史行为序列中的信息；二是显式的高阶特征交叉网络优化，待特征丰富后，可以尝试工业界常用的<span>xDeepFM</span>、<span>DCN</span>和<span>AutoInt</span>学习特征之间的信息，使模型学习更加充分。</p>
<p>本文作为“<span>QB</span>小说召回中的<span>DSSM</span>模型优化实践”系列的第一篇，抛砖引玉。后续还有模型结构、<span>loss</span>设计和采样优化的介绍，欢迎大家一起交流讨论！</p>
<p>本文由helenykwang和claraluo共同完成，感谢项目组同学jessiexyliu、petergong的支持，jasonyin、leevenluo的指导</p>
<p></p>
<p><strong>参考文献</strong></p>
<p>[1] <em>Huang, Po-Sen, et al. "Learning deep structured semantic models for web search using clickthrough data." Proceedings of the 22nd ACM international conference on Information &amp; Knowledge Management. 2013.</em></p>
<p>[2] <em>S. Rendle, "Factorization Machines," 2010 IEEE International Conference on Data Mining, Sydney, NSW, 2010, pp. 995-1000, doi: 10.1109/ICDM.2010.127.</em></p>				</div>
