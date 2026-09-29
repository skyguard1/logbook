---
title: "Gemini-2.0：基于微信Flink on K8S 的应用层稳定性优化及应用合集沉淀"
date: 2022-03-30 10:44:11
categories:
  - 算法
  - 数据工程与系统实践
---

{% raw %}

<h1>一、Flink的高可用要求</h1>
<p>        Flink作为一款优秀的流处理组件在实时流计算业务中发挥着重要的作用，而实时计算往往承担着实时样本、实时特征、实时BI等场景的需求。在这些场景下任务的稳定性(稳定，准确，实时)相对于离线批处理有着更高的要求。Flink的稳定性可以从两个方面去考虑：</p>
<ul><li>平台侧：平台侧需要提高作业提交，资源调度，运行环境以及相关依赖组件的高可用和稳定性。</li>
<li>应用侧：应用侧则需要从应用侧角度出发，解决诸如反压、OOM等性能问题，逻辑失败、数据异常等逻辑问题以及全链路上的容灾和抖动等稳定性问题。</li>
</ul><p>   本文主要介绍在应用层面上的一些稳定性优化实践。</p>
<h1>二、应用层的稳定性优化</h1>
<p><br/></p>
<h2>1、状态监控与预警</h2>
<p>        Flink作业通过Metrics将运行时的指标暴露给外部系统。Metrics类型包括Counters(用来计数),  Gauges(用来统计k-v值)，Histograms(用来统计分布) 和 Meters(用来统计吞吐)。Flink自带的指标可以在其官方文档上查阅<a href="https://nightlies.apache.org/flink/flink-docs-master/zh/docs/ops/metrics/#system-resources">Flink自带metric</a>，这些指标覆盖了大部分衡量作业稳定性所需，其余部分的指标通过在任意的RichFunction通过调用getRuntimeContext().getMetricGroup()</p>
<p>获取MetricGroup对象并上报自定义Metric。</p>
<p>        在原生的Flink UI页面可以通过Metric监控看到算子级别的监控 ，如下图：     <img alt="" loading="lazy" src="/logbook/images/algorithm/3cb35e8e0c4b79b22c9c.png"/></p>
<p>        但是使用Flink UI查看Metric存在以下问题：1、指标较多需要逐个筛选查看; 2、指标精确到slot粒度，排查某个算子的问题需要逐个slot查看；3、作业失败后无法查看无法事后追查问题。<br/>        基于此，我们采用将指定平台Metrics和自定Metrics上报到全景的方式，通过开发自定义Reporter将指标上报到全景监控，Reporter根据自身需求定制开发，随用户Jar一同提交运行。<img alt="" loading="lazy" src="/logbook/images/algorithm/d188e010fefa3976eb67.png"/></p>
<p>     这里我们按照4个维度进行划分：</p>
<ul><li>Pipeline维度：一条Pipeline代表一个具体的业务线，包含多个任务，一般任务之间具有血缘关系。</li>
<li>任务维度：一个具体的Flink作业，包含一个或者多个算子(链)。</li>
<li>算子维度：一个Flink作业中的每一个具体的算子(链)，包含多个Metrics。</li>
<li>Metric维度：具体的每一个指标。<br/><img alt="" loading="lazy" src="/logbook/images/algorithm/def78037dcb9f8cc7cce.png"/><br/></li>
</ul><p>       这样划分的好处是既可以覆盖到每一个Flink作业的情况，又可以从整个业务线的角度出发来把握整个Pipeline的稳定性以及按照Pipeline维度来配置告警。我们根据业务中的实际需求选择一些非常常用的指标，并进行加工后上报。常用的指标有：CPU负载、内存使用率、反压指标、处理耗、checkpoint耗时以及GC相关的指标，并同时上报均值与最大值。</p>
<p>       Metrics指标的使用：使用metrics指标可以极大程度上帮助定位和预知Flink作业存在的性能问题。比如常见的<strong>反压问题</strong>, 通过网络buffer处理得到的反压指标可以精确定位到具体是有哪一个算子导致的反压，通过耗时监控和数据监控可以解释反压的原因并指导优化。对于不同的任务可以根据实际需求配置不同程度的告警以提前预警性能问题并提前做出调整，如对反压指标配置[0.5,1]之间的告警可以在其发生严重反压之前引起注意。例如对demoPPL配置堆内存使用率告警<br/><img alt="" loading="lazy" src="/logbook/images/algorithm/c8d4f57c8e14e0735245.png"/><br/></p>
<p>可以对整个业务线下的所有任务进行堆内存使用监控和预警，从而可以提前做好干预(扩容或者配置调整)预防故障的发生。</p>
<p><br/> </p>
<h2>2、容错能力</h2>
<p>       配置合适的重启策略：Flink有以下三种重启策略：1、固定延迟重启策略，重启策略会按照固定的等待时间在一个给定的次数范围内来重启Job，超过了最大的重启次数将最终失败。2、失败率重启策略，在Job失败后会重启，但是超过失败率后，Job会最终被认定失败。3、无重启策略，Job直接失败，不会尝试进行重启。</p>
<p>       在实际生产环境中，由于异常导致的失败不可避免，采用失败率重启策略不仅可以大大减少任务失败停止并重新提交的时间开销，又能避免极端情况下固定延迟策略长期重启不成功的状况。<br/>        状态的使用与持久化: 使用MapState 和 ValueState来存储中间的状态，通过并继承CheckpointedFunction来实现具体的Snapshot逻辑将状态持久化，这样在作业重启或者手动变更的时候，可以使用CheckPoint来恢复来状态，避免缓存或者中间结果的丢失。</p>
<p>       At Least Once 与 Exactly Once 模式</p>
<p>       Source端：采用At Least Once模式，如图所示</p>
<p>                 <img alt="" loading="lazy" src="/logbook/images/algorithm/21487cc49c0c155549df.png"/></p>
<p>       作业会周期性的保存CheckPoint来持久化Source端的游标和各个算子的状态数据，当故障发生时会从上一个CheckPoint恢复，Source端会读取CheckPoint记录的数据源的游标并从游标处从新消费数据，其他的算子的状态也从CheckPoint恢复，以保障Source端是At Least Once模式。</p>
<p>       Sink端：Sink端不做任务处理的情况下，整个链路是At Least Once模式的。在部分场景下我们通过实现Sink接口的幂等性来保证端到端的Exactly Once。</p>
<h2>3、大作业优化</h2>
<p>       大作业是指消耗资源较多，运行图复杂的作业。这类作业往往需要的TaskManager数量和Slot数量较多，按照官方的资源申请和分配策略，申请和分配是同时进行。这种方式不能保证每个TaskManager上处理不同算子的Slot的分布的均衡性，尤其是Source算子，在不同TaskManager上的分配不均会导致不同TaskManager上流量不均。如图是一个常见的的Source + FlatMap + Sink 的网络图示例，资源分配为 16 TaskManager* 32 Slot:</p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm/981dd7907595af913de0.png"/></p>
<p>      数据源为64个分区的Pulsar数据，对应64个Slot进行处理，FlatMap和Sink对应复杂的操作和IO需要的并发更大。理想状态是64个分区均摊到16个TaskManager上以保证Source端处理的数据量一致。然而实际情况可能如下：<br/>     <br/>               <img alt="" loading="lazy" src="/logbook/images/algorithm/95feb2786910a7a62889.png"/></p>
<p>      Source算子只分布在少量的Tm上且分布不均，Sink算子也有同样的问题，这种会导致不同TaskManager上的流量和内存使用不均，这种不均导致部分的TaskManager成为整个作业的短板，最容易造成反压和OOM。</p>
<p>       造成这种现象的原是Flink在申请资源和分配资源的时候，没有考虑到用户的拓扑逻辑进行的随机分配导致某些类型的算子在不同的TaskManager上分布不均。 缓解这类的问题可以从两个方面考虑：<br/>       一是从调度侧优化，需要改动Flink底层代码，按照算子类型进行全局编排调度，目前等公司在自己的版本中均有实现；   二是在应用层优化，通过减少slot数并尽可能的形成算子链来实现Slot的均匀分布，这种在开源的Flink版本上就能实现。如下图，上面示例中的三个算子形成一个并行度为64的算子链，不仅个TaskManager的流量分布均衡而且省去了TaskManager之间通信的网络带宽以及内存中Network Buffer部分的消耗，在减少了延迟的同时增加了整体的吞吐量。</p>
<p>         <img alt="" loading="lazy" src="/logbook/images/algorithm/cb388c8180b2a3cd7444.png"/><br/>         <img alt="" loading="lazy" src="/logbook/images/algorithm/caceb820aa656477b386.png"/></p>
<p>        这里需要解决的问题在于如何用少量的Slot数就能解决较大的并发，在FlatMap或者Sink算子中，我们采用了如下的线程池架构：<br/>         <img alt="" loading="lazy" src="/logbook/images/algorithm/92af4c1f3a0c0c9b4f2f.png"/></p>
<p>        单个Slot中通过线程池极大的提高了并发处理能力，单个Slot处理能力为总线程池大小，处理能力通常可以比传统方案提高两个数量级左右，也就是通常我们Slot数上千的大作业可以用几十个Slot就能实现。在这个范围内，通过Slot的分配来形成算子链来保证TaskManager的均衡就相对简单了。通过合理配置线程池和缓冲队列可以杜绝FlatMap算子或者Sink算子由于局部高延时导致的反压问题。</p>
<h2>4、降低OOM风险</h2>
<p>        除反压问题外，由于OOM导致作业失败是Flink中另外一个比较常见的问题。我们对Flink堆内存进行分析，部分作业由于老年代内存没有得到及时的释放导致堆内存占用过高，进而导致Flink占用的系统内存不断走高，有超过预设值被系统Kill的风险。这里我们引入一个自定义内存回收算子，按照需求逐个对TaskManager进行内存回收，有效的防止了堆内存持续居高不下的情况。结合Metric监控中的堆内存使用率预警，可以将非突发情况导致的OOM问题彻底解决。</p>
<h2>5、Pipeline链路优化</h2>
<h3>跨集群容灾</h3>
<p>        对于依赖实时流的业务而言，Flink计算所依赖的消息队列集群或者Flink的计算集群以及强依赖的其他组件发生故障带来的影响都是灾难性的，为保障整体Pipeline的整体稳定性，引入了备份容灾的方案。主备链路使用相互隔离的物理环境，以Pulsar集群和Flink集群为例，主备链路分别使用不同IDC的存储和计算集群。这里采用了冷备和热备两种方式。</p>
<p>      <img alt="" loading="lazy" src="/logbook/images/algorithm/33ea26b05b6f493b0fac.png"/></p>
<p>        冷备：在备份Pulsar集群预先准备好最原始的Source数据；在备份计算集群预先准备好计算任务(在主链路故障时刻启动)。</p>
<p>        热备：一些比较重要的任务主备同时计算，主链路故障时一键切换。 </p>
<p><br/></p>
<p>实时控制</p>
<p>        Flink作业的重启是全局的，并不能像后台Server一样灰度TaskManager重启，频繁重启会导致数据流的波动，这对于一些需要频繁变更参数的任务不大友好。这里引入动态参数配置功能，可以在不重启作业的情况下完成一些常规的配置变更：</p>
<ul><li>特征Meta变更</li>
<li>过滤/准入阈值调整</li>
<li>特定ID过滤</li>
<li>......</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/4796185be907ad8c2521.png"/></p>
<p>     Random Source 通过一定的频率不断拉取配置，并将配置和数据Union后发送到下游数据，下游的RichFunction可以获取并更新最新的配置来使用。这种方案既不会频繁重启作业，也不会因为在RichFunction的处理逻辑里频繁读取配置造成反压的风险。</p>
<p><br/></p>
<p>精准流控</p>
<p>        在实际生产环境中通常会遇到以下情况： <br/>        1、业务突发活动导致短期数据大幅上涨<br/>       2、任务异常导致反压，或者任务重启后处理大量的积压数据</p>
<p>        如果短期处理的数据量超过一些系统(pulsar/redis/hbase/kv等)能承受的上限，会继而引发大量的高时延或者失败进而导致整个链路处于不稳定状态，这种风险很可能会导致雪崩的出现。</p>
<p>        这里采用了精准流控的方式来规避这种风险，即为每个算子设置一个安全阈值，使用令牌桶的方式进行限速。</p>
<p>                                          <img alt="" loading="lazy" src="/logbook/images/algorithm/45d475aa79fe25ae2b88.png"/></p>
<p>        当处理数据速率超过预设值时，可以根据任务需求进行限速反压或者随机丢弃以保障系统的安全。例如对Sink算子进行限速：       <img alt="" loading="lazy" src="/logbook/images/algorithm/93850e9657c979332cc2.png"/></p>
<p>        模拟任务失败一段时间后通过Checkpoint重启的情况，Sink算子处理的数据量会稳定保持在预设值直至处理完积压数据。</p>
<p>               <img alt="" loading="lazy" src="/logbook/images/algorithm/179dc74d98a97b959327.png"/></p>
<p>       通过精准流控的方法，整个链路可以实现算子级别的精准控制，极大程度的提高了链路的可控性和稳定性。</p>
<h2>6、开发流程优化</h2>
<p>        大数据作业一般以提交用户自己打包的jar来进行发布，但对于线上任务而言，这样的流程不能满足其高质量的要求。因此我们与微信测试中心合作基于蓝盾和笛卡尔构建了如下一套发布流程。<br/>      <img alt="" loading="lazy" src="/logbook/images/algorithm/3b8abc1c2a7d2119bbd2.png"/></p>
<p>        通过上述流程加强了线上作业的代码管理和版本控制，保障了线上作业的逻辑和变更在项目范围内公开透明，在一定程度上降低了变更导致故障的发生，统一的流程减少了环境不一致，版本混乱等问题导致的开发和运维的负担。</p>
<h1>三、总结和展望</h1>
<p>        本文从几个方面介绍了Flink在应用层的优化方案，在实际应用中合理的利用上述方案能有效的解决之前遇到的许多性能问题，基本不会再出现由于Flink原因导致的任务失败或者反压等情况，也能从整个链路的角度增强Pipeline的整体可用性并加强对上下游的保护。上述方案基于微信 Flink on K8S 进行开发，基于社区开源Flink，可以很方便的应用到其他基于开源Flink的作业上。<br/>        更多的Flink使用示例和优化方案我们已经开源出来，并附带指引文档和运行示例：<br/>        <strong>Flink应用合集</strong> [内部或本地链接已移除]        <strong>指引文档</strong> [内部或本地链接已移除]        在flink-application-plus中，我们提供了常用的Flink应用示例，可以基于此轻松完成使用Flink来实现实时BI，实时特征，实时样本，样本特征拼接等功能，搭建BI或者推荐数据流的Pipeline。并且在微信 Flink on K8S的环境下可以与微信后台的FeatureKv 等模块打通，非常方便可靠的生产可供线上直接使用的数据。<br/>        后续我们将结合实际业务持续优化和沉淀Flink的使用经验和稳定性优化方案，并解决Flink在开发运维过程中遇到的问题。</p>
<p><br/></p>
<p>更多详细内容，请访问：<strong>微信大数据计算平台 Gemini-2.0 系列文章</strong></p> 
{% endraw %}
