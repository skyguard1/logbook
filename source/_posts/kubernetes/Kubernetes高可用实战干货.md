---
title: "Kubernetes高可用实战干货"
date: 2022-06-12 11:03:52
categories:
  - kubernetes
---

<p>在企业生产环境，Kubernetes高可用是一个必不可少的特性，其中最通用的场景就是如何在Kubernetes集群宕机一个节点的情况下保障服务依旧可用</p>

<p>本文就针对这个场景下在实现集群和应用高可用过程中遇到的各种问题进行一个梳理和总结</p>

<h2 id="整体架构">整体架构</h2>

<p>本文描述的高可用方案对应架构如下：</p>

<ul>
<li>control plane node</li>
</ul>

<p>管理节点采用kubeadm搭建的3节点标准高可用方案(<a href="https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ha-topology/#stacked-etcd-topology" target="_blank">Stacked etcd topology</a>)：</p>

<p style=""><img src="./Kubernetes高可用实战干货 - CSIG新人专区（已转至云知） - KM平台_files/cos-file-url(2)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>该方案中，所有管理节点都部署kube-apiserver，kube-controller-manager，kube-scheduler，以及etcd等组件；kube-apiserver均与本地的etcd进行通信，etcd在三个节点间同步数据；而kube-controller-manager和kube-scheduler也只与本地的kube-apiserver进行通信(或者通过LB访问)</p>

<p>kube-apiserver前面顶一个LB；work节点kubelet以及kube-proxy组件对接LB访问apiserver</p>

<p>在这种架构中，如果其中任意一个master节点宕机了，由于kube-controller-manager以及kube-scheduler基于<a href="https://github.com/kubernetes/client-go/tree/master/examples/leader-election" target="_blank">Leader Election Mechanism</a>实现了高可用，可以认为管理集群不受影响，相关组件依旧正常运行(在分布式锁释放后)</p>

<ul>
<li>work node</li>
</ul>

<p>工作节点上部署应用，应用按照<a href="https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#more-practical-use-cases" target="_blank">反亲和</a>部署多个副本，使副本调度在不同的work node上，这样如果其中一个副本所在的母机宕机了，理论上通过Kubernetes service可以把请求切换到另外副本上，使服务依旧可用</p>

<h2 id="网络">网络</h2>

<p>针对上述架构，我们分析一下实际环境中节点宕机对网络层面带来的影响</p>

<h3 id="service backend剔除">service backend剔除</h3>

<p>正如上文所述，工作节点上应用会按照反亲和部署。这里我们讨论最简单的情况：例如一个nginx服务，部署了两个副本，分别落在work node1和work node2上</p>

<p>集群中还部署了依赖nginx服务的应用A，如果某个时刻work node1宕机了，此时应用A访问nginx service会有问题吗？</p>

<p>这里答案是会有问题。因为service不会马上剔除掉宕机上对应的nginx pod，同时由于service常用的<a href="https://kubernetes.io/docs/concepts/services-networking/service/#proxy-mode-iptables" target="_blank">iptables代理模式</a>没有实现<a href="https://kubernetes.io/docs/concepts/services-networking/service/#proxy-mode-iptables" target="_blank">retry with another backend</a>特性，所以在一段时间内访问会出现间歇性问题(如果请求轮询到挂掉的nginx pod上)，也就是说会存在一个访问失败间隔期</p>

<p style=""><img src="./Kubernetes高可用实战干货 - CSIG新人专区（已转至云知） - KM平台_files/cos-file-url(3)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>这个间隔期取决于service对应的endpoint什么时候踢掉宕机的pod。之后，kube-proxy会watch到endpoint变化，然后更新对应的iptables规则，使service访问后端列表恢复正常(也就是踢掉该pod)</p>

<p>要理解这个间隔，我们首先需要弄清楚Kubernetes节点心跳的概念：</p>

<p>每个node在kube-node-lease namespace下会对应一个Lease object，kubelet每隔node-status-update-frequency时间(默认10s)会更新对应node的Lease object</p>

<p>node-controller会每隔node-monitor-period时间(默认5s)检查Lease object是否更新，如果超过node-monitor-grace-period时间(默认40s)没有发生过更新，则认为这个node不健康，会更新NodeStatus(ConditionUnknown)。如果这样的状态在这之后持续了一段时间(默认5mins)，则会驱逐(evict)该node上的pod</p>

