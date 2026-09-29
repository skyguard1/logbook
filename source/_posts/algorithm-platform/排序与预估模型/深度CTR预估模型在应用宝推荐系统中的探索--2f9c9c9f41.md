---
title: "深度CTR预估模型在应用宝推荐系统中的探索"
date: 2022-04-06 09:50:13
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<p>一、业务背景</p>
<p>二、基本框架</p>
<p>三、多行为融合训练</p>
<p>四、引入更长周期用户行为</p>
<p>五、引入APP描述文本信息</p>
<p>六、预训练embedding融合</p>
<p>七、基于attention的用户行为挖掘</p>
<p>八、小结 </p>
<h2>一、业务背景</h2>
<p>点击率（click-through rate, CTR）预估的本质是对用户/商品建模，进而计算用户的点击概率。模型的衍变经历了从经典机器学习LR、FM再到深度学习DNN、Wide&amp;Deep、双塔、DIN等的百花齐放。本文将针对应用宝的推荐场景，展开CTR模型探索优化。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c1a691caac2d1c5ac5d6.png"/>    <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/892a20e7470bbb6c039b.png"/>  </p>
<p>应用宝推荐业务主要包括首页推荐、游戏推荐等，与常见信息流推荐（新闻/视频）不同，本场景下的数据分布具有明显的差异：</p>
<ul><li>App曝光频次差异巨大：头部1%的app曝光占比超85%，长尾app曝光严重不足；</li>
<li>用户行为极其稀疏：用户月下载中位数2-3个，平均数3-4个。</li>
</ul><p>面对着以上问题，当前的推荐模型主要面临着以下挑战：</p>
<ul><li>在训练样本稀缺的情况下，如何保证<strong>低频特征</strong>（e.g., 长尾appid）的充分学习；</li>
<li>鉴于用户行为极其稀疏，如果更精准地捕捉用户的<strong>兴趣偏好</strong>。</li>
</ul><p>本文主要针对以上挑战，在当下深度ctr预估模型的基础上展开模型优化探索，通过引入更长周期用户行为和app描述文本信息，并进一步挖掘用户行为兴趣，有效促进了推荐效果提升。</p>
<p>在这里也特别感谢我的导师@jimberxin(辛俊波）、组长@kelvincai(蔡锴）对我整个实习工作的悉心指导，以及应用宝应用算法组其他同事的帮助</p>
<h2>二、基本框架</h2>
<p>应用宝的整体推荐流程如下图所示，从底层数据流抽取特征，经过召回、排序以及重排，最终应用到实际业务场景中。本文主要针对排序模型优化。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/dfb82dd170f373f00ceb.png"/>排序模型我们以业内广泛使用的Wide&amp;Deep模型作为baseline，其中，Wide侧具有记忆能力，能够记住高频特征组合，达到准确推荐的目的；Deep侧为了弥补交互矩阵稀疏的不足，将特征映射到低维向量表示，经过多层神经网络，使模型具有泛化能力。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5b06c12b9bc8063b1cad.png"/></p>
<h2>三、多行为融合训练</h2>
<p>在我们的场景中拥有很多appid 相关的行为特征，例如用户历史点击、下载、安装等，基本的Wide&amp;Deep框架会将每个行为特征映射到单独的embedding，并单独更新。由于每一类特征的用户行为记录十分稀疏，这种操作会造成低频特征embedding的训练不充分。<br/> 针对于此，我们设计了基于appid embedding共享的多行为融合训练机制，体现在模型中为Deep侧的appid embedding聚合共享。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9db5c74e87622332f427.png"/></p>
<p>由于appid类的特征较多，在实际选取时，我们主要利用了用户的实时行为特征和短期行为特征，避免了由安装/卸载记录带来的数据噪音。</p>
<p>Wide&amp;Deep中embedding参数约占总量的95%，通过特征共享，参数量从2800w降低到了2000w，在模型保存和训练速度方面均有一定的优化。</p>
<p>效果方面，我们主要考虑离线auc和copc（pcvr/cvr，反映模型打分偏差），经过特征共享的模型效果在auc上基本持平，而在copc指标上得到了明显的优化，一定程度上缓解了模型的打分偏差。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1bcf6f2d2826d96da239.png"/>由于我们的特征中用户行为只涵盖了15天内近30个app的记录，对于低频app依然没有充足的学习样本，该如何优化？ </p>
<h2>四、引入更长周期用户行为</h2>
<p>一种自然的想法便是引入更长周期的用户行为记录。近年来，以DeepWalk, Graphsage为代表的图模型能够较好地捕捉用户的长周期行为特点。<br/> 我们根据用户过去90天内的下载行为进行构图，考虑到用户在同一天中的下载序列无明显的先后关系，我们构建了基于共线下载的无向图，接着训练随机游走模型生成预训练的deepwalk appid embedding，作为先验信息指导排序模型优化。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/83c5200901b44666efe6.png"/></p>
<p>在共享appid embedding的基础上，我们尝试了多种训练策略。</p>
<ol><li>固定初始化：直接将预训练的deepwalk appid embedding赋值给共享appid embedding；</li>
<li>初始化微调：在1的基础上进行参数微调；</li>
<li>特征蒸馏：引入辅助loss，度量学习得到的embedding与预训练embedding的相似度（向量点积）；</li>
</ol><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f673d1075cc8a3402438.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5cb4d54ed9a36c418726.png"/></p>
<p>从效果来看，只有初始化微调的方式会带来一定的效果提升，说明经过deepwalk训练的embedding和wide&amp;deep训练的embedding在向量分布上是有差异的。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d86ce483ff8cbfe8c127.png"/>但目前为止auc的提升还很微弱，即使我们引入了30天甚至更久的用户行为数据，对于一些低频app依然无法充分学习，那是否还有外部信息可以利用呢？</p>
<h2>五、引入APP描述文本信息</h2>
<p>Deepwalk的训练本质是从用户行为信息中发掘app间的相似关联，若直接从app自身的属性信息（e.g., 标题、描述文本）出发，是否也能发现相似的规律？</p>
<p>近年来，以BERT为代表的预训练语言模型在文本表示方面取得了巨大的成功，我们将每个app的标题和描述文本作为输入训练tag分类模型，得到一个高维（768维）的向量表示，尝试指导Wide&amp;Deep中的appid embedding学习。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/db8d558b863b99782363.png"/></p>
<p>由于Wide&amp;Deep模型规模的限制以及前期的经验，我们的embedding size往往很小（30维/60维），更高的维度会导致效果下降，所以需要探索一种有效的降维方式。</p>
<p>这里我们主要尝试了外部pca降维和内部通过全连层自动学习的降维方式，实验表明，在网络中进行端到端自动学习的降维方式更有效果。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/76ea24ba19aca0db9381.png"/></p>
<h2>六、预训练embedding融合</h2>
<p>为了更直观地展现embedding分布，我们对deepwalk和bert预训练的embs分别进行了tsne可视化。图中不同的颜色表明不同的一级类目，二者均呈现了明显的类目空间聚集性，同类目的app自然地聚集到了一起；同时两者的embedding分布也具有空间差异性，比如，bert可视化图中的左下角部分是视频类app，而deepwalk是出行类app。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d9a4326528b1c7efc4c2.png"/></p>
<p>鉴于二者的差异性，我们的做法是将其分别做投影变换，投影到同一向量空间中，这里投影变换的参数随网络一起学习。融合embedding的方式则为拼接或相加。<em><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/64a4966b9d999ffcaccc.png"/></em></p>
<p>模型的整体框架图如下：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d365ef8db5481706eebf.png"/></p>
<p>从实验效果来看，向量投影拼接的方式具有更好的表现。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4aedfef16233bff1bb10.png"/>为了进一步展示加入deepwalk/bert外部预训练embedding的效果，我们接着进行了tsne可视化，其中左边为wide&amp;deep appid embedding的可视化表示，右边是融合embedding的可视化表示，可以发现app的分布从杂乱无序学到了呈现明显的聚簇，具有了一定的可解释性。 <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/40c4a4c0013de9da98e4.png"/></p>
<p>通过这个实验，我们已经知道app embs的初始化不同会对模型结果产生影响，那么它们分布的具体聚簇是否与模型效果有着严格的相关性，还需要更多的探索求证。</p>
<h2>七、基于attention的用户行为挖掘</h2>
<p>用户的历史行为对当前app推荐具有直观的影响，如下图中，同样的历史点击序列，对不同app的影响大小不同。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4c6169471d36fe5b253d.png"/></p>
<p>下图是用户近72h内同类目app点击次数（match特征）与cvr的关系，我们可以发现，用户历史点击的同类目app次数越多，当前app的cvr也就越高。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8aec4ee83d628edc3179.png"/></p>
<p>图中从123级类目由粗至细定位了用户的兴趣。但同类目的限制往往比较严苛，有时相关的app可能不在同一类目下（e.g., 和平精英、地图），而且用户的兴趣也更加广泛。于是我们使用基于attention的方式对用户行为进行挖掘，希望可以从一定程度上缓解同类目限制所带来的泛化性弱的问题。但由于用户行为序列极短，平均点击序列长度只有不到5个，一般的attention操作是否适用呢?</p>
<p>首先我们进行了一组基础attention的实验，额外引入app embedding作为query，对用户行为序列进行attenion 操作，具体公式和图示如下：<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a16317f31bc7a336f4eb.png"/></p>
<p>从效果来看，随机初始化query embedding的attention操作甚至会使效果变差，而且模型的训练过程往往第二个epoch开始就出现了过拟合。受上一步工作的影响，我们认为app embs query和key的初始化也对模型有着极大的影响。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9888fbf892764fd834df.png"/> 下图中展示了在i2i召回中，app相似度和cvr的关系。横坐标表示当前app和用户历史app的cos相似度的log值，蓝线表示cvr。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b6e5b549a7a373d12e7a.png"/></p>
<p>我们发现app召回中，cvr随着相似度的增加而增加，用户总是倾向于喜欢与他历史行为app相似的app。</p>
<p>体现在deepwalk/bert的融合embedding中，由于相似app具有明显的聚集性，它们的点乘得分也高。</p>
<p>在attention中，我们添加了以dw+bert融合向量为初始化embedding的点乘打分方式，最终效果auc效果提升明显。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/7341cf0ca80445253b38.png"/><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1ba5cc7e7ab1fc8a7ba1.png"/></p>
<h2>八、小结 </h2>
<p>综上，本文针对应用宝推荐场景下的两大挑战（app曝光差异大、用户行为少），从两方面对现有的深度CTR模型进行了改进：</p>
<ul><li>引入了基于Deepwalk的长周期用户行为挖掘和基于BERT的app文本描述信息增强；</li>
<li>利用attention机制挖掘用户的历史行为序列，并融合外部embedding，实现用户兴趣发掘。</li>
</ul> 
{% endraw %}
