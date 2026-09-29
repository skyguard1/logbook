---
title: "【WEOLAP】ClickHouse SQL优化案例"
date: 2022-06-16 07:54:31
categories:
  - flink
  - SQL与查询优化
---

{% raw %}

<div><dir><p>目录</p><li>一、背景</li><li>二、优化思路</li><li>三、数据集</li><li>四、优化场景和案例</li><li>      1. 基础字段选择</li><li>      2. 过滤场景</li><li>      3. UNION ALL场景</li><li>      4. with子查询（CTE）</li><li>      5. Join 场景</li><li>      6. 去重场景</li><li>      7. 写入即计算（物化列）</li><li>      8. 元数据查询</li><li>五、总结</li><li>六、致谢</li></dir><h1>一、背景</h1><p>随着接入的业务增多，集群的规模和数据量的持续增长，业务同学在受益ClickHouse的高速查询时，提交的未优化或者不合理的查询也逐步增多。慢查询和大查询不止影响业务同学的体验，也容易产生较高的集群CPU负载、IO占用、内存占用。结合目前的业务查询场景，一起做了一些慢查询和大查询的优化，总结一些SQL优化的经验，分享给大家参考和借鉴。</p><h1>二、优化思路</h1><p>本文主要讲了一些业务场景下的优化案例：</p><ul><li><p>基础字段的合理选择可以有效降低表的存储，提升表的写入和读取、过滤性能。</p></li><li><p>表的量级到一定规模时，合理的使用分区和主键可以有效降低读取量，提升查询效率。跳数/稀疏索引在一定程度上可以缓解表主键设计不合理的情况下查询效率低下的问题。</p></li><li><p>在一些union all 的场景下，对一张表的多次读取可以借助array join 实现一次读取，较大程度减少IO带宽占用，从而降低查询耗时。</p></li><li><p>with子查询（CTE）可以通过缓存临时数据，简化代码，增加可读性，同时也替代一些cross join场景下的占比计算，提高查询效率。</p></li><li><p>分布式Join的效率较差时，可以结合with子查询（CTE）对关联key进行手动下推，从而在表读取时过滤数据，减少不必要的数据广播，提升计算效率，降低Join的内存使用。</p></li><li><p>OLAP场景下，精确去重意味着高内存使用和高查询耗时，需要在精度和查询耗时做一些折中，模糊计算可以极大的提高查询效率，推荐使用。</p></li><li><p>物化列可以部分场景替代物化视图的计算逻辑，简化使用成本，可以很容易的实现写入即计算。</p></li><li><p>列举了一些常用的元数据查询的SQL，包含获得表的记录和存储占用，物化视图的依赖关系，表字段的查询频率等。</p></li></ul><p>本文列举了大量的SQL代码和配图，篇幅较长，请耐心阅读。</p><h1>三、数据集</h1><p>为了容易的描述优化场景和方法，先抽象一个简单的用户点击数据集。
建表语句和生成规则如下。</p><div>
<pre>drop table if exists test.test_dataset_t1_local on cluster mmdcchsvrnewtest;
create  table test.test_dataset_t1_local on cluster mmdcchsvrnewtest
(
    `day_` Date COMMENT '数据时间-天',
    `hour_` DateTime COMMENT '数据时间-小时',
    `minute_` DateTime COMMENT '数据时间-分钟',
    `u8_type` UInt8,
    `u16_subtype` UInt16,
    `u32_uid` UInt32,
    `u64_feedid` UInt64,
    `str_sessionid` String,
    `shown_time` UInt32,
    `click_cnt` UInt32
)
ENGINE = ReplicatedMergeTree('/clickhouse/tables/{layer}-{shard}/test.test_dataset_t1_local', '{replica}')
PARTITION BY day_
PRIMARY KEY (hour_,minute_,u8_type,u16_subtype)
ORDER BY (hour_,minute_,u8_type,u16_subtype)
TTL (day_ + toIntervalDay(3600)) + toIntervalHour(4)
SETTINGS index_granularity = 8192, use_minimalistic_part_header_in_zookeeper = 1;

drop table if exists test.test_dataset_t1 on cluster mmdcchsvrnewtest;
create  table test.test_dataset_t1 on cluster mmdcchsvrnewtest
as test.test_dataset_t1_local
engine=Distributed(mmdcchsvrnewtest,test,test_dataset_t1_local,rand());

set distributed_directory_monitor_sleep_time_ms=3000;
set insert_distributed_sync=0;
INSERT INTO test.test_dataset_t1 SELECT
    toDate('2022-05-25') - (x1 % 7) AS day_,
    toStartOfHour(minute_) AS hour_,
    toStartOfMinute(toDateTime(day_) + (x2 % 86399)) AS minute_,
    u8_type % 10 AS u8_type,
    u16_subtype % 100 AS u16_subtype,
    u32_uid % 1000000 AS u32_uid,
    u64_feedid % 200000 AS u64_feedid,
    toString(str_sessionid) AS str_sessionid,
    shown_time,
    click_cnt
FROM generateRandom('x1 UInt32, x2 UInt32, u8_type UInt8,u16_subtype UInt16, u32_uid UInt32, u64_feedid UInt64, str_sessionid UUID ,shown_time UInt32,click_cnt UInt32', 1, 3)
LIMIT 561282820;

optimize table test.test_dataset_t1_local on cluster mmdcchsvrnewtest;

SELECT
    _shard_num,
    sum(1) AS s,
    sum(rows) AS r,
    sum(bytes) AS b
FROM cluster(mmdcchsvrnewtest, system, parts)
WHERE table = 'test_dataset_t1_local'
GROUP BY _shard_num
ORDER BY _shard_num ASC

