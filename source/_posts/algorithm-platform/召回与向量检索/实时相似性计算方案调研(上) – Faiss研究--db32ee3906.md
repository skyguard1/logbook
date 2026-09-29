---
title: "实时相似性计算方案调研(上) – Faiss研究"
date: 2022-04-06 11:44:19
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<div>
<p>在当今这个大数据时代，我们每天都面临海量信息的冲击。 设想有一天你看到一幅建筑的照片，映像中它在你以前的某一次旅途中见过，但你就是想不起来这个地方是哪里； 此时我们想要搜索这个地方，传统的数据查找方法是没法帮你的， 类似DB查询或者传统搜索引擎，你得有关键字；但此时你手里只有一张图片，这里就是典型的查找相似图片的问题。此外还有诸如相似性文档查找、位置信息等等， 这些都可以归结为最近邻检索（Nearest Neighbor Search）的应用领域。</p>
<h3><strong>一、距离度量</strong></h3>
<p>在介绍Faiss之前，先介绍下距离度量的概念。</p>
<p>在做相似度计算时，最重要的就是如何判断两个item是否相似。距离度量方式有很多， 常用的有欧氏距离、余弦相似度等等，像知名的word2vec采用的就是余弦相似度，而后边我要介绍的Faiss用的就是欧式距离。距离度量详细的原理我就不介绍了， 很多同学应该都知道，可以参考：[<a href="https://blog.csdn.net/zhzhx1204/article/details/69668597">计算距离方法总结</a>]、[<a href="https://blog.csdn.net/Kevin_cc98/article/details/73742037">欧式距离</a>]。这里我主要介绍下欧式距离和余弦相似度。</p>
<p>欧式距离主要就是计算n维空间中的两点的绝对距离，所以距离越小，两个点越近，对应的item越相似；而余弦相似度是比较两个向量方向上的差异，通过计算其夹角的余弦值来判断相似性，所以两个向量夹角越小、余弦值越大，两个向量的方向越一致，对应的item越相似。两者的公式如下：</p>
<p>欧式距离：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/dfc9b5da3e6f18aff819.png"/></p>
<p>余弦相似度：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7232e2ee094ecd003c32.png"/></p>
<p></p>
<h3><strong>二、最近邻问题的方法概述</strong></h3>
<p><strong></strong></p>
<p>最近邻检索是被广泛研究的技术，最容易想到的是暴力穷举（Faiss确实提供了暴力搜索算法，工程实践中可以用来做基线对比），虽然效果最好，但性能很差(需要遍历数据集中的所有向量)，无法在工程中落地。除此之外还有基于索引树的搜索方法，如KD-Tree，其基本思想是对空间进行划分，在进行快速匹配； 但是这种方法在数据总量较少以及数据维度较低时是可以的，一旦数据维度变高，效率可能大幅降低。 而后又出现了近似最近邻的方法，即ANN； 这些方法基于对数据本身进行处理，如LSH、矢量量化等， 以取得检索性能和检索效果的平衡。本文主要介绍向量量化方面由开源的Faiss，后续可能也会加入KD-Tree、LSH的调研，以便在不同业务场景中选用其最合适的工具。</p>
<h3>三、向量量化（Vector Quantization）</h3>
<p></p>
<p>在介绍Faiss之前，我先介绍下向量量化的概念，因为Faiss的主要原理就是采用了名为Product Quantization的方法来做相似向量计算。</p>
<p>量化是一个在信息论里边被广泛研究的概念，本质上来说它是一种数据压缩方法。所谓量化即采用一个量化器（映射函数q），来将原始的D维向量x映射到一个D维向量q(x)，q(x)被称为centroid，即下图中一个个的中心点；如下图所示，原始向量空间被划分为一个个块，称为Voronoi cell。q(x)属于有限集合C，C叫做量化后的codebook，C的大小记为k。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/483a9ba401e65144a111.png"/></p>
<p>因为量化的质量将直接影响后续我们检索结果的优劣，所以要保证向量集中的所有向量x都真正被量化到了离它最近的centroid；为了达到这个条件，量化器需要满足Lloyd optimality conditions， 即：</p>
<p>1.  向量x必须被量化到codebook中离它最近的centroid：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6603ce9e281a8aa0deb9.png"/></p>
<p>2.  每个cell中所有向量的期望必须与<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/06ea0bef5c6f7bc2e568.png"/>相等：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f00fb386ff675af58d3a.png"/></p>
<p>满足Lloyd条件的量化器(Lloyd quantizer)，量化完成后，即相当于执行了一次k-means聚类算法，原始的向量集就被映射到k个子集中(cell)，而对于所有centroid的编码采用<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/84e34075e3ef5790da79.png"/>个bit就可以了。</p>
<h2>四、Faiss介绍</h2>
<p>Faiss是由 开源的相似性搜索和稠密矢量聚类的工具，项目地址：[<a href="https://github.com/facebookresearch/faiss">Faiss</a>]，论文原文：[<a href="https://lear.inrialpes.fr/pubs/2011/JDS11/jegou_searching_with_quantization.pdf">Product quantization for nearest neighbor search</a>]，其号称包含了可在任何大小向量集合里进行搜索的算法，向量集合的大小甚至可达到RAM容纳不下的地步，下边将重点分析Faiss的实现原理。</p>
<p>先假设有一个D=128维的向量集，用64bit对其进行量化，则总共会有<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c31285e1bd22f654978c.png"/>个centroid，因为这个值非常大，所要求的样本数量和学习复杂度是k的几倍，所以不可能使用Lloyd算法；即便codebook能学习出来，存储k * D个浮点型值也是很难完成的。</p>
<h3>4.1 Product Quantization</h3>
<p>所以当面对大量高维向量集时，普通的VQ方式是无法实施的。针对这个问题， 才有了PQ算法，其核心思想是把一个高维向量先分解为m个低维向量，然后对分解得到的子向量分别做量化。也就是说，原始的D维向量(如D=128)被分解成m组(如m=8，通常D为m的倍数)， 则每组子向量的维数为D*=D/m，则原始向量会被映射成：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/937eff3b96a549f05441.png"/></p>
<p>然后这m组子向量会采用m个不同的量化器进行量化，每个子量化器都会生成一个codebook <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7a2e0eaae42fdd3b68cc.png"/>，<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7a2e0eaae42fdd3b68cc.png"/>的大小为<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ee32e61bf21c3993958a.png"/>，则原始D维向量对应的codebook为<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7a2e0eaae42fdd3b68cc.png"/>的笛卡尔积，大小为k：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/14f90efd0b9b861d67b5.png"/> ，<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f3381fc9ae9dbb93fde7.png"/>。</p>
<p>可以看出，PQ算法的优势就是用几个小的codebook来产生一个较大的codebook，而这几个小的codebook是可以采用Lloyd算法学习出来的(低维向量可以完成k-means算法)，这样就解决了原始的高维向量学习复杂度太高而无法完成的问题。</p>
<p>接下来就是m和<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ee32e61bf21c3993958a.png"/>如何设定的问题，论文作者通过采用均方损失的方法来评价不同的m、<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ee32e61bf21c3993958a.png"/>时表现，最后得出<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ee32e61bf21c3993958a.png"/>=256、m=8是一个好的选择。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d36f05d4253cd8598ee6.png"/></p>
<h3>4.2 距离计算方法</h3>
<p>最近邻搜索依赖于计算查询向量x和数据集中向量y的距离，原论文提出了两种距离计算方式： SDC(对称距离计算)、ADC(非对称距离计算)。</p>
<p><em>4.2.1 SDC</em></p>
<p>所谓SDC，即vector x跟vector y都采用各自的centroid q(x)、q(y)来近似表示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1dded8e415e34dbe241f.png"/></p>
<p>则d(x,y)可以近似的表示为：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d47015c9e8d5e9e54a7c.png"/>，</p>
<p>另外在采用PQ算法情况下，则此式又可以表示为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f5de43498fdfa52edaf4.png"/></p>
<p><em>4.2.2 ADC</em></p>
<p>而ADC，则只把vector y用其对应的q(y)近似表示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/faea60e1986ac88e8208.png"/></p>
<p>则d(x,y)可以近似表示为：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8723bedc44b04e28bf43.png"/></p>
<p>完整计算公式为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b52b54f59074d1a397c9.png"/></p>
<p>在实际应用中当使用SDC时，<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/253bb7c0b256cf7cbc49.png"/>（即两个中心点之间的距离）可以以O(1)的时间复杂度获得，因为在检索之前可以先把每个分组向量集合中的<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/bc0b02380a59f05e99d5.png"/>个centroid先计算好距离并缓存，等实际检索时距离就可以通过查表获得，则每组查找表的大小为：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/04b353e9e743e92dc09a.png"/>。另外根据论文介绍，当使用ADC时<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25bd7c208ae226df3f10.png"/>也可以在搜索之前计算好，理论上是可行的， 但是工程应用中可能会有问题。一是要求查询向量都来自原始向量集，二是如果原向量集很大，则这里也会需要比较大的内存空间。</p>
<p>下表对比了使用SDC和ADC时， 在大小为n的向量集Y中查找向量x的k个最近邻各阶段的复杂度。可以看出在查询之前的预处理过程都是一样的，复杂度跟n无关；当<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c6a788c0169e7b71c744.png"/> 时，计算瓶颈主要在上述公式的计算上，虽然距离可以通过查表以O(1)的复杂度获取，但是仍需要做m次求和操作并且需要遍历n次。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e6ef6c6dc4ae80d5c1d8.png"/></p>
<p>（表1）</p>
<p>另外在原论文中作者还针对SDC和ADC的距离误差做了详细的分析，一般在实际应用中都推荐使用ADC算法。</p>
<h3>4.3 IVFADC</h3>
<p>通过上边的介绍， PQ算法已经解决普通VQ无法量化高维向量的问题并且大大减少了储存centroid的内存要求，也能采用一些预处理来提高计算的速度(距离查表)。不过如表1所示，当<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b72cbb496bbd76ed7d60.png"/>时，特别是在实际工程应用中n的数量级可能是千万量级，朴素的PQ算法计算量还是太大，无法满足工程要求。</p>
<p>另外朴素PQ算法做最近邻计算时，还是遍历了一把原向量集，做开发的同学都知道，当我们面对一个查找的需求时，遍历是最低效的方式；一般我们都会在以空间换时间的方式，预先把数据分组或者过滤好，来缩小查找的范围。</p>
<p>试想我们此时面对的需求是查找k个最近邻向量，理论上我们根本不需要去对整个向量集中查找，只需要把计算范围限定在向量x周围就好了。那么有没有这种办法呢？答案是肯定的，就是原论文提出的IVFADC(invert file system)。</p>
<p><em>4.3.1 Coarse quantizer（粗粒度量化器）</em></p>
<p>先在原向量集中使用k-means算法学习得到量化器<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/0d5f536cca385a34eb3c.png"/>，生成大小为<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/855d58b8b8ab226cf400.png"/>的codebook，之所以叫Coarse quantizer是因为<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/855d58b8b8ab226cf400.png"/>的范围一般在1000~1000000(一般建议为<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/3f7276c28d087b8ee929.png"/>)，远远小于常规的codebook大小。</p>
<p>进行Coarse quantizer之后，查询时可以直接以<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/70d4ecf2f28b36b44006.png"/>作为索引来缩小计算数量。不过在计算距离时还是不可能用暴力计算的方式，所以第二步继续采用Product Quantization来分别量化。不过这里在做PQ时，并不是对原向量，而是引入residual vector：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2cd702997aa04d8eb16e.png"/></p>
<p>可以理解为向量y相对<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/680872765f756086f68c.png"/>的偏移，则原向量y近似表示为：<br/></p>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7648a8395eb1f3dcec13.png"/><p></p>
<p>则d(x, y)可以采用<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/3a783a52909e9fb995ab.png"/>来计算：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/26dae47ed2d149453fae.png"/></p>
<p>所以完整的距离计算公式为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/65459187ce6106bac125.png"/></p>
<p></p>
<p><strong>备注：根据上边的公式，其实就是把x，y的距离转换为r(x)、r(y)的距离，只是最终距离计算是采用ADC算法（减少计算量）。但是这里为啥可以这样转换，数学上的意义我也还没想太清楚，如果有知道的同学可以一同探讨。</strong></p>
<p></p>
<p><em>4.3.2 Indexing structure</em></p>
<p>由coarse quantizer <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/74ee49597cef58f590fc.png"/>生成的centroid <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/cb08a34f409fe76dd81b.png"/>作为索引列表（可以理解为一种hash结构），每个<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/cb08a34f409fe76dd81b.png"/>会对应一个倒排列表<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7e1167a502271d22c59f.png"/>，而列表<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7e1167a502271d22c59f.png"/>中的每一项包含两个元素：向量标识符和r(y)的量化编码<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9fe91731d43e5ff56e3c.png"/>    。</p>
<p>下图展示了IVFADC算法对数据集进行索引和查询的过程：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/72bda90c50c61f9d1c8c.png"/></p>
<p><strong>Indexing</strong></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/cd06885821e20a8d41d5.png"/></p>
<p>由于在索引过程中采用了Coarse quantizer对原向量集执行了粗糙的k-means聚类，所以向量x以及它的最近邻向量不一定都被量化到了同一个centroid。</p>
<p>为了提高搜索的精度，论文提出了一种叫做Multiple assignment的策略，实际查询时并不仅仅只把向量x量化到一个centroid，而是同时将向量x量化到w个跟它临近的centroid。计算距离时把这w个倒排同时取出来并一起做距离计算。对比朴素ADC的<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ee449bcfabe03e7427b3.png"/>的时间复杂度，IVFADC的时间复杂度为：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/010408d406d9e942316b.png"/>。</p>
<p><strong>Searching</strong></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/bf78c568fb30317e0d01.png"/></p>
<p> </p>
<p>至此，Faiss的基本原理就介绍完了，另外原论文中还有一些关于最近邻搜索的评估， 例如数据集大小啊、内存和搜索精度的平衡啊等等， 这些就等下篇作者整理相似度计算的工程方案时再一并来探讨， 结合实际的业务场景来做这些评估更有参考意义。</p>
<p> 参考文献：</p>
<ol><li><a href="https://lear.inrialpes.fr/pubs/2011/JDS11/jegou_searching_with_quantization.pdf">Product quantization for nearest neighbor search</a></li>
<li><a href="http://140.117.156.238/temp/5_ITCT_Vcector_%20quantization_coding.pdf">向量量化编码</a></li>
<li><a href="http://vividfree.github.io/%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0/2017/08/05/understanding-product-quantization">理解 product quantization 算法</a></li>
<li><a href="https://blog.csdn.net/zouxy09/article/details/9153255">语音信号处理之（三）矢量量化</a></li>
</ol><p> </p>
</div> 
{% endraw %}