<p>对于母机宕机的场景，node controller在node-monitor-grace-period时间段没有观察到心跳的情况下，会更新NodeStatus(ConditionUnknown)，之后endpoint controller会从endpoint backend中踢掉该母机上的所有pod，最终服务访问正常，请求不会落在挂掉的pod上</p>

<p>也就是说在母机宕机后，在node-monitor-grace-period间隔内访问service会有间歇性问题，我们可以通过调整相关参数来缩小这个窗口期，如下：</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token punctuation">(</span>kubelet<span class="token punctuation">)</span>node<span class="token operator">-</span>status<span class="token operator">-</span>update<span class="token operator">-</span>frequency：default 10s
<span class="token punctuation">(</span>kube<span class="token operator">-</span>controller<span class="token operator">-</span>manager<span class="token punctuation">)</span>node<span class="token operator">-</span>monitor<span class="token operator">-</span>period：default 5s
<span class="token punctuation">(</span>kube<span class="token operator">-</span>controller<span class="token operator">-</span>manager<span class="token punctuation">)</span>node<span class="token operator">-</span>monitor<span class="token operator">-</span>grace<span class="token operator">-</span>period：default 40s
<span class="token operator">-</span> Amount of time which we allow running Node to be unresponsive before marking it unhealthy<span class="token punctuation">.</span> Must be N times more than kubelet's nodeStatusUpdateFrequency<span class="token punctuation">,</span> where N means number of retries allowed <span class="token keyword">for</span> kubelet to post node status<span class="token punctuation">.</span>
<span class="token operator">-</span> Currently nodeStatusUpdateRetry <span class="token keyword">is</span> constantly <span class="token builtin">set</span> to <span class="token number">5</span> <span class="token keyword">in</span> kubelet<span class="token punctuation">.</span>go
</code></pre>

<h3 id="连接复用-长连接-">连接复用(长连接)</h3>

<p>对于使用长连接访问的应用来说(默认使用都是tcp长连接，无论HTTP/2还是HTTP/1)，在没有设置合适请求timeout参数的情况下可能会出现15mins的超时问题，详情见<a href="https://duyanghao.github.io/kubernetes-ha-http-keep-alive-bugs/" target="_blank">Kubernetes Controller高可用诡异的15mins超时</a>。解决方案如下：</p>

<blockquote>
<p>通过上面的分析，可以知道是TCP的ARQ机制导致了Controller在母机宕机后15mins内一直超时重试，超时重试失败后，tcp socket关闭，应用重新创建连接</p>
</blockquote>

<blockquote>
<p>这个问题本质上不是Kubernetes的问题，而是应用在复用tcp socket(长连接)时没有考虑设置超时，导致了母机宕机后，tcp socket没有及时关闭，服务依旧使用失效连接导致异常</p>
</blockquote>

<blockquote>
<p>要解决这个问题，可以从两方面考虑：</p>
</blockquote>

<blockquote>
<ul>
<li>应用层使用超时设置或者健康检查机制，从上层保障连接的健康状态 - 作用于该应用</li>
<li>底层调整TCP ARQ设置(/proc/sys/net/ipv4/tcp_retries2)，缩小超时重试周期，作用于整个集群</li>
</ul>
</blockquote>

<blockquote>
<p>由于应用层的超时或者健康检查机制无法使用统一的方案，这里只介绍如何采用系统配置的方式规避无效连接，如下：</p>
</blockquote>

<blockquote>
<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash"><span class="token comment"># 0.2+0.4+0.8+1.6+3.2+6.4+12.8+25.6+51.2+102.4 = 222.6s</span>
$ <span class="token builtin class-name">echo</span> <span class="token number">9</span> <span class="token operator">&gt;</span> /proc/sys/net/ipv4/tcp_retries2
</code></pre>
</blockquote>

<blockquote>
<p>另外对于推送类的服务，比如Watch，在母机宕机后，可以通过tcp keepalive机制来关闭无效连接(这也是上面测试cluster-coredns-controller时其中一个连接5分钟(30+30*9=300s)断开的原因)：</p>
</blockquote>

<blockquote>
<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash"><span class="token comment"># 30 + 30*5 = 180s</span>
$ <span class="token builtin class-name">echo</span> <span class="token number">30</span> <span class="token operator">&gt;</span>  /proc/sys/net/ipv4/tcp_keepalive_time
$ <span class="token builtin class-name">echo</span> <span class="token number">30</span> <span class="token operator">&gt;</span> /proc/sys/net/ipv4/tcp_keepalive_intvl
$ <span class="token builtin class-name">echo</span> <span class="token number">5</span> <span class="token operator">&gt;</span> /proc/sys/net/ipv4/tcp_keepalive_probes
</code></pre>
</blockquote>