┌─_shard_num─┬──s─┬─────────r─┬───────────b─┐
│          1 │ 53 │ 187100410 │ 10157073992 │
│          2 │ 41 │ 187109173 │ 10157469034 │
│          3 │ 64 │ 187073237 │ 10174547290 │
└────────────┴────┴───────────┴─────────────┘</pre>
</div><h1>四、优化场景和案例</h1><h2>1. 基础字段选择</h2><p>clickhouse 的字段类型在函数使用中，要求是很严格的，不同字段类型几乎不会隐式转换，数值之间会向上+1 兼容。常用的基础字段类型会占用多少存储，聚合和过滤效果怎么样，这里用测试数据给大家在选择字段类型时有个参考。
假设我们从 1-100 数字随机取 10 亿个，分别用不同的数据类型存储，表的空间为多少，去重查询 TP50。</p><p><strong>注：表为单个字段(无分区 key 和主键)，均进行 optimize 强制 merge, 耗时为 benchmark(c=1,i=10)后取 50%耗时。</strong></p><div>
<table><thead><tr><th>字段类型</th><th>占用<br/>字节</th><th>生成<br/>耗时s</th><th>表存储（GB）</th><th>去重 TP50s</th><th>过滤 TP50s</th></tr></thead><tbody><tr><td>Int8</td><td>1</td><td>4.917</td><td>0.938</td><td>1.074</td><td>0.07</td></tr><tr><td>Int16</td><td>2</td><td>13.469</td><td>1.43</td><td>1.15</td><td>0.205</td></tr><tr><td>Int32</td><td>4</td><td>18.488</td><td>2.76</td><td>1.362</td><td>0.477</td></tr><tr><td>Int64</td><td>8</td><td>21.624</td><td>2.79</td><td>1.547</td><td>0.491</td></tr><tr><td>UInt8</td><td>1</td><td>4.785</td><td>0.938</td><td>1.007</td><td>0.089</td></tr><tr><td>UInt16</td><td>2</td><td>12.367</td><td>1.43</td><td>1.067</td><td>0.169</td></tr><tr><td>UInt32</td><td>4</td><td>18.794</td><td>2.76</td><td>1.385</td><td>0.441</td></tr><tr><td>UInt64</td><td>8</td><td>22.607</td><td>2.79</td><td>1.428</td><td>0.471</td></tr><tr><td>Float32</td><td>4</td><td>19.898</td><td>2.74</td><td>2.091</td><td>0.462</td></tr><tr><td>Float64</td><td>8</td><td>22.415</td><td>2.8</td><td>1.649</td><td>0.487</td></tr><tr><td>String</td><td>9+n</td><td>35.908</td><td>1.79</td><td>4.414</td><td>0.997</td></tr><tr><td>LowCardinality(String)</td><td>n</td><td>39.35</td><td>0.943</td><td>4.525</td><td>0.226</td></tr><tr><td>Nullalbe(Int8)</td><td>1</td><td>6.233</td><td>0.945</td><td>1.095</td><td>0.137</td></tr><tr><td>Nullalbe(Int16)</td><td>2</td><td>13.131</td><td>1.43</td><td>1.213</td><td>0.245</td></tr><tr><td>Nullalbe(Int32)</td><td>4</td><td>20.466</td><td>2.76</td><td>1.566</td><td>0.548</td></tr><tr><td>Nullalbe(Int64)</td><td>8</td><td>24.12</td><td>2.79</td><td>1.602</td><td>0.604</td></tr><tr><td>Nullalbe(UInt8)</td><td>1</td><td>5.301</td><td>0.945</td><td>1.105</td><td>0.148</td></tr><tr><td>Nullalbe(UInt16)</td><td>2</td><td>14.181</td><td>1.43</td><td>1.311</td><td>0.247</td></tr><tr><td>Nullalbe(UInt32)</td><td>4</td><td>20.163</td><td>2.76</td><td>1.541</td><td>0.552</td></tr><tr><td>Nullalbe(UInt64)</td><td>8</td><td>23.701</td><td>2.79</td><td>1.561</td><td>0.591</td></tr><tr><td>Nullalbe(Float32)</td><td>4</td><td>21.582</td><td>2.75</td><td>2.228</td><td>0.58</td></tr><tr><td>Nullalbe(Float64)</td><td>8</td><td>22.415</td><td>2.8</td><td>1.805</td><td>0.594</td></tr><tr><td>Nullalbe(String)</td><td>9+n</td><td>35.908</td><td>1.8</td><td>4.447</td><td>1.106</td></tr><tr><td>LowCardinality(Nullable(String))</td><td>n</td><td>39.081</td><td>0.943</td><td>4.576</td><td>0.321</td></tr></tbody></table></div><p>结合测试数据，可以得到以下结论：</p><ol><li><p>选择合理的字段类型可以明显加速大数据量下的写入、去重和过滤。</p></li><li><p>存储相同的数据，String 的查询和过滤的性能是最差的。同时在生成数据，写入表中也是最慢的。</p></li><li><p>低基数通过 part 级别字典编码优化了存储和查询耗时，但是因为多了编码环节增加了写入耗时。</p></li><li><p>Nullable 类型需要额外的空间存储 null 的信息，且在去重和过滤时耗时会多 10%-20%的耗时，通常建议不要定义 Nullable 类型。</p></li></ol><p>注：<strong>String存储偏低是因为1-100占用的空间较小，如果是实际数据，存储会远远高于这个</strong>。
所以在接入数据的时候，合理的选择字段，不仅可以降低存储，也可以提升聚合和过滤的效率。所以能用UInt8不用UInt64，能用UInt或者Int不用String。</p><h2>2. 过滤场景</h2><p>在ClickHouse中，索引共有MinMax索引，Partition索引，PrimaryKey索引，Data Skipping索引。我们的查询中，建议尽可能按照 从前往后的顺序依次过滤，会达到最好的查询效率。可以通过explain indexes=1 SQL 查询这次查询是否命中索引(只会展示当前节点，不会跨节点)。
在查询数据时，应该先指定分区（比如day_='2022-05-25'）时，会先命中MinMax索引和Partition索引，这时选择读取的part就只有2022-05-25分区的part。
<img alt="" loading="lazy" src="/logbook/images/flink/3140fffee72189df4bf0.png"/></p><p>如果我们想要查询某个小时（2022-05-25 12:00:00）的数据，常见的会有两种写法:</p><ol><li><p>where day_='2022-05-25' and hour_='2022-05-25 12:00:00'</p></li><li><p>where hour_='2022-05-25 12:00:00'</p></li></ol><p>在表test.test_dataset_t1_local 中，hour_是主键的第一个字段，写法1 day_会先命中MinMax索引和Partition索引，然后hour_会命中PrimaryKey索引。写法2 只有hour_命中PrimaryKey索引。</p><p>写法1：MinMax索引和Partition索引过滤9/53 个part，hour_过滤了144/3268 个Granule。
<img alt="" loading="lazy" src="/logbook/images/flink/1aec7eb6ed70f00ce6b0.png"/> </p><p>写法2：MinMax索引和Partition索引没有使用，hour_过滤了9/15和part，144/3268 个Granule。
<img alt="" loading="lazy" src="/logbook/images/flink/008596a30c6c982906f9.png"/> </p><p>结合explain和实际的查询测试，当hour_位于第一个主键时，两种的查询效率几乎是一样的，因为在查询前就已经确认了要读哪些granule。
minute_是主键中的第二个字段，那么查minute_呢？
常见的3种写法:</p><ol><li><p>where day_='2022-05-25' and hour_='2022-05-25 12:00:00' and minute_='2022-05-25 12:30:00'</p></li><li><p>where  day_='2022-05-25' and minute_='2022-05-25 12:30:00'</p></li><li><p>where  minute_='2022-05-25 12:30:00'</p></li></ol><p>写法1：MinMax索引和Partition索引过滤9/53 个part，hour_和minute_过滤了12/3268 个Granules。
<img alt="" loading="lazy" src="/logbook/images/flink/1e369f95a74265e85810.png"/> </p><p>写法2：MinMax索引和Partition索引过滤9/53 个part，minute_过滤了219/3268 个Granules。
<img alt="" loading="lazy" src="/logbook/images/flink/a7c4831ce2e64ce35614.png"/> </p><p>写法3：MinMax索引和Partition索引没有使用，minute_没有过滤part，过滤了1197/3268 个Granules。
<img alt="" loading="lazy" src="/logbook/images/flink/ab59933160640dc4020b.png"/> </p><p>然后对比一下查询耗时和查询数据量（benchmart i=100,c=5）</p><div>
<table><thead><tr><th></th><th>耗时TP50</th><th>耗时TP90</th><th>单次读取行数</th><th>单次读取大小</th></tr></thead><tbody><tr><td>写法1</td><td>0.034s</td><td>0.057s</td><td>25.4万</td><td>13.93 MB</td></tr><tr><td>写法2</td><td>0.035s</td><td>0.068s</td><td>444万</td><td>34.31 MB</td></tr><tr><td>写法3</td><td>0.049s</td><td>0.093s</td><td>2758万</td><td>118.31 MB</td></tr></tbody></table></div><p>结合测试数据，三种不同的写法，因为命中的索引不同，读取的数据量也不同，最终的查询耗时也不同。以写法1为最优，写法2次之，不推荐使用写法3。
这个在生产环境表现更明显(生产环境数据会远远大于测试数据集)。</p><p>针对写法2和写法3有什么方式可以减少扫描的数据量，优化这个查询呢？
<strong>使用跳数/稀疏索引。</strong>
通过以下sql可以快速创建一个minmax 跳数/稀疏索引。</p><div>
<pre>ALTER TABLE test.test_dataset_t1_local on cluster mmdcchsvrnewtest  ADD INDEX minute_index_ minute_ TYPE minmax GRANULARITY 2;
ALTER TABLE test.test_dataset_t1_local on cluster mmdcchsvrnewtest MATERIALIZE INDEX minute_index_;</pre>
</div><p>写法2和写法3 在查询的时候会多一次跳数索引检索。</p><p><img alt="" loading="lazy" src="/logbook/images/flink/ac364f44cfcfafb753d4.png"/></p><p><img alt="" loading="lazy" src="/logbook/images/flink/6136debc440c658a40db.png"/></p><p>在增加minute_的跳数索引后，再次对比查询耗时和查询数据量（benchmart i=100，c=5，max_threads=16）。</p><p>可以看到，在增加minute_的跳数索引后，查询的读取行数和大小明显减低，查询耗时也明显降低。
如果我想进行一些点查的场景，比如查某个u32_uid的数据呢？
此时我们发现，uid并没有在主键列表中，MinMax索引，Partition索引，PrimaryKey索引也都无法触发，唯一能加速的索引，只有跳数索引了。
跳数索引共有3种类型: Minmax，Set，BloomFilter。
u32_uid是一个高基数，所以Set明显是不适用的，因为uin可能出现在任何一个小时和分钟，且可能多次出现，Minmax也明显不适用，那么唯一的选择就是BloomFilter了。
创建一个BloomFilter索引：</p><div>
<pre>ALTER TABLE test.test_dataset_t1_local on cluster mmdcchsvrnewtest  ADD INDEX u32_uid_bm_index_ u32_uid TYPE bloom_filter GRANULARITY 2;
ALTER TABLE test.test_dataset_t1_local on cluster mmdcchsvrnewtest MATERIALIZE INDEX u32_uid_bm_index_;</pre>
</div><p>加索引后读取数据量:</p><div>
<table><thead><tr><th></th><th>耗时TP50</th><th>耗时TP90</th><th>单次读取行数</th><th>单次读取大小</th></tr></thead><tbody><tr><td>写法1</td><td>0.038s</td><td>0.066s</td><td>25.4万</td><td>13.93 MB</td></tr><tr><td>写法2</td><td>0.033s</td><td>0.058s</td><td>30.3万</td><td>13.62 MB</td></tr><tr><td>写法3</td><td>0.037s</td><td>0.064s</td><td>30.3万</td><td>13.50 MB</td></tr></tbody></table></div><p>跳数索引在部分场景下可以降低读取数据量，提升查询效率，但是需要选择合理的跳数索引的类型。
使用可以参考这些规则：</p><ul><li><p>有明显时间规律的字段，可以考虑使用minmax</p></li><li><p>低基数的类型可以考虑使用set，但是如果类型分布直接比较均匀，每个Granule都可能出现这些type的大部分，那么就不建议使用跳数索引了，无实际过滤效率。比如type为0和1的枚举值，每个Granule都有0和1出现，那么跳数索引就无法有效过滤出0和1所在的Granule，而会返回所有的Granule。</p></li><li><p>高基数的类型可以使用BloomFilter。</p></li></ul><p>总结来讲，在写clickhouse的SQL时，需要先指定分区进行part过滤，然后尽可能按照主键的顺序依次过滤，这样可以达到最优的查询效率。具体原理可以参考官网文章<a href="https://clickhouse.com/docs/en/guides/improving-query-performance/sparse-primary-indexes/sparse-primary-indexes-design">ClickHouse索引设计</a>。当主键索引不能满足实际的查询场景时，可以考虑使用跳数索引加速查询。</p><h2>3. UNION ALL场景</h2><p>业务场景经常会遇到对同一张表既需要计算各个分类的情况，又需要计算整个分类的数据，常规的做法是使用union all 将两个子查询的结果合并起来或者使用cube（如果维度不是唯一，cube计算存在很多无用计算）。在clickhouse中，每个子查询实际是提交到集群的独立SQL，相当于对原表发起了多次查询，然后再由汇总节点合并多次查询的结果。如果查询的表量级很大(日均TB)，读取多次，计算多次的代价非常高，如何避免？</p><p>使用<strong>Array Join</strong>。通过array join 可以避免多次查询，多次读取。可以很好的解决类似的业务场景。大多数场景，Array Join 多数情况下被用来进行一些字段的拆分列转行，比如Array Join splitByChar(',',expids_) as expid_。但是实际上array Join的使用上限很高，可以很友好 的解决对同一张表多次读取的情况。</p><p>以数据集举例说明:</p><p>CASE 1: 需要计算u8_type的1-10个枚举值下的uv和pv，又需要计算u8_type的1-10个枚举值下总uv和总pv。</p><p>常规写法:</p><div>
<pre>SELECT
    day_,
    type,
    uv,
    pv,
    cnt
