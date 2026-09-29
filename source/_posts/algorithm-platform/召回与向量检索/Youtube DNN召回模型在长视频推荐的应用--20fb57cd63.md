---
title: "Youtube DNN召回模型在长视频推荐的应用"
date: 2022-04-06 11:18:09
categories:
  - 算法平台
  - 召回与向量检索
---

{% raw %}

<p>首先要感谢junlewang(王俊乐)，tigong(龚题)一起对模型的优化和指导，感谢owenhe(贺杰)对线上tensorflow模型加载和faiss的支持，虽然只是一次简单的深度模型的尝试，但是从中受益良多。本文将从背景，模型架构，数据处理，模型实现和训练，模型上线，最终效果，后续工作七个方面来介绍。</p>
<ul><li>
<h2><strong>背景</strong></h2>
</li>
</ul><p>目前，我们组主要专注于视频长视频推荐系统建设和效果优化，从用户的追剧到兴趣探索，为用户提供个性化的视频推荐。首先简单介绍下视频推荐中长视频的概念，这也和后面的样本采样相关。在视频首页中，长视频是以专辑（cid）的形式推荐给用户，而专辑下又会包含对应的视频（vid）。比如“风骚律师 第二季”这个专辑内包含了每一集的vid，但是在首页上推荐的时候都是以同一个cid被推荐出来的，当用户点击进入底层页播放某一集，终端又会把专辑cid和具体的vid的相关信息一起上报给后台。简单来说，就是首页长视频以cid推荐给用户。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/6afff39ee0e0fd619ede.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ce84bae809eef6d075aa.png"/></p>
<p></p>
<p></p>
<p>视频专辑的数量相比视频的数量要少得多，同时内容的质量对用户观看、付费等行为影响非常大，新热剧的播放远超其他，“内容为王”也算是很贴切的。内容当然是要好，但是长视频的头部新热聚集效应很强，如何提高个性化的效果，增强长尾分发的能力就显得非常重要了。因此在我们的推荐系统中，设计和实验了多路召回，比如追剧推荐，全网新热，item-cf，标签召回，实时关联等算法，尽可能多地召回用户可能感兴趣的专辑。其中追剧推荐的效果要远超其他算法，这也是长视频推荐的一个特性，用户更倾向于追剧，平台电视剧的播放也是最大的。而除开追剧推荐算法之外，item-cf的效果明显好于其他算法，因此我们也尝试了基于播放行为word2vec,fast-text,edges等多种cf算法，也取得了不错的收益。</p>
<p>item-cf的优势在于线上使用简单，体积小，效果好，但是用到的主要是播放列表，模型的扩展性和泛化能力相比Youtube召回模型还是要弱。Youtube召回模型虽然相比最近层出不穷的深度模型结构要简单，但在Youtube这个工业级视频推荐上能取得正向效果，还是很有实验的价值。因此，我们选择在精选的猜你喜欢和猜你在追模块增加一路Youtube召回，来实验Youtube召回模型的效果。你的精选首页不长这个样子？嗯，得益于我们的实验系统的不断优化和完善，排版样式也在不断分流实验，提高体验和效果，说不好有一天你就和这个一样了。不要在意这些细节，请耐心往下看。</p>
<ul><li>
<h2><strong>模型架构</strong></h2>
</li>
</ul><p>在介绍本部分之前，个人强烈建议阅读下这两个博客（论文相信大家早都读过了，毕竟经典），的论文给出了很多非常有意义的干货，但是有些细节可能一笔带过，没有很详尽，这两个博客从理论和实践的角度对论文进行解析，我们在模型的开发中也遇到了一些坑，通过这两篇文章也受到了启发 。</p>
<ul><li><a href="https://zhuanlan.zhihu.com/p/52169807">重读Youtube深度学习推荐系统论文，字字珠玑，惊为神文</a></li>
<li><a href="http://www.shataowei.com/2018/06/26/%E5%85%B3%E4%BA%8EDeep-Neural-Networks-for-YouTube-Recommendations%E7%9A%84%E4%B8%80%E4%BA%9B%E6%80%9D%E8%80%83%E5%92%8C%E5%AE%9E%E7%8E%B0/">关于'Deep Neural Networks for YouTube Recommendations'的一些思考和实现</a></li>
</ul><p>Youtube召回模型的解析网上已经很多，这里简要介绍下。</p>
<ul><li>
<h3>模型的输入</h3>
</li>
<li>多值离散特征：视频播放列表、搜索词表，通过embedding的方式获取每一个视频/词的隐向量，然后直接平均求和，得到一个固定长度的隐向量；</li>
<li>单值离散特征：地理位置等，通过embedding的方式获取固定长度的隐向量；</li>
<li>单值连续特征：年龄，性别等；</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/0056b867e88bc03a56f4.png"/></p>
<ul><li>
<h3>模型的结构</h3>
</li>
</ul><p>模型的第一层直接将这三类特征concat成一个向量，提供给后面的全连接层，全连接层的激活函数采用ReLU函数，最后输出一个固定维度的user向量<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>。</p>
<p>在模型训练阶段，将召回问题看成一个超大多分类问题，输入是用户向量和cid向量的内积，softmax多分类交叉熵来计算损失函数；</p>
<p>在模型线上预测阶段，通过最近邻算法（我们采用<a href="https://github.com/facebookresearch/faiss">faiss</a>）对每一个模型输出的用户向量<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>，快速求出最相关的TopK个视频。</p>
<ul><li>
<h3>损失函数</h3>
</li>
</ul><p>损失函数这里模型采用softmax的多分类交叉熵损失函数，类似word2vec的损失函数。将一次训练样本（在下面会介绍怎样构建样本）中播放的cid作为命中的分类，而cid的数量就是这个多分类问题的类目个数<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>，这里分三步介绍下损失函数,下面推导为了方便只介绍batch_size=1的情况。</p>
<ul><li>Youtube召回模型是通过最后一层输出的user向量<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>和cid的隐向量<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>的内积<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>来度量用户对该cid的兴趣程度，所以最后一层和cid的隐向量的维度应该保持一致。注意这里隐向量<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>和视频播放列表中的隐向量都是同一个隐向量矩阵，没有必要在这里再创建一个视频的隐向量矩阵。这里具体实现时也可以加上一个偏置，可以理解是让模型针对每个cid学出一个偏置，[图片未保存到本地]，内积<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>越大则用户越感兴趣。</li>
<li>通过softmax函数将用户对所有cid的兴趣程度转化成概率：</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/> </p>
<ul><li>最后利用交叉熵来得到损失函数,其中<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>是一个<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>维one-hot向量，播放的cid对应那一维是1，其余都是0</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/></p>
<p>思考一个问题，Youtube里的视频数量<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>有数百万上千万（视频中的cid大概百万级别，经过各种过滤10万级别），如果按照softmax训练效率会很低，所以这里Youtube采取了负采样（negative sampling）来解决（类似word2vec的处理），简单来说就是降低<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>中0的数量，来达到采样负样本的目的。根据上面推荐的第二篇文章的作者在博客中介绍，就这样还采样了200万负例做训练，只能说卡多任性。</p>
<ul><li>
<h2><b>数据处理</b></h2>
</li>
</ul><p>“数据与特征工程决定了模型的上限，改进算法只不过是逼近这个上限而已“，这是大学机器学习老师不断重复的名言，其实就是在说特征工程的重要性。这里主要介绍下我们在优化模型过程中几个有效数据处理方法。老实说，当时读Youtube召回这部分论文的时候，就感觉和word2vec非常相似，所以在数据处理这里会多次提到word2vec，实际运用中也确实从word2vec中获得了启发。</p>
<ul><li>
<h3>cid编码</h3>
</li>
</ul><p>在模型的具体实现时采用tensorflow的sample_softmax_loss接口实现了负采样和损失函数计算，当时踩了一个坑，这个接口在进行负采样的时候会默认调用一个<a href="https://www.tensorflow.org/api_docs/python/tf/random/log_uniform_candidate_sampler">log_uniform_candidate_sampler</a>来进行负采样，简单来说，这个采样器有一个特性，数值越小被采样到的概率越大。针对这种情况，我们对cid进行了编号，按照cid在所有用户播放历史中出现的次数降序排列，从1开始编号，即出现次数越大，编号越小，作为负样本被采样到的概率越大，0作为保留编号用于替换缺失值。这里可能要问，为什么要多采样这些出现次数大的cid作为负例？word2vec内部也是这么做的，我的理解是：一方面，这些高频cid对整体的影响更大，在作为负例的同时模型也在不断学习和优化高频cid的隐向量；另一方面，对于一些长尾的cid作为正例，用这些高频cid作为负例更能学习这些长尾cid的隐向量，避免模型预测出来的都是高频cid。不过这样编码也存在弊端，当前每天训练模型都要重新计算数据里cid的频度并重新编码，不利于模型增量更新。</p>
<ul><li>
<h3>样本选择和处理</h3>
</li>
</ul><p>不同于ctr模型，这里没有采用曝光点击数据，而是直接采用了用户在首页的播放数据来构造样本。那怎样构造样本呢？首先，我们先得到一个用户的播放序列。这里再回顾下专辑cid的概念，专辑cid包含了多个视频vid，首页以cid的形式推荐。所以一个用户一段时间的cid序列按照时间升序排列后极可能出现cid连续的情况，比如<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>。由于此前在做word2vec版本的item-cf召回时，我们曾为了节省空间和性能，尝试了对原始播放序列进行相邻cid去重后输入给word2vec模型，也取得了不错的效果。于是第一版本我们沿用了这一做法，<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>。</p>
<p>在获得<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>后，类似word2vec的方法，按照一定的窗口滑动构建样本，比如这里假设窗口最大是3，那么<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>会得到下面几条样本：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/></p>
<p>在初期我们想让模型仅用播放序列的特征直接达到word2vec的效果，就没有加其他特征直接训练模型。这里我们写了一个工具来辅助我们进行模型效果的评估，能把一个用户输入的的cid播放列表和模型预测的最感兴趣的cid列表同时以专辑标题和封面的形式直观地展示出来，这对于我们前期调试模型非常重要，能够快速检验模型是否有效。在第一版本上线后，我们就发现了模型的问题，这是第一版模型预测的结果：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8253974003f5cdcda2ed.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7fb8ba5cb2cd070e1f8b.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/410970c1736c799350c2.png"/></p>
<p>很明显，对于不同观看历史的用户，模型预测出来的结果已经有一定的区分度，比如针对上图的三种类型播放历史的用户，模型都分别预测出了电影、电视剧和动漫，但是在头部都出现了《神探蒲松龄》这部在平台上播放上亿次的cid，由此可见高频cid对模型的影响还是很大。但是对比word2vec版本的icf，我们发现就不会有这么明显的头部效应，再次读了下<a href="https://papers.nips.cc/paper/5021-distributed-representations-of-words-and-phrases-and-their-compositionality.pdf">word2vec论文</a>和<a href="https://github.com/chrisjmccormick/word2vec_commented">word2vec源码</a>后发现，内部对序列进行了高频采样，并且论文中的列出的高频采样的公式跟实际源码实现中还不太一致。论文中，词在每次样本中被保留的概率为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/></p>
<p>其中<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>表示阀值,通常取<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>，<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>表示<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>出现的频次。</p>
<p>但是实际源码中，高频词在每次样本中被保留的概率实现如下：</p>
<div>
<pre>if (sample &gt; 0) {
  // Calculate the probability of keeping 'word'.
  real ran = (sqrt(vocab[word].cn / (sample * train_words)) + 1) * (sample * train_words) / vocab[word].cn;
  
  // Generate a random number.
  // The multiplier is 25.xxx billion, so 'next_random' is a 64-bit integer.
  next_random = next_random * (unsigned long long)25214903917 + 11;

  // If the probability is less than a random fraction, discard the word.
  //
  // (next_random &amp; 0xFFFF) extracts just the lower 16 bits of the 
  // random number. Dividing this by 65536 (2^16) gives us a fraction
  // between 0 and 1. So the code is just generating a random fraction.
  if (ran &lt; (next_random &amp; 0xFFFF) / (real)65536) continue;
}</pre>
</div>
<p>转化成公式即：</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>表示词的频率，从下图可以看出，高频词被保留的概率更小，词频概率&lt;=0.0026时，词一定会保留；词频概率&lt;=0.00746时，词被保留的概率是0.5；当词频=1.0时,词被保留的概率是0.033。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8bf2cc078db9846a57cb.png"/></p>
<p>具体哪种更可信暂时没有找到准确的官方解释，但是作为程序员比起论文还是更相信源码，于是在我们生成样本时采用ran对应的公式对cid进行抽样。注意这里是每次生成样本时进行高频抽样，比如cid1在<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>这条样本中抽样被丢弃，但是在<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25d269c5507f531611eb.gif"/>这条样本中抽样又可能会保留。通过这样的方法，实现了对训练样本进行高频采样的目的。第二版的效果头部效应就明显好很多,直观上内容的相关性也更高，2个epoch之后模型的loss也从2.8下降到1.35（也与数据分布变化有关）：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/01002566326e93d5a6c6.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/74314770ac7f9bb4098a.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b052be93e9a010ba692a.png"/></p>
<ul><li>
<h3>增加特征</h3>
</li>
</ul><p>在只采用用户播放列表达到我们期望的同word2vec相似的效果之后，我们又陆续加入了用户的基础属性特征，用户的画像标签，不仅可以将用户更多的特征利用起来，同时针对那些短期内没有播放列表或者播放很少的用户，也起到一定冷启动和更加个性化的作用。比如下面这两个用户就由于画像里不同的标签影响到模型最后的召回预测。不过加入画像信息可能也会一定程度上损害相关度，因为画像的标签可能由于累积时间窗口过长，累积多个设备导致无法突出用户最近的行为，所以在我们最终上线的版本没有加上用户的标签信息，只增加了用户的基础画像。</p>
<p>用户A<br/><br/>  <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/713a69ae26f742d5cce9.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ad03ce5fd18c8ef576e2.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/633a52839ec77e3aa83d.png"/></p>
<p>用户B：<br/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5d3c9817336c8b0933f9.png"/><br/>  </p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/aab04d4669435cb85a89.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7cb5a2dd8cf745677c86.png"/></p>
<p></p>
<ul><li>
<h2><strong>模型实现和训练</strong></h2>
</li>
</ul><p>模型采用tensorflow实现，数据传到cephes后在tesla上用GPU训练，模型的架构清楚后就是import tensorflow as tf搭积木了，Youtube这个模型虽然非常有名，rank模型经常作为各种deep ctr模型的baseline来对比。但是DNN召回模型的开源实现相对较少，公司内部git上倒是有一些大佬们开源的实现（赞），大家也可以搜索看下，模型很简单，这里就放几个关键部分的示例代码片段。</p>
<ul><li>
<h3>输入处理</h3>
</li>
</ul><p>模型输入这里，样本通过spark处理成tfrecord的格式传到cephes上，输入解析采用tensorflow Dataset的API，这样可以很方便地支持多线程读取数据。</p>
<div>
<pre>def decode_train(example):
    example = tf.identity(example, name='example')
    features = tf.parse_example(example,
        features={
            "label": tf.FixedLenFeature([], tf.int64, default_value=0),
            "age": tf.FixedLenFeature([], tf.int64, default_value=0),
            "sex": tf.FixedLenFeature([], tf.int64, default_value=0),
            "profession": tf.FixedLenFeature([], tf.int64, default_value=0),
            "province": tf.FixedLenFeature([], tf.int64, default_value=0),
            "city": tf.FixedLenFeature([], tf.int64,default_value=0),
            "education": tf.FixedLenFeature([], tf.int64,default_value=0),
            "vip": tf.FixedLenFeature([], tf.int64,default_value=0),
            "hist": tf.VarLenFeature(tf.int64)
        })
    hist = features['hist']
    labels = features['label']
    return hist,features,labels

