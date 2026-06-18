---
title: "Elasticsearch性能、稳定性调优实践"
date: 2022-01-28 11:07:50
categories:
  - es
---

<h1 id="背景">背景</h1>

<blockquote>
<p>Elasticsearch（ES）作为NOSQL+搜索引擎的有机结合体，不仅有近实时的查询能力，还具有强大的聚合分析能力。因此在全文检索、日志分析、监控系统、数据分析等领域ES均有广泛应用。而完整的Elastic Stack体系（Elasticsearch、Logstash、Kibana、Beats），更是提供了数据采集、清洗、存储、可视化的整套解决方案。<br>
本文基于ES 5.6.4，从性能和稳定性两方面，从linux参数调优、ES节点配置和ES使用方式三个角度入手，介绍ES调优的基本方案。当然，ES的调优绝不能一概而论，需要根据实际业务场景做适当的取舍和调整，文中的疏漏之处也随时欢迎批评指正。</p>
</blockquote>

<p style=""><img src="./Elasticsearch性能、稳定性调优实践 - KM平台_files/cos-file-url(1)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h1 id="性能调优">性能调优</h1>

<h2 id="一 Linux参数调优">一 Linux参数调优</h2>

<h3 id="1- 关闭交换分区-防止内存置换降低性能- 将-etc-fstab 文件中包含swap的行注释掉">1. 关闭交换分区，防止内存置换降低性能。 将/etc/fstab 文件中包含swap的行注释掉</h3>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">sed <span class="token operator">-</span>i <span class="token string">'/swap/s/^/#/'</span> <span class="token operator">/</span>etc<span class="token operator">/</span>fstab
swapoff <span class="token operator">-</span>a
</code></pre>

<h3 id="2-   磁盘挂载选项">2.   磁盘挂载选项</h3>

<ul>
<li>noatime：禁止记录访问时间戳，提高文件系统读写性能</li>
<li>data=writeback： 不记录data journal，提高文件系统写入性能</li>
<li>barrier=0：barrier保证journal先于data刷到磁盘，上面关闭了journal，这里的barrier也就没必要开启了</li>
<li>nobh：关闭buffer_head，防止内核打断大块数据的IO操作</li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">mount <span class="token operator">-</span>o noatime<span class="token punctuation">,</span>data<span class="token operator">=</span>writeback<span class="token punctuation">,</span>barrier<span class="token operator">=</span><span class="token number">0</span><span class="token punctuation">,</span>nobh <span class="token operator">/</span>dev<span class="token operator">/</span>sda <span class="token operator">/</span>es_data
</code></pre>

<h3 id="3- 对于SSD磁盘-采用电梯调度算法-因为SSD提供了更智能的请求调度算法-不需要内核去做多余的调整 -仅供参考-">3. 对于SSD磁盘，采用电梯调度算法，因为SSD提供了更智能的请求调度算法，不需要内核去做多余的调整 (仅供参考)</h3>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">echo noop <span class="token operator">&gt;</span> <span class="token operator">/</span>sys<span class="token operator">/</span>block<span class="token operator">/</span>sda<span class="token operator">/</span>queue<span class="token operator">/</span>scheduler
</code></pre>

<h2 id="二  ES节点配置-conf-elasticsearch-yml-">二  ES节点配置（conf/elasticsearch.yml）</h2>

<h3 id="1- 适当增大写入buffer和bulk队列长度-提高写入性能和稳定性">1. 适当增大写入buffer和bulk队列长度，提高写入性能和稳定性</h3>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">indices<span class="token punctuation">.</span>memory<span class="token punctuation">.</span>index_buffer_size<span class="token punctuation">:</span> <span class="token number">15</span><span class="token operator">%</span>
thread_pool<span class="token punctuation">.</span>bulk<span class="token punctuation">.</span>queue_size<span class="token punctuation">:</span> <span class="token number">1024</span>
</code></pre>

<h3 id="2-  计算disk使用量时-不考虑正在搬迁的shard">2.  计算disk使用量时，不考虑正在搬迁的shard</h3>

<p>在规模比较大的集群中，可以防止新建shard时扫描所有shard的元数据，提升shard分配速度。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">cluster<span class="token punctuation">.</span>routing<span class="token punctuation">.</span>allocation<span class="token punctuation">.</span>disk<span class="token punctuation">.</span>include_relocations<span class="token punctuation">:</span> false
</code></pre>

