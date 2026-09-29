---
title: "Flink监控报表实战：Promethus+Grafana"
date: 2022-06-16 07:58:15
categories:
  - flink
  - 监控与故障排查
---

{% raw %}

<div>

</div>
<p>上一篇文章提到了通过在flink-conf.yml中配置Reporter，可以将Flink监控指标数据定期推送至第三方外部系统。今天这篇文章就来详细讲解一下使用Promethus和Grafana展示Flink Metric的步骤。</p>
<h1>1、文件配置</h1>
<p>Flink支持使用Promethus作为第三方报表展示系统，提供了相关jar包供开发者使用。</p>
<p>首先，将{FLINK_HOME}/opt/路径下的flink-metrics-prometheus-{version}.jar包拷贝到{FLINK_HOME}/lib路径下。然后在flink-conf.yml文件中按照官方说明文档配置Metric Repoter：</p>
<div>
<pre>metrics.reporter.prom.class: org.apache.flink.metrics.prometheus.PrometheusReporter  
metrics.reporter.prom.port: 9250-9260</pre>
</div>
<p>指定Promethus的Reporter Class，并设定端口为9250-9060。值得一提的是port参数为可选项，若不进行配置默认为9249端口，之所以设定一个范围值是为了应对一台主机上JobManager和TaskManager共存的情况，使该台主机能运行多个Reporter实例。</p>
<p>因为本次测试集群为Standalone集群，因此我只配置了9249-9250这两个端口。确保单台节点既能report jobmanager的监控指标，也能report taskmanager的监控指标。</p>
<p>接着对Promethus进行配置，编辑promethus.yml文件，新增Flink集群监控配置：</p>
<div>
<pre>scrape_configs:  
  - job_name: 'flink-jm'
    metrics_path: '/'
    static_configs:
    - targets: ['FLINK_JM:9250']
  - job_name: 'flink-tm'
    metrics_path: '/'
    static_configs:
    - targets: ['FLINK_TM:9250']</pre>
</div>
<p>以上为配置针对分布式集群的配置，通过设置多个job将不同节点的监控指标分开。但因为本次测试集群为伪分布式集群，单节点同时扮演着jobmanager和taskmanager的角色，通过9249和9250两个端口，所以我进行的配置稍有不同：</p>
<div>
<pre>scrape_configs:  
  - job_name: 'flink-cluster'
    metrics_path: '/'
    static_configs:
    - targets: ['HOST:9249', 'HOST:9250']</pre>
