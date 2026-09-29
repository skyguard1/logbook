---
title: "下一代广告系统pCVR大模型-多维度Embedding建模"
date: 2022-04-22 15:07:06
categories:
  - deep-learning
---

{% raw %}

<div><p><strong>编者按：本文为下一代广告系统技术分享季的第五篇干货文章，主要介绍了系统核心模块——pCVR大模型在多维度Embedding建模上的探索和思考，项目主要参与者为的justinquan，lenmu，feihengluo，zodwu，jonaspan.</strong></p><h2>1. 背景</h2><p>pCVR（转化率预估）模型是oCPM广告最为核心的模型之一，准确的预估能让用户和广告精准地匹配，从而提升流量价值。当前广告可出价的转化目标多达上百种，一条广告有同时优化多种转化目标的诉求，比如游戏APP广告可以有激活、付费等优化目标（具体如图1所示）。转化链路越深，转化样本越稀疏，对模型的考验越大。</p><p>随着业务发展，精排模型添加了越来越多的细粒度特征，特别是到了大模型时代，细粒度特征的数量和种类都有大幅增加，这导致样本量相对特征参数空间不足，容易出现模型过拟合的情况。本文提出了一种多维度Embedding（Multi-Emb Net）的方案用来解决pCVR场景样本稀疏不易学习的问题。该方案在原来特征固定Embedding维度的基础上，引入多种不同大小的Embedding分别建立不同维度的专家模型，并通过多任务MMoE（Multi-gate Mixture-of-Experts）结构动态调整不同优化目标下多维度专家网络的权重，提升模型对不同层级目标的泛化能力。
         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/f54a92739d1531f81543.png"/>
<em>图1. 广告转化链路示意图</em></p><h2>2. 基础模型</h2><h3>样本构造</h3><p>        pCVR模型预估的是点击到转化的概率。样本为用户的单个广告点击记录，标签为用户是否发生转化行为。一条点击记录可能会带来多种优化目标的转化，比如激活、付费。当前的pCVR模型大多采用多任务学习，每个任务对应不同的优化目标，比如task 1为激活，task 2为付费。
		</p><h3>模型结构</h3><p>        大模型攻坚前，pCVR主力模型结构如下图所示，自底向上大致分为稀疏特征预处理、特征交叉、多任务分塔、多目标输出四个部分：
         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/7bc5105c82fd3a920287.png"/>
<em>图2. 简单FwFFM模型</em></p><ol><li>稀疏特征预处理：模型首层主要使用稀疏的离散特征（连续型特征可离散化为离散特征），首先会对用户侧、广告侧以及上下文等稀疏特征的每一个key查询一个embedding向量，该向量维度固定。</li><li>特征交叉：广告精排模型主要采用NFwFFM（Neural Field-weighted Field-aware Factorization Machines）网络结构对（1）中查询出的embedding向量进行特征交叉，具体公式为</li></ol><p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/845afd5151bc8b46cdbb.svg"/>
        
其中i, j是特征key的下标，         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/cf8339933b53d056494f.svg"/>
        ,          
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/bba0256b4d587c140c80.svg"/>
        指代特征key i和j相应的特征域（feature group，又称为field）。         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/a8fea8ded6a4509cbaef.svg"/>
        表示特征域之间的交叉强度。</p><ol><li>多任务分塔：pCVR模型需要预估多个优化目标的转化率，因此考虑按优化目标进行任务拆分。原主力模型采用简单的Shared-bottom多任务网络结构，即各任务均基于（2）中的输出进行进一步的网络扩展。</li><li>多目标输出：对（3）中各塔的输出通过softmax函数得到各个目标的pCVR预估值。</li></ol><h3>3. 优化方案</h3><p>在大模型攻坚项目中，针对pCVR模型结构我们在底层和隐层均尝试了一些优化。针对底层Embedding，我们尝试对Embedding的维度做扩参，由64维扩展到128维，但离线AUC和线上GMV都没有取得稳定正向效果。针对隐层，我们构建了多套维度同为64的embedding子网络作为专家，并通过MMoE网络加强多任务建模，也没有取得稳定正向效果。分析后我们认为，pCVR模型的样本量比pCTR模型少的多，越深层的目标样本越少，因此盲目扩大参数量反而容易导致模型过拟合。基于这一点我们转变思路，结合扩参和MMoE两种思路，设计了一种多维度Embedding（Multi-Emb Net）的方案，该方案通过多维度Embedding构建了多种尺寸的专家模型，并通过MMoE网络动态调整专家模型权重，解决pCVR模型样本空间小的问题。</p><p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/b529fe9ac2326b83ff07.png"/>