<blockquote>
<p>注意：在Kubernetes环境中，容器不会直接继承母机tcp keepalive的配置(可以直接继承母机tcp超时重试的配置)，因此必须通过一定方式进行适配。这里介绍其中一种方式，添加initContainers使配置生效：</p>
</blockquote>

<blockquote>
<pre class="  language-yaml" style="position: relative; z-index: 2;"><code class="prism  language-yaml"><span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> init<span class="token punctuation">-</span>sysctl
  <span class="token key atrule">image</span><span class="token punctuation">:</span> busybox
  <span class="token key atrule">command</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> /bin/sh
  <span class="token punctuation">-</span> <span class="token punctuation">-</span>c
  <span class="token punctuation">-</span> <span class="token punctuation">|</span><span class="token scalar string">
    sysctl -w net.ipv4.tcp_keepalive_time=30
    sysctl -w net.ipv4.tcp_keepalive_intvl=30
    sysctl -w net.ipv4.tcp_keepalive_probes=5</span>
  <span class="token key atrule">securityContext</span><span class="token punctuation">:</span>
    <span class="token key atrule">privileged</span><span class="token punctuation">:</span> <span class="token boolean important">true</span>
</code></pre>
</blockquote>

<blockquote>
<p>通过上述的TCP keepalive以及TCP ARQ配置，我们可以将无效连接断开时间缩短到4分钟以内，一定程度上解决了母机宕机导致的连接异常问题。不过最好的解决方案是在应用层设置超时或者健康检查机制及时关闭底层无效连接</p>
</blockquote>

<h2 id="节点驱逐">节点驱逐</h2>

<p>这里我们对节点驱逐分应用和存储两方面进行分析：</p>

<h3 id="应用相关">应用相关</h3>

<p>pod驱逐可以使服务自动恢复副本数量。如上所述，node controller会在节点心跳超时之后一段时间(默认5mins)驱逐该节点上的pod，这个时间由如下参数决定：</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token punctuation">(</span>kube<span class="token operator">-</span>apiserver<span class="token punctuation">)</span>default<span class="token operator">-</span><span class="token keyword">not</span><span class="token operator">-</span>ready<span class="token operator">-</span>toleration<span class="token operator">-</span>seconds：default <span class="token number">300</span>
<span class="token punctuation">(</span>kube<span class="token operator">-</span>apiserver<span class="token punctuation">)</span>default<span class="token operator">-</span>unreachable<span class="token operator">-</span>toleration<span class="token operator">-</span>seconds：default <span class="token number">300</span>
</code></pre>

<blockquote>
<blockquote>
<p>Note: Kubernetes automatically adds a toleration for <a href="http://node.kubernetes.io/not-ready" target="_blank">node.kubernetes.io/not-ready</a> and <a href="http://node.kubernetes.io/unreachable" target="_blank">node.kubernetes.io/unreachable</a> with tolerationSeconds=300, unless you, or a controller, set those tolerations explicitly. These automatically-added tolerations mean that Pods remain bound to Nodes for 5 minutes after one of these problems is detected.</p>
</blockquote>
</blockquote>

<p>这里面涉及两个<a href="https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/#taint-based-evictions" target="_blank">tolerations</a>：</p>

<ul>
<li><a href="http://node.kubernetes.io/not-ready:" target="_blank">node.kubernetes.io/not-ready:</a> Node is not ready. This corresponds to the NodeCondition Ready being “False”.</li>
<li><a href="http://node.kubernetes.io/unreachable:" target="_blank">node.kubernetes.io/unreachable:</a> Node is unreachable from the node controller. This corresponds to the NodeCondition Ready being “Unknown”.</li>
</ul>

<pre class="  language-yaml" style="position: relative; z-index: 2;"><code class="prism  language-yaml"><span class="token key atrule">tolerations</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoExecute
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/not<span class="token punctuation">-</span>ready
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Exists
    <span class="token key atrule">tolerationSeconds</span><span class="token punctuation">:</span> <span class="token number">300</span>
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoExecute
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/unreachable
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Exists
    <span class="token key atrule">tolerationSeconds</span><span class="token punctuation">:</span> <span class="token number">300</span>
</code></pre>

<p>当节点心跳超时(ConditionUnknown)之后，node controller会给该node添加如下taints：</p>