def get_features(data_dir, batch_size):
    filenames = get_filenames(data_dir)
    files = tf.data.Dataset.list_files(filenames)
    ds = files.apply(tf.contrib.data.parallel_interleave(tf.data.TFRecordDataset, cycle_length=8))
    ds = ds.shuffle(batch_size)
    ds = ds.batch(batch_size).prefetch(1)
    iterator = ds.make_initializable_iterator()
    return iterator</pre>
</div>
<p> </p>
<ul><li>
<h3>特征处理</h3>
</li>
</ul><p>特征处理主要采用feature_column API的方式，根据特征的分布情况进行了相应的离散化处理。播放列表hist的处理需要试验id映射，加权平均，attention等更复杂，所以单独拿出来进行了处理</p>
<div>
<pre>def get_feature_columns():
    # age 有-1的值,并且占比很大，所以要单独分出来
    age_col = fc.bucketized_column(fc.numeric_column("age"), boundaries=[10, 18, 25, 30, 35, 40, 45, 50, 55, 60, 65])
    # gender就三个值
    gender_col = fc.indicator_column(fc.categorical_column_with_identity("sex",num_buckets=3,default_value=0))
    # profession_id取值[0,1,2,3,4,5,6,7,41]
    profession_col = fc.indicator_column(fc.categorical_column_with_identity("profession",num_buckets=9,default_value=0))
    province_col = fc.indicator_column(fc.categorical_column_with_identity("province",num_buckets=35,default_value=0))
    # city取值太多，先不加
    city_col = fc.embedding_column(fc.categorical_column_with_hash_bucket("city", 500,dtype=tf.int32), 16)
    # grade,取值[0,7]
    grade_col = fc.indicator_column(fc.categorical_column_with_identity("education",num_buckets=8,default_value=0))
    # vip 取值[0,1,-1]
    vip_col = fc.indicator_column(fc.categorical_column_with_identity("vip",num_buckets=3,default_value=0))
    cols = [age_col,gender_col,profession_col,province_col,city_col,grade_col,vip_col]
    return cols</pre>
