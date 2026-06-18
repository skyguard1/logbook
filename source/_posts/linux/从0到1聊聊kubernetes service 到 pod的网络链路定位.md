---
title: "从0到1聊聊kubernetes service 到 pod的网络链路定位"
date: 2022-06-17 08:21:36
categories:
  - linux
---

<dir data-lines="1" data-sign="a61e3c279d7465fd56a580e52f930f89-1" class="toc"><p class="toc-title">目录</p><li class="toc-li"><a class="level-2" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#%E8%AE%A4%E8%AF%86service">认识service</a></li><li class="toc-li"><a class="level-2" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#service%E4%BD%BF%E7%94%A8%E5%9C%BA%E6%99%AF">service使用场景</a></li><li class="toc-li">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a class="level-3" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#1-clustertpye">1. ClusterTpye</a></li><li class="toc-li">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a class="level-3" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#2-nodeport">2. NodePort</a></li><li class="toc-li">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a class="level-3" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#3-headless">3. Headless</a></li><li class="toc-li">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a class="level-3" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#4-loadbalancer">4. LoadBalancer</a></li><li class="toc-li">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a class="level-3" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#5-%E6%97%A0%E6%A0%87%E7%AD%BE%E9%80%89%E6%8B%A9">5. 无标签选择</a></li><li class="toc-li"><a class="level-2" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#service%E5%BA%95%E5%B1%82%E5%AE%9E%E7%8E%B0">service底层实现</a></li><li class="toc-li"><a class="level-2" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#service%E5%88%B0pod%E7%BD%91%E7%BB%9C%E9%93%BE%E8%B7%AF%E7%A4%BA%E4%BE%8B%E5%88%86%E6%9E%90">service到pod网络链路示例分析</a></li><li class="toc-li">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a class="level-5" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#1-%E7%A1%AE%E8%AE%A4%E5%BD%93%E5%89%8D%E7%8E%AF%E5%A2%83%E6%98%AFiptables-%E6%88%96-ipvs">1. 确认当前环境是iptables 或 ipvs</a></li><li class="toc-li">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a class="level-5" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#2-%E8%8E%B7%E5%8F%96service-ip%E5%9C%B0%E5%9D%80">2. 获取service ip地址</a></li><li class="toc-li">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a class="level-5" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#3-%E6%A0%B9%E6%8D%AEservice-ip-%E5%9C%B0%E5%9D%80%E8%BF%BD%E5%AF%BBpod-ip%E8%B4%9F%E8%BD%BD%E5%9D%87%E8%A1%A1">3. 根据service ip 地址追寻pod ip负载均衡</a></li><li class="toc-li"><a class="level-2" href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#%E5%8F%82%E8%80%83%EF%BC%9A">参考：</a></li></dir><h2 data-lines="2" data-sign="b80ddc51e0161c271070764d18f91207" id="%E8%AE%A4%E8%AF%86service"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#%E8%AE%A4%E8%AF%86service" class="anchor"></a>认识service</h2><p data-lines="1" data-type="p" data-sign="f3c32b57f21d2e57932bffecc3f857f4">Service 是 kuberneres将一组Pod暴露给外界访问的一种机制。为什么引入service？直接pod进行交互不行吗？引入service主要原因有二：     </p><ol start="1" class="cherry-list__default" data-lines="7" data-sign="4fcb2f479b54c4685d63df6c7e987988list7"><li>pod 生命周期是短暂的，会随着发布新版本而被销毁，pod ip不固定;</li><li>一组pod负载均衡需求    <br><br>而service恰好能通过标签选择器或直接与endpoint关联将一组pod进行绑定做为一组pod的统一入口和提供负载均衡能力。Service 有两种类型：service和Headless Service, Service 通常应用在无状态服务上；Headless Service 则应用在有状态服务。Service和Headless Service有什么区别呢？Service 和 Headless Service主要有如下表象区别：     <br></li></ol><ol start="1" class="cherry-list__default" data-lines="1" data-sign="4fcb2f479b54c4685d63df6c7e987988list1"><li>service 有一个cluster ip(虚拟ip)作为一组pod的统一入口，而headless service 则没有这个cluster ip；</li><li>通过service 名访问时，coredns或者kubedns会解析到service的vip地址，而headless service 则通常需要headless service 名前加上pod_name,有状态服务pod_name 都会带编号，这样coredns或者kubedns就可以直接解析到具体的pod实例。</li></ol><p data-lines="1" data-type="p" data-sign="ae1d125ce83af1e44ea4251864730273" style=""><img alt="" src="/logbook/images/linux/从0到1聊聊kubernetes service 到 pod的网络链路定位/d1cc0e0ac5bf.png" style="position: relative; z-index: 2;" class="amplify"></p><p data-lines="1" data-type="p" data-sign="8c29a951efc10239b9bf132d5ed03601">为什么有了service还需要引入headless service呢？引入headless service为了解决有状态服务既要解决pod ip不固定并且还需要固定访问具体的pod(mysql 的主或者备)的问题。service 会采用负载均衡的方式引流到后端，无法固定；而headless service 通过结合coredns/kubedns解析后直接对接具体的pod。上面聊了这么多，接下来看看Service面纱背后面目：    </p><div data-sign="7f0fdd909170921e4f0d230f35613cb9" data-type="codeBlock" data-lines="13"><pre><code>apiVersion: v1
kind: Service # 定义当前kuernetes资源类型为Service
metadata:
  name: my-service # service 名称
spec:
  selector: # 标签选择器与一组pod进行绑定
    app: MyApp # Pod上定义的一组标签
  ports:
    - protocol: TCP # 对外暴露的协议
      port: 80 # service 的端口
      targetPort: 9376 # pod监听端口
</code></pre>

<p data-lines="2" data-type="p" data-sign="79fc6760417acccc2a3b3e947fd7d510">上面是通常使用的Service定义，那headless service又如何定义？其实只需要spec.clusterIP值设置为"None" 即可。</p><h2 data-lines="2" data-sign="b66e884af291f0ca23deaf61956a1ab4" id="service%E4%BD%BF%E7%94%A8%E5%9C%BA%E6%99%AF"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#service%E4%BD%BF%E7%94%A8%E5%9C%BA%E6%99%AF" class="anchor"></a>service使用场景</h2><p data-lines="1" data-type="p" data-sign="ff4921bcb8244739f4eb1d50b871d43f">对Service有了一定认识，接下来聊聊Service的使用场景。</p><h3 data-lines="1" data-sign="f92074ce0bd9a40b69385ab886616bcc" id="1-clustertpye"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#1-clustertpye" class="anchor"></a>1. ClusterTpye</h3><p data-lines="1" data-type="p" data-sign="11f62a2490cee8aee56a6b70defc785a">clusterType 场景很普遍，通常集群内通信几乎均采用clusterType类型场景；clusterType类型会创建一个虚拟ip地址作为一组pod的统一入口以及负载均衡。例子：    </p><div data-sign="4effd918c9413df14ab89d2b1fb4b3a4" data-type="codeBlock" data-lines="23"><pre><code>apiVersion: v1
kind: Service
metadata:
  labels:
    app: kibana
    heritage: Tiller
    release: kibana
  name: kibana-kibana
  namespace: default
