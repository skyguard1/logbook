---
title: "ClickHouse物化视图在直播场景中的实践"
date: 2022-06-17 11:34:24
categories:
  - linux
---

<h2 id="807f7fb6-400f-6d12-d6f4-5ce8c5553ab9" class="toc-enable">一、前言</h2>
<p>ClickHouse 是一个列式存储的数据库管理系统 (DBMS)，用于在线分析处理 (OLAP)，被认为是在OLAP领域查询最快的数据库。</p>
<p>由Yandex Metrica团队于2016年基于Apache 2.0协议开源。github：<a href="https://github.com/ClickHouse/ClickHouse">https://github.com/ClickHouse/ClickHouse</a>&nbsp;star 18.8k。</p>
<p><strong>数据中心ClickHouse目前应用于实时计算场景：<br></strong></p>
<ul><li>实时指标：实时接入+维度扩展</li>
<li>活动运营：聚合中间表(物化视图+字典)</li>
<li>在线特征服务数据支持：全链路接入优化(秒级)、稳定高效查询</li>
</ul><p><strong>数据中心目前ClickHouse集群规模：</strong></p>
<ul><li class="auto-cursor-target">目前已接入视频号，直播，实验平台等10多个业务，提供稳定、高效查询的服务，且结合业务做更加贴近深度场景易用性提升和内核优化</li>
<li>集群近千台节点</li>
<li>数百万亿数据，PB级存储规模</li>
<li>单集群日均分布式查询百万+次，平均耗时1.68s，TP90&nbsp;1.98s</li>
<li>单集群日均实时写入百万+次，峰值写入量1亿+/s 。其中在线特征集群写入(全链路)平均延迟 2秒，TP90 3秒</li>
</ul><h2 id="78b8d6f4-d057-0884-70cb-913a49dc1f62" class="toc-enable">二、整体架构</h2>
<p style=""><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(1)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p>在数据中心实时Pipeline的整个架构中，主要分为5个模块：</p>
<ul><li>Pulsar：消息队列，用于实时数据的接收和转发，目前支持千亿级别的流量收发，是整个实时Pipeline的流量入口；</li>
<li>Flink：流计算引擎，主要用于对实时流进行加工处理，通过关联Redis和HBase进行用户画像、实验命中信息关联；</li>
<li>Sinker：数据接入层，消费Pulsar数据写入Clickhouse，支持流控、重试，数据准确性保证，hash接入等功能，可支持十亿级流量写入；</li>
<li>ClickHouse：OLAP计算引擎，支持实时数据的处理和秒级查询分析，集群稳定性保障(99.5%)，针对业务场景内核优化，协助业务查询优化；</li>
<li>Fisher：元数据管理和BI分析平台，支持分钟级配置实时数据接入CH，支持分钟级配置离线数据导入，支持Clickhouse建表和加工，结合Superset和Datatalk提供BI分析。</li>
</ul><p>在每个模块我们都做了很多定制和优化，本文主要介绍ClickHouse物化视图在直播场景的探索和实践。</p>
<h2 id="e78ea69a-cba6-4247-7cf0-d0161ea7c032" class="toc-enable"><span style="color:#333333;">三、为什么要用物化视图？</span></h2>
<p><strong>在直播场景下我们通过物化视图解决了哪些问题：</strong></p>
<ul><li>数据预聚合：按照维度聚合数据，减少数据量，加速查询，用于BI场景下的指标分析：<br>举个例子，我们针对2个日增量分别为<strong>80亿</strong>的基础表，为了统计每30秒的统计uv和pv，做了一个时间窗口为30秒、3个非时间维度，uv、pv为聚合指标的2个物化视图，日均分布式查询<strong>1w+次</strong>，平均耗时<strong>360ms</strong>，TP90 <strong>900ms。</strong>单次扫描数据量降低<strong>99%，</strong>耗时降低<strong>90%</strong>。</li>
<li>维度关联：通过物化视图结合字典表关联维度，实现直播热度排名等实时计算关联的维度，也补充了部分实验的相关维度数据。</li>
<li>多流指标聚合：可以解决部分join问题(后面会针对这个场景详细展开)。<br>通过物化视图组合宽表，我们解决了部分场景下的join问题，避免了业务同学写<strong>上千行</strong>代码去处理多流指标聚合的问题，<strong>开发效率高</strong>，<strong>可维护性强</strong>。避开了分布式join，单表查询，<strong>查询效率更高</strong>。</li>
</ul><p>列一个简单的业务场景和查询效率对比，了解下物化视图的查询优势。</p>
<p><strong>业务场景</strong></p>
<p>数据源：1天6亿数据表，1个日期维度hour_，2个普通维度x1和x2和uuid(脱敏)。<br>诉求：业务会按照到小时粒度查询上述数据源任意维度组合的uv和pv数据。uv采用uniqCombined(uuid)，pv采用sum(1)<br>要求：支持多种维度组合查询，尽可能快的返回结果。</p>
<p><strong>效果对比</strong></p>
<p><strong>1.基础表和物化视图行数和存储占用</strong></p>
<table class="relative-table wrapped confluenceTable"><colgroup><col><col><col></colgroup><tbody><tr><th class="confluenceTh"><br></th>
<th class="confluenceTh">行数</th>
<th class="confluenceTh">存储占用</th>
</tr><tr><td class="confluenceTd">基础表</td>
<td class="confluenceTd">6.3亿</td>
<td class="confluenceTd">2.13G</td>
</tr><tr><td class="confluenceTd">物化视图</td>
<td class="confluenceTd">6k</td>
<td class="confluenceTd">168M</td>
</tr></tbody></table><p class="auto-cursor-target"><strong>2.基础表和物化视图查询对比</strong></p>
<p class="auto-cursor-target">基准测试：</p>
<ul><li class="auto-cursor-target">基础表与物化视图对比；</li>
<li class="auto-cursor-target">
<p class="auto-cursor-target">1次提交sql次数对比：1次提交1个，提交10次；1次提交3个，提交10次；1次提交5个，提交10次；1次提交10个，提交10次。</p>
</li>
</ul><div class="km_insert_code">
<pre class="language-sql" style="position: relative; z-index: 2;"><code class="prism language-sql">基础表查询：
<span class="token keyword">select</span> hour_<span class="token punctuation">,</span>uniqCombined<span class="token punctuation">(</span>uuid<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span><span class="token function">sum</span><span class="token punctuation">(</span><span class="token number">1</span><span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mergetree_local <span class="token keyword">group</span> <span class="token keyword">by</span> hour_
<span class="token keyword">select</span> hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>uniqCombined<span class="token punctuation">(</span>uuid<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span><span class="token function">sum</span><span class="token punctuation">(</span><span class="token number">1</span><span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mergetree_local <span class="token keyword">group</span> <span class="token keyword">by</span> hour_<span class="token punctuation">,</span>x1
<span class="token keyword">select</span> hour_<span class="token punctuation">,</span>x2<span class="token punctuation">,</span>uniqCombined<span class="token punctuation">(</span>uuid<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span><span class="token function">sum</span><span class="token punctuation">(</span><span class="token number">1</span><span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mergetree_local <span class="token keyword">group</span> <span class="token keyword">by</span> hour_<span class="token punctuation">,</span>x2
<span class="token keyword">select</span> x1<span class="token punctuation">,</span>x2<span class="token punctuation">,</span>uniqCombined<span class="token punctuation">(</span>uuid<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span><span class="token function">sum</span><span class="token punctuation">(</span><span class="token number">1</span><span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mergetree_local <span class="token keyword">group</span> <span class="token keyword">by</span> x1<span class="token punctuation">,</span>x2
<span class="token keyword">select</span> hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>x2<span class="token punctuation">,</span>uniqCombined<span class="token punctuation">(</span>uuid<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span><span class="token function">sum</span><span class="token punctuation">(</span><span class="token number">1</span><span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mergetree_local <span class="token keyword">group</span> <span class="token keyword">by</span> hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>x2

物化视图查询：
<span class="token keyword">select</span> hour_<span class="token punctuation">,</span>uniqCombinedMerge<span class="token punctuation">(</span>uv<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span>sumMerge<span class="token punctuation">(</span>pv<span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mv_local <span class="token keyword">group</span> <span class="token keyword">by</span> hour_
<span class="token keyword">select</span> hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>uniqCombinedMerge<span class="token punctuation">(</span>uv<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span>sumMerge<span class="token punctuation">(</span>pv<span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mv_local <span class="token keyword">group</span> <span class="token keyword">by</span> hour_<span class="token punctuation">,</span>x1
<span class="token keyword">select</span> hour_<span class="token punctuation">,</span>x2<span class="token punctuation">,</span>uniqCombinedMerge<span class="token punctuation">(</span>uv<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span>sumMerge<span class="token punctuation">(</span>pv<span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mv_local <span class="token keyword">group</span> <span class="token keyword">by</span> hour_<span class="token punctuation">,</span>x2
<span class="token keyword">select</span> x1<span class="token punctuation">,</span>x2<span class="token punctuation">,</span>uniqCombinedMerge<span class="token punctuation">(</span>uv<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span>sumMerge<span class="token punctuation">(</span>pv<span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mv_local <span class="token keyword">group</span> <span class="token keyword">by</span> x1<span class="token punctuation">,</span>x2
<span class="token keyword">select</span> hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>x2<span class="token punctuation">,</span>uniqCombinedMerge<span class="token punctuation">(</span>uv<span class="token punctuation">)</span> <span class="token keyword">as</span> uv<span class="token punctuation">,</span>sumMerge<span class="token punctuation">(</span>pv<span class="token punctuation">)</span> <span class="token keyword">as</span> pv <span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mv_local <span class="token keyword">group</span> <span class="token keyword">by</span> hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>x2

测试方法：
benchmark <span class="token comment">--port=9000  --password=xxxxx --host=host --database=test -c 3 -i 30 --max_threads=16 --cumulative -d 10 &lt;sql</span></code></pre>

<table class="fixed-table wrapped confluenceTable" style="width:890px;"><colgroup><col><col><col><col><col><col><col></colgroup><tbody><tr><th class="confluenceTh" style="width:15px;"><br></th>
<th class="confluenceTh" style="width:141px;">指标</th>
<th class="confluenceTh" style="width:108px;">按hour_聚合</th>
<th class="confluenceTh" style="width:108px;">按hour_&amp;x1维度聚合</th>
<th class="confluenceTh" style="width:114px;">按hour_&amp;x2维度聚合</th>
<th class="confluenceTh" style="width:97px;">按x1和x2维度聚合</th>
<th class="confluenceTh" style="width:113px;">全维度聚合</th>
</tr><tr><td class="confluenceTd" rowspan="5" style="width:15px;">基础表</td>
<td class="confluenceTd" style="width:141px;">扫描行数</td>
<td class="confluenceTd" style="width:108px;">6.3亿</td>
<td class="confluenceTd" style="width:108px;">6.3亿</td>
<td class="confluenceTd" style="width:114px;">6.3亿</td>
<td class="confluenceTd" style="width:97px;">6.3亿</td>
<td class="confluenceTd" style="width:113px;">6.3亿</td>
</tr><tr><td class="confluenceTd" style="width:141px;">扫描数据量</td>
<td class="confluenceTd" style="width:108px;">7.64 GB</td>
<td class="confluenceTd" style="width:108px;">12.73 GB</td>
<td class="confluenceTd" style="width:114px;">12.73 GB</td>
<td class="confluenceTd" style="width:97px;">15.27 GB</td>
<td class="confluenceTd" style="width:113px;">17.82 GB</td>
</tr><tr><td class="confluenceTd" colspan="1" style="width:141px;">1次1个耗时TP50/TP90</td>
<td class="confluenceTd" colspan="1" style="width:108px;">2.359s/2.442</td>
<td class="confluenceTd" colspan="1" style="width:108px;">3.548s/3.634s</td>
<td class="confluenceTd" colspan="1" style="width:114px;">6.554s/6.656</td>
<td class="confluenceTd" colspan="1" style="width:97px;">2.045s/2.082s</td>
<td class="confluenceTd" colspan="1" style="width:113px;">13.106s/13.213s</td>
</tr><tr><td class="confluenceTd" colspan="1" style="width:141px;">1次5个耗时TP50/TP90</td>
<td class="confluenceTd" colspan="1" style="width:108px;">6.828s/7.156s</td>
<td class="confluenceTd" colspan="1" style="width:108px;">13.821s/14.402s</td>
<td class="confluenceTd" colspan="1" style="width:114px;">26.827s/28.740s</td>
<td class="confluenceTd" colspan="1" style="width:97px;">4.741s/4.967s</td>
<td class="confluenceTd" colspan="1" style="width:113px;">26.329s/29.319</td>
</tr><tr><td class="confluenceTd" colspan="1" style="width:141px;">1次10个耗时TP50/TP90</td>
<td class="confluenceTd" colspan="1" style="width:108px;">14.225s/15.152s</td>
<td class="confluenceTd" colspan="1" style="width:108px;">28.850s/29.854s</td>
<td class="confluenceTd" colspan="1" style="width:114px;">58.618s/61.870s</td>
<td class="confluenceTd" colspan="1" style="width:97px;">9.282s/9.553s</td>
<td class="confluenceTd" colspan="1" style="width:113px;">52.295s/55.439</td>
</tr><tr><td class="confluenceTd" rowspan="5" style="width:15px;">物化视图</td>
<td class="confluenceTd" style="width:141px;">扫描行数</td>
<td class="confluenceTd" style="width:108px;">6k</td>
<td class="confluenceTd" style="width:108px;">6k</td>
<td class="confluenceTd" style="width:114px;">6k</td>
<td class="confluenceTd" style="width:97px;">6k</td>
<td class="confluenceTd" style="width:113px;">6k</td>
</tr><tr><td class="confluenceTd" style="width:141px;">扫描数据量</td>
<td class="confluenceTd" style="width:108px;">955.96 KB</td>
<td class="confluenceTd" style="width:108px;">1.00 MB</td>
<td class="confluenceTd" style="width:114px;">1.00 MB</td>
<td class="confluenceTd" style="width:97px;">1.03 MB</td>
<td class="confluenceTd" style="width:113px;">1.05 MB</td>
</tr><tr><td class="confluenceTd" colspan="1" style="width:141px;">1次1个耗时TP50/TP90</td>
<td class="confluenceTd" colspan="1" style="width:108px;">
<p>1.186s/1.193s</p>
</td>
<td class="confluenceTd" colspan="1" style="width:108px;">1.546s/1.583s</td>
<td class="confluenceTd" colspan="1" style="width:114px;">1.687s/1.710s</td>
<td class="confluenceTd" colspan="1" style="width:97px;">1.240s/1.320</td>
<td class="confluenceTd" colspan="1" style="width:113px;">5.164s/5.223s</td>
</tr><tr><td class="confluenceTd" colspan="1" style="width:141px;">1次5个耗时TP50/TP90</td>
<td class="confluenceTd" colspan="1" style="width:108px;">1.431s/1.592s</td>
<td class="confluenceTd" colspan="1" style="width:108px;">1.693s/1.868s</td>
<td class="confluenceTd" colspan="1" style="width:114px;">1.977s/2.225s</td>
<td class="confluenceTd" colspan="1" style="width:97px;">1.486s/1.585s</td>
<td class="confluenceTd" colspan="1" style="width:113px;">5.431s/5.554s</td>
</tr><tr><td class="confluenceTd" colspan="1" style="width:141px;">1次10个耗时TP50/TP90</td>
<td class="confluenceTd" colspan="1" style="width:108px;">1.682s/2.497s</td>
<td class="confluenceTd" colspan="1" style="width:108px;">2.086s/2.851s</td>
<td class="confluenceTd" colspan="1" style="width:114px;">2.967s/4.310s</td>
<td class="confluenceTd" colspan="1" style="width:97px;">1.788s/2.429s</td>
<td class="confluenceTd" colspan="1" style="width:113px;">5.801s/6.383s</td>
</tr></tbody></table><p>注：单台IT3B 32核64线程，256G内存，限制了max_threads=16，耗时是指并行完成多个sql的总耗时。</p>
<p><strong>3.查询对比分析</strong></p>
<p>通过以上数据可知，物化视图通过降低查询时的磁盘IO，可以有效的降低查询耗时，且在同时提交多个查询时仍然可以保证查询效率。<br>其中单次查询，通过物化视图，耗时可以<span style="color:#ff0000;"><strong>降低40%-75%</strong></span>，多次查询耗时可以<span style="color:#ff0000;">降低<strong>80%-95%</strong></span>，且同时提交sql越多，查询耗时差距越明显。<br>同时执行多个查询时，基础表根据执行的sql数量，耗时成线性增长，因为磁盘带宽打满，几乎为<span style="color:#ff0000;"><strong>串行执行</strong></span>。而物化视图可以做到真正的<span style="color:#ff0000;"><strong>并行执行</strong></span>。<br>物化视图同时执行多个查询时总耗时，与执行单次查询时的总耗时差距很小，约为单次查询的<span style="color:#ff0000;"><strong>1-1.4倍</strong></span>，而基础表这个比例为<span style="color:#ff0000;"><strong>4-9倍</strong></span>。</p>
<p>接下来将介绍物化视图是如何通过预聚合提高查询效率的，以及物化视图如何解决业务实际问题。</p>
<h2 id="c18f974f-e149-6bc5-1121-d555c2e55563" class="toc-enable"><span style="color:#333333;">四、物化视图实践</span></h2>
<h3 id="2107f61c-ce14-c36a-2597-670e74e1f0fe" class="toc-enable">1.物化视图简单介绍</h3>
<p><span style="color:#333333;"><a href="https://clickhouse.com/docs/en/sql-reference/statements/create/view/#materialized">物化视图</a>是一种通过<strong>空间换时间</strong>的预计算逻辑，是查询结果的持久化存储。<br></span>物化视图实际上分为两部分：视图计算<strong>view</strong>和物化存储<strong>table（以下简称为view和table）</strong>。<br></p>
<p style=""><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(2)" width="310" height="366" alt="" style="position: relative; z-index: 2;">&nbsp;<img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(3)" width="458" height="363" alt="" style="position: relative; z-index: 2;"></p>
<p>通过上述的创建sql看到，正常创建一个物化视图<strong>view</strong>(test.test_mv_data_local)，同时也会在test库下生成一个.inner.test_mv_data_local的表<strong>table</strong>。<br>其中<strong>view</strong>是物化视图的计算过程，是一串可定义的Select语句，主要描述数据应该如何计算。<strong>table</strong>是将<strong>view</strong>计算的结果进行实际存储的物理表。<br>数据写入<strong>基础表</strong>(test.test_mv_local)后，由<strong>view</strong>(test,test_mv_data_local)计算存储到<strong>table</strong>(test.`.inner.test_mv_data_local`)中，是一个写入流(BlockInputStream)的单向传递过程，基础表的更新和删除不会传递给物化视图，物化视图的更新和删除也不会影响基础表。<br><strong>*AggregatingMergeTree</strong>是物化视图<strong>table</strong>的主要表引擎。可以针对聚合数据结果，做增量计算优化，具有后台<strong>merge</strong>时按照<strong>order by</strong>再次聚合数据的能力。<br>表字段分为两部分：</p>
<ul><li><strong>聚合函数字段</strong>：可以将聚合函数计算的中间状态（而不是结果）存储在字段中，中间状态支持增量迭代，可以理解为<strong>计算指标</strong>，图中的uv和pv使用了<strong>AggregateFunction</strong>；</li>
<li><strong>Group by Key</strong>：建表时的<strong>Order by key</strong>，是指按照不同的字段进行数据聚合的key，可以理解为<strong>维度</strong>，图中的day_，hour_，x1，x2。</li>
</ul><p>普通的聚合函数后加State就可以转换为聚合函数字段。比如uinqCombinedState(uuid)生成AggregateFunction(uniqCombined,Int64)，sumState(1)生成AggregateFunction(sum,UInt8)。<br>简单理解下<strong>中间状态（State）</strong>的概念，以uv为例，通常使用去重函数计算会得到数值结果。但是往往会遇到有不同的维度枚举情况，会有用户重复使得uv计算的数值结果无法通过简单加法进行计算的。<br>常规做法是创建一张新的表，在计算时将所有的可能维度都计算出来，比如对每个维度计算一个总计，这样是可以支持维度组合(不需要的维度过滤为汇总)，但是计算的代价很大，2的n次方unoin。<br>有什么办法可以像常规方式一样进行维度组合计算，同时避免高额的计算代价？<br>将计算的指标不存储最终计算的值，而是存储一个可迭代的中间状态（State）。<br>比如通过array、set、或者<a href="https://en.wikipedia.org/wiki/HyperLogLog">HyperLogLog</a>将uin进行聚合，数据结构中的元素为uin，这样数据的组织形式会变成&lt;时间维度、维度1、维度2、维度3、uvstate&gt;。<br>从上述的维度中任意取一个维度组合，都会得到一个uin的结果集，不论是array、set、<a href="https://en.wikipedia.org/wiki/HyperLogLog">HyperLogLog</a>，都可以进行合并和去重，最终结果集的基数就是uv。</p>
<p>用一个表格描述下AggregatingMergeTree的merge过程，假设目前表中有以下数据存在表中等待merge，其中 order by (day_,id_)，数据将会以day_，id_为维度对聚合字段类型的指标的中间状态进行组合（这里通过值的计算来解释这个过程，实际存储是经过序列化的中间状态）。</p>
<p style=""><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(4)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" width="683" height="121" alt="" class="amplify"></p>
<p>在实际生产环境中，我们遇到了挺多问题，这里分享一下给大家排排坑。</p>
<p style=""><em><strong>坑1：<span style="color:#ff0000;">order by key</span></strong><span style="color:#ff0000;"> <strong>一定要是数据聚合的group by key</strong></span>，否则数据merge后会有问题<br></em>举个例子：假设我们有3个维度 day_、x1、x2，但是order by (day_,x1) ，如下图所示，这个时候聚合后 x2的维度将会被忽略，只保留order by 排序后的最小的值。<br>创建表<br><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(5)" alt="" style="position: relative; z-index: 2;"><br></p>
<p style="">写入3条测试数据<br><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(6)" alt="" style="position: relative; z-index: 2;"><br></p>
<p style="">手动触发merge后的数据<br><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(7)" alt="" style="position: relative; z-index: 2;"><br></p>
<p>merge后X2维度失去了基数，当需要查询或者枚举这个维度的数据时，查询的数据是错误的。</p>
<p><em><strong>坑2：AggregateFunction</strong>使用时注意字段输入类型<span style="color:#ff0000;"><strong>严格对齐</strong></span>，不会隐式转换<br></em><a href="https://clickhouse.com/docs/en/sql-reference/data-types/aggregatefunction/">AggregateFunction</a>(函数名称, types_of_arguments…)，这里的types_of_arguments是输入参数类型。<br>这个输入类型必须要和真正的字段类型严格对齐。字段类型不一致是无法正常写入的，会出现错误。<br>AggregateFunction(sum,UInt8)与AggregateFunction(sum,UInt16)不等价，AggregateFunction(sum,Nullable(UInt8))与AggregateFunction(sum,UInt8)不等价。<br>其中最容易出现问题的是sumState(1)，1在clickhouse的类型为UInt8，而sumState(1)的聚合函数字段类型是AggregateFunction(sum, UInt8)。<br>如果将一个sumState(toUInt16(1))写入到AggregateFunction(sum, UInt8)会出现如下错误：<br>DB::Exception: Conversion from AggregateFunction(sum, UInt16) to AggregateFunction(sum, UInt8) is not supported: while<br>converting source column pv to destination column pv.</p>
<h3 id="453340cb-b07f-c7eb-91c0-41d3f17a0188" class="toc-enable">2.物化视图的两种创建方法</h3>
<p>物化视图的创建语法：</p>
<div class="km_insert_code">
<pre class="language-sql" style="position: relative; z-index: 2;"><code class="prism language-sql"><span class="token keyword">CREATE</span> MATERIALIZED <span class="token keyword">VIEW</span> <span class="token punctuation">[</span><span class="token keyword">IF</span> <span class="token operator">NOT</span> <span class="token keyword">EXISTS</span><span class="token punctuation">]</span> <span class="token punctuation">[</span>db<span class="token punctuation">.</span><span class="token punctuation">]</span>table_name <span class="token punctuation">[</span><span class="token keyword">ON</span> CLUSTER<span class="token punctuation">]</span> <span class="token punctuation">[</span><span class="token keyword">TO</span><span class="token punctuation">[</span>db<span class="token punctuation">.</span><span class="token punctuation">]</span>name<span class="token punctuation">]</span> <br><span class="token punctuation">[</span><span class="token keyword">ENGINE</span> <span class="token operator">=</span> <span class="token keyword">engine</span><span class="token punctuation">]</span> <span class="token punctuation">[</span>POPULATE<span class="token punctuation">]</span> <br><span class="token keyword">AS</span> <span class="token keyword">SELECT</span> <span class="token punctuation">.</span><span class="token punctuation">.</span><span class="token punctuation">.</span></code></pre>

<p>物化视图的创建实际上是创建<strong>view</strong>和<strong>table</strong>的过程。<br>有两种方式创建：</p>
<ul><li><strong>由view计算生成table，view和table绑定在一起共同组成物化视图，其中table为私有表；</strong></li>
<li><strong>view和table分开创建，view和table解耦，view计算的结果持久化存储在table。</strong></li>
</ul><div class="km_insert_code">
<pre class="language-sql" style="position: relative; z-index: 2;"><code class="prism language-sql">方法<span class="token number">1</span>：
<span class="token keyword">create</span> MATERIALIZED <span class="token keyword">VIEW</span>  test<span class="token punctuation">.</span>test_mv_data_local
<span class="token keyword">ENGINE</span> <span class="token operator">=</span> AggregatingMergeTree
<span class="token keyword">partition</span> <span class="token keyword">by</span> day_
<span class="token keyword">order</span> <span class="token keyword">by</span> <span class="token punctuation">(</span>hour_<span class="token punctuation">,</span>x1<span class="token punctuation">)</span>
<span class="token keyword">as</span> <span class="token keyword">select</span> day_<span class="token punctuation">,</span>hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>x2
        <span class="token punctuation">,</span>uniqCombinedState<span class="token punctuation">(</span>uuid<span class="token punctuation">)</span> <span class="token keyword">as</span> uv
        <span class="token punctuation">,</span>sumState<span class="token punctuation">(</span><span class="token number">1</span><span class="token punctuation">)</span> <span class="token keyword">as</span> pv
<span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mv_local
<span class="token keyword">group</span> <span class="token keyword">by</span> day_<span class="token punctuation">,</span>hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>x2
<span class="token comment">--此时会在test库下新增一张表，表名test.`.inner_test_mv_data_local`(数据库引擎Ordinary)或者`.inner_id.{uuid}`(数据库引擎Atomic)</span>
<span class="token comment">--这张表是物化视图实际存储数据的表table，test.test_mv_data_local是物化视图的view。</span>
<span class="token keyword">CREATE</span> <span class="token keyword">TABLE</span> test<span class="token punctuation">.</span><span class="token punctuation">`</span><span class="token punctuation">.</span><span class="token keyword">inner</span><span class="token punctuation">.</span>test_mv_data_local<span class="token punctuation">`</span>
<span class="token punctuation">(</span>
    <span class="token punctuation">`</span>day_<span class="token punctuation">`</span> <span class="token keyword">Date</span><span class="token punctuation">,</span>
    <span class="token punctuation">`</span>hour_<span class="token punctuation">`</span> <span class="token keyword">DateTime</span><span class="token punctuation">,</span>
    <span class="token punctuation">`</span>x1<span class="token punctuation">`</span> Int64<span class="token punctuation">,</span>
    <span class="token punctuation">`</span>x2<span class="token punctuation">`</span> Int64<span class="token punctuation">,</span>
    <span class="token punctuation">`</span>uv<span class="token punctuation">`</span> AggregateFunction<span class="token punctuation">(</span>uniqCombined<span class="token punctuation">,</span> Int64<span class="token punctuation">)</span><span class="token punctuation">,</span>
    <span class="token punctuation">`</span>pv<span class="token punctuation">`</span> AggregateFunction<span class="token punctuation">(</span>sum<span class="token punctuation">,</span> UInt8<span class="token punctuation">)</span>
<span class="token punctuation">)</span>
<span class="token keyword">ENGINE</span> <span class="token operator">=</span> AggregatingMergeTree
<span class="token keyword">PARTITION</span> <span class="token keyword">BY</span> day_
<span class="token keyword">ORDER</span> <span class="token keyword">BY</span> <span class="token punctuation">(</span>hour_<span class="token punctuation">,</span> x1<span class="token punctuation">,</span> x2<span class="token punctuation">)</span>
方法<span class="token number">2</span>：
<span class="token comment">--首先创建物化视图的存储表table，如方法1中生成的`.inner_test_mv_data_local`</span>
<span class="token comment">--创建物化视图存储table</span>
<span class="token keyword">CREATE</span> <span class="token keyword">TABLE</span> test<span class="token punctuation">.</span>test_mv_data_3_local
<span class="token punctuation">(</span>
    <span class="token punctuation">`</span>day_<span class="token punctuation">`</span> <span class="token keyword">Date</span><span class="token punctuation">,</span>
    <span class="token punctuation">`</span>hour_<span class="token punctuation">`</span> <span class="token keyword">DateTime</span><span class="token punctuation">,</span>
    <span class="token punctuation">`</span>x1<span class="token punctuation">`</span> Int64<span class="token punctuation">,</span>
    <span class="token punctuation">`</span>x2<span class="token punctuation">`</span> Int64<span class="token punctuation">,</span>
    <span class="token punctuation">`</span>uv<span class="token punctuation">`</span> AggregateFunction<span class="token punctuation">(</span>uniqCombined<span class="token punctuation">,</span> Int64<span class="token punctuation">)</span><span class="token punctuation">,</span>
    <span class="token punctuation">`</span>pv<span class="token punctuation">`</span> AggregateFunction<span class="token punctuation">(</span>sum<span class="token punctuation">,</span> UInt8<span class="token punctuation">)</span>
<span class="token punctuation">)</span>
<span class="token keyword">ENGINE</span> <span class="token operator">=</span> AggregatingMergeTree
<span class="token keyword">PARTITION</span> <span class="token keyword">BY</span> day_
<span class="token keyword">ORDER</span> <span class="token keyword">BY</span> <span class="token punctuation">(</span>hour_<span class="token punctuation">,</span> x1<span class="token punctuation">,</span> x2<span class="token punctuation">)</span>
<span class="token comment">--然后创建物化视图的view,将数据以TO的方式写入物化视图的table(test.test_mv_data_3_local)</span>
<span class="token keyword">create</span> MATERIALIZED <span class="token keyword">VIEW</span>  test<span class="token punctuation">.</span>test_mv_view_local <span class="token keyword">to</span> test<span class="token punctuation">.</span>test_mv_data_3_local
<span class="token keyword">as</span> <span class="token keyword">select</span> day_<span class="token punctuation">,</span>hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>x2
        <span class="token punctuation">,</span>uniqCombinedState<span class="token punctuation">(</span>uuid<span class="token punctuation">)</span> <span class="token keyword">as</span> uv
        <span class="token punctuation">,</span>sumState<span class="token punctuation">(</span><span class="token number">1</span><span class="token punctuation">)</span> <span class="token keyword">as</span> pv
<span class="token keyword">from</span> test<span class="token punctuation">.</span>test_mv_local
<span class="token keyword">group</span> <span class="token keyword">by</span> day_<span class="token punctuation">,</span>hour_<span class="token punctuation">,</span>x1<span class="token punctuation">,</span>x2</code></pre>

<p>两者的区别在于是否指定TO [db.] name：<br></p>
<ul><li>当不指定时，系统认为需要创建存储table（需申明表引擎），将会根据view的计算表达式生成所需的存储table。</li>
<li>当指定TO&nbsp;[db.]那么时，系统会认为已创建好了存储table，只需要将计算的结果写入到table中即可，不需要申明表引擎。</li>
</ul><p>两种方式在使用过程中都存在部分问题：</p>
<table class="fixed-table wrapped confluenceTable" style="margin-left:30px;width:850px;"><colgroup><col style="width:87px;"><col style="width:93px;"><col style="width:89px;"><col style="width:101px;"><col style="width:77px;"><col style="width:163px;"><col style="width:262px;"><col style="width:165px;"></colgroup><tbody style="margin-left:30px;"><tr style="margin-left:30px;"><th class="confluenceTh" style="width:20px;"><br></th>
<th class="confluenceTh" style="text-align:center;width:81px;">select</th>
<th class="confluenceTh" style="text-align:center;width:50px;">insert</th>
<th class="confluenceTh" style="text-align:center;width:59px;">alter</th>
<th class="confluenceTh" style="text-align:center;width:41px;">drop</th>
<th class="confluenceTh" style="text-align:center;width:106px;">字段一致性</th>
<th class="confluenceTh" style="text-align:center;width:182px;">错误感知</th>
<th class="confluenceTh" style="width:90px;">组合指标宽表</th>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;width:20px;">方法1</td>
<td class="confluenceTd" style="text-align:left;width:81px;">支持</td>
<td class="confluenceTd" style="text-align:left;width:50px;">支持</td>
<td class="confluenceTd" style="text-align:left;width:59px;">不支持</td>
<td class="confluenceTd" style="text-align:left;width:41px;">支持</td>
<td class="confluenceTd" style="text-align:left;width:106px;">完全一致</td>
<td class="confluenceTd" style="text-align:left;width:182px;" colspan="1">强,只有创建成功才能运行</td>
<td class="confluenceTd" colspan="1" style="width:90px;">不支持</td>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;width:20px;">方法2</td>
<td class="confluenceTd" style="text-align:left;width:81px;">支持</td>
<td class="confluenceTd" style="text-align:left;width:50px;">支持</td>
<td class="confluenceTd" style="text-align:left;width:59px;">支持</td>
<td class="confluenceTd" style="text-align:left;width:41px;">支持</td>
<td class="confluenceTd" style="text-align:left;width:106px;">需用户实现</td>
<td class="confluenceTd" style="text-align:left;width:182px;" colspan="1">弱，部分错误会在建表时隐藏，写入时暴露</td>
<td class="confluenceTd" colspan="1" style="width:90px;">支持</td>
</tr></tbody></table><p style="">方法1因为alter的局限性，修改逻辑只能重新创建，历史数据处理很麻烦，所以适用场景有限。<br>方法2在扩展性，灵活性上更好，且风险可以主动避免，是目前生产环境<strong>主要的</strong>使用方式。<br>方法2需要注意<strong>插入数据使用列名而不是顺序，这里展开讲一下：<br></strong>正常我们在往基础表写入数据时，会按照顺序匹配字段，如果insert的列在select中不存在时，且会出现列不匹配的错误，但是这个在物化视图中不一样，存在差异点。<br>物化视图是Create as select，当列在create中但是不在select时，这个列将会填充默认值，而不是返回列不匹配的错误。<br>当列不在Create中但是在select时，这个列将会忽略。<br>举个例子：<br>创建物化视图table，有day_、hour_、x1、x2 四个维度，uv、pv 2个指标。<br><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(8)" alt="" style="position: relative; z-index: 2;"><br></p>
<p style="">创建物化视图view，注意view中没有x2,多了一个x3,多了1个succ_pv，创建物化视图view是成功的。<br><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(9)" width="409" height="283" alt="" style="position: relative; z-index: 2;"><br></p>
<p style="">手动写入一条测试数据，显示成功，说明物化视图数据也写入成功了。<br><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(10)" alt="" style="position: relative; z-index: 2;"><br></p>
<p style="">查询物化视图可以看到刚才写入的测试数据，x1填充了默认值0，succ_pv忽略了。<img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(11)" width="410" height="111" alt="" style="position: relative; z-index: 2;"></p>
<h3 id="1e8557c8-a2c5-4ba2-e676-2746bd3c221f" class="toc-enable">3.物化视图的常用操作</h3>
<p>上文介绍了物化视图创建的2种方法，其中方法1存在alter的局限性，维度、指标的新增，逻辑的修改都需要重建物化视图。以下操作主要适用于方法2。</p>
<p><strong>1.新增维度和指标</strong></p>
<p>通常我们会遇到给物化视图增加维度的情况，可以和基础表新增维度一样，通过alter增加，不过物化视图和基础表有个差异点，必须要同时修改order by 。上面讲到，物化视图的order by 一定要和group by 一致，不然数据后台merge会有错误。这里给个修改模板，以上述的test.test_mv_data_3_local为例，新增一个x3维度并加到order by 中。</p>
<p style=""><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(12)" alt="" style="position: relative; z-index: 2;"></p>
<p>只能在新增字段时将这个字段加到order by 中，存量的字段是不允许新增到order by 的。<br>新增指标就和基础表增加字段一样，不需要修改order by。</p>
<p><strong>2.调整计算逻辑</strong></p>
<p>在方法2中，因为view和table是分开的，单纯的删除view，并不会影响table中的存量数据，只是不增加新数据了。<br>所以可以将这个view删除，然后修改sql后重建物化视图的view，新的数据将会按照新的逻辑进行计算写入。<br>更新计算逻辑是有损的，在删除物化视图的view和重新创建的过程中，如果有block写入，这部分block是不会写入到这个物化视图中的，相对于这部分数据丢失了，虽然删除和新建的速度非常快，但是不能保证没有数据丢失。</p>
<h3 id="22154c73-66a7-a46f-75fd-deccfbbf0c09" class="toc-enable">4. 物化视图使用注意事项</h3>
<p>物化视图是一把双刃剑，用得好，加速查询，降低磁盘IO，提高查询并发，用的不好反而会影响查询效率。<br>以下为我们使用过程中总结的经验：</p>
<ul><li><strong>复杂逻辑影响写入效率</strong>：维度过多、维度基数高、查询逻辑复杂，会影响写入耗时，降低系统吞吐量；</li>
<li><strong>高维度基数影响查询效率</strong>：聚合函数字段的存储是多于基础字段的，如果存在基数较高的列作为维度，数据将不能有效的聚合在一起，存储可能会大于基础表，查询效率反而会降低；</li>
<li><strong>物化视图表依赖</strong>：物化视图的基础表只能是本地表，不能是分布式表。TO之后的表可以是分布式表，但是写放大非常明显（<strong>慎用</strong>）。</li>
</ul><h2 id="9e2d6507-8b76-3e60-191e-69e9f95e7ae9" class="toc-enable">五、物化视图进阶</h2>
<h3 id="c058238f-af35-03db-def7-95c44c7e9bfe" class="toc-enable">1.物化视图数据写入流程</h3>
<p>物化视图在创建时会在基础表中增加一个依赖关系，当基础表有block写入时，会根据这个依赖关系触发物化视图的计算过程。<br>通过一个简单的流程图描述一下基础表和物化视图的写入流程。</p>
<p style=""><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(13)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p>在这个过程中，整个流程的触发来源于对基础表的Insert操作，然后block在基础表和物化视图中流转，在整个操作过程中，<br>会先对基础表加写锁，在写物化视图时，对物化视图table加写锁，只有整个流程都成功，这个block才算真正写入完成，保证基础表和物化视图的数据一致性。<br>在实际的生产环境中，上述过程存在一个问题，如果一个基础表有多个物化视图，物化视图是根据view名顺序执行的，整个过程的耗时是累计加在一起的总耗时，会导致insert写入耗时增大，系统的吞吐降低。<br>可以通过在users.xml中<strong>新增parallel_view_processing=true</strong>将<strong>串行</strong>过程改成<strong>并行</strong>。当一个基础表有多个物化视图时，耗时是取决于耗时最长的那个物化视图计算，并行度由<strong>max_threads</strong>控制。<br>物化视图在数据写入之后，类似于查基础表的方式查询就行，如果有聚合函数字段，需要去解这个中间状态得到结果，-State 和-Merge组合器的配套使用。</p>
<h3 id="952c0308-0b2e-9dfa-c4c6-ad74261f05fc" class="toc-enable">2.物化视图组合指标宽表</h3>
<p>在直播业务的实际使用中，我们遇到了以下问题：</p>
<ul><li>直播指标来源于多个基础表，分析查询时需要将多个协议关联分析，在hive中通常采用join的方式实现，但是在clickhouse 分布式join性能较差。</li>
<li>基于关联查询会导致查询分析时sql复杂，SQL长达上千行，可读性差，维护困难。</li>
<li>维度实时更新问题，有些维度基于当时的状态，不能查询时关联。</li>
</ul><p><strong>思考点：</strong></p>
<ul><li>ClickHouse 分布式Join差属于查询引擎实现机制问题，改造困难，开发耗时长；</li>
<li>基于不同的基础表生成物化视图，最终维度关联仍然需要join或者union实现，虽然能降低io，但是还是效率差，上层使用还是不方便。</li>
</ul><p><strong>解决方案：通过多个基础表物化视图指标预计算组合成指标宽表解决。</strong></p>
<p>以直播场景为例，我们的数据上游有多个协议，在经过flink关联画像和实验信息后写入到clickhouse。<br>每张基础表的数据会通过物化视图进行计算，然后指定字段写入到一个公共的存储<strong>table</strong>中，每个指标来源于上游某个基础表的计算逻辑生成，也可以来自与多个基础表的计算逻辑共同生成，不参与计算的字段将由默认值填充。<br>相当于计算层union all的实现机制。<br>物化视图<strong>table</strong>只存储一份数据，由多个物化视图的<strong>view</strong>计算得到，然后使用ReplicatedAggregatingMergeTree通过后台merge将数据打平(可以手动触发)。<br>以直播的物化视图大盘中间表举例介绍实现过程：</p>
<p style=""><img src="./【WeOLAP】ClickHouse物化视图在直播场景中的实践 - OLAP - KM平台_files/cos-file-url(14)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" width="733" height="250" alt="" class="amplify"></p>
<p>直播的物化视图大盘数据表，共有33个维度，110个指标，一共使用了3个聚合函数(uniqCombined,sum,groupBitmap)，其中指标字段都是聚合函数字段AggregateFunction字段。<br>接入层写入clickhouse生成6个mid基础表，每个基础表对应一个物化视图view，然后<strong>共同</strong>写入一个物化视图table。这里采用的是物化视图view和table分离的建表方式，TO模式写入。<br>比如mid_10001是关于曝光的数据，根据公共维度，计算曝光相关指标（AggregateFunction(uniqCombined,UInt64)），然后写入到物化视图table中指定的字段中。<br>每个数据流都只需要产出相关的部分数据，某个流的指标延迟，也不会影响其他流。<br>物化视图table采用的是ReplicatedAggregatingMergeTree，数据会在后台自动根据维度数据merge聚合函数中间态，将多个流写入的数据聚合打平，让记录和存储进一步降低。<br>以指标宽表的方式解决了指标关联问题，查询基于单表进行，上层查询只需要通过简单select即可得到结果，符合clickhouse使用场景，使用便捷，查询高效。</p>
<h3 id="8c7fa959-8984-fc23-83ae-67695983ffc8" class="toc-enable">3.物化视图结合外部字典实现维度补充</h3>
<p>在直播场景中，需要将实验补充、直播热度等低基数维度关联到clickhouse，既有计算关联，也有查询关联。<br>依赖clickhouse数据进行计算得到热度和聚集度的数据，这些数据因为是状态数据，需要进行计算时关联。<br>我们选择使用clickhouse外部字典进行这方面数据的加工和补充。<br>外部字典是clickhouse中的一种高效维表实现方式，具有以下优势：</p>
<ul><li>kv存储，支持多种存储介质，如内存、缓存、SSD、外部来源</li>
<li>高效查询</li>
<li>支持压缩</li>
<li>使用便捷</li>
<li>自动加载和更新</li>
</ul><p>字典查询的方式：</p>
<div class="km_insert_code">
<pre class="language-sql" style="position: relative; z-index: 2;"><code class="prism language-sql"><span class="token comment">--普通查询</span>
<span class="token keyword">select</span> dictGet<span class="token punctuation">(</span><span class="token string">'test.hot_view_dim'</span><span class="token punctuation">,</span><span class="token string">'rank_'</span><span class="token punctuation">,</span>toUInt64OrZero<span class="token punctuation">(</span>id_<span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token comment">--这里的id_ 是表中的字段，通过传入id_获得人数和排名</span>

<span class="token comment">--在物化视图中补全维度</span>
<span class="token keyword">WITH</span> dictGet<span class="token punctuation">(</span><span class="token string">'test.hot_view_dim'</span><span class="token punctuation">,</span><span class="token string">'rank_'</span><span class="token punctuation">,</span>toUInt64OrZero<span class="token punctuation">(</span>id_<span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token keyword">AS</span> rank_
<span class="token keyword">select</span> multiIf<span class="token punctuation">(</span> rank_<span class="token operator">&gt;</span><span class="token number">0</span> <span class="token operator">AND</span> rank_<span class="token operator">&lt;=</span><span class="token number">10</span><span class="token punctuation">,</span><span class="token string">'top10'</span>
             <span class="token punctuation">,</span>rank_<span class="token operator">&gt;</span><span class="token number">10</span> <span class="token operator">AND</span> rank_<span class="token operator">&lt;=</span><span class="token number">100</span><span class="token punctuation">,</span><span class="token string">'top100'</span>
             <span class="token punctuation">,</span>rank_<span class="token operator">&gt;</span><span class="token number">100</span> <span class="token operator">AND</span> rank_<span class="token operator">&lt;=</span><span class="token number">200</span><span class="token punctuation">,</span><span class="token string">'top200'</span>
             <span class="token punctuation">,</span>rank_<span class="token operator">&gt;</span><span class="token number">200</span><span class="token punctuation">,</span><span class="token string">'top200+'</span>
             <span class="token punctuation">,</span><span class="token string">'未知'</span><span class="token punctuation">)</span> <span class="token keyword">AS</span> rank_top_
    <span class="token punctuation">,</span><span class="token punctuation">`</span>各种维度<span class="token punctuation">`</span>
    <span class="token punctuation">,</span><span class="token punctuation">`</span>各种指标<span class="token punctuation">`</span>
<span class="token keyword">from</span> test<span class="token punctuation">.</span><span class="token keyword">table</span>
<span class="token keyword">group</span> <span class="token keyword">by</span> rank_top_<span class="token punctuation">,</span><span class="token punctuation">`</span>各种维度<span class="token punctuation">`</span></code></pre>

<p>我们针对外部字典做的一些测试数据。内存存储，对比不同数据量，正常内存存储和内存压缩存储，以UInt64为key，Int8，Int8两个值为属性，做了以下测试：</p>
<table class="wrapped confluenceTable" style="margin-left:30px;"><colgroup><col style="width:93px;"><col style="width:119px;"><col style="width:107px;"><col style="width:107px;"><col style="width:107px;"></colgroup><thead style="margin-left:30px;"><tr style="margin-left:30px;"><th class="confluenceTh" style="text-align:left;">
<p style="margin-left:30px;">数据量</p>
</th>
<th class="confluenceTh" style="text-align:left;">
<p style="margin-left:30px;">存储结构</p>
</th>
<th class="confluenceTh" style="text-align:left;">
<p style="margin-left:30px;">存储大小</p>
</th>
<th class="confluenceTh" style="text-align:left;">
<p style="margin-left:30px;">加载时间</p>
</th>
<th class="confluenceTh" style="text-align:left;">
<p style="margin-left:30px;">查询耗时</p>
</th>
</tr></thead><tbody style="margin-left:30px;"><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;" colspan="1">2000w</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">MergeTree</td>
<td class="confluenceTd" style="text-align:left;" colspan="1"><br></td>
<td class="confluenceTd" style="text-align:left;" colspan="1"><br></td>
<td class="confluenceTd" style="text-align:left;" colspan="1">0.052 sec</td>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;">2000w</td>
<td class="confluenceTd" style="text-align:left;">sparse_hashed</td>
<td class="confluenceTd" style="text-align:left;">420Mb</td>
<td class="confluenceTd" style="text-align:left;">23.939&nbsp;sec</td>
<td class="confluenceTd" style="text-align:left;">0.365 sec</td>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;">2000w</td>
<td class="confluenceTd" style="text-align:left;">hashed</td>
<td class="confluenceTd" style="text-align:left;">2147Mb</td>
<td class="confluenceTd" style="text-align:left;">6.921&nbsp;sec</td>
<td class="confluenceTd" style="text-align:left;">0.097&nbsp;sec</td>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;">5000w</td>
<td class="confluenceTd" style="text-align:left;">MergeTree</td>
<td class="confluenceTd" style="text-align:left;"><br></td>
<td class="confluenceTd" style="text-align:left;"><br></td>
<td class="confluenceTd" style="text-align:left;">0.114 sec</td>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;">5000w</td>
<td class="confluenceTd" style="text-align:left;">sparse_hashed</td>
<td class="confluenceTd" style="text-align:left;">1023Mb</td>
<td class="confluenceTd" style="text-align:left;">70.895&nbsp;sec</td>
<td class="confluenceTd" style="text-align:left;">1.135 sec</td>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;">5000w</td>
<td class="confluenceTd" style="text-align:left;">hashed</td>
<td class="confluenceTd" style="text-align:left;">4294Mb</td>
<td class="confluenceTd" style="text-align:left;">17.475&nbsp;sec</td>
<td class="confluenceTd" style="text-align:left;">0.238 sec</td>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;" colspan="1">10000w</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">MergeTree</td>
<td class="confluenceTd" style="text-align:left;" colspan="1"><br></td>
<td class="confluenceTd" style="text-align:left;" colspan="1"><br></td>
<td class="confluenceTd" style="text-align:left;" colspan="1">0.214 sec</td>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;" colspan="1">10000w</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">sparse_hashed</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">2053Mb</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">148.11&nbsp;sec</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">2.227 sec</td>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" style="text-align:left;" colspan="1">10000w</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">hashed</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">8589Mb</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">37.185 sec</td>
<td class="confluenceTd" style="text-align:left;" colspan="1">0.453 sec</td>
</tr></tbody></table><p>其中 key UInt64 占用8个bytes，2个value Int8、Int8 各占1个字节。<br></p>
<table class="fixed-table wrapped confluenceTable" style="height:113px;margin-left:30px;" width="843"><colgroup><col style="width:80px;"><col style="width:60px;"><col style="width:75px;"><col style="width:69px;"><col style="width:69px;"><col style="width:54px;"><col style="width:56px;"><col style="width:58px;"><col style="width:59px;"><col style="width:74px;"><col style="width:75px;"></colgroup><tbody style="margin-left:30px;"><tr style="margin-left:30px;"><th class="confluenceTh" style="width:65.375px;"><br></th>
<th class="confluenceTh" style="width:42.2969px;">UInt8</th>
<th class="confluenceTh" style="width:59.6094px;">UInt16</th>
<th class="confluenceTh" style="width:52.6875px;">UInt32</th>
<th class="confluenceTh" style="width:52.6875px;">UInt64</th>
<th class="confluenceTh" style="width:35.3594px;">Int8</th>
<th class="confluenceTh" style="width:37.6719px;">Int16</th>
<th class="confluenceTh" style="width:39.9688px;">Int32</th>
<th class="confluenceTh" style="width:41.1406px;">Int64</th>
<th class="confluenceTh" style="width:58.4688px;">Float32</th>
<th class="confluenceTh" style="width:59.7344px;">Float64</th>
</tr><tr style="margin-left:30px;"><td class="confluenceTd" colspan="1" style="width:65.375px;">byteSize</td>
<td class="confluenceTd" style="width:42.2969px;">1</td>
<td class="confluenceTd" style="width:59.6094px;">2</td>
<td class="confluenceTd" style="width:52.6875px;">4</td>
<td class="confluenceTd" style="width:52.6875px;">8</td>
<td class="confluenceTd" style="width:35.3594px;">1</td>
<td class="confluenceTd" style="width:37.6719px;">2</td>
<td class="confluenceTd" style="width:39.9688px;">4</td>
<td class="confluenceTd" style="width:41.1406px;">8</td>
<td class="confluenceTd" style="width:58.4688px;">4</td>
<td class="confluenceTd" style="width:59.7344px;">8</td>
</tr></tbody></table><p>String 空字符串占9个bytes，一个英文符号1个bytes，1个中文符号3个bytes，。<br>容量可参考在redis中的内存使用（参考网址<a href="http://www.redis.cn/redis_memory/">http://www.redis.cn/redis_memory/</a>），与ClickHouse内存使用相差不大 。<br><strong>在字典的使用中，需要注意以下问题：</strong></p>
<ul><li>字典是惰性加载的，创建后不会立即加载，首次查询会全量加载；</li>
<li>字典更新是全量更新，只有完全加载新数据才会替换老的数据；</li>
<li>字典的更新逻辑中不要引用该字典，服务重启时会出现循环引用问题，导致死锁；</li>
<li>字典是本地的，每个节点都会单独拉取一份数据，如果指向一个host，会导致加载时资源暴涨，容易出现单点故障；</li>
<li>字典的容量是有限的，如果量大的维表，建议做key hash 后本地join。</li>
</ul><h2 id="a7096fe8-5a89-f542-1c91-64497ea81b7b" class="toc-enable">六、总结</h2>
<h3 id="fc66991f-0e1c-e830-33b3-b59977aef3d2" class="toc-enable"><strong>1.物化视图</strong></h3>
<p>ClickHouse物化视图是非常强大的功能，可以提供快速稳定的查询服务，合理使用物化视图可以提高查询效率，降低磁盘IO，提高系统的查询吞吐量。<br>通过将物化视图view和table的拆分后，以多个view写同一个table的方式实现多个协议的指标计算，生成指标宽表，降低维护成本，简化上层查询方式。<br>物化视图可以在计算过程中结合字典实现计算时维度补全，字典的数据也可以来自于物化视图，互相结合使用支撑更多的查询场景。<br>物化视图和字典还是有学习和使用成本的，需要结合业务场景多思考多使用多优化。希望大家可以合理利用物化视图解决业务遇到的实际问题，也可以相互交流使用场景和遇到的问题。</p>
<h3 id="fb38c57b-6898-8f5b-ec69-6786bbe48c91" class="toc-enable"><strong>2.优化方向</strong></h3>
<ul><li><strong>Uin Hash</strong>：预先将uin hash之后，每个节点计算后的物化视图在分布式查询时，可以避免传输聚合函数中间状态，通过传输结果可以较大程度提高查询效率，目前已在部分集群实现，表现很好；</li>
<li><strong>查询优化</strong>：集群中很多sql以hive的代码风格提交，在clickhouse可能执行效率不高，需要借助query server 提供拦截、限流、智能分析优化等能力；</li>
<li><strong>数据均衡</strong>：clickhouse依赖于高性能本地硬盘提供高效查询，存储有限，同时架构决定了扩容会带来数据均衡问题，目前已上线数据均衡服务，符合预期，后续优化均衡的性能，目前也在和云OLAP团队共建存算分离方案；</li>
<li><strong>projection</strong>：projection作为社区新版本功能，是一种另外的预聚合模式，在测试版本兼容性后将逐步应用于业务实际场景中。</li>
</ul><h3 id="51081689-f95e-ecc8-2f0e-793e96ccecbe" class="toc-enable"><strong>3.平台化实践</strong></h3>
<p>Clickhouse是非常强大的OLAP查询引擎，引擎本身门槛较高，<strong>易用难精</strong>，需要投入较多人力开发。<br>数据中心提供fisher平台进行封装，<span style="color:#993300;"><strong>让用户无感知内部的实现机制，支持10分钟完成数据接入，并集成了Superset和Datetalk支持敏捷分析，轻松使用ClickHouse得到最佳性能体验，欢迎试用<a href="http://fisher.woa.com/">Fisher数据分析平台</a></strong></span></p>
<h2 id="cf017e69-10e9-93b0-1688-5b6d5b51560d" class="toc-enable"><span style="color:#003366;">七、致谢&amp;后续</span></h2>
<h3 id="93300895-a6b5-03ce-629a-b3eabca5a39f" class="toc-enable">致谢</h3>
<p>在物化视图实践过程中，和koningliu一起完成物化视图组合指标宽表和字典应用的测试和结论输出。chaoboxiong基于数仓模型和业务口径抽象整合出贴合业务场景的多个指标宽表，并在直播、视频号、搜一搜等业务中落地应用。<br>非常感谢@koningliu和@chaoboxiong对于整个应用实践过程的大力支持。<br>非常感谢@huaweihuang和@lucasdong对本篇文章的排版格式、内容、叙述逻辑等方面的审阅和修改意见。<br></p>
<h3 id="4a910bc3-2520-11d8-81aa-af12c9680c04" class="toc-enable"><strong>后续</strong></h3>
<p>数据中心长期招聘<u>数据库内核开发人员、后台开发人员、实时数仓开发，数据分析师</u>等岗位，欢迎广大同学加入，让我们一起做对用户有价值的事情（<strong><a class="external-link" href="http://huoshui.oa.com/huoshui/page/my/apply/77804">JD</a></strong>）。</p>
<p>文章待续 参看 WeOLAP 系列文集：</p>
<p>WeOLAP ：基于Clickhouse内核的云原生数仓WeOLAP<em>(合作出品)</em></p>
<p>WeOLAP 生态：WeOLAP Sinker 百亿级接入层的设计与实现</p>
<p>WeOLAP 生态：WeOLAP Manager 千台规模生产集群“高可用”自动化运维挑战</p>
<p>WeOLAP 生态：WeOLAP QueryServer 集群过载保护机制与智能SQL分析的应用</p>
<p>WeOLAP 核心技术：End2End全链路精确一次写入的思考、实现与自证</p>
<p>WeOLAP 核心技术：存算分离技术生产环境落地挑战<em>(合作出品)</em></p>
<p>WeOLAP 核心技术：WeOLAP！？如何做到生产环境万亿规模单表P95查询时延5s内&nbsp;</p>
<p>WeOLAP 应用实践：Clickhouse在X实验平台场景下50倍性能优化之路</p>
<p>WeOLAP 内核：Clickhouse 线程模型</p>
<p>WeOLAP 内核：<a href="https://km.woa.com/group/wxolap/articles/show/487828" target="_blank" rel="noreferrer">Clickhouse 查询优化指南</a></p>
<p>WeOLAP 内核：Clickhouse 基于ZK的同步机制</p>
<p>WeOLAP 内核：Clickhouse 索引和二级索引</p>				</div>
