---
title: "小视频自动分类技术解析与实践，AI为你省人力提效果"
date: 2022-04-28 10:32:47
categories:
  - deep-learning
---

<h1>1. 任务背景及分析</h1>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 随着近几年发展，视频在用户碎片化时间中消费信息中的比例逐年增大，因此对视频的相关工作亟待发展。其中最为基础的即视频分类，分类的结果可用于用户画像、标签、推荐系统等广泛应用领域。而爆发式增长的视频数量，人工标注已无法满足需求，因此需机器自动识别分类来减轻人工工作量、提升分类效果、缩短视频标准化流程的时间。</p>
<h2>1.1 小视频数据形态分析</h2>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 小视频，时长较短、集中在15秒左右，大部分为用户手拍的视频。以下面为例，分别是用户手拍的美食、自拍和时尚。根据业务小视频数据需求，标准化团队制定了小视频分类体系（19个一级分类）。</p>
<p style="text-align: center;">&nbsp;&nbsp;&nbsp;&nbsp;</p>
<p style="text-align:center;">图1&nbsp; 小视频截图展示</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 我们从三个方面分析数据形态：</p>
<table width="517"><tbody><tr style="height:29px;"><td style="width:69px;text-align:center;height:29px;"><strong>模态</strong></td>
<td style="width:295px;height:29px;text-align:center;"><strong>数据形态</strong></td>
</tr><tr style="height:18px;"><td style="width:69px;text-align:center;height:18px;">图像</td>
<td style="width:295px;text-align:center;height:18px;">视频帧集中在15s左右，较短</td>
</tr><tr style="height:28px;"><td style="width:69px;text-align:center;height:28px;">文本</td>
<td style="width:295px;text-align:center;height:28px;">用户填写标题、背景BGM</td>
</tr><tr style="height:28px;"><td style="width:69px;text-align:center;height:28px;">音频</td>
<td style="width:295px;text-align:center;height:28px;">用户选择配的背景音</td>
</tr></tbody></table><h2>1.2 难点分析</h2>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 根据1.1中的数据形态，小视频分类中存在的难点如下：</p>
<ul><li>图像侧：图像侧数据多集中在15s左右，视频较短。且多为用户手持手机拍摄、内容随意性较大。此外，搞笑、绝活等视频的分类涉及到视频内容语义理解，难度较大。</li>
<li>
<p>文本侧：文本侧可用数据主要集中在用户在上传视频时自己填写的标题和背景BGM。其中标题部分存在大部分无意义的标题，比如“哈哈哈哈哈”之类的；而背景BGM也会出现不同分类的小视频配同一个背景BGM。</p>
</li>
<li>
<p>音频侧：该部分数据同样来源于用户上传视频的自己选择，具有一定随意性。而根据用户习惯，一些热门的火爆音频更容易被选择，而这些小视频也分属于不同的类别，这就造成了不同的小视频分类用了相同或者相似的背景音频。</p>
</li>
</ul><h1>2. 技术方案</h1>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 技术方案分四部分，分别是图像模态、文本模态、音频模态和融合部分，见图2的整体技术方案。</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">图2 整体技术方案</p>
<ul><li>图像模态：RGB表示原始图像，RGBdiff表示相邻两帧图像的差（用于表征运动信息），各自都经过图像特征提取部分抽取图像特征，之后分别进入各自的分类器，输出预测概率到融合模块，该部分将在2.1中进行详述。</li>
<li>
<p>文本模态：将标题、背景BGM、topic等文本信息切词后，进行过滤处理；之后输入到bi-LSTM（双向LSTM）中，再经过self-attention部分，输出预测概率，该部分将在2.2中详细介绍。</p>
</li>
<li>
<p>音频模态：将视频对应音频提取mfcc特征，之后抽取vggish特征；根据数据分布特性，分别训练两个模型（普适性模型和特定模型），该部分在2.3中详述。</p>
</li>
<li>
<p>多模态融合：将各个模态的输出预测概率进行融合，给出最终的分类预测概率，详见2.4。</p>
</li>
<li>
<p>文档后续所涉及到的提高值和降低值均为绝对值。</p>
</li>
</ul><h2>2.1 图像模态</h2>
<h3>2.1.1 图像模型</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 图像模态的图像模型采用Inception-ResNet-v2对图像进行特征抽取，抽取的图像包括原始视频帧图像和相邻两帧之间的RGBdiff图像。Inception-ResNet-v2是google在inception系列的基础上引入resnet残差。</p>
<p style="text-align: center;">&nbsp;&nbsp;</p>
<p style="text-align:center;">图3 Inception-ResNet-v2结构图</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp; 图3中左图为Inception-ResNet-v2的整体网络结构图，右图为结构中的Stem结构。</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp; 在图像模态，原始RGB图像并不包含运动信息，考虑到时间性能，用RGBdiff代替光流来表征视频中的运动信息。RGBdiff是相邻两帧相减求绝对值。由于小视频的时长较短，相邻两帧的动作变化幅度较大，存在RGBdiff图并不是黑色占比较大的情况。如图4所示：</p>
<p style="text-align: center;">&nbsp;&nbsp;&nbsp;&nbsp;</p>
<p style="text-align:center;">(a)&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;(b)&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; (c)</p>
<p style="text-align:center;">图4&nbsp; (a)(b)分别为相邻两帧的RGB图像，(c)为两帧的RGBdiff图像</p>
<p style="text-align: left;"></p>
<p style="text-align:center;">图5 图像模型流程</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 以RGB图像序列为例，输入RGB图像序列，序列中每张图像都经过Inception-ResNet-v2网络，提取mixed7a层的特征为图像特征，之后将各个图片的mixed7a特征进行平均池化为一维图像特征向量，即RGB fea。Classifier部分，一层隐含层，后接softmax层，输出各类别在该模型情况下的预测概率。RGBdiff同理。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; RGB和RGBdiff在提取图像特征部分有权值共享策略，后续训练各自分类器则分别训练和预测。</p>
<h3>2.1.2 相关实验</h3>
<p><strong>(1) Inception-ResNet-v2特征层的选择</strong></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 图像的深度网络，越深层的特征输出对图像的高层语义表征更强；越浅层的对图像细节的捕获更好。以Inception-ResNet-v2为例，验证了conv7b、mixed7a、mixed6a三种不同深度层的特征输出。</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">图6 conv7b, mixed7a, mixed6a特征层示意图</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 如图6所示，conv7b是后面紧连softmax层的一层特征输出，可认为是在该模型下图像的高级表征；mixed7a是往前追溯的某一层特征输出，相对于conv7b来说包含更多的细节特征；而mixed6a是更靠前的特征输出。总体来说，越靠近input输入，则特征包含图像细节特征越多，而越靠近最后的softmax，则包含图像的高级特征越多。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; a)&nbsp;以常用的conv7b特征层为基准，替换为mixed7a特征，test acc提升2.38%，macro-F提升2.66%；替换为mixed6a特征，则test acc降低11.56%。由此可见，论单层特征的效果，mixed7a层的效果最佳。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; b)&nbsp;融合conv7b层和mixed7a层的特征，之后连接分类器输出预测概率，与单纯mixed7a层相比，test acc降低了0.76%，macro-F降低了0.85%。因此，特征层面的融合并没有提升单层特征的效果。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; c)&nbsp;融合conv7b层和mixed7a层的概率输出，与单纯的mixed7a层相比，test acc降低0.07%，而macro-F提升了0.37%。</p>
<p><strong>(2) 各分类训练数据均衡</strong></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 各分类数据的不均衡易造成模型偏重于数据量大的类别。均衡数据后，与未均衡之前相比，macro-F提升了7.46%</p>
<p><strong>(3) 融合video2vec模型（AILab自研）</strong></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 增加AILAB的video2vec，将图像序列经过Inception-v3，再经过PCA降维到1024维。该video2vec的预测概率与mixed7a层特征预测概率相融合，与单独mixed7a相比，test acc提升0.38%，macro-F提升0.71%</p>
<p><strong>(4) 增加RGBdiff</strong></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; a)&nbsp;相同视频帧的情况下，单独RGBdiff与RGB相比，test acc降低了4.18%，macro-F降低了5.31%</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; b) 融合RGB和RGBdiff的预测概率，与单独RGB相比，test acc提升了1.02%，macro-F提升了1.21%。由此可见，单独RGBdiff虽无RGB效果好，但融合后效果比RGB好</p>
<p><strong>(5) 增加目标检测</strong></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 利用深度Inception-ResNet-v2提取的是图像整体的特征，而细粒度的图像特征（比如手部）等则需要利用目标检测来提取。实验采用Faster-RCNN模型，在open image dataset数据集上已训练好的检测545类目标物体的模型，Faster-RCNN的算法示意图见图7：</p>
<p style=""></p>
<p style="text-align:center;">图7 Faster-RCNN算法</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 由Faster-RCNN算法，每张图可计算出检测出的目标（包括目标类别、bbox位置、置信度信息），根据检测出来的信息，设计了三种特征（目标检测可检测出545类目标物体）：</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; i) &nbsp;目标物体是否出现特征：0、1表征的目标物体是否出现在视频中，共545维。有一帧图像中出现某目标物体，则该目标物体对应的位置置为1；</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; ii) 目标物体面积占比特征：545类目标物体bbox占图像的最大比例，共545维。统计某目标物体出现在视频中的bbox大小占据整幅图面积的占比最大值即为该维特征；</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; iii) 目标物体相对位移特征：545类目标物体bbox的中心点在相邻两帧之间位移的最大值，共545*2=1090维。统计某目标物体出现在视频相邻两帧之间的bbox中心点的位移，取整个视频的最大位移即为特征。&nbsp; &nbsp;</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 一系列实验及相关结论如下：</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; a) 545类目标检测情况下，增加iii)特征，test acc降低0.31%，macro-F提升0.13%。分析原因在于545类目标的误检较高而影响效果。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; b) 从545类目标中抽取100类在音乐、美食、体育三类出现相对准确率高的物体来实验：增加i)特征，test acc提升0.56%，macro-F提升0.25%；增加ii)特征，test acc提升0.56%，macro-F提升0.25%；增加iii)特征，test acc提升0.5%，macro-F提升0.19%</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; c) 由此可见，增加目标检测可提升效果，目标检测误检高对效果有影响。</p>
<p><strong>(6) 图像特征用max-pooling</strong></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 将图5中的average-pooling替换为max-pooling，test acc降低了0.35%，macro-F降低了0.46%。因此max-pooling并未提升效果</p>
<p><strong>(7) 视频子片段切分</strong></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 将视频按照时长等分为2等分，设计两组实验如下：</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; i) 训练部分不变，在预测部分将2等分的视频分别处理，得到的softmax score求平均</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; ii) 训练部分也修改为两个输入，输入2等分视频的特征，计算loss也是softmax score求平均后来计算；预测部分与i)一致</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 与当前mixed7a层的算法相比，i)方法在test acc降低0.02%，macro-F降低0.27%；ii)方法在test acc提升0.04%，macro-F降低0.16%。因此将视频划分后分别处理的方法并不能在当前业务场景下提升效果。</p>
<h2>2.2 文本模态</h2>
<h3 style="">2.2.1&nbsp;数据预处理<br></h3>
<p style="text-align:center;">图8&nbsp;数据预处理流程</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 文本模态的数据预处理如图8所示，主要包括去噪、分词、实体词回捞、去停用词等步骤，与视频、音频模态稍有区别：1.在用户上传的视频中，文本信息含量相对较少，因此需要更多的训练样本；2.用户上传的文本信息较为随意，样本集方差较大，相对视频、音频，文本模态受数据预处理影响更为明显。</p>
<p><b>(1)&nbsp;</b><b>去噪</b></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 去噪的目的之一在于去除文本语料中可能干扰分类效果的噪声信息，例如用户在上传视频时会填写所使用的背景音乐的名称，对于不在默认曲库中的背景音乐，文本信息中通常会打上“用户上传”的字样，例如“Havana(用户上传)”，这些额外信息通常情况下对分类无益，需要在预处理阶段去掉。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 去噪的另一个目的是去除语料中内容重复的样本，通常情况下训练语料的获取来自不同渠道或不同时间窗口，不可避免存在重复的情况。为避免重复语料对数据分布造成影响，需要在去噪阶段去除重复样本。</p>
<p><b>(2)&nbsp;</b><b>分词</b></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 分词的目的是将长句子切成词粒度的小段，例如“露娜瞬间五杀，太秀了”分词后结果为“露娜&nbsp;瞬间&nbsp;五&nbsp;杀&nbsp;，&nbsp;太&nbsp;秀&nbsp;了”，切分后便可以针对词进行统计和建模。除此之外，分词还承担繁简、大小写转换等作用，本质的作用是将高维的句子空间映射到低维的词空间，降低计算复杂性。</p>
<p><b>(3)&nbsp;</b><b>实体词回捞</b></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 实体词回捞依赖实体词表，作用是回捞分词阶段误切分成多段的实体词，例如上例中“五杀”切分成“五&nbsp;杀”，但“五杀”为游戏术语不宜切开，所以需要在实体词回捞阶段将其合并为一个词汇。</p>
<p><b>(4)&nbsp;</b><b>去停用词</b></p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 停用词与(1)中的噪声类似，通常是对分类无意义的语气词（如“啊”、“呀”）、代词（如“他”、“咱们”）、助词（“的”、“了”）、标点符号、数字等&nbsp;，这些信息对分类效果会产生干扰，需要去除。</p>
<h3>2.2.2&nbsp;文本分类模型</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 使用fasttext作为基础模型，首先在fasttext模型上获取基本结论，在fasttext结果的基础上，我们再尝试使用bi-lstm+attention模型结构，进一步提升分类效果。</p>
<p><b>(1)&nbsp;</b><b>Fasttext</b></p>
<p style="text-align:center;">表1&nbsp;输入数据对分类结果的影响</p>
<table style="height:150px;width:630px;margin-left:auto;margin-right:auto;"><tbody><tr><td style="width:36px;text-align:center;">
<p><strong>编号</strong></p>
</td>
<td style="width:70px;text-align:center;">
<p><strong>1</strong></p>
</td>
<td style="width:77px;text-align:center;">
<p><strong>2</strong></p>
</td>
<td style="width:76px;text-align:center;">
<p><strong>3</strong></p>
</td>
<td style="width:89px;text-align:center;">
<p><strong>4</strong></p>
</td>
<td style="width:136px;text-align:center;">
<p><strong>5</strong></p>
</td>
</tr><tr><td style="width:36px;text-align:center;">
<p><strong>数据</strong></p>
</td>
<td style="width:70px;text-align:center;">
<p>title</p>
</td>
<td style="width:77px;text-align:center;">
<p>title+topic</p>
</td>
<td style="width:76px;text-align:center;">
<p style="text-align:center;">title+bgm</p>
</td>
<td style="width:89px;text-align:center;">
<p>title+bgm+topic</p>
</td>
<td style="width:136px;text-align:center;">
<p>title+bgm+topic(扩大训练数据规模)</p>
</td>
</tr><tr><td style="width:36px;text-align:center;">
<p><strong>Acc</strong></p>
</td>
<td style="width:70px;text-align:center;">
<p>55.20%</p>
</td>
<td style="width:77px;text-align:center;">
<p>57.60%</p>
</td>
<td style="width:76px;text-align:center;">
<p>61.10%</p>
</td>
<td style="width:89px;text-align:center;">
<p>63%</p>
</td>
<td style="width:136px;text-align:center;">
<p>64.30%</p>
</td>
</tr></tbody></table><p>&nbsp; &nbsp; &nbsp; &nbsp; 本业务视频的文本信息除标题（title）外，还包括topic（上游生成的主题）和bgm（用户所选的背景音乐名称），我们尝试将这三路数据叠加输入到模型中进行训练，模型效果如表1所示。结论：(1)与单独训练标题数据相比，添加topic和bgm信息后模型指标（acc）有明显提升，说明topic和bgm信息对分类有正向作用；(2)对比4、5编号两组实验，补充训练数据模型效果提升也较为显著。</p>
<p style=""><b>(2)&nbsp;</b><b>Bi-lstm+attention</b><br></p>
<p style="text-align:center;">图9&nbsp;bi-lstm+attention模型结构</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; Bi-lstm+attention模型结构如图9所示，标题、topic和bgm信息在输入层进行拼接后输入到双向lstm中，双向lstm的输出经过attention模块修正权重后输入到softmax中做分类。与fasttext相比，bi-lstm+attention有如下优势：(1)bi-lstm+attention是时序模型，意味着可以覆盖时序的上下文信息；(2)attention模块可以动态调整词的权重，起到捕捉关键词的作用。以上两个特性在短文本分类任务中尤为重要。</p>
<p style="text-align:center;">表2&nbsp;fasttext对比bi-lstm+attention</p>
<table style="margin-left:auto;margin-right:auto;"><tbody><tr style="height:39px;"><td style="height:39px;">
<p>&nbsp;</p>
</td>
<td style="height:39px;text-align:center;">
<p><strong>Fasttext</strong></p>
</td>
<td style="height:39px;text-align:center;">
<p><strong>Bi-lstm+attention</strong></p>
</td>
</tr><tr style="height:16px;"><td style="height:16px;">
<p style="text-align:center;"><strong>Acc</strong></p>
</td>
<td style="height:16px;">
<p style="text-align:center;">64.30%</p>
</td>
<td style="height:16px;">
<p style="text-align:center;">66.30%</p>
</td>
</tr></tbody></table><p>&nbsp; &nbsp; &nbsp; &nbsp; 表2对比fasttext与bi-lstm+attention在相同训练、测试数据集上的效果，相比fasttext，bi-lstm+attention指标提升较为显著。</p>
<h2>2.3 音频模态</h2>
<h3>2.3.1 特征提取</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 特征提取部分包括两部分，首先提取音频的mfcc特征，在此基础上，计算vggish特征（from tensorflow slim），1秒可产生128维特征，实验过程中可设计需要多少秒的特征。</p>
<h3>2.3.2&nbsp;普适分类器和特定分类器设计</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 分类器部分，得到N*128的vggish特征后，输送到双层LSTM中，即可得到最终在音频模态的分类结果。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 这里的普适分类器是指分类类别数与小视频一致（均为19类），而特定分类器是指为了区分具有明显区别的类别（比如搞笑与非搞笑）。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 实验结论：音频侧，在普适分类器的基础上增加特定分类器，在test acc提升0.12%，macro-F提升0.94%</p>
<h3>2.3.3 其他尝试，m34和m3</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 尝试了其他较新的方法，m34和m3，因参数过多（m34有400W参数，m3有20W参数），数据量不足而导致过拟合。</p>
<h2>2.4 多模态融合</h2>
<h3>2.4.1 特征层融合与概率层融合</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 特征层面融合是指不同模态的特征进行拼接，后连接softmax来得到最终概率；概率层融合是指不同模态的预测概率进行拼接，后接softmax得到最终概率，如图8所示：</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">(a)&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; (b)</p>
<p style="text-align:center;">图10 (a)为特征层融合，(b)为概率层融合</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 相同的输入模态，概率层融合比特征层融合效果更好，在test acc上提升0.59%~8.77%</p>
<h3>2.4.2 同一模态不同算法的融合</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 当各模态不止一种算法时候，需要实验2种融合方式：</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">&nbsp;(a)&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; (b)</p>
<p style="text-align:center;">图11 同一模态不同算法的融合</p>
<p style="text-align:left;"><span style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp; a) 对同一模态的不同算法，首先将对应概率进行融合；再将融合后的与其他模态的概率融合，输出最终的预测概率；</span></p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp; b) 不区分同一模态的不同算法，直接将所有概率进行拼接，融合后输出最终的预测概率。</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp; 方法b相比方法a，在test acc上提升0.3%~0.65%，在macro-F上提升0.24%-0.48%</p>
<h3 style="text-align:left;">2.4.3 不同模态数据分布决定不同融合算法</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 实验过程中发现不同模态数据分布，在选择融合算法上的差异较大。如图10所示，红色和蓝色代表不同模态的数据分布（比如图像和音频），左图为不同模态具有相同或相似的数据分布，而右图是不同模态具有不同或互补的数据分布。</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">图12 不同模态数据分布示意图</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 对于数据分布同趋势的情况下，可选xgboost等系列算法；而数据分布不同趋势的情况下，可优选softmax算法。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 针对小视频的数据分布，符合数据分布不同趋势。使用softmax算法比xgboost算法效果明显：使用softmax算法比xgboost算法，在test acc上提升33.15%，在macro-F上提升50.53%；在数据趋势不同分布的情况下使用xgboost等系列算法，融合后的效果更差。</p>
<h3>2.4.4 增加文本、音频模态提升效果</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 增加不同模态有助于提升小视频分类效果：</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; a) 图像+音频模态，与单纯图像模态相比，test acc提升2.94%，macro-F提升2.46%</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; b) 图像+音频+文本模态，与图像+音频模态相比，test acc提升7.12%，macro-F提升7.24%</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp; c) 使用恰当融合算法，融合多种模态比单模态效果更佳</p>
<h2>2.5 实验效果</h2>
<p>&nbsp; &nbsp; &nbsp; &nbsp; 目前小视频一级分类的效果，在均衡数据上19类中F值在80%以上的10类，占比52.63%；游戏、动物、美食等4类F值在90%以上。近期该服务会在内容平台部小视频标准化平台上线。</p>				</div>
