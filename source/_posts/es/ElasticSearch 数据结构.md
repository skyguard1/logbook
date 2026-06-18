---
title: "ElasticSearch 数据结构"
date: 2022-06-16 22:01:47
categories:
  - es
---

<h1 class="toc-enable" id="488ac5be-48e8-bfb8-b23e-b3aa7e44d1c2">1.&nbsp;ElasticSearch简介</h1>
<p><strong>Elasticsearch</strong>(简称ES)是基于Lucene库实现的开源搜索引擎，其是作为Elastic Stack的核心的分布式搜索和分析引擎，可对所有数据提供近实时的搜索和分析。</p>
<h1 id="58ece4ce-17ca-91c7-e909-1bc87ba0b4bf" class="toc-enable">2.&nbsp;索引(index)</h1>
<p>ES里的索引(<strong>index</strong>)和MYSQL的索引是不一样的，ES官方对索引的释义如下:</p>
<div>
<div style="border-left:5px solid #e2e3e4;padding-left:10px;margin-top:20px;">
<p>An Elasticsearch index is a <span style="text-decoration:underline;"><strong>collection of documents</strong></span> that are related to each other. Elasticsearch stores data as JSON documents.</p>
</div>

<p>即ES中索引是一个相互关联的文档(documents)的集合，会以JSON文档格式来存储数据。而文档(document)是存储在ES索引中的JSON对象，是最基本的存储单位。在ES中是索引通过<strong>倒排索引(Inverted Index)</strong>来实现的，这种结构可以用来快速地进行全文搜索。那有倒排索引，自然就有<strong>正向索引(forward Index)</strong>。首先看看什么是正向索引。</p>
<h2 id="0dfb9bd8-cced-0013-f17a-e3262b11c569" class="toc-enable">2.1.&nbsp;正向索引(forward Index)</h2>
<p>正向索引其实就是一种文档(documents)映射(map)到单词(term)的数据结构，通过正向索引可以直接通过文档然后获取其所包含的单词。</p>
<p>举个例子，假如现在有三个文档</p>
<div class="km_insert_code">
<pre><code>doc1: hello world
doc2: hello golang
doc2: ElasticSearch World</code></pre>

<p>那么对其进行分词后就可以建立如下的正向索引</p>
<table class="md-table" style="margin-left:auto;margin-right:auto;"><thead><tr class="md-end-block"><th style="text-align:center;"><span><span>Document</span></span></th>
<th style="text-align:center;"><span><span>term</span></span></th>
</tr></thead><tbody><tr class="md-end-block"><td><span><span>doc1</span></span></td>
<td><span><span>hello, world</span></span></td>
</tr><tr class="md-end-block"><td>
<p><span><span>doc2</span></span></p>
</td>
<td><span><span>hello, golang</span></span></td>
</tr><tr class="md-end-block md-focus-container"><td><span><span>doc3</span></span></td>
<td><span><span>ElasticSearch , world</span></span></td>
</tr></tbody></table><h2 id="552907d6-dd4b-9565-4c52-243dfc3fc87e" class="toc-enable">2.2.&nbsp;倒排索引(Inverted Index)</h2>
<p>在正向索引中是从文档映射到单词，那么将这种映射关系反过来再稍作修改那就可以得到倒排索引。</p>
<p>倒排索引其实就是一种单词映射到文档的数据结构，我们可以通过某个单词来得到包含了这个单词的文档列表（可以是一个或多个文档）。</p>
<p>同样是上述三个文档，可以建立如下的倒排索引</p>
<table style="margin-left:auto;margin-right:auto;"><tbody><tr><td style="text-align:center;"><strong>term</strong></td>
<td style="text-align:center;"><strong>freq(频率)</strong></td>
<td style="text-align:center;"><strong>Document</strong></td>
</tr><tr><td>hello</td>
<td>2</td>
<td>doc1, doc2</td>
</tr><tr><td>world</td>
<td>2</td>
<td>doc1, doc3</td>
</tr><tr><td>golang</td>
<td>1</td>
<td>doc2</td>
</tr><tr><td>ElasticSearch</td>
<td>1</td>
<td>doc3</td>
</tr></tbody></table><div>
<div style="border-left:5px solid #e2e3e4;padding-left:10px;margin-top:20px;">
<p>注意在倒排索引中不会出现重复的term.</p>
</div>

