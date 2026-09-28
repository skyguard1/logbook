---
title: "AI如何深化视频语义特征？探索多模态联合学习的五种方法"
date: 2022-04-28 10:33:40
categories:
  - deep-learning
---

<h1>背景</h1>
<p>&nbsp; &nbsp; &nbsp; &nbsp;近几年，视频在用户碎片化时间的浏览兴趣占比逐年增加，而针对视频内容理解的相关工作也陆续开展。视频内容理解包括范围较广，比如视频分类、细粒度分类、动作识别、场景识别等。对视频内容的多样化理解能力，在视频特征层面能为后续的内容推荐提供丰富的信息，有助于提高用户体验。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp;而视频内容理解在特征层面，如何寻找一种视频的语义表征，使得该表征包含更多有用信息，能够应用在多个视频内容理解任务。我们以基础的视频分类问题为切入点，探索在该任务中如何得到更好的<strong>视频语义表征</strong>。</p>
<h1 style="text-align:left;">效果</h1>
<p>&nbsp; &nbsp; &nbsp; &nbsp;我们的实验效果，以图像<span>+</span>文本两种模态之间的实验为主，可按原理迁移到其他模态之间。基于图像<span>+</span>文本模态实验：在各单模态已达到天花板的情况下，大幅提升文本模态效果（绝对值提升<span>3.46%</span>），小幅提升图像模态效果（绝对值提升<span>0.98%</span>），意味着图像和文本模态都学习到了对方的优势信息来增强自身模态模型效果。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp;对于多模态联合学习方法的探索，使得我们在视频语义表征部分有了进一步的进展，改变以往视频仅有的视觉特征、文本特征、音频特征等等，而是有一种包含多模态信息的语义表征方式。这种多模态的视频语义表征，不仅可用于视频分类，也可迁移到其他视频内容理解的相关工作，增强视频内容理解的技术沉淀。</p>
<h1>问题分析</h1>
<p>&nbsp; &nbsp; &nbsp; &nbsp;以视频分类为例，视频分类是视频内容理解最基础的内容之一。针对视频分类问题，目前较为广泛使用的技术方案如图<span>1</span>所示，整体框架接受多个模态的输入，各单模态进行单独的训练，最终用多模态融合得到最后结果。</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">图1</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;如上图所示，最终结果是基于多模态融合的方式。多模态融合方式从浅层特征到深层特征过渡，包含<span>pixel level</span>、<span>feature level</span>和<span>decision level</span>。多模态融合的方式可以提高最终效果。</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;大量研究学者在提高各个单模态模型上作了很多工作，以优化单模态模型的方式来达到提升最终融合效果。而我们想要探索另一种单模态之间信息互补学习的方式，即多模态联合学习方式：</p>
<ol><li>多模态融合可以提升最终模型的效果，意味着单模态模型之间是有信息互补的。但各模态之间无信息交互，最终的融合效果受限于各单模态模型能达到的天花板。</li>
<li>探索单模态之间的信息交互表示方法，进行多模态联合学习，如图2所示。</li>
</ol><p style="text-align: center;"></p>
<p style="text-align:center;">图2</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;总而言之，我们进行多模态学习的原因：（1）在单模态模型已可能接近天花板的时候，多模态之间进行学习，提升单模态的模型效果和特征表示能力；（2）单模态模型效果的提升，有助于提升最终效果。</p>
<h1 style="text-align:left;">多模态联合学习</h1>
<p>&nbsp; &nbsp; &nbsp; &nbsp;多模态联合学习，在模型训练过程中让单模态之间有信息交互和交流，使得各单模态最终的特征表示包含了其他模态的有效信息。我们尝试了隐式和显式的多模态联合学习方法，按照模型架构中是否设计单模态之间的强制限制条件分为隐式和显式。</p>
<h2>隐式的多模态联合学习</h2>
<p>&nbsp; &nbsp; &nbsp; &nbsp;隐式的多模态联合学习，是指在模型设计上对模态之间<strong>无强制限制</strong>，通过反向传播来隐式地影响其他单模态。</p>
<h3>一、反向传播方式优化</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp;常见的视频分类技术方案大部分在单模态分类的基础上，对概率值进行多模态融合得到最终结果，这样的网络结构设计限制了多模态融合效果的天花板。</p>
<p>&nbsp; &nbsp; &nbsp; &nbsp;我们放开多模态单独训练部分，使得多模态同时训练，因此训练过程中通过优化神经网络的反向传播机制进而达到各个单模态相辅相成的目的。</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">图3</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;相对于单模态分类的网络结构，反向传播方式优化有了进一步改进。</p>
<h3 style="text-align:left;">二、隐式语义空间转换</h3>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;在反向传播方式优化版本的基础上，探索隐式语义空间转换带来的收益。因此在此增加特征转换模块，尝试其他特征空间表示对多模态联合学习带来的收益。</p>
<h3 style="text-align:left;">三、基于KD的自适应学习</h3>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;借鉴知识蒸馏（<span>Knowledge Distillation</span>）的思想，在优化目标中增加<span>soft target</span>，如图4所示的示意图：</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">图4</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;图中的<span>Big Model</span>是效果较好的复杂模型，而<span>Small Model</span>是简单模型。用<span>soft target</span>来辅助<span>hard target</span>一起训练，而<span>soft target</span>来自于复杂模型的预测输出，其原因是：<span>hard target</span>包含的信息熵很低，而<span>soft target</span>包含的信息熵较大。</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;最终的训练目标函数为：</p>
<p style="text-align: center;"></p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;其中的<span>Big Model</span>可迁移到本任务中的效果较好的单模态模型。</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;根据多模态联合学习的任务目标，我们引入<span>soft target</span>使得模态之间自适应的相互学习，最终通过<span>hard target + soft target+</span>自适应目标达到了较好的效果。</p>
<h2 style="text-align:left;">显式的多模态联合学习</h2>
<p>&nbsp; &nbsp; &nbsp; &nbsp;与隐式的多模态联合学习不同，显式的多模态联合学习在模型设计上对模态之间<strong>增加强制限制</strong>，模型的优化目标中不但包括主任务也包括强制限制条件。</p>
<h3>一、多模态Feature Transfer</h3>
<p>&nbsp; &nbsp; &nbsp; &nbsp;如图5所示为多模态<span>Feature Transfer</span>的模型架构，红色代表<span>Feature Transfer</span>部分，该部分在特征级别进行<span>transfer</span>学习：</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">图5</p>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;该模型架构的设计基于以下设想：（<span>1</span>）模态特征之间可进行<span>transfer</span>，互相交换有效信息；（<span>2</span>）模态特征之间进行<span>transfer</span>后的结果是互补关系还是趋同关系需要实验验证。尤其是第（<span>2</span>）点，探索多模态<span>Feature Transfer</span>对于最终主任务效果的影响趋势。</p>
<h3 style="text-align:left;">二、基于Matrix Learning的语义互学习</h3>
<p style="text-align:left;">&nbsp; &nbsp; &nbsp; &nbsp;基于Matrix Learning的语义互学习，是在各个模态的不同特征空间之间进行相互学习。如图6所示：</p>
<p style="text-align: center;"></p>
<p style="text-align:center;">图6</p>
<h2 style="text-align:left;">视频理解相关工作</h2>
<ul><li>小视频自动分类技术解析与实践，AI为你省人力提效果</li>
</ul>				</div>