FROM
(
    SELECT
        day_,
        CAST(u8_type, 'String') AS type,
        uniqCombined(u32_uid) AS uv,
        uniqCombined(u32_uid, str_sessionid) AS pv,
        sum(1) AS cnt
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
    GROUP BY
        day_,
        type
    UNION ALL
    SELECT
        day_,
        'ALL' AS type,
        uniqCombined(u32_uid) AS uv,
        uniqCombined(u32_uid, str_sessionid) AS pv,
        sum(1) AS cnt
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
    GROUP BY
        day_,
        type
)
10 rows in set. Elapsed: 1.092 sec. Processed 160.38 million rows, 8.34 GB (146.90 million rows/s., 7.64 GB/s.)</pre>
</div><p><strong>使用array Join改写后:</strong></p><div>
<pre>SELECT
    day_,
    dim_ AS type,
    uniqCombined(u32_uid) AS uv,
    uniqCombined(u32_uid, str_sessionid) AS pv,
    sum(1) AS cnt
FROM test.test_dataset_t1
ARRAY JOIN [CAST(u8_type, 'String'), 'ALL'] AS dim_
WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
GROUP BY
    day_,
    type
10 rows in set. Elapsed: 0.756 sec. Processed 80.19 million rows, 4.17 GB (106.07 million rows/s., 5.52 GB/s.)</pre>
</div><p>可以明显看到，读取数据量和读取大小都是改写前的1/2，查询耗时也有小幅度降低。
CASE 2:(1)需要计算u8_type的1-10个枚举值下且u16_subtype in (1,5) 的uv和pv；(2)需要计算u8_type的11-22个枚举值下且u16_subtype in (11,22)的uv和pv；(3)需要计算u8_type的33-40个枚举值下且u16_subtype in (33,40)的uv和pv；(4)需要计算总的uv和pv(不过滤u8_type和u16_subtype)。</p><p>常规写法:</p><div>
<pre>SELECT
    day_,
    type,
    uv,
    pv,
    cnt
FROM
(
    SELECT
        day_,
        CAST(u8_type, 'String') AS type,
        uniqCombined(u32_uid) AS uv,
        uniqCombined(u32_uid, str_sessionid) AS pv,
        sum(1) AS cnt
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND (u16_subtype IN (1, 5))
    GROUP BY
        day_,
        type
    UNION ALL
    SELECT
        day_,
        '11-22' AS type,
        uniqCombined(u32_uid) AS uv,
        uniqCombined(u32_uid, str_sessionid) AS pv,
        sum(1) AS cnt
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22)) AND (u16_subtype IN (11, 22))
    GROUP BY
        day_,
        type
    UNION ALL
    SELECT
        day_,
        '33-40' AS type,
        uniqCombined(u32_uid) AS uv,
        uniqCombined(u32_uid, str_sessionid) AS pv,
        sum(1) AS cnt
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (33, 34, 35, 36, 37, 38, 39, 40)) AND (u16_subtype IN (33, 40))
    GROUP BY
        day_,
        type
    UNION ALL
    SELECT
        day_,
        'ALL' AS type,
        uniqCombined(u32_uid) AS uv,
        uniqCombined(u32_uid, str_sessionid) AS pv,
        sum(1) AS cnt
    FROM test.test_dataset_t1
    WHERE day_ = '2022-05-25'
    GROUP BY
        day_,
        type
)
10 rows in set. Elapsed: 0.945 sec. Processed 320.72 million rows, 9.22 GB (339.33 million rows/s., 9.76 GB/s.)
--使用内存 791.85 MiB</pre>
</div><p><strong>使用Array Join改写后：</strong></p><div>
<pre>    select  day_
           ,dim_tup_.1                          as type
           ,uniqCombined(u32_uid)               as uv
           ,uniqCombined(u32_uid,str_sessionid) as pv
           ,sum(1)                              as cnt
    from test.test_dataset_t1 array Join [(CAST(u8_type,'String'),u8_type,[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],u16_subtype,[1,5]),('11-22',u8_type,[11,12,13,14,15,16,17,18,19,20,21,22],u16_subtype,[11,22]),('33-40',u8_type,[33,34,35,36,37,38,39,40],u16_subtype,[33,40]),('ALL',1,[1],1,[1])] as dim_tup_
    where (day_ = '2022-05-25')
    AND has(dim_tup_.3,dim_tup_.2)
    AND has(dim_tup_.5,dim_tup_.4)
    group by  day_
             ,type
