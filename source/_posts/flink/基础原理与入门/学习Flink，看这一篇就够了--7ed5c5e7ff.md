---
title: "学习Flink，看这一篇就够了"
date: 2022-06-16 08:00:40
categories:
  - flink
  - 基础原理与入门
---

{% raw %}

<h3>1、流式计算和批处理</h3>
<p>批处理在大数据世界有着悠久的历史。早期的大数据处理基本上是批处理的天下。批处理主要操作大容量的静态数据集，并在计算过程完成之后返回结果。所以批处理面对的数据集通常具有以下特征：</p>
<ul><li><strong>有界</strong>：批处理数据集代表数据的有限集合</li>
<li><strong>持久</strong>：数据通常存储在<strong>可重复获取</strong>的持久存储设备中</li>
<li><strong>就绪</strong>：数据在计算之前已经就绪，不会发生变化</li>
<li><strong>大量</strong>：批处理操作通常是处理海量数据集的唯一方法</li>
</ul><p>批处理非常适合需要访问全部记录才能完成的计算工作。例如在计算数据集的总数或者平均数时，必须将数据集作为一个整体加以处理，而不能只处理其中的部分数据集。这些操作在计算进行的过程中需要维持计算的<strong>中间信息</strong>，即<strong>状态</strong>。当作业执行完成后，批处理系统会将最终的结果存储到持久介质中。由于批处理是离线计算，且大数据量的处理往往耗时较久，所以批处理适合于对时效性要求没那么高的场景。</p>
<p>相比于批处理，流处理是一种截然不同的处理方式。流处理系统需要对<strong>随时进入</strong>系统的数据进行实时计算。批处理和流处理的差异主要体现在：首先，流处理中的数据集是“<strong>无边界</strong>”的；其次，流处理中的数据不一定是持久化的，有可能是业务系统实时产生的；再次，流式计算常常需要处理业务系统实时产生的数据，而并非已就绪。这些差异就产生了以下几个重要的影响：</p>
<ul><li>完整数据集只能代表截至目前已经进入到系统中的数据总量</li>
<li>处理工作是基于事件的，除非明确停止，否则没有“尽头”</li>
<li>处理结果立刻可用，并随着新数据的抵达持续更新</li>
<li>无界、非就绪、非持久化，导致对流式计算有更高的容错要求</li>
</ul><p>如下图所示，流处理系统可以处理无限量的数据。显然，同批处理一样，在流处理过程中，也都需要维持中间<strong>状态</strong>。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/1d0e872b7d00f4254579.png"/></p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/learn-flink/overview/">https://ci.apache.org/projects/flink/flink-docs-master/docs/learn-flink/overview/</a></p>
<h3>2、流式计算的状态与容错</h3>
<p>前一小节提到了流计算的状态，本小节将进一步详细讨论这个概念。在流计算中，状态（State）是一个较宽泛的概念。这里我们先明确给个定义：状态（State）就是计算过程中的“<strong>中间信息（Intermediate Information）</strong>”。</p>
<p>从数据的角度看，流计算的处理方法主要有以下两种：</p>
<ul><li><strong>无状态（Stateless）</strong>：每一个进入的记录独立于其他记录。不同记录之间没有任何关系，它们可以被独立处理和持久化。例如：map、fliter、静态数据 join 等操作。</li>
<li><strong>有状态（Stateful）</strong>：处理进入的记录依赖于之前记录处理的结果。因此，我们需要维护不同数据处理之间的中间信息。每一个进入的记录都可以读取和更新该信息。我们把这个中间信息称作状态（State）。例如：独立键的聚合计数、去重等等。</li>
</ul><p>对应地，状态处理也分为两种：</p>
<ol><li><strong>过程状态</strong>：它是流计算的元数据（metadata），用于追踪和记录历史至今，已经被处理的数据偏移量及流处理系统当前的状态。在流的世界中，这些元数据包括 checkpoint /savepoint （后面会介绍）以及保存已经处理数据的偏移量（offset）等。这些信息是任何高可靠流处理的基本，同时被无状态和有状态处理需要。</li>
<li><strong>数据状态</strong>：这些中间数据来自于数据本身（目前为止处理过的），它需要在记录之间维护（只在Stateful模式下需要维护）。</li>
</ol><p>事实上，维护流式计算的中间信息不仅仅是因为计算本身所需要，还有个非常重要的原因是<strong>流式计算系统的容错性要求</strong>。维基百科对容错性（fault tolerance）的定义：容错性是指存在故障的情况下计算机系统不失效并且仍然能够正常工作的特性。</p>
<p>根据这个定义我们可以知道为什么需要容错：因为“故障”的存在。故障产生的原因多种多样（例如机器故障、网络故障、软件失败或者服务异常重启等），并且发生的时机也具有不确定性，但最终对用户产生的直接影响都是导致任务执行失败。为此，流计算系统需要一种机制来周期性地持久化相应的状态快照（即checkpoint机制），当计算系统出现异常后，就可以从最近的持久化快照中恢复执行，从而确保计算结果的正确性。<br/></p>
<p>在批处理场景中，我们可以很容易地应对故障导致的种种问题，因为所有的输入数据都是可再次获得的。我们可以重启作业然后重放所有输入数据。而在流计算场景中，却有以下三方面的挑战：第一，流式计算的数据集有可能是非持久化的，即有可能是无法再次获得的，或者再次获得的成本将会很高；第二，流式计算面向的是无界数据集，理论上作业的执行时间也是无界的，即便理论上可能达不到这一点，在实际情况下流作业的执行周期也非常长，因此状态很可能关联着整个执行周期内的计算结果；第三，相较于批处理，流式计算对计算结果的实时性更为敏感，从头开始重新计算得到的结果对于系统而言往往已经没有价值。这就导致了流计算作业状态的价值更为“昂贵”，因为一旦状态丢失，要重新计算并恢复它有可能做不到，或者需要花费非常高的计算开销以及时间成本，或者得到已经失去价值的结果。</p>
<h3>3、Flink简介及其在业务系统中的位置</h3>
<p>Apache Flink是由Apache软件基金会开发的开源流处理框架，其核心是用Java和Scala编写的<strong>分布式</strong>流数据引擎。Flink以数据<strong>并行</strong>（分布式）和<strong>流水线</strong>方式执行任意流<strong>数据程序</strong>，Flink的流水线运行时系统可以执行<strong>批处理</strong>和<strong>流处理</strong>程序。</p>
<p>下图给出了<strong>基于DB事务的传统业务系统</strong>和<strong>基于Flink的流数据处理系统</strong>的类比图。由此可知，传统业务系统和流数据处理系统的功能是类似的，两者都是对事件进行响应，并在响应完成后触发相应的行为。但在实际应用中，业务系统的事件往往直接来自用户的实时请求，而数据处理系统的事件则常常是由业务系统所触发。以风控系统为例，风控系统需要实时收集业务系统中用户的操作行为，以此计算出存在风险的用户及其风险操作，并将计算结果反馈给业务系统。</p>
<p>传统业务系统和流数据处理系统的主要差异体现在，前者的计算层和持久化存储层是分开的，计算层从持久化层读写数据；后者的数据和计算都是在本地的（内存或本地磁盘），因此可以有更高的吞吐量和更低的时延。而为了达到容错性要求，流计算需要定期将本地状态持久化到外部存储设备。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/124c355e8c2add36c265.png"/></p>
<p>图片来源：<a href="https://flink.apache.org/usecases.html">https://flink.apache.org/usecases.html</a></p>
<h3>4、Flink模型</h3>
<p>Flink对数据的处理被抽象为以下三步：第一，接受数据；第二，处理数据；第三，输出处理结果。具体来说就是，1，接收（ingest）一个或者多个数据源（hdfs，kafka等）；2，执行若干用户需要的转换算子（transformation operators）；3，将转换后的结果输出（sink）。</p>
<p>如下图所示，Flink处理数据流的算子（operator）也分为三类：Source负责管理输入（数据源），Tranformation负责数据运算，Sink负责管理结果输出。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/21d44f6a4b05c266e05e.png"/></p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/learn-flink/overview/">https://ci.apache.org/projects/flink/flink-docs-master/docs/learn-flink/overview/</a></p>
<p>Source和Sink就不再多说了，一个负责输入，一个负责输出。对于Transformation operators，熟悉java stream的同学应该很容易理解，因为Flink中的map，flatMap，reduce，apply等算子和java stream中对应的算子含义差不多。keyBy作为Flink的一个高频使用算子，其功能跟MySQL的group by功能差不多；而window算子则是通过窗口机制，将无界数据集拆分成一个个有界数据集，详细信息后面会进一步介绍。</p>
<p>作为一个分布式流数据处理引擎，各算子可以在不同的线程（不同的线程可以位于相同或者不同的物理节点）中<strong>并行执行</strong>。如下图所示，在Flink中可以对每个算子单独指定并行度（parallelism），也可以统一指定Flink的并行度，优先级是算子的并行度值高于统一的并行度值。还有一点需要注意的是，Flink中执行的作业还必须要有<strong>最大并行度</strong>，可以用户指定，否则Flink会根据并行度计算出一个默认值。关于最大并行度的作用，后面介绍Key Group时会详细说明。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/63e6fdd18d9611edf292.png"/></p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/learn-flink/overview/">https://ci.apache.org/projects/flink/flink-docs-master/docs/learn-flink/overview/</a><br/></p>
<h3>5、Flink的架构</h3>
<p>Flink的系统架构如下图所示。用户在客户端提交作业（Job）到服务端。服务端为分布式的主从架构。Master上的Dispatcher服务负责提供REST接口来接收Client提交的Job，运行Web UI，并负责启动和派发Job给JobManager。Resource Manager负责计算资源（TaskManager）的管理。JobManager负责将任务调度到TaskManager执行、检查点（checkpoint，后面会介绍）的创建等工作，而TaskManager(worker)负责SubTask的实际执行。当服务端的JobManager接收到一个Job后，会按照各个算子的并发度将Job拆分成多个SubTask，并分配到TaskManager的Slot上执行。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/bd45100117db8f723f8d.png"/></p>
<p>图片来源：<a href="https://nightlies.apache.org/flink/flink-docs-master/docs/learn-flink/datastream_api/">https://nightlies.apache.org/flink/flink-docs-master/docs/learn-flink/datastream_api/</a><br/></p>
<p>任务的提交流程如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/6ab57cf0b725a8a98bf0.png"/></p>
<p>图片来源：<a href="https://blog.csdn.net/lisenyeahyeah/article/details/100662367">https://blog.csdn.net/lisenyeahyeah/article/details/100662367</a></p>
<h3>6、Flink的重要概念</h3>
<p>上一小节提到了Job、SubTask、Slot等概念，本小节就来对Flink涉及到的Job、Task、SubTask、 Slot、Slotsharing、Thread等概念进行详细介绍。</p>
<p>首先，Job最容易理解，一个Job代表一个可以独立提交给Flink执行的作业，我们向JobManager提交任务的时候就是以Job为单位的，只不过一份代码里可以包含多个Job（每个Job对应一个类的main函数）。接着我们来看Task和SubTask，如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/c9cb103c91c32331fab5.png"/></p>
<p>图片来源：<a href="https://niyanchun.com/flink-quick-learning-job-task-slotsharing.html">https://niyanchun.com/flink-quick-learning-job-task-slotsharing.html</a></p>
<p>图说明如下：</p>
<ul><li>图中每个圆代表一个Operator（算子），每个<strong>虚线圆角框</strong>代表一个Task，每个<strong>虚线直角框</strong>代表一个Subtask，其中的p表示算子的并行度。</li>
<li>最上面是StreamGraph，在没有经过任何<strong>优化</strong>时，可以看到包含4个Operator/Task：Task A1、Task A2、Task B、Task C。</li>
<li>StreamGraph经过链式优化（Flink默认会将一些并行度相同的算子连成一条链）之后，Task A1和Task A2两个Task合并成了一个新的Task A（可以认为合并产生了一个新的Operator），得到了中间的JobGraph。</li>
<li>然后以并行度为2（需要2个Slot）执行的时候，Task A产生了2个Subtask，分别占用了Thread #1和Thread #2两个线程；Task B产生了2个Subtask，分别占用了Thread #3和Thread #4两个线程；Task C产生了1个Subtask，占用了Thread #5。</li>
</ul><p>由此可以总结如下：</p>
<ol><li><strong>Task是逻辑概念，一个Operator就代表一个Task</strong>（多个Operator被chain之后产生的新Operator算一个Operator）；</li>
<li><strong>真正运行的时候，Task会按照并行度分成多个Subtask，Subtask是执行/调度的基本单元</strong>；</li>
<li><strong>每个Subtask需要一个线程（Thread）来执行</strong>。</li>
</ol><p>前一小节讲了TaskManager才是真正干活的，启动的时候，它会将自己的内存资源以Slot的方式注册到master节点上的资源管理器（ResourceManager）。JobManager从ResourceManager处申请到Slot资源后将自己优化过后的SubTask调度到这些Slot上面去执行。在整个过程中<strong>SubTask是调度的基本单元</strong>，而<strong>Slot则是资源分配的基本单元</strong>。需要注意的是目前Slot只隔离内存，不隔离CPU。</p>
<p>为了更高效地使用资源，<strong>Flink默认允许同一个Job中不同Task的SubTask运行在同一个Slot中</strong>，这就是SlotSharing。注意以下描述中的几个关键条件：</p>
<ul><li>必须是同一个Job。这个很好理解，slot是给Job分配的资源，目的就是隔离各个Job，如果跨Job共享，但隔离就失效了；</li>
<li>必须是不同Task的Subtask。这样是为了更好的资源均衡和利用。一个计算流中（pipeline），每个Subtask的资源消耗肯定是不一样的，如果都均分slot，那必然有些资源利用率高，有些低。限制不同Task的Subtask共享可以尽量让资源占用高的和资源占用低的放一起，而不是把多个高的或多个低的放一起。比如一个计算流中，source和sink一般都是IO操作，特别是source，一般都是网络读，相比于中间的计算Operator，资源消耗并不大。</li>
<li>默认是允许sharing的，也就是你也可以关闭这个特性。</li>
</ul><p>下面我们依次来看看官方文档给出的两幅图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/1e071661efc901228129.png"/></p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/concepts/flink-architecture/">https://ci.apache.org/projects/flink/flink-docs-master/docs/concepts/flink-architecture/</a></p>
<p>图中两个TaskManager节点共有6个slot，5个SubTask，其中sink的并行度为1，另外两个SubTask的并行度为2。此时由于Subtask少于Slot个数，所以每个Subtask独占一个Slot，没有SlotSharing。下面我们把把并行度改为6：<br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/490391f8676cd2ddf678.png"/></p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/concepts/flink-architecture/">https://ci.apache.org/projects/flink/flink-docs-master/docs/concepts/flink-architecture/</a></p>
<p>此时，Subtask的个数多于Slot了，所以出现了SlotSharing。一个Slot中分配了多个Subtask，特别是最左边的Slot中跑了一个完整的Pipeline。SlotSharing除了提高了资源利用率，还简化了并行度和Slot之间的关系：<strong>一个Job运行需要的最少的Slot个数就是其中并行度最大的那个Task的并行度</strong>（ps：并行度最高和作业的最大并行度没有任何关系哈）。<br/></p>
<p>掌握了这些概念，就可以较好地评估流式计算作业所需要的资源量了。</p>
<p>ps：本小节主要内容摘自：<a href="https://niyanchun.com/flink-quick-learning-job-task-slotsharing.html">https://niyanchun.com/flink-quick-learning-job-task-slotsharing.html</a></p>
<h3>7、Flink的状态、状态分区、状态缩放（rescale）和Key Group</h3>
<p>由前面的小节已知，Flink的一个算子可能会有多个子任务，每个子任务可能分布在不同的实例上，我们可以把<strong>Flink的状态理解为某个算子的子任务在其当前实例上的一个变量</strong>，该<strong>变量记录了流过当前实例算子的历史记录产生的结果</strong>。当新数据记录流入时，我们需要结合该结果（即状态）来进行计算。实际上，Flink的状态是由算子的子任务来创建和管理的。一个状态的更新和获取的流程如下图所示，一个算子子任务接收输入流，获取对应的状态，根据新的计算结果更新状态。一个简单的例子是对一个时间窗口内流入的某个<strong>整数字段</strong>进行求和，那么当算子子任务接收到新元素时，会获取已经存储在状态中的数值（历史记录的<strong>求和结果</strong>），然后将当前输入加到状态上，并将状态数据更新。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/436cf3af7d8e1828883b.png"/></p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104171679">https://zhuanlan.zhihu.com/p/104171679</a></p>
<p>为了保证流式计算的高可用性（容错），<strong>子任务的状态除了会暂存在节点内，还需要进行持久化存储（快照）</strong>。对于一个分布式计算系统，要自行实现状态的备份和故障恢复，并没有那么容易。可喜的是，Flink提供了有状态的计算能力，它封装了一些底层的实现，比如状态的高效存储、Checkpoint和Savepoint的持久化备份机制、计算资源扩缩容等能力。因为Flink接管了这些问题，开发者只需调用Flink API，这样可以更加专注于业务逻辑。</p>
<p>按照状态的管理方式来分，Flink有两种基本类型的状态：托管状态（Managed State）和原生状态（Raw State）。从名称中也能读出两者的区别：Managed State是由Flink直接管理的，由Flink帮忙存储、恢复和优化；Raw State是开发者自己管理的，需要自己序列化。实际上，在绝大多数场景下我们都不需要自行维护状态，所以这里只介绍托管状态。对Managed State继续细分，又可以分为两种类型：Keyed State和Operator State。</p>
<p>我们首先来看Keyed State。由前面第4小节可知，env.addSource()方法返回的是一个类型为DataStream的数据流，而这个数据流再按照数据记录中的某个关键字段（比如id字段）为Key进行了keyBy分组操作，得到就是一个类型为<code>KeyedStream的数据流。Keyed State就是这些Key的状态。</code>数据流中所有相同id值的的记录共享一个状态（比如数据记录求和的值），可以访问和更新这个状态。以此类推，每个Key对应一个自己的状态。下图展示了Keyed State，因为一个算子子任务可以处理一到多个Key，算子子任务1处理了两种Key，两种Key分别对应自己的状态。<br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/7371bfd3b47f4733051e.png"/></p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104171679">https://zhuanlan.zhihu.com/p/104171679</a></p>
<p>介绍完Keyed State，我们再来看Operator State。顾名思义，Operator State就是算子上的状态，每个算子子任务管理自己的Operator State。虽然理论上它可以用在所有算子上，但在实际应用中它常常被用在Source或Sink等算子上，用来保存流入数据的偏移量或对输出数据做缓存，以保证Flink应用的Exactly-Once语义。每个算子的子任务或者说每个算子实例共享同一个状态，流入这个算子子任务的数据可以访问和更新这个状态。下图展示了Operator State，算子子任务1上的所有数据可以共享第一个Operator State，以此类推，每个算子子任务上的数据共享自己的状态。<br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/da1f6659631a925ea35e.png"/></p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104171679">https://zhuanlan.zhihu.com/p/104171679</a></p>
<p>无论是Keyed State还是Operator State，Flink的状态都是基于本地的，即每个算子子任务维护着这个算子子任务对应状态的存储，算子子任务之间的状态不能相互访问。<br/></p>
<p>介绍完Keyed State和Operator State，我们再来看状态的缩放，即状态的横向扩展问题。该问题主要是指因为一些业务原因，需要修改Flink作业中算子的并行度（比如，发现某个运行中的作业的某个算子的耗时较长，影响了整体的计算速度，需要重新调整该算子的并行度，以提升作业的整体处理速度；又比如，发现某个运行的作业的资源利用率不高，可以减少一些算子的并行度）。对于Flink而言，当某个算子的并行实例数或算子的子任务数发生了变化，应用需要关停或新启动一些算子子任务，某些原来在某个算子子任务上的状态数据需要平滑地更新到新的算子子任务上。</p>
<p>如下图所示，Flink的Checkpoint机制，为状态数据在各算子间迁移提供了保障。Flink定期将分布式节点上的状态数据生成快照（SNAPSHOT），并保存到分布式存储（如rocksDb或hdfs）上。横向伸缩后，算子子任务的个数发生变化，子任务重启，相应的状态从分布式存储上重建即可。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/76e0af3248d994f1f376.png"/></p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104171679">https://zhuanlan.zhihu.com/p/104171679</a></p>
<p>以扩容为例，上图将算子B和C进行了扩容（并行度从2调整到了3）。算子的扩缩容涉及到状态的重新分配。显然，Keyed State和Operator State重新分配机制是不一样的。相对来说，Operator State的重新分配更为简单，有两种常见的状态分配方式：一种是均匀分配，另一种是将所有状态合并，再分发给每个实例上。下面以Source接入kafka消息为例，先介绍Operator State的重新分配机制。假如接入消息的topic的分区数为5，且Source一开始的并行度为1，扩容后的并行度为2，则扩容前后Operator State的重新分配结果如下图（缩容为反向过程）：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/9cea2264ddf667c10be0.png"/></p>
<p>我们接着来看Keyed State的重新分配。按照最简单的思路考虑，Flink中的key是按照hash(key) % parallelism的规则分配到各个Sub-Task上去的，那么我们可以在缩放完成后，根据新分配的key集合从hdfs直接取回对应的Keyed State数据。下图示出并行度从3增加到4后，Keyed State中各个key的重新分配过程。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/8587375ef2a1773d0e60.png"/></p>
<p>图片来源：<a href="https://blog.csdn.net/nazeniwaresakini/article/details/104220138">https://blog.csdn.net/nazeniwaresakini/article/details/104220138</a></p>
<p>在Checkpoint发生时，状态数据是顺序写入文件系统的。但从上图可以看出，从状态恢复时是随机读的，效率非常低下。并且缩放之后各SubTask处理的key有可能大多都不是缩放之前的那些key，无形中降低了<strong>本地性</strong>。为了解决这两个问题，在FLINK-3755对Keyed State专门引入了Key Group，下面具体看看。以下引自Flink官方文档：<br/></p>
<div>
<div>
<p>Keyed State is further organized into so-called Key Groups. Key Groups are the atomic unit by which Flink can redistribute Keyed State; there are exactly as many Key Groups as the defined maximum parallelism. During execution each parallel instance of a keyed operator works with the keys for one or more Key Groups.</p>
</div>
</div>
<p>翻译一下，Key Group是Keyed State分配的原子单位，且Flink作业内Key Group的数量与Flink作业（注意不是算子的最大并行度）的最大并行度相同，也就是说<strong>Key Group的索引位于[0, maxParallelism - 1]的区间内</strong>。每个Sub-Task都会处理一个到多个Key Group，在源码中，以KeyGroupRange这一数据结构来表示。即KeyGroupRange实际上是多个连续的Key Group组成的闭区间（[startKeyGroup, endKeyGroup]）。</p>
<p>引入Key Group的同时，又带来了两个新的问题：</p>
<ol><li>如何决定一个key该分配到哪个Key Group中？</li>
<li>如何决定一个SubTask该处理哪些Key Group（即对应的KeyGroupRange）？</li>
</ol><p>对于第一个问题，Flink实际上是对原始的key进行两重哈希（一次取hashCode，一次做MurmurHash）之后，再对<strong>最大并行度</strong>取余，得到Key Group的索引。</p>
<p>而对于第二个问题，由源码可知，SubTask处理哪些Key Group是由<strong>并行度</strong>、<strong>最大并行度</strong>和<strong>算子实例</strong>（即SubTask）<strong>的ID</strong>共同决定的。简单来说就是，Flink会将[0, maxParallelism - 1]的区间内的Key Group尽可能均匀地、连续地分给各SubTask。按照这样的Key Group分配逻辑，上一节中Keyed State重分配的场景就会变成下图所示（设最大并行度为10）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/3cc8ee0d1ecbdd553ccb.png"/></p>
<p>图片来源：<a href="https://blog.csdn.net/nazeniwaresakini/article/details/104220138">https://blog.csdn.net/nazeniwaresakini/article/details/104220138</a><br/></p>
<p>很明显，将Key Group作为Keyed State的基本分配单元之后，上文所述本地性差和随机读的问题都部分得到了解决。当然还要注意，最大并行度对Key Group分配的影响是显而易见的，因此不要随意修改最大并行度的值。<br/></p>
<p>小结：Key Group机制，是将原始key进行<strong>有限分组</strong>，并将分组作为子任务分配的最小单位，从而在原始key随机性的前提下实现了系统期望的本地性。</p>
<p>ps：本小节主要内容摘自：<a href="https://zhuanlan.zhihu.com/p/104171679">https://zhuanlan.zhihu.com/p/104171679 </a>和 <a href="https://blog.csdn.net/nazeniwaresakini/article/details/104220138">https://blog.csdn.net/nazeniwaresakini/article/details/104220138</a></p>
<h3>8、Flink数据交换<br/></h3>
<p>由前面的介绍可知，Flink服务端的JobManager和TaskManager之间、两个TaskManager之间都存在相互通信。本小节就来详细介绍它们之间的通信机制和过程。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/5d729882282a27b8687e.png"/></p>
<p>图片来源：<a href="https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks">https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks</a></p>
<p>Flink的数据交换遵循以下两条原则：</p>
<div>
<ol><li>The control flow for data exchange (i.e., the message passing in order to initiate the exchange) is receiver-initiated, much like the original MapReduce.</li>
<li>The data flow for data exchange, i.e., the actual transfer of data over the wire is abstracted by the notion of an IntermediateResult, and is pluggable. This means that the system can support both streaming data transfer and batch data transfer with the same implementation.</li>
</ol></div>
<p>简单翻译一下就是，1，数据交换的<strong>控制流</strong>是由数据的接收方触发的（当然，需要发送方先通知接收方数据已经准备就绪）；2，数据交换的<strong>数据流</strong>是通过抽象的概念“<strong>中间结果</strong>”（<strong>IntermediateResult</strong>）来实现的，而且数据流是可插拔的。</p>
<p>关于这两条原则，下面会进一步详细介绍。不过为了能更好地理解Flink的数据交换，我们需要先了解以下一些重要概念：</p>
<p>JobManager：作为Flink服务端的master节点，负责任务的分配、协调、故障恢复。此外，它还保存着作业（Job）实际运行时数据流的<strong>执行逻辑拓扑图</strong>，即<strong>ExecutionGraph</strong>。</p>
<p>TaskManager：作为Flink服务端的worker节点，通过多线程执行（子）任务。每一个TM还包含一个CommunicationManager（多个任务之间共享）和一个MemoryManager（也是多个任务之间共享）。TM之间通过TCP连接进行通信。这里需要强调的是，<strong>在Flink中，一个TaskManager内的多个子任务和另一个TaskManager内的多个子任务之间复用同一个网络连接来实现通信</strong>（同一个TaskManager内部的任务之间也可能需要通信，但内部通信不需要走网络连接，而是本地线程间的通信机制）。</p>
<p>ExecutionGraph：如下图所示，<strong>执行逻辑拓扑图</strong>由EV、IRP和EE构成。其中EV代表<strong>计算任务</strong>（即ExecutionVertex）本身，而IRP代表计算任务产生的<strong>中间结果分区</strong>（<strong>IntermediateResultPartition</strong>，简写为IRP或者RP），EE（ExecutionEdge）由IRP指向EV，代表该计算任务负责消费上游任务产生的计算结果。</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/dbe1fcd24c486fc5d7d9.png"/></p>
<p>图片来源：<a href="https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks">https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks</a><br/></p>
<p>ResultPartition：<strong>中间结果分区</strong>代表单个任务计算后输出的一块数据写缓存区（BufferWriter）。一个RP实际上包含多个Result Subpartition（简写为RS）。</p>
<p>ResultSubpartition：<strong>中间结果分区</strong>由上游的计算任务（EV）计算得到，其中的一个子分区对应下游的一个计算任务（EV）。<br/></p>
<p>下面这幅图是对上面这些概念的一个汇总图示：</p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks">https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks</a><br/></p>
<p>上图中JobManager保存着执行逻辑拓扑图。两个计算节点TaskManager之间通过ConnectionManager管理的tcp进行通信。到此，Flink的主从节点之间数据交换的<strong>数据流</strong>和<strong>控制流</strong>也可以汇总如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/b093a805b48fad0c746f.png"/></p>
<p>图片来源：<a href="https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks">https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks</a><br/></p>
<p>上图为一个简单的并行度为2的map-reduce作业的示例。图中有2个TaskManager，每个TaskManager各有一个Map任务和一个Reduce任务。图中的粗箭头代表<strong>数据流</strong>，细箭头代表消息通知。还记得前面提到过“数据交换的<strong>控制流</strong>是由数据的接收方触发的”这一原则么？这里就来详细说明这一原则。</p>
<p>首先，M1计算得到中间结果RP1（箭头1）。当RP变得可用之后，它会通知JobManager（箭头2）。JobManager会将RP可用的消息通知到R1和R2（箭头3a和3b）。收到通知后，R1和R2会发起数据交换的请求（箭头4a和4b），该请求会触发数据的交换（箭头5a和5b）。由此可见，数据交换本质上是采用了一种消费端的“<strong>拉</strong>”模式。</p>
<p>关于TaskManager内部线程之间，以及不同TaskManager的线程之间具体的通信机制，这里不再做进一步介绍，感兴趣的可以查阅相关官方文档或查阅源码。</p>
<p>ps：本小节主要内容摘自：<a href="https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks">https://cwiki.apache.org/confluence/display/FLINK/Data+exchange+between+tasks</a></p>
<h3>9、时间语义</h3>
<p>流式计算的应用通常都有强实时性或时间敏感性，因此在流式处理中，算子对流中的数据进行处理时采用不同的时间，就会直接影响算子的计算结果。目前Flink支持三种时间语义，如下图所示：</p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/concepts/time/">https://ci.apache.org/projects/flink/flink-docs-master/docs/concepts/time/</a></p>
<ul><li><strong>处理时间（Processing time）</strong></li>
</ul><p>处理时间是三种时间语义里最简单的一种。它跟具体执行任务的主机的系统时间有关。处理时间不要求在数据流与计算节点之间进行协同，因此相对于其他两种时间，基于处理时间的流计算作业在执行时，无需等待水位线（它是一种表示时间进度的信号机制，本节后续会介绍）的到来触发窗口，所以可以提供较低的延迟。</p>
<p>然而，在分布式和异步的场景中，处理时间有时候不能保证处理结果的正确性，因为它可能无法真实地反映事件的实际发生时间。举例而言，现在需要计算一个网站的QPS然后绘制出变化曲线图，访问请求被记录并收集到消息系统中，最终通过流处理系统来统计。因为某些原因，流处理系统出现故障，导致它不得不下线一段时间（假设宕机时长为十分钟）。在这段时间内持续产生的事件仍然堆积在消息系统中（假设采集模块仍然正常工作）。当你的流处理系统恢复并重新上线后。如果你以处理时间作为基准，那么这中断十分钟的请求日志就仿佛是突然到来的请求一样。因此，绘制的曲线图将会呈现一个非常短区间的尖锐脉冲，而中断的那段时间反映在图表中则几乎为零，这显然是不符合事实的。所以处理时间常常应用在不关心事件发生的实际时间，只希望快速得到结果的场景中。<strong><br/></strong></p>
<ul><li><strong>事件时间（Event time）</strong></li>
</ul><p>事件时间是指每个独立事件发生时所在设备上的时间。事件时间通常在事件进入Flink之前就已经被内嵌在事件中了，其时间戳可以从事件中提取出来。举例而言，一个小时的事件时间窗口将包含所携带的事件时间落在这一小时内的所有事件，而不管它们什么时候并且以怎样的顺序到达Flink。事件时间能够保证正确性，哪怕事件是无序的、延迟的甚至是从持久层的日志或者备份中恢复的。事件时间依赖于事件本身，而不依赖于执行任务的主机的时钟。通常，基于事件时间消费外部事件的source需要定义如何生成事件时间的水位线，以及如何从事件消息中提取事件时间。<strong><br/></strong></p>
<ul><li><strong>摄入时间（Ingestion time）</strong></li>
</ul><p>摄入时间指事件进入Flink的时间。作业在执行时，每个事件以执行source运算符对应的任务的节点的当前时钟作为时间戳。摄入时间介于事件时间和处理时间之间。跟处理时间相比，其开销会稍微大一点，但会更接近正确的结果。因为摄入时间使用稳定的时间戳，一旦到达source，事件时间戳就会被分配，在不同窗口之间流动的事件将始终携带着最初生成的时间戳，而对处理时间而言，由于各节点本地系统时钟的差异以及传输延迟等因素，原先在同一个窗口中的元素在后续可能会被分配到不同的窗口中去，从而导致了处理结果上的差异。跟事件时间相比，摄入时间不能处理任何的乱序或者延迟事件，但这些基于摄入时间的程序也无需指定生成水位线方式，且其延迟会比事件时间更小。摄入时间更多地被当作事件时间来处理，具备自动的时间戳分配以及水位线生成机制。<strong><br/></strong></p>
<p>小结：由于处理时间不依赖水位线，所以水位线实际上只在基于事件时间和摄入时间这两种时间类型下起作用。</p>
<h3>10、水位线</h3>
<p>支持事件时间的流处理引擎需要一种度量事件时间进度的方式。例如，一个运算符基于大小为一小时的事件时间窗口进行计算，需要被告知到达下一个完整小时的时间点（因为事件时间不依赖于<strong>当前节点的时钟</strong>），以便该运算符可以结束当前窗口。<br/></p>
<p>在Flink计算引擎中度量事件时间进度的机制被称为水位线（Watermarks），有的也翻译成水印。水位线作为特殊的事件被注入到事件流中流向下游，设其携带时间戳t，则Watermark(t)定义了在一个流中事件时间已到达时间t，同时这也意味着所有的带有时间戳 t’（t’ &lt; t）的事件<strong>应该</strong>已经发生并已被系统处理（这里说应该，是因为实际业务场景中可能还存在已发生但还没被处理的迟到元素，后面会具体介绍如何处理）。<br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/0f60b20bed169b5850c6.png"/></p>
<p>图片来源：<a href="https://blog.csdn.net/weixin_42551508/article/details/112247181">https://blog.csdn.net/weixin_42551508/article/details/112247181</a></p>
<p>通常水位线在source中生成。每个source的并行任务都会生成各自的水位线从而产生并行流中的水位线场景。并行流中的水位线彼此互不依赖，它们在特定的并行source任务中定义各自的事件时间。<br/></p>
<p>随着水位线的流动，它们会在到达下游某个运算符的任务实例时提升该任务的事件时间。一旦某个任务提升了它的事件时间，它也将为下游任务生成新的水位线并输出。</p>
<p>消费多个输入流的任务，例如，跟在keyBy和partition函数之后的运算符的任务，会在它们的每个输入流上跟踪事件时间。任务的当前事件时间则由其所有输入流的最小事件时间决定。</p>
<p>下图展示了事件和水位线流经并行数据流以及并行执行的任务跟踪事件时间的示例：</p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/concepts/time/">https://ci.apache.org/projects/flink/flink-docs-master/docs/concepts/time/</a></p>
<p>从上图中我们看到window运算符的两个并行任务实例都接收上游map运算符的两个并行任务实例的输出作为其输入。以window运算符的第一个子任务为例，它从上游的两个输入流中接收事件时间为29和14的两个元素，基于最小事件时间原则，该任务当前的事件时间为14。<br/></p>
<h3>11、时间窗口</h3>
<p>窗口将无界流切片成一系列有界的数据集。窗口基本上都是基于时间的，不过也有些系统支持基于元组（tuple-based）的窗口，这种窗口可以认为是基于一个逻辑上的时间域，该时间域中的元素包含顺序递增的逻辑时间戳。从窗口所应用到的数据集的完整度来看，窗口要么是对齐的，要么是非对齐的，对齐的窗口可以应用到整个数据集上，而非对齐的窗口只能应用在整个数据集的子集上（比如某些特定的键对应的数据集）。Flink目前支持的窗口类型列举如下：</p>
<ul><li><strong>固定窗口（Fixed Windows）：</strong>有时也称之为翻滚窗口（Tumbling WIndows），固定窗口按固定的时间段或长度（比如小时或元素个数）来分片数据集。固定窗口可应用到数据集中的所有数据上，因此它通常被称为对齐窗口。但有时为了把窗口计算的负荷均匀分摊到整个时间范围内，会把固定窗口的边界时间加上一个随机数，这样的固定窗口则变成了不对齐窗口。</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/flink/0e40cb5c331fb506a4e6.png"/></p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/dev/datastream/operators/windows/">https://ci.apache.org/projects/flink/flink-docs-master/docs/dev/datastream/operators/windows/</a></p>
<ul><li><strong>滑动窗口（Sliding Windows）：</strong>它是固定窗口的一般化形式。由窗口大小以及滑动周期构成（比如以小时作为窗口大小，分钟作为滑动周期）。如果滑动周期小于窗口大小，那么窗口会发生部分重叠；而如果滑动周期跟窗口大小相等，则该窗口就是固定窗口。滑动窗口通常也是对齐的，出于性能考虑某些情况下也可以是非对齐的。需要注意的是，上图为了表明滑动的性质而没有把每个窗口对应到所有的键，实际情况是每个窗口都会对应到所有的键。</li>
</ul><p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/dev/datastream/operators/windows/">https://ci.apache.org/projects/flink/flink-docs-master/docs/dev/datastream/operators/windows/</a><br/></p>
<ul><li><strong>会话窗口（Session Windows）：</strong>它是一种动态窗口，用于在数据的子集上（比如某个键所对应的数据集）捕获一些活跃的阶段性的数据集。通常会话窗口会定义一个超时时间间隙（Gap），任何发生在小于超时时间点的持续时间段内的事件都归属于同一个会话。会话窗口是非对齐窗口。会话窗口常用于用户行为分析，即观察在一个会话窗口内用户的一系列操作所产生的事件。</li>
</ul><p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/dev/datastream/operators/windows/">https://ci.apache.org/projects/flink/flink-docs-master/docs/dev/datastream/operators/windows/</a></p>
<ul><li><strong>更多类型的窗口：</strong></li>
</ul><p>实际上，还在不断迭代的Flink支持更多类型的窗口，展示如下。感兴趣的可以查看最新版的文档。</p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://ci.apache.org/projects/flink/flink-docs-master/docs/learn-flink/streaming_analytics/">https://ci.apache.org/projects/flink/flink-docs-master/docs/learn-flink/streaming_analytics/</a></p>
<h3>12、迟到元素</h3>
<p>现实世界中，在Event Time的语义下，可能会出现Watermark(t)到达某个算子后，仍然有一些时间戳为t’（t’ &lt;= t）的元素随后到达，甚至t’比t小任意值都是有可能的，这些元素就是迟到元素。为了支持小于水位线基准的迟到元素被正确处理，通常需要界定一个合适的允许迟到的最大时间范围，这个范围是权衡的结果，它不可能非常大，因为这将严重拖慢事件时间窗口的计算。</p>
<p>Flink在事件时间窗口中对迟到元素提供了支持并允许设置一个明确的最大允许迟到时间。该值默认为零，也就是说默认情况下，迟到元素将会被删除，而如果设置了该值，在迟到时间范围内的元素仍然会被加入到窗口中，依赖于事件时间触发器的逻辑，迟到的元素可能会导致窗口被重新计算（重新计算可能会产生重复甚至错误的输出，需要考虑去重方案）。<br/></p>
<p>下面的例子展示了迟到元素基于事件时间在固定窗口中的用法：<br/></p>
<div>
<pre>DataStream&lt;Tuple2&lt;String, Integer&gt;&gt; counts = ...

