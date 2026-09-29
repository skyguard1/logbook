---
title: "内平：多模态视频分类和视频embedding技术小结"
date: 2022-04-18 14:32:44
categories:
  - deep-learning
---

{% raw %}

<h2>一、前言</h2>
<p>  视频分类和视频embedding技术具有广泛的应用场景和业务需求，如视频分类，视频打标签、视频质量分层，视频调性分层，视频相似性召回，视频排序等任务。近期，我们参加了视频理解中台的embedding大赛，借此机会小结并分享我们小组在视频理解上的心得。同时，为了共建视频理解开源生态以期促进视频理解技术的交流和合作，我们开源了视频分类模型框架，业务方可以基于自己的垂类数据，动手实现视频分类和视频embedding的相关实验。<br/>       文章的章节以这样的方式组织：第一章是前言；第二章介绍我们的视频分类框架和模型；第三章介绍我们针对视频embedding的一些优化探索；第四章是对这次视频理解中台embedding比赛的小结；第五、六、七章分别是总结、致谢和参考文献。</p>
<hr/><p><strong>项目开源git地址：</strong><br/>        [内部或本地链接已移除]</p>
<p><strong>基于视频embedding的视频相似性检索Demo: </strong><br/>       以微视小视频为例子，demo主要展示了基于视频embedding相似性检索的功能。同时，支持自己上传视频，进行相似视频的检索，以及预测新视频分类和标签。<br/>       基于embedding的相似检索：<a href="http://9.21.136.98:8081/cate2">http://9.21.136.98:8081/cate2 </a></p>
<p><strong>PaaS接口调用: </strong><br/>       如果不想自己部署这套系统，可以通过下面的PaaS接口直接调用我们结果：<br/>       小视频分类：[内部或本地链接已移除]  <br/>       短视频分类：<a href="http://paas.pcg.com/#/function-detail/196">http://paas..com/#/function-detail/196</a>  </p>
<p><strong>Venus视频理解组件：</strong></p>
<p><strong></strong>       我们部分的视频分类模型已经在 Venus上完成组件化，方便后续供大家使用，有问题欢迎交流！</p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/deep-learning/1a0f3aee594c6ad15a8d.png"/></strong></p>

