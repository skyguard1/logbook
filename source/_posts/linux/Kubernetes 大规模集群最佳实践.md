---
title: "Kubernetes 大规模集群最佳实践"
date: 2022-06-17 08:24:01
categories:
  - linux
---

<h1 id="h1-kubernetes-"><a name="Kubernetes 搭建大规模集群最佳实践" class="reference-link"></a><span class="header-link octicon octicon-link"></span>Kubernetes 搭建大规模集群最佳实践</h1><p>Kubernetes 自 v1.6 以来，官方就宣称单集群最大支持 5000 个节点。不过这只是理论上，在具体实践中从 0 到 5000，还是有很长的路要走，需要见招拆招。</p>
<p>官方标准如下：</p>
<ul>
<li>不超过 5000 个节点</li><li>不超过 150000 个 pod</li><li>不超过 300000 个容器</li><li>每个节点不超过 100 个 pod</li></ul>
<h2 id="h2-u5185u6838u8C03u4F18"><a name="内核调优" class="reference-link"></a><span class="header-link octicon octicon-link"></span>内核调优</h2><pre><code># max-file 表示系统级别的能够打开的文件句柄的数量， 一般如果遇到文件句柄达到上限时，会碰到
# "Too many open files" 或者 Socket/File: Can’t open so many files 等错误
fs.file-max=1000000

# 配置 arp cache 大小
# 存在于 ARP 高速缓存中的最少层数，如果少于这个数，垃圾收集器将不会运行。缺省值是 128
net.ipv4.neigh.default.gc_thresh1=1024
# 保存在 ARP 高速缓存中的最多的记录软限制。垃圾收集器在开始收集前，允许记录数超过这个数字 5 秒。缺省值是 512
net.ipv4.neigh.default.gc_thresh2=4096
# 保存在 ARP 高速缓存中的最多记录的硬限制，一旦高速缓存中的数目高于此，垃圾收集器将马上运行。缺省值是 1024
net.ipv4.neigh.default.gc_thresh3=8192
# 以上三个参数，当内核维护的 arp 表过于庞大时候，可以考虑优化

# 允许的最大跟踪连接条目，是在内核内存中 netfilter 可以同时处理的“任务”（连接跟踪条目）
net.netfilter.nf_conntrack_max=10485760
net.netfilter.nf_conntrack_tcp_timeout_established=300
# 哈希表大小（只读）（64位系统、8G内存默认 65536，16G翻倍，如此类推）
net.netfilter.nf_conntrack_buckets=655360

# 每个网络接口接收数据包的速率比内核处理这些包的速率快时，允许送到队列的数据包的最大数目
net.core.netdev_max_backlog=10000

