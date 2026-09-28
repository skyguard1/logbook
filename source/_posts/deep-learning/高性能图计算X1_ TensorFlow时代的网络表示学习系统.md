---
title: "高性能图计算X1_ TensorFlow时代的网络表示学习系统"
date: 2022-04-21 10:36:50
categories:
  - deep-learning
---

{% raw %}

<p></p>
<div>
<h1>TensorFlow时代的网络表示学习系统</h1>
<h2>1.  引言</h2>
<p>图（Graph）作为一种数据结构，可以非常自然的表达出现实世界中多种实体以及之间的关系。它无处不在，人与人之间的关系是一个社交关系图，电商平台上用户的购买记录形成的用户商品购买网络、银行转账记录构成的交易图。</p>
<p>利用图极强的表达能力，将数据按照图的方式进行描述，并在此基础上进行数据分析逐渐成为一种趋势[13][14]。学术界和工业界也正在将图所表达的信息应用于机器学习模型中，提升模型效率。随着数据规模的日益增长，直接将图按照高维稀疏矩阵的表达方式应用到机器学习模型中，会对计算和存储方面的带来极大地挑战。</p>
<p>为此，图表示学习应运而生。通过将图的节点映射到低维向量空间中，可以极大的减轻计算和存储的负担。同时，低维向量的表示可以大致还原出图的某些特性。例如，图中连接比较紧密的节点在向量空间中距离较短。生成的低维稠密向量可以作为该节点的基础特征应用于下游的各个机器学习任务中，例如：基于社交关系的推荐系统[24]、节点分类、连接预测[15]等等。</p>
<p> </p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/bcd778d59237246be18d.png"/></p>
<p>图1表示学习及其应用</p>
<p>一方面，传统的图计算系统[16][17][18]在设计时针对传统图算法的特性进行了定制的优化，同时也带来了很好的性能。但由于图表示学习的计算模式与传统图算法更为不同，并且所涉及的数据量往往有数量级的提升，因此传统的图计算系统不论在接口设计上还是计算效率上均无法很好地处理图表示学习的计算。</p>
<p>另一方面，传统机器学习（深度学习）系统[9][19]在处理稠密数据计算达到了很好的效果，并且在人工智能领域得到了广泛的应用。但在处理大规模稀疏图数据上，由于没有充分利用图数据的特性而导致无法达到理想的性能。</p>
<p>因此，如何充分利用图数据的特性、结合图表示学习计算的模式的特点，设计出通信开销小、计算负载均衡的分布式图机器学习系统是解决现有系统在图数据上进行机器学习计算的关键。</p>
<p>本文总结了过去几年中，在处理大规模图表示学习方面进行通信优化、计算优化以及如何在TensorFlow系统上支持该类计算等方面的工作进展及适用场景。最后，笔者结合微信数据中心在图表示学习方面的复杂业务需求，在已有柏拉图计算平台上，探索出支持图表示学习的图机器（深度）学习系统。笔者对图表示学习尚处于学习阶段，如有描述有误或不准确之处还请指出。</p>
<h2>2.  图表示学习计算的分类</h2>
<p>对于图表示学习算法的介绍以及演进在[13][14]的文章中已经描述的很清楚，这里不再赘述。本章将从计算模式的角度对常用的图表示学习算法进行归类。具体来说，可以分为<b>矩阵分解类</b>、<b>SkipGram类</b>以及<b>GNN（图神经网络）类</b>三种算法。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/f190adbf8680cdb30257.png"/></p>
<p>图2 图表示学习计算的分类</p>
<p> </p>
<p><b>矩阵分解类</b>算法包括NMF、ALS等等，该算法核心思想是将图看作高维稀疏矩阵，通过若干个低维稠密矩阵的运算结果来逼近高维稀疏矩阵。因此该类算法可以直接将原始图作为输入数据进行训练。</p>
<p><b>SkipGram类</b>算法包括LINE、DeepWalk、Node2Vec、Metapath2Vec等等。该类算法借鉴了NLP领域常用的WordEmbedding技术。首先通过某种游走的方式生成游走路径（LINE除外），之后将路径作为语料通过NLP模型（如SkipGram或CBoW）及其变种进行训练。</p>
<p>最近兴起的<b>GNN类</b>算法包括GraphSAGE、PINSage、GCN等图神经网络算法。该类算法的计算一般包含两个阶段。采样阶段：在原始图上通过采样的方式生成若干个小图。训练阶段：将小图作为输入数据，通过多层神经网络模型（FC、LSTM、GRU）训练。</p>
<h2>3.  图机表示学习系统及优化</h2>
<p>针对上一章节中提到的三类计算模式，学术界和工业界涌现出许多在海量图数据下的针对上述算法设计的图机器学习系统。本章以TensorFlow为分界线，分别介绍了TensorFlow出现之前从通信优化、计算优化相关的研究工作，以及TensorFlow出现之后，在TensorFlow等系统基础上进行的优化工作。</p>
<h2>3.1     前TensorFlow时代的图机器学习系统</h2>
<h3>3.1.1 以通信为中心的设计</h3>
<p>       <b>矩阵运算视角的数据并行与模型并行。</b>对于前面提到的矩阵分解类以及SkipGram类算法，模型量级通常和图中点的数目成正比。在超大规模图上训练时，单机往往无法满足大量模型数据的存储需求。因此需要采用分布式的方式、对模型切分进行训练。上述算法大部分的计算核心为<b><i>Batched GeMV</i></b>（批量矩阵向量乘法）或<b><i>GeMM</i></b>（矩阵和矩阵乘法）。节点的Embedding矩阵为N*H的稠密矩阵（N为节点数目，H为向量维度）。目前对节点的Embedding矩阵的切分方式可以分为两类：按行切分和按列切分。按行切分是指将N维度进行切分，也就是常用的数据并行。按列切分则是切分H维度，也就是Erik[1]等人提出的模型并行的方式。以LINE的前向计算为例，其核心为<img alt="" loading="lazy" src="/logbook/images/deep-learning/51e9cd5065627e21690b.png"/>的矩阵向量乘法，其中向量<img alt="" loading="lazy" src="/logbook/images/deep-learning/8c578d5252eb1e678455.png"/>表示正样本的Embedding，大小为<img alt="" loading="lazy" src="/logbook/images/deep-learning/f1688e42ad7bb6441075.png"/>。矩阵<i>M</i>为负样本的Embedding，大小为<img alt="" loading="lazy" src="/logbook/images/deep-learning/3fe9d7f7e5b2c41076b6.png"/>。当按行切分时，每个分区可以拿到部分节点的完整embedding向量，每次计算通信量为<img alt="" loading="lazy" src="/logbook/images/deep-learning/3fe9d7f7e5b2c41076b6.png"/>（如图 3（a）所示）。按列切分则为<img alt="" loading="lazy" src="/logbook/images/deep-learning/3deb0a08d23872d765e8.png"/>（其中p为分区数目）。在上述描述中，<img alt="" loading="lazy" src="/logbook/images/deep-learning/71281ca640baac05dbef.png"/>为Embedding维度，<img alt="" loading="lazy" src="/logbook/images/deep-learning/1660689012df6b17cdb6.png"/>为负采样数目。一般来说<img alt="" loading="lazy" src="/logbook/images/deep-learning/818960516113d01c791a.png"/>，因此，按列切分的方式通信代价更小。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/b4992706819ee5b25a12.png"/></p>
<p>图3 行切分与列切分GeMV计算示意图</p>
<p><b>图视角的混合并行模式</b>。列切分（模型并行）的方式在减少通信量方面能够起到显著的作用，同时也被公司内部多个系统所采纳[2][3][25]，但没有考虑到模型参数之间的关联性。清华大学的Zhang[4]等人结合图的结构特性，挖掘参数之间的关联性，提出了图的<b>3D切分方式</b>（如图 4所示），在模型并行的基础上进一步减少了通信的数据量。3D划分的核心思想<b>不但切分模型，而且切分数据</b>。是首先利用分布式图计算领域中的Vertex-Cut进行图结构的划分（也就是作者提到的2D划分）。在此基础上，在每个点的H维度（Embedding向量维度）进行切分（作者提到的第3个维度）。在进行H维度切分时，每个点也会因此分裂到多个layer上。每个layer包含了<b>所有点</b>的<b>部分embedding向量</b>。因此，训练过程中的通信分为了两类：Layer内部的通信以及Layer之间的通信。Layer内通信采用传统图计算中的Pull/Push的通信模式，Layer间的通信采用MPI_Allreduce通信模式。通过这种方式，对于ALS等算法可以带来显著的性能提升。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/ba3d2e6b9231b06122d3.png"/></p>
<p>图4 3D图切分示意图</p>
<p> <b>系统和算法联合设计减少通信开销</b>。除以上方法之外，来自Yahoo的Stergios等人[5]另辟蹊径，从算法层面优化通信。在计算<img alt="" loading="lazy" src="/logbook/images/deep-learning/51e9cd5065627e21690b.png"/>时，<i>M</i>为负样本矩阵，该矩阵是通过采样的方式得到。因此作者在采样策略上提出了两种不同的方式，来减少通信开销。具体来说，提出了<b>单点负采样</b>（SingleNegativeSampling，SNS）和<b>目标负采样</b>（TargetNegativeSampling，简称TNS）的方法。在SNS的采样方式中，对于每个正样本只从一台服务器中进行负采样，在进行负样本的计算时，由于<i>M</i>保存于本地无需通信，因此只需要传输正样本对的<i>V</i>向量即可，通信量为<img alt="" loading="lazy" src="/logbook/images/deep-learning/6776535942c587df030f.png"/>。但在SNS的方式下，仍然需要传输正样本对的Embedding向量。对此，作者提出了更激进的优化--TNS。在TNS采样策略下，只从正样本对中输出节点所在的机器采样，这样只需要传输正样本对中输入单词的Embedding向量即可，通信量相比SNS减少一倍。作者在论文中提到，即使采用TNS的策略，在NLP任务上训练出的模型表现依然很好。 </p>
<h3>3.1.2以计算为中心的设计</h3>
<p>上述工作均是针对减少训练过程中的通信开销而展开。然而随着网络技术的发展，InfiniBand等高性能网络设备在工业生产环境中得到了广泛的应用。InfiniBand的普及将使得计算过程中的通信开销占比更少。对此也出现了许多对图机器学习从计算角度进行优化的系统。</p>
<p><b>图划分有助于使计算负载更为均衡</b>。来自MSRA的Xiao[6]等人提出了高速网络环境下的在图数据上进行机器学习计算的TuX2系统。该系统将MiniBatch的训练与图结构数据相结合，提出了<i>MEGA</i>编程模型。通过将PowerGraph的图划分策略应用于机器学习计算中，与参数服务器架构相比，可以使得计算的负载更加均衡。实验表明，在54Gbps的Infiniband上可以达到很好的性能。</p>
<p><b>系统算法联合设计使计算更为高效</b>。Ji[7]等人则提出了<b>HogBatch</b>的方法来提升训练过程中的计算效率。在传统的Word2Vec的训练过程中，每个正样本所采集的负样本是不同的，计算核心为BatchedGeMV操作。在HogBatch的方法中，提出了将一个MiniBatch内所有负样本共享的计算方式。通过这种方式可以<b>将BatchedGeMV的计算转化为GeMM计算</b>。在现有的计算机体系结构下，GeMM计算可以更好的利用cache从而带来计算性能的提升。但在该系统中，假设模型是可以存储于单机内存中。因此该系统无法进行大规模图数据（亿级别以上的节点）的表示学习计算。</p>
<h2>3.3 后TensorFlow时代的图机器学习系统--以Tensor为中心的设计</h2>
<p>随着深度学习技术的发展，计算变得日趋复杂，从包含8层网络的AlexNet到包含22层网络的GoogLeNet，让用户手写如此复杂的计算过程逐渐成为一件不可能的任务。对此Google在2016年提出了TensorFlow计算框架。TensorFlow提供了易用的Python编程接口、自动求导等功能，这使得数据科学家们可以从繁琐的编程工作中解脱出来，只专注于算法的设计。同时在计算性能方面提供了XLA[8] 编译优化工具，让程序可以自动的生成可在多种设备上执行的高效代码。</p>
<p>虽然TensorFlow在处理深度学习任务上得到了很好的效果，但是在处理图数据上依然欠缺高效的工具。针对这个问题，学界和业界涌现出一批将图深度学习和以Tensorflow为代表的tensorframework结合的“翻译”系统（如图 5所示）。</p>
<p>正如Butler Lampson的一句名言：<b><i>All problems in computer science can be solved by another level of indirection</i></b><b><i>.</i></b></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/33c0a7b3372eaf41148a.jpg"/></p>
<p>在此放上老爷子头像镇楼</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1322e228604219212ebe.png"/></p>
<p>图5 将“图表示”翻译为“Tensor表示”的系统</p>
<p> 比较典型的是提出的Euler系统[10]。该系统将图结构的存储服务抽象为Graph Engine，在此基础上实现了图查询相关接口（如随机游走、邻居节点查询）。通过将图结构数据转换为张量（Tensor）形式，可以对接TensorFlow等系统进行大规模分布式训练。Euler不仅可以支持LINE、Node2Vec等传统网络表示学习的训练，而且可以支持GNN类计算复杂的模型训练。</p>
<p> 与此同时，来自NYU的Wang[11]等人提出了DGL系统，该系统除了提供一套图查询相关操作之外，还设计出专门针对GNN计算的基于MessagePassing的编程接口，大大简化了编程工作。之后多特蒙德工业大学公开出的PyTorchGeometric[12]也采用了类似的设计。上述两个系统目前只支持做GNN相关的计算。</p>
<p> 针对知识图谱领域的多关系网络表示学习（Multi-relationNetworkEmbedding），Facebook的Adam[21]等研究员提出了 PyTorch-BigGraph（PBG）系统。该系统后端采用PyTorch作为计算引擎。通过将图按照网格的方式切分，计算时只将该网格相关数据读取到内存中进行计算，这样可以达到在少数几台机器上利用外存进行训练的目的。但由于该系统在设计时与算法强绑定（针对知识图谱领域的多关系网络表示学习），因此无法支持Node2Vec以及Metapath2Vec等算法的计算。</p>
<h2>4.  总结与启发</h2>
<p>本文总结了过去几年里在图表示学习方面的系统优化工作。以TensorFlow为分界线，分别介绍了TensorFlow出现前从通信以及计算角度进行优化的工作，和TensorFlow出现后，如何在现有计算框架基础上增加网络表示学习计算能力的系统。在此，笔者对以上系统在各类算法支持程度以及超大规模网络支持层面进行了对比，如表格 1所示。</p>
<p> </p>
<p>表格1 图表示学习系统对比       （l表示全部支持，º表示部分支持）</p>
<div><img alt="" loading="lazy" src="/logbook/images/deep-learning/8cc9112e2e32526dde56.png"/></div>
<p>尽管现有系统在对网络表示学习的计算性能以及易用性方面行了深度优化工作。但在超大规模网络下仍然存在一些问题亟待解决。针对这些问题，学术界和工业界也处于不断探索的阶段。</p>
<p><b>缺乏在有限资源情况下针对超大规模网络游走算法高效计算的能力</b>。对于Node2Vec、Metapath2Vec等算法，需要首先根据游走的规则生成路径数据才可训练。由于该类算法的不规则数据访问等特性，在超大规模网络数据上往往需要较高的内存资源，甚至生成游走数据的时间比训练时间还要长[22][23]。虽然Euler提出的图查询引擎的方式可以解决TensorFlow上做该类计算的需求。但在实际使用过程中面临两方面重要的问题。一方面，部署成本高。尤其在超大规模网络下，为满足单个算法计算需要，除去训练过程本身所需内存资源外，还需要维护一个TB级别的图结构数据在内存中作为查询服务。在资源受限的情况下这种方式并不实用。另一方面，计算性能不理想。由于Euler采用了查询服务的方式做游走类计算，这种设计方式引入了许多不必要的数据拷贝与传输。</p>
<p><b>通用性与复杂业务场景下追求极致计算性能之间的矛盾</b>。TensorFlow等计算框架在深度学习领域的广泛应用证明了张量（Tensor）形式的数据表示在深度学习计算方面的成功。在图表示学习方面，若想利用TensorFlow作为后端计算引擎则需通过一层额外的“<b>翻译</b>”：将图数据结构转化为Tensor格式，以及将<b>图视角的计算模式</b>转化为更通用的<b>数据流图视角的计算模式</b>。这种方式在某些情况下可以兼顾通用性以及很好的性能。目前主流的图深度学习框架均采用了这种方式。然而，在一些特定业务场景下，这层“翻译”的开销变得不可忽略。为了追求极致性能，也需要针对性的做定制化的计算优化。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/f6516e933bc1085d92f6.png"/></p>
<p>      图5 Plato2.0架构</p>
<p>综合上述考量，微信数据中心团队通过博览众家所长，结合业务特点批判性地接收了过去不同图表示学习框架的设计精髓，将已有的柏拉图（Plato）图计算平台[20]，扩展成为支持高性能分布式图表示学习计算的图机器学习平台。填补了在图计算平台与机器学习平台之间的空白。在微信全量关系网络上，将以往若干天才能完成的二阶游走类算法（Node2Vec等路径生成部分计算）的计算缩短到了“一杯咖啡时间”，实现了从天级别到分钟级别的跨越。对于模型训练，相比Euler以及AngleEmbedding，可以在使用20%资源基础上达到3-6倍的性能提升。</p>
<h2>更多详细内容，请访问：高性能图计算平台Plato系列文集</h2>
<h3>参考文献</h3>
<p>[1] Ordentlich, Erik, et al. "Network-efficient distributed word2vec training system for large vocabularies." Proceedings of the 25th ACM International on Conference on Information and Knowledge Management. ACM, 2016.</p>
<p>[2]分布式机器学习系统AnyEmbedding设计与实现[内部链接已移除]</p>
<p>[3]千亿级网络表示学习的Angel实现[内部或本地链接已移除]</p>
<p>[4] Zhang, Mingxing, et al. "Exploring the hidden dimension in graph processing." 12th {USENIX} Symposium on Operating Systems Design and Implementation ({OSDI} 16). 2016.</p>
<p>[5] Stergiou, Stergios, et al. "Distributed negative sampling for word embeddings." Thirty-First AAAI Conference on Artificial Intelligence. 2017.</p>
<p>[6]Xiao, Wencong, et al. "Tux²: Distributed Graph Computation for Machine Learning." 14th {USENIX} Symposium on Networked Systems Design and Implementation ({NSDI} 17). 2017.</p>
<p>[7] Ji, Shihao, et al. "Parallelizing word2vec in shared and distributed memory." IEEE Transactions on Parallel and Distributed Systems (2019).</p>
<p>[8] TensorFlow XLA <a href="https://www.tensorflow.org/xla">https://www.tensorflow.org/xla</a></p>
<p>[9] Abadi, Martín, et al. "Tensorflow: A system for large-scale machine learning." 12th {USENIX} Symposium on Operating Systems Design and Implementation ({OSDI} 16). 2016.</p>
<p>[10] A distributed graph deep learning framework. <a href="https://github.com/alibaba/euler">https://github.com/alibaba/euler</a></p>
<p>[11] Deep Graph Library <a href="https://www.dgl.ai/">https://www.dgl.ai/</a></p>
<p>[12]Geometric Deep Learning Extension Library for PyTorch<a href="https://github.com/rusty1s/pytorch_geometric">https://github.com/rusty1s/pytorch_geometric</a></p>
<p>[13] Hamilton, William L., Rex Ying, and Jure Leskovec. "Representation learning on graphs: Methods and applications." arXiv preprint arXiv:1709.05584 (2017).</p>
<p>[14] Zhou, Jie, et al. "Graph neural networks: A review of methods and applications." arXiv preprint arXiv:1812.08434 (2018).</p>
<p>[15] 大规模Network Embedding算法研究与应用[内部或本地链接已移除]</p>
<p>[16] Malewicz, Grzegorz, et al. "Pregel: a system for large-scale graph processing." Proceedings of the 2010 ACM SIGMOD International Conference on Management of data. ACM, 2010.</p>
<p>[17] Gonzalez, Joseph E., et al. "Powergraph: Distributed graph-parallel computation on natural graphs." Presented as part of the 10th {USENIX} Symposium on Operating Systems Design and Implementation ({OSDI} 12). 2012.</p>
<p>[18] Gonzalez, Joseph E., et al. "Graphx: Graph processing in a distributed dataflow framework." 11th {USENIX} Symposium on Operating Systems Design and Implementation ({OSDI} 14). 2014.</p>
<p>[19] Li, Mu, et al. "Scaling distributed machine learning with the parameter server." 11th {USENIX} Symposium on Operating Systems Design and Implementation ({OSDI} 14). 2014.</p>
<p>[20] 高性能图计算平台Plato[内部或本地链接已移除]</p>
<p>[21] Lerer, Adam, et al. "PyTorch-BigGraph: A Large-scale Graph Embedding System." arXiv preprint arXiv:1903.12287 (2019).</p>
<p>[22]Qiu, Jiezhong, et al. "NetSMF: Large-Scale Network Embedding as Sparse Matrix Factorization." (2019).</p>
<p>[23] Zhou, Dongyan, Songjie Niu, and Shimin Chen. "Efficient Graph Computation for Node2Vec." arXiv preprint arXiv:1805.00280 (2018).</p>
<p>[24] 微信传播系列一：社会传播简述[内部或本地链接已移除]</p>
<p>[25] 微信传播系列三：超大规模Network Embedding在微信网络的实践（Node2Vec篇）[内部或本地链接已移除]</p>
<p> </p>
</div> 
{% endraw %}
