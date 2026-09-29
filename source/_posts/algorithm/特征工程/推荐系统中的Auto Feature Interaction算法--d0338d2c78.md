---
title: "推荐系统中的Auto Feature Interaction算法"
date: 2022-03-23 16:43:45
categories:
  - 算法
  - 特征工程
---

{% raw %}

<h2>一、Feature Interaction的经典算法</h2>
<p>在介绍Auto Feature Interaction(AFI)前，我们先介绍一下推荐系统中的feature interaction方案。概括来讲，以进行interaction的feature数量为“阶”，feature interaction可以分为二阶（如factor matchine即FM）和高阶方案（如XdeepFM, InterHAT）。</p>
<h3>1.1 二阶特征交叉方案</h3>
<p>FM [1]是最经典的feature interaction了，其对两两特征vi和vj求内积，此外还有线性项和偏置项：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/56a5bf8f200511492a2a.png"/></p>
<p>在订阅号业务实践中，我们尝试将“内积”换成“hadamard积”，效果可以进一步提升。所谓向量间的hadamard积是指element-wise的乘积，得到的交叉特征与输入特征同维度。</p>
<p>为了更好地建模feature interaction，OPNN [2] 使用了向量外积，每对特征进行interaction后生成一个MxM的矩阵，M是输入特征的维度。实际上，OPPN可以允许进行交叉的embedding的维度不一致，这是FM做不到的：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2fc362f85fd04ac9743c.png"/></p>
<p>FM假定所有的交叉项具有相同的权重，因此简单地进行了reduce sum。而AFM [3]提出使用attention机制来对这些交叉项进行加权，具体公式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b631fa76e0485725f86f.png"/></p>
<p>关注其中的a_{ij}，是通过attention机制求得。这里W、b以及h都是共享参数，用于生成attention scores：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/c8157afc07e44ecdc6ba.png"/></p>
<p>类似的attention方案还有AutoInt [4]等，这里不展开讲。与之不同的是，FmFM [5]提出，只用一个标量值来衡量interaction的重要性是不够的，同一个feature，与不同的feature进行交叉时其特性应该是不一致的，或者说应该处在不同的几何空间中，以最大化信息熵。因此FmFM使用矩阵对进行的pair对进行空间变换，从而提取到更有意义的交叉特征表达：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/17fe34d3c0d4b3709237.png"/></p>
<p>其中M_{F(i)F(j)}是为所有pair对定制的转换矩阵。FmFM引入的额外参数量是比较小的，我们在线上验证的效果也比DeepFM好。但是由于pair间引入了转换矩阵，无法进行并行计算，因而计算复杂度较高。</p>
<h3>1.2 高阶特征交叉方案</h3>
<p>最暴力的高阶交叉方案自然是枚举了，以3阶为例，一共会有m^3对triplets：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b22c74e8675f6153ece5.png"/></p>
<p>可以看到，随着阶数的增加，计算复杂度也呈指数级上升，因此这种brute-force的方式是不实际的。更多的方法是“堆叠式”的，即“1+2=3”，"1+3=4"这样：在k-1层得到k-1阶feature interaction，与第一层（输入层）进行交叉得到k阶特征。</p>
<p>XDeepFM [6] 使用CIN来构建(k-1)阶特征与k阶特征的关系，CIN的网络结构图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/bf11d6e0008995063ee0.png"/></p>
<p>数学表达式如下，其中H_{k-1}是第(k-1)阶交叉特征的“数量”。以FM为例，二阶交叉特征的数量是m*(m-1)/2；而XDeepFm则是可以自定义的，这是因为它的交叉方式也不同。具体而言，XDeepFM先计算pair(i, j)的hadamard积，得到一个D维向量，并且使用H_k个(D x D)的矩阵W进行线性变换，得到H_k组D维向量；对H_{k-1}*m对pair对执行这样的操作，并且在pair对的维度进行求和，最后可以得到H_k * D的向量。注意H_k即是第k阶交叉特征的数量。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/cb797e7a7791f485f544.png"/></p>
<p>在获得所有的K阶交叉特征后，在进行一次sum pooling得到最后的交叉特征表达。原文是对D维度（embedding size维度）进行sum，因此输出的特征向量维度是H_1 + ... + H_{K}。而我们在实验中发现，对H_k维度进行求和效果更好，这样输出的特征向量维度是D维，和DeepFM一致。</p>
<p>InterHAT [7]使用异构的attention来建模(k-1)阶交叉特征与k阶交叉特征的关系，模型图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4f8eb9b8430c26a47605.png"/></p>
<p>其中α_k可以用来观测各阶特征交叉贡献的权重（同时这也是通过attention得到的分数），因此InterHAT是“可解释性”的，这里不做延伸讨论。先看一下α_k的计算：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/5780e507df6816edffbf.png"/></p>
<p>这里的x_i^{(j)}即是第(k-1)层的交叉特征，维度是d，而c_i，W_i都是共享的。通过α_k对(k-1)阶特征进行加权，得到了(k-1)阶特征交叉的“浓缩表达” -- u_i，它是一个d维的向量：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e3200c254b4cdd862d49.png"/></p>
<p>最后将u_i与一阶特征（输入特征）求hadamard积，即可得到k阶交叉特征：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/3257eb544d11e77fd6d9.png"/></p>
<p>在得到所有m阶交叉特征后，再进行一次attention求和，最终输出向量的维度是d，与FM的输出维度一致。</p>
<p>AFN [8]提出使用log变换，将向量间的交叉（hadamard积）转化为log(向量)求和，并且通过可学习的权重W来自动选择交叉的阶数。模型结构图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f3b970d4884c2ef4ee54.png"/></p>
<p>其中Logarithmic Transformation Layer是核心组件，可以用一条公式来表示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/0ecb0622d5cd30068033.png"/></p>
<p>假设w_{1j}=w_{2j}=1，其余w为0，则y_j是feature #1与feature #2的二阶交叉。设计多组的w，即可表示融合不同阶的交叉特征。实现的具体过程如下：</p>
<ul><li>对输入的embedding（维度m x k）求Abs，使得所有元素都为正数</li>
<li>对embedding矩阵求log(.)，维度依旧是m x k，将其转置得到k x m维矩阵</li>
<li>构造可学习的权重矩阵W，维度是m x H，H是你所期望的高阶特征组合数目（即由多少组不同的高阶特征组合）。将embedding与W相乘，得到k x H矩阵</li>
<li>对k x H矩阵求exp(.)，最后对H维度求和，得到k维向量，即为最终的交叉特征表达</li>
</ul><h2>二、Auto Feature Interaction (AFI)工作的意义</h2>
<p>上面介绍的二阶、高阶feature interaction方法都是假定所有的feature interaction均有意义，并最终参与到ctr预测任务中。而更多的学术研究表明，一些性质差异大甚至互斥的feature interaction将会带来额外的噪声，降低模型效果，因此对feature interaction必须加以甄别使用。虽然如AFM，AutoInt这样的attention机制可以对那些信息量小的feature interaction进行降权，但很难保证是“完全切除”，而这便是AFI工作的重点：<strong>仅保留那些比较有意义的feature interaction</strong>。</p>
<p>AFI问题的搜索空间往往与特征交叉的阶数有关：主流的feature interaction都是field间进行的，以n阶交叉为例，假设一共有m个field，则feature interaction的数量级是O(m^n)。在我们的文献调研工作中，大多数AFI算法是针对2阶特征交叉进行的；针对高阶特征交叉的指数爆炸问题，可以通过近似的方式来降低搜索空间复杂度。</p>
<p>我们将在接下来的章节详细介绍这些算法。</p>
<h2>三、AFI相关算法介绍</h2>
<h3>3.1 AutoFIS算法</h3>
<p>AutoFIS [9] 使用门控机制（参数alpha）来对feature interaction进行筛选，原理图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f62bbea01763d2f3a126.png"/></p>
<p>这里的α_{(i,j)}应当是一个binary值，但是这样设定后loss对α就不可导了，因此参考DARTS，将α松弛为连续的自然数。加入门控机制后的特征表达式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/15eaa4124c33e0c7e8bd.png"/></p>
<p>AutoFIS提到，由于不同的feature进行interaction时得到的输出特征的量级是不一致的，会导致α无法发挥“重要性衡量”这一作用（即α越大该交叉特征越重要）。因此在进入selection gate之前，需要先进行归一化(batch normalization)：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e54aa599d8aff4b501ee.png"/></p>
<p>DARTS是将α的优化和网络参数W的优化建模为双层优化问题，并且在小batch的train/test集上使用“交替优化”的方式，AutoFIS认为这样可能会导致优化过程不稳定。与之不同的是，AutoFIS直接将α和W一起优化（在同一个batch训练数据上，文中将其成为"one-shot optimization"），其梯度计算方式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4257c7d9a41111ceaa5f.png"/></p>
<p>最后的问题是，如何保证alpha的稀疏度呢？AutoFIS使用了Generalized regularized dual averaging optimizer (GRDA优化器) 来优化alpha，这是在稀疏学习中常用的优化器，梯度表达式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b7d296bff47752c79905.png"/></p>
<p>g(t, γ) = c * γ^{1/2} * (t * γ)^μ, γ是学习率，c和μ是用来平衡accuracy和稀疏度的可学习参数。</p>
<p>训练结束后，去掉α为0的interaction，并且对新的子网络进行retrain，并且使用adam优化器进行优化（对于子网络来说，此时的α仅相当于衡量各feature interaction的权重，不再具有“筛选”的意义）。</p>
<p>AutoFIS的代码已开源： <a href="https://github.com/zhuchenxv/AutoFIS">https://github.com/zhuchenxv/AutoFIS</a></p>
<h3>3.2 BP-FIS算法</h3>
<p>BP-FIS [10] 使用了贝叶斯优化的方案来解决personalized AFI问题，即为每个用户定制一套feature interaction的方案，求解难度比常规的AFI问题更大。BP-FIS的原理可以用一张有向图来解释：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/9e4e778afc4a4ee16a9e.png"/></p>
<p>这里贝叶斯变量w_i，s_{ui} (binary变量)共同决定了w_{ui}，即用户u的特征i的权重（注意这里d是特征field的数量而非embedding size）；贝叶斯变量s_{ui} (binary变量)和s_{uj} (binary变量，图中未画出)共同formulate了变量s_{uij} (binary变量)，然后s_{uij} (binary变阿玲)与w_{ij}决定了w_{uij}，即用户的第i个特征与第j个特征的交叉特征的权重，最后w_{ui}和w_{uij}共同构筑了最后的特征表达，数学表达式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/871c570621100582c68a.png"/></p>
<p><strong>A. 生成阶段</strong>，目的是使用随机噪声生成特征 &amp;&amp; ctr预测值，具体算法如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/fe71e1ee9ad501124b35.png"/></p>
<p>Algorithm 1中的采样可以用下面的公式表示，文中称这种算法是“Hereditary spike-and-slab prior”（有点类似于因果建模），其中π1和π2是统计值：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/859680015cebb7618edc.png"/></p>
<p>可以看到Algorithm 1的第10-12步，这里的\hat{r}(x)即预估的ctr值。采样值r(x)关于\hat{r}(x)的分布可以是伯努利分布/正态分布，根据具体的假设而定，文中使用的是正态分布。</p>
<p><strong>B. 变分推断阶段 </strong>这里需要定义一下可学习的变量来构建整个ctr预估网络q，并且使其逼近生成网络p：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/9f56bd18c1618635f7a7.png"/></p>
<p>其中q(.)的表达式分别如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b775981c1d1fba169aff.png"/></p>
<p>各项概率值是通过伯努利分布或者高斯分布采样得到（这里w_i和w_{ij}头上应该带弯弯？），如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/05d90f1c8d89d0b7719f.png"/></p>
<p>采样的过程使用<strong>reparameterization</strong>，使用简单的均匀分布/标准正态分布采样（π是统计值）：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7c7a87a5884ac9c78d2a.png"/></p>
<p>这里μ_{ij}和σ_{ij}是对user定制的，假设一共有m个user，则参数复杂度是O(m*d^2)。可对其进行简化，降低到O(m*d)；同时不直接求μ和σ，而是使用模型推断 (faster inference)的方式来进行，效率可以进一步提高：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/d794bce40133b0af1372.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2f945e7e49bb7bb50d90.png"/></p>
<p>其中v_i，v_j是输入特征。</p>
<p><strong>C. Optimization</strong> 最后，优化目标如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/d9105bdcaadf349963e0.png"/></p>
<p>其中r(x)是通过生成模型采样的ctr值；\hat{r}(x)是通过变分推断得到w_i, w_{ij}，进而预估出的ctr值。第二项中，对KL散度的优化比较复杂，有兴趣的同学可以直接看原文，这里将附录中给出的优化公式直接贴出来：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f557804152d5804038a2.png"/></p>
<h3>3.3 Auto-Group算法</h3>
<p>Auto-Group [11] 解决的是高阶特征交叉的AFI问题，其方式有点像“生成式”的方法，即通过网络学习生成交叉的特征组合，而不是将先所有可能的交叉特征罗列出来，最后通过“筛选”的方式完成AFI。其网络结构图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7a38589c97d73941dcf5.png"/></p>
<p>可以看到有一个"grouping"的步骤，实际上，AutoGroup是将高阶特征交叉定义为一个grouping的问题：假设最高阶为P阶，定义sum(n_i), i=1,..., p个set（n_p表示p阶set的数量），对于某个feature f_i，可以将其投放到代表不同阶的set中，从而参加不同阶的feature interaction。思想上与DARTS类似，仍然建模为一个soft selection问题：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a92ace9588faa59d4006.png"/></p>
<p>其中π_{i, j}^p表示是否将feature f_i分配到第p阶的第j个set（binary变量），而α则是将hard selection转化为soft selection。因此AutoGroup的关键是优化α。</p>
<p>当确定了α后，\bar{π}_{i, j}^p由下面的式子确定：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/d70f2ece88d66f1bd1e0.png"/></p>
<p>但是argmax是不可导的，所以采用gumbel softmax采样来近似argmax：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/da1ad12dfb18ef7f5e58.png"/></p>
<p>其中G=-log(log(u))，u ~ N(0, 1)。在inference阶段，则去掉gumbel softmax，直接按照α进行soft selection即可。</p>
<p>AutoGroup对p阶interaction的求解进行了简化，虽然引入了一些不合法的项，但是将计算量从O(n^p)降低到O(n):</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a836d64b5341b3c380f8.png"/></p>
<p>因此，各阶feature interaction的计算如下，其中w_i^p是特征f_i在p阶交叉时的权重，g_j^p的计算方式为<img alt="" loading="lazy" src="/logbook/images/algorithm/ce15621fceeac0e9dddc.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/432ef2a0027a0aa5846c.png"/></p>
<p>最终的feature interaction特征表达为所有set的interaction结果进行concat:</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/35478367929c54c5c527.png"/></p>
<p>优化步骤依旧是DARTS的双层优化方法，但不同的是，对结构化参数和网络参数的优化都是用训练集，而非划分训练/测试集，文中提到这样可以缓解不同数据集间的分布不一致问题。</p>
<h3>3.4 AutoFeature算法</h3>
<p>Auto-Feature [12] 使用了Naive-Bayes tree来解决高阶特征交叉的指数爆炸问题（类似于进化算法）其原理图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/3e489e6f8de53e9d395b.png"/></p>
<p>Naive-Bayes tree是一棵二分树。以当前节点的population的acc值90分位作为阈值T，将该population分到左、右两颗子树上：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/522c99097fca4110f4d7.png"/></p>
<p>因此，Auto-Feature实际上以树的形式将整个种群分到各个叶子节点上。在一次采样中，选中某叶子节点k的概率值根据Chinese Restaurant Process (CRP)算法，数学公式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/5adcf59ec06f59344102.png"/></p>
<p>其中N是目前总的采样数，n_k是该叶子节点被采样的个数，而向量c是各个叶子节点的计数变量。n_k的更新如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7ec845182d49448bd5ae.png"/></p>
<p>C是一个常数，(acc-τ)是计算从第k个叶子节点得到的最后一个样本的acc增益（相对于预设的期望值）。</p>
<p>采样得到一个叶子节点后，还需要生成sample（即feature interaction的方案），具体算法如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/3dacbc0d435e5f7d1ffe.png"/></p>
<p>可以看到，Sample(leaf, D)实际上就对应了进化算法中的“变异”阶段。</p>
<p>这里补充说明一下编码方法。Auto-Feature使用了directed acyclic graph (DAG)来编码，feature interaction的操作有如下几种：</p>
<ul><li>Pointwise addition，即两个/多个向量直接相加</li>
<li>Hadamard Production，即两个/多个向量按照element-wise的方式相乘</li>
<li>Concatenation Layer，即将两个/多个向量直接concat，并且后面加一个feed-forward层进行降维</li>
<li>Generalized Product，将Hadamard Production的结果再经过一个feed-forward层</li>
<li>Null，即不进行feature interaction</li>
</ul><p>可以将以上的operation编码为{0, 1, 2, 3, 4}，对于某一组feature组合可以进行多次operation（也可以完成不做interaction），这样可以得到一个sub-network。将这些sub-network对应的固定长度的编码组合拼起来，即可得到architecture string。比如，对于Avazu数据集，AutoGroup得到了如下的sub-networks，可以看到不同的特征组合其交叉的复杂度也不同：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/c0b53e2874df4aae5295.png"/></p>
<p>整个search的过程如Algorithm 2所示，对应上面的Figure 3：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/8a970e6a5f41653f14e5.png"/></p>
<p>其中NB.learn(.)其实是训练Naive-Bayes tree的分类能力，即给定一个architecture string，判断其分到左子树还是右子树。通过不断优化Bayes tree以及不断优化种群成员，最终输出能够达到预期acc的网络结构（特征交叉方案）。可以看到，这个搜索过程和你问题的复杂度有很大关系，特征交叉的阶数越高，搜索空间越大，搜索时间越长。而且其中有一步"acc=train(archs)"，相当于得到一个新的sample（网络）后，要用训练集对新的网络进行训练，再得到acc，这一步耗时也是“很可观”的。</p>
<h3>3.5 SIF算法</h3>
<p>SIF [13] 求解的问题是给不同的特征组合分配不同的interaction function，候选的function如下表的"human-designed"一栏所示（注：不包括conv和outer-product），不同的IFC时间复杂度和空间复杂度都不一样。注意这里SIF的计算复杂度是O(k)，这是因为SIF对这些operation操作进行了统一的分解，使用神经网络来近似，最后只使用5种复杂度为O(k)的operation来拟合，在下文中我会说明这一技巧。<br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f1ec140ef8c3c96f6bc9.png"/></p>
<p>对于给定的feature组合，通过AutoML的方式选择一种operation：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/25ddb2121de08cd32139.png"/></p>
<p>α需要满足如下条件C1和C2：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/8ae47d57eb4063caad3e.png"/></p>
<p>对于一个d维的向量z，将其投影到C1和C2的方法分别为：</p>
<ul><li>prox_{C1}：取i = argmax_i{z}，然后输出one_hot向量，仅第i个位置为1</li>
<li>prox_{C2}：直接将z的每一位clip到[0, 1]的范围</li>
</ul><p>SIF的优化问题是user-item CF问题的延伸版本，其目标函数如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/dfd2bc51d009f0f1d918.png"/></p>
<p>SIF认为，为每个feature组合安排Table 1中所列举的operation会使得搜索空间变得很大，难以求解，这也是NAS方法的通病。因此，SIF寻求降低搜索空间，具体而言，这些operations分解为2步：1. 先进行micro以及macro转换；2. 从5种operation: multi, plus, min, max, concat 中选择一个operation。其中micro和macro的定义如下：</p>
<ul><li>Micro (element-wise)：使用非线性变化作用于每个embedding element</li>
<li>Macro (vector-wise): 作用于整个vector，比如minus和multiplication</li>
</ul><p>Micro，Macro的transform过程可以建模为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/108412f542569887503c.png"/></p>
<p>其中g(.)是一个轻量的mlp模型，p，q分别是user/item特征的mlp参数，注意这里是逐个element进行的。最终，对transformed后的embedding再选择5种operation中的1种即可，回顾一下加权系数α：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/70014de198f2925f818b.png"/></p>
<p>其中C = C1 + C2。最终，优化的目标函数转化如下，M可以理解为loss的泛化形式：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f7bf074077b4e1a2b83b.png"/></p>
<p>完整的优化步骤如下，其实也是基于DARTS的方案：每一步选择一个batch的train set + 一个batch的val set，val set用来优化结构化参数α，train set用来优化网络参数：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/9d4470bc3d27fb5beab8.png"/></p>
<p>SIF算法的代码已开源：<a href="https://github.com/quanmingyao/SIF">https://github.com/quanmingyao/SIF</a></p>
<h3>3.6 AutoDis算法</h3>
<p>AutoDis [14] 实际上不是用来解决auto feature interaction的问题的，而是在feature interaction之前，对numerical  features进行专门的优化，这一视角比较新颖。因此在这里我也和大家分享一下这篇论文。</p>
<p>AutoDis提出，对数值类特征的合理分桶是非常重要的。AutoDis有三个重要的组成要素：meta embeddings, automatic discretization和aggregation。其中meta embeddings从不同的角度学习numerical features的特征表征；automatic discretization使用soft selection方案选择meta embeddings；最终的embedding输出通过aggregation function对这些embedding进行整合获得。经典的CTR模型图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e7c51f7bd790c3bdf5e3.png"/></p>
<p>在Figure 1中显示，对数值特征的处理有如下三种方式：</p>
<ul><li>No embedding，是指对数值特征直接进行处理，如平方、开方等，这一方案在Youtube DNN [15]中得到应用</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/cccf92a447f19401e1e9.png"/></p>
<ul><li>Field Embedding，即直接进行embedding lookup</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/b8373145f2f2f00f0ebd.png"/></p>
<ul><li>Discretization，即先将数值特征离散化，转化为one-hot数值，再进行embedding lookup:</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/19817efe8c735962f795.png"/></p>
<p>      离散化有“等距离离散化” (EDD)和"log离散化" (LD)两种，分别如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/13999601ef9616a0c400.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7d9bea9167e00c1696ba.png"/></p>
<p>AutoDis的整体算法框架如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a477885146e94d0f8cea.png"/></p>
<p>其中meta embeddings实际上就是为每个分桶值设定的embedding，假设embedding size为d，分桶值为H_j，则mata embeddings的大小为H_j x d。有了meta embeddings后，AutoDis的功能就是将数值x_j自动分桶，然后从meta embeddings中选择一个embedding。分桶的网络是一浅层的MLP网络：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/30a80fc9a7483cf27852.png"/></p>
<p>其中w_j是1xH_j大小，W_j是H_j x H_j大小，对\tilde{x}_j进行归一化，即可得到在不同分桶值上的probability:</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b2c228e40c1ee6951631.png"/></p>
<p>τ在这里扮演了“平滑”的角色，可以发现当τ→0时，这个分布会趋向于one-hot。因此为不同的feature设计不同的τ值很重要，论文设计了一个MLP网络来自动调整τ的值：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/891943e4a7c0ab001e01.png"/></p>
<p>这里的\bar{n}_j是该数值特征的全局统计值（比如CDF，平均值等），W^1和W^2是可学习参数。为了保证训练的稳定性，τ_{xj}会被rescale到[τ-ξ，τ+ξ]的范围，τ是一个全局温度值。</p>
<p>由于是soft selection，最终将会获得H_j个embeddings，需要进行aggregation，文中直接进行了reduce sum:</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/ebbc2fdb2db4e2b63b18.png"/></p>
<p>论文提到，需要对数值特征进行预处理，归一化到[0, 1]的范围，再使用AutoDis：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/24de9de52fe94c3e7b72.png"/></p>
<h2>四、小结</h2>
<p>本文首先介绍了推荐系统中的feature interaction的几种经典的建模方法，从FM的二阶特征交叉，到XDeepFM、InterHAT等高阶特征交叉方法。应该说，feature interaction在推荐系统中扮演着重要角色。但我们在实验中发现，并非越高阶的交叉越好：具体来说，在订阅号推荐的场景中，我们训练的xDeepFM在auc上始终比不过DeepFM。这个现象也说明，高阶、复杂的交叉中有可能携带了一些对模型表现有害的噪声，因此Auto Feature Interaction -- 即自动剔除那些无用的feature interaction，在实际业务场景中具有重要意义。</p>
<p>我们详细介绍了几种AFI算法，包括了贝叶斯生成网络、进化算法以及DARTS优化算法等，文章数量不多，但都很有代表性，相信对大家一定也有所启发。</p>
<p>从学术研究的层面来讲，AFI仍有许多可以优化的空间，比如streaming环境下的AFI问题，大规模稀疏特征场景的AFI问题等，也等着大家去挖掘和创新。</p>
<p>P.S. Auto Embedding Size的相关算法调研请查看文章《推荐系统中的Auto Embedding Size算法》。<br/></p>
<h2>五、参考文献</h2>
<p>[1] Factorization Machines</p>
<p>[2] Produce-based Neural Networks for User Response Prediction<br/></p>
<p>[3] Attentional Factorization Machines</p>
<p>[4] Automatic Feature Interaction Learning</p>
<p>[5] 𝐹𝑀2: Field-matrixed Factorization Machines for Recommender Systems</p>
<p>[6] xDeepFM: Combining Explicit and Implicit Feature Interactions for Recommender Systems</p>
<p>[7] Interpretable Click-Through Rate Prediction through Hierarchical Attention</p>
<p>[8] Adaptive Factorization Network: Learning Adaptive-Order Feature Interactions</p>
<p>[9] AutoFIS: Automatic Feature Interaction Selection in Factorization Models for Click-Through Rate Prediction</p>
<p>[10] Bayesian Personalized Feature Interaction Selection for Factorization Machines</p>
<p>[11] AutoGroup: Automatic Feature Grouping for Modelling Explicit High-Order Feature Interactions in CTR Prediction</p>
<p>[12] AutoFeature: Searching for Feature Interactions and Their Architectures for Click-through Rate Prediction</p>
<p>[13] Efficient Neural Interaction Function Search for Collaborative Filtering</p>
<p>[14] An Embedding Learning Framework for Numerical Features in CTR Prediction</p>
<p>[15] <strong></strong>Deep Neural Networks for YouTube Recommendations</p> 
{% endraw %}
