---
title: "短视频分类进化：从LR到LSTM"
date: 2022-04-24 09:53:19
categories:
  - deep-learning
---

{% raw %}

<div>
<p></p>
<h2>前言</h2>
<p>由于深度学习近年来在图像领域的巨大成功，其他领域如语音、NLP等领域的研究也逐渐被深度学习所统治，而且其结果几乎都是 "state of the art"。为了跟上这波趋势，我使用深度学习中的LSTM网络对短视频分类进行了尝试，并与目前使用的传统分类方法（LR）进行对比，的确取得了更好的效果。</p>
<h2>短视频分类任务介绍</h2>
<p>对我们浏览器来说，短视频内容都是合作方提供，拿不到视频内容，只有视频链接和视频标题。所以如果想通过机器学习的方法对短视频进行分类，能拿到的信息只有视频的标题。幸运的是，短视频基本都是标题党，标题基本也包含了视频内的主要信息，如下图所示：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/deep-learning/a3536e3f1cc1ad6a8d3c.png"/></p>
<p>图1</p>
<p>      我们的短视频分类任务包括两部分：</p>
<p>1）从上报的所有视频站点标题里识别出短视频，这是一个二分类的问题。</p>
<p>2）对识别出的短视频，需要进行类别的识别。目前我们运营主推的短视频包含4类：娱乐、生活、搞笑、奇闻，是一个4分类的任务。</p>
<p>另一方面的问题是整个任务的训练样本构造。由于人力有限，没有专门的同事来对短视频及短视频的类别进行标注，只有合作方提供的一些带标注的样本，累计差不多200条。这么少的样本量来训练机器学习模型基本上会过拟合。所以我写了个爬虫抓取了合作方之一的的站点的所有短视频及其分类信息，去除不需要的类别，剩下的就可以加入到有类别的短视频中。这样处理后，有标注的短视频总量为16519。在从上报的视频站点标题里抽样本部分非短视频的样本，两部分加起来样本总量为86040。另外，从爱奇艺、视频拿了最近1个月内标注好的热门短视频和帅选的一些非短视频标题作为新测试集，共1000条，用来测试模型的泛化能力。</p>
<h2>传统机器学习方法</h2>
<p>对文本分类来说，由于维度高，特征也高度稀疏，传统机器学习方法中效果较好的就是LR和线性SVM。对标题的建模方法是采用经典的词袋模型，先对标题进行分词，去除停用词和其他词频较小的词，词库大小为20000，对词采用one-hot向量化。</p>
<p>1. 识别短视频二分类</p>
<p>主要尝试了LR和线性SVM模型，训练时按4:1来切分训练集与测试集，效果如下：</p>
<div>
<table><tbody><tr><td>
<p>模型</p>
</td>
<td>
<p>样本中测试集准确率</p>
</td>
<td>
<p>新测试集准确率</p>
</td>
</tr><tr><td>
<p><b>LR</b></p>
</td>
<td>
<p>0.960</p>
</td>
<td>
<p>0.876</p>
</td>
</tr><tr><td>
<p><b>SVM</b></p>
</td>
<td>
<p>0.966</p>
</td>
<td>
<p>0.852</p>
</td>
</tr></tbody></table></div>
<p>表1</p>
<p>可以看到，LR和SVM在训练集上都已达到了很高的准确率，而且相差不大。但是，在新的测试集上，准确率有明显的下降。这个主要是采用one-hot建模方式的固有缺陷。新测试集上出现了不少没有在训练集上出现的新词，这些词不能映射到已有的词典里就只能丢弃，而原来的模型也没有学到这些信息，所以会降低模型的泛化能力。</p>
<p>2. 短视频多分类</p>
<p>短视频目前共分4类，每类的数量为：奇闻: 6720，生活: 2520，搞笑: 3736，娱乐: 3543。新测试集中主要是奇闻和娱乐，其他类别太少，不参与评估。奇闻数量为694，娱乐数量为90。多分类的分类器是LR，效果如下：</p>
<table><tbody><tr><td>
<p>模型</p>
</td>
<td>
<p>类别</p>
</td>
<td>
<p>样本中测试集准确率</p>
</td>
<td>
<p>样本中测试集召回率</p>
</td>
<td>
<p>新测试集准确率</p>
</td>
<td>
<p>新测试集召回率</p>
</td>
</tr><tr><td rowspan="5">
<p><b>LR</b></p>
</td>
<td>
<p>总体</p>
</td>
<td>
<p>0.88</p>
</td>
<td>
<p> </p>
</td>
<td>
<p>0.81</p>
</td>
<td>
<p> </p>
</td>
</tr><tr><td>
<p>奇闻</p>
</td>
<td>
<p>0.89</p>
</td>
<td>
<p>0.89</p>
</td>
<td>
<p>0.96</p>
</td>
<td>
<p>0.86</p>
</td>
</tr><tr><td>
<p>生活</p>
</td>
<td>
<p>0.87</p>
</td>
<td>
<p>0.94</p>
</td>
<td>
<p> </p>
</td>
<td>
<p> </p>
</td>
</tr><tr><td>
<p>搞笑</p>
</td>
<td>
<p>0.81</p>
</td>
<td>
<p>0.70</p>
</td>
<td>
<p> </p>
</td>
<td>
<p> </p>
</td>
</tr><tr><td>
<p>娱乐</p>
</td>
<td>
<p>0.92</p>
</td>
<td>
<p>0.97</p>
</td>
<td>
<p>0.63</p>
</td>
<td>
<p>0.79</p>
</td>
</tr></tbody></table><p>表2</p>
<p>可以看到，对这个多分类问题，LR的总体准确率还不错。但在新测试集中，娱乐的分类准确率很差。这个主要是新测试集中娱乐的样本出现了不少新明星（娱乐类短视频就是明星相关），所以基于词袋模型的LR就有点无能为力了。而奇闻类的样本则取得了优于训练样本的结果。新测试集中的娱乐类样本相对有点极端，模型上线的时候每天进行一次训练能一定程度上降低这个问题的影响。</p>
<h2>使用LSTM网络分类</h2>
<p>1.LSTM简介</p>
<p>RNN(Recurrent Neural Networks)是一种包含循环结构的神经网络，主要用来处理连续的序列问题，比如股票预测、机器翻译、语音识别等。它的问题主要是当网络变深变大后会带来梯度消失或梯度爆炸的问题，非常难以训练。而LSTM（Long-Short Term Memory）是一种改进的RNN网络结果，部分上解决了传统RNN网络难以训练的问题。目前，LSTM在自然语言处理等领域已经有了很多成功的应用，如文本分类、机器翻译等。关于LSTM网络的具体介绍推荐看这篇文章：<a href="http://colah.github.io/posts/2015-08-Understanding-LSTMs/">http://colah.github.io/posts/2015-08-Understanding-LSTMs/</a>。</p>
<p>2.训练词向量</p>
<p>由于原始样本只有86040条，单纯用这么少的数据量训练词向量。由于训练词向量并不要求对样本进行标注，所以词向量的训练并不受这批样本的影响，原则上肯定是数据量越大越好。由于此向量能很好地反映词的相关性，我刷选了一天可能要预测的视频站点标题加入到原有的短视频样本中，使样本量扩展到80w+（如果上分布式训练可以用更大的样本集）。由于在window 7上进行开发，就用python版的wrod2vec工具gensim来训练词向量。词向量维数设置为100，训练出来的词向量词典大小为38053。gensim训练词向量的代码特别简单：</p>
<div>
<pre>model = gensim.models.Word2Vec(sentences, size=100, 
        window=5, min_count=3, sg=1,  max_vocab_size=vocabulary_size)