10 rows in set. Elapsed: 1.586 sec. Processed 80.19 million rows, 4.33 GB (50.55 million rows/s., 2.73 GB/s.)
--使用内存 1.45 GiB</pre>
</div><p>读取行数是改写前的1/4，读取的大小约是改写前的1/2，耗时比原来的要高67%。这里耗时高是因为测试数据集的量级小，存储较小，导致读取速度不是该查询的瓶颈，所以每个子查询的读取耗时较低，所以总耗时较低，array join需要在内存膨胀这部分数据，所以一次读取后，计算耗时要偏大一些。</p><p>在实际的业务场景下，这个改写能有效降低对于ODS或者DWD的查询数据量，比如一次查询1TB-10TB，会占用较大集群IO资源的查询，具有非常明显的优化效果。大家可以结合业务场景和查询表现，选择是否使用Array Join进行改写。</p><p>这里再举个ArrayJoin的例子，算0点-23点的累计UV。</p><p>经常我们为了分析dau的上升趋势时，会选择按小时进行累计DAU的计算，通常采用的方式是每小时使用调度(或查询cache)或者多次union all进行计算，这里以array join为例，列举一个解决方案(并不是最优解)。</p><p>查询SQL:</p><div>
<pre>SELECT
    day_,
    agg_hour_,
    uniqCombined(u32_uid) AS uv,
    uniqCombined(u32_uid, str_sessionid) AS pv,
    sum(1) AS cnt
FROM test.test_dataset_t1
ARRAY JOIN timeSlots(toDateTime(day_), 86399, 3600) AS agg_hour_
WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND (hour_ &lt;= agg_hour_)
GROUP BY
    day_,
    agg_hour_
ORDER BY
    day_ ASC,
    agg_hour_ ASC</pre>
</div><p><img alt="" loading="lazy" src="/logbook/images/flink/0f534029d76a662e9cd9.png"/></p><h2>4. with子查询（CTE）</h2><p>ClickHouse支持公用表表达式（Common Table Expression，简称CTE）。CTE是在单个语句的执行范围内定义的临时结果集，只在查询期间有效。可以自引用，也可在同一查询中多次引用，实现了<strong>代码段的重复利用</strong>。</p><p>举一个简单的例子。计算各个分类对于总分类的占比。比较常见的写法是做一个cross join。</p><div>
<pre>SELECT
    day_,
    u8_type,
    uv,
    pv,
    round((uv / sum_uv) * 100, 2) AS uv_rate,
    round((pv / sum_pv) * 100, 2) AS pv_rate
FROM
(
    SELECT
        day_,
        u8_type,
        uniqCombined(u32_uid) AS uv,
        uniqCombined(u32_uid, str_sessionid) AS pv
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
    GROUP BY
        day_,
        u8_type
) AS t1
CROSS JOIN
(
    SELECT
        uniqCombined(u32_uid) AS sum_uv,
        uniqCombined(u32_uid, str_sessionid) AS sum_pv
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
) AS t2
9 rows in set. Elapsed: 1.122 sec. Processed 160.38 million rows, 8.34 GB (142.92 million rows/s., 7.43 GB/s.)
-- 使用内存 530.35 MiB</pre>
</div><p><strong>使用CTE改写后：</strong></p><div>
<pre>with (
    select (uniqCombined(u32_uid),uniqCombined(u32_uid,str_sessionid))
    from test.test_dataset_t1
    WHERE (day_ = '2022-05-25') and u8_type in (1,2,3,4,5,6,7,8,9,10)
) as metric_tup_
select day_,
     u8_type,
     uniqCombined(u32_uid)  as uv,
     uniqCombined(u32_uid,str_sessionid)  as pv,
     round(uv/metric_tup_.1*100,2) as uv_rate,
     round(pv/metric_tup_.2*100,2) as pv_rate
from test.test_dataset_t1
WHERE (day_ = '2022-05-25') and u8_type in (1,2,3,4,5,6,7,8,9,10)
group by day_,
        u8_type
9 rows in set. Elapsed: 1.019 sec. Processed 160.38 million rows, 8.34 GB (157.33 million rows/s., 8.18 GB/s.)
-- 使用内存 421.71 MiB</pre>
</div><p>我们需要进行一些逻辑上的转换，我们不想把这个字段在selelct中查出来，却多次使用这个转换后的结果，此时可以放在with中进行这个处理。</p><div>
<pre>WITH murmurHash3_32(u32_uid) AS u32_hash_uid
SELECT
    day_,
    u8_type,
    uniqCombined(u32_hash_uid, str_sessionid) AS pv
FROM test.test_dataset_t1
WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND ((u32_hash_uid % 100) IN (1, 3, 5, 7, 9))
GROUP BY
    day_,
    u8_type</pre>
</div><p>我们经常需要进行一些临时变量的命名，需要在查询中多次使用，只希望每次修改只需要改1个地方。</p><div>
<pre>WITH
    '2022-05-21' AS start_date,
    '2022-05-25' AS end_date,
    murmurHash3_32(u32_uid) AS u32_hash_uid
SELECT
    day_,
    u8_type,
    uniqCombined(u32_hash_uid, str_sessionid) AS pv
FROM test.test_dataset_t1
WHERE (day_ &gt;= start_date) AND (day_ &lt;= end_date) AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND ((u32_hash_uid % 100) IN (1, 3, 5, 7, 9))
GROUP BY
    day_,
    u8_type</pre>
</div><p>我们需要过滤一些用户，可以先用With子查询查一个固定人群的bitmap，然后在行为流水中过滤这部分用户计算uv，pv。</p><div>
<pre>WITH (
        SELECT groupBitmapState(u32_uid) AS bm
        FROM test.test_dataset_t1
        WHERE (day_ = '2022-05-25') AND (u8_type IN (1)) AND ((u32_uid % 23) = 3)
    ) AS bm
SELECT
    day_,
    u8_type,
    uniqCombined(u32_uid) AS uv,
    uniqCombined(u32_uid, str_sessionid) AS pv
FROM test.test_dataset_t1
WHERE (day_ = '2022-05-25') AND bitmapContains(bm, u32_uid) AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
GROUP BY
    day_,
    u8_type</pre>
</div><p>with子查询（CTE）的使用场景比较固定，需要注意的是，with返回的结果只能是单行记录，如果想要存储多行记录，需要进行行转列，存在Array或者Map中，然后查询时取对应的数据。</p><h2>5. Join 场景</h2><p>ClickHouse并不擅长进行分布式Join。在分布式Join下，会先计算右表(左表的读取会同时进行)，然后广播到各个shard，再与左表的local表进行计算，最终将各个shard的计算结果中间数据汇总到查询的节点进行数据最终计算。所以clickhouse建议大表在左，小表在右，这个和hive是刚好相反的。</p><p>所以通常会遇到几个问题:</p><ol><li><p>左表的关联key 并不会下推到右表中，在右表读取时过滤右表数据；</p></li><li><p>右表的关联key 也不会下推到左表中，在左表读取时过滤左表数据；</p></li><li><p>最终汇总查询的节点需要聚合各个节点的数据，容易超内存。</p></li></ol><p>所以我们可以借助CTE手动做这个下推操作。
举个Left Join例子：</p><div>
<pre>SELECT
    t1.day_,
    t1.u8_type,
    uniqCombined(t1.u32_uid) AS d0_uv,
    uniqCombined(t1.u32_uid, t1.u64_feedid) AS d0_pv,
    uniqCombinedIf(t2.u32_uid, t2.u32_uid != 0) AS d1_uv,
    uniqCombinedIf(t2.u32_uid, t2.u64_feedid, (t2.u32_uid != 0) AND (t2.u64_feedid != 0)) AS d1_pv
FROM test.test_dataset_t1 AS t1
LEFT JOIN
(
    SELECT
        u32_uid,
        u64_feedid
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
    GROUP BY
        u32_uid,
        u64_feedid
) AS t2 ON (t1.u32_uid = t2.u32_uid) AND (t1.u64_feedid = t2.u64_feedid)
WHERE (t1.day_ = '2022-05-24') AND (t1.u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) and t1.u32_uid % 23 = 3
GROUP BY
    t1.day_,
    t1.u8_type