<em>图3. Multi-Emb FwFFM模型</em></p><h4>3.1 固定维度Embedding-&gt;多维度Embedding</h4><p>        多维度Embedding的想法来自Auto-Embedding Size思想 [1]。推荐算法中的特征通常比较稀疏，比如对于广告ID特征，大部分广告只有个位数的点击，因此在样本中出现的频率极低，对于这种频率较低的特征key，理应设置较小的Embedding Size，以防止过拟合。相反对于出现频次较高的特征key，蕴含的信息量大，可用于学习它的样本量也大，应当设置比较大的Embedding Size，提高模型表达能力。类似地，对于pCVR模型，深度目标样本量较少，参数量应设置的更小防止过拟合，浅层目标样本量较大，参数量也可以设置的较大。以下是朋友圈场景各优化目标的转化样本量对比，浅层目标激活的转化样本数是深层目标付费的大约10倍，但付费贡献的收入甚至更高，对大盘影响更大，因此深度目标预估精准更困难，但是也非常重要。下表为朋友圈某日主要优化目标的转化样本情况。</p><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9a6411c16e36535a6294.png"/></p><p><em>表1. 朋友圈场景主要优化目标样本量对比</em></p><p>        单一尺寸的模型可能对部分目标最合适，但对于其他目标容易造成过拟合或欠拟合。基于这一点，我们考虑在主力模型固定Embedding的基础上，引入多组不同维度的Embedding（图4展示的是16，32，64维三种不同维度Embedding），并分别构建不同大小的子网络，希望不同大小的子网络能够动态地作用在不同优化目标上，从而提升模型对不同层级目标的泛化能力。
             
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/cdb4ed8884270decac31.png"/></p><p><em>图4. 固定Embedding vs 多维度Embedding</em></p><h4>3.2 底层共享-&gt;MMoE</h4><p>        为了将不同尺寸的子网络动态地用在不同优化目标上，我们引入了MMoE（Multi-gate Mixture-of-Experts）门控结构，模型结构如图5所示：
         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/fa58e1d8bc60a5621a1f.png"/>
<em>图5. pCVR多目标模型MMoE网络结构</em></p><p>即对不同优化目标，使用不同权重将不同维度的专家模型组合起来：
         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/856c31056b69065f4c91.svg"/></p><p>其中，n表示专家模型个数，         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/9a9cdd017e5eab0a5216.svg"/>
        表示第i个专家模型，         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/48f8c29d290410b3096e.svg"/>
        表示对于第k个目标，第i个专家模型的权重，输入包含全部的特征，并通过DNN网络以及softmax函数输出，         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/b1fbf5c2833afe30f02f.svg"/>
        表示将专家模型通过全连接层映射到64维，以便进行向量加法。</p><h2>4. 技术优势</h2><p>本文提出的算法主要借鉴了Auto Embedding Size算法的思想，但在具体实现上，本文的算法相比业界的算法具有以下优势</p><h3>端到端</h3><p>        在业界，Auto Embedding Size算法一般基于AutoML进行优化，比如NIS、AutoDim，这一般需要两阶段。第一阶段需给定不同维度候选Embedding，通过AutoML进行筛选，第二阶段固定使用筛选出的Embedding维度进行模型训练，得到最终的模型。而我们的模型可以一步实现维度的筛选和网络参数训练，使用效率更高，更适合在线学习。
         
        <img alt="" loading="lazy" src="/logbook/images/deep-learning/f8b7c756404f30a3dcac.png"/>
