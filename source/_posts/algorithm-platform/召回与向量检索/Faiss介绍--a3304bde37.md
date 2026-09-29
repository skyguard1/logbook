---
title: "Faiss介绍"
date: 2022-04-06 11:46:03
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<h3>1.简介</h3>
<p>    Faiss全称为 AI Similariry Search，是开源的一款能够提供高效相似度检索和稠密向量聚类的库。注意Faiss一系列相似度检索算法的集合，不仅仅是一个算法。使用者可以根据自己的应用场景，综合数据量级、内存占用、检索速度、检索准确度等多个因素，选择恰当的检索算法。后面本文将选择检索算法的一些思路。同时，Faiss支持CPU和GPU，在GPU上具有更好的性能。</p>
<p>    这里首先介绍下相似度检索。相似性搜索的概念是在n维空间中通过比较数据之间的相似性，寻找与输入点最接近的目标点。该技术被广泛应用在数据库、信息检索、模式识别、数据分析等各个领域。衡量两个item在n维空间上的相似性，即计算两个n维向量的相似度，常用的方法有欧式距离、余弦相似度、Jaccard相似度等，这里就不一一展开。</p>
<p>    然而，当被检索库拥有千万级别的向量等待被检索时，输入向量需要与检索库中的所有向量计算相似度，最终通过排序给出topK个相似向量。显然，这个过程是非常耗时的，在这个背景下，ANN（Approximate Nearest Neighbor）被提出。常用的ANN方法可以大致分成三类：基于树的方法，如KD-Tree；基于Hash的方法，如LSH；矢量量化方法，如PQ（ Product Quantization）。详细介绍可以参考<a href="http://yongyuan.name/blog/ann-search.html">http://yongyuan.name/blog/ann-search.html</a>。Faiss的索引库中，也采用了类KD-Tree思想和PQ算法。</p>
<p>    至于稠密向量聚类，我们简化理解为聚类。通过对要聚类的对象向量化表示之后，通过衡量对象之间的聚类进行聚类。Faiss主要是含括了高效版的Kmeans算法。</p>
<h3>2.Faiss原理及关键技术</h3>
<p>    Faiss中采用的相似度计算方法主要是两种：欧式距离和点积。在此对点积进行说明下，当向量归一化之后，两个向量的余弦相似度与其点积保持一致。</p>
<p>    因为Faiss是一堆索引算法的集合，这里我们首先介绍下Faiss中应用的关键技术，然后介绍Faiss具体索引类型时，详细介绍关键技术在其中的应用。Faiss采用的关键技术如下：</p>
<p>   （1）OpenMP ，并行计算中的理论，对其不熟，有兴趣的可以自行研究。</p>
<p>   （2）堆排序，一种高效的排序算法，Faiss中用在TopK个近邻的获取上。</p>
<p>   （3）PQ算法，一种矢量量化方法，有兴趣可以了解下。</p>
<p>   （4）倒排索引，常用于搜索引擎中，是文档检索系统中最常用的数据结构。</p>
<p>   （5）Kmeans，一种聚类算法。</p>
<p>   （6）PCA，主成分分析，一种降维的算法。</p>
<h3>3.Faiss支持的索引类型</h3>
<p>    Faiss的索引，根据检索结果是否为全局最优，分为暴力精准索引和近似近邻索引。前者的返回结果是全局最优的，而近似查找，如前面所讲，在准确率和检索速度上做了一定权重，返回的可能不是全局最优结果。Faiss提供的索引，如下图所示。如果看不清，可以参考<a href="https://github.com/facebookresearch/faiss/wiki/Faiss-indexes">https://github.com/facebookresearch/faiss/wiki/Faiss-indexes</a> 。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/85e882a744f5f132a765.png"/></p>
<p>    面对Faiss不同种类的索引，使用者该如何选取合适的索引？这里使用者需要结合自己的应用场景，思考以下几个问题：</p>
<p>   （1）是否一定要精确的检索结果？</p>
<p>   （2）检索是要全局检索还是局部搜索？</p>
<p>   （3）数据是否需要压缩？不压缩内存能否容的下？</p>
<p>    下图给出了一些选择策略。官方可以参考：<a href="https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index">https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index</a> </p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1a7a173d08637bcf45e8.png"/></p>
<h3>4.索引类型举例</h3>
<p>    接下来，本文将以官方文档的例子，介绍下几种常见索引的使用，及其中所采用的关键技术。这里我们以python为主，官网里面也提供C++代码。首先，我们准备以下数据，供后面案例使用。</p>
<div>
<pre>import numpy as np
d = 64                           # dimension
nb = 100000                      # database size
nq = 10000                       # nb of queries
np.random.seed(1234)             # make reproducible
xb = np.random.random((nb, d)).astype('float32')
xb[:, 0] += np.arange(nb) / 1000.
xq = np.random.random((nq, d)).astype('float32')
xq[:, 0] += np.arange(nq) / 1000.</pre>
</div>
<p> </p>
<p>    （1）IndexFlatL2 </p>
<p>    IndexFlatL2是一种暴力索引，会返回全局最优的结果。不需要训练过程，遍历全局数据集，返回准确topK个相似向量。该索引常常适用于数据量在十万以内的检索，可以秒级返回结果。与传统暴力检索有些不同，其采用了OpenMP技术，并且使用了高效矩阵计算BLAS，以及堆排序技术。<a href="https://zhuanlan.zhihu.com/p/34111594">https://zhuanlan.zhihu.com/p/34111594</a> 中对Faiss中该索引的源码进行了分析，有兴趣可以查看。下面给出python中IndexFlatL2的使用：</p>
<div>
<pre>import faiss                   # make faiss available
index = faiss.IndexFlatL2(d)   # build the index
print(index.is_trained)
index.add(xb)                  # add vectors to the index
print(index.ntotal)
k = 4                          # we want to see 4 nearest neighbors
D, I = index.search(xb[:5], k) # sanity check
print(I)
print(D)
D, I = index.search(xq, k)     # actual search
print(I[:5])                   # neighbors of the 5 first queries
print(I[-5:])                  # neighbors of the 5 last queries</pre>
</div>
<p>    （2）IndexIVFFlat</p>
<p>    IndexIVFFlat是一种近似查找算法。其采用类似于KD-Tree策略，首先对全局向量进行Kmeans粗聚类，根据聚类结果，得到N个簇中心，以及每个向量归属的簇ID，这个过程需要训练。当输入一个向量时，首先计算其和N个簇中心的聚类的距离，得到距离最近的m个簇。进而，计算输入向量与m个簇中每个向量的相似度，得到最相近的K个相似向量。IndexIVFFlat在内存允许的条件下，适用于亿级别的向量检索，检索速度与m值的选择相关，可控制在秒级。与IndexFlatL2相比，IndexIVFFlat需要预训练，在关键技术上，采用了Kmean聚类和倒排索引技术。关于IndexIVFFlat的源码分析，可参考：<a href="https://zhuanlan.zhihu.com/p/34184844">https://zhuanlan.zhihu.com/p/34184844</a>。下面给出python中IndexIVFFlat的使用：</p>
<div>
<pre>nlist = 100
k = 4
quantizer = faiss.IndexFlatL2(d)  # the other index
index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_L2)
       # here we specify METRIC_L2, by default it performs inner-product search