spec:
  ports:
  - name: http # 当一个service需要对外暴露多个端口时，需要加名称加以区分
    port: 5601
    protocol: TCP
    targetPort: 5601
  selector:
    app: kibana
    release: kibana
  sessionAffinity: None # 默认时rr（round-robin轮询），可以设置为: ClientIP,基于客户端ip的会话保持类似ha的source ip，nginx的ip_hash
  type: ClusterIP # 定义为cluster Type类型的service,ClusterIP也是默认的service类型
</code></pre>

<p data-lines="1" data-type="p" data-sign="53ed18b1161d6f3666a3998379c20de5">通过使用</p><div data-sign="ba2492c322b22ddc2def8ea4c73bf3ed" data-type="codeBlock" data-lines="15"><pre><code>kubectl get svc $SERVICE_NAME -n $NAME_SPACES
[root@VM_70_26_centos ~]# kubectl get svc -n default
NAME                            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
elasticsearch-master            ClusterIP   172.x.y.127   &lt;none&gt;        9200/TCP,9300/TCP            6d6h
elasticsearch-master-headless   ClusterIP   None            &lt;none&gt;        9200/TCP,9300/TCP            6d6h
kafka                           ClusterIP   172.x.y.142   &lt;none&gt;        9092/TCP                     6d6h
kafka-headless                  ClusterIP   None            &lt;none&gt;        9092/TCP                     6d6h
kafka-manager                   ClusterIP   172.x.y.198   &lt;none&gt;        9000/TCP                     6d6h
kafka-zookeeper                 ClusterIP   172.x.y.86    &lt;none&gt;        2181/TCP                     6d6h
kafka-zookeeper-headless        ClusterIP   None            &lt;none&gt;        2181/TCP,3888/TCP,2888/TCP   6d6h
kibana-kibana                   ClusterIP   172.x.y.143   &lt;none&gt;        5601/TCP                     6d6h

</code></pre>

<p data-lines="1" data-type="p" data-sign="68495060ac7cb6a3e0d4a0d79e5a5fd5">获取当前namespace下的service 列表. 使用</p><div data-sign="b61226d1869d1b8967c81731848ef0cf" data-type="codeBlock" data-lines="19"><pre><code>kubectl describe svc $SERVICE_NAME -n $NAME_SPACES
[root@VM_70_26_centos ~]# kubectl describe svc kibana-kibana -n pot
Name:              kibana-kibana
Namespace:         pot
Labels:            app=kibana
                   heritage=Tiller
                   release=kibana
Annotations:       &lt;none&gt;
Selector:          app=kibana,release=kibana
Type:              ClusterIP
IP:                172.x.y.143
Port:              http  5601/TCP
TargetPort:        5601/TCP
Endpoints:         172.x.z.8:5601 # pod ip+port
Session Affinity:  None
Events:            &lt;none&gt;
</code></pre>

<p data-lines="1" data-type="p" data-sign="476801d50d394f0f6d523add8046b12b">查看service事件信息。使用</p><div data-sign="dc002a81b31ae87d77390b276dcc72d4" data-type="codeBlock" data-lines="4"><pre><code>kubectl get svc $SERVICE_NAME -n $NAME_SPACES -o yaml
</code></pre>

<p data-lines="1" data-type="p" data-sign="720d4347045ed51a37eda0cb4682b742">查看当前service配置内容。</p><p data-lines="2" data-type="br" data-sign="br2">&nbsp;</p><h3 data-lines="1" data-sign="aab76c583ff7821920d58477247c1b31" id="2-nodeport"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#2-nodeport" class="anchor"></a>2. NodePort</h3><p data-lines="1" data-type="p" data-sign="9f25fd543d4ec7ae570e181b2cb0a0ea">当一组pod需要跨集群或需要提供集群外访问能力时可以采用NodePort模式，使用NodePort方式会在集群内所有节点占用一个宿主机端口（默认值：30000-32767）,可以通过--service-node-port-range设置端口范围段，为此使用此场景需要注意端口规划；访问时直接访问kubernetes集群中任意节点IP+映射的宿主机端口即可。</p><div data-sign="7ec714752ce4cd07fb12e5956030f973" data-type="codeBlock" data-lines="21"><pre><code>apiVersion: v1
kind: Service
labels:
    app: kibana
    heritage: Tiller
    release: kibana
  name: kibana-kibana
  namespace: default
spec:
  - name: http
    port: 5601
    protocol: TCP
    targetPort: 5601
  selector:
    app: kibana
    release: kibana
  sessionAffinity: None
  type: NodePort # 只需要将type 类型改为NodePort即可。
</code></pre>

<h3 data-lines="2" data-sign="11a4d1dede229991e60aa564e5a1e64d" id="3-headless"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#3-headless" class="anchor"></a>3. Headless</h3><p data-lines="1" data-type="p" data-sign="ea3f6372905c3624c6b8b386b5122b98">Headless service 主要应用在statefulset（有状态服务），对于有状态服务有的需要固定访问，比如mysql主从模式时需要写的时候通过service 访问时候不能轮训模式，因为只有主节点可以写，这时候就需要headless service，通过访问<code>$pod_name.$headless_service_name.$namespace.svc.cluster.local</code> coredns/kubedns就会将此域名解析到具体的pod ip实现固定访问。</p><div data-sign="1f8c62ce0a8b95c8b7b4e0b56f1edfdc" data-type="codeBlock" data-lines="24"><pre><code>apiVersion: v1
kind: Service
metadata:
  labels:
    app: kibana
    heritage: Tiller
    release: kibana
  name: kibana-kibana
  namespace: default
spec:
  clusterIP: None # 只需要将clusterIP设置为None即可
  ports:
  - name: http
    port: 5601
    protocol: TCP
    targetPort: 5601
  selector:
    app: kibana
    release: kibana
  sessionAffinity: None
  type: ClusterIP
</code></pre>

<h3 data-lines="2" data-sign="5152c5417ab627bbb8206636572caed2" id="4-loadbalancer"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#4-loadbalancer" class="anchor"></a>4. LoadBalancer</h3><p data-lines="1" data-type="p" data-sign="ce4a7f481747c93b31a376484686e129">当一组pod需要跨集群或需要提供集群外访问除了上述提到的NodePort方式，还可以对接IaaS层的负载均衡器，当然这个是需要编写对应的driver实现注册到IaaS的LoadBalancer，这种场景在云上（，阿里云，华为云，ucloud等）已经做好了集成；不同厂商需要添加的annotations不一样，annotations届时看所应用的厂商配置说明即可，但根还是一样的。这种方式就解决了NodePort端口规划以及当某个节点异常了也会导致统一入口的高可用问题。以下annotations 以tke为例：</p><div data-sign="21b1dd29da35c3b7f345b684d6230446" data-type="codeBlock" data-lines="27"><pre><code>apiVersion: v1
kind: Service
metadata:
  annotations: # annotations 部分需要根据不同厂商而定
    service.kubernetes.io/loadbalance-id: lb-xxx
    service.kubernetes.io/qcloud-loadbalancer-clusterid: cls-xxx
    service.kubernetes.io/qcloud-loadbalancer-internal-subnetid: subnet-xxx
  labels:
    app: kibana
    heritage: Tiller
    release: kibana
  name: kibana-kibana
  namespace: default
