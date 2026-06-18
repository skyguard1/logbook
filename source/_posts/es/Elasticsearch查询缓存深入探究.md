---
title: "Elasticsearch查询缓存深入探究"
date: 2022-06-16 21:45:48
categories:
  - es
---

<h2 data-lines="1" data-sign="9ae12804c91b10510a0b38807af66bfe" id="%E4%B8%80%E3%80%81%E5%9F%BA%E7%A1%80%E6%A6%82%E5%BF%B5"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#%E4%B8%80%E3%80%81%E5%9F%BA%E7%A1%80%E6%A6%82%E5%BF%B5" class="anchor"></a>一、基础概念</h2><p data-lines="3" data-type="p" data-sign="ad684a980af7f82199d24026bb364de3" style=""><img alt="" src="/logbook/images/es/Elasticsearch查询缓存深入探究/ffeef47bb25e.png" style="position: relative; z-index: 2;" class="amplify"><br>上图是Elasticsearch的存储结构</p><h3 data-lines="1" data-sign="f1d042b1c9e04203cdb42496bdae1977" id="11-index%EF%BC%88%E7%B4%A2%E5%BC%95%EF%BC%89"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#11-index%EF%BC%88%E7%B4%A2%E5%BC%95%EF%BC%89" class="anchor"></a>1.1 Index（索引）</h3><p data-lines="1" data-type="p" data-sign="3c2ec8af9213f931052044d2fca6abf2">Elasticsearch是文档型数据库，索引就是一堆文档的集合。他本身并不是一个物理上的概念，而是逻辑上的命名空间，指向一个或者多个分片</p><h3 data-lines="2" data-sign="852cd2e9b4f38914101157e1628fb971" id="12-shard%EF%BC%88%E5%88%86%E7%89%87%EF%BC%89"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#12-shard%EF%BC%88%E5%88%86%E7%89%87%EF%BC%89" class="anchor"></a>1.2 Shard（分片）</h3><p data-lines="1" data-type="p" data-sign="461a6bbeacc7d8e9ab2c9bd1cde2eec6">Elasticsearch为了解决单机的性能和可用性问题，分割巨大的索引，让读写并行，在索引分成了多个分片存储。</p><p data-lines="3" data-type="p" data-sign="397c24ac2dad42051a858efebefd2b7b">一个索引可以分成多组分片，分组分片有一个主分片，一个或者多个副本。<br>写数据的时候，先写主分片，再同步到副本。读的时候所有的主分片和副本都可提供读的能力。</p><p data-lines="2" data-type="p" data-sign="0bd70efa9ffd5387408a9e1ba6700c4c">我们都知道Elasticsearch是基于Lucene实现的分布式存储，它的每一个分片就是一个Lucene索引。</p><h3 data-lines="2" data-sign="c99a3ca3caca147ef3b64ee6fa2628ba" id="13-lucene-index%EF%BC%88lucene%E7%B4%A2%E5%BC%95%EF%BC%89"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#13-lucene-index%EF%BC%88lucene%E7%B4%A2%E5%BC%95%EF%BC%89" class="anchor"></a>1.3 Lucene Index（Lucene索引）</h3><p data-lines="1" data-type="p" data-sign="d1e81d5c1bd3c725c38fe1198f02df81">Lucene索引就是一个完整的搜索引擎，可以执行索引和搜索任务。</p><h3 data-lines="2" data-sign="f21b19273cb0a55ba158ee552adb16b1" id="14-segment%EF%BC%88%E6%AE%B5%EF%BC%89"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#14-segment%EF%BC%88%E6%AE%B5%EF%BC%89" class="anchor"></a>1.4 Segment（段）</h3><p data-lines="1" data-type="p" data-sign="f449d062be559c48e818dbf9a69f3330">Lucene索引有很多段组成，每个段都一个倒排索引。Elasticsearch每refresh一次，就会生成一个新的段，段的内部就是一堆文档的集合。</p><h3 data-lines="2" data-sign="9ce9045301944dc1e6ccb74ea687e270" id="15-%E9%9B%86%E7%BE%A4%E8%8A%82%E7%82%B9"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#15-%E9%9B%86%E7%BE%A4%E8%8A%82%E7%82%B9" class="anchor"></a>1.5 集群节点</h3><p data-lines="1" data-type="p" data-sign="af9e5c9040e92fdba74236effb5d20e9">Elasticsearch集群中的节点一共分为四种：</p><div data-lines="6" data-sign="c59bc783f6c60d6d2f897f0085829ff8" class="cherry-table-container"><table class="cherry-table"><thead><tr><th>节点名称</th><th>作用</th></tr></thead><tbody><tr><td>Master节点</td><td>负责集群层面的操作，管理集群变更</td></tr><tr><td>数据节点</td><td>负责保存数据，执行数据相关操作</td></tr><tr><td>协调节点</td><td>处理客户端请求的节点</td></tr><tr><td>预处理节点</td><td>允许数据在被索引之前，定义事先配置的处理器和管道对数据进行转换</td></tr></tbody></table>

