---
title: "Elasticsearch 工作笔记"
date: 2022-06-16 21:59:36
categories:
  - es
---

<div data-inline-code-theme="red" data-code-block-theme="default"><h1 data-lines="1" data-sign="0f2c04cd3bafc61b5a70b8a4dbf8a9f1" id="elasticsearch-%E5%B7%A5%E4%BD%9C%E7%AC%94%E8%AE%B0"><a href="https://km.woa.com/group/34177/articles/show/505564?kmref=search&amp;from_page=1&amp;no=7#elasticsearch-%E5%B7%A5%E4%BD%9C%E7%AC%94%E8%AE%B0" class="anchor"></a>Elasticsearch 工作笔记</h1><p data-lines="2" data-type="p" data-sign="fe731da6d2efab76dd8c5d011320d7c3">从事Elasticsearch云产品的研发已经四年多了，在服务公有云客户的过程中也遇到了各种各样的使用方式以及问题，本文就把过去几年记录的一些问题和解决办法进行归类和总结，常读常新。</p><p data-lines="2" data-type="p" data-sign="cfeff30d2c2710419322f21c2bfd856c">目录：</p><ul class="cherry-list__square" data-lines="7" data-sign="12ca40ba36b72df6e0a9e530a3b931belist7"><li>一、es内核bug类的问题记录<br></li><li>二、使用方式类的问题记录<br></li><li>三、优化类的问题记录<br></li><li>四、原理咨询类的问题记录</li></ul><h2 data-lines="2" data-sign="b4d7b2f9fcb6dc42537193b661b70492" id="%E4%B8%80%E3%80%81es%E5%86%85%E6%A0%B8bug%E7%B1%BB%E7%9A%84%E9%97%AE%E9%A2%98%E8%AE%B0%E5%BD%95"><a href="https://km.woa.com/group/34177/articles/show/505564?kmref=search&amp;from_page=1&amp;no=7#%E4%B8%80%E3%80%81es%E5%86%85%E6%A0%B8bug%E7%B1%BB%E7%9A%84%E9%97%AE%E9%A2%98%E8%AE%B0%E5%BD%95" class="anchor"></a>一、es内核bug类的问题记录</h2><ol start="1" class="cherry-list__default" data-lines="68" data-sign="d3f27ae22ca4a9e3a62dda4a45743fc7list68"><li>集群升级到7.5版本后自定义的normalizer无法使用了<br><br>es内核的bug，7.0版本对自定义analyzer这部分的代码进行了重构，导致所有的自定义normalizer都无法正常使用。<br><br>相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/48650">https://github.com/elastic/elasticsearch/issues/48650</a><br><br>相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/48866">https://github.com/elastic/elasticsearch/pull/48866</a><br></li><li>使用_search/template API查询时返回结果总量不准<br><br>在_search/template API的处理逻辑中，虽然rest_total_hits_as_int设置为了true, trackTotalHitsUpTo值却没有被设置，因此只能获取到最多为10000的total hits。<br><br>相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/52801">https://github.com/elastic/elasticsearch/issues/52801</a><br><br>相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/53155">https://github.com/elastic/elasticsearch/pull/53155</a><br></li><li>处理字符串类型数据的ingest processor, 不支持传入的field字段值为数组<br><br>对Lowercase Processors、Uppercase Processors、Trim Processors等处理字符串类型数据的ingest processor, 都支持要处理的字段类型为数组类型：<br><br>相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/51087">https://github.com/elastic/elasticsearch/issues/51087</a><br><br>相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/53343">https://github.com/elastic/elasticsearch/pull/53343</a><br></li><li>reindex api在max_docs参数小于slices时，会报错max_docs为0<br><br>调用reindex api,当max_docs参数&lt;slices时，会报错max_docs为0，实际上是因为没有提前校验max_docs是否&lt;slices，导致max_docs被设置为0。<br><br>相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/52786">https://github.com/elastic/elasticsearch/issues/52786</a><br><br>相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/54901">https://github.com/elastic/elasticsearch/pull/54901</a><br></li><li>ingest pipeline simulate API 在传入的docs参数是空列表时，没有响应<br><br>在调用_ingest/pipeline/_simulate API时，如果传入的docs参数是空列表，则什么结果都不会返回。<br>Bug产生的原因是，在异步请求的ActionListener中没有对docs参数进行判空，导致始终没有响应给客户端。<br><br>相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/52833">https://github.com/elastic/elasticsearch/issues/52833</a><br><br>相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/52937">https://github.com/elastic/elasticsearch/pull/52937</a><br></li><li>Rename inegst processor对于设置ignore_missing参数无效<br><br>当使用template snippets时，如果取到的字段不存在，此时如果设置了ignore_missing， 仍然会报错。<br><br>相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/74241">https://github.com/elastic/elasticsearch/issues/74241</a><br><br>相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/74248">https://github.com/elastic/elasticsearch/pull/74248</a><br></li><li>ILM中的Shrink Action，如果设置的目标分片数不合适，也就是不是原索引分片数的因子时，Shrink Action会卡住<br><br>在Shrink Action中增加校验，如果设置的目标分片数不合适，就提前中断ILM的执行。<br><br>相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/72724">https://github.com/elastic/elasticsearch/issues/72724</a><br><br>相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/74219">https://github.com/elastic/elasticsearch/pull/74219</a><br></li><li>Get Snapshot API如果指定了ignore_unavailable为true时，会把当前正在执行的所有快照都返回<br><br>相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/68090">https://github.com/elastic/elasticsearch/issues/68090</a><br><br>相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/68091">https://github.com/elastic/elasticsearch/pull/68091</a><br></li><li>在ILM中使用的AllocationDeciders，会忽略掉用户自定义的cluster level的routing allocation 配置，导致在某些场景下需要移动分片时把分片移动了到了错误的节点上。<br><br>相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/64529">https://github.com/elastic/elasticsearch/issues/64529</a><br><br>相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/65037">https://github.com/elastic/elasticsearch/pull/65037</a></li></ol><p data-lines="1" data-type="p" data-sign="6c5d00d55498c26e8198de586586d8bb">10 . 在执行bulk写入时，如果body里指定了pipeline, 执行结果是错误的</p><p data-lines="6" data-type="p" data-sign="1c8bf950db8d69ea5d1308aaacadd284">	 在bulk写入时，如果有的请求带有ingest pipeline, 有的没有，那么执行结果就是完全乱序的，也就是文档内容和指定的docId对应不上。

	 相关issue: <a rel="nofollow" href="https://github.com/elastic/elasticsearch/issues/60437">https://github.com/elastic/elasticsearch/issues/60437</a>

	 相关PR：<a rel="nofollow" href="https://github.com/elastic/elasticsearch/pull/60818">https://github.com/elastic/elasticsearch/pull/60818</a></p><h2 data-lines="2" data-sign="876f56bb78c5e5b258eb1db7512984a3" id="%E4%BA%8C%E3%80%81%E4%BD%BF%E7%94%A8%E6%96%B9%E5%BC%8F%E7%B1%BB%E7%9A%84%E9%97%AE%E9%A2%98%E8%AE%B0%E5%BD%95"><a href="https://km.woa.com/group/34177/articles/show/505564?kmref=search&amp;from_page=1&amp;no=7#%E4%BA%8C%E3%80%81%E4%BD%BF%E7%94%A8%E6%96%B9%E5%BC%8F%E7%B1%BB%E7%9A%84%E9%97%AE%E9%A2%98%E8%AE%B0%E5%BD%95" class="anchor"></a>二、使用方式类的问题记录</h2><p data-lines="2" data-type="p" data-sign="8dd7a4def4660f79856b5c1864ab8070">11 . 二进制字段如何设置mapping?</p><div data-sign="1669a8bd08e6b714fc8d25646749919a" data-type="codeBlock" data-lines="10">
      <pre><code>	"mapping": {
	  "type": "binary",
	  "doc_values": "false",
	  "norms": "false",
	  "fielddata": "false",
	  "store": "false"
	}</code></pre>

