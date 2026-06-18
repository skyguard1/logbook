---
title: "ElasticSearch 应用架构介绍与开发优化经验"
date: 2022-06-16 21:57:00
categories:
  - es
---

<h1 id="h1-elasticsearch-"><a name="ElasticSearch 应用架构介绍与开发优化经验" class="reference-link"></a><span class="header-link octicon octicon-link"></span>ElasticSearch 应用架构介绍与开发优化经验</h1><div class="markdown-toc editormd-markdown-toc"><ul class="markdown-toc-list"><li><a class="toc-level-1" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#ElasticSearch%20%E5%BA%94%E7%94%A8%E6%9E%B6%E6%9E%84%E4%BB%8B%E7%BB%8D%E4%B8%8E%E5%BC%80%E5%8F%91%E4%BC%98%E5%8C%96%E7%BB%8F%E9%AA%8C" level="1">ElasticSearch 应用架构介绍与开发优化经验</a><ul><li><a class="toc-level-2" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#1.%20%E8%83%8C%E6%99%AF%E4%BB%8B%E7%BB%8D" level="2">1. 背景介绍</a></li><li><a class="toc-level-2" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#2.%20%E6%9E%B6%E6%9E%84%E9%83%A8%E7%BD%B2%E6%96%B9%E6%A1%88" level="2">2. 架构部署方案</a><ul><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#2.1.%20%20mmuxelasticsearchproxy" level="3">2.1.  mmuxelasticsearchproxy</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#2.2.%20mq" level="3">2.2. mq</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#2.3.%20http%20basic_auth_proxy" level="3">2.3. http basic_auth_proxy</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#2.4.%20WFS%20fuse" level="3">2.4. WFS fuse</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#2.5.%20%E5%85%B6%E4%BB%96%E5%B7%A5%E5%85%B7" level="3">2.5. 其他工具</a></li></ul></li><li><a class="toc-level-2" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#3.%20%E5%9F%BA%E4%BA%8EElasticSearch%20%E7%9A%84%E5%BC%80%E5%8F%91%E6%8C%87%E5%8D%97" level="2">3. 基于ElasticSearch 的开发指南</a><ul><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#3.1.%20query%20DSL%20%E8%AF%AD%E6%B3%95" level="3">3.1. query DSL 语法</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#3.2.%20%E5%88%86%E8%AF%8D" level="3">3.2. 分词</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#3.3.%E5%85%B3%E7%B3%BB%E5%9E%8B%E6%90%9C%E7%B4%A2" level="3">3.3.关系型搜索</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#3.4.%20%E7%9B%B8%E5%85%B3%E6%80%A7%E6%89%93%E5%88%86" level="3">3.4. 相关性打分</a><ul><li><a class="toc-level-4" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#3.4.1.%20BM25%20%E4%BE%8B%E8%A7%A3" level="4">3.4.1. BM25 例解</a></li><li><a class="toc-level-4" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#3.4.2.%20BM25%20shard%20%E8%B0%83%E6%95%B4" level="4">3.4.2. BM25 shard 调整</a></li><li><a class="toc-level-4" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#3.4.3.%20BM25%20similarity%20%E5%8F%82%E6%95%B0%E8%B0%83%E6%95%B4" level="4">3.4.3. BM25 similarity 参数调整</a></li></ul></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#3.5%20%E7%89%88%E6%9C%AC%E6%8E%A7%E5%88%B6" level="3">3.5 版本控制</a></li></ul></li><li><a class="toc-level-2" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#4.%E6%80%A7%E8%83%BD%E4%BC%98%E5%8C%96" level="2">4.性能优化</a><ul><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#4.1.%20page%20cache%20%E5%86%85%E5%AD%98%E4%BC%98%E5%8C%96" level="3">4.1. page cache 内存优化</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#4.2.%20%20int%20%E5%AD%97%E6%AE%B5%E6%9F%A5%E8%AF%A2%E4%BC%98%E5%8C%96" level="3">4.2.  int 字段查询优化</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#4.3.%20%E5%89%AF%E6%9C%AC%E6%95%B0%20replicas%20num" level="3">4.3. 副本数 replicas num</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#4.4.%20%20%E5%A4%9A%20SSD" level="3">4.4.  多 SSD</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#4.5.%20%E5%86%85%E5%AD%98%E9%85%8D%E7%BD%AE" level="3">4.5. 内存配置</a></li><li><a class="toc-level-3" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#4.6.%20refresh_interval" level="3">4.6. refresh_interval</a></li></ul></li><li><a class="toc-level-2" href="https://km.woa.com/group/24938/articles/show/390684?kmref=search&amp;from_page=1&amp;no=4#5.%20%E4%B8%80%E4%BA%9B%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99" level="2">5. 一些参考资料</a><ul></ul></li></ul></li></ul>