<h2 data-lines="2" data-sign="a96f4aab7e35c613abaed82e0e179d66" id="%E4%BA%8C%E3%80%81%E6%9F%A5%E8%AF%A2%E7%BC%93%E5%AD%98query-cache"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#%E4%BA%8C%E3%80%81%E6%9F%A5%E8%AF%A2%E7%BC%93%E5%AD%98query-cache" class="anchor"></a>二、查询缓存Query Cache</h2><p data-lines="2" data-type="p" data-sign="3c911a21aa1b8db36b8087b8a82dd929">Elasticsearch中的查询缓存又成为FilterCache。顾名思义，就是针对filter条件过滤的结果进行缓存。<br>那为什么filter的结果可以缓存，因为<strong>filter主要用于结构化的数据过滤，不进行相关性得分计算</strong>，比如</p><div data-sign="01e53c1e6da2db243703b3852b15b02d" data-type="codeBlock" data-lines="6"><pre><code>      "filter": [
        { "term":  { "status": "published" }},
        { "range": { "publish_date": { "gte": "2015-01-01" }}}
      ]
</code></pre>

<h3 data-lines="1" data-sign="531ce70f384cce2681c81191d07d1cac" id="21-%E6%9F%A5%E8%AF%A2%E7%BC%93%E5%AD%98%E5%AD%98%E5%82%A8%E5%9C%A8%E5%93%AA%E9%87%8C%EF%BC%9F"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#21-%E6%9F%A5%E8%AF%A2%E7%BC%93%E5%AD%98%E5%AD%98%E5%82%A8%E5%9C%A8%E5%93%AA%E9%87%8C%EF%BC%9F" class="anchor"></a>2.1 查询缓存存储在哪里？</h3><p data-lines="1" data-type="p" data-sign="cb1e36cc92d3f307be6ecbb389402a3e">查询缓存全称其实是<code>Node Query Cache</code>。再一次顾名思义，它是节点级别的缓存，针对每个段分别维护了<code>LeafCache</code>。前面提到执行数据相关操作的是数据节点，所以<code>QueryCache</code>存在于数据节点中。</p><h3 data-lines="2" data-sign="8fc2ccc284bee00cbc7c1ad3cdd185b1" id="22-%E6%9F%A5%E8%AF%A2%E7%BC%93%E5%AD%98%E7%9A%84%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#22-%E6%9F%A5%E8%AF%A2%E7%BC%93%E5%AD%98%E7%9A%84%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84" class="anchor"></a>2.2 查询缓存的数据结构</h3><p data-lines="1" data-type="p" data-sign="09a3cecc9199d5e1b4bc8ff1856e670f"><code>QueryCache</code>是两层嵌套结构的Map。</p><div data-sign="59c82b275f85d84718de71d5b3aff452" data-type="codeBlock" data-lines="3"><pre><code>private final Map&lt;IndexReader.CacheKey, LeafCache&gt; cache;
</code></pre>

