---
title: "Elasticsearch聚合查询源码解析(一)"
date: 2022-06-16 21:31:48
categories:
  - es
---

<p>Elasticsearch的查询类型默认是query_then_fetch, 也就是先执行query获取到命中文档的Top N个docId列表， 接着执行fetch, 根据docId列表获取具体的doc内容。其中query阶段中根据请求入参也会执行rescorePhrase（重新评分）、suggestPhrase（查询建议）、aggregationPhrase（聚合）这几个阶段, 如下所示：</p>

<pre><code>@Override
    public void execute(SearchContext searchContext) throws QueryPhaseExecutionException {
        if (searchContext.hasOnlySuggest()) {
            suggestPhase.execute(searchContext);
            searchContext.queryResult().topDocs(new TopDocsAndMaxScore(
                    new TopDocs(new TotalHits(0, TotalHits.Relation.EQUAL_TO), Lucene.EMPTY_SCORE_DOCS), Float.NaN),
                new DocValueFormat[0]);
            return;
        }

        if (LOGGER.isTraceEnabled()) {
            LOGGER.trace("{}", new SearchContextSourcePrinter(searchContext));
        }

        // Pre-process aggregations as late as possible. In the case of a DFS_Q_T_F
        // request, preProcess is called on the DFS phase phase, this is why we pre-process them
        // here to make sure it happens during the QUERY phase
        aggregationPhase.preProcess(searchContext);
        boolean rescore = executeInternal(searchContext);

        if (rescore) { // only if we do a regular search
            rescorePhase.execute(searchContext);
        }
        suggestPhase.execute(searchContext);
        aggregationPhase.execute(searchContext);

        if (searchContext.getProfilers() != null) {
            ProfileShardResult shardResults = SearchProfileShardResults
                .buildShardResults(searchContext.getProfilers());
            searchContext.queryResult().profileResults(shardResults);
        }
    }
</code></pre>

<p>本文会以常用的Terms Aggregation查询为例，介绍了ES在聚合查询上的实现方式。<br>
如下是一个最简单的terms聚合查询：</p>

<pre><code>{
  "query":{
      "match_all":{

      }
  },
  "aggs":{
      "a":{
          "terms":{
              "field":"b"
          }
      }
  }
}
</code></pre>

<h2 id="AggregationPhrase">AggregationPhrase</h2>

<p style="">AggregationPhrase和其它几种Phrase都实现了SearchPhrase, 入口方法为execute()<br>
</p>

<h3 id="1-生成Aggregators列表">1.生成Aggregators列表</h3>

<p>根据查询语句中的聚合查询条件，构造出Aggregator对象列表， 这里只包含GlobalAggregator， SubAggregator不在内。</p>

<pre><code>        Aggregator[] aggregators = context.aggregations().aggregators();
        List globals = new ArrayList&lt;&gt;();
        for (int i = 0; i &lt; aggregators.length; i++) {
            if (aggregators[i] instanceof GlobalAggregator) {
                globals.add(aggregators[i]);
            }
        }
</code></pre>

<h3 id="2-构建BucketCollector">2.构建BucketCollector</h3>

<p>根据GlobalAggregator列表， 构建BucketCollector，BucketCollector实现自Lucene的Collector， 用于完成对查询结果的聚合和统计。</p>

<pre><code>BucketCollector globalsCollector = MultiBucketCollector.wrap(globals);
</code></pre>

<h3 id="3- preCollection">3. preCollection</h3>

<p>聚合预处理：</p>

<pre><code>globalsCollector.preCollection();
</code></pre>

<h3 id="4- 调用Lucene search方法">4. 调用Lucene search方法</h3>

<p>真正执行聚合的地方，调用了Lucene indexSearch的search方法，用于对查询结果进行分Bucket统计。</p>

<pre><code>context.searcher().search(query, collector);
</code></pre>

<h3 id="5- postCollection">5. postCollection</h3>

<p>聚合后处理：</p>

<pre><code>aggregator.postCollection();
</code></pre>

<h3 id="6-结果赋值">6.结果赋值</h3>

<pre><code>aggregations.add(aggregator.buildAggregation(0));
</code></pre>

<h3 id="7-执行pipelineAggregator">7.执行pipelineAggregator</h3>

<p>pipelineAggregator需要在Global aggregator执行完毕后才能执行。</p>

<h3 id="核心类">核心类</h3>

<p style=""></p>
