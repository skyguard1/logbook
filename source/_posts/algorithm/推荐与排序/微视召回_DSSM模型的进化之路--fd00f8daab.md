---
title: "微视召回_DSSM模型的进化之路"
date: 2022-04-01 14:43:09
categories:
  - 算法
  - 推荐与排序
---

{% raw %}

<h3><strong>一、短视频业务特点分析与</strong><strong>dssm简介</strong></h3>
<p><strong>       </strong>像微视、抖音类的feeds流形式的短视频推荐业务，有别于普通的CTR点击正反馈式场景，其最大特点在于目标的多样性。比如在短视频业务中视频的播放时长、播放完整度、点赞、转发、分享、评论等多种行为都可以作为推荐模型的训练目标。召回作为推荐系统的底层，需要充分考虑这种多样性的特点。另外，召回作为个性化推荐的第一步，要保证召回结果的准确性、多样性，从而帮助后续精排、混排做多种推荐策略。其中，准确性指基于用户行为和画像，召回的内容是用户感兴趣的。多样性是指召回列表的内容，在类别和tag上，应该适当分散，不应该过于集中，避免为用户只推荐同一类内容。</p>
<p><strong>       </strong>DSSM，即基于深度网络的语义模型，其核心思想是将query和doc通过深度神经网络映射到同维度的语义空间中，通过计算模型输出的query和doc语义向量之积（即余弦相似度）来达到深度检索匹配的目的。作为经典的匹配模型，DSSM在召回上有着天然的优势，可以DSSM建立user-user、user-item等匹配模式，基于大量的业务数据加以训练，利用模型产出user embedding、item embedding进行召回推荐。</p>
<h3>二、DSSM召回模型之初生</h3>
<p><strong>       </strong>本文主要采用了user-item模式的DSSM模型，特点是user session VS item，即用户观看的m条序列(即session，本文模型中m设置为20)去匹配未来用户可能感兴趣的某个视频，这样做的好处是可以根据用户的观看行为序列及时捕捉用户的兴趣变化。需要考虑的是如何构造user session，即以何种目标去定义用户的session，本文采用“大杂烩”式选取：用户产生完播、互动行为的视频都放入session，这样做的目的是避免把目标做窄（若DSSM单纯以点赞为目标，会导致后面的推荐流程越做越窄）；但是，这也带来了其他问题：多目标形态下，如何突出主次，比如完播和点赞虽然都是正向信号，但是孰轻孰重呢？这里，我们在原始DSSM的user session侧加入attention，基于用户数据让深度网络去关注用户兴趣偏好的主次， attention本质上是权重的学习，对高价值目标赋予高权重，低价值目标赋予低权重（当然，这要经过大规模数据训练才能获得相对理想的效果）。</p>
<p>             <img alt="" loading="lazy" src="/logbook/images/algorithm/ef54de7b50787a180ae0.png"/></p>
<p>图1. DSSM with attention模型结构</p>
<p><strong>       </strong>基于attention的DSSM模型结构如图1所示，其中图1的q1~qm代表了用户的session，attention模块即加在此处，attention有多种形式，本文采用的是图1右侧的形式；模型的输入是采用w2v预先训练好的item embedding，模型从下到上经过三层全连接神经网络，分别得到user和item的embedding，经过l2 正则后采用dot（本质是计算cosine距离操作，即判断二者是否相似），最后经过sigmoid函数。</p>
<p>主要模型结构代码如下：</p>
<div>
<pre>with tf.name_scope("fc1"):
    if self.is_Att:
        query_fc1 = self.fully_connect(self.attQuery(query_vec), 256, 1, "fc1_q")
    else:
        query_fc1 = self.fully_connect(tf.reduce_mean(query_vec, axis=1), 256, 1, "fc1_q")
    item_fc1 = self.fully_connect(item_vec, 256, 1, "fc1_i")

with tf.name_scope("fc2"):
    query_fc2 = self.fully_connect(query_fc1, 256, 1, "fc2_q")
    item_fc2 = self.fully_connect(item_fc1, 256, 1, "fc2_i")

with tf.name_scope("fc3"):
    query_fc3 = self.fully_connect(query_fc2, 128, 1, "fc3_q")
    item_fc3 = self.fully_connect(item_fc2, 128, 1, "fc3_i")

