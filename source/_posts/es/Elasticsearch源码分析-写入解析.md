---
title: "Elasticsearch源码分析-写入解析"
date: 2022-06-16 21:28:22
categories:
  - es
---

<h2>1. 简介</h2>
<p>&nbsp; &nbsp; &nbsp; &nbsp;Elasticsearch(ES)是一个基于Lucene的近实时分布式存储及搜索分析系统，其应用场景广泛，可应用于日志分析、全文检索、结构化数据分析等多种场景，既可作为NoSQL数据库，也可作为搜索引擎。由于ES具备如此强悍的能力，因此吸引了很多公司争相使用，如维基百科、GitHub、Stack Overflow等。</p>
<p>&nbsp; &nbsp; &nbsp; 对于ES的写入，我们主要关心写入的实时性及可靠性。本文将通过源码来探索ES写入的具体流程。</p>
<h2>2. 分布式写入流程</h2>
<p>&nbsp; &nbsp; &nbsp; &nbsp;ES的写入模型参考了微软的<span style="color:#444444;font-family:&#39;Open Sans&#39;, helvetica;font-size:16px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;"><span>&nbsp;</span></span><a href="https://www.microsoft.com/en-us/research/publication/pacifica-replication-in-log-based-distributed-storage-systems/" style="box-sizing:border-box;background-color:#ffffff;color:#00a9e5;text-decoration:none;font-weight:400;font-family:&#39;Open Sans&#39;, helvetica;font-size:16px;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">PacificA</a>协议。写入操作必须在主分片上面完成之后才能被复制到相关的副本分片，如下图所示&nbsp;：</p>
<p style="">&nbsp; &nbsp;</p>
<p>&nbsp; &nbsp; &nbsp; 写操作一般会经历三种节点：协调节点、主分片所在节点、从分片所在节点。上图中NODE1可视为协调节点，协调节点接收到请求后，确定写入的文档属于分片0，于是将请求转发到分片0的主分片所在的节点NODE3，NODE3完成写入后，再将请求转发给分片0所属的从分片所在的节点NODE1和NODE2，待所有从分片写入成功后，NODE3则认为整个写入成功并将结果反馈给协调节点，协调节点再将结果返回客户端。</p>
<p>&nbsp; &nbsp; &nbsp;上述为写入的大体流程，整个流程的具体细节，下面会结合源码进行解析。</p>
<h2>3. 写入源码分析</h2>
<p>&nbsp; &nbsp; &nbsp; ES的写入有两种方式一种是逐个文档写入（index），另一种是多个文档批量写入（bulk）。对于这两种写入方式，ES都会将其转换为bulk写入。本节，我们就以bulk写入为例，根据代码执行主线来分析ES写入的流程。</p>
<h3>3.1 bulk请求分发</h3>
<p>&nbsp; &nbsp; &nbsp; ES对用户请求一般会经过两层处理，一层是Rest层，另一层是Transport层。Rest层主要进行请求参数解析，Transport层则进行实际用户请求处理。在每一层请求处理前都有一次请求分发，如下图所示：</p>
<p style=""></p>
<p>&nbsp; &nbsp; &nbsp; 客户端发送的http请求由HttpServerTransport初步处理后进入RestController模块，在RestController中进行实际的分发过程：</p>
<div>
<pre><code>public void dispatchRequest(RestRequest request, RestChannel channel, ThreadContext threadContext) {
        if (request.rawPath().equals("/favicon.ico")) {
            handleFavicon(request, channel);
            return;
        }
        RestChannel responseChannel = channel;
        try {
            final int contentLength = request.hasContent() ? request.content().length() : 0;
            assert contentLength &gt;= 0 : "content length was negative, how is that possible?";
            final RestHandler handler = getHandler(request);
        ... ...
}

void dispatchRequest(final RestRequest request, final RestChannel channel, final NodeClient client, ThreadContext threadContext,
                         final RestHandler handler) throws Exception {
            ... ...
            final RestHandler wrappedHandler = Objects.requireNonNull(handlerWrapper.apply(handler));
            wrappedHandler.handleRequest(request, channel, client);
            ... ...
        }
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; 从上面的代码可以看出在第一个dispatchRequest中，会根据request找到其对应的handler，然后在第二个dispatchRequest中会调用handler的handleRequest方法处理请求。那么getHandler是如何根据请求找到对应的handler的呢？这块的逻辑如下：</p>
<div>
<pre><code>public void registerHandler(RestRequest.Method method, String path, RestHandler handler) {
        PathTrie&lt;RestHandler&gt; handlers = getHandlersForMethod(method);
        if (handlers != null) {
            handlers.insert(path, handler);
        } else {
            throw new IllegalArgumentException("Can't handle [" + method + "] for path [" + path + "]");
        }
}

private RestHandler getHandler(RestRequest request) {
        String path = getPath(request);
        PathTrie&lt;RestHandler&gt; handlers = getHandlersForMethod(request.method());
        if (handlers != null) {
            return handlers.retrieve(path, request.params());
        } else {
            return null;
        }
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; &nbsp;ES会通过RestController的registerHandler方法，提前把handler注册到对应http请求方法（GET、PUT、POST、DELETE等）的handlers列表。这样用户请求到达时，就可以通过RestController的getHandler方法，并根据http请求方法和路径取出对应的handler。对于bulk操作，其请求对应的handler是RestBulkAction，该类会在其构造函数中将其注册到RestController，代码如下：</p>
<div>
<pre><code>public RestBulkAction(Settings settings, RestController controller) {
        super(settings);
        controller.registerHandler(POST, "/_bulk", this);
        controller.registerHandler(PUT, "/_bulk", this);
        controller.registerHandler(POST, "/{index}/_bulk", this);
        controller.registerHandler(PUT, "/{index}/_bulk", this);
        controller.registerHandler(POST, "/{index}/{type}/_bulk", this);
        controller.registerHandler(PUT, "/{index}/{type}/_bulk", this);
        this.allowExplicitIndex = MULTI_ALLOW_EXPLICIT_INDEX.get(settings);
}</code></pre>

<p>&nbsp; &nbsp;&nbsp;&nbsp; RestBulkAction会将RestRequest解析并转化为BulkRequest，然后再对BulkRequest做处理，这块的逻辑在prepareRequest方法中，部分代码如下：</p>
<div>
<pre><code>    public RestChannelConsumer prepareRequest(final RestRequest request, final NodeClient client) throws IOException {
       // 根据RestRquest构建BulkRequest
       ... ...
       // 处理bulkRequest
        return channel -&gt; client.bulk(bulkRequest, new RestStatusToXContentListener&lt;&gt;(channel));
    }</code></pre>

<p>&nbsp; &nbsp; &nbsp; NodeClient在处理BulkRequest请求时，会将请求的action转化为对应Transport层的action，然后再由Transport层的action来处理BulkRequest，action转化的代码如下：</p>
<div>
<pre><code>    public &lt;  Request extends ActionRequest, Response extends ActionResponse &gt;
Task executeLocally(GenericAction&lt;Request, Response&gt; action, Request request, TaskListener&lt;Response&gt; listener) {
        return transportAction(action).execute(request, listener);
    }

    private &lt;    Request extends ActionRequest,Response extends ActionResponse &gt;
           TransportAction&lt;Request, Response&gt; transportAction(GenericAction&lt;Request, Response&gt; action) {
       ... ...
        // actions是个action到transportAction的映射，这个映射关系是在节点启动时初始化的
        TransportAction&lt;Request, Response&gt; transportAction = actions.get(action);
        ... ...
        return transportAction;
    }</code></pre>

<p>&nbsp; &nbsp; &nbsp; TransportAction会调用一个请求过滤链来处理请求，如果相关的插件定义了对该action的过滤处理，则先会执行插件的处理逻辑，然后再进入TransportAction的处理逻辑，过滤链的处理逻辑如下：</p>
<div>
<pre><code>public void proceed(Task task, String actionName, Request request, ActionListener&lt;Response&gt; listener) {
    int i = index.getAndIncrement();
    try {
        if (i &lt; this.action.filters.length) {
            this.action.filters[i].apply(task, actionName, request, listener, this); // 应用插件的逻辑
        } else if (i == this.action.filters.length) {
            this.action.doExecute(task, request, listener);  // 执行TransportAction的处理逻辑
        } else ... ...
    } catch(Exception e) { ... ... }
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; 对于Bulk请求，这里的TransportAction对应的具体对象是TransportBulkAction的实例，到此，Rest层转化为Transport层的流程完成，下节将详细介绍TransportBulkAction的处理逻辑。</p>
<p><span style="font-size:19px;font-weight:bolder;">3.2 写入步骤</span></p>
<h3>3.2.1 创建index</h3>
<p>&nbsp; &nbsp; &nbsp; 如果bulk写入时，index未创建则es会自动创建出对应的index，处理逻辑在TransportBulkAction的<span style="color:#444444;font-family:&#39;Helvetica Neue&#39;, Helvetica, Tahoma, Arial, &#39;Microsoft Yahei&#39;, &#39;微软雅黑&#39;, &#39;Hiragino Sans GB&#39;, &#39;PingFang SC&#39;, STHeiTi, sans-serif;font-size:16px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;">doExecute方法中：</span></p>
<div>
<pre><code>for (String index : indices) {
    boolean shouldAutoCreate;
    try {
        shouldAutoCreate = shouldAutoCreate(index, state);
    } catch (IndexNotFoundException e) {
        shouldAutoCreate = false;
        indicesThatCannotBeCreated.put(index, e);
    }
    if (shouldAutoCreate) {
        autoCreateIndices.add(index);
    }
}
...&nbsp;...
for (String index : autoCreateIndices) {
 createIndex(index, bulkRequest.timeout(), new ActionListener&lt;CreateIndexResponse&gt;() {
   ... ...
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; &nbsp;我们可以看到，在for循环中，会遍历bulk的所有index，然后检查index是否需要自动创建，对于不存在的index，则会加入到自动创建的集合中，然后会调用createIndex方法创建index。index的创建由master来把控，master会根据分片分配和均衡的算法来决定在哪些data node上创建index对应的shard，然后将信息同步到data node上，由data node来执行具体的创建动作。index创建的具体流程在后面的文章中将会做分析，这里不展开介绍了。</p>
<h3>3.2.2 协调节点处理并转发请求</h3>
<p>&nbsp; &nbsp; &nbsp; 创建完index后，index的各shard已在数据节点上建立完成，接着协调节点将会转发写入请求到文档对应的primary shard。协调节点处理Bulk请求转发的入口为executeBulk方法：</p>
<div>
<pre><code>void executeBulk(Task task, final BulkRequest bulkRequest, final long startTimeNanos, final ActionListener&lt;BulkResponse&gt; listener,
        final AtomicArray&lt;BulkItemResponse&gt; responses, Map&lt;String, IndexNotFoundException&gt; indicesThatCannotBeCreated) {
    new BulkOperation(task, bulkRequest, listener, responses, startTimeNanos, indicesThatCannotBeCreated).run();
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; 真正的执行逻辑在BulkOperation的doRun方法中，首先，遍历BulkRequest的所有子请求，然后根据请求的操作类型执行相应的逻辑，对于写入请求，会首先根据IndexMetaData信息，为每条写入请求IndexRequest生成路由信息，并在process过程中按需生成_id字段：&nbsp;</p>
<div>
<pre><code>for (int i = 0; i &lt; bulkRequest.requests.size(); i++) {
    DocWriteRequest docWriteRequest = bulkRequest.requests.get(i);
    ... ...
    Index concreteIndex = concreteIndices.resolveIfAbsent(docWriteRequest);
    try {
        switch (docWriteRequest.opType()) {
            case CREATE:
            case INDEX:
                ... ...
                indexRequest.resolveRouting(metaData); // 根据metaData对indexRequest的routing赋值
                indexRequest.process(mappingMd, allowIdGeneration, concreteIndex.getName()); // 这里，如果用户没有指定doc id，则会自动生成
                break;
            ... ...
        }
    } catch (... ...) { ... ... }
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; 然后根据每个IndexRequest请求的路由信息（如果写入时未指定路由，则es默认使用doc id作为路由）得到所要写入的目标shard id，并将DocWriteRequest封装为BulkItemRequest且添加到对应shardId的请求列表中。代码如下：</p>
<div>
<pre><code>for (int i = 0; i &lt; bulkRequest.requests.size(); i++) {
  DocWriteRequest request = bulkRequest.requests.get(i); // 从bulk请求中得到每个doc写入请求
  // 根据路由，找出doc写入的目标shard id
  ShardId shardId = clusterService.operationRouting().indexShards(clusterState, concreteIndex, request.id(), request.routing()).shardId();
  // requestsByShard的key是shard id，value是对应的单个doc写入请求（会被封装成BulkItemRequest）的集合
  List&lt;BulkItemRequest&gt; shardRequests = requestsByShard.computeIfAbsent(shardId, shard -&gt; new ArrayList&lt;&gt;());
  shardRequests.add(new BulkItemRequest(i, request));
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; 上一步已经找出每个shard及其所需执行的doc写入请求列表的对应关系，这里就相当于将请求按shard进行了拆分，接下来会将每个shard对应的所有请求封装为BulkShardRequest并交由TransportShardBulkAction来处理：</p>
<div>
<pre><code>for (Map.Entry&lt;ShardId, List&lt;BulkItemRequest&gt;&gt; entry : requestsByShard.entrySet()) {
    final ShardId shardId = entry.getKey();
    final List&lt;BulkItemRequest&gt; requests = entry.getValue();
    // 对每个shard id及对应的BulkItemRequest集合，封装为一个BulkShardRequest
    BulkShardRequest bulkShardRequest = new BulkShardRequest(shardId, bulkRequest.getRefreshPolicy(),
            requests.toArray(new BulkItemRequest[requests.size()]));
    shardBulkAction.execute(bulkShardRequest, new ActionListener&lt;BulkShardResponse&gt;() {
       ... ...
    });
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; 执行逻辑最终会进入到doRun方法中，这里会通过ClusterState获取到primary shard的路由信息，然后得到primay shard所在的node，如果node为当前协调节点则直接将请求发往本地，否则发往远端：</p>
<div>
<pre><code>protected void doRun() {
    ......
    final ShardRouting primary = primary(state); // 获取primary shard的路由信息
    ... ...
    // 得到primary所在的node
    final DiscoveryNode node = state.nodes().get(primary.currentNodeId());
    if (primary.currentNodeId().equals(state.nodes().getLocalNodeId())) {
        // 如果primary所在的node和primary所在的node一致，则直接在本地执行
        performLocalAction(state, primary, node, indexMetaData);
    } else {
        // 否则，发送到远程node执行
        performRemoteAction(state, primary, node);
    }
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; 在performAction方法中，会调用TransportService的sendRequest方法，将请求发送出去。如果对端返回异常，比如对端节点故障或者primary shard挂了，对于这些异常，协调节点会有重试机制，重试的逻辑为等待获取最新的集群状态，然后再根据集群的最新状态（通过集群状态可以拿到新的primary shard信息）重新执行上面的doRun逻辑；如果在等待集群状态更新时超时，则会执行最后一次重试操作（执行doRun）。这块的代码如下：</p>
<div>
<pre><code>void retry(Exception failure) {
    assert failure != null;
    if (observer.isTimedOut()) {
        // 超时时已经做过最后一次尝试，这里将不会重试了
        finishAsFailed(failure);
        return;
    }
    setPhase(task, "waiting_for_retry");
    request.onRetry();
    request.primaryTerm(0L);
    observer.waitForNextChange(new ClusterStateObserver.Listener() {
        @Override
        public void onNewClusterState(ClusterState state) {
            run(); // 会调用doRun
        }
        @Override
        public void onClusterServiceClose() {
            finishAsFailed(new NodeClosedException(clusterService.localNode()));
        }
        @Override
        public void onTimeout(TimeValue timeout) { // 超时，做最后一次重试
            run();  // 会调用doRun
        }
    });
}</code></pre>

<h3>3.2.3 primary node</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; primary所在的node收到协调节点发过来的写入请求后，开始正式执行写入的逻辑，写入执行的入口是在ReplicationOperation类的execute方法，该方法中执行的两个关键步骤是，首先写主shard，如果主shard写入成功，再将写入请求发送到从shard所在的节点。</p>
<div>
<pre><code>public void execute() throws Exception {
    ......
    // 关键，这里开始执行写primary shard
    primaryResult = primary.perform(request);
    final ReplicaRequest replicaRequest = primaryResult.replicaRequest();
    if (replicaRequest != null) {
        ......
        // 关键步骤，写完primary后这里转发请求到replicas
        performOnReplicas(replicaRequest, shards);
    }
    successfulShards.incrementAndGet();
    decPendingAndFinishIfNeeded();
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; 下面，我们来看写primary的关键代码，写primary入口函数为TransportShardBulkAction.shardOperationOnPrimary:</p>
<div>
<pre><code>public WritePrimaryResult&lt;BulkShardRequest, BulkShardResponse&gt; shardOperationOnPrimary(
            BulkShardRequest request, IndexShard primary) throws Exception {
        ... ...
        Translog.Location location = null;
        for (int requestIndex = 0; requestIndex &lt; request.items().length; requestIndex++) {
            if (isAborted(request.items()[requestIndex].getPrimaryResponse()) == false) {
                location = executeBulkItemRequest(metaData, primary, request, preVersions, preVersionTypes, location, requestIndex);
            }
        }
      ... ...
  }</code></pre>

<p>&nbsp; &nbsp; &nbsp; 写主时，会遍历一个bulk任务，逐个执行具体的写入请求，ES调用InternalEngine.Index将数据写入lucene并会将整个写入操作命令添加到translog，如下所示：</p>
<div>
<pre><code>final IndexResult indexResult;
if (plan.earlyResultOnPreFlightError.isPresent()) {
    indexResult = plan.earlyResultOnPreFlightError.get();
    assert indexResult.hasFailure();
} else if (plan.indexIntoLucene) {
    // 将数据写入lucene，最终会调用lucene的文档写入接口
    indexResult = indexIntoLucene(index, plan);
} else {
    assert index.origin() != Operation.Origin.PRIMARY;
    indexResult = new IndexResult(plan.versionForIndexing, plan.currentNotFoundOrDeleted);
}
if (indexResult.hasFailure() == false &amp;&amp;
    plan.indexIntoLucene &amp;&amp; // if we didn't store it in lucene, there is no need to store it in the translog
    index.origin() != Operation.Origin.LOCAL_TRANSLOG_RECOVERY) {
    Translog.Location location =
        translog.add(new Translog.Index(index, indexResult)); // 写translog
    indexResult.setTranslogLocation(location);
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; &nbsp;从以上代码可以看出，ES的写入操作是先写lucene，将数据写入到lucene内存后再写translog，这里和传统的<span style="color:#222222;font-family:sans-serif;font-size:15.008px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;">WAL先写日志后写内存有所区别。ES之所以先写lucene后写log<span style="color:#1a1a1a;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;Helvetica Neue&#39;, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-size:medium;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;">主要原因大概是写入Lucene时，Lucene会再对数据进行一些检查，有可能出现写入Lucene失败的情况。如果先写translog，那么就要处理写入translog成功但是写入Lucene一直失败的问题，所以ES采用了先写Lucene的方式。</span></span></p>
<p><span style="color:#222222;font-family:sans-serif;font-size:15.008px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;"><span style="color:#1a1a1a;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;Helvetica Neue&#39;, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-size:medium;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;">&nbsp; &nbsp; &nbsp; 在写完primary后，会继续写replicas，</span></span><span style="color:#222222;font-family:sans-serif;font-size:15.008px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;"><span style="color:#1a1a1a;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;Helvetica Neue&#39;, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-size:medium;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;">接下来需要将请求转发到从节点上，如果replica shard未分配，则直接忽略；如果replica shard正在搬迁数据到其他节点，则将请求转发到搬迁的目标shard上，否则，转发到replica shard。这块代码如下：</span></span></p>
<div>
<pre><code>private void performOnReplicas(ReplicaRequest replicaRequest, List&lt;ShardRouting&gt; shards) {
    final String localNodeId = primary.routingEntry().currentNodeId();
    // If the index gets deleted after primary operation, we skip replication
    for (final ShardRouting shard : shards) {
        if (executeOnReplicas == false || shard.unassigned()) {
            if (shard.primary() == false) {
                totalShards.incrementAndGet();
            }
            continue;
        }
        if (shard.currentNodeId().equals(localNodeId) == false) {
            performOnReplica(shard, replicaRequest);
        }
        if (shard.relocating() &amp;&amp; shard.relocatingNodeId().equals(localNodeId) == false) {
            performOnReplica(shard.getTargetRelocatingShard(), replicaRequest);
        }
    }
}</code></pre>

<p>&nbsp; &nbsp; &nbsp; &nbsp;performOnReplica方法会将请求转发到目标节点，如果出现异常，如对端节点挂掉、shard写入失败等，对于这些异常，primary认为该replica shard发生故障不可用，将会向master汇报并移除该replica。这块的代码如下：</p>
<div>
<pre><code>private void performOnReplica(final ShardRouting shard, final ReplicaRequest replicaRequest) {

    totalShards.incrementAndGet();
    pendingActions.incrementAndGet();
    replicasProxy.performOn(shard, replicaRequest, new ActionListener&lt;TransportResponse.Empty&gt;() {
        @Override
        public void onResponse(TransportResponse.Empty empty) {
            successfulShards.incrementAndGet();
            decPendingAndFinishIfNeeded();
        }
        @Override
        public void onFailure(Exception replicaException) {
            if (TransportActions.isShardNotAvailableException(replicaException)) {
                decPendingAndFinishIfNeeded();
            } else {
                RestStatus restStatus = ExceptionsHelper.status(replicaException);
                shardReplicaFailures.add(new ReplicationResponse.ShardInfo.Failure(
                    shard.shardId(), shard.currentNodeId(), replicaException, restStatus, false));
                replicasProxy.failShard(shard, message, replicaException,
                    ReplicationOperation.this::decPendingAndFinishIfNeeded,
                    ReplicationOperation.this::onPrimaryDemoted,
                    throwable -&gt; decPendingAndFinishIfNeeded()
                );
            }
        }
    });
}</code></pre>

<p><span style="color:#222222;font-family:sans-serif;font-size:15.008px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;"><span style="color:#1a1a1a;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;Helvetica Neue&#39;, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-size:medium;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;">&nbsp; &nbsp; &nbsp; &nbsp;replica的写入逻辑和primary类似，这里不再具体介绍。为了防止primary挂掉后不丢数据，ES会等待所有replicas都写入成功后再将结果反馈给客户端。因此，写入耗时会由耗时最长的replica决定。</span></span><span style="color:#222222;font-family:sans-serif;font-size:15.008px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;"><span style="color:#1a1a1a;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;Helvetica Neue&#39;, &#39;PingFang SC&#39;, &#39;Microsoft YaHei&#39;, &#39;Source Han Sans SC&#39;, &#39;Noto Sans CJK SC&#39;, &#39;WenQuanYi Micro Hei&#39;, sans-serif;font-size:medium;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;">至此，ES的整个写入流程已解析完毕。</span></span></p>
<h2>4. 小结</h2>
<p>&nbsp; &nbsp; &nbsp; &nbsp;本文主要分析了ES分布式框架写入的主体流程，对其中的很多细节未做详细剖析，后面会通过一些文章对写入涉及的细节做具体分析，<span style="color:#444444;font-family:&#39;Helvetica Neue&#39;, Helvetica, Tahoma, Arial, &#39;Microsoft Yahei&#39;, &#39;微软雅黑&#39;, &#39;Hiragino Sans GB&#39;, &#39;PingFang SC&#39;, STHeiTi, sans-serif;font-size:16px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;display:inline !important;float:none;">欢迎大家一起交流讨论。</span></p>				</div>
