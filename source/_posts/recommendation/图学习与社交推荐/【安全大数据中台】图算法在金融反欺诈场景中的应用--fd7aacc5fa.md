---
title: "【安全大数据中台】图算法在金融反欺诈场景中的应用"
date: 2022-06-13 15:23:39
categories:
  - 推荐算法
  - 图学习与社交推荐
---

{% raw %}

<h1>1. 背景介绍</h1>
<p>随着近些年金融科技的迅速发展，在数字技术的加持下，金融欺诈的风险也在不断升级；个人信贷业务作为金融行业的一个重要业务领域，也面临着极高的信贷风险，行业面临着例如包装、骗贷、多头借贷等黑产的威胁。因此，准确、稳定的个人信贷风险评估成为各大金融信贷企业的痛点所在。</p>
<p>个人信贷风险评估流程主要包括贷前风险评估、贷后风险评估、贷中风险管理和贷后催收评估等；贷前风险评估作为整个流程的第一步便显得尤为重要；其业务场景大体如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/daf6e5af5a26b48a86d8.png"/></p>
<p>因此，我们在这里要做的，便是依托安全大数据中台已有的海量数据，针对大盘的个人用户进行画像并建模，最终生成对每个用户的取值在0-100分之间的风险分；这个风险分将会最终提供给金融机构用于进行是否放贷的评估标准之一。</p>
<p><br/></p>
<h1>2. 基础流程介绍</h1>
<p>建模的样本来源于多个金融机构在实际场景中申请贷款的用户，这批用户在贷款发放的未来6个月内是否发生逾期行为则会作为用户的正负标签。拿到的样本包含有申请的时间戳，时间范围涵盖从202103~202109共计6个月的用户数据，将样本按照如下时间线划分成训练集和验证集得到：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/4940cf08919601d85606.png"/></p>
<p>其中训练集26万，验证集7万，总计33万。</p>
<p>用于构建特征的数据主要是user-item关系数据（安全大数据中台已做合规脱敏处理），这份数据大约覆盖了十亿级别的用户以及百亿级别的关系；我们对item数据进行了分类处理，而后基于分类信息和user-item的关系数据，构建了基础的用户画像特征，使用Xgboost模型作为模型，得到了最基础的用户风险分模型作为baseline；大体流程如下图所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/ae5272538f6e5046670c.png"/></p>
<p>后续所有优化效果皆基于该baseline模型进行优化。</p>
<p><br/></p>
<h1>3. 图算法讨论</h1>
<p>用于进行贷前风险评估的数据主要是user-item的关系数据，在user和item都不包含特征的时候，这份数据包含的就是user结点和item结点的连接关系，因此很容易想到将user、item都作为图上的结点，而且user-item的连接关系则变成了图上的连边，这份数据就自然而然形成了一个具有user-item关系的二部图；如果想从这张图里面提取到用户的特征，那么首先能够想到的便是通过图嵌入的方式提取用户特征。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/8bbaeda02f146fca90da.png"/></p>
<p><br/></p>
<h2>3.1 图嵌入</h2>
<p>图嵌入实际上是图神经网络的一种，是一种"Topology-driven"的图网络，其核心在于：通过保留网络拓扑架构信息，将网络顶点表示到低维向量空间中；因此，图嵌入算法生成的Embedding，包含的是结点与结点的拓扑关系信息，是对结点互相之间的“距离”的一种表征。</p>
<p>图嵌入算法比较经典的主要有2014年提出的DeepWalk算法[1]，2015年提出的LINE算法[2]以及结合以上两者并于2016年提出的Node2Vec算法[3]；这三种算法有着极为相似的算法框架，主要包含两步：</p>
<p>1. 通过不同的游走策略，在图上采样一系列"结点访问序列"，作为下一步的"语料数据"。<br/>2. 使用Embedding算法将"结点访问序列"进行Embedding，得到每个结点的Embedding特征（一般使用SkipGram算法）</p>
<p>以上三种算法的不同之处则在于游走策略的不同，而Node2Vec结合考虑了DeepWalk和LINE两种游走策略，因此我们主要讨论Node2Vec.</p>
<h3>Node2Vec</h3>
<p>Node2Vec和以上两种算法最大的不同，在于设计了一种灵活的带有偏重的随机游走策略，使得广度优先遍历和深度优先遍历两种游走策略能够很好的融为一体。给定当前顶点v，访问下一个顶点x的概率为</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/80fb3bc9ab3f18375d1d.png"/></p>
<p>其中<img alt="" loading="lazy" src="/logbook/images/recommendation/cb5cb537b257a75fe54f.png"/>是顶点v和顶点x之间的未归一化转移概率，Z是归一化常数；Node2Vec引入两个超参数 p 和 q 来控制随机游走的策略，假定当前随机游走经过边(t, v)到达v，设<img alt="" loading="lazy" src="/logbook/images/recommendation/d06b066abe932979c255.png"/>，其中<img alt="" loading="lazy" src="/logbook/images/recommendation/721136ee4ef89eb163b2.png"/>是顶点v和x之间的权重，</p>
<div><img alt="" loading="lazy" src="/logbook/images/recommendation/87ffd46a463a4c1bd75b.png"/></div>
<p>其中<img alt="" loading="lazy" src="/logbook/images/recommendation/e9508a6de3c8082b360a.png"/>为顶点t和顶点x之间的最短路径距离。Node2Vec中设计了两个参数：P 和 Q 用于控制随机游走的策略：</p>
<ul><li>P 控制重复访问刚刚访问顶点的概率。如果 P 较高，则访问刚刚访问过的顶点的概率会变低，反之则会变高。</li>
<li>Q 控制倾向于向外游走还是倾向于向周边游走。若 Q &gt; 1 则倾向于访问附近的结点（即广度优先遍历），反之则倾向于访问更远的结点(即深度优先遍历)</li>
</ul><p><br/></p>
<p><strong>Node2Vec中的同质性和结构性</strong></p>
<p>论文中其实有讨论过关于Node2Vec的同质性和结构性的讨论[4]：</p>
<ul><li>侧重于 DFS 的话，即使两个结点不彼此相连，只要它们有共同的1阶2阶邻居，也会得到相似的上下文，从而学到的 embedding 会比较像。此时同质性较强，具备这种特征的DFS可以更好的找到簇的边界，如图中上半部分所示。</li>
<li>侧重于 BFS 的话，处于同一个密集连接的局部的结点会更加相似，因为它们的上下文会有更多的重叠。此时结构性较强，具备这种性质的 BFS 可以更好地感知结点所处的局部结构。</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/recommendation/9310b1ba365df1787ee4.png"/></p>
<p><strong>业务场景使用</strong></p>
<p>首先，由于构建的原始图是user-item的图，是一个标准的异构二部图，而Node2Vec算法原始的使用场景是在同构图上的，因此需要对Node2Vec进行小幅度的调整才能才业务上使用，常规的做法包括：</p>
<ol><li>将user-item的二部图，转化成user-user的同构图。</li>
<li>引入Node2Vec的异构版本：metapath2vec来处理该业务场景。</li>
<li>考虑游走时加入一些额外的策略来生成序列。</li>
</ol><p>在实际业务中，可以根据实际情况选择合适的做法；</p>
<ol><li>user-item数据具有极其明细的头部效应，头部item覆盖绝大多数user；在这种场景下将图转为user-user的同构图将会导致边关系迅速膨胀，因此未被采用。</li>
<li>当前图中只有user-item两类结点，且为标准的二部图；限定meta path就相当于限定了Node2Vec的游走路径，在当前场景上并不适用。</li>
</ol><p>因此，最后我们选用的第三种策略；由于我们的目的是为了生成user embedding作为特征补充到分类器中，因此我们采用的策略是：游走策略不变，但是会将游走结果中的item结点丢弃掉，直到游走的路径中user结点的个数达到原设定的 <em>L</em> 时结束游走；这样生成的序列就是长度为 <em>L</em> 的全user序列。</p>
<p>另外，在金融反欺诈场景中，也有关于同质性和结构性的取舍：如果业务场景更偏向于寻找多个社群里面的不同身份的角色，那么更多的需要关注结点的结构性，因而需要更加侧重BFS；而在我们贷前风险评估场景中，更加关注的是用户的欺诈风险，而这种欺诈风险是往往是图上有直接关联关系的结点，因此我们需要关注结点的同质性，从而需要更侧重DFS。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/bc144aa240332c3cd7a8.png"/></p>
<p>从结果来看，Node2Vec生成的特征效果明显不佳，0.4%效果的提升几乎可以认为该特征没有起到效果；分析原因主要考虑：</p>
<ol><li>原始的baseline特征中就包含user-item关系信息，因此通过Node2Vec的方式捕捉到的额外的关系信息并没有带来额外的信息量。</li>
<li>随机游走会偏向于在图中采样度数更高更热门的结点，对于反欺诈场景中趋向于捕捉长尾item的目标不符。</li>
</ol><p>其实从实际业务场景中的使用可以看出来，通过Node2Vec生成的用户Embedding特征，包含的信息主要来源于user-item的连接关系，以及基于user-item连接关系衍生出来的user-user的共现关系；而user-item的数据里面，还包含了每个user的item序列信息，还包含item本身所包含的聚集信息；这些信息都是Node2Vec这类图嵌入算法无法引入的特征；因此，当考虑到需要引入这些额外结点信息时，就需要我们将目光，转向另一类图算法：图神经网络算法。</p>
<h2><br/></h2>
<h2>3.2 图神经网络</h2>
<p>不同于图嵌入分支的由"Topology-driven"，基于空间的图神经网络则是一种典型的"Feature-driven"模型，他本质上是让结点所包含的特征，依托于结点和结点的连接关系，让结点特征像消息一样在整个图里面流动和传递；从而达到借助周边邻居结点的特征，来更新自身结点的特征的目的；这类基于”消息传递“的图神经网络模型，主要包括GraphSAGE、GAT等。</p>
<h3>GraphSAGE</h3>
<p>GraphSAGE[5]是一种较为简单直观的图神经网络结构，从本质上说，他只是将中心结点周围K阶的邻居结点的特征，通过若干个聚合函数，逐层合并到中心结点上，从而将中心结点周围K阶邻居的特征信息，融入到中心结点的Embedding之中。</p>
<p>相比于传统的图神经网络，GraphSAGE主要有以下几点优势：</p>
<ul><li>归纳学习，可以泛化到未见过的结点。</li>
<li>高效高性能，使得GraphSAGE比较适合在工业界实际落地。</li>
<li>灵活性好，可定制的空间大。</li>
</ul><p><strong>算法框架</strong></p>
<p>GraphSAGE的核心，不在于学习一个图上所有结点的Embedding，而在于学习一个每个结点与周围结点的推导关系；因此，即使对于不在训练图上出现的陌生结点，GraphSAGE也能根据这个陌生节点的周围结点，得到该结点的Embedding；GraphSAGE算法大体流程如下：</p>
<p>1. 对当前结点<em> v</em> 的周边<em> k</em> 度邻居进行逐层的采样，这里采样的目的是在尽量维持算法效果的基础上提高算法效率。<br/>2. 采样命中的邻居结点的特征，从外向内逐层进行聚合，最终得到结点<em> v</em> 的特征结果。<br/>3. 使用结点<em> v</em> 的特征结果（一般加一层线性层转成标量）和标签计算损失函数，而后反向传播调整GraphSAGE网络的参数。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/5e305387e02189e94ae1.png"/></p>
<p>算法伪代码如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/b0833ba3c0014ff96851.png"/></p>
<p>其中，<em>K </em>表示图神经网络的采样层数，也是图神经网络的深度，他表示每个结点将会聚合周边几阶的邻居特征；对于图上每个结点<em>v</em>，来自第<em>k</em>阶的结点特征将会通过<em><strong>AGGREGATE</strong></em>函数进行聚合，并且把聚合结果赋给第<em>k-1</em>阶的结点，则第<em>k-1</em>阶的特征将变为上一层聚合特征和自身特征的<strong><em>CONCAT</em></strong>，而后通过一个加权函数合成；一次类推，直到最终得到结点<em> v</em> 的Embedding特征。</p>
<p><strong>业务应用</strong></p>
<p>对于以上GraphSAGE框架，可以在如下方面针对业务场景调整：</p>
<p>1. GraphSAGE算法的层数，一般3层以内，高于3层将容易出现过平滑现象。<br/>2. GraphSAGE算法每一层聚合的<em><strong>AGGREGATE</strong></em>函数<br/>3. GraphSAGE算法每一层采样的邻居个数</p>
<p>在金融反欺诈场景中，由于涉及全量大盘用户的打分，处理的数据量极大，因此模型的性能显得尤为重要，所以对于1、2点，我们都没有没有做过于复杂的策略，大家可以根据业务需求自行调整。对于第三点，由于反欺诈场景中，与欺诈相关联的item在众多正常的item中往往在长尾item中，因此采样策略需要尽量采集到相对长尾的item数据；这里我们做了如下实验：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/cbc5a8947629b281e765.png"/></p>
<p>从最终结果来看，GraphSAGE算法中的随机采样策略并不适用于金融反欺诈场景，为了捕捉到长尾item的特征信息，采用度倒数甚至全量采样的方式，都能够明显提高算法的最终效果。</p>
<p>与此同时，GraphSAGE的缺陷也被暴露了出来：即使通过采样方式捕捉到了欺诈相关的item的特征信息，也有可能在做聚合（例如取平均值）的时候，被大量普通无效的item信息淹没，从而大大削弱了用户实际风险，因此，需要换种方式，让模型能够提高这些欺诈相关的item的权重，从而"重视"这些风险欺诈的item；此时Attention机制便进入了我们的视野。</p>
<p><br/></p>
<h3>GAT</h3>
<p>2017年，《Attention Is All You Need》一作，让整个机器学习领域刮起了一股Attention的风潮，所有神经网络模型都摩拳擦掌，试图在原本网络的基础上，将Attention机制引入进来；在这样的背景下，GAT网络[6]也应运而生，并且随着对Attention机制研究的不断深入，新的基于Attention的图神经网络也在不断研究出来甚至发展成了一个专门的分支。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/8d1eb9b19462b5121839.png"/></p>
<p>GAT既然核心思路来源于Attention，自然免不了Attention机制计算的两步走：1.注意力系数计算；2.合并求和。</p>
<p>(1) 计算注意力系数</p>
<p>图神经网络中使用的是加性，因此对于顶点<em> i</em> ，他的邻居顶点<em> j</em> 的Attention系数<img alt="" loading="lazy" src="/logbook/images/recommendation/3bd4f53aae93a808f709.png"/>的计算公式为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/e8ddbfe10805c350f671.png"/></p>
<p>其中W是一个共享的参数矩阵，他的目的在于对顶点特征进行增维，是一种典型的特征增强的方法；得到该系数以后，对其进行归一化后就可以得到注意力系数</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/2b3997049599d7264f5c.png"/></p>
<p>(2) 合并求和</p>
<p>将注意力系数与原本的结点的特征相乘求和即可得到顶点的Embedding特征：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/b04bbba568ce504d8327.png"/>引入多头机制则有：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/0a5880037621e67e05d4.png"/></p>
<p><br/></p>
<p><strong>业务应用</strong></p>
<p>基于前文构建的user-item的二部图网络，GAT的实际使用和论文提到的略有不同；原文中GAT使用在一个同构图上，图上所有结点均为同种类型，而在我们这里本质上是一个异构的网络，因此在结点聚合所有邻居结点的时候，需要考虑不同的结点类型来分别处理Attention系数的计算；但是有趣的是，由于提取的数据构建的是标准的user-item二部图网络，从而确保了：所有user结点的邻居都是item，所有item结点的邻居都是user，从而只需要针对这两种情况分别处理即可。</p>
<p>实际应用到业务上的效果大体如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/7fbf063e3ae85e97897b.png"/></p>
<p><br/></p>
<p>从实际业务结果来看，GAT的效果会要比全采样的GraphSAGE要更好，显然是Attention机制在这里发挥了作用，抽样查看Attention Weight的值时，也发现与金融相关的item的权重会要更高一些。</p>
<p><br/></p>
<h1>4. 工程落地实践</h1>
<p>因为涉及到数十亿级别的点以及百亿级别的边，结点上还包含高维的user特征以及item特征；如此大的内存开销单机很明显是满足不了需求的，因此我们首先考虑的是使用分布式图计算平台来解决工程化落地的问题。</p>
<h2>Angel图计算平台</h2>
<p>Angel[7]是公司内部一款使用PS Server架构构建的高性能分布式图计算平台，上面提供了大量图相关的算法，包括LINE、Node2Vec等图嵌入算法；GraphSAGE、GAT等图神经网络也有实践。当前Angel图计算平台主要部署在太极平台使用，目前Venus平台的Angel图计算也已经上线可以使用，大约包含5类共计约40个图算法组件；具体的使用说明在KM上有诸多文章在此便不再赘述[8]；</p>
<p>在实际的使用过程中，发现一个主要的瓶颈是在性能上：我们构建了一个测试样例，测试样例包含百万级别结点，亿级别边；在测试样例上训练二度HGAT网络，使用单机和Angel的耗时大体如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/278a339401d430baed9d.png"/></p>
<p>在仔细分析原因的时候，还是发现了一些问题：</p>
<p>1. 不同集群性能差别非常大：在实际使用过程中，我们使用Angel 图计算进行预测，在完全相同的配置之下，使用 Common集群进行预测，耗时大约在30min左右，而使用天鹰集群进行预测，耗时则在6min左右；定位的时候发现，一是不同的集群在Spark数据本地化级别上有较大差异，导致不同集群在数据读取上就有所不同，二是发现不同的集群的结点稳定性有较大差异，在 Common集群上结点会频繁出现结点挂掉的情况导致耗时被大幅度拉长。<br/>2. 图计算场景是一个内存开销大，而计算开销相对小的场景，因此Angel偏向于使用"少量有大内存"的机器结点；venus平台因为历史原因，也基于避免资源浪费的考虑，结点内存被限制在16G以下，图场景由于点分割需要额外复制点信息，因此小内存、多结点并不适用于该场景，会频繁的出现OOM的问题；最近venus已经在尝试解除这个限制，相信解除该限制后，Angel在Venus平台上的可用性会再上一个台阶。<br/>3. Angel图计算更多的是为了处理一个通用图计算场景，而对于一些定制化的端到端的需求，暂时无法很好的满足。比如说在我们的场景中，原始特征在进入到图神经网络之前，还有一层TextCNN用于提取文本信息并融入到图神经网络中，这些需求就暂时没法得到很好的满足。<br/>4. Angel的最终性能对于参数的设置非常敏感，不同参数的性能设置常常有好几倍的性能差距，无形中就提高了学习的成本，建议大家在使用的时候还是要好好了解一下Angel的参数设置文档。[9]</p>
<p><br/></p>
<p>总的来说，Angel提供了一个海量数据下进行图计算的通用框架，里面包含大量通用的图神经网络算法可以用来快速部署；而且Angel的同事对于使用框架中出现的问题响应速度比较快，有问题也能够较快的得到反馈并较好的解决；但是由于内存限制，最终我们还是选择基于DGL框架来落地如上的图神经网络算法。</p>
<p><br/></p>
<h2>DGL图计算框架</h2>
<p>DGL框架（Deep Graph Library)是由的DMLC团队开放出来的图神经网络通用框架[10]，里面提供了大量图神经网络的标准实现，并且从众多横向评测的文章来看，DGL在性能和内存开销上也有着一定的优势，尤其是对于异构图有着良好的支持。</p>
<p>虽然DGL框架最新版本已经开始尝试支持分布式场景，但是一方面分布式部署还不太成熟，仍旧有诸多BUG；一方面分布式部署依赖一些外部模块（比如说分图模块），外部模块对于大规模数据的处理支持有限，因此还不太建议使用DGL在分布式场景下去使用。</p>
<p>在我们的业务场景中，训练集样本量大概在十万级，即使加上一度、二度结点的点量级大约也在千万级，边大约在亿级；在特征并不是特别复杂的情况下，单台普通机器的内存便足以存下这个训练图。因此训练在单台机器上便可以完成；在此便不做赘述。</p>
<p>预测场景则相对而言比较复杂，需要涉及到百亿级别边，十亿级别的点的图的存储，显然单台机器是无法存下这么大的一张图的，因此需要对整张图进行切分，将其切割成若干个小的子图；然后逐个子图加载到内存中执行预测，从而完成全图的预测；这里使用Spark/Hive来做图的邻居查找，因此图网络的度数不能超过2度，大于2度的时候使用Spark/Hive来做邻居查找的计算量就会变得非常巨大。大体流程可以分成5步：</p>
<ol><li>
<p><strong>查找关系</strong>：将user_id用哈希分组，分组的数量由单机能容纳的子图大小决定；使用Spark/Hive查找出user的一度、二度邻居和连边，保存到HDFS上。</p>
</li>
<li>
<p><strong>提取特征</strong>：将user_id的一度、二度邻居结点的特征提取出来，保存到HDFS上。建议在提取特征的时候预先进行特征填充和部分特征预处理操作。</p>
</li>
<li>
<p><strong>构图</strong>：将数据分子图拉取到本地，使用networkX或者DGL Graph将结点特征、结点连接关系构成一个完整的图。</p>
</li>
<li>
<p><strong>预测</strong>：在本地上分批次执行预测操作后将预测结果推回HDFS上。</p>
</li>
<li>
<p><strong>后处理</strong>：删除缓存数据，对数据输出的格式进行处理。</p>
</li>
</ol><p><img alt="" loading="lazy" src="/logbook/images/recommendation/18b15d6ae934a1851894.png"/></p>
<p>这个过程中，第1、2、5步都是在Spark/Hive上进行的，因为Spark/Hive本身就可以用来进行大数据处理的工具，因此这个流程并没有太多问题；只是在二度的结点查找上耗时会略长，如果有专门的分布式图计算框架用来进行二度结点查找可能会更好。主要性能瓶颈还是在单机处理的第3、4步中，下面是在实施落地中可能需要的问题和要注意的一些点：</p>
<p><strong>构图步骤</strong></p>
<p>1. 数据预处理的程度需要权衡，建议数据填充可以由Spark完成，而一些增加特征列的操作（比如OneHot、特征交叉）等操作应该在该步骤完成，因为增加特征列的操作将大大增加下载的数据量，从而导致I/O瓶颈。<br/>2. 数据从HDFS上拉取到本地刚好是多个gz文件，因此可以直接并发读取后合并，可以较大程度降低读取的耗时。<br/>3. 构图步骤主要瓶颈是在内存上，使用multiprocessing来并发增加CPU利用率并不是一个好的方案，使用Queue、共享内存都并不能很好的解决问题；还有内存泄漏的风险，慎用慎用。<br/>4. 构图过程中有大量临时数据和中间结果，这些数据建议直接存储在本地的临时硬盘上，而只把最终的子图bin文件写入到CephFS/CFS中；从而尽可能降低CephFS/CFS的网络I/O，从而提升性能。</p>
<p><strong>预测步骤</strong></p>
<p>1. 预测流程因为不涉及太多数据处理，内存不构成瓶颈，因此可以通过增加CPU核数和并发来增加预测效率；同时使用DataLoader对数据进行预加载，虽然会造成额外的内存开销，但是对于加速预测有较大帮助。<br/>2. 如果有GPU资源可以切换到GPU上加速，实测GPU的推理性能大约是CPU推理的10倍以上；但要注意GPU使用率的问题。<br/>3. 使用Bore组件推回HDFS时，将有可能遇到推送失败的情况，建议增加重试，如果失败就缓存到CFS/CephFS上，交由后续结点再集中上推；推回HDFS建议使用子进程或者子线程来完成，避免CPU/GPU陷入等待而降低了效率。</p>
<p><br/></p>
<p>在金融风控的实际业务场景中，训练集包含十万级别用户，近千万级别边；训练流程大体耗时如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/aa794778f18dde556830.png"/></p>
<p>备注：以上训练步骤耗时是使用GPU进行训练耗时。</p>
<p><br/></p>
<p>预测场景中大约包含十亿级别用户以及百亿级别边，整个流程大约耗时在24h左右，因为特征更新频率是按月，因此即使运行时长差不多需要24h在当前场景下也是完全可以接受的；在此基础上，我们对部分构图流程进行优化，主要包括将数据预处理前推到”提取特征步骤”，将数据读取、HDFS数据拉取流程改成并发，分成多个结点提高磁盘I/O吞吐上限等方式，最终整个流程耗时约18小时。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommendation/4549f1dfb01d032583ce.png"/></p>
<p>备注：</p>
<p>1. 构图步骤：(15 core+50G内存) * 6，运行CPU使用率50%+，内存80%左右；预测使用(30 core/30G内存) * 6，CPU使用率99%+，内存占用80%+。<br/>2. 此处预测耗时是使用CPU进行计算的耗时，如果切换到GPU上运行，预测耗时大约可以控制在3h左右。</p>
<p><br/></p>
<h1>5.总结</h1>
<p>本文主要讨论金融反欺诈场景中的图嵌入算法以及图神经网络的使用，图嵌入算法由"拓扑驱动"，生成的Embedding主要是对结点拓扑连接关系的一个编码，在实际场景中效果较为一般；而图神经网络由"特征驱动"，当图上的各个结点包含特征的时候，生成的Embedding包含了相邻结点的相互关系，生成的Embedding能够较为良好的表征用户的特征；同时，结合金融反欺诈场景业务特征，我们对图神经网络算法的各个模块进行了微调，最终相比于baseline模型在最终效果上提升了约17%。</p>
<p>而后，我们在十亿级别点，百亿级别边的数据上进行了部署落地，由于内存限制和定制化的原因我们没有能够使用Angel图计算框架，于是最终采用了Spark/Hive进行分图+数据预处理，使用Bore镜像构图并预测的方案；该方案能够很好的满足业务场景的需求，并且在经过优化后，全流程耗时能够控制在18.5h左右；如果能够使用GPU，耗时还能够被进一步缩短。</p>
<p><br/></p>
<h1>参考文献</h1>
<p>[1] Perozzi, Bryan, Rami Al-Rfou, and Steven Skiena. "Deepwalk: Online learning of social representations." Proceedings of the 20th ACM SIGKDD international conference on Knowledge discovery and data mining. 2014.</p>
<p>[2] Tang, Jian, et al. "Line: Large-scale information network embedding." Proceedings of the 24th international conference on world wide web. 2015.</p>
<p>[3] Grover, Aditya, and Jure Leskovec. "node2vec: Scalable feature learning for networks." Proceedings of the 22nd ACM SIGKDD international conference on Knowledge discovery and data mining. 2016.</p>
<p>[4]  <a href="https://zhuanlan.zhihu.com/p/64756917">关于Node2vec算法中Graph Embedding同质性和结构性的讨论</a></p>
<p>[5] Hamilton, Will, Zhitao Ying, and Jure Leskovec. "Inductive representation learning on large graphs." Advances in neural information processing systems 30 (2017).</p>
<p>[6] Veličković, Petar, et al. "Graph attention networks." arXiv preprint arXiv:1710.10903 (2017).</p>
<p>[7] <a href="https://github.com/Angel-ML/angel">Angel分布式机器学习和图计算平台</a></p>
<p>[8] Angel Graph on Venus机器学习平台</p>
<p>[9] Angel算法参数配置和性能数据</p>
<p>[10] <a href="https://github.com/dmlc/dgl/">DGL框架</a></p>
<p><br/></p>
<p>--</p> 
{% endraw %}
