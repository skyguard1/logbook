---
title: "【万亿数据】看点多维实时分析系统技术架构"
date: 2022-04-06 10:37:49
categories:
  - 算法平台
  - 平台工程与评估
---

{% raw %}

<h1>1、可解决的痛点</h1>
<p>        可以先看一下，多维实时数据分析系统可以解决哪些<strong>痛点</strong>。比如：</p>
<p>        <strong>推荐</strong>同学10分钟前上了一个<strong>推荐策略</strong>，想知道在不同人群的<strong>推荐效果怎么样</strong>？</p>
<p>        <strong>运营</strong>同学想知道，在广东省的用户中，最火的广东地域内容是哪些，方便做<strong>地域Push</strong>。</p>
<p>        <strong>审核</strong>同学想知道，过去5分钟，游戏类<strong>被举报最多的内容</strong>和<strong>账号</strong>是哪些？</p>
<p>        <strong>老板</strong>可能想了解，过去10分钟<strong>有多少用户</strong>在看点消费了内容，对<strong>消费人群</strong>有一个<strong>宏观了解</strong>。</p>
<h1>2、调研</h1>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b4559f6afc606bcb3553.png"/></p>
<p>        在进行开发之前，我们做了这些调研。</p>
<p>        1、离线数据分析平台能否满足这些需求，结论是<strong>不能满足</strong>。离线数据分析平台不行的<strong>原因如下</strong>。a、C侧数据上报过来，需要经过Spark的多层离线计算，最终结果出库到Mysql或者ES提供给离线分析平台查询。这个过程的延时最少3-6个小时，目前比较常见的都是<strong>提供隔天的查询</strong>，所以很多实时性要求高的业务场景都是不能满足的。b、另一个问题是，看点的数据量太大，带来的<strong>不稳定性也比较大</strong>，经常会有预料不到的延迟。所以，离线分析平台是<strong>无法满足</strong>很多需求的。</p>
<p>        2、实时数据分析平台的话，事业群内部提供了<strong>准实时</strong>数据查询的功能，底层技术用的是<strong>Kudu+Impala</strong>，Impala虽然是MPP架构的大数据计算引擎，并且访问以列式存储数据的Kudu。但是对于实时数据分析场景来说，查询响应的速度和数据的<strong>延迟都还是比较高</strong>，查询一次实时DAU，返回结果耗时至少<strong>几分钟</strong>，无法提供良好的交互式用户体验。所以（Kudu+Impala）这种通用大数据处理框架的速度优势更多的是相比（Spark+Hdfs）这种离线分析框架来说的，对于我们这个实时性要求更高的场景，是<strong>无法满足</strong>的。</p>
<h1>3、项目背景</h1>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a66717f0e09bb1dd9f11.png"/></p>
<p>        经过刚才的介绍，再来看下我们这个项目的背景。</p>
<p>        作者发文的内容被内容中心引入，经过内容审核链路，启用或者下架。启用的内容给到推荐系统和运营系统，然后推荐系统和运营系统将内容进行C侧分发。内容分发给C侧用户之后，用户会产生各种行为，曝光、点击、举报等，通过埋点上报实时接入到消息队列中。</p>
<p>        接下来我们做了<strong>两部分工作</strong>，就是图中有颜色的这两部分。</p>
<p>        第一部分构建了一个看点的<strong>实时数据仓库</strong>。</p>
<p>        第二部分就是基于OLAP存储引擎，开发了<strong>多维实时数据分析系统</strong>。</p>
<p>        我们<strong>为什么</strong>要构建实时数仓，因为原始的上报<strong>数据量非常大</strong>，一天上报峰值就有上万亿条。而且<strong>上报格式混乱</strong>。<strong>缺乏</strong>内容维度信息、用户画像信息，下游<strong>没办法直接使用</strong>。而我们提供的实时数仓，是根据看点信息流的业务场景，进行了内容维度的关联，用户画像的关联，各种粒度的聚合，下游可以<strong>非常方便的使用实时数据</strong>。</p>
<h1>4、<b>方案选型</b></h1>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/75460ec27ebf4e1449a5.png"/></p>
<p>        那就看下我们多维实时数据分析系统的<strong>方案选型</strong>，选型我们对比了行业内的领先方案，选择了最符合我们业务场景的方案。</p>
<p>        1、第一块是<strong>实时数仓</strong>的选型，我们选择的是业界比较成熟的<strong>Lambda架构</strong>，他的优点是灵活性高、容错性高、成熟度高和迁移成本低；缺点是实时、离线数据用两套代码，可能会存在一个口径修改了，另一个没改的问题，我们每天都有做数据对账的工作，如果有异常会进行告警。</p>
<p>        2、第二块是<strong>实时计算引擎</strong>选型，因为<strong>Flink</strong>设计之初就是为了流处理，SparkStreaming严格来说还是微批处理，Strom用的已经不多了。再看Flink具有Exactly-once的准确性、轻量级Checkpoint容错机制、低延时高吞吐和易用性高的特点，我们选择了Flink作为实时计算引擎。</p>
<p>        3、第三块是<strong>实时存储引擎</strong>，我们的要求就是需要有维度索引、支持高并发、预聚合、高性能实时多维OLAP查询。可以看到，Hbase、Tdsql和ES都不能满足要求，Druid有一个缺陷，它是按照时序划分Segment，无法将同一个内容，存放在同一个Segment上，计算全局TopN只能是近似值，所以我们选择了最近两年大火的MPP数据库引擎<strong>ClickHouse</strong>。</p>
<h1><b>5、设计目标与设计难点</b></h1>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5edc72af5577ced84c38.png"/></p>
<p>        我们多维实时数据分析系统分为三大模块</p>
<p><strong>        1、实时计算引擎</strong></p>
<p><strong>        2、实时存储引擎</strong></p>
<p>        3、App层</p>
<p>        <strong>难点</strong>主要在<strong>前两个模块</strong>：实时计算引擎和实时存储引擎。</p>
<p>        1、<strong>千万级/s</strong>的海量数据如何<strong>实时接入</strong>，并且进行<strong>极低延迟维表关联</strong>。</p>
<p>        2、实时存储引擎如何支持<strong>高并发写入</strong>、<strong>高可用分布式</strong>和<strong>高性能索引</strong>查询，是比较难的。</p>
<p>        这几个模块的具体实现，看一下我们系统的架构设计</p>
<h1>6、<b>架构设计</b></h1>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/120dacc245d92b324843.png"/></p>
<p>        1、<strong>前端</strong>采用的是开源组件Ant Design，利用了Nginx服务器，部署静态页面，并反向代理了浏览器的请求到后台服务器上。</p>
<p>        2、<strong>后台</strong>服务是基于自研的RPC后台服务框架写的，并且会进行一些二级缓存。</p>
<p>        3、<strong>实时数仓</strong>部分，分为了<strong>接入层</strong>、<strong>实时计算层</strong>和<strong>实时数仓存储层</strong>。<strong>接入层</strong>主要是从<strong>千万级/s</strong>的原始消息队列中，<strong>拆分</strong>出不同行为数据的微队列，拿看点的视频来说，拆分过后，数据就只有<strong>百万级/s</strong>了；<strong>实时计算层</strong>主要负责，多行行为流水数据进行<strong>行转列</strong>，<strong>实时关联</strong>用户画像数据和内容维度数据；<strong>实时数仓存储层</strong>主要是设计出符合看点业务的，下游好用的实时消息队列。我们暂时提供了<strong>两个消息队列</strong>，作为实时数仓的两层。一层<strong>DWM</strong>层是<strong>内容ID-用户ID</strong>粒度聚合的，就是一条数据包含内容ID-用户ID还有B侧内容数据、C侧用户数据和用户画像数据；另一层是<strong>DWS</strong>层，是<strong>内容ID</strong>粒度聚合的，一条数据包含内容ID，B侧数据和C侧数据。可以看到内容ID-用户ID粒度的消息队列流量进一步减小到<strong>十万级/s</strong>，内容ID粒度的更是<strong>万级/s</strong>，并且<strong>格式更加清晰</strong>，<strong>维度信息更加丰富</strong>。</p>
<p>        4、实时存储部分分为<strong>实时写入层</strong>、<strong>OLAP存储层</strong>和<strong>后台接口层</strong>。实时写入层主要是负责<strong>Hash路由</strong>将数据写入；OLAP存储层利用MPP存储引擎，设计符合业务的<strong>索引和物化视图</strong>，高效存储海量数据；后台接口层提供高效的多维实时查询接口。</p>
<h1>7、<b>实时计算</b></h1>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/aa80a2ad27e67fd103f1.png"/></p>
<p>        这个系统<strong>最复杂的两块</strong>，<strong>实时计算</strong>和<strong>实时存储</strong>。先介绍实时计算部分：分为<strong>实时关联</strong>和<strong>实时数仓</strong>。</p>
<h2><b>   7.1 实时高性能维表关联</b></h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/37841eaa088683361911.png"/></p>
<p>        实时维表关联这一块<strong>难度在于</strong>。百万级/s的实时数据流，如果直接去关联HBase，1分钟的数据，关联完HBase耗时是小时级的，会导致数据<strong>延迟严重</strong>。</p>
<p>        我们提出了几个<strong>解决方案</strong>，<strong>第一个</strong>是，在Flink实时计算环节，先按照1分钟进行了<strong>窗口聚合</strong>，将窗口内多行行为数据转一<strong>行多列</strong>的数据格式，经过这一步操作，原本<strong>小时级的</strong>关联耗时下降到了十几<strong>分钟</strong>，但是还是不够的。<strong>第二个</strong>是，在访问HBase内容之前设置一层<strong>Redis缓存</strong>，因为1000条数据访问HBase是秒级的，而访问Redis是毫秒级的，访问Redis的速度基本是访问HBase的<strong>1000倍</strong>。为了防止过期的数据浪费缓存，缓存过期时间设置成24小时，同时通过监听写HBase Proxy来保证缓存的一致性。这样将访问时间从十几分钟变成了<strong>秒级</strong>。<strong>第三个</strong>是，上报过程中会上报不少非常规内容ID，这些内容ID在内容HBase中是不存储的，会造成缓存穿透的问题。所以在实时计算的时候，我们直接过滤掉这些内容ID，<strong>防止缓存穿透</strong>，又减少一些时间。<strong>第四个</strong>是，因为设置了定时缓存，会引入一个缓存雪崩的问题。为了<strong>防止雪崩</strong>，我们在实时计算中，进行了<strong>削峰填谷</strong>的操作，错开设置缓存的时间。</p>
<p>        可以看到，<strong>优化前后</strong>，数据量从百亿级减少到了十亿级，耗时从小时级减少到了数十秒，<strong>减少99%</strong>。</p>
<h2><b>   7.2 </b><b>实时数仓建设</b><b>-</b><b>向下游提供服务</b></h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2fd4c689b9376b093839.png"/></p>
<p>        实时数仓的<strong>难度</strong>在于：它处于<strong>比较新</strong>的领域，并且各个公司各个业务<strong>差距比较大</strong>，怎么能设计出方便，好用，<strong>符合看点</strong>业务场景的实时数仓是有难度的。</p>
<p>        先看一下实时数仓<strong>做了什么</strong>，实时数仓对外就是几个<strong>消息队列</strong>，不同的消息队列里面存放的就是<strong>不同聚合粒度</strong>的实时数据，包括内容ID、用户ID、C侧行为数据、B侧内容维度数据和用户画像数据等。</p>
<p>        我们是<strong>怎么搭建</strong>实时数仓的，就是上面介绍的<strong>实时计算引擎的输出</strong>，放到消息队列中保存，可以提供给下游多用户<strong>复用</strong>。</p>
<p>        我们可以看下，在我们建设实时数据仓库前后，开发一个实时应用的<strong>区别</strong>。没有数仓的时候，我们需要消费<strong>千万级/s</strong>的原始队列，进行复杂的数据清洗，然后再进行用户画像关联、内容维度关联，才能拿到符合要求格式的实时数据，<strong>开发和扩展的成本</strong>都会比较高，如果想开发一个新的应用，又要走一遍这个流程。有了数仓之后，如果想开发内容ID粒度的实时应用，就直接申请TPS<strong>万级/s</strong>的DWS层的消息队列。开发成本变<strong>低很多</strong>，资源消耗<strong>小很多</strong>，可扩展性也<strong>强很多</strong>。</p>
<p>        看个实际例子，开发我们系统的<strong>实时数据大屏</strong>，原本需要进行如上所有操作，才能拿到数据。现在只需要消费DWS层消息队列，写<strong>一条Flink SQL</strong>即可，仅消耗<strong>2个cpu</strong>核心，<strong>1G内存</strong>。</p>
<p>        可以看到，以50个消费者为例，建立实时数仓前后，下游开发一个实时应用，可以<strong>减少98%</strong>的资源消耗。包括计算资源，存储资源，人力成本和开发人员学习接入成本等等。并且消费者越多，<strong>节省越多</strong>。就拿Redis存储这一部分来说，一个月就能省下<strong>上百万人民币</strong>。</p>
<h1>8、<b>实时存储</b></h1>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a90b47f6b0d42c9624e9.png"/></p>
<p>              介绍完<strong>实时计算</strong>，再来介绍<strong>实时存储</strong>。</p>
<p>              这块分为三个部分来介绍</p>
<p>              第一是 <strong>分布式-高可用</strong></p>
<p>              第二是 <strong>海量数据-写入</strong></p>
<p>              第三是 <strong>高性能-查询</strong></p>
<h2><b>   8.1 分布式-高可用</b></h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1a1e3e44365f826ece65.png"/></p>
<p>        我们这里听取的是<strong>C</strong><strong>lickhouse官方</strong>的建议，借助ZK实现高可用的方案。数据写入一个分片，仅写入一个副本，然后再写ZK，通过ZK告诉同一个分片的其他副本，其他副本再过来拉取数据，保证数据一致性。</p>
<p>        这里没有选用消息队列进行数据同步，是因为ZK更加轻量级。而且写的时候，任意写一个副本，其它副本都能够通过ZK获得一致的数据。而且就算其它节点第一次来获取数据失败了，后面只要发现它跟ZK上记录的数据不一致，就会再次尝试获取数据，保证一致性。</p>
<h2><b>   8.2 海量数据-写入</b></h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a98208c4dc8622b33107.png"/></p>
<p>        数据写入遇到的<strong>第一个问题</strong>是，海量数据直接写入Clickhouse的话，会导致<strong>ZK的QPS</strong>太高，解决方案是改用<strong>Batch方式写</strong>入。Batch设置多大呢，Batch太小的话缓解不了ZK的压力，Batch也不能太大，不然上游内存压力太大，通过实验，最终我们选用了大小几十万的Batch。</p>
<p>        <strong>第二个问题</strong>是，随着数据量的增长，单QQ看点的视频内容每天可能写入百亿级的数据，默认方案是写一张分布式表，这就会造成<strong>单台机器</strong>出现<strong>磁盘的瓶颈</strong>，尤其是Clickhouse底层运用的是Mergetree，原理类似于HBase、RocketsDb的底层<strong>LSM-Tree</strong>。在合并的过程中会存在<strong>写放大</strong>的问题，<strong>加重磁盘压力</strong>。峰值每分钟几千万条数据，写完耗时几十秒，如果正在做Merge，就会阻塞写入请求，查询也会非常慢。我们做的两个优化方案：一是<strong>对磁盘做Raid</strong>，提升磁盘的IO；二是在写入之前进行分表，直接<strong>分开写入到不同的分片</strong>上，磁盘压力直接变为1/N。</p>
<p>        <strong>第三个问题</strong>是，虽然我们写入按照分片进行了划分，但是这里引入了一个分布式系统常见的问题，就是<strong>局部的Top并非全局Top</strong>的问题。比如同一个内容ID的数据落在了不同的分片上，计算全局Top100阅读的内容ID，有一个内容ID在分片1上是Top100，但是在其它分片上不是Top100，导致汇总的时候，会丢失一部分数据，影响最终结果。我们做的优化是在写入之前加上一层<strong>路由</strong>，将同一个内容ID的记录，全部路由到同一个分片上，解决了该问题。</p>
<p>        介绍完写入，下一步介绍Clickhouse的高性能存储和查询。</p>
<h2><b>   8.3 高性能-存储-查询</b></h2>
<p>        Clickhouse<strong>高性能查询</strong>的一个关键点是<strong>稀疏索引</strong>。稀疏索引这个设计就很有讲究，设计得好可以加速查询，设计不好反而会影响查询效率。我根据我们的业务场景，因为我们的查询大部分都是时间和内容ID相关的，比如说，某个内容，过去N分钟在各个人群表现如何？我按照<strong>日期</strong>，<strong>分钟粒度时间</strong>和<strong>内容ID</strong>建立了稀疏索引。针对某个内容的查询，建立稀疏索引之后，可以<strong>减少99%</strong>的文件扫描。</p>
<p>        还有一个问题就是，我们现在<strong>数据量太大</strong>，<strong>维度太多</strong>。拿QQ看点的视频内容来说，一天流水有上百亿条，有些维度有几百个类别。如果一次性把所有维度进行预聚合，数据量会指数膨胀，查询反而变慢，并且会占用大量内存空间。我们的优化，针对不同的维度，建立对应的<strong>预聚合物化视图</strong>，用空间换时间，这样可以缩短查询的时间。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4d19dcb16390c56812e9.png"/></p>
<p>        分布式表查询还会有一个问题，查询单个内容ID的信息，分布式表会将查询下发到<strong>所有的分片</strong>上，然后再返回查询结果进行汇总。实际上，因为做过路由，一个内容ID只存在于一个分片上，剩下的分片都在<strong>空跑</strong>。针对这类查询，我们的优化是后台按照同样的规则先<strong>进行路由</strong>，直接查询目标分片，这样<strong>减少了N-1/N的负载</strong>，可以<strong>大量缩短查询</strong>时间。而且由于我们是提供的OLAP查询，数据满足最终一致性即可，通过<strong>主从副本读写分离</strong>，可以进一步提升性能。</p>
<p>        我们在后台还做了一个<strong>1分钟的数据缓存</strong>，针对相同条件查询，后台就直接返回了。</p>
<h2><b>   8.4 扩容</b></h2>
<p>        这里再介绍一下我们的扩容的方案，调研了业内的一些常见方案。</p>
<p>        比如HBase，原始数据都存放在HDFS上，扩容只是Region Server扩容，不涉及原始数据的迁移。但是Clickhouse的每个分片数据都是在本地，是一个比较底层存储引擎，不能像HBase那样方便扩容。</p>
<p>        Redis是哈希槽这种类似一致性哈希的方式，是比较经典分布式缓存的方案。Redis slot在Rehash的过程中虽然存在短暂的ask读不可用，但是总体来说迁移是比较方便的，从原h[0]迁移到h[1]，最后再删除h[0]。但是Clickhouse大部分都是OLAP批量查询，不是点查，而且由于列式存储，不支持删除的特性，一致性哈希的方案不是很适合。</p>
<p>        目前扩容的方案是，另外<strong>消费一份数据</strong>，写入新Clickhouse集群，两个集群<strong>一起跑</strong>一段时间，因为实时数据就保存3天，等3天之后，后台服务<strong>直接访问新集群</strong>。</p>
<h1>9、成果</h1>
<p>        看点<strong>实时数据仓库</strong>：DWM层和DWS层，数据延迟1分钟。</p>
<p>        <strong>远见多维</strong><strong>实时数据分析系统</strong>：亚秒级响应多维条件查询请求，在未命中缓存情况下，过去30分钟的查询，99%的请求耗时在1秒内；过去24小时的查询，90%的请求耗时在5秒内，99%的请求耗时在10秒内。</p> 
{% endraw %}
