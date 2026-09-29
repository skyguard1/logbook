---
title: "PlatoDeep：Plato团队开源新一代GNN图神经网络计算框架"
date: 2022-04-16 10:29:34
categories:
  - 算法平台
  - 图学习与图计算
---

{% raw %}

<h1></h1>
<h1>1. 引言</h1>
<p>近年来，深度学习借着大数据和算力崛起的东风，成功掀起了一股新的AI浪潮。深度学习在图像/视频（计算时局）、音频（语音识别）、文本（自然语言处理）领域有着非常广泛的应用。除了以上三种数据类型之外，图（关系）数据在现实生活中是普遍存在的。用户的社交网络、电子支付的交易网络、甚至用户在朋友圈的交互都可以用图（Graph）进行建模。图数据在社交推荐、社交营销、社交广告、金融反欺诈等领域有着非常广泛的应用。针对图数据的深度学习算法在最近一年来也逐渐受到学界和工业界的重视，涌现出许多将图数据与神经网络模型相结合的开创性的工作。图神经网路（GNN）将图数据与深度神经网络相结合，首次实现了在图数据上进行端到端学习的突破，为产业界带来了新的思路。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/79d311d804654a1bb541.png"/></p>
<p>图1 图神经网络在深度学习领域的地位</p>
<p>由于GNN兼顾传统<strong>图算法</strong>和<strong>深度学习算法</strong>的特点，导致以往系统无法高效、便捷的在大规模网络上进行模型的训练和推理，具体的：<br/>    <strong>1. GNN在数据层面具有传统图计算的特点</strong>：大规模和异构性。在的生产环境中，面临的是十亿级别节点的社交网络，且节点和边上存在附加属性数据。超大规模的图数据超过了单机的存储能力，这导致传统以tensorflow为代表的深度学习系统无法处理该类任务。除此之外，在社交推荐等场景下，面临的是高阶异构网络（用户-公众号文章-商品），如何提供高效且易用的接口表达复杂高阶异构网络算法也是一个亟待解决的问题。<br/>    <strong>2. GNN在计算层面具有深度学习计算的特点</strong>：计算复杂且多样。在深度学习时代，网络模型往往是高度定制化的，对不同的场景需要定制化损失函数以及网络结构。这对系统的编程模型层面提出了更高的要求：1. 用户可以定制计算函数（提供便捷且易用的编程模型）2. 自动化的计算生成（训练过程中的反向求导）。</p>
<p>针对以上的问题，学术界和业界涌现出一批优秀的图深度学习系统。他们在易用性、性能和针对大规模图数据方面做了很多尝试，也取得了不错的效果。但当前GNN模型还处于不断探索阶段，图数据的规模也在不断扩大，系统层面的工作也在不断的迭代更新。</p>
<h1>2. 相关工作</h1>
<p>在2018年底开源的Euler[1]系统是国内首个支持大规模图神经网络的分布式计算系统。Euler将图的访问接口抽象为若干个TensorFlow的算子，用户可以轻松的使用TensorFlow编写图神经网络模型代码。随后，DGL[2]和PyTorch-Geometric[3]相继发布单机图神经网络框架。以上两种框架将Tensor的计算原语转化为图相关的计算原语，用户可以使用图的方式实现GNN模型。在2019年底也开源了基于PaddlePaddle的分布式图神经网络框架PGL。PGL使用redis作为图数据存储引擎来满足对大规模图数据的支持。北京大学也发表了基于TensorFlow的单机多卡图神经网络框架NGra[4]。同年，KDD上发表的AliGraph[6]，弥补了Euler在图引擎用户接口的不足。</p>
<p>公司内，Angel团队针对PyTorch在分布式训练上的短板，将AngelPS与PyTorch相结合，研发出PyTorchOnAngel系统，专门针对高维稀疏场景设计，也可以进行GNN的计算。</p>
<p>笔者在此从超大规模网络支持、执行后端以及编程模型三个维度对上述工作进行了简要的总结，如表1所示。</p>
<p>表1 现有图神经网络系统在不同维度的比较</p>
<table><tbody><tr><td>系统</td>
<td>超大规模网络支持</td>
<td>后端</td>
<td>编程模型</td>
</tr><tr><td>PyG</td>
<td>N</td>
<td>PyTorch</td>
<td>Message Passing</td>
</tr><tr><td>DGL</td>
<td>N</td>
<td>PyTorch/MxNet/TensorFlow</td>
<td>Message Passing</td>
</tr><tr><td>PGL</td>
<td>Y</td>
<td>PaddlePaddle</td>
<td>Message Passing</td>
</tr><tr><td>NGra</td>
<td>N</td>
<td>TensorFlow</td>
<td>Message Passing</td>
</tr><tr><td>Euler</td>
<td>Y</td>
<td>TensorFlow</td>
<td>Tensor+Dataflow</td>
</tr><tr><td>Angel</td>
<td>Y</td>
<td>PyTorch</td>
<td>Tensor+Dataflow</td>
</tr><tr><td>AliGraph</td>
<td>Y</td>
<td>-</td>
<td>-</td>
</tr><tr><td>PlatoDeep</td>
<td>Y</td>
<td>TensorFlow</td>
<td>Tensor+Dataflow</td>
</tr></tbody></table><p>注：AliGraph和NGra暂未开源</p>
<p>随着网络规模的日趋增长，业务对模型的计算时间要求也越来越高。学术界提出的DGL、PyG、NGra在处理小规模图场景下有很大的优势，但由于系统要求图数据可以存储于单台服务器之上，因此无法满足工业量级数据的计算需求。Euler虽然可以支撑工业量级的数据规模，但在实际使用时，性能无法满足对任务例行时间的要求。PyTorchOnAngel是基于PyTorch开发，TensorFlow与PyTorch的优劣对比此处不再赘述。PGL基于PaddlePaddle开发，PaddlePaddle生态环境远不及TensorFlow和PyTorch。</p>
<p>Plato团队批判性的吸收了上述系统的设计精髓，基于Plato高性能图计算的设计经验，研发<strong>PlatoDeep</strong>--基于TensorFlow的支持千亿规模网络的高性能图深度学习系统。PlatoDeep将Plato的高性能引入图深度学习领域，取图计算系统与深度学习系统之长，兼顾易用性、高性能和大规模图数据处理的能力，为数据科学家在大规模图数据上快速尝试新模型提供了高效的工具。</p>
<h1>3. PlatoDeep图深度学习平台</h1>
<h2>3.1 设计理念</h2>
<p>由于GNN计算兼顾图计算和深度学习计算的特点，PlatoDeep在架构上将系统设计为图引擎（PlatoEngine）和机器学习计算引擎（PlatoTrainer）两个模块。在图引擎设计上，借鉴传统图计算系统的设计经验，机器学习训练引擎则充分吸收现有深度学习框架的经验，基于TensorFlow进行开发。通过吸取两个领域系统的设计精髓，从而最终在性能与易用性上同时达到最优。</p>
<h2>3.2 系统设计</h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b53ae97a90d3ce612091.png"/></p>
<p>图2 PlatoDeep平台架构图</p>
<p>PlatoDeep平台架构如图2所示。在PlatoDeep的最底层是在<strong>线图引擎-PlatoEngine</strong>和<strong>高性能图算子库--PLAS</strong>。PlatoEngine生成的数据通过包装为tf.dataset对象的方式可以完美融合TensorFlow生态圈。同时，PlatoDeep总结并提炼了GNN中一些基础图相关操作，并针对TensorFlow在这些操作上的不足进行补充，设计出PLAS高性能图算子库来弥补TensorFlow基础算子的性能问题。在此基础上，PlatoDeep做了针对GNN的计算图层面的优化来进一步的提升性能。目前PlatoDeep提供了5种经典GNN算法（算法库还在不断的丰富中）。</p>
<h3>PlatoEngine-高性能在线图引擎</h3>
<p>PlatoEngine是对PlatoGraph在近线/在线场景下的补全。PlatoGraph可以高效的处理传统离线图计算任务，但是在GNN场景下，对于图的采样往往要求是<strong>近线或者在线</strong>的。PlatoEngine总结了PlatoGraph在离线场景的成功经验，针对近线/在线场景采用了<strong>ID Mapping Free、Asynchronous、Graph Partitioning、Prefetching</strong>等一系列优化方法来达到极致性能。具体性能优化详解详见后续文章。</p>
<p>在用户接口层面，PlatoEngine总结了经典GNN的采样方式，提供了一些定制化的高性能采样类，对常用算法可以达到“开箱即用”的效果。PlatoEngine提供的采样类可以天然的与TensorFlow自带的Dataset对接，实现与TensorFlow系统的融合。</p>
<h3>PLAS-高性能图算子库</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/700639958ec054e9cc19.png"/></p>
<p>图3 GNN中稀疏算子计算模式</p>
<p>在GNN的计算中，数据往往是<strong>二维稀疏</strong>的，算子的计算往往针对图的结构展开，具体的计算模式可以归纳为图3所示。图中，采样后图的图可以表示为稀疏矩阵的格式（灰色方块），对于矩阵中的每个非零元对应的源点u、汇点v、边e。由于图中的点、边可以有任意的属性，因此U、V、E分别对应源点、汇点、边的属性矩阵。在运算时需要获取每个非零元的u向量、v向量、e向量（深色部分）进行计算。计算的函数也可以是多种多样的。例如常用的edge_softmax则是对于E矩阵根据图的结构进行softmax操作。</p>
<p>目前，TensorFlow使用了SparseTensor的方式表达稀疏数据，配合Eigen库来实现稀疏算子。为了兼顾高维稀疏数据的通用性，SparseTensor使用了COO的数据格式。然而，COO数据格式在实现一些算子上存在一些的性能问题，对于某些算子不是并行友好的。</p>
<p>在PLAS中，考虑到GNN计算的二维稀疏性，我们使用<strong>Attributed CSR/CSC/COO</strong>（ACSR/ACSC/ACOO)格式表达稀疏数据。基于ACSR/ACSC/ACOO，PLAS将GNN常用算子提炼为库函数的形式（在不断扩充中），其中包含GraphSAGE用到的u_gather_v、u_gather_v_reduce_sum和GAT用到的u_gather_v_mul_e_reduce_sum等等。在实现上，使用了多线程配合代码向量化的方法。对于存在broadcast语义的一些算子，我们将broadcast语义下沉到向量化的指令集中，相比已有实现可以带来10倍左右性能提升。</p>
<h3>PlatoDeep GLO-计算图层面优化</h3>
<p>对于同一个操作，可以有ACSR、ACSC、ACOO三种数据格式的不同实现。如何做到针对不同的运算，选择最优的数据格式对应的PLAS实现，是PlatoDeep GLO要做的事情。例如，在PlatoDeep GLO中，我们对一些原始数据为ACSC格式，但使用ACSR算子更为高效的运算，添加了GraphTranspose操作，首先将ACSC格式转化为ACSR格式，然后调用ACSR对应算子。目前，在计算图层面的部分优化仍然对用户有很高的的要求。如何做到全自动的计算图优化，PlatoDeep还在不断的探索中。</p>
<h3>PlatoDeep算法库</h3>
<p>基于PlatoDeep，我们实现了包括SupervisedGraphSAGE、UnSupervisedGraphSAGE、GAT、GCN、SGC、DGI在内的6个算法，均可以复现论文作者提出的准确率。算法库还在不断的扩充中，欢迎各位算法同学使用PlatoDeep，同时贡献算法，共建公司级的PlatoDeep算法库！</p>
<p>表2 PlatoDeep算法效果</p>
<table><tbody><tr><td>Model</td>
<td>Dataset</td>
<td>Accuracy of Author's Code</td>
<td>Accuracy of PlatoDeep</td>
</tr><tr><td>SupervisedGraphSAGE</td>
<td>Reddit</td>
<td>95.0%(F1 score)</td>
<td>95.3%(F1 score)</td>
</tr><tr><td>SupervisedGraphSAGE</td>
<td>RedditFull</td>
<td>-</td>
<td>96.8%(F1 score)</td>
</tr><tr><td>GAT</td>
<td>Cora</td>
<td>83.0%</td>
<td>82.9%</td>
</tr><tr><td>GCN</td>
<td>Cora</td>
<td>81.6%</td>
<td>80.7%</td>
</tr><tr><td>S-GCN</td>
<td>Cora</td>
<td>81.0%</td>
<td>80.9%</td>
</tr><tr><td>DGI</td>
<td>Cora</td>
<td>82.3%</td>
<td>81.5%</td>
</tr></tbody></table><p>注：GCN、DGI原作者使用了FullBatch Training的方式，在大图上不可扩展。PlatoDeep使用了MiniBatch Training方式将大图上的GCN实现变成为可能，但精度上会有一些差距。</p>
<h1>4. 性能对比</h1>
<p>为了证明PlatoDeep的设计在性能上的优势，我们对比了已有开源的支持大规模图数据的图神经网络计算框架：Euler和PyTorchOnAngel（PGL理论上也可以支持大规模图神经网络计算，但由于PaddlePaddle生态环境远不及TensorFlow和PyTorch，因此这里暂未比较）。</p>
<p>在这里，我们使用了公开的Reddit-Full（点数目：232965，边数目57307946）作为测试数据。在相同计算资源下，性能比较如图4 所示（注：由于Euler采用了异步训练方式，在迭代相同轮数的Epoch后，Euler准确率无法达到PlatoDeep和PyTorchOnAngel准确率，PlatoDeep和PyTorchOnAngel可以达到相同准确率）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4f7033d95349835d6e79.png"/></p>
<p>图4 GraphSAGE模型在不同系统下性能比较</p>
<p>为了证明PlatoDeep在超大规模网络上的性能，我们从社交网络中抽样得到包含1700万节点和14千万边的测试图，在480计算核的资源下，GraphSAGE每个epoch耗时135秒。</p>
<p>同时为了证明PlatoDeep是大规模可扩展的，我们在上述图数据上测试了不同机器数情况下PlatoDeep的横向可扩展性，结果入图5和图6所示。我们可以看到PlatoDeep在扩展到40台机器时依然保证了高性能，但距离线性可扩展还有一定的距离，PlatoDeep还在不断的完善中。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/539fae5c82c7c0d074dc.png"/></p>
<p>图5 PlatoDeep横向可扩展性</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e37b12e70b85d217d4b2.png"/></p>
<p>图6 PlatoDeep横向可扩展性</p>
<p></p>
<h1>5. 开源协同&amp;代码规范</h1>
<p>目前PlatoDeep已在公司内开源：[内部或本地链接已移除]</p>
<p>开源文集路径：[内部或本地链接已移除]</p>
<p>技术图谱项目主页：[内部或本地链接已移除]</p>
<p>PlatoDeep代码风格严格遵循 Cpp， Python代码规范。对于PlatoDeep定制的算子也实现了单元测试，保证计算的准确性。PlatoDeep提供定期更新的python wheel包供用户下载使用。目前PlatoDeep代码已接入CI系统，欢迎大家贡献代码。使用中遇到问题，请通过issue进行反馈，共建PlatoDeep，打造业界领先的图深度学习框架！</p>
<p>感谢以下同学对PlatoDeep代码的贡献：@cedricsun 设计出高性能的PlatoEngine图引擎让PlatoDeep性能进一步提升，@healyhuang 和@wenqiangwu对PlatoDeep在sample接口以及部署层面的突出贡献，以及 @kazechen @aaronymwu @nickgu对PlatoDeep模型库的不断完善（排名不分先后）！</p>
<h1>6. 参考文献</h1>
<p>[1] https://github.com/alibaba/euler<br/>[2] Wang, Minjie, et al. "Deep graph library: Towards efficient and scalable deep learning on graphs." arXiv preprint arXiv:1909.01315 (2019).<br/>[3] Fey, Matthias, and Jan Eric Lenssen. "Fast graph representation learning with PyTorch Geometric." arXiv preprint arXiv:1903.02428 (2019).<br/>[4] Ma, Lingxiao, et al. "Neugraph: parallel deep neural network computation on large graphs." 2019 {USENIX} Annual Technical Conference ({USENIX}{ATC} 19). 2019.<br/>[5] http://[内部链接已移除] pytorch on angel: 面向稀疏高维场景的轻量深度学习框架<br/>[6] Zhu, Rong, et al. "AliGraph: A Comprehensive Graph Neural Network Platform." arXiv preprint arXiv:1902.08730 (2019).<br/>[7] https://en.wikipedia.org/wiki/Sparse_matrix</p> 
{% endraw %}