with tf.name_scope('loss'):
    # Cosine similarity
    query_norm = tf.nn.l2_normalize(query_fc3, axis=1, epsilon=1e-8, name="l2_q") 
    item_norm = tf.nn.l2_normalize(item_fc3, axis=1, epsilon=1e-8, name="l2_i")
    dot = tf.reduce_sum(tf.multiply(query_norm, item_norm), axis=1, keepdims=True,name='cos')
    logits = tf.layers.dense(dot, units=1, kernel_constraint=tf.keras.constraints.NonNeg(), name="output")
    self.output = tf.nn.sigmoid(logits)</pre>
</div>
<p> </p>
<p><strong>       </strong>从图1我们可以看出三种召回方式，即一个模型产生三路召回，分别是：</p>
<p><strong>       </strong>（1.<strong><em>user embedding</em></strong> To <em><strong>item embedding </strong></em>：这是最容易想到的方式，难度在于我们要实时地获取用户的session序列，以此实时追踪用户兴趣。因此我们基于venus平台，采用了将模型部署到tf-serving的方式，实时地获取user embedding，最后用user embedding在all item embedding中进行检索推荐，具体流程如图2所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b00f58f02e8a16caa108.png"/></p>
<p>图2. 基于tf-serving的DSSM user-emb2item-emb召回</p>
<p></p>
<p><strong>       </strong>（2.<em><strong>item embedding</strong></em> To <strong><em>item embedding</em></strong>：即经典的item cf方式，可以通过用户观看的正向视频序列item去查找相似的其他item。</p>
<p><strong>       </strong>（3.<em><strong>user</strong><strong><em> </em>embedding</strong></em> To <strong><em>user embedding</em></strong>：即user cf方式，可以根据user embedding查找兴趣相似用户，给用户推荐相似兴趣用户的正向行为视频，如点赞视频等</p>
<h3>三、DSSM召回模型之发展</h3>
<p><strong>       </strong>图1的模型只采用了session特征，即单纯只采用feedid特征，会导致一些长尾视频也会在训练中得不到充分训练，并且高热视频也对模型产生较大的影响，使模型预测得结果偏于高热。我们希望能有辅助性特征信息比如用户的年龄性别、视频的标签分类等（即side information）去强化长尾视频特征，比如category、tag等特征，帮助长尾视频得到更好的训练，一定程度上也可以缓解高热视频带来的负面影响。新DSSM模型网络结构如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/9134241740d8136c9102.png"/></p>
<p>图2 DSSM with side information</p>
<p><strong>       </strong>图2可以看到，我们增加了age、gender、视频的tag、category、author等信息，在模型的右塔也加入了attention模块，目的是使模型注意item本身以及其对应的属性信息的主次，在利用side information的基础上进一步去缓解曝光少的新视频在训练中“竞争力”低下的问题。这里需要注意的是不同于第一版网络预先采用w2v训练好item embedding，图2模型是把整个item embedding矩阵封装到模型里面一起训练，主要原因在于：预训练好的item embedding与age、gender特征在分布空间有比较大的差异，很容易导致模型学偏。同时由于item embedding矩阵包含巨大的参数，会导致整个网络训练极慢，本文采用mask掩码将不参与训练的item embedding进行stop gradient，以此加快网络训练。</p>
<p>mask掩码式梯度停更代码如下：</p>
<div>
<div>
<pre>#mask feed embedding
squeze_feed = tf.reduce_sum(tf.reduce_sum(tf.one_hot(tf.concat(axis=-1, values=[self.query, self.item]), depth=self.feed_embedding_in),axis=1),axis=0) # (feed_num,)
feed_mask = tf.tile(tf.expand_dims(tf.where(squeze_feed &gt; 0, tf.ones_like(squeze_feed), tf.zeros_like(squeze_feed)),axis=-1),
                    [1,self.feed_embedding_out]) #(feed_num,embedding_dim)