9 rows in set. Elapsed: 29.870 sec. Processed 320.75 million rows, 4.81 GB (10.74 million rows/s., 161.07 MB/s.)
--10.25 GiB</pre>
</div><p>在这个例子中，我们计算的是2022-05-24的用户在2022-05-25的留存，是一个left join，在这个场景中，2022-05-24 和2022-05-25的用户群体会有交叉，但是只在25号出现，24号没有出现的用户，其实没有必要在右表中查询出来，应该做一个过滤，我们使用CTE过滤下。（因为测试数据用户量较小，所有的用户每天都会出现，所以加了一个t1.u32_uid % 3 = 3的逻辑模拟实际场景）。</p><p><strong>SQL改写后</strong></p><div>
<pre>with (
select groupBitmapState(u32_uid)
from test.test_dataset_t1
where day_='2022-05-24' and u8_type in (1,2,3,4,5,6,7,8,9,10) and u32_uid % 23 = 3
) as bm 
select t1.day_,
       t1.u8_type,
       uniqCombined(t1.u32_uid) as d0_uv,
       uniqCombined(t1.u32_uid,t1.u64_feedid) as d0_pv,
       uniqCombinedIf(t2.u32_uid,t2.u32_uid&lt;&gt;0) as d1_uv,
       uniqCombinedIf(t2.u32_uid,t2.u64_feedid,t2.u32_uid&lt;&gt;0 and t2.u64_feedid&lt;&gt;0) as d1_pv
from test.test_dataset_t1 as t1 
left join (
    select u32_uid,
          u64_feedid
    from test.test_dataset_t1
    where day_ = '2022-05-25'
    and u8_type in (1,2,3,4,5,6,7,8,9,10)
    and bitmapContains(bm,u32_uid)
    group by u32_uid,u64_feedid
) as t2 
on t1.u32_uid=t2.u32_uid and t1.u64_feedid=t2.u64_feedid 
where t1.day_='2022-05-24' and t1.u8_type in (1,2,3,4,5,6,7,8,9,10) and t1.u32_uid % 23 = 3
group by t1.day_,t1.u8_type
9 rows in set. Elapsed: 1.854 sec. Processed 481.09 million rows, 5.93 GB (259.52 million rows/s., 3.20 GB/s.)
--918.48 MiB</pre>
</div><p>改写后的分布式Join，在右表但不存在左表的用户，会在右表读取数据的同时过滤掉，会降低右表的实际读取量和广播量，这样在左表计算时，会减少计算量级，从而提升查询效率，在实际的生产场景，这样的查询能优化5X的查询性能，很多报超时的分布式Join 也能查询出来。<strong>可优化的必要前提是 t1的用户群体只会和t2的用户群体有交叉，不是包含关系。</strong></p><p>另外再举个Inner Join例子。</p><div>
<pre>SELECT
    t1.day_,
    t1.u8_type,
    uniqCombined(t1.u32_uid) AS d0_uv,
    uniqCombined(t1.u32_uid, t1.u64_feedid) AS d0_pv
