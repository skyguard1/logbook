---
title: "Elasticsearch使用总结"
date: 2022-06-16 22:02:11
categories:
  - es
---

<h2 id="背景">背景</h2>

<p>开源的 <a href="https://www.elastic.co/cn/" target="_blank">Elasticsearch</a>（以下简称 <code>Elastic</code>）是目前全文搜索引擎的首选。它可以快速地储存、搜索和分析海量数据，维基百科、Stack Overflow、Github 都采用它。</p>

<p>Elastic 的底层是开源库 <a href="https://lucene.apache.org/" target="_blank">Lucene</a>。但是，你没法直接用 <code>Lucene</code>，必须自己写代码去调用它的接口。<code>Elastic</code> 是 <code>Lucene</code> 的封装，提供了 <code>REST API</code> 的操作接口，开箱即用。</p>

<h2 id="ES基本概念">ES基本概念</h2>

<p><strong>ES中概念和关系型数据库的概念类比关系如下表所示。</strong></p>
</div><div class="table-wrapper"><table>
<thead>
<tr>
<th>Relational Database</th>
<th>Elasticsearch</th>
</tr>
</thead>
<tbody>
<tr>
<td>Database</td>
<td>Index</td>
</tr>
<tr>
<td>Table</td>
<td>Type</td>
</tr>
<tr>
<td>Row</td>
<td>Document</td>
</tr>
<tr>
<td>Column</td>
<td>Field</td>
</tr>
<tr>
<td>Scheme</td>
<td>Mapping</td>
</tr>
<tr>
<td>Index</td>
<td>Everything is indexed</td>
</tr>
<tr>
<td>SQL</td>
<td>Query DSL</td>
</tr>
<tr>
<td>SELECT * FROM …</td>
<td>GET http://…</td>
</tr>
<tr>
<td>UPDATE table_name SET …</td>
<td>PUT http://…</td>
</tr>
</tbody>
</table>
</div>

<blockquote>
<p>Tip: ES中一个 index 下最好只创建一个 type，不要创建多个type。</p>
</blockquote>

<h3 id="Node-与-Cluster">Node 与 Cluster</h3>

<p>Elastic 本质上是一个分布式数据库，允许多台服务器协同工作，每台服务器可以运行多个 Elastic 实例。</p>

<p>单个 Elastic 实例称为一个节点（<code>node</code>）。一组节点构成一个集群（<code>cluster</code>）。</p>

<h3 id="Index">Index</h3>

<p>Elastic 会索引所有字段，经过处理后写入一个反向索引（<code>Inverted Index</code>）。查找数据的时候，直接查找该索引。</p>

<p>所以，<strong>Elastic 数据管理的顶层单位就叫做 </strong><code>Index</code>（索引）。它是单个数据库的同义词。每个 <code>Index</code> （即数据库）的名字必须是小写。</p>

<p>下面的命令可以查看当前节点的所有 Index。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>X GET <span class="token string">'http://localhost:9200/_cat/indices?v'</span>
</code></pre>

<h3 id="Document">Document</h3>

<p>Index 里面单条的记录称为 <code>Document</code>（文档）。许多条 <code>Document</code> 构成了一个 Index。</p>

<p>Document 使用 JSON 格式表示，下面是一个例子。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token punctuation">{</span>
  <span class="token string">"user"</span><span class="token punctuation">:</span> <span class="token string">"张三"</span><span class="token punctuation">,</span>
  <span class="token string">"title"</span><span class="token punctuation">:</span> <span class="token string">"工程师"</span><span class="token punctuation">,</span>
  <span class="token string">"desc"</span><span class="token punctuation">:</span> <span class="token string">"数据库管理"</span>
<span class="token punctuation">}</span>
</code></pre>

<p>同一个 Index 里面的 Document，不要求有相同的结构（scheme），但是最好保持相同，这样有利于提高搜索效率。</p>

<h3 id="Type">Type</h3>

<p>Document 可以分组，比如 <code>weather</code> 这个 Index 里面，可以按城市分组（北京和上海），也可以按气候分组（晴天和雨天）。这种分组就叫做 <code>Type</code>，<strong>它是虚拟的逻辑分组，用来过滤 Document</strong>。</p>

<p>不同的 Type 应该有相似的结构（<code>schema</code>），举例来说，id 字段不能在这个组是字符串，在另一个组是数值。这是与关系型数据库的表的<a href="https://www.elastic.co/guide/en/elasticsearch/guide/current/mapping.html" target="_blank">一个区别</a>。性质完全不同的数据（比如 <code>products</code> 和 <code>logs</code>）应该存成两个 Index，而不是一个 Index 里面的两个 Type（虽然可以做到）。</p>