# 默认值: 128 指定了每一个 real user ID 可创建的 inotify instatnces 的数量上限
fs.inotify.max_user_instances=524288
# 默认值: 8192 指定了每个inotify instance相关联的watches的上限
fs.inotify.max_user_watches=524288
</code></pre><h2 id="h2-etcd-"><a name="ETCD 存储" class="reference-link"></a><span class="header-link octicon octicon-link"></span>ETCD 存储</h2><h3 id="h3--iops"><a name="磁盘 IOPS" class="reference-link"></a><span class="header-link octicon octicon-link"></span>磁盘 IOPS</h3><p>ETCD 对磁盘写入延迟非常敏感，对于负载较重的集群，建议使用 500 顺序写入 IOPS，比如 local SSD 或者高性能云盘。可以使用 diskbench 或 fio 测量磁盘实际顺序 IOPS。</p>
<h3 id="h3--io-"><a name="磁盘 IO 优先级" class="reference-link"></a><span class="header-link octicon octicon-link"></span>磁盘 IO 优先级</h3><p>由于 ETCD 必须将数据持久保存到磁盘日志文件中，因此来自其他进程的磁盘活动可能会导致增加写入时间，结果导致 ETCD 请求超时和临时 leader 丢失。当给定高磁盘优先级时，ETCD 服务可以稳定地与这些进程一起运行。</p>
<pre><code>$ sudo ionice -c2 -n0 -p $(pgrep etcd)
</code></pre><h3 id="h3-u4FEEu6539u5B58u50A8u914Du989D"><a name="修改存储配额" class="reference-link"></a><span class="header-link octicon octicon-link"></span>修改存储配额</h3><p>默认 ETCD 空间配额大小为 2G，超过 2G 将不再写入数据。通过给 ETCD 配置 <code>--quota-backend-bytes</code> 参数增大空间配额，最大支持 8G。</p>
<h3 id="h3-u7F51u7EDCu5EF6u8FDF"><a name="网络延迟" class="reference-link"></a><span class="header-link octicon octicon-link"></span>网络延迟</h3><p>如果有大量并发客户端请求 ETCD leader 服务，则可能由于网络拥塞而延迟处理 follower 对等请求。在follower 节点上的发送缓冲区错误消息：</p>
<pre><code>dropped MsgProp to 247ae21ff9436b2d since streamMsg's sending buffer is full
dropped MsgAppResp to 247ae21ff9436b2d since streamMsg's sending buffer is full
</code></pre><p>可以通过在客户端提高 ETCD 对等网络流量优先级来解决这些错误。在 Linux 上，可以使用 tc 对对等流量进行优先级排序：</p>
<pre><code>$ tc qdisc add dev eth0 root handle 1: prio bands 3
$ tc filter add dev eth0 parent 1: protocol ip prio 1 u32 match ip sport 2380 0xffff flowid 1:1
$ tc filter add dev eth0 parent 1: protocol ip prio 1 u32 match ip dport 2380 0xffff flowid 1:1
$ tc filter add dev eth0 parent 1: protocol ip prio 2 u32 match ip sport 2379 0xffff flowid 1:1
$ tc filter add dev eth0 parent 1: protocol ip prio 2 u32 match ip dport 2379 0xffff flowid 1:1
</code></pre><h3 id="h3--kubernetes-events-"><a name="分离 Kubernetes events 存储" class="reference-link"></a><span class="header-link octicon octicon-link"></span>分离 Kubernetes events 存储</h3><p>为了在大规模集群下提高性能，可以将 events 存储在单独的 ETCD 实例中。<br>配置 kube-apiserver：</p>
<pre><code>--etcd-servers="http://etcd1:2379,http://etcd2:2379,http://etcd3:2379" --etcd-servers-overrides="/events#http://etcd4:2379,http://etcd5:2379,http://etcd6:2379"
</code></pre><h2 id="h2-master-"><a name="Master 节点配置" class="reference-link"></a><span class="header-link octicon octicon-link"></span>Master 节点配置</h2><p>GCE 推荐配置：</p>
<ul>
<li>1-5 节点: n1-standard-1</li><li>6-10 节点: n1-standard-2</li><li>11-100 节点: n1-standard-4</li><li>101-250 节点: n1-standard-8</li><li>251-500 节点: n1-standard-16</li><li>超过 500 节点: n1-standard-32</li></ul>
<p>AWS 推荐配置：</p>
<ul>
<li>1-5 节点: m3.medium</li><li>6-10 节点: m3.large</li><li>11-100 节点: m3.xlarge</li><li>101-250 节点: m3.2xlarge</li><li>251-500 节点: c4.4xlarge</li><li>超过 500 节点: c4.8xlarge</li></ul>
<p>对应 CPU 和内存为：</p>
<ul>
<li>1-5 节点: 1vCPU 3.75G内存</li><li>6-10 节点: 2vCPU 7.5G内存</li><li>11-100 节点: 4vCPU 15G内存</li><li>101-250 节点: 8vCPU 30G内存</li><li>251-500 节点: 16vCPU 60G内存</li><li>超过 500 节点: 32vCPU 120G内存</li></ul>
<h2 id="h2-kube-apiserver"><a name="kube-apiserver" class="reference-link"></a><span class="header-link octicon octicon-link"></span>kube-apiserver</h2><h3 id="h3-u9AD8u53EFu7528"><a name="高可用" class="reference-link"></a><span class="header-link octicon octicon-link"></span>高可用</h3><p>设置 <code>--apiserver-count</code> 和 <code>--endpoint-reconciler-type</code>，可使得多个 kube-apiserver 实例加入到 Kubernetes Service 的 endpoints 中，从而实现高可用。又或者，启动多个 kube-apiserver 实例通过外部 LB 做负载均衡。不过由于 TLS 会复用连接，所以上述两种方式都无法做到真正的负载均衡。为了解决这个问题，可以在服务端实现限流器，在请求达到阀值时告知客户端退避或拒绝连接，客户端则配合实现相应负载切换机制。</p>
<h3 id="h3-u8FDEu63A5u6570"><a name="连接数" class="reference-link"></a><span class="header-link octicon octicon-link"></span>连接数</h3><p>设置 <code>--max-requests-inflight</code> 和 <code>--max-mutating-requests-inflight</code>，默认是 200 和 400。</p>
<p>节点数量在 1000 - 3000 之间时，推荐：</p>
<pre><code>--max-requests-inflight=1500
--max-mutating-requests-inflight=500
</code></pre><p>节点数量大于 3000 时，推荐：</p>
<pre><code>--max-requests-inflight=3000
--max-mutating-requests-inflight=1000
</code></pre><h2 id="h2-kube-controller-manager-kube-scheduler"><a name="kube-controller-manager 和 kube-scheduler" class="reference-link"></a><span class="header-link octicon octicon-link"></span>kube-controller-manager 和 kube-scheduler</h2><h3 id="h3-u9AD8u53EFu7528"><a name="高可用" class="reference-link"></a><span class="header-link octicon octicon-link"></span>高可用</h3><p>kube-controller-manager 和 kube-scheduler 是通过 leader election 实现高可用，启用时需要添加以下参数：</p>
<pre><code>--leader-elect=true
--leader-elect-lease-duration=15s
--leader-elect-renew-deadline=10s
--leader-elect-resource-lock=endpoints
--leader-elect-retry-period=2s
</code></pre><h3 id="h3-qps"><a name="QPS" class="reference-link"></a><span class="header-link octicon octicon-link"></span>QPS</h3><p>与 kube-apiserver 通信的 qps 限制，推荐为：</p>
<pre><code>--kube-api-qps=100
</code></pre><h2 id="h2-kube-dns"><a name="kube-dns" class="reference-link"></a><span class="header-link octicon octicon-link"></span>kube-dns</h2><p>设置反亲和，使 kube-dns 分散在集群中：</p>
<pre><code>affinity:
 podAntiAffinity:
   requiredDuringSchedulingIgnoredDuringExecution:
   - weight: 100
     labelSelector:
       matchExpressions:
       - key: k8s-app
         operator: In
         values:
         - kube-dns
     topologyKey: kubernetes.io/hostname