FROM test.test_dataset_t1 AS t1
INNER JOIN
(
    SELECT
        u32_uid,
        u64_feedid
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
    GROUP BY
        u32_uid,
        u64_feedid
) AS t2 ON (t1.u32_uid = t2.u32_uid) AND (t1.u64_feedid = t2.u64_feedid)
WHERE (t1.day_ = '2022-05-24') AND (t1.u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND ((t1.u32_uid % 23) = 3)
GROUP BY
    t1.day_,
    t1.u8_type
9 rows in set. Elapsed: 33.309 sec. Processed 320.75 million rows, 4.81 GB (9.63 million rows/s., 144.44 MB/s.)
--10.27 GiB</pre>
</div><p><strong>使用CTE优化改写。</strong></p><div>
<pre>WITH
    (
        SELECT groupBitmapState(u32_uid)
        FROM test.test_dataset_t1
        WHERE (day_ = '2022-05-24') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND ((u32_uid % 23) = 3)
    ) AS bm1,
    (
        SELECT groupBitmapState(u32_uid)
        FROM test.test_dataset_t1
        WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND ((u32_uid % 23) = 3)
    ) AS bm2
SELECT
    t1.day_,
    t1.u8_type,
    uniqCombined(t1.u32_uid) AS d0_uv,
    uniqCombined(t1.u32_uid, t1.u64_feedid) AS d0_pv
FROM test.test_dataset_t1 AS t1
INNER JOIN
(
    SELECT
        u32_uid,
        u64_feedid
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND bitmapContains(bm1, u32_uid)
    GROUP BY
        u32_uid,
        u64_feedid
) AS t2 ON (t1.u32_uid = t2.u32_uid) AND (t1.u64_feedid = t2.u64_feedid)
WHERE (t1.day_ = '2022-05-24') AND (t1.u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND ((t1.u32_uid % 23) = 3) AND bitmapContains(bm2, t1.u32_uid)
GROUP BY
    t1.day_,
    t1.u8_type
9 rows in set. Elapsed: 2.561 sec. Processed 882.03 million rows, 8.74 GB (344.37 million rows/s., 3.41 GB/s.)
--936.04 MiB</pre>
</div><p>也可以让bm1和bm2做and后在t1和t2表中过滤数据。</p><div>
<pre>WITH bitmapAnd((
        SELECT groupBitmapState(u32_uid)
        FROM test.test_dataset_t1
        WHERE (day_ = '2022-05-24') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND ((u32_uid % 23) = 3)
    ), (
        SELECT groupBitmapState(u32_uid)
        FROM test.test_dataset_t1
        WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND ((u32_uid % 23) = 3)
    )) AS bm3
SELECT
    t1.day_,
    t1.u8_type,
    uniqCombined(t1.u32_uid) AS d0_uv,
    uniqCombined(t1.u32_uid, t1.u64_feedid) AS d0_pv
FROM test.test_dataset_t1 AS t1
INNER JOIN
(
    SELECT
        u32_uid,
        u64_feedid
    FROM test.test_dataset_t1
    WHERE (day_ = '2022-05-25') AND (u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND bitmapContains(bm3, u32_uid)
    GROUP BY
        u32_uid,
        u64_feedid
) AS t2 ON (t1.u32_uid = t2.u32_uid) AND (t1.u64_feedid = t2.u64_feedid)
WHERE (t1.day_ = '2022-05-24') AND (t1.u8_type IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)) AND ((t1.u32_uid % 23) = 3) AND bitmapContains(bm3, t1.u32_uid)
GROUP BY
    t1.day_,
    t1.u8_type
9 rows in set. Elapsed: 1.981 sec. Processed 641.48 million rows, 7.06 GB (323.86 million rows/s., 3.56 GB/s.)
--955.74 MiB</pre>
</div><p>改写后的分布式Join，会在右表读取时过滤左表中存在的uid,会在左表读取时过滤右表中存在的uid，这样一方面降低了右表读取和广播的数据量，又一方面降低了左表读取的量级，参与计算的量级降低，最终的查询耗时降低。</p><p>因为计算bm的过程是最早执行的，如果用户基数很高，bm计算的耗时也会较高，所以在使用中需要对比测试后上线使用，这里只是提供一个绝大部分场景有效的解决方案。</p><p>bitmap本身也存在性能问题，如果数据分布过于分散，会导致bitmap的每个桶都分布一些元素，从而需要遍历更多的桶获得元素个数才能拿到最终结果。因为如果字段类型为UInt32，使用Bitmap 32性能是可以接受的，如果这个字段的基数低但是范围跨度大（比如1000w个元素，从1到42亿随机分布，N=10000000），想要进一步加速，可以考虑column %（2<em>10000019）（10000019是大于N且最近的一个质数），这样会使原本可能存在于65535个桶的元素，填充到了306个桶中。String同样也可以这样去做，不过需要先进行一次hash（推荐murmurHash3_32(column)%(2</em>10000019)），比如测试集中的str_sessionid（篇幅有限，这里不展开）。这么做数据结果是不会改变，因为碰撞会导致过滤后的数据变多，不会变少，join会再进行一次关联和过滤，保证最后的数据是对的。</p><p>local join 也是非常高效的join方式，但是需要对join key进行预先分桶，且t1和t2 的join key遵循同一套分桶策略。这里不详细展开，需要注意的是 local join 有独特的sql语法，这里举个例子。</p><div>
<pre>select t1.day_,
       t1.u8_type,
       uniqCombined(t1.u32_uid) as d0_uv,
       uniqCombined(t1.u32_uid,t1.u64_feedid) as d0_pv
from test.test_dataset_t1 as t1 
local inner join (
    select u32_uid,
          u64_feedid
    from test.test_dataset_t1 as t
    where day_ = '2022-05-25'
    and u8_type in (1,2,3,4,5,6,7,8,9,10)
    group by u32_uid,u64_feedid
) as t2 
on t1.u32_uid=t2.u32_uid and t1.u64_feedid=t2.u64_feedid 
where t1.day_='2022-05-24' and t1.u8_type in (1,2,3,4,5,6,7,8,9,10) 
group by t1.day_,t1.u8_type
settings distributed_product_mode='local'
可以通过 EXPLAIN SYNTAX SQL 发现</pre>
</div><p>需要注意的是<strong>FROM test.test_dataset_t1 AS t 中的 AS t 不能省略</strong>，<strong>SQL结尾的 settings distributed_product_mode = 'local'  也不能省略</strong>。
可以通过 EXPLAIN SYNTAX SQL 发现，右表被自动改写为local表。</p><p><img alt="" loading="lazy" src="/logbook/images/flink/2c94e489607d9bda39de.png"/></p><h2>6. 去重场景</h2><p>我们经常会遇到一些算uv的场景，需要进行去重计算。
目前已知的慢查询（耗时超30秒）中，50%以上来自于精确计算带来的慢查询。</p><p><strong>精确去重为什么慢呢？</strong> 以测试数据集为例。我们随机将5亿的数据分发到了3个shard，每个u32_uid都可能存在于每个shard，现在我们要对u32_uid字段去重，实现过程需要以下的流程。</p><ol><li><p>接收到分布式查询的查询节点会生成每个shard的子查询</p></li><li><p>子查询对当前shard的uin进行去重。</p></li><li><p>全局去重需要把每个节点的uin集合序列化后通过网络传输到查询节点。</p></li><li><p>查询节点得到每个节点的uin集合后然后再次去重</p></li><li><p>查询节点获得全局去重结果。</p></li></ol><figure><svg height="257" id="mermaid-b3a26896af19eaaf305657a4cc72389d-1655282068111" viewBox="0 0 673.46875 257" width="673.46875" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g><g><g></g><g><g id="L-B-A"><path d="M541.8203125,128.5L545.9869791666666,128.5C550.1536458333334,128.5,558.4869791666666,128.5,566.8203125,128.5C575.1536458333334,128.5,583.4869791666666,128.5,587.6536458333334,128.5L591.8203125,128.5"></path><defs><marker id="arrowhead27" viewBox="0 0 10 10"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker></defs></g><g id="L-C1-B"><path d="M265.609375,31.5L277.7760416666667,31.5C289.9427083333333,31.5,314.2760416666667,31.5,343.88386289196734,43.75C373.49168411726805,56,408.3739932345361,80.5,425.8151477931701,92.75L443.25630235180415,105"></path><defs><marker id="arrowhead28" viewBox="0 0 10 10"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker></defs></g><g id="L-C2-B"><path d="M265.609375,128.5L277.7760416666667,128.5C289.9427083333333,128.5,314.2760416666667,128.5,338.609375,128.5C362.9427083333333,128.5,387.2760416666667,128.5,399.4427083333333,128.5L411.609375,128.5"></path><defs><marker id="arrowhead29" viewBox="0 0 10 10"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker></defs></g><g id="L-C3-B"><path d="M265.609375,225.5L277.7760416666667,225.5C289.9427083333333,225.5,314.2760416666667,225.5,343.88386289196734,213.25C373.49168411726805,201,408.3739932345361,176.5,425.8151477931701,164.25L443.25630235180415,152"></path><defs><marker id="arrowhead30" viewBox="0 0 10 10"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker></defs></g><g id="L-D1-C1"><path d="M104.4765625,31.5L111.57552083333333,31.5C118.67447916666667,31.5,132.87239583333334,31.5,146.8046875,31.5C160.73697916666666,31.5,174.40364583333334,31.5,181.23697916666666,31.5L188.0703125,31.5"></path><defs><marker id="arrowhead31" viewBox="0 0 10 10"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker></defs></g><g id="L-D2-C2"><path d="M106.0703125,128.5L112.90364583333333,128.5C119.73697916666667,128.5,133.40364583333334,128.5,147.0703125,128.5C160.73697916666666,128.5,174.40364583333334,128.5,181.23697916666666,128.5L188.0703125,128.5"></path><defs><marker id="arrowhead32" viewBox="0 0 10 10"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker></defs></g><g id="L-D3-C3"><path d="M106.0703125,225.5L112.90364583333333,225.5C119.73697916666667,225.5,133.40364583333334,225.5,147.0703125,225.5C160.73697916666666,225.5,174.40364583333334,225.5,181.23697916666666,225.5L188.0703125,225.5"></path><defs><marker id="arrowhead33" viewBox="0 0 10 10"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker></defs></g></g><g><g transform=""><g transform="translate(0,0)"><rect height="0" rx="0" ry="0" width="0"></rect><foreignobject height="0" width="0"><div xmlns="http://www.w3.org/1999/xhtml"></div></foreignobject></g></g><g transform="translate(338.609375,31.5)"><g transform="translate(-48,-13.5)"><rect height="27" rx="0" ry="0" width="96"></rect><foreignobject height="27" width="96"><div xmlns="http://www.w3.org/1999/xhtml">传输中间数据</div></foreignobject></g></g><g transform="translate(338.609375,128.5)"><g transform="translate(-48,-13.5)"><rect height="27" rx="0" ry="0" width="96"></rect><foreignobject height="27" width="96"><div xmlns="http://www.w3.org/1999/xhtml">传输中间数据</div></foreignobject></g></g><g transform="translate(338.609375,225.5)"><g transform="translate(-48,-13.5)"><rect height="27" rx="0" ry="0" width="96"></rect><foreignobject height="27" width="96"><div xmlns="http://www.w3.org/1999/xhtml">传输中间数据</div></foreignobject></g></g><g transform="translate(147.0703125,31.5)"><g transform="translate(-16,-13.5)"><rect height="27" rx="0" ry="0" width="32"></rect><foreignobject height="27" width="32"><div xmlns="http://www.w3.org/1999/xhtml">聚合</div></foreignobject></g></g><g transform="translate(147.0703125,128.5)"><g transform="translate(-16,-13.5)"><rect height="27" rx="0" ry="0" width="32"></rect><foreignobject height="27" width="32"><div xmlns="http://www.w3.org/1999/xhtml">聚合</div></foreignobject></g></g><g transform="translate(147.0703125,225.5)"><g transform="translate(-16,-13.5)"><rect height="27" rx="0" ry="0" width="32"></rect><foreignobject height="27" width="32"><div xmlns="http://www.w3.org/1999/xhtml">聚合</div></foreignobject></g></g></g><g><g id="flowchart-A-15" transform="translate(628.64453125,128.5)"><rect height="47" rx="0" ry="0" width="73.6484375" x="-36.82421875" y="-23.5"></rect><g transform="translate(0,0)"><g transform="translate(-26.82421875,-13.5)"><foreignobject height="27" width="53.6484375"><div xmlns="http://www.w3.org/1999/xhtml">UV结果</div></foreignobject></g></g></g><g id="flowchart-B-16" transform="translate(476.71484375,128.5)"><rect height="47" rx="0" ry="0" width="130.2109375" x="-65.10546875" y="-23.5"></rect><g transform="translate(0,0)"><g transform="translate(-55.10546875,-13.5)"><foreignobject height="27" width="110.2109375"><div xmlns="http://www.w3.org/1999/xhtml">各节点SET合并</div></foreignobject></g></g></g><g id="flowchart-C1-18" transform="translate(226.83984375,31.5)"><rect height="47" rx="0" ry="0" width="77.5390625" x="-38.76953125" y="-23.5"></rect><g transform="translate(0,0)"><g transform="translate(-28.76953125,-13.5)"><foreignobject height="27" width="57.5390625"><div xmlns="http://www.w3.org/1999/xhtml">uin SET</div></foreignobject></g></g></g><g id="flowchart-C2-20" transform="translate(226.83984375,128.5)"><rect height="47" rx="0" ry="0" width="77.5390625" x="-38.76953125" y="-23.5"></rect><g transform="translate(0,0)"><g transform="translate(-28.76953125,-13.5)"><foreignobject height="27" width="57.5390625"><div xmlns="http://www.w3.org/1999/xhtml">uin SET</div></foreignobject></g></g></g><g id="flowchart-C3-22" transform="translate(226.83984375,225.5)"><rect height="47" rx="0" ry="0" width="77.5390625" x="-38.76953125" y="-23.5"></rect><g transform="translate(0,0)"><g transform="translate(-28.76953125,-13.5)"><foreignobject height="27" width="57.5390625"><div xmlns="http://www.w3.org/1999/xhtml">uin SET</div></foreignobject></g></g></g><g id="flowchart-D1-24" transform="translate(57.03515625,31.5)"><rect height="47" rx="0" ry="0" width="94.8828125" x="-47.44140625" y="-23.5"></rect><g transform="translate(0,0)"><g transform="translate(-37.44140625,-13.5)"><foreignobject height="27" width="74.8828125"><div xmlns="http://www.w3.org/1999/xhtml">shard1 uin</div></foreignobject></g></g></g><g id="flowchart-D2-26" transform="translate(57.03515625,128.5)"><rect height="47" rx="0" ry="0" width="98.0703125" x="-49.03515625" y="-23.5"></rect><g transform="translate(0,0)"><g transform="translate(-39.03515625,-13.5)"><foreignobject height="27" width="78.0703125"><div xmlns="http://www.w3.org/1999/xhtml">shard2 uin</div></foreignobject></g></g></g><g id="flowchart-D3-28" transform="translate(57.03515625,225.5)"><rect height="47" rx="0" ry="0" width="98.0703125" x="-49.03515625" y="-23.5"></rect><g transform="translate(0,0)"><g transform="translate(-39.03515625,-13.5)"><foreignobject height="27" width="78.0703125"><div xmlns="http://www.w3.org/1999/xhtml">shard3 uin</div></foreignobject></g></g></g></g></g></g></svg></figure><p>所以在精确去重的场景下，查询节点需要不断的将各个节点传输过来的数据进行merge，
merge的同时对uin set进行去重，这个环节会使用大量的内存，同时查询耗时也很高。</p><p>所以提升查询效率可以从2个点出发:</p><ol><li><p>提升聚合uin set的速度</p></li><li><p>降低中间传输的数据量</p></li></ol><p>常用的方式包括：通过模糊去重替代精确去重；hash分桶，用局部去重替代全局去重，降低中间传输数据量。</p><p>clickhouse提供中了多种非精确去重的算法。
比较常用的有:</p><ul><li><p>uniq 通用模糊去重。</p></li><li><p>uniqCombined 自适应去重，先对输入参数进行了32位hash（String使用64位），低基数用array，中基数用hash table，高基数用 HeperLogLog。</p></li><li><p>uniqCombined64 与uniqCombined的区别在于对所有的输入参数都使用了64位hash。</p></li></ul><p>大数据量时：模糊计算耗时0.5秒到20秒，精度98%到99.5%，精确计算耗时10秒到超时，精度100%。耗时差距是非常明显的。
以测试数据集为例，分别对比不同字段类型，不同基数，不同去重函数的耗时内存使用和计算误差(benchmark i=10，c=1，max_threads=16)。</p><div>
<pre>select day_,uniqExact(${column}) as uv  from test.test_dataset_t1 where day_='2022-05-25' group by day_;
select day_,uniq(${column}) as uv  from test.test_dataset_t1 where day_='2022-05-25' group by day_;
select day_,uniqCombined(${column}) as uv  from test.test_dataset_t1 where day_='2022-05-25' group by day_;
select day_,uniqCombined64(${column}) as uv  from test.test_dataset_t1 where day_='2022-05-25' group by day_;</pre>
</div><p><img alt="" loading="lazy" src="/logbook/images/flink/9c2c7455f21215dad22d.png"/></p><p>结合测试数据可以看到，随着基数越高，精确去重的耗时也越高（也与节点数有关，节点数越多，精确去重耗时越长，这边不做详细数据展示）。模糊计算的耗时会随着基数增长而增长，但是增长很少。模糊去重的误差在测试集上小于0.5%(murmurHash的物化是由于Hash碰撞产生)。</p><p>如果想要精确去重，但是又要保证查询效率，应该怎么做呢？</p><p><strong>用局部去重代替全局去重。</strong></p><p>如果预先将要计算的去重key(比如uin)进行hash 分桶，这样局部去重的uin set的所有元素数据，不需要跨节点传输到查询节点，只需要把每个shard的uin-set去重后的元素个数传给查询节点，查询节点对这些元素个数进行加和处理，就可以得到全局去重的结果。篇幅有限，这里不做展开介绍。</p><p>总结来讲，能用模糊去重，就用模糊去重，如果想要追求性能的同时兼顾精度，可以考虑hash 分桶后局部去重代替全局去重。</p><h2>7. 写入即计算（物化列）</h2><p>我们经常会遇到解析一些列或者做一些逻辑转化，或者维度关联，单独起一个物化视图进行这些转化和字典调用，开销很大，维护成本也很高。
物化列是一个很友好的解决方案，物化列(MATERIALIZED COLUMN)是指只能通过逻辑表达式生成，而不能直接insert。</p><p>为什么不使用DEFAULT呢？</p><p>多数场景下，sinker都是指定字段去写，新增一个default列容易产生误解，这个列需要实时写入还是计算补全， 为了保证block可以回放，default的默认值目前是在sinker端进行补全的，这里容易产生混乱。同时一些字典调用需要在server端补全，而不是client端，所以物化列更适合。</p><p>比如我们在测试数据集上新增一个物化列，u32_hash_uin。</p><div>
<pre>alter table test.test_dataset_t1_local on cluster mmdcchsvrnewtest add column if not exists u32_hash_uid UInt32 MATERIALIZED murmurHash3_32(u32_uid) after u32_uid;
alter table test.test_dataset_t1 on cluster mmdcchsvrnewtest add column if not exists u32_hash_uid UInt32 MATERIALIZED murmurHash3_32(u32_uid) after u32_uid;</pre>
</div><p>物化列添加后，新写入的数据会按照逻辑表达式生成物化列，历史数据会在查询时进行计算，如果希望数据生成好，查询时直接查询而不是计算得到，需要手动进行MATERIALIZE（数据量大时不建议，mutation操作）。</p><div>
<pre>alter table test.test_dataset_t1 on cluster mmdcchsvrnewtest MATERIALIZE column if exists u32_hash_uid;</pre>
</div><p>也可以在MATERIALIZED 表达式中调用字典查询数据，这里不展开字典的创建，假设我们有一个u64_feedid的维表字典，字典有2个属性feed_name,feed_type，key为UInt64的u64_feedid。我们可以新增一列，将字典的维度固定到表中。</p><div>
<pre>alter table test.test_dataset_t1_local on cluster mmdcchsvrnewtest add column if not exists str_feed_name String MATERIALIZED dictGetOrDefault('test.dim_feedid','feed_name',u64_feedid,'') after u64_feedid;
alter table test.test_dataset_t1 on cluster mmdcchsvrnewtest add column if not exists str_feed_type String MATERIALIZED dictGetOrDefault('test.dim_feedid','feed_type',u64_feedid,'') after str_feed_name;</pre>
</div><p>物化列也可以实时关联字典获取一些经常变动的指标，比如feedid的热度排名(瞬时状态)。</p><p>需要注意的是，如果分布式表和本地表不处在同一个database，会<strong>出现字典加载问题</strong>，节点掉线后因为字典晚于分布式表加载，显示不存在导致分布式表无法正常被加载，节点无法正常启动。解决办法是<strong>只在本地表加物化列，在分布式表中，只加列，不加任何表达式。</strong></p><h2>8. 元数据查询</h2><p>我们经常会查询表数据量，分区数据量，物化视图的依赖关系，表字段的查询频率等元数据查询，这里将列举一些比较常用的元数据查询SQL。（接下来的mmdcchsvrnewtest需要替换成业务集群名）。</p><p><strong>借助一些元数据的查询，我们可以很容易分析表的数据量级和热点字段，可以结合查询频率对热点字段进行二级索引的添加。</strong></p><p><strong>查询表数据量。</strong></p><div>
<pre>SELECT
    database,
    table,
    sum(rows) AS r,
    formatReadableSize(sum(bytes)) AS b
FROM cluster(mmdcchsvrnewtest, system.parts)
WHERE (database = 'test') AND (table = 'test_dataset_t1_local')
GROUP BY
    database,
    table
┌─database─┬─table─────────────────┬─────────r─┬─b─────────┐
│ test     │ test_dataset_t1_local │ 561282820 │ 28.38 GiB │
└──────────┴───────────────────────┴───────────┴───────────┘
1 rows in set. Elapsed: 0.012 sec. </pre>
</div><p><strong>查询表分区数据量。</strong></p><div>
<pre>SELECT
    database,
    table,
    partition,
    sum(rows) AS r,
    formatReadableSize(sum(bytes)) AS b
FROM cluster(mmdcchsvrnewtest, system.parts)
WHERE (database = 'test') AND (table = 'test_dataset_t1_local')
GROUP BY
    database,
    table,
    partition
ORDER BY
    database ASC,
    table ASC,
    partition ASC
┌─database─┬─table─────────────────┬─partition──┬────────r─┬─b────────┐
│ test     │ test_dataset_t1_local │ 2022-05-19 │ 80183831 │ 4.05 GiB │
│ test     │ test_dataset_t1_local │ 2022-05-20 │ 80178826 │ 4.05 GiB │
│ test     │ test_dataset_t1_local │ 2022-05-21 │ 80191599 │ 4.06 GiB │
│ test     │ test_dataset_t1_local │ 2022-05-22 │ 80169932 │ 4.05 GiB │
│ test     │ test_dataset_t1_local │ 2022-05-23 │ 80193819 │ 4.06 GiB │
│ test     │ test_dataset_t1_local │ 2022-05-24 │ 80174306 │ 4.06 GiB │
│ test     │ test_dataset_t1_local │ 2022-05-25 │ 80190507 │ 4.06 GiB │
└──────────┴───────────────────────┴────────────┴──────────┴──────────┘
7 rows in set. Elapsed: 0.013 sec. </pre>
</div><p><strong>获取物化视图的依赖关系。</strong></p><div>
<pre>with t1 as (
with extract(create_table_query,'ENGINE = (.*)') as engine_full
select database as local_database
      ,arrayMap((x,y) -&gt; concat(x,'.',y),dependencies_database,dependencies_table) as mv_tables
      ,name as local_table
from system.tables
where engine&lt;&gt;'Distributed'
and mv_tables &lt;&gt; []
)
,t2 as (
with extract(create_table_query,'MATERIALIZED VIEW .* TO ([A-Za-z0-9_]*\.[A-Za-z0-9_]*)' ) as to_table
select database as local_database
      ,name as local_table
      ,concat(local_database,'.',local_table) as mv_table
      ,to_table
from system.tables
where engine='MaterializedView'
and to_table&lt;&gt;''
group by local_database
       ,local_table
       ,to_table
order by to_table
)
select t11.local_database as base_database
     ,t11.local_table as base_table
     ,t2.local_database as mv_database
     ,t2.local_table as mv_table
     ,t2.to_table as to_table
from (
select local_database,local_table,mv_table
from t1 array join mv_tables as mv_table
) as t11
left join t2 
on t11.mv_table=t2.mv_table
order by to_table</pre>
</div><p><strong>获取表中字段的查询频率排序。</strong></p><div>
<pre>SELECT
    name,
    sumIf(tup_.2, (tup_.1) = name) AS cnt
FROM system.columns
ARRAY JOIN (
        WITH
            arrayJoin(tables) AS table_,
            arrayJoin(arrayMap(x -&gt; (splitByChar('.', x)[3]), arrayFilter(x -&gt; (position(x, concat(table_, '.')) &gt; 0), columns))) AS column,
            splitByChar('.', table_)[1] AS database,
            splitByChar('.', table_)[2] AS table
        SELECT arraySort(x -&gt; (-(x.2)), arrayZip(sumMap([column], [1]).1, sumMap([column], [1]).2))
        FROM clusterAllReplicas(mmdcchsvrnewtest, system, query_log)
        WHERE (event_date &gt;= (today() - 7)) AND (is_initial_query = 1) AND (database = 'test') AND (table = 'test_dataset_t1_local')
    ) AS tup_
WHERE table = 'test_dataset_t1_local'
GROUP BY name
ORDER BY cnt DESC
┌─name──────────┬──cnt─┐
│ day_          │ 4734 │
│ str_sessionid │ 4584 │
│ u32_uid       │ 4486 │
│ minute_       │ 3912 │
│ hour_         │ 1416 │
│ u64_feedid    │  484 │
│ u8_type       │   84 │
│ u16_subtype   │   30 │
│ u32_hash_uid  │    4 │
│ shown_time    │    2 │
│ click_cnt     │    2 │
└───────────────┴──────┘
11 rows in set. Elapsed: 0.103 sec. Processed 984.29 thousand rows, 28.22 MB (9.54 million rows/s., 273.44 MB/s.)</pre>
</div><h1>五、总结</h1><p>代码优化不是一天就能完成的，正如罗马不是一天就能建成。</p><p>ClickHouse在高效查询的同时，也存在上手使用难度高的问题，是一个手动档赛车，难驯化的千里马。需要我们在不断的使用过程中，不断总结业务场景问题，提出优化思路和方案并落地，一步步的将ClickHouse用熟、用好、用精。</p><p>本文以遇到的实际场景出发，整理了常见的一些优化思路和方案，供大家借鉴，也欢迎大家一起交流学习，优化和解决业务实际问题。</p><h1>六、致谢</h1><p>感谢@chaoboxiong @sterkge @huanghuawei  对于业务场景SQL优化的支持和帮助。</p><p>感谢@welkinwen @lucasdong @luissun @terrylin 对于内核原理和优化分析的支持和帮助。</p><p>欢迎大家使用Fisher平台，体验实时接入、离线接入、自助建表（字典、离线、实时物化视图）、BI分析等功能。</p><p>文章待续 参看 WeOLAP 系列文集：
WeOLAP ：基于Clickhouse内核的云原生数仓WeOLAP(合作出品)</p><p>WeOLAP 生态：WeOLAP Sinker 百亿级接入层的设计与实现</p><p>WeOLAP 生态：WeOLAP Manager 千台规模生产集群“高可用”自动化运维挑战</p><p>WeOLAP 生态：WeOLAP QueryServer 集群过载保护机制与智能SQL分析的应用</p><p>WeOLAP 核心技术：End2End全链路精确一次写入的思考、实现与自证</p><p>WeOLAP 核心技术：存算分离技术生产环境落地挑战(合作出品)</p><p>WeOLAP 核心技术：WeOLAP！？如何做到生产环境万亿规模单表P95查询时延5s内 </p><p>WeOLAP 应用实践：ClickHouse物化视图在直播场景中的实践</p><p>WeOLAP 应用实践：Clickhouse在X实验平台场景下50倍性能优化之路</p><p>WeOLAP 应用实践：【WeOLAP】ClickHouse离线导入优化方案的探索和实践</p><p>WeOLAP 内核：Clickhouse 线程模型</p><p>WeOLAP 内核：Clickhouse 查询优化指南</p><p>WeOLAP 内核：Clickhouse 基于ZK的同步机制</p><p>WeOLAP 内核：Clickhouse 索引和二级索引</p></div> 
{% endraw %}
