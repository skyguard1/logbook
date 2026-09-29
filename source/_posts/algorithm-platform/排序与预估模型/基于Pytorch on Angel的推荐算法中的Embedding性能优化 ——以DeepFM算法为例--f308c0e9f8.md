---
title: "基于Pytorch on Angel的推荐算法中的Embedding性能优化 ——以DeepFM算法为例"
date: 2022-04-15 10:00:03
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<h2>引言</h2>
<p>在推荐系统中，原始的one-hot编码特征具备高维、稀疏的特点，并且推荐系统的性能与低阶和高阶组合特征的学习十分相关。在这种情况下，目前主流的推荐算法，如：DeepFM算法，除了原始高维稀疏线性模型的学习外，还引入嵌入向量（embedding vector）解决高维稀疏场景下样本缺失导致组合特征学习不充分的问题，并且利用深度学习模型强大的特征表示能力对高阶组合特征进行学习以保证推荐系统的性能。这样的算法要求机器学习平台具有处理高维稀疏模型与深度模型的复合能力。</p>
<p>Pytorch on Angel便是能满足这一要求的面向高维稀疏场景的高性能分布式深度学习平台，并且目前已支持DeepFM、xDeepFM、Attention-Net、Attention-FM等多种结合深度学习模型的推荐算法。尽管Pytorch on Angel已是功能全面、性能高效的平台，但就算法的具体实现而言，仍存在优化的空间。在上述推荐算法中，各个对象的embedding vector学习是算法流程整体耗时的主要来源之一，本文将以DeepFM算法为例，重点关注算法流程中embedding vector学习的相关步骤的耗时情况，并且进行优化，实现耗时的显著降低以达到提升算法整体性能的目的。</p>
<h2>Pytorch on Angel架构简介</h2>
<p>首先对Pytorch on Angel的主要架构进行简要介绍,详情可参考文章《Pytorch on Angel：面向稀疏高维场景的轻量深度学习框架》。如图1所示，PyTorch on Angel 的架构设计主要由Python Client、Angel PS以及Spark Executor三部分组成:</p>
<ul><li>Python Client:用户使用TorchScript语法编写算法模型, TorchScript是一种利用PyTorch代码创建可序列化和可优化模型的方法，任何TorchScript都可以从Python进程中定义并保存, 然后加载到非Python环境下运行, 如c++。</li>
<li>Angel PS: 提供通用的参数服务器服务，负责模型的分布存储，通讯同步和协调计算。</li>
<li>Spark Executor: 负责数据处理、加载编写好的PyTorch算法模型通过Angel PS完成模型的分布式训练和预测。特别地，PyTorch C++后端作为实际的计算引擎以native的方式运行在Spark Executor中。</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ebfba5fd5e0fbe3330df.png"/></p>
<p><strong>图</strong><strong>1:</strong><strong>Pytorch on Angel架构示意图</strong> </p>
<h2>Embedding相关步骤与耗时分析</h2>
<p>首先介绍Embedding优化前一个完整的算法流程中与embedding相关的各主要步骤。</p>
<ul><li>
<h3>Embedding PS Model的构建与划分</h3>
</li>
</ul><p>Python Client完成pytorch model的初始化后，Spark executor加载pytorch model并与Angel PS通信，Angel PS根据pytorch model创建MatrixContext以描述embedding矩阵的size、行数据类型与划分方式等信息，并进一步完成embedding模型矩阵的创建、划分和分布式存储。</p>
<p>所创建的embedding矩阵大小为（embedding_dim*input_dim）（为了描述简便，暂不考虑optimizer的numslots，即numslots=1）。在优化之前，模型的划分方式是在模型矩阵的行尺度和列尺度上均进行分割，即将模型矩阵分割成一个个block（partition）存储在各个PS上，此时需要注意，每个block中的每一列vector均不是完整的一个embedding vector，如图2所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8668848df0632cbfec5e.png"/></p>
<p><strong>图</strong><strong>2：优化前的</strong><strong>embedding矩阵划分示意图</strong></p>
<p> </p>
<ul><li>
<h3>pull步骤</h3>
</li>
</ul><p>Executor根据所分到的一个batch的输入数据向PS申请拉取对应的模型参数向量，形成参数矩阵，此时，参数矩阵中的每一列均为一个完整的参数向量，即在拉取之后需要对不完整的参数向量进行整合，并以Array[Vector]的方式进行存储。</p>
<ul><li>
<h3>参数数据结构转换步骤</h3>
</li>
</ul><p>对参数矩阵进行数据结构转换以便后续的梯度计算。具体地，将Array[Vector]转换为Array[Float]以存储参数矩阵的所有元素，代码中采用逐个元素遍历的方式完成，需要两层循环实现。</p>
<ul><li>
<h3>梯度计算步骤</h3>
</li>
</ul><p>利用pytorch自动求导完成梯度计算，并以Array[Float]形式输出。</p>
<ul><li>
<h3>梯度数据结构转换步骤</h3>
</li>
</ul><p>对输出的梯度进行数据结构转换以便后续的push&amp;update进行。具体地，将Array[Float]转换为Array[Vector]形式存储梯度从而与embedding模型矩阵对应，代码中同样采用逐个元素遍历的方式完成，需要两层循环实现。</p>
<ul><li>
<h3>push&amp;update步骤</h3>
</li>
</ul><p>在该步骤中，Spark executor会向Angel PS传送embedding模型参数更新请求，请求是按PS上对模型划分产生的相关blocks依次进行发送的，PS接收到请求就会更新相应blocks的模型参数，blocks数量越多，需要通信与执行更新请求的次数就越多。 </p>
<p>基于以上介绍，embedding相关步骤的耗时存在优化空间的原因主要如下：一方面，对于pull和push&amp;update步骤而言，耗时长的原因主要是Angel PS上对embedding矩阵模型<strong>划分粒度过于细化</strong>。原有的方式是在两个维度上将embedding矩阵划分成了一个个小块（block）分别存储于各个PS上。如此一来，在executor从PS拉取（pull）这些block后还要将相关block进行整合生成完整的embedding vector以便后续计算，整合的操作产生了耗时。而在push&amp;update步骤中，excutor需要按每个block分别向PS传送请求，PS接收到请求后需要对相应block的模型参数分别进行更新，过于细化的模型划分增加了block个数（即通信与执行更新的次数），增加了耗时。我们可以发现，初始完整的embedding vector至此经过了模型划分、拉取后整合、更新前再划分的操作，存在明显的冗余操作。另一方面，两次数据类型转换步骤的代码实现均采用了两层循环遍历矩阵所有元素的方式，这也是耗时较高的原因。</p>
<h2>优化思路与方案</h2>
<p>由于embedding向量的维度相比原始one-hot编码向量维度要小得多，因此无需对embedding矩阵做如此细化的划分，只需要在矩阵的行尺度上进行划分而在列尺度上保留完整的embedding vector即可，即划分后最小单位是一个完整的embedding vector，如图3所示。</p>
<p>在具体实现上，采用自定义的EmbeddingNode数据类型封装embedding vector，以K-V数据结构的形式进行访问与操作，每个embedding vector取出后为Array[Float]形式。基于上述划分方式，可以避免pull步骤中的整合耗时以及push&amp;update步骤中由于划分过于细化产生过多blocks增加了通信与执行更新操作次数的耗时。另外，在两次数据结构转换步骤中，也只需要一层循环，每次对一个完整的embedding vector进行操作，由于原始特征的稀疏特性，循环次数也十分有限，因此能够一定程度上减少耗时。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e2fc1f31872adf902411.png"/></p>
<p><strong>图</strong><strong>3 : 优化后的</strong><strong>embedding矩阵划分示意图</strong></p>
<p> </p>
<h2>性能结果</h2>
<p>我们以DeepFM算法为例，对embedding优化前后的性能进行测试与比较。具体的测试环境设置与性能结果如下：</p>
<ul><li>
<h3>数据集与模型参数</h3>
</li>
</ul><p>采用的数据集：kaggle-2014-criteo</p>
<p>数据集参数：sample_num = 45 million，input_dim = 1 million，fields_num = 39</p>
<p>Torch模型参数：input_dim = 1 million，fields_num = 39，embedding_dim = 200，fc_dims = 200, 400, 1</p>
<ul><li>
<h3>集群配置信息</h3>
</li>
</ul><p>ps.instances = 10，ps.cores = 1，ps.memory = 10 G，driver-memory=20 G</p>
<p>num-executors = 30，executor-cores = 1，executor-memory = 10 G</p>
<ul><li>
<h3>DeepFM算法参数</h3>
</li>
</ul><p>numDataPartitions = 100，numEpoch = 10，testRation = 0.1，batchSize = 2048</p>
<p>optimizer: Async Adam，stepSize = 0.001，decay = 0</p>
<ul><li>
<h3>结果展示与比较</h3>
</li>
</ul><p><strong>表1：</strong><strong>Embedding优化前后的各步骤平均耗时结果</strong><strong>(ms)</strong></p>
<table><tbody><tr><td>
<p> </p>
</td>
<td>
<p>优化前</p>
</td>
<td>
<p>优化后</p>
</td>
<td>
<p>性能提升百分比</p>
</td>
</tr><tr><td>
<p>avrPullTime</p>
</td>
<td>
<p>406</p>
</td>
<td>
<p>88.25</p>
</td>
<td>
<p>360.1%</p>
</td>
</tr><tr><td>
<p>avrMakeParamTime</p>
</td>
<td>
<p>822.75</p>
</td>
<td>
<p>666.75</p>
</td>
<td>
<p>23.4%</p>
</td>
</tr><tr><td>
<p>avrGradCalTime</p>
</td>
<td>
<p>1308.5</p>
</td>
<td>
<p>1350.75</p>
</td>
<td>
<p>X</p>
</td>
</tr><tr><td>
<p>avrMakeGradTime</p>
</td>
<td>
<p>1100.25</p>
</td>
<td>
<p>239.75</p>
</td>
<td>
<p>358.9%</p>
</td>
</tr><tr><td>
<p>avrPushUpdateTime</p>
</td>
<td>
<p>1157.75</p>
</td>
<td>
<p>49.25</p>
</td>
<td>
<p>2350.8%</p>
</td>
</tr><tr><td>
<p>avrEpochTime</p>
</td>
<td>
<p>7063518 (1.96h)</p>
</td>
<td>
<p>4889472 (1.35h)</p>
</td>
<td>
<p>44.5% </p>
</td>
</tr></tbody></table><p>如表1所示，除了梯度计算步骤外（优化前后均由pytorch自动完成），优化后各步骤的性能均有显著提升。具体地，pull步骤、参数数据结构转换（MakeParam）步骤、梯度数据结构转换步骤（MakeGrad）与push&amp;update步骤的性能分别提升了360.1%、23.4%、358.9%与2350.8%，单次epoch的性能提升了44.5%。</p>
<h2>结语</h2>
<p>本文仅以DeepFM算法为例介绍Embedding优化的原理、方案以及效果，但优化的思想与方案对包含embedding vector学习的算法具有扩展性，同样可以借鉴。</p> 
{% endraw %}