<h2 id="h2-1-"><a name="1. 背景介绍" class="reference-link"></a><span class="header-link octicon octicon-link"></span>1. 背景介绍</h2><p>ElasticSearch 是由 Lucene 包装上分布式复制一致性算法等附加功能，构成的开源搜索引擎系统。</p>
<p>近两年在业界热度大增，主要有 3 种应用场景：</p>
<ol>
<li>全文搜索引擎</li><li>NOSQL 数据库</li><li>日志分析数据库 ELK</li></ol>
<p>随着中心业务探索发展，出现越来越多的垂直领域搜索需求，因此最近半年我们引入了 ElasticSearch 到我们的基础架构中，来实现此类需求。</p>
<p>目前已经支撑了 13 个搜索推荐召回业务，最大的文档数过 20亿。</p>
<p>ElasticSearch 大幅度提升了相关业务的迭代开发速度，<br>并在相对高 qps 的在线业务中，保证了毫秒级的延迟，极高的可用性和稳定性。</p>
<p>在持续的研读官方文档，调研业界经验，并在开发中应用实践反思后，我们总结出一套在  后台环境下的 ElasticSearch 架构方案。故写本文，供大家参考，也欢迎意见建议。</p>
<h2 id="h2-2-"><a name="2. 架构部署方案" class="reference-link"></a><span class="header-link octicon octicon-link"></span>2. 架构部署方案</h2><p></p><div style="text-align: left;">

