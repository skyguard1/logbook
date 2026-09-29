---
title: "DeepFM模型的分布式训练与调优"
date: 2022-06-15 14:46:35
categories:
  - 推荐算法
  - 训练平台与实时工程
---

{% raw %}

<h2>1.前言</h2>
<p>现阶段Deep Learning在推荐系统中广泛应用，深度模型尤其是<a href="https://arxiv.org/abs/1703.04247">DeepFM</a>在CTR排序取得了不错的效果。</p>
<p>DeepFM模型由FM与Deep两部分组成，：</p>
<p>1.FM部分可以通过隐向量点积的方法高效的获得2阶特征表示</p>
<p>2.Deep部分通过多层的全连接网络，学习high-order高阶特征</p>
<p></p>
<p>当前DeepFM模型在我们的金融资讯推荐场景中，已经线上服务了一年多，并贡献了优异的效果。我们基于GaiaStack集群和Ceph文件存储实现DeepFM模型的例行化训练，实现方案可参考我们过去的文章： Tesla上基于TF的深度模型训练与性能优化</p>
<p>但是随着业务的发展，数据量的增多，这套模型训练框架存在一些局限性：</p>
<p>1. 不支持直接读取TDW表，需要将TDW数据下载到Ceph集群</p>
<p>2. 数据基于python预处理，对数据量大的场景十分吃力</p>
<p>3. 不支持分布式训练，若没有GPU资源，训练效率比较低</p>
<p></p>
<h2>2.分布式提升训练效率</h2>
<p>综上所述，我们希望对数据预处理与模型训练两个模块，优化训练框架的效率与性能。在没有GPU资源的前提下，要想提升深度模型的训练效率，只能依赖于多机分布式训练。TensorFlow是支持模型的分布式训练，其默认采用Ps-Worker架构，原理如下图所示。其中PS节点执行模型相关的作业，包括模型参数存储，分发，汇总，更新。Worker节点执行训练相关的作业，包括推理计算和梯度计算。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/06db9c7729e7a24d9306.png"/></p>
<p>为实现深度模型的分布式训练，我们对比了公司内外多个分布式训练框架OnlineDeepCTR、Spark-Fuel、Horovod等，Spark-Fuel具有直接在Tesla部署训练任务读取TDW数据的易用性优势，因此我们基于Spark-Fuel框架实现对整个训练流程进行优化。</p>
<p>首先针对数据预处理模块，整个训练框架由GaiaStack集群切换为Spark集群实现，可直接分布式处理TDW的RDD数据。打破数据壁垒，无需将数据转移至Ceph存储，再通过低效率的Python线性处理。Spark分布式数据处理效率是Python线性处理的10倍左右。</p>
<table><tbody><tr><td>数据量</td>
<td>Spark处理时长</td>
<td>Python处理时长</td>
</tr><tr><td>300万</td>
<td>5min</td>
<td>48min</td>
</tr></tbody></table><p>然后针对模型训练模块，我们基于机器学习加速框架Spark-Fuel，开发了深度模型的分布式训练组件，可直接在Tesla的Spark集群上分布式训练TensorFlow的深度模型，显著提升模型训练速率。不同节点数我们资讯业务场景DeepFM模型的分布式训练耗时如下表所示：</p>
<table><tbody><tr><td>work节点数</td>
<td>ps节点数</td>
<td>训练耗时</td>
</tr><tr><td>单机</td>
<td>单机</td>
<td>130min</td>
</tr><tr><td>12</td>
<td>2</td>
<td>122min</td>
</tr><tr><td>24</td>
<td>4</td>
<td>61min</td>
</tr><tr><td>40</td>
<td>8</td>
<td>52min</td>
</tr><tr><td>60</td>
<td>12</td>
<td>58min</td>
</tr></tbody></table><p>由表中的实验结果，可看出分布式训练速率优于单机训练，但并不是分布式的节点越多越好。当节点数量增加的同时，分布式训练过程中节点通信消耗会增大，同时在Tesla平台申请资源的耗时也会增加。</p>
<p></p>
<h2>3.分布式训练导致效果下滑</h2>
<p>基于Spark分布式训练对比单机训练，给深度模型带来了训练速率的提升，但是训练出的深度模型的效果更加重要。对于推荐场景的DeepFM这类CTR预估模型，在离线下一般通过AUC评估其效果，AUC可一定程度反应模型可能的线上效果。</p>
<p>我们选取了相同的训练数据和评测数据进行多组DeepFM模型训练实验，发现分布式训练的模型在评测集的AUC相比于单机有显著的下滑，且AUC波动很大，甚至出现了AUC为0.5的情况。我们打开TensorBoard对模型训练过程，对训练集的Loss变化进行分析，发现训练集Loss波动非常大，且会在某些step突然增高。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/7798f88d8bfb6b9fbbd0.png"/></p>
<p>大多数推荐业务场景都不可能为了离线模型训练速度的提升，去接受线上效果的下滑。一个效果不稳定的模型训练方案，是无法例行化部署供上线使用的，若是得到上图这类完全跑飞的模型，线上用户的体验将会受到很大影响。</p>
<p></p>
<h2>4.DeeopFM模型效果下滑问题分析</h2>
<p>我们对DeepFM分布式训练时AUC下滑的原因进行了思考，认为分布式训练会带来一定模型效果的损失，但模型拟合过程不应该如此不稳定，我们认为还可能是数据质量或模型结构等原因导致。为了找出导致DeepFM模型效果下滑的因素，我们从<strong>分布式</strong>、<strong>数据</strong>、<strong>模型</strong>三方面出发进行了多组对比实验，并基于TensorBoard分析训练过程中Loss的变化。</p>
<h3>1.分布式因素分析</h3>
<p>首先我们将DeepFM模型分布式训练直接与单机训练对比，得到如下图所示的Loss变化，其中左图为分布式训练，右图为单机训练。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/380453199dfc83f56403.png"/><img alt="" loading="lazy" src="/logbook/images/recommendation/754d7b052b2c38f76759.png"/></p>
<p>分析上图的结果，显然分布式训练的确会给DeepFM模型性能带来负面影响。为了更深入地探究分布式节点数目是否会影响DeepFM模型效果，我们对DeepFM模型进行不同work和ps节点的分布式训练，并记录了如下表所示的实验结果(3次实验取平均)。</p>
<table><tbody><tr><td>work节点数</td>
<td>ps节点数</td>
<td>评测集AUC</td>
<td>评测集Loss</td>
</tr><tr><td>单机</td>
<td>单机</td>
<td>0.753311(±0.003)</td>
<td>0.2253</td>
</tr><tr><td>12</td>
<td>2</td>
<td>0.743713(±0.01)</td>
<td>0.2306</td>
</tr><tr><td>24</td>
<td>4</td>
<td>0.731418(±0.03)</td>
<td>0.2361</td>
</tr><tr><td>40</td>
<td>8</td>
<td>0.704394(±0.05)</td>
<td>0.2724</td>
</tr><tr><td>60</td>
<td>12</td>
<td>0.640923(±0.1)</td>
<td>0.4278</td>
</tr></tbody></table><p>由上图的结果和Loss变化曲线的分析，我们发现分布式节点数越多，DeepFM模型的效果越差，Loss跑飞的概率越大。分布式训练中多个计算节点计算进度不是完全一致的，在ps架构中同步机制可分为三种：</p>
<p>BSP：在每一轮迭代中都需要等待所有的Task计算完成。<br/>SSP：最快的Task最多领先最慢的Task staleness 轮迭代。<br/>ASP：Task之间完全不用相互等待，先完成的Task，继续下一轮的训练。 TensorFlow分布式训练的默认同步方式。</p>
<p>为了探究是否是ASP这类异步训练机制导致的模型效果下降，我们实现了SSP方式进行DeepFM模型训练实验，其中下图为staleness=100的Loss变化曲线。我们发现SSP的同步机制，有缓解分布式训练过程中带来的抖动，但是仍会存在Loss的突然升高，且模型的训练时长增加了约15%。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/8b8fb8649557a2b65c06.png"/></p>
<h3>2.数据因素分析</h3>
<p>为了探究是否为业务上报数据质量问题，脏数据较多导致的模型效果下滑。我们下载了质量较高的公开kaggle广告比赛数据集，CTR评估数据集<a href="https://www.kaggle.com/c/criteo-display-ad-challenge">criteo</a>对DeepFM模型进行分布式训练，实验的Loss变化如下图所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/425f2f059c06662d2735.png"/></p>
<p>对多组实验结果分析，我们发现criteo数据也会出现Loss跑飞的现象，但是能迅速拉会。而同样的DeepFM模型在业务数据中分布式训练表现较差，因此我们认为相对于criteo数据集，我们的业务数据可能质量不高或者分布不佳。</p>
<h3>3.模型因素分析</h3>
<p>为了探究分布式训练对除了DeepFM模型以外的其他深度模型，是否会带来的模型效果下滑。我们实现了一个普通的DNN模型在同样的业务数据下进行分布式训练实验，得到了如下图所示的Loss变化曲线。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/15101ca7d16bb11ca240.png"/></p>
<p>对多组实验结果分析，我们发现DNN模型的Loss拟合十分平稳，即使增大ps节点数，也不会带来较大的波动。但是DNN模型的效果确实不如DeepFM，评测集AUC为0.73。</p>
<p></p>
<h2>5.性能优化</h2>
<h3>1.DeepFM模型结构优化</h3>
<p>在之前的分析中，发现DNN模型并不会出现Loss大幅度升高。因此我们做了消融实验将DeepFM模型的FM部分去除，仅输出Deep部分结果在同样的条件下去进行分布式训练，结果并没有出现剧烈的Loss波动问题。因此我们认为DeepFM模型中的FM部分可能是导致该问题的重要原因。</p>
<p><strong>1.1 FM部分输出层优化</strong></p>
<p>在DeepFM论文中FM部分的输出由一个Addition unit 和 一个Inner Product units 求和得到：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/8b8cf7db6d7e69c41793.png"/></p>
<p>在我们最初的DeepFM模型的实现中，是完全参考论文中的公式实现，对于公式左边的Addition unit实现如下：</p>
<div>
<pre>with tf.variable_scope("First-order"):
        feat_wgts = tf.nn.embedding_lookup(FM_W, feat_ids)  # None * F
        y_w = tf.reduce_sum(tf.multiply(feat_wgts, feat_vals), 1)  # None * 1</pre>