<p data-lines="1" data-type="p" data-sign="d25ee2f268920c73beff54106f316477">最外层是一个支持LRU淘汰的Map。CacheKey是一个Java的Object，作为段的标识，CacheValue是上面说的<code>LeafCache</code>。</p><p data-lines="2" data-type="p" data-sign="2c6d07e55c85e91745a9bed4cf0d451b">这里比较奇特的是，LRU并不是针对这个cache的key来淘汰的（当然这样就更不合理了），而是针对<code>LeafCache</code>中的key。</p><p data-lines="1" data-type="p" data-sign="ed28f90d74d451f188ca6d2513a9d6c5">缓存的的核心是<code>LeafCache</code>。</p><div data-sign="af2ed4b1dffa3c96c2008ce073232c5d" data-type="codeBlock" data-lines="5"><pre><code>private class LeafCache implements Accountable {
  private final Map&lt;Query, DocIdSet&gt; cache;
  }
</code></pre>

<p data-lines="1" data-type="p" data-sign="c26b6ddb4aee180cad7b05e8535667d6"><code>LeafCache</code>的本质也是一个Map。Map的Key是Query，也就是符合缓存条件的子查询，具体实现类有<code>TermQuery</code>，<code>BooleanQuery</code>，<code>TermRangeQuery</code>等等，Value是DocIdSet。</p><h4 data-lines="2" data-sign="fe5d5400d742c7364d77b56946c3ee65" id="docidset"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#docidset" class="anchor"></a>DocIdSet</h4><p data-lines="2" data-type="p" data-sign="76af1f55bb0b4ee6eadaa5786ab7fb22">顾名思义，是文档ID的集合。我们知道Elasticsearch的搜索其实两个阶段，『Query Then Fetch』。慢的是Query阶段，根据ID Fetch阶段是很快的，这个缓存刚好是加速Query。<br><code>DocIdSet</code>的底层实现是可以有很多种，默认情况是<code>FixedBitSet</code>或者<code>RoaringBitSet</code>(源自<code>RoaringBitmap</code>，在查询命中很多文档时使用，优化稀疏数据的空间占用)</p><h3 data-lines="1" data-sign="492a9e2f26b10c26728cb8aded1910cd" id="23-%E7%BC%93%E5%AD%98%E7%AD%96%E7%95%A5"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#23-%E7%BC%93%E5%AD%98%E7%AD%96%E7%95%A5" class="anchor"></a>2.3 缓存策略</h3><p data-lines="1" data-type="p" data-sign="3d55f28e8f9e6f43d053d60d78401897"><code>QueryCache</code>的缓存策略并不是来者不拒，而是有门槛的，只有符合条件的查询才可以被缓存。</p><h4 data-lines="2" data-sign="062f2e08ec25014d4619c72d302ab3e2" id="231-%E5%93%AA%E4%BA%9B%E6%AE%B5%E5%8F%AF%E4%BB%A5%E7%BC%93%E5%AD%98"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#231-%E5%93%AA%E4%BA%9B%E6%AE%B5%E5%8F%AF%E4%BB%A5%E7%BC%93%E5%AD%98" class="anchor"></a>2.3.1 哪些段可以缓存</h4><div data-sign="a524ba1a136b77b684742b7d28baf676" data-type="codeBlock" data-lines="12"><pre><code>if (in.isCacheable(context) == false) {
  // this segment is not suitable for caching
  return in.bulkScorer(context);
}

// Short-circuit: Check whether this segment is eligible for caching
// before we take a lock because of #get
if (shouldCache(context) == false) {
  return in.bulkScorer(context);
}
</code></pre>

