---
title: "QQ浏览器：小说召回中的DSSM模型优化实践（二）"
date: 2022-04-18 15:21:49
categories:
  - deep-learning
---

{% raw %}

<h3><strong><img alt="" loading="lazy" src="/logbook/images/deep-learning/c97647fc76c237e001ca.png"/></strong></h3>
<h3><strong>一、背景</strong><strong>简介</strong></h3>
<p>在上一篇《QQ浏览器：小说召回中的DSSM模型优化实践（一）》中，我们介绍了QQ浏览器小说推荐的主要架构。QQ浏览器小说推荐系统旨在为用户推荐可能感兴趣的小说，其主体框架与目前主流的推荐系统架构一致，主要由召回层、粗排层、精排层构成。DSSM作为召回层的其中一路召回，其主要目的在于挖掘用户和物品在语义空间的相关性。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/955d5e42130ee4f4f478.png"/></p>
<p>(欢迎大家来QQ浏览器看小说，海量免费正版优质好书看到停不下来！）</p>
<p>优化DSSM模型是一个漫长的过充，在我们优化模型的过程中，我们发现引入新特征以及修改loss函数所带来的提升最大。在特征优化方面，我们尝试引入了许多新的用户画像特征，以及加入了书籍统计特征，这些在我们的上一篇文章中已经详细介绍，因此本文不加以赘述。本文中，我们将聚焦于loss函数的优化。</p>
<h3><strong>二、基础模型</strong></h3>
<p><strong></strong>本文主要采用user-item模式的DSSM模型，其模型结构如图1所示。该模型首先将用户侧与物品侧的稀疏特征通过embedding look-up layer转化为稠密特征，两侧的稠密特征通过塔内的多层神经网络结构，最终生成两个多维的稠密向量。在模型的最后，我们计算两边的向量的余弦相似度。我们希望通过梯度下降，使得相关的用户和物品向量（用户与其点击/阅读过的书）的余弦相似度尽可能高，而用户与其不相关的物品向量的余弦相似度尽可能低。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/cd471a42a86f91bd113e.png"/></p>
<p>图1. DSSM模型结构</p>
<p></p>
<h3><strong>三、模型演化</strong></h3>
<p>在本章，我们介绍我们在模型优化的过程中所遇到的问题以及提出的解决方案。</p>
<p><strong>1. Pointwise loss</strong></p>
<p>目前公司内有大量业务的推荐系统用的是pointwise形式的loss，该loss形式在这些业务上也取得了非常不凡的表现。pointwise形式的loss具有代码逻辑简单，可解释性强，运算速度快等优点。在运用pointwise loss的时候，一条样本由一个用户和一本小说组成。如果用户点击过该小说，则样本的label为1，反正为0。用户和item的匹配程度，可以用这两个向量的余弦距离来表示，再通过一个sigmoid函数，将相似性转化为一个后验概率。<img alt="" loading="lazy" src="/logbook/images/deep-learning/99022ccb9c4a8bedfe3b.png"/>然后我们使用二分类交叉熵作为模型的损失函数</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/15436549a9903e65dc48.png"/></p>
<p>但是经过实践检验，该形式的loss在我们的数据集上没有起到很好的效果。尽管在我们学习的过程中，training loss和validation loss都可以达到0.8以上，但是CE的结果表明，不同种类的书籍没有很好的区分性。不同用户召回的书籍也有很大的重复性。我们尝试了各种优化，包括负样本的采集，正负样本的比例，特征的修改，均没有起到很好的效果。经过初步的分析，我们认为可能的原因是我们的数据存在很强的头部效应。在用户侧，有些活跃用户就是喜欢点击推荐的书籍，而大部分用户没有任何点击，只有曝光负样本。这样一来，我们的模型只需要学习不同用户的ctr，就可以使得整体模型的训练指标很可观。我们做出这样的推断有两点原因：第一，我们按照现有的训练样本的比例构造了一个虚拟模型，该模型将所有有过点击的用户预测为1，将所有没有任何点击的用户预测为0，该虚拟模型的AUC就可以达到0.8以上。事实上如果该模型能够更加准确预测ctr，该模型能够达到更高的AUC；第二，当我们保留用户特征，在书籍侧特征传入一些随机噪声，发现该模型的AUC仅有略微下降。因为我们得出结论，我们的模型只学习到了用户侧的特征而忽略了书籍侧的特征，导致最终模型效果很差。类似的分析，我们发现其实书籍侧也存在很强的头部效应，即使我们解决了用户侧的问题，模型依旧可以通过学习不同书籍的ctr而得到很好的AUC。因此我们得出结论在我们的数据集上，pointwise loss不是一个很合适的选择。当然这只是我们的初步猜测，还需要更细致的分析来得到更准确的原因。也希望遇到过类似问题的大佬能给我们一些建议。</p>
<p><strong>2. Listwise loss</strong></p>
<p>在提出DSSM模型之初，其所用的loss就是listwise形式的。相比于pointwise loss，listwise loss旨在对比同一个用户对不同物品的喜好。与pointwise loss不同的是，该loss希望提升某一用户对其点击过的书相对于未点击过的书的打分，而这个正样本的预测值的绝对值不需要很高。该loss可以很好解决我们前面遇到的问题，仅仅预测书籍或者用户的ctr无法很好优化该loss，从而强迫我们的模型学习到用户和书籍的相关性。并且该loss也更符合召回的场景。在计算该loss时，对于每一个用户，我们构建一个样本候选池，通过一个softmax函数计算不同候选物品的概率：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/cbfc500a7d3830b1eb31.png"/></p>
<p>随后将其看作一个多分类问题，采用交叉熵loss旨在增大该用户在正样本物品上的概率：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/e8ca5b3163c37ef159aa.png"/></p>
<p>在无量组件上执行listwise loss时，会遇到一定的问题。首先，该loss需要对比单用户对多个item的打分，而在无量组件上样本通常由单个用户特征和单个物品特征组成。如果我们事先将一个用户与多个物品拼接，当负样本比较多的时候（在我们的实践中，增加负样本的个数能提升模型表现），样本会过长造成存储问题。虽然利用插件能够将同一用户的不同样本放在同一batch中，但是这会增加样本预处理的工作量。其次，假设一条样本中要对比1个正例与99个负例，需要有100个item的特征过塔，这无疑使得训练的时间非常缓慢。因此，我们采用了batch内的负采样，且在过塔之后得到的item的embedding中进行采样。代码示例如下：</p>
<div>
<pre># doc_emb 与 user_emb 为过塔之后得到的用户与item的embedding
negative_num = 100
inner_product = tf.multiply(doc_emb, user_emb)
inner_sum = tf.reduce_sum(inner_product, 1, keepdims=True)
cosine = inner_sum
for i in range(, negative_num):
    doc_emb = tf.manip.roll(doc_emb, shift=1, axis=0)
    inner_product = tf.multiply(doc_emb, user_emb)
    cosine_tmp = tf.reduce_sum(inner_product, 1, keepdims=True)
    cosine = tf.concat([cosine, cosine_tmp], axis=1)
prob = tf.nn.log_softmax(cosine)
# y_data 包括0与1，其中1为原始样本中的点击样本，0为曝光未点击样本
hit_prob = tf.reshape(tf.slice(prob, [0, 0], [-1, 1]), [-1])
hit_prob = tf.multiply(hit_prob, tf.reshape(y_data,[-1]))
loss = -(tf.reduce_sum(hit_prob)+0.1) / (tf.reduce_sum(y_data)+0.1)
</pre>
</div>
<p>我们将这一版模型作为单独一路召回上线，与上线之前相比，整个推荐系统的表现有了显著的提升，部分重要指标展示如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/654c7c8e855943f4694f.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/d67db15e743cd347dbd5.png"/></p>
<p><strong>3. Listwise loss修正</strong></p>
<p>当我们进行batch内负采样的时候，item被采作负样本的概率等于其出现在原始样本中的概率。这样会导致一些热门的受欢迎的书籍更容易被当成负样本。而正如前所述，小说场景中有很明显的热点效应，而对于这些热门小说的过度打压会使得模型倾向于推荐一些冷门的书，从而影响线上表现。因此我们借鉴了google在2019提出的loss修正：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/bb61f20319a5998be3dc.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1fc2c3db7983c0f64dc0.png"/></p>
<p>其中<img alt="" loading="lazy" src="/logbook/images/deep-learning/56cf8df9dd2e5a5ab38a.png"/>是随机挑选一个batch，item j 出现在其中的概率。在原始论文中，所用的数据是流数据，无法精确估计此概率，因此作者给出了一个在线估计item频率的方法。而在我们的场景下，我们的数据是离线数据，因此估计每个物品的出现概率比较简单。即：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/b39a107641e3157e7229.png"/></p>
<p>在离线测评中，该loss修正显著提升了模型的表现，其中主要指标如下:</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/8d23f628250f25013f51.png"/></p>
<p>线上实验中该优化同样获得了很大的提升，部分重要指标展示如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/ee081d5847c9ffd918f3.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/e7e910ad1f4d935c70af.png"/></p>
<p><strong>4. 采样优化</strong></p>
<p>使用batch内负采样，所采集的负样本与样本本身没有关系，相当于全局负采样。这些样本通常与用户实际点击的正样本差距很大，模型学习会比较容易，导致最终书籍的分类比较粗糙。从我们的CE结果来看，模型召回的书籍通常类似的几个三级分类的，即用户喜欢的三级分类，但是对于同一个三级分类下不同的书用户到底偏好哪一本，模型没法很好地进行区分。一个解决办法是在负样本中加入较难区分的hard negative样本。对于hard negative的选择，一种方式是采用同一用户的曝光未点击样本，另一种方式是采用与用户点击的书籍类似的（同一分类、tag、作者等）书籍作为负样本。在Facebook 2020发表的论文中，作者提到使用曝光未点击作为hard negative带来的提升很小。因此在我们的实践中，我们随机抽取同一三级分类下用户未点击过书籍作为hard negative。鉴于样本拼接导致的存储问题，我们为每一个正样本匹配了3个hard neative，用前述的batch内负采样采集其余96个easy negative。在离线评测中，相比于baseline，增加hard negative会带来一定的提升，但是当我们将hard negative与loss修正叠加之后，得到的提升并不明显。初步猜测是因为hard negative的采样影响了样本的出现频率，对loss修正带来了一定的负向作用。目前该版本还没有上线实验，我们还在探索如何在loss修正的基础上通过增加hard negative进一步提升模型的表现。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/e4ecf2c78c3362d9bdce.png"/></p>
<p></p>
<h3><strong>四、后续优化</strong></h3>
<p>在特征与loss优化上面方面，我们还有很多可以尝试的方向。例如，引入FM模型对特征进行交叉，包括user侧、item侧内部的特征交叉已经两侧特征的相互交叉；采用CNN-DSSM以及LSTM-DSSM模型，提取小说的封面以及简介中包含的信息；引入实时的上下文特征以及用户历史点击序列；利用用户的阅读时长对不同样本的loss进行加权等。同时，基于书籍出现频率的loss修正强依赖于实际场景，很难迁移到其他分布不同的场景，我们也在探索使之更加具有泛化性的方式。除了特征与loss的优化，我们还探索了许多模型方面的优化。我们将这些优化的思路以及结果记录在《QQ浏览器：小说召回中的DSSM模型优化实践（三）》，后续会继续探索并进行线上实验。非常欢迎有这一方向探索的朋友一起交流相关经验。</p>
<p><strong>参考文献：</strong></p>
<p>[1] Covington, Paul, Jay Adams, and Emre Sargin. "Deep neural networks for youtube recommendations." <i>Proceedings of the 10th ACM conference on recommender systems</i>. 2016.</p>
<p>[2] Yi, Xinyang, et al. "Sampling-bias-corrected neural modeling for large corpus item recommendations." <i>Proceedings of the 13th ACM Conference on Recommender Systems</i>. 2019.</p>
<p>[3] Huang, Po-Sen, et al. "Learning deep structured semantic models for web search using clickthrough data." <i>Proceedings of the 22nd ACM international conference on Information &amp; Knowledge Management</i>. 2013.</p>
<p>[4] Guo, Huifeng, et al. "DeepFM: a factorization-machine based neural network for CTR prediction." <i>arXiv preprint arXiv:1703.04247</i> (2017).</p>
<p>[5] Huang, Jui-Ting, et al. "Embedding-based retrieval in  search." <i>Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery &amp; Data Mining</i>. 2020.</p>
<p></p> 
{% endraw %}