</div>
<p> 对于公式右边的Inner Product units，通过以下公式可简化其计算，转化为和平方与平方和两部分：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/74942c1662199d9a98fe.png"/></p>
<div>
<pre>with tf.variable_scope("Second-order"):
        embeddings = tf.nn.embedding_lookup(FM_V, feat_ids)  # None * F * K
        feat_vals = tf.reshape(feat_vals, shape=[-1, field_size, 1])
        embeddings = tf.multiply(embeddings, feat_vals)  # vij*xi
        sum_square = tf.square(tf.reduce_sum(embeddings, 1))
        square_sum = tf.reduce_sum(tf.square(embeddings), 1)
        y_v = 0.5 * tf.reduce_sum(tf.subtract(sum_square, square_sum), 1)  # None * 1

y_fm = y_w + y_v</pre>
</div>
<p>FM部分的输出的计算仅有FM_W和FM_V两个参数，主要通过公式计算得到，且参数FM_V与Deep部分共享。为了避免某些包含异常值的Batch，导致FM部分出现分布变化较大的问题，我们在FM部分的输出层增加了<strong>Batch_Norm</strong>与<strong>Dropout</strong>，以加速DeepFM模型训练平稳收敛。</p>
<div>
<pre>with tf.variable_scope("First-order"):
    feat_wgts = tf.nn.embedding_lookup(FM_W, feat_ids)  # None * F
    first_order_part = tf.multiply(feat_wgts, feat_vals)  # None * F
    first_order_part = batch_norm_layer(first_order_part, train_phase=train_phase, scope_bn='bn_first')  # None * F
    if train_phase:
        first_order_part = tf.nn.dropout(first_order_part, keep_prob=0.8)
    y_w = tf.reduce_sum(first_order_part, 1)  # None * 1