spec:
  ports:
  - name: http
    port: 5601
    protocol: TCP
    targetPort: 5601
  selector:
    app: kibana
    release: kibana
  sessionAffinity: None
  type: LoadBalancer # 将类型设置为LoadBalancer 即可。
</code></pre>

<h3 data-lines="2" data-sign="65693602c03dbe9cb2a35344b4b686e1" id="5-%E6%97%A0%E6%A0%87%E7%AD%BE%E9%80%89%E6%8B%A9"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#5-%E6%97%A0%E6%A0%87%E7%AD%BE%E9%80%89%E6%8B%A9" class="anchor"></a>5. 无标签选择</h3><p data-lines="2" data-type="p" data-sign="ea0cffca8de4b6bec6b9d7c14c1e3f4c">kubernetes集群需要对接一些外部的服务，比如mysql，redis等，此时无标签选择场景就很适合使用。此场景使用分两步走，第一步先创建endpoints, 然后再创建没有标签选择的service，这种service是一种特殊的service。这样就解决了集群内的服务通过service即可访问集群外的服务。    <br>定义endpoints:    </p><div data-sign="f9d0bf77777863cc388b0ee1f60118a8" data-type="codeBlock" data-lines="12"><pre><code>apiVersion: v1
kind: Endpoints
metadata:
  name: my-service # 注意Endpoints 需要和service的名称保持一致
subsets:
  - addresses:
      - ip: 192.0.2.42 # 外部服务IP地址，这是一个数组
    ports:
      - port: 9376 # 外部服务端口
</code></pre>

<p data-lines="1" data-type="p" data-sign="11772a856094c030e5c4c9fee22ef13e">定义service</p><div data-sign="2604689fd305060baa58ff688fd8af19" data-type="codeBlock" data-lines="12"><pre><code>apiVersion: v1
kind: Service
metadata:
  name: my-service #  注意service 需要和Endpoints的名称保持一致
spec:
  ports:
    - protocol: TCP
      port: 80 # service 端口
      targetPort: 9376 # 外部服务端口
</code></pre>

<p data-lines="1" data-type="p" data-sign="2858112b7250a126b1bac32214ea32ac">无标签选择场景还有一种特殊的使用<a rel="nofollow" href="https://kubernetes.io/zh/docs/concepts/services-networking/service/#externalname">externalName</a>。</p><h2 data-lines="2" data-sign="8604c5252401b8eaa1d3ec8f8ec137d2" id="service%E5%BA%95%E5%B1%82%E5%AE%9E%E7%8E%B0"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#service%E5%BA%95%E5%B1%82%E5%AE%9E%E7%8E%B0" class="anchor"></a>service底层实现</h2><p data-lines="1" data-type="p" data-sign="5dd446655b046ffb4e74fb8f4e5a1f91">从认识到使用，那service到底是如何实现？实际上，Service 是由 kube-proxy 组件，加上 iptables 来共同实现的。举个例子，对于如下创建的名叫 elasticsearch-master 的 Service 来说，一旦它被提交给 Kubernetes，那么 kube-proxy 就可以通过 Service 的 Informer 感知到这样一个 Service 对象的添加。而作为对这个事件的响应，它就会在宿主机上创建这样一条 iptables 规则（你可以通过 iptables-save 看到它），如下所示：:    </p><div data-sign="6818020eedcabd2f97f2946d26f1e85a" data-type="codeBlock" data-lines="15"><pre><code>[root@VM_197_156_centos /data/helms/business]# kubectl get svc -n pot
NAME                            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
elasticsearch-master            ClusterIP   172.16.31.63    &lt;none&gt;        9200/TCP,9300/TCP   5d20h
elasticsearch-master-headless   ClusterIP   None            &lt;none&gt;        9200/TCP,9300/TCP   5d20h
kibana-kibana                   ClusterIP   172.16.31.144   &lt;none&gt;        5601/TCP            5d20h
nginx-ingress-nginx-ingress     ClusterIP   172.16.31.177   &lt;none&gt;        80/TCP,443/TCP      5d20h
sgikes-sg-helm                  ClusterIP   172.16.31.73    &lt;none&gt;        5601/TCP            5d17h
sgikes-sg-helm-clients          ClusterIP   172.16.31.141   &lt;none&gt;        9200/TCP,9300/TCP   5d17h
sgikes-sg-helm-discovery        ClusterIP   172.16.31.50    &lt;none&gt;        9300/TCP            5d17h
[root@VM_197_156_centos ~]# iptables-save | grep 172.16.31.63
-A KUBE-SERVICES -d 172.16.31.63/32 -p tcp -m comment --comment "pot/elasticsearch-master:transport cluster IP" -m tcp --dport 9300 -j KUBE-SVC-B3S4WZAGNU4F7PKP
-A KUBE-SERVICES -d 172.16.31.63/32 -p tcp -m comment --comment "pot/elasticsearch-master:http cluster IP" -m tcp --dport 9200 -j KUBE-SVC-HXMF37AORSHYWP2V
</code></pre>

<p data-lines="1" data-type="p" data-sign="82405caccc5f0051808620ec1b664262">可以看到，这条 iptables 规则的含义是：凡是目的地址是 172.16.31.63、目的端口是 9200 的 IP 包，都应该跳转到另外一条名叫KUBE-SVC-HXMF37AORSHYWP2V 的 iptables 链进行处理。而我们前面已经看到，172.16.31.63 正是这个 Service 的 VIP。所以这一条规则，就为这个 Service 设置了一个固定的入口地址。并且，由于 172.16.31.63 只是一条 iptables 规则上的配置，并没有真正的网络设备，所以你 ping 这个地址，是不会有任何响应的。那么，我们即将跳转到的 KUBE-SVC-HXMF37AORSHYWP2V 规则，又有什么作用呢？实际上，它是一组规则的集合，如下所示：   </p><div data-sign="8fe719e63bbeb1d62a6d0e4a36d86c93" data-type="codeBlock" data-lines="6"><pre><code>-A KUBE-SVC-HXMF37AORSHYWP2V -m statistic --mode random --probability 0.33332999982 -j KUBE-SEP-5CBHBRMC3HLKEFQM
-A KUBE-SVC-HXMF37AORSHYWP2V -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-FUG6U5TLAHSW77BL
-A KUBE-SVC-HXMF37AORSHYWP2V -j KUBE-SEP-KT57KYP65COAGJLX
</code></pre>