<p>下面的命令可以列出每个 Index 所包含的 Type。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token string">'localhost:9200/_mapping?pretty=true'</span>
</code></pre>

<p>根据规划，Elastic 6.x 版只允许每个 Index 包含一个 Type，7.x 版将会彻底移除 Type。</p>

<h2 id="Index-新建-删除">Index 新建/删除</h2>

<p>新建 <code>Index</code>，可以直接向 Elastic 服务器发出 PUT 请求。下面的例子是新建一个名叫 <code>weather</code> 的 Index。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>X PUT <span class="token string">'localhost:9200/weather'</span>
</code></pre>

<p>服务器返回一个 JSON 对象，里面的 <code>acknowledged</code> 字段表示操作成功。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token punctuation">{</span>
  <span class="token string">"acknowledged"</span><span class="token punctuation">:</span>true<span class="token punctuation">,</span>
  <span class="token string">"shards_acknowledged"</span><span class="token punctuation">:</span>true
<span class="token punctuation">}</span>
</code></pre>

<p>然后，我们发出 DELETE 请求，删除这个 Index。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>X DELETE <span class="token string">'localhost:9200/weather'</span>

<span class="token punctuation">{</span>
   <span class="token string">"acknowledged"</span><span class="token punctuation">:</span>true
<span class="token punctuation">}</span>
</code></pre>

<h2 id="数据操作">数据操作</h2>

<p>在 ES 6.0之后，采用了严格 <code>content-type</code> 校验，需要添加 <code>-H'Content-Type: application/json'</code> 参数在命令行中。比如</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">curl <span class="token operator">-</span>X PUT <span class="token string">'localhost:9200/accounts/person/1'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
  <span class="token operator">//</span><span class="token punctuation">.</span><span class="token punctuation">.</span><span class="token punctuation">.</span>
<span class="token punctuation">}</span>'
</code></pre>

<p>需要更新为</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">curl <span class="token operator">-</span>H<span class="token string">'Content-Type: application/json'</span> <span class="token operator">-</span>X PUT <span class="token string">'localhost:9200/accounts/person/1'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
  <span class="token operator">//</span><span class="token punctuation">.</span><span class="token punctuation">.</span><span class="token punctuation">.</span>
<span class="token punctuation">}</span>'
</code></pre>

<h3 id="新增记录">新增记录</h3>

<p>向指定的 <code>/Index/Type</code> 发送 PUT 请求，就可以在 Index 里面新增一条记录。比如，向 <code>/accounts/person</code> 发送请求，就可以新增一条人员记录。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token operator">-</span>X PUT <span class="token string">'localhost:9200/accounts/person/1'</span> <span class="token operator">-</span>d '
<span class="token operator">&gt;</span> <span class="token punctuation">{</span>
<span class="token operator">&gt;</span>   <span class="token string">"user"</span><span class="token punctuation">:</span> <span class="token string">"张三"</span><span class="token punctuation">,</span>
<span class="token operator">&gt;</span>   <span class="token string">"title"</span><span class="token punctuation">:</span> <span class="token string">"工程师"</span><span class="token punctuation">,</span>
<span class="token operator">&gt;</span>   <span class="token string">"desc"</span><span class="token punctuation">:</span> <span class="token string">"数据库管理"</span>
<span class="token operator">&gt;</span> <span class="token punctuation">}</span>'
</code></pre>

<p>服务器返回的 JSON 对象，会给出 Index、Type、Id、Version 等信息。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token punctuation">{</span>
    <span class="token string">"_index"</span><span class="token punctuation">:</span><span class="token string">"accounts"</span><span class="token punctuation">,</span>
    <span class="token string">"_type"</span><span class="token punctuation">:</span><span class="token string">"person"</span><span class="token punctuation">,</span>
    <span class="token string">"_id"</span><span class="token punctuation">:</span><span class="token string">"1"</span><span class="token punctuation">,</span>
    <span class="token string">"_version"</span><span class="token punctuation">:</span><span class="token number">1</span><span class="token punctuation">,</span>
    <span class="token string">"result"</span><span class="token punctuation">:</span><span class="token string">"created"</span><span class="token punctuation">,</span>
    <span class="token string">"_shards"</span><span class="token punctuation">:</span><span class="token punctuation">{</span><span class="token string">"total"</span><span class="token punctuation">:</span><span class="token number">2</span><span class="token punctuation">,</span><span class="token string">"successful"</span><span class="token punctuation">:</span><span class="token number">1</span><span class="token punctuation">,</span><span class="token string">"failed"</span><span class="token punctuation">:</span><span class="token number">0</span><span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token string">"_seq_no"</span><span class="token punctuation">:</span><span class="token number">0</span><span class="token punctuation">,</span>
    <span class="token string">"_primary_term"</span><span class="token punctuation">:</span><span class="token number">1</span>
 <span class="token punctuation">}</span>
