---
title: "用户画像中台建设探索之PeterRec"
date: 2022-04-14 16:07:29
categories:
  - 算法平台
  - 特征工程与用户建模
---

{% raw %}

<p><strong>论文题目：</strong>Parameter-Efficient Transfer from Sequential Behaviors for User Modeling and Recommendation</p>
<p><strong>链接：</strong><a href="https://arxiv.org/pdf/2001.04253.pdf">https://arxiv.org/pdf/2001.04253.pdf</a></p>
<p><strong>开源代码：</strong><a href="https://github.com/fajieyuan/sigir2020_peterrec">https://github.com/fajieyuan/sigir2020_peterrec</a></p>
<p><strong>会议：</strong>SIGIR2020</p>
<p><strong>仅从一个人的抖音、、视频的观看记录里，我们能发现什么？近日，看点推荐团队、 Research和中科大的研究工作首次证实，仅依靠用户视频新闻观看记录，就可以精确地推测出用户的各种个人信息信息，包括但不限于用户年龄段、性别、喜好、人生状况（例如单身/已婚/怀孕等）、职业、学历等信息，甚至是否有心理抑郁暴力倾向。这一客观发现和研究方法将有利于改进现有的一些公共服务质量，提供相关辅助依据实现更为精准的政府决策，也可以为商家和广告商等带来更大的利润，同时也会进一步推动隐私保护的相关研究和相关法案（可以想像以抖音这种短视频APP为例，每天每个常规用户可以产生数百乃至数千的点击记录，如此巨大的用户行为数据潜在地包含了我们无法想象的个人隐私数据）。该项研究已经被信息检索领域顶级国际会议SIGIR接受为长文章。以下主要针对该文章的技术部分进行总结介绍</strong></p>
<ol><li><strong><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a3ada0cdc23bfe7bdc30.png"/></strong></li>
</ol><p>摘要：推导迁移学习对计算机视觉和NLP领域产生了重大影响，但尚未在推荐系统广泛使用。 虽然大量的研究根据建模的用户-物品交互序列生成推荐，其中很少尝试表征和迁移这些模型从而用于下游任务（数据样本通常非常有限）。</p>
<p>在本文中，我们深入研究了通过学习单一用户表征用户各种不同的下游任务，包括跨域推荐和用户画像预测。优化一个大型预训练网络并将其适配到下游任务是解决此类问题的有效方法。但是，微调通常要重新训练整个网络，优化大量的模型参数，因此从参数量角度微调是非常低消效的。为了克服这个问题，我们开发了一种参数高效的迁移学习架构，称为PeterRec。PeterRec可以快速动态地配置成各种下游任务。具体来说，PeterRec通过注入一些的的小型但是极具表达力的神经网络，使得预训练参数在微调过程中保持不变。我们进行大量的实验和对比测试以展示学习到的用户表示在五个下游任务中有效的。此外，我们证实了PeterRec可以在多个领域进行高效的迁移学习时可以达到与微调所有参数相当或有时更好的性能</p>
<ol><li><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/eb44ba001ab5b601b910.png"/></li>
</ol><p> </p>
<p><strong>序言：</strong></p>
<p>在过去的十年中，社交媒体平台和电子商务系统（例如抖音，或Netflix）越来愈多的被使用。 大量的点击和购买互动，以及其他用户反馈是在此类系统中显式或隐式创建的。 以抖音为例，常规用户在每个周可能观看成百上千个短视频。与此同时，大量的研究表明这些用户交互行为可以用来建模用户对于物品的喜好。比较有代表性的深度学习模型，例如GRU4Rec和NextItNet在时序推荐系统任务中都取得了较大的成功。然而绝大多数已有工作仅仅研究推荐任务在同一平台的场景，很少的工作尝试学习一个通用用户表征，并且将该用户表征应用到下游任务中，例如冷启动用户场景，用户画像预测。</p>
<p> </p>
<p>为了解决这个挑战，本文尝试一种无监督训练方式预训练一个神经网络，然后将此神经网络迁移到下游任务中。 为此，论文需要至少解决三个问题；（1）构造一个有效的预训练模型，能够建模超长用户点击序列；（2）设计一种微调策略，能够将预训练网络适配到下游任务。目前为止，没有相关文献证实这种无监督学习的用户表征是否对其他场景有帮助。（3）设计一个适配方法，能够使得不同任务都能充分利用预训练网络参数，从而不需要微调整个网络，达到更加高效的迁移学习方式。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1ce84f502904dec202c3.png"/></p>
<p>图1: PeterRec进行用户画像预测示意图。注意：PeterRec不需要借助于任何图像和文本特征，仅需要用户点击物品ID即可。中间网络为大量堆叠的空洞卷积网络。</p>
<p>为了达到以上目标，研究者提出采用空洞卷积神经网络构建大型的预训练模型，采用一定空洞率设置的多层卷积网络可以实现可视域指数级增长，从而捕获和建模超长的用户点击行为，这一优势是目前很多时序网络难以达到的，例如经典的RNN网络建模长序列时通常会遇到梯度消失和爆炸问题，并且并行训练低效， Transformer等知名NLP网络对显存需求和复杂度也会随着序列长度以二次方的级增加。同时为了实现对预训练网络参数的最大化共享，论文提出了一种模型补丁方式，类似于植物嫁接技术，只需要在预训练网络插入数个的模型补丁网络，既可以实现预训练网络的快速迁移，效果甚至好于对整个模型全部微调。研究主要贡献：</p>
<ul><li>提出一种通用用户表征学习架构，首次证实采用无监督或者自监督的预训练网路学习用户点击行为可以内用来推测用户的属性信息。这一发现将有望改进很多公共服务，带来更大的商业利润，同时也会引发甚至推动对于隐私保护的相关问题的研究。</li>
<li>论文提出了一种非常有效的模型补丁网络，网络相对于原来的空洞卷积层参数量更小，但是具有同等表达能力。</li>
<li>论文提出了两种模型补丁的插入方式，并行插入和串行插入</li>
<li>论文通过分割实验报告了很多有洞察的发现，可能会成为这个领域的未来一些研究方向</li>
<li>论文开源相关代码和高质量的数据集，从而推动推荐系统领域迁移学习的研究，建立相关基准。</li>
</ul><p><strong>方法：</strong></p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/681109a90137aae5bc6f.png"/></strong></p>
<p>图1: PeterRec 预训练网络（a）和微调网络（b）的参数分布。</p>
<p>本研究预训练网络采用空洞卷积网络，每层空洞因子以增加，通过叠加空洞卷积层达到可视域指数级的增加，这一设计主要遵循时序模型NextItNet [1]，如图1所示。预训练优化方式，本文采用了两种自监督方式，分别是单向自回归方式[1]以及双向遮掩法[2]，分别对应因果卷积和非因果卷积网络，如图2所示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9af0a011340622172dca.png"/></p>
<p>图2: 采用空洞卷积网络的几种微调策略。（a）(b)为因果卷机，（c）(d)为非因果卷积。</p>
<p>本文的微调方式非常简单，采用直接移除预训练softmax层，然后添加新任务的分类层，另外，本文的主要贡献是在预训练的残差块（图3（a））插入了模型补丁网络，每个模型补丁有一个瓶颈结构的残差块构成，如图3 （f）所示。本研究提出了几种可选择的插入方式，如图3（b）（c）（d）。注意（e）的设计效果非常差，文章分析很可能是因为模型补丁的和操作，并行插入的和操作与原始残差网络的和操作夹杂在一起，影响最终优化效果。另外文中给出分析，通常模型补丁的参数量仅有原始空洞卷积不到十分之一的参数量，但是可以达到与所有参数一起优化类似或者更好的效果。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/82f0774067576cda377d.png"/></p>
<p> </p>
<p>图3:（a）为原始残差块；（b）（c）（d）（e）为插入模型补丁后的微调残差块；（f）为模型补丁。</p>
<p><strong> </strong></p>
<p><strong>实验：</strong></p>
<p>本文作者进行了大量的真实业务数据实验，论文报道了采用QQ浏览器业务流水构建预训练模型，然后在看点feeds业务冷用户推荐场景进行微调，实现新用户和冷用户的精准推荐，同时论文也采用欧拉用户标签数据测试了画像预测准确率。</p>
<p>实验1 </p>
<p>论文首次证实采用无监督预训练方式非常有效，论文对比PeterRec的两种设置，有无预训练下的实验效果，如图4. 图中所示PeterRec大幅度超越PeterZero，证实了本研究预训练的有效性。</p>
<p> </p>
<p>  <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c17972afb01fead681ad.png"/>  </p>
<p>（a）冷用户推荐对比                    （b）人生状态预测</p>
<p>图4 PeterRec在有无预训练下的预测效果。 PeterZero为无预训练初始化的PeterRec</p>
<p>实验2</p>
<p>几种微调方式比较，如图5所示。图中证实PeterRec仅仅微调模型补丁和softmax层参数达到了跟微调所有参数一样的效果，但是由于仅有少数参数参与优化，可以很好的抗过拟合现象。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e1f2b0cc3d4016045aed.png"/></p>
<p>（a）冷用户推荐对比                    （b）年龄状态预测</p>
<p>图5 各种微调方式。 FineAll 微调所有参数，FineCLS只微调最后softmax层，FineLast1微调最后一个空洞卷积层，FineLast2微调最后两个空洞卷积层。</p>
<p>实验3</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/05f452acab472eb462d7.png"/></p>
<p>与常规的比较知名的baseline比较冷启动推荐效果和用户画像预测效果。具体分析可参见原文分析。</p>
<p>实验4</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5fbe280bfcf5b2accb84.png"/></p>
<p>在少量标签有效的情况下PeterRec效果。可以发现PeterRec不仅超过FineAll，而且相对于FineAll微调过程几乎不会出现过拟合现象。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/44e8bbf17cf75930fd2b.png"/></p>
<p>图6少量target数据标签下 PeterRec vs. FineAll</p>
<p>论文在结论和未来工作部分说明PeterRec不仅仅可以用户论文中的实验，甚至可以用来提前感知青少年心理健康，例如如果我们如果知道青少年每天观看浏览的视频信息，通过PeterRec仅需要少量的标签数据就可以预测出该少年是否心理健康，是否存在暴力倾向阴郁等问题，从而提前告知父母以便提前采取措施。</p>
<p> </p>
<p>[1] A simple convolutional generative network for next item recommendation. Yuan, Fajie and Karatzoglou, Alexandros and Arapakis, Ioannis and Jose, Joemon M and He, Xiangnan, WSDM2019.</p>
<p> </p>
<p>[2] Future Data Helps Training: Modeling Future Contexts for Session-based Recommendation. Yuan, Fajie and He, Xiangnan and Jiang, Haochuan and Guo, Guibing and Xiong, Jian and Xu, Zhezhao and Xiong, Yilin. WWW2020</p>
<p> </p> 
{% endraw %}