<p data-lines="1" data-type="p" data-sign="672fbc94328090a973d08863d3e23337">可以看到，这一组规则，实际上是一组随机模式（–mode random）的 iptables 链。而随机转发的目的地，分别是 KUBE-SEP-5CBHBRMC3HLKEFQM、KUBE-SEP-FUG6U5TLAHSW77BL 和 KUBE-SEP-KT57KYP65COAGJLX。而这三条链指向的最终目的地，其实就是这个 Service 代理的三个 Pod。所以这一组规则，就是 Service 实现负载均衡的位置。需要注意的是，iptables 规则的匹配是从上到下逐条进行的，所以为了保证上述三条规则每条被选中的概率都相同，我们应该将它们的 probability 字段的值分别设置为 1/3（0.333…）、1/2 和 1。这么设置的原理很简单：第一条规则被选中的概率就是 1/3；而如果第一条规则没有被选中，那么这时候就只剩下两条规则了，所以第二条规则的 probability 就必须设置为 1/2；类似地，最后一条就必须设置为 1。你可以想一下，如果把这三条规则的 probability 字段的值都设置成 1/3，最终每条规则被选中的概率会变成多少。</p><p data-lines="1" data-type="p" data-sign="4c58a5b6f54bc9148cff4ba9c8eae723">通过查看上述三条链的明细，我们就很容易理解 Service 进行转发的具体原理了，如下所示：</p><div data-sign="d462de2ff84c859c2331ee626e1817a2" data-type="codeBlock" data-lines="11"><pre><code>-A KUBE-SEP-5CBHBRMC3HLKEFQM -s 172.16.0.18/32 -j KUBE-MARK-MASQ
-A KUBE-SEP-5CBHBRMC3HLKEFQM -p tcp -m tcp -j DNAT --to-destination 172.16.0.18:9200

-A KUBE-SEP-FUG6U5TLAHSW77BL -s 172.16.1.8/32 -j KUBE-MARK-MASQ
-A KUBE-SEP-FUG6U5TLAHSW77BL -p tcp -m tcp -j DNAT --to-destination 172.16.1.8:9200

-A KUBE-SEP-KT57KYP65COAGJLX -s 172.16.2.7/32 -j KUBE-MARK-MASQ
-A KUBE-SEP-KT57KYP65COAGJLX -p tcp -m tcp -j DNAT --to-destination 172.16.2.7:9200
</code></pre>

<p data-lines="2" data-type="p" data-sign="5bcc38ab7b445557df3386952205f317">可以看到，这三条链，其实是三条 DNAT 规则。但在 DNAT 规则之前，iptables 对流入的 IP 包还设置了一个“标志”（通过KUBE-MARK-MASQ链设置–set-xmark）。这个“标志”的作用对于符合条件的包 set mark 0x4000, 有此标记的数据包会在KUBE-POSTROUTING chain中统一做MASQUERADE为SNAT做准备 。而 DNAT 规则的作用，就是在 PREROUTING 检查点之前，也就是在路由之前，将流入 IP 包的目的地址和端口，改成–to-destination 所指定的新的目的地址和端口。可以看到，这个目的地址和端口，正是被代理 Pod 的 IP 地址和端口。这样，访问 Service VIP 的 IP 包经过上述 iptables 处理之后，就已经变成了访问具体某一个后端 Pod 的 IP 包了。不难理解，这些 Endpoints 对应的 iptables 规则，正是 kube-proxy 通过监听 Pod 的变化事件，在宿主机上生成并维护的。</p><p data-lines="2" data-type="p" data-sign="05546078d21d8bb55a9ba4daf757f636">以上，就是 Service 最基本的工作原理。</p><p data-lines="2" data-type="p" data-sign="f4eb07cdbe8b9d3972277fc8f238f6eb">此外，你可能已经听说过，Kubernetes 的 kube-proxy 还支持一种叫作 IPVS 的模式。这又是怎么一回事儿呢？</p><p data-lines="2" data-type="p" data-sign="42f035850b0520d92da1387beef3745d">其实，通过上面的讲解，你可以看到，kube-proxy 通过 iptables 处理 Service 的过程，其实需要在宿主机上设置相当多的 iptables 规则。而且，kube-proxy 还需要在控制循环里不断地刷新这些规则来确保它们始终是正确的。</p><p data-lines="2" data-type="p" data-sign="c0afe06cc1cee7d57f3f5433de8c74fd">不难想到，当你的宿主机上有大量 Pod 的时候，成百上千条 iptables 规则不断地被刷新，会大量占用该宿主机的 CPU 资源，甚至会让宿主机“卡”在这个过程中。所以说，<strong>一直以来，基于 iptables 的 Service 实现，都是制约 Kubernetes 项目承载更多量级的 Pod 的主要障碍。</strong></p><p data-lines="2" data-type="p" data-sign="607700e68489c9d15146bf8e8f7bf57d">而 IPVS 模式的 Service，就是解决这个问题的一个行之有效的方法。</p><p data-lines="1" data-type="p" data-sign="44cb96dbbf9b3079d733f31fb2f96bc7">IPVS 模式的工作原理，其实跟 iptables 模式类似。当我们创建了前面的 Service 之后，kube-proxy 首先会在宿主机上创建一个虚拟网卡（叫作：kube-ipvs0），并为它分配 Service VIP 作为 IP 地址，如下所示：</p><div data-sign="df85c53b26221789014344e240d9b7cd" data-type="codeBlock" data-lines="10"><pre><code>[root@VM_27_156_centos ~]#  kubectl get svc -n kube-system
NAME                  TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)         AGE
hpa-metrics-service   ClusterIP   172.16.159.69    &lt;none&gt;        443/TCP         83d
kube-dns              ClusterIP   172.16.158.116   &lt;none&gt;        53/TCP,53/UDP   83d
[root@VM_27_156_centos ~]# ip ad | grep ipv
4: kube-ipvs0: &lt;BROADCAST,NOARP&gt; mtu 1500 qdisc noop state DOWN
    inet 172.16.159.69/32 brd 172.16.159.69 scope global kube-ipvs0
</code></pre>

<p data-lines="1" data-type="p" data-sign="cb9f57b5db1d1e8b1f89596824cea4bd">而接下来，kube-proxy 就会通过 Linux 的 IPVS 模块，为这个 IP 地址设置三个 IPVS 虚拟主机，并设置这三个虚拟主机之间使用轮询模式 (rr) 来作为负载均衡策略。我们可以通过 ipvsadm 查看到这个设置，如下所示：</p><div data-sign="7705ca3b8f54106a2063aaea84404706" data-type="codeBlock" data-lines="16"><pre><code>[root@VM_27_156_centos ~]# ipvsadm -ln
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -&gt; RemoteAddress:Port           Forward Weight ActiveConn InActConn
TCP  127.0.0.1:30762 rr
  -&gt; 172.16.128.181:80            Masq    1      0          0
TCP  127.0.0.1:31017 rr
  -&gt; 172.16.128.239:80            Masq    1      0          0
TCP  127.0.0.1:31244 rr
  -&gt; 172.16.129.7:1358            Masq    1      0          0
TCP  172.16.128.129:30263 rr
TCP  172.16.128.129:30344 rr
  -&gt; 172.16.128.196:80            Masq    1      0          0
