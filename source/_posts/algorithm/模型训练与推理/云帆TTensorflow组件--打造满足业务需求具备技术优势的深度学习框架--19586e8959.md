---
title: "云帆TTensorflow组件--打造满足业务需求具备技术优势的深度学习框架"
date: 2022-03-30 10:02:55
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<div>一、TTensorflow介绍</div>
<div>二、模型编译优化</div>
<div>      2.1 业界编译优化方法</div>
<div>      2.2 云帆编译优化改进</div>
<div>              2.2.1 自适应动态编译框架</div>
<div>              2.2.2 改进算子表达</div>
<div>              2.2.3 改进编译图优化</div>
<div>              2.2.4 XLA支持Horovod算子</div>
<div>三、高维动态稀疏特征支持</div>
<div>        3.1 动态Embedding</div>
<div>        3.2 稀疏优化器SparseAdam</div>
<div>四、LAMB优化器</div>
<div>五、混合精度</div>
<div>六、TTensorflow安装方法</div>
<div>七、TTensorflow接入太极平台</div>
<div>八、TTensorflow上云</div>
<div>九、总结与展望</div>
<div>        9.1 云帆Oteam TTensorflow组件贡献者</div>
<div>        9.2 后续规划</div>
<div>        9.3 如何加入</div>
<div>十、参考文献</div>
<div>
<h1>一、TTensorflow介绍</h1>
<p>云帆Oteam联合公司6大BG，19个团队协同打造端到端具备行业领先技术及影响力的深度学习框架和加速能力。TTensorflow组件是云帆Oteam的重要组件之一，立足于公司内丰富的深度学习场景，深耕编译优化、混合精度、稀疏支持等加速能力，已经接入了游戏AI绝悟/微信人脸支付/TI平台/微信看一看等业务，助力业务团队产生了正向收益。</p>
<h1>二、模型编译优化 </h1>
<h2>2.1 业界编译优化方法</h2>
<p>随着深度学习算法的飞速发展，模型结构变得越来越复杂，TensorFlow作为通用深度学习框架，不但要应对算力需求不断增长的计算密集型算子，也要应对用于IO或控制的大量小算子的扩展。此外，硬件算力也在不断提升，TensorFlow的模型执行也必须快速应对新硬件增长的算力潜力。</p>
<p>模型的执行可以等效于程序的编译，因而模型的优化可以借鉴程序编译的优化方法。对于模型的编译优化，原生TensorFlow推出了TensorFlow Grappler、XLA（Accelerated Linear Algebra）、MLIR（Multi-Layer Intermediate Representation）等方案。</p>
<p>    <img alt="" loading="lazy" src="/logbook/images/algorithm/0b4f6de4ce3fb444fa50.png"/></p>
<p>TensorFlow Grappler是TensorFlow runtime默认的图优化器，在TensorFlow的图执行器Executor执行时可进行图层级的指定优化，目前有Const foldingoptimization、Layout optimization等15种原生优化器，也支持基于MetaOptimizer扩展自定义的图执行优化器。</p>
<p>TensorFlowGrappler只支持图层级的优化，通常的使用范式是自定义实现优化的算子，再自定义实现一个GrapplerOptimizer，在模型执行时将TensorFlow的原生算子实现替换为自定义的优化实现。这种优化方案是由TensorFlow runtime支持的，因而可以用于训练和推理。云帆OTeam目前在云端GPU推理场景结合TF-TRT已有相关实践（详情见[3]）。</p>
<p>TensorFlowGrappler虽然可以做到平台无关，但只能在图层级进行优化，无法充分提升模型执行的性能。因而，TensorFlow在TensorFlow Dev Summit 2017上提出了XLA技术。XLA是一种TensorFlow上典型的模型编译技术，如下图所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/08a9f2d71b94a74cd769.png"/>XLA的典型流程如下。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/974d1c68b94686f08763.png"/></p>
<p>MLIR是TensorFlow在CGO 2019上提出的一个统一的深度学习编译器架构，致力于打造一个统一、模块化、可扩展的深度学习编译器基础设施。目前还处在实验改进阶段，实践应用还比较少。</p>
<p>可见，原生TensorFlow在模型编译优化方面打造并不断强化了基础设施支持，但是在实际业务场景的使用上依然存在优化策略不丰富、算子覆盖率不足、硬件支持度不够等缺陷。TensorFlow Grappler支持图层级优化只有典型的15种左右，XLA可以支持的模式和硬件也非常有限，MLIR目前则还处于实验阶断。</p>
<h2>2.2 云帆编译优化改进</h2>
<p>云帆OTeam针对原生TensorFlow在模型编译优化上的不足，在TensorFlow Grappler、XLA上都结合一线业务场景进行了深度优化，并保持着对MLIR等新技术的跟进。具体地：</p>
<ul><li>
<p>在实际业务的复杂模型场景中，针对原生XLA在特定业务瓶颈算子上的不足进行了深度优化，如多机多卡通信算子、DiagPartOp、DeptwiseConv2D等，在游戏AI、视觉智能（人脸识别等）等业务场景的模型训练中取得了不错的效果（详情见[4]）</p>
</li>
<li>
<p>针对原生TensorFlow Grappler的图优化丰富度不够，难以在实际业务中提升性能的问题，结合TF-TRT在云上GPU场景扩展了TensorFlowGrappler的图优化能力，在电商、直播、视频等云上客户的模型推理场景中取得了50%-200%的提升</p>
</li>
<li>在开源TensorFlow版本中，开源编译模块没有根据运行时实际的信息划分出适当的编译区域，实际运行中会产生冗余重编译等性能问题。例如，在TensorFLow编译优化流程中会强依赖张量形状，额外编译时间占用运行时间，而且编译形状变化的张量时，会导致重编译。云帆TTensorflow提出自适应动态编译框架，在游戏AI王者监督模型上已取得40%+加速比</li>
</ul><p>TTensorFlow中XLA的使用与原生XLA保持一致，用户可使用环境变量或config配置进行使用</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/03be5a1f130808a82a00.png"/>目前TTensorFlowXLA已经应用广泛应用到了实际业务场景中，几个典型场景的性能提升数据如下。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/60daa3f04876a4d0530a.png"/></p>
<h3><b>2.2.1 自适应动态编译框架</b></h3>
</div>
<div>通过采样运行时信息，自动调整编译区域和策略，灵活适应复杂场景。<br/><p><img alt="" loading="lazy" src="/logbook/images/algorithm/737e86bf1f2a997ea53d.png"/></p>
<h3><b>2.2.2 改进算子表达</b></h3>
<p>精细调整算子表达形式，避免引入冗余的计算和同步开销。</p>
</div>
<ol><li>动态形状算子识别与编译方案：预热运行时，采集张量实际的形状信息。比较同一张量在不同迭代步的形状，识别出形状变化的张量。将以这个张量为输入输出的算子标记成动态形状算子，在划分编译区域时排除在编译区域以外。</li>
<li>张量对角线算子表达的改进：用Gather操作代替Reduce操作，实现张量取对角线（DiagPart）语义。实测算子GPU性能提升4倍。</li>
</ol><p><img alt="" loading="lazy" src="/logbook/images/algorithm/e34836112112ed734cff.png"/></p>
<p>TensorFlow开源方案</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/89ae9e04bd0d5d5c1ebd.png"/></p>
<p>云帆TTensorflow改进方案</p>
<h3><b><strong>2.2.3 改进编译图优化</strong></b></h3>
<p>精细调整图变化算法，去除冗余操作，聚合亲和性算子。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/c3faa879031a90012304.png"/></p>
<h3>2.2.4 XLA支持Horovod算子</h3>
<p>在部分业务中，发现开启XLA会导致训练速度下降，分析原因后是由于XLA不支持Horovod导致的。因为XLA不支持Horovod，所以Nccl通信与计算无法并行，使得GPU空闲，训练速度缓慢。</p>
<p>云帆TTensorflow通过将Horovod Allreduce Op与XLA Cluster融合，将通信与计算并行，提升了训练速度，在绝艺围棋AI训练场景下，512卡扩展性从72.58%提升至91.32%；并且节省了手工切分jit_scope的耗时，在多个场景下，都可以达到甚至超过算法工程师手工优化的效果。下图为XLA支持Horovod后的timeline效果图（Horovod Allreduce算子已融入XLA Cluster）：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e771c9fbd5638a7af25f.png"/></p>
<h1>三、高维动态稀疏特征支持</h1>
<p>一方面，推荐场景有两大特点：</p>
<ol><li>
<p>用户、物品（内容）随时间快速变化：需要训练的特征参数也随之动态变化，流式数据+在线学习是常用的训练模式</p>
</li>
<li>
<p>千人千面千亿特征：一般而言，特征越丰富，模型表达能力越强，业务效果越好，为了保证训练效果，稀疏模型动辄100GB级别，乃至数十TB量级</p>
</li>
</ol><p>另一方面，原生TensorFlow是面向处理稠密数据而设计的，其应用拓展到推荐、广告、搜索等高维稀疏数据场景时，一般通过tf.Variable的方式实现静态Embedding机制，所谓“静态”是指用于存储Embedding的Variable空间大小固定，不能在训练过程中根据用户、物品动态调整，这一机制在实际业务中暴露出很多弊端，例如：</p>
<ul><li>
<p>不论是用户还是物品数量都非常庞大，往往达到过亿级别，特征维度高达上亿维。处理这种高维数据时，TensorFlow需要提前将“特征ID化”，即强制将其映射到有限的tf.Variable空间中，这个过程会造成Hash冲突，即不同ID可能会取到相同Embedding，直接影响业务效果；</p>
</li>
<li>
<p>用户与物品的增删非常频繁，导致高维特征的某个维度需要频繁地动态增删，而基于连续存储的Variable所实现的静态Embedding不能真正释放某一段内存，只能置0，既不灵活也浪费内存资源；</p>
</li>
<li>
<p>稀疏模型达到TB量级时，为了保证线上推理效率，通常需要对模型进行裁剪、降低大小，但原生TensorFlow的连续存储方式无法做到删除特定维度，这导致模型过大无法高效存储和加载，实用性受到限制。</p>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/f6cd388e3af9300d86d9.png"/></p>
<p>针对原生TensorFlow在高维稀疏数据场景的上述不足，云帆OTeam融合了各业务团队的一线实战经验，基于稀疏域隔离方案推出了动态Embedding机制，并针对稀疏场景进行了优化器（SparseAdam）的深度定制。</p>
<div>
<div>
<h2>3.1 动态Embedding</h2>
<div>
<div>
<p>动态Embedding机制基于HashTable原理实现，并使HashTable在TensorFlow中可训练（Trainable），该方案<strong>没有hash冲突，效果更好，内存动态伸缩，单机也能调高维模型</strong>，并与原生TensorFlow所有重要机制兼容，可在特征无Hash冲突的训练条件下，以经济的方式使用内存资源，从而实现超大规模特征的离线训练和模型上线，其原理如下图所示，详细方案见[1]。</p>
</div>
</div>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e07f95a160dc8632fc13.png"/></p>
<p>与原生TensorFlow的静态Embedding相比，动态Embedding的典型使用方式如下:</p>
<div>
<pre>import tensorflow as tf
import tensorflow.dynamic_embedding as de

