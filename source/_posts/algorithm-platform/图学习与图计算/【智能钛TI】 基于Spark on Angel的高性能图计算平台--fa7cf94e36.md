---
title: "【智能钛TI】 基于Spark on Angel的高性能图计算平台"
date: 2022-04-15 10:01:41
categories:
  - 算法平台
  - 图学习与内容理解
---

{% raw %}

<h2>1 图计算平台面临的问题</h2><p>为了支撑公司内部各个业务线对于图计算的需求，在算法平台构建方面需要解决如下几个问题</p>
<ul>
<li>提供节点测度、社区发现和图表示学习等多种算法的高效实现</li><li>支撑十亿节点和百亿边（千亿边）的数据规模</li><li>支持节点稀疏编码，避免额外的编码步骤</li><li>支持端到端处理，避免额外的数据预处理步骤</li><li>高效的容错机制，保证任务在集群环境可稳定运行</li><li>资源可伸缩，不能受到资源环境的限制而导致任务性能下降或者不能运行</li></ul>
<p>算法层次和数据规模是大规模图计算平台的通用难题，公司内部的业务需求和数据量使得一个图计算平台必须解决这两个问题。除此之外，一个成熟的图计算平台还需要满足支持节点稀疏编码、端到端训练、容错和资源可伸缩等要求，才能在实际应用中更方便用户的使用。</p>
<p><strong>节点稀疏编码：</strong>现有的大多数图计算平台都假设节点的ID是从0开始连续编码的，因为这样可以方便处理并且使得存储空间可以连续访问。然而实际的图数据则并非如此，比如qq的uid从10001开始，最大在40亿左右；某些图的节点ID则是通过哈希函数生成，覆盖整个长整型空间。由于图数据是动态变化的，让每一份图数据在运行任务前都进行一次节点重编码，对用户来说是增加了不少的维护成本。</p>
<p><strong>端到端处理：</strong>端到端处理则表示说不需要用户有额外的预处理步骤，用户的输入是一个HDFS目录或者TDW表，系统的输出也是一个HDFS目录或者TDW表，形成一个闭环。一些图计算平台往往要求用户将数据处理成特定的格式，手动划分到各个运行节点等等，这给用户也带来了不少额外的开销。</p>
<p><strong>容错与资源：</strong>在大集群运行任务，容错是一个必备的技能，并且容错还不能太影响性能。此外。由于大集群的资源限制，图计算平台需要支持可弹性伸缩的资源配置，对单个计算节点的内存和CPU不能有太高限制，否则可能会申请不到资源或者影响性能。</p>
<h2>2 Spark on Angel图计算架构</h2><p>为了应对上述的六个难题，我们基于Spark on Angel系统开发了一个图计算平台。Spark on Angel将Angel灵活的参数服务器<strong>插件式</strong>地赋能到了原生Spark之上，为Spark提供高效的数据存储/更新/共享服务，因而天生地非常适合用作分布式图计算的框架；同时，Spark on Angel又沿用了原生Spark的编程接口，使得在其上的算法开发可以利用Spark的能力。</p>
<p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/819143eef61656108f70.png"/><br/><div> [ Figure 1. Spark on Angel图计算架构 ]</div></div><p></p>
<p><strong>系统架构：</strong>如图1所示，Spark on Angel图计算模块的系统架构由Spark组件和Angel组件构成：</p>
<p><strong>Spark组件</strong></p>
<ul>
<li>Spark Driver：负责控制整体计算逻辑；</li><li>Spark Executor：存储图邻接表/边表等不可变数据，在每轮迭代中从PS拉取（pull）所需的节点属性等数据，在本地完成处理和计算，并将结果推送（push）回PS，交由PS进行更新；</li></ul>
<p><strong>Angel组件</strong></p>
<ul>
<li>Angel Master：管理参数服务器的生命周期；</li><li>Angel PS (Parameter Server)：将节点属性等可变数据以向量的抽象形式储存（<strong>支持存储自定义的元素数据结构，支持负载均衡分区</strong>），通过Angel特有的PS函数实现节点属性in-place更新及其他根据特定算法定制的灵活计算；</li><li>Angel Agent：作为代理桥接Spark Executor和Parameter Server。</li></ul>
<p><strong>系统特点与优势：</strong>基于Spark on Angel的图计算平台有如下优势：</p>
<ul>
<li>高扩展性：Angel的参数服务器可以水平扩展，存储十亿甚至百亿规模的参数；Spark则可以处理TB级别的数据。同时二者均可以运行于大集群之中，不会受到资源申请的限制。</li><li>端到端处理：Spark提供了ETL数据处理能力，读写TDW/HDFS的能力</li><li>支持稀疏数据：Angel的参数服务器为高维稀疏模型而设计，可以支持图节点的稀疏编码</li><li>高容错：Spark自带了容错能力，Angel的参数服务器也具备状态恢复能力</li><li>算法支持：Angel目前提供了包括节点测度，社区发现和图表示学习等多种丰富的算法</li></ul>
<p>结合Spark on Angel的系统特点与优势，通过在其上实现高效的图算法，则可以解决公司内部对于图计算平台的需求。在本篇文章的后续内容中，我们主要介绍网络节点测度算法在Spark on Angel上的实现细节。后续会有其它文章介绍社区发现和图表示学习算法的相关内容。</p>
<p>目前Spark on Angel平台支持了不少图算法，并上线到智能钛(Tesla)平台，想试用可以参考样例Demo。</p>
<h4>智能钛Demo工程样例</h4><ul>
<li>PageRank</li><li>Kcore</li><li>Closeness</li><li>Common Friends</li><li>Triangle Count</li><li>LINE</li><li>GraphSage Supervised</li><li>Deep Graph Infomax</li><li>Relational GCN</li></ul>
<h2>3 网络节点测度算法</h2><p>在一个网络中，不同的节点会有不同的结构性作用，如在社交网络中某些节点（用户）扮演着意见领袖的角色，而某些则是小透明和僵尸粉。在处理业务问题时，我们常常希望挖掘出网络中比较重要的节点对其进行重点分析，图计算领域中的节点测度算法便是为解决这类需求而生的。</p>
<p>目前主流的节点测度算法可按照出发点分为1）网络拓扑结构，以及2）网络动力学两类，前者包括常见的中心度算法，如degree centrality（点度中心度）、closeness centrality（紧密中心度）、betweenness centrality（介数中心度），以及K-Core等，后者则包括大名鼎鼎的PageRank。</p>
<p>我们在本篇文章中对PageRank、K-Core和Closeness做一下简单介绍。这三个算法用得比较多，而betweenness目前计算还是太困难，或者精度太低。</p>
<h3>3.1 PageRank</h3><p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/322896c2e61bcfbd54d5.png"/><br/><div> [ Figure 2. PageRank示例 ]</div></div><p></p>
<p>PageRank[^1]可能是最出名的节点测度算法，由Larry Page大神于1998年提出，被用来对网页搜索结果进行重要性排名，可以说是现代搜索引擎的基石。图2[^2]给出了PageRank在一个小网络中的示例。PageRank的核心思想是<strong>一个节点（网页）的重要性取决于指向它的其他节点（网页）的数量及重要性</strong>。</p>
<p>该算法首先给每一个节点赋一个初始PageRank值（一般会是1÷网络中总节点个数），接下来在每一轮迭代中对网络中的节点做如下运算，直到所有节点的PageRank值收敛：</p>
<p><nobr>PageRank(pi;t+1)=α∑pj∈I(pi)PageRank(pj;t)dj+1−αN(1)</nobr><math><mtable displaystyle="false"><mlabeledtr><mtd><mtext>(1)</mtext></mtd><mtd><mtext>PageRank</mtext><mo>(</mo><msub><mi>p</mi><mi>i</mi></msub><mo>;</mo><mi>t</mi><mo>+</mo><mn>1</mn><mo>)</mo><mo>=</mo><mi>α</mi><munder><mo>∑</mo><mrow><msub><mi>p</mi><mi>j</mi></msub><mo>∈</mo><mi>I</mi><mo>(</mo><msub><mi>p</mi><mi>i</mi></msub><mo>)</mo></mrow></munder><mstyle displaystyle="true"><mfrac><mrow><mtext>PageRank</mtext><mo>(</mo><msub><mi>p</mi><mi>j</mi></msub><mo>;</mo><mi>t</mi><mo>)</mo></mrow><msub><mi>d</mi><mi>j</mi></msub></mfrac></mstyle><mo>+</mo><mstyle displaystyle="true"><mfrac><mrow><mn>1</mn><mo>−</mo><mi>α</mi></mrow><mi>N</mi></mfrac></mstyle></mtd></mlabeledtr></mtable></math></p>
<p>其中<nobr>PageRank(pi;t+1)</nobr><math><mtext>PageRank</mtext><mo>(</mo><msub><mi>p</mi><mi>i</mi></msub><mo>;</mo><mi>t</mi><mo>+</mo><mn>1</mn><mo>)</mo></math>代表节点<nobr>pi</nobr><math><msub><mi>p</mi><mi>i</mi></msub></math>在第<nobr>t+1</nobr><math><mi>t</mi><mo>+</mo><mn>1</mn></math>轮迭代后的PageRank值，<nobr>α</nobr><math><mi>α</mi></math>为一个修正因子（一般取0.85），<nobr>I(pi)</nobr><math><mi>I</mi><mo>(</mo><msub><mi>p</mi><mi>i</mi></msub><mo>)</mo></math>为指向该节点的所有其他节点的集合，<nobr>dj</nobr><math><msub><mi>d</mi><mi>j</mi></msub></math>为节点<nobr>pj</nobr><math><msub><mi>p</mi><mi>j</mi></msub></math>的出度（以它为起点的边的个数，在有权图中则为边的权重之和），<nobr>N</nobr><math><mi>N</mi></math>为网络中的节点个数。</p>
<p>通过公式可以看出，PageRank的计算逻辑其实就是一个Markov过程，可以通过随机冲浪者模型来解释：假设有一个冲浪者在网上冲浪，在每一个时刻（i.e.每一轮迭代），该冲浪者都停留在某个网页上，并且须从下述两个选择中选取一个作为下一时刻的行动：</p>
<ol>
<li>从该网页所指向的其他站点中随机选择一个，并跳转过去；</li><li>离开该网页，从互联网所有页面中挑选一个并跳转。</li></ol>
<p>其中选取第一个选项的概率就是上面提到的修正因子<nobr>α</nobr><math><mi>α</mi></math>。让冲浪者不断重复上述动作，其停留在每一个页面的频率/概率会趋于稳定，这个收敛后的值就是网页的PageRank值。</p>
<h3>3.2 Closeness</h3><p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/481241f6f702348cba03.png"/><br/><div> [ Closeness中心度示例 ]</div></div><p></p>
<p>Closeness centrality，顾名思义， 衡量的是节点到网络中其他节点的紧密程度。如图4[^2]所示，一个节点若离其他节点距离都较近，则它会具有更高的紧密中心度。closeness的计算公式非常简洁明了：</p>
<p><nobr>closenessv=N−1∑u≠vd(u,v)(2)</nobr><math><mtable displaystyle="false"><mlabeledtr><mtd><mtext>(2)</mtext></mtd><mtd><msub><mtext>closeness</mtext><mi>v</mi></msub><mo>=</mo><mstyle displaystyle="true"><mfrac><mrow><mi>N</mi><mo>−</mo><mn>1</mn></mrow><mrow><munder><mo>∑</mo><mrow><mi>u</mi><mo>≠</mo><mi>v</mi></mrow></munder><mi>d</mi><mo>(</mo><mi>u</mi><mo>,</mo><mi>v</mi><mo>)</mo></mrow></mfrac></mstyle></mtd></mlabeledtr></mtable></math></p>
<p>其中<nobr>N</nobr><math><mi>N</mi></math>为网络中的总节点个数，<nobr>d(u,v)</nobr><math><mi>d</mi><mo>(</mo><mi>u</mi><mo>,</mo><mi>v</mi><mo>)</mo></math>代表节点<nobr>u</nobr><math><mi>u</mi></math>和<nobr>v</nobr><math><mi>v</mi></math>之间的最短路径。虽然公式看上去特别简单，但算法的时间复杂度高达<nobr>(n3)</nobr><math><mrow><mi mathvariant="script">O</mi></mrow><mo>(</mo><msup><mi>n</mi><mn>3</mn></msup><mo>)</mo></math>，且分布式的单源最短路径（SSSP）求解涉及BFS（宽度优先搜索），并发起来也非常地空间不友好，因此在亿级网络中高效且精确地测算所有结点的closeness基本上是一件mission impossible。</p>
<p>为了解决大规模网络上的closeness计算问题，学界提出了各种各样的近似算法。经仔细调研后，我们选择采用Kang et al.[^3]提出的Effective Closeness作为具体的实现算法，该算法的核心思想是<strong>使用基数估计算法来近似统计每个节点distinct的邻居节点个数</strong>。论文中使用的基数估计算法是Flajolet-Martin，而在具体实现中我们采用了Flajolet-Martin进化进化再进化后的<strong>HyperLogLog++</strong>计数器（HyperLogLog的原理可参考<a href="http://www.rainybowe.com/blog/2017/07/13/%E7%A5%9E%E5%A5%87%E7%9A%84HyperLogLog%E7%AE%97%E6%B3%95/index.html">《神奇的HyperLogLog算法》</a>)。为什么求解最短路径问题会涉及基数估计？让我们从上面的公式说起。</p>
<p>当一个图是无权图，也即其中的每一条边权重都为1时，我们可以将公式2做如下变形：</p>
<p><nobr>closenessv=N−1∑u≠vd(u,v)=N−1∑dr=1r⋅Nv(r)(3)</nobr><math><mtable displaystyle="false"><mlabeledtr><mtd><mtext>(3)</mtext></mtd><mtd><msub><mtext>closeness</mtext><mi>v</mi></msub><mo>=</mo><mstyle displaystyle="true"><mfrac><mrow><mi>N</mi><mo>−</mo><mn>1</mn></mrow><mrow><munder><mo>∑</mo><mrow><mi>u</mi><mo>≠</mo><mi>v</mi></mrow></munder><mi>d</mi><mo>(</mo><mi>u</mi><mo>,</mo><mi>v</mi><mo>)</mo></mrow></mfrac></mstyle><mo>=</mo><mstyle displaystyle="true"><mfrac><mrow><mi>N</mi><mo>−</mo><mn>1</mn></mrow><mrow><munderover><mo>∑</mo><mrow><mi>r</mi><mo>=</mo><mn>1</mn></mrow><mi>d</mi></munderover><mi>r</mi><mo>⋅</mo><msub><mi>N</mi><mi>v</mi></msub><mo>(</mo><mi>r</mi><mo>)</mo></mrow></mfrac></mstyle></mtd></mlabeledtr></mtable></math> </p>
<p>其中<nobr>d</nobr><math><mi>d</mi></math>代表图的最大直径，<nobr>Nv(r)</nobr><math><msub><mi>N</mi><mi>v</mi></msub><mo>(</mo><mi>r</mi><mo>)</mo></math>代表网络中距离节点<nobr>v</nobr><math><mi>v</mi></math>的最短路径等于<nobr>r</nobr><math><mi>r</mi></math>的节点个数，也即<nobr>Nv(r)=∣u:d(u,v)=r∣</nobr><math><msub><mi>N</mi><mi>v</mi></msub><mo>(</mo><mi>r</mi><mo>)</mo><mo>=∣</mo><mrow><mi>u</mi><mo>:</mo><mi>d</mi><mo>(</mo><mi>u</mi><mo>,</mo><mi>v</mi><mo>)</mo><mo>=</mo><mi>r</mi></mrow><mo>∣</mo></math>。这样看起来计数器就派上用场了。然而在此之前，我们还需要对上式的分母部分做进一步变形：</p>
<p><nobr>∑dr=1r⋅Nv(r)=∑dr=1r⋅(N(r,v)−N(r−1,v))(4)</nobr><math><mtable displaystyle="false"><mlabeledtr><mtd><mtext>(4)</mtext></mtd><mtd><munderover><mo>∑</mo><mrow><mi>r</mi><mo>=</mo><mn>1</mn></mrow><mi>d</mi></munderover><mi>r</mi><mo>⋅</mo><msub><mi>N</mi><mi>v</mi></msub><mo>(</mo><mi>r</mi><mo>)</mo><mo>=</mo><munderover><mo>∑</mo><mrow><mi>r</mi><mo>=</mo><mn>1</mn></mrow><mi>d</mi></munderover><mi>r</mi><mo>⋅</mo><mo>(</mo><mi>N</mi><mo>(</mo><mi>r</mi><mo>,</mo><mi>v</mi><mo>)</mo><mo>−</mo><mi>N</mi><mo>(</mo><mi>r</mi><mo>−</mo><mn>1</mn><mo>,</mo><mi>v</mi><mo>)</mo><mo>)</mo></mtd></mlabeledtr></mtable></math></p>
<p>其中<nobr>N(r,v)</nobr><math><mi>N</mi><mo>(</mo><mi>r</mi><mo>,</mo><mi>v</mi><mo>)</mo></math>代表网络中距离节点<nobr>v</nobr><math><mi>v</mi></math>的最短路径小于等于<nobr>r</nobr><math><mi>r</mi></math>的所有节点个数，也即<nobr>Nv(r)=∣u:d(u,v)≤r∣</nobr><math><msub><mi>N</mi><mi>v</mi></msub><mo>(</mo><mi>r</mi><mo>)</mo><mo>=∣</mo><mrow><mi>u</mi><mo>:</mo><mi>d</mi><mo>(</mo><mi>u</mi><mo>,</mo><mi>v</mi><mo>)</mo><mo>≤</mo><mi>r</mi></mrow><mo>∣</mo></math>。这下问题就非常明晰了：</p>
<p>求解Effective Closeness，其实就是为每一个节点设一个储存不重复邻居节点的计数器，并逐层向外扩散，加权统计在每一层能接触到的新的邻居节点个数。在每一轮迭代中，节点会向所有邻居发送自己的计数器，分享距自己<nobr>SSSP≤r</nobr><math><mtext>SSSP</mtext><mo>≤</mo><mi>r</mi></math>的节点（也即距邻居<nobr>SSSP≤r+1</nobr><math><mtext>SSSP</mtext><mo>≤</mo><mi>r</mi><mo>+</mo><mn>1</mn></math>的节点），从而实现不断的更新。</p>
<p>举个栗子，假设有如下的有向图（无向图的closeness计算可视为双向流动的有向图计算）：</p>
<p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/1d431d7889444118db56.png"/><br/><div> [ Figure 5. Effective Closeness计算示例图 ]</div></div><p></p>
<p>在迭代开始时，每个节点的计数器均只包含其自身。在第一轮迭代中，节点1接收到了来自节点2、3、4的计数器，2接收到3和6的，3接收到5的，5接收到7的，因此第一轮迭代结束后各节点拥有的<nobr>r≤1</nobr><math><mi>r</mi><mo>≤</mo><mn>1</mn></math>邻居节点如下：</p>
<p><strong>1</strong>: [1,2,3,4]; <strong>2</strong>:[2,3,6]; <strong>3</strong>:[3,5]; <strong>4</strong>:[4]; <strong>5</strong>:[5,7]; <strong>6</strong>:[6]; <strong>7</strong>:[7]</p>
<p>类似地，经过第二轮邻居节点传递后：</p>
<p><strong>1</strong>: [1,2,3,4,5,6]; <strong>2</strong>:[2,3,5,6]; <strong>3</strong>:[3,5,7]; 其余节点不变</p>
<p>由此扩散至所有节点的计数器均不再更新（也即到达图的直径），则停止迭代。在迭代过程中不断计算每个节点当前轮数获得的新的邻居节点个数，便可求出closeness。实际上，我们不需要在每一轮都对所有链路进行计数器传递，当一个节点在上一轮迭代后已经没有新的邻居节点（也即计数器保持不变），该节点便可被标为inactive，在往后的迭代中便不需要再向下游节点分享它的计数器了。</p>
<h3>3.3 K-Core</h3><p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/b0fe4f97aaefa824bb3a.png"/><br/><div> [ K-Core示例 ]</div></div><p></p>
<p>K-Core算法用于分离提取网络中紧密连接的子图。在一个k-core子图中，任一节点均有<nobr>≥k</nobr><math><mo>≥</mo><mi>k</mi></math>个同在该子图中的邻居节点。如图8所示，图中黄色节点组成一个k=4的子图，其中每个节点都有至少4个黄色的邻居节点；同时，黄色节点也存在于k=3、k=2…的子图中。一个节点所能拥有的最大k值就是它的<strong>coreness</strong>， 可以看出coreness也能用于衡量一个节点在网络中的重要性。</p>
<p>K-Core算法的最直观解释是<strong>剥洋葱</strong>：首先将网络中degree（邻居节点数）为1的节点剥离，由此会在网络中产生一些新的degree=1的节点，并再次将它们剥离，如此往复直至网络中所有剩余的节点degree均≥2，那么此前所剥离的节点coreness即为1；重复上述迭代，直至所有节点均获得对应的coreness。</p>
<p>显然，上述朴素解法并不适用于在大规模数据上分布式运行的场景。通过调研，我们选用了Montresor et al. (2012)[^4]提出的分布式K-Core解法。其核心思想是<strong>一个节点的coreness等于它可以取到的k的最大值，使得该节点至少有k个属于k’-core (k’≥k)的邻居节点（其实也就是其邻居节点coreness值的<a href="https://stackoverflow.com/questions/20139640/looking-for-algorithm-to-calculate-h-index-fast">h-index</a>）</strong>，可以证明这与上述的朴素K-Core解法是等价的，具体证明可参考论文。这个等价概念传达了一个非常好的信息：<strong>一个节点的coreness完全可以根据它邻居节点的coreness计算出来</strong>，这就非常契合分布式图计算的逻辑了。</p>
<p>具体的分布式K-Core算法如下。图中每个节点都持有三个变量：1）<code>core</code>：该节点当前的coreness估计值，初始值为该节点的degree；2）<code>est[]</code>：该节点邻居节点的最新coreness估计值，以及3）<code>changed</code>：记录该节点在上一轮是否更新过<code>core</code>的flag。在每一轮迭代中：</p>
<ol>
<li>在上一轮迭代中更新过<code>core</code>的节点向自己的邻居广播其新的<code>core</code>值（第一轮迭代所有节点均进行广播）；同时每个节点接收来自邻居节点的新的<code>core</code>值，并储存在<code>est[]</code>数组中对应该邻居节点的位置；</li><li>用计算h-index的方法，根据<code>est[]</code>计算出该节点新的coreness估计值（符合“<code>est[]</code>中有至少h个数大于等于h”条件的最大h值）。如果新的估计值小于旧估计值，则记该节点为在这一轮更新过。</li></ol>
<p>如此迭代直至没有节点更新coreness估计值即为收敛。</p>
<p>还是举个栗子，假设我们有如下的无向图：<br/></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/9af4dc34e7b848c51184.png"/><br/><div> [ Figure 9. K-Core计算示例图 ]</div></div><p></p>
<p>在第一轮，每个节点的coreness估计值均为它的degree。节点2、3、4、5将core=3分享给它们的邻居，节点1和6则将core=1分享给邻居节点。如此一来，每个节点的<code>core</code>和<code>est[]</code>如下所示：<br/></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/4c53fcfe858d9da52f99.png"/><br/><div> [ 第一轮迭代 ]</div></div><p></p>
<p>因此，节点1、3、4、6的coreness估计值不变，依旧为其degree；而节点2和5的新的coreness估计值则降为2（[1,3,3]中有2个元素≥2）。在下一轮迭代中，节点2和5向邻居发送新的core=2，其他节点不发送信息，则该轮迭代每个节点的<code>est[]</code>为：<br/></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/d51815e4cf7be0b5f01d.png"/><br/><div> [ 第二轮迭代 ]</div></div><p></p>
<p>节点3、4的coreness估计值在这一轮也降为2，并在下一轮向邻居节点发送更新。第三轮迭代过后，每个节点的<code>est[]</code>如下：<br/></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/16ac5e0c67d23662d531.png"/><br/><div> [ 第三轮迭代 ]</div></div><p></p>
<p>现在已经没有节点能够更新一个更低的coreness估计值了，也即算法收敛，最后可得出节点1和6的coreness=1，其余节点coreness=2。</p>
<h2>4 算法实现</h2><p>在Spark on Angel上实现节点测度算法需要解决两个问题：</p>
<ul>
<li>哪些数据放在Angel-PS上存储，哪些数据放在Spark Executor上存储？</li><li>如何利用节点测度算法的迭代稀疏性加快迭代速度？</li></ul>
<p>我们带着这两个问题去解释三个测度算法在Spark on Angel上实现的具体细节。</p>
<h4>4.1 PageRank在Spark on Angel上的实现</h4><p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/af1375b720bedaf14d7a.png"/><br/><div> [ Figure 3. Spark on Angel的PageRank实现原理 ]</div></div><p></p>
<p>为了利用迭代算法的稀疏性，我们在Spark on Angel上实现GraphX采用的增量版本—PageRank-Delta。由于不同节点的PageRank值收敛所需迭代轮数不同，采用增量版本可以对提前收敛的节点采用早停策略，缩短算法整体收敛时间，加快收敛速度。</p>
<p>从存储架构上来看，Spark Executor存储每个子图（graph partition）的邻接表，Angel参数服务器上存储三个向量：迭代至当前轮数的每个节点的PageRank值，节点在上一轮迭代中获得的PageRank增量<nobr>δt−1</nobr><math><msub><mi>δ</mi><mrow><mi>t</mi><mo>−</mo><mn>1</mn></mrow></msub></math> （记为<code>reader</code>），以及节点在当前迭代中接收到的增量<nobr>δt</nobr><math><msub><mi>δ</mi><mi>t</mi></msub></math>（记为<code>writer</code>）。在一轮迭代中，</p>
<ol>
<li>每个Executor从PS端<code>reader</code>拉取该partition中所有上游节点的PageRank增量<nobr>δ</nobr><math><mi>δ</mi></math>；</li><li>Executor在本地过滤掉已经收敛（上一轮增量小于指定阈值）的节点，将剩下的活跃节点的增量按照上述公式传递给下游邻居；</li><li>Executor将邻居节点在该partition中所接收到的总增量推送添加给PS的<code>writer</code> <nobr>δ</nobr><math><mi>δ</mi></math>向量；</li><li>在所有Executor完成计算后，PS端将该轮所有节点所获得的总增量累加到PageRank向量中；</li><li>将<code>writer</code>设为下一轮新的<code>reader</code>，重置<code>writer</code>，完成一轮迭代。</li></ol>
<p>这里给出在Spark上Driver端和Executor端的代码示例。</p>
<p><strong>Driver</strong>端</p>
<pre>do {
      // graph: RDD[PageRankGraphPartition]
      graph.map(_.process(model, $(resetProb), $(tol)).reduce(_ + _) // Executor并行完成增量传递计算
      model.computeRanks(initRank, $(resetProb)) // 在PS端更新PageRank值
      numMsgs = model.numMsgs()
      numIterations += 1
    } while (numMsgs &gt; 0)
</pre>
<p><strong>Executor端</strong></p>
<pre>class PageRankGraphPartition extends Serializable {
  ...
  def process(model: PageRankPSModel, resetProb: Float, tol: Float): Int = {
    val outMsgs = new Long2FloatOpenHashMap()
    val inMsgs = model.readMsgs(keys) // 从PS拉取该graph partition对应节点的PageRank增量

    for (idx &lt;- srcs.indices) {
      val delta = inMsgs.get(srcs(idx)) * (1 - resetProb)
      if (delta &gt; tol) // 过滤已收敛节点
        outMsgs.addTo(dsts(idx), delta * weights(idx) / outDegrees(idx)) // 将增量传递给邻居节点
    }

    val update = VFactory.sparseLongKeyFloatVector(model.dim)
    update.setStorage(new LongFloatSparseVectorStorage(update.dim(), outMsgs))
    model.sendMsgs(update) // 将邻居节点在该partition接收的总增量推送至PS
    outMsgs.size()
  }
  ...
}
</pre>
<p>此外，我们还为PageRank做了一系列性能优化：</p>
<ul>
<li>支持边割（edge-cut）和点割（vertex-cut）两种图分割方式，适配不同量级数据；</li><li>在参数服务器端支持稀疏和稠密两种向量储存格式，二者之间可自动转化，从而支持更大规模（千亿边级）数据；</li><li>Spark端可以支持磁盘和内存混合使用，从而可以在资源允许的情况下尽量使用内存缓存加快运行速度。</li><li>可以根据节点的分布来自动划分参数服务器上的分区大小与分区数量，从而保证负载均衡</li></ul>
<h4>4.2 Closeness在Spark on Angel上的实现</h4><p>通过closeness的算法介绍，其计算其实也是对每个节点进行一个类似于增量的更新，因此实现逻辑也与PageRank非常相似，如下图所示：</p>
<p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/a5841ef8bfd638056ed0.png"/><br/><div> [ Figure 6. Spark on Angel的closeness实现架构 ]</div></div><p></p>
<p>我们知道在邻居传播的过程中，当一个节点的计数器本轮没有被任何邻居所更新，那么它以后也不会再被任何其它节点的计数器更新，因此我们可以将这个节点标记为inactive。在每轮迭代中，我们只需要访问活跃的节点，将其的计数器传播给他的邻居。随着迭代的进行，inactive的节点会越来越多，迭代速度也会越来越快。</p>
<p>从存储架构上来看，Spark Executor依旧存储每个子图（graph partition）的邻接表。在PS上则为每一个节点储存两个HyperLogLog++数据结构，其中一个对应上一轮迭代结束后的计数器（记为<code>reader</code>），一个对应该节点在当前正在进行的迭代中更新的计数器（记为<code>writer</code>）。</p>
<p>具体计算逻辑如下。在每一轮迭代中：</p>
<ol>
<li>Executor从PS上拉取活跃节点（上一轮迭代后计数器有更新的节点）的<code>reader</code> HLL++；</li><li>在每个graph partition中，节点将自己的计数器传递给下游邻居节点；</li><li>将每个下游邻居节点接收到的计数器聚合后push回PS，写入<code>writer</code>HLL++；</li><li>所有Executor结束步骤1~3的计算后，PS上每个节点的<code>writer</code> HLL++即是该轮迭代后的新的计数器。由此可以在PS端通过psFunc完成closeness计算公式分母部分（i.e. 公式4）的增量计算，并将<code>writer</code> merge到<code>reader</code>中，从而进入下一轮迭代。</li></ol>
<p>既然HyperLogLog++是一种基数估计算法，<strong>估算精度</strong>自然是个不可避免的问题，上面引用的原理介绍文章对HyperLogLog的精度概念有详细阐述。经测试发现，加大HyperLogLog++精度能够可观地提升closeness算法的结果稳定性以及准确性，尤其是对于大规模数据集而言；图7给出了在公开小数据集上用Angel运行不同精度的closeness结果与真实closeness的对比。Angel的closeness算法支持在提交任务时自定义计数器精度，我们建议用户在资源允许的情况下尽量增加精度，但一般来说超过10后便不会继续对结果有显著提升了。</p>
<p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/80cc8d5ed9a6df09dbb4.png"/><br/><div> [  Figure 7. 不同精度下Angel计算closeness的准确性 ]</div></div><p></p>
<h4>4.3 K-Core在Spark on Angel上的实现</h4><p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/6e6550bd0e325a1ef0d7.png"/><br/><div> [  Figure 10. Spark on Angel的K-Core实现架构 ]</div></div><p></p>
<p>从K-Core的算法描述中可以看出，计算一个节点的coreness值需要扫描其所有邻居的coreness值。如果我们将节点的coreness值存储在参数服务器上，在每轮迭代中，我们就需要将节点的所有邻居的coreness都从参数服务器拉取下来。为了利用迭代的稀疏性 （随着迭代的进行，大部分节点的coreness不会改变），我们将节点的coreness存储在Spark Executor端，在参数服务器端只存储变化的节点的coreness值。</p>
<p>在计算K-Core时需要储存与图中的<strong>边</strong>一一对应的<strong>可变</strong>数据（<code>est[][]</code>，每个节点的邻居的coreness估计值数组），我们将它与邻接表一起储存在Executor中。K-Core的具体实现架构如上图所示。PS端存储两个节点向量<code>reader</code>和<code>writer</code>，其中<code>reader</code>对应在上一轮迭代更新过的节点的coreness，<code>writer</code>对应这一轮迭代中正在更新的节点coreness；Executor端除了存储邻接表以外，还需存储子图每个节点及其邻居节点对应的coreness。具体计算流程如下：</p>
<ol>
<li>Executor从<code>reader</code>拉取<code>est[][]</code>中可更新的节点coreness，对其进行更新；</li><li>对Executor中的每个节点，计算其对应<code>est[]</code>的h-index，更新该节点的coreness估计值；</li><li>将经过步骤2更新了的coreness推送到<code>writer</code>上；</li><li>所有Executor结束步骤1-3的计算之后，PS端的<code>writer</code>即为下一轮的新的<code>reader</code>，同时将<code>writer</code>重置。</li></ol>
<p>Spark RDD本质上是不可变的，原则上来说每个graph partition RDD内部所存储的数据都不应当被修改；但在每一轮迭代中，<code>core[]</code>和<code>est[][]</code>两变量都有变化的可能。为了防止某些时候worker down掉重启时加载了上一次checkpoint储存在另一台机器的、内容已经是数次迭代之前的RDD，我们在每一轮迭代过后都需要<strong>重新建立新的graph partition RDD</strong>并persist到内存/磁盘上。如果存储级别是内存，则每轮不会有太多额外开销，因为并不会有新的对象生成；如果存储级别是磁盘，则每轮都需要将新的数据写入磁盘，则会有较大的开销。</p>
<p><strong>Driver端</strong></p>
<pre>do {
  curIteration += 1
  // graph: RDD[KCoreGraphPartition]
  graph = prev.map(_.process(model, numMsgs)) // 步骤1~3：进行一轮迭代计算，创建新的graph partition RDD
  graph.persist($(storageLevel)) // 将新的RDD写入缓存
  graph.count()
  prev.unpersist(true) // 释放旧的graph partition RDD
  prev = graph
  model.resetMsgs() // 步骤4：重置PS端变量
  numMsgs = model.numMsgs()
} while (numMsgs &gt; 0)
</pre>
<p><strong>Executor端</strong></p>
<pre>class KCoreGraphPartition extends Serializable {
  ...
  def process(model: KCorePSModel, numMsgs: Long): KCoreGraphPartition = {
    val inMsgs = model.readMsgs(indices) // 步骤1：从PS拉取est[][]中的可更新值
    val outMsgs = VFactory.sparseLongKeyIntVector(inMsgs.dim())
    for (idx &lt;- keys.indices) {
      val newIndex = calcOne(idx, inMsgs) // 步骤2：根据更新的est[][]计算本地节点的新的coreness
      if (newIndex &lt; keyCores(idx)) {
        outMsgs.set(keys(idx), newIndex)
        keyCores(idx) = newIndex
      }
    }
    model.writeMsgs(outMsgs) // 步骤3：将更新过的coreness推送到PS
    new KCoreGraphPartition(...)
  }
  ...
}
</pre>
<h2>5 性能测试</h2><p></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/69f3ef3feb25eefa3600.png"/><br/><div> [  Figure 11. PageRank、K-Core和Closeness在Spark on Angel和GraphX上的性能对比 ]</div></div><p></p>
<p>我们使用7亿节点110亿边的真实业务数据集，进行了Spark on Angel与Spark GraphX在上述三种算法上的性能对比，我们的测试环境为TDW贵妃集群。结果如上图所示。在使用同样资源的情况下运行K-Core和closeness，Spark GraphX均会因内存不足（OOM）而无法完成计算，而Spark on Angel能够分别在2小时和1小时内完成；唯一能够在GraphX上正常运行的PageRank算法，在Spark on Angel上也能够仅用1/3的资源，以9倍的速度完成计算。</p>
<h2>6 总结</h2><p>本文介绍了三个主流的节点重要性评价算法在Angel平台上的分布式实现。目前PageRank、K-Core和Closeness均已在智能钛Ti平台的算法-&gt;图算法模块上线，欢迎大家尝试使用。相关代码也已开源到Angel项目，欢迎各位提出宝贵的意见和建议，帮助我们一起改进。接下来我们将继续对Angel的现有图算法进行功能补充和性能优化，后续还会有介绍图神经网络的相关文章。</p>
<h2>参考文献</h2><p>[^1]: Page, L., Brin, S., Motwani, R., &amp; Winograd, T. (1999). <em>The PageRank citation ranking: Bringing order to the web</em>. Stanford InfoLab.<br/>[^2]: Aksakalli, C. G. (2017). Network Centrality Measures and Their Visualization. <a href="https://aksakalli.github.io/2017/07/17/network-centrality-measures-and-their-visualization.html#closeness-centrality">https://aksakalli.github.io/2017/07/17/network-centrality-measures-and-their-visualization.html#closeness-centrality</a><br/>[^3]: Kang, U., Papadimitriou, S., Sun, J., &amp; Tong, H. (2011). Centralities in large networks: Algorithms and observations. In <em>Proceedings of the 2011 SIAM international conference on data mining</em> (pp. 119-130). Society for Industrial and Applied Mathematics.<br/>[^4]: Montresor, A., De Pellegrini, F., &amp; Miorandi, D. (2012). Distributed k-core decomposition. <em>IEEE Transactions on parallel and distributed systems</em>, <em>24</em>(2), 288-300.</p>

{% endraw %}