</div>
<p> </p>
<ul><li>
<h3>模型构建</h3>
</li>
</ul><p>在Youtube的模型架构上加入一些预训练，加权平均，attention，batch_mormalize等特性，输出一个user_v的向量</p>
<div>
<pre>    def build_model(self,is_training=True,use_pretrain=0):
        self.item_b = tf.get_variable("item_b", [self.num_item], initializer=tf.constant_initializer(0.0))
        if use_pretrain == 1:
            pretrain_emb_matrix = self.load_pretrain_emb()
            self.item_emb_matrix = tf.get_variable(name="hist_emb", shape=[self.num_item, self.embed_size],
                                               dtype=tf.float32, initializer=tf.constant_initializer(pretrain_emb_matrix))
        else:
            self.item_emb_matrix = tf.get_variable(name="hist_emb", shape=[self.num_item, self.embed_size],
                                                   dtype=tf.float32, initializer=tf.truncated_normal_initializer)
        # 播放id列表embedding加权平均 
        # sp_ids = tf.SparseTensor(indices=self.hist.indices, values=self.hist.values, dense_shape=[self.batch_size, self.num_item])
        # hist_emb = tf.nn.embedding_lookup_sparse(self.item_emb_matrix, sp_ids=sp_ids, sp_weights=sp_weights, combiner="mean")
        # attention
        hist_emb = self.attention_layer(self.hist)
        # 用户基础画像特征+播放标签
        cols = get_feature_columns()
        print(cols)
        user_profile = fc.input_layer(self.other_features,cols)

        self.layers = [None]*(len(self.layers_unit)+2)
        last_layer_size = self.embed_size # 最后一层必须和item的embedding size一致
        self.layers_unit.append(last_layer_size)
        self.layers[0] = tf.concat([user_profile,hist_emb],axis=1)
        for l,num_unit in enumerate(self.layers_unit):
            input_layer = tf.layers.batch_normalization(self.layers[l],training=is_training)
            # input_layer = self.layers[l]
            self.layers[l+1] = tf.layers.dense(input_layer,num_unit,activation=tf.nn.relu,name="layer-%d" % (l+1))
        self.user_v = tf.identity(self.layers[-1],name='user_v')</pre>