<p data-lines="1" data-type="p" data-sign="325d8999c14080d0a21fc8a125269529">对段有两个检查，第一个是是否可以缓存，第二个是缓存它是否优雅。</p><p data-lines="2" data-type="p" data-sign="4ae994c8ecafef81c23d613724d5f7d3">是否可以缓存主要是检查段是否可以修改，只有补课修改才可以被缓存。如果段依赖全局的统计或者评分，就不可以缓存。</p><p data-lines="1" data-type="p" data-sign="ee94105760536280480340a1d60fe433">缓存优雅的定义：</p><ol start="1" class="cherry-list__default" data-lines="2" data-sign="11631c4a5a9ead72c355d0d603e79b03list2"><li>假设索引所有的文档都被缓存，也就是每个bit一个文档，内存开销必须要小于的<code>QueryCache</code>总内存的20%。这里主要是避免空间开销过大，导致频繁会回收。</li><li>查询对应的段持有文档数大于10000，占索引总文档数3%以上才可以缓存。</li></ol><h4 data-lines="2" data-sign="2374bee5c25af70398ba56cafc615bd3" id="232-%E5%93%AA%E4%BA%9B%E5%AD%90%E6%9F%A5%E8%AF%A2%E5%8F%AF%E4%BB%A5%E7%BC%93%E5%AD%98"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#232-%E5%93%AA%E4%BA%9B%E5%AD%90%E6%9F%A5%E8%AF%A2%E5%8F%AF%E4%BB%A5%E7%BC%93%E5%AD%98" class="anchor"></a>2.3.2 哪些子查询可以缓存</h4><p data-lines="1" data-type="p" data-sign="e3e6577e54f6dfff874f5083c6964f60">Lucene默认的缓存策略是<code>UsageTrackingQueryCachingPolicy</code>来控制的。</p><div data-sign="0c54b5777438b0522d59caf0d55aac1e" data-type="codeBlock" data-lines="11"><pre><code>@Override
public boolean shouldCache(Query query) throws IOException {
  if (shouldNeverCache(query)) {
    return false;
  }
  final int frequency = frequency(query);
  final int minFrequency = minFrequencyToCache(query);
  return frequency &gt;= minFrequency;
}
</code></pre>

<p data-lines="1" data-type="p" data-sign="913a0b726d59a301339b5f30973b954d">从上面的代码可以看出来首先过滤不能被缓存的查询：</p><ol start="1" class="cherry-list__default" data-lines="4" data-sign="950d65e232e91dbc6fac3945a9d384f7list4"><li>本身查询比较快的：<br><code>TermQuery</code>，<code>DocValuesFieldExistsQuery</code>，<code>MatchAllDocsQuery</code>。<strong>这里尤其要注意，我们常用的<code>TermQuery</code>是不可以被缓存的。</strong></li><li>无效的查询：<br>比如<code>MatchNoDocsQuery</code>，空的<code>BooleanQuery</code>和空的<code>DisjunctionMaxQuery</code></li></ol><p data-lines="3" data-type="p" data-sign="b28c8851e5b910a52aa26f5a7270fbc8">然后再就是查询的频率检查，只要查询的频率大于最新的频率要求即可。<br>一般来说，耗时的查询是2次，非耗时的查询是5次，<code>BooleanQuery</code>和<code>DisjunctionMaxQuery</code>是4次。<br>这个耗时查询的判断也比较简单粗暴，只是限定几种特定的类型：</p><div data-sign="93e3b5bae2ad511859fc66db3815e910" data-type="codeBlock" data-lines="11"><pre><code>static boolean isCostly(Query query) {
  // This does not measure the cost of iterating over the filter (for this we
  // already have the DocIdSetIterator#cost API) but the cost to build the
  // DocIdSet in the first place
  return query instanceof MultiTermQuery ||
      query instanceof MultiTermQueryConstantScoreWrapper ||
      query instanceof TermInSetQuery ||
      isPointQuery(query);
}
</code></pre>

