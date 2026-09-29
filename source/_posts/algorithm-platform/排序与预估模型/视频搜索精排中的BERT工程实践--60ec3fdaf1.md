---
title: "视频搜索精排中的BERT工程实践"
date: 2022-04-16 13:36:48
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<h2>业务背景</h2>
<p>    搜索相关性代表着搜索结果和用户查询词之间的匹配程度。保证高度的相关性是一个搜索引擎的核心能力，结果不相关的搜索引擎对用户来说毫无价值。</p>
<p>    和几乎所有的在线系统一样，快速响应是对搜索引擎的基本要求。现在业界会通过各种算法来提升结果的相关性、CTR等指标，而随着算法越来越复杂，在线服务的响应速度和资源消耗会面临更多的挑战。</p>
<p>    视频搜索排序场景下，算法团队通过多次调研和实验，选择在精排阶段使用 BERT 模型来帮助提升搜索结果的相关性(详情见  《站在BERT的肩膀上——视频搜索中的深度语义匹配模型》)。尝试引入BERT模型不仅带来了算法应用上的困难，也给在线工程带来了很多挑战，这里介绍下工程上如何应对BERT模型全量上线带来的挑战。</p>
<p><br/></p>
<h2>系统架构简介</h2>
<p>    一个基本的搜索系统大体可以分为离线挖掘和在线检索两部分，其中包含的重要模块主要有：Item内容理解、Query理解、检索召回、排序模块等。整个检索系统的目标可以抽象为给定query，检索出最能满足用户需求的item. 简易流程图如下所示：</p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/12236ddfd3e617cf3b3d.png"/></p>
<p>   视频搜索系统的实现思路与上述类似，其分层架构如下图所示：               </p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e6859490e9657e648b3d.png"/></p>
<p>   本篇文章将注意力聚焦在排序层的精排相关性模型上，对应上图中用深红色颜色标出的模块。如“业务背景”一节所述，算法同学尝试在精排阶段引入BERT模型来提高排序结果相关性。具体模型结构如下所示：</p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/38c4c618a43de68714ac.png"/></p>
<p>其中，绿色方框标注的 BERT score 为BERT 模型计算得出的 query 和 doc 的相关性得分，该得分被作为一路特征进入GBDT 模型参与最终的query和doc的相关性计算。</p>
<p> 相关性精排服务对应的在线服务拓扑结构如下:</p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/73dee80acfd191be8b4e.png"/></p>
<h2>系统性能面临挑战</h2>
<p>    视频作为国内长视频领域的龙头产品，用户DAU 达到亿级别，视频搜索每天搜索请求量达到数亿级别。相关性精排服务的高峰期达到数w 量级qps ，单机qps(16核)  几k量级， 单个请求的视频数为50。</p>
<p>    BERT 模型是基于 Transformer 的双向编码表示模型，它本身就是一个非常重的模型。视频搜索相关性精排使用的BERT 模型是在4层BERT 网络之后加入了分类网络进行fine-tuning 得到，模型结构如下：</p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/015fa30eba37faa544c5.png"/></p>
<p>    同时，为了保证搜索引擎整体的极致响应速度，视频搜索相关性精排对于BERT模型服务推理的耗时可接受平均耗时 &lt; 10ms，99.9 分位耗时 &lt; 50ms。</p>
<p>    因此，BERT 模型需要在满足高吞吐低延时的条件下，进行大计算量的模型推理。</p>
<h2>上线优化</h2>
<p>     4层的BERT模型全量上线，对于工程和算法的挑战非常巨大。最开始使用Tensorflow 进行模型线上推理测试，发现如果要全量上线4层的BERT模型需要近20000核的CPU资源。</p>
<p>    为了能够在尽可能少的消耗资源的情况下全量上线，算法和工程团队都做了很多工作。《站在BERT的肩膀上——视频搜索中的深度语义匹配模型》 和 《模型蒸馏优化——视频query-doc匹配模型》两篇文章中介绍了算法团队进行的一系列努力，最终在保证效果的前提下，将4层 BERT网络压缩为1层，从而极大的降低了计算量（约 70% - 80%）。而工程同学则从如下几个方面进行了一系列的优化工作。</p>
<h3>1.推理框架的选择和优化</h3>
<p>    机器学习领域通用的推理框架百花齐放，如Tensorflow、Libtorch、ONNX Runtime 等等，专用的推理框架也层出不穷，比如针对Transformer模型推理的 TurboTransformers。不同的框架各有优劣，Tensorflow 应用广泛，ONNX Runtime 通过算子融合等手段优化性能，TurboTransformers 重写了transformer中的大部分逻辑，对transformer进行针对性优化，但没有一个针对上述各种推理框架使用相同的模型、测试数据的benchmark。因此首先针对Tensorflow， Libtorch, ONNX Runtime, TurboTransformers 等推理方案进行了各自框架的调优以及一轮benchmark（详情见《几种模型推理框架的BERT推理性能测试》）</p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ed750d84c4cea360abfb.png"/></p>
<p>    上图展示的是在batch size = 26， token length = 64 时，不同框架在线程数分别为1，2，4，8情况下的推理耗时。可见 TurboTransformer 在单线程下性能最优，但是多线程下性能严重恶化；多线程下，ONNX Runtime 框架在几类可选方案中更具优势(推理性能对比 ONNX Runtime : Tensorflow : TurboTransformers : Libtorch = 1 : 0.65 : 0.097 : 0.48)。</p>
<p>    另外，对比了基于 TensorRT的GPU 方案和 ONNX Runtime 的CPU方案，GPU 方案虽然性能更优，但是消耗的GPU资源换算成费用要比ONNX Runtime的CPU 方案多了3倍，因此最终采用 ONNX Runtime的CPU 方案进行线上推理。</p>
<h3>2.服务框架的选择和优化</h3>
<h4>2.1 tRPC runtime 选型</h4>
<p>     内部的在线服务在逐步统一到tRPC 框架上，tRPC  框架相比它的前辈 spp 和 taf 有着性能、易用性、扩展性等方面的诸多优势，因此考虑使用tRPC-cpp(tRPC 的cpp 语言版本) 框架搭建服务。tRPC-cpp 支持不同类型的服务端运行时模式（线程/协程调度模型）。我们尝试上线的BERT模型服务，是个典型的CPU bound服务，适合采用 io/handle分离模式，但是同时它又是个对实时性要求高的在线服务，fiber 或许更能满足对实时性的要求。因此，使用tRPC-cpp服务搭建ONNX Runtime 推理服务并再次进行了tRPC-cpp 运行时框架的测试，从而辅助决策方案选型（详情见《BERT 模型服务 tRPC-cpp runtime 性能测试》）。从测试结果可见fiber 模式对于cpu利用率和长尾耗时控制更有优势。</p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f2a7abc27771a4667114.png"/></p>
<h4>2.2 Triton 框架的引入</h4>
<p>    Triton 是NVIDIA 推出的高性能推理服务器，可以在CPU 和 GPU 上使用所有的主流框架后端进行推理，包括 Tensorflow，Pytorch，TensorRT, ONNX Runtime。Triton 作为c++ 框架，通过共享内存通信、dynamic batcher等特性提升了服务整体推理性能。《Triton Server 性能加速对比测试》详细记录了 ONNX Runtime 推理服务使用和不使用Triton的推理性能对比。从测试结果可知Triton框架能给服务性能带来明显提升。</p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/143a75d8d1fe75ad9108.png"/></p>
<p>     的 Venus 平台在21年11月份的时候将Triton引入RondaServing 体系内，整合 tRPC 与 Triton，并推出了 TritonServable 方便用户使用。TritonServable 直接和 Venus 训练平台联动，支持一站式的模型训练&amp;部署；且支持 ONNX Runtime 推理。因此，我们直接使用了平台同学提供的TritonServable： 算法同学离线先通过Tensorflow 训练好模型，然后转成 ONNX 格式并发布到 TritonServable，TritonServable使用 ONNX Runtime backend 进行在线推理。</p>
<p><br/></p>
<p>注：目前TritonServable 的 tRPC runtime 暂不支持fiber 模式。所以目前BERT 模型服务为 tRPC io/handle 分离的TritonServable，平台同学正在加急支持TritonServable使用fiber模式，之后升级为 fiber 模式后服务性能会有进一步提升。</p>
<h3>3.缓存优化</h3>
<p>    在使用TritonServable 进行线上推理之后，BERT模型全量上线还是需要5000 核左右的cpu资源。考虑到 BERT模型更新非常不频繁（周级别更新），模型更新频率相比在线请求频率低了几个数量级，因此可以考虑在线缓存BERT模型结果来减少重复的计算。</p>
<p>    通过实现一个通用高性能的c++内存cache 组件（详情见 《一个通用高性能的c++内存cache组件》），支持key-key-value 形式的数据存储，将query 和 doc 的BERT 得分缓存在相关性精排服务内部，缓存命中率高达60%，从而减少了60% 的重复计算。</p>
<h3>4.负载均衡策略优化</h3>
<p>    由于目前的视频搜索未加入用户侧特征以及非常实时的doc侧/query侧特征，因此相同的query 召回之后进入精排阶段的doc集合在短时间内基本是恒定的，因此为了尽可能的提高缓存命中率，尝试将上游请求相关性精排服务的负载均衡策略调整为query 一致性hash，缓存命中率被提高到90%+。但是考虑到视频搜索这样的垂搜场景经常有随着热剧更新而产生的热点搜索词，为了避免query 一致性hash 造成单机热点从而影响系统整体稳定性，因此将负载均衡策略调整为query + uid 一致性hash 策略，相比于默认的负载均衡策略，缓存命中率也有明显提升（从60% 提升到77%）。</p>
<h3>5.业务逻辑层面的优化</h3>
<p>    经过上述1-4环节的优化，BERT模型全量上线需要消耗的cpu核数降低到了1000核左右。为了进一步削减资源消耗，考虑到视频搜索的流量有很多来自站外（比如QQ浏览器搜索）的请求，这些请求很多时候用户的意图并不是在视频的搜索，针对这些流量使用BERT模型提高相关性ROI 较低，且这些流量的query相比站内流量非常分散，不利于cache 命中率的提升。因此，相关性精排内部对于这些站外流量的BERT 得分计算不通过模型，而是直接赋给一个离线统计得到的默认值，从而将BERT模型全量上线消耗的CPU 核数控制在了800核左右。</p>
<p><br/></p>
<h2>总结及未来展望</h2>
<p>    最终我们通过（1）算法同学的模型压缩，（2）推理框架从Tensorflow切换到ONNX Runtime，（3）服务框架使用 tRPC + Triton(Venus平台提供的TritonServable），（4）在线服务高性能 cache，（5）站外流量的定向优化 等手段，将全量上线BERT模型所需消耗20000核CPU 削减为&lt;1000 核并完成上线。</p>
<p>        <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/fb543252b8f207250aec.png"/></p>
<p>    全量上线之后，BERT模型服务平均耗时 &lt; 8ms，99.9分位耗时 &lt; 25ms，视频搜索短视频有效曝光人均观看时长获得了1.39%的显著提升。</p>
<p><br/></p>
<p>    BERT模型的优化后续还有很多可以继续探究的地方：</p>
<p>（1）TritonServable 支持fiber 模式</p>
<p>（2）ONNX Runtime 对transformer 模型的定制化优化</p>
<p>（3）TuborTransformers 多线程下的性能加速，期望超越ONNX Runtime</p>
<p>（4）TritonServable 对 TurboTransformers backend的支持</p>
<p><br/></p>
<h2>致谢</h2>
<p>    精排相关性BERT模型全量上线，依赖很多同学的努力。</p>
<p>    感谢 chengcanye（叶澄灿）, evexlwang（王晓利），ruichenwang（王瑞琛），jinglongyi（衣景龙），penneypeng（彭婷），ziyueren（任志远），maydayfu（付豪），allensyqiu（邱思远）在模型迭代和优化上的贡献。</p>
<p>    感谢robertzhu（朱昱锦），bowenxiao（肖博文）在中台triton推理框架上的推进。</p>
<p>    感谢hebinli（李贺斌），orchardwen（温泉），liuxizhou（周智毅），kitezhu（朱旦奇），iheyhe（贺一峰），chasenzhang（张成）在模型上线部署做的工作。</p>
<p><br/></p>
<h2>相关资料</h2>
<p>[1] 站在BERT的肩膀上——视频搜索中的深度语义匹配模型</p>
<p>[2] 模型蒸馏优化——视频query-doc匹配模型</p>
<p>[3] 一个通用高性能的 c++内存cache组件</p>
<p>[4] 几种模型推理框架的BERT推理性能测试</p>
<p>[5] BERT 模型服务tRPC-cpp runtime 性能测试</p>
<p>[6] Triton Server 性能加速对比测试</p>
<p>[7] <a href="https://github.com/microsoft/onnxruntime">ONNX Runtime.ai</a></p>
<p>[8] <a href="https://github.com/triton-inference-server/server">Triton Inference Server</a></p>
<p>[9] <a href="https://github.com/Tencent/TurboTransformers">TurboTransformers</a></p> 
{% endraw %}
