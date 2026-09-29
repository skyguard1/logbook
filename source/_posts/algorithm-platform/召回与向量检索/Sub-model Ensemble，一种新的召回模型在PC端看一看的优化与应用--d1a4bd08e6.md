---
title: "Sub-model Ensemble，一种新的召回模型在PC端看一看的优化与应用"
date: 2022-04-14 16:09:18
categories:
  - 算法平台
  - 召回与向量检索
---

{% raw %}

<p>    Hi 大家好，我是来自看一看团队的应用研究员刘冲，接下来我会详细地为大家介绍Sub-model Ensemble这一系列优化的来龙去脉。第一次在km上进行总结归纳，文笔不好望大家海涵。</p>
<h2>一、数据增强与 Unsupervised Contrastive Learning</h2>
<div>
<div>    数据是推荐系统的重中之重，而生产环境中的真实数据往往会面临着数据稀疏，尤其是长尾用户数据量不足的问题，有的小场景还存在数据量整体不足的问题。我们在优化pc端看一看的时候，也遇到了长尾数用户数据稀疏，user representation embedding 不容易收敛的问题。</div>
<div>    众所周知，图像旋转、缩放平移等数据增强方法在CV中有着广泛且重要的应用，能够为模型补充训练样本，并且有效地提升CV模型的泛化能力。所以在今年三月份的时候，我就开始思考能不能借鉴CV里的数据增强做法，增强召回模型的泛化能力。第一个版本的数据增强模型比较简单，随机地 drop 掉一些 user 侧特征，然后作为新样本输入dssm模型中，并给予可调节的超参权重，命名为Random DSSM (R-DSSM)。在离线实验中，发现随着每次 drop 的特征不同，HR@200指标上下波动很大。很明显，这种随机drop特征的方法由于随机性太强，效果不稳定。<br/><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/14bfa628cb20a596b45c.png"/><br/></p>
<p>    那么如何对R-DSSM进行一个约束呢？ 在这里我进一步借鉴了simCLR——Hinton大佬提出的对比学习框架，将Unsupervised Contrastive Learning融入了R-DSSM中，命名为CL-DSSM。 CL-DSSM 通过最小化同一用户的表达向量之间的距离，并且最大化不同用户的表达向量之间的距离，来对我的R-DSSM做一个约束， InfoNCE被用来用作对比学习的loss。将对比学习模块的loss作为辅助loss，加到DSSM模型的原始loss里。</p>
<p>    在CL-DSSM里，有如下几个模块。首先是 Random-Feature-Drop Module，与R-DSSM一样，在数据输入的时候，随机 drop 一些特征。第二是 Encoder Module，这里我仍然采用DSSM的MLP结构，用来提取用户的兴趣表达向量，当然这里也可以换成其他结构，比如transformer之类的。需要注意的是，与普通的DSSM不同，在这里我会将原始的user特征与经过数据增强之后的user特征分别通过同一个encoder，得到同一个用户的两个user representation embedding。第三呢，就是我的CL Module，将全量用户特征的 user embedding 作为待对比的基础向量，同一用户的数据增强 embedding 作为正样本，batch内其他用户的数据增强 embedding 作为负样本，进行无监督对比学习。</p>
<p>CL-loss：</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e4808aec0e5f82d754da.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/588ed8fd1a474f1553ac.png"/></p>
<p>                                                    图一： CL-DSSM</p>
<p><br/></p>
<p>    离线结果如下表所示，HR@200 和 HR@500都有了稳定提升。 </p>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c83d866816188c5e729f.png"/><p><br/></p>
</div>
<h2>二、更优雅的Contrastive Embedding Encoder 方法——Dropout大法</h2>
<div>    在上一阶段，我成功地验证了 Unsupervised Contrastive Learning 在召回模型中的巨大作用，但是 R-DSSM 的随机性过强缺陷其实并没有被完全解决。由此，引发了下一个问题：如何获得一个约束性更强的对比学习向量？关于这个问题，我思考了很久，也摸索了很久。最终，Chen Danqi 老师的 SimCSE 模型进入了我的视野里。</div>
<div><br/></div>
<div>    借鉴Chen Danqi老师的SimCSE模型，我用一种更优雅也更简洁的Contrastive Embedding Encoder 方法取代了上一阶段的 Random-Feature-Drop Module，这种方法就是Dropout。Dropout 大家都很熟悉，在模型训练的时候，随机地 mask 掉一些神经元，以达到增强模型鲁棒性的效果。Hold on，随机地 mask 一些神经元？ 这和我们随机drop一些user特征，是不是有异曲同工之妙呢？ 是的，所以我去掉了CL-DSSM中的 Random-Feature-Drop Module，将用户特征，过两遍同样的 MLP Encoder，以及同样的 dropout rate，通过 dropout 层的随机性，得到两个不同的 user embedding，然后将这两个 user embedding输入对比学习模块。我将这个新模型命名为 Dropout-CL-DSSM (DCL-DSSM)。</div>
<div>
<p><br/></p>
<p>    DCL-DSSM 通过 dropout 方法，获得了同一user的不同 embedding 表达。第一阶段的数据增强方法是虚拟构造了一些与真实user相接近的 user， 而这种虚拟构造没有任何的约束。DCL-DSSM 里对 MLP Encoder 的每一次不同的 dropout操作，其实是获得了一个 sub-model，通过对两个sub-model 的输出结果进行约束，从而起到了一个很强的正则化作用，得到更好的 user representation embedding。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/599c88d2a827e7eceddb.png"/></p>
<p>                                                       图2: DCL-DSSM</p>
<p><br/></p>
<p>     离线实验结果如下表所示，HR@200 和 HR@500 都有了进一步的明显提升。</p>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f524dc644144ca3fd675.png"/><p><br/></p>
<p><br/></p>
<h2>三、百尺竿头更进一步，双重正则化</h2>
<p>    在第二阶段，我通过dropout得到了不同的 sub-model，然后通过对这些 sub-model 的输出进行对比学习，从而起到一个正则化的作用，那还能不能更进一步，继续加强这种正则化呢？答案是可以。在苦苦探索和尝试了多种方法之后，我寻觅到了另一种正则化方法，两种正则化方法强强联合，起到了双重正则化的作用。</p>
<p>    在第二阶段，我们的正则化方法体现在对 user representation embedding 的对比学习约束上，那么还有什么哪里可以进行正则化约束呢？ 答案是在 user embedding 和 item embedding 的 softmax 分布上。众所周知，在双塔召回架构上，user embedding 最终要和 n 个 item embedding 做softmax，这n个 item中有一个是正样本，其余是负样本。那么这个softmax过程，就得到了一个概率分布。而通过第二阶段，我得到了两个相似但不同的 user embedding，那么理所当然的，我可以进一步得到两个不同的 softmax 概率分布，而这两个概率分布也理所应当的是两个非常相似的分布。至此，我探索出了第二种 sub-model 的正则化方法——将两个softmax概率分布计算 Kullback-Leibler (KL) divergence，然后把得到的KL divergence作为辅助loss。 这个模型，我将其命名为 DKL-DSSM。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5d866e182b540b08c12a.png"/></p>
<p>图三: DKL-DSSM</p>
<p><br/></p>
<p>    至此，我设计出了两种利用 dropout 得到 sub-model，然后进行正则化约束的方法。最后，我尝试将两种正则化方法叠加在一起，希望能够强强联合 1+1 &gt;= 2 。该模型被我命名为 DKC-DSSM。</p>
<div>
<div>
<div>
<div>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/567984461eadbf3c42e8.png"/></p>
<p>                                                  图三: DKC-DSSM</p>
<p><br/></p>
<p>     最终的离线效果如下表所示，融合了两种正则化方法的 KL-CL-DSSM 模型起到了 1+1 &gt; 2 的效果。</p>
</div>
</div>
</div>
</div>
<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/21834e128f20f953d0e8.png"/><p><br/></p>
<h2>四、线上实验效果</h2>
<p>   讲了这么多，是时候展示一下我在业务上实际应用的真实效果了。我的应用场景是pc端看一看，于 7月2号 - 7月6号 做了五天的线上实验。实验组大盘整体的<strong>内容点击率</strong>提升 <strong>+</strong><strong><strong>7</strong>.42%</strong>，<strong>pv+vv(曝光uv)</strong>提升 <strong>+</strong><strong><strong>5</strong>.87%</strong>，<strong>人均图文点击数</strong>提升<strong> +</strong><strong><strong>6</strong>.86%</strong>，对一路召回来说，在线上已经有多路复杂的模型召回的前提下，是一个非常了不起的巨大提升！</p>
<p>    线上实验使用了的X实验系统，多对比修正—FDR按指标维度，FDR水平—0.05，α =0.01，1-β =0.8，delta=0 累计对比A1A2 vs B1B2效果，各20%流量。 经过五天时间的科学比较，线上结果稳定且具有统计学意义上的置信。出于对项目的保密，不能在这里贴实验系统里的具体数据截图，往大家海涵。</p>
<p><br/></p>
<h2>五、Future Work</h2>
<p>    接下来我会在公开数据集上验证 DKC-DSSM 的效果，并且尝试在其他的召回模型，例如bert4rec等模型上加入我的双正则化算法，验证这个正则化算法是否是个通用的machine learning 算法。未来计划将本文整理成一篇学术成果，投稿 WWW会议。</p>
<p><br/></p>
<h2>六、 参考文献</h2>
<p>Ting Chen, Simon Kornblith, Mohammad Norouzi, and Geoffrey Hinton. 2020. A simple framework for contrastive learning of visual representations. In International Conference on Machine Learning (ICML), pages 1597–1607.</p>
<p><br/></p>
<p>Tianyu Gao, Xingcheng Yao, and Danqi Chen. SimCSE: Simple contrastive learning of sentence embeddings. arXiv preprint arXiv:2104.08821, 2021.</p>
<p><br/></p>
</div>
</div>
<p><br/></p> 
{% endraw %}