# graph defination
x, labels = dataset
w = de.get_variable(name="dynamic_embeddings",
                    devices=[
                        "/job:ps/replica:0/task:0/CPU:0",
                        "/job:ps/replica:0/task:1/CPU:0"
                    ],
                    initializer=tf.random_normal_initializer(0, 0.005),
                    dim=1)
z = de.embedding_lookup(params=w, ids=x, name="wide-sparse-weights")

# graph defination
opt = tf.train.AdamOptimizer(0.001)
update = opt.minimize(loss)
saver = tf.train.Saver()

# training loop
with tf.Session() as sess:
  for _ in range(100):
    sess.run(update)
  saver.save(sess, './ckpt/ckpt')</pre>
</div>
<p>可以看到，TTF的动态Embedding的API与tf.nn.embedding_lookupAPI几乎一样：参数相同、行为相同、名称相同，同时很好的兼容了原生TensorFlow各种算子和重要机制，用户使用时不会增加学习成本，使算法模型开发周期大幅度下降：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/eeb420ade17b5188b831.png"/></p>
<p>TTensorflow动态Embedding组件在看点视频、看点图文、快报视频、快报图文、微信看一看在看、热点广场、视频号、浏览器UGC等业务场景中落地并取得了不错的效果，同时通过智能钛平台的TI-TensorFlow品牌向公司外部输出稀疏训练能力。下图是动态Embedding在两个典型模型上相对于原生TensorFlow的效果提升。</p>
<p>离线测试结果，Amazon数据集，DIN模型</p>
<div>
<div>
<div>
<div>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm/15c43750a7031200e1fd.png"/></p>
</div>
</div>
</div>
</div>
<p>某推荐业务，Wide&amp;Deep模型</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7719dae3325fec95ef05.png"/></p>
<p>详情参考：TTensorFlow动态稀疏训练用户手册</p>
</div>
</div>
<div>
<div>
<h2>3.2 稀疏优化器SparseAdam</h2>
<p>在模型训练时，优化器通常选择AdamOptimizer，迭代公式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/83908a77c449e23675f5.png"/></p>
<p>对于稀疏数据场景，某一个mini-batch往往只涉及极其少量的embedding参数的更新，但是AdamOptimizer作为momentum-based的优化器，每次都会全局更新动量和参数，非常低效且没有必要。因此，基于AdamOptimizer提出了LazyAdamOptimizer，每次只更新梯度不为0的embedding参数，如下式所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2dcc2666bce11e6acd76.png"/></p>
<p>LazyAdamOptimizer虽然可以解决样本稀疏问题，但是当一个样本更新时，其参数的衰减却是由全局step计算的，这非常不合理，会影响模型的收敛精度。云帆OTeam为了解决这个问题，设计了SparseAdamOptimizer（详情见[2]），如下式所示</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7c6355e170298f7c740a.png"/></p>
<p>SparseAdamOptimizer为每个参数记录了上一次更新到本次更新的步数，在做参数衰减更新时由c决定，其它步骤与LazyAdamOptimizer相同，这种衰减策略显得更为合理。</p>
<p>使用TTensorFlow，用户可以非常简便地使用SparseAdamOptimizer。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b5fcfd4c4524723245db.png"/></p>
<p>使用MLPerf的NCF模型评估SparseAdamOptimzer，结果如下。可见，在稀疏数据场景，SparseAdam相比于Adam、LazyAdam能提升模型精度。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/8423e812cced01be2e38.png"/></p>
</div>
</div>
<h1>四、LAMB优化器</h1>
<p>LAMB（Layer-wise Adaptive Moments optimizer for Batching training）优化器是由大脑的研究者于2019年提出的<a href="https://arxiv.org/abs/1904.00962v3">[6]</a>，NVIDIA在Tranformer等语言模型上有代码实现<a href="https://github.com/NVIDIA/DeepLearningExamples/blob/8a5808138648d2e008078a0601f7184511eed275/TensorFlow/LanguageModeling/Transformer-XL/tf/lamb.py#L62">[7]</a>，其作用在于模型在进行大批量训练时，不会造成精度损失。LAMB优化器是结合了Adam优化器和LARS优化器的特点，支持了自适应的逐元素更新（adaptive elementwise updating）和分层学习率（ layerwise adaptive learning rates）。</p>
<p>LAMB 是一款通用优化器，它适用于小批量和大批量，且除了学习率以外其他超参数均无需调整。在原始论文中，LAMB 可将 BERT 预训练的batch_size大小扩展到 64k/32k，达到与小批量同等的准确率，同时训练时间缩短到76分钟。</p>
<p>云帆TTensorflow支持了LAMB优化器，具体接口定义如下：</p>
<div>
<pre>tf.train.LAMBOptimizer(learning_rate=0.001, beta1=0.9, beta2=0.999, epsilon=1e-6, weight_decay=0., use_locking=False, name="LAMB")</pre>
</div>
<p>参数含义（其参数与Adam优化器各参数含义一致）：</p>
<ul><li>learning_rate：学习率，可以是张量或者浮点值</li>
<li>beta1：一阶矩估计的指数衰减率</li>
<li>beta2：二阶矩估计的指数衰减率</li>
<li>epsilon：一个非常小的数，防止除以零，维持数值稳定性</li>
<li>use_locking：如果True，要使用锁进行更新操作</li>
<li>name：优化器名称，默认为“LAMB”</li>
</ul><p>用户可在其训练代码中直接将优化器替换为LAMBOptimizer，使用方式与TensorFlow原生的各优化器相同。使用示例：</p>
<ul><li>定义输入与模型</li>
</ul><div>
<pre>loss = model(input)
</pre>
</div>
<ul><li> 定义优化器为LAMB，参数使用默认参数</li>
</ul><div>
<pre>opt = tf.train.LAMBOptimizer()</pre>
</div>
<ul><li> 反向计算与更新</li>
</ul><div>
<pre>train_op = opt.minimize(loss)
sess = tf.Session()
sess.run(train_op)</pre>
</div>
<ul><li> 对梯度做需要的处理，比如clip等</li>
</ul><div>
<pre>grads, _  = tf.clip_by_global_norm(gradients, clip_ratio)
train_op = opt.apply_gradients(zip(grads, var_list))
sess = tf.Session()
sess.run(train_op)</pre>
</div>
<h1>五、混合精度</h1>
<p>随着深度学习在实际业务中的深入应用，模型复杂度与业务数据量不断增长，导致模型的训练耗时越来越高，影响了线上业务的模型迭代速度。</p>
<p>针对实际业务场景中大模型与大数据量的特点，也随着硬件算力的不断提升，混合精度训练方案被提了出来。我们先简要回顾一下混合精度训练的发展历程。</p>
<p>2017年，NVIDIA发布了V100 GPU，推出了全新的Tensor Core硬件架构，在硬件层面支持4*4尺寸fp16的矩阵计算优化。    <img alt="" loading="lazy" src="/logbook/images/algorithm/a61ae916b09038f8831b.png"/></p>
<p>2018年，NVIDIA联合发表了学术文章，详细探讨了如何利用TensorCore实现混合精度训练机制提升大模型、大数据量的业务场景的训练速度。如下图所示，通过保存一份fp32的weight，以及一份fp32的累积梯度，在计算时使用fp16，因为训练样本量非常巨大，从而训练时可以大大节省存储并进行加速。</p>
<p>    <img alt="" loading="lazy" src="/logbook/images/algorithm/90f615b7bdc3da2c02d3.png"/></p>
<p>2019年，NVIDIA推出了自动混合精度方案（AMP，Automatic Mixed Precision training），移除了混合精度训练时需要的手动操作，简化了混合精度训练在实际模型中的使用。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/69f2cea937460696219b.png"/></p>
<p>原生TensorFlow自1.14版本以后，已经可以支持混合精度训练，可通过简单的开关进行控制使用。</p>
<p>然而，在优图的业务实践过程中，特别是微信支付人脸模型中，在FAR亿分之一标准下，单纯使用混合精度训练存在着明显的精度损失。虽然可以用混合精度训练中穿插全精度训练的方式来弥补精度，目前tensorflow不支持自动切换，需要用户手动停止训练，切换配置，再重新加载模型，极为不便，也不适合进行线上的长时间训练。</p>
<p>基于上述问题，云帆TTensorflow设计了一套能进行灵活的混合进度训练的框架，从而不需要手动对模型训练进行启停，同时也可以实现更好地协调精度和时间的训练策略。设计框架主要为下图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/3b15fdb5869cc46c942f.png"/></p>
<p>在python部分开放了实现自定义策略接口，并在c++部分对tensorflow源码进行了修改，增加了混合精度训练的运行时开关。具体实现细节可见[5]。</p>
<p>在上述机制设计下，我们设计了TTensorflow策略来进行灵活混合精度训练。该策略在training阶段采用混合精度计算的同时，检测学习率是否发生变化，若当前step的学习率改变，则在当前step后的hold_step内切换到全精度训练，hold_step后在采用混合精度训练。详情可见左下流程图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/668333ad8b5e9c469b2d.png"/></p>
<p>上方右图为使用TTensorflow策略在imagenet数据集上训练resnet50的loss曲线，可以明显的观察到在learning rate发生变化的时候进行了精度上的切换（蓝色区间是混合精度计算，橙色是全精度计算。横轴为迭代步，纵轴是Loss）。</p>
<p>通过灵活混合精度策略，我们成功解决了开启混合精度计算后，模型精度下降的问题。可以从下表中看出，使用TTensorflow策略进行灵活混合精度训练已基本和使用全精度训练持平，并广泛应用到了多个业务场景中，具体数据如下：</p>
<div>
<div>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm/b3270dbe9fe6065ddf2c.png"/></p>
</div>
</div>
<p>TTensorflow自适应混合精度使用示例：</p>
<div>
<pre>from tensorflow.python.training.experimental import mixed_precision_policy
# 用户调用一个policy，目前提供LossDescendingSpeedPolicy, 
# TimeSchedulePolicy和TimeAndLrSchedulePolicy。
# 或者可以根据提供的MixedPrecisionTrainingPolicy类自行创建。
policy = mixed_precision_policy.TimeSchedulePolicy(
        start_step=100, end_step=1000)