<p data-lines="2" data-type="p" data-sign="00d6af319fe028489db93eb9b287018f">12 . 对ip字段进行聚合，希望聚合结果返回每个ip的一条数据，该怎么实现？</p><span data-lines="2" data-type="br" data-sign="br2"></span><p data-lines="1" data-type="p" data-sign="9a9b6614035f3ea7d0c6ef6c0e0517ea">	先使用terms聚合，再使用top_hits子聚合能达到目的，使用&nbsp;collapse 配合 inner_hits也可以实现</p><span data-lines="2" data-type="br" data-sign="br2"></span><p data-lines="1" data-type="p" data-sign="82ff7749b73d2a9d2f174a4f0d787699">13 . 有一张消费明细表(一个人有多条消费记录)，首先想计算出一个人的总消费金额，然后想得到总消费大于500美金的所有人数，query DSL该怎么写？</p><div data-sign="17d4b22271596ca1fb481da2b60377f8" data-type="codeBlock" data-lines="32">
      <pre><code>	{
    "aggs":{
        "one":{
            "terms":{
                "field":"mobile_nbr"
            },
            "aggs":{
                "x":{
                    "sum":{
                        "field":"trans_amt"
                    }
                },
                "sum_bucket_filter":{
                    "bucket_selector":{
                        "buckets_path":{
                            "totalSum":"x"
                        },
                        "script":"params.totalSum &gt; 500"
                    }
                }
            }
        },
        "stats_buckets":{
            "stats_bucket":{
                "buckets_path":"one.x"
            }
        }
    }
}</code></pre>