</div>
<p> </p>
<ul><li>
<h3>模型训练</h3>
</li>
</ul><p>模型训练这块采用了tensorflow的sample_softmax_loss接口实现了负采样和损失函数计算，采用Adam算法作为模型优化器</p>
<div>
<pre>    def train(self):
        soft_loss = tf.nn.sampled_softmax_loss(self.item_emb_matrix, self.item_b, labels=tf.reshape(self.labels,[-1,1]),
                       num_classes=self.num_item, inputs=self.user_v, num_sampled=100,partition_strategy="div")
        self.loss = tf.reduce_mean(soft_loss)
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            self.opt = tf.train.AdamOptimizer(learning_rate=self.lr).minimize(loss=self.loss)</pre>
</div>
<ul><li>
<h2> <strong>模型上线</strong></h2>
</li>
</ul><p>模型最终上线的方式是调用tensorflow C++的API来实现的。但是最初我们采用的是离线列表的方式，即在模型训练好之后，我们会在实验系统上选取一个分桶的用户(1kw左右)，然后模型离线预测出这个分桶用户的召回列表，存储到线上redis中，这样在这个分桶的用户上实验深度召回时就可以直接去redis上读取。主要是因为在模型开发初期，模型结构，特征输入等都需要优化，线上引擎当时还没有完全支持tensorflow模型的加载和预测；其次这种方式也方便模型快速迭代和查看效果。在我们离线列表取得一定正向效果之后，就开始配合后台同学进行线上实时开发，这里主要包括模型离线打包，C++加载模型和预测，faiss求TopK三个方面。</p>
<ul><li>
<h3>模型离线打包</h3>
</li>
</ul><p>利用tensorflow的freeze_graph工具或者内部的tf.graph_util将模型的图结构和参数生成一个文件，可参考<a href="https://medium.com/@prasadpal107/saving-freezing-optimizing-for-inference-restoring-of-tensorflow-models-b4146deb21b5">Saving, Freezing, Optimizing for inference, Restoring of tensorflow models</a>；</p>
<p>导出所有cid对应的embedding向量，用于线上求TopK；</p>
<p>在这里当时踩了一个坑，我们直接将训练过程中生成的模型freeze了，导致预测时结果不正常，结果都几乎一致。后来发现是batch_normalize传入了一个is_training的值，训练时设置为True，预测时False。后来单独为预测导出了模型，线上打分才正常。</p>
<ul><li>
<h3>C++加载模型和预测</h3>
</li>
</ul><p>这里搭建环境可参考<a href="https://www.jianshu.com/p/d46596558640">TensorFlow C++动态库编译</a></p>
<p>接口主要是一个加载接口和一个预测接口，可参考<a href="https://www.tensorflow.org/guide/extend/cc">tensorflow C++ API</a></p>
<div>
<pre>// Load the protobuf graph
GraphDef graph_def;
status = ReadBinaryProto(Env::Default(), "./freeze-model.pb", &amp;graph_def);
// Run the session, evaluating our "c" operation from the graph
status = session-&gt;Run(inputs, {"user_v"}, {}, &amp;outputs);</pre>
</div>
<ul><li>
<h3>faiss求TopK</h3>
</li>
</ul><p>这里<a href="https://github.com/facebookresearch/faiss">的github</a>上有详细的介绍，但是在实际使用中我们还是遇到了一些问题。Faiss支持欧氏距离（L2）和内积（IP）方式，通过构建索引来加快查询的速度，几种最常用索引的如下。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/149fb5beacc7da91ce6f.png"/></p>
<p>由于我们需要计算的是内积，所以直接尝试了IndexFlatIP,IndexIVFFlat这两种索引，但是线上在均衡效果和时耗的情况下都没有符合我们的预期。IndexHNSWFlat性能非常好，但是只支持L2。我们知道，只有当两个向量都是单位向量时，这两个向量的欧氏距离和内积才是等价的，这里有两个解决思路：</p>
<p>一是在模型训练的时候给用户向量和cid向量增加L2正则化，用户向量可以在输出时正则化，但是cid向量在更新中不断变化，每次都对所有cid进行正则化，训练非常低效，效果也不好；</p>
<p>二是想办法把内积转化成欧式距离的问题，这里xbox团队在<a href="http://ulrichpaquet.com/Papers/SpeedUp.pdf">《Speeding Up the Xbox Recommender System Using a Euclidean Transformation》</a>给出了解法。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/89a4c270a879ba7f360f.png"/></p>
<p>通过将cid向量增加一维<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/543a6af3c4967af19838.png"/>,  用户向量在query时增加一维0，这样新向量间的欧氏距离和原向量的内积刚好成负相关关系，这样就可以使用IndexHNSWFlat来完成TopK的查询。（这里感兴趣可以详细参考junlewang(王俊乐)的文章长视频推荐:基于欧氏转换的top-k内积解决方案）</p>
<p>在M=32的基础上，离线测试faiss计算出来的top100个的cid相比暴力计算，覆盖准确度到了86%以上，基本具备上线条件。</p>
<ul><li>
<h2><strong>最终效果</strong></h2>
</li>
</ul><p>我们在精选首页的猜你会追和猜你喜欢两个模块增加了Youtube DNN召回（index2358），发现在频道整体对比base（index2366）各项指标都正向，曝光人均vv提升2%，播放转化率提升1.8%，曝光人均时长提升2%。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a83d53ea0629cdaca51f.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b6f2ff5fb28b5bc55fe7.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a1bda64b7e5749c0f99d.png"/></p>
<p>在猜你会追模块内部，除了追剧推荐算法（用户的强追剧行为，出在头部，远高过其他算法，其他算法作为补足），Youtube DNN召回算法的效果是所有补足召回算法中最好的，超过了item-cf。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9262d528f52d2dc78660.png"/></p>
<p>在猜你喜欢模块内部，所有召回算法混排，Youtube DNN召回算法的效果也是最好的。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/38292c63ec55d6cf9ebd.png"/></p>
<ul><li>
<h2><strong>后续工作</strong></h2>
</li>
</ul><p>现在Youtube DNN模型的线上版本还只是用了用户的播放列表，基础画像等特征，还有很多特征可以考虑加入，比如上下文特征，用户统计特征等。模型结构也还可以进行优化，对播放列表进行时间衰减，时长/次数等加权，尝试DIN中的attention机制等。再次感谢junlewang(王俊乐)，tigong(龚题)，owenhe(贺杰)共同的努力使得Youtube DNN召回模型能在视频长视频推荐成功落地，感恩团队对我们实验的支持，希望未来我们能做得更好。</p>
<p>相关代码可见：[内部或本地链接已移除]</p> 
{% endraw %}