</code></pre>

<p>仔细看，会发现请求路径是 <code>/accounts/person/1</code>，最后的 <code>1</code> 是该条记录的 <code>Id</code>。它不一定是数字，任意字符串（比如<code>abc</code>）都可以。</p>

<p>新增记录的时候，也可以不指定 <code>Id</code>，这时要改成 <code>POST</code> 请求。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token operator">-</span>X POST <span class="token string">'localhost:9200/accounts/person'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
  <span class="token string">"user"</span><span class="token punctuation">:</span> <span class="token string">"李四"</span><span class="token punctuation">,</span>
  <span class="token string">"title"</span><span class="token punctuation">:</span> <span class="token string">"工程师"</span><span class="token punctuation">,</span>
  <span class="token string">"desc"</span><span class="token punctuation">:</span> <span class="token string">"系统管理"</span>
<span class="token punctuation">}</span>'
</code></pre>

<p>这个时候，服务器返回的 JSON 对象里面，<code>_id</code> 字段就是一个随机字符串。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token punctuation">{</span>
  <span class="token string">"_index"</span><span class="token punctuation">:</span><span class="token string">"accounts"</span><span class="token punctuation">,</span>
  <span class="token string">"_type"</span><span class="token punctuation">:</span><span class="token string">"person"</span><span class="token punctuation">,</span>
  <span class="token string">"_id"</span><span class="token punctuation">:</span><span class="token string">"A9QxNXEBLRNcEQlvnE1_"</span><span class="token punctuation">,</span>
  <span class="token string">"_version"</span><span class="token punctuation">:</span><span class="token number">1</span><span class="token punctuation">,</span>
  <span class="token string">"result"</span><span class="token punctuation">:</span><span class="token string">"created"</span><span class="token punctuation">,</span>
  <span class="token string">"_shards"</span><span class="token punctuation">:</span><span class="token punctuation">{</span><span class="token string">"total"</span><span class="token punctuation">:</span><span class="token number">2</span><span class="token punctuation">,</span><span class="token string">"successful"</span><span class="token punctuation">:</span><span class="token number">1</span><span class="token punctuation">,</span><span class="token string">"failed"</span><span class="token punctuation">:</span><span class="token number">0</span><span class="token punctuation">}</span><span class="token punctuation">,</span>
  <span class="token string">"_seq_no"</span><span class="token punctuation">:</span><span class="token number">2</span><span class="token punctuation">,</span>
  <span class="token string">"_primary_term"</span><span class="token punctuation">:</span><span class="token number">2</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="查看记录">查看记录</h3>

<p>向 <code>/Index/Type/Id</code> 发出 GET 请求，就可以查看这条记录。</p>

<p>URL 的参数 <code>pretty=true</code> 表示以易读的格式返回。</p>

<p>返回的数据中，<code>found</code> 字段表示查询成功，<code>_source</code> 字段返回原始记录。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token string">'localhost:9200/accounts/person/1?pretty=true'</span>

