---
title: "Transformer：加速、长依赖、序列预测"
date: 2022-03-24 10:46:33
categories:
  - 算法
  - 多模态与自然语言处理
---

{% raw %}

<h1>1. 注意力机制：Self-Attention 与 Multi-Head Self-Attention</h1>
<h2>1.1 Self-Attention</h2>
<p>Self-Attention可以理解为自适应加权组合，很多自动化特征工程中都有类似的模块。既然是自适应权重策略的一种，很明显，Self-Attention不具备保序性。</p>
<p>目前，科研论文中存在大量不同形式的Attention，可以参考论文[1]。本文主要讨论Transformer，因此，只讨论Vaswani所用的Scaled Dot-Product Attention[2].</p>
<p>给定query矩阵<strong>Q</strong>, key矩阵<strong>K</strong>以及value矩阵<strong>V</strong>，那么输出就是值向量的加权和，其中，分配给每个值槽的权重由Quey与相应Key的点积确定。即：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7cccb629f3539a2e4f20.png"/></p>
<p>这样，对于一个query以及一个key向量，标量权重计算如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4e6b047f0c6f66927c4d.png"/></p>
<p>Si是所有索引key的集合。因此，可以看出Self-Attentio没有保序性。</p>
<h2>1.2 Multi-Head Self-Attention</h2>
<p>Multi-Head Self-Attention可以直接粗暴理解为：将输入Input划分为更小的数据块Sub-Inputs，然后针对每一个Sub-Input计算Scaled Dot-Product Attention (这里就可以并行计算了嗷)，然后将所有的Attention输出Sub-Outputs拼接起来，得到Multi-Head Self-Attention的输出。即：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/69915a8d4204e615163a.png"/></p>
<p>一般Concat输出之后，也会加一个线性变换，如上Wo所示。Vaswani在[2]中也给了图示，更方便理解了。如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2ded69f61c159c9cd79d.png"/></p>
<h1>2. 基础版Transformer</h1>
<h2>2.1 基本结构</h2>
<p>Transformer采用了神经机器翻译（Neural Machine Translation）中常用的Encoder-Decoder结构。最开始，Transformer并没有获取如此大的网络声量，其名声大噪是因为，只采用了其Decoder模块的BERT和GPT在各项Challenge中接连屠榜。其结构如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/681be68055245d6c0148.png"/></p>
<p>Encoder：编码器部分就是为了生成一个基于Attention的表示；这样，针对一个很大的文本，表示层就可以定位到与任务相关的特征信息片段。 Transformer中有6个如上图左侧的模块。该模块进一步又包含两个子模块：Multi-Head Self-Attention层和Point-Wise Fully Connected Feed Forward Network。看上图也能发现， 每个子模块都有Residule Connected和Layer Normalization，这也是NLP模型的常规操作。</p>
<p>Decoder: 解码器是对输入信息的Attention表示进行信息信息抽取。与编码器不同的是，解码器是使用了两个Multi-Head Self-Attention层。其中， 为了防止位置穿越，第一个Multi-Head Self-Attention是被屏蔽的。</p>
<p>Position Embedding: 前面提到了Self-Attention不具有保序性， 但是对于序列预测、机器翻译等场景，位置信息无疑是最重要的。Transformer通过位置编码提供序列位置信息。因为位置编码和输入Embedding具有相同的维度，所以，位置信息可以直接作为输入。基础版的Transformer主要考虑了两种位置编码。</p>
<ul><li>正弦位置编码，Token的位置记为i=1,…,L； 维度信息记为δ=1,…,D，则位置编码记为：</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/733ec80bb649c7e8adfe.png"/></p>
<p>这样，位置编码的每一个维度与不同维度的正弦波长相关，[2]给了L=32 &amp; D=128条件下的正弦位置编码示例， 如下所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/804d9e36cb26cd4b1e3b.png"/></p>
<ul><li>学习型位置编码：顾名思义，学习的位置编码为每个元素分配一个学习的列向量，该向量对其绝对位置进行编码。Gehring [3]在 English-French翻译研究中给出了响应实现方式。</li>
</ul><h2>2.2 辅助损失函数设计</h2>
<p>采用Mask预测方式直接训练上述模型结构，当transformer的层数超过10层后，正弦位置信息会消失，模型收敛速度变慢，性能变差。为了解决层数加深，性能变差；Al-Rfou[4]提出了辅助Loss（Multiple Positions + Intermediate Layer Losses  + Multiple Targets loss）。<br/></p>
<h3>3.1 多位置损失</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/df5cb3cf57fa96afcdd5.png"/></p>
<p>原来的模型预测是在最后一层进行，现在将每个样本进行一次预测变为进行L（序列长度）次预测。其实，这是RNN-based模型中是标准做法。</p>
<h3>3.1 中间层损失</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/51ab952fd84a41775f81.png"/></p>
<p>除了模型最后一层用于预测，Intermediate Layer Losses将中间层的所有位置都用于预测，由此产生了各个层进行预测的损失。但随着训练的进行，模型的低层对该损失的贡献越来越少。若模型总共有n层，那么第L层在训练进行了L/2n之后，其会停止对该损失的贡献。举个例子，模型总共10层，那么第2层的各个位置预测在进行了2/(10*2)​ =1/10之后便停止了。这种衰减策略会让所有中间层在训练进行了1/2后停止预测。 </p>
<h3>3.2 多标的损失</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f0fac9a02bec9d213f03.png"/></p>
<p>在序列中的每个位置，模型对下一个字符进行两次（或更多次）预测。对每次预测使用不同的分类器，这样对于transformer的每一层的每个位置都会产出两个或多个损失函数，选择一类作为主要损失，其他的都称为辅助损失。每个位置的多个损失需要合并成当前位置的总损失，将每个辅助损失乘0.5加上主损失得到当前位置的总损失。</p>
<p>此外, 基础版transform中位置编码用的是正弦曲线产生的时间信息，并且位置编码是在输入transformer最下层之前加入到词embeding中去的。当模型深度比较深时，这种时间信号可能在沿着transformer向上传递的时候发生丢失。为了解决这个问题，Al-Rfou[4]在每一层添加一个维度512的Positional Embeddings矩阵，这些矩阵都是可学习的。这样第i−1层的输出加上第i−1层的Positional Embeddings后再输入到第i层中去。</p>
<p>Al-Rfou[4]的工作区别于以往在字符级别的语言建模领域RNN-based主导的局面，在当时主流数据集上取得了最好的效果。</p>
<p>我们曾经用游戏领域预料fine-tuning该模型，整体上Auxiliary Loss取得的收益要超过Learned Position Embedding， 甚至进行召回A/B test时，采用Fixed Position Embedding取得了更好的效果。</p>
<h1>4. 超长序列版Transformer-XL</h1>
<p>如1.2中谈及的，基础版Transformer存在的一个问题是：Self-Attention实际上存在一个固定且有限的跨度。在每个更新步骤中，独立的Attention只能关心Sub-input内的信息，并且没有任何信息可以在Sub-input与Sub-input之间流动。这实际上是长文本分割输入存在的必然问题，也是根本问题。 </p>
<p>这种文本分割-模型输入方案存在以下问题：</p>
<ul><li>超长文本问题：模型很难学习到超长文本上下文之间的信息关系</li>
<li>超短文本问题：由于分割后，每个Sub-input中的文本仅有几个Tokens，很难去学习头部Tokens的表示</li>
<li>文本重叠问题：每当segment右移一位时，新的segment就会从头开始重新处理</li>
</ul><p>Transformer-XL[5]主要通过两个策略解决了文本分割问题：</p>
<ul><li>两个文本片段（也就是Sub-inputs）的中间Hidden State重复使用</li>
<li>对于重复使用的Hidden State，采用新的位置编码方法</li>
</ul><h2>4.1 Hidden State Reuse</h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/71780b82356834a6b19b.png"/></p>
<p>如上图所示，通过连续使用先前分段的隐藏状态，可以将分段之间的Recurrent connection引入模型。通过从前面隐藏状态加入信息，模型可以将Self-Attention的跨度进行扩大，进而在多个文本片段之间发挥作用</p>
<p>如果将第（t+1）个文本片段的第n层Hidden State表示为h[n][t+1]， 则XL的Self-Attention过程可以表示为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e11b04069c4c9e25c600.png"/></p>
<h2>4.2 Relative Positional Encoding</h2>
<p>为了有效处理4.1中所示的Attention的跨度问题，Transformer-XL也提出了一种相对位置编码的思想。这是因为如果使用相同的方法对绝对位置进行编码，则前一段和当前段将分配相同的编码，这是不需要的。</p>
<p>为了保证位置信息可以在文本片段中得到一致性的流动，Transformer-XL采用的相对位置编码可以很容易记住每一次的位置偏移。 这样，针对位置i的Query和位置j的Key，1.1中的权重计算如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f8034d8fece06e972d99.png"/></p>
<p>Transformer-XL在进行宏观介绍的时候，将上面的公式进行进一步表示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/683624262684c0f35e9d.png"/></p>
<p>这也就是我们目前熟悉的文本片段信息、上下文片段依赖信息、全局信息关联等。</p>
<h2>4.3 Adaptive Attention Span</h2>
<p>既然文本片段之间的信息依赖，或者说Attention的跨度对模型影响很大，那是不是Attention跨度越大越好呢？ 答案明显不是。 一方面，计算资源的限制，另一方面，文本片段/信息量不同，每个Attention关心的跨度原则上也应该是各异的。 因此，大佬们开始关注自适应Attention跨度的设计了。</p>
<p>Sukhbaatar[6]基于此提出了Adaptive Attention方案。 这里的Adaptive可以理解为“在减少计算和内存成本条件下，支持模型中更长的最大上下文片段”。这里Sukhbaatar做了一个假设：<strong>不同的Attention-Head在相同的上下文Window可能赋予不同的权重分数，因此，对Attentin跨度的优化就是独立训练Attention-Head</strong>。Sukhbaatar得到的实验结果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a552a7c6c6f54aa1c062.png"/></p>
<p> 上图表明：同一模型A和B中的两个Attention-HEad在同一上下文窗口中分配的关注度有所不同。 Attention-Head-A更多地关注最近的Tokens，而Attention-Head-A一致性地关注过去的Tokens(相比A而言)。</p>
<p>计算如下: 给定第i个token,我们需要计算该token和其它在j位置keys的attention权重，其中Si定义了第i个token第上下文窗口：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/ede05ed949faf6281fc7.png"/></p>
<p>此外，这里也采用soft mask函数mz控制有效的可调Attention跨度，将query和key之间的距离映射成一个[0, 1]值。如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/15029d01272a73860b4a.png"/></p>
<p>这样，soft mask就可以直接作用于Attention：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/018106d0b3f20d34590f.png"/></p>
<p>此外，在Sukhbaatar的实验中还发现了一个普遍存在的趋势：<strong>模型低层不需要很长的Attention跨度，顶层的一些attention heads会使用非常长的注意广度。</strong>适应性attention span有助于大大减少失败的次数，特别是在一个有多Attention层和大上下文长度的大模型中。</p>
<p>该经验性结论也促进了后来推荐/计算广告领域等精排模型结构的发展，即底层进行细粒度特征提取、特征组合，顶层进行大范围特征融合。</p>
<h1>5. 强化版Transformer-Informer</h1>
<p>Informer的出现还是源于LSTF（Long Sequence Time-Series Forecasting）经典难题。上面提到的Transformer-XL主要解决Multi-head Attention之间的信息依赖，其实从某种程度上来讲，更像是“Local Incention”。但是对于更长的序列预测问题，这种邻域依赖的方案是不是最好的呢？</p>
<p>根据1.2，不妨先复习一下self-attention的计算：在计算出q、k、v和split head之后，q、k、v的形状是[batch, heads, L, hidden]，dot product的时间复杂度是O(batch*heads*hidden*L^2)，计算出的logits的形状是[batch, heads, L, L]。相对于序列长度L，self-attention的时空复杂度都是O(L^2)的。之所以只考虑L是因为，相比于L，batch和heads都不怎么增长。</p>
<p>因此，对于超长序列L,Transformer模型有以下几个缺陷：</p>
<ul><li>计算复杂度高：self-attention的计算是平方级别的：dot product self-attention在每层的时间和空间复杂度都是O(L^2)</li>
<li>显存消耗过大：多层导致长输入消耗的显存过多：J层encoder/decoder消耗的显存是O(J*L^2)</li>
<li>预测速度太慢：因为Transformer采用的是动态解码，所以它的预测速度和LSTM一样慢</li>
</ul><p>之前也有一些论文，旨在解决Transformer这些问题，但综合解决的Informer是以第一篇（AAAI-Best Paper实至名归）。</p>
<h2>5.1 结构分析</h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/9b5e6b2463335bf61c46.png"/></p>
<p>从上图看，Informer整体还是沿袭了Transformer的Encoder-Decoder结构。子结构上进行了改进， 具体为：</p>
<ol><li>Self-Attention 被 ProbSparse Self-Attention，时空复杂度骤降为O(L*log(L))</li>
<li>Self-Attention Distilling：在每两层之间过滤出决定性的attention score，降低网络宽度，把总空间复杂度降低到O((2-eps)*L*log(L))</li>
<li>Generative Style Decoder：长序列可以一步输出</li>
</ol><h2>5.2 ProSparse self-attention</h2>
<p>首先，[7]给出了Self-Attention计算复杂的推理过程：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/978108a0bae45552e4ab.png"/></p>
<p>根据上面公式，可以看出，需要计算LQxLQ次k(qi,kj), 也就是时间复杂度达到了O(LQxLQ)， 对于长序列，这显然是需要进行加速的。</p>
<p>作者的处理方式还是很巧妙的-<strong>数据的稀疏性</strong>！</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7125b492b81f3ab9410f.png"/></p>
<p>Haoyi Zhou通过实验验证了原自注意力机制存在稀疏性，即自注意力特征图的也存在<strong>长尾分布</strong>现象。具体为，选取多头注意力的头1和头7的注意力得分，发现较少的点积对贡献绝大部分的注意力得分，也就是说其余部分的成对点积可以忽略。</p>
<p>那么问题就转变成：如何过滤出Attention的重要部分？这里作者首先进行Query稀疏度的度量，然后根据“筛选”后的Query，提出ProbSparse Self-attention，计算自注意力得分。具体操作，可以参考[7]。</p>
<h2>5.3 Self-Attention Distilling</h2>
<p>采用的就是常规的“蒸馏操作”，以突出主要特征，降低网络参数。</p>
<h2>5.4 Generative Style Decoder</h2>
<p>从传统的auto-regressive到Haoyi Zhou的直接预测，这一步的改进还是很大胆的，之前想过抛弃动态解码，以加速预测过程。 感知总感觉精度会受到损失，此外一次性解码的长度也很难估计。</p>
<p>其实，这就涉及到处理问题的态度了。 把问题总想的的太复杂，就是会导致实验难以推进！因为LSTF问题能提前知道输出长度，所以采用一站式输出自然可以理解。</p>
<p>从Haoyi Zhou的LSTF实验上看，informer的表现比其他模型都好，且随时间窗口长度增加，预测错误率的增加缓慢；此外，Informer比使用传统self-attention的Informer表现好，说明sparse的假设是正确的 （<strong>这里是存在疑问的</strong>）。关于输入长度，在预测短序列时，MSE随输入长度先增大再减小；在预测长序列时，输入长度越大，MSE越小。最后就是训练和推理环节，毫无疑问， Informer可以吊打一切Transformer。</p>
<p>我们小组在游戏用户历史消费画像上研究了Informer的性能：总体来看，Informer的性能确实比Transformer略好，但是也没有特别明显，这主要是因为我们场景内的长序列与原作者的长序列不在一个量级；我们消融实验没有明显验证Sparse的性能，更侧重“蒸馏”带来的收益。</p>
<h1>6.加速版Transformer-Reformer</h1>
<p>在5.1中，已经详细介绍了Transformer先天存在的弊病-计算复杂度高 &amp; 显存内耗大。 Informer虽然提供了一种比较可行的方案-稀疏Attention+特征蒸馏，但是Informer主要目的是做长序列预测，也就是已经知道了序列的输出长度，这明显是对NLP不友好的。</p>
<p>除了Informer，我们也调研了一些减少Transformer计算量的工作，包括基于局部敏感哈希的Reformer、基于稀疏矩阵分解的Attention机制。</p>
<p>如2和5所述，Transformer先天的问题就是： 1. 内存消耗极大，具有N层的模型中的内存比单层模型中的内存大N倍，因为我们需要存储反向传播的activations； 2. 如5.2所述，对于长序列，Attention的计算太复杂。</p>
<p>Reformer对这两个问题的处理非常巧妙： 1. 将标准residual block替换为reversible residual layer，在训练期间只允许存储一次激活； 2. 提出了时空复杂度为O(L*log(L))的Attention机制，该方法与Informer在本质上有异曲同工之妙。</p>
<h2>6.1 局部敏感哈希Attention</h2>
<p>先说一下，局部敏感哈希。</p>
<p>局部敏感哈希是一组将高维向量映射到一组离散值(桶/集群)的方法。它最常用来作为近似最近邻搜索的一种方法，用于近似的重复检测或视觉搜索等应用。 局部敏感哈希方法尝试将高维空间中相近的向量以高概率分配到相同的哈希。具体可以参考[9]。</p>
<p>Reformer的论文选择了局部敏感哈希的angular变体。它们首先约束每个输入向量的L2范数(即将向量投影到一个单位球面上)，然后应用一系列的旋转，最后找到每个旋转向量所属的切片。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/cce7e5eca93bfb7b6b42.png"/></p>
<p>该图演示了一个用4个桶进行3轮哈希的设置。下面的图中的向量映射到了同一个bucket，因为它们的输入很接近，而上一张图中的向量映射到第一个和最后一个bucket。找到给定的向量选择之后属于哪个桶也可以看成是找到和输入最一致的向量。在为每个token计算一个桶之后，将根据它们的桶对这些token进行排序，并将标准的点积注意力应用到桶中的token的块上。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/bf5b9496b9fb8910ffe4.png"/></p>
<p>有了足够多的桶，这就大大减少了所有的给定的token需要处理的token的数量 。 在实验中，Reformer的论文运行的模型被配置为使用128块大小的块。因此，局部敏感HASH操作将昂贵的key协同矩阵乘法的上下文大小限制为更易于管理的值。</p>
<h2>6.2 <strong>Reversible Residual Network</strong></h2>
<p>Transformer耗显存的原因是我们缓存了太多的Activation； 缓存大量Activation的原因在于我们想通过梯度计算参数更新，加速Transformer收敛。</p>
<p>Reformer论文使用了序列长度为64k的enwiki8语言建模数据集来做实验，隐藏单元的大小为1024，层数为12层，这意味着存储key和value需要2 * 64000 * 1024 * 12 = ~ 1.5B个浮点数，大约是6GB的内存。使用这种内存使用方式，我们将无法在训练期间使用大的批处理大小，从而影响运行时间。</p>
<p>RevNets有个非常聪明的计算技巧，通过以一种特定的方式构造每一层，使内存使用与网络深度保持一致。每一层分为两个部分，X₁和X₂，前向计算如下：</p>
<div>
<pre>def forward_pass(x1, x2, Wf, Wg):
    """
    Need an extra node in the computational graph
    because the gradient of the loss with respect to z1       # differs from the gradient of loss with respect to y1
	x1: one half of layer input
    x2: other half of layer input
    Wf: weights that parameterize function f
    Wg: weights that parameterize function g
    """
    z1 = x1 + f(Wf, x2)
    y2 = x2 + g(Wg, z1)
    y1 = z1</pre>
