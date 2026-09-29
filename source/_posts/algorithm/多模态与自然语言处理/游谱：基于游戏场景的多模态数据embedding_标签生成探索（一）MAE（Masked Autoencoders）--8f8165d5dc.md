---
title: "游谱：基于游戏场景的多模态数据embedding_标签生成探索（一）MAE（Masked Autoencoders）"
date: 2022-03-31 14:50:14
categories:
  - 算法
  - 多模态与自然语言处理
---

{% raw %}

<div>

</div>
<div>
<p>游谱：游谱项目的任务是构建一个涵盖游戏行业内所有游戏的多模态知识图谱， 这张图谱需要尽可能的包括每个游戏生命周期内的所有信息， 除了包含每个游戏的基本属性，如开发商、发行时间等， 还要包含游戏的一些热度指标， 如下载量、同时在线人数、直播热度等。针对多模态数据类型（不同的数据类型）甚至实体属性都有不同的处理方式，有的需要利用算法进行知识抽取，如利用自然语言处理NLP/NLU进行命名实体识别，利用远程监督学习deepdive进行关系抽取，利用计算机视觉技术理解音视频内容等；有的需要根据规则进行属性融合等。如何对这些数据分而治之，并有序的链接和融合在一起构建我们的游戏图谱。<br/></p>
</div>
<h1>一、MAE architecture</h1>
<p>    <img alt="" loading="lazy" src="/logbook/images/algorithm/50f04deff8902773e134.png"/></p>
<p>主要思想是：对输入图像的patch序列进行随机mask，学习目标是重建mask的部分，其中主要有两个核心设计：</p>
<p>     1.提出了一种非对称的编码器-解码器结构。其中，非对称即：“编码器” 和 “解码器”的参数量有较大的不同（编码器是应用的核心）。同时，编码器只对可见的patch子集（删除了mask的token）进行操作，而解码器选用的是轻量级的小网络，节省计算量（MAE能够加快模型的训练速度（3倍或更多）并提高精度）。该解码器从编码器的特征向量和mask token中重建原始图像。</p>
<p>      2.mask高比例的输入图像patch（例如75%）会变成一个不错且有意义的自监督任务。在仅使用ImageNet-1K数据时，ViT-Huge模型的Top-1精确度为87.8%。 此外，在检测、分割等计算机视觉下游任务中的迁移性能优于有监督的预训练。</p>
<h1>二、相关实验&amp;结论</h1>
<p>    下面介绍流程会按照pipliine数据处理流程进行介绍，不一定和论文介绍流程一致，按照“图像输入/处理”-&gt;encoder-&gt;decode 步骤介绍。</p>
<h2>（一）结论一览</h2>
<table><tbody><tr><td>环节</td>
<td>主要结论</td>
</tr><tr><td>数据处理</td>
<td>
<p>1)不需要太多的数据增强就能获得比较好的效果</p>
<p>2)采用random mask 方式效果最好，同时maks radio 采用75%并丢弃掉mask的patch</p>
</td>
</tr><tr><td>Encoder</td>
<td>Encoder 采用的ViT框架，同时只保留25%的可见patches</td>
</tr><tr><td>Decoder</td>
<td>
<p>1)非对称的编码器-解码器结构，提升训练速度</p>
<p>2)fine-tuning情况下，depth block 可以选1，width dim可以选128</p>
<p>3)Reconstruction target 选取 pixel norm 效果最好</p>
</td>
</tr><tr><td>Other</td>
<td>
<p>1)Partial Fine-tuning中，MAE的表征（representations）体现了：更少的线性，更多的非线性。因此，linear probing（0 blocks）效果差，但 non-linear probing（blocks &gt; 0） 效果好。</p>
<p>2)MAE能够有更好的扩展性（can help scale up model sizes），不容易出现精度饱和</p>
<p>3)MAE在目标检测、分割、实例分割方面的迁移学习上，都有不错的效果</p>
</td>
</tr></tbody></table><h2>（二） 图像输入部分的选取设计&amp;实验</h2>
<h3>1.数据增强<br/></h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/11fc2a9cf57e7aeb621c.png"/></p>
<p>    这里作者研究了数据增强对MAE pre-training的影响，因为mae本身使用了75%的random radio 所以在训练阶段不用太多的数据增强就能获得较好的效果了。</p>
<h3>2.图像mask方式选取</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/8b6d55701ef48f725bcb.png"/>   <img alt="" loading="lazy" src="/logbook/images/algorithm/efb93da367440fe83e44.png"/></p>
<p>        通过上面右图可知，随机采样的mask方式效果最好。</p>
<h3>3.Masking ratio选取</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/74377432afe439149677.png"/></p>
<p>        上图可知无论是pretrain、finetune，Masking ratio都是在 75%的时候表现的最好。</p>
<h3>4.Masking token选取<br/></h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a4df5af31d405166e0d6.png"/></p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/41b11bad610a426a8551.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/57c36bdf49806cfb7905.png"/></p>
<p><br/></p>
<p><br/></p>
<p>       </p>
<p>    通常的encode操作会将mask部分的数据也进入encode模块训练，而MAE做了实验，发现去掉这部分后，不仅降低了图片处理量、内存占用量，提升了pretrain的训练速度（3.3倍），还提升了精度，特别是在linear probing 提升～14%。 其给出的解释是：<strong>By removing the mask token from the encoder, we constrain the encoder to always see real patches and thus improve accuracy</strong>.同时，节省下来的内存、计算量使得在同样条件下可以尝试更大的模型。</p>
<h2>（三）Encoder部分设计思考&amp;实验</h2>
<p>    MAE在Encoder上面没有做太多的实验，和标准VIT不同的是MAE在Encoder输入部分去掉了mask的patches（上面已介绍），下面是VIT的pipeline，这里不过多介绍。VIT论文见：<a href="https://arxiv.org/pdf/2010.11929.pdf">https://arxiv.org/pdf/2010.11929.pdf</a></p>
<h3><img alt="" loading="lazy" src="/logbook/images/algorithm/008be24c757b0dab658d.png"/></h3>
<h2>（四）Decoder部分设计思考&amp;实验</h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4910946fe560a54c163a.png"/></p>
<p>   非对称的编码器-解码器结构，通过设计更大的encoder和更小的decoder，提升模型训练速度的同时尽可能让encoder学习到更多的表征（representations）。</p>
<h3>1.Decoder depth &amp; Decoder width</h3>
<p>    <img alt="" loading="lazy" src="/logbook/images/algorithm/2d0efbc8be84e3eeb139.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/a54c9ee425e78b5a86c7.png"/></p>
<p>   MAE的Decoder设计可以相对自由，因为在实际业务应用中，迁移到其他任务fine-tuning，如：分类、检测、分割等，使用的都是Encoder部分。这里作者分别在Decoder depth &amp; Decoder width做了相关实验，实验结果表明：</p>
<p>    i）更深的Decoder对linear probing 提升更明显（8-blocks比1-blocks有8%的提升），而fine-tuning则影响不大。这可以解释为更浅的Decoder，其对应的Encoder最后一层对Reconstruction任务表示更好，对识别任务表示更差。反之，更深的Decoder使得对应的Encoder最后一层的潜在表征更加抽象（leaving the latent representations at a more abstract level）。而fine-tuning则在后续training中可以微调以适应对应的识别任务，从而对指标的影响较弱。</p>
<p>    ii）512宽度的Decoder在fine-tuning和linear probing都表现的最好，并且如果使用fine-tuning，可以使用更窄的Decoder（128-dim）.<br/></p>
<h3>2.Reconstruction target   <img alt="" loading="lazy" src="/logbook/images/algorithm/d52fdb38675773ec7854.png"/></h3>
<p>   作者做了像素级重建、像素级重建+norm、PCA、dVAE token。实验表明，通过normalization能够获取更好的效果，使用PCA降维后效果反而变差了，说明高频分量在整个重构任务中是比较有用的。</p>
<h2>（五）和当前业界模型的比较</h2>
<h3>1.和自监督模型比较</h3>
<h3><img alt="" loading="lazy" src="/logbook/images/algorithm/95cf54a2c68da8b41850.png"/></h3>
<p>   实验表明，MAE随着模型的变大，其体现的效果更加的明显。同时，和业界的无监督模型对比，都会的了更好的效果，在ViT-H-448中获得了87.8%的accuracy。<br/></p>
<h3>2.和有监督pre-training模型比较</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7f9b62d0c1ea868a2a52.png"/></p>
<p>    实验结果表明，i）直接使用MAE进行有监督训练，比ViT原始结果更好，但是随着params变大，模型提升有限（“our impl.”曲线相对平缓），说明指标已经到了相对饱和的情况。ii）仅使用IN1K数据作为pre-training的MAE的曲线趋势和使用JFT-300M supervised pre-training的ViT有相同的趋势，说明MAE can help scale up model sizes（在更小的数据集合上，随着模型参数量变大其趋势表现和大数据训练的模型ViT-H-JFT-300M一致，能支持更大的模型而不至于“相对饱和”）。</p>
<h2>（六）Partial Fine-tuning（局部微调实验）</h2>
<p>     论文上面介绍的fine-tuning结果比linear probing的要好，主要是因为linear probing不能很好的拟合非线性特征（misses the opportunity of pursuing strong but non-linear features），这里作者将Encoder的最后几层进行fine-tuning（其他freezing）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/1c140f113b145502f5d1.png"/></p>
<p>    从上图可以知道，linear probing（0 blocks）的效果 MAE比 MoCo V3要差，但是后续曲线趋势看，MAE上升的更快，达到同样的指标时需要fine-tuning的block数更少。说明MAE的表征（representations）体现了：更少的线性，更多的非线性。因此，linear probing并不是“刻画模型训练效果优劣”的最好选择。linear evaluation的方式也不经常用于NLP for benchmarking pre-training。</p>
<h2>（七）Transfer Learning Experiments</h2>
<p>    作者在目标检测、分割、实例分割方面评估了pretrain model的迁移学习情况。</p>
<h3>1.Object detection and segmentation  <img alt="" loading="lazy" src="/logbook/images/algorithm/9d73bae4ee083fbc6e0f.png"/></h3>
<h3>2.Semantic segmentation</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/84114d625441a6a813c4.png"/></p>
<h3>3.Pixels vs. tokens.</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/bedc9a06269096be7b54.png"/></p>
<h2>（八）其他设计说明-Training schedule</h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/ca928d15faac210cfcbe.png"/></p>
<p>     可以发现的是，MAE随着训练epoch的增加指标上升。同时，可以发现在linear probing accuracy 方面，对于ViT-L模型，我们训练到了1600个epoch也没有精度饱和情况，但是MoCo v3训练到300epoch就已经饱和了。可以注意的是：在每个epoch中，MAE只看了其中25%的patches，然而在contrastive learning中，其encoder看到了200%或者更多的patches。</p>
<h1>三、MAE复现效果</h1>
<h2>（一）复现imagenet-1k数据集合指标结果</h2>
<table><tbody><tr><td>ViT-B-paper</td>
<td>ViT-B-our<br/></td>
</tr><tr><td>83.6</td>
<td>81.2</td>
</tr></tbody></table><p>    当时论文刚出来时，我们就准备复现了。使用了非官方的方案，同样的ViT-B模型只能在imagenet-1K-valid上面复现到81.2%的准确，可能是我们pretrain-model只训练了400-epoch原因（官方800/1600-epoch &amp; 128 TPU-v3 cores）。</p>
<h2>（二）游戏场景的图片效果</h2>
<p>    我们在公司内部游戏数据上进行了pretrain-model，并在外部网站上获取数据进行了测试。为了更好的观测到训练效果，分别选取了与训练数据接近的“王者”数据，训练数据中完全不可能出现的原神数据。</p>
<h3>1.在王者素材上面的效果</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/35f2ab912e9275f282cb.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/b0c852bbfb5c5e1bf68a.png"/></p>
<p>    可以看到，“王者”数据还原的细节较好，同时可以看到上图中能够基本还原“王者荣耀”的字体区域、色调等。</p>
<h3>2.在其他素材上面的效果</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/ebb80502ea483c7a8161.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/54272f33f7de0cf47ccd.png"/></p>
<p>    因为训练数据中有王者数据，为了进一步观察模型学习的效果情况，选用了网上的其他数据测试。在下面英文字母发现，虽然mask掉了大部分，可见的只有G、S的部分，但是模型依旧能定位出其他字母的大致位置情况。虽然细节处理没有还原的很好，但是可以发现在有一定的整体复原效果。</p>
<h2>（三）游戏内容素材打标签实验<br/></h2>
<p>    为了进一步了解不同数据源训练的pretrain-model在游戏场景下的表现情况。我们标注了15544训练样本，和1756张测试/验证样本，训练的目标是：区分该样本是否是“现代” 或者“古代/古风/神话”的题材内容。我们分别观察了随着训练epoch的增加，不同pretrain-model训练的数据源（imagenet-1k、game_data），和scratch方式在测试/验证集合上的accuracy、loss情况。其中，pretrain-model-imagenet-1k使用的是～120w的imagenet图片数据训练，pretrain-model-game_data使用的是公司内部业务游戏场景数据～120w张图片。实验均采用的是-KP平台上“55核cpu，5张V100GPU，225G内存”的pytorch组件训练，pretrain-model-epoch=400等。更多的实验数据、代码等联系：youzengli。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/1d810fb04f599820c87d.png"/></p>
<p>    如上图，展示了～200epoch的训练过程中的测试数据的accuracy情况，其中pretrian-model都收敛接近95%，scratch则接近85%。可以发现：1、红色（game data）整体在绿色（imagenet-1k/baseline）上面，收敛稳定，上升快。2、初始化的时候，和最后分类的线性层初始值有关，多次实验发现game_data，imagenet-1k 在测试数据上，第一个epoch呈现精度效果比较随机。3、pretrain-model远远比scratch好。同时，scratch的精度天花板比两个pretrian-model都低～10%，基本在200 epoch后三个模型都开始呈现了过拟合情况。下图为训练loss情况：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/c7c86fc9e663e4845c23.png"/></p>
<h1>四、总结&amp;展望</h1>
<p>    本文主要介绍了论文Masked Autoencoders的主要思想和实验情况。同时，简单的使用游戏数据，在游戏场景下，进行了内容与素材的embedding，并观察了打标实验的情况。但是，在游戏场景业务中的应用目前介绍的不多，后续将会介绍更多在具体业务上的使用和业务指标的尝试。   </p>
<h1>五、附件其他效果图</h1>
<h2>（一）素材内容上打标签实验样图</h2>
<h3>1.同款游戏的相同宣传题材（古风/现代）</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2df8197a4caba08baf55.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/40954a12a7551ebc03a1.png"/></p>
<h3>2.同款游戏的不同宣传题材（左：古风，右：现代）<img alt="" loading="lazy" src="/logbook/images/algorithm/f3ee1bcdf34065fdae0b.png"/></h3>
<h2>（二）MAE 其他效果图</h2>
<h2><img alt="" loading="lazy" src="/logbook/images/algorithm/7731aba9ab8b86cc3846.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/7f056e085a711cddfa86.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/429ab00613127c136e88.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/62693b53a41601812d27.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/0c0212a64d7ddc156ffb.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/1279dfb85a2bcb68cb4b.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/8aa3a4fe9da04ea627f7.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/29963362ea888daa2b8d.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/cfc2d33695caa9c0d8e6.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/09a822108d9d00212da5.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm/4da83895bba79be24c15.png"/></h2>
<p><br/></p>
<p><br/></p>
<p>欢迎大家加入<strong></strong> ，解锁更多游戏数据科学核心技术和游戏增长方法论！<br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/937c2a614f865b84eb3f.jpg"/></p> 
{% endraw %}
