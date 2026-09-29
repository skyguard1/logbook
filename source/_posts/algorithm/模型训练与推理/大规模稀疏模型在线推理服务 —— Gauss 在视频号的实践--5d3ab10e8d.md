---
title: "大规模稀疏模型在线推理服务 —— Gauss 在视频号的实践"
date: 2022-03-30 10:03:29
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<div><h4>背景</h4>
</div><div><p><strong>动机</strong></p>
</div><div><p>TTensorflow 是云帆 Oteam[2] 针对公司内使用场景，定制优化的 Tensorflow 版本。针对推荐场景下大规模稀疏参数使用原生 Tensorflow 的诸多痛点，TTensorflow 实现了一套动态Embedding API[3]，着重解决了训练过程中参数动态变化频繁，内存使用效率低下等的问题，显著提升了推荐模型在训练过程中的开发和执行效率。</p>
</div><div><p>在另一个方面，相比于离线/近线的训练任务，在线推理服务拥有更加严苛的服务质量要求（高可用，低时延等），如何为大规模稀疏模型提供在线推理服务，目前还没有标准答案。在笔者有限的经验内，将大规模稀疏模型搬上线，业界目前主流做法主要分为 2 派：1）自研参数服务器[4]，适配特定框架进行小幅度修改，例如阿里 XDL[5]，360 TensorNet[7]，微信 WePs[6]；2）自研整套深度学习框架，例如： paddlepaddle [8], 无量 [9]；此外，还有部分系统（微信 tfcc [10]）仅重写了模型的前向部分，对线上环境进行适配，这里受限于篇幅原因，笔者就不进行详细介绍了。</p>
</div><div><p>上述方案在各自的场景中，进行了不同程度的定制优化，都取得了不错的效果，但是也都存在一定的局限性。自研参数服务器的方式，一定程度上限制了用户在训练过程中对原有框架功能的使用，例如，部分在原生 PS 上执行的 Op 无法在定制的参数服务器上执行，需要额外进行开发；自研整套深度学习框架的方式，在 Tensorflow, Pytorch 大行其道的当下，开发人力成本过高，小团队自研无法跟上业界先进生产力的发展。</p>
</div><div><p>有没有一种方案，可以以较小的开发代价，充分起利用公司内外诸多成熟框架的优秀特性，为大规模稀疏模型提供在线推理服务呢？带着上述问题，笔者所在团队结合视频号场景，重新审视了大规模稀疏模型在线推理服务要求，归结起来，至少需要满足如下 3 点：</p>
</div><div><ol>
<li>模型参数量可水平扩展，大规模稀疏模型中的“大规模”描述的就是其参数量巨大，业界常见推荐模型参数大小已达到数百 GBytes 甚至 TBytes 级别[11]，在线参数存储可扩展是上线的“硬要求”；</li>
<li>模型服务高可用，视频号场景下，在线模型服务直接对接用户请求，请求失败直接影响推荐效果；</li>
<li>模型参数实时上线（分钟级甚至秒级），用户数据产生到其作用于线上模型的间隔长短直接影响模型表现[12]，此外，受推荐领域大规模稀疏模型建模方法的影响，模型参数更新上线的越及时，新产生的优质内容越能尽早的触达用户；</li>
</ol>
</div><div><p>在推理场景下，如果可以将“模型参数”与“模型结构”在部署上进行分离，本质上模型参数可以视为一种形式的只读 KeyValue 数据，可以借助司内任意一款成熟的 KV 型存储部署上线。</p>
</div><div><p>同时，笔者团队也注意到，应用于推荐场景的大规模稀疏参数模型，其参数一般由体积庞大的“稀疏部分”（GB~TB级别）和体积较小的“稠密部分”（MB级别）组成，“稀疏部分” 顾名思义，在每一轮模型训练迭代中，只有极为少量的参数参与更新，对于“稠密部分”，则全部参数都有可能参与更新。在完成一定轮次的训练迭代后，如果可以针对“稀疏部分”与“稠密部分”中存在更新的参数分别设计上线方案，理论上，可以将每次参与上线的参数量限制在较小的量级，从而可以达到参数实时同步上线的要求。</p>
</div><div><p><strong>贡献</strong></p>
</div><div><p>本文基于上述观察事实，结合 TTensorflow 与微信后台组件 —— SvrKit[13], ,WePS[6], FeatureKv(下文中称之为 FKV)[14]，设计并实现出一套应用于实时推荐场景下的稀疏参数模型推理服务部署方案，主要贡献如下：</p>
</div><div><ol>
<li>扩展 TTensorflow 能力，针对模型"稀疏部分"与"稠密部分"参数，结合推理场景，设计实现“参数导出”与“参数导入”相关功能，在不改变用户使用习惯，保持 Tensorflow 与社区版本兼容的前提下，提出并实现了一种通用的“模型结构”与“模型参数”分离部署方案，整套模型推理服务高可用，支持水平扩展；</li>
<li>借鉴 redis sds[15] 数据结构设计，定制参数序列化方法，节省KV存储空间，“稀疏部分”参数存储 overhead 最低降低至1 Byte；</li>
<li>自研高性能本地Cache，结合Warmup请求，压缩参数分离部署带来的额外时间消耗，视频号场景下单Batch（feature-ids = 5w ，embedding-dim = 8） Lookup 总耗时低至 5ms；</li>
</ol>
</div><div><p><strong>开源协同</strong></p>
</div><div><p>本文工作全部开源，目前代码托管在 external_kv_support 分支，近期会合入 TTensorflow 主干中，欢迎大家吐槽拍砖，一起共建司内 Tensorflow 生态。</p>
</div><div><h4>设计方案</h4>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm/044680849f7786744c63.png"/></p>
</div><div><p>上图展示了本文设计的核心步骤，其中，离线/近线部分，用户使用 Tensorflow 进行模型训练，定期或者在训练结束时将模型参数按照 KeyValue 的形式通过 Export Ops 导出，随后通过 FeatureKv 提供的上线接口对线上参数进行更新。在线部分，推理服务加载 SavedModel 后，模型内部会通过 Import Ops ，针对“稠密部分”，定期替换更新；针对“稀疏部分”，每次处理推理请求时，依据样本按需查询。在线服务逻辑无需做任何适配。</p>
</div><div><p>对于上述设计选型，有 2 点需要额外进行说明：</p>
</div><div><ol>
<li>
<p>模型的“稠密部分”参数因为较小（MB级别），也可以打包进 SavedModel  内随模型结构一同上线，这里之所以选择将这部分参数也放入 KV 中主要出于以下几点考虑：</p>
<ul>
<li>对于时效性要求较高的场景，模型更新会非常频繁（分钟甚至秒级别），频繁的加载与卸载模型会导致推理时延出现颠簸（频繁需要预热，cache失效等问题），有损在线服务的 SLOs(Service Level Objectives)；</li>
<li>需要额外的数据链路用于 SavedModel 的频繁发布，俗话说：“多个香炉多个鬼”，增加了系统出错的概率；</li>
<li>从方案完整性上考虑，只导出模型的“稀疏部分”，并没有彻底的将模型参数与模型结构分离，可能成为整个服务的“阿喀琉斯之踵”；</li>
</ul>
</li>
<li>
<p>Kv 选择上，如果单单基于满足功能的角度，可以使用任意一款成熟的分布式 Kv （例如 Redis）作为存储后端，但是结合参数存储这一使用场景，笔者认为额外提供如下 2 种能力会更佳：</p>
<ul>
<li>离线/近线的训练过程不能影响在线服务，二者最好可以做到一定的“物理隔离”；</li>
<li>参数存储需要提供版本管理的能力，故障时可以快速回滚在线参数到指定版本；</li>
</ul>
<p>基于以上考虑，专门针对大规模参数存储设计的高性能参数服务器 WePS（只使用其存储部分） 和支持版本回退，采用近线导入，提供只读查询能力的微信高性能特征存储 FeatureKV，2 款存储组件从诸多 Kv 中脱颖而出，成为 Gauss 的首选。</p>
</li>
</ol>
</div><div><p>本章的剩余部分，将从“参数导出”开始，详细介绍整套方案。</p>
</div><div><h5>1. 参数导出</h5>
</div><div><p>Tensorflow 中自定义参数导出方式，笔者团队在调研过程中发现 2 种方式：1）实现一种 <code>SaverBuilder</code> ，将其作为参数传入 <code>Saver</code> 的构造函数中，即可在模型保存时按用户所需的方式将模型参数导出；2）实现一种 <code>tf.train.SessionRunHook</code> 配合Tensorflow 高层次API Estimator 一同使用，其通过在计算图中插入 Op 的形式，按需在训练的某些阶段将参数导出。对比 2 种方案，方案1 参数导出的时机被限制在模型保存时，且在实践过程中，笔者发现模型保存时 Tensorflow 会首先将模型结构与所有参数加载到集群的单个实例上，再执行模型导出操作，这样的机制将模型大小限制在了单台机器的物理内存范围内，扩展性较差（当然，这里不排除笔者经验有限，没有掌握 <code>SaverBuilder</code>  的正确使用方式，如有谬误，各位看官尽管板砖招呼）。相比之下，方案2拥有导出时机灵活，保存模型不受单机物理内存大小限制的优点，最终促使笔者团队基于方案2进行实现。</p>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm/831b596fade6939bc0bc.png"/></p>
</div><div><p>上图展示了通过 SessiongRunHook 导出参数的全过程。首先，在 begin 阶段，计算图尚未冻结，我们针对模型的“稀疏部分”和“稠密部分”分别向 chief 节点的计算图中注入 2 种 ExportOp，在指定轮数/指定时间间隔以及模型训练完成时，ExportOp 会被调度执行。其中，</p>
</div><div><ul>
<li>“稀疏部分”的参数体积较大，我们选择在 PS 节点上执行导出 Op，参数直接从 Tensroflow 内存进入 Kv 的内存，或者落地到文件系统，效率较高；</li>
<li>“稠密部分”的参数体积较小，为了避免直接在 PS 导出参数造成大量小文件的问题，我们选择通过 Chief 节点拉取所有参数，再集中导出到 Kv 或落地文件系统，在满足效率要求的同时，降低对存储系统造成的压力；</li>
<li>当"稀疏部分"参数体积过于庞大时，可以通过记录每次导出间隔中有更新的参数id，有选择进行导出，增量上线；</li>
</ul>
</div><div><p>在导出算子内部，首先会将参数编码成 KeyValue 的形式然后通过 Kv / FileSystem 提供的 Api 写入存储。为了提高导出效率和存储效率，实现时我们应用了如下 2 种后台开发中常见的优化方式：</p>
</div><div><ol>
<li>借鉴 redis sds 数据结构设计思想，针对常用数据类型和参数长度，优化定制参数的序列化&amp;反序列化方法，对比 protobuf 动辄几十bytes 的 overhead，在不损失精度的前提下，将数据存储的 overhead 压缩至// 1Byte；</li>
<li>借助微信后台协程库 libco [16]，以 2 级流水线（如下图所示）的方式执行导出过程，理想状态下，可以充分利用起 CPU 与带宽资源。</li>
</ol>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm/9be2f60463c40b6dd3b2.png"/></p>
</div><div><h5>2. 参数导入</h5>
</div><div><p>基于 Tensorflow 开发的模型，通常会按照 SavedModel 的格式导出上线。对于在线模型服务来说，通常会配合 Tensorflow 运行时将 SavedModel 当做黑盒使用，不会侵入模型内部执行过程，只参与模型版本管理等少数外围工作。这样的做法最大程度的将建模工作和在线服务解耦开来，便于算法和工程同学协同开发。但是，也为模型的部署带来了一定的困扰，我们无法像训练时一样，通过 hook 注入 op 的形式，在指定时机执行稠密参数更新和稀疏参数拉取操作，只能另取他法。</p>
</div><div><p>经过一段时间的调研，在保证在线服务逻辑简洁的前提下，Gauss 采用微调推理用计算图的方式着手实现从 Kv 获取模型参数。其中，针对“稀疏部分”，替换 dynamic embedding 使用的 “LookupTable”，每次推理时，直接从线上 Kv 获取“稀疏参数”；针对“稠密部分”，在计算图最开始的位置插入 “SyncAssignVariables” 操作，配合适当的依赖，定期异步从 Kv 拉取全量“稠密参数”替换本地对应部分。</p>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm/73d3719e544ecb646fb2.png"/></p>
</div><div><p>上图左半部分描绘了基于 FKV 的 LookupInterface 实现，使用分布式存储替换本地 Hashtable，必定带来执行效率的损失，为了减少这方面的影响，Gauss 在实现过程中额外施加了下列优化：</p>
</div><div><ol>
<li>基于 Cuckoo Hash 与 Clock 淘汰算法实现了一种高效的 Concurrent Cache[17]，工作负荷下，单 key Lookup 耗时低至 1.3us，通过在请求与 FKV 之间引入该 Cache ，大幅优化了参数查找时延，减轻 FKV 压力；</li>
<li>为每个 Cache Key 设置一长一短 2 个超时参数，前者用于标记参数更新间隔，后者用于指示 Cache 存活时间。每次请求，优先从 Cache 中获取相应参数，当参数不存在或者超过存活时间时，转而从 FKV 获取参数，并删除 Cache 中对应条目；否则直接使用 Cache 中的参数，并判断其存活时长是否超过更新间隔，如果超过，则将对应参数ID推入异步更新队列中，由异步更新线程在后台代为从 FKV 拉取，执行 Cache 更新过程。该优化通过提升 Cache 命中率的方式，进一步降低 Lookup 过程耗时；</li>
<li>结合定制优化的编解码器，使用 Tensorflow 内部多线程机制，并行执行解码过程，降低 CPU 消耗的同时缩减解码耗时；</li>
</ol>
</div><div><p>用户接口方面，上述优化都封装在 LookupTable 内部，用户只需在推理模式下微调数行代码即可完成。下方代码中的红框部分展示了相比于原生 TTF ，用户仅需调整数行代码，即可完成改造。</p>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm/08cbd113b3f686bd9a2b.png"/></p>
</div><div><p>至于“稠密部分”，前图的右半部分描绘了其更新过程。原生 Tensorflow Variable 其实是对一个 Tensor 的引用，且其总大小较小（MBytes 级别），为了降低参数更新对推理服务造成的性能影响，Gauss 在更新 Op 内部使用专门的异步线程，配合“双buffer”的方式，对所有需要更新的参数定期从 FKV 同步数据，原子的切换 Variable 所引用的 Tensor。使用上述优化后，参数实时更新的同时，推理耗时几乎不会上升。</p>
</div><div><p>在便捷性方面，让用户自行选择需要更新的参数，建立“更新Op”与已有步骤的依赖无疑是令人痛苦的。有鉴于此，Gauss 也为专门提供了自动注入依赖的辅助函数，用户只需在建模代码的最后，调用注入函数，即可自动在默认的计算图中添加“更新Op”和相应的依赖（自动为所有没有输入的Op，加上对“更新Op”的依赖，变向的使得“更新Op”被最早的执行）。</p>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm/43a295efa0815b7bbd79.png"/></p>
</div><div><p>下图以 DeepFM 模型为例，显示了依赖注入后的计算图，可以看到，每次用户请求时，都会优先调用一次 SyncAssignOp（Op内部视情况直接返回，或原子切换参数引用）。</p>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm/6cb91baf99be68b264cd.png"/></p>
</div><div><h4>总结</h4>
</div><div><p>本文基于 TTensorflow 与微信后台基础组件，实现了一种用于大规模稀疏场景下，模型参数和结构分离的在线推理服务部署方案 —— Gauss。通过该方案可以在不显著增加服务时延的前提下，实时上线（分钟甚至秒级别） TB 级别模型，同时受惠于成熟的计算与后台组件，整个模型服务高可用且易于维护。</p>
</div><div><p>目前 Gauss 推理服务已在视频号欧拉推荐系统中推广使用，上线后模型参数更新间隔从数十分钟降低至最低 1 分钟内，有效的提升了模型的时效性。</p>
</div><div><h4>后续计划</h4>
</div><div><p>近期笔者团队会继续改进文中描述方案，并重点推动如下 2 个方面的工作：</p>
</div><div><ol>
<li>推动上述改造合入 TTensorflow r1.15.2 主干，接受各方意见，持续打磨 Gauss 组件；</li>
<li>建设高效易用的在线模型托管服务，降低模型上线门槛，提升算法同学工作效率；</li>
</ol>
</div><div><p>本文从系统设计角度阐述了大规模稀疏模型推理服务的部署实践，后续笔者团队陆续还将有文章从具体应用出发，配合实时推荐场景，更加详细的介绍实施过程，敬请期待。</p>
</div><div><h4>致谢</h4>
</div><div><p>笔者以 Tensorflow 小白身份入手，切入该工作，非常感谢一路上提供无私帮助的同事，没有你们这项工作根本无法完成。感谢海栋哥, 王洋, kimmyzhang, 提供了宝贵的 TTensorflow 使用建议和改造意见；感谢 franklintli，在笔者缺乏经验的情况下，不厌其烦的协助解决 CI 过程中遇到的问题；感谢 flashlin, sauronzhang, nrwu, 司马小哥提供了业界顶尖的存储平台，成为了我们最坚实的后盾；感谢 pangyue, 小刚老师，永安老师，星雅，力宏，tylerchen, zelincai 等一班数据平台支撑同学提供的基础设施和宝贵努力，让我们的设计有了稳固的根基，不至于成为空中楼阁；感谢 pris, 俊爷，goonerding 等一班算法同学，心甘情愿的充当小白鼠，在组件完善的路上提供了宝贵使用意见与建议；最后感谢 cc, hunter, randy, chris, noah 各位领导给予的足够耐心和支持，使得这项工作最终得以较为圆满完成。</p>
</div><div><h4>参考文献</h4>
</div><div><p>[1] franklintli, 云帆TTensorflow组件–打造满足业务需求具备技术优势的深度学习框架， [内部或本地链接已移除].</p>
</div><div><p>[2] Olston C, Fiedel N, Gorovoy K, et al. Tensorflow-serving: Flexible, high-performance ml serving[J]. arXiv preprint arXiv:1712.06139, 2017.</p>
</div><div><p>[3] hudsonrong, TTensorflow动态稀疏训练用户手册, [内部或本地链接已移除].</p>
</div><div><p>[4] Li M, Andersen D G, Park J W, et al. Scaling distributed machine learning with the parameter server[C]//11th {USENIX} Symposium on Operating Systems Design and Implementation ({OSDI} 14). 2014: 583-598.</p>
</div><div><p>[5] Jiang B, Deng C, Yi H, et al. XDL: an industrial deep learning framework for high-dimensional sparse data[C]//Proceedings of the 1st International Workshop on Deep Learning Practice for High-Dimensional Sparse Data. 2019: 1-9.</p>
</div><div><p>[6] chijunsima, ,微信在线参数服务器WePS, [内部或本地链接已移除].</p>
</div><div><p>[7] Yansheng Zhang, etc, TensorNet, <a href="https://github.com/Qihoo360/tensornet">https://github.com/Qihoo360/tensornet</a>.</p>
</div><div><p>[8] Ma Y, Yu D, Wu T, et al. PaddlePaddle: An open-source deep learning platform from industrial practice[J]. Frontiers of Data and Domputing, 2019, 1(1): 105-115.</p>
</div><div><p>[9] 无量, [内部或本地链接已移除]</p>
</div><div><p>[10] TFCC, [内部或本地链接已移除]</p>
</div><div><p>[11] 机器之心, “1.9万亿参数量，落地业界首个万亿参数推荐精排模型”,  <a href="https://www.jiqizhixin.com/articles/2021-02-03-6">https://www.jiqizhixin.com/articles/2021-02-03-6</a>.</p>
</div><div><p>[12] He X, Pan J, Jin O, et al. Practical lessons from predicting clicks on ads at [C]//Proceedings of the Eighth International Workshop on Data Mining for Online Advertising. 2014: 1-9.</p>
</div><div><p>[13] svrkit(summer多进程框架), [内部或本地链接已移除].</p>
</div><div><p>[14] 特征服务Featurekv, [内部或本地链接已移除].</p>
</div><div><p>[15] redis, <a href="https://github.com/redis/redis/blob/unstable/src/sds.h">https://github.com/redis/redis/blob/unstable/src/sds.h</a></p>
</div><div><p>[16] libco, <a href="https://github.com/Tencent/libco">https://github.com//libco</a>.</p>
</div><div><p>[17] Fan B, Andersen D G, Kaminsky M. Memc3: Compact and concurrent memcache with dumber caching and smarter hashing[C]//10th {USENIX} Symposium on Networked Systems Design and Implementation ({NSDI} 13). 2013: 371-384.</p>
</div> 
{% endraw %}