<pre class="  language-yaml" style="position: relative; z-index: 2;"><code class="prism  language-yaml"><span class="token key atrule">spec</span><span class="token punctuation">:</span>
  <span class="token punctuation">...</span>
  <span class="token key atrule">taints</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoSchedule
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/unreachable
    <span class="token key atrule">timeAdded</span><span class="token punctuation">:</span> <span class="token string">"2020-07-02T03:50:47Z"</span>
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoExecute
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/unreachable
    <span class="token key atrule">timeAdded</span><span class="token punctuation">:</span> <span class="token string">"2020-07-02T03:50:53Z"</span>
</code></pre>

<p>由于pod对<code>node.kubernetes.io/unreachable:NoExecute</code> taint容忍时间为300s，因此node controller会在5mins之后驱逐该节点上的pod</p>

<p>这里面有比较特殊的情况，例如：statefulset，daemonset以及static pod。我们逐一说明：</p>

<ul>
<li>statefulset</li>
</ul>

<p>pod删除存在两个阶段，第一个阶段是controller-manager设置pod的spec.deletionTimestamp字段为非nil值；第二个阶段是kubelet完成实际的pod删除操作(volume detach，container删除等)</p>

<p>当node宕机后，显然kubelet无法完成第二阶段的操作，因此controller-manager认为pod并没有被删除掉，在这种情况下statefulset工作负载形式的pod不会产生新的替换pod，<a href="https://github.com/kubernetes/kubernetes/issues/55713#issuecomment-518340883" target="_blank">并一直处于"Terminating"状态</a></p>

<blockquote>
<blockquote>
<p>Like a Deployment, a StatefulSet manages Pods that are based on an identical container spec. Unlike a Deployment, a StatefulSet maintains a sticky identity for each of their Pods. These pods are created from the same spec, but are not interchangeable: each has a persistent identifier that it maintains across any rescheduling.</p>
</blockquote>
</blockquote>

<blockquote>
<blockquote>
<p>In normal operation of a StatefulSet, there is never a need to force delete a StatefulSet Pod. The StatefulSet controller is responsible for creating, scaling and deleting members of the StatefulSet. It tries to ensure that the specified number of Pods from ordinal 0 through N-1 are alive and ready. StatefulSet ensures that, at any time, there is at most one Pod with a given identity running in a cluster. This is referred to as at most one semantics provided by a StatefulSet.</p>
</blockquote>
</blockquote>

<p>原因是statefulset为了保障<a href="https://kubernetes.io/docs/tasks/run-application/force-delete-stateful-set-pod/#statefulset-considerations" target="_blank">at most one semantics</a>，需要满足对于指定identity同时只有一个pod存在。在node shoudown后，虽然pod被驱逐了(“Terminating”)，但是由于controller无法判断这个statefulset pod是否还在运行(因为并没有彻底删除)，故不会产生替换容器，一定是要等到这个pod被完全删除干净(<a href="https://github.com/kubernetes/community/blob/master/contributors/design-proposals/storage/pod-safety.md#current-guarantees-for-pod-lifecycle" target="_blank">by kubelet</a>)，才会产生替换容器(deployment不需要满足这个条件，所以在驱逐pod时，controller会马上产生替换pod，而不需要等待kubelet删除pod)</p>

<ul>
<li>daemonset</li>
</ul>

<p>daemonset则更加特殊，默认情况下daemonset pod会被设置多个tolerations，使其可以容忍节点几乎所有异常的状态，所以不会出现驱逐的情况。这也很好理解，因为daemonset本来就是一个node部署一个pod，如下：</p>

<pre class="  language-yaml" style="position: relative; z-index: 2;"><code class="prism  language-yaml"><span class="token key atrule">tolerations</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoSchedule
    <span class="token key atrule">key</span><span class="token punctuation">:</span> dns
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Equal
    <span class="token key atrule">value</span><span class="token punctuation">:</span> <span class="token string">"false"</span>
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoExecute
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/not<span class="token punctuation">-</span>ready
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Exists
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoExecute
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/unreachable
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Exists
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoSchedule
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/disk<span class="token punctuation">-</span>pressure
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Exists
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoSchedule
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/memory<span class="token punctuation">-</span>pressure
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Exists
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoSchedule
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/pid<span class="token punctuation">-</span>pressure
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Exists
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoSchedule
    <span class="token key atrule">key</span><span class="token punctuation">:</span> node.kubernetes.io/unschedulable
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Exists
</code></pre>

<ul>
<li>static pod</li>
</ul>

<p>static pod类型类似daemonset会设置tolerations容忍节点异常状态，如下：</p>