<em>图6. 两阶段模型vs一阶段模型</em></p><h3>性能好</h3><p>        两阶段算法需要将大量时间消耗在参数搜索上，训练耗时高，对于当前小时级别线上发布更新的pCVR模型非常不友好，而本文的算法在原基础模型上训练方式不变，性能更好。</p><h3>可继承</h3><p>        随着业务发展，部分目标样本量可能由稀疏变的稠密，需要的模型参数量也会产生相应变化，两阶段模型无法适应这种变化，除非频繁重复执行超参数搜索阶段，而这将导致模型更新的性能极差。而我们的模型更新更加连续，可以很快适应这种变化。</p><h2>5. 效果收益</h2><h3>5.1 线上AB实验在线AUC</h3><p>多维度Embedding模型在多个流量上AUC相比主力定长Embedding模型取得了显著的提升，在实验中，我们主要尝试了3种不同维度的Embedding（16，32，64维），相比主力固定64维Embedding，AUC-lift如表2所示</p><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1713b184cb060eb128fa.png"/></p><p><em>表2. 多维度Embedding（16，32，64维）模型主要目标AUC-lift</em></p><h3>5.2 放量收益</h3><p>多维度Embedding模型结构在朋友圈、公众号和PCAD pCVR场景均通过线上实验验证有效，并在朋友圈和PCAD pCVR场景通过特征（约1.5%提升）+模型结构联合实验完成了全量，表3为大模型线上实验效果：</p><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/5c2e6dd66419acf7dd98.png"/></p><p><em>表3. 多维度Embedding（16，32，64维）模型线上效果</em></p><p>另外我们还在朋友圈场景尝试了在此基础上新增96维Embedding，离线和线上实验进一步取得了2%的显著提升，这是单一Embedding扩参所达不到的</p><h2>6. 总结</h2><p>        在精排大模型攻坚背景下，本文提出了一种多Embedding的模型结构，用来解决pCVR模型正样本稀疏不易学习的问题。核心思想是引入了不同维度的Embedding向量用来构建不同尺寸的子网络，并通过MMoE门控机制针对不同层级的优化目标动态调整权重，提升模型泛化能力。该方案的亮点在于从模型尺寸的角度考虑构建专家模型，这与pCVR多任务模型各目标样本量相对应。在大模型攻坚项目中，该方案在朋友圈、PCAD等多个场景全量，GMV取得了2%以上的显著提升。</p><h1>参考文献</h1><p>[1]. Zhao, X., Liu, H., Liu, H., Tang, J., Guo, W., Shi, J., Wang, S. D., Gao, H. J., &amp; Long, B. (2020b). Memory-efficient embedding for recommendations. arXiv preprint arXiv:2006.14827.</p><p>[2]. Manas R Joglekar, Cong Li, Mei Chen, Taibai Xu, Xiaoming Wang, Jay K Adams, Pranav Khaitan, Jiahui Liu, and Quoc V Le. 2020. Neural input search for large scale recommendation models. In Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery &amp; Data Mining. 2387–2397.</p><p>[3]. Ma J, Zhao Z, Yi X, et al. Modeling task relationships in multi-task learning with multi-gate mixture-of-experts[C]//Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery &amp; Data Mining. 2018: 1930-1939.</p><p>[4]. Junwei Pan, Jian Xu, Alfonso Lobos Ruiz, Wenliang Zhao, Shengjun Pan, Yu Sun, and Quan Lu. 2018. Field-weighted Factorization Machines for Click-Through Rate Prediction in Display Advertising. In Proceedings of the 2018 World Wide Web Conference on World Wide Web (WWW). Lyon, France, 1349–1357.</p><p>[5]. Yuchin Juan, Damien Lefortier, and Olivier Chapelle. 2017. Field-aware Factorization Machines in a Real-world Online Advertising System. In Proceedings of the 26th International</p></div> 
{% endraw %}