assert not index.is_trained
index.train(xb)
assert index.is_trained

index.add(xb)                  # add may be a bit slower as well
D, I = index.search(xq, k)     # actual search
print(I[-5:])                  # neighbors of the 5 last queries
index.nprobe = 10              # default nprobe is 1, try a few more
D, I = index.search(xq, k)
print(I[-5:])                  # neighbors of the 5 last queries</pre>
</div>
<p>     （3）IndexIVFPQ</p>
<p>    IndexIVFPQ也是一种近似查找算法。其在IndexIVFFLat的基础上，通过基于PQ对向量进行一个有损压缩，从而缩小其内存占用量，以便适用于超大规模数据。其源码分析可以参考：<a href="https://zhuanlan.zhihu.com/p/34363377">https://zhuanlan.zhihu.com/p/34363377</a> 。下面给出python中IndexIVFPQ的用法：</p>
<div>
<pre>nlist = 100
m = 8                             # number of bytes per vector
k = 4
quantizer = faiss.IndexFlatL2(d)  # this remains the same
index = faiss.IndexIVFPQ(quantizer, d, nlist, m, 8)
                                    # 8 specifies that each sub-vector is encoded as 8 bits
index.train(xb)
index.add(xb)
D, I = index.search(xb[:5], k) # sanity check
print(I)
print(D)
index.nprobe = 10              # make comparable with experiment above
D, I = index.search(xq, k)     # search
print(I[-5:])</pre>
</div>
<h3>5.Faiss安装 </h3>
<p>    Faiss的安装可以参考<a href="https://github.com/facebookresearch/faiss/blob/master/INSTALL.md">https://github.com/facebookresearch/faiss/blob/master/INSTALL.md</a>，其对GCC版本有一定要求，最好是GCC4.8以上。如果是python用户，可以先安装conda，然后 conda install faiss-cpu -c pytorch。</p>
<h3>6.应用场景</h3>
<p>    Faiss的应用场景比较广泛，涉及到相似性查找或者聚类的场景都可以适用。将其应用于图片的相似度检索，并将其作为官网的一个案例；应用宝将其应用于推荐领域、APP搜索、用户群looklike、天天快报的相似文档检索等。当我们遇到大规模向量检索时，都可以考虑使用Faiss。我们将在下一篇文章——基于Faiss的md5变种发现系统，介绍faiss在安全领域的应用，以及相关的性能指标。</p> 
{% endraw %}