<p data-lines="3" data-type="br" data-sign="br3">&nbsp;</p><h3 data-lines="1" data-sign="e8020e68e585d7bbd3a8835bd967d4d0" id="24-%E6%B7%98%E6%B1%B0%E7%AD%96%E7%95%A5"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#24-%E6%B7%98%E6%B1%B0%E7%AD%96%E7%95%A5" class="anchor"></a>2.4 淘汰策略</h3><h4 data-lines="1" data-sign="38029b68f959aefad1e87f3cbabddc1b" id="241-%E6%95%B4%E4%B8%AAleafcache%E6%B7%98%E6%B1%B0"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#241-%E6%95%B4%E4%B8%AAleafcache%E6%B7%98%E6%B1%B0" class="anchor"></a>2.4.1 整个LeafCache淘汰</h4><p data-lines="1" data-type="p" data-sign="b841b2a128dfdd2f242ad82927690137">段存在合并或者删除，在创建<code>LeafCache</code>的时候会注册一个段关闭的监听器，以便段不存在时可以释放缓存空间。</p><div data-sign="3c8642e2fafded6e4d4a25c4b0266b9e" data-type="codeBlock" data-lines="10"><pre><code>if (leafCache == null) {
  leafCache = new LeafCache(key);
  final LeafCache previous = cache.put(key, leafCache);
  ramBytesUsed += HASHTABLE_RAM_BYTES_PER_ENTRY;
  assert previous == null;
  // we just created a new leaf cache, need to register a close listener
  cacheHelper.addClosedListener(this::clearCoreCacheKey);
}
</code></pre>

<h4 data-lines="1" data-sign="cf67c62fac451931d638baf24a2ef3f0" id="242-docidset%E7%9A%84%E6%B7%98%E6%B1%B0"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#242-docidset%E7%9A%84%E6%B7%98%E6%B1%B0" class="anchor"></a>2.4.2 DocIdSet的淘汰</h4><p data-lines="1" data-type="p" data-sign="4c1aa6835e3dbfb70937c892e146dedd">每一次往LeafCache新增KV的时候，都会检查是否是需要淘汰数据，如果需要就不断的淘汰，直到缓存符合要求。</p><div data-sign="3ff2e2379bd39b7d8407c705542091a4" data-type="codeBlock" data-lines="12"><pre><code>/** Whether evictions are required. */
boolean requiresEviction() {
  assert lock.isHeldByCurrentThread();
  final int size = mostRecentlyUsedQueries.size();
  if (size == 0) {
    return false;
  } else {
    return size &gt; maxSize || ramBytesUsed() &gt; maxRamBytesUsed;
  }
}
</code></pre>

<p data-lines="1" data-type="p" data-sign="a20540547778db7083037fc8f41d71e1">是否需要淘汰的标准就是总的缓存条目数量或者内存占用是超标。默认配置maxSize=10000，maxRamBytesUsed=10%的jvm内存。</p><p data-lines="1" data-type="p" data-sign="0878753056025499f22bf7771de791c7">说完了什么时候要淘汰，那改淘汰谁如何决定。上面提到这个缓存是基于LRU来实现。</p><div data-sign="ff8b84701565c2ed536736d7fbfad3a1" data-type="codeBlock" data-lines="4"><pre><code>uniqueQueries = new LinkedHashMap&lt;&gt;(16, 0.75f, true);
mostRecentlyUsedQueries = uniqueQueries.keySet();
</code></pre>

<p data-lines="1" data-type="p" data-sign="a9b444c4a5637b6be15059bd2ad7ba2c">从上面的源码可以看到LRU是通过<code>LinkedHashMap</code>实现的，注意第三个参数是true，表示遍历的时候按照访问顺序排序。</p><h3 data-lines="2" data-sign="deba05ab8e6f692875cb620422953619" id="25-%E5%A6%82%E4%BD%95%E6%9F%A5%E7%9C%8B%E6%9F%A5%E8%AF%A2%E7%BC%93%E5%AD%98%E7%BB%9F%E8%AE%A1%E4%BF%A1%E6%81%AF"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#25-%E5%A6%82%E4%BD%95%E6%9F%A5%E7%9C%8B%E6%9F%A5%E8%AF%A2%E7%BC%93%E5%AD%98%E7%BB%9F%E8%AE%A1%E4%BF%A1%E6%81%AF" class="anchor"></a>2.5 如何查看查询缓存统计信息</h3><p data-lines="3" data-type="p" data-sign="05eb4ab5b451b1a7cb7ee187af21d4f1">可以REST接口查看整个集群的QueryCache统计数据<br><code>GET http://HOST/_stats/query_cache?pretty&amp;human</code><br>下面是我们这边某一个业务的查询缓存统计情况：</p><div data-sign="ceae3c81cb73b9a89c6c35d54302bee9" data-type="codeBlock" data-lines="31"><pre><code>{
    "index_xxx":{
        "uuid":"70C4hjUNQBmdhgIwldjGWw",
        "primaries":{
            "query_cache":{
                "memory_size":"38.9mb",
                "memory_size_in_bytes":40797183,
                "total_count":40152875,
                "hit_count":10128303,
                "miss_count":30024572,
                "cache_size":614,
                "cache_count":7007355,
                "evictions":7006741
            }
        },
        "total":{
            "query_cache":{
                "memory_size":"79.8mb",
                "memory_size_in_bytes":83679114,
                "total_count":44022035,
                "hit_count":11528037,
                "miss_count":32493998,
                "cache_size":1288,
                "cache_count":7496441,
                "evictions":7495153
            }
        }
    }
}
</code></pre>