<p data-lines="2" data-type="p" data-sign="484da3f172920df673e971c62a75f15f">
14 . 使用Logstash迁移ES的数据，简单的配置文件</p><div data-sign="1e9e0daaab8042873d4f797591937d78" data-type="codeBlock" data-lines="16">
      <pre><code>	input {
	    elasticsearch {
	        hosts =&gt; ["http://x.x.x.x:9200"]
	        index =&gt; "*"
	        docinfo =&gt; true
	    }
	}
	output {
	    elasticsearch {
	        hosts =&gt; ["http://x.x.x.x:9200"]
	        index =&gt; "%{[@metadata][_index]}"
	    }
	}</code></pre>

<p data-lines="1" data-type="p" data-sign="fea29f31b69751d53943d6abe88bbe56">15 . 一个有用的脚本,用于追加netsted objects</p><div data-sign="5e41890899886ddeee50a80f25a82a74" data-type="codeBlock" data-lines="16">
      <pre><code>	{
	  "script": {
	    "lang": "painless",
	    "inline": " if (ctx._source.redu!=null) {ctx._source.redu.add(params.object);} else {Object[] temp= new Object[]{params.object};ctx._source.redu= temp;}",
	    "params": {
	      "object": {
	        "visit_time": "2020-03-15 22:00:00",
	        "visit_cnt": 1000,
	        "visit_scene": 2
	      }
	    }
	  }
	}</code></pre>

<p data-lines="1" data-type="p" data-sign="1d464bbcf875bcda790fb78484acea8b">16 . mustache小胡子脚本,用于把一个数组类型的字段复制到另外一个字段，高版本7.x可以使用set processor的copy_from， 低版本不支持copy_from</p><div data-sign="59ce2446a2152e94d396b705318ef673" data-type="codeBlock" data-lines="37">
      <pre><code>	{
  "pipeline": {
    "processors": [
      {
        "set": {
          "field": "a",
          "value": "{{#b}}{{.}},{{/b}}"
        }
      },
      {
        "split": {
          "field": "a",
          "separator": ","
        }
      },
      {
        "convert": {
          "field": "a",
          "type": "integer"
        }
      }
    ]
  },
  "docs": [
    {
      "_source": {
        "b": [
          1,
          2
        ]
      }
    }
  ]
}</code></pre>

<p data-lines="2" data-type="p" data-sign="5c7a53606bb5b48d1da4438eb8268982">17 . 查询时对结果进行排序，如果文档的分值相同，需要返回顺序是随机的，可以通过script来进行处理</p><div data-sign="26feef242eb5652186859bcd9a7ef1ea" data-type="codeBlock" data-lines="10">
      <pre><code>	{
      "_script": {
        "script": "Math.random()",
        "type": "number",
        "order": "asc"
      }
    }</code></pre>

<p data-lines="1" data-type="p" data-sign="bbebcd8c837ebe19db91384a9b7736aa">18 . 取消reindex任务</p><div data-sign="c5ef1386df5ab8ebc632e209e3abe19b" data-type="codeBlock" data-lines="10">
      <pre><code>	列出运行中的任务
	_tasks
	_tasks?nodes=nodeId1,nodeId2
	取消任务
	_tasks/node_id:task_id/_cancel
	取消重建索引任务
	_tasks/_cancel?nodes=nodeId1,nodeId2&amp;action=*reindex</code></pre>

<p data-lines="2" data-type="p" data-sign="32f920064387fe3b6bdfe8a1a970a2db">
19 . 查看阻塞在队列中的索引</p><div data-sign="8e2a03257a1bb7b1b12d230c08fc479e" data-type="codeBlock" data-lines="4">
      <pre><code>	GET  _tasks?pretty\&amp;detailed  | grep description | awk -F 'index' '{print $2}' | sort | uniq -c | sort -n</code></pre>

