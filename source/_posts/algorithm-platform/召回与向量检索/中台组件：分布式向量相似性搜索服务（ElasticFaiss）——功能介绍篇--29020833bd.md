---
title: "中台组件：分布式向量相似性搜索服务（ElasticFaiss）——功能介绍篇"
date: 2022-04-06 11:52:09
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<h2>1     组件基础功能</h2>
<ul><li>向量相似性搜索，提供<strong>RESTful API</strong></li>
<li>支持多种ANN算法：<strong>Faiss</strong>()、<strong>HNSW</strong>、<a href="https://github.com/google-research/google-research/tree/master/scann"><strong>SCANN</strong>()</a></li>
<li>部分算法支持向量<strong>实时写入</strong>和搜索</li>
<li>支持水平扩展，单索引可承载<strong>十亿量级</strong>数据量</li>
<li><strong>高性能</strong>，线上单集群最高QPS峰值超过10w</li>
<li>支持Venus/ Tesla组件<strong>可视化数据管理</strong></li>
<li><b>支持多地部署和自动同步</b></li>
<li><b>支持类SQL语法条件过滤</b></li>
<li><b>模型更新时数据一致性保障</b></li>
<li><b>分布式下数据最终一致性保障</b></li>
<li><b>曝光过滤</b></li>
</ul><p>  项目地址：[内部或本地链接已移除]欢迎加入协同共建！</p>
<p>  Oteam地址：[内部或本地链接已移除]</p>
<p>  快速体验指南：[内部或本地链接已移除]</p>
<h2>2     在线搜索</h2>
<ul><li>支持按指定<strong>向量值搜索</strong>。例如输入一个1024维向量值作为Query搜索TOP K。</li>
<li>支持按指定<strong>向量ID搜索</strong>。如果搜索向量在候选集中，那么可以直接用向量ID作为Query搜索TOP K。系统内部会把ID转化为向量值，免去业务自己的Embedding过程。搜索集和候选集重合的场景可以用这种方式，很多业务不符合这个要求，还是需要自己做搜索集的在线Embedding。</li>
<li>支持<strong>批量搜索</strong>，可以同时搜索多个向量值或者向量ID或者两者的混合，每个输入的Query都会返回对应的TOP K。</li>
<li>单个Query支持<strong>10w以内的召回数量</strong>，召回量越大搜索越慢，业务根据实际需求选择，一般建议1000以内。</li>
<li>支持返回<strong>向量ID，向量值</strong>（默认关闭），<strong>相似度，附加属性</strong>。例如视频搜索，可以把视频的标题，类目等信息放在附加属性里返回，方便业务做下一步处理。</li>
<li>支持按向量ID查询向量值，类似一个分布式KV系统，不过不建议这样用。</li>
<li>支持<strong>范围搜索</strong>：指定一个向量和半径，返回半径内的全部向量。例如地图搜索1KM米范围内所有的店铺，相似人群搜索相似度在一个阈值内的所有人。</li>
<li>排序功能：指定一批向量或者ID排序。</li>
</ul><h2>3     数据管理</h2>
<ul><li><strong>离线数据管理</strong></li>
</ul><p>    实际运营中发现，80%以上业务数据是离线周期性全量更新的，因此我们联合Venus和Tesla平台开发了专用的数据管理组件，让业务在不写代码的情况下方便管理数据。组件分为训练组件和数据导入组件，训练组件用来训练Faiss模型，数据导入组件用于向在线集群更新数据。业务可以通过拖曳组件图标后配置相关参数后定时去执行，完成自动化数据更新的需求。组件在计算框架分类下可以找到。组件帮助文档地址：<a href="http://doc.venus.wsd.com/platform-framework/ef_readme.html">http://doc.venus.wsd.com/platform-framework/ef_readme.html</a></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ce265d3264ad448e0bbc.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/62b7e91f0d707411698a.png"/></p>
<ul><li><strong>实时数据更新</strong></li>
</ul><p>部分业务有实时更新数据需求，由于实现机制的问题，有不少限制：</p>
<ul><li>只有Faiss的IVFx,Flat/IVFx,PQ以及HNSW索引支持实时更新。</li>
<li>性能限制，一般QPS只能达到200左右，且随着数据量的增长性 能会持续下降。原因在于实时构建索引是非常耗时的操作。</li>
</ul><p>为了在有限条件下满足业务实时更新的需求，在实践中一般采用<strong>大索引 + 小索引</strong>方式，大索引存放历史全量数据，可以选择不支持实时更新的高性价比索引，周期性离线更新数据；小索引选择支持实时更新的索引，只保存近1天的数据量，当天的更新请求只在小索引上执行。搜索时同时搜索大小索引，结果再做聚合。目前看点已经实现了此功能的封装，可以联系接入使用。</p>
<h2>4     集群管理</h2>
<p>    绝大部分业务集群由中台专业运维管理，业务无需关心。如果需要了解集群运营情况，可以找运维要自己业务集群的运营数据看板链接，大致内容如下图。可以看到集群的资源利用率，请求QPS，平均耗时，每个节点的状态等。更多的可视化内容在持续建设中。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/273c0866ca5e5a0c00c5.png"/></p>
<p>    如果需要查询集群更加详细的数据，如有哪些索引，数据量，数据分布情况等，我们提供客户端工具ef_cli, 可以通过./ef_cli --help 了解详细功能。</p>
<p>    部分涉密/涉及用户隐私/涉及支付的业务，可以自行部署集群运营，中台提供技术支持。一般建议以容器方式部署，业务可能需要开发部署脚本。</p>
<p>    注意：如果业务占用资源量较少的，机器由中台资源池提供；否则业务可能需要自行提供机器资源。</p>
<h2>5     向量索引类型选择</h2>
<p>不同索引类型在资源消耗、精度、平均耗时上差异很大，需要根据业务实际情况选择，一般遵循以下原则：</p>
<ul><li>如果是<strong>二值化</strong>的向量，就选Faiss二进制索引。</li>
<li>如果数据量很小（百万级以内的），优先选择HNSWLIB，其次是Faiss的IVFx,Flat</li>
<li>百万到千万量级的，选择Faiss的IVFx,Flat或者IVFx,SQ8，对精度要求不高也可以选择IVFx,PQy</li>
<li>亿级以上，优先选择IVFx,SQ8或者IVFx,SQ4，其次选择IVFx,PQy</li>
<li>对性能极致要求，选择VSL索引，需要<strong>业务提供GPU卡</strong>，成本比较高。</li>
</ul><h2>6     向量距离的度量</h2>
<p>支持以下4种距离，业务根据实际需求选择。</p>
<ul><li><strong>内积距离</strong>（inner product），值越大越相似。如果向量做过normalize L2归一化，等价于<strong>cosine距离</strong>（cosine distance）。</li>
<li><strong>欧氏距离</strong>（european distance），值越小越相似。</li>
<li>Faiss二进制索引使用<strong>汉明距离</strong>（Hamming distance），值越小越相似。</li>
</ul><h2>7     客户端</h2>
<p>线下测试建议使用RESTFul API或者客户端工具，线上建议使用HTTP + ProtoBuffer</p>
<table><tbody><tr><td>
<p><strong>客户端</strong></p>
</td>
<td>
<p><strong>性能</strong></p>
</td>
<td>
<p><strong>支持语言</strong></p>
</td>
<td>
<p><strong>外部依赖</strong></p>
</td>
</tr><tr><td>
<p>RESTFul(HTTP + Json)</p>
</td>
<td>
<p>最差</p>
</td>
<td>
<p>几乎所有，包括shell</p>
</td>
<td>
<p>无</p>
</td>
</tr><tr><td>
<p>HTTP + ProtoBuffer</p>
</td>
<td>
<p>较好</p>
</td>
<td>
<p>大部分支持PB即可</p>
</td>
<td>
<p>ProtoBuffer库</p>
</td>
</tr><tr><td>
<p>BRPC(ProtoBuffer)</p>
</td>
<td>
<p>最好</p>
</td>
<td>
<p>最少（C/C++）</p>
</td>
<td>
<p>ProtoBuffer + 第三方库brpc</p>
</td>
</tr><tr><td>
<p>TRPC</p>
</td>
<td>
<p>最好</p>
</td>
<td>
<p>主流语言</p>
</td>
<td>
<p>ProtoBuffer + trpc</p>
</td>
</tr><tr><td>
<p>客户端工具ef_cli</p>
</td>
<td colspan="3">
<p>用于调试和运维</p>
</td>
</tr></tbody></table><p>客户端代码示例：</p>
<ul><li>Golang：[内部或本地链接已移除]</li>
<li>TAF C++：[内部或本地链接已移除]</li>
</ul><h2>8    在用产品</h2>
<ul><li>看点</li>
<li>QQ音乐</li>
<li>视频</li>
<li>新闻</li>
<li>QQ小世界</li>
<li>体育</li>
<li>心悦俱乐部</li>
</ul><h2>9     不支持的功能和缺陷</h2>
<ul><li><strong>不支持数据过期淘汰</strong>。（规划中，即将支持）</li>
<li>“三高”资源消耗：高内存占用（全内存索引）、高CPU消耗（计算密集型服务）、高磁盘占用（存储型服务，可靠服务至少3个副本）。</li>
<li>实时写入性能不高。</li>
</ul><h2>10  业务自助接入流程</h2>
<ul><li>阅读以上介绍后，根据业务实际情况判断是否适合接入。</li>
<li>准备测试数据（或者直接用官方测试数据），在公共测试集群（L5地址是：64674945:65536），使用<a href="http://doc.venus.wsd.com/platform-framework/ef_readme.html">venus组件</a>导入数据。或者通过客户端工具直接导入数据，参见用户指南。</li>
<li>测试没问题以后，正式上线之前，到<a href="http://ef.pcg.com/#/ApplyService">资源申请页面</a>申请正式环境资源。在资源充足的情况下，一个工作日完成集群部署，提供L5地址。</li>
<li>Venus/Tesla上配置数据更新任务，或者根据开放API自主开发管理数据流程。</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f03caefaccb5c43b93cc.png"/></p> 
{% endraw %}
