---
title: "天下武功，唯快不破：高性能图计算平台Plato图表示学习极致优化之路"
date: 2022-04-16 10:31:43
categories:
  - 算法平台
  - 图学习与图计算
---

{% raw %}

<h2>天下武功，唯快不破</h2>
<h2>高性能图计算平台Plato图表示学习极致优化之路</h2>
<h3>1.   缘起</h3>
<p>       在《高性能图计算X1：前后TensorFlow时代的图表示学习系统》中，我们回顾了多年来图表示学习方向的发展，这里不再赘述。针对社交网络场景下图表示学习所面临的各种问题，公司内涌现出很多优秀的工作[1][2][3]，并取得了显著效果。为了解决图表示学习计算中所面临的巨大的通信开销问题，上述工作均采用了列切分（模型并行）的思路。看起来列切分的方法在图表示学习中的应用已经成为一种<strong>“标准答案”</strong>。在此，笔者不禁抛出一个问题：<em>“<strong>列切分难道就是图表示学习的终极形态么？</strong>”</em></p>
<h3>2.   重新思考列切分（模型并行）</h3>
<p>       区别于数据并行，在图表示学习计算中，列切分（模型并行）是指将模型从embedding维度进行切分，每台服务器存储所有节点的部分embedding向量（如图 1所示）。在这种切分方式下，两个向量的点乘操作 ，可以拆分为，其中<em>p</em>为分区数，和为第<em>i</em>个分区对应的向量partition。这样，在计算操作时不会引入任何通信开销，点乘操作的通信开销仅为<em>O(p)</em>。对于同样的操作，数据并行的方式通信开销为<em>O(h)</em>，其中<em>h</em>为向量的维度。一般来说<em>h&gt;&gt;p</em>，因此列切分的方式有助于减少通信数据量。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f349ae8256de3fbfe412.png"/></p>
<p>图 1 列切分示意图</p>
<p>       但随着网络技术的发展，数据中心网络逐渐从千兆以太网演变为万兆以太网甚至100Gpbs的Infiniband网络。更重要的是，真实业务场景下的图表示学习维度一般在100维到300维之间。在这个背景下，列切分逐渐暴露出一些问题，其中最重要的是：<strong>列切分会导致单机性能的下降，从而导致系统不可线性扩展</strong>。</p>
<p>       在此笔者通过一个micro-benchmark来展示列切分带来的问题。我们实现了一个简易版的LINE算法（ToyLINE），测试不同参数配置下该算法在单线程性能（B70机型下测试）。算法参数如下：batch_size 4096，负样本数目为5，分别测试embedding维度为128, 64, 32, 16, 8, 4, 2, 1下的表现。计算库使用了Intel MKL 2019.4。测试结果如图 2所示，其中Ideal表示在理想情况下，计算时间随着embedding维度是线性可扩展时的曲线。我们可以看到，随着embedding维度的降低，计算时间并不是线性可扩展的。这是因为embedding维度切分的越细，内存的访问模式逐渐从顺序访问变为随机访问，TLB miss逐渐成为系统瓶颈，导致性能的降低。<br/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/418d76f07366f05df43e.png"/></p>
<p>图 2 列切分对计算性能的影响</p>
<p>       对于列切分方式实现的图表示学习计算，以embedding维度为128为例，使用8台服务器（每台切分到16维）与使用32台服务器（每台切分到4维），计算量减少4倍，但单机计算时间几乎保持不变，这是不可接受的。</p>
<p>       正如 AI的老前辈<em>Paul Barham</em>所言“<strong><em>You can have a second computer once you’ve shown you know how to use the first one</em>.</strong>” 只有当用好一台服务器的时候再考虑分布式。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/41ab359d0fb0c8b3b611.png"/></p>
<p>图 3 在此放上Paul Barham老爷子头像镇帖</p>
<h3>3.   “以数据为中心”的设计思想</h3>
<p>       针对上述问题，PlatoGraph（柏拉图）充分利用了图表示学习的计算特性：1）数据访问密集型的本质 2）负样本计算通信占比高，打破传统按列切分的方式，提出“<strong>以数据为中心</strong>”的设计思想，从网络到CPU寄存器，从底层体系结构到上层算法应用，优化整个数据访问的Pipeline（通道），如图 4所示。</p>
<p>       在图表示学习计算过程中，一块数据，首先需要通过网络传输的方式传递到内存中，当CPU调用load指令时，数据经过复杂的缓存协议读入至Cache中，之后load至CPU片上寄存器中，才可被ALU、FPU等运算单元计算。为进行一个浮点数运算，一块数据要经过网络、内存、缓存、寄存器这一条复杂的通道才可被计算，然而Embedding的运算大部分为向量乘法，也就是每个数据在大部分情况下只会被访问一次。因此未经优化的程序性能会被卡在这样一条的数据搬运的通道上。</p>
<p><strong>       以数据为中心：减少计算过程中的数据搬运，提升数据访问性能。</strong></p>
<p> <strong><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a18af98c63f50698f6db.png"/></strong></p>
<p>图 4 以数据为中心-优化整个数据访问的pipeline</p>
<h4>3.1 网络优化</h4>
<p>       整体上Plato使用了参数服务器的架构（图 5），针对Embedding计算的数据访问密集型的特性，我们采用了将PS、Worker联合部署的方式，Embedding 存储于共享内存中，PS和Worker可以直接访问本分区内的Embedding模型，这样有助于减少不必要的数据拷贝。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/92b965380a3cbed413eb.png"/></p>
<p>图 5 整体架构</p>
<p>       其次，Plato打破传统列切分方式，采用<strong>行切分辅以局部负采样</strong>的方法（图 6），充分发挥CPU的计算性能。在Embedding的计算中，一个正样本对需要结合若干个负样本对进行联合训练，因此，不论在计算还是在通信上，负样本占比较高。考虑到负样本是通过采样的方式得到，Plato使用局部负采样的方式来减少通信开销。具体的，在每轮迭代时，对于每个正样本随机被分配到一个shard上，之后在该shard内部进行负采样。局部负采样可减少通信量（1+n/2）倍，其中n为负样本数目。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5c61ec666d58ba04c23d.png"/></p>
<p>图 6 局部负采样</p>
<p>       对于word2vec这类算法，每个正样本对是在一个序列上通过滑动窗口的方式生成。在mini batch训练中，一个序列内的每个点存在于多个正样本的滑动窗口范围内，因此在batch内部存在一定的数据局部性。针对这个特性，Plato采用了batch内部的参数去重来减少通信的数据量。该优化可减少通信量约w倍（w为window大小）。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/624392da78e24930c59e.png"/></p>
<p>图 7 word2vec训练中隐藏的数据局部性</p>
<p>       此外，考虑到embedding的物理意义为高维空间中点的坐标，一般使用向量之间的夹角来还原图中两个顶点的距离远近。因此embedding结果的相对值更为重要，一个训练成熟的embedding结果的绝对值一般较小。在某个实际产品中，我们统计了embedding绝对值的分布，结果显示分布在[-1.9145789, 2.2909719]范围内。用32位的浮点数表示该范围显得有些奢侈。因此，在通信过程中（参数拉取，梯度更新），我们使用了16位浮点数对数据压缩。经测试，使用fp16 进行精度压缩能够达到在保证模型训练效果的同时，减少约1倍的通信量。</p>
<p>       经过上述一系列优化后，对于400维以内的图表示学习计算，在万兆网络环境下，通信不会成为瓶颈（超过400维的情况，可采用进一步优化手段消除通信瓶颈）。</p>
<h4>3.2 内存访问优化&amp;cache优化&amp;寄存器优化</h4>
<p>       此时可能会有人提问，为什么不用TensorFlow？TensorFlow对于处理复杂且计算密集的算法具有很大的优势，但是基于tensor的数据抽象在处理数据访问密集型计算中便显得有些不足。具体来说，我们测试了TF实现的单机版LINE，并做了profiling，结果如图 8所示。由于所有数据在TF中都需要转化为tensor的格式，因此在Gather阶段（Embedding lookup），需要对所需要的embedding参数拷贝到一块连续的内存空间中，在更新梯度阶段，将梯度写回。因此实际计算只占了不到1/3的总时间。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1253851f70e5669a1dc8.png"/></p>
<p>图 8 TF数据拷贝的开销</p>
<p>       为了避免数据拷贝，Plato在计算时使用数据引用进行访问，同时对于需要访问多个行向量的场景，采用了RowSparseMatrix数据抽象，只保存每个行向量的引用，而不是直接存储该行。</p>
<p>       哈希表的方式可以很好的对离散的数据进行索引，但是会在计算的关键路径上污染cache，对此我们使用了ID压缩技术，将离散的ID通过编码的方式转换为连续的ID，在计算的关键路径上对key的索引可以通过数组的方式直接访问，计算完毕后，将连续ID解码还原为离散ID。经测试，该方法能有效提升单机性能约78%。</p>
<p>       在传统的深度学习系统中，一个batch的前向计算和反向计算是分离的。这种方式会导致数据的重复访问。对此Plato采用了Loop Fusion机制，将每个正负样本的前向与后向计算融合，从而提升cache的利用率，减少数据的重复读取。<br/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7cee13491b783a5d4d12.png"/></p>
<p>图 9 Loop Fusion</p>
<p>       图表示学习的负样本计算可以抽象为行稀疏矩阵（RowSparseMatrix）向量乘法操作（RSMV）。对于该操作，一种简单的实现方式是拆分为若干个向量乘法操作。但考虑到被乘向量在计算时被用到多次。对此，Plato采用Loop Tiling机制，实现了寄存器级别的数据重用（图 10）。具体的，首先将向量V的部分元素load至寄存器，之后遍历RSM中所有行向量对应的维度进行计算。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1f3e4fbdf0249191d4bf.png"/></p>
<p>图 10 Loop Tiling</p>
<p> </p>
<h3>4.   性能对比</h3>
<p>       目前Plato在千亿边规模网络上，1400CPU core资源下，embedding维度128，负样本数目5，单轮迭代仅需48分钟，负样本数目为3，单轮迭代可在38分钟内完成。同时，在千亿规模网络下几乎可以线性可扩展。对比业界Euler(201905)以及公司内部的AngleML(201905)，可以实现使用1/5资源情况下，性能提升12倍的效果。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5de17db2546d2620e022.png"/></p>
<p>图 11 Plato可扩展性测试（左：千亿规模网络，右：十亿规模网络）</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f44c2a0252b6197b1166.png"/></p>
<p>图 12 与其他系统性能对比</p>
<h3>5.   开源协同</h3>
<p>开源项目路径：[内部或本地链接已移除]</p>
<p>开源文集路径：[内部或本地链接已移除] </p>
<p>技术图谱项目主页：[内部或本地链接已移除]</p>
<p>使用过程中如果遇到问题，欢迎通过 [内部或本地链接已移除]</p>
<p>进行反馈，柏拉图团队将竭诚为您服务。</p>
<h3>6.   总结</h3>
<p>       本文介绍了针对图表示学习的计算，Plato提出的以数据为中心的设计思想和优化方法。目前Plato的Embedding项目已开源，同时均在笛卡尔平台上线部署，欢迎大家尝试使用。</p>
<h3>7.   引用</h3>
<p>[1] [内部或本地链接已移除] 千亿级别语料 network embedding 计算优化</p>
<p>[2] [内部或本地链接已移除] 分布式机器学习系统AnyEmbedding设计与实现</p>
<p>[3] [内部或本地链接已移除] [Network Embedding]千亿级网络表示学习的Angel实现</p>
<p> </p> 
{% endraw %}
