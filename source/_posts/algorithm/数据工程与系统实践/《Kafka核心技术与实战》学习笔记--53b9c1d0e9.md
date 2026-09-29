---
title: "《Kafka核心技术与实战》学习笔记"
date: 2022-03-19 09:18:26
categories:
  - 算法
  - 数据工程与系统实践
---

{% raw %}

<h2>一、Kafka简介</h2>
<h3>1. 消息引擎系统ABC</h3>
<p>Apache Kafka是一款开源的消息引擎系统，也是一个分布式流处理平台。除此之外，Kafka还能够被用作分布式存储系统（极少）。</p>
<p>A. 常见的两种消息引擎系统传输协议（即用什么方式把消息传输出去）</p>
<ul><li>
<p>点对点模型：也叫消息队列模型。系统A发送的消息只能被系统B接收，其他任何系统都不能读取A发送的消息。</p>
</li>
<li>
<p>发布/订阅模型：与点对点模型不用的是，发布/订阅模型有一个主题(Topic)的概念，可以理解为逻辑语义相近的消息容器。发布/订阅模型的发送方成为发布者(Publisher)，接收方(Subscriber)。和点对点模型不同的是，这个模型可能存在多个发布者向相同的主题发送消息，而订阅者也可能存在多个，它们都能接收到相同主题的消息。</p>
</li>
</ul><p>B. Kafka在设计之初就旨在提供三个方面的特性：</p>
<ul><li>
<p>提供一套API实现生产者和消费者</p>
</li>
</ul><ul><li>
<p>降低网络传输和磁盘存储开销</p>
</li>
</ul><ul><li>
<p>实现高伸缩性架构</p>
</li>
</ul><p>C. 作为流处理平台，Kafka与其他主流大数据流式计算框架相比，优势有两点：</p>
<ul><li>
<p>更容易实现端到端的正确性</p>
</li>
<li>
<p>它自己对于流式计算的定位</p>
</li>
</ul><h3>2. 术语</h3>
<p><strong>Kafka体系架构 = M个producer +N个broker +K个consumer+ZK集群</strong></p>
<ul><li>
<p><strong>producer</strong>：生产者</p>
</li>
</ul><ul><li>
<p><strong>broker</strong>：服务代理节点，Kafka服务实例。</p>
<p>n个组成一个Kafka集群，通常一台机器部署一个Kafka实例，一个实例挂了其他实例仍可以使用，体现了高可用</p>
</li>
</ul><ul><li>
<p><strong>consumer</strong>：消费者</p>
<p>消费topic 的消息， 一个topic 可以让若干个consumer消费，若干个consumer组成一个 consumer group ，一条消息只能被consumer group 中一个consumer消费，若干个partition 被若干个consumer 同时消费，达到消费者高吞吐量</p>
</li>
</ul><ul><li>
<p><strong>topic</strong> ：主题</p>
</li>
</ul><ul><li>
<p><strong>partition</strong>：分区</p>
</li>
</ul><p>      一个topic 可以拥有若干个partition（从 0 开始标识partition ），分布在不同的broker 上， 实现发布与订阅时负载均衡。producer 通过自定义的规则将消息发送到对应topic 下某个partition，以offset标识一条消息在一个partition的唯一性。</p>
<p>      一个partition拥有多个replica，提高容灾能力。replica 包含两种类型：leader 副本（负责读写请求）、follower副本（负责同步leader副本消息，通过副本选举实现故障转移）。</p>
<p>      partition在机器磁盘上以log 体现，采用顺序追加日志的方式添加新消息、实现高吞吐量。</p>
<p>[图片未保存到本地]</p>
<h3>3. Kafka选型</h3>
<table><colgroup><col/><col/><col/></colgroup><thead><tr><th>Kafka类型</th>
<th>特点</th>
<th>场景</th>
</tr></thead><tbody><tr><td>Apache Kafka</td>
<td>最“正宗”的 Kafka。 1. 迭代速度快，社区响应度高，更高的把控度；2. 只提供读写磁盘文件的连接器，与其他外部系统交互时需要自行编写代码实现； 3. 没有没有提供任何监控框架或工具，但是可以借助Kafka manage、kafka eagler等第三方框架进行监控</td>
<td>需要一个消息引擎系统亦或是简单的流处理应用场景，同时需要对系统有较大把控度</td>
</tr><tr><td>Confluent Kafka</td>
<td>Confluent Kafka 提供了一些 Apache Kafka 没有的高级特性，比如跨数据中心备份、Schema 注册中心以及跨数据中心备份和集群监控等。但相关文档资料不全，普及率较低（Schema 注册中心：集中管理 Kafka 消息格式；REST proxy ：支持开放 HTTP 接口的方式访问）</td>
<td>需要用到 Kafka 的一些高级特性</td>
</tr><tr><td>Cloudera/Hortonworks Kafka</td>
<td>集成了目前主流的大数据框架，能够帮助用户实现从分布式存储、集群调度、流处理到机器学习、实时数据库等全方位的数据处理</td>
<td>需要快速地搭建消息引擎系统，或者需要搭建的是多框架构成的数据平台且 Kafka 只是其中一个组件</td>
</tr></tbody></table><h3>4. kafka版本号</h3>
<p>Kafka 版本命名规则正式从 4 位</p>
<p>Kafka 目前总共演进了 7 个大版本，分别是 0.7、0.8、0.9、0.10、0.11、1.0 和 2.0</p>
<p>0.7版本：只提供了最基本的消息队列功能</p>
<p>0.8版本：引入了副本机制，至此Kafka成为了一个真正意义上完备的分布式高可靠消息队列解决方案</p>
<p>0.9.0.0版本：增加了基础的安全认证/权限功能；使用Java重写了新版本消费者API；引入了Kafka Connect组件</p>
<p>0.10.0.0版本：引入Kafka Streams，正式升级成分布式流处理平台</p>
<p>0.11.0.0版本：提供了幂等性Producer API以及事务API；对Kafka消息格式做了重构</p>
<p>1.0和2.0版本：主要还是Kafka Streams的各种改进</p>
<p><br/></p>
<h2>二、Kafka线上集群部署</h2>
<h3>1. 部署方案</h3>
<p>操作系统、磁盘、磁盘容量和带宽</p>
<p><strong>A. 操作系统</strong></p>
<p>kafka支持Linux、Windows 和 macOS的服务端部署，但一般选择Linux作为服务器部署（I/O 模型、数据网络传输效率、社区支持度）</p>
<p>上 Kafka 客户端底层使用了 Java 的 selector，selector 在 Linux 上的实现机制是 epoll，而在 Windows 平台上的实现机制是 select。因此在这一点上将 Kafka 部署在 Linux 上是有优势的，因为能够获得更高效的 I/O 性能。</p>
<p>Kafka 需要在磁盘和网络间进行大量数据传输。Linux 部署 Kafka 能够享受到零拷贝技术（Zero Copy，当数据在磁盘和网络进行传输时避免昂贵的内核态数据拷贝从而实现快速的数据传输）所带来的快速数据传输特性。</p>
<p><strong>B. 磁盘</strong></p>
<ul><li>
<p>机械硬盘：使用的方式多是顺序读写操作，SSD没有太大的性能优势，Kafka 在软件层面提供机制来保证可靠性</p>
</li>
<li>
<p>磁盘阵列（RAID）：提供冗余的磁盘存储空间提供负载均衡</p>
</li>
</ul><p><strong>C. 磁盘容量</strong></p>
<p>新增消息数消息留存时间平均消息大小备份数是否启用压缩</p>
<p><strong>D. 带宽</strong></p>
<ul><li>
<p>使用带宽资源的70%</p>
</li>
<li>
<p>预留2/3带宽资源</p>
</li>
<li>
<p>与其说是带宽资源的规划，其实真正要规划的是所需的 Kafka 服务器的数量</p>
<p>机器数 = 处理数据量/可用资源 * 3 </p>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/6c33d9df17dd48d077ee.jpg"/></p>
<p><br/></p>
<h3>2. 最重要的集群参数配置</h3>
<p><strong>(1) Broker端参数</strong></p>
<ul><li>
<p>与存储信息相关的参数：<code>logdirs</code>和<code>logdir</code></p>
</li>
<li>
<p>与ZooKeeper相关的参数：<code>zookeeper.connect</code>。</p>
</li>
<li>
<p>与Broker连接相关的参数：<code>listeners</code>、<code>advertised.lis- teners</code>和<code>hostname/port</code></p>
</li>
<li>
<p>关于Topic管理的参数：<code>auto.createtopicsenable</code>、<code>unclean.leaderelection.enable</code>和<code>auto.leader.rebal-
anceenable</code></p>
</li>
<li>
<p>关于数据留存的参数：<code>log.retention.{hours minutes ms}</code>、<code>log.retention.bytes</code>和<code>message.maxbytes</code>。</p>
</li>
</ul><p><strong>(2) Topic级别参数</strong></p>
<ul><li>
<p><code>retentionms</code>：规定了该Topic消息被保存的时长</p>
</li>
<li>
<p><code>reten-tionbytes</code>：规定了要为该Topic预留多大的磁盘空间</p>
</li>
<li>
<p><code>maxmessage.bytes</code>：决定了KafkaBroker能够正常接收该Topic的最大消息大小</p>
</li>
</ul><p><strong>(3) JVM参数</strong></p>
<ul><li>
<p>指定堆大小：<code>KAFKA_HEAP_OPTS</code></p>
</li>
<li>
<p>指定GC参数：<code>KAFKA_JVM_PERFORMANCE_OPTS</code>:</p>
</li>
</ul><p><strong>(4) 操作系统参数</strong></p>
<ul><li>
<p>文件描述符限制</p>
</li>
<li>
<p>文件系统类型</p>
</li>
<li>
<p>Swappiness</p>
</li>
<li>
<p>提交时间</p>
</li>
</ul><h2>三、客户端实践与原理解析</h2>
<h3>1. 生产者消息分区机制原理</h3>
<p>Kafka的主题（Topic）是承载真实数据的逻辑容器，主题之下还分为若干个分区，Kafka消息组织方式实际上是三级结构：主题-分区-消息。主题下的每条消息只会在某一个分区中，而不会在多个分区中被保存多份。</p>
<p><strong>(1) 产生原因</strong></p>
<ol><li>
<p>使用分区的作用就是提供负载均衡的能力，对数据进行分区的主要目的就是为了实现系统的高伸缩性（Scalability）。不同的分区能够放在不同的节点的机器上，而数据的读写操作也都是针对分区这个粒度进行的，每个节点的机器都能独立地执行各自分区读写请求。我们还可以通过增加节点来提升整体系统的吞吐量。</p>
</li>
<li>
<p>可以实现业务级别的消息顺序的问题。</p>
</li>
</ol><p><strong>(2) 分区策略</strong></p>
<p>分区策略是指决定生产者将消息发送到那个分区的算法。</p>
<p>Kafka提供了默认的分区策略是 <strong>轮询</strong>，同时kafka也支持用户自己制定。</p>
<p><strong>常见的分区策略：</strong></p>
<ul><li>
<p><strong>轮询</strong>：也称为Round-robin策略，即顺序分配。轮询的优点是有着优秀的负载均衡的表现</p>
</li>
<li>
<p><strong>随机策略</strong>：虽然也是追求负载均衡，但总体表现差于轮询。如果追求数据的均匀分布，推荐使用轮询策略</p>
</li>
<li>
<p><strong>按消息键保序策略</strong>：为每条消息配置一个key，按消息的key来存。</p>
<ul><li>
<p>Kafka允许为每条消息指定一个key。一旦指定了key ，就可以将相同的key存入相同的分区中，而且每个分区下的消息都是有序的。</p>
</li>
<li>
<p>key的作用很大，可以是一个有着明确业务含义的字符串，也可以是用来表征消息的元数据。</p>
</li>
</ul></li>
<li>
<p>其他的分区策略：<strong>基于地理位置的分区</strong>。</p>
</li>
</ul><p><strong>(3) 小结</strong></p>
<p>分区是实现负载均衡，系统伸缩性，进而实现Kafka高吞吐量的重要机制。在搭建时就应当仔细的规划生产者端的分区策略，避免数据倾斜，使得某些分区成为性能瓶颈，这样极易引发下游消费数据的性能下降。</p>
<h3>2. 生产者压缩算法</h3>
<p>压缩秉承了用时间换空间的经典trade-off思想，即用CPU的时间去换取磁盘空间或网络I/O传输量，Kafka的压缩算法也是出于这种目的。</p>
<p><strong>(1) 如何压缩</strong></p>
<p>了解Kafka如何压缩消息，首先要清楚Kafka的消息格式，目前kafka有两大类消息格式，社区称之为V1版本和V2版本。</p>
<p><strong>A：共同点</strong></p>
<ul><li>
<p>Kafka的消息层次分为：消息集合（message set）和消息（message）；一个消息集合中包含若干条日志项（record item），而日志项才是真正封装消息的地方。</p>
</li>
<li>
<p>Kafka底层的消息日志由一系列消息集合日志项组成。Kafka通常不会直接操作具体的一条条消息，他总是在消息集合这个层面上进行写入操作。</p>
</li>
</ul><p><strong>B：不同点：引入V2的目的主要是针对V1版本的一些弊端做了修正</strong></p>
<ul><li>
<p>把消息的公共部分抽取出来放到外层集合里。</p>
<p>如：在V1中每条消息都要执行CRC校验（循环冗余校验），有些情况下消息的CRC值会变，对每条消息都执行CRC校验，不仅浪费空间还耽误CUP时间。</p>
</li>
<li>
<p>报存压缩消息的方法发生了变化</p>
<ul><li>
<p>v1把多条消息进行压缩后在保存到外层消息的消息体字段中</p>
</li>
<li>
<p>v2 对整个消息集合进行压缩，压缩效果好与前者</p>
</li>
</ul></li>
</ul><p><strong>(2) 何时压缩</strong></p>
<p>在kafka中可能发生压缩的地方：<strong>生产者端和Broker端</strong></p>
<p>A：生产者端：配置compression.type参数即表示指定类型的压缩算法。</p>
<p>B：有两种情况会样Broker端也可能进行压缩</p>
<ul><li>
<p>Broker端指定了和Producer端不同的压缩算法，这会导致Broker端接收到生产者发来的压缩消息，Broker端重新解压、在压缩。</p>
</li>
<li>
<p>Broker端发生了消息格式转换，这种转换主要是为了兼容老版本的消费者程序，（v1和v2的差别）。这个过程会涉及消息的解压和重新压缩。这不仅对性能影响很大，还会让Kafka丧失引以为豪的Zero Copy特性。</p>
</li>
</ul><p><strong>(3) 何时解压</strong></p>
<p>通常情况下解压发生在消费者端。</p>
<p>A：这个流程是Producer发送的压缩消息到Broker，Broker原封不动的保存起来，当Consumer程序请求这部分消息时，Broker原样发出去，当下消息到的Consumer端后，由Consumer自行解压。</p>
<p>B：Consume之所以知道这些消息是用何种压缩算法的，是因为Kafka会将启用了哪种压缩算法封装到消息集合中，当Consumer读取到消息集合时，就会知道消息所使用的压缩算法。</p>
<p><strong>(4) 压缩算法对比</strong></p>
<p>[图片未保存到本地]</p>
<p>在Kafka2.1.0版本之前，仅支持GZIP，Snappy和LZ4。2.1.0后还支持Zstandard算法（Facebook开源，能够提供超高压缩比）</p>
<p>A：一个压缩算法的优劣，有两个重要指标：压缩比和压缩/解压缩吞吐量，两者都是越高越好。</p>
<p>B：吞吐量：LZ4&gt;Snappy&gt;zstd和GZIP，压缩比：zstd&gt;LZ4&gt;GZIP&gt;Snappy</p>
<p><strong>(5) 最佳实践</strong></p>
<ul><li>
<p>启用压缩的一个条件是Producer端所在机器CPU资源充裕</p>
</li>
<li>
<p>生产环境网络带宽资源有限</p>
</li>
<li>
<p>尽量不要出现消息格式转换的情况。</p>
</li>
</ul><h3>3. 无消息丢失配置实现</h3>
<p><strong>(1) 什么是不丢失</strong></p>
<p>Kafka只对“已提交”的消息（committed message）做有限度持久化保证。  A：“已提交”的定义：Kafka的若干个（可自定义配置为一个或全部）Broker成功接收到，并写入日志后即为以成功提交。  B：有限度的持久化保证：kafka的消息不丢失的前提是N个Broker中至少有一个存活。</p>
<p><strong>(2) 消息丢失场景</strong></p>
<p>A：生产者丢失消息： （1）：Kafka Producer是异步发送消息，使用producer.send(msg)发送消息，可以立即得到响应，但不能确定是否真的发送成功。 （2）：网络抖动，消息本身不合格都会导致Broker无法正常接收消息 解决：使用带有回调的producer.send(msg，callback)，回调可以准确的告诉我们消息是否真的发送成功。</p>
<p>B：消费者丢失消息： （1）Consumer端的位移数据出现异常，导致消息被略过 解决：先消费消息，在更新位移记录（这个可能会导致重复消费问题） （2）多个Consumer实例同时消费，但部分实例消费失败，原因是每个确认消息是否成功消费，位移数据就已经被更新。 解决：如果是多线程异步处理消费消息，consumer，程序就不要开启自动提交位移，让应用程序手动提交。</p>
<p><strong>(3) 最佳实践</strong></p>
<p>A：使用带回调通知的方法，发送消息</p>
<p>B：Producer端设置相关参数：</p>
<ul><li>
<p>设置acks=all，表示所有副本Broker都要接收到该消息，才算提交成功。</p>
</li>
<li>
<p>设置retries&gt;0，表示Producer能够自动重试消息发送，避免消息丢失。</p>
</li>
</ul><p>C：Broker端设置相关参数：</p>
<ul><li>
<p>设置unclean.leader.election.enable = false，控制Broker有资格竞选分区的leader，禁止落后原Leader的太多Broker参加竞选，避免成为新的Leader，造成消息丢失。</p>
</li>
<li>
<p>设置 replication.factor &gt;=3，表示将消息多备份几份。</p>
</li>
<li>
<p>设置 min.insync.replicas &gt;1，控制消息至少要被写入到多少个副本才算是“已提交”。这个设置成大于1可以提升消息持久性。生产环境不可以设置为默认值1。</p>
</li>
<li>
<p>设置replication.factor = min.insync.replicas + 1， 确保replication.factor&gt;min.insync.replicas，若两者相等，那么只要有一个副本挂机，整个分区都无法正常工作。</p>
</li>
</ul><p>D：Consumer端设置相关参数：</p>
<p>设置enable.auto.commit=false，表示关闭自动提交，使用手动提交位移方式。</p>
<h3>4. Kafka拦截器</h3>
<p><strong>(1) 什么是拦截器</strong></p>
<p>拦截器：允许应用程序在不修改逻辑的情况下，动态地实现一组可插拔的事件处理逻辑链。它能够在主业务操作的前后多个时间点上插入对应的“拦截”逻辑。</p>
<p>Kafka 拦截器分为生产者拦截器和消费者拦截器。</p>
<p>生产者拦截器允许你在发送消息前以及消息提交成功后植入你的拦截器逻辑；而消费者拦截器支持在消费消息前以及提交位移后编写特定逻辑。这两种拦截器都支持链的方式，Kafka 会按照添加顺序依次执行拦截器逻辑。</p>
<p><strong>(2) 典型使用场景</strong></p>
<p>Kafka 拦截器可以应用于包括客户端监控、端到端系统性能检测、消息审计等多种功能在内的场景。</p>
<p>计算消息从 Producer 端到 Consumer 端平均的处理延时</p>
<p><strong>A. 实现生产者拦截器：</strong></p>
<div>
<pre>public class AvgLatencyProducerInterceptor implements ProducerInterceptor&lt;String, String&gt; {
    private Jedis jedis; // 省略Jedis初始化

    @Override
    public ProducerRecord&lt;String, String&gt; onSend(ProducerRecord&lt;String, String&gt; record) {
        //在发送消息前更新总的已发送消息数
        jedis.incr("totalSentMessage");
        return record;
    }

    @Override
    public void onAcknowledgement(RecordMetadata metadata, Exception exception) {
    }

    @Override
    public void close() {
    }

    @Override
    public void configure(Map&lt;java.lang.String, ?&gt; configs) {
    }
}</pre>
</div>
<p><strong>B. 实现消费者拦截器：</strong></p>
<div>
<pre>public class AvgLatencyConsumerInterceptor implements ConsumerInterceptor&lt;String, String&gt; {
    private Jedis jedis; //省略Jedis初始化

    @Override
    public ConsumerRecords&lt;String, String&gt; onConsume(ConsumerRecords&lt;String, String&gt; records) {
        long lantency = 0L;
        //在真正消费一批消息前首先更新它们的总延时
        for (ConsumerRecord&lt;String, String&gt; record : records) {
            lantency += (System.currentTimeMillis() - record.timestamp());
        }
        //累计得到这批消息总的端到端处理延时并更新到Redis中
        jedis.incrBy("totalLatency", lantency);
        long totalLatency = Long.parseLong(jedis.get("totalLatency"));
        long totalSentMsgs = Long.parseLong(jedis.get("totalSentMessage"));
        //总延时和总消息数
        jedis.set("avgLatency", String.valueOf(totalLatency / totalSentMsgs));
        return records;
    }

    @Override
    public void onCommit(Map&lt;TopicPartition, OffsetAndMetadata&gt; offsets) {
    }

    @Override
    public void close() {
    }

    @Override
    public void configure(Map&lt;String, ?&gt; configs) {
    }
}</pre>
</div>
<p> </p>
<h3>5. 生产者管理TCP连接</h3>
<p>Apache Kafka的所有通信都是基于TCP的。</p>
<p><strong>(1) 为什采用TCP</strong></p>
<ul><li>
<p>TCP拥有一些高级功能，如多路复用请求和同时轮询多个连接的能力。</p>
</li>
<li>
<p>很多编程语言的HTTP库功能相对的比较简陋。</p>
</li>
</ul><blockquote>
<p>多路复用请求：multiplexing request，是将两个或多个数据合并到底层—物理连接中的过程。TCP的多路复用请求会在一条物理连接上创建若干个虚拟连接，每个虚拟连接负责流转各自对应的数据流。</p>
<p>严格讲，TCP并不能多路复用，只是提供可靠的消息交付语义保证，如自动重传丢失的报文。</p>
</blockquote>
<p><strong>(2) 何时创建TCP连接</strong></p>
<p>A. 在创建KafkaProducer实例时</p>
<ol><li>
<p>生产者应用会在后台创建并启动一个名为Sender的线程，该Sender线程开始运行时，首先会创建与Broker的连接。</p>
</li>
<li>
<p>此时不知道要连接哪个Broker，kafka会通过METADATA请求获取集群的元数据，连接所有的Broker。</p>
</li>
</ol><p>B. 可能在更新元数据后，或在消息发送时</p>
<p><strong>(3) 何时关闭TCP连接</strong></p>
<p>Producer端关闭TCP连接的方式有两种：用户主动关闭、kafka自动关闭</p>
<ul><li>
<p>用户主动关闭，通过调用producer.close()方关闭，也包括kill -9暴力关闭。</p>
</li>
<li>
<p>Kafka自动关闭，这与Producer端参数<a href="http://connection.max.idles.ms/">connection.max.idles.ms</a>的值有关，默认为9分钟，9分钟内没有任何请求流过，就会被自动关闭（该参数可以调整）</p>
</li>
</ul><p>kafka自动关闭时，TCP连接是在Broker端被关闭的，但这个连接请求是客户端发起的，对TCP而言这是被动的关闭，被动关闭会产生大量的CLOSE_WAIT连接。</p>
<h3>6. Kafka 消息交付可靠性保障</h3>
<p><strong>(1) 消息交付可靠性</strong></p>
<p>常见的可靠性保障有三种：</p>
<ul><li>
<p>最多一次（at most once）:消息可能会丢失，但不会被重复发送</p>
</li>
<li>
<p>至少一次（at least once）:消息不会丢失，但可能会重复发送</p>
</li>
<li>
<p>精确一次（exactly once）:消息不会对丢失，也不会被重复发送</p>
</li>
</ul><p>Kafka默认提供交付可靠性保障是至少一次。</p>
<p>Kafka消息交付可靠性保障以及精确处理一次语义通过两种机制来实现的：幂等性（Idempotence）和事务（Transaction）。</p>
<p><strong>(2) 幂等性（Idempotence）</strong></p>
<p><strong>A. 含义及优点</strong></p>
<p>“幂等”原是数学概念，指某些操作或函数能够被执行多次，但每次得到的结果都不变。</p>
<p>计算机领域的含义：</p>
<ul><li>
<p>在命令式编程语言（如C）中，若一个子程序是幂等的，那它必然不能修改系统状态。无论这个子程序运行多少次，与该子程序的关联的那部分系统保持不变。</p>
</li>
<li>
<p>在函数式编程语言（比如Scala或Haskell）中，很多纯函数（pure function）天然就是幂等的，他们不执行任何的side effect。</p>
</li>
</ul><p>幂等性的优点：最大的优势是可以安全地重试任何冥等性操作，因为他们不会破坏系统状态</p>
<p><strong>B. 幂等性Producer：</strong></p>
<p>开启：设置props.put（“enable.idempotence”，true）或props.put(ProducerConfig.ENABLE_IDEMPOTENC_CONFIG，true)。 </p>
<p>特征：开启后，Kafka自动做消息的重复去重。</p>
<p><strong>实现思路</strong>：用空间换取时间，Broker端多保存一些字段，当Producer发送了具有相同字段值的消息后，Broker就可以知道这些消息重复，就将这些消息丢弃。</p>
<p>作用范围：</p>
<ul><li>
<p>只能保证单分区上幂等性，无法实现多个分区的幂等性。</p>
</li>
<li>
<p>只能实现单会话上的冥等性，当Producer重启后，这种幂等性保证就失效了。</p>
</li>
</ul><p><strong>(3) 事务（Transaction）</strong></p>
<p><strong>A. 事务概念</strong></p>
<ul><li>
<p>事务提供的安全性保障是经典的ACID。原子性(Atomicity)，一致性(Consistency)，隔离性(Isolation)，持久性(Durability)。</p>
</li>
<li>
<p>kafka的事务机制可以保证多条消息原子性地写入到目标分区，同时也能保证Consumer只能看到事务成功提交的消息。</p>
</li>
</ul><p><strong>B. 事务型Producer：</strong></p>
<p>开启：</p>
<ol><li>
<p>设置enable.idempotence = true</p>
</li>
<li>
<p>设置Producer端参数<a href="http://transactional.id/">transactional.id</a>。最好为其设置一个有意义的名字</p>
</li>
<li>
<p>调整Producer代码，显示调用事务API</p>
</li>
<li>
<p>设置Consumer端参数 isolation.level 值：</p>
</li>
</ol><ul><li>
<p>read_uncommitted(默认值，能够读到kafka写入的任何消息)</p>
</li>
<li>
<p>read_committed（Consumer只会读取事务型Producer成功事务写入的消息。）</p>
</li>
</ul><p><strong>特征：</strong></p>
<ol><li>
<p>能够保证将消息原子性地写入到多个分区中。一批消息要么全部成功，要么全部失败。</p>
</li>
<li>
<p>不惧进程重启，Producer重启回来后，kafka依然能保证发送的消息的精确一次处理。</p>
</li>
</ol><p><strong>关键事项：</strong></p>
<ol><li>
<p>幂等性无法实现多个分区以及多会话上的消息无重复，但事务（transaction）或依赖事务型Produce可以做到。</p>
</li>
<li>
<p>开启事务对性能影响很大，在使用时要充分考虑</p>
</li>
</ol><h3>7. 消费者组</h3>
<p>Consumer Group ：Kafka提供的可扩展且具有容错性的消息者机制。</p>
<p><strong>(1) 重要特征</strong></p>
<p>A：组内可以有多个消费者实例（Consumer Instance）。</p>
<p>B：消费者组的唯一标识被称为Group ID，组内的消费者共享这个公共的ID。</p>
<p>C：消费者组订阅主题，主题的每个分区只能被组内的一个消费者消费</p>
<p>D：消费者组机制，同时实现了消息队列模型和发布/订阅模型。</p>
<p><strong>(2) 重要问题</strong></p>
<p><strong>A：消费组中的实例与分区的关系</strong></p>
<p>消费者组中的实例个数，最好与订阅主题的分区数相同，否则多出的实例只会被闲置。一个分区只能被一个消费者实例订阅。</p>
<p><strong>B：消费者组的位移管理方式</strong></p>
<ul><li>
<p>对于Consumer Group而言，位移是一组KV对，Key是分区，V对应Consumer消费该分区的最新位移。</p>
</li>
<li>
<p>Kafka的老版本消费者组的位移保存在Zookeeper中，好处是Kafka减少了Kafka Broker端状态保存开销。但ZK是一个分布式的协调框架，不适合进行频繁的写更新，这种大吞吐量的写操作极大的拖慢了Zookeeper集群的性能。</p>
</li>
<li>
<p>Kafka的新版本采用了将位移保存在Kafka内部主题的方法。</p>
</li>
</ul><p><strong>C：消费者组的重平衡</strong></p>
<p>重平衡：本质上是一种协议，规定了消费者组下的每个消费者如何达成一致，来分配订阅topic下的每个分区。</p>
<p><strong>触发条件：</strong></p>
<ol><li>
<p>组成员数发生变更</p>
</li>
<li>
<p>订阅主题数发生变更</p>
</li>
<li>
<p>定阅主题分区数发生变更</p>
</li>
</ol><p>影响：Rebalance 的设计是要求所有consumer实例共同参与，全部重新分配所有用分区。并且Rebalance的过程比较缓慢，这个过程消息消费会中止。</p>
<h3>8. 位移主题</h3>
<p><strong>(1) 产生原因</strong></p>
<p>A ：老版本的Kafka会把位移信息保存在Zk中，当Consumer重启后，自动从Zk中读取位移信息。这种设计使Kafka Broker不需要保存位移数据，可减少Broker端需要持有的状态空间，有利于实现高伸缩性。</p>
<p>B ：zk不适用于高频的写操作，在新版本中将消费者的位移数据作为一条条普通的Kafka消息，提交至内部主题（_consumer_offsets）中保存。实现高持久性和高频写操作。</p>
<p><strong>(2) 特点</strong></p>
<p>A ：位移主题是一个普通主题，同样可以被手动创建，修改，删除。。</p>
<p>B ：位移主题的消息格式是kafka定义的，不可以被手动修改，若修改格式不正确，kafka将会崩溃。</p>
<p>C ：位移主题保存了三部分内容：Group ID，主题名，分区号。</p>
<p><strong>(3) 创建</strong></p>
<p>A ：当Kafka集群中的第一个Consumer程序启动时，Kafka会自动创建位移主题。也可以手动创建</p>
<p>B ：分区数依赖于Broker端的offsets.topic.num.partitions的取值，默认为50</p>
<p>C ：副本数依赖于Broker端的offsets.topic.replication.factor的取值，默认为3</p>
<p><strong>(4) 使用</strong></p>
<p>A ：当Kafka提交位移消息时会使用这个主题</p>
<p>B ：位移提交得分方式有两种:手动和自动提交位移。</p>
<p>C ：推荐使用手动提交位移，自动提交位移会存在问题：只有consumer一直启动设置，他就会无限期地向主题写入消息。</p>
<p><strong>(5) 清理</strong></p>
<p>A ：Kafka使用Compact策略来删除位移主题中的过期消息，避免位移主题无限膨胀。</p>
<p>B ：kafka提供专门的后台线程定期巡检待compcat的主题，查看是否存在满足条件的可删除数据。</p>
<p><strong>(6) 注意事项</strong></p>
<p>A ：建议不要修改默认分区数，在kafka中有些许功能写死的是50个分区</p>
<p>B ：建议不要使用自动提交模式，采用手动提交，避免消费者无限制的写入消息。</p>
<p>C ：后台定期巡检线程叫Log Cleaner，若线上遇到位移主题无限膨胀占用过多磁盘，应该检查此线程的工作状态。</p>
<h3>9. 消费者组的重平衡</h3>
<p><strong>(1) 什么是重平衡</strong></p>
<p>A ：让一个Consumer Group下所有的consumer实例就如何消费订阅主题的所有分区达成共识的过程。</p>
<p>B ：在重平衡过程中，所有Consumer实例共同参与，在协调者组件的帮助下，完成订阅分区的分配。</p>
<p>C ：整个过程中，所有实例都不能消费任何消息，因此对Consumer的TPS影响很大</p>
<p><strong>(2) 为什要避免重平衡</strong></p>
<p>A ：Rebalance影响Consumer端的TPS，因为重平衡过程中消费者不能消费消息</p>
<p>B ：Rebalance很慢，如果有数百个消费者实例，整个过程耗时可能达到几个小时</p>
<p>C ：Rebalance效率低，这个过程是全员参与，通常不考虑局部性原理，但局部性原理对系统性能提升特别重要。</p>
<p>D ：真实的业务场景中，很多Rebalance都是计划外或是不必要的。</p>
<p><strong>(3) 何时会触发重平衡</strong></p>
<p>A ：组成员数量发生变化</p>
<p>B ：订阅主题数量发生变化</p>
<p>C ：订阅主题分区数发生变化</p>
<p><strong>(4) 要避免哪些重平衡</strong></p>
<p>最常见的是消费者数发生变化触发的重平衡，其他的重平衡是不可避免的，但消费者数量变化是可避免的</p>
<p>A ：Consumer实例增加</p>
<p>当启动一个配置相同的<a href="http://group.id/">group.id</a>值的consumer程序时，就是向这个组中增加一个消费者实例，这中情况一般是我们为了提升消费者端的TPS，是计划内的，所以也不用避免。</p>
<p>B ：Consumer实例减少</p>
<p>按计划的减少消费者实例，同样不用避免，而计划外的减少触发的重平衡才是要关注的。</p>
<p><strong>(5) 如何避免重平衡</strong></p>
<p>在某些情况下，Consumer实例会被Coordinateor错误地认为“已停止”，进而被踢出Group。这种情况导致的重平衡是需要避免的。</p>
<p><strong>A ：Consumer实例不能及时的发送心跳请求</strong></p>
<p>当消费者组完成重平衡后，每个Consumer实例都会定期地向Coordinator发送心跳请求，如这个心跳请求没有被及时发送，Coordinator就会认为该Consumer已经掉线，将其从组中移除，并开启新一轮重平衡。</p>
<p><strong>解决：Consumer端参数设置优化</strong></p>
<ul><li>
<p><a href="http://session.timeout.ms/">Session.timeout.ms</a>：默认为10秒，表示10秒内Coordinator没有收到Group下某个Consumer实例的心跳，就认为实例下线。这个可以适当的增大</p>
</li>
<li>
<p><a href="http://heartbeat.interval.ms/">heartbeat.interval.ms</a>：控制发送心跳请求的频率，频繁的发送心跳请求会额外消耗带库资源</p>
</li>
<li>
<p><a href="http://max.poll.interval.ms/">max.poll.interval.ms</a>：限定Consumer端应用程序两次调用poll方法的最大时间间隔。默认值是5分钟，表示如果Consumer程序在5分钟之内无法消费完poll方法返回的消息，那么consumer会主动的发起“离开组”的请求，</p>
</li>
</ul><p>建议：<a href="http://session.timeout.ms/">session.timeout.ms</a>=6s <a href="http://heartbeat.interval.ms/">Heartbeat.interval.ms</a>=2s</p>
<p>保证Consumer实例在判定为“dead”之前，能够发送至少3轮的心跳请求，即<a href="http://session.timeout.ms/">session.timeout.ms</a> &gt;=3 * <a href="http://heartbeat.interval.ms/">heartbeat.interval.ms</a>。</p>
<p><strong>B ：Consumer消费时间过长</strong></p>
<p>消费者端处理了一个很重的消费逻辑，耗时较长，导致Consumer端应用程序两次调用poll方法的时间超出设置的最大时间间隔。</p>
<p><strong>解决：将<a href="http://max.poll.interval.ms/">max.poll.interval.ms</a>参数设置较大一些；优化消费者端业务逻辑，压缩消费耗时</strong></p>
<p><strong>C ：GC影响</strong></p>
<p>Consumer端的GC表现也会导致频繁的重平衡，频繁的Ful GC会导致长时间的断顿。</p>
<p><strong>解决：JVM调优。</strong></p>
<h3>10. 位移提交</h3>
<p><strong>(1) 概念</strong></p>
<p><strong>概念区分</strong></p>
<ul><li>
<p>Consumer端的位移概念和消息分区的位移概念不是一回事。</p>
</li>
<li>
<p>Consumer的消费位移，记录的是Consumer要消费的下一条消息的位移。</p>
</li>
</ul><p><strong>提交位移</strong></p>
<ul><li>
<p>Consumer 要向Kafka汇报自己的位移数据，这个汇报过程被称为提交位移（Committing Offsets）。</p>
</li>
<li>
<p>Consumer需要为分配给它的每个分区提交各自的位移数据。</p>
</li>
</ul><p><strong>(2) 作用及特点</strong></p>
<p><strong>提交位移的作用：</strong></p>
<p>提交位移主要是为了表征Consumer的消费进度，这样当Consumer发生故障重启后，能够从kafka中读取之前提交的位移值，从相应的位置继续消费，避免从头在消费一遍。</p>
<p><strong>位移提交的特点：</strong>位移提交的语义保障是由你来负责的，Kafka只会“无脑”地接受你提交的位移。位移提交错误，就会消息消费错误。</p>
<p><strong>(2) 位移提交方式</strong></p>
<p>从用户的角度讲，位移提交分为自动提交和手动提交；从Consumer端的角度而言，位移提交分为同步提交和异步提交。</p>
<ul><li>
<p><strong>自动提交</strong>：由Kafka consumer在后台默默的执行提交位移，用户不用管。开启简单，使用方便，但可能会出现重复消费。</p>
</li>
<li>
<p><strong>手动提交</strong>：好处在更加灵活，完全能够把控位移提交的时机和频率。</p>
<ul><li>
<p>同步提交：在调用commitSync()时，Consumer程序会处于阻塞状态，直到远端Broker返回提交结果，这个状态才会结束。对TPS影响显著</p>
</li>
<li>
<p>异步提交：在调用commitAsync()时，会立即给响应，但是出问题了它不会自动重试。</p>
</li>
</ul><p>手动提交最好是同步和异步结合使用，正常用异步提交，如果异步提交失败，用同步提交方式补偿提交。</p>
</li>
</ul><ul><li>
<p>批次提交：对于一次要处理很多消费的Consumer而言，将一个大事务分割成若干个小事务分别提交。这可以有效减少错误恢复的时间，避免大批量的消息重新消费。</p>
</li>
</ul><p>更精细化的位移管理：使用commitSync（Map&lt;TopicPartition，Offset&gt;）和commitAsync(Map&lt;TopicPartition，OffsetAndMetadata&gt;)。</p>
<h3>11. CommitFailedException异常</h3>
<p>A ：定义</p>
<p>所谓CommitFailedException，是指Consumer客户端在提交位移时出现了错误或异常，并且并不可恢复的严重异常。</p>
<p><strong>B ：产生原因</strong></p>
<ul><li>
<p>消费者端处理的总时间超过预设的<a href="http://max.poll.interval.ms/">max.poll.interval.ms</a>参数值</p>
</li>
<li>
<p>出现一个Standalone Consumerd的独立消费者，配置的<a href="http://group.id/">group.id</a>重名冲突。</p>
</li>
</ul><p><strong>C ：解决方案</strong></p>
<ul><li>
<p>减少单条消息处理的时间</p>
</li>
</ul><ul><li>
<p>增加Consumer端允许下游系统消费一批消息的最大时长</p>
</li>
</ul><ul><li>
<p>减少下游系统一次性消费的消息总数</p>
</li>
</ul><ul><li>
<p>下游使用多线程加速消费</p>
</li>
</ul><h3>12. 多线程开发消费者实例</h3>
<p><strong>(1) Kafka Java Consumer 单线程设计原理</strong></p>
<p>在Kafka从0.10.1.0版本开始，KafkaConsumer就变成双线程设计即：用户主线程和心跳线程。</p>
<ul><li>
<p>主线程是指启动Consumer应用程序main方法的那个线程，而新引入的心跳线程只负责定期给对应的Broker机器发送心跳请求，以标识消费者应用的存活性。</p>
</li>
<li>
<p>老版本中有Scala Consumer的API，是多线程架构的，每个Consumer实例在内部为所有订阅的主题分区创建对应消息获取线程，也称为Fetcher线程。老版本Consumer同时也是阻塞式的（blocking），Consumer实例启动后，内部会创建很多阻塞式的消息迭代器。</p>
</li>
<li>
<p>在很多场景下，Consumer端是有非阻塞需求的，如流处理应用中执行过滤（filter），连接（join），分组（group by）等操作时就不能是阻塞式的。</p>
</li>
</ul><p>所以，新版本Consumer设计了单线程+轮询的机制。这种设计能够较好的实现非阻塞式的消息获取。</p>
<p>单线程设计优点： （1）单线程可以较好的实现如在流处理应用中执行过滤（filter），连接（join）,分组（group by）等操作。 （2）单线程能够简化Consumer端设计。Consumer端获取到消息后，处理消息的逻辑是否采用多线程，由自己决定。 （3）单线程设计在很多种编程中都比较易于实现，编译社区移植。</p>
<p><strong>(2) 多线程方案</strong></p>
<p>KafkaConsumer类不是线程安全的（thread-safe）。所有的网络I/O处理都是发生在用户主线程中，所以不能在多线程中共享同一个KafkaConsumer实例，否则程序会抛ConcurrentModificationException异常。</p>
<table><thead><tr><th>方案</th>
<th>描述</th>
<th>优点</th>
<th>缺点</th>
</tr></thead><tbody><tr><td>方案一</td>
<td>消费者程序启动多个线程，每个线程维护专属的KafkaConsumer实例，负责完整的消息获取，消息处理流程。</td>
<td>方便实现，速度快，无线程间交互开销，易于维护分区的消息顺序</td>
<td>占用更多的系统资源，线程数受限于主题分区数，扩展性差。线程自己处理消息容易超时，进而引发Rebalance</td>
</tr><tr><td>方案二</td>
<td>消费者程序使用单或多线程获取消息，同时创建多个消费线程执行消息处理逻辑。获取消息的线程可以是多个，每个线程维护专属的KafkaConsumer实例，处理消息则交由特定的线程池来做。</td>
<td>可独立扩展消费获取线程数和worker线程数，伸缩性好</td>
<td>难以维护分区内的消息消费顺序，处理链路拉长，不易于位移提交管理，实现难度高。</td>
</tr></tbody></table><h3>13. 消费者管理TCP连接</h3>
<p><strong>(1) 何时创建</strong></p>
<p>A ：消费者和生产者不同，在创建KafkaConsumer实例时不会创建任何TCP连接。</p>
<p>原因：是因为生产者入口类KafkaProducer在构建实例时，会在后台启动一个Sender线程，这个线程是负责Socket连接创建的。</p>
<p>B ：TCP连接是在调用KafkaConsumer.poll方法时被创建。在poll方法内部有3个时机创建TCP连接</p>
<ul><li>
<p><strong>发起findCoordinator请求时创建</strong></p>
<p>Coordinator（协调者）消费者端主键，驻留在Broker端的内存中，负责消费者组的组成员管理和各个消费者的位移提交管理。 当消费者程序首次启动调用poll方法时，它需要向Kafka集群发送一个名为FindCoordinator的请求，确认哪个Broker是管理它的协调者。</p>
</li>
</ul><ul><li>
<p><strong>连接协调者时</strong></p>
<p>Broker处理了消费者发来的FindCoordinator请求后，返回响应显式的告诉消费者哪个Broker是真正的协调者。 当消费者知晓真正的协调者后，会创建连向该Broker的socket连接。 只有成功连入协调者，协调者才能开启正常的组协调操作。</p>
</li>
</ul><ul><li>
<p><strong>消费数据时</strong></p>
<p>消费者会为每个要消费的分区创建与该分区领导者副本所在的Broker连接的TCP.</p>
</li>
</ul><p><strong>消费者程序会创建3类TCP连接：</strong></p>
<ul><li>
<p>第一类：确定协调者和获取集群元数据</p>
</li>
<li>
<p>第二类：连接协调者，令其执行组成员管理操作</p>
</li>
<li>
<p>第三类：执行实际的消息获取</p>
</li>
</ul><p><strong>(2) 何时关闭</strong></p>
<p>和生产者相似，消费者关闭Socket也分为主动关闭和Kafka自动关闭。</p>
<ul><li>
<p>主动关闭指通过KafkaConsumer.close()方法，或者执行kill命令，显示地调用消费者API的方法去关闭消费者。</p>
</li>
<li>
<p>自动关闭指消费者端参数<a href="http://connection.max.idle.ms/">connection.max.idle.ms</a>控制的，默认为9分钟，即如果某个socket连接上连续9分钟都没有任何请求通过，那么消费者会强行杀死这个连接。</p>
</li>
</ul><p>若消费者程序中使用了循环的方式来调用poll方法消息消息，以上的请求都会被定期的发送到Broker，所以这些socket连接上总是能保证有请求在发送，从而实现“长连接”的效果。</p>
<p>当第三类TCP连接成功创建后，消费者程序就会废弃第一类TCP连接，之后在定期请求元数据时，会改为使用第三类TCP连接。对于一个运行了一段时间的消费者程序来讲，只会有后面两种的TCP连接。</p>
<h3>14. 消费者组消费进度监控</h3>
<p><strong>(1) 为什么要监控</strong></p>
<p>A ：对于Kafka消费者，最重要的事情就是监控它们的消费进度（消费的滞后程度）常称为：Consumer Lag</p>
<p>B ：Lag的单位是消息数，他直接反映了一个消费者的运行情况。一个正常的消费者的Lag应当很小，设置为0。这表明消费者能够及时地消费生产者生产出来的消息。反之，一个消费者Lag值很大的话表明它无法跟上生产者的速度。</p>
<p>C ：如果消费者速度无法匹及生产者的数据，极有可能导致它消费的数据已经不在操作系统的页缓存中了，那些数据就失去了享有Zero Copy技术的条件，不得不从磁盘中读取，进一步拉大了与生产者的差距。并且会越来大。</p>
<p>所以，在实际业务场景中必须时刻关注消费者的消费进度。一旦出现Lag逐步增加的趋势，就要立即定位问题，及时处理。</p>
<p><strong>(2) 如何监控</strong></p>
<ul><li>
<p>使用Kafka自带的命令行工具kafka-consumer-groups脚本</p>
</li>
<li>
<p>使用Kafka Java Conssumer API编程</p>
</li>
<li>
<p>使用Kafka自带的JMX监控指标</p>
</li>
</ul><p><strong>(3) 方法分析</strong></p>
<p><strong>A ：Kafka自带命令</strong></p>
<ul><li>
<p> kafka-consumer-groups脚本是kafka为我们提供的最直接的监控消费者消费进度工具。</p>
</li>
<li>
<p> 使用命令：</p>
</li>
</ul><div>
<pre>$ bin/kafka-consumer-groups.sh --bootstrap-server &lt;Kafka broker连接信息 &gt; --describe --group &lt;group 名称 &gt;</pre>
</div>
<p> &lt;Kafka broker 连接信息 &gt;：主机：端口</p>
<p>&lt;group 名称 &gt; ：要监控的消费组的 <a href="http://group.id/">group.id</a>值</p>
<p>[图片未保存到本地]</p>
<p>展示的信息：主题，分区，该消费者组最新消费消息的位移值（CURRENT-OFFSET值），每个分区当前最新生产的消息的位移值（LOG-END-OFFSET）,LAG（前两者的差值），消费者实例ID，消费者连接Broker的主机名以及消费者的CLENT-ID信息。</p>
<p><strong>B ：Kafka Java Consumer API</strong></p>
<ol><li>
<p>首先获取给定的消费者组的最新消费消息的位移</p>
</li>
<li>
<p>再获取订阅分区的最新消息位移</p>
</li>
<li>
<p>最后执行相应的减法操作，获取Lag值并封装进一个Map对象。</p>
</li>
</ol><p><strong>C ：Kafka JMX监控指标</strong></p>
<p>使用Kafka默认提供 的JMX监控指标来监控消费者的Lag值。</p>
<ul><li>
<p>Kafka消费者提供了一个名为Kafka.consumer:type=consumer-fetch-manager-metrics，client-id=”{client-id}”的JMX指标。</p>
</li>
<li>
<p>有两个重要的属性：records-lag-max 和 records-lead-min 分别表示消费者在测试窗口时间内曾经达到的最大的Lag值和最小的Lead值。</p>
</li>
<li>
<p>Lead值是指消费者最新消费消息的位移和分区当前第一条消息的位移的差值。即：Lag越大，Lead就越小。</p>
</li>
</ul><p><br/></p>
<h2>四、深入Kafka内核</h2>
<h3>1. Kafka副本机制</h3>
<p><strong>(1) 概念</strong></p>
<p><strong>A. 副本机制：</strong></p>
<p>副本机制（Replication）：也称为备份机制，通常是指分布式在多台网络互连的机器上保存有相同的数据拷贝。</p>
<p>好处：提供数据冗余、提供高伸缩性、改善数据局部性（将数据放入与用户地理位置相近的地方）。</p>
<p>Kafka的副本机制，只实现了提供数据冗余的价值。</p>
<p><strong>B. 副本</strong></p>
<p>Kafka有主题的概念，每个主题又分为若干个分区。副本的概念是在分区层级下定义的，每个分区配置有若干个副本。</p>
<p>Kafka的副本（Replica），本质是一个只能追加写消息的提交日志。</p>
<p>根据Kafka副本机制的定义，同一个分区下的所有副本保存有相同的消息序列，这些副本分散保存在不同的Broker上，从而能够一定程度上避免部分Broker宕机带来的数据不可用。</p>
<p><strong>(2) 副本角色</strong></p>
<p>A ：为解决分区下多个副本的内容一致性问题，常用方案就是采用基于领导者的副本机制。</p>
<p>B ：在kafka中，副本分两类：领导者副本和追随者副本。每个分区在创建时都选举一个副本，称为领导者副本，其余的副本自动成为追随者副本。</p>
<p>C ：Kafka的副本机制比其他分布式系统严格。Kafka的追随者副本不对外提供服务。所有的请求都要由领导者副本处理。追随者副本唯一的任务就是从领导者副本异步拉取消息，并写入到自己的提交日志中，从而实现与领导者副本的同步。</p>
<p>Kafka的追随者副本不对外提供服务的原因：</p>
<ul><li>
<p>方便实现Read-your-writes（当使用生产者 API 向 Kafka 成功写入消息后，马上使用消费者 API 去读取刚才生产的消息）；</p>
</li>
<li>
<p>方便实现单调读（对于一个消费者用户而言，在多次消费消息时，不会看到某条消息一会儿存在一会儿不存在）</p>
</li>
</ul><p>D ：当领导者副本所在Broker宕机了，Kafka依托于Zookeeper提供的监控功能能够实时感知到，并立即开启新一轮的领导者选举，从追随者副本中选一个新的领导者。当老的Leader副本重启回来后，只能作为追随者副本加入到集群中。</p>
<p>基于领导者（Leader-based）的副本机制：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/abaeec8326b0118c037b.jpg"/></p>
<p><br/></p>
<p><strong>(3) Kafka副本机制的优点</strong></p>
<p><strong>A ：方便实现“Read-your-writes”</strong></p>
<ul><li>
<p>Read-your-writes：当使用生产者API向Kafka成功写入消息后，马上使用消息者API去读取刚才生产的消息。</p>
</li>
<li>
<p>如果允许追随者副本对外提供服务，由于副本同步是异步的，就可能因为数据同步时间差，从而使客户端看不到最新写入的消息。 </p>
</li>
</ul><p><strong>B ：方便实现单调读（Monotonic Reads）</strong></p>
<ul><li>
<p>单调读：对于一个消费者用户而言，在多处消息消息时，他不会看到某条消息一会存在，一会不存在。</p>
</li>
<li>
<p>如果允许追随者副本提供读服务，由于消息是异步的，则多个追随者副本的状态可能不一致。若客户端每次命中的副本不同，就可能出现一条消息一会看到，一会看不到。</p>
</li>
</ul><p><strong>(4) In-sync Replicas（ISR）同步副本</strong></p>
<p>A ：追随者副本定期的异步拉取领导者副本中的数据，这存在不能和Leader实时同步的风险。</p>
<p>B ：Kafka引入了In-sync Replicas。ISR中的副本都是于Leader同步的副本，相反，不在ISR中的追随者副本就是被认为是与Leader不同步的。</p>
<p>C ：Leader 副本天然就在ISR中，即ISR不只是追随者副本集合，他必然包括Leader副本。甚至某些情况下，ISR只有Leade这一个副本。</p>
<p>D ：follower副本是否与leader同步的判断标准取决于Broker端参数 <a href="http://replica.lag.time.max.ms/">replica.lag.time.max.ms</a>参数值。默认为10秒，只要一个Follower副本落后Leader副本的时间不连续超过10秒，那么Kafka就认为该Follower副本与leader是同步的，即使此时Follower副本中保存的消息明显小于Leader副本中的消息。</p>
<p>E ：如果同步过程持续慢于Leader副本消息的写入速度，那么<a href="http://replica.lag.time.max.ms/">replica.lag.time.max.ms</a>时间后，此Follower副本就会被认为是与Leader副本不同步的，因此不能再放入ISR中。此时，kafka会自动收缩ISR的进度，将该副本“踢出”ISR。ISR是一个动态调整的集合，而非静态不变的。</p>
<p><strong>(5) Unclean 领导者选举（Unclean Leader Election）</strong></p>
<p> A ：ISR是可以动态调整的，所以会出现ISR为空的情况，由于Leader副本天然就在ISR中，如果ISR为空了，这说明Leader副本也挂掉了，Kafka需要重新选举一个新的Leader。</p>
<p> B ：Kafka把所有不在ISR中的存活副本都会称为非同步副本。通常，非同步副本落后Leader太多，如果让这些副本做为新的Leader，就可能出现数据的丢失。在kafka中，选举这种副本的过程称为Unclean领导者选举。</p>
<p> C ：Broker端参数unclean.leader.election.enable 控制是否允许Unclean领导者选举。开启Unclean领导者选举可能会造成数据丢失，但它使得分区Leader副本一直存在，不至于停止对外提供服务，因此提升了高可用性。禁止Unclean领导者选举的好处是在于维护了数据的一致性，避免了消息丢失，但牺牲了高可用性。</p>
<h3>2. 请求处理流程解析</h3>
<p>Apache Kafka 自己定义了组请求协议，用于实现各种交互操作。常见有：</p>
<ul><li>
<p>PRODUCE 请求：用于生产消息</p>
</li>
<li>
<p>FETCH请求：用于消费消息</p>
</li>
<li>
<p>METADATA请求：用于请求Kafka集群元数据信息</p>
</li>
</ul><p>Kafka定义了很多类似的请求格式，所有的请求都是通过TCP网络以Socket的方式进行通讯的。</p>
<p><strong>(1) Broker端的请求处理流程</strong></p>
<p>A ：常用请求处理方案</p>
<ul><li>
<p>顺序处理请求：实现方法简答，但吞吐量太差是致命缺陷。每个请求都必须等待前一个请求处理完毕才能得到处理。适用于请求发送非常不频繁的系统。</p>
</li>
<li>
<p>每个请求使用单独线程处理：完全异步的，每个请求的处理都创建单独线程处理，但缺陷明显，为每个请求都创建线程开销极大，某些场景甚至会压垮整个服务。</p>
</li>
</ul><p>B ：Kafka的方案：使用Reactor模式</p>
<ul><li>
<p>Reactor模式是JUC包作者的作品</p>
</li>
<li>
<p>Reactor模式是事件驱动架构的一种实现方式，特别适应用于处理多个客户端并发向服务端发送请求的场景。</p>
</li>
</ul><p><strong>(2) Kafka的请求处理方式</strong></p>
<p>A ：Reactor模式中，多个客户端发送请求到Reactor，Reactor中的请求分发线程Dispatcher会将不同的请求下发到多个工作线程</p>
<p>Acceptor线程只用于请求分发，不涉及具体逻辑处理，因此有很高的吞吐量。而工作线程可以根据实际业务处理需要任意增减，从而动态调节系统负载能力。</p>
<p>B ：kakfa中，Broker端有个SocketServer组件，类似于Reactor模式中的Dispatcher，他也有对应的Acceptor线程和一个工作线程池，在kafka中，被称为网络线程池</p>
<p>Broker端参数num.network.threads，用于调整该网络线程池的线程数，默认为4，表示每台Broker启动时，会创建3个网络线程，专门处理客户端发送的请求。</p>
<p>C ：Acceptor线程采用轮询的方式将入站请求公平的发送到所有网络线程中。</p>
<p>D ：当网络线程接收到请求后，Kafka在这个环节又做了一层异步线程池的处理</p>
<ul><li>
<p>当网络线程拿到请求后，不是自己处理，而是将请求放入到一个共享请求队列中。</p>
</li>
<li>
<p>Broker端有个IO线程池，负责从该队列中取出请求，执行真正的处理。如果是PRODUCE生产请求，则将消息写入到底层的磁盘日志中；如果是FETCH请求，则从磁盘或页缓存中读取消息。</p>
</li>
</ul><p>E ：IO线程池中的线程是执行请求逻辑的线程。Broker端参数<a href="http://num.io/">num.io</a>.threads控制了这个线程数，默认为8，表示每台Broker启动后自动创建8个IO线程处理请求。</p>
<p>F ：请求队列是所有网络线程共享的，而响应队列则是每个网络线程专属的。原因在于Dispatcher只是用于请求分发而不负责响应回传，因此只能让每个网络线程自己发送Repsone给客户端，所有这些Response没必要放在一个公共的地方。</p>
<p>G ：Purgatory组件，专门用来缓存延时请求（Delayed Requset）。</p>
<p>如设置了acks=all的PRODUCE请求，该请求要必须等待ISR中所有副本都接收了消息后才能返回，此时处理该请求的IO线程就必须瞪大其他Broker的写入结果。当请求不能立即处理时，他就会暂存在Purgatory中。待满足了完成条件，IO线程会继续处理该请求，并将Response放入到对应的网络线程的响应队列中</p>
<p><strong>(3) Kafka对请求的处理特点</strong></p>
<ul><li>
<p>Kafka Broker对所有的请求都是一视同仁的</p>
</li>
<li>
<p>这些请求根据功能，可分为不同的请求类型。从业务的权重角度来讲，是有高低之分的，如控制类请求可以影响数据类请求。</p>
</li>
<li>
<p>无原则的平等，会造成混乱</p>
</li>
</ul><p>社区采取的方案是，同时创建两套完全样的组件，实现两类请求的分离。</p>
<p><br/></p>
<h3>3. 重平衡流程解析</h3>
<p><strong>(1) 重平衡的通知</strong></p>
<p>A ：重平衡过程通过消息者端的心跳线程（Heartbeat Thread）通知到其他消费者实例。</p>
<p>B ：Kafka Java消费者需要定期地发送心跳请求到Broker端的协调者，以表明它还存活着。</p>
<ul><li>
<p>在kafka 0.10.1.0版本之前，发送心跳请求和消息处理逻辑是在消费者主线程完成的，也就是代码中调用KafkaConsumer.poll方法的那个线程。一旦消息处理消耗了过长的时间，心跳请求将无法及时发到协调者那里，导致协调者错判消费者已死。</p>
</li>
<li>
<p>在此版本后，kafka社区引入了单独的心跳线程来专门执行心跳请求发送，避免这个问题。</p>
</li>
</ul><p>C ：重平衡的通知机制是通过心跳线程来完成的，当协调者决定开启新一轮重平衡后，他会将“REBALANCE_IN_PROGRESS”封装进心跳请求的响应中，发还给消费者实例。当消费者实例发现心跳响应中包含了”REBALANCE_IN_PROGRESS”，就能立即知道重平衡开始了。</p>
<p>D ：消费者端的参数 <a href="http://heartbeat.interval.ms/">heartbeat.interval.ms</a>的真实用途是控制重平衡通知的频率。</p>
<p><strong>(2) 消费者组状态机</strong></p>
<p>Kafka设计了一套消费者组状态机（State Machine），帮助协调者完成整个重平衡流程。</p>
<p>A ：kafka消费者组状态</p>
<p>（1）<strong>Empty</strong>：组内没有任何成员，但消费者组可能存在已提交的位移数据，而且这些位移尚未过期。</p>
<p>（2）<strong>Dead</strong>：组内没有任何成员，但组的元数据信息已经在协调者端被移除。协调者保存着当前向它注册过的所有组信息，所谓元数据就是类似于这些注册信息。</p>
<p>（3）<strong>PreparingRebalance</strong>：消费者组准备开启重平衡，此时所有成员都要重新请求加消费者组</p>
<p>（4）<strong>CompletingRebalance</strong>：消费者组下所有成员已经加入，各个成员正在等待分配方案。</p>
<p>（5）<strong>Stable</strong>：消费者组的稳定状态。该状态表明重平衡已经完成，组内成员能够正常消费数据了。</p>
<p>B ：Kafka定期自动删除过期位移的条件：消费者处于Empty状态。</p>
<p>如果消费者组停了很长时间（超过7天），那么Kafka很可能就把该组的位移数据删除了。</p>
<p><strong>(3) 消费者端重平衡流程</strong></p>
<p>A ：重平衡的完整流程需要消费者端和协调者组件共同参与才能完成。</p>
<p>B ：在消费者端，重平衡分为两个步骤：</p>
<ol><li>
<p>加入组，对应请求：JoinGroup请求</p>
</li>
<li>
<p>等待领导者消费者分配方案：SyncGroup请求</p>
</li>
</ol><p>C ：当组内成员加入组时，他会向协调者发送JoinGroup请求。在该请求中，每个成员都要将自己订阅的主题上报，这样协调者就能收集到所有成员的订阅信息。一旦收集了全部成员的JoinGroup请求后，协调者会从这些成员中选择一个担任这个消费者组的领导者。</p>
<p>D ：通常情况下，第一个发送JoinGroup 请求的成员自动成为领导者。这里的领导者是具体的消费者实例，它既不是副本，也不是协调者。领导者消费者的任务是收集所有成员的订阅信息，然后根据这些信息，制定具体的分区消费分配方案。</p>
<p>E ：选出领导者之后，协调者会把消费者组订阅信息封装进JoinGroup请求的响应中，然后发给领导者，由领导统一做出分配方案后，进入下一步：发送SyncGroup请求。</p>
<p>F ：领导者向协调者发送SyncGroup请求，将刚刚做出的分配方案发给协调者。值得注意的是，其他成员也会向协调者发送SyncGroup请求，只是请求体中并没有实际内容。这一步的目的是让协调者接收分配方案，然后统一以SyncGroup 响应的方式发给所有成员，这样组内成员就都知道自己该消费哪些分区了。</p>
<p><strong>(4) Broker端重平衡场景剖析</strong></p>
<p><strong>A ：新成员入组</strong></p>
<p>当协调者收到新的JoinGroup请求后，它会通过心跳请求响应的方式通知组内现有的所有成员，强制他们开启新一轮的重平衡。</p>
<p><strong>B ：组成员主动离组</strong></p>
<p>消费者实例所在线程或进程调用close()方法主动通知协调者他要退出。这个场景涉及第三类请求：LeaveGroup请求。协调者收到LeaveGroup请求后，依然会以心跳响应的方式通知其他成员。</p>
<p><strong>C ：组成员崩溃离组</strong></p>
<p>崩溃离组是指消费者实例出现严重故障，突然宕机导致的离组。崩溃离组是被动的，协调者通常需要等待一段时间才能感知，这段时间一般是由消费者端参数<a href="http://session.timeout.ms/">session.timeout.ms</a>控制的。</p>
<p><strong>D ：重平衡时协调者对组内成员提交位移的处理</strong></p>
<p>正常情况下，每个组内成员都会定期汇报位移给协调者。当重平衡开启时，协调者会给予成员一段缓冲时间，要求每个成员必须在这段时间内快速地上报自己的位移信息，然后在开启正常JoinGroup/SyncGroup请求发送。</p>
<p><br/></p>
<h3>4. Kafka控制器</h3>
<p><strong>(1) 简介</strong></p>
<p>控制器组件（Controller），是Apache Kafka的核心组件。它的主要作用是Apache Zookeeper的帮助下管理和协调整个Kafka集群。 集群中任意一台Broker都能充当控制器的角色，但在运行过程中，只能有一个Broker成为控制器。</p>
<p>特点：控制器是重度依赖Zookeeper。</p>
<p>产生：控制器是被选出来的，Broker在启动时，会尝试去Zookeeper中创建/controller节点。Kafka当前选举控制器的规则是：第一个成功创建/controller节点的Broker会被指定为控制器。</p>
<p><strong>(2) 功能</strong></p>
<p>A ：主题管理（创建，删除，增加分区）</p>
<p>当执行kafka-topics脚本时，大部分的后台工作都是控制器来完成的。</p>
<p>B ：分区重分配</p>
<p>Kafka-reassign-partitions脚本提供的对已有主题分区进行细粒度的分配功能。</p>
<p>C ：Preferred领导者选举</p>
<p>Preferred领导者选举主要是Kafka为了避免部分Broker负载过重而提供的一种换Leade的方案。</p>
<p>D ：集群成员管理（新增Broker，Broker主动关闭，Broker宕机）</p>
<p>控制器组件会利用watch机制检查Zookeeper的/brokers/ids节点下的子节点数量变更。当有新Broker启动后，它会在/brokers下创建专属的znode节点。一旦创建完毕，Zookeeper会通过Watch机制将消息通知推送给控制器，这样，控制器就能自动地感知到这个变化。进而开启后续新增Broker作业。</p>
<p>侦测Broker存活性则是依赖于刚刚提到的另一个机制：临时节点。每个Broker启动后，会在/brokers/ids下创建一个临时的znode。当Broker宕机或主机关闭后，该Broker与Zookeeper的会话结束，这个znode会被自动删除。同理，Zookeeper的Watch机制将这一变更推送给控制器，这样控制器就能知道有Broker关闭或宕机了，从而进行善后。</p>
<p>E ：数据服务</p>
<p>控制器上保存了最全的集群元数据信息，其他所有Broker会定期接收控制器发来的元数据更新请求，从而更新其内存中的缓存数据。</p>
<p><strong>(3) 数据保存与故障转移</strong></p>
<p><strong>A. 控制器数据保存</strong>：控制器中保存的这些数据在Zookeeper中也保存了一份。每当控制器初始化时，它都会从Zookeeper上读取对应的元数据并填充到自己的缓存中。</p>
<p><strong>B. 控制器故障转移（Failover）</strong>：当运行中的控制器突然宕机或意外终止时，Kafka能够快速地感知到，并立即启用备用控制器来替代之前失败的控制器。</p>
<p><strong>(4) 内部设计原理</strong></p>
<p><strong>A ：控制器的多线程设计</strong></p>
<p>控制器是多线程的设计，会在内部创建很多线程。如：</p>
<ul><li>
<p>为每个Broker创建一个对应的Socket连接，然后在创建一个专属的线程，用于向这些Broker发送特定的请求。</p>
</li>
<li>
<p>控制连接zookeeper,也会创建单独的线程来处理Watch机制通知回调。</p>
</li>
<li>
<p>控制器还会为主题删除创建额外的I/O线程。</p>
</li>
</ul><p>这些线程还会访问共享的控制器缓存数据，为了维护数据安全性，控制在代码中大量使用ReetrantLock同步机制，进一步拖慢了整个控制器的处理速度。</p>
<p><strong>B ：在0.11版对控制器的低沉设计进了重构</strong></p>
<p><strong>第一个改进（最大改进）：把多线程的方案改成了单线程加事件对列的方案。</strong></p>
<ul><li>
<p>单线程+队列的实现方式：社区引入了一个事件处理线程，统一处理各种控制器事件，然后控制器将原来执行的操作全部建模成一个个独立的事件，发送到专属的事件队列中，供此线程消费。</p>
</li>
<li>
<p>单线程不代表之前提到的所有线程都被干掉了，控制器只是把缓存状态变更方面的工作委托给了这个线程而已。</p>
</li>
</ul><p><strong>第二个改进：将之前同步操作Zookeeper全部改为异步操作。</strong></p>
<p>Zookeeper本身的API提供了同步写和异步写两种方式。同步操作zk，在有大量主题分区发生变更时，Zookeeper容易成为系统的瓶颈。</p>
<p><br/></p>
<h3>5. 高水位和Leader Epoch</h3>
<p><strong>(1) 概念</strong></p>
<p><strong>A ：水位</strong>：多用于流式处理领域，如Spark Streaming 或Flink框架中都有水位的概念。</p>
<p>在教科书中关于水位定义：在即刻T，任意创建时间（Event Time）为T ’ ，且T ’ &lt;= T的所有事件都已经到达或被观测到，那么T就被定义为水位。在《Streaming System》一书则是这样表述水位：水位是一个单调增加且表征最早未完成工作（oldest work not yet completed）的时间戳。</p>
<p><strong>B ：kafka的水位概念</strong>：kafka的水位不是时间戳，与时间无关。他是和位置信息绑定的，它是用消息位移来表征的。 Kafka源码使用的表述是高水位。在Kafka中也有低水位（Low Watermark）,它是与Kafka删除消息相关的概念。</p>
<p><strong>(2) 高水位作用</strong></p>
<ul><li>
<p>定义消息可见性，用来标识分区下的哪些消息是可以被消费者消费的。</p>
</li>
<li>
<p>帮助Kafka完成副本同步。</p>
</li>
</ul><p>[图片未保存到本地]</p>
<p><strong>关键点：</strong></p>
<ul><li>
<p>在分区高水位以下的消息被认为是已提交消息，反之就是未提交消息。</p>
</li>
<li>
<p>消费者只能消费已提交消息</p>
</li>
<li>
<p>事务机制会影响消息者所能看到的消息的范围，他不只是简单依赖高水位来判断，还依靠一个名为LSO(Log Stable Offset)的位移值来判断事务型消费者的可见性。</p>
</li>
<li>
<p>位移值等于高水位的消息也属于为提交消息。即，高水位消息的消息是不能被消费者消费的。</p>
</li>
<li>
<p>日志末端位移的概念：Log End Offset，简写是LEO。他表示副本写入下一条消息的位移值。同一个副本对象，其高水位值不会大于LEO值。</p>
</li>
<li>
<p>高水位和LEO是副本对象的两个重要属性。Kafka所有副本都有对应的高水位和LEO值，而不仅仅是Leader副本。只是Leader副本比较特殊，Kafka使用Leader副本的高水位来定义所在分区的高水位。即，分区的高水位就是其Leader副本的高水位。</p>
</li>
</ul><p><strong>(3) 高水位更新机制</strong></p>
<p>在Leader副本所在Broker上，还保存了其他Follower副本的LEO值。而其他Broker上仅仅保存该分区的某个Follower副本。Kafka将Leader副本所在Broker上保存的这些Follower副本称为远程副本。</p>
<p>Kafka副本机制在运行过程中，会更新Broker1上Follower副本的高水位和LEO值，同时也会更新Broker0上Leader副本的高水位和LEO，以及所有远程副本的LEO。但它不会更新远程副本的高水位值。Broker0上保存这些远程副本的作用是帮助Leader副本确定其高水位，即分区高水位。</p>
<p><strong>A. Leader副本上的更新机制</strong></p>
<p><strong>处理生产者请求的逻辑：</strong></p>
<p> a. 写入消息到本地磁盘。</p>
<p> b. 更新分区高水位值</p>
<p> 1. 获取Leader副本所在Broker端保存的所有远程副本LEO值{LEO-1，LEO-2，……，LEO-n}。</p>
<p> 2. 获取Leader副本高水位值:currentHW。</p>
<p> 3. 更新currentHW = max（currentHW ，min(leo-1,leo-2,……leo-n)）.</p>
<p><strong>处理follwer副本拉取消息的逻辑：</strong></p>
<p> a. 读取磁盘（或页缓存）中的消息数据</p>
<p> b. 使用Follower副本发送请求中的位移值更新远程副本LEO值。</p>
<p> c. 更新分区高水位值（具体步骤与处理生产者请求的步骤相同）</p>
<p><strong>B. Follower副本上的更新机制</strong></p>
<p>从Leader拉取消息的处理逻辑：</p>
<p> a. 写入消息到本地磁盘</p>
<p> b. 更新LEO值</p>
<p> c. 更新高水位值</p>
<p>  1. 获取Leader发送的高水位值：currentHW。</p>
<p>  2. 获取步骤2中更新过的LEO值：currentLEO。</p>
<p>  3. 更新高水位为min（currentHW，currentLEO）。</p>
<p><strong>(4) Leader Epoch</strong></p>
<p>Leader Epoch：用来规避因高水位更新错配导致的各种不一种问题。所谓Leader Epoch大致可以认为是Leader版本。</p>
<p>A ：组成：由两部分数据组成。</p>
<ul><li>
<p>Epoch：一个单调增加的版本号。每当领导权发生变更时，都会增加该版本号。小版本号的Leader被认为是过期的Leader，不能在行使Leader权利。</p>
</li>
<li>
<p>起始位移（Start Offset）：Leader副本在改Epoch值上写入的首条消息的位移。</p>
</li>
</ul><p>B ：Kafka Broker会在内存中为每个分区都缓存Leader Epoch数据，同时他还会定期地将这些信息持久化到一个checkpoint文件中。</p>
<p><br/></p>
<h2>五、管理与监控</h2>
<h3>1. 主题管理</h3>
<p><strong>(1) 创建主题</strong></p>
<p>Kafka提供了自带的Kafka-topic脚本用于帮助用户创建主题。</p>
<div>
<pre>bin/kafka-topic.sh  --bootstarp-server broker_host:port  --create –topic my_topic  --partitions 1  --replication-factor 1</pre>
</div>
<p>create 表明要创建主题的行为，而partitions和replication factor分别设置了主题的分区数以及每个分区下的副本数。</p>
<p><strong>(2) 查询主题</strong></p>
<p>查询所有主题的列表：</p>
<div>
<pre>/bin/kafka-topic.sh --bootstrap-server broker_host:port --list </pre>
</div>
<p> 查询单个主题的详细数据：</p>
<div>
<pre>/bin/kafka-topic.sh --bootstrap-server broker_host:port --describe --topic </pre>
</div>
<p><strong>(3) 修改主题</strong></p>
<p>A ：修改分区</p>
<div>
<pre>/bin/kafka-topic.sh --bootstrap-server broker_host : port --alter --topic  --partitions &lt;新分区数&gt;</pre>
</div>
<p> 区数一定要比原有分区数大。</p>
<p>B ：修改主题级别参数：使用kafka-configs脚本修改对应的参数。</p>
<p>修改主题级别的max.message.bytes ：</p>
<div>
<pre>/bin/kafka-configs.sh --zookeeper zookeeper_host:port --entity-type topic --entity-name  --alter --add-config max.message.bytes=10485760</pre>
</div>
<p> 这个命令里使用的 –zookeeper，也可以使用 --bootstrap-server，只是他是用来设置动态参数的。</p>
<p>C ：变更副本数</p>
<p>使用kafka-reassign-partitions 脚本，增加副本数</p>
<p>D ：修改主题限速 </p>
<p>这是指设置Leader副本和follower 副本使用的带宽。有时候，需要让某个主题的副本在执行副本同步机制时，不要消耗过多的带宽。 要做到这个需要先设置leader.replication.throttled.rate和follower.replication.throttled.rate</p>
<div>
<pre>bin/kafka-configs.sh --zookeeper zookeeper_host:port --alter --add-config 'leader.replication.throttled.rate=104857600,follower.replication.throttled.rate=104857600' --entity-type brokers --entity-name 0</pre>
</div>
<p>E ：主题分区迁移</p>
<p>同样是使用kafka-ressign-partitions脚本。</p>
<p>F ：删除主题</p>
<pre>/bin/kafka-topic.sh –bootstrap-server broker_host:port --delete --topic </pre>
<p>删除主题的操作是异步的，执行完这条命令不代表主题立即就被删除了，它仅仅是被标记成“已删除”状态而已。Kafka会在后台默默地开启主题删除操作。</p>
<p><strong>(4) 常见主题错误处理</strong></p>
<p>A：主题删除失败</p>
<p>造成主题删除最常见的原因有两个：副本所在Broker宕机了；待删除主题的部分分区依然在执行迁移过程。</p>
<p>解决：</p>
<ol><li>
<p>手动删除Zookeeper节点/admin/delete_topics 下待删除主题为名的znode。</p>
</li>
<li>
<p>手动删除该主题的磁盘上的分区目录。</p>
</li>
<li>
<p>在Zookeeper中执行rmr/controller，触发Controller重选举，刷新Controller缓存。</p>
</li>
</ol><p>在执行最后一步时，要慎重，因为他可能造成大面积的分区Leader重选举。事实上，仅仅执行前两步也是可以的，只是Controller缓存中没有清空删除主题，不影响使用。</p>
<p>B：_consumer_offset占用太多的磁盘</p>
<p>如果发现这个主题占用了过多的磁盘空间，就要显示的使用jstack 命令查看kafka-log-cleaner-thread前缀线程状态。</p>
<h3>2. 动态配置</h3>
<p>一般配置的做法是，一次性在server.properties文件中配置好所有参数后，启动Broker。在需要变更任何参数时，必须要重启Broker。</p>
<p>在1.1.0版本中正是引入了动态Broker参数（Dynamic Broker Configs）。</p>
<p><strong>概念：</strong>所谓动态，就是指修改参数值后，无需重启Broker就能立即生效，在server.properties中配置的参数称之为静态参数（Static Configs）。</p>
<p><strong>(1) 分类</strong></p>
<ul><li>
<p>read-only：被标记为read-only的参数和原来的参数行为一样，只有重启Broker，才能令修改生效；</p>
</li>
<li>
<p>per-broker：被标记为per-broker的参数属于动态参数，修改它之后，只会在对应的Broker上生效；</p>
</li>
<li>
<p>cluster-wide：被标记为cluster-wide的参数也属于动态参数，修改它之后，会在整个集群范围内生效；</p>
</li>
</ul><p><strong>(2) 使用场景</strong></p>
<ul><li>
<p>动态调整Broker端各种线程池大小，实时应对突发流量；</p>
</li>
<li>
<p>动态调整Broker端连接信息或安全配置信息；</p>
</li>
<li>
<p>动态更新SSL Keystore有效期；</p>
</li>
<li>
<p>动态调整Broker端Compact操作性能；</p>
</li>
<li>
<p>实时变更JMX指示收集器（JMX Metrics Reporter）；</p>
</li>
</ul><p><strong>(3) 配置存储</strong></p>
<p>A ：首先Kafka将动态Broker参数保存在Zookeeper中</p>
<p>[图片未保存到本地]</p>
<ul><li>
<p>changes：是用来实时监控动态参数变更的，不会保存参数值；</p>
</li>
<li>
<p>topic是用来保存Kafka主题级别参数的；</p>
</li>
<li>
<p>user和clients是用于动态调整客户端配额（Quota）的znode节点。所谓配额是指Kafka运维人员限制连入集群的客户端的吞吐量或</p>
<p>是限定他们的使用CPU资源。</p>
</li>
</ul><p>B ：/config/brokers znode才是真正保存动态Broker参数的地方，该znode下有两大类子节点：</p>
<ul><li>
<p>第一类子节点只有一个，固定叫&lt; default &gt;，保存cluster-wide范围的动态参数</p>
</li>
<li>
<p>第二类以<a href="http://broker.id/">Broker.id</a>为名，保存特定Broker的per-broker范围参数。</p>
</li>
</ul><p>C ：参数的优先级别：per-broker参数 &gt; cluster-wide参数 &gt; static参数 &gt; Kafka默认值。</p>
<p><strong>(4) 如何配置</strong></p>
<p>A ：使用Kafka自带的Kafka自带的Kafka-configs脚本。</p>
<p>如果要设置cluster-wide范围的动态参数，需要显式指定entity-default。</p>
<p>B ：较大几率被动态调整的参值</p>
<ul><li>
<p>log.retention.ms：修改日志留存时间</p>
</li>
<li>
<p>num.io.threads 和 num.network.threads </p>
</li>
<li>
<p>与SS相关的参数：ssl.keystore.type，ssl.keystore.location，ssl.kestore.password和ssl.key.password。允许动态实时调整相关参数就能创建过期时间很短的SSL证书，使用新的Keystore，阶段性的调整这组参数，提升安全</p>
</li>
<li>
<p>num.replica.fetchers：这个可以增加该参数值，确保有充足的线程可以执行Follower副本向Leader副本的拉取。</p>
</li>
</ul><h3>3. 重设消费者位移</h3>
<p>当需要实现重复消费历史数据的时候，就需要重设消费者组位移</p>
<p><strong>(1) 重设位移的原因</strong></p>
<p>A ：Kafka和传统的消费引擎在设计上有很大区别，其中一个比较显著的区别是：Kafka的消息费者读取消息是可以重演的（replayable）</p>
<p>B ：如RabbitMQ或ActiveMQ这样的传统消息中间件，他们处理和响应消息的方式是破坏性的（destructive）,一旦消息被成功处理，就会被从Broker上删除。</p>
<p>C ：Kafka，由于它是基于日志结构（log-based）的消息引擎，消费者在消费消息时，仅仅是从磁盘文件上读取数据，是只读操作，因此消费者不会删除消息数据。同时，由于位移数据是由消费者控制的，因此他能够很容易的修改位移值，实现重复消费历史数据的功能。</p>
<p><strong>(2) 重设位移的策略</strong></p>
<p>A ：位移维度：根据位移值来重设。直接把消费者的位移值重设成我们给定的值。</p>
<p>B ：时间维度：可以给定一个时间，让消费者吧位移调整成大于该时间的最小位移；亦可以给出一段时间间隔，如30分钟，然后让消费者直接将位移调回30分钟之前的位移值。</p>
<p><strong>七种策略：</strong></p>
<ul><li>
<p>Earliest：将位移调整到主题当前最早位移处。可以实现重新消费主题的所有消息；--to-earliest</p>
</li>
<li>
<p>Latest：把位移重设成最新末端位移。可以跳过所有历史消息，从最新消息开始消费；--to-latest</p>
</li>
<li>
<p>Current：将位移调整成消费者当前提交的最新位移，可以实现把位移重设到消费者重启时的位置；--to-current</p>
</li>
<li>
<p>Specified-Offset：把位移值调整到指定的位移处。这可以实现跳过某条错误信息，避免造成消费阻塞；--to-offset</p>
</li>
<li>
<p>Shift-By-N：相对于当前位值的位移值，可以向前或向后，跳出一段距离；--shift-by N</p>
</li>
<li>
<p>DataTime：指定一个时间，然后将位移重置到该时间之后的最早位移处；--to-datetime</p>
</li>
<li>
<p>Duration：给定相对时间间隔，让位移调整到距离当前给定时间间隔的位移处；--by-duration</p>
</li>
</ul><p><strong>(3) 重设的方法</strong></p>
<p>A ：通过消费者API来实现</p>
<p>B ：通过Kafka-consumer-groups命令行脚本来实现</p>
<p>消费者API注意事项：</p>
<ul><li>
<p>要创建消费者程序，要禁止自动提交位移</p>
</li>
<li>
<p>组ID要设置成要重设的消费者组的组ID</p>
</li>
<li>
<p>调用seekToBeginning方法时，要一次性构造主题的所有分区对象</p>
</li>
<li>
<p>最重要的是，一定要调用带长整形的poll方法，而不调用consumer.poll(Duration.ofSecond(0))。</p>
</li>
<li>
<p>要实现DateTime策略：需要借助KafkaConsumer.offsetsForTimes方法。</p>
</li>
</ul><p>总之：使用Java API的方式来实现重设策略的主要入口方法，就是seek方法。</p>
<p><br/></p>
<h3>4. 常见工具脚本</h3>
<p>2.2版本提供了30多个Shell脚本</p>
<ol><li>
<p>connect-standalone：支持kafka Connect组件支持单节点Standalone模式</p>
</li>
<li>
<p>connect-distributed：支持多节点的Distributed模式</p>
</li>
<li>
<p>kafka-acls：用于设置Kafka权限，如设置哪些用户可以访问哪些主题之类的权限</p>
</li>
<li>
<p>kafka-broker-api-versions：主要目的是验证不同Kafka版本之间服务器和客户端的适配性。</p>
</li>
<li>
<p>kafka-configs：用于配置管理</p>
</li>
<li>
<p><strong>kafka-console-consumer：消费消息</strong></p>
</li>
<li>
<p><strong>kafka-console-producer：生产消息</strong></p>
</li>
<li>
<p><strong>kafka-producer-perf-test：生产者的性能测试</strong></p>
</li>
<li>
<p><strong>kafka-consumer-perf-test ：消费者的性能测试</strong></p>
</li>
<li>
<p><strong>kafka-consumer-groups：查看消费者组位移</strong></p>
</li>
<li>
<p>kafka-delegation-tokens：管理Delegation Token的，基于Delegation Token的认证是一种轻量级的认证机制，补充了现有的SASL认证机制</p>
</li>
<li>
<p>kafka-delete-records：用于删除Kafka的分区消息</p>
</li>
<li>
<p><strong>kafka-dump-log：能够查看kafka消息文件的内容，包括消息的各种元数据信息</strong></p>
</li>
<li>
<p>kafka-log-dirs:可以帮助查询各个Broker上的各个日志路径的磁盘占用情况</p>
</li>
<li>
<p>kafka-mirror-maker：可以帮助实现kafka集群间消息同步</p>
</li>
<li>
<p>kafka-preferred-replica-election：执行Preferred Leader选举。他可以为指定的主题执行“换Leader”的操作</p>
</li>
<li>
<p>kafka-reassign-partitions：用于执行分区副本迁移以及副本文件路径迁移</p>
</li>
<li>
<p>kafka-topics：所有主题管理操作，都是有该脚本来实现</p>
</li>
<li>
<p>kafka-run-class：可以用这个脚本执行任何带main方法的Kafka类</p>
</li>
<li>
<p>kafka-server-start和kafka-server-stop：启动和停止Kafka Broker进程</p>
</li>
<li>
<p>kafka-streams-application-reset：用来给kafka-Streams应用程序重试位移，以便重新消费数据</p>
</li>
<li>
<p>kafka-verifiabel-producer和kafka-verifiable-consumer是用来测试生产者和消费者功能的。</p>
</li>
<li>
<p>zookeeper开头的脚本是用来管理和运维Zookeeper的</p>
</li>
</ol><h3>5. KafkaAdminClient</h3>
<p><strong>(1) 引入原因</strong></p>
<ol><li>
<p>kafka自带的各种命令行脚本都只能运行在控制台上，不便于集成进应用程序或运维框架</p>
</li>
<li>
<p>这些命令行脚本很多都是通过连接Zookeeper来提供服务，这存在一些潜在问题，如这可能绕开Kafka的安全设置。</p>
</li>
<li>
<p>这些脚本需要使用Kafka内部的类实现，即Kafka服务端的代码。社区希望用户只使用Kafka客户端代码，通过现有的请求机制来运维管理集群。</p>
</li>
</ol><p><strong>(2) 使用及功能</strong></p>
<p>使用：需要在工程中显示的地增加依赖。</p>
<p>九大类功能：</p>
<ul><li>
<p>主题管理：包括主题的创建，查询和删除</p>
</li>
<li>
<p>权限管理：包括具体权限的配置与删除</p>
</li>
<li>
<p>配置参数管理：包括Kafka各种资源的参数设置，详情查询。所谓的kafka资源主要有Broker，主题，用户，Client-id等</p>
</li>
<li>
<p>副本日志管理：包括副本底层日志路径的变更和详情查询</p>
</li>
<li>
<p>分区管理：即创建额外的主题分区</p>
</li>
<li>
<p>消息删除：删除指定位移之前的分区消息</p>
</li>
<li>
<p>Delegation Token管理：包括Delegation Token的创建，更新，过期和详情查询</p>
</li>
<li>
<p>消费者组管理：包括消费者组的查询，位移查询和删除</p>
</li>
<li>
<p>Preferred领导者选举：推选指定主题分区的Preferred Broker为领导者。</p>
</li>
</ul><p><strong>(3) 工作原理</strong></p>
<p><strong>A ：从设计上来看，AdminClient是一个双线程的设计：前端主线程和后端I/O线程。</strong></p>
<ul><li>
<p>前端线程负责将用户要执行的操作转换成对应的请求，然后将请求发送到后端I/O线程的队列中；</p>
</li>
<li>
<p>后端I/O线程从队列中读取相应的请求，然后发送到对应的Broker节点上，之后把执行结果保存起来，以便等待前端线程的获取。</p>
</li>
</ul><p><strong>B ：AdminClient在内部大量使用生产者—消费者模型将请求生产和处理解耦</strong></p>
<p><strong>C ：前端主线程会创建一个名为Call的请求对象实例。</strong></p>
<p>该实例的有两个主要任务：</p>
<ul><li>
<p>构建对应的请求对象：如要创建主题，就创建CreateTopicRequest；要查询消费者位移，就创建OffsetFetchRequest</p>
</li>
<li>
<p>指定响应的回调逻辑：如Broker端接收到CreateTopicResponse之后要执行的动作。</p>
</li>
</ul><p>一旦创建好Call实例，前端主线程会将其放入到新请求队列（New Call Queue）中，此时，前端主线程的任务就算完成了。他只需要等待</p>
<p>结果返回即可。剩下的所有事情都是后端I/O线程的工作了。   <strong>D ：后端I/O线程，该线程使用了3个队列（新请求队列、待发送请求队列、处理中请求队列）来承载不同时期的请求对象</strong></p>
<p>使用3个队列的原因：</p>
<ul><li>
<p>新请求队列的线程安全是有Java的monitor锁来保证的。为了确保前端主线程不会因为monitor锁被阻塞，后端I/O线程会定期地将新请求队列中的所有Call实例全部搬移到待发送请求队列中进行处理。</p>
</li>
<li>
<p>待发送请求队列和处理中请求队列只由后端I/O线程处理，因此无需任何锁机制来保证线程安全。当I/O线程在处理某个请求时，他会显式的将该请求保存在处理中请求队列。一旦处理完成，I/O线程会自动地调用Call 对象中的回调完成最后的处理。最后，I/O线程会通知前端主线程处理完毕，这样前端主线程就能够及时的获取到执行操作的结果。</p>
</li>
</ul><p><strong>(4) 构造和销毁AdminClient实例</strong></p>
<p>A ：切记它的的完整路径是org.apche.kafka.clients.admin.AdminClient。</p>
<p>B ：创建AdminClient实例和创建KafkaProducer或KafkaConsumer实例的方法是类似的，你需要手动构造一个Properties对象或Map对象，然后传给对应的方法。</p>
<p><br/></p>
<h3>6. Kafka监控</h3>
<p><strong>(1) 监控维度</strong></p>
<table><thead><tr><th>监控维度</th>
<th>指标</th>
</tr></thead><tbody><tr><td>主机监控</td>
<td>含义：指监控Kafka集群Broker所在的节点机器的性能。 常见的主机监控指标：机器负载、CPU使用率、内存使用率、磁盘I/O使用率、网络I/O使用率、TCP连接数、打开文件数和inode使用情况</td>
</tr><tr><td>JVM监控</td>
<td>3个指标：FullGC发生频率和时长、活跃对象大小和应用线程总数</td>
</tr><tr><td>集群监控</td>
<td>5个方法：查看Broker进程是否启动，端口是否建立；查看Broker端关键日志;查看Broker端关键线程的运行状态；查看Broker端的关键JMX指标；监控Kafka客户端</td>
</tr></tbody></table><p><strong>(4) 主流的Kafka监控框架</strong></p>
<table><thead><tr><th>监控框架</th>
<th><br/></th>
</tr></thead><tbody><tr><td>JMXTool工具</td>
<td>可以实时查看KafkaJMX指标，不过只能应用于简单的监控场景</td>
</tr><tr><td>Kafka Manager</td>
<td>作为一款强大的Kafka开源监控框架，它提供了丰富的实时监控指标以及适当的管理功能，非常适合一般的Kafka集群监控</td>
</tr><tr><td>Burrow</td>
<td>目前提供的功能十分有限，但质量是很有保证的</td>
</tr><tr><td>JMXTrans+InfluxDB+Grafana</td>
<td>可以在一套监控框架中同时监控企业的多个关键技术组件</td>
</tr><tr><td>ConfluentControlCenter</td>
<td>目前已知的最强大的Kafka监控框架了。实时地监控 Kafka 集群，方便操作和搭建基于 Kafka 的实时流处理应用；提供了统一式的主题管理功</td>
</tr></tbody></table><p><br/></p>
<h3>7. 性能调优</h3>
<p>调优目标：高吞吐量、低延时。</p>
<p>优化漏斗：自上而下分为应用程序层、框架层、JVM层和操作系统层。层级越靠上，调优的效果越明显。</p>
<table><thead><tr><th>调优类型</th>
<th>建议</th>
</tr></thead><tbody><tr><td>操作系统</td>
<td>挂载文件系统时禁掉atime更新；选择ext4或XFS文件系统；swap空间的设置；页缓存大小</td>
</tr><tr><td>JVM（堆设置和GC收集器）</td>
<td>将JVM 堆大小设置成 6～8GB；建议使用 G1 收集器，方便省事，比 CMS 收集器的优化难度小</td>
</tr><tr><td>Broker端</td>
<td>保持服务器端和客户端版本一致</td>
</tr><tr><td>应用层</td>
<td>要频繁地创建Producer和Consumer对象实例；用完及时关闭；合理利用多线程来改善性能</td>
</tr></tbody></table><p>调优吞吐量(TPS)和延时：</p>
<p>调优 TPS：</p>
<table><thead><tr><th><br/></th>
<th>参数列表</th>
</tr></thead><tbody><tr><td>Broker端</td>
<td>适当增加num.replica.fetchers参数值，但不超过CPU核数</td>
</tr><tr><td><br/></td>
<td>调优GC参数以避免经常性的Full GC</td>
</tr><tr><td>Producer端</td>
<td>适当增加batch.size参数值，比如从默认的16KB增加到512KB或1MB</td>
</tr><tr><td><br/></td>
<td>适当增加<a href="http://linger.ms/">linger.ms</a>参数值，比如10～100</td>
</tr><tr><td><br/></td>
<td>设置compression.type=lz4或zstd</td>
</tr><tr><td><br/></td>
<td>设置acks=0或1</td>
</tr><tr><td><br/></td>
<td>设置retries=0</td>
</tr><tr><td><br/></td>
<td>如果多线程共享同一个Producer实例，则增加buffer.memory参数值</td>
</tr><tr><td>Consumer端</td>
<td>采用多Consumer进程或线程同时消费数据</td>
</tr><tr><td><br/></td>
<td>增加fetch.min.bytes参数值，比如设置成1KB或更大</td>
</tr></tbody></table><p>调优延时：</p>
<table><colgroup><col/><col/></colgroup><thead><tr><th><br/></th>
<th>参数列表</th>
</tr></thead><tbody><tr><td>Broker端</td>
<td>适当设置num.replica.fetchers值</td>
</tr><tr><td>Producer端</td>
<td>设置<a href="http://linger.ms/">linger.ms</a>=0</td>
</tr><tr><td><br/></td>
<td>不启用压缩，即设置compression.type=none</td>
</tr><tr><td><br/></td>
<td>设置ackes=1</td>
</tr><tr><td>Consumer端</td>
<td>设置fetch.min.bytes=1</td>
</tr></tbody></table><p><br/></p>
<p><br/></p>
<p><br/></p>
<p><br/></p>
<p><br/></p>
<p><strong><br/></strong></p> 
{% endraw %}