</code></pre>

<p data-lines="2" data-type="p" data-sign="8908aa8e4c36e1bf97a253ecd119133b">可以看到，这三个 IPVS 虚拟主机的 IP 地址和端口，对应的正是三个被代理的 Pod。</p><p data-lines="2" data-type="p" data-sign="664295d8404234cdf6044b73e84d4e30">这时候，任何发往 172.16.128.181:80 的请求，就都会被 IPVS 模块转发到某一个后端 Pod 上了。</p><p data-lines="2" data-type="p" data-sign="06337e37f862dcedc76c7985d2933aaf">而相比于 iptables，IPVS 在内核中的实现其实也是基于 Netfilter 的 NAT 模式，所以在转发这一层上，理论上 IPVS 并没有显著的性能提升。但是，IPVS 并不需要在宿主机上为每个 Pod 设置 iptables 规则，而是把对这些“规则”的处理放到了内核态，从而极大地降低了维护这些规则的代价。这也正印证了我在前面提到过的，“将重要操作放入内核态”是提高性能的重要手段。    </p><p data-lines="2" data-type="p" data-sign="19a89aef908216c19acedc5a2a78a91b">不过需要注意的是，IPVS 模块只负责上述的负载均衡和代理功能。而一个完整的 Service 流程正常工作所需要的包过滤、SNAT 等操作，还是要靠 iptables 来实现。只不过，这些辅助性的 iptables 规则数量有限，也不会随着 Pod 数量的增加而增加。</p><p data-lines="2" data-type="p" data-sign="718ff03925a4f7834761991ead8e82d4">所以，在大规模集群里，我非常建议你为 kube-proxy 设置–proxy-mode=ipvs 来开启这个功能。它为 Kubernetes 集群规模带来的提升，还是非常巨大的。</p><p data-lines="2" data-type="p" data-sign="1a02278f8cc19ac125b816e28c42ebff">原理已介绍完毕，接下来看下大概的流量流程图， 如下图所示：    </p><p data-lines="2" data-type="p" data-sign="e68bf78bb66425718f99a97b4bebbf0d" style=""><img alt="" src="/logbook/images/linux/从0到1聊聊kubernetes service 到 pod的网络链路定位/9105a869ac3b.png" style="position: relative; z-index: 2;" class="amplify"></p><p data-lines="3" data-type="br" data-sign="br3">&nbsp;</p><h2 data-lines="1" data-sign="3edab15a252591ce8a8e16da8e42c3e9" id="service%E5%88%B0pod%E7%BD%91%E7%BB%9C%E9%93%BE%E8%B7%AF%E7%A4%BA%E4%BE%8B%E5%88%86%E6%9E%90"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#service%E5%88%B0pod%E7%BD%91%E7%BB%9C%E9%93%BE%E8%B7%AF%E7%A4%BA%E4%BE%8B%E5%88%86%E6%9E%90" class="anchor"></a>service到pod网络链路示例分析</h2><p data-lines="2" data-type="p" data-sign="9b047ab91192c54a6e4a638c25ecce2b">原理已掌握，那如何配合原理解决实际问题？下图是service 到 pod 网络链路分析的流程图：    </p><p data-lines="2" data-type="p" data-sign="b6fdb277897acb915e2dbea561a7e889" style=""><img alt="" src="/logbook/images/linux/从0到1聊聊kubernetes service 到 pod的网络链路定位/3204c99dc4f4.png" style="position: relative; z-index: 2;"></p><p data-lines="2" data-type="p" data-sign="1f8c228f9f029d253c458afeccfe5d0a">接下来通过pod尚在not ready状态时就开始有业务流量进入例子实战分析。</p><h5 data-lines="2" data-sign="d60cb0cb1d5eab9efa148fdecf8717ec" id="1-%E7%A1%AE%E8%AE%A4%E5%BD%93%E5%89%8D%E7%8E%AF%E5%A2%83%E6%98%AFiptables-%E6%88%96-ipvs"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#1-%E7%A1%AE%E8%AE%A4%E5%BD%93%E5%89%8D%E7%8E%AF%E5%A2%83%E6%98%AFiptables-%E6%88%96-ipvs" class="anchor"></a>1. 确认当前环境是iptables 或 ipvs</h5><p data-lines="1" data-type="p" data-sign="88849764aa07898700050148a59b85ce">通过查看kube-proxy 配置文件确认是否开启ipvs：    </p><div data-sign="ac81f519eafd419361213450363dee6b" data-type="codeBlock" data-lines="20"><pre><code># 开启ipvs
[root@VM_27_156_centos ~]# cat /etc/kubernetes/kube-proxy
MASQUERADE_ALL="--masquerade-all=true"
IPVS_SCHEDULER="--ipvs-scheduler=rr" # ipvs 负载均衡策略
IPVS_MIN_SYNC_PERIOD="--ipvs-min-sync-period=1s"
HOSTNAME_OVERRIDE="--hostname-override=1x.x.x.y"
KUBECONFIG="--kubeconfig=/etc/kubernetes/kubeproxy-kubeconfig"
IPVS_SYNC_PERIOD="--ipvs-sync-period=5s"
V="--v=2"
PROXY_MODE="--proxy-mode=ipvs" # 启动了ipvs，若是iptables则不会有这个设置

# 使用iptables
[root@VM_24_43_centos ~]# cat /etc/kubernetes/kube-proxy
V="--v=2"
HOSTNAME_OVERRIDE="--hostname-override=10.26.24.43"
KUBECONFIG="--kubeconfig=/etc/kubernetes/kubeproxy-kubeconfig"

</code></pre>

<p data-lines="1" data-type="p" data-sign="574930fd84e644108c71e86b965fb11b">kube-proxy 配置文件不一定是在/etc/kubernetes/目录下，也有可能直接通过configmap方式挂载，为此通过kube-proxy 配置文件查看需要根据实际情况找到kube-proxy配置文件。有没有更快速方法确定到底使用的是ipvs还是iptables呢？ 当然有，其实只需要通过iptables-save命令查看即可快速确认是否采用哪种模式。如下所示：        </p><div data-sign="94b68275055a629ae83598e8b4569818" data-type="codeBlock" data-lines="40"><pre><code># 使用iptables
...
-A KUBE-SVC-WXR6WDM6ASCPSYWK -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-ZVKDBRHJUGWWPSCX
-A KUBE-SVC-WXR6WDM6ASCPSYWK -j KUBE-SEP-3NB7RG36OMJ2OTYG
-A KUBE-SVC-WYEU5GYTOACWWH2H -j KUBE-SEP-RZOYF7X4QTGHRIUZ
-A KUBE-SVC-WYPG2HFD6NQWUD3O -m statistic --mode random --probability 0.25000000000 -j KUBE-SEP-ZN4XLDVG3UXF3BYX
-A KUBE-SVC-WYPG2HFD6NQWUD3O -m statistic --mode random --probability 0.33332999982 -j KUBE-SEP-YQSJFJLDPNMWWAG2
-A KUBE-SVC-WYPG2HFD6NQWUD3O -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-EMAQR5ULITZF3NZ3
-A KUBE-SVC-WYPG2HFD6NQWUD3O -j KUBE-SEP-GRJIGAH5VYJMAB5G
-A KUBE-SVC-WYQJ3DTTDOGESYBK -j KUBE-SEP-6AJEHI5DMIZPR5MF
...