<pre class="  language-yaml" style="position: relative; z-index: 2;"><code class="prism  language-yaml"><span class="token key atrule">tolerations</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">effect</span><span class="token punctuation">:</span> NoExecute
    <span class="token key atrule">operator</span><span class="token punctuation">:</span> Exists
</code></pre>

<p>因此在节点宕机后，static pod也不会发生驱逐</p>

<h3 id="存储相关">存储相关</h3>

<p>当pod使用的volume只支持RWO读写模式时，如果pod所在母机宕机了，并且随后在其它母机上产生了替换副本，则该替换副本的创建会阻塞，如下所示：</p>

<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash">$ kubectl get pods -o wide
nginx-7b4d5d9fd-bmc8g       <span class="token number">0</span>/1     ContainerCreating   <span class="token number">0</span>          0s    <span class="token operator">&lt;</span>none<span class="token operator">&gt;</span>         <span class="token number">10.0</span>.0.1   <span class="token operator">&lt;</span>none<span class="token operator">&gt;</span>           <span class="token operator">&lt;</span>none<span class="token operator">&gt;</span>
nginx-7b4d5d9fd-nqgfz       <span class="token number">1</span>/1     Terminating         <span class="token number">0</span>          19m   <span class="token number">192.28</span>.1.165   <span class="token number">10.0</span>.0.2   <span class="token operator">&lt;</span>none<span class="token operator">&gt;</span>           <span class="token operator">&lt;</span>none<span class="token operator">&gt;</span>
$ kubectl describe pods/nginx-7b4d5d9fd-bmc8g
<span class="token punctuation">[</span><span class="token punctuation">..</span>.truncate<span class="token punctuation">..</span>.<span class="token punctuation">]</span>
Events:
  Type     Reason              Age   From                     Message
  ----     ------              ----  ----                     -------
  Normal   Scheduled           3m5s  default-scheduler        Successfully assigned default/nginx-7b4d5d9fd-bmc8g to <span class="token number">10.0</span>.0.1
  Warning  FailedAttachVolume  3m5s  attachdetach-controller  Multi-Attach error <span class="token keyword">for</span> volume <span class="token string">"pvc-7f68c087-9e56-11ea-a2ef-5254002f7cc9"</span> Volume is already used by pod<span class="token punctuation">(</span>s<span class="token punctuation">)</span> nginx-7b4d5d9fd-nqgfz
  Warning  FailedMount         62s   kubelet, <span class="token number">10.0</span>.0.1        Unable to <span class="token function">mount</span> volumes <span class="token keyword">for</span> pod <span class="token string">"nginx-7b4d5d9fd-bmc8g_default(bb5501ca-9fea-11ea-9730-5254002f7cc9)"</span><span class="token builtin class-name">:</span> <span class="token function">timeout</span> expired waiting <span class="token keyword">for</span> volumes to attach or <span class="token function">mount</span> <span class="token keyword">for</span> pod <span class="token string">"default"</span>/<span class="token string">"nginx-7b4d5d9fd-nqgfz"</span><span class="token builtin class-name">.</span> list of unmounted <span class="token assign-left variable">volumes</span><span class="token operator">=</span><span class="token punctuation">[</span>nginx-data<span class="token punctuation">]</span>. list of unattached <span class="token assign-left variable">volumes</span><span class="token operator">=</span><span class="token punctuation">[</span>root-certificate default-token-q2vft nginx-data<span class="token punctuation">]</span>
</code></pre>

<p>这是因为只支持RWO(ReadWriteOnce – the volume can be mounted as read-write by a single node)的volume正常情况下在Kubernetes集群中只能被一个母机attach，由于宕机母机无法执行volume detach操作，其它母机上的pod如果使用相同的volume会被挂住，最终导致容器创建一直阻塞并报错：</p>

<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash">Multi-Attach error <span class="token keyword">for</span> volume <span class="token string">"pvc-7f68c087-9e56-11ea-a2ef-5254002f7cc9"</span> Volume is already used by pod<span class="token punctuation">(</span>s<span class="token punctuation">)</span> nginx-7b4d5d9fd-nqgfz
</code></pre>

<p>解决办法是采用支持RWX(ReadWriteMany – the volume can be mounted as read-write by many nodes)读写模式的volume。另外如果必须采用只支持RWO模式的volume，则可以执行如下命令强制删除pod，如下：</p>

<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash">$ kubectl delete pods/nginx-7b4d5d9fd-nqgfz --force --grace-period<span class="token operator">=</span><span class="token number">0</span>
</code></pre>