<span class="token punctuation">{</span>
  <span class="token string">"_index"</span> <span class="token punctuation">:</span> <span class="token string">"accounts"</span><span class="token punctuation">,</span>
  <span class="token string">"_type"</span> <span class="token punctuation">:</span> <span class="token string">"person"</span><span class="token punctuation">,</span>
  <span class="token string">"_id"</span> <span class="token punctuation">:</span> <span class="token string">"1"</span><span class="token punctuation">,</span>
  <span class="token string">"_version"</span> <span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
  <span class="token string">"_seq_no"</span> <span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
  <span class="token string">"_primary_term"</span> <span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
  <span class="token string">"found"</span> <span class="token punctuation">:</span> true<span class="token punctuation">,</span>
  <span class="token string">"_source"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"user"</span> <span class="token punctuation">:</span> <span class="token string">"张三"</span><span class="token punctuation">,</span>
    <span class="token string">"title"</span> <span class="token punctuation">:</span> <span class="token string">"工程师"</span><span class="token punctuation">,</span>
    <span class="token string">"desc"</span> <span class="token punctuation">:</span> <span class="token string">"数据库管理"</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="删除记录">删除记录</h3>

<p>删除记录就是发出 DELETE 请求。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>X DELETE <span class="token string">'localhost:9200/accounts/person/1'</span>
</code></pre>

<h3 id="更新记录">更新记录</h3>

<p>更新记录就是使用 PUT 请求，重新发送一次数据。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token operator">-</span>X PUT <span class="token string">'localhost:9200/accounts/person/1'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
    <span class="token string">"user"</span> <span class="token punctuation">:</span> <span class="token string">"张三"</span><span class="token punctuation">,</span>
    <span class="token string">"title"</span> <span class="token punctuation">:</span> <span class="token string">"工程师"</span><span class="token punctuation">,</span>
    <span class="token string">"desc"</span> <span class="token punctuation">:</span> <span class="token string">"数据库管理，软件开发"</span>
<span class="token punctuation">}</span>'
</code></pre>

<p>可以发现，返回的JSON对象中，记录的 <code>Id</code> 没变，但是版本（<code>version</code>）变化了，操作类型（<code>result</code>）从 <code>created</code> 变成 <code>updated</code>，<code>created</code> 字段变成 <code>false</code>，因为这次不是新建记录。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token punctuation">{</span>
  <span class="token string">"_index"</span><span class="token punctuation">:</span><span class="token string">"accounts"</span><span class="token punctuation">,</span>
  <span class="token string">"_type"</span><span class="token punctuation">:</span><span class="token string">"person"</span><span class="token punctuation">,</span>
  <span class="token string">"_id"</span><span class="token punctuation">:</span><span class="token string">"1"</span><span class="token punctuation">,</span>
  <span class="token string">"_version"</span><span class="token punctuation">:</span><span class="token number">3</span><span class="token punctuation">,</span>
  <span class="token string">"result"</span><span class="token punctuation">:</span><span class="token string">"updated"</span><span class="token punctuation">,</span>
  <span class="token string">"_shards"</span><span class="token punctuation">:</span><span class="token punctuation">{</span><span class="token string">"total"</span><span class="token punctuation">:</span><span class="token number">2</span><span class="token punctuation">,</span><span class="token string">"successful"</span><span class="token punctuation">:</span><span class="token number">1</span><span class="token punctuation">,</span><span class="token string">"failed"</span><span class="token punctuation">:</span><span class="token number">0</span><span class="token punctuation">}</span><span class="token punctuation">,</span>
  <span class="token string">"_seq_no"</span><span class="token punctuation">:</span><span class="token number">3</span><span class="token punctuation">,</span>
  <span class="token string">"_primary_term"</span><span class="token punctuation">:</span><span class="token number">2</span>
<span class="token punctuation">}</span>
</code></pre>

<p>额外补充的是，若要对返回的 JSON 对象格式化，可以执行下述步骤</p>

<ol>
<li>NPM 全局安装<code>json</code>：<code>npm install -g json</code></li>
<li>在上述命令参数后面加上 <code>| json</code></li>
<li>若不想显示 <code>curl</code> 的统计信息，可以添加 <code>-s</code> 参数。</li>
</ol>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token operator">-</span>X PUT <span class="token string">'localhost:9200/accounts/person/1'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
    <span class="token string">"user"</span> <span class="token punctuation">:</span> <span class="token string">"张三"</span><span class="token punctuation">,</span>
    <span class="token string">"title"</span> <span class="token punctuation">:</span> <span class="token string">"工程师"</span><span class="token punctuation">,</span>
    <span class="token string">"desc"</span> <span class="token punctuation">:</span> <span class="token string">"数据库管理，软件开发"</span>
<span class="token punctuation">}</span>'  <span class="token operator">|</span>json
</code></pre>

<h2 id="数据查询">数据查询</h2>

<h3 id="返回所有记录">返回所有记录</h3>

<p>使用 GET 方法，直接请求 <code>/Index/Type/_search</code>，就会返回所有记录。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token string">'localhost:9200/accounts/person/_search'</span>

