---
title: "一文精通知识图谱的实体对齐(Entity Alignment)"
date: 2022-03-24 10:52:11
categories:
  - 算法
  - 图学习与知识图谱
---

{% raw %}

<div>

</div>
<h1><strong>1, 什么是实体对齐</strong></h1>
<p>首先我们看下什么是实体对齐,  在实际应用中，无论工业界还是学术界， 我们很少完全从0去构建一个知识图谱， 而是从某一个或多个已知开源的图谱开始， 慢慢填充我们自己需要的知识。 那么问题就来了， 我们怎么确保我们填充的数据中，或者我们融合的多个图谱中不会出现多个一模一样的实体呢？ 如何确保我们的图谱中不存在多个”刘德华“实体呢？</p>
<div>
<p><strong>Entity alignment is the task of linking entities with the same real-world identity from different knowledge graphs (KGs)</strong></p>
</div>
<p>或许大家已经想到了， 我们直接用名字这个属性匹配， 找到知识图谱里边的所有‘刘德华’不就完成了么， 对的， 这就是实体对齐最早期， 也是最有效的方法。 但是这种方法召回率和准确率都不太高， 有的图谱里边刘德华会叫做刘德华， 有的图谱里边刘德华会叫做"刘德华(Andy)"或者”Andy“ 。 就是由于这种原因，  有人提出了一些传统的方法， 比如《<strong>Semantic matching with S-Match</strong>》  。 这类型的方法主要思想是，首先我们通过实体周围的属性类型来判断两个实体是不是一个类型的实体 ，然后查看两个实体的属性有多少相似。 在没有word2vec, Bert的年代，判断相似度的方法主要基于WordNet和编辑距离。 </p>
<h1>2, 近年效果提升思路总结</h1>
<p>近些年， 随着表示学习方法的发酵， 给实体对齐提供了更多的可能性， 各种骚操作接踵而至。 我们通过分析近几年会议中的实体对齐论文， 来看看近几年实体对齐都有哪些思路和方法。 说到Embedding， 我们最直观的方法就是把两个图谱中的所有实体都投影到一个或者多个向量空间里， 然后给定一个距离阈值， 低于这个阈值的两个实体就是一个实体。我们大概把近期效果提升的思路分为三大类， 通过投影空间， 通过增加内容， 通过迭代与修改。 以下分别介绍。</p>
<h2>2.1 通过空间投影来进行实体对齐</h2>
<p>比如下边这个工作《<strong>A Joint Embedding Method for Entity Alignment of Knowledge Bases</strong>》</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/21380946442249ac1e99.png"/></p>
<p>这是一个半监督的工作，需要利用种子进行训练， 他的思路就如上边所说的， 把两个图谱投影到一个空间里， 然后希望相同实体（种子）的embedding之间的距离越小越好，当然还要同时满足三元组H+R~T( 详见TransE, 这里不再赘述)。 这篇论文的另外一个贡献是说关系信息一样重要。 ”<strong>The results show that the proposed approach which only utilize the structure information of KBs also works well.</strong>“</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/aa687080ce4331e0ef89.png"/></p>
<p>这个loss有三个部分， 第一部分为了让真实三元组和算法构建的FAKE三元组距离尽可能的大，d(h+r, t)是指positive triple， 然后d(h'+r, t)' 是指negative triple,  第二部分是个软限制， 控制embedding的质量， 第三部分就是我们种子部分的学习，希望种子之间的距离越小越好。 第一部分和第三部分是实体对齐的常见loss。一般来讲， 带有第一种LOSS的方法， 被称为基于翻译的方法(Translation-based)。</p>
<p>上边提到的方法是把两个图谱投影到一个向量空间里， 并且使两个图谱中的种子e1和e2的距离越小越好。 那么肯定还可以把两个知识图谱投影到两个向量空间里， 然后通过某种手段， 让两个图谱里对应的实体尽量相近。 比如论文《<strong>Multilingual Knowledge Graph Embeddings for Cross-lingual Knowledge Alignment</strong>》把KG1 ， KG2投影到两个向量空间， 然后利用三个约束条件，<strong> Axis calibration</strong>,<strong> Translation vectors</strong>, <strong>Linear transformations  </strong>来控制种子中的对应实体。</p>
<p>相类似的投影到多个空间的还有几个工作， 其中有一个创新性非常强（脑洞大开）， 2019年的AAAI《<strong>Entity Alignment between Knowledge Graphs Using Attribute Embeddings</strong>》。  </p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a717a6862c3ef9c05887.png"/></p>
<p>简单来说， 这篇论文就是把两个KG的数据放在一起， 分成Attribute Triple 和 Relationship Triple 然后分别学习他的属性embedding 和 关系embedding.  之后利用关系和属性相互监督来达到对齐效果</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/45d378fe56ef6902f8b4.png"/></p>
<p>这里边的hse， hce分别指Strucutre Embedding和Attribute Character embedding. </p>
<p>这个工作有几个特点，1 无监督， 不需要种子; 2 同时利用的关系和属性知识进行对齐；3 在我们的数据集上试验了下， 效果竟然还可以接受。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a8a1b464149d7979bcab.png"/></p>
<p>所以结论就是<strong>当没有种子的时候， 这个方法可以一试</strong>。 与这个工作有一个非常相似的工作， 利用种子的，是ISWC的《<strong>Cross-lingual Entity Alignment via Joint Attribute-Preserving Embedding</strong>》</p>
<h2>2.2 通过丰富对齐信息</h2>
<p>之前我们按照投影空间来进行效果优化， 其实近来还有个趋势就是按照信息的丰富程度来进行优化。只利用单一的关系信息， 或者是标签信息， 或者是属性信息很难达到好的对齐效果。 因此如何利用好所有信息也是一种优化的方向。 比如这个工作， 他把实体的描述也作为实体对齐的一种知识《<strong>Co-training Embeddings of Knowledge Graphs and Entity Descriptions for Cross-lingual Entity Alignment</strong>》 还有这篇EMNLP的《<strong>Cross-lingual Knowledge Graph Alignment via Graph Convolutional Networks</strong>》通过把属性信息和关系信息放在一起， 然后进行对齐操作：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4d5ff5a9dc830721f25e.png"/></p>
<p>如图所示， 这个方法是把关系信息和属性信息放在一起然后通过GCN训练， 通过控制种子里的两个对齐实体的距离来约束。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm/d86a81e94fd227bdd47c.png"/></p>
<p>这个地方特别值得说明一下， 因为GCN就是学习关系的，但是在GCN中，关系是通过邻接矩阵进行传入，两个点有关系， 那么邻接矩阵里边的值就为1. 所以说普通的GCN是把所有的关系都当成一种关系来学习。 这篇论文把关系信息放到了输入X中。当然还可以用RGCN（通过多个邻接矩阵）来实现这个想法。 </p>
<p>还有另外一个非常值得一提的工作是《<strong>Multi-view Knowledge Graph Embedding for Entity Alignment</strong>》。 在这个工作中， 他提出了一个框架， 把实体名字，关系， 属性，通过不同的方法进行融合来提升最终的准确率。还有一个近期的工作， IJCAI 《<strong>Relation-Aware Entity Alignment for Heterogeneous Knowledge Graphs</strong>》这个工作为了更好的学习图谱中的关系信息， 提出了利用关系对偶图的方式来进行学习。 </p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a7ca782b3ddef4cf9617.png"/></p>
<p>如图所示， 为了更好的学习关系信息， 这个工作把每个KG分别做了对偶转换后， 一同输入GCN。 其他的部分和之前的基于GCN alignment的工作差别不大。</p>
<p></p>
<h2>2.3 迭代与修改</h2>
<p>在说如何在迭代中阻止错误传播之前， 我们先说一下迭代学习方法，因为我们知道种子数量有限， 那么为了提升种子数量， 我们会把新学习到的对齐实体继续放入训练集中进行训练。 这个可以参考2017年IJCAI的《<strong>Iterative Entity Alignment via Joint Knowledge Embeddings</strong>》这个工作。 我们新标注的对齐实体作为训练集肯定会产生很多错误， 放在训练集中继续训练肯定会产生更多的错误， 于是就有了通过修改错误的方法来进行提升效果。 </p>
<p> 2018 IJCAI 的《<strong>Bootstrapping Entity Alignment with Knowledge Graph Embedding</strong>》这个工作除了解决了冷启动的问题， 同时提出了一种对齐编辑(alignment editing)的方法。 这种方法主要是为了防止错误被进一步传播。他们阻止错误传播的方法很简单， 利用查找冲突(conflicts)。 在一轮迭代中的结果如果和另一个迭代中的不一样，就会被判断哪个更有可能是正确的。例如， 在不同的迭代中， 实体x 被分别标注为 y, y', 那么就产生了冲突， 于是，通过判断两个标签的likelihood, 如果大于0， 那么y的可能性就大一些，然后进行修改。 </p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/1d545e706841f36753c7.png"/></p>
<h1>3， 结论与一些试验效果</h1>
<p>在阅读了大量的近期工作后，我们发现大家近期的工作主要从空间投影， 丰富对齐内容，迭代三个方面来尝试提升对齐效果。 我们对一些效果比较好， 或者创新性比较强的工作在我们数据集上进行了试验， 部分试验效果如下图。 </p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/49eaca40181253924f34.png"/></p>
<p>AttrE[4]是我们前文提到的无监督的方法，由于是无监督方法，效果还可以接受。  Multi-View[8] 可以说是实体信息考虑最全的方法， 他的效果相对较好。 RDGCN[11] 随机初始化的效果非常差， 于是我们加了一层N-GRAM把属性信息和名字加入初始的embedding之后， 效果有显著提升。 更多的试验结果将在我们下次分享我们自己的实体对齐方法中提及。 </p>
<p></p>
<h1>4， 参考文献</h1>
<p>1，Giunchiglia, Fausto, Pavel Shvaiko, and Mikalai Yatskevich. "S-Match: an algorithm and an implementation of semantic matching." European semantic web symposium. Springer, Berlin, Heidelberg, 2004.</p>
<p>2,  Hao, Yanchao, et al. "A joint embedding method for entity alignment of knowledge bases." China Conference on Knowledge Graph and Semantic Computing. Springer, Singapore, 2016.</p>
<p>3,  Chen, Muhao, et al. "Multilingual knowledge graph embeddings for cross-lingual knowledge alignment." arXiv preprint arXiv:1611.03954 (2016).</p>
<p>4, Trisedya, Bayu Distiawan, Jianzhong Qi, and Rui Zhang. "Entity alignment between knowledge graphs using attribute embeddings." Proceedings of the AAAI Conference on Artificial Intelligence. Vol. 33. 2019.</p>
<p>5, Sun, Zequn, Wei Hu, and Chengkai Li. "Cross-lingual entity alignment via joint attribute-preserving embedding." International Semantic Web Conference. Springer, Cham, 2017.</p>
<p>6, Chen, Muhao, et al. "Co-training embeddings of knowledge graphs and entity descriptions for cross-lingual entity alignment." arXiv preprint arXiv:1806.06478 (2018).</p>
<p>7, Wang, Zhichun, et al. "Cross-lingual knowledge graph alignment via graph convolutional networks." Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing. 2018.</p>
<p>8, Zhang, Qingheng, et al. "Multi-view Knowledge Graph Embedding for Entity Alignment." arXiv preprint arXiv:1906.02390 (2019).</p>
<p>9, Zhu, Hao, et al. "Iterative Entity Alignment via Joint Knowledge Embeddings." IJCAI. 2017.</p>
<p>10, Sun, Zequn, et al. "Bootstrapping Entity Alignment with Knowledge Graph Embedding." IJCAI. 2018.</p>
<p>11，Wu, Yuting, et al. "Relation-aware entity alignment for heterogeneous knowledge graphs." arXiv preprint arXiv:1908.08210 (2019).</p>
<p></p>
<p></p>
<p></p>
<div>
<div>
<div>
<div>
<div>
<div>
<h2></h2>
<div>
<div>
<div></div>
</div>
</div>
</div>
</div>
</div>
</div>
</div>
</div> 
{% endraw %}