<p></p>
<h2>二、视频分类模型小结</h2>
<p>       当前，内平的多模态视频分类框架，采用两步走的方法：<br/>       步骤一：Frame-level 特征提取；<br/>       步骤二：Multi-Frame 特征的融合分类。<br/>       这两个步骤组成了一个完整的视频分类模型。这里并没有将这两个步骤合并成端到端的方式，主要原因是出于训练效率的考虑。降低训练周期是很有意义的，这使得我们可以利用更大规模的训练数据，进行更丰富的实验，甚至使用更多的模型做集成以提高最终的效果。下面对这两个步骤中使用的模型进行简要的介绍（更多关于多模态短小视频分类模型的细节，可参考我们组之前的另一篇KM文章 [2]，里面做了详细的介绍)。</p>
<h3>2.1 Frame-level 特征提取</h3>
<p>  视频帧和音频帧特征提取模块，用以提取frame-level的表征。我们采用EfficientNet-B3来提取视频帧特征，并做了一些优化工作（详见我们组另一篇KM [3] ），音频帧特征则采用了Vggish进行抽取。在许多业务分享中，通常大家采用公开数据集预训练好的模型，进行帧特征的抽取。值得一提的是，我们对这两个卷积网络在业务数据上进行了finetune，finetune后的分类准确率效果有显著提升，详见 [3] 中的分析。</p>
<h3>2.2 Multi-Frame 特征的融合分类</h3>
<p>  对特征序列进行有效地融合，生成video-level的整体表征，后接多层感知机（MLP）预测视频的分类。得益于两阶段的做法，我们可以用较少代价来训练多个特征序列模型。我们开源了4个特征序列模型，分别是NetVlad、NeXtVlad、TRN和MultiScale-TRN。下面分别简要介绍这四个模型。</p>
<h4>2.2.1 NetVlad</h4>
<p>  我们第一版的视频分类模型中采用的特征序列模块，详见[2]，这里不做赘述。</p>
<h4>2.2.2 NeXtVlad</h4>
<p>  NeXtVlad [5] 是第2届Youtube8M比赛中最优的单模型，它是NetVlad的改进版本。与NetVlad相比，主要是在编码前先将输入特征分解成一组相对低维度的向量，以达到压缩模型大小的目的。</p>
<h4>2.2.3 TRN</h4>
<p>  TRN(Temporal Relation Network) [6]，作为2D-CNN经典解决方案 TSN(Temporal Segment Network) [7] 的一版改进网络，依然沿用视频分段稀疏采样作为网络输入的方式，主要改进是在帧间信息融合时采用了MLP来替换了原来朴素的average pooling，以提高模型时域模式的学习和建模能力。原版的TRN采用的是端到端的模型，我们这里将TRN模块改成特征序列模型以适应我们两阶段的设计，并做了两点小改进：<br/>       (1）添加一条与MLP并行的支路对输入的多帧特征向量做Temporal average pooling + 1x1卷积，并将两支路输出相加，其结构如图2所示，将其命名为残差TRN；<br/>       (2）多模态concat后的特征和网络最后一层特征通过类似 SE(Squeeze-and-Excitation) 的channel attention模块来增强。<br/><img alt="" loading="lazy" src="/logbook/images/deep-learning/3b12863aa9a6b51fc0f9.png"/></p>
<h4>[ 图1 残差TRN结构图解 ]</h4>
<h4>  2.2.4 MultiScale-TRN</h4>
<p>  我们定义的TRN的多时间(帧)尺度的版本（与原论文中有不同），具体地，我们采用了6帧、12帧、18帧和24帧4个尺度，每个尺度使用一个独立的MLP来捕捉该尺度下的时域模式，再对各个尺度下的特征进行拼接，以提高对动作快慢变化的鲁棒性，如下面公式所示，<em>T<sub>d </sub></em>表示输入为<em>d</em>帧的MLP学习到时域特征，[<strong>·</strong>]表示特征拼接，<em>H</em>(<strong>·</strong>)这里使用了恒等映射。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/359d20fbe169d7d81bee.png"/></p>
<p>[ 公式一：多时间尺度TRN ]</p>
<p></p>
<h2>三、视频embedding优化小结</h2>
<p>    目前，视频embedding业务方相关的解决方案大都是直接训练一个分类网络，然后把embedding作为其中间产物。这样，只需要专注优化模型的分类准确率，然而这对于embedding相关的召回任务可能不是最优的。 通常，多类别的分类模型采用Softmax后接交叉熵作为损失函数（下文称为Softmax Loss）。使用分类损失函数训练的深度特征（embedding），会将整个超空间按类别进行划分，保证类别是可分的，然而并不显式约束 “类内紧凑和类间分离”，而这个显然是embedding的任务更加关注的目标。<br/>       上一章节的主要篇幅集中在介绍整个视频分类模型结构，本章节将会介绍我们针对embedding任务做的一些探索和尝试，以获取区分性更好的视频embedding，包括度量学习、人脸识别损失函数、局部邻域融合embedding。</p>
<h3>3.1 度量学习</h3>
<p>  一般地，计算特征空间中数据点间的距离可以使用欧式距离，cosine距离等通用的距离度量方式，而距离度量学习是从（弱）监督数据中学习出适合特定任务的距离度量方式。传统的度量学习一般是学习马氏距离度量：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/a355514bbfd6a317a13e.png"/></p>
<p>[ 公式二：马氏距离 ]</p>
<p>  其中，<em>L</em>是需要学习的线性投影矩阵，当<em>L</em>为单位矩阵则为欧式距离，<img alt="" loading="lazy" src="/logbook/images/deep-learning/a31363e4ed3d6ce25546.png"/>是一个半正定矩阵，称为度量矩阵。马氏距离度量学习，也可以看成是学习一个新的embedding空间，在该空间使用欧式距离度量。投影矩阵<em>L</em>的学习，最终形式化为一个优化问题。随着深度学习的发展，现在更常用的做法是通过神经网络进行非线性变换来替换线性变换，深度度量学习的焦点也放在损失函数的设计上。</p>
<h4>3.1.1 传统度量学习</h4>
<p>  如上所述，传统度量学习一般是学习一个线性投影矩阵<em>L</em>，方法有很多，这里介绍一种在我们实验中验证有效的方法——经典的线性监督降维方法LDA(线性判别分析)。LDA的思想是，寻找投影方向使同类的投影点尽可能接近，不同类的投影点尽可能远离。即，在投影后的空间中，类别在距离度量上尽可能可分，如图2所示，这跟我们的任务目标是很一致的。具体以二分类为例说明，LDA寻找直线<em>w，</em>将样本投影到<em>w</em>上后，能最大化投影点的异类中心距离与投影点的同类类内方差的比，即所谓的类间散度矩阵与类内散度矩阵的广义瑞利商。LDA可推广到多分类任务，求取投影矩阵<em>L</em>，将样本投影到类别数 - 1维的空间中<em>。</em>实验中我们将模型输出的embedding作为LDA的输入，训练一个投影矩阵<em>L</em>，求取新的embedding。<br/><img alt="" loading="lazy" src="/logbook/images/deep-learning/d3daacd77e92f83f7733.png"/></p>
<h4>[ 图2 二分类的LDA投影方向二维图解 ，“+”、“-”分别代表不同两类，虚线表示投影，红色实心圆和实心三角形分别表示两类样本投影后的中心点，出自周志华《机器学习》]</h4>
<h4>3.1.2 深度度量学习损失函数</h4>
<p>  关于深度度量学习损失函数，我们组另一篇KM [4] 对此进行了详细的介绍，感兴趣的请移步至此文。</p>
<h3>3.2 人脸识别损失函数</h3>
<p>       人脸识别损失函数也是一类深度度量学习损失函数。人脸识别是一个开集的问题，即测试集中的类别一般在训练集中是没有出现过的，测试时通常是用网络提取人脸embedding特征进行相似性比对，而不是直接由网络输出分类类别。因此，深度学习时代人脸识别问题的一些研究，集中在用更好的损失函数来获取更好的人脸embedding特征上，这些方法和思想是值得被借鉴到我们的视频embedding任务上来的。<br/>       此外，人脸的损失函数大都基于Softmax Loss 改造（通常是用更严苛的分类约束以获得尽可能类内近，类间远的embedding），因此可以保留网络直接分类的能力，这样也比较符合我们实际业务要求（当然，Softmax Loss + 类似Triplet Loss的多任务学习也可以）。<br/>       我们对此进行了一系列的尝试和探索，如Center Loss，Large Margin系列的CosFace (同AMSoftmax，属撞车) 和ArcFace等。Large Margin系列的Loss在人脸识别中的研究很多，这些Loss通过引入一个余弦间距项，来最大化特征在角度空间上的不同类的决策间距（可见图3所示的传统Softmax Loss的决策边界和AMSoftmax的决策边界对比），从而学到区分性更好的embedding特征。不同的Loss通常是采用不同的Margin形式，如CosFace的Margin是加在余弦值上，ArcFace则是直接加在角度值上。关于人脸识别损失函数的更多内容，可见 [8]。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/8668c511c5c6b953df8c.png"/></p>
<h4>[ 图3 传统Softmax Loss的决策边界和AMSoftmax的决策边界对比，来自[9] ]</h4>
<h3>3.3 局部邻域融合embedding</h3>
<p>  在我们离线的实验评估中发现，query从候选集召回的TopK个视频中，正确的召回（相同类别）占比很高，这启发了我们应该充分去利用这些信息。本小节介绍的方法，就是我们利用query在候选集中的局部邻域构建embedding的一个尝试，将其称为局部邻域融合embedding。它可以看作是query和候选集的“距离度量”方式，或者说是一种后处理方式，能有效提高最终测评指标。下面我们从距离计算的角度出发，来引入这种局部邻域融合embedding。目前，计算query和候选集样本距离时，都是考虑两个孤立点的距离，对于更复杂的数据结构，衡量两个样本之间的距离，仅用它们之间的相似度是不够的，这个距离度量需要融合更多的信息。我们考虑融入query在候选集中的局部邻域信息，将任一query样本<em>q</em>与候选集<em>C</em>中任一样本<em>c∈C </em>的距离定义为<em>q</em>在<em>C</em>中<em>K</em>个近邻样本与<em>c</em>的距离均值，具体地，定义 <img alt="" loading="lazy" src="/logbook/images/deep-learning/de7a5c94a702de7376f3.png"/> 为<em>q</em>在候选集中的<em>K</em>近邻，<em>q</em>和<em>c</em>的最终距离定义为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9f6e35bc617585510dbb.png"/>  [ 公式三：局部邻域距离 ]</p>
<p>       其中，<em>d </em>(<strong>·,·</strong>)为cosine距离。为求取上面定义的距离， 将<em>N(q, k)</em> 的embedding向量取均值，来作为q最终的embedding向量<em>q<sup>new</sup></em>，这个<em>q<sup>new</sup></em>即为局部邻域融合embedding。可以证明，用<em>q<sup>new</sup></em>再去跟候选集计算cosine距离即为公式三所定义的距离。</p>
<p></p>
<h2>四、视频理解中台embedding比赛小结</h2>
<p>       为了促进业务方更好地使用视频embedding和不同团队间的技术交流，视频理解中台举办了第一届 “视频理解中台视频embedding比赛”，详细信息详细请移步 [1]。利用上述的模型和方法，我们最终在比赛中取得了公榜第一名，私榜第二名的成绩。   <br/>       比赛分为小视频（微视分类体系）和短视频（信息流分类体系）两个赛道。在小视频中，我们融合了 TRN , Multi-TRN, NetVlad,NeXtVlad 四个模型；在短视频中，我们融合了Multi-TRN, Multi-TRN, NeXtVlad 三个模型。我们在比赛中使用的整个模型框架如图4所示。其中，阶段1和阶段2涉及的模型在第二章中已经介绍。阶段3利用MLP对多个子模型的特征进行融合，使用Triplet Loss训练融合模型。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/720ad3020d47e16280b0.png"/></p>
<h4>[ 图4 比赛整体框架图 ]</h4>
<p>      下面结合在比赛公榜上的表现，对我们上文介绍的模型和方法进行测评。分类效果测评采用自建数据集，embedding召回效果测评采用比赛公榜的数据集。</p>
<h3>4.1 各个分类模型的分类效果</h3>
<p>       本小节对第二章中介绍的分类模型的分类准确率进行测评。</p>
<h4>4.1.1 实验数据集</h4>
<p>       实验用数据集的情况如表格1所示。训练集经过头部降权采样，测试集符合线上大盘分布。</p>
<table><caption>表格1 分类数据集介绍</caption>
<tbody><tr><td>数据集</td>
<td>训练集数量</td>
<td>测试集数量</td>
<td>类别数</td>
</tr><tr><td>微视小视频</td>
<td>~400w</td>
<td>~30w</td>
<td>201类</td>
</tr><tr><td>信息流短视频</td>
<td>~200w</td>
<td>~30w</td>
<td>376类</td>
</tr></tbody></table><h4></h4>
<h4>4.1.2 微视和信息流分类结果</h4>
<p>       在第二章提到了对TRN进行了两点小改进，其结果如表格2所示，朴素TRN是原始的TRN结构。可见，这两个小改进都带来一定的提升。为方便，后面提到的TRN都是指残差TRN + SE module这个版本。</p>
<table><caption>表格2 TRN两点改进在微视小视频上的分类结果</caption>
<tbody><tr><td>模型</td>
<td>准确率(%)</td>
</tr><tr><td>朴素 TRN</td>
<td>74.18</td>
</tr><tr><td>残差TRN</td>
<td>74.27</td>
</tr><tr><td>残差TRN + SE module</td>
<td>74.38</td>
</tr></tbody></table><h4></h4>
<table><caption>表格3 各个模型在微视和信息流数据上的分类结果</caption>
<tbody><tr><td>模型</td>
<td>
<p>微视 准确率(%)</p>
</td>
<td>信息流 准确率(%)</td>
</tr><tr><td>NetVlad</td>
<td>74.35</td>
<td>86.56</td>
</tr><tr><td>NeXtVlad</td>
<td>74.21</td>
<td>86.63</td>
</tr><tr><td>TRN</td>
<td>74.38</td>
<td>86.30</td>
</tr><tr><td>MultiScale-TRN</td>
<td>73.96</td>
<td>86.32</td>
</tr><tr><td>TRN＋NetVlad + NeXtVlad + MultiScale-TRN (ensemble)</td>
<td>74.83</td>
<td>86.85</td>
</tr></tbody></table><p></p>
<p>       微视数据集和信息流数据集上的分类结果如表格3所示。在微视数据集上，单模型中TRN表现最好，而在信息流数据集上单模型则是NeXtVlad表现最好。两个数据集上，四个模型集成的结果均一致优于任一单模型。上面的实验结果，有几点值得注意的思考：<br/>       1）不同帧间特征融合模型的分类准确率差异不大，主要影响效果的可能是提取特征的卷积网咯，但模型集成的结果体现了这几个模型间仍存在一定互补性。我们的方案解耦了特征提取步骤和帧间特征融合步骤，特征对于不同模型是复用的，所以大大降低了多个模型集成的代价；<br/>       2）在微视小视频上最优的单模型是TRN，而在信息流短视频上NeXtVlad这种复杂度更高的模型体现出了优势，值得注意的是，在微视上，TRN使用固定的16帧 vs. NeXtVlad使用最多100帧作为输入，信息流上，TRN使用固定的64帧 vs. NeXtVlad使用最多300帧作为输入，由此看，稀疏帧已经可以达到不错的效果，使用更少的帧可以让整个推理过程更高效，降低部署时对硬件资源的需求。此外，TRN的参数量要远少于NeXtVlad，推理时占用的显存也大大降低。至于哪个模型效果更优需要结合到实际业务数据去判断。</p>
<h3>4.2 分类模型的embedding召回结果</h3>
<p>       本小节给出分类模型提取的embedding在公榜的召回测评结果，微视和信息流的候选集均为50w，query集均为5w，测评指标采用MAP@20，测评结果如表格4所示。</p>
<table><caption>表格4 公榜上各模型embedding测评结果</caption>
<tbody><tr><td>模型</td>
<td>微视 MAP@20</td>
<td>信息流 MAP@20</td>
</tr><tr><td>NetVlad</td>
<td>0.6967</td>
<td>0.7467</td>
</tr><tr><td>NeXtVlad</td>
<td>0.7044</td>
<td>0.7461</td>
</tr><tr><td>TRN</td>
<td>0.6831</td>
<td>0.7424</td>
</tr><tr><td>MultiScale-TRN</td>
<td>0.6983</td>
<td>0.7422</td>
</tr><tr><td>TRN＋NetVlad + NeXtVlad + MultiScale-TRN (concat)</td>
<td>0.7086</td>
<td>0.7492</td>
</tr></tbody></table><p></p>
<p>         从公榜的embedding测评结果来看，NetVlad系列的效果较好，跟上面的分类准确率呈现的并不完全一致。这应该主要是5w query集的数据分布跟上面用来测评分类的30w数据分布的差异导致的。表格的最后一列是将多个模型的embedding拼接作为最后embedding的测评结果，融合多个模型的embedding依然取得了最好的效果。</p>
<h3>4.3 视频embedding优化方法的测评</h3>
<p>        本小节对第三章介绍的针对视频embedding进行优化的一些方法进行实验评估。</p>
<h4>4.3.1 度量学习</h4>
<p>        度量学习方法在微视公榜上的测评结果如表格5所示，添加LDA的实验在单模型上给出MultiScale-TRN上的结果，可见加上LDA后MAP@20提高了0.0044；利用Triplet Loss训练MLP来融合比朴素的concat有明显提高，同时加上LDA则仍有轻微提高。</p>
<table><caption>表格5 度量学习方法在微视公榜embedding测评结果</caption>
<tbody><tr><td>模型</td>
<td>MAP@20</td>
</tr><tr><td>MultiScale-TRN</td>
<td>0.6983</td>
</tr><tr><td>MultiScale-TRN <strong>+ LDA</strong></td>
<td>0.7027</td>
</tr><tr><td>TRN＋NetVlad + NeXtVlad + MultiScale-TRN (concat)</td>
<td>0.7086</td>
</tr><tr><td>TRN＋NetVlad + NeXtVlad + MultiScale-TRN (concat) <strong>+ Triplet Loss</strong></td>
<td>0.7213</td>
</tr><tr><td>TRN＋NetVlad + NeXtVlad + MultiScale-TRN (concat) <strong>+ Triplet Loss + LDA</strong></td>
<td>0.7232</td>
</tr></tbody></table><h4><br/>4.3.2 人脸识别损失函数</h4>
<p>       我们以TRN作为基准模型尝试了Center Loss, CosFace, ArcFace 几个人脸识别中效果较好的损失函数，表格6是其在微视30w分类测试集上的分类结果和微视公榜上的embedding测评结果。从分类和embedding测评结果来看，最好的反而是 Softmax Loss，在人脸识别任务上效果显著的这些损失函数在我们的任务上没有带来提升。这里猜测可能是由任务数据的特性造成的，如若数据类内差异性本身太大，加这种强约束反而导致模型难以收敛；也可能是参数还没有调节到合适的区间，具体深入的分析理解将放在后续的工作中，这些损失函数对我们之后的优化仍是有一定启发和参考作用。</p>
<table><caption>表格6 几个人脸识别损失函数在微视上的分类准确率和embedding测评结果</caption>
<tbody><tr><td>模型</td>
<td>准确率(%)</td>
<td>MAP@20</td>
</tr><tr><td>TRN + Softmax Loss (baseline)</td>
<td>74.38</td>
<td>0.6831</td>
</tr><tr><td>TRN + Center Loss</td>
<td>74.25</td>
<td>0.6795</td>
</tr><tr><td>TRN + CosFace</td>
<td>74.14</td>
<td>0.6803</td>
</tr><tr><td>TRN + ArcFace</td>
<td>74.22</td>
<td>0.6782</td>
</tr></tbody></table><h4><br/>4.3.3 局部邻域融合embedding</h4>
<p>       表格7和表格8是局部邻域融合embedding方法在微视和信息流上的结果。局部邻域融合embedding方法在微视和信息流上都一致带来了提高，而且随着<em>k</em>越大，提高越明显，当k=50时，相比baseline，在微视上显著地提高了0.151，在信息流上也提高了0.052。</p>
<table><caption>表格7 局部邻域融合embedding方法在微视上的结果</caption>
<tbody><tr><td>模型</td>
<td>MAP@20</td>
</tr><tr><td>Baseline (TRN＋NetVlad + NeXtVlad + MultiScale-TRN (concat) <strong>+ </strong>Triplet Loss)</td>
<td>0.7213</td>
</tr><tr><td>Baseline + k=20局部邻域</td>
<td>0.7335</td>
</tr><tr><td>Baseline + k=30局部邻域</td>
<td>0.7347</td>
</tr><tr><td>Baseline + k=50局部邻域</td>
<td>0.7364</td>
</tr></tbody></table><p><strong> </strong></p>
<table><caption>表格8 局部邻域融合embedding方法在信息流上的结果</caption>
<tbody><tr><td>模型</td>
<td>MAP@20</td>
</tr><tr><td>Baseline (NetVlad + NeXtVlad + MultiScale-TRN (concat) )</td>
<td>0.7492</td>
</tr><tr><td>Baseline + k=20局部邻域</td>
<td>0.7537</td>
</tr><tr><td>Baseline + k=30局部邻域</td>
<td>0.7541</td>
</tr><tr><td>Baseline + k=50局部邻域</td>
<td>0.7544</td>
</tr></tbody></table><p></p>
<p><strong>   </strong>    由于时间所限，我们在比赛私榜最终提交的方案没有加上LDA和局部邻域距离的方法，能预期这些方法在私榜上会带来进一步的提高。</p>
<h3>4.4 视频embedding比赛中的思考</h3>
<p>       上述，已经详细介绍了我们的视频分类和视频embedding的方法以及这些方法在比赛中的实验结果。本小节主要分享这次比赛历程中的一些思考和总结，主要整理自 @stoneye(叶振旭) 的分享。以下实验暂且以微视体系的小视频为例子，信息流体系的短视频实验趋势亦然。<br/><strong></strong></p>
<p><strong>4.4.1 思考一</strong><br/><strong>背景：</strong>公榜候选池子数据（50w微视）的二级分类label，对参赛队伍开放。如何充分利用候选池子真实label的先验信息?<br/><strong>结论：</strong>【预定假设：如果可以提前知道候选池子的二级分类的真实label 】 ---&gt;公榜池子数据<br/>          候选池子的emb，用真实的label进行onehot编码作为视频的emb向量；query则采用模型的的预测logit(二级分布得分)作    为emb向量，如此query召回的视频，mAP@1 、mAP@20指标可达到最好（理论上能达到在query上的分类准确率）。 视频理解中台的embedding比赛中，由于公榜的候选池子的二级分类label是开放的，我们用此方法，公榜我们刷到了第一的成绩。具体做法如下：<br/>        步骤1：后选池子视频emb的表征：譬如，后续池子的某个视频的二级label为10（id=10,总共有201个分类），则进行onehot编码，得到一个201维的向量作为该视频的表征，即，该向量index=10的位置设置为1，其他位置设置为0；<br/>        步骤2：query视频emb的表征： 采用模型的预测二级logit（又称score得分）作为该视频的表征。如果有多个不同的模型，可直接进行简单的logit相加融合；<br/>        步骤3： 根据query的emb，用annoy or fassi or  VSL 去候选池召回 topK 个向量，统计 mAP@1 、mAP@20 等指标<br/>最后，我们线上提交的公榜，融合了 neXtvlad，netvlad，multi-trn 3个模型的logit（即 logit相加），公榜MAP@20=0.78，比用emb来召回能达到的最好效果0.7364（如上文实验数据所示）提高了约4个百分点。</p>
<p><strong>4.4.1 思考二</strong></p>
<p><strong>背景：</strong>2019.11.15 提交了候选池子的视频emb （此时，emb融合了 neXtvlad，netvlad，multi-trn 和trn 4个模型 。2019.11.22号前需要提交私榜query视频emb 。然而，在11月21号的时候，上线联调小视频分类模型的时候，不小心覆盖了比赛用了netvlad的模型（即tensorflow的ckpt模型），但是保留了一份ckpt转pb（供tfServing调用，算是保留下了火种）的模型。问题是，如何根据pb模型，infer 得到 logit 前一层的dense vector，得到netvlad模型的query向量，保证query向量和候选池子向量的一致性？<br/><strong>结论：</strong>根据 tensorboard 可以查看保存的任意tensor节点的op操作名称，然后往pb的placehold灌数据，可以获取到任意节点的输出。具体操作如下：<br/>       步骤1：首先，根据pb模型生成 log 文件(tensor计算图和参数)，生成了一个 events.out.tfevents.1574357400.9-24-132-197 日志文件，包含了tensor 参数计算图；<br/>       步骤2：其次，利用tensorboard --logdir 可视化整个pb模型的节点图。具体展示如下图5所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/b65a32925d83cbd944cd.png"/></p>
<h4>[ 图5 Tensorboard可视化网络节点 ]</h4>
<p>       步骤3：往pb的placeholder灌数据，从self.secondTag_scores_l2 节点获取最终netvlad模型的视频emb向量。步骤2中，可以得知10个placeholde和 secondTag_scores_l2 节点所对应的pb的op操作的tensor名字。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/97e638ffc6028a62c901.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/98c552d1ed9c06468fe4.png"/></p>
<h4>[ 图6  placeholder 和 self.secondTag_scores_l2]</h4>
<p>大功告成，总算完成自我救赎之路 !</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/fc86537c30c139a1b39d.jpg"/></p>
<h4>[ 图7  ps 左图： 2019/12/22 凌晨1点半，尝试从pb复原netvlad模型的query向量; 右图： 最后，自己一个人，debug到凌晨3点半，第一次在公司过夜。]</h4>
<p><strong>4.4.1 思考三</strong></p>
<p><strong>背景：</strong>私榜候选池子数据，未能获取到真实的分类label。<br/><strong>结论：</strong>【预定假设：如果未能提前获取候选池子的二级分类的真实label 】 ---&gt; 私榜池子数据<br/>         根据3.3中的方法局部邻域融合embedding，利用了topK个召回视频的embedding的平均值替换原query视频的embedding，可以降低query embedding表征的噪声。<br/>         步骤1：根据query的embedding，采用annoy or fassi从候选池子召回topK个视频 <br/>         步骤2：根据topK个视频embedding的平均值作为query视频的embedding表征（即，用topK个视频的平均值替换掉原query的embedding，可大大消除embedding的噪声）<br/>         最终，我们测试得到mAP@20提升了1.51个百分点。</p>
<p><em>特别特别遗憾的是： </em><br/><em>"pb复原netvlad模型" 和  "局部邻域融合embedding" 未能及时在规定时间内应用在比赛中，最终我们私榜成绩排在了第二。</em></p>
<p><em>脑海中，突然浮现出这么一个画面：针对灌篮高手的结局，有人问井上说，湘北最终为什么没有夺冠？ 井上回答说，因为青春的梦想往往是不完美的……</em></p>
<p><em>留点遗憾，多点积累与成长，全新出发！</em></p>
<p><strong></strong></p>
<h2>五、总结</h2>
<p>       本文简要总结了视频分类模型和视频embedding方法的经验，并结合这次中台视频embedding比赛进行了实验分析和思考。上文所述的部分方法在比赛中验证了其有效性，部分方法则没有带来效果的提升，需要后续更多深入的实验和分析去深耕理解，但这些思路都值得被借鉴引入视频理解，并结合实际问题进一步优化。我们小组将持续探索更多有关视频理解和视频embedding的最新技术，期待下一篇km的更新。</p>
<p></p>
<h2>六、致谢</h2>
<p>       感谢视频理解中台主办方举办了这次比赛，促进了团队间视频embedding技术的交流和分享；<br/>       感谢我们组各位伙伴在各方面的给力支持，尤其是俊烽老弟（hughhe）、金华哥（josephqian）和翔哥（shawnche）。</p>
<p></p>
<h2>七、参考文献</h2>
<p>[1]  [内部或本地链接已移除]</p>
<p>[2]  叶振旭. [内部或本地链接已移除] [DB/OL]. : 深圳, 2019.</p>
<p>[3]  王珩. [内部或本地链接已移除] [DB/OL]. : 深圳, 2019.</p>
<p>[4]  何俊烽. [内部或本地链接已移除] [DB/OL]. : 深圳, 2019.</p>
<p>[5]  Lin Rongcheng, Xiao Jing, and Jianping Fan. Nextvlad: An efficient neural network to aggregate frame-level features for large-scale video classification[C]. In 2nd Workshop on YouTube-8M Large-Scale Video Understanding, 2018.</p>
<p>[6]  Bolei Zhou, Alex Andonian, and Antonio Torralba. Temporal relational reasoning in videos[C]. In European Conference on Computer Vision (ECCV), 2018</p>
<p>[7]  Limin Wang, Yuanjun Xiong, Zhe Wang, et al. Temporal segment networks: Towards good practices for deep action recognition[C]. In European Conference on Computer Vision(ECCV), 2016.</p>
<p>[8]  <a href="https://zhuanlan.zhihu.com/p/34404607">https://zhuanlan.zhihu.com/p/34404607.</a></p>
<p>[9]  Feng Wang, Weiyang Liu, Haijun Liu, Jian Cheng. Additive margin softmax for face verification[J]. IEEE Signal Processing Letters, 2018.</p> 
{% endraw %}