<h2 id="三  ES使用方式">三  ES使用方式</h2>

<h3 id="1- 控制字段的存储选项">1. 控制字段的存储选项</h3>

<p>ES底层使用Lucene存储数据，主要包括行存（StoreFiled）、列存（DocValues）和倒排索引（InvertIndex）三部分。<br>
大多数使用场景中，没有必要同时存储这三个部分，可以通过下面的参数来做适当调整：</p>

<ul>
<li>StoreFiled： 行存，其中占比最大的是_source字段，它控制doc原始数据的存储。在写入数据时，ES把doc原始数据的整个json结构体当做一个string，存储为_source字段。查询时，可以通过_source字段拿到当初写入时的整个json结构体。<br>
所以，如果没有取出整个原始json结构体的需求，可以通过下面的命令，在mapping中关闭_source字段或者只在_source中存储部分字段，数据查询时仍可通过ES的docvalue_fields获取所有字段的值。**注意：**关闭_source后， update, update_by_query, reindex等接口将无法正常使用，所以有update等需求的index不能关闭_source。</li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token comment"># 关闭 _source</span>
PUT my_index
<span class="token punctuation">{</span>
  <span class="token string">"mappings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"my_type"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"_source"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"enabled"</span><span class="token punctuation">:</span> false
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>

<span class="token comment"># _source只存储部分字段，通过includes指定要存储的字段或者通过excludes滤除不需要的字段</span>
PUT my_index
<span class="token punctuation">{</span>
  <span class="token string">"mappings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"_doc"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"_source"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"includes"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
          <span class="token string">"*.count"</span><span class="token punctuation">,</span>
          <span class="token string">"meta.*"</span>
        <span class="token punctuation">]</span><span class="token punctuation">,</span>
        <span class="token string">"excludes"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
          <span class="token string">"meta.description"</span><span class="token punctuation">,</span>
          <span class="token string">"meta.other.*"</span>
        <span class="token punctuation">]</span>
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>

</code></pre>