feed_mask_h = tf.abs(feed_mask - 1) #(feed_num,embedding_dim)
self.feed_embedding_selected = tf.stop_gradient(feed_mask_h * self.feed_embedding) + feed_mask * self.feed_embedding #(feed_num,embedding_dim) </pre>
</div>
</div>
<h3>四、DSSM召回模型之进化</h3>
<p><strong>       </strong>这部分将从特征层面上去思考，如何能扩大特征层面，给模型更多更好的特征去促使模型充分学习。上面两个模型的user session方式，会导致一部分用户数据无法参与训练（如部分新用户的正向行为序列无法满足参与训练session的长度要求，因此也就无法参与训练）；如何能利用全部的用户数据进行训练，是模型进化的重中之重，而排序侧的特征数据可以覆盖绝大部分用户，采用排序层特征训练召回模型是可行之路。</p>
<p><strong>       </strong>模型如下（with <strong>hiedalong</strong>）：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/021699b6b72476445238.png"/></p>
<p>图3 DSSM+FM模型结构</p>
<p>  <strong>       </strong>图3 为基于排序特征的DSSM模型，为了模型能覆盖绝大部分用户，此模型中放弃了user侧session的做法，用user相关特征作为左塔输入，item相关特征作为右塔输入；同时，在模型结构上也进行了调整，融入了FM层，这点主要参考了deepFM做法，在匹配模型的顶端加入FM模式生成的一阶项特征和二阶项特征，将dnn产出的高级语义特征和FM模式产出的低级语义特征加以融合，最终user表达如下：<img alt="" loading="lazy" src="/logbook/images/algorithm/1cd181802cfd03d1ea6d.png"/>，item表达如下：<img alt="" loading="lazy" src="/logbook/images/algorithm/cc7145fa375dafc8130c.png"/>。效果验证部分，实验采用800万样本训练，200万样本测试，效果如下：</p>
<table><tbody><tr><td>模型</td>
<td>AUC</td>
</tr><tr><td>FM</td>
<td>0.779</td>
</tr><tr><td>FM+DSSM</td>
<td>0.824</td>
</tr><tr><td>FMM(无法用于向量召回)</td>
<td>0.793</td>
</tr><tr><td>DeepFM（无法用于向量召回）</td>
<td>0.831</td>
</tr></tbody></table><p>五、DSSM深度匹配模型的总结和未来工作</p>
<p><strong>       </strong>模型不是简单应用，结合实际业务特点才是王道，本文基于短视频业务特点、数据特点步步改进DSSM，主要做法如下：</p>
<p><strong>       </strong>（1.基于短视频业务目标多样性，将attention思路融入DSSM中的user session侧，使得模型更好理解用户偏好。</p>
<p><strong>       </strong>（2.丰富DSSM模型特征，采用双attention结构分别作用于DSSM模型的左右塔，提高新资源的竞争力，一定程度上缓解高热视频对模型训练的负面影响；同时将item embedding特征矩阵封入模型内训练，防止特征分布不一致。</p>
<p><strong>       </strong>（3.扩大训练数据，将排序特征数据用于召回模型训练，同时构造FM+DSSM融合模型，丰富user\item embedding的特征表达。</p>
<p><strong>      </strong>上文提到的三种召回方式均已在线上使用，收益总计：人均观看时长相对提升约<strong>3.5%。</strong> 同时，DSSM依然有比较多的进化方向需要尝试，比如训练数据的均衡（热门与长尾），模型负样本的负采样策略，以及模型结构上的改变等。</p>
<p></p>
<p>主要贡献者：jiantinghe、civeehe、theobaldhe、oliverlwang、hiedalong</p>
<p><strong>参考文献：</strong></p>
<p>[1] Huang P S, He X, Gao J, et al. Learning deep structured semantic models for web search using clickthrough data[C]//Proceedings of the 22nd ACM international conference on Information &amp; Knowledge Management. ACM, 2013: 2333-2338.</p>
<p>[2] Vaswani A, Shazeer N, Parmar N, et al. Attention is all you need[C]//Advances in neural information processing systems. 2017: 5998-6008.</p>
<p>[3] Covington P, Adams J, Sargin E. Deep neural networks for youtube recommendations[C]//Proceedings of the 10th ACM conference on recommender systems. ACM, 2016: 191-198.</p>
<p>[4] Zhou G, Zhu X, Song C, et al. Deep interest network for click-through rate prediction[C]//Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery &amp; Data Mining. ACM, 2018: 1059-1068.</p>
<p>[5] Tomas Mikolov, Kai Chen, Greg Corrado, and Jeffrey Dean. Efficient estimation of word representations in vector space. <i>ICLR Workshop</i>, 2013</p>
<p>[6] Rendle S. Factorization machines[C]//2010 IEEE International Conference on Data Mining. IEEE, 2010: 995-1000.</p>
<p>[7] Guo H, Tang R, Ye Y, et al. DeepFM: a factorization-machine based neural network for CTR prediction[J]. arXiv preprint arXiv:1703.04247, 2017.</p>
<p>[8] He X, Chua T S. Neural factorization machines for sparse predictive analytics[C]//Proceedings of the 40th International ACM SIGIR conference on Research and Development in Information Retrieval. ACM, 2017: 355-364.</p> 
{% endraw %}