<p data-lines="1" data-type="p" data-sign="f4b96011bc5445df6220d4ad0f6871c4">20 . cancel掉所有存量的查询，释放内存</p><div data-sign="0238abf372767b5965c694be79e9fdfb" data-type="codeBlock" data-lines="4">
      <pre><code>	POST _tasks/_cancel?actions='indices:data/read/search*'</code></pre>

<h2 data-lines="1" data-sign="2596997e22daea7f7e8751a651386a6a" id="%E4%B8%89%E3%80%81%E4%BC%98%E5%8C%96%E7%B1%BB%E7%9A%84%E9%97%AE%E9%A2%98%E8%AE%B0%E5%BD%95"><a href="https://km.woa.com/group/34177/articles/show/505564?kmref=search&amp;from_page=1&amp;no=7#%E4%B8%89%E3%80%81%E4%BC%98%E5%8C%96%E7%B1%BB%E7%9A%84%E9%97%AE%E9%A2%98%E8%AE%B0%E5%BD%95" class="anchor"></a>三、优化类的问题记录</h2><p data-lines="2" data-type="p" data-sign="754b0dc48067fe1bb0f00fe904206256">21 . 在需要批量拉取聚合结果时，可以使用index sorting + composite 聚合来代替term 聚合，composite聚合可以根据排序优化聚合提前结束并且支持分页。</p><p data-lines="2" data-type="p" data-sign="a5c6b7b9bdfbd8882e8532156350b54c">22 . 系统高阶内存不足导致的节点离线</p><p data-lines="8" data-type="p" data-sign="82287b9d2a97448f50679ee0f3d70fb6" style="">	
	线上某个写入量比较大的集群，不定时的会出现某个节点离线又加回集群的情况。经过定位发现是虚拟机高阶内存不足，导致网卡收发包异常。

	es和Lucene 会大量使用堆外内存，在应用层面的内存分配都是申请的低阶内存（0阶、1阶），会将高阶内存（3阶及以上）逐步拆分用掉。而系统内核层面的网卡驱动会优先分配高阶内存，如果高阶内存不足会再尝试分配低阶内存，这个过程会有一定延时，可能导致节点短暂收发包异常，短暂脱离集群。当应用层面将高阶内存拆分申请完毕后，就会出现这一高阶内存不足的现象。系统会有内存整理的过程但是不会那么及时。

	解决办法是通过设定系统参数预留系统内存：

	</p><div data-sign="ff3ae9d9836c83e889dfef1c245eeeac" data-type="codeBlock" data-lines="5">
      <pre><code>	echo %2的系统总内存（单位kb） &gt; /proc/sys/vm/min_free_kbytes

	echo 1 &gt; /proc/sys/vm/compact_memory</code></pre>

<p data-lines="1" data-type="p" data-sign="6b0a19c3989965a5ef9e3ccccff6ab4a">23 . es节点上TCP全连接队列参数设置，防止节点数大于100的这种的集群中，节点异常重启时全连接队列在启动瞬间打满，造成节点hung住，导致集群响应迟滞：</p><div data-sign="2eff3756a60a01aa667c9bfea081cd4f" data-type="codeBlock" data-lines="5">
      <pre><code>	echo "net.ipv4.tcp_abort_on_overflow = 1" &gt;&gt;/etc/sysctl.conf
	echo "net.core.somaxconn = 2048" &gt;&gt;/etc/sysctl.conf</code></pre>

<p data-lines="1" data-type="p" data-sign="89eb48d58a0ea9150bd346b7f4e93387">24 . 查询时需要返回文档原文中的几个字段，从行存改为从列存读取，高压力查询场景性能可以提升 50%。从行存读取涉及到解压的开销，列存则可直接取对应字段的部分block，性能会更高：</p><p data-lines="3" data-type="p" data-sign="216d7eb1d30bdd35c7958de146ecdc37">	查询body 中的取source 部分：

	</p><div data-sign="36e2a1fa61b2ca3e24cb616dd8ebad00" data-type="codeBlock" data-lines="9">
      <pre><code>	"_source": {
	    "includes": [
	      "a",
	      "b",
	      "c"
	    ]
	  }	</code></pre>

<p data-lines="4" data-type="p" data-sign="4dd08372ead8ee017a27eb32e506dff0">
	调整为从列存读取字段：

	</p><div data-sign="09d2daf3997049c515f596dc236b07af" data-type="codeBlock" data-lines="8">
      <pre><code>	  "docvalue_fields":  [
	      "a",
	      "b",
	      "c"
	    ],
	  "stored_fields": "_none_", // 关闭行存读取</code></pre>