with tf.variable_scope("Second-order"):
    embeddings = tf.nn.embedding_lookup(FM_V, feat_ids)  # None * F * K
    feat_vals = tf.reshape(feat_vals, shape=[-1, field_size, 1])
    embeddings = tf.multiply(embeddings, feat_vals)  # vij*xi
    sum_square = tf.square(tf.reduce_sum(embeddings, 1))  # None * K
    square_sum = tf.reduce_sum(tf.square(embeddings), 1)  # None * K
    second_order_part = 0.5 * (tf.subtract(sum_square, square_sum))  # None * K
    second_order_part = batch_norm_layer(second_order_part, train_phase=train_phase, scope_bn='bn_second')  # None * K
    if train_phase:
        second_order_part = tf.nn.dropout(second_order_part, keep_prob=0.8)
    y_v = tf.reduce_sum(second_order_part, 1)  # None * 1

y_fm = y_w + y_v</pre>
</div>
<p> 对优化后的模型进行多次分布式训练，训练过程中Loss变化如下图所示，模型收敛平稳了许多，且评测集AUC达到了74.85%。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/47280a9929fda339aaea.png"/></p>
<p><strong>2.2 FM与Deep部分结合方式优化</strong></p>
<p>在DeepFM论文<a href="https://arxiv.org/pdf/1703.04247.pdf"></a>中最终的模型输出如下公式所示，由FM部分的输出与Deep部分的输出相加得到。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/f1f835b2222992843722.png"/></p>
<p>在深度模型的网络结构设计中，特征结合的方式一般有concat和add两种，查阅了GitHub上开源的DeepFM模型实现，既有concat结合也有add结合的实现。在CV图像的特征结合中，一般认为concat是通道数的合并，也就是说描述图像本身的特征增加了，而每一特征下的信息是没有增加。add是描述图像的特征下的信息量增多了，但是描述图像的维度本身并没有增加，只是每一维下的信息量在增加。DeepFM论文中作者选择的是将FM部分与deep部分使用add方式结合，这样需要的内存和参数会小于concat。但是直观上我们认为二者得到并非同一特征，因此我们按照以下代码实现了concat结合方式的DeepFM模型，没有对FM部分的输出做reduce_sum，Deep部分也保留了隐层维度。</p>
<div>
<pre>with tf.variable_scope("First-order"):
    feat_wgts = tf.nn.embedding_lookup(FM_W, feat_ids)  # None * F
    first_order_part = tf.multiply(feat_wgts, feat_vals)  # None * F