<p>之后，对于新创建的pod，attachDetachController会在6mins(代码写死)后强制detach volume，并正常attach，如下：</p>

<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash">W0811 04:01:25.024422       <span class="token number">1</span> reconciler.go:328<span class="token punctuation">]</span> Multi-Attach error <span class="token keyword">for</span> volume <span class="token string">"pvc-e97c6ce6-d8a6-11ea-b832-7a866c097df1"</span> <span class="token punctuation">(</span>UniqueName: <span class="token string">"kubernetes.io/rbd/k8s:kubernetes-dynamic-pvc-f35fc6fa-d8a6-11ea-bd98-aeb6842de1e3"</span><span class="token punctuation">)</span> from node <span class="token string">"10.0.0.3"</span> Volume is already exclusively attached to node <span class="token number">10.0</span>.0.2 and can<span class="token string">'t be attached to another
I0811 04:01:25.024480       1 event.go:209] Event(v1.ObjectReference{Kind:"Pod", Namespace:"default", Name:"default-nginx-6584f7ddb7-jx9s2", UID:"5322240f-db87-11ea-b832-7a866c097df1", APIVersion:"v1", ResourceVersion:"28275287", FieldPath:""}): type: '</span>Warning<span class="token string">' reason: '</span>FailedAttachVolume<span class="token string">' Multi-Attach error for volume "pvc-e97c6ce6-d8a6-11ea-b832-7a866c097df1" Volume is already exclusively attached to one node and can'</span>t be attached to another
W0811 04:07:25.047767       <span class="token number">1</span> reconciler.go:232<span class="token punctuation">]</span> attacherDetacher.DetachVolume started <span class="token keyword">for</span> volume <span class="token string">"pvc-e97c6ce6-d8a6-11ea-b832-7a866c097df1"</span> <span class="token punctuation">(</span>UniqueName: <span class="token string">"kubernetes.io/rbd/k8s:kubernetes-dynamic-pvc-f35fc6fa-d8a6-11ea-bd98-aeb6842de1e3"</span><span class="token punctuation">)</span> on node <span class="token string">"10.0.0.2"</span> This volume is not safe to detach, but maxWaitForUnmountDuration 6m0s expired, force detaching
I0811 04:07:25.047860       <span class="token number">1</span> operation_generator.go:500<span class="token punctuation">]</span> DetachVolume.Detach succeeded <span class="token keyword">for</span> volume <span class="token string">"pvc-e97c6ce6-d8a6-11ea-b832-7a866c097df1"</span> <span class="token punctuation">(</span>UniqueName: <span class="token string">"kubernetes.io/rbd/k8s:kubernetes-dynamic-pvc-f35fc6fa-d8a6-11ea-bd98-aeb6842de1e3"</span><span class="token punctuation">)</span> on node <span class="token string">"10.0.0.2"</span>
I0811 04:07:25.148094       <span class="token number">1</span> reconciler.go:288<span class="token punctuation">]</span> attacherDetacher.AttachVolume started <span class="token keyword">for</span> volume <span class="token string">"pvc-e97c6ce6-d8a6-11ea-b832-7a866c097df1"</span> <span class="token punctuation">(</span>UniqueName: <span class="token string">"kubernetes.io/rbd/k8s:kubernetes-dynamic-pvc-f35fc6fa-d8a6-11ea-bd98-aeb6842de1e3"</span><span class="token punctuation">)</span> from node <span class="token string">"10.0.0.3"</span>
I0811 04:07:25.148180       <span class="token number">1</span> operation_generator.go:377<span class="token punctuation">]</span> AttachVolume.Attach succeeded <span class="token keyword">for</span> volume <span class="token string">"pvc-e97c6ce6-d8a6-11ea-b832-7a866c097df1"</span> <span class="token punctuation">(</span>UniqueName: <span class="token string">"kubernetes.io/rbd/k8s:kubernetes-dynamic-pvc-f35fc6fa-d8a6-11ea-bd98-aeb6842de1e3"</span><span class="token punctuation">)</span> from node <span class="token string">"10.0.0.3"</span>
I0811 04:07:25.148266       <span class="token number">1</span> event.go:209<span class="token punctuation">]</span> Event<span class="token punctuation">(</span>v1.ObjectReference<span class="token punctuation">{</span>Kind:<span class="token string">"Pod"</span>, Namespace:<span class="token string">"default"</span>, Name:<span class="token string">"default-nginx-6584f7ddb7-jx9s2"</span>, <span class="token environment constant">UID</span><span class="token builtin class-name">:</span><span class="token string">"5322240f-db87-11ea-b832-7a866c097df1"</span>, APIVersion:<span class="token string">"v1"</span>, ResourceVersion:<span class="token string">"28275287"</span>, FieldPath:<span class="token string">""</span><span class="token punctuation">}</span><span class="token punctuation">)</span>: type: <span class="token string">'Normal'</span> reason: <span class="token string">'SuccessfulAttachVolume'</span> AttachVolume.Attach succeeded <span class="token keyword">for</span> volume <span class="token string">"pvc-e97c6ce6-d8a6-11ea-b832-7a866c097df1"</span>
</code></pre>