<p data-lines="5" data-type="p" data-sign="568eeba1a116cb90d18e431871871614">25 . 部署es时磁盘挂载时的可选配置
	* noatime：禁止记录访问时间戳，提高文件系统读写性能
	* data=writeback： 不记录data journal，提高文件系统写入性能
	* barrier=0：barrier保证journal先于data刷到磁盘，上面关闭了journal，这里的barrier也就没必要开启了
	* nobh：关闭buffer_head，防止内核打断大块数据的IO操作</p><h2 data-lines="2" data-sign="55ffcb53d50f7010a4b9c06ccd0d4a69" id="%E5%9B%9B%E3%80%81%E5%8E%9F%E7%90%86%E5%92%A8%E8%AF%A2%E7%B1%BB%E7%9A%84%E9%97%AE%E9%A2%98%E8%AE%B0%E5%BD%95"><a href="https://km.woa.com/group/34177/articles/show/505564?kmref=search&amp;from_page=1&amp;no=7#%E5%9B%9B%E3%80%81%E5%8E%9F%E7%90%86%E5%92%A8%E8%AF%A2%E7%B1%BB%E7%9A%84%E9%97%AE%E9%A2%98%E8%AE%B0%E5%BD%95" class="anchor"></a>四、原理咨询类的问题记录</h2><p data-lines="2" data-type="p" data-sign="655bbde270ccb85803f158c56c1c0a77">26 . 为了满足查询时延，是不是索引的分片数设置的越少越好？</p><p data-lines="2" data-type="p" data-sign="7bbd26332b504583e45c01a69ed4a509">如果单次搜索的时延可以满足业务上的要求，可以设置索引为1分片多副本。 如果时延过高，可以增加shard数量，代价是每次搜索的并发两增大，带来的额外开销更大，因而集群能支撑的峰值QPS可能会降低。 原则上，在满足搜索时延的前提下，划分尽量少的分片数。 </p><p data-lines="2" data-type="p" data-sign="a95d00f145736767b37d13aa7c8c3fbc">另外有一种场景划分更多的分片数是合理的，那就是集群大多数搜索都会用到某个字段做过滤，比如城市id。 这个时候，可以用该字段做为routing_key，将相关联的数据route到某个或某几个(如果用到routing partition)shard。 适当多划分一些分片，可以让单个分片上的数据集较小，搜素速度快，同时因为搜索不会hit所有的分片，规避了划分过多的分片带来的并发过高，以及需要汇总的数据过多引起的性能问题。</p><p data-lines="3" data-type="p" data-sign="08e544723ba65bc8621c2b4600c6c605">27 . filter缓存的策略是怎么样的？