若采用了iptables模式的service一般都带以上这些iptables 规则。

# 使用ipvs
A KUBE-POSTROUTING -m comment --comment "Kubernetes endpoints dst ip:port, source ip for solving hairpin purpose" -m set --match-set KUBE-LOOP-BACK dst,dst,src -j MASQUERADE
-A KUBE-SERVICES -m comment --comment "Kubernetes service lb portal" -m set --match-set KUBE-LOAD-BALANCER dst,dst -j KUBE-LOAD-BALANCER
-A KUBE-SERVICES -m comment --comment "Kubernetes service cluster ip + port for masquerade purpose" -m set --match-set KUBE-CLUSTER-IP dst,dst -j KUBE-MARK-MASQ
-A KUBE-SERVICES -m addrtype --dst-type LOCAL -j KUBE-NODE-PORT

ipvs 并没有类似iptables 那样关于pod相关的iptables规则，并且ipvs的iptables 规则很精简，通常就包含了一些主要的链相关的iptables规则设置。

需要检查更多pod ip tcp建立连接情况可以ssh到pod所在节点上做如下操作:
cd /proc/net
more ip_vs_conn_sync/ip_vs_conn
Pro FromIP   FPrt ToIP     TPrt DestIP   DPrt State       Origin Expires
TCP 0A63DDC2 9BC4 0A631A8B 7F6F AC10A419 1F48 TIME_WAIT   LOCAL       10
TCP 0A631AD5 DBE5 0A631A8B 7CBE AC10A9D2 1F90 SYN_RECV    LOCAL       41
TCP 0A631AB6 6D81 0A631A8B 7A50 0A631B07 1F90 SYN_RECV    LOCAL       50
TCP 0A631AAC 8BBD 0A631A8B 7DB7 0A631B35 1F90 SYN_RECV    LOCAL       40
TCP 0A63DDC2 A168 0A631A8B 7F6F AC10A00C 1F48 TIME_WAIT   LOCAL       54
TCP AC10A07A C81C AC10BBF4 0050 AC10A076 0050 TIME_WAIT   LOCAL       86
UDP AC10A07B EAD7 AC10BED4 0035 AC10A9CE 0035 UDP         LOCAL       43
TCP 0A631AA5 D609 0A631A8B 7F0B AC10A0AB 1F90 SYN_RECV    LOCAL       58

从这里可以看到从哪个"IP:端口"发起请求，经过哪"IP:端口"代理，到最终"IP:端口"，当前连接处于什么状态，只需要将pod ip地址转换成十六进制，端口则是从十进制转换成十六进制进行定位分析。或者用“conntrack -Ln”命令（适用Netfilter 技术栈，比如：iptables，ipvs）

</code></pre>

<h5 data-lines="2" data-sign="d36de1c7bd688691ad8c240dc7611cf9" id="2-%E8%8E%B7%E5%8F%96service-ip%E5%9C%B0%E5%9D%80"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#2-%E8%8E%B7%E5%8F%96service-ip%E5%9C%B0%E5%9D%80" class="anchor"></a>2. 获取service ip地址</h5><p data-lines="1" data-type="p" data-sign="0ee16da0485b706a31b195eb1c514aa6">获取service ip地址是为了通过iptables-save命令/ipvsadm 命令查看当前kube 自定义链(KUBE-SERVICE或KUBE_NODEPORT等)链与pod ip 负载均衡的相关规则。</p><div data-sign="762c7599f6cd12bc4fcd4cf7a4d27151" data-type="codeBlock" data-lines="12"><pre><code># iptables 模式
[root@VM_197_156_centos ~]# kubectl get svc
NAME                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
log-test-svc           ClusterIP   172.16.31.250   &lt;none&gt;        80/TCP    38s

# ipvs 模式
[root@VM_27_156_centos /data/cyh]# kubectl get svc
NAME           TYPE           CLUSTER-IP       EXTERNAL-IP    PORT(S)         AGE
log-test-svc   ClusterIP      172.16.153.144   &lt;none&gt;         80/TCP          9s

</code></pre>

<h5 data-lines="2" data-sign="2ad6811aa2829a90974389ef8da0f75f" id="3-%E6%A0%B9%E6%8D%AEservice-ip-%E5%9C%B0%E5%9D%80%E8%BF%BD%E5%AF%BBpod-ip%E8%B4%9F%E8%BD%BD%E5%9D%87%E8%A1%A1"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#3-%E6%A0%B9%E6%8D%AEservice-ip-%E5%9C%B0%E5%9D%80%E8%BF%BD%E5%AF%BBpod-ip%E8%B4%9F%E8%BD%BD%E5%9D%87%E8%A1%A1" class="anchor"></a>3. 根据service ip 地址追寻pod ip负载均衡</h5><p data-lines="1" data-type="p" data-sign="ca171560fe7001b198bad726730623fa">我们先来看iptables 模式下的iptables 负载均衡：</p><div data-sign="fcbaca9d9b089358f1b47f8ffdac9149" data-type="codeBlock" data-lines="89"><pre><code>[root@VM_197_156_centos ~]# iptables-save | grep 172.16.31.250
-A KUBE-SERVICES -d 172.16.31.250/32 -p tcp -m comment --comment "default/log-test-svc:tcp-80-80 cluster IP" -m tcp --dport 80 -j KUBE-SVC-AQE36IJ35YYI2EX3

# 根据service ip 可以获取到service ip 下一跳的 iptables 链 KUBE-SVC-AQE36IJ35YYI2EX3， 我们再根据KUBE-SVC-AQE36IJ35YYI2EX3 链即可找到pod ip 目标 iptables 规则：
[root@VM_197_156_centos ~]# iptables-save | grep KUBE-SVC-AQE36IJ35YYI2EX3
:KUBE-SVC-AQE36IJ35YYI2EX3 - [0:0]
-A KUBE-SERVICES -d 172.16.31.250/32 -p tcp -m comment --comment "default/log-test-svc:tcp-80-80 cluster IP" -m tcp --dport 80 -j KUBE-SVC-AQE36IJ35YYI2EX3
-A KUBE-SVC-AQE36IJ35YYI2EX3 -m statistic --mode random --probability 0.33332999982 -j KUBE-SEP-3UCY2DW22C7NZ2EC
-A KUBE-SVC-AQE36IJ35YYI2EX3 -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-5DWF3POVR3KORS2S
-A KUBE-SVC-AQE36IJ35YYI2EX3 -j KUBE-SEP-V3THYN75ZNVYIPX6

