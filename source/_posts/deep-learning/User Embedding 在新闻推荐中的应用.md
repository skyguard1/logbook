---
title: "User Embedding 在新闻推荐中的应用"
date: 2022-04-20 10:49:30
categories:
  - deep-learning
---

{% raw %}

<p><strong><b>1  概述<br/></b></strong></p>
<p>个性化新闻推荐，是根据用户的喜好，为其推荐其关注的、感兴趣的新闻资讯。相关技术已经在新闻、今日头条等产品成功应用。个性化推荐技术，按照推荐原理可以分为三大类：基于协同过滤的推荐、基于画像属性的推荐、基于热度的推荐。其中，1）基于画像的推荐是根据用户的一些固有属性，比如性别、 年龄、地域、喜欢的类别、喜欢的关键词等进行推荐，这种方式侧重满足用户的长期兴趣； 2）基于热度的推荐，是为用户推荐一段时间内热度很高、大家都喜欢文章； 3）与上面两种方式不同， 基于协同过滤的推荐，更加侧重用户当前的行为、即时的兴趣，推荐文章的准确率和用户体验都显著高于前两种方式。</p>
<p>基于协同过滤的推荐分为两种： 一种是基于Item的协同过滤（Item Collaborative Filtering，简称ICF），一种是基于User的协同过滤(User Collaborative Filtering, 简称UCF)。 在推荐应用中，这两个策略各有侧重，经常配合使用。其中， ICF是根据用户历史点击，推荐与这些历史点击相关的文章； UCF是根据用户之间的相关性，推荐和他相似的用户点击的文章。</p>
<p>UCF推荐的文章不依赖用户的历史点击， 也不依赖用户的固有画像，因此具有很强的扩展性、多样性。可以避免用户点击集中造成的“信息孤岛”，有利于用户的兴趣探测，提升用户的产品体验。 因此，对UCF的深度探索和优化是推荐系统需要重点关注的方向。 UCF算法的关键是计算用户之间的相关性，传统的UCF算法，主要是根据用户在历史点击来计算用户之间的相关性。 这种方法计算简单，但依赖用户大量的历史点击，来统计两两用户之间的共点击文章次数。在目前的新闻个性化推荐中，用户规模往往是亿级，传统UCF算法的复杂度可以达到（亿 * 亿）的级别。 因此计算量巨大，且只能覆盖头部活跃用户， 对于大量的非活跃用户很难准确覆盖（一般很难做到70%以上， 我们在新闻二级频道场景的实际测试中，UCF的覆盖最高只能达到50%）。</p>
<p>为了提升UCF的覆盖率，我们提出了基于<strong><b>用户分桶Embedding的协同推荐算法（UeCF）</b></strong>，</p>
<p>通过DNN模型来计算用户之间的相似度，而不在依赖其历史点击的统计。该算法采用哈希映射的方法， 将每个用户id映射到一个固定的分桶， 然后通过学习桶与桶之间的相似度，来表示用户之间的相似度。<strong><b>主要优点</b></strong><strong><b>有</b></strong>：1）通过用户hash分桶， 将问题的复杂度降低，从亿的级别， 降低到百万量级； 这就将原本需要计算上亿的用户相似度， 转成只需要计算百万hash桶的相似度即可，大幅提升召回率； 2）用户分桶之后， 采用桶内用户合并的展点日志，来训练学习桶的Embedding， 避免了长尾用户训练数据少、特征学习不够充分的问题； 3）效果好，在我们已经将算法在新闻二级频道的个性化推荐中成功使用，召回的文章的点击率召和传统的UCF召回的文章持平， 但召回率可以达到98%以上，系统整体的点击指标提升7%以上。</p>
<p><strong><b>2  现有技术的技术方案</b></strong></p>
<ul><li>基于用户共点击的UCF算法； 该算法是推荐系统最常用的UCF计算方法。 统计用户两两之间的历史点击的相似度，来计算用户的相似度。常用的计算公式如下：                                        score = click_num(A,B)/(click_num(A) + click_num(B))； 其中， click_num(A,B)表示，用户A和用户B， 共同点击过的文章个数， click_num(A)表示用户A一共点击过的文章个数，click_num(B)表示用户B一同点击过的文章数。 这种计算方式原理简单， 易于理解。但是存在的缺点也很明显：a）用户的量级很大，一般是亿的量级，计算量可以达到 亿 x亿；b）且长尾用户较多，点击日志不够丰富，这就会导致覆盖率很低，大多只能计算头部用户的相关性。</li>
</ul><ul><li>基于用户画像embedding的UCF算法； 该方法， 每个用户id都有一系列的tag（根据用户历史的行为， 提取计算的文章关键词）； 然后采用类似word2vec的算法， 将这些tag转成向量，用tag的向量按照一定的方式（比如，加权平均）计算得到用户的embedding向量。 然后根据用户向量之间的距离来表示用户的相似度。这种方法相当于基于共点击的UCF算法，有一定的进步：从用户的画像数据出发，避免了大量的统计计算。</li>
</ul><ul><li> 基于用户点击序列的UCF算法； 该算法和2)类似，区别在于使用用户的历史点击文章，来间接计算用户的Embedding。 历史点击文章的Embedding可以采用文章tag的计算，有可以把文章当做word，采用word2vec的思路直接计算文章的向量。然后采用类似的方式，比如加权平均的方法获取用户的Embedding，进而计算user直接的相似度。</li>
</ul><p><strong><b>3  User 分桶 Embedding的协同推荐<br/></b></strong></p>
<p>现有技术上节列出了常用的三种， 其中第一种使用最广泛，基于统计来计算用户的相似度，优点是准确率高，特别是当数据量丰富的时候，对用户之间的相似度刻画最为准确； 缺点也很明显， 计算量大、覆盖率低，因为它需要用户大量的历史数据。</p>
<p>为了避免大量的统计计算，后两种算法将user的相似度计算转成user向量表示之间的计算，不得不说，这是一个很大的进步。两种算法都是通过用户喜欢的文章或tag的向量，来间接计算用户的Embedding，然后通过用户Embedding向量之间的距离表示用户的相似程度。相对于统计的传统方法， 计算量少很多，避免了大量的统计计算。 </p>
<p>但是， 这两种方法依然没有解决长尾用户的覆盖问题。 基于用户画像的UCF， 依赖用户的画像tag，长尾用户的画像tag较少也会导致覆盖率不高；基于用户点击序列的UCF算法，也一样，依赖用户的历史点击，点击少的长尾用户，文章或者tag的Embedding学习不够充分，无法大幅提升长尾用户的有效覆盖。</p>
<p>为了解决现有算法的缺点，提高长尾用户的覆盖率，我们提出了该算法，即对用户分桶计算embedding，用桶之间的相似度来衡量用户的相似度。1）通过用户hash分桶， 将问题的复杂度降低，从亿的级别， 降低到百万量级； 这就将原本需要覆盖上亿的用户，转成只需要覆盖百万的hash桶即可，大幅提升召回率； 2）用户分桶之后， 采用桶内用户的展点日志，来训练学习桶的Embedding， 避免了长尾用户训练数据少、特征学习不够重复的问题。</p>
<p> 实验表明，本方案在我们的具体应用场景中，所以用户的覆盖率（召回率）达到98%以上。</p>
<p><strong><b>4  技术实现<br/></b></strong></p>
<p>本方案主要包括两部分：离线模型训练和在线查询推荐模块。框架图如下。</p>
<table><tbody><tr><td><img alt="" loading="lazy" src="/logbook/images/deep-learning/46e0498da366105d7de8.png"/></td>
</tr><tr><td>图1. User分桶Embedding 协同过滤框架图</td>
</tr></tbody></table><p>离线训练模块，通过hash的方式将用户id聚合，使用同一个分桶（hash桶）内，多个用户的展现、点击、用户tag等数据， 做为该桶的训练数据进行训练DNN模型。 DNN模型采用pairwise的方式训练，学习模型各层的参数。模型训练完成之后， 计算出各个分桶的Embedding， 然后为每个桶计算相关性最高的TopN的桶。 最后将桶与桶之间的相关， 转成桶与用户之间的相关，存储redis即可。</p>
<p>在线查询模块，首先将用户的ID，通过哈希函数计算出对应的桶号。 然后用该桶号从redis里面取出对应的、相关性最好的TopN的用户id；最后用这批用户id从redis里面取出他们最近点击的文章，将其按照一定的权重计算，排序之后推荐给用户即可。</p>
<p><strong><b>5 各步骤，详细说明：</b></strong></p>
<p><strong><b>5.1 数据预处理</b></strong></p>
<p>在应用场景内，根据过去一段时间内用户展现和点击的日志，分别获取两份数据：</p>
<ul><li>用户的画像tag， 基于用户的点击文章，从中提取用户点击次数最多的TopN的tag， 作为该用户的画像tag，存储方式为&lt;User_ID, TAG_list&gt;;</li>
<li>用户的展点日志，merger过去一段时间内，用户的展现和点击日志，获取每个用户的点击文章列表和展现文章列表。存储方式为：&lt;User_ID，Click_list,  NonClick_list&gt;。</li>
</ul><p><strong><b>5.2 哈希分桶</b></strong></p>
<p>哈希分桶流程如下图。</p>
<table><tbody><tr><td>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/1b17a2e936201dca0067.png"/></p>
</td>
</tr><tr><td>
<p>图3. 哈希分桶处理流程</p>
</td>
</tr></tbody></table><p>其中，User_ID为用户的id，字符串格式，哈希函数是将字符串转成0到K的正整数，这里K是桶的大小，n是用户的个数。 将User_ID映射到分桶ID即Hash_ID的公式为： </p>
<p>Hash_ID=Hash(User_ID) % K;</p>
<p>一般情况下， K的大小根据用户的量级而定， 用户数n在亿的级别时，K可以取百万量级。哈希映射之后，每个哈希桶里面会有m个用户id（其中m约等于n/K）。 取该桶中m个用户的画像tag 加权得分最高的TopN个tag作为该桶的tag；取m个用户在过去一段时间内的展现、点击的文章，作为该桶的展现和点击的文章列表。相应数据分布存储为：</p>
<p>&lt;Hash_ID, Hash_TAG_list&gt;</p>
<p>&lt;Hash_ID，Click_Doc_TAG_List&gt; </p>
<p>&lt;Hash_ID, NonClick_Doc_TAG_List&gt;</p>
<p><strong><b>5.3 </b></strong><strong><b>DNN模型训练</b></strong></p>
<p>DNN模型训练框架如下图。</p>
<table><tbody><tr><td>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/ab838cff5efdb7ba2254.png"/></p>
</td>
</tr><tr><td>
<p>图4. DNN模型训练框架</p>
</td>
</tr></tbody></table><p>其中，TAG embedding table是 tag的Embedding表，大小为(Dx128)，其中D为tag的总个数； Hash_ID embedding table 是哈希桶的Embedding表，大小为(K x 32)，其中K为哈希桶的个数。 训练时，根据上一步获取的数据，获取一系列的如下格式的三元组，作为训练数据：</p>
<p><em><i>&lt;Hash_ID,Hash_TAG_List；Click_Doc_TAG_List；NonClick_Doc_TAG_List&gt;</i></em></p>
<p>Loss为hinge-loss，模型采用SGD进行迭代。Embedding表和FC层的参数，初始化均为随机初始化，通过模型的迭代训练进行学习。训练完成之后，保存各层参数.<strong></strong><strong><b> </b></strong></p>
<p><strong><b>5.</b></strong><strong><b>4</b></strong><strong><b> </b></strong><strong><b>计算哈希桶的Embedding</b></strong></p>
<p>哈希桶的Embedding计算，即模型前向预估，流程如下图，查询结果存储为Hash_ID_Vector_List。</p>
<table><tbody><tr><td>
<p>    <img alt="" loading="lazy" src="/logbook/images/deep-learning/98f6a6e2239c060aa596.png"/></p>
</td>
</tr><tr><td>
<p>图5. 前向计算获得桶的Embedding</p>
</td>
</tr></tbody></table><p> </p>
<p><strong><b>5.</b></strong><strong><b>5</b></strong><strong><b> </b></strong><strong><b>计算Hash_ID和User的相关数据</b></strong></p>
<p>该步主要分两部分：1）计算每个桶的cosine得分最高的TopN的桶；2）利用桶和User_ID的映射关系，将桶与桶之间的相关， 转成桶与User之间的相关，并存储。相关流程如下：</p>
<table><tbody><tr><td>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/bb20e86bd64b5d346952.png"/></p>
</td>
</tr><tr><td>
<p>图6. 计算HashID和UserID的相关数据</p>
</td>
</tr></tbody></table><p><strong><b> </b></strong></p>
<p><strong><b>5.</b></strong><strong><b>6 在线推荐模块</b></strong></p>
<p>基于前面几步的结果，在线推荐的逻辑就很清晰：1）根据User_ID映射对应的Hash_ID；2）根据Hash_ID查询redis，获得TopN相关的User_ID；3）根据相关User_ID，查询各自最近的点击文章， 综合排序之后推荐给用户。相关流程如下：</p>
<table><tbody><tr><td>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/53e933eacbe1c05cdc09.png"/></p>
</td>
</tr><tr><td>
<p>图7. 在线查询过程</p>
</td>
</tr></tbody></table><p></p>
<p><strong><b>6 结尾</b></strong></p> 
{% endraw %}