es会基于使用频次自动缓存查询。如果一个非评分查询在最近的 256 次查询中被使用过（次数取决于查询类型），那么这个查询就会作为缓存的候选。但是，并不是所有的segment都能保证缓存 bitset 。只有那些文档数量超过 10000 （或超过总文档数量的 3% )的segment才会缓存 bitset 。因为小的片段可以很快的进行搜索和合并。一旦缓存了，非评分计算的 bitset 会一直驻留在缓存中直到它被剔除。剔除规则是基于 LRU 的，一旦缓存满了，最近最少使用的过滤器会被剔除。</p><p data-lines="3" data-type="p" data-sign="f58947e102590b452e725be4a8a607e4">28 . bool查询是如何计算得到文档的分值的？
以should子句为例，先运行should子句中的两个查询，然后把子句查询返回的分值相加，相加得到的分值乘以匹配的查询子句的数量，再除以总的查询子句的数量得到最终的分值。</p><p data-lines="2" data-type="p" data-sign="69b5ab65dfb70087aaeb0325a682767e">29 . 查询时的tie_breaker参数的作用是什么？</p><p data-lines="6" data-type="p" data-sign="48f5322c9378bfac5725824cabdca1a8">	tie_breaker参数会让dis_max查询的行为更像是dis_max和bool的一种折中。它会通过下面的方式改变分值计算过程：
	* 取得最佳匹配查询子句的score
	* 将其它每个匹配的子句的分值乘以tie_breaker
	* 将以上得到的分值进行累加并规范化
	通过tie_breaker参数，所有匹配的子句都会起作用，只不过最佳匹配子句的作用更大。</p><p data-lines="2" data-type="p" data-sign="77fad269d70af59f40c6eb327aaf02e0">30 . min_score参数设置后，多次查询结果可能会不一致，因为查询primary shard和replica shard的结果可能不一致。</p><p data-lines="2" data-type="p" data-sign="04f924d7eda8e3410c60ba03b35ecff1">31 . 在plainless脚本中使用doc['field']取值和使用['_source']['field']取值有什么不同？</p><p data-lines="2" data-type="p" data-sign="99d58eefd84cdce1f76b0f29b3c6bac2">	使用doc['field']取值会把字段field的所有term都加载到内存(并且会被缓存)，执行效率高，但是比较消耗内存，另外这种取值方式只能去简单类型的字段，不能对Object类型的字段取值；使用_source取值因为不会有缓存，所以每次都要把_source内容加载到内存并且解析，因此效率很低。推荐使doc['field']取值。</p><p data-lines="2" data-type="p" data-sign="1b762b16cb54523942eecde6ac983d95">32 . scroll api里的scroll参数的作用是保持search context, 但是只需要设置为处理一个批次所需的时间即可。scroll时会在merge操作时依然保留merge前的old segments， 会带来存储上的开销以及需要更多文件描述符；search.max_open_scroll_context参数可以设置node上最大的context数量，默认无限制。scroll请求不会用到cache，因为使用cache在查询请求执行过程中会修改search context，会破坏掉scroll的context。</p><p data-lines="2" data-type="p" data-sign="dbea1f569da3eacc3cf3e26f15c02c07">33 . es 5.6以后在search api中加入了pre filter shards 逻辑，当要查询的shards数量超过128并且查询可能会被重写为MatchNoneQuery时，会进行pre filter， 过滤掉shards，提高查询效率。在search时返回结果中的_shards.skipped表示了过滤掉了多少shard。</p><p data-lines="2" data-type="p" data-sign="ee12734b0f3fc58c0bbe195bcd361437">34 . es默认使用的用于打分的bm2.5相似度算法中，计算idf的部分，log(docCount+1/docFreq+0.5), docCount的值是所有包含要查询的field的文档数量；docFreq是所有包含field value的文档数量。</p><p data-lines="2" data-type="p" data-sign="394c03e9e78541fae7cedfabc4b03ae3">35 . es统计的索引大小是整个索引所占空间空间的大小，整个索引包括很多文件，比如tim词典，tip词典索引，pos位置信息，fdt存储字段信息（_source实际存储的文件），等等。es中"codec": "best_compression" ，是对fdt这个文件进行压缩，其他的是不会进行压缩的。</p><p data-lines="2" data-type="p" data-sign="5f3878967c6d162b0173f3dd4463f12f">36 . 横向增加节点扩容时，不能搬迁已经close的索引到新的节点上, 需要先手动处理这种索引才可以。</p><p data-lines="2" data-type="p" data-sign="7380d6c2063fd22562f57f822ca257f9">37 . fielddata是在堆内存的，docvalues是在堆外内存的；docvalues默认对所有not_analyzed字段开启(index时生成)，如果要对analyzed字段进行聚合，就要使用fielddata了(使用时把所有的数据全都加载进内存)。如果不需要对analyzed字段进行聚合，就可以降低堆内存的使用。</p><p data-lines="5" data-type="p" data-sign="b11edeed4208ffeb82aad09a75ef5fe7">38 . ES 写入异常流程总结：
	* 如果请求在协调节点的路由阶段失败，则会等待集群状态更新，拿到更新后，进行重试，如果再次失败，则仍旧等集群状态更新，直至1分钟超时为止，超时后则进行整体请求失败处理
	* 在主分片写入过程中，写入是阻塞的；只有写入成功，才会发起写副本请求；如果主分片写失败，则整个请求被认为处理失败；如果有部分副本分片写失败，则整个请求被认为是处理成功的，会在结果中返回多少个分片成功，多少个分片失败；
	* 无论主分片还是副本分片，当写一个doc失败时，集群不会重试，而是关闭本地shard，然后向master汇报。</p><p data-lines="4" data-type="p" data-sign="84ac72f041fe5734503303cce864590f">39 . ES写入流程存在的一些问题：
	* 副本分片写入过程重新写入数据，不能单纯复制数据，浪费计算能力，影响写入速度
	* 磁盘管理能力较差，对坏盘检查和容忍性比HDFS差不少；在配置多次盘路径的情况下，有一块坏盘就无法启动节点。</p><p data-lines="1" data-type="p" data-sign="96c89e338f55bb95642b2fa89768bfbb">40 . ES在分布式上表现的一些特性：</p><ul class="cherry-list__square" data-lines="5" data-sign="256ccc962247bec0a933f89c3628aae6list5"><li>数据可靠性：通过分片副本和事务日志保障数据安全</li><li>服务可用性：在可用性和一致性的取舍方面，默认ES更倾向于可用性，只要主分片可用即可执行写入操作</li><li>一致性：弱一致性？最终一致性？只要主分片写入成功，数据就能被读取</li><li>原子性：数据读写是原子操作，不会出现中间状态，但是bulk不是原子操作，不能用来实现事务</li><li>扩展性：主分片和副本分片都可以承担读请求，分担系统负载</li></ul><p data-lines="1" data-type="p" data-sign="ffe1cc967822b11629f3f51d9283e12f">41 . Elasticsearch有自研的熔断器，默认情况下当jvm old 区使用率超过85% ，拒绝写入；当jvm old 区使用率超过90% ，拒绝查询；日志报错有"pressure too high"字样; 详细介绍见<a rel="nofollow" href="https://cloud.tencent.com/document/product/845/56272%E3%80%82">https://cloud.tencent.com/document/product/845/56272。</a></p><p data-lines="4" data-type="p" data-sign="0ef941d0e3e2be81d3cabefa34821019">42 . term聚合，在High Cardinality下，性能越来越差的原因是什么？