<p>而默认的6mins对于生产环境来说太长了，而且Kubernetes并没有提供参数进行配置，因此我向官方提了一个<a href="https://github.com/kubernetes/kubernetes/pull/93776" target="_blank">PR</a>用于解决这个问题，如下：</p>

<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash">--attach-detach-reconcile-max-wait-unmount-duration duration   maximum amount of <span class="token function">time</span> the attach detach controller will <span class="token function">wait</span> <span class="token keyword">for</span> a volume to be safely unmounted from its node. Once this <span class="token function">time</span> has expired, the controller will assume the node or kubelet are unresponsive and will detach the volume anyway. <span class="token punctuation">(</span>default 6m0s<span class="token punctuation">)</span>
</code></pre>

<p>通过配置<code>attach-detach-reconcile-max-wait-unmount-duration</code>，可以缩短替换pod成功运行的时间</p>

<p>另外，注意<code>force detaching</code>逻辑只会在pod被<code>force delete</code>的时候触发，正常delete不会触发该逻辑</p>

<h2 id="存储">存储</h2>

<p>对于存储，可以分为Kubernetes系统存储和应用存储，系统存储专指etcd；而应用存储一般来说只考虑persistent volume</p>

<h3 id="系统存储 - etcd">系统存储 - etcd</h3>

<p>etcd使用<a href="https://ramcloud.atlassian.net/wiki/download/attachments/6586375/raft.pdf" target="_blank">Raft一致性算法</a>(leader selection + log replication + safety)中的leader selection来实现节点宕机下的高可用问题，如下：</p>

<p style=""><img src="./Kubernetes高可用实战干货 - CSIG新人专区（已转至云知） - KM平台_files/cos-file-url(4)" alt="" style="position: relative; z-index: 2;"></p>

<h3 id="应用存储 - persistent volume">应用存储 - persistent volume</h3>

<p>这里考虑存储是部署在集群外的情况(通常情况)。如果一个母机宕机了，由于没有对外部存储集群产生破坏，因此不会影响其它母机上应用访问pv存储</p>

<p>而对于Kubernetes存储本身组件功能(in-tree, flexVolume, external-storage以及csi)的影响实际上可以归纳为对存储插件应用的影响，这里以csi为例子进行说明：</p>

<p style=""><img src="./Kubernetes高可用实战干货 - CSIG新人专区（已转至云知） - KM平台_files/cos-file-url(5)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>通过实现对上述StatefulSet/Deployment工作负载类型应用(CSI Driver+Identity Controller以及external-attacher+external-provisioner)的高可用即可</p>

<h2 id="应用">应用</h2>

<h3 id="Stateless Application">Stateless Application</h3>

<p>对于无状态的服务(通常部署为deployment工作负载)，我们可以直接通过设置反亲和+多副本来实现高可用，例如nginx服务：</p>

<pre class="  language-yaml" style="position: relative; z-index: 2;"><code class="prism  language-yaml"><span class="token key atrule">apiVersion</span><span class="token punctuation">:</span> apps/v1
<span class="token key atrule">kind</span><span class="token punctuation">:</span> Deployment
<span class="token key atrule">metadata</span><span class="token punctuation">:</span>
<span class="token key atrule">name</span><span class="token punctuation">:</span> web<span class="token punctuation">-</span>server
<span class="token key atrule">spec</span><span class="token punctuation">:</span>
<span class="token key atrule">selector</span><span class="token punctuation">:</span>
  <span class="token key atrule">matchLabels</span><span class="token punctuation">:</span>
    <span class="token key atrule">app</span><span class="token punctuation">:</span> web<span class="token punctuation">-</span>store