with tf.variable_scope("Second-order"):
    embeddings = tf.nn.embedding_lookup(FM_V, feat_ids)  # None * F * K
    feat_vals = tf.reshape(feat_vals, shape=[-1, field_size, 1])
    embeddings = tf.multiply(embeddings, feat_vals)  # vij*xi
    sum_square = tf.square(tf.reduce_sum(embeddings, 1))  # None * K
    square_sum = tf.reduce_sum(tf.square(embeddings), 1)  # None * K
    second_order_part = 0.5 * (tf.subtract(sum_square, square_sum))

with tf.variable_scope("FM-part"):
    fm_part = tf.concat([first_order_part, second_order_part], axis=1)  # None * (F+K)
    fm_part = batch_norm_layer(fm_part, train_phase=train_phase, scope_bn='bn_second')  # None * K
    if train_phase:
        fm_part = tf.nn.dropout(fm_part, keep_prob=0.8)

with tf.variable_scope("Deep-part"):
    deep_part = tf.reshape(embeddings, shape=[-1, field_size * embedding_size])  # None * (F*K)
    for i in range(len(layers)):
        deep_part = tf.contrib.layers.fully_connected(inputs=deep_part, num_outputs=layers[i],
                                                      weights_regularizer=tf.contrib.layers.l2_regularizer(
                                                            l2_reg), scope='mlp%d' % i)
        deep_part = batch_norm_layer(deep_part, train_phase=train_phase, scope_bn='bn_%d' % i)
        if train_phase:
            deep_part = tf.nn.dropout(deep_part, keep_prob=dropout[i])