for _ in range(num_step):
    # policy判断当前的状态是否应该打开混合精度
    flag = policy.enable_mixed_precision(step, loss=loss, ...)
    # 利用RunOptions传递配置
    run_options = tf.RunOptions()
    run_options.experimental.enable_mixed_precision = flag
    sess.run(train_op, run_options=run_options)</pre>
</div>
<h1>六、TTensorflow安装方法</h1>
<p>云帆OTeam目前已经搭建好了一套完整的CI，是针对TTensorFlow开发新特性自动化测试流程（如下图所示）。流程主要包括：</p>
<ol><li>stage1:事件触发。插件监听相关Git事件，本CI监听Merge Request事件。当对应代码库的监听分支有MR事件发生时，触发流水线的执行</li>
<li>stage2:作业制作。该阶段由拉取Git、Bash、归档构件三个插件组成。将Git拉取的测试代码创建预合并分支，并打包</li>
<li>stage3:制作推送Docker镜像。该阶段由作业平台构件分发和脚本执行两个插件组成。通过构件分发可以将阶段2归档的文件分发到指定的目标机。在镜像内将新特性TTensorFlow编译安装文件，并安装在镜像内，并将镜像推送到镜像源</li>
<li>stage4:提交测试并反馈。通过机智客户端配置阶段3制作出的镜像，提交新特性测试任务到机智平台</li>
</ol><p><img alt="" loading="lazy" src="/logbook/images/algorithm/fabda2c005bf258718f3.png"/></p>
<p>针对发布新版本的TTensorflow，OTeam目前也有一套完整的生成TTensorFlow安装包，并制作适用于内网的TTensorFlow基础镜像制作流程（与上述测试流程相似）。用户可以直接使用pip安装TTensorflow，与原生TensorFlow类似。</p>
<ul><li>
<p>安装TTensorflow 1.15.2 -- CPU版本</p>
</li>
</ul><div>
<pre>pip uninstall tensorflow -y &amp;&amp; pip install ttensorflow==1.15.2 --upgrade --no-cache-dir -i [内部链接已移除] --extra-index-url [内部链接已移除]</pre>
</div>
<ul><li>安装TTensorflow 1.15.2 -- GPU版本 </li>
</ul><div>
<pre>pip uninstall tensorflow -y &amp;&amp; pip install ttensorflow==1.15.2 --upgrade --no-cache-dir -i [内部链接已移除] --extra-index-url [内部链接已移除]
</pre>
</div>
<ul><li> 安装TTensorflow 2.2.0 -- CPU版本</li>
</ul><div>
<pre>pip uninstall tensorflow -y &amp;&amp; pip install ttensorflow==2.2.0 --upgrade --no-cache-dir -i [内部链接已移除] --extra-index-url [内部链接已移除]</pre>
</div>
<ul><li>安装TTensorflow 2.2.0 -- GPU版本 </li>
</ul><div>
<pre>pip uninstall tensorflow-gpu -y &amp;&amp; pip install ttensorflow-gpu==2.2.0 --upgrade --no-cache-dir -i [内部链接已移除] --extra-index-url [内部链接已移除] </pre>
</div>
<h1>七、TTensorflow接入太极平台</h1>
<p>云帆TTensorflow组件已接入太极/机智机器学习平台，致力于打造面向公司统一的、高效的机器学习训练服务。</p>
<p>目前太极平台已经提供了TTensorflow的基础镜像，用户可以选择使用，无需配置环境，开箱即用，方便用户上手。</p>
<p>后续TTensorflow会与云帆Oteam的大规模并行训练组件Light一起，在太极平台提供方便易用的一站式训练服务，支持各类场景（例如监督学习、强化学习、推荐&amp;信息流）的深度学习任务，提供业界一流的加速能力。用户只需提供模型代码与数据集，无需关注底层加速细节，太极平台会处理各类异常情况，帮助用户稳定，高效的完成训练任务。</p>
<h1>八、TTensorflow上云</h1>
<p>云帆TTensorflow已经接入，帮助提升在AI领域的技术影响力，并为云上客户提供行业领先的AI技术方案，对外产品名为TI-Tensorflow。</p>
<p>用户使用接口：TI-ONE Studio图形界面、TI-Notebook、TI-SDK。TI-TensorFlow目前已支持了TI-SDK的使用，TI-ONE Studio和TI-Notebook的使用接口将随TI 2.0一同推出。</p>
<p>TI-SDK使用TI-TensorFlow的方式如下：</p>
<div>
<pre>tf_estimator = TensorFlow(role=role,
                          base_job_name='test',
                          train_instance_count=instance_count,
                          train_instance_type=instance_type,
                          py_version='py3',
                          framework_version='titf-1.15',
                          script_mode=True,
                          hyperparameters=code_parameters,
                          entry_point='start.sh',
                          source_dir='code',
                          train_max_run=48 * 60 * 60,
                          )</pre>
