---
title: "多视角新闻推荐及其在CTR预测任务的实践"
date: 2022-05-13 19:58:56
categories:
  - deep-learning
---

{% raw %}

<div>
</div><div><h1>1. 背景</h1>
</div><div><p>目前，信息流平台已经成为广大用户主要的阅读渠道，但是海量的信息也带来了严重的信息过载问题。个性化推荐技术对于信息流平台的重要性体现在两个地方：1.主动帮助用户发现感兴趣的信息，提高阅读体验；2.提高信息流平台的用户粘性，增加收入。<br/>
信息流推荐中，主要面临三个关键问题：</p>
</div><div><ul>
<li>如何利用用户的阅读历史对其兴趣进行建模，并刻画用户兴趣在某时间段内的演变</li>
<li>如何利用资讯进行建模，充分考虑标题、标签、段落等信息</li>
<li>为了提高推荐响应速度和推荐多样性，候选内容池采用多种策略进行召回。类似该种“多模态”情况，如何对召回内容进行有效地排序？</li>
</ul>
</div><div><h3>1.1 资讯信息的多样性</h3>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/fcda5f2ed55b66b62d4c.png"/><br/>
资讯中通常会包含多种不同类型的信息，例如标题、正文、类别等。不同类型的信息特性差异很大，如，类别简明扼要，标题短小精悍概述性极强，正文冗长但细节丰富。因此，如何利用这些异构的信息学习更加丰富的内容表示是内容推荐的关键问题。</p>
</div><div><h3>1.2 用户兴趣的多样性</h3>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/a19d44f2207d959d1ad5.png"/><br/>
不同的用户对资讯阅读有不同的兴趣，并且不同的用户可能会关注同一篇新闻文章的不同重点。这导致了他们可能会因为不同的兴趣而点击相同的新闻。因此，如何学习个性化的新闻和用户表示是需要研究的问题。</p>
</div><div><h1>2. 多视角新闻推荐示例</h1>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/2214845ee157ad9c6d86.png"/></p>
</div><div><p>多视角推荐框架如上图所示。该模型包含两个核心模块，分别是一个新闻编码器和一个用户编码器。在新闻编码器中，作者从新闻的标题、正文、类别和子类别中学习新闻表示。然后将这些不同类型的新闻数据视作不同的新闻视角，并且使用词语和视角级的注意力网络来选择重要的词语和视角。在用户编码器中，作者使用新闻级的注意力机制来选取高信息量的新闻（兴趣）。而在最后的点击预测模块中，根据候选新闻和用户表示的内积来计算点击分数，用于资讯排序。</p>
</div><div><h3>2.1 数据集评估 与 同行算法对比</h3>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/b05d02b2bd0844b447b6.png"/><br/>
作者的算法架构在真实新闻推荐数据集上开展，数据集是从MSN 新闻一个月的记录中采样得到。然后使用最后一周的日志作为测试，其余用作训练和验证。结果上表所示。<br/>
同时，作者还将多视角方法与其他主流方法进行性能对比，结果如下表。性能十分优越。<br/>
<img alt="" loading="lazy" src="/logbook/images/deep-learning/d22f66c389fb5fa68a30.png"/></p>
</div><div><h3>2.2 消融实验及分析</h3>
</div><div><p>文章进一步通过消融实验进一步验证基于注意力机制的多视角学习的有效性。<br/>
<img alt="" loading="lazy" src="/logbook/images/deep-learning/4f93ed8c42c59d689730.png"/><br/>
(a)显示了模型及其仅使用一种视角的变体的性能。消融分析显示：正文比标题更为重要， 标题比标签更为重要，通过多视角学习将三种不同的信息结合能够明显提升模型效果。<br/>
(b)显示了不同注意力机制的有效性。通过分别移除某一种注意力机制来探究每种注意力网络的贡献。实验结果显示，词语级别的注意力机制最为重要。这可能是因为词语是承载新闻语义信息的基本单位。新闻和视角级别的注意力同样对于模型性能有用，并且将三者结合可以进一步提升模型性能。这也验证了模型中基于注意力机制的多视角学习方法的有效性。</p>
</div><div><h3>2.2 注意力机制可视化研究</h3>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/ca0b87037949fcd8439e.png"/><br/>
<img alt="" loading="lazy" src="/logbook/images/deep-learning/18ccd46407f86ae6a4fb.png"/><br/>
多注意力机制、层次注意力使用是文章的亮点之一。为了研究各个注意力模块学习情况，作者也进行的attention权重分布可视化研究。通过上图可以发现，该模型能识别和选择重要的词语和新闻。例如，Bowl、Coach 这样的词语对于推测新闻的主题很有帮助，因此被高亮，而像 weekend 这样的词语则信息量较低。对于新闻而言，例如第4条新闻被高亮，因为它能够很好地反映用户的兴趣，而如第3和第5条新闻则可能被各种类型的用户浏览，没有兴趣区分度，因此获得了较低的权重。</p>
</div><div><h1>3. 代码复现</h1>
</div><div><p>新闻编码器实现：<br/>
embedding_layer = Embedding(len(word_dict), 300, weights=[embedding_mat], trainable=True)</p>
</div><div><p>title_input = Input(shape=(MAX_SENT_LENGTH,), dtype=‘int32’) # shape = [None, 30]<br/>
embedded_sequences_title = embedding_layer(title_input) # shape = [None, 30, 300]<br/>
embedded_sequences_title = Dropout(0.2)(embedded_sequences_title) # shape = [None, 30, 300]<br/>
title_cnn = Convolution1D(nb_filter=400, filter_length=3,  padding=‘same’, activation=‘relu’, strides=1)(embedded_sequences_title)<br/>
title_cnn = Dropout(0.2)(title_cnn) # shape = [None, 30, 400]<br/>
attention = Dense(200,activation=‘tanh’)(title_cnn) # shape = [None, 30, 200]<br/>
attention = Flatten()(Dense(1)(attention))<br/>
attention_weight = Activation(‘softmax’)(attention)<br/>
title_rep = keras.layers.Dot((1, 1))([title_cnn, attention_weight]) # shape = [None, 400]</p>
</div><div><p>body_input = Input(shape=(MAX_BODY_LENGTH,), dtype=‘int32’) # shape = [None, 300]<br/>
embedded_sequences_body  = embedding_layer(body_input) # shape = [None, 300, 300]<br/>
embedded_sequences_body  = Dropout(0.2)(embedded_sequences_body) # shape = [None, 300, 300]<br/>
body_cnn = Convolution1D(nb_filter=400, filter_length=3,  padding=‘same’, activation=‘relu’, strides=1)(embedded_sequences_body)<br/>
body_cnn = Dropout(0.2)(body_cnn) # shape = [None, 30, 400]<br/>
attention_body = Dense(200,activation=‘tanh’)(body_cnn) # shape = [None, 300, 200]<br/>
attention_body = Flatten()(Dense(1)(attention_body))<br/>
attention_weight_body = Activation(‘softmax’)(attention_body)<br/>
body_rep=keras.layers.Dot((1, 1))([body_cnn, attention_weight_body]) # shape = [None, 400]</p>
</div><div><p>vinput = Input((1,), dtype=‘int32’)  # shape = [None, 1]<br/>
svinput = Input((1,), dtype=‘int32’)<br/>
v_embedding_layer  = Embedding(len(category)+1, 50, trainable=True)    # 类别信息嵌入层<br/>
sv_embedding_layer = Embedding(len(subcategory)+1, 50, trainable=True)<br/>
v_embedding  = Dense(400,activation=‘relu’)(Flatten()(v_embedding_layer(vinput))) # shape = [None, 400]<br/>
sv_embedding = Dense(400,activation=‘relu’)(Flatten()(sv_embedding_layer(svinput))) # shape = [None, 400]</p>
</div><div><p>all_channel = [title_rep,body_rep,v_embedding,sv_embedding]<br/>
views = concatenate([Lambda(lambda x: K.expand_dims(x,axis=1))(channel) for channel in all_channel], axis=1) # shape = [None, 4, 400]<br/>
attentionv = Dense(200,activation=‘tanh’)(views) # shape = [None, 4,200]<br/>
attention_weightv = Lambda(lambda x: K.squeeze(x,axis=-1))(Dense(1)(attentionv)) # shape = [None, 4]<br/>
attention_weightv = Activation(‘softmax’)(attention_weightv) # shape = [None, 4]</p>
</div><div><p>newsrep = keras.layers.Dot((1, 1))([views, attention_weightv]) # shape = [None, 400]</p>
</div><div><p>newsEncoder = Model([title_input,body_input,vinput,svinput], newsrep)<br/>
plot_model(newsEncoder, to_file=‘newsEncoder.png’)</p>
</div><div><p>用户编码器实现：<br/>
browsed_title_input = [keras.Input((MAX_SENT_LENGTH,), dtype=‘int32’) for _ in range(MAX_SENTS)]<br/>
browsed_body_input = [keras.Input((MAX_BODY_LENGTH,), dtype=‘int32’) for _ in range(MAX_SENTS)]<br/>
browsed_v_input = [keras.Input((1,), dtype=‘int32’) for _ in range(MAX_SENTS)]<br/>
browsed_sv_input = [keras.Input((1,), dtype=‘int32’) for _ in range(MAX_SENTS)]<br/>
browsednews = [newsEncoder([browsed_title_input[],browsed_body_input[],browsed_v_input[],browsed_sv_input[] ])<br/>
for _ in range(MAX_SENTS)]<br/>
browsednewsrep = concatenate([Lambda(lambda x: K.expand_dims(x,axis=1))(news)<br/>
for news in browsednews],axis=1)<br/>
attentionn = Dense(200,activation=‘tanh’)(browsednewsrep)<br/>
attentionn = Flatten()(Dense(1)(attentionn))<br/>
attention_weightn = Activation(‘softmax’)(attentionn)<br/>
user_rep = keras.layers.Dot((1, 1))([browsednewsrep, attention_weightn])</p>
</div><div><p>candidates_title = [keras.Input((MAX_SENT_LENGTH,), dtype=‘int32’) for _ in range(1+npratio)]<br/>
candidates_body = [keras.Input((MAX_BODY_LENGTH,), dtype=‘int32’) for _ in range(1+npratio)]<br/>
candidates_v = [keras.Input((1,), dtype=‘int32’) for _ in range(1+npratio)]<br/>
candidates_sv = [keras.Input((1,), dtype=‘int32’) for _ in range(1+npratio)]</p>
</div><div><p>candidate_vecs = [newsEncoder([candidates_title[],candidates_body[],candidates_v[],candidates_sv[]])<br/>
for _ in range(1+npratio)]<br/>
logits = [keras.layers.dot([user_rep, candidate_vec], axes=-1)<br/>
for candidate_vec in candidate_vecs]<br/>
logits = keras.layers.Activation(keras.activations.softmax)(keras.layers.concatenate(logits))</p>
</div><div><p>model = Model(candidates_title + browsed_title_input +<br/>
candidates_body  + browsed_body_input  +<br/>
candidates_v     + browsed_v_input     +<br/>
candidates_sv    + browsed_sv_input,<br/>
logits)<br/>
plot_model(model, to_file=‘User_News_train.png’)</p>
</div><div><h1>4. 多视角在CTR预测任务上的应用</h1>
</div><div><p>通过上面分析，我们可以发现，多视角主要为了解决特征信息的多样性，不同维度特征之间是通过注意力机制进行融合。这样做的目的，笔者认为有两点：1. 多视角下的特征不应该直接通过concat输入到分类器，防止feature conflict； 2. attention机制的使用可以认为是data-driven型的特征筛选与融合。<br/>
我们将该思想应用到因子分解机中，尝试提升CTR预测的精度。我们将一阶特征、二阶交叉特征、高阶交叉特征视为不同的视角</p>
</div><div><h3>4.1 FM vs AFM vs AMFM (attention multi-view)</h3>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/65e05aa50e6014620fda.png"/>我们在ml-tag数据集上进行测试，训练集和验证集的mrse随着epoch的变化，以及测试集统计结果如下：<br/>
<img alt="" loading="lazy" src="/logbook/images/deep-learning/9410e427f34d27cbf5fc.png"/></p>
</div><div><h3>4.2 deepFM vs AM deepFM</h3>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/f8c34bc7b2165fb8d50a.png"/><br/>
我们在ml-tag数据集上进行测试，训练集和验证集的mrse随着epoch的变化，以及测试集统计结果如下：<br/>
<img alt="" loading="lazy" src="/logbook/images/deep-learning/f6971ad5f292dc480443.png"/></p>
</div><div><h1>5. 总结</h1>
</div><div><ol>
<li>同一视角中的attention模块，可以理解为该视角下的特征选择与融合的过程</li>
<li>多视角中的attention模块，可以理解为机器学习中的集成分类器；综合考虑各个视角对任务的贡献程度，通过自适应分配权重而提高性能。</li>
<li>该方法后续将在游戏资讯推荐中落地，用以解决多路召回内容的排序</li>
</ol>
</div><div><h1>参考文献：</h1>
</div><div><p>[1] IJCAI-2019 : Neural News Recommendation with Attentive Multi-View Learning<br/>
[2] KDD-2019 : NPA: Neural News Recommendation with Personalized Attention</p>
</div> 
{% endraw %}