<span class="token punctuation">{</span>
    <span class="token string">"took"</span><span class="token punctuation">:</span> <span class="token number">629</span><span class="token punctuation">,</span>
    <span class="token string">"timed_out"</span><span class="token punctuation">:</span> false<span class="token punctuation">,</span>
    <span class="token string">"_shards"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"total"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
        <span class="token string">"successful"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
        <span class="token string">"skipped"</span><span class="token punctuation">:</span> <span class="token number">0</span><span class="token punctuation">,</span>
        <span class="token string">"failed"</span><span class="token punctuation">:</span> <span class="token number">0</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token string">"hits"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"total"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
            <span class="token string">"value"</span><span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
            <span class="token string">"relation"</span><span class="token punctuation">:</span> <span class="token string">"eq"</span>
        <span class="token punctuation">}</span><span class="token punctuation">,</span>
        <span class="token string">"max_score"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
        <span class="token string">"hits"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
            <span class="token punctuation">{</span>
                <span class="token string">"_index"</span><span class="token punctuation">:</span> <span class="token string">"accounts"</span><span class="token punctuation">,</span>
                <span class="token string">"_type"</span><span class="token punctuation">:</span> <span class="token string">"person"</span><span class="token punctuation">,</span>
                <span class="token string">"_id"</span><span class="token punctuation">:</span> <span class="token string">"A9QxNXEBLRNcEQlvnE1_"</span><span class="token punctuation">,</span>
                <span class="token string">"_score"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
                <span class="token string">"_source"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
                    <span class="token string">"user"</span><span class="token punctuation">:</span> <span class="token string">"李四"</span><span class="token punctuation">,</span>
                    <span class="token string">"title"</span><span class="token punctuation">:</span> <span class="token string">"工程师"</span><span class="token punctuation">,</span>
                    <span class="token string">"desc"</span><span class="token punctuation">:</span> <span class="token string">"系统管理"</span>
                <span class="token punctuation">}</span>
            <span class="token punctuation">}</span><span class="token punctuation">,</span>
            <span class="token punctuation">{</span>
                <span class="token string">"_index"</span><span class="token punctuation">:</span> <span class="token string">"accounts"</span><span class="token punctuation">,</span>
                <span class="token string">"_type"</span><span class="token punctuation">:</span> <span class="token string">"person"</span><span class="token punctuation">,</span>
                <span class="token string">"_id"</span><span class="token punctuation">:</span> <span class="token string">"1"</span><span class="token punctuation">,</span>
                <span class="token string">"_score"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
                <span class="token string">"_source"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
                    <span class="token string">"user"</span><span class="token punctuation">:</span> <span class="token string">"张三"</span><span class="token punctuation">,</span>
                    <span class="token string">"title"</span><span class="token punctuation">:</span> <span class="token string">"工程师"</span><span class="token punctuation">,</span>
                    <span class="token string">"desc"</span><span class="token punctuation">:</span> <span class="token string">"数据库管理，软件开发"</span>
                <span class="token punctuation">}</span>
            <span class="token punctuation">}</span>
        <span class="token punctuation">]</span>
    <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<p>上面代码中，返回结果的 <code>took</code> 字段表示该操作的耗时（单位为毫秒），<code>timed_out</code> 字段表示是否超时，<code>hits</code> 字段表示命中的记录，里面子字段的含义如下</p>

<ul>
<li><code>total</code>：返回记录数</li>
<li><code>max_score</code>：最高的匹配程度</li>
<li><code>hits</code>：返回的记录组成的数组</li>
</ul>

<h3 id="全文搜索">全文搜索</h3>

<p>Elastic 的查询非常特别，使用自己的<a href="https://www.elastic.co/guide/en/elasticsearch/reference/5.5/query-dsl.html" target="_blank">查询语法</a>，要求 GET 请求带有数据体。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token string">'localhost:9200/accounts/person/_search'</span>  <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
  <span class="token string">"query"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"match"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"desc"</span> <span class="token punctuation">:</span> <span class="token string">"软件"</span> <span class="token punctuation">}</span><span class="token punctuation">}</span>
<span class="token punctuation">}</span>'
</code></pre>