<p></p>
<p>如图所示， 一个 ElasticSearch 集群 cluster 部署成一个  后台模块，<br>集群的每台 ElasticSearch 机器上，同机部署： </p>
<ol>
<li>基于 svrkit 的转发代理  mmuxelasticsearchproxy</li><li>本地的 mq</li><li>带认证的 http proxy basic_auth_proxy</li><li>fuse 方式 mount wfs  </li></ol>
<h3 id="h3-2-1-mmuxelasticsearchproxy"><a name="2.1.  mmuxelasticsearchproxy" class="reference-link"></a><span class="header-link octicon octicon-link"></span>2.1.  mmuxelasticsearchproxy</h3><p>mmuxelasticsearchproxy 的功能是：</p>
<ol>
<li>协议转换 ，做 svrkit protobuf 和 ElasticSearch REST json 之间的协议转换，<br> 对文档更新等请求，定义了 proto，便于后文 mq 做各种处理。<br> 对灵活多变的 Search/Aggression 等请求，直接透传 json 。</li><li>引入  svrkit RPC 框架成熟的负载均衡，容灾，故障屏蔽等功能，到对 ES 的 RPC 中，<br> 比如如果单机 ES 进程挂了，通过返回 -601 COMM_ERR_SVRACTIVEREJECT ，让调用方自动换机器重试。</li><li>监控告警，用  统一监控告警系统，监控各种请求失败，延迟分布等，并监控 ElasticSearch java 进程状态，集群状态</li><li>转发文档更新 BulkOp 请求给本机的 mq 。用 mq 做削峰填谷，自动合并批量，做限流。</li><li>提供双写能力，便于索引升级切换</li><li>proxy 到本机 ES 做了 http 连接池，避免频繁的 HTTP tcp 建连接。</li></ol>
<h3 id="h3-2-2-mq"><a name="2.2. mq" class="reference-link"></a><span class="header-link octicon octicon-link"></span>2.2. mq</h3><p>mq 实现了 出队限流，请求合并，削峰填谷 3个功能。</p>
<p>在我们实际业务中，常常会每天做文档全量更新，会出现短时间内写请求高峰，</p>
<p>之前的做法是直接写 ES，这样请求高峰时，经常出现 ES  write 线程池占满，导致部分写请求失败。</p>
<p>另外部分业务每次请求只更新1个文档，导致 ES cpu 高，影响 ES 的写性能，不符合官方推荐做法。</p>
<p>为此，我们使用了技术架构部的成熟的 mq 3.0 ，</p>
<p>用配置限制了出队的 QPS ，确保集中高峰被抹平，以匀速稳定地写入 ES，彻底消除了更新失败。</p>
<p>并用配置自动把多个请求合并成批量 （比如 5000个文档一个批量），优化了 ES 的写入性能。</p>
<p>请求高峰中超出配置 QPS 的请求，mq 自动暂存在文件中，随后处理，保证了 ES 服务平稳。</p>
<p>在此为 mq 3.0 点赞。</p>
<h3 id="h3-2-3-http-basic_auth_proxy"><a name="2.3. http basic_auth_proxy" class="reference-link"></a><span class="header-link octicon octicon-link"></span>2.3. http basic_auth_proxy</h3><p>默认的 ElasticSearch 没有权限认证，只要能连上端口，就能随意增删改查数据，这是极大的安全隐患。</p>
<p>因此我们配置 ElastSearch 只监听 loopback 127.0.0.1 。</p>
<p>那 Kibana 之类的网页管理工具怎么连接服务器呢？<br>于是我用 python 写了个 http proxy，把本机 eth1 上的 http 端口，代理到 loopback 上的 http 端口，代码很简单只有 200多行。</p>
<p>并在 http proxy 中实现了基于公司统一 smart proxy 的 OA token 认证，并接入了  统一的权限管理系统，点点鼠标即可管理权限。</p>
<p>另外，ES 7.2 版本开放了 xpack-security ，包含用户管理权限认证等，后续也在考虑集成。</p>
<h3 id="h3-2-4-wfs-fuse"><a name="2.4. WFS fuse" class="reference-link"></a><span class="header-link octicon octicon-link"></span>2.4. WFS fuse</h3><p>另外， 和技术架构部的同事合作， 以 fuse 方式挂载了 WFS 作为远程文件系统，实现了 数据的周期性备份。</p>
<h3 id="h3-2-5-"><a name="2.5. 其他工具" class="reference-link"></a><span class="header-link octicon octicon-link"></span>2.5. 其他工具</h3><p>另外，繁荣的 ES 开源生态中，周边工具非常丰富便捷，<br>我们常用的两种周边工具：kinana 和 bin/elasticsearch-sql-cli，极其方便快捷，大幅度提升了开发效率。</p>
<h2 id="h2-3-elasticsearch-"><a name="3. 基于ElasticSearch 的开发指南" class="reference-link"></a><span class="header-link octicon octicon-link"></span>3. 基于ElasticSearch 的开发指南</h2><p>垂直搜索系统的在线检索部分，一般流程如下</p>
<p></p><div style="text-align: left;">