model.wv.save_word2vec_format(wrod2vec,
                 "word2vec/vocabulary",binary=False)
</pre>
</div>
<p> 3.      识别短视频二分类</p>
<p>从上面的实践可以看到，使用线性模型（LR）就能对短视频分类取得比较好的效果，复杂的非线性模型（如GBDT、SVM）效果可能还不如LR。因此对短视频分类来说，由于特征是高维稀疏的，所以是一个偏线性的模型。在异乡文献中对文本分类的实践也一般都是简单模型反而能取得比较好的效果。所以我在使用LSTM网络对短视频进行分类时，也只设计了一个隐含层，输入层就是标题分词后word embedding的结果，输出层采用全连接的softmax回归进行分类。另一方面也是由于样本量特别少，设计过于复杂的网络结果也很容易造成过拟合。网络结构如下：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/deep-learning/b3f44d25d725f98df821.png"/></p>
<p>图3</p>
<p>由于数据量较少，直接用公司办公机进行训练，训练框架采用TensorFlow 1.2 GPU版本。公司的办公机配置还可以，GPU是GTX660,2G显存。</p>
<p>对于上述LSTM网络结构，隐含层设置为128，序列长度设置为15，LSTM层dropout的值设置为0.5。其中序列长度原则上应该选分词后的标题的最大词数。经统计发现，词数最大是33，词数小于15的达到了0.99。但是，随着序列长度的增大，训练时间会变得越长，而且由于样本量较少，过大的序列长度也容易引起过拟合。所以，综合上述考虑就选择序列长度为15.相关代码如下：</p>
<div>
<pre># Network Parameters
n_input = 100
n_steps = seq_len# timesteps
n_hidden = 128 # hidden layer num of features
n_classes = 2 #
#tf Graph input
x = tf.placeholder(tf.float32, [None, n_steps, n_input])
y = tf.placeholder(tf.float32, [None, n_classes])
# Define weights
weights = {
'out' : tf.Variable(tf.random_normal([n_hidden, n_classes]))
}
biases = {
'out': tf.Variable(tf.random_normal([n_classes]))
}