字段唯一值非常多，对该字段进行terms聚合时需要构建Global Ordinals(内部实现)，对旧的索引只需构建一次也就是首次查询时构建一次，后续查询就可以直接使用缓存中的Global Ordinals; 而对持续写入的索引，每当底层segment发生变化时(有新数据写入导致产生新的Segment、Segment Merge), 就需要重新构建Global Ordinals，随着数据量的增大，字段的唯一值越来越多，构建Global Ordinals越来越慢，所以对持续写入的索引，聚合查询会越来越慢。
terms聚合查询使用的Global Ordinals是shard级别的，把字符串转为整型，目的是为了在聚合时降低内存的使用；最后再reduce阶段，也就是收集各个shard的聚合结果的时候并且汇总完毕后，再把整型转换为原始字符串。
当底层的Segment发生变化时，Global Ordinals就失效了，再次查询时就需要重新构建；默认的构建时机是search查询时，在6.x版本引入了eager_global_ordinals，把构建全局序数放在了index索引时，但是对index性能有一定影响。</p><p data-lines="1" data-type="p" data-sign="8d3235e07eb94d7a0e89d2783c302da2">43 . es使用了CMS垃圾回收器，默认情况下JVM堆内存young区和old区的大小是多少？</p><p data-lines="7" data-type="p" data-sign="b2c0b8e48a00fe6d01c675c11b3b73af">	JVM堆内存参数中用于控制young区和old区大小的参数如下：

		* 最高优先级：&nbsp; -XX:NewSize=1024m和-XX:MaxNewSize=1024m
		* 次高优先级：&nbsp; -Xmn1024m&nbsp; （默认等效效果是：-XX:NewSize==-XX:MaxNewSize==1024m）
		* 最低优先级：-XX:NewRatio=2
	es用的是CMS垃圾回收器，所以young区的大小是JVM根据系统的配置计算得到的，newRatio默认虽然为2但是不起作用;除非显式的配置-Xmn或者-XX:NewSize， young区大小的计算公式为：
	</p><div data-sign="70d8d3057436cdd32fd8a136bc870044" data-type="codeBlock" data-lines="4">
      <pre><code>const size_t preferred_max_new_size_unaligned =
    MIN2(max_heap/(NewRatio+1), ScaleForWordSize(young_gen_per_worker * parallel_gc_threads));</code></pre>

