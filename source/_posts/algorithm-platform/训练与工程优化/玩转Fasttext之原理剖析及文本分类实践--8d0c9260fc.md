---
title: "玩转Fasttext之原理剖析及文本分类实践"
date: 2022-04-06 13:57:14
categories:
  - 算法平台
  - 平台工程与评估
---

{% raw %}

<p>Fasttext是 AI Research最近推出的文本分类和词训练工具，其<a href="https://github.com/facebookresearch/fastText">源码</a>已经托管在Github上。Fasttext最大的特点是模型简单，只有一层的隐层以及输出层，因此训练速度非常快，在普通的CPU上可以实现分钟级别的训练，比深度模型的训练要快几个数量级。同时，在多个标准的测试数据集上，Fasttext在文本分类的准确率上，和现有的一些深度学习的方法效果相当或接近。</p>
<p>最近一直在做广告文章分类的工作，正好顺手研究了下Fasttext，并在广告文章识别上做了一些尝试。因为代码开源的时间不长，网上相应的文章和资料还比较少， 希望这篇文章对想了解和使用Fasttext做文本分类的同学有所帮助。</p>
<h2>原理</h2>
<p>介绍原理之前，我们先稍微聊一点八卦。Fasttext的其中一个作者是Thomas Mikolov。熟悉<a href="https://code.google.com/archive/p/word2vec/">word2vec</a>的同学应该对这个名字很熟悉，正是他当年在带了一个团队倒腾出来了word2vec，很好的解决了传统词袋表示的缺点，极大地推动了NLP领域的发展。后来这哥们跳槽去了，才有了现在的Fasttext。从“血缘”角度来看，Fasttext和word2vec可以说是一脉相承。</p>
<p>回到正题，Fasttext主要有两个功能，一个是训练词向量，另一个是文本分类。词向量的训练，相对于word2vec来说，增加了subwords特性。subwords其实就是一个词的character-level的n-gram。比如单词"hello"，长度至少为3的char-level的ngram有"hel","ell","llo","hell","ello"以及本身"hello"。每个ngram都可以用一个dense的向量zg表示，于是整个单词"hello"就可以表示表示为：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/3f88d15d9ac618223e9e.png"/></p>
<p>具体细节可以参考论文<a href="https://arxiv.org/pdf/1607.04606v1.pdf">Enriching Word Vectors with Subword Information</a>，这里就不展开叙述了。那么把每个word，拆成若干个char-level的ngram表示有什么好处呢？其实细想一下也非常容易理解，无非就是丰富了词表示的层次。比方说"english-born"和"china-born"，从单词层面上看，是两个不同的单词，但是如果用char-level的ngram来表示，都有相同的后缀"born"。因此这种表示方法可以学习到当两个词有相同的词缀时，其语义也具有一定的相似性。这种方法对英语等西语来说可能是奏效的，因为英语中很多相同前缀和后缀的单词，语义上确实有所相近。但对于中文来说，这种方法可能会有些问题。比如说，"原来"和"原则"，虽有相同前缀，但意义相去甚远。可能对中文来说，按照偏旁部首等字形的方式拆解可能会更有意义一些。</p>
<p>Fasttext的另一个功能是做文本分类。主要的原理在论文<a href="https://arxiv.org/pdf/1607.01759v2.pdf">Bag of Tricks for Efficient Text Classification</a>中有所阐述。其模型结构简单来说，就是一层word embedding的隐层+输出层。结构如下图所示：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/5b55e5160e74c834fac7.png"/></p>
<p>上图中左边的图就是Fasttext的网络结构，其中W(1)到W(n)表示document中每个词的word embedding表示。文章则可以用所有词的embedding累加后的均值表示，即</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/1d6774d5f3b6c7e26e51.png"/></p>
<p>最后从隐层再经过一次的非线性变换得到输出层的label。通过对比word2vec中的cbow模型（continuous bag of word），可以发现两个模型其实非常地相似。不同之处在于，Fasttext模型最后预测的是文章的label，而cbow模型预测的是窗口中间的词w(t)，一个是有监督的学习，一个是无监督的学习。另外cbow模型中输入层只包括当前窗口内除中心词的所有词的Embeddings，而Fasttext模型的输出层则是文章全部词的Embeddings。</p>
<p>和word2vec类似，Fasttext本质上也可以看成是一个浅层的神经网络，因此其forward-propogation过程可描述如下：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/6aa5a8cc6614e07ecc10.png"/><br/>其中z是最后输出层的输入向量，Wo表示从隐层到输出层的权重。因为模型的最后我们要预测文章属于某个类别的概率，所以很自然的选择就是softmax层了，于是损失函数可以定义为：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/9b8f774daf38e1fa56ab.png"/><br/>当类别数较少时，直接套用softmax层并没有效率问题，但是当类别很多时，softmax层的计算就比较费时了。为了加快训练过程，Fasttext同样也采用了和word2vec类似的方法。一种方法是使用hierarchical softmax，当类别数为K，word embedding大小为d时，计算复杂度可以从O(Kd)降到O(dlog(K))。另一种方法是采用negative sampling，即每次从除当前label外的其他label中选择几个作为负样本，并计算出现负样本的概率加到损失函数中，用公式可表达为：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/46af19f06c667b6b297d.png"/></p>
<p>其中hi是第i个样本的隐层，uj表示Wo中第j行向量。</p>
<h2>N-gram特征</h2>
<p>到目前为止，Fasttext有个比较严重的问题，就是丢失了词顺序的信息，因为隐层是通过简单的求和取平均得到的。为了弥补这个不足，Fasttext增加了N-gram的特征。具体做法是把N-gram当成一个词，也用embedding向量来表示，在计算隐层时，把N-gram的embedding向量也加进去求和取平均。举个例子来说，假设某篇文章只有3个词，W1，W2和W3，N-gram的N取2，w1、w2、w3以及w12、w23分别表示词W1、W2、W3和bigram W1-W2，W2-W3的embedding向量，那么文章的隐层可表示为：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/13a3f9df83882a795adc.png"/></p>
<p>通过back-propogation算法，就可以同时学到词的Embeding和n-gram的Embedding了。</p>
<p>具体实现上，由于n-gram的量远比word大的多，完全存下所有的n-gram也不现实。Fasttext采用了Hash桶的方式，把所有的n-gram都哈希到buckets个桶中，哈希到同一个桶的所有n-gram共享一个embedding vector。如下图所示：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/d97c64756e03bc4a1ee5.png"/></p>
<p>图中Win是Embedding矩阵，每行代表一个word或N-gram的embeddings向量，其中前V行是word embeddings，后Buckets行是n-grams embeddings。每个n-gram经哈希函数哈希到0-bucket-1的位置，得到对应的embedding向量。用哈希的方式既能保证查找时O(1)的效率，又可能把内存消耗控制在O(buckets * dim)范围内。不过这种方法潜在的问题是存在哈希冲突，不同的n-gram可能会共享同一个embedding。如果桶大小取的足够大，这种影响会很小。</p>
<h2>Tricks</h2>
<p>Fasttext为了提升计算效率做了很多方面的优化，除了上节提到的Hash方法外，还使用了很多小技巧，这对我们实际写代码的时候提供了很多的借鉴。</p>
<p>首先，对计算复杂度比较高的运算，Fasttext都采用了预计算的方法，先计算好值，使用的时候再查表，这是典型的空间或时间的优化思路。比如sigmoid函数的计算，源代码如下：</p>
<div>
<pre>void initSigmoid() {
    t_sigmoid = new real[SIGMOID_TABLE_SIZE + 1];
    for (int i = 0; i &lt; SIGMOID_TABLE_SIZE + 1; i++) {
        real x = real(i * 2 * MAX_SIGMOID) / SIGMOID_TABLE_SIZE - MAX_SIGMOID;
        t_sigmoid[i] = 1.0 / (1.0 + std::exp(-x));
    }
}</pre>
</div>
<p>其次，在Negative Sampling中，Fasttext也采用了和word2vec类似的方法，即按照每个词的词频进行随机负采样，词频越大的词，被采样的概率越大。每个词被采样的概率并不是简单的按照词频在总量的占比，而是对词频先取根号，再算占比，即</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/ff14db6cc0989ee86ce2.png"/></p>
<p>其中fw表示词w的词频。这里取根号的目的是降低高频词的采用概率，同时增加低频词的采样概率，具体代码如下：</p>
<div>
<pre>void Model::initTableNegatives(const std::vector&lt;int64_t&gt;&amp; counts) {
    real z = 0.0;
    for (size_t i = 0; i &lt; counts.size(); i++) {
    z += pow(counts[i], 0.5);
    }
    for (size_t i = 0; i &lt; counts.size(); i++) {
        real c = pow(counts[i], 0.5);
        for (size_t j = 0; j &lt; c * NEGATIVE_TABLE_SIZE / z; j++) {
            negatives.push_back(i);
        }
    }
    std::shuffle(negatives.begin(), negatives.end(), rng);
}
</pre>
</div>
<h2></h2>
<h2>应用</h2>
<p>在弄清了Fasttext基本原理之后，我们在广告文章识别的场景下进行了尝试和探索。首先，简单地说明下任务的背景：公众号的文章中存在不少的广告文章，比如各类产品类广告，公众号广告以及大量的夹带广告。</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/726a7d4b546ff6adb800.png"/></p>
<p>大量广告文章的存在不仅影响用户的阅读体验，而且在索引侧也占用了大量的存储资源。因此，我们希望能训练一个广告识别的模型，来对广告类的文章在排序侧进行打压或者直接从索引中去除。从机器学习的角度看，这是经典的二分类问题，但是考虑的广告文章本身的多样性，和正常文章界限较模糊，以及软文广告，图片广告等大量存在，因此做到比较高的准确率并不是很容易。</p>
<p>训练模型之前，我们先看下实验用到的数据集。通过人工标注，交叉验证的方式共收集了约32.4万的样本数据，其中正样本（广告文章）15.7万，负样本（正常文章）16.7万。按照8:2的比例切分成训练数据和验证数据（用于调参）。另外还有1500左右的独立测试样本，正负样本占比为1：1。每个样本为一篇文章，包括文章的标题和正文。</p>
<p>实验中，我们选择了另外两种常见的分类算法和Fasttext进行对比。第一种方法是广告特征词袋的方法，其中包括单个的特征词和bigram，大约3万多个。另一种方法是使用CNN+word2vec的方法，先用word2vec训练词的Embedding，然后把文章的词序列转化成Embeddings向量构成的二维矩阵，之后再套用CNN的网络架构进行分类，具体方法可参考<a href="https://blog.keras.io/using-pre-trained-word-embeddings-in-a-keras-model.html">这里</a>。所有模型的超参数都是通过验证数据集来选择的。</p>
<p>我们先从分类准确率的评价指标来对比三种方法的实际效果。</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/51213eac981928681af7.png"/></p>
<p>从实际效果上来看，Fasttext的表现还是非常不错的。相对于传统的特征词袋的方法，Fasttext在准确率上有较大的提升，大约高出1.3个百分点。另外，和相对复杂的CNN模型对比，Fasttext的效果甚至要略好一些。</p>
<p>从算法的执行效率上看，我们同样对这三种方法进行了简单地对比：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/6fdd82d51143e4492c2c.png"/></p>
<p>上图显示的是每种算法单次迭代的训练时间，单位是秒。可以看到Fasttext相对于深度学习等方法，在训练速度上的优势还是非常明显，单次迭代速度比CNN快了60多倍。而且Fasttext是在普通CPU上执行，而CNN是在k20的GPU上运行的。而特征词袋的方法是用liblinear来训练的，采用的是逻辑回归算法，比较简单，所以速度要比Fasttext快一些。</p>
<h2>结论和思考</h2>
<p>其实关于学术界对Fasttext的评价，网上也有许多不同的声音。有些人认为Fasttext模型非常简单，理论上也没有什么很多创新之处。但是从实际的使用效果和训练速度上来看，我认为Fasttext依然是一个非常优秀的开源文本分类工具。</p>
<p>首先从工业界的角度来看，Fasttext因为其优秀的性能，不错的分类效果，使用起来也非常简单，因此非常适合大规模的文本分类问题。实际上已经将Fasttext应用于实际的大规模文本分类的场景中了。另外作为浅层的文本分类模型，Fasttext也非常适合作为Baseline算法来和复杂的深度学习算法进行对比。</p>
<p>另一方面，从理论或者学术的角度看，Fasttext也引发了我们一些新的思考。首先，对于文本分类等偏线性的数据集，复杂的深层网络对于浅层网络来说，优势并不明显，深度学习可能容易过拟合，而浅层的简单网络反而泛化能力更好。但也不是说浅层的方法就一定比深层的好，这是由数据集来决定的。其次，除了数据本身，数据量的大小很大程度上也决定了方法的选择。对于小规模的数据集，可能简单的浅层模型就可以了，深度学习因为参数很多，模型复杂，反而训练不充分。但随着数据量的增加，可能深度模型的优势就逐步体现出来。不过深度学习受限于GPU本身的性能和内存问题，面对一些超大规模的数据集，深度学习可能无能无力。这时候，选择有些简单的浅层方法，反而是一个比较好的选择。</p> 
{% endraw %}