defRNN(x, weights, biases, keep_prob):
    # Unstack to get a list of 'n_steps' tensors of shape (batch_size, n_input)
    x = tf.unstack(x, n_steps, 1)
    # Define a lstm cell with tensorflow
    lstm_cell = rnn.BasicLSTMCell(n_hidden, forget_bias=1.0)
    # Get lstm cell output
    outputs, states = rnn.static_rnn(lstm_cell, x, dtype=tf.float32)
    # Linear activation, using rnn inner loop last output
    lstm_out = tf.matmul(outputs[-1], weights['out']) + biases['out']
    out_drop = tf.nn.dropout(lstm_out, keep_prob)
    return out_drop

keep_prob = tf.placeholder(tf.float32)
pred = RNN(x, weights, biases, keep_prob)
# Define loss and optimizer
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
# Evaluate model
correct_pred = tf.equal(tf.argmax(pred,1), tf.argmax(y,1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32)) </pre>
</div>
<p>      训练结果与LR做了对比如下：</p>
<div>
<table><tbody><tr><td>
<p>模型</p>
</td>
<td>
<p>样本中测试集准确率</p>
</td>
<td>
<p>新测试集准确率</p>
</td>
</tr><tr><td>
<p><b>LR</b></p>
</td>
<td>
<p>0.960</p>
</td>
<td>
<p>0.876</p>
</td>
</tr><tr><td>
<p><b>LSTM</b></p>
</td>
<td>
<p>0.974</p>
</td>
<td>
<p>0.929</p>
</td>
</tr></tbody></table></div>
<p>表3</p>
<p>从对比可以看到，LSTM在样本测试集中准确率提高了0.014，而且在新测试集中仍然表现了较好的性能，比LR具有更好的泛化能力，准确率提高了0.053。这个提升个人觉得除了LSTM模型本身的能力外，还有就是因为训练词向量时采用了更大的数据集，词库也更大。这就使得原来没有在有标注的样本中出现过的词但是在词向量训练集中出现的词的信息没有丢失，这些词在新测试集中出现时能对分类发挥作用，但是原来使用基于词袋模型的建模方法就只能丢弃这个词。举个例子，词向量结果中“李易峰”相似度最高的前三个词为：</p>
<p>('陈伟霆', 0.816763162612915), ('赵丽颖', 0.8164128661155701), ('杨洋', 0.7692270874977112)</p>
<p>       如果“陈伟霆”并没有出现在有标注的短视频标题中，但是出现在新测试集里，它会发挥与原来“李易峰”在有标注的短视频标题中类似的作用。</p>
<p>4. 短视频多分类</p>
<p>对于4分类的短视频问题，LSTM的网络结构跟上述二分类的一样。开始时直接对样本进行训练。整体准确率为0.86，比LR的效果（0.88）还差。后来发现LSTM进行多分类时对类别平衡具有一定的敏感性，于是对样本中类别少的类进行过采样再进行训练，分类效果就有了很大的提升： </p>
<table><tbody><tr><td>
<p>模型</p>
</td>
<td>
<p>类别</p>
</td>
<td>
<p>样本中测试集准确率</p>
</td>
<td>
<p>样本中测试集召回率</p>
</td>
<td>
<p>新测试集准确率</p>
</td>
<td>
<p>新测试集召回率</p>
</td>
</tr><tr><td rowspan="5">
<p><b>LR</b></p>
</td>
<td>
<p>总体</p>
</td>
<td>
<p>0.88</p>
</td>
<td>
<p> </p>
</td>
<td>
<p>0.81</p>
</td>
<td>
<p> </p>
</td>
</tr><tr><td>
<p>奇闻</p>
</td>
<td>
<p>0.89</p>
</td>
<td>
<p>0.89</p>
</td>
<td>
<p>0.96</p>
</td>
<td>
<p>0.86</p>
</td>
</tr><tr><td>
<p>生活</p>
</td>
<td>
<p>0.87</p>
</td>
<td>
<p>0.94</p>
</td>
<td>
<p> </p>
</td>
<td>
<p> </p>
</td>
</tr><tr><td>
<p>搞笑</p>
</td>
<td>
<p>0.81</p>
</td>
<td>
<p>0.70</p>
</td>
<td>
<p> </p>
</td>
<td>
<p> </p>
</td>
</tr><tr><td>
<p>娱乐</p>
</td>
<td>
<p>0.92</p>
</td>
<td>
<p>0.97</p>
</td>
<td>
<p>0.63</p>
</td>
<td>
<p>0.79</p>
</td>
</tr><tr><td rowspan="5">
<p><b>LSTM</b></p>
</td>
<td>
<p>总体</p>
</td>
<td>
<p>0.95</p>
</td>
<td>
<p> </p>
</td>
<td>
<p>0.84</p>
</td>
<td>
<p> </p>
</td>
</tr><tr><td>
<p>奇闻</p>
</td>
<td>
<p>0.93</p>
</td>
<td>
<p>0.92</p>
</td>
<td>
<p>0.96</p>
</td>
<td>
<p>0.87</p>
</td>
</tr><tr><td>
<p>生活</p>
</td>
<td>
<p>0.96</p>
</td>
<td>
<p>0.98</p>
</td>
<td>
<p> </p>
</td>
<td>
<p> </p>
</td>
</tr><tr><td>
<p>搞笑</p>
</td>
<td>
<p>0.92</p>
</td>
<td>
<p>0.92</p>
</td>
<td>
<p> </p>
</td>
<td>
<p> </p>
</td>
</tr><tr><td>
<p>娱乐</p>
</td>
<td>
<p>0.97</p>
</td>
<td>
<p>0.97</p>
</td>
<td>
<p>0.75</p>
</td>
<td>
<p>0.89</p>
</td>
</tr></tbody></table><p>表4</p>
<p>       跟二分类的结果一样，LSTM的效果对比LR的结果也有了一定的提升。从对比可以看到，LSTM在样本测试集中准确率提高了0.07，而且在新测试集中仍然表现了较好的性能，总体准确率提升了0.03，其中娱乐类提升较大，从0.66提升到了0.75，而且也提升了召回率。新测试集中总体准确率看起来提升不大明显是因为新测试集的样本分布太不均衡（奇闻数量为694，娱乐数量为90），在实际数据中的类别分布并没有这么不平衡，所以实际效果肯定有更大的提升。这个提升的原因分析与二分类的结果类似。</p>
<h2>总结</h2>
<p>从短视频分类的实践中，可以看到LSTM在文本分类中的确能取得比传统分类模型更好的效果。虽然在应用中的LSTM网络的深度都不太深（只有1层隐层），但是取得的效果也已经非常不错。当然，如果有更多有标注的样本，设计更复杂的网络肯定能取得更好的效果。另一方面，由于深度学习的黑盒特性，调参的确是个苦力活，比如LSTM网络的层数、序列长度、dropout的设置、训练事batch_size的大小等等，这些参数都有可能对结果产生很大的影响。对应深度学习调参，需要多看paper，多实践，目前还是缺乏有效理论指导。</p>
<p>PS：感谢calvinlai对本文工作的指导~</p>
<p> </p>
<p> </p>
</div> 
{% endraw %}