<p data-lines="1" data-type="p" data-sign="1ccf89884af11316ba7a5b6e4d5ae459">这里memory_size 和memory_size_in_bytes都表示内存占用</p><h5 data-lines="1" data-sign="922ebdab0557a0911e5e35e3f31d6ba5" id="total-count"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#total-count" class="anchor"></a>total_count</h5><p data-lines="1" data-type="p" data-sign="112336d55b21929ff8032a1e8f4c41c3">等于hit_count + miss_count</p><h5 data-lines="1" data-sign="6a2afb0964ddc64e7141fcf6ded307da" id="hit-count"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#hit-count" class="anchor"></a>hit_count</h5><p data-lines="1" data-type="p" data-sign="1326222008353602dd02574cf7a238a5">命中缓存的次数</p><h5 data-lines="1" data-sign="72892e17bddaa4c199736d70573a8c45" id="miss-count"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#miss-count" class="anchor"></a>miss_count</h5><p data-lines="1" data-type="p" data-sign="34ac98f353ac0a5e75b0512477c9ac66">没有命中缓存的次数</p><h5 data-lines="1" data-sign="9febc05ff6e04a70dfa5a40c7aa0a0e7" id="cache-size"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#cache-size" class="anchor"></a>cache_size</h5><p data-lines="1" data-type="p" data-sign="693b6d89648890a8db7e2c2ae4cb8a40">缓存中当前entry的数量</p><h5 data-lines="1" data-sign="f1273386a1989a9803ead0ed09721e4a" id="cache-count"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#cache-count" class="anchor"></a>cache_count</h5><p data-lines="1" data-type="p" data-sign="8e12af17a1f25b8d74536266ccc3eccb">所有生成的entry总数。如果hit_count比这个值高很多，说明缓存的作用比较明显。上面的数据中，miss_count比cache_count高很多，主要原因是使用了很多Term查询，不需要缓存，这个需要具体场景具体分析。</p><h5 data-lines="1" data-sign="a09c7d6f8f9288978ac1edff59780270" id="evictions"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#evictions" class="anchor"></a>evictions</h5><p data-lines="1" data-type="p" data-sign="d5fd9a41adfdcb369cb865df1d2dcfb4">等于cache_count - cache_size。我们前面讲淘汰策略的时候知道这里可能是因为内存总量或者entry总数达到上限被清理，也包括段被关闭。这个值高说明查询被复用，或者因为段早早的被合并，缓存策略有些激进。</p><h2 data-lines="2" data-sign="469304e70470af63b233f5ec52624a88" id="%E6%80%BB%E7%BB%93"><a href="https://km.woa.com/articles/show/516036?kmref=search&amp;from_page=1&amp;no=9#%E6%80%BB%E7%BB%93" class="anchor"></a>总结</h2><p data-lines="1" data-type="p" data-sign="47d9713d964bf794a58a91d394a10e88">本文从源码层面深入探究了Elasticsearch查询缓存的内部实现。这些原理性的东西，虽然对于日常开发需求作用不大，但是在存在性能瓶颈时，熟悉内部实现，可以帮助我们快速找到解决问题的办法，有的场景是需要增大缓存，而有的场景是则是需优化查询条件。</p><p data-lines="7" data-type="br" data-sign="br7">&nbsp;</p>				</div>