<p>上面代码使用 <a href="https://www.elastic.co/guide/en/elasticsearch/reference/5.5/query-dsl-match-query.html" target="_blank">Match 查询</a>，指定的匹配条件是 <code>desc</code> 字段里面包含"软件"这个词。返回结果如下。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token punctuation">{</span>
    <span class="token string">"took"</span><span class="token punctuation">:</span> <span class="token number">33</span><span class="token punctuation">,</span>
    <span class="token string">"timed_out"</span><span class="token punctuation">:</span> false<span class="token punctuation">,</span>
    <span class="token string">"_shards"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"total"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
        <span class="token string">"successful"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
        <span class="token string">"skipped"</span><span class="token punctuation">:</span> <span class="token number">0</span><span class="token punctuation">,</span>
        <span class="token string">"failed"</span><span class="token punctuation">:</span> <span class="token number">0</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token string">"hits"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
        <span class="token string">"total"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
            <span class="token string">"value"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
            <span class="token string">"relation"</span><span class="token punctuation">:</span> <span class="token string">"eq"</span>
        <span class="token punctuation">}</span><span class="token punctuation">,</span>
        <span class="token string">"max_score"</span><span class="token punctuation">:</span> <span class="token number">1.1978253</span><span class="token punctuation">,</span>
        <span class="token string">"hits"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
            <span class="token punctuation">{</span>
                <span class="token string">"_index"</span><span class="token punctuation">:</span> <span class="token string">"accounts"</span><span class="token punctuation">,</span>
                <span class="token string">"_type"</span><span class="token punctuation">:</span> <span class="token string">"person"</span><span class="token punctuation">,</span>
                <span class="token string">"_id"</span><span class="token punctuation">:</span> <span class="token string">"1"</span><span class="token punctuation">,</span>
                <span class="token string">"_score"</span><span class="token punctuation">:</span> <span class="token number">1.1978253</span><span class="token punctuation">,</span>
                <span class="token string">"_source"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
                    <span class="token string">"user"</span><span class="token punctuation">:</span> <span class="token string">"张三"</span><span class="token punctuation">,</span>
                    <span class="token string">"title"</span><span class="token punctuation">:</span> <span class="token string">"工程师"</span><span class="token punctuation">,</span>
                    <span class="token string">"desc"</span><span class="token punctuation">:</span> <span class="token string">"数据库管理，软件开发"</span>
                <span class="token punctuation">}</span>
            <span class="token punctuation">}</span>
        <span class="token punctuation">]</span>
    <span class="token punctuation">}</span>
<span class="token punctuation">}</span>
</code></pre>

<p>Elastic 默认一次返回10条结果，可以通过 <code>size</code> 字段改变这个设置。还可以通过 <code>from</code> 字段指定位移。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token string">'localhost:9200/accounts/person/_search'</span>  <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
  <span class="token string">"query"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"match"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"desc"</span> <span class="token punctuation">:</span> <span class="token string">"管理"</span> <span class="token punctuation">}</span><span class="token punctuation">}</span><span class="token punctuation">,</span>
  <span class="token string">"size"</span><span class="token punctuation">:</span> <span class="token number">20</span>   <span class="token operator">//</span>定义size
  “<span class="token keyword">from</span>"<span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>   <span class="token operator">//</span> 从位置<span class="token number">1</span>开始（默认是从位置<span class="token number">0</span>开始）
<span class="token punctuation">}</span>'
</code></pre>

<h3 id="逻辑运算">逻辑运算</h3>

<p>如果有多个搜索关键字， Elastic 认为它们是或 (<code>or</code>) 关系。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span>  <span class="token string">'localhost:9200/accounts/person/_search'</span>  <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
  <span class="token string">"query"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"match"</span> <span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"desc"</span> <span class="token punctuation">:</span> <span class="token string">"软件 系统"</span> <span class="token punctuation">}</span><span class="token punctuation">}</span>
<span class="token punctuation">}</span>'
</code></pre>

<p>上面代码搜索的是 <code>软件 or 系统</code>。</p>

<p>如果要执行多个关键词的 <code>and</code> 搜索，必须使用<a href="https://www.elastic.co/guide/en/elasticsearch/reference/5.5/query-dsl-bool-query.html" target="_blank">布尔查询</a>。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">$ curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token string">'localhost:9200/accounts/person/_search'</span>  <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
  <span class="token string">"query"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
    <span class="token string">"bool"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span>
      <span class="token string">"must"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
        <span class="token punctuation">{</span> <span class="token string">"match"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"desc"</span><span class="token punctuation">:</span> <span class="token string">"软件"</span> <span class="token punctuation">}</span> <span class="token punctuation">}</span><span class="token punctuation">,</span>
        <span class="token punctuation">{</span> <span class="token string">"match"</span><span class="token punctuation">:</span> <span class="token punctuation">{</span> <span class="token string">"desc"</span><span class="token punctuation">:</span> <span class="token string">"系统"</span> <span class="token punctuation">}</span> <span class="token punctuation">}</span>
      <span class="token punctuation">]</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">}</span>
<span class="token punctuation">}</span>'
</code></pre>

<h2 id="中文分词设置">中文分词设置</h2>

<h3 id="分词基本概念">分词基本概念</h3>

