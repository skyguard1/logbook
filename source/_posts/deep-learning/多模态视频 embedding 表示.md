---
title: "多模态视频 embedding 表示"
date: 2022-04-18 14:50:10
categories:
  - deep-learning
---

{% raw %}

<h2>背景介绍</h2>
<p>推荐系统需要同时理解 user 和 item，并在当前 context 下给出推荐结果。能否准确的理解 user 和 item 将直接影响推荐效果的好坏，也是推荐技术中的一项挑战。在短视频推荐等应用场景中，对视频的理解是否准确会直接影响推荐的效果。视频作为一种多媒体载体，同时包含文本、语音和图像，直接对视频原始内容理解难度较大。一种常见的思路是学习视频的 embedding 表示，并将 embedding 向量用户召回和排序模型中。</p>
<p>目前在推荐系统中广泛使用的方式是基于 word2vec 的思想，将 item 看成 word，用户点击 item 的序列当做一个 sentence，采用 skip-gram 或者 cbow 的方式学习 itme 的 embedding 表示[1][2]。该方法实现简单，在视频推荐中取得了非常好的效果，但是也存在一定的问题。首先视频 embedding 的生成完全基于用户的点击序列，没用充分利用视频本身信息和其它 meta 信息；其次，该方法对于行为非常稀疏的视频 embedding 效果往往一般；同时，对于新产生的视频，需要积攒一段时间行为数据才能基于点击序列训练模型得到 embedding 表示，此外，模型无法保证历史的 embedding 和新产生的 embeedding 在同一个 embedding 空间中，限制了 embedding 向量的使用场景。</p>
<p>在火锅视频推荐系统的开发中，我们参考文献[3]，并结合我们实际的业务场景，基于视频封面图和描述学习视频的 embedding 表示并将用于线上推荐系统中，本方案主要的优点：</p>
<p><strong>（1）充分利用了视频本身封面图和描述信息。</strong></p>
<p><strong>（2）新视频实时计算 embedding 表示，并能保证 embdding 在同一个空间内</strong></p>
<h2>设计思路</h2>
<p>模型整体网络结构如图 1 所示，输入视频封面图和描述信息，输入视频的 embedding 表示。模型主要包含 2 个部分：Feature Extractor Network 和 Embedding Network，其中 Feature Extractor network 的作用为分别提取视频封面图特征和文本特征，Feature Extractor 输出的 Image Feature 和 Text Feature 作为 Embedding Network 的输入，Embedding Network 计算最终的视频  embedding 向量。下面我们分别描述 Feature Extractor 和 Embedding Network 的设计流程。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/8c71539827a99db245c9.png"/></p>
<p>图 1 多模态视频 embedding 整体网络结构</p>
<h3>Feature Extractor</h3>
<p>Feature Extractor 包含 Image Feature Extractor 和 Text Feature Extractor。其中 Image Feature Extractor 用于从视频封面图中提取图像特征，图像识别领域有很多经典的网络结构可选，如 AlexNet、VGG、GoogleNet、ResNet 等，综合考虑模型效果和计算效率，最终选择 ResNet-50 作为 Image Feature Extractor。ResNet-50 最后一层全连接输出维度为 2048，Image  Feature Extractor 以这一层作为输出的图像特征。在实践中，考虑到图像数据重新训练需要大量的封面图标注数据和 GPU 资源，我们使用<a href="https://github.com/tensorflow/models"> Tensorflow Model Zoo</a> 中开源的 ResNet-50 作为我们的 Image Feauter Extractor ，后续可以考虑基于我们现有的图片数据做 finetuning，学习封面图更好的图片表示特征。</p>
<p>Text Feature Extractor 作用是计算视频描述的文本特征表示，这里我们采用 pre-trained 词向量 + TextCNN[6] 的方法，以全站的短视频描述信息作为语料库，训练 word2vec 模型，去掉低频词后词向量大约为 39W。TextCNN 训练语料为抽取的 20W 条带有类别的视频数据，视频二级类别作为视频的 label 训练监督学习模型。TextCNN 的最后一个全连接层作为 text feature，维度为 256。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/4abc5f7bdba13c4970fd.png"/></p>
<p>图 2 TextCNN</p>
<h3>Embedding Network</h3>
<p>Embedding network 的主要目标是学习输入特征到 embedding 空间的映射 f。网络结构非常简单，如图 3 所示，模型输入为 Image Feature 和 Text Feature 的特征拼接，分别经过一个 512 维和 256 维的 full connect layer，激活函数为 ReLU，最后对输入特征 l2 normalize。</p>
<p></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/681da3456074457d460c.png"/></p>
<p>图 3 Embedding Network</p>
<p>模型的输入是三元组 &lt;a, p, n&gt;，其中 a 为 anchor，p(potive) 表示和 anchor 在 embedding 空间中接近或者具有相似性的 item，negative 表示和 anchor 在 embedding 空间中距离较远的样本。Embedding network 的目标是学习一个函数 f(x)，使得 anchor 和 positive 的距离相比 anchor 和 negative 的距离更近。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/7fc8973af287b72835fa.png"/></p>
<p>图 4 Tripelte Loss</p>
<p>最终目标为使得 triplet loss 最小，triplet loss 为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/74f541c2851f0db47843.png"/></p>
<ul><li><b>&lt;a，p&gt; 构造</b></li>
</ul><p>Anchor 和 Positive 我们基于用户在站内的视频点击行为构造，这里尝试了 2 中思路：</p>
<p>1）视频共现度</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/de8c12e51aea86c8a4cf.png"/></p>
<p>图 5 视频共现度</p>
<p>视频共现度表示两个视频被共同用户点击的程度，如上图所示，计算公式类似于 PMI 的计算：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/5ed0c47d8c2e0233f1bc.png"/></p>
<p>保留共现度大于某一阈值的视频作为 &lt;a, p&gt;。</p>
<p>2）ItemCF </p>
<p>ItemCF  能得到 item 对应的 TopK  视频列表，此时 item 为 anchor，ItemList TopK 视频作为 positive。</p>
<p>在实践中基于 ItemCF 构建的 &lt;a, p&gt; 直观效果上优于第一种。</p>
<ul><li><b>负样本构造</b></li>
</ul><p>负样本尝试了两种方法：</p>
<p>1） Negative Sample</p>
<p>对于 &lt;a, p&gt; 对，随机选择 item 作为负样本，每个 &lt;a, p&gt; 对可以随机采样 K 个。</p>
<p>2）Online Triplet Mining</p>
<p>参考论文[7]，在训练过中基于 mini-batch 中的数据动态构建 triplet，如下图所示，一共有 3 类 triplet，</p>
<ul><li>easy triplet：d(a,p) + margin &lt; d(a, n)</li>
<li>semi-hard triplet：处于 margin 之间</li>
<li>hard triplet：d(a, p) &gt; d(a, n)</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/c5583f7389dd3dc53359.png"/></p>
<p>图 6 Triplet 类型 </p>
<p>在训练中选取 semi-hard triplet 和 hard triplet 计算 loss</p>
<h3>效果验证</h3>
<ul><li><b>embedding 用于 item2item 召回</b></li>
</ul><p><b>  </b>根据视频的 embedding 我们可以计算每个视频在 embedding 空间中最近的 TopK 视频列表，如图 5 所示，我们展示了部分视频相关的 Top3 视频，从图中可以看出在 embedding 空间距离近的视频有明显的语义相关性。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/04b7caeb3cc04c021324.png"/></p>
<p>图 5 Top3 视频展示</p>
<p>此外，根据用户的点击历史点击序列在推荐系统中增加一路基于 embedding 的召回，小流量实验结果为视频 CTR 提升 1.21%、人均时长提升 1.75%、人均 VV 提升1.49%。</p>
<ul><li><b>DeepFM 特征</b></li>
</ul><p>Embedding 作为 DeepFM 特征训练排序模型，如图 6 所示，embedding 特征作为 value 和各个 filed 的 embedding concat 输入到  DNN 中，相比于不加 Embedding 的排序模型，离线 AUC 由 （0.752 -&gt; 0.758）有 0.8%的轻微提升。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/31771ecffe2f32385a46.png"/></p>
<p>图 6 DeepFM</p>
<h2>参考文献</h2>
<p>[1] Barkan O, Koenigstein N. Item2vec: neural item embedding for collaborative filtering[C]//Machine Learning for Signal Processing (MLSP), 2016 IEEE 26th International Workshop on. IEEE, 2016: 1-6.<br/>[2] Grover A, Leskovec J. node2vec: Scalable feature learning for networks[C]//Proceedings of the 22nd ACM SIGKDD international conference on Knowledge discovery and data mining. ACM, 2016: 855-864.<br/>[3] Lee J, Abu-El-Haija S, Varadarajan B, et al. Collaborative Deep Metric Learning for Video Understanding[J]. 2018.<br/>[4] He K, Zhang X, Ren S, et al. Deep residual learning for image recognition[C]//Proceedings of the IEEE conference on computer vision and pattern recognition. 2016: 770-778.<br/>[5] Davidson J, Liebald B, Liu J, et al. The YouTube video recommendation system[C]//Proceedings of the fourth ACM conference on Recommender systems. ACM, 2010: 293-296<br/>[6] Kim Y. Convolutional neural networks for sentence classification[J]. arXiv preprint arXiv:1408.5882, 2014.<br/>[7]Schroff F , Kalenichenko D , Philbin J . [IEEE 2015 IEEE Conference on Computer Vision and Pattern Recognition (CVPR) - Boston, MA, USA (2015.6.7-2015.6.12)] 2015 IEEE Conference on Computer Vision and Pattern Recognition (CVPR) - FaceNet: A unified embedding for face recognition and clustering[J]. 2015:815-823.</p>
<p>[8] https://omoindrot.github.io/triplet-loss</p> 
{% endraw %}