从以上结果我们可以看到service 的下一跳链对应的pod 链负载均衡模式以及流量的负载的比例；我们再根据具体的pod的链查看pod 链的明细，比如KUBE-SEP-3UCY2DW22C7NZ2EC的明细：
[root@VM_197_156_centos ~]# iptables-save | grep KUBE-SEP-3UCY2DW22C7NZ2EC
:KUBE-SEP-3UCY2DW22C7NZ2EC - [0:0]
-A KUBE-SEP-3UCY2DW22C7NZ2EC -s 172.16.0.27/32 -j KUBE-MARK-MASQ
-A KUBE-SEP-3UCY2DW22C7NZ2EC -p tcp -m tcp -j DNAT --to-destination 172.16.0.27:80
-A KUBE-SVC-AQE36IJ35YYI2EX3 -m statistic --mode random --probability 0.33332999982 -j KUBE-SEP-3UCY2DW22C7NZ2EC

其实当定位pod 尚处于 not ready状态时就有流量进入只需要到service 的下一跳链即可，无需查看pod明细链，因为service 的下一跳链 的明细我们就可以观察当新的pod处于ready状态时薪的负载规则的创建和旧的pod负载规则删除。

定位pod尚处于not ready 状态就有流量进入问题，需要注意将健康检查时间的initialDelaySeconds参数设置足够长时间比如：180，用来准备观察操作，比如新pod 访问日志以及service 下一跳链变化wathc，当然服务副本数设置为1更有利于定位分析。
比如：
测试服务健康检查设置：
livenessProbe:
  failureThreshold: 2
  initialDelaySeconds: 180
  periodSeconds: 3
  successThreshold: 1
  httpGet:
    port: 80
    path: /
  timeoutSeconds: 2
readinessProbe:
  failureThreshold: 2
  initialDelaySeconds: 180
  periodSeconds: 3
  successThreshold: 1
  httpGet:
    port: 80
    path: /
  timeoutSeconds: 2

我们改变下deployment一个配置，比如健康检查时间或者镜像什么的用来触发新版本pod的创建：
[root@VM_197_156_centos ~]# kubectl get pod
NAME                        READY   STATUS    RESTARTS   AGE
log-test-6c4dd57c6d-jdcbs   0/1     Running   0          4s
log-test-f99d7d6fb-h7947    1/1     Running   0          2m28s

已经触发新版本创建，接下来我们观察新版pod的访问日志：

[root@VM_197_156_centos ~]# kubectl exec -ti log-test-6c4dd57c6d-jdcbs /bin/bash
root@log-test-6c4dd57c6d-jdcbs:/# cd /data/logs/nginx/logs/
root@log-test-6c4dd57c6d-jdcbs:/data/logs/nginx/logs# ls
access.log  error.log
root@log-test-6c4dd57c6d-jdcbs:/data/logs/nginx/logs# tail  -f access.log

此时暂时没有流量进入新pod。

观察service 下一跳链的iptables规则变化:

[root@VM_197_156_centos ~]# for i in {1..10000}; do iptables-save | grep KUBE-SVC-AQE36IJ35YYI2EX3 &amp;&amp; sleep 1 ;done
:KUBE-SVC-AQE36IJ35YYI2EX3 - [0:0]
-A KUBE-SERVICES -d 172.16.31.250/32 -p tcp -m comment --comment "default/log-test-svc:tcp-80-80 cluster IP" -m tcp --dport 80 -j KUBE-SVC-AQE36IJ35YYI2EX3
-A KUBE-SVC-AQE36IJ35YYI2EX3 -j KUBE-SEP-EDYWNHLXPB6XYTC5

当新pod处于ready状态后，可以发现新pod有访问日志，另外service 下一跳链的iptables规则也发生了变更：
[root@VM_197_156_centos ~]# kubectl get pod
NAME                        READY   STATUS        RESTARTS   AGE
log-test-6c4dd57c6d-jdcbs   1/1     Running       0          3m01s
log-test-f99d7d6fb-h7947    1/1     Terminating   0          5m25s

root@log-test-6c4dd57c6d-jdcbs:/data/logs/nginx/logs# tail  -f access.log
{"time_local":"2020-06-14T09:54:12+00:00","client_ip":"","remote_addr":"x.x.199.56","remote_user":"","request":"GET / HTTP/1.1","status":"200","body_bytes_sent":"612","request_time":"0.000","http_referrer":"","http_user_agent":"kube-probe/1.16","request_id":"8d4d649f5cd7551ca7173c96e967b0fb"}
...

[root@VM_197_156_centos ~]# for i in {1..10000}; do iptables-save | grep KUBE-SVC-AQE36IJ35YYI2EX3 &amp;&amp; sleep 1 ;done
:KUBE-SVC-AQE36IJ35YYI2EX3 - [0:0]
-A KUBE-SERVICES -d 172.16.31.250/32 -p tcp -m comment --comment "default/log-test-svc:tcp-80-80 cluster IP" -m tcp --dport 80 -j KUBE-SVC-AQE36IJ35YYI2EX3
-A KUBE-SVC-AQE36IJ35YYI2EX3 -j KUBE-SEP-EDYWNHLXPB6XYTC5

...

:KUBE-SVC-AQE36IJ35YYI2EX3 - [0:0]
-A KUBE-SERVICES -d 172.16.31.250/32 -p tcp -m comment --comment "default/log-test-svc:tcp-80-80 cluster IP" -m tcp --dport 80 -j KUBE-SVC-AQE36IJ35YYI2EX3
-A KUBE-SVC-AQE36IJ35YYI2EX3 -j KUBE-SEP-MCLJ6WU2SKYADXJ3

</code></pre>

<p data-lines="1" data-type="p" data-sign="5c637424c24817b4e274a72b979f712f">接下来再看看ipvs负载均衡：</p><div data-sign="f27c2ac4d0e4a19061a85aec40f16bf1" data-type="codeBlock" data-lines="25"><pre><code>[root@VM_27_156_centos /data/cyh]# ipvsadm -ln | grep 172.16.153.144
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -&gt; RemoteAddress:Port           Forward Weight ActiveConn InActConn

...

TCP  172.16.153.144:80 rr
  -&gt; 172.16.128.185:80            Masq    1      0          0
  -&gt; 172.16.128.241:80            Masq    1      0          0
  -&gt; 172.16.129.16:80             Masq    1      0          0

...

[root@VM_27_156_centos /data/cyh]# kubectl get pods -o wide
NAME                        READY   STATUS    RESTARTS   AGE   IP               NODE           NOMINATED NODE   READINESS GATES
log-test-5cbd4bc5d5-db7ws   1/1     Running   0          38m   172.16.128.241   10.x.x.y   &lt;none&gt;           &lt;none&gt;
log-test-5cbd4bc5d5-j6jln   1/1     Running   0          38m   172.16.128.185   10.x.x.k   &lt;none&gt;           &lt;none&gt;
log-test-5cbd4bc5d5-tp2lq   1/1     Running   0          62m   172.16.129.16    10.x.x.z   &lt;none&gt;           &lt;none&gt;