<p>当一个文档被存储时，ES 会使用分词器从文档中提取出若干词元（<code>token</code>）来支持索引的存储和搜索。ES 内置了很多分词器，但内置的分词器对中文的处理不好。下面通过例子来看内置分词器的处理。在 web 客户端发起如下的一个 REST 请求，对英文语句进行分词</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token operator">-</span>PUT <span class="token string">'localhost:9200/_analyze'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
    <span class="token string">"text"</span><span class="token punctuation">:</span> <span class="token string">"hello world"</span>
<span class="token punctuation">}</span>' <span class="token operator">|</span> json

<span class="token operator">//</span> <span class="token operator">|</span>json 表示对返回结果进行json化展示
</code></pre>

<p>返回结果如下</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">  <span class="token operator">%</span> Total    <span class="token operator">%</span> Received <span class="token operator">%</span> Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
<span class="token number">100</span>   <span class="token number">213</span>  <span class="token number">100</span>   <span class="token number">179</span>  <span class="token number">100</span>    <span class="token number">34</span>  <span class="token number">44750</span>   <span class="token number">8500</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token number">53250</span>
<span class="token punctuation">{</span>
  <span class="token string">"tokens"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"hello"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">0</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">5</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">""</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">0</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"world"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">6</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">11</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">""</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">1</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">]</span>
<span class="token punctuation">}</span>
</code></pre>

<p>上面结果显示 <code>"hello world"</code> 语句被分为两个单词，因为英文天生以空格分隔，自然就以空格来分词，这没有任何问题。</p>

<p>下面我们看一个中文的语句例子，请求 REST 如下</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token operator">-</span>PUT <span class="token string">'localhost:9200/_analyze'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
    <span class="token string">"text"</span><span class="token punctuation">:</span> <span class="token string">"我爱编程"</span>
<span class="token punctuation">}</span>' <span class="token operator">|</span> json

</code></pre>

<p>操作成功后，响应的内容如下</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">  <span class="token operator">%</span> Total    <span class="token operator">%</span> Received <span class="token operator">%</span> Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
<span class="token number">100</span>   <span class="token number">383</span>  <span class="token number">100</span>   <span class="token number">348</span>  <span class="token number">100</span>    <span class="token number">35</span>  <span class="token number">69600</span>   <span class="token number">7000</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token number">76600</span>
<span class="token punctuation">{</span>
  <span class="token string">"tokens"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"我"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">0</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">""</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">0</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"爱"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">""</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">1</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"编"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">3</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">""</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">2</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"程"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">3</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">4</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">""</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">3</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">]</span>
<span class="token punctuation">}</span>
</code></pre>

<p>从结果可以看出，这种分词把每个汉字都独立分开来了，这对中文分词就没有意义了，所以 ES 默认的分词器对中文处理是有问题的。好在有很多不错的第三方的中文分词器，可以很好地和 ES 结合起来使用。在 ES 中，每种分词器（包括内置的、第三方的）都会有个名称。上面默认的操作，其实用的分词器的名称是 <code>standard</code>。下面的请求与前面介绍的请求是等价的，如：</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token operator">-</span>PUT <span class="token string">'localhost:9200/_analyze'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
    <span class="token string">"analyzer"</span><span class="token punctuation">:</span> <span class="token string">"standard"</span><span class="token punctuation">,</span>
    <span class="token string">"text"</span><span class="token punctuation">:</span> <span class="token string">"我爱编程"</span>
<span class="token punctuation">}</span>' <span class="token operator">|</span> json

</code></pre>

<p>当我们换一个分词器处理分词时，只需将 <code>"analyzer"</code> 字段设置相应的分词器名称即可。</p>

<p>ES通过安装插件的方式来支持第三方分词器，对于第三方的中文分词器，比较常用的是中科院 ICTCLAS 的 smartcn 和 IKAnanlyzer 分词器。</p>

<p>下面，对 IKAnanlyzer 分词器（下面简称为 <code>ik</code>）进行介绍。</p>

<h3 id="ik中文分词器的使用">ik中文分词器的使用</h3>

<p>下面进行 <code>ik_max_word</code> 和 <code>ik_smart</code> 分词效果的对比。</p>

<p>可以发现，<strong>对中文“世界如此之大”进行分词，</strong><code>ik_max_word</code> 比 <code>ik_smart</code> 得到的中文词更多，但这样也带来一个问题，使用 <code>ik_max_word</code> 会占用更多的存储空间。</p>