</div>
<h1>2、Grafana配置数据源并创建监控报表</h1>
<p>Grafana是一个跨平台的开源仪表盘应用，主要用于度量分析和数据可视化。支持如Graphite，InfluxDB，OpenTSDB，Prometheus，Elasticsearch等多种数据源。</p>
<p>针对这次使用Grafana配置报表监控Flink集群及任务的需求，Grafana其实也提供了使用Promethus作为数据源的<a href="https://grafana.com/grafana/dashboards/8966">Flink Metric</a>仪表盘，截至现在该仪表盘已有611次下载。展示效果图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/81e4d93d83d0a253b6d5.png"/></p>
<p>可以看到该Dashboard提供的监控指标还是比较齐全，包含了记录总数、消息处理延时和kafka消费速率等运维人员可能比较关心的指标。如果以上监控指标已经能满足需求的话，推荐直接使用该款Dashboard。不过本文会详细讲解一些使用Grafana配置任务（Job）和算子（Operator）级别的监控报表细节步骤，因此还有下文。</p>
<h2>2.1 配置Promethus数据源</h2>
<p>首先，我们需要在Grafana Configuration下的Data Sources模块下创建Promethus数据源：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/c40ce8870323a2420026.png"/></p>
<p>Type处选择Promethus作为数据源类型，URL处填写Pomethus服务器及端口地址，其余按默认配置即可。</p>
<h2>2.2 配置job变量</h2>
<p>配置好数据源后，创建用于展示监控指标的Dashboard。为了避免集群上任务较多造成指标数量混乱不易观察的现象。可以考虑将集群上的任务作为参数（Variable），根据选中的参数进行具体任务指标的展示。</p>
<p>于Dashboard的Settings/Variables中创建$job变量：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/d2a1e7ee424b505525b2.png"/></p>
<p>上图中通过使用label_values方法从指标中提取出存活的任务名，并在界面上以下拉框展示。</p>
<h2>2.3 配置报表</h2>
<p>接下来我们就可以正式开始配置报表了，本次报表主要针任务内各算子的吞吐量以及Flink消费Kafka的offset延迟、消费速度指标进行监控。首先针对任务内各算子吞吐量指标进行配置：</p>
<h3>2.3.1 配置算子进出吞吐量对比报表</h3>
<p>在笔者上一篇KM文章中有提到Operator级别的监控指标中有针对各算子进、出吞吐量的监控，分别为numRecordsInPerSecond和numRecordsOutPerSecond，表示该Operator或Task每秒内消息的进、出条数。</p>
<p>对于Flink程序来说，算子吞吐量的监控是十分有必要的，在消息处理时出现阻塞或者延迟严重的现象时能根据程序中算子的进出吞吐量对比快速定位问题，找出程序中是具体哪一个算子处理消息的速度赶不上消息消费的速度。因此，吞吐量监控报表应该这样去配置：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/b9501932fc5a25ced866.png"/></p>
<p>通过job参数确定具体Flink任务，以task_name进行groupby并对指标进行sum操作（对并行度&gt;1的task的指标进行聚合），最后结果展示按照task_name的形式进行直观展示。出吞吐量numRecordsOutPerSecond也按照上述方式进行配置。最终效果如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/809b9583fe195ab38a8a.png"/></p>
<p>以上图来看，程序中的map算子进出吞吐量曲线基本趋于一致，这说明在这段时间内该算子内部没有出现处理速度小于消费速度的情况。如果一个算子是程序阻塞问题发生的源头，那经过进出吞吐量曲线图的对比将会明显不一致。</p>
<h3>2.3.2 配置算子间延迟监控报表</h3>
<p>Flink提供了对消息在Flink拓扑中各算子间传输的延时监控，但是默认未启用。</p>
<p>其实现方式类似于Storm tick机制——Source将定期发出一个称为LatencyMarker的特殊记录，包含从Source处发出记录的时间戳，通过计算该记录到达算子的时间与发出记录的时间间的差值得出延时。</p>
<p>使用该种方式就有两点需要注意：一是集群间机器的时钟必须保持同步，二是启用延时监控可能会影响集群性能。这也是为什么Flink为将该监控默认开启的原因。</p>
<p>可以通过在flink-conf.yml文件中配置metrics.latency.interval属性或者在程序中设置ExecutionConfig两种方式启用Flink latency tracking。笔者建议只针对特定需要监控延时的任务，在ExecutionConfig进行配置开启延时监控，配置代码如下：</p>
<div>
<pre>final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
ExecutionConfig config = env.getConfig();
// 设置发送mark的周期为3秒
config.setLatencyTrackingInterval(3000);</pre>
</div>
<p>然后在报表中计算任务中所有算子间latency的最大值（最大值即代表Source到Sink的处理延时）</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/b0f29f3576a0e702c312.png"/></p>
<p>最终时延报表效果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/84afdf4e10d99c35e6e4.png"/></p>
<h3>2.3.2 配置Kafka消费监控指标</h3>
<p>Flink Kafka Connector内置监控指标涵盖面丰富，records_lag_max表示该消费组消息主题下的分区consumer lag最大值，而records_consumed_rate则代表着当前Flink程序消费kafka的速率。我们同样可以针对这两个指标配置如下报表：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/2317c6cce89b9c96a2fd.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/f2552f396b7976be9a5e.png"/></p>
<p>至此，我们简陋的监控报表就算配置完成了。看下效果：</p>
<p><img alt="" loading="lazy" src="/logbook/images/flink/57226560e9d00698d698.png"/></p>
<p>当各算子的进出吞吐量曲线趋势基本保持一致、Latency不夸张且最大分区消费offset lag值不大的情况下，就可以说明当前Flink程序是出于很健康的状态啦。反之根据曲线的异常趋势，我们也能快速定位出Flink job中究竟是哪一环拉了跨。</p>
<p>怎样，这样看来Flink Metric是不是很强大呢？只需要借助一下第三方图形化报表系统的力量，就能瞬间针对我们关注的监控点进行图形化展示了，在线上发生阻塞时更能快速定位到问题所在。事不宜迟，赶紧动手自己配置一副Flink的监控报表吧！</p> 
{% endraw %}