counts
    .keyBy(0)
    .window(TumblingEventTimeWindows.of(Time.minutes(10)))
    .allowedLateness(Time.minutes(1))
    .sum(1);</pre>
</div>
<p> 上面例子的含义是基于事件时间，设定一个10分钟的固定窗口，并允许1分钟的数据延迟。即对于[12:00–12:10)这个窗口而言，当第一个属于此区间的元素到达时，窗口被创建；当水位线超过12:10时，窗口被触发，进行一次sum运算，但窗口内的元素并不会被删除；当水位线超过12:11时，窗口中的元素才被删除。当水位线处于12:10–12:11之间，如果有属于本窗口的迟到元素到达，则会引起窗口的再次触发，再进行一次计算，并输出计算结果。</p>
<p>实际上，对于迟到元素，Flink目前有三种处理迟到数据的方式：</p>
<ul><li>直接将迟到数据丢弃</li>
<li>将迟到数据发送到另一个流（<strong>旁路流</strong>，后面会介绍）</li>
<li>重新执行一次计算，将迟到数据考虑进来，更新计算结果</li>
</ul><h3>13、恰好一次处理</h3>
<p>在分布式的场景中，事件会被不断地传递（delivery）与处理（process），处理的结果可以作为状态保存并用于失败恢复。因此，数据传递与处理语义（delivery semantics）跟容错紧密相关。业界将之划分为三个级别：<br/></p>
<p><strong>- 最多一次（at most once）：</strong>事件可能会丢失但不会被重复传递<br/><strong>- 至少一次（at least once）：</strong>事件不会丢失但可能会被重复传递<br/><strong>- 恰好一次（exactly once）：</strong>事件既不会丢失也不会被重复传递<br/>以上三种传递语义的严谨性是逐个递增的。“最多一次”某种程度上跟没提供任何保证一样，而只有“恰好一次”能够保证计算结果的正确性，因此“恰好一次”的传递语义也意味着正确的结果保证。</p>
<p>Flink的分布式异步快照机制支持“恰好一次”语义，但同样提供了对“至少一次”语义的支持，这给予了用户根据不同场景（比如允许数据重复，但希望延迟尽可能低）进行合理选择的灵活性。</p>
<p>下面我们来分析一下Flink的快照机制对待这两种语义的差异。首先，对于“恰好一次”语义，它意味着系统的快照必须提供这样的保证：在恢复时，每条记录只对运算符状态产生一次影响。例如，如果有一个用户在流中应用元素计数函数，那么统计的结果将总是跟流中元素的真实个数一致，不管有没有发生执行失败还是恢复。需要注意的是，这并不意味着每条数据流过处理引擎仅仅一次。另外，这里的“恰好一次”语义主要指的是Flink自身提供的保证，但并不一定能保证Flink跟外部系统交互时的行为也满足“恰好一次”语义，这属于端到端（end to end）的语义范畴。因为Flink跟外部系统交互是依靠其source和sink两个部件，所以端到端的语义取决于source和sink针对外部系统的连接器的实现，但本质上取决于外部系统是否有结合Flink共同提供“恰好一次”语义保证的能力。Flink支持跟某些外部系统在某些端（比如在source端跟Apache Kafka，在sink端跟hdfs）的“恰好一次”语义，关于更多端到端的“恰好一次”的语义保证，可以参考官方给出的详细列表和用法。</p>
<h3>14、Checkpoint和Savepoint</h3>
<p>Flink定期将分布式节点上的状态数据保存到远程存储设备（比如rocksDB或者hdfs等）上，故障发生后从之前的备份中恢复，整个被称为Checkpoint机制，它为Flink提供了Exactly-Once的计算保障。本小节就来详细介绍一下checkpoint的原理。<br/></p>
<p>首先，一个简单的Checkpoint的大致流程包含以下三步：</p>
<ul><li>暂停处理新流入数据，将新数据缓存起来。</li>
<li>将算子子任务的<strong>本地状态数据</strong>（只拷贝状态数据，新流入的流数据不需要拷贝）拷贝到一个远程的持久化存储上。</li>
<li>继续处理新流入的数据，包括刚才缓存起来的数据。</li>
</ul><p>下面详细进行说明。</p>
<p>在介绍Flink的快照流程之前，我们需要先了解检查点的分界线（Checkpoint Barrier）概念。它和Watermark类似，也是作为特殊事件被注入到事件流中流向下游。如下图所示，Checkpoint Barrier被插入到数据流中，它将数据流切分成段。Flink的Checkpoint逻辑是，一段新数据流入导致状态发生了变化，Flink的算子接收到Checpoint Barrier后，对状态进行快照。每个Checkpoint Barrier有一个ID，表示该段数据属于哪次Checkpoint。如图所示，当ID为n的Checkpoint Barrier到达每个算子后，表示要对n-1和n之间状态的更新做快照。Checkpoint Barrier有点像Event Time中的Watermark，它被插入到数据流中，但并不影响数据流原有的处理顺序。</p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104601440">https://zhuanlan.zhihu.com/p/104601440</a></p>
<p>接下来，我们构建一个并行数据流图，用这个并行数据流图来演示Flink的分布式快照机制。这个数据流图有两个Source子任务，数据流会在这些并行算子上从Source流动到Sink。</p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104601440">https://zhuanlan.zhihu.com/p/104601440</a><br/></p>
<p>首先，Flink的检查点协调器（Checkpoint Coordinator）触发一次Checkpoint（Trigger Checkpoint），这个请求会发送给Source的各个子任务。<br/></p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104601440">https://zhuanlan.zhihu.com/p/104601440</a><br/></p>
<p>各Source算子子任务接收到这个Checkpoint请求之后，会将自己的状态写入到状态后端，生成一次快照，并且会向下游广播Checkpoint Barrier。<br/></p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104601440">https://zhuanlan.zhihu.com/p/104601440</a><br/></p>
<p>Source算子做完快照后，还会给Checkpoint Coodinator发送一个确认，告知自己已经做完了相应的工作。这个确认中包括了一些元数据，其中就包括刚才备份到State Backend的状态句柄，或者说是指向状态的指针。至此，Source完成了一次Checkpoint。跟Watermark的传播一样，一个算子子任务要把Checkpoint Barrier发送给所连接的所有下游算子子任务。<br/></p>
<p>对于下游算子来说，可能有多个与之相连的上游输入，我们将算子之间的边称为通道。Source要将一个ID为n的Checkpoint Barrier向所有下游算子广播，这也意味着下游算子的多个输入里都有同一个Checkpoint Barrier，而且不同输入里Checkpoint Barrier的流入进度可能不同。Checkpoint Barrier传播的过程需要进行对齐（Barrier Alignment），我们从数据流图中截取一小部分来分析Checkpoint Barrier是如何在算子间传播和对齐的。<br/></p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104601440">https://zhuanlan.zhihu.com/p/104601440</a><br/></p>
<p>如上图所示，对齐分为四步：</p>
<ul><li>算子子任务在某个输入通道中收到第一个ID为n的Checkpoint Barrier，但是其他输入通道中ID为n的Checkpoint Barrier还未到达，该算子子任务开始准备进行对齐。</li>
<li>算子子任务将第一个输入通道的数据缓存下来，同时继续处理其他输入通道的数据，这个过程被称为对齐。</li>
<li>第二个输入通道的Checkpoint Barrier抵达该算子子任务，该算子子任务执行快照，将状态写入State Backend，然后将ID为n的Checkpoint Barrier向下游所有输出通道广播。</li>
<li>对于这个算子子任务，快照执行结束，继续处理各个通道中新流入数据，包括刚才缓存起来的数据。</li>
</ul><p>数据流图中的每个算子子任务都要完成一遍上述的对齐、快照、确认的工作，当最后所有Sink算子确认完成快照之后，说明ID为n的Checkpoint执行结束，Checkpoint Coordinator向State Backend写入一些本次Checkpoint的元数据。<br/></p>
<p>[图片未保存到本地]</p>
<p>图片来源：<a href="https://zhuanlan.zhihu.com/p/104601440">https://zhuanlan.zhihu.com/p/104601440</a><br/></p>
<p>之所以要进行对齐，主要是为了保证一个Flink作业所有算子在执行快照时的状态是一致的。也就是说，某个ID为n的Checkpoint Barrier从前到后流入所有算子子任务后，所有算子子任务都能将同样的一段状态数据写入快照。<br/></p>
<p>以上就是Checkpoint的简单流程，很显然，这个流程仍存在一些潜在的问题：</p>
<ul><li>每次进行Checkpoint前，都需要暂停处理新流入数据，然后开始执行快照，假如状态比较大，一次快照可能长达几秒甚至几分钟。</li>
<li>Checkpoint Barrier对齐时，必须等待所有上游通道都处理完，假如某个上游通道处理很慢，这可能造成整个数据流堵塞。</li>
</ul><p>针对这些问题Flink已经有了一些解决方案，并且还在不断优化。</p>
<p>对于第一个问题，Flink提供了异步快照（Asynchronous Snapshot）的机制。当实际执行快照时，Flink可以立即向下广播Checkpoint Barrier，表示自己已经执行完自己部分的快照。同时，Flink启动一个后台线程，它创建本地状态的一份拷贝，这个线程用来将本地状态的拷贝同步到State Backend（负责持久化存储数据）上，一旦数据同步完成，再给Checkpoint Coordinator发送确认信息。拷贝一份数据肯定占用更多内存，这时可以利用写入时复制（Copy-on-Write）的优化策略。Copy-on-Write指：如果这份内存数据没有任何修改，那没必要生成一份拷贝，只需要有一个指向这份数据的指针，通过指针将本地数据同步到State Backend上；如果这份内存数据有一些更新，那再去申请额外的内存空间并维护两份数据，一份是快照时的数据，一份是更新后的数据。</p>
<p>对于第二个问题，Flink允许跳过对齐这一步，或者说一个算子子任务不需要等待所有上游通道的Checkpoint Barrier，直接将Checkpoint Barrier广播，执行快照并继续处理后续流入数据。为了保证数据一致性，Flink必须将那些较慢的数据流中的元素也一起快照，一旦重启，这些元素会被重新处理一遍。</p>
<p>下面我们来看下在Checkpoint机制下的重启恢复流程。<br/></p>
<p>Flink的重启恢复逻辑相对比较简单：</p>
<ul><li>重启应用，在集群上重新部署数据流图。</li>
<li>从持久化存储上读取最近一次的Checkpoint数据，加载到各算子子任务上。</li>
<li>继续处理新流入的数据。</li>
</ul><p>这样的机制就保证了Flink内部状态的Excatly-Once一致性。至于端到端的Exactly-Once一致性，要根据Source和Sink的具体实现而定。当发生故障时，一部分数据有可能已经流入系统，但还未进行Checkpoint，Source的Checkpoint记录了输入的Offset；当重启时，Flink能把最近一次的Checkpoint恢复到内存中，并根据Offset，让Source从该位置重新发送一遍数据，以保证数据不丢不重。像Kafka等消息队列是提供重发功能的，而<code>socketTextStream</code>就不具有这种功能，也意味着不能保证Exactly-Once投递保障。<br/></p>
<p>最后，简单来说下Checkpoint和Savepoint的区别。</p>
<p><b>Flink Checkpoint 是一种容错恢复机制。</b>这种机制保证了实时程序运行时，即使突然遇到异常也能够进行自我恢复。Checkpoint 对于用户层面，是透明的，用户会感觉程序一直在运行。Flink Checkpoint 是 Flink 自身的系统行为，用户无法对其进行交互，用户可以在程序启动之前，设置好实时程序 Checkpoint 相关参数，当程序启动之后，剩下的就全交给 Flink 自行管理。当然在某些情况，比如 Flink On Yarn 模式，某个 Container 发生 OOM 异常，这种情况程序直接变成失败状态，此时 Flink 程序虽然开启 Checkpoint 也无法恢复，因为程序已经变成失败状态，所以此时可以借助外部参与启动程序，比如外部程序检测到实时任务失败时，从新对实时任务进行拉起。<br/></p>
<p><b>Flink Savepoint 你可以把它当做在某个时间点程序状态全局镜像，以后程序在进行升级，或者修改并发度等情况，还能从保存的状态位继续启动恢复。</b>Flink Savepoint 一般存储在hdfs上面，它需要用户主动进行触发。如果是用户自定义开发的实时程序，比如使用DataStream进行开发，建议为每个算子定义一个 uid，这样我们在修改作业时，即使导致程序拓扑图改变，由于相关算子 uid 没有变，那么这些算子还能够继续使用之前的状态，如果用户没有定义 uid ， <strong>Flink 会为每个算子自动生成 uid，如果用户修改了程序，可能导致之前的状态程序不能再进行复用</strong>。<br/></p>
<p>Checkpoint和Savepoint的差异对比如下：</p>
<ol><li><strong>概念</strong>：Checkpoint 是 自动容错机制 ，Savepoint 是程序全局状态镜像 。</li>
<li><strong>目的</strong>： Checkpoint 是程序自动容错，快速恢复 。Savepoint是 程序修改后继续从状态恢复，程序升级等。</li>
<li><strong>用户交互</strong>：Checkpoint 是 Flink 系统行为 。Savepoint一般是由用户触发。</li>
<li><strong>状态文件保留策略</strong>：Checkpoint默认会被删除，可以设置CheckpointConfig中的参数进行保留 。Savepoint会一直保存，除非用户主动删除 。</li>
</ol><p>ps：本小节主要内容摘自：<a href="https://zhuanlan.zhihu.com/p/104601440">https://zhuanlan.zhihu.com/p/104601440</a></p>
<h3>15、旁路流</h3>
<p>在一些业务场景中，一个流中可能有多种类型的数据，比如订单：有线上订单，有线下订单。当需要将不同类型的数据进行分别处理，比如 写入到不同的数据表或者join 不同的其他流时，这个时候使用旁路流就比较合适。</p>
<p>示例代码如下：</p>
<div>
<pre>private static final OutputTag&lt;T&gt; outputTag = new OutputTag&lt;&gt;("tagName", TypeInformation.of(T.class));   //T为类泛型，具体业务中替换