<ul>
<li><code>ik_max_word</code></li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token operator">-</span>PUT <span class="token string">'localhost:9200/_analyze'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
    <span class="token string">"analyzer"</span><span class="token punctuation">:</span> <span class="token string">"ik_max_word"</span><span class="token punctuation">,</span>
    <span class="token string">"text"</span><span class="token punctuation">:</span> <span class="token string">"世界如此之大"</span>
<span class="token punctuation">}</span>' <span class="token operator">|</span> json

<span class="token operator">//</span>echo

  <span class="token operator">%</span> Total    <span class="token operator">%</span> Received <span class="token operator">%</span> Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
<span class="token number">100</span>   <span class="token number">407</span>  <span class="token number">100</span>   <span class="token number">339</span>  <span class="token number">100</span>    <span class="token number">68</span>  <span class="token number">12107</span>   <span class="token number">2428</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token number">14535</span>
<span class="token punctuation">{</span>
  <span class="token string">"tokens"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"世界"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">0</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"CN_WORD"</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">0</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"如此之"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">5</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"CN_WORD"</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">1</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"如此"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">4</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"CN_WORD"</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">2</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"之大"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">4</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">6</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"CN_WORD"</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">3</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">]</span>
<span class="token punctuation">}</span>
</code></pre>

<ul>
<li><code>ik_smart</code></li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">curl <span class="token operator">-</span>H <span class="token string">"Content-Type: application/json"</span> <span class="token operator">-</span>PUT <span class="token string">'localhost:9200/_analyze'</span> <span class="token operator">-</span>d '
<span class="token punctuation">{</span>
    <span class="token string">"analyzer"</span><span class="token punctuation">:</span> <span class="token string">"ik_smart"</span><span class="token punctuation">,</span>
    <span class="token string">"text"</span><span class="token punctuation">:</span> <span class="token string">"世界如此之大"</span>
<span class="token punctuation">}</span>' <span class="token operator">|</span> json

<span class="token operator">//</span>echo

  <span class="token operator">%</span> Total    <span class="token operator">%</span> Received <span class="token operator">%</span> Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
<span class="token number">100</span>   <span class="token number">324</span>  <span class="token number">100</span>   <span class="token number">255</span>  <span class="token number">100</span>    <span class="token number">69</span>  <span class="token number">51000</span>  <span class="token number">13800</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span><span class="token punctuation">:</span><span class="token operator">-</span><span class="token operator">-</span> <span class="token number">64800</span>
<span class="token punctuation">{</span>
  <span class="token string">"tokens"</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"世界"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">0</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"CN_WORD"</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">0</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"如此"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">2</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">4</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"CN_WORD"</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">1</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span>
    <span class="token punctuation">{</span>
      <span class="token string">"token"</span><span class="token punctuation">:</span> <span class="token string">"之大"</span><span class="token punctuation">,</span>
      <span class="token string">"start_offset"</span><span class="token punctuation">:</span> <span class="token number">4</span><span class="token punctuation">,</span>
      <span class="token string">"end_offset"</span><span class="token punctuation">:</span> <span class="token number">6</span><span class="token punctuation">,</span>
      <span class="token string">"type"</span><span class="token punctuation">:</span> <span class="token string">"CN_WORD"</span><span class="token punctuation">,</span>
      <span class="token string">"position"</span><span class="token punctuation">:</span> <span class="token number">2</span>
    <span class="token punctuation">}</span>
  <span class="token punctuation">]</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="常用分词器比较">常用分词器比较</h3>

<p>ES的分词在创建索引（index）后，可以通过 REST 命令来设置，这样后续插入到该索引的数据都会被相应的分词器进行处理。</p>

<p>比较下ik 的 <code>ik_smart</code> 和 <code>ik_max_word</code> 这两个分词器及默认的分词器 <code>standard</code>。一般来说：</p>

<ul>
<li><code>ik_smart</code> 既能满足英文的要求，又更智能更轻量，占用存储最小，所以首推 <code>ik_smart</code></li>
<li><code>standard</code> 对英语支持是最好的，但是对中文是简单暴力每个字建一个反向索引，浪费存储空间而且效果很c差</li>
<li><code>ik_max_word</code> 比 <code>ik_smart</code> 对中文的支持更全面，但是存储上的开销实在太大，不建议使用。</li>
</ul>

<h2 id="总结">总结</h2>

<p>本文主要介绍了ES的基本概念、相关ES数据的操作方法和中文分词的设置，总结了ES的入门使用方法，希望对同样入门使用ES的同学有所帮助。</p>