<p data-lines="2" data-type="p" data-sign="3700f93fd01c8e81e3e8cc8e03ba7098">	其中ScaleForWordSize大约为64M (64位机器)<em> (机器cpu核数) </em> 13 / 10</p><span data-lines="2" data-type="br" data-sign="br2"></span><p data-lines="1" data-type="p" data-sign="2c8d407042cb8d37980494f660a30c16">44 . update操作不一定会触发refresh, 如果update的doc_id已经是可以被searcher检索到的，比如已经存在于某个segment里，就无需refresh。 但是如果update的doc_id存在于index writter buffer里，还未refresh，典型的就是同一个bulk操作里写入了多个重复的id， 实时GET就会触发refresh。</p><p data-lines="2" data-type="p" data-sign="d00c3f5a1c2c64c4ffaa28468a9a74f5">45 . 一般1 TB的磁盘数据，需要 2- 5GB 左右的 FST内存开销，这个只是FST的开销（常驻内存），一般FST占用50%左右的堆内内存。如果查询和写入压力稍微大一点，32GB Heap，内存很容易成为瓶颈。</p><p data-lines="2" data-type="p" data-sign="13cd66b2f096182f7307e0e0fe3ca80b">46 . zen2相比zen的优势？</p><p data-lines="5" data-type="p" data-sign="4ad3a95ba83082b276ff71302c406357">	* mininum_master_nodes被移除，es自己决定哪些节点作为candidate master nodes；而6.x版本的zen协议，可能会因为该参数配置错误导致集群无法选主，另外在扩缩容节点时也需要调整该参数
	* 典型的主节点选举可以在1s内完成，相比6.x, es通过延迟几秒钟的时间再进行选举防止各种各样的配置错误，意味着有几秒钟的时间集群不可用
	* 增长和缩小集群变得更安全，更容易，并且错误配置导致数据丢失的机会变少了。
	* 点增加更多的记录状态的日志，帮助诊断无法加入集群或无法选举出主节点的原因</p><p data-lines="2" data-type="p" data-sign="0e7f787fcf065ada5adf6e4e8aa75a73">47 . 什么是adaptive replica selection？</p><p data-lines="9" data-type="p" data-sign="0d84e5d4083b18aa838bc38b55d59f0b">	默认情况下，ES的协调节点选择在处理查询请求时，对于有多个副本的某个分片，选择哪个分片进行查询，依据的准则1是shard allocation awareness， 也就是和协调节点在同一个位置（location）的节点，比如协调节点在可用区1，那么如果可用区1有要查询的副本分片，则会优先选择可用区1的节点进行查询；依据的准则2是：
	(1) 协调节点和候选节点之前查询的响应时间，响应时间越短，优先选择
	(2) 之前的查询中，候选节点执行查询任务的处理时间(took time)，处理时间越短,优先选择
	(3) 候选节点的查询队列，队列中查询任务越少，优先选择

	adaptive replica selection旨在降低查询延迟，可以通过动态修改cluster.routing.use_adaptive_replica_selection配置为false关闭该特性，关闭之后，查询时将会采用round robin策略，可能会使得查询延迟增加。

48 . es为什么不适用一致性hash做数据的sharding?</p><p data-lines="3" data-type="p" data-sign="31d12cad9e2a489dddc64b7cd565dc88">	es使用简单的hash方式：hash(routing) % number_of_shards，实现起来较为简单，效率也更高。当需要扩展分片数量的时候，可以通过创建新索引+别名的方式解决。
	为什么不用一致性hash？对es来说，底层的存储是lucene 的segment, 它的不可变特性造成了仅仅移动5%左右的文档到新的分片，代价就会很大(因为使用一致性hash需要考虑rehash，所以需要移动文档到新的分片)。所以通过创建新的分片数量更大的索引进行读写，实现要简单的多，不必考虑移动文档造成的系统资源开销。</p><p data-lines="7" data-type="p" data-sign="6421f7653c833e188589f01df1b426f4">49 . ES在CAP理论上的实践：
	* C是一致性：最终一致性，主分片写完后再写副本分片，可能存在主分片写完之后可读，副本分片还没有refresh读不到数据
	* A是可用性：通过副本和translog保证数据可靠性
	* P是分区容错性：master和data节点间互相ping，进行故障节点检测与恢复

	在CAP三个特性上如何做折中？写数据时主分片写完之后，写副本分片时不要求所有的副本分片都能成功，在一致性与可用性上倾向于可用性。</p><p data-lines="6" data-type="p" data-sign="5187da2764f765eb1bb15af0403263f3">50 . es的读写模型相比原生的PacificA算法的区别
	* Prepare阶段：PacificA中有Prepare阶段，保证数据在所有节点Prepare成功后才能Commit，保证Commit的数据不丢，ES中没有这个阶段，数据会直接写入。
	* 读一致性：ES中所有InSync的Replica都可读，提高了读能力，但是可能读到旧数据。另一方面是即使只能读Primary，ES也需要Lease机制等避免读到Old Primary。因为ES本身是近实时系统，所以读一致性要求可能并不严格。

	总结来讲，就是原生的PacificA算法具有两阶段提交的过程，ES并没有，数据会直接写入副本分片；ES中副本分片也是可以承担读请求的，因为ES本身设计之初是为了满足搜索场景，也是一个近实时系统，所以在读一致性上可能要求并不严格。</p></div>				</div>