<p></p>
<p>ES 用来实现 召回和粗排环节 ，和部分自动补全环节。</p>
<p>对比之前的一些内部 C++ 搜索框架 和  ES/Lucene，</p>
<p>基于内部框架开发的痛点：</p>
<ol>
<li>代码晦涩，没有文档，学习成本高，容易误用，一旦出问题要耗费大量时间解决。</li><li>开发流程繁琐，开发周期长速度慢，开发成本高，无法支撑业务逻辑快速迭代。</li><li>设计灵活性通用性不足，部分 and/or/not 深度嵌套的复杂业务检索 query 无法表达。</li><li>框架代码 bug 多不稳定，框架变更引入的 bug 屡次导致故障，影响了在线业务稳定性。</li></ol>
<p>基于 ES 开发的优点：</p>
<ol>
<li>ES/Lucene 的 Query DSL 极其强大全面灵活，业务逻辑代码大幅度简化，开发简单便捷，业务迭代开发速度大大提高。</li><li>有商业公司维护的高质量官方文档， 网上也有海量资料，新同事几天就可以上手，快速形成生产力，提升团队效率。</li><li>成熟稳定，就我们目前经验没有遇到过 bug</li><li>业务如果扩展，后续伸缩性，扩展性，分 shard ，多副本等，都有比较成熟方案。</li></ol>
<h3 id="h3-3-1-query-dsl-"><a name="3.1. query DSL 语法" class="reference-link"></a><span class="header-link octicon octicon-link"></span>3.1. query DSL 语法</h3><p>基于 ES 的开发，首先需要学习常见的几种 query，</p>
<p>ES 的 query  简单分成 4 类:</p>
<ol>
<li>term query，对单个词的 query，包括 term/terms/range/exists/missing/ids/regexp 等</li><li>full text query ，全文检索query，对多个词（即句子）的query，包括<br> match/multi_match/common 等</li><li>compound query 复合 query，包括 bool/dis_max/function_score 等</li><li>match_all ，简单匹配所有文档</li></ol>
<p>建议先学习 term/match/range/bool ，就可以实现大部分业务逻辑。</p>
<p>网上资料较多，就不转述了。</p>
<p>可以先看看这些中文资料，在 test 环境的 kibana 做做实验，快速上手：</p>
<p><a href="https://www.elastic.co/guide/cn/elasticsearch/guide/current/search-in-depth.html" target="_blank">https://www.elastic.co/guide/cn/elasticsearch/guide/current/search-in-depth.html</a></p>
<p><a href="https://my.oschina.net/yumg/blog/637409" target="_blank">https://my.oschina.net/yumg/blog/637409</a></p>
<p><a href="https://www.cnblogs.com/yjf512/p/4897294.html" target="_blank">https://www.cnblogs.com/yjf512/p/4897294.html</a></p>
<p>当然最好的还是官方英文文档：</p>
<p><a href="https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html" target="_blank">https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html</a></p>
<h3 id="h3-3-2-"><a name="3.2. 分词" class="reference-link"></a><span class="header-link octicon octicon-link"></span>3.2. 分词</h3><p>中文搜索的一个核心议题，就是分词。</p>
<p>ElasticSearch 常用的中文分词是 ik analyzer。ik 是开箱即用，便于小型业务快速开发的。</p>
<p>但是作为对分词可定制性要求较高的业务，我们实际测试，发现 ik analyzer :</p>
<ol>
<li>不支持本地自定义词典文件的热加载；</li><li>无法针对不同 index 配置不同自定义词典；</li><li>另外对一些分词的 bad case ，比如没有正确切分的词，没法简单 fix。</li></ol>
<p>因此推荐不用 ik ，而是在更新文档和搜索的时候，在外部做分词，然后用空格拼起来，传给 ES 做索引/搜索。这种方案中，在 ES mapping 中配置成 whitespace 分词器。</p>
<p>外部分词可以灵活使用 cppjieba，QQSeg 等，其中索引分词还可以合并多种分词算法结果提高召回率。</p>
<p>另外，索引分词之前，也有必要做 UTF8 的 normalize，全角转半角，英文大小写统一，和英文的词干提取， mapping 中常用</p>
<pre style="position: relative; z-index: 2;"><code class="hljs haskell"><span class="hljs-string">"cjk_width"</span>, <span class="hljs-string">"lowercase"</span>, <span class="hljs-string">"porter_stem"</span>
</code></pre><p>这些filter</p>
<p>具体可以参考已有业务代码。</p>
<h3 id="h3-3-3-"><a name="3.3.关系型搜索" class="reference-link"></a><span class="header-link octicon octicon-link"></span>3.3.关系型搜索</h3><p>实际某业务开发中，我们遇到了典型的  one-many 关系型数据上的检索需求，</p>
<p>经过调研发现常见有 4 种方案：</p>
<ol>
<li><p>分开2 个 index : one + many ，分开2次串行 search，<br>问题: 需要2次延迟大</p>
</li><li><p>反范式，完全展开，one 的数据追加到每一个 many 文档中，<br>问题：数据量变大，更新 one 需要用 _update_by_query<br>如果 one 数据更新频繁，可能导致大量写操作</p>
</li><li><p>nested ，比如 one 嵌套 many 子文档<br>问题是：nested 嵌套文档更新需要更新整个 root 文档，即要把整个 one 文档 和含有的 many 文档 select 出来，修改，再写回。<br>对热门 one 文档， 更新会操作大量数据，并发写还可能 data race。</p>
</li></ol>
<ol>
<li>join, has_parent, has_child<br>把 one 和 many 的所有字段合并到一个 index 中， one 和  many 分别独立更新。</li></ol>
<p>经过实际数据测试 join field 方案， 发现当 one:many = 1:1000万 时， 延迟在 5ms 可以接受，因此目前采用了这种方案。</p>
<p>当然，官方文档指出 join 性能是会慢的，后续也有待实践检验。</p>
<p><a href="https://www.elastic.co/guide/en/elasticsearch/guide/master/relations.html" target="_blank">https://www.elastic.co/guide/en/elasticsearch/guide/master/relations.html</a></p>
<h3 id="h3-3-4-"><a name="3.4. 相关性打分" class="reference-link"></a><span class="header-link octicon octicon-link"></span>3.4. 相关性打分</h3><p>Lucene 从 2016年的 6.0 版本开始，默认的相关性算法切换成了 bm25 ，<br>bm25 是一种调整过的 tf idf 算法。</p>
<p>这里可以做一简单举例介绍，更深入的介绍可以参见下面文章，以及官方文档：</p>
<p><a href="https://farer.org/2018/09/10/practical-bm25-part-1-how-shards-affect-relevance-scoring-in-elasticsearch/" target="_blank">https://farer.org/2018/09/10/practical-bm25-part-1-how-shards-affect-relevance-scoring-in-elasticsearch/</a> </p>
<p><a href="https://www.cnblogs.com/richaaaard/p/5254988.html" target="_blank">https://www.cnblogs.com/richaaaard/p/5254988.html</a></p>
<p>ES 的 explain 对 bm25 算分的过程有详尽的解释，推荐自行实验。</p>
<p><a href="https://www.elastic.co/guide/en/elasticsearch/reference/current/search-explain.html" target="_blank">https://www.elastic.co/guide/en/elasticsearch/reference/current/search-explain.html</a></p>
<h4 id="h4-3-4-1-bm25-"><a name="3.4.1. BM25 例解" class="reference-link"></a><span class="header-link octicon octicon-link"></span>3.4.1. BM25 例解</h4><p>比如某业务的真实数据中，我们在所有文档的 title 这个 field 搜索 “牛奶 ” 这个词，</p>
<p>explain 可以看到，这个 bm25 分数的是这样得来的：</p>
<pre style="position: relative; z-index: 2;"><code class="hljs groovy">sum( weight(<span class="hljs-string">title:</span>牛奶 <span class="hljs-keyword">in</span> <span class="hljs-number">77341</span>) [PerFieldSimilarity] ) ，
weight(<span class="hljs-string">title:</span>牛奶 <span class="hljs-keyword">in</span> <span class="hljs-number">77341</span>) [PerFieldSimilarity] = idf * tfNorm
</code></pre><p>首先，如果某 field 被多个 term 命中，分别算每个 term 的分数 (PerFieldSimilarity)，然后求和，本例子只有1个 term “牛奶”。</p>
<p>每个 term 的分数 PerFieldSimilarity</p>
<pre style="position: relative; z-index: 2;"><code class="hljs ini"><span class="hljs-attr">PerFieldSimilarity</span> = idf * tfNorm
</code></pre><p>而 idf 表征词的重要程度，与具体文档无关。</p>
<pre style="position: relative; z-index: 2;"><code class="hljs lisp">idf = log(<span class="hljs-number">1</span> + (<span class="hljs-name">docCount</span> - docFreq + <span class="hljs-number">0.5</span>) / (<span class="hljs-name">docFreq</span> + <span class="hljs-number">0.5</span>))
</code></pre><p>其中<br>docFreq 就是本shard 中，有多少个文档含有 “牛奶”，<br>docCount 就是本shard 一共有多少个文档。</p>
<pre style="position: relative; z-index: 2;"><code class="hljs ini"><span class="hljs-attr">tfNorm</span> = (freq * (k1 + <span class="hljs-number">1</span>)) / (freq + k1 * (<span class="hljs-number">1</span> - b + b * fieldLength / avgFieldLength))
<span class="hljs-attr">termFreq</span>=<span class="hljs-number">1.0</span>
<span class="hljs-attr">k1</span>=<span class="hljs-number">1.2</span>
<span class="hljs-attr">b</span>=<span class="hljs-number">0.75</span>
<span class="hljs-attr">avgFieldLength</span>=<span class="hljs-number">14.456173</span>
<span class="hljs-attr">fieldLength</span>=<span class="hljs-number">2</span> //比如如果 title 是 <span class="hljs-string">"牛奶 醪糟"</span> ，那就是 <span class="hljs-number">2</span>个 term
</code></pre><p>freq 即该 field 中，“牛奶”这个词出现了几次<br>k1 和 b 都是固定常数。<br>fieldLength 是当前文档的当前field ，一共有多少个 term。<br>avgFieldLength 即本 shard 中的所有文档的本 field 的 fieldLength 的平均值</p>
<h4 id="h4-3-4-2-bm25-shard-"><a name="3.4.2. BM25 shard 调整" class="reference-link"></a><span class="header-link octicon octicon-link"></span>3.4.2. BM25 shard 调整</h4><p>实际业务发现，当 index 内文档太少(比如 10w 量级就算少) 时 ， 有的词在多个 shard 内，词频分布会出现严重不均匀，可能会导致 bm25 分数产生较大偏差，</p>
<p>实践中的解决办法：</p>
<ol>
<li>Search 的 url_parameters 参数填 “&amp;search_type=dfs_query_then_fetch”</li><li>减少 shard 数</li></ol>
<h4 id="h4-3-4-3-bm25-similarity-"><a name="3.4.3. BM25 similarity 参数调整" class="reference-link"></a><span class="header-link octicon octicon-link"></span>3.4.3. BM25 similarity 参数调整</h4><p>如上计算过程可见，bm25 中的 b 参数，是用来给短文档做加权的，即 b 越大，越倾向于给短文档更高的 score，<br>实际中，和算法同学一起分析后，发现针对我们的某业务，不应该对短文本有太高偏向，所以我们把 b 调整成了 0.3 ，<br>实测发现解决了一批 bad case，用户体验有明显改善。</p>
<h3 id="h3-3-5-"><a name="3.5 版本控制" class="reference-link"></a><span class="header-link octicon octicon-link"></span>3.5 版本控制</h3><p>后台数据一般都有持续的实时增量更新，有时候又希望一次导入全量数据。在全量导入的场景下，<br>由于全量数据从产生到实际导入，总是有一段时间区间，在区间内，就有部分文档被实时增量更新过了，<br>这样就存在 “老覆盖新”的风险。</p>
<p>对此， ES 提供一种 index-versioning 机制，对每个文档，都有个内置的 int64 的版本号，<br>利用这一机制，我们可以把时间戳填入 version，即 在 Bulk 更新的时候，</p>
<pre style="position: relative; z-index: 2;"><code class="hljs groovy"><span class="hljs-string">version_type :</span> <span class="hljs-string">"external"</span>,
<span class="hljs-string">version :</span> 数据产生时时间戳
</code></pre><p>ES 发现 请求版本号&lt;= 当前文档版本号，就会拒绝更新，就解决了 “老覆盖新” 的问题。</p>
<p><a href="https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-index/_.html#index-versioning" target="_blank">https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-index\_.html#index-versioning</a></p>
<p><a href="https://cloud.tencent.com/developer/article/1373212" target="_blank">https://cloud.tencent.com/developer/article/1373212</a></p>
<h2 id="h2-4-"><a name="4.性能优化" class="reference-link"></a><span class="header-link octicon octicon-link"></span>4.性能优化</h2><p>计算机程序的性能取决于数据结构和算法，<br>ES/Lucene 中主要有几种数据结构:</p>
<ol>
<li>FST</li><li>Posting List ，著名的倒排索引，PForDelta 压缩，支持 SkipList 方式跳跃</li><li>BKD Tree，用来实现 int 和 geo 查询</li><li>DocValues , 以 DocID 为 Key 的列存储</li></ol>
<p><a href="https://zhuanlan.zhihu.com/p/47951652" target="_blank">https://zhuanlan.zhihu.com/p/47951652</a></p>
<p><a href="https://www.elastic.co/blog/elasticsearch-query-execution-order" target="_blank">https://www.elastic.co/blog/elasticsearch-query-execution-order</a></p>
<p><a href="https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html" target="_blank">https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html</a></p>
<p>更深入的理解，我目前也在探索中。</p>
<p>在垂直搜索引擎业务中，用户对延迟非常敏感，一般业界经验认为，良好的用户体验应该是在 <strong> 200毫秒 </strong> 内返回搜索结果，<br>这就意味着 ES 延迟最好控制在 100毫秒之内。</p>
<p>经过我们实际业务发现，决定 ES 延迟的因素主要有：</p>
<ol>
<li>内存是否足够，主要是 page cache 是否 cache 了检索过程用到的文件数据</li><li>具体 query 的优化，类比 mysql slow query 优化</li></ol>
<h3 id="h3-4-1-page-cache-"><a name="4.1. page cache 内存优化" class="reference-link"></a><span class="header-link octicon octicon-link"></span>4.1. page cache 内存优化</h3><p>page cache 是决定 ES 延迟的首要因素，</p>
<p>实际中用作在线检索服务的 ES ，<br>在线检索的代码路径不能有硬盘 io 访问  (实践证明， SSD也不行) 。</p>
<p>实际中，某业务 index 发现延迟非常高，达到了 1-2秒，用户体验很差。<br>调查发现，iostat 看 io util 很高，经常到 80% - 90%，单机索引数据文件是 page cache 可用内存的 4倍，<br>于是降低了副本数，单机数据量减少到 page cache 可用内存2倍后， 硬盘 io 降到了 0 ，延迟一下降低到了 150ms 。</p>
<p>可以参考<br><a href="https://zhuanlan.zhihu.com/p/68706615" target="_blank">https://zhuanlan.zhihu.com/p/68706615</a><br><a href="https://zhuanlan.zhihu.com/p/60458049" target="_blank">https://zhuanlan.zhihu.com/p/60458049</a></p>
<h3 id="h3-4-2-int-"><a name="4.2.  int 字段查询优化" class="reference-link"></a><span class="header-link octicon octicon-link"></span>4.2.  int 字段查询优化</h3><p>业务中常会有一些 int 型的字段，存一些枚举性质的值。<br>在 10亿以上文档的情况下，实际发现有的会出性能问题。</p>
<p>比如前述业务有1个 int 类型的 filter 字段，实际只有 {0,1} 2种取值，</p>
<p>借助 ES 的 profile  ，我们发现搜索 query  93% 的耗时在 filter 字段的 PointInSetQuery 中，</p>
<p>随后发现，针对该业务，只需要返回 filter 为 0 的文档，于是我们在更新文档时，发现 filter 非0 的文档，直接把所有字段都清空，并随后在 query 中去掉了 filter 字段的过滤条件。</p>
<p>之后发现耗时从 150ms 降到了 20ms。</p>
<h3 id="h3-4-3-replicas-num"><a name="4.3. 副本数 replicas num" class="reference-link"></a><span class="header-link octicon octicon-link"></span>4.3. 副本数 replicas num</h3><p>ES 确定副本数的思路：</p>
<ol>
<li>副本数越小越好。越小，单机数据越少，文件被 cache 的比例越高，性能越好。</li><li>副本太少会影响可用性。因此必须大于最大能容忍故障单机个数 max_failures 。</li></ol>
<p>综合起来就是： </p>
<pre style="position: relative; z-index: 2;"><code class="hljs stylus"><span class="hljs-function"><span class="hljs-title">max</span><span class="hljs-params">(max_failures, ceil(num_nodes / num_primaries)</span></span> - <span class="hljs-number">1</span>).
</code></pre><p>num_primaries 是 primary shards 的数量，就是一个 index 有多少个 shards，一般都 &gt; num_nodes</p>
<p><a href="https://www.elastic.co/guide/en/elasticsearch/reference/master/tune-for-search-speed.html#_replicas_might_help_with_throughput_but_not_always" target="_blank">replicas_might_help_with_throughput_but_not_always</a></p>
<p>对数据量特别少的 index，可以每台机都存一个副本<br>“auto_expand_replicas”: “0-all”,</p>
<h3 id="h3-4-4-ssd"><a name="4.4.  多 SSD" class="reference-link"></a><span class="header-link octicon octicon-link"></span>4.4.  多 SSD</h3><p>在 elasticsearc.yml 的 path.data 配置多个路径，ES 会自动把 shard 均分到多个路径上，如果有多个硬盘，可以充分利用多设备的 io 带宽，当然对在线业务意义不大。</p>
<h3 id="h3-4-5-"><a name="4.5. 内存配置" class="reference-link"></a><span class="header-link octicon octicon-link"></span>4.5. 内存配置</h3><p>最开始我们使用 16G 内存机型，<br>后来发现出现大量 Elasticsearch Data too large Error 错误，随后发现，解决办法就是换到 64G 内存机型，</p>
<p>改 jvm.options 加大 jvm 的 heap 解决，从 10G 加大到 30G 解决<br>-Xms30g<br>-Xmx30g</p>
<p>需要注意的是，不建议大于 32G，避免 jvm 的指针压缩优化失效。<br>可以看 ES 的启动 log 确定<br>[2019-05-22T12:29:16,961][INFO ][o.e.e.NodeEnvironment    ] [node_xxx] heap size [29.7gb], compressed ordinary object pointers [true]</p>
<p><a href="https://www.elastic.co/cn/blog/a-heap-of-trouble" target="_blank">https://www.elastic.co/cn/blog/a-heap-of-trouble</a></p>
<h3 id="h3-4-6-refresh_interval"><a name="4.6. refresh_interval" class="reference-link"></a><span class="header-link octicon octicon-link"></span>4.6. refresh_interval</h3><p>如网上众多文章所说， refresh_interval 一般都设成了 30秒。<br>还有 translog 中 sync_interval, durability 的优化</p>
<h2 id="h2-5-"><a name="5. 一些参考资料" class="reference-link"></a><span class="header-link octicon octicon-link"></span>5. 一些参考资料</h2><p>中文社区业界资料汇总 <a href="https://elasticsearch.cn/slides/" target="_blank">https://elasticsearch.cn/slides/</a><br>滴滴 Elasticsearch 多集群架构实践 <a href="https://cloud.tencent.com/developer/article/1405404" target="_blank">https://cloud.tencent.com/developer/article/1405404</a><br>京东到家订单中心 Elasticsearch 演进历程 <a href="https://cloud.tencent.com/developer/article/1377194" target="_blank">https://cloud.tencent.com/developer/article/1377194</a><br>从平台到中台：Elaticsearch在蚂蚁金服的实践经验 <a href="https://new.qq.com/omn/20190117/20190117A09ADY.html" target="_blank">https://new.qq.com/omn/20190117/20190117A09ADY.html</a><br>美团点评旅游搜索召回策略的演进 <a href="https://tech.meituan.com/2017/06/16/travel-search-strategy.html" target="_blank">https://tech.meituan.com/2017/06/16/travel-search-strategy.html</a><br>eBay 的 Elasticsearch 性能调优实践  <a href="https://www.infoq.cn/article/elasticsearch-performance-tuning-practice-at-ebay" target="_blank">https://www.infoq.cn/article/elasticsearch-performance-tuning-practice-at-ebay</a><br>有赞搜索系统的架构演进 <a href="https://tech.youzan.com/search-tech-1/" target="_blank">https://tech.youzan.com/search-tech-1/</a><br>有赞搜索引擎实践(工程篇) <a href="https://tech.youzan.com/search-engine1/" target="_blank">https://tech.youzan.com/search-engine1/</a></p>