我们可以发现service ip 172.16.153.144:80 通过rr 也就是轮询模式负载了172.16.128.241，172.16.128.185，172.16.129.16。对于pod尚在not ready 定位观察新pod的访问日志以及健康检查设置和iptables 类似，只不过观察service ip负载均衡pod ip 列表变化转化为通过ipvsadm -ln | grep ${service-ip} ， 在这不在赘述。

</code></pre>

<p data-lines="1" data-type="p" data-sign="9fbd74bc57d92d03be92924d0ce3415f">tcpdump 命令我们可以用来定位流量，不过这个建议跨节点访问抓包，定位ipvs 模式下pod 处于Terminating 状态是否存在流量进入，我们可以通过如下操作进行定位：</p><div data-sign="c9d2fa4df0fe525bb112478ffe3f35bc" data-type="codeBlock" data-lines="44"><pre><code>[root@VM_27_156_centos /data/cyh]# kubectl get pods -o wide
NAME                        READY   STATUS    RESTARTS   AGE     IP               NODE           NOMINATED NODE   READINESS GATES
log-test-6c7d8575d5-59jk8   0/1     Running   0          87s     172.16.129.20    1x.x.27.165   &lt;none&gt;           &lt;none&gt;
log-test-cf8cf596f-nk52d    1/1     Running   0          10m     172.16.128.186   1x.x.27.156   &lt;none&gt;           &lt;none&gt;
log-test-cf8cf596f-npc8h    1/1     Running   0          10m     172.16.128.242   1x.x.27.146   &lt;none&gt;           &lt;none&gt;
log-test-cf8cf596f-rbvcb    1/1     Running   0          4m37s   172.16.129.19    1x.x.27.165   &lt;none&gt;           &lt;none&gt;

通过访问服务的service ip 测试pod 负载均衡情况：
for i in {1..10000};do curl -s -v http://172.16.153.144/ &amp;&amp; sleep 1;done

针对不在当前节点的pod ip进行抓包：
tcpdump -i eth1 -nn host 172.16.129.19
18:40:13.921362 IP 1x.x.27.156.45606 &gt; 172.16.129.19.80: Flags [.], ack 851, win 261, options [nop,nop,TS val 4271317408 ecr 3695053014], length 0
18:40:13.921551 IP 1x.x.27.156.45606 &gt; 172.16.129.19.80: Flags [F.], seq 79, ack 851, win 261, options [nop,nop,TS val 4271317408 ecr 3695053014], length 0
18:40:13.921657 IP 172.16.129.19.80 &gt; 1x.x.27.156.45606: Flags [F.], seq 851, ack 80, win 57, options [nop,nop,TS val 3695053014 ecr 4271317408], length 0
18:40:13.921681 IP 1x.x.27.156.45606 &gt; 172.16.129.19.80: Flags [.], ack 852, win 261, options [nop,nop,TS val 4271317409 ecr 3695053014], length 0

查看当前ipvs service 负载列表变化情况：
for i in {1..10000};do ipvsadm -ln | grep 172.16.153.144 -A 5 &amp;&amp; sleep 1; done
TCP  172.16.153.144:80 rr
  -&gt; 172.16.128.186:80            Masq    1      0          41
  -&gt; 172.16.128.242:80            Masq    1      0          40
  -&gt; 172.16.129.19:80             Masq    1      0          41
...

改变deployment触发新版变更：
[root@VM_27_156_centos /data/cyh]# kubectl get pods -o wide
NAME                        READY   STATUS        RESTARTS   AGE     IP               NODE           NOMINATED NODE   READINESS GATES
log-test-6c7d8575d5-59jk8   1/1     Running       0          2m30s   172.16.129.20    1x.x.27.165   &lt;none&gt;           &lt;none&gt;
log-test-6c7d8575d5-xr6j7   0/1     Running       0          27s     172.16.128.243   1x.x.27.146   &lt;none&gt;           &lt;none&gt;
log-test-cf8cf596f-nk52d    1/1     Running       0          11m     172.16.128.186   1x.x.27.156   &lt;none&gt;           &lt;none&gt;
log-test-cf8cf596f-npc8h    1/1     Running       0          11m     172.16.128.242   1x.x.27.146   &lt;none&gt;           &lt;none&gt;
log-test-cf8cf596f-rbvcb    1/1     Terminating   0          5m40s   172.16.129.19    1x.x.27.165   &lt;none&gt;           &lt;none&gt;

当抓包的Pod 处于Terminating 查看抓包是否还有流量？并且ipvs service 的负载均衡该pod ip 流量权重已变为0：
TCP  172.16.153.144:80 rr
  -&gt; 172.16.128.186:80            Masq    1      0          40
  -&gt; 172.16.128.242:80            Masq    1      0          40
  -&gt; 172.16.129.19:80             Masq    0      0          13
  -&gt; 172.16.129.20:80             Masq    1      0          27

</code></pre>

<p data-lines="2" data-type="p" data-sign="d1a4f4f9e63ee43cb392dc03d483506a">至此已从初识service, service 应用场景，service实现原理到实战分析讲解完毕。</p><h2 data-lines="2" data-sign="78ca4c52344112800ef234e1606eae40" id="%E5%8F%82%E8%80%83%EF%BC%9A"><a href="https://km.woa.com/group/11791/articles/show/426476?kmref=search&amp;from_page=1&amp;no=6#%E5%8F%82%E8%80%83%EF%BC%9A" class="anchor"></a>参考：</h2><p data-lines="2" data-type="p" data-sign="d280ec878ba2f5e2a948d3fd76d43a2e"><a rel="nofollow" href="https://kubernetes.io/zh/docs/concepts/services-networking/service/#externalname">kubernetes-official-Services</a></p><p data-lines="2" data-type="p" data-sign="99a5ef6b2a6e19e2838a204bbcd02263"><a rel="nofollow" href="https://www.jianshu.com/p/89f126b241db?utm_campaign=maleskine&amp;utm_content=note&amp;utm_medium=seo_notes&amp;utm_source=recommendation">k8s集群中ipvs负载详解</a></p><p data-lines="2" data-type="p" data-sign="556f3c0760dae5f9a7d2a7941fe42d33"><a rel="nofollow" href="https://blog.csdn.net/u010771890/article/details/103226784">K8s网络实战分析之service调用</a></p><p data-lines="2" data-type="p" data-sign="69fc0db2e9f01275296b6147cd83651a"><a rel="nofollow" href="https://www.cnblogs.com/charlieroro/p/9588019.html">理解kubernetes环境的iptables</a></p><p data-lines="2" data-type="p" data-sign="1f71ce5bcc15c0fdd37e78c9b4b09766"><a rel="nofollow" href="https://github.com/kubernetes/kubernetes/blob/master/pkg/proxy/ipvs/proxier.go">kubernetes-source-code-ipvs-kube-proxy</a></p><p data-lines="2" data-type="p" data-sign="e6893099f340a91f1f2e55cd5365cfa2"><a rel="nofollow" href="https://github.com/kubernetes/kubernetes/blob/master/pkg/proxy/iptables/proxier.go">kubernetes-source-code-iptables-kube-proxy</a></p>				</div>