SingleOutputStreamOperator&lt;T&gt; mainDataStream = entityDataStream
                 .process(new ProcessFunction&lt;T,T&gt;() {
                    @Override
                    public void processElement(T entity, Context context,
                            Collector&lt;T&gt; collector) throws Exception {
                        //collector为常规流
                        collector.collect(entity);
                        //旁路流
                        context.output(outputTag, entity);
                    }
                });

//旁路输出流
DataStream&lt;ActivityActionEntity&gt; entityDataStream outputStream = mainDataStream.getSideOutput(ipRiskCalcTag);</pre>
</div>
<h3>16、示例代码</h3>
<p>最后，本文给出一个简单的Flink作业（Job）的完整的java示例代码。代码监听kafka消息，并基于滑动窗口（窗口大小为10s，滑动大小为5s）统计消息中相同key在窗口内出现的次数，将此处实时输出到另外一个kafka。示例代码如下：</p>
<div>
<pre>public class FlinkJobDemo {

    public static void main(String[] args) throws Exception {

        // 1、创建流处理的执行环境
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        //使用eventTime需要设置，否则不生效，设置了EventTime后面就需要设置watermark
        env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime);
        //设置watermark产生间隔，默认为200ms
        env.getConfig().setAutoWatermarkInterval(1000);

        //2、设置输入流dataStream
        FlinkKafkaConsumer011&lt;String&gt; kafkaSource =
                getKafkaSource("监听的kafka消息的服务器ip + port", "消费组",
                        Collections.singletonList("kafka 消息 topic"));
        DataStream&lt;String&gt; dataStream = env.addSource(kafkaSource);

        //3 反序列化stream  T为泛型，具体业务中替换
        DataStream&lt;T&gt; entityDataStream = dataStream.map(data -&gt; {
            KafkaMessage message = JSON.parseObject(data, KafkaMessage.class);
            T entity = JSON.parseObject(message.getData(), T.class);
            return entity;
        });

        //4 设置消息事件时间戳提取方式及水文线，并将事件映射成Tuple
        DataStream&lt;Tuple2&lt;String, Integer&gt;&gt; keyedDataStream = entityDataStream
                //设置事件的时间戳提取方式和水文线与时间戳的关系
                .assignTimestampsAndWatermarks(new BoundedOutOfOrdernessTimestampExtractor&lt;T&gt;(Time.of(5,
                        TimeUnit.SECONDS)) {
                    @Override public long extractTimestamp(T t) {
                        return t.getActionTs();   //返回事件时间
                    }

                })//将事件映射成Tuple2，方便后面基于窗口统计
                .flatMap(new FlatMapFunction&lt;T, Tuple2&lt;String, Integer&gt;&gt;() {
                    @Override public void flatMap(T entity, Collector&lt;Tuple2&lt;String, Integer&gt;&gt; collector) throws Exception {
                        Tuple2&lt;String, Integer&gt; tuple = Tuple2.of(entity.getKey(), 1);
                        collector.collect(tuple);
                    }
                });

        //5 滑动窗口进行分组聚合统计(keyBy：将key相同的分到一个组中)
        DataStream&lt;Tuple2&lt;String, Integer&gt;&gt; windowStream = keyedDataStream
                .keyBy(0)
                .timeWindow(Time.seconds(10), Time.seconds(5))
                .sum(1);

        //6 普通流调用Sink，输出kafka
        windowStream.map(data -&gt; {
            Map&lt;String, Object&gt; kafkaMsgMap = new HashMap&lt;&gt;();
            kafkaMsgMap.put("key", data.f0);
            kafkaMsgMap.put("count", data.f1);
            return JSON.toJSONString(kafkaMsgMap);
        }).addSink(getKafkaSink("消息需要发送到的kafka服务器 ip + port", "kafka消息topic"));

        //启动(这个异常不建议try...catch... 捕获,因为它会抛给flink,flink根据异常来做相应的处理)
        env.execute("FlinkJobDemo");
    }


    public static FlinkKafkaConsumer011&lt;String&gt; getKafkaSource(String bootstrap, String consumer,
            List&lt;String&gt; topics) {
        Properties properties = new Properties();
        properties.put("bootstrap.servers", bootstrap);
        properties.put("group.id", consumer);
        properties.put("enable.auto.commit", "true");
        properties.put("auto.commit.interval.ms", "30000");
        properties.put("max.poll.interval.ms", "8000");
        properties.put("max.poll.records", "16000");
        properties.put("key.deserializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.deserializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("auto.offset.reset", "earliest");
        return new FlinkKafkaConsumer011&lt;&gt;(
                topics,
                new SimpleStringSchema(),
                properties);
    }

    public static FlinkKafkaProducer011&lt;String&gt; getKafkaSink(String bootstrap, String topic) {
        Properties properties = new Properties();
        properties.put("bootstrap.servers", bootstrap);
        properties.put("request.timeout.ms", "120000");
        return new FlinkKafkaProducer011&lt;&gt;(
                topic,
                new SimpleStringSchema(),
                properties
        );
    }

    /**
     * 消息体中的对象实例
     */
    @Data
    public static class T {
        private long actionTs;
        private String key;
    }

}
</pre>
</div>
<p> </p>
<h3>最后声明</h3>
<p>1、实际上，要想对Flink有更深入的了解，仅阅读本文肯定不够的哈。本文只是提纲挈领地将Flink的一些重要概念做了介绍，让大家对Flink有一个整体的认知，对Flink的进一步深入了解需要在实际的业务实践中进行，所谓实践出真知。</p>
<p>2、本文部分篇幅直接摘自其他博客并在其基础上补充了一些自己的理解，其目的在于系统地介绍Flink，若有侵权，请联系本人删除。</p> 
{% endraw %}
