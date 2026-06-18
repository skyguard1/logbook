---
title: "Elasticsearch聚合查询源码解析(一)"
date: 2022-06-16 21:31:48
categories:
  - es
---

<p>Elasticsearch的查询类型默认是query_then_fetch, 也就是先执行query获取到命中文档的Top N个docId列表， 接着执行fetch, 根据docId列表获取具体的doc内容。其中query阶段中根据请求入参也会执行rescorePhrase（重新评分）、suggestPhrase（查询建议）、aggregationPhrase（聚合）这几个阶段, 如下所示：</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token decorator annotation punctuation">@Override</span>
    public void execute<span class="token punctuation">(</span>SearchContext searchContext<span class="token punctuation">)</span> throws QueryPhaseExecutionException <span class="token punctuation">{</span>
        <span class="token keyword">if</span> <span class="token punctuation">(</span>searchContext<span class="token punctuation">.</span>hasOnlySuggest<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
            suggestPhase<span class="token punctuation">.</span>execute<span class="token punctuation">(</span>searchContext<span class="token punctuation">)</span><span class="token punctuation">;</span>
            searchContext<span class="token punctuation">.</span>queryResult<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">.</span>topDocs<span class="token punctuation">(</span>new TopDocsAndMaxScore<span class="token punctuation">(</span>
                    new TopDocs<span class="token punctuation">(</span>new TotalHits<span class="token punctuation">(</span><span class="token number">0</span><span class="token punctuation">,</span> TotalHits<span class="token punctuation">.</span>Relation<span class="token punctuation">.</span>EQUAL_TO<span class="token punctuation">)</span><span class="token punctuation">,</span> Lucene<span class="token punctuation">.</span>EMPTY_SCORE_DOCS<span class="token punctuation">)</span><span class="token punctuation">,</span> Float<span class="token punctuation">.</span>NaN<span class="token punctuation">)</span><span class="token punctuation">,</span>
                new DocValueFormat<span class="token punctuation">[</span><span class="token number">0</span><span class="token punctuation">]</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
            <span class="token keyword">return</span><span class="token punctuation">;</span>
        <span class="token punctuation">}</span>

        <span class="token keyword">if</span> <span class="token punctuation">(</span>LOGGER<span class="token punctuation">.</span>isTraceEnabled<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
            LOGGER<span class="token punctuation">.</span>trace<span class="token punctuation">(</span><span class="token string">"{}"</span><span class="token punctuation">,</span> new SearchContextSourcePrinter<span class="token punctuation">(</span>searchContext<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
        <span class="token punctuation">}</span>

        <span class="token operator">//</span> Pre<span class="token operator">-</span>process aggregations <span class="token keyword">as</span> late <span class="token keyword">as</span> possible<span class="token punctuation">.</span> In the case of a DFS_Q_T_F
        <span class="token operator">//</span> request<span class="token punctuation">,</span> preProcess <span class="token keyword">is</span> called on the DFS phase phase<span class="token punctuation">,</span> this <span class="token keyword">is</span> why we pre<span class="token operator">-</span>process them
        <span class="token operator">//</span> here to make sure it happens during the QUERY phase
        aggregationPhase<span class="token punctuation">.</span>preProcess<span class="token punctuation">(</span>searchContext<span class="token punctuation">)</span><span class="token punctuation">;</span>
        boolean rescore <span class="token operator">=</span> executeInternal<span class="token punctuation">(</span>searchContext<span class="token punctuation">)</span><span class="token punctuation">;</span>

        <span class="token keyword">if</span> <span class="token punctuation">(</span>rescore<span class="token punctuation">)</span> <span class="token punctuation">{</span> <span class="token operator">//</span> only <span class="token keyword">if</span> we do a regular search
            rescorePhase<span class="token punctuation">.</span>execute<span class="token punctuation">(</span>searchContext<span class="token punctuation">)</span><span class="token punctuation">;</span>
        <span class="token punctuation">}</span>
        suggestPhase<span class="token punctuation">.</span>execute<span class="token punctuation">(</span>searchContext<span class="token punctuation">)</span><span class="token punctuation">;</span>
        aggregationPhase<span class="token punctuation">.</span>execute<span class="token punctuation">(</span>searchContext<span class="token punctuation">)</span><span class="token punctuation">;</span>

        <span class="token keyword">if</span> <span class="token punctuation">(</span>searchContext<span class="token punctuation">.</span>getProfilers<span class="token punctuation">(</span><span class="token punctuation">)</span> <span class="token operator">!=</span> null<span class="token punctuation">)</span> <span class="token punctuation">{</span>
            ProfileShardResult shardResults <span class="token operator">=</span> SearchProfileShardResults
                <span class="token punctuation">.</span>buildShardResults<span class="token punctuation">(</span>searchContext<span class="token punctuation">.</span>getProfilers<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
            searchContext<span class="token punctuation">.</span>queryResult<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">.</span>profileResults<span class="token punctuation">(</span>shardResults<span class="token punctuation">)</span><span class="token punctuation">;</span>
        <span class="token punctuation">}</span>
    <span class="token punctuation">}</span>
</code></pre>

<p>本文会以常用的Terms Aggregation查询为例，介绍了ES在聚合查询上的实现方式。<br>
如下是一个最简单的terms聚合查询：</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token punctuation">{</span>
  <span class="token string">"query"</span><span class="token punctuation">:</span><span class="token punctuation">{</span>
      <span class="token string">"match_all"</span><span class="token punctuation">:</span><span class="token punctuation">{</span>

      <span class="token punctuation">}</span>
  <span class="token punctuation">}</span><span class="token punctuation">,</span>
  <span class="token string">"aggs"</span><span class="token punctuation">:</span><span class="token punctuation">{</span>
      <span class="token string">"a"</span><span class="token punctuation">:</span><span class="token punctuation">{</span>
          <span class="token string">"terms"</span><span class="token punctuation">:</span><span class="token punctuation">{</span>
              <span class="token string">"field"</span><span class="token punctuation">:</span><span class="token string">"b"</span>
          <span class="token punctuation">}</span>
      <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<h2 id="AggregationPhrase">AggregationPhrase</h2>

<p style="">AggregationPhrase和其它几种Phrase都实现了SearchPhrase, 入口方法为execute()<br>
<img src="./Elasticsearch聚合查询源码解析(一) -  - KM平台_files/cos-file-url(2)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h3 id="1-生成Aggregators列表">1.生成Aggregators列表</h3>

<p>根据查询语句中的聚合查询条件，构造出Aggregator对象列表， 这里只包含GlobalAggregator， SubAggregator不在内。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">        Aggregator<span class="token punctuation">[</span><span class="token punctuation">]</span> aggregators <span class="token operator">=</span> context<span class="token punctuation">.</span>aggregations<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">.</span>aggregators<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
        List <span class="token builtin">globals</span> <span class="token operator">=</span> new ArrayList<span class="token operator">&lt;&gt;</span><span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
        <span class="token keyword">for</span> <span class="token punctuation">(</span><span class="token builtin">int</span> i <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span> i <span class="token operator">&lt;</span> aggregators<span class="token punctuation">.</span>length<span class="token punctuation">;</span> i<span class="token operator">+</span><span class="token operator">+</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
            <span class="token keyword">if</span> <span class="token punctuation">(</span>aggregators<span class="token punctuation">[</span>i<span class="token punctuation">]</span> instanceof GlobalAggregator<span class="token punctuation">)</span> <span class="token punctuation">{</span>
                <span class="token builtin">globals</span><span class="token punctuation">.</span>add<span class="token punctuation">(</span>aggregators<span class="token punctuation">[</span>i<span class="token punctuation">]</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
            <span class="token punctuation">}</span>
        <span class="token punctuation">}</span>
</code></pre>

<h3 id="2-构建BucketCollector">2.构建BucketCollector</h3>

<p>根据GlobalAggregator列表， 构建BucketCollector，BucketCollector实现自Lucene的Collector， 用于完成对查询结果的聚合和统计。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">BucketCollector globalsCollector <span class="token operator">=</span> MultiBucketCollector<span class="token punctuation">.</span>wrap<span class="token punctuation">(</span><span class="token builtin">globals</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
</code></pre>

<h3 id="3- preCollection">3. preCollection</h3>

<p>聚合预处理：</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">globalsCollector<span class="token punctuation">.</span>preCollection<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
</code></pre>

<h3 id="4- 调用Lucene search方法">4. 调用Lucene search方法</h3>

<p>真正执行聚合的地方，调用了Lucene indexSearch的search方法，用于对查询结果进行分Bucket统计。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">context<span class="token punctuation">.</span>searcher<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">.</span>search<span class="token punctuation">(</span>query<span class="token punctuation">,</span> collector<span class="token punctuation">)</span><span class="token punctuation">;</span>
</code></pre>

<h3 id="5- postCollection">5. postCollection</h3>

<p>聚合后处理：</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">aggregator<span class="token punctuation">.</span>postCollection<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
</code></pre>

<h3 id="6-结果赋值">6.结果赋值</h3>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">aggregations<span class="token punctuation">.</span>add<span class="token punctuation">(</span>aggregator<span class="token punctuation">.</span>buildAggregation<span class="token punctuation">(</span><span class="token number">0</span><span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
</code></pre>

<h3 id="7-执行pipelineAggregator">7.执行pipelineAggregator</h3>

<p>pipelineAggregator需要在Global aggregator执行完毕后才能执行。</p>

<h3 id="核心类">核心类</h3>

<p style=""><img src="./Elasticsearch聚合查询源码解析(一) -  - KM平台_files/cos-file-url(3)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