<span class="token key atrule">replicas</span><span class="token punctuation">:</span> <span class="token number">3</span>
<span class="token key atrule">template</span><span class="token punctuation">:</span>
  <span class="token key atrule">metadata</span><span class="token punctuation">:</span>
    <span class="token key atrule">labels</span><span class="token punctuation">:</span>
      <span class="token key atrule">app</span><span class="token punctuation">:</span> web<span class="token punctuation">-</span>store
  <span class="token key atrule">spec</span><span class="token punctuation">:</span>
    <span class="token key atrule">affinity</span><span class="token punctuation">:</span>
      <span class="token key atrule">podAntiAffinity</span><span class="token punctuation">:</span>
        <span class="token key atrule">requiredDuringSchedulingIgnoredDuringExecution</span><span class="token punctuation">:</span>
        <span class="token punctuation">-</span> <span class="token key atrule">labelSelector</span><span class="token punctuation">:</span>
            <span class="token key atrule">matchExpressions</span><span class="token punctuation">:</span>
            <span class="token punctuation">-</span> <span class="token key atrule">key</span><span class="token punctuation">:</span> app
              <span class="token key atrule">operator</span><span class="token punctuation">:</span> In
              <span class="token key atrule">values</span><span class="token punctuation">:</span>
              <span class="token punctuation">-</span> web<span class="token punctuation">-</span>store
          <span class="token key atrule">topologyKey</span><span class="token punctuation">:</span> <span class="token string">"kubernetes.io/hostname"</span>
    <span class="token key atrule">containers</span><span class="token punctuation">:</span>
    <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> web<span class="token punctuation">-</span>app
      <span class="token key atrule">image</span><span class="token punctuation">:</span> nginx<span class="token punctuation">:</span>1.16<span class="token punctuation">-</span>alpine
</code></pre>

<p>如果其中一个pod所在母机宕机了，则在endpoint controller踢掉该pod backend后，服务访问正常</p>

<p>这类服务通常依赖于其它有状态服务，例如：WebServer，APIServer等</p>

<h3 id="Stateful Application">Stateful Application</h3>

<p>对于有状态的服务，可以按照高可用的实现类型分类如下：</p>

<ul>
<li>RWX Type</li>
</ul>

<p>对于本身基于多副本实现高可用的应用来说，我们可以直接利用反亲和+多副本进行部署(一般部署为deployment类型)，后接同一个存储(支持ReadWriteMany，例如：Cephfs or Ceph RGW)，实现类似无状态服务的高可用模式</p>

<p>其中，docker distribution，helm chartmuseum以及harbor jobservice等都属于这种类型</p>

<ul>
<li>Special Type</li>
</ul>

<p>对于特殊类型的应用，例如database，它们一般有自己定制的高可用方案，例如常用的主从模式</p>

<p>这类应用通常以statefulset的形式进行部署，每个副本对接一个pv，在母机宕机的情况下，由应用本身实现高可用(例如：master选举-主备切换)</p>

<p>其中，redis，postgres，以及各类db都基本是这种模式，如下是redis一主两从三哨高可用方案：</p>

<p style=""><img src="./Kubernetes高可用实战干货 - CSIG新人专区（已转至云知） - KM平台_files/cos-file-url(6)" alt="" style="position: relative; z-index: 2;"></p>

<p>还有更加复杂的高可用方案，例如etcd的<a href="https://ramcloud.atlassian.net/wiki/download/attachments/6586375/raft.pdf" target="_blank">Raft一致性算法</a>：</p>

<p style=""><img src="./Kubernetes高可用实战干货 - CSIG新人专区（已转至云知） - KM平台_files/cos-file-url(7)" alt="" style="position: relative; z-index: 2;"></p>

<ul>
<li>Distributed Lock Type</li>
</ul>

<p>Kubernetes Controller就是利用分布式锁实现高可用</p>

<p>这里归纳了一些应用常用的实现高可用的方案。当然了，各个应用可以定制适合自身的高可用方案，不可能完全一样</p>

<h2 id="Conclusion">Conclusion</h2>

<p>本文先介绍了Kubernetes集群高可用的整体架构，之后基于该架构从网络，存储，以及应用层面分析了当节点宕机时可能会出现的问题以及对应的解决方案，希望对Kubernetes高可用实践有所助益。实际生产环境需要综合上述因素全面考虑，将整体服务的恢复时间控制在一个可以接受的范围内</p>

<h2 id="Refs">Refs</h2>

<ul>
<li><a href="https://duyanghao.github.io/kubernetes-ha/" target="_blank">Kubernetes高可用实战干货</a></li>
</ul>
