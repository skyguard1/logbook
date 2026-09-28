---
title: "推荐系统中的Auto Embedding Size算法"
date: 2022-03-23 16:44:16
categories:
  - 算法
  - 特征工程
---

{% raw %}

<h2><strong>0. 引言</strong></h2>
<p>推荐系统的输入特征具有稀疏性、分布差异大的特性，这两个特性决定了AES工作的意义。其中“稀疏性”理解为特征id经过hash化后，往往只占据完整hash表的一部分。比如文章的category，一般是百级别到千级别的，为了避免冲突，我们一般设定hash表的大小是category数量的数倍，这样就会存在着大量没有使用到的表元素。进一步的，对hash表中的元素建立embedding table，也会存在着大量embedding没有被使用。因此，embedding占据了推荐模型中的大部分参数量。而“分布差异大”则表现为，不同field的特征数量往往差别很大，比如对于“性别”只有3个值，而user ID的量级可能是数以亿计。因此，不同的features所携带的信息也是各异的。特别的，对于一些低频的特征，不仅应该设定更小的embedding size，甚至还可能要将其过滤掉以避免出现过拟合；而对于一些高频的特征，不仅本身携带较大的信息量，和其他特征也会有更大的“共现”机会（“共现”的特性可以用来建模交叉特征，这里不做展开讲），因此应该设定更大的embedding size。</p>
<p>有效、合理地分配emedding size，不仅可以提高计算、存储的效率，而且对于算法性能的提升有大有裨益。但是，手工设定embedding size是一项非常繁冗的工作，涉及到“组合爆炸”的问题，因此一般是将tuning embedding size的工作交由机器学习算法完成，在下面的章节中，我们将介绍 一些比较知名的AES算法，并且将这些方法归纳为4大类：</p>
<ul><li>启发式方法：根据feature的统计信息，通过一定的规则/数值计算设定embedding size</li>
<li>Natural Architecture Search (NAS)：即建模为网络结构搜索问题，使用强化算法、演化算法等求解。</li>
<li>Diffenrential Architecture Search (DARTS)：建立若干的candidates，使用weighting的方式来选择。</li>
<li>Pruning Method：使用剪枝的方式。</li>
</ul><p>在介绍具体算法前，我们先捋清一些定义（notification）：</p>
<ul><li>feature id：实际上就是feature instance，一般是用离散化的ID来表示。该ID会通过hash映射到hash table中的index值，比如tf中的feature column工具包就提供了这样的功能。</li>
<li>feature field: 特征域，比如“年龄”，“性别”等，一个field包含多个feature id</li>
<li>embedding table: 为每个feature id分配的embedding的集合，一般是用dense tensor实现，因此其大小取决于hash table的大小，通常比feature id的数量大。</li>
<li>embedding size：可以为每一个feature id设定（或者将若干个feature id组成block），也可以为每一个field设定，甚至可以分别为user/item设定。不同的细粒度对应着不同的搜索复杂度。</li>
</ul><h2><strong>1. 启发式方法</strong></h2>
<p>MixedEmb [1] 提出了一种启发式算法，该文章认为embedding size与feature的出现频率（frequency）成正比，即frequency越大的feature应该被赋予更大的embedding size，该方法总结为如下三步：</p>
<ul><li>统计feature的频率frequency，并且按照从高到底进行排序，按一定规则组成k个block。</li>
<li>将frequency进行归一化，转化为probability，方法是frequency / sum(frequency)。probability的维度是k+1。</li>
<li>设定baseline维度bar_d，计算缩放比例lambda，然后为每个block计算embedding size，如下（alpha一般取2就可以）：</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/09d7d7f5b70f1ea2f02e.png"/></p>
<ul><li>最后每个block E_i内的特征共享embedding size d_i。</li>
</ul><p>MixedEmb有开源的代码实现：<a href="https://github.com/facebookresearch/dlrm">https://github.com/facebookresearch/dlrm</a></p>
<h2><strong>2. NAS方法</strong></h2>
<p>NAS的方法可以归结为"trial and error"，即搜索一组网络参数，训练该模型，然后在验证集上测试，获得评测指标，再决定下一轮的搜索方向……因此是一种比较耗时的方法。</p>
<p><strong>NIS [2]</strong> 使用了强化学习方法来解决AES问题，其定义了两种状态空间:</p>
<ul><li>Single-Size Embedding(SE): 一个field下所有features都使用同样的embedding size</li>
<li>Multi-Size Embedding(ME)：将一个field下的feature IDs划分成若干个group，每个block内的features共享embedding size</li>
</ul><p>SE和ME的思想可以用下图的(a)，(b)来表示。首先对于某一个field，对features按照frequency进行排序，并且编号；同时，以64维为基本单元，最终分配的embedding size由若干个64维组成，这样可以构成大小为SxT的embedding block。比如，在图(a)中，前7M的features使用embedding size=192，后3M的features被过滤掉(embedding size=0)；在(b)中，前3M的feature使用size=64x3=192，后7M的feature使用size=64。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/57b2348c8820f3a02abb.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/7a308c6e467e4febd1da.png"/></p>
<p>现在可以定义policy network，它的作用是在每个training step为一个field的features选择embedding size（<strong>注意，一个step只操作一个field!</strong>）。SE和ME的情况有所不同：对于SE，在每个step，policy network只需要做一次选择，相当于(a)中的红框，因此对于每个field，其策略空间大小为(SxT+1)，1为(0,0)的选择，即不为该field分配embedding size；而对于ME，每个step下需要做T次选择，如图(b)所示，其中第3次选择了（0，0）。这样对于每个field，其策略空间大小为(S^T+1)。</p>
<p>NIS的reward由两部分组成，分别是常规的评价指标，如auc等，定义为R_Q；还有memory cost，定义为C_M，其中C_F是指field F所消耗的memory，而B是总的budget。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2a462a3442804c0a1323.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/d676a776d58ff61bd2be.png"/></p>
<p><strong>RULE [3]</strong> 使用了进化算法来求解AES。其解决的问题是要将model的memory cost限制在给定的budge内，因此属于硬约束问题。对于此类问题，强化学习算法是不足以应付的，一般只能用组合优化的方式来求解，而进化算法则是一个很好的选择。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/d0ac7ae5b57049ca7e37.png"/></p>
<p>上图是RULE算法对block的定义，和NIS中ME的定义大同小异，不过这里的"groups"不是为每个field设定的，而是对所有的features进行统一的grouping。每个group内的embedding size是一致的，由<strong>N</strong>个size为d的embedding block组成(定义为E_g(n)，n的取值范围是<strong>1到N</strong>)。这样一共构成了G个groups，每个group定义为B_g。</p>
<p>进化算法的核心元素是种群，即一些可行解的集合。首先简述一下初始种群的构造方法：</p>
<ul><li>对G个group，分别以高斯分布采样embedding blocks组成embedding（size为(1~N)*d）。</li>
<li>这样得到的总memory cost可能超出budget，因此需要剪枝，方法是轮询每一个group，随机删掉embedding block</li>
<li>这样得到了可行的embedding size分配方案（种群成员），通过estimator计算该成员的performance，并且加入种群中</li>
<li>以上三步重复若干次，即可得到一个初始种群。</li>
</ul><p>接下来是要对种群进行演进（每个training step都要做一次），具体来说就是从种群中选出当前最优秀的成员作为parent，然后对其进行变异：1. 不同group的embedding分配方案进行交换；2. 对于某一个group，随机选择相同数量的block（比如原来选择index是1，2，现在改为2，3，注意每一个embedding block的representation是不一样的），获得child。对child通过estimiator计算其performance，将child加入到种群中，并且淘汰掉performance最差的成员。重复此步骤C轮，选出最好的candidate。</p>
<p>这里的estimator是一个轻量级的模型，以performance如auc等为目标训练得到。使用estimator可以简化获得performance的过程，避免要过一遍validation set，是一种比较popular的方法，当然也会损失一定的精度。</p>
<p>每个training step，选出最好的candidate后，需要对模型进行优化（优化目标包括所有的embedding block的参数以及其余模型参数），优化目标选择BPR loss。这里的E_n是对Figure1 中的embedding block按列拼接，比如E_1是第一列embedding block的集合。下面式子中最后一部分正则化项，实际是促使不同列的embedding block要有所差异。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/300dbf73985962852b87.png"/></p>
<p>这样，经过若干个training step后，最佳的embedding size分配方案也就呼之而出，并且也严格限制在给定的budget中。</p>
<p><strong>ESAPN [4] </strong>解决的是在<strong>streaming setting（即online learning）</strong>下的AES问题，使用的也是强化学习方法。不过ESAPN只分别为user和item各设定embedding size，搜索空间比较小。</p>
<p>ESAPN的overview如下图所示。具体而言，就是在第k时刻，收集到关于user/item的log信息，然后对policy network进行更新，实际上就是在动态调整embedding size，然后把新的embedding size 配置传给recommender。recommender更新更新网络结构参数，返回reward给policy network。周而复始，使得policy network的方案最优。</p>
<h2><strong><img alt="" loading="lazy" src="/logbook/images/algorithm/0c211672514d8ae66825.png"/></strong></h2>
<p>ESAPN定义的policy只有两种：unchanged和enlarge (<strong>这样embedding size不就往单调递增的方向发展了？论文没有去提及这个问题</strong>)。为了节省内存，模型并不是把所有size的embedding都分别保存一份，而是在他们之间建立线性映射关系。具体而言，size=8的embedding通过8x16的权重矩阵W投影到size=16，以此类推，建立“多米诺骨牌”式的embedding之间的联系：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/8fe15ea07cdff4b0aee7.png"/></p>
<p>因此，当user和item的embedding size不一致时，可以统一投影到e_n，然后再forward到其他网络层。</p>
<p>当policy network做出“enlarge”的决定时，新的embedding由原embedding通过投影得到，因此可以获得比较好的初始值。</p>
<p>ESAPN定义的reward为当前的loss与历史T次平均loss的“增益”：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/d87cb975f180e671c630.png"/></p>
<p>ESAPN算法的代码已开源：<a href="https://github.com/zgahhblhc/E">https://github.com/zgahhblhc/ESAPN</a></p>
<h2><strong>3. DARTS方法</strong></h2>
<p>与NAS方法不同，DARTS将AES问题与传统的ctr优化问题融合起来，建立了双层优化问题：下层优化问题选择最佳的embedding size，上层优化则完成对网络参数的优化：<br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/1de7c96d671b8cdd0e38.png"/></p>
<p>这里的alpha充当weights的作用，用来从多个candidate中选择embedding size。其优化步骤分为两步</p>
<p>1. 使用训练集优化W</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/951cf573a9002bdb4448.png"/></p>
<p>2. 使用验证集优化alpha</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4ed6626935b7ea312298.png"/></p>
<p>step1 和 step2 交替进行，直至最终收敛。DARTS相当于是可导的NAS方法。</p>
<p>注意，在实际应用中，W和alpha的更新都是one-step的（也就是<strong>在一个batch数据上更新</strong>而非整个数据集），这样效率比较高。</p>
<p>下面介绍几种以DARTS为基础的AES算法。</p>
<p><strong>AutoDim [5] </strong>为不同的feature field设定embedding size。首先定义candidate embedding size，比如4，8，16。每个candidate size对应一个candidate embedding，然后设计可训练的权重alpha来为每个field选择candidate embedding，以此来达到AES的目的。整体framework如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/8e6f6d8f0e1b9d9e35e0.png"/></p>
<p>以field m为例，假定有N个candidate，则alpha_m的维度是N，通过top-1的alpha_m可以选出confidence最大的candidate，但是这样的选择是不可导的，不能直接用于DARTS的框架下。常用gumbel-softmax来近似代替离散采样，如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/414c08db9ecf40978413.png"/></p>
<p>但是argmax仍然是一个不可导的操作，因此选择使用softmax来近似：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/331423e47552f7ceff5f.png"/></p>
<p>最终的embedding为使用p_m^n为权重对N个candidate进行加权。虽然这里N个candidate的size不一致，但是论文使用两种方式将其映射到同一个维度(统一的embedding size对于feature interaction来说是必须的)：zero-padding或者linear transform。为了避免transform后的embedding的magnitude差异过大，论文使用了BatchNormalization来进行归一化：</p>
<p><br/></p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm/89197468f1e78b722917.png"/></strong></p>
<p>在训练中使用p_m^n来对hat(x)_m^n进行soft selection：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/1baa83898de880aef6ce.png"/></p>
<p>完成训练后，就可以根据alpha推断出最优的embedding size方案，即soft selection -&gt; hard selection，因此p就不需要再使用了。这样可以获得一个模型，每个field都只有一个确定size的embedding，对这个模型进行retrain就可以得到最优模型。</p>
<p><strong>DNIS [6] </strong>提出了一种不一样的方案，不需要设定N个candidate，而是为所有的features设定最大的embedding size K，DNIS需要做的是从中选出有效的components。具体而言，先把features按frequence排序，分成L个block，因此全体的embedding的size为LxK（block内的features共享size），相应的，权重alpha（trainable）的size也是LxK。</p>
<p>对于第L个block的features，经过加权后的embedding tilde(e)计算如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/92786560d69cad90eaf5.png"/></p>
<p>将tilde(e)传给后面的网络层，即可搭建常规的ctr模型，然后基于DARTS的思想通过交替训练从而获得最优的alpha。在训练中，为了避免alpha的gradient的variance过大，论文对gradient进行的normalize，如下：<br/><img alt="" loading="lazy" src="/logbook/images/algorithm/281014a0c8706cd7a670.png"/></p>
<p>在得到alpha后，基于tilde(e)的magnitude进行裁剪：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/de371101a91b6d4ebf8c.png"/></p>
<p>可以将DNIS理解为DARTS和pruning方法的结合体。。。</p>
<p><strong>AutoEmb [7] </strong>也是DARTS方法，目标是为user/item分别设定最优的embeding size，并且适用于<strong>streaming recommendation</strong>中。结构如下：<br/></p>
<h2><strong><img alt="" loading="lazy" src="/logbook/images/algorithm/84e7598c4a1294b01570.png"/></strong></h2>
<p>不过这里的alpha，beta并不是简单的可训练参数，而是由controller产生。controller的输入是user/item当前的popularity和contextual information，中间网络层是多个FC layers。</p>
<p>在训练/serving过程中使用的是soft selection，即user/item的embedding是N个candidate embedding的加权和</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/3c6792f8d880f179fed3.png"/></p>
<p>上式中hat(e)对应图中的"Transformed Embeddings"，是对原candidate embedding e进行线性投影，并且通过normalization得到。这是为了使得对于所有的candidate，hat(e)都具有相同的size。<br/><img alt="" loading="lazy" src="/logbook/images/algorithm/73026192a028fe1aa508.png"/></p>
<p>训练的流程如下，注意是在streaming data下进行的，没有pre-split的train、val和test set：</p>
<ul><li>从历史的user-item interactions中sample一部分，定义为validation set。在该set上更新controller；</li>
<li>收集一部分实时的训练数据，并且根据实时的popularity以及contextual information，利用controller求取alpha和beta；</li>
<li>根据alpha，beta构建模型，然后执行常规的ctr模型训练，更新模型参数W；</li>
<li>重复以上步骤直至收敛。</li>
</ul><h2><strong>4. Pruning方法</strong></h2>
<p>与DARTS的双层优化策略不同，<strong>PEP [8] </strong>提出了一种更加直接的优化方法。具体而言，PEP 先为所有的features设定一个最大的embedding size，构造出一个overloaded的embedding table。通过ctr等任务对embedding table进行训练，最后过滤掉那些峰值低于给定阈值的embedding elements，从而完成embedding size分配。</p>
<p>PEP的思想可以理解为约束embedding table的稀疏性，即L0范数约束：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/6778e4934f9211fe0fca.png"/></p>
<p>但是L0范数约束问题是一个高度不可微的优化问题，需要进行松弛。PEP使用了符号函数sign和激活函数RELU来近似：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/778edeb0af21c1804d72.png"/></p>
<p>其中g(s)是以s为输入参数的阈值网络，也就是说PEP中的阈值是自动调整的。而hat(V)是V的稀疏化版本，会被feed到后续的网络层中。</p>
<p>由此可见，PEP将对embedding table V的稀疏性约束融入到ctr模型的训练中，因此不需要像DARTS那样执行alternative training，效率更高。而且其过滤阈值可以自动调整，免除了用户要小心设定阈值的麻烦和风险。注意在hat(V)的公式中，loss function对V并不是处处可导（当V=0时不可导）的，因此使用次梯度法来更新V：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/779e865f263c95165a9f.png"/></p>
<p>g(s)可以是为每个features单独设定，也可以为field单独设定，也可以全局设定。</p>
<p>文中recall了一下彩票假设（Lottery Ticket Hypothesis, LTH），即一个base模型存在一个子模型，其performance优于base模型；如果子模型warm up了base模型的参数，则其performance可以得到进一步的boosted。论文中的实验也佐证了这一点：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/77baca01e59972ddbcec.png"/></p>
<p>PEP算法的官方代码实现：<a href="https://github.com/ssui-liu/learnable-embed-sizes-for-RecSys">https://github.com/ssui-liu/learnable-embed-sizes-for-RecSys</a><a href="https://github.com/ssui-liu/learnable-embed-sizes-f"></a></p>
<p><br/></p>
<p><strong>ATML [9] </strong>也是一种类似于pruning的方法，只不过是一种结构化的pruning方法。与PEP不同的是，ATML假设disinformative的embedding elements都会分布在完整embedding的后半段。因此算法的目的是要计算出断点breaking point，然后为每个feature取breaking point前的embedding即可。算法的架构图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/599e861cd10bcdf1c7f0.png"/></p>
<p>ATML算法的一个特点是它设计了两个AML（adaptively-masked layer），分别是encode高频特征(h-AML)和低频特征(I-AML)。由特征的frequency value转化而成的weight score将自动地对h-AML即I-AML进行加权，并最终产生每个element的分数。选取最大element分数所在的位置作为breaking point：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/83826b1012e997ffe4fe.png"/></p>
<p>但是t_i的计算是不可导的，因此需要进行近似，作者采用了带温度加权的softmax函数：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/6b45cf2e8cbd66386440.png"/></p>
<p>在训练过程中，使用hat(t)来传递梯度；而在最终inference时，直接使用t来生成不同size的embedding即可。在论文中作者使用了一个trick，保证两个过程是无缝结合的：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/52641a69358e34fd76b7.png"/></p>
<p>在实验结论中，作者也验证了LTH的正确性（Warm Start即加载base model的参数）：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f5a21d4476cfb131babd.png"/></p>
<p><strong>COLD [10] </strong>使用了SE(Squeeze-and-Excitation) block来剪枝，去除那些不重要的feature fields。<strong>严格来讲COLD并不是用于解决AES问题</strong>，但是该文章对于提高模型效率等有深入探讨，使用于对耗时要求高的粗排场景，因此这里也介绍一下。COLD的网络结构设计如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/fc105c006f091f893f2d.png"/></p>
<p>SE Block的实现很简单，由少量几层全连接层组成，输出是各个field的分数：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e298b7f86009980011a9.png"/></p>
<p>对分数进行排序，按照memory cost约束，并且在满足一定的performance质量的前提下，选出top-K个field。</p>
<h2><strong>5. 小结</strong></h2>
<p>本文回顾了业界有关auto embedding size (AES)的一些解决方法，从最早的启发式算法，到NAS，DARTS以及pruning的方法，应该说AES的问题得到了学术界的充分重视。这些方法涵盖了强化学习、演化算法、双层优化等技术，基本都与具体模型无关，具有普适性和通用性。</p>
<p>大部分AES算法是针对静态场景的，也就是算法只执行一次，然后所得到的模型就一直在线上迭代更新；当然也有关于streaming data pipeline场景的，只是可能需要一些trick来处理对大量candidate的存储问题（比如使用投影矩阵来建立不同size的embedding间的关联），或者干脆将问题的规模缩小（只对user/item的size分别作统一调整）。另外在一些特定的场景中，比如在移动端部署时，需要满足strict memory constraint……AES还有许多的应用场景可以挖掘，我们也期待能看到更多的成果，并且最终反哺到具体业务中。</p>
<p>总的来说，AES对于提高计算效率、节省内存消耗等具有重要意义，因此是学术研究和业务应用的一个很好的结合点。</p>
<p>在另外一篇文章中，我将介绍AutoML在另一个场景的应用：Auto Feature Interaction，欢迎大家前去探讨！文章链接地址：[内部或本地链接已移除]</p>
<h2><strong>6. 参考文献</strong></h2>
<div>
<div>
<div>
<p>[1] Mixed Dimension Embeddings with Application to Memory-Efficient Recommendation Systems</p>
<p>[2] Neural Input Search For Large Scale Recommendation Models</p>
<p>[3] Learning Elastic Embeddings for Customized On-Device Recommenders</p>
<p>[4] Automated Embedding Size Search in Deep Recommendation Systems</p>
<p>[5] Memory-efficient Embedding for Recommendations</p>
<p>[6] Differentiable Neural Input Search for Recommender Systems</p>
<p>[7] AutoEmb: Automated Embedding Dimensionality Search in Streaming Recommendations</p>
<p>[8] Learnable Embedding Sizes for Recommender Systems</p>
<p>[9] Learning Effiective and Efficient Embedding via an Adaptively-Masked Twins-based Layer</p>
<p>[10] Computing power cost-aware Online and Lightweight Deep pre-ranking system</p>
<div>
<div>
<div>
<p><br/></p>
</div>
</div>
</div>
</div>
</div>
</div> 
{% endraw %}