</code></pre><p>以上是配置和方案层面的大集群优化思路。后续有时间，我会专门介绍如何从 Kubernetes 代码层面进行规模和性能优化。</p>
<h2 id="h2-u53C2u8003u6750u6599"><a name="参考材料" class="reference-link"></a><span class="header-link octicon octicon-link"></span>参考材料</h2><ul>
<li><a href="https://kubernetes.io/docs/setup/best-practices/cluster-large/#allowing-minor-node-failure-at-startup" target="_blank">Building large clusters
</a></li><li><a href="https://openai.com/blog/scaling-kubernetes-to-2500-nodes/" target="_blank">Scaling Kubernetes to 2,500 Nodes
</a></li><li><a href="https://feisky.gitbooks.io/kubernetes/practice/big-cluster.html" target="_blank">Kubernetes 大规模集群
</a></li><li><a href="https://www.flftuu.com/2019/03/12/%E5%A4%A7%E8%A7%84%E6%A8%A1%E9%9B%86%E7%BE%A4%E9%85%8D%E7%BD%AE%E4%BC%98%E5%8C%96/" target="_blank">大规模集群配置优化
</a></li></ul>
<p></p><div style="text-align: left;"><img src="/logbook/images/linux/Kubernetes 大规模集群最佳实践/d63c771dce8d.jpg" style="position: relative; z-index: 2;" class="amplify">

<p></p>
<h2 id="h2-u6B64u5904u662Fu5E7Fu544A"><a name="此处是广告" class="reference-link"></a><span class="header-link octicon octicon-link"></span>此处是广告</h2><p>目前开源协同 Kubernetes 正在参加文档大赛，跪求各位打 call 和点赞。<br>具体方法如下：</p>
<blockquote>
<p>点赞，后评论，以 #文档大赛# 开头，留言20字，内容不重复<br>项目地址：<br><a href="https://techmap.oa.com/oteam/8486" target="_blank">https://techmap.oa.com/oteam/8486</a><br><a href="http://iwiki.oa.com/pages/viewpage.action?pageId=10722626" target="_blank">http://iwiki.oa.com/pages/viewpage.action?pageId=10722626</a></p>
</blockquote>
