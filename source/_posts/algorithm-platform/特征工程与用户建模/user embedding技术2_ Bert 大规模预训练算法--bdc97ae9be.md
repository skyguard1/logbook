---
title: "user embedding技术2_ Bert 大规模预训练算法"
date: 2022-04-16 10:34:22
categories:
  - 算法平台
  - 特征工程与用户建模
---

{% raw %}

<h3>场景介绍</h3><p>      这里的应用场景主要是基于用户embedding的行为预测场景。应用过程为使用历史行为序列进行预训练，然后根据得到的序列预训练模型，结合用户前一数据周期的行为序列推理下一周期的可能行为。本文主要针对公众号阅读场景，使用历史阅读公众号行为序列预训练，针对两类任务测评。一类是预测任务，根据待评测用户上一月行为序列推荐下一个月开始阶段最可能阅读的公众号。我们将产生的item embedding 通过加权求和的方式生成use embedding，将产出的user embedding和item embedding做内积，进行排序，取每个用户的 topN公众号，计算对该用户下一个月开始阶段的阅读行为的覆盖情况。另一类是召回任务，根据使用的user embedding数据，通过LSH算法召回相似用户，通过被召回用户的阅读文章作为推荐结果，衡量召回效果，即模型效果。</p>
<h3>Bert 大规模实现必要性</h3><p>      应用于NLP场景的Bert预训练模型，随着预训练语料的增多，效果会逐渐提升；因此，语料充足情况下往往需要大规模Bert做预训练。为了验证Bert在公众号行为预测场景，增加语料是否有同样的提升效果。我们将Bert用于公众号场景进行预训练，比较不同量级语料分别执行BERT预训练模型(其他条件相同)的公众号预测效果。这里我们分别使用540万用户的行为序列，及2700万用户的行为序列作为语料执行预训练。应用两个预训练模型生成的embedding结果，推理抽样用户公众号阅读，结果如图1所示（这里预测是新阅读公众号的top5、10、50、100结果)。结果显示，增加语料能够对新边预测任务带来明显的提升(这里top5 提升了20%)。然而，伴随效果提升还存在的问题是预训练耗时较长，训练亿级别用户的长度64的行为序列耗时要20-30天，难以例行。可见，无论出于效果还是效率的考虑，对于数据足够丰富的场景，Bert的大规模实现都十分必要也十分重要。-research版本Bert采用TPU处理大规模数据，成本较大。因此我们对原版进行优化，实现了更普适的GPU版本的Bert大规模预训练模型用于我们的场景。</p>
<p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/7f3ab87f0a01ea9ffb93.png"/><br/><div> [  增加语料效果对比 ]</div></div><p></p>
<h3>Bert 大规模优化策略</h3><h4>算法优化</h4><p><strong>1) NEG 替代 softmax</strong><br/> NLP场景诞生的预训练Bert，在对mask token做预测时，其采样方式是softmax，对于较多词汇空间，其计算性能较差。为了提高性能，这里采用Negative Sampling（简称NEG）的采样方式来替代softmax。这里采用tensorflow提供的候选采样函数tf.nn.learned_unigram_candidate_sampler按照训练数据中类别出现分布进行采样。具体实现方式为首先初始化一个 [0, range_max] 的数组, 数组元素初始为1; 然后在训练过程中碰到一个新阅读的公众号，就将相应数组元素加 1； 每次按照数组归一化得到的概率进行采样。这里负采样数目需要根据场景语料量调优。这里对于亿级别用户，不到百万的token 空间，负采样取的是1000。</p>
<p><strong>2) 去掉next sentence Prediction相关计算</strong><br/>我们将Bert用于行为预测，旨在挖掘行为序列间的联系，因此这里预训练的目标函数仅仅保留用于句内相关性挖掘的mask loss，去掉了计算句间相关性的next sentence loss。由于这里的行为预测场景是直接根据预训练得到的模型抽取user embedding 和 item embedding，然后用于预测用户行为；不涉及下游接类似句子关系判断的fine-tuning任务，因此这里忽略next sentence prediction的效果对行为预测的效果影响不大。相应的我们去掉了segment embedding及段落随机拼接的相关计算，从而提高计算效率。</p>
<h4>系统优化</h4><p>     由于Bert模型预训练过程时间开销较大，这里的系统优化除了保持pipeline减少I/O开销外，采用多块gpu并行计算方式代替之前的单卡计算，从而对预训练过程进行加速。这里为了减少多块gpu间数据传输带来的通信开销，多块gpu采用allreduce的方式进行通信。这里简单描述下allreduce的数据交互和梯度更新过程，整体而言，可以看作两个部分：</p>
<p>1） <strong>数据交互</strong><br/>  待处理的梯度数据拆分成k个数据分片，分别计算；第k-1个进程将第k-1个分片结果传到第k个进程。<br/></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/471cc1ca7a171bc296c2.png"/></div><p></p>
<p>2） <strong>梯度更新</strong><br/>  第k个进程节点将接收到的第k-1个数据分片与自身的第k-1个数据分片做reduce，然后传给下一个进程；反复k-1次至每一个节点能收集每个数据块的all reduce结果。<br/></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/61b3256cfde4905c3c41.png"/></div><p></p>
<h4>运行优化</h4><p>      影响Bert预训练模型效果的因素较多，而不同量级语料及网络结构的参数需要根据实际场景调优，这里主要介绍行为预测的预训练加速相关的运行参数，以及在我们场景对应的较优参数值，供其他场景类比参考。这样我们针对百亿级语料，百万行为token空间，训练3-10个epoch的场景进行运行优化，调优的参数值如下：<br/><strong>1） 序列长度</strong> ：不用场景序列长度有场景内用户粘性关系密切，序列越长预训练所需时间越长，但并不是序列长度越长越好，这里以用户行为覆盖的80%为阈值取的序列长度为64。<br/><strong>2） 向量embedding维度</strong> ： 决定向量空间的大小，维度越大预训练需要迭代step越多，出于计算效率考虑这里取的96。<br/><strong>3） batch_size</strong> : 影响gpu资源利用率，训练一定epoch情况下，batch_size决定着训练所需step数，为了保证效果batch_size 不适合太大，百亿语料以内场景64较合适，百亿语料场景过较多epoch时可以取256-512以加速训练。<br/><strong>4 ) 优化器</strong> ：这里采用LazyAdam 只更新抽取样本梯度从而加速预算。<br/><strong>5 ) multi-head数</strong>：attention头数越大模型越复杂，对于抽取user embedding场景效果影响不大，因此这里取的multi-head=8（需要被embedding整除）。<br/><strong>6） transformer层数</strong>：直接决定模型的复杂度，训练语料越多，层数应该设置越大，出于计算效率的考虑这里取的3-12层。</p>
<h3>Bert 大规模任务部署</h3><p><strong>任务部署</strong><br/>    我们的Bert预训练模型部署在yard平台(后续会笛卡尔算法节点供使用，其他embedding相关应用同样可关注笛卡尔)，GPU型号为Tesla P40, compute capability: 6.1，使用4块GPU进行预训练，任务流程如下图所示。<br/>Bert预训练任务流程<br/></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/bf99a74fd9cb6354d453.png"/><br/><div> [ Bert预训练任务流程 ]</div></div><br/> <strong>1) traindata_Prepare:</strong> 预训练数据准备任务，对原始序列执行mask策略，mask一定的公众号阅读行为用于预训练。<br/> <strong>2) BERT_gpu_train:</strong> 使用gpu进行Bert大规模预训练。<br/> <strong>3) get_Item_embedding:</strong> 从预训练模型中抽取用户阅读的公众号对应的item embedding。<br/> <strong>4) testdata_Prepare: </strong>待评测用户序列准备任务，将待评测用户前一数据周期行为序列按时间顺序打横<br/> <strong>5) get_User_embedding:</strong> 对待评测用户序列的item embedding 通过加权求和的方式生成待评测用户user embedding。<p></p>
<p><strong>运行效率</strong><br/>   我们实现的Bert大规模预训练模型，对GPU的显存利用率可以达到 <strong>90%</strong>。采用算法优化、系统优化及运行优化配置较优参数后，使用2块Tesla P40 GPU例行，每分钟扫描接近百万样本，对应百亿级别语料，过8个epoch可以压缩到4天。</p>
<p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/5451111517a6abc946e6.png"/></div><p></p>
<p><strong>场景效果</strong><br/>   这里我们对比原bert(1%抽样用户) 预训练和 全量用户改进后大规模Bert预训练产生的user embedding用于召回相似用户的召回效果。大规模Bert-all(黄线)能够提升15%效果。<br/></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/c0f52163241944628911.png"/></div><p></p>
<p><strong>踩坑小结</strong><br/>   我们在应用Bert大规模预训练过程中，同样也是遇到了大大小小不少的坑。这里大致说明几点，旨在为大家遇到类似问题，提供填坑方法。<br/><strong>1) 相同step预训练时间差异很大：</strong>在平台部署相同的任务，重跑发现有时耗时几十分钟，有时几小时，分析发现除了调度的因素，主要是拿到不同型号gpu造成的。预训练使用的资源是动态分配共享GPU资源(有TPU资源和较多独占资源池土豪团队除外)，运行分配的GPU机型对运算时长有一定影响，可能导致例行任务不同数据周期时长有较大差异，具体拿到什么机型可以查询运行日志。<br/><strong>2) 参数设置不合理导致OOM：</strong>这里是加大batch_size遇到过，因此batch_size不宜设置过大。此外，还需注意一个小点是随着语料增加，所需内存会逐渐增大，但整体而言，内存不是主要瓶颈。<br/><strong>3) 有些多gpu策略不能用：</strong>多gpu策略选择根据运行平台设置，需要考虑是单机多卡/多机多卡，tf版本Bert需要考虑镜像版本以选择合适的tensorflow API。<br/><strong>4) 加长序列反而效果下降：</strong>尽管增加序列长度，可以增加语料信息；但是往往实际场景中长序列往往占比较少，因此需要更加场景用户序列长度来设置合适的序列训练长度。</p>
<blockquote>
<h4>硬广时间:</h4><p>大规模BERT相关技术及产生embedding结果，同样会沉淀于我们笛卡尔和柏拉图中，产出方式为:</p>
<ol>
<li>生成的全部类型embedding结果，会在<strong>笛卡尔特征库</strong>中供大家使用.</li><li>embedding技术相关的算法组件，会沉淀在<strong>柏拉图平台</strong>，用于生成业务相关的embedding计算.<br/>若有需求，欢迎合作！</li></ol>
</blockquote>
<h4>附录</h4><ol>
<li>bert介绍：<a href="https://arxiv.org/abs/1810.04805">https://arxiv.org/abs/1810.04805</a></li><li>bert实现：<a href="https://github.com/google-research/bert">https://github.com/-research/bert</a></li><li>User embedding技术应用综述：[内部或本地链接已移除]</li><li>用户行为序列建模Bert4UserEmbedding：[内部或本地链接已移除]</li><li>采样优化 ：<a href="https://zhuanlan.zhihu.com/p/66417229">https://zhuanlan.zhihu.com/p/66417229</a></li><li>NEG采样 : <a href="https://zhuanlan.zhihu.com/p/75971908">https://zhuanlan.zhihu.com/p/75971908</a></li><li>Pipeline介绍：[内部或本地链接已移除]</li><li>笛卡尔接入: [内部或本地链接已移除]</li><li>柏拉图embedding算法参考: [内部或本地链接已移除]</li></ol>

{% endraw %}
