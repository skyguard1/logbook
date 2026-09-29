---
title: "User embedding技术应用综述"
date: 2022-04-16 10:37:21
categories:
  - 算法平台
  - 特征工程与用户建模
---

{% raw %}

<p>       在互联网业务场景中，用户/物品的表征是机器学习任务中基础且重要的工作之一，传统的方法一般是给用户或者物品打标签，比如给用户定义一个三级类目的兴趣标签。但是构建一个高质量的标签体系费时费力，成本非常高，而且应用效果也总是不尽人意。自从NLP领域词表征代表作Word2vec出来后，Embedding的表征方法论快速应用到了各个领域。本文首先简单介绍Embedding技术近几年在学术界和工业界的进展，第二部分重点介绍的user Embedding技术及其在业务场景上的应用。</p>
<h2><strong>Embedding</strong><strong>技术发展简介</strong></h2>
<p>        最近几年, 学术界和工业界产出了非常多的Embedding技术论文，本文主要对以下两类技术进行简单的归纳：第一类是基于Word2vec衍生的的Embedding技术，第二大类基于图神经网络的Embedding技术。</p>
<p><strong>1 </strong><strong>基于Word2vec衍生的</strong>Embedding<strong>技术</strong></p>
<p>         自2013年NLP领域的词表征算法Word2vec问世以来，便产生了一系列的衍生算法应用到其他领域，比较重要的一些工作列举如下。</p>
<p>        2014年WWW，Deepwalk算法，该算法将Word2vec的方法应用到了Network Embedding，主要用于同构网络。算法首先通过Random walk算法生成节点序列，基于节点序列复用Word2vec算法，得到了网络节点的Embedding向量，该向量应用到链路预测、节点分类等任务中，取得不错的效果。这个算法非常关键的一步是Random walk算法，这一步本质是在生成网络节点的邻居，生成不同的邻居将决定最后Embedding向量中包含了什么信息。我们知道，NLP领域Word2vec生成的Embedding代表了word的语义相似性，那么Deepwalk得到的节点Embedding表达了什么？本质上是用网络邻居（这里指的是广义上的邻居，可能是一度好友也可以是二度好友）表达了节点自己，那么实际上生成的Embedding表达了社交环境的相似性，即用较多共同邻居的节点，其Embedding向量会更接近。这里Deepwalk的Random walk的超参和Word2vec算法中的window-size这个超参数共同决定了节点的邻居。</p>
<p>        2016年KDD-Best，Node2vec算法，是基于Deepwalk的优化，主要用于同构网络的节点Embedding的生成，Node2vec的思路和Deepwalk类似，差异点是对Deepwalk的Random walk的算法进行了优化，也就是Node2vec在如何生成节点的邻居上做了工作，论文使用两个超参（p和q）来控制游走的方向选择了不同意义的邻居（广度优先搜索、宽度优先搜索），该算法的问题在于p和q这两个超参数很难控制，在使用应用中，建议大家根据业务经验或者需求来改造Random walk算法，选择出合适的邻居生成Embedding向量。</p>
<p>        2016年ICML-workshop，Item2vec算法，的工作，将Word2vec算法应用到item的Embedding，论文以用户的item行为sequence 看成NLP的文本序列，即以item的共现性作为NLP的上下文关系。复用Word2vec的数学模型实现了item协同的推荐。</p>
<p>        2017年KDD，Metapath2vec算法，主要应用于异构网络。算法整体框架与Deepwalk相似，差一点在于，针对异构网络该如何设计游走算法，论文提出基于metapath进行游走生成节点序列，这里Metapath需要根据网络的特点（实际意义）事先给出的，算法的第二部是基于Metapath游走出来的序列利用skip-gram得到节点的Embedding，在skip-gram这步可以将同类节点摘出来进行Embedding，也可以将异构节点一起进行Embedding，哪个更好？还是得看实际的下游任务的需求以及效果。</p>
<p>        2018年KDD-Best，Airbnb Embedding论文，这篇论文是应用实践方面的成功案例。其中两个细节值得大家参考，一是结合了业务目标（目标是希望用户订房），将用户已经订的房源作为正样本进行训练，并且放进去了目标函数中，二是针对稀疏item进行分桶再emebedding。关于这篇论文外部有很多详细解读，这里就不做赘述。这个实践论文说明对业务的分析洞察十分重要，通过分析或者理解的结论来设计模型，可能会带来很好的收益，值得我们学习。</p>
<p>       2018年KDD，阿里的EGES算法，该算法用户根据用户的item行为序列，构造了item的网络后再用Deepwalk的思路进行Embedding，但是对skipgram进行了调整，利用了item的side-info（即item属性：品类、材质等等），这对一些长尾稀疏item是非常友好的，一定程度解决了冷启动的问题。</p>
<p>        综上可见，后续算法对Deepwalk的优化点都在随机游走这一步，这一步本质上是生成语料，选择具备“业务意义”的邻居节点对Embedding的结果至关重要，结合loss函数来说，也就是如何选择节点的正样本，Airbnb的优化思路巧妙地把业务目标（已订房源作为正样本）加进来，对业务也有很大的帮助。另外，值得一提的是，loss函数设计，所有算法基本都借鉴了word2ve的负采样技术，一方面负采样loss相对多分类的softmax节省了训练时间；另者，互联网大多数场景下只有隐式反馈，很难获取真正意义上的负样本，因此适当的负采样显得更为必要。</p>
<p><strong>2</strong><strong>、基于图神经网络的Embedding技术</strong></p>
<p>          自GCN算法提出以来，最近几年很多工作在持续follow，GNN的算法主要的场景是用于节点分类等监督任务。但其中也有很多工作是用来做无监督或者半监督的embedding的工作。GNN用来做embedding可以分为两大类，第一大类是用于做拓扑结构特征的表达（我们知道deepwalk这一类的算法主要也是对拓扑相似的表达），比如以GCN做encoder的GAE算法/VGAE算法，主要是利用GCN对拓扑特征的表达。第二大类的工作是以节点特征（如同上文提到的side-info），将节点特征和拓扑特征进行融合表达，这一类工作以GraphSage为代表。下面简单介绍以下GNN-embedding技术。</p>
<p>          2016年NIPS-workshop论文, GAE&amp;VGAE，GAE将自编码器迁移到图领域，基本思路就是用GCN算法作为编码器，然后将链路预测作为解码目标重新构建图，团队在抽样网络上实现了GAE和VGAE，效果和Deepwalk只有非常微小幅度的提升。</p>
<p>         2017年NIPS，Graphsage算法，Graphsage解决了两个痛点：一是Graphsage是inductive。我们知道Deepwalk派系、GAE的算法是transductive的，即，在学习Embedding的时候仅考虑了了当前网络，对于另一个网络Embedding是需要重新训练得到的。但是Graphsage不需要，它学习出来的聚集函数可以inductive到其他网络。二是GCN的计算量的问题，训练过程中使用到图的拉普拉斯矩阵进行计算，对于大网络分分钟爆内存。那么Graphsage是怎么做到的呢？笔者认为主要有两个点： （1）Graphsage巧妙地将GCN的卷积操作转化为学习一个聚集函数（当然卷积的本质也是集聚），而且聚集函数可以多种形势。聚集函数学习的是邻居节点的信息该怎么聚集到中心节点上来。从graphsage开源的代码上看到，做一次聚集相当于一层图卷积，在此之上再迭代一次聚集即相当于实现了两层的图卷积。这里Graphsage模型要学习的参数是聚集函数的参数，如果用来做无监督的Embedding任务，其原始输入是user或者item的side-info（即特征信息）。这里参数量相比Deepwalk、GAE（每个节点的Embedding）少很多，对于网络来说，那是少了几个数量级的参数。（2）对于不同网络结构不同，算法是怎么做到inductive呢？这里在学习的过程中用到了采样技术。比如一阶邻居采样10个，二阶邻居采样5个，学习到聚集函数，这个聚集函数就可以应用到其他的网络进行打分，在打分过程中，被打分的网络也会按照这个采样进行网络采样。即通过这样的网络采样，就实现了不同结构的网络可以inductive学习了。邻居采样在实现思路和DGL的NodeFlow基本一致。其训练迭代过程中，10个邻居节点在每个epoch里面是随机生成的，即这里学习到的聚集方式是随机10个邻居的聚集方式。 Graphsage通过以上两点实现了GCN的落地应用，个人认为这里存在一些可以优化的点，即邻居采样在每次迭代过程中随机生成，那么这里学习到了是平均意义上的聚集？也许可以引起更好的采样技术，比如加入更加的节点特征或者边的特征、加一些监督信息进行指导性的采样。</p>
<p>         2018年KDD，Pinsage算法，算法应用于异构网络。Pinsage算法与graphsage思路类似，也是学习聚集函数，不同的是邻居采样策略，Pinsage不是逐层采样，而是使用了random walk with restart进行邻居采样，这种策略Node2vec使用过。Node2vec、Graphsage和Pinsage都是Jure Leskovec 的作品，其间有着千丝万缕的联系。对于Graphsage、Pinsage在外部有很多优秀的解读文章，这里就不再赘述。后续团队会分享一些实践经验。</p>
<h2><strong>User Embedding</strong><strong>在业务的应用</strong></h2>
<p><strong>1 </strong><strong>无监督user Embedding的必要性</strong></p>
<p>         在互联网业务，Embedding技术最主要的一个应用场景就是推荐系统。那么，一个非常自然的想法就是，将Embedding技术可以直接应用到做end2end推荐模型中，即加一个Embedding层，其作用是完成高维稀疏特征向量到低维稠密向量的转换。比如说著名的 deep&amp;wide模型，其中的deep部分的dense Embeddings层是将稀疏特征转化为dense特征，完成了高维向量向低维向量的直接映射。从理论上讲，将Embedding层与整个深度学习网络整合后进行end2end的训练是一个结果最优的方案，因为上层的有监督梯度信息可以直接反向传播到输入层，模型整体是统一的。但这样做的缺点同样显而易见的，由于Embedding层输入向量的维度很大，Embedding层的加入会拖慢整个模型的收敛速度，使得模型的训练成本非常大，且每一个任务都要训练一个模型。特别地，在业务场景，若使用到社交特征，这里的原始输入数据是一个10亿维的高维稀疏矩阵（关系链邻接矩阵），参数量为10亿*embedding维度，这种模型对业务侧的计算压力非常大。因此，在实际应用过程中，我们将Embedding技术进行了剥离，利用无监督的Embedding（相当于预训练）方式完成。Embedding产出的结果给多个下游任务共享，可以用于做推荐系统的召回层，或者作为精排模型的输入特征进行使用。</p>
<p>       在平台，团队针对不同类型的数据，使用合适的User Embedding的提取出有用信息，表达为向量，服务于下游的用户行为预测任务。比如直接计算相似度用于推荐系统的召回任务，或者作为特征用到推荐精排模型等。下图中展示了数据中心User Embedding的工作简图。</p>
<p>                         <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/01e81be5394ac8023ec7.png"/></p>
<p><strong>2 </strong><strong>User Embedding技术演化路线</strong></p>
<p>       团队自2016年底研发user Embedding的技术，目前在技术层面我们已经实现多种Embedding的技术，用于适配不同的数据类型和业务场景。17年我们重点研发Network Embedding的技术，最近一年来，我们更多地考虑多源异构数据的Embedding融合。下图展示了user Embedding技术路线，大部分的算法已经沉淀在plato平台。</p>
<p>                          <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7a1e37040ef5dd914ddb.png"/></p>
<p>         众所周知，去年Bert模型名声大噪，在平台，有丰富的用户行为序列数据，它和文本存在着一定的相似性，比如说行为（单词）分布的幂率性等；但是两者也存在很大的差异，文本序列中的单词具备很强的语义相关性，而人类的行为序列中的行为之间存在一定的相关性，还受到时间、空间等其他因素的影响。因此，最近一年来，团队研发Bert在user Embedding的应用以及与GNN算法的结合，取得不错的效果。后续会从以下四个方面进行实践经验的总结，与同事们讨论学习。</p>
<ul><li>Bert4UserEmbedding：主要介绍用户在某个单领域的行为序列Embedding的模型设计，以及其如何对接下游任务，加side-info的提升。</li>
<li>M-bert4UserEmbedding：介绍bert在跨领域行为序列的user Embedding的应用，使用M-bert的思路对多种行为进行融合Embedding，达到跨领域推荐的目标，一定程度地解决了冷启动的问题。</li>
<li>GPU-BERT实现技术：介绍BERT的GPU并行实现，并阐述在用户行为预训练领域BERT模型的复杂度需求。</li>
<li>Graph-autoencoder：介绍利用GCN作为encoder的Graph auto encoder算法原理及其实践。</li>
<li>GraphSage算法实践：介绍Graphsage算法在user embeddding的模型应用，剖析模型原理及参数分析。</li>
<li>SocialTrans: 从推荐的角度来说，BERT的物理含义主要是利用了item协同，对于行为稀疏行为的用户，其Embedding向量质量较差，因此我们进一步将BERT模型和GAT模型进行融合(SocialTrans模型)，在Bert的基础上增加user社交协同的思想，得到user Embedding向量。</li>
</ul><p><strong>3  </strong><strong>user Embedding技术的落地应用</strong></p>
<p>        user Embedding技术主要以两种方式应用落地。（1）基于社交、行为等数据产出用户Embedding向量沉淀在笛卡尔平台，供下游任务直接使用。目前，我们已经产出了用户的社交网络的Embedding向量、用户阅读兴趣向量、用户POI兴趣向量、用户广告兴趣向量等用户表征，已经应用于多个下游的机器学习任务，包括朋友圈广告、支付广告、看一看推荐业务、读书推荐业务、小程序推荐业务等。（2）产出Embedding技术，沉淀在Plato平台，供算法工程师使用。现在Deepwalk、LINE、Metapath2vec、BERT等Embedding算法，已经服务于公司10多个业务团队，包括游戏、小程序推荐、视频推荐业务、推荐业务、全民K歌等。同事们若有需求，欢迎合作o(∩_∩)o 。</p>
<h2><strong>总结与展望</strong></h2>
<p>        通过实践经验，我们总结出Embedding技术应用落地的两个关键点。一者是 Loss函数设计和负采样技术；在互联网很多场景下都是隐式反馈，也存在样本不平衡的问题，这里的Loss和负采样技术都值得细细斟酌。Airbnb的成功经验也来自于对业务的理解进行loss的设计。其次是大规模实现技术，大规模实现是Embedding相关技术在工业界落地的必经之路。具体的分享可以参见plato系列分享文章。另外，还有几个问题需要我们去解决：（1）多源异构数据的融合；（2）时间信息：考虑用户信息的dynamic特性。（3）Auto-Embedding：模型的超参优化，引入autoML选择合适的Embedding算法。</p>
<p> </p>
<p>参考文献：</p>
<p>[1]Deepwalk: <a href="https://arxiv.org/pdf/1403.6652.pdf">https://arxiv.org/pdf/1403.6652.pdf</a></p>
<p>[2]Node2vec: <a href="https://www-cs.stanford.edu/~jure/pubs/node2vec-kdd16.pdf">https://www-cs.stanford.edu/~jure/pubs/node2vec-kdd16.pdf</a></p>
<p>[3]Item2vec: <a href="https://arxiv.org/ftp/arxiv/papers/1603/1603.04259.pdf">https://arxiv.org/ftp/arxiv/papers/1603/1603.04259.pdf</a></p>
<p>[4]Metapath2vec: <a href="http://library.usc.edu.ph/ACM/KKD%202017/pdfs/p135.pdf">http://library.usc.edu.ph/ACM/KKD%202017/pdfs/p135.pdf</a></p>
<p>[5]Airbnb embedding: <a href="https://dl.acm.org/citation.cfm?id=3219885">https://dl.acm.org/citation.cfm?id=3219885</a></p>
<p>[6]阿里EGES算法：<a href="https://arxiv.org/pdf/1803.02349.pdf">https://arxiv.org/pdf/1803.02349.pdf</a></p>
<p>[7]GAE&amp;VGAE <a href="https://arxiv.org/pdf/1611.07308.pdf">https://arxiv.org/pdf/1611.07308.pdf</a></p>
<p>[8]GAE相关应用论文<a href="https://arxiv.org/pdf/1703.06103.pdf">https://arxiv.org/pdf/1703.06103.pdf</a></p>
<p>[9]Graphsage：<a href="https://papers.nips.cc/paper/6703-inductive-representation-learning-on-large-graphs.pdf">https://papers.nips.cc/paper/6703-inductive-representation-learning-on-large-graphs.pdf</a></p>
<p>[10]Pinsage: <a href="https://arxiv.org/pdf/1806.01973.pdf">https://arxiv.org/pdf/1806.01973.pdf</a></p>
<p>[11]Transformer: <a href="https://papers.nips.cc/paper/7181-attention-is-all-you-need.pdf">https://papers.nips.cc/paper/7181-attention-is-all-you-need.pdf</a></p>
<p>[12]Bert: <a href="https://arxiv.org/pdf/1810.04805.pdf%E3%80%91">https://arxiv.org/pdf/1810.04805.pdf%E3%80%91</a></p>
<p>[13]Network embedding综述[内部或本地链接已移除]</p>
<p>[14]异构网络embedding[内部或本地链接已移除]</p> 
{% endraw %}