</div>
<p> RevNets的前向和反向可以简单表示为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/5f498d3f45185696a4cd.png"/></p>
<p>由于结构特定，可以直接自定义函数进行参数更新，这意味着不需要缓存任何激活来计算后向传播。此外，由于每一层的输入都可以很容易地从它的输出中构造出来，内存使用不再需要随网络中层数的增加而增加。</p>
<div>
<pre>def backward_pass(y1, y2, d_y1, d_y2, Wf, Wg):
    """
    Pseudocode for RevNet of backward pass
    
    y1: one half of layer output
    y2: second half of layer output
    d_y1: derivative of y1
    d_y2: derivative of y2
    Wf: weights that parameterize function f
    Wg: weights that parameterize function g
    """
    z1 = y1
    
    # Extra computation -- the price we pay for memory
    # complexity that doesn't scale with n_layers
    # Importantly this means we don't have to store x1 or x2!
    x2 = y2 - g(Wg, z1)
    x1 = y1 - f(Wf, x2)

    # Standard backprop:
    # vjp --&gt; Vector Jacobian Product
    d_Wf, partial_x2 = jax.vjp(f, Wf, x2)(d_z1)
    d_Wg, partial_z1 = jax.vjp(g, Wg, z1)(d_y2)
    d_z1 = d_y1 + partial_z1
    d_x2 = d_y2 + partial_x2
    
    d_x1 = d_z1

    return x1, x2, d_x1, d_x2, d_Wf, d_Wg</pre>