<p>(1) <strong>Term Dictionary</strong></p>
<p>将文档写入ES时，ES会对其进行分词，这些分出来的一个个分词（这里可能包含一些专有名词，它并不会被分词器分离，比如'Hong Kong'或者自定义的）汇总起来叫做<strong>Term Dictionary</strong>.</p>
<p>(2) <strong>Posting Lists</strong></p>
<p>上面提到ES是基于Lucene库实现的，在ES中索引中的数据会被分成多个分片，而<strong>ES分片(shared)</strong>的底层是Lucene索引，即分片本质上是个<strong>Lucene索引(Lucene Index)</strong>。Lucene中索引文件会被拆分多个子文件，每个子文件是一个<strong>段(segment)</strong>，段都是独立可被搜索的数据集，里面存储着文档，倒排索引等信息，并且会定期合并成一个新的大段(段不变性导致合并，<a href="https://fdv.github.io/running-elasticsearch-fun-profit/003-about-lucene/003-about-lucene.html" target="_blank" rel="noreferrer">[具体见这]</a>)。在每个段中最多可以存储 <em>2^{31}</em> 个文档，并且每个文档都用一个范围在 [0 , 段中文档数(最大<em>2^{31}-1</em>) ]&nbsp; 的数字来唯一标识，即文档ID。</p>
<p style=""><img src="/logbook/images/es/ElasticSearch 数据结构/ce3925d011a8.png" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p></p>
<p style=""><img src="/logbook/images/es/ElasticSearch 数据结构/3bc1f9c10641.png" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p>在倒排索引中每个词都对应着一个文档列表，而文档又有其对应的文档ID。每个分词对应的<strong>文档ID列表</strong>叫做<strong>Posting Lists.</strong>建立了倒排索引后，当需要查询某个单词的时候，就可以直接在<strong>排序</strong>后的term decitionary中<strong>二分查找</strong>，然后再从它的posting list找到想要的文档。这里在posting list中为了快速查找文档ID，posting list中的ID是有序存储的，并且lucene底层采用了<strong>跳表（skiplist）</strong>数据结构进行维护。在联合查询时，就可以遍历多个term的posting list然后利用跳表进行并集操作。</p>
<p>(3) <strong>Term Index</strong></p>
<p>在ES中，若要提高检索速度，就需要把term dicionary搬入内存中，可是当词条数量很多时，将其全部搬进内存将会耗费太多空间。因此ES中对term dicionary建立&nbsp;<span style="text-decoration:underline;"><strong>term index&nbsp;</strong></span>词条索引放入内存中，term index会存储单词的<strong>部分前缀</strong>，利用term index可以快速定位到term dictionary中的对应磁盘block位置，然后再顺序查找。内存中存储term index的数据结构则是<strong>FST(Finite State Transducers)&nbsp;<strong style="font-weight:bold;color:rgba(0,0,0,.75);font-family:&#39;Helvetica Neue&#39;, Helvetica, sans-serif;font-size:16px;font-style:normal;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">有限状态转换器。</strong></strong></p>
<p><strong style=""><img src="/logbook/images/es/ElasticSearch 数据结构/ace69ebd5d35.png" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></strong></p>
<h1 id="146a519b-6cf6-4031-43cb-9ab2370bc4c6" class="toc-enable">3. Finite State Transducers(FST)</h1>
<p><strong>FST(<strong style="font-weight:bold;color:rgba(0,0,0,.75);font-family:&#39;Helvetica Neue&#39;, Helvetica, sans-serif;font-size:16px;font-style:normal;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">有限状态转换器</strong>)</strong>是一种有限状态机，可以将term(字节序)映射到任意输出，即当它读取读取输入时可以产生对应的输出。它的结构如下:</p>
<p style=""><img src="/logbook/images/es/ElasticSearch 数据结构/f937ae933d35.png" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p>在上图中的这个FST中，它将<strong>排序</strong>后的单词 <em>mop</em> , <em>moth</em> , <em>pop</em> , <em>stat</em> , <em>stop</em> 和 <em>top</em> 分别映射到序数0,1,2,3,4,5。当沿着途中箭头遍历时，就可以将路径上的数字进行求和，从而得到对应的序数。举例，当我们遍历stop时，在 '<em>s'</em> 箭头中得到3，在 '<em>o'</em> 箭头中得到1，而其他字母没有标识数字，即0。这样就可以得到stop的排序结果 <em>3+0+1+0=4</em> ​​​。</p>
<p>利用这种数据结构，就可以以 <em>O(len(key))</em> 的时间复杂度去查找一个term对应的值，实现term-value映射。上面提到，这种结构只保存了词典中每个词条的前缀。实际查找时是根据这个前缀快速定位到磁盘block，然后再在这个block查找posting list。</p>
<p>[<a href="http://examples.mikemccandless.com/fst.py?terms=&amp;cmd=Build+it%21" target="_blank" rel="noreferrer">演示工具</a>]</p>
<h1 id="f3578e36-455d-b1ed-17e5-dcb3b733ba34" class="toc-enable">4.&nbsp;Frame Of Reference(FOR)</h1>
<p>posting list中的ID都是有序保存的，这种有序结构可以在ES查询时方便对posting lists进行交集并集查询（比如同时查询包含 term1 和 term2 的文档ID)，而这种有序结构正好可以使用<strong>增量编码(delta-encoding)</strong>来对postling lists进行压缩。增量压缩即是保存除了第一个数字之外其他数字减去前一个数字的结果。</p>
<p>比如现在有个posting lists是 [73, 300, 302, 332, 343, 372] ，那么其增量压缩后得到的列表为 [73,227,2,30,11,29] 。在这里所有增量的大小都在 0~255范围内，这就意味着可以我们只用1 byte来存储每个数字。</p>
<p>在ES中（也可说是在Lucene中），首先会将posting lists先增量编码，然后分成多个块(block)，每个块有256个文档ID。分别在每一个块中计算需要多少个位(bit)来存储里面的每一个数，这个数字由块中最大的数字所需要的位数决定，之后将这个数字保存到每个块的块头。最终就可以用这个头部的位数信息决定要采用多少个位来保存每一个增量数字。这种编码方法就是 <span style="text-decoration:underline;"><strong>Frame Of Reference</strong></span> 。</p>
<p>假设posting lists每个块只有3个文档ID，则过程如下</p>
<p style=""><img src="/logbook/images/es/ElasticSearch 数据结构/f9af5d9dca5e.png" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p>当然这样只是为了能够在磁盘中用更少的空间来保存posting list,实际上使用时还是需要将其恢复成原样。</p>
<h1 id="bd0ca684-011c-baca-26b5-ab1b100b1d01" class="toc-enable">5.&nbsp;Roaring bitmaps</h1>
<p>在ES中查询时经常需要对posting list进行交集并集，即对多个posting list进行交并集计算，同时为了优化查询，在ES中，可以使用过滤器（filter）来进行文档匹配，这种匹配不会影响文档查询的评分(query会)，并且查询结果可以缓存。</p>
<p>为了优化查询，在ES中，可以使用过滤器来进行文档匹配，这种匹配不会影响文档查询的评分(query会)。常用的过滤器查询会被缓存起来放入内存，即过滤器缓存(filter cache)，过滤器缓存会将（filter,segment）映射到其所匹配的<strong>文档列表</strong>，但每个列表可能包含很多个文档ID，若过滤器将文档ID列表（从FOR复原后）全部搬到内存中存储也是一笔不小的空间开销。由于过滤器是缓存在内存中并且是常用的，因此对过滤器缓存进行解压缩时的速度不能太慢，其压缩结构不与加压缩比较费时的FOR相同。</p>
<p><strong><span style="text-decoration:underline;">Roaring bitmaps</span>&nbsp;</strong>结构能满足对缓存过滤器中的文档ID列表的快速解压缩，这是一种将<strong>integer array</strong>(整数数组)和<strong>bitmap</strong>结合起来的结构。首先看一下integer array和bitmap。</p>
<p>(1)&nbsp;<strong>integer array</strong></p>
<p>顾名思义，就是一个保存文档ID的整型(int)数组。其好处就是可以直接通过下标访问，迭代十分方便。但是这种结构却需要用4个字节来保存每一个文档ID，这使得密集的posting list得耗费大量内存，若需要保存100M个文档，则其需要400MB的内存空间。</p>
<p>(2)&nbsp;<strong>bitmap</strong></p>
<p>在位图中将会使用一个位(bit)来代表一个文档ID是否存在。想知道位图中是否包含某个文档ID，只需要找到该ID对应的位置，并判断这个位的值，0代表不存在，1代表存在。对比上述同样100M个文档，若这100M个文档ID都是递增的，我们就只需要100M个bit=12.5MB存储即可。</p>
<p>[0,1,2,...,1000000] =&gt; [1,1,1,1,.....,1,1,1,1,1]</p>
<p>但bitmap也不一定是最佳选择，比如当列表ID只有两个文档[1,1000000]时，使用bitmap存储大小还是12.5MB。而使用integer array只需要8B</p>
<p>(3)&nbsp;<strong>roaring bitmaps</strong></p>
<p><span style="text-decoration:underline;"><strong>roaring bitmaps</strong></span> 则将 <strong>integer array</strong> 和 <strong>bitmap</strong> 结合起来。它会在posting list中的数据按照最高的16个位分块。例如，第一个块中文档ID包含[0-65535] (前16个位均为0),第二个块包含[65536-131071] (前15个位为0最后一个位为1).这样划分后在每一个块中只需要独立编码最低的16个位就足够了，并且块内存储的数字也只会在范围[0-65535]中。</p>
<p>如果这个块中的ID个数小于4096则使用integer array来存储，否则使用bitmap来存储。</p>
<p style=""><img src="/logbook/images/es/ElasticSearch 数据结构/73c46a5f53a6.png" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p>为什么是以4096为分界线，具体原因如下:</p>
<p>由于每个ID的前16个位已经被划分出去了，我们只需要关注最低的16个位，即存储每一个ID只需要两个字节。假设现在一个块内有n个文档ID，这样若使用integer array来保存，则空间大小2n B。则对于bitmap，无论块内有多少个文档ID其都是固定大小（65536个bit）：65536 / 8 = 8192B 。因此当n等于4096时，二者所需要耗费的空间相等，小于4096则integer array占用空间小，大于4096则bitmap占用空间小。利用这种思路，<strong>roaring bitmaps&nbsp;</strong>可以用更少空间缓存过滤器。</p>
<p style=""><img src="/logbook/images/es/ElasticSearch 数据结构/5465630b0447.png" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<h1 id="23cc83bf-9eaa-4a9e-cb98-4a9b7972d5b0" class="toc-enable">6.&nbsp;References</h1>
<p><a target="_blank" href="https://www.elastic.co/cn/blog/frame-of-reference-and-roaring-bitmaps" rel="noreferrer">https://www.elastic.co/cn/blog/frame-of-reference-and-roaring-bitmaps</a></p>
<p><a target="_blank" href="https://learnku.com/elasticsearch/t/46888" rel="noreferrer">https://learnku.com/elasticsearch/t/46888</a></p>
<p><a target="_blank" href="https://xiaoming.net.cn/2020/11/25/Elasticsearch%20%E5%80%92%E6%8E%92%E7%B4%A2%E5%BC%95/" rel="noreferrer">https://xiaoming.net.cn/2020/11/25/Elasticsearch%20%E5%80%92%E6%8E%92%E7%B4%A2%E5%BC%95/</a></p>
<p><a target="_blank" href="https://juejin.cn/post/6844904133162434574" rel="noreferrer">https://juejin.cn/post/6844904133162434574</a></p>
<p><a target="_blank" href="https://segmentfault.com/a/1190000037658997" rel="noreferrer">https://segmentfault.com/a/1190000037658997</a></p>
<p><a target="_blank" href="https://fdv.github.io/running-elasticsearch-fun-profit/003-about-lucene/003-about-lucene.html" rel="noreferrer">https://fdv.github.io/running-elasticsearch-fun-profit/003-about-lucene/003-about-lucene.html</a></p>
<p><a target="_blank" href="https://www.cnblogs.com/richaaaard/p/5226334.html" rel="noreferrer">https://www.cnblogs.com/richaaaard/p/5226334.html</a></p>
<p></p>
<p></p>
<p></p>				</div>