<ul>
<li>doc_values：控制列存。ES主要使用列存来支持sorting, aggregations和scripts功能，对于没有上述需求的字段，可以通过下面的命令关闭doc_values，降低存储成本。</li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">PUT my_index
<span class="token punctuation">{</span>
  <span class="token string">"mappings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"my_type"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"properties"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"session_id"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
          <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"keyword"</span><span class="token punctuation">,</span>
          <span class="token string">"doc_values"</span><span class="token punctuation">:</span> false
        <span class="token punctuation">}</span>
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<ul>
<li>index：控制倒排索引。ES默认对于所有字段都开启了倒排索引，用于查询。对于没有查询需求的字段，可以通过下面的命令关闭倒排索引。</li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">PUT my_index
<span class="token punctuation">{</span>
  <span class="token string">"mappings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"my_type"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"properties"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"session_id"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
          <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"keyword"</span><span class="token punctuation">,</span>
          <span class="token string">"index"</span><span class="token punctuation">:</span> false
        <span class="token punctuation">}</span>
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<ul>
<li>_all：ES的一个特殊的字段，ES把用户写入json的所有字段值拼接成一个字符串后，做分词，然后保存倒排索引，用于支持整个json的全文检索。这种需求适用的场景较少，可以通过下面的命令将_all字段关闭，节约存储成本和cpu开销。（ES 6.0+以上的版本不再支持_all字段，不需要设置）</li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">PUT <span class="token operator">/</span>my_index
<span class="token punctuation">{</span>
  <span class="token string">"mapping"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"my_type"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"_all"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"enabled"</span><span class="token punctuation">:</span> false
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<ul>
<li>_field_names：该字段用于exists查询，来确认某个doc里面有无一个字段存在。若没有这种需求，可以将其关闭。</li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">PUT <span class="token operator">/</span>my_index
<span class="token punctuation">{</span>
  <span class="token string">"mapping"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"my_type"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"_field_names"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"enabled"</span><span class="token punctuation">:</span> false
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="2- 开启最佳压缩">2. 开启最佳压缩</h3>

<p>对于打开了上述_source字段的index，可以通过下面的命令来把lucene适用的压缩算法替换成 DEFLATE，提高数据压缩率。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">PUT <span class="token operator">/</span>my_index<span class="token operator">/</span>_settings
<span class="token punctuation">{</span>
    <span class="token string">"index.codec"</span><span class="token punctuation">:</span> <span class="token string">"best_compression"</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="3- bulk批量写入">3. bulk批量写入</h3>

<p>写入数据时尽量使用下面的bulk接口批量写入，提高写入效率。每个bulk请求的doc数量设定区间推荐为1k~1w，具体可根据业务场景选取一个适当的数量。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">POST _bulk
<span class="token punctuation">{</span> <span class="token string">"index"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"_index"</span> <span class="token punctuation">:</span> <span class="token string">"test"</span><span class="token punctuation">,</span> <span class="token string">"_type"</span> <span class="token punctuation">:</span> <span class="token string">"type1"</span> <span class="token punctuation">}</span> <span class="token punctuation">}</span>
<span class="token punctuation">{</span> <span class="token string">"field1"</span> <span class="token punctuation">:</span> <span class="token string">"value1"</span> <span class="token punctuation">}</span>
<span class="token punctuation">{</span> <span class="token string">"index"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"_index"</span> <span class="token punctuation">:</span> <span class="token string">"test"</span><span class="token punctuation">,</span> <span class="token string">"_type"</span> <span class="token punctuation">:</span> <span class="token string">"type1"</span> <span class="token punctuation">}</span> <span class="token punctuation">}</span>
<span class="token punctuation">{</span> <span class="token string">"field1"</span> <span class="token punctuation">:</span> <span class="token string">"value2"</span> <span class="token punctuation">}</span>
</code></pre>

<h3 id="4- 调整translog同步策略">4. 调整translog同步策略</h3>

<p>默认情况下，translog的持久化策略是，对于每个写入请求都做一次flush，刷新translog数据到磁盘上。这种频繁的磁盘IO操作是严重影响写入性能的，如果可以接受一定概率的数据丢失（这种硬件故障的概率很小），可以通过下面的命令调整 translog 持久化策略为异步周期性执行，并适当调整translog的刷盘周期。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">PUT my_index
<span class="token punctuation">{</span>
  <span class="token string">"settings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"index"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"translog"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"sync_interval"</span><span class="token punctuation">:</span> <span class="token string">"5s"</span><span class="token punctuation">,</span>
        <span class="token string">"durability"</span><span class="token punctuation">:</span> <span class="token string">"async"</span>
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="5- 调整refresh_interval">5. 调整refresh_interval</h3>

<p>写入Lucene的数据，并不是实时可搜索的，ES必须通过refresh的过程把内存中的数据转换成Lucene的完整segment后，才可以被搜索。默认情况下，ES每一秒会refresh一次，产生一个新的segment，这样会导致产生的segment较多，从而segment merge较为频繁，系统开销较大。如果对数据的实时可见性要求较低，可以通过下面的命令提高refresh的时间间隔，降低系统开销。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">PUT my_index
<span class="token punctuation">{</span>
  <span class="token string">"settings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"index"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"refresh_interval"</span> <span class="token punctuation">:</span> <span class="token string">"30s"</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="6- merge并发控制">6. merge并发控制</h3>

<p>ES的一个index由多个shard组成，而一个shard其实就是一个Lucene的index，它又由多个segment组成，且Lucene会不断地把一些小的segment合并成一个大的segment，这个过程被称为merge。默认值是Math.max(1, Math.min(4, Runtime.getRuntime().availableProcessors() / 2))，当节点配置的cpu核数较高时，merge占用的资源可能会偏高，影响集群的性能，可以通过下面的命令调整某个index的merge过程的并发度：</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">PUT <span class="token operator">/</span>my_index<span class="token operator">/</span>_settings
<span class="token punctuation">{</span>
    <span class="token string">"index.merge.scheduler.max_thread_count"</span><span class="token punctuation">:</span> <span class="token number">2</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="7- 写入数据不指定_id-让ES自动产生">7. 写入数据不指定_id，让ES自动产生</h3>

<p>当用户显示指定_id写入数据时，ES会先发起查询来确定index中是否已经有相同_id的doc存在，若有则先删除原有doc再写入新doc。这样每次写入时，ES都会耗费一定的资源做查询。如果用户写入数据时不指定doc，ES则通过内部算法产生一个随机的_id，并且保证_id的唯一性，这样就可以跳过前面查询_id的步骤，提高写入效率。<br>
所以，在不需要通过_id字段去重、update的使用场景中，写入不指定_id可以提升写入速率。CES技术团队的测试结果显示，无_id的数据写入性能可能比有_id的高出近一倍，实际损耗和具体测试场景相关。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token comment"># 写入时指定_id</span>
POST _bulk
<span class="token punctuation">{</span> <span class="token string">"index"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"_index"</span> <span class="token punctuation">:</span> <span class="token string">"test"</span><span class="token punctuation">,</span> <span class="token string">"_type"</span> <span class="token punctuation">:</span> <span class="token string">"type1"</span><span class="token punctuation">,</span> <span class="token string">"_id"</span> <span class="token punctuation">:</span> <span class="token string">"1"</span> <span class="token punctuation">}</span> <span class="token punctuation">}</span>
<span class="token punctuation">{</span> <span class="token string">"field1"</span> <span class="token punctuation">:</span> <span class="token string">"value1"</span> <span class="token punctuation">}</span>

<span class="token comment"># 写入时不指定_id</span>
POST _bulk
<span class="token punctuation">{</span> <span class="token string">"index"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"_index"</span> <span class="token punctuation">:</span> <span class="token string">"test"</span><span class="token punctuation">,</span> <span class="token string">"_type"</span> <span class="token punctuation">:</span> <span class="token string">"type1"</span> <span class="token punctuation">}</span> <span class="token punctuation">}</span>
<span class="token punctuation">{</span> <span class="token string">"field1"</span> <span class="token punctuation">:</span> <span class="token string">"value1"</span> <span class="token punctuation">}</span>

</code></pre>

<h3 id="8- 使用routing">8. 使用routing</h3>

<p>对于数据量较大的index，一般会配置多个shard来分摊压力。这种场景下，一个查询会同时搜索所有的shard，然后再将各个shard的结果合并后，返回给用户。对于高并发的小查询场景，每个分片通常仅抓取极少量数据，此时查询过程中的调度开销远大于实际读取数据的开销，且查询速度取决于最慢的一个分片。开启routing功能后，ES会将routing相同的数据写入到同一个分片中（也可以是多个，由index.routing_partition_size参数控制）。如果查询时指定routing，那么ES只会查询routing指向的那个分片，可显著降低调度开销，提升查询效率。<br>
routing的使用方式如下：</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token comment"># 写入</span>
PUT my_index<span class="token operator">/</span>my_type<span class="token operator">/</span><span class="token number">1</span>?routing<span class="token operator">=</span>user1
<span class="token punctuation">{</span>
  <span class="token string">"title"</span><span class="token punctuation">:</span> <span class="token string">"This is a document"</span>
<span class="token punctuation">}</span>

<span class="token comment"># 查询</span>
GET my_index<span class="token operator">/</span>_search?routing<span class="token operator">=</span>user1<span class="token punctuation">,</span>user2
<span class="token punctuation">{</span>
  <span class="token string">"query"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"match"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"title"</span><span class="token punctuation">:</span> <span class="token string">"document"</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>

</code></pre>

<h3 id="9- 为string类型的字段选取合适的存储方式">9. 为string类型的字段选取合适的存储方式</h3>

<ul>
<li>存为text类型的字段（string字段默认类型为text）： 做分词后存储倒排索引，支持全文检索，可以通过下面几个参数优化其存储方式：
<ul>
<li>norms：用于在搜索时计算该doc的_score（代表这条数据与搜索条件的相关度），如果不需要评分，可以将其关闭。</li>
<li>index_options：控制倒排索引中包括哪些信息（docs、freqs、positions、offsets）。对于不太注重_score/highlighting的使用场景，可以设为 docs来降低内存/磁盘资源消耗。</li>
<li>fields: 用于添加子字段。对于有sort和聚合查询需求的场景，可以添加一个keyword子字段以支持这两种功能。</li>
</ul>
</li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">PUT my_index
<span class="token punctuation">{</span>
  <span class="token string">"mappings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"my_type"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"properties"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"title"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
          <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"text"</span><span class="token punctuation">,</span>
          <span class="token string">"norms"</span><span class="token punctuation">:</span> false<span class="token punctuation">,</span>
          <span class="token string">"index_options"</span><span class="token punctuation">:</span> <span class="token string">"docs"</span><span class="token punctuation">,</span>
          <span class="token string">"fields"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
            <span class="token string">"raw"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
              <span class="token string">"type"</span><span class="token punctuation">:</span>  <span class="token string">"keyword"</span>
            <span class="token punctuation">}</span>
          <span class="token punctuation">}</span>
        <span class="token punctuation">}</span>
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>

</code></pre>

<ul>
<li>存为keyword类型的字段： 不做分词，不支持全文检索。text分词消耗CPU资源，冗余存储keyword子字段占用存储空间。如果没有全文索引需求，只是要通过整个字段做搜索，可以设置该字段的类型为keyword，提升写入速率，降低存储成本。<br>
设置字段类型的方法有两种：一是创建一个具体的index时，指定字段的类型；二是通过创建template，控制某一类index的字段类型。</li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token comment"># 1. 通过mapping指定 tags 字段为keyword类型</span>
PUT my_index
<span class="token punctuation">{</span>
  <span class="token string">"mappings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"my_type"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"properties"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"tags"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
          <span class="token string">"type"</span><span class="token punctuation">:</span>  <span class="token string">"keyword"</span>
        <span class="token punctuation">}</span>
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>

<span class="token comment"># 2. 通过template，指定my_index*类的index，其所有string字段默认为keyword类型</span>
PUT _template<span class="token operator">/</span>my_template
<span class="token punctuation">{</span>
    <span class="token string">"order"</span><span class="token punctuation">:</span> <span class="token number">0</span><span class="token punctuation">,</span>
    <span class="token string">"template"</span><span class="token punctuation">:</span> <span class="token string">"my_index*"</span><span class="token punctuation">,</span>
    <span class="token string">"mappings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"_default_"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"dynamic_templates"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
          <span class="token punctuation">{</span>
            <span class="token string">"strings"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
              <span class="token string">"match_mapping_type"</span><span class="token punctuation">:</span> <span class="token string">"string"</span><span class="token punctuation">,</span>
              <span class="token string">"mapping"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
                <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"keyword"</span><span class="token punctuation">,</span>
                <span class="token string">"ignore_above"</span><span class="token punctuation">:</span> <span class="token number">256</span>
              <span class="token punctuation">}</span>
            <span class="token punctuation">}</span>
          <span class="token punctuation">}</span>
        <span class="token punctuation">]</span>
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token string">"aliases"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span><span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
</code></pre>