</div>
<p>TTensorflow上云离不开以下云帆OTeam的杰出贡献者，分别是：</p>
<ul><li>云帆·推荐SIG的 @hudsonrong 完善了动态稀疏特征相关的内容与工作</li>
<li>云帆·TCompiler SIG的 @hopezhou @xinanjiang @wenxizhu @pengmeng 完善了模型编译优化相关的内容与工作</li>
<li>云帆·TCompiler SIG的 @xinanjiang @boyyang @lambdafang 完善了自动化混合精度训练相关的内容和工作</li>
</ul><h1>九、总结与展望</h1>
<h2>9.1 云帆Oteam TTensorflow组件贡献者</h2>
<table><tbody><tr><td>
<p><strong>RTX</strong></p>
</td>
<td><strong>BG/部门 </strong></td>
</tr><tr><td>adnywang(王建东)</td>
<td>/Turing Lab</td>
</tr><tr><td>billpeng(彭彪)</td>
<td>/</td>
</tr><tr><td>boyyang(杨博)</td>
<td>/优图实验室</td>
</tr><tr><td>cathyxhuang(黄雪)</td>
<td>/</td>
</tr><tr><td>chenyangguo(郭晨阳)</td>
<td>/优图实验室</td>
</tr><tr><td>chuancheng(程川)</td>
<td>/推荐产品中心</td>
</tr><tr><td>captwang(王耀东)</td>
<td>/</td>
</tr><tr><td>fesun(孙飞)</td>
<td>/</td>
</tr><tr><td>hopezhou(周飞虎)</td>
<td>/</td>
</tr><tr><td>hudsonrong(戎海栋)</td>
<td>/推荐产品中心</td>
</tr><tr><td>jeffreypu(蒲俊峰)</td>
<td>/精准推荐中心</td>
</tr><tr><td>kimmyzhang(张亚霏)</td>
<td>/推荐产品中心</td>
</tr><tr><td>lambdafang(方杰)</td>
<td>/优图实验室</td>
</tr><tr><td>leapouyang(欧阳显斌)</td>
<td>/</td>
</tr><tr><td>nickeylin(林志恒)</td>
<td>
<p>/</p>
</td>
</tr><tr><td>pengmeng(孟鹏)</td>
<td>/</td>
</tr><tr><td>robertxiong(熊鹏飞)</td>
<td>/个性化推荐中心</td>
</tr><tr><td>ruibobchen(陈志博)</td>
<td>/优图实验室</td>
</tr><tr><td>slashwang(王洋子豪)</td>
<td>/</td>
</tr><tr><td>weilianglin(林卫亮)</td>
<td>/</td>
</tr><tr><td>whiskywang(王自昊)</td>
<td>/个性化推荐中心</td>
</tr><tr><td>yonglinfu(符泳淋)</td>
<td>/个性化推荐中心</td>
</tr><tr><td>xinanjiang(姜曦楠)</td>
<td>/</td>
</tr><tr><td>zilinzhu(朱子霖)</td>
<td>/</td>
</tr></tbody></table><h2>9.2 后续规划</h2>
<p>云帆TTensorflow汇聚了公司内各技术团队，致力于打造公司内统一的、易用的、具备技术领先性的深度学习框架。在以上技术创新与优化上，云帆TTensorflow会进一步钻研技术深度，满足用户定制化需求，更好的服务和接入业务，拓展在深度学习框架的技术影响力。</p>
<p>后续TTensorflow会与太极/机智机器学习平台深入协作，为公司内用户提供一站式的深度学习框架加速方案，提高易用性，降低上手门槛，助力更多业务取得成功；此外，由云帆Oteam主导创新的采样指导优化（PGO：Profile Guided Optimizations）将会于TTensorflow下一个版本上线，该方案通过Session运行时收集采样动态信息，并结合静态信息分析计算图特征，指导图优化，进一步加速训练进程。同时，云帆TTensorflow的编译优化可视化分析工具也在开发中，该工具可以通过页面直观展示各模块性能，例如Op耗时饼状图、显存分析、硬件性能分析等，自动生成性能报告及优化建议，帮助算法工程师快速定位性能问题。</p>
<h2>9.3 如何加入</h2>
<p>云帆TTensorflow是云帆Oteam的重要组件之一，协同团队已经搭建好一套完整高效的开发流程，并有周期性内部交流分享会，营造了良好的技术氛围。欢迎对深度学习框架感兴趣的同学一起共建TTensorflow，共同打造业界一流的深度学习框架。</p>
<p>云帆各组件最近进展均会同步至云帆Oteam主页：[内部或本地链接已移除]。</p>
<p>欢迎咨询企业微信咨询<strong>yunfan_helper(云帆深度学习框架与加速)</strong>，了解更多协同与业务接入信息。</p>
<h1>十、参考文献</h1>
<ol><li><a href="https://github.com/tensorflow/community/pull/237">RFC: Sparse Domain Isolation for Supporting large-scale Sparse Weights Training.</a></li>
<li>SparseAdam: Adam在稀疏数据上的优化实现</li>
<li>基于TensorFlow的Wide&amp;Deep模型推理优化</li>
<li>首个TensorFlow开源贡献-改进TensorFlow DiagPart Op的XLA实现</li>
<li>自适应混合精度设计</li>
<li><a href="https://arxiv.org/abs/1904.00962v3">Large Batch Optimization for Deep Learning: Training BERT in 76 minutes</a></li>
<li><a href="https://github.com/NVIDIA/DeepLearningExamples/blob/8a5808138648d2e008078a0601f7184511eed275/TensorFlow/LanguageModeling/Transformer-XL/tf/lamb.py#L62">NVIDIA：LAMB Optimizer Examples</a></li>
</ol><h1><strong><a href="https://github.com/NVIDIA/DeepLearningExamples"></a></strong></h1> 
{% endraw %}
