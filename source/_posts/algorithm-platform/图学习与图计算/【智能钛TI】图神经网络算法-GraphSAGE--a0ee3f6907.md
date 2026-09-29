---
title: "【智能钛TI】图神经网络算法-GraphSAGE"
date: 2022-04-15 09:58:23
categories:
  - 算法平台
  - 图学习与内容理解
---

{% raw %}

<div><h2>图神经网络</h2>
</div><div><p>最近几年，深度学习已在图片、语音、文本等领域得到了广泛的研究和应用，并且取得了很好的效果。如果将深度学习视为人工智能1.0，那么图神经网络便可以被看作人工智能2.0，因为它在一定程度上解决传统深度学习无法解决的问题，如“不可解释性”，“难以推理”，“黑箱”等问题。</p>
</div><div><p>现实业务场景中，由于数据之间的联系，许多问题可以抽象成图的问题。以往我们受限于算力，数据只能切割开来，进行局部的优化；而图神经网络框架和算法，以图的视角看待数据之间的联系，不仅利用直接联系的1阶信息，还引入了2阶或者更高阶的信息，天然的考虑到全局的优化。</p>
</div><div><p>为了满足各方业务对图计算的需求，我们实现了传统图挖掘、图表示学习和图神经网络“三位一体”的图计算框架；以及丰富的图算法。</p>
</div><div><h2>图神经网络算法的挑战</h2>
</div><div><p>图计算平台中面临的一些通用性的问题，如：端到端处理，节点编码及容错等在文章《基于Spark on Angel的高性能图计算平台》中有详细介绍这里不再赘述，点击查看详细内容</p>
</div><div><p>在公司内部业务中实现高效的图神经网络除了解决端到端处理，节点编码及容错等问题外，还面临着如下的挑战：</p>
</div><div><ul>
<li>海量图数据带来的大数据处理难题</li>
<li>海量图数据的训练中面临二跳邻居采样的问题</li>
<li>神经网络带来深度学习的需求</li>
<li>图神经网络模型众多</li>
</ul>
</div><div><h2>PyTorch on Angel图计算架构</h2>
</div><div><p>为了解决图神经网络中面临的问题，在Spark on Angel图计算平台的基础上开发了PyTorch on Angel。有效的解决了上面的难题，首先，借助spark来解决大数据处理的问题；其次，angel参数服务器提供的自定义数据存储及灵活的PSF能够实现高效的二阶邻居采样；最后利用PyTorch的自动求导功能能够高效且便捷地构建一个神经网络。目前基于PyTorch on Angel已经实现了一些图神经网络算法，如GraphSAGE，DGI, R-GCN，EdgeProp等。PyTorch on Angel图计算架构图如下：</p>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a86f655cb8b61ed04bf8.png"/></p>
</div><div><center>图 1. PyTorch on Angel图计算架构</center>
</div><div><p><strong>Spark组件</strong></p>
</div><div><ul>
<li>Spark Driver：负责控制整体计算逻辑；</li>
<li>Spark Executor：存储图邻接表/边表等不可变数据，加载PyTorch模型文件，在每轮迭代中从PS拉取（pull）所需的节点属性等数据，在本地完成处理和计算，并将结果推送（push）回PS，交由PS进行更新；特别之处在于pytorch c++后端以本地模式运行在实际计算后端中。</li>
</ul>
</div><div><p><strong>Angel组件</strong></p>
</div><div><ul>
<li>Angel Master：管理参数服务器的生命周期；</li>
<li>Angel PS (Parameter Server)：将节点属性等可变数据以向量的抽象形式储存（ <strong>支持存储自定义的元素数据结构，支持负载均衡分区</strong> ），通过Angel特有的PS函数实现节点属性in-place更新及其他根据特定算法定制的灵活计算；</li>
<li>Angel Agent：作为代理桥接Spark Executor和Parameter Server。</li>
</ul>
</div><div><p><strong>Python组件</strong></p>
</div><div><ul>
<li>Python client：生成pytorch模型文件</li>
</ul>
</div><div><h3>系统的特点与优势：</h3>
</div><div><p>基于Spark on Angel 的PyTorch on Angel不仅具有高扩展性、端到端处理、支持稀疏数据、高容错等特点，同时还具有如下特点：</p>
</div><div><ul>
<li>开发一个新的图神经网络算法容易</li>
<li>底层通过JNI调用C++代码大大提高了运行速度</li>
<li>可利用PyTorch自动求导功能轻松构建深度神经网络</li>
<li>Angel参数服务器可以自定义数据存储并利用PSF实现二阶邻居采样</li>
</ul>
</div><div><h2>GraphSAGE</h2>
</div><div><p>GraphSAGE[1]全称是Graph SAmple and aggreGate，由斯坦福大学提出，该算法旨在从图网络中学习出节点的特征表示，并以此为理论基础，斯坦福和Pinterest公司合作提出了第一个工业级别（数十亿节点和数百亿边）基于GCN的推荐系统，并在离线评估和AB实验选中取得了不错的效果。</p>
</div><div><p>近年来的Deepwalk,LINE, node2vec, SDNE, DNGR等模型能够高效地、直推式(transductive)地得到节点的embedding，与这些算法相比，GraphSAGE有什么不同与优势呢？<br/>
从目前大部分表示学习算法实现方面可以分为大体两类：直推式（transductive）与归纳式（inductive）。<br/>
直推式的算法通常是在一个固定的网络中学习节点的特征表示，这样的算法通常会有以下几个问题：</p>
</div><div><ul>
<li>无法共享权重，像Deepwalk, LINE这样的算法通常节点的embedding是一个n∗dn*dn∗d的矩阵，并以每个节点的embedding作为参数，通过优化器进行优化，互相之间不共享学习参数。</li>
<li>通常输入固定为节点个数n，当出现新的节点则需要重新计算，演化性较差。</li>
</ul>
</div><div><p>归纳式的算法则可以简化具有相同形式特征，即图的一般化，从而使得对于没有出现的节点也具有识别能力。如：GraphSAGE通过对节点局部邻居进行采样并聚合其特征来训练一组算子，通过算子来生成节点的特征表示，该方法能够有效的为未出现的节点生成特征表示。这样的计算一方面达到了权重的共享，另一方面当有新节点出现时，无需重新计算，直接利用已经训练好的算子即可得出新节点的特征表示。</p>
</div><div><h3>算法原理</h3>
</div><div><p>GraphSAGE的核心逻辑在于如何聚合节点邻居的特征信息<br/>
<strong>前向传播</strong> 的原理如图2所示（图片来源于论文[1]）</p>
</div><div><ol>
<li>首先，对某节点v的邻居进行k阶随机采样，采样的目的是降低计算的复杂度，在本例中k=2，一阶邻居3个，二阶邻居5个。</li>
<li>其次，先对k阶特征进行聚合，其次k-1阶特征聚合，直至k=0，即获得v的特征表示，在聚合的过程中可以使用不同的聚合函数，后文将详细介绍。</li>
<li>GraphSAGE能够生成节点的特征表示，同时也可以将特征embedding向量作为全连接层的输入进行节点预测。</li>
</ol>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/327a9755ad150da863da.png"/></p>
</div><div><center>图 2. graphsage采样与聚合过程[1]</center>
</div><div><p>前向传播的伪代码如图3所示<br/>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/290c06932a180fd37b47.png"/></p>
</div><div><center>图 3. GraphSAGE前向传播算法伪代码[1]</center>
</div><div><p>GraphSAGE的输入包含：</p>
</div><div><ul>
<li>图网络</li>
<li>节点特征</li>
<li>采样阶数</li>
<li>权重矩阵</li>
<li>非线性激活函数</li>
<li>聚合函数</li>
<li>邻居采样函数</li>
</ul>
</div><div><p>输出：节点的特征表示向量<br/>
其中核心的逻辑是4-5行对所有节点进行遍历通过聚合邻居节点特征更新目标节点，外层循环K则表示目标节点最终能被K阶的邻居更新到。</p>
</div><div><p>从上边的计算逻辑中可以发现除输入数据外，还有很多输入需要确定下来。<br/>
参考论文结果，对于GraphSAGE算法参数提出了一些建议：</p>
</div><div><ul>
<li>采样阶数：通常K=2时即可达到较高的效果</li>
<li>邻居采样个数：一阶采样S1S1S1个，二阶采样S2S2S2个，建议 S1∗S2&lt;=500S1*S2&lt;=500S1∗S2&lt;=500</li>
</ul>
</div><div><p><strong>聚合函数</strong><br/>
图网络数据与文本、图像等数据不同，节点之间虽有编号，但并无顺序关系，因此在GraphSAGE算法中使用聚合时需要不仅能够处理任意顺序的节点，还要考虑到对称性（即排序不变性），同时还是可训练的。一般使用的聚合函数有以下几种（一般 σ\sigmaσ 可以被任意深的多层感知器代替）：<br/>
均值聚合：即逐元素的对节点v邻居k-1阶特征向量进行平均得到k阶特征，然后与节点v的k-1特征相拼接最后计算出节点v的k阶特征，公式如下：</p>
</div><div><p>hN(v)k=MEAN(huk−1,∀u∈N(v)) h^k_{N(v)} = MEAN({h_u^{k-1}, \forall u \in N(v)})  hN(v)k​=MEAN(huk−1​,∀u∈N(v))<br/>
hvk=σ(Wk⋅CONCAT(hvk−1,hN(v)k)) h^k_v = \sigma({W^k \cdot CONCAT(h^{k-1}_v, h^k_{N(v)})})  hvk​=σ(Wk⋅CONCAT(hvk−1​,hN(v)k​))</p>
</div><div><p>归纳式均值聚合：<br/>
借鉴均值聚合的思想，将节点v的k-1阶特征向量与节点v邻居的k-1阶特征进行并集，然后逐元素平均。这样的做法可以被当做是一个卷积操作，因为它是局部频谱卷积的粗略线性近似。公式如下：<br/>
hvk=σ(Wk⋅MEAN({hvk−1}⋃{huk−1,∀u∈N(v)})) h^k_v = \sigma({W^k \cdot MEAN(\{h^{k-1}_v\} \bigcup
 \{h_u^{k-1}, \forall u \in N(v)\})})  hvk​=σ(Wk⋅MEAN({hvk−1​}⋃{huk−1​,∀u∈N(v)}))</p>