with tf.variable_scope("DeepFM-out"):
    y = tf.layers.dense(tf.concat([fm_part, deep_part], axis=1), 1, activation=None)
    y = tf.reshape(y, shape=[-1])
    pred = tf.sigmoid(y)</pre>
</div>
<p>在相同条件下，对concat和add两种结合方式的DeepFM进行了分布式训练对比实验，由下表结果可看出concat方式的评测集AUC略优于add结合方式。</p>
<table><tbody><tr><td>
<p>实验</p>
</td>
<td>DeepFM_Add(AUC)</td>
<td>DeepFM_Concat(AUC)</td>
<td>DeepFM_Add(Loss)</td>
<td>DeepFM_Concat(Loss)</td>
</tr><tr><td>第一次</td>
<td>0.747851</td>
<td>0.748426</td>
<td>0.230794</td>
<td>0.228343</td>
</tr><tr><td>第二次</td>
<td>0.747009</td>
<td>0.750478</td>
<td>0.227214</td>
<td>0.227494</td>
</tr><tr><td>第三次</td>
<td>0.750747</td>
<td>0.753215</td>
<td>0.225695</td>
<td>0.233153</td>
</tr><tr><td>平均</td>
<td>0.7485(±0.0022)</td>
<td>0.7507(±0.0025)</td>
<td>0.2279</td>
<td>0.2296</td>
</tr></tbody></table><p>下左图为concat结合方式的DeepFM的训练Loss拟合曲线，对比右图add结合方式的训练Loss拟合曲线（注意纵坐标刻度不一致），可看出concat结合方式模型收敛更快（左图在1k steps loss拟合至0.3以下，而右图在4k才拟合至0.3以下），且Loss波动更小（左图拟合后Loss在0.24-0.3之间波动，而右图在0.24-0.47之间波动）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/7e7d5787a068f63960f2.png"/>     <img alt="" loading="lazy" src="/logbook/images/recommendation/6b22f5c3f496cb1446f7.png"/></p>
<h3>2.业务数据优化</h3>
<p><strong>2.1 连续特征归一化优化</strong></p>
<p>连续值在输入Deep模型时需要归一化，在之前的深度模型训练方案中，我们使用的是Z-Score归一化。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/c4379e5e167c0f1e939f.png"/></p>
<p>其中μ为特征的均值，σ为特征的标准差，两者均需在特征预处理前统计。最初受限于Python的计算速率与资源的限制，我们采样部分样本提前统计一份特征的μ与σ用于归一化，很长时间(1-2月)更新一次。</p>
<p>新的深度模型训练方案转移至Spark集群实现，我们将Z-Score归一化参数μ和σ每日基于全量训练数据重新统计，并对特征进行归一化输入深度模型。实验表明，对连续特征归一化参数优化后，DeepFM模型训练过程中Loss的抖动得到改善。</p>
<p><strong>2.2 训练样本打散策略优化</strong></p>
<p>基于Spark集群分布式训练深度模型原理是，通过pySpark读取RDD数据，预处理后为RDD Batch数据，然后Feed给TensorFlow的Worker节点直接训练。</p>
<p>为了RDD样本数据更好地满足独立同分布，在RDD数据的预处理部分我们首先通过repartition进行了第一层打散。为了避免一些异常数据集中在同一个Batch中，我们在mapPartition将RDD数据转化为Batch前，对其进行了第二层的打散。实验表明，增加两层样本打散策略后不仅Loss的抖动得到了缓解，同时还带来了约1%的AUC提升。</p>
<p></p>
<h3>3.超参优化</h3>
<p>设计对比实验分析节点数量，对模型分布式训练速度与效果的影响，我们发现节点数量的增多并不能线性提高训练速率，反而带来了模型效果的波动。最终模型训练任务设置ps节点数为4，worker节点20。同时为了减少训练过程中异常数据带来的波动，我们增大了batch_size，降低了学习率，增大了模型训练epoch。</p>
<p>下表为2020-05-27至2020-05-31，基于Spark分布式训练DeepFM模型与基于GaiaStack单机训练DeepFM模型，在资讯业务数据中离线评估AUC结果对比。</p>
<table><tbody><tr><td>日期</td>
<td>分布式 AUC</td>
<td>单机 AUC</td>
</tr><tr><td>20200527</td>
<td>0.755266</td>
<td>0.753037</td>
</tr><tr><td>20200528</td>
<td>0.758298</td>
<td>0.753096</td>
</tr><tr><td>20200529</td>
<td>0.748367</td>
<td>0.748781</td>
</tr><tr><td>20200530</td>
<td>0.753311</td>
<td>0.755004</td>
</tr><tr><td>20200531</td>
<td>0.760408</td>
<td>0.760977</td>
</tr></tbody></table><p>在推荐业务场景中离线AUC的评测效果，并不能完全反应线上的点击率表现，因此仍需在线上进行ABTest对比。下图是近一周资讯推荐业务中深度模型线上的点击率表现，其中黄线是基于Spark分布式训练的DeepFM模型，蓝线是旧框架基于GaiaStack单机训练的DeepFM模型，可以看出优化后的分布式训练DeepFM模型在线上表现甚至略优于旧DeepFM模型，同时离线训练速率快了2.5倍。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/b6d44136f6cbd8c1bfb5.png"/></p>
<p></p>
<h2>5.结语</h2>
<p>我们通过在Spark集群分布式训练TensorFlow深度模型，以提升在金融推荐场景下深度模型的训练效率。同时针对分布式训练过程中DeepFM模型效果下滑，进行了多角度的问题分析，并从数据、模型结构等多方面进行优化。最终金融资讯场景DeepFM模型的训练耗时由2.1小时减少至1小时，且线上ABTest表现略优于单机DeepFM模型。在此也感谢leocchen，sunnyqiao，shijiexu，sharkdtu等同事的探讨和协作。以上工作内容已经在资讯推荐业务场景中应用上线，同时也将我们尝试过的深度模型算法及分布式训练实现开源至TRSx项目中，欢迎大家关注和贡献代码。</p>
<p></p>
<h2>6.附录及参考文献</h2>
<p><strong>公司内部开源分布式训练框架：</strong></p>
<p>Spark-Fuel (Python+Spark) : [内部或本地链接已移除]</p>
<p>OnlineDeepCTR (Python+Spark) ：[内部或本地链接已移除]</p>
<p>Lingqu (Scala+Spark) : [内部或本地链接已移除]</p>
<p><strong>DeepFM相关资料:</strong></p>
<p>论文：<a href="https://arxiv.org/pdf/1703.04247.pdf">https://arxiv.org/pdf/1703.04247.pdf</a></p>
<p>DeepFM模型TensorFlow实现开源代码（来自开源协同项目TRSx）：[内部或本地链接已移除]</p>
<p>DeepFM模型TensorFlow实现开源代码（来自GitHub Star最高）：<a href="https://github.com/ChenglongChen/tensorflow-DeepFM/blob/master/DeepFM.py">https://github.com/ChenglongChen/tensorflow-DeepFM/blob/master/DeepFM.py</a></p> 
{% endraw %}
