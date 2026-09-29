---
title: "应用宝embedding向量搜索系统设计和应用（基于Faiss）"
date: 2022-04-06 11:49:13
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<p>本项目已经开源：[内部或本地链接已移除]，欢迎大家协同共建！</p>
<div>
<h2>1 背景</h2>
<p>近年来，随着深度学习、AI等技术的快速发展，在智能推荐、对话系统、搜索系统、广告系统等领域中越来越多的应用到embedding技术，即向量化的方式来描述现实世界。这种方式不仅适用范围广，而且能够较好的描述现实世界的语义相关性。在实际应用中，寻找相似item是一个基本需求。而采用向量化表达以后，这种需求变成了一个纯数学问题，即给定一个向量，从全部向量中找出距离最近的N个向量（最近邻检索，Nearest Neighbor Search）。这个数学问题在学术界已经研究的很充分，比如各种近似最近邻搜索（ANN），局部敏感哈希(LSH)等。</p>
<h2>2 业务需求</h2>
<p>在当前多数应用场景中，通常是离线的方式使用embedding技术。item离线做向量化，然后用最近邻检索算法提前计算每个item的相似item列表，然后导入线上系统存储（例如redis，DCahe， BDB等），在线系统直接读取相似结果。这种方式有几个缺陷：</p>
<p>1.      浪费存储资源：需要穷举每个item的相似item列表</p>
<p>2.      时效性差：全部向量计算相似非常消耗资源，速度很慢，限制了更新频率</p>
<p>3.      覆盖有限：无法完全枚举的item或新item无法被覆盖到</p>
<p>4.      某些场景embedding无法通过离线计算：例如用户实时行为序列embedding</p>
<p>为了追求更好的线上应用效果，就需要在线embedding生成向量，然后实时在全量向量中执行最近邻搜索，也就是需要一套在线embedding向量搜索服务。在线系统就需要考虑可靠性、响应时间、精度等各种问题。值得庆幸的是，的人工智能研究团队2017年开源的一套向量相似性搜索库FIASS，可在GPU 上实现十亿规模级的相似性搜索，而且性能特别高。FAISS开源后，我们立即进行了工程上的前期测试论证工作，证明了其强大的业务价值。随即启动了应用宝embedding向量搜索服务项目（代号ElasticFaiss，灵感来自ElasticSearch），本文将着重介绍该系统的架构设计和实际应用。</p>
<h2>3 设计目标</h2>
<p>Faiss是一个开源的向量相似性搜索库，功能强大。其原理这里就不再赘述，网上有大量资料可供研究。</p>
<p>但是 Faiss仅仅只是一个库。为了充分发挥其功能，你需要使用 C++或者Python 并将 Faiss直接集成到应用程序中。如果你需要基于Faiss创建一个可靠的搜索服务，那么还需要考虑数据的存储，服务可靠性，可用性，扩展能力等一系列复杂问题。</p>
<p>我们希望基于Faiss库构建一个独立完备的搜索服务，类似ElasticSearch之于lucene，于是命名为ElasticFaiss。另外，在现在动辄数亿数据的规模前，单机肯定是不行的，因此分布式集群是一个基本要求。要实现一个完备的分布式相似性搜索服务，一般需要提供以下能力：</p>
<p>1.      分布式的实时对象存储，其中存储对象携带相似性向量；</p>
<p>2.      分布式实时分析搜索引擎；</p>
<p>3.      能胜任尽可能多的服务节点数（1000+），支持尽可能多的数据存储（PB级）。</p>
<h2>4 基础架构</h2>
<p>ElasticFaiss分布式向量搜索服务同时也是一个分布式的存储服务，由三种角色相互协作构成：分布式索引存储（Index Node）、搜索执行引擎（Search Engine Node）、集群管理（Cluster Management Node）。它们之间的关系和功能如下图所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7b66a7f70d30ef612b7f.png"/></p>
<h3>4.1 索引与分片（Shard）</h3>
<p>首先，我们引入索引（Index）与分片（Shard）的概念。从抽象概念出发，我们约定一份完整的原始数据，可以先给定一个唯一的名字（Index），类似MySQL里的DB概念。索引实际上是指向一个或者多个物理 分片 的逻辑命名空间。</p>
<p>其次，针对数据可以按一定的规则split划分为几个独立单元，可称之为Shard。</p>
<p>最后，还需要引入副本（Replica）的概念。针对任意的Shard，一般需要有Replica Shard存在以保证容灾能力。副本分片作为硬件故障时保护数据不丢失的冗余备份，并为搜索和返回文档等读操作提供服务。</p>
<h3>4.2 索引存储（IndexNode）</h3>
<p>Index Node 负责存储数据的索引，从外部看 Index Node 是一个分布式的提供事务的 Faiss检索存储引擎。存储数据的基本单位是 Shard，每个 Shard负责存储一个hash区间数据，每个 Index Node 节点会负责多个 Shard 。数据在多个Index Node之间的负载均衡由 CM调度分配。数据索引的建立过程如下图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/da346d56aac4b181eb1d.png"/></p>
<h3>4.3 CM（Cluster Management Node）</h3>
<p>Cluster Management (简称 CM) 是整个集群的管理模块，其主要工作有以下：</p>
<p>l  集群全局配置管理</p>
<p>l  管理集群的元信息（某个 shard存储在哪个 Index Server 节点）；</p>
<p>l  对Index Server集群进行调度和负载均衡（如数据的迁移）；</p>
<p>l  节点发现与故障迁移。</p>
<p>CM目前是借助Raft协议实现的，主要逻辑如下图所示。</p>
<p>CM节点由至少三节点组成，通过Raft一致性协议保证所有的集群状态（shard分配等）在CM集群中是强一致性的。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/95d98739077a341ae4ec.png"/></p>
<h3>4.4 搜索执行引擎（SearchEngine Node）</h3>
<p>搜索执行引擎负责接收搜索请求，处理搜索相关的逻辑，并通过CM找到索引数据的 Index Node 地址，与 Index Node 交互获取数据，最终返回结果。执行引擎是无状态的，其本身并不存储数据，只负责计算，可以无限水平扩展，通过负载均衡组件对外提供统一的服务。</p>
<p>搜索执行引擎的工作流程：</p>
<p>1.      query向量化（每个DB算法不一样）</p>
<p>2.      查表获得DB所有Shard地址，每个Shard选择一个索引节点</p>
<p>3.      给索引节点发送子搜索请求</p>
<p>4.      索引节点查本地cache</p>
<p>5.      索引节点执行Faiss算法的搜索过程</p>
<p>6.      所有索引节点搜索结果合并、排序、取TOP</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/afccf96957d9265fb2a3.png"/></p>
<h3>4.5 性能测试数据</h3>
<p>在3台M10Dokcer上测试数据如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2bcbe587573a75647f1e.png"/></p>
<h2>5 应用展示</h2>
<h3>5.1 以图搜图</h3>
<p>图片是向量化技术应用最成熟的领域之一，我们对130W ImageNet图片，运用inception-v4模型，离线抽取1001维特征，构建索引入库，实现“以图搜图”的效果。语音、视频等多媒体搜索也可以采用类似的方法。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/17e41eddac7507d89041.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f90e17f36f0357ace091.png"/></p>
<h3>5.2 王者荣耀对话机器人妲己小秘书</h3>
<p>应用宝与王者荣耀合作的对话机器人“妲己小秘书”在王者知识问答和王者FAQ中采用检索式的模型，其中用户query和标准问答库中的Question都映射为句子向量，然后使用了Faiss基于余弦相似度进行搜索排序召回。由于不需要加载倒排索引，内存消耗降低到原来的五分之一，召回时间降低到原来的一半，有效提高了系统性能。</p>
<h3>5.3 应用宝内嵌的天天快报相似文章推荐</h3>
<p>在应用宝天天快报内容推荐中，我们对文章内容抽取300维embedding特征，构建索引入库，在更多新闻场景实时推荐相似内容，人均点击率提升23.7%。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4e89a82068f756b64cce.jpg"/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/82f323ab1ed677001779.jpg"/></p>
<h3>5.4 对话系统中的Query泛化</h3>
<p>网上爬取1.4亿语料，抽取150维embedding特征，对比ES的传统关键词搜索召回可以看出，Faiss搜索结果在语义层面上更为接近，比较适合在意图槽位标注中做泛化。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7d813774c2b876ce5bff.png"/></p>
<h3>5.5 应用宝APP搜索</h3>
<p>通过CNN将query和app语义实时投影到同一个语义空间（semantic embedding），再通过Faiss索引。</p>
<p>                                            </p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2661df9439c632da6093.png"/></p>
<h3>5.6 用户画像相似人群LookAlike</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a339b5a1aaf37a151ddd.png"/></p>
<h2>6 展望</h2>
<p>       目前系统已经接入十几个场景数据，还处于应用的初级阶段。除了以上展示的应用场景外，预计未来还可以在以下业务场景中使用：</p>
<p>1.      短视频推荐</p>
<p>2.      广告系统关键词拓展</p>
<p>3.      社交产品兴趣圈子</p>
<p>4.    地图空间索引（忽然想到的，2018/8/30补充）</p>
<p>当前系统在易用性上还有很多不足，需要不断迭代优化，例如：</p>
<p>1.      自动寻参：自动寻找向量集最优索引参数</p>
<p>2.      引入Tensorflow Serving使Embedding算法组件化</p>
<p>3.      支持GPU：满足对性能有极致要求的业务场景</p>
<p>我们的目标是打磨一个通用的分布式相似性搜索服务，做到像关键词搜索服务ES一样易用，将来能为公司内更多业务提供助力。</p>
<h2>7 结语</h2>
<p>基于向量化表示的实体通用性强，适用范围广，随着embedding算法的丰富，基于这种相似性搜索的业务需求也会越来越多，数据量也会越来越大，分布式相似性搜索服务很可能成为搜索服务中不可缺失的一部分。当然，任何系统都不会完美，相似性搜索缺点在于策略干预能力有限，因此适合做底层的粗召回，上层再做算法策略的精排，这样才能在实际应用中取得不错的效果。</p>
</div> 
{% endraw %}