</div>
<p> 区别于Informer的特征蒸馏方案，Reformer选择从结构上对Transformer进行改进。有了RevNet架构，只需要在内存中存储单层的激活，就可以在训练期间使用更大的批处理大小。 </p>
<p>此外，与informer的知识蒸馏降低显存消耗不同，NLP的LOSS不会因为RevNet而降低，[8]给出了实验：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/97c048dba604d7ad6e37.png"/></p>
<p>Reformer是我们之前忽视的一个工作。 从Transformer跳到Informer，才发现Informer对NLP任务很不友好， 里面的一些策略在之前的研究中还是有痕迹的。 当然， 用Informer进行用户阅读标签预测、游戏时长估计等长序列预测还是有优势的。</p>
<p></p>
<p>参考论文：</p>
<p>[1] Attention综述 <a href="https://arxiv.org/pdf/1904.02874.pdf">https://arxiv.org/pdf/1904.02874.pdf</a></p>
<p>[2] Scaled Dot-Product Attention <a href="https://arxiv.org/abs/1706.03762v5">https://arxiv.org/abs/1706.03762v5</a></p>
<p>[3] 学习型位置编码 <a href="https://arxiv.org/abs/1705.03122">https://arxiv.org/abs/1705.03122</a></p>
<p>[4] 辅助Loss函数+学习型位置编码 <a href="https://arxiv.org/abs/1808.04444">https://arxiv.org/abs/1808.04444</a></p>
<p>[5] Transformer-XL <a href="https://arxiv.org/abs/1901.02860">https://arxiv.org/abs/1901.02860</a></p>
<p>[6] 自适应Attention跨度 <a href="https://arxiv.org/abs/1905.07799">https://arxiv.org/abs/1905.07799</a></p>
<p>[7] Informer <a href="https://arxiv.org/abs/2012.07436">https://arxiv.org/abs/2012.07436</a></p>
<p>[8] Reformer <a href="https://arxiv.org/pdf/2001.04451.pdf">https://arxiv.org/pdf/2001.04451.pdf</a></p>
<p>[9] 局部敏感HASH <a href="https://zhuanlan.zhihu.com/p/115741192">https://zhuanlan.zhihu.com/p/115741192</a></p>
<p></p>
<p></p>
<p></p> 
{% endraw %}
