---
title: "基于Tensorflow的Wide&Deep模型推理性能优化"
date: 2022-03-30 10:04:04
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<h2>背景介绍</h2>
<p>Wide &amp; Deep (W&amp;D) 模型最早出现在  发表在 DLRS 2016上的文章《Wide &amp; Deep Learning for Recommender System》。该结构被提出后即引起热捧，在业界影响力非常大，很多公司纷纷仿照该结构并成功应用于自身的推荐等相关业务[1]。鉴于W&amp;D类模型的大量部署，本文总结了智能钛机器学习（<u>TI-ML</u>）团队对某电商客户在智能钛弹性模型服务（TI-EMS）平台上的W&amp;D模型的推理优化的工作，总体性能提升207%。</p>
<p> </p>
<h2>模型结构与分析</h2>
<p>经典W&amp;D包括LR部分和DNN部分，框架如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/bf039e3fb98fe72a51f8.png"/></p>
<p>图1. W&amp;D模型结构</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b3eacb79b8019f661567.png"/></p>
<p>图2. APP推荐所用网络结构</p>
<p>目前各种基于W&amp;D应用，主要结构类似图2，差别主要在特征的选取与处理，网络的宽度等。</p>
<p>本文实验所用的智能钛弹性模型服务（TI-EMS）平台上某电商客户的模型结构类似图2，网络结构分析如下：</p>
<p>本文评估了两个模型，总体参数规模分别为：490MB（小模型）和680MB（大模型），其中DNN部分都是三层，DNN层网络输入大小分别为：432和1144。RELU层输入大小分别为：256-128-64和1024-512-448。DNN层参数规模分别为：0.61MB和7.36MB。因此参数主要集中在Embedding层，对Embedding层的优化，也是本文主要工作。</p>
<p>本文测试所用机器为标准型S4 CVM（S4 8XLARGE64）， 32core机器，FP32峰值计算性能约为：2.4Tflops。线上模型固定使用Batch Size等于80对服务进行请求。每次服务请求，小模型和大模型DNN层所需计算量分别为：24.1M次浮点计算和294.4M浮点计算。因此在不考虑带宽瓶颈的情况下（DNN部分MATMUL计算M，N， K都比较大，每个weight/activation读的计算量分别为2M/2N，一般M和N越大，带宽瓶颈越小），DNN计算部分理论所需时间分别为：0.01ms和0.12ms，因此DNN部分理论上不会成为瓶颈。实际应用中，小模型服务使用Tensorflow各版本DNN部分皆不会成为瓶颈，大模型DNN部分使用不带MKLDNN 的Tensorflow会成为性能瓶颈。</p>
<p>以上是对DNN部分简单分析。W&amp;D模型推理服务主要时间开销在特征处理部分，其中主要是Embedding查询部分。</p>
<h2>推理服务参数优化</h2>
<p>参数设置对Tensorflow模型推理服务影响很大。比如如下Tensorflow参数设置：</p>
<p>intra_op_parallelism_threads, 线程池中线程的数量，一些独立的操作可以在这指定的数量的线程中进行并行，如果设置为0代表让系统设置合适的数值。</p>
<p>inter_op_parallelism_threads, 每个进程可用的为进行阻塞操作节点准备的线程池中线程的数量，设置为0代表让系统选择合适的数值。</p>
<p>对分类等计算密集模型，intra_op_parallelism_threads一般推荐值为物理core个数。inter_op_parallelism_threads一般推荐值为socket个数。</p>
<p>MKLDNN参数设置：</p>
<p>KMP_BLOCKTIME：设置线程在睡眠之前完成并行区域执行后应该等待的时间（以毫秒为单位）。</p>
<p>OMP_NUM_THREADS：指定要使用的线程数。一般和intra_op_parallelism_threads相同。</p>
<p>KMP_AFFINITY：启用运行时库将线程绑定到物理处理单元。</p>
<p>本测试使用Tensorflow版本为TF 1.14，测试机型为标准型S4 8XLARGE64。小模型推理服务使用不带MKLDNN版本Tensorflow,大模型带MKLDNN支持。</p>
<p>表1. 大模型不同参数配置推理时间</p>
<table><tbody><tr><td>
<p>INTER</p>
</td>
<td>
<p>INTRA</p>
</td>
<td>
<p>OMP_NUM_THREADS</p>
</td>
<td>
<p>KMP_BLOCKTIME</p>
</td>
<td>
<p>malloc</p>
</td>
<td>
<p>推理时间</p>
</td>
</tr><tr><td>
<p>Default</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>12ms</p>
</td>
</tr><tr><td>
<p>1</p>
</td>
<td>
<p>16</p>
</td>
<td>
<p>1</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>12ms</p>
</td>
</tr><tr><td>
<p>2</p>
</td>
<td>
<p>16</p>
</td>
<td>
<p>2</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>14ms</p>
</td>
</tr><tr><td>
<p>2</p>
</td>
<td>
<p>8</p>
</td>
<td>
<p>2</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>7.3ms</p>
</td>
</tr><tr><td>
<p>4</p>
</td>
<td>
<p>8</p>
</td>
<td>
<p>4</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>Default</p>
</td>
<td>
<p>9.2ms</p>
</td>
</tr><tr><td>
<p>2</p>
</td>
<td>
<p>8</p>
</td>
<td>
<p>2</p>
</td>
<td>
<p>1</p>
</td>
<td>
<p>tcmalloc</p>
</td>
<td>
<p>6.2ms</p>
</td>
</tr><tr><td>
<p>4</p>
</td>
<td>
<p>8</p>
</td>
<td>
<p>4</p>
</td>
<td>
<p>1</p>
</td>
<td>
<p>tcmalloc</p>
</td>
<td>
<p>5.6ms</p>
</td>
</tr></tbody></table><p>可以看到，不同参数设置，对性能会有一倍以上影响。</p>
<h2>网络结构优化</h2>
<p>除了运行参数设置，Tensorflow框架本身也有很大性能优化空间。Tensorflow FeatureColumns提供了丰富的特征操作，可以将类别、字符串等特征转换为深度学习框架所支持的浮点数特征。比如，典型特征处理过程如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b3aca06e7e7ece9b34c3.png"/></p>
<p>图3. 特征转换过程示例</p>
<p>上图显示了一个从字符串特征到浮点向量特征的转换过程。其中最后一步从ID到浮点向量的操作，也叫查表操作（Embedding lookup，即从表中取出相应的行，可能多维）。查表操作，包括查询多个行以及融合多行操作，在Tensorflow的实现如图4所示，共需要39个节点完成。</p>
<p>针对这类Tensorflow使用率比较高而且实现相对复杂（性能比较低）的计算子图，我们设计了大尺度融合算子，将目前整个子图功能由单个算子完成。</p>
<p>首先在Tensorflow内核添加SparseEmbeddingWithShape算子，实现完整Embedding Lookup操作。然后在Tensorflow Grappler模块添加图优化算法，识别上述计算子图，并将整个计算子图替换为SparseEmbeddingWithShape算子。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm/ce8e4f088a65dfcc1504.png"/></p>
<p>图4. Tensorflow Sparse Embedding Lookup （优化前）</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4dc4342df9c141c79635.png"/></p>
<p>图5. Tensorflow Sparse Embedding Lookup （优化后）</p>
<p>通过以上优化，大模型推理性能从5.6ms提升到3.9ms。小模型推理性能从2.9ms提升到1.2ms。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2380fcc86f9cd09449a9.png"/></p>
<p>图6. 大模型推理性能优化前后对比</p>
<h2>总结</h2>
<p>推荐类算法是深度学习主要应用方向之一，Tensorflow是目前最流行的深度学习框架。本文总结了智能钛机器学习团队对推荐算法在Tensorflow框架的推理性能优化工作，性能提升了207%。另外，针对经典分类，目标识别等算法，团队提供了基于TensorRT和OpenVINO的优化服务镜像，性能提升从百分之几十到几倍不等。团队也针对流行框架（比如Facebook Detectron）做了深度优化方案，欢迎大家登录智能钛弹性模型服务[3]试用。后面也会撰写系列文章分享。因为撰写时间仓促，有错误或不足之处，欢迎拍砖。</p>
<h2>感谢</h2>
<p>感谢CSIGAI基础中心邓攀、胡玉、林卫亮、刘刚、刘翃、茅婷婷、彭彪、孙旻、王磊、谢博文、尹迪、余祖坤支持。感谢智慧行业产品一部行业专家中心行业专家二组詹旭、智慧行业产品一部业务架构中心华东业务组水大伟的支持。</p>
<p> </p>
<p>[1] <a href="https://zhuanlan.zhihu.com/p/53361519">https://zhuanlan.zhihu.com/p/53361519</a></p>
<p>[2] [内部或本地链接已移除]</p>
<p>[3] [内部或本地链接已移除]</p>
<p> </p> 
{% endraw %}