</div><div><p>LSTM聚合：<br/>
是一个基于LSTM框架的更为复杂的聚合器，因此与均值聚合相比具有更强的表达能力。但是由于LSTM是一种有序性的操作集合，不满足“排序不变性”，所以在使用时需要对节点邻居进行随机排序。这里LSTM不作为重点介绍，详细原理参见论文[2]。</p>
</div><div><p>pooling聚合：<br/>
在池化聚合中，每个邻居的特征向量将通过完全连接的神经网络独立地馈入，最后通过最大化池化对邻居信息进行聚合，公式如下：<br/>
AGGREGATEkpool=max({σ(Wpoolhuk+b),∀u∈N(v)}) AGGREGATE^{pool}_k = max(\{\sigma(W_{pool}h_{u}^k + b) , \forall u \in N(v)\})  AGGREGATEkpool​=max({σ(Wpool​huk​+b),∀u∈N(v)})<br/>
一般 σ\sigmaσ 可以被任意深的多层感知器代替，同时最大化池化可以被平均池化代替。</p>
</div><div><p><strong>参数学习</strong><br/>
上面介绍节点邻居特征聚合的基础是相应的一些参数已经学习好，本小节将介绍如何学习这些参数。<br/>
参数学习的过程就是一个目标函数的优化过程，根据目标函数的应用情况，又可以选择有监督的损失函数与无监督的损失函数。</p>
</div><div><ul>
<li>
<p>基于图网络的有监督损失<br/>
有监督的损失将特征向量作为全连接层的输入，依据任务类型选择相应的目标函数，如交叉熵，通过优化目标函数来更新网络中的参数。</p>
</li>
<li>
<p>基于图网络的无监督损失<br/>
在无监督的学习中，通常希望节点与较近邻的节点之间相似度高，而与不相邻节点的相似度低，所以在无监督的学习中需要有这样的正负样本，即选取某节点v的邻居作为正样本，选取一些与v没有交集的点作为负样本，通过优化该目标函数来进行网络中的参数更新，公式如下：</p>
</li>
</ul>
</div><div><p>JG(zv)=−log⁡(σ(zvTzu))−Q⋅Eun∼Pn(u)log⁡(σ(zvTzun)) J_G(z_v) = -\log(\sigma(z_v^Tz_u)) -Q\cdot \Bbb
E_{u_n\sim P_n(u)}\log(\sigma(z_v^Tz_{u_n}))  JG​(zv​)=−log(σ(zvT​zu​))−Q⋅Eun​∼Pn​(u)​log(σ(zvT​zun​​))</p>
</div><div><p>其中u表示v固定步长的随机邻居， PnP_nPn​ 是一个负采样分布， Q为负采样的个数。值得注意的是，这里的节点embedding向量 zvz_vzv​ 是从邻居的特征中学习而来的，不是简单地查询。</p>
</div><div><h3>算法实现</h3>
</div><div><p>通过上边对算法GraphSAGE的介绍，要通过PyTorch on Angel实现该算法需要解决以下几个关键点：<br/>
数据的存储，邻居采样，聚合函数，梯度计算，参数更新，批量计算</p>
</div><div><p><strong>数据的存储</strong><br/>
Spark Executor上存储每个子图（graph partition）的邻接表，Angel参数服务器上自定义了节点类型，用于存放图中的节点与节点属性如：节点ID，特征，邻居，节点类型等，该类型能够方便的存储节点信息，同时有利于进行节点采样。</p>
</div><div><p><strong>邻居采样</strong><br/>
使用分布式参数服务器架构能够轻松实现邻居的多阶采样，其中一阶采样在spark executor上实现，上传采到的一阶邻居到ps上，使用psf进行二阶邻居采样。</p>
</div><div><p><strong>聚合函数&amp;梯度计算</strong><br/>
在python客户端定义网络的结构，实现模型接口后，网络中的聚合函数与激活函数可由用户自己定义并且由于PyTorch具备自动求导功能，因此实现与更改图网络结构都非常方便，而且用户也无需关心底层的实现。</p>
</div><div><p><strong>参数更新</strong><br/>
如上述算法所介绍，我们知道GraphSAGE是在学习一些算子，并将这些算子应用到新的图中，因此在学习的过程中就涉及到参数的更新，这些参数便是各个网络层中的权重，他们的大小数量由用户定义的图网络决定并初始化，通过加载模型文件将权重传到ps端，以row partition格式存储，计算时从ps端拉取，通过后向计算更新后再更新到ps上。</p>
</div><div><p><strong>如何进行小批量计算</strong><br/>
前面介绍的GraphSAGE算法原理是基于每次对全部节点进行邻居采样并更新，如果想要使用小批量快速迭代应该如何做呢？</p>
</div><div><ul>
<li>小批量如何采样，使用小批量会面临如何能够做到在全局均匀的邻居采样，由这个问题出发，可以想到先将小批量 BBB 中节点的一阶邻居全部拿到，再将一阶邻居的一阶邻居全部拿到作为小批量节点 BBB 的二阶邻居，以此类推。</li>
<li>小批量如何更新，与全局更新类似，在获得小批量节点 $ B $ 的1到K阶邻居集合后，用小批量邻居集合代替原来的全量节点进行节点特征的更新。（假设K=2） B2B^2B2 或者 BBB 为 批量节点数据，  B1B^1B1 为其一阶邻居，  B0B^0B0 为其二阶邻居，节点的初始表示为节点的输入特征，更新顺序是先对一阶邻居( B1B^1B1 )的邻居，即二阶邻居( B0B^0B0 )进行采样，通过聚合二阶邻居的特征来更新一阶邻居，然后通过聚合一阶邻居的特征再更新批量节点的表示向量，以此类推。</li>
</ul>
</div><div><p>GraphSAGE小批量前向传播算法伪代码如下图所示：</p>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/cff7d706d54633e952a5.png"/></p>
</div><div><center>图 4. GraphSAGE小批量前向传播算法伪代码[1]</center>
</div><div><h2>性能测试</h2>
</div><div><p>为了验证算法性能与效果，我们在公开数据集reddit及内部业务数据上进行了测试，数据的一些描述信息如下：<br/>
表 1. 测试数据基本信息</p>
</div><div><div><table>
<thead>
<tr>
<th>数据集</th>
<th>点数</th>
<th>边数</th>
</tr>
</thead>
<tbody>
<tr>
<td>reddit</td>
<td>23万</td>
<td>1亿</td>
</tr>
<tr>
<td>业务数据</td>
<td>8亿</td>
<td>120亿</td>
</tr>
</tbody>
</table>
</div></div><div><p>通过多次实验对比了不同大小数据集在基于PyTorch on Angel与Euler平台的性能，如图5所示在reddit数据集上平均一轮训练耗时Angel比Euler快20+倍，同时在百亿边的数据集上，Angel能够快速跑出结果，但是在Euler上至今还未跑成功过。通过这样的对比，能够说明基于PyTorch on Angel实现的图神经网络不仅性能非常好，同时在非常巨大的图网络上还能够稳定的运行。</p>
</div><div><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ed481d6ccf7bbdac8704.png"/></p>
</div><div><center>图 5. GraphSAGE性能对比</center>
</div><div><h3>智能钛Demo链接</h3>
</div><div><p>目前基于PyTorch on Angel已经实现了一些图神经网络算法，如GraphSage，DGI, R-GCN，EdgeProp等。</p>
</div><div><ul>
<li>GraphSAGESupervised</li>
<li>GraphSAGESupervised使用文档</li>
</ul>
</div><div><h2>参考文献</h2>
</div><div><p>[1] Hamilton W L , Ying R , Leskovec J . Inductive Representation Learning on Large Graphs[J]. 2017.<br/>
[2] S. Hochreiter and J. Schmidhuber. Long short-term memory. Neural Computation, 9(8):1735–1780, 1997.</p>
</div> 
{% endraw %}