<h3 id="10- 查询时-使用query-bool-filter组合取代普通query">10. 查询时，使用query-bool-filter组合取代普通query</h3>

<p>默认情况下，ES通过一定的算法计算返回的每条数据与查询语句的相关度，并通过_score字段来表征。但对于非全文索引的使用场景，用户并不care查询结果与查询条件的相关度，只是想精确的查找目标数据。此时，可以通过query-bool-filter组合来让ES不计算_score，并且尽可能的缓存filter的结果集，供后续包含相同filter的查询使用，提高查询效率。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token comment"># 普通查询</span>
POST my_index<span class="token operator">/</span>_search
<span class="token punctuation">{</span>
  <span class="token string">"query"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"term"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"user"</span> <span class="token punctuation">:</span> <span class="token string">"Kimchy"</span> <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>

<span class="token comment"># query-bool-filter 加速查询</span>
POST my_index<span class="token operator">/</span>_search
<span class="token punctuation">{</span>
  <span class="token string">"query"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"bool"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"filter"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"term"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"user"</span><span class="token punctuation">:</span> <span class="token string">"Kimchy"</span> <span class="token punctuation">}</span>
      <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="11- index按日期滚动-便于管理">11. index按日期滚动，便于管理</h3>

<p>写入ES的数据最好通过某种方式做分割，存入不同的index。常见的做法是将数据按模块/功能分类，写入不同的index，然后按照时间去滚动生成index。这样做的好处是各种数据分开管理不会混淆，也易于提高查询效率。同时index按时间滚动，数据过期时删除整个index，要比一条条删除数据或delete_by_query效率高很多，因为删除整个index是直接删除底层文件，而delete_by_query是查询-标记-删除。<br>
举例说明，假如有[module_a,moduleb]两个模块产生的数据，那么index规划可以是这样的：一类index名称是module_a + {日期}，另一类index名称是module_b+ {日期}。对于名字中的日期，可以在写入数据时自己指定精确的日期，也可以通过ES的ingest pipeline中的<a href="https://www.elastic.co/guide/en/elasticsearch/reference/5.6/date-index-name-processor.html" target="_blank">index-name-processor</a>实现（会有写入性能损耗）。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token comment"># module_a 类index</span>
<span class="token operator">-</span> 创建index：
PUT module_a@2018_01_01
<span class="token punctuation">{</span>
    <span class="token string">"settings"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"index"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span>
            <span class="token string">"number_of_shards"</span> <span class="token punctuation">:</span> <span class="token number">3</span><span class="token punctuation">,</span>
            <span class="token string">"number_of_replicas"</span> <span class="token punctuation">:</span> <span class="token number">2</span>
        <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
PUT module_a@2018_01_02
<span class="token punctuation">{</span>
    <span class="token string">"settings"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"index"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span>
            <span class="token string">"number_of_shards"</span> <span class="token punctuation">:</span> <span class="token number">3</span><span class="token punctuation">,</span>
            <span class="token string">"number_of_replicas"</span> <span class="token punctuation">:</span> <span class="token number">2</span>
        <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
<span class="token punctuation">.</span><span class="token punctuation">.</span><span class="token punctuation">.</span>

<span class="token operator">-</span> 查询数据：
GET module_a@<span class="token operator">*</span><span class="token operator">/</span>_search

<span class="token comment">#  module_b 类index</span>

<span class="token operator">-</span> 创建index：
PUT module_b@2018_01_01
<span class="token punctuation">{</span>
    <span class="token string">"settings"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"index"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span>
            <span class="token string">"number_of_shards"</span> <span class="token punctuation">:</span> <span class="token number">3</span><span class="token punctuation">,</span>
            <span class="token string">"number_of_replicas"</span> <span class="token punctuation">:</span> <span class="token number">2</span>
        <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
PUT module_b@2018_01_02
<span class="token punctuation">{</span>
    <span class="token string">"settings"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"index"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span>
            <span class="token string">"number_of_shards"</span> <span class="token punctuation">:</span> <span class="token number">3</span><span class="token punctuation">,</span>
            <span class="token string">"number_of_replicas"</span> <span class="token punctuation">:</span> <span class="token number">2</span>
        <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
<span class="token punctuation">.</span><span class="token punctuation">.</span><span class="token punctuation">.</span>

<span class="token operator">-</span> 查询数据：
GET module_b@<span class="token operator">*</span><span class="token operator">/</span>_search

</code></pre>

<h3 id="12- 按需控制index的分片数和副本数">12. 按需控制index的分片数和副本数</h3>

<p>分片（shard）：一个ES的index由多个shard组成，每个shard承载index的一部分数据。<br>
副本（replica）：index也可以设定副本数（number_of_replicas），也就是同一个shard有多少个备份。对于查询压力较大的index，可以考虑提高副本数（number_of_replicas），通过多个副本均摊查询压力</p>

<p>shard数量（number_of_shards）设置过多或过低都会引发一些问题：shard数量过多，则批量写入/查询请求被分割为过多的子写入/查询，导致该index的写入、查询拒绝率上升；对于数据量较大的inex，当其shard数量过小时，无法充分利用节点资源，造成机器资源利用率不高 或 不均衡，影响写入/查询的效率。<br>
对于每个index的shard数量，可以根据数据总量、写入压力、节点数量等综合考量后设定，然后根据数据增长状态定期检测下shard数量是否合理。CES技术团队的推荐方案是：</p>

<ul>
<li>对于数据量较小（100GB以下）的index，往往写入压力查询压力相对较低，一般设置3~5个shard，number_of_replicas设置为1即可（也就是一主一从，共两副本） 。</li>
<li>对于数据量较大（100GB以上）的index：
<ul>
<li>一般把单个shard的数据量控制在（20GB~50GB）</li>
<li>让index压力分摊至多个节点：可通过index.routing.allocation.total_shards_per_node参数，强制限定一个节点上该index的shard数量，让shard尽量分配到不同节点上</li>
<li>综合考虑整个index的shard数量，如果shard数量（不包括副本）超过50个，就很可能引发拒绝率上升的问题，此时可考虑把该index拆分为多个独立的index，分摊数据量，同时配合routing使用，降低每个查询需要访问的shard数量。</li>
</ul>
</li>
</ul>

<h1 id="稳定性调优">稳定性调优</h1>

<h2 id="一  Linux参数调优">一  Linux参数调优</h2>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token comment"># 修改系统资源限制</span>
<span class="token comment"># 单用户可以打开的最大文件数量，可以设置为官方推荐的65536或更大些</span>
echo <span class="token string">"* - nofile 655360"</span> <span class="token operator">&gt;&gt;</span><span class="token operator">/</span>etc<span class="token operator">/</span>security<span class="token operator">/</span>limits<span class="token punctuation">.</span>conf
<span class="token comment"># 单用户内存地址空间</span>
echo <span class="token string">"* - as unlimited"</span> <span class="token operator">&gt;&gt;</span><span class="token operator">/</span>etc<span class="token operator">/</span>security<span class="token operator">/</span>limits<span class="token punctuation">.</span>conf
<span class="token comment"># 单用户线程数</span>
echo <span class="token string">"* - nproc 2056474"</span> <span class="token operator">&gt;&gt;</span><span class="token operator">/</span>etc<span class="token operator">/</span>security<span class="token operator">/</span>limits<span class="token punctuation">.</span>conf
<span class="token comment"># 单用户文件大小</span>
echo <span class="token string">"* - fsize unlimited"</span> <span class="token operator">&gt;&gt;</span><span class="token operator">/</span>etc<span class="token operator">/</span>security<span class="token operator">/</span>limits<span class="token punctuation">.</span>conf
<span class="token comment"># 单用户锁定内存</span>
echo <span class="token string">"* - memlock unlimited"</span> <span class="token operator">&gt;&gt;</span><span class="token operator">/</span>etc<span class="token operator">/</span>security<span class="token operator">/</span>limits<span class="token punctuation">.</span>conf

<span class="token comment"># 单进程可以使用的最大map内存区域数量</span>
echo <span class="token string">"vm.max_map_count = 655300"</span> <span class="token operator">&gt;&gt;</span><span class="token operator">/</span>etc<span class="token operator">/</span>sysctl<span class="token punctuation">.</span>conf

<span class="token comment"># TCP全连接队列参数设置， 这样设置的目的是防止节点数较多（比如超过100）的ES集群中，节点异常重启时全连接队列在启动瞬间打满，造成节点hang住，整个集群响应迟滞的情况</span>
echo <span class="token string">"net.ipv4.tcp_abort_on_overflow = 1"</span> <span class="token operator">&gt;&gt;</span><span class="token operator">/</span>etc<span class="token operator">/</span>sysctl<span class="token punctuation">.</span>conf
echo <span class="token string">"net.core.somaxconn = 2048"</span> <span class="token operator">&gt;&gt;</span><span class="token operator">/</span>etc<span class="token operator">/</span>sysctl<span class="token punctuation">.</span>conf

<span class="token comment"># 降低tcp alive time，防止无效链接占用链接数</span>
echo <span class="token number">300</span> <span class="token operator">&gt;</span><span class="token operator">/</span>proc<span class="token operator">/</span>sys<span class="token operator">/</span>net<span class="token operator">/</span>ipv4<span class="token operator">/</span>tcp_keepalive_time

</code></pre>

<h2 id="二  ES节点配置">二  ES节点配置</h2>

<h3 id="1- jvm-options">1. jvm.options</h3>

<p>-Xms和-Xmx设置为相同的值，推荐设置为机器内存的一半左右，剩余一半留给系统cache使用。</p>

<ul>
<li>jvm内存建议不要低于2G，否则有可能因为内存不足导致ES无法正常启动或OOM</li>
<li>jvm建议不要超过32G，否则jvm会禁用内存对象指针压缩技术，造成内存浪费</li>
</ul>

<h3 id="2- elasticsearch-yml">2. elasticsearch.yml</h3>

<ul>
<li>
<p>设置内存熔断参数，防止写入或查询压力过高导致OOM，具体数值可根据使用场景调整。<br>
indices.breaker.total.limit: 30%<br>
indices.breaker.request.limit: 6%<br>
indices.breaker.fielddata.limit: 3%</p>
</li>
<li>
<p>调小查询使用的cache，避免cache占用过多的jvm内存，具体数值可根据使用场景调整。<br>
indices.queries.cache.count: 500<br>
indices.queries.cache.size: 5%</p>
</li>
<li>
<p>单机多节点时，主从shard分配以ip为依据，分配到不同的机器上，避免单机挂掉导致数据丢失。<br>
cluster.routing.allocation.awareness.attributes: ip<br>
node.attr.ip: 1.1.1.1</p>
</li>
</ul>

<h2 id="三 ES使用方式">三 ES使用方式</h2>

<h3 id="1- 节点数较多的集群-增加专有master-提升集群稳定性">1. 节点数较多的集群，增加专有master，提升集群稳定性</h3>

<p>ES集群的元信息管理、index的增删操作、节点的加入剔除等集群管理的任务都是由master节点来负责的，master节点定期将最新的集群状态广播至各个节点。所以，master的稳定性对于集群整体的稳定性是至关重要的。当集群的节点数量较大时（比如超过30个节点），集群的管理工作会变得复杂很多。此时应该创建专有master节点，这些节点只负责集群管理，不存储数据，不承担数据读写压力；其他节点则仅负责数据读写，不负责集群管理的工作。这样把集群管理和数据的写入/查询分离，互不影响，防止因读写压力过大造成集群整体不稳定。<br>
将专有master节点和数据节点的分离，需要修改ES的配置文件，然后滚动重启各个节点。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token comment"># 专有master节点的配置文件（conf/elasticsearch.yml）增加如下属性：</span>
node<span class="token punctuation">.</span>master<span class="token punctuation">:</span> true
node<span class="token punctuation">.</span>data<span class="token punctuation">:</span> false
node<span class="token punctuation">.</span>ingest<span class="token punctuation">:</span> false

<span class="token comment"># 数据节点的配置文件增加如下属性（与上面的属性相反）：</span>
node<span class="token punctuation">.</span>master<span class="token punctuation">:</span> false
node<span class="token punctuation">.</span>data<span class="token punctuation">:</span> true
node<span class="token punctuation">.</span>ingest<span class="token punctuation">:</span> true

</code></pre>

<h3 id="2- 控制index-shard总数量">2. 控制index、shard总数量</h3>

<p>上面提到，ES的元信息由master节点管理，定期同步给各个节点，也就是每个节点都会存储一份。这个元信息主要存储在cluster_state中，如所有node元信息（indices、节点各种统计参数）、所有index/shard的元信息（mapping, location, size）、元数据ingest等。<br>
ES在创建新分片时，要根据现有的分片分布情况指定分片分配策略，从而使各个节点上的分片数基本一致，此过程中就需要深入遍历cluster_state。当集群中的index/shard过多时，cluster_state结构会变得过于复杂，导致遍历cluster_state效率低下，集群响应迟滞。CES技术团队曾经在一个20个节点的集群里，创建了4w+个shard，导致新建一个index需要60s+才能完成。<br>
当index/shard数量过多时，可以考虑从以下几方面改进：</p>

<ul>
<li>降低数据量较小的index的shard数量</li>
<li>把一些有关联的index合并成一个index</li>
<li>数据按某个维度做拆分，写入多个集群</li>
</ul>

<h3 id="3- Segment Memory优化">3. Segment Memory优化</h3>

<p>前面提到，ES底层采用Lucene做存储，而Lucene的一个index又由若干segment组成，每个segment都会建立自己的倒排索引用于数据查询。Lucene为了加速查询，为每个segment的倒排做了一层前缀索引，这个索引在Lucene4.0以后采用的数据结构是FST (Finite State Transducer)。Lucene加载segment的时候将其全量装载到内存中，加快查询速度。这部分内存被称为SegmentMemory，<code>常驻内存，占用heap，无法被GC</code>。<br>
前面提到，为利用JVM的对象指针压缩技术来节约内存，通常建议JVM内存分配不要超过32G。当集群的数据量过大时，SegmentMemory会吃掉大量的堆内存，而JVM内存空间又有限，此时就需要想办法降低SegmentMemory的使用量了，常用方法有下面几个：</p>

<ul>
<li>定期删除不使用的index</li>
<li>对于不常访问的index，可以通过close接口将其关闭，用到时再打开</li>
<li>通过force_merge接口强制合并segment，降低segment数量</li>
</ul>

<p>CES技术团队在此基础上，对FST部分进行了优化，释放高达40%的Segment Memory内存空间。</p>

<p>最后打个广告，内部使用请联系galenmingli(李明)同学~</p>
