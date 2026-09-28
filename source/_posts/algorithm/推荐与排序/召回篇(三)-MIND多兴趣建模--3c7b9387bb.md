---
title: "召回篇(三)-MIND多兴趣建模"
date: 2022-04-01 14:51:59
categories:
  - 算法
  - 推荐与排序
---

{% raw %}

<div></div>
<div>一、多兴趣推荐系统<br/><p>        推荐系统是由召回、粗排和精排等步骤构成。召回模型常用的方法是根据用户表征与大量Items表征之间的相似度来召回候选items，其重要的步骤之一便是来建模用户的兴趣，且根据用户的兴趣来构建用户的表征，由此能检索到与用户兴趣匹配的items。在微视短视频中用户与大量不同类型的items交互，反映出用户的兴趣是非单一，而是多样的。然而传统的推荐系统（例如经典的DSSM模型）只通过单一的用户表征来表示用户的兴趣，无法准确地表示出用户兴趣的多样性。用户的多兴趣推荐系统通过显性建模用户的多个兴趣能有效果缓解上述问题，例如MIND[2]通过对用户的不同兴趣点构建不同的表征，由此能提升召回items的多样性和准确性。</p>
<p>        目前主流的多兴趣推荐系统有DIN[1]、MIND[2]和基于MIND模型的一系列优化模型[3]。DIN是通过计算候选item与历史交互items之间的相似后，通过Sum Pooling操作来动态获取用户兴趣表征，然而由于DIN模型采用单个向量来表示用户兴趣，当遇到用户兴趣数量增多和复杂的用户兴趣等情况时，DIN模型表达用户的多兴趣能力不足。为解决上述问题，我们首先采用MIND模型[2]建模微视短视频领域中的用户多兴趣。MIND模型通过Dynamic Routing的方法，从用户行为和用户固有属性信息中动态学习出多个表示用户不同兴趣的向量，更好地捕捉用户的多样兴趣。此外，为在微视短视频业务场景中让MIND模型更好地发挥效果，我们针对MIND模型进行了一系列改进。</p>
<h1>二、模型的优化之旅</h1>
</div>
<div>
<h2>2.1 任务定义</h2>
<p>        在介绍模型之前，首先介绍推荐系统中召回任务，推荐系统召回阶段主要目标是从海量视频中获取与用户兴趣相关的候选集Item，用三元组表示一条训练样本，其中 [图片未保存到本地] 为用户行为序列（即与用户有交互行为的item序列）， [图片未保存到本地] 为用户基本属性（如性别、年龄）， [图片未保存到本地] 为目标Item的基本属性（如item id, category id）。</p>
<p>        正如第一章所述，我们采用MIND模型来建模用户的多兴趣，MIND主要任务就是学习一个函数可以将用户的原始特征映射为兴趣空间的向量表达：</p>
<p>[图片未保存到本地]</p>
<p>其中 [图片未保存到本地] 为用户多兴趣的向量表达，这里K表示用户的K个兴趣向量。</p>
<p>同样，目标Item的向量表达可以表示为：</p>
<p>[图片未保存到本地]</p>
<p>当我们学习到兴趣向量表达后，TopN候选Item可以通过dot product计算得出：</p>
<p>[图片未保存到本地]</p>
<h2>2.2 MIND模型</h2>
<p>        由于MIND模型本质上基于DSSM模型的优化，我们首先简要介绍下DSSM模型。DSSM模型是经典的双塔模型，模型采用复杂的网络结构分别对User侧和Item侧特征建模，且根据两者是否匹配来训练模型。预测时，通过User侧和Item侧的网络来分别获取User的和Item的embedding。但是由于经典的DSSM模型存在无法准确描述用户偏好多样性的缺点，我们引入MIND模型来建模用户的多兴趣。MIND模型的整体网络结构如图1所示，整体由Embedding和Pooling层、多重兴趣提取层、Label aware Attention层组成。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/3d64a8fe2e81e8ac54cb.png"/></p>
<p>图1 Mind模型的整体架构图</p>
2.2.1 Embedding和Pooling层<br/><p>        MIND的输入由三部分组成：用户属性、用户行为序列、和目标Item。每组输入都包含了极其稀疏的离散id类特征，因此使用embedding lookup的方式，将这些id特征映射为低维稠密的向量，从而可以显著减少参数量，并简化学习过程。如模型结构图中蓝框中的部分，User特征经过embedding后使用concat构成用户属性向量，Item特征在embedding后经过pooling层得到Item属性向量，多个Item向量按时间顺序排列好即得到用户行为序列表示。</p>
<p>2.2.2 多重兴趣提取层</p>
<p>        如果把与用户兴趣各种相关的信息都压缩成为一个表达向量，这会成为用户多样兴趣表达的瓶颈：因为在推荐召回阶段召回候选集时，用户不同兴趣混合在一起使用，会导致召回Item的相关性大大降低。因此，这里采用多个向量来表达用户不同的兴趣，将用户的历史行为分组到多个兴趣capsule，各个capsule分别提取出用户兴趣的一个特定方面，可见模型结构图中红框中的部分。</p>
<p>        Capsule network的思想在近两年由Hinton提出，首先用于CV领域。MIND在模型中借鉴了这个结构，但提出了自己的Behavior-to-Interest（B2I）dynamic routing，来代替原始的routing机制，计算逻辑如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/59af888938a1ef533e61.png"/></p>
<p>        通过这种方法，将用户行为序列的N个Item，由K个兴趣来表达。除此之外，MIND还提出在Capsule中使用动态的K：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/033a6e2141b51dac4a94.png"/></p>
<p>        其中， [图片未保存到本地] 为用户u的行为序列。</p>
<p>2.2.3 Label-aware Attention层</p>
<p>        通过多兴趣提取层，得到多个兴趣Capsule表达用户多样的兴趣分布。为了估计多个兴趣Capsule对目标Item 相关度及贡献度，MIND使用了Label感知的Attention机制来权衡目标Item选择使用哪个兴趣Capsule，如模型结构图中绿框部分：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/c0e30b3057f56b8657fd.png"/></p>
<p>        注意这一层只在训练中出现，用于辅助损失函数衡量用户兴趣和目标Item的相似度。</p>
<h2>2.3 MIND模型的优化策略</h2>
<h3>2.3.1 优化“动态路由”中初始兴趣向量</h3>
<p>        MIND模型的原始论文中对(图1中的红色框部分)实现方式的描述是在同一个batch中运行r次期间通过累加的方式实现的，但是上述描述存在两个疑惑点:</p>
<ol><li>
<p>[图片未保存到本地] 在不同batch之间是否共享？换言之，在当前batch中累加得到的 [图片未保存到本地] 是否传递到下一个batch？</p>
</li>
<li>
<p>[图片未保存到本地] 的初始值是通过随机初始化还是固定参数的方式实现的？</p>
</li>
</ol><p>       为探索上述两个问题，我们构建不同的组合来验证推荐的效果，例如 [图片未保存到本地] 在batch之间共享和随机初始化的方法，实验结果表明 [图片未保存到本地] 在batch之间非共享和固定初始化的方式效果最佳，可能的原因是batch之间的累积是无意义的，且每个batch采用随机初始化的方法会导致Serving时同个用户行为序列多次运行会产生不同的用户向量，此不确定性也影响了模型的稳定性。</p>
<h3>2.3.2 修正Label-aware Attention层中的权重</h3>
<p>        Label-aware Attention层的意义是在训练过程中，根据目标item将K个兴趣向量通过Attention机制融合，从而使loss优化的重心更多的放在前向传播时已经与目标item很相似的兴趣向量上。但在实际训练过程中，多数情况是每个兴趣向量的Attention差异不大。为了让“正确”的兴趣点得到更多的“关注”，换言之，如何让兴趣分布更加 “尖锐”，原始MIND采用以下方式：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/deb2fd641e949d156400.png"/></p>
<p>        其中， [图片未保存到本地] 表示K个兴趣向量组成的矩阵, [图片未保存到本地] 为正样本的item向量，p是调整兴趣分布平滑度的超参数。本质上通过调整指数操作中的指数p来调整兴趣分布的平滑度，特别是当p→无穷时，类似于hard attention操作。优势在于与target更相似的兴趣向量会在 [图片未保存到本地] 中成分占比更高，相应的在梯度回传时，传回的梯度也相对更大。</p>
<p>        尽管这个hard attention的想法在这里用的很巧妙，但我们在这里需要指出一个明显的缺陷：超参数p是偶数时，会完全消去兴趣向量与目标item向量相似度的正负性，其结果的单调性也被完全破坏！由此我们将公式中的power调整为了乘法：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/3aaaf94179091a0513f5.png"/></p>
<p>        既满足了attention平滑度的可调整的特性，p的奇偶性也不会影响结果的单调性。</p>
<h3>2.3.3 融合负向用户行为(“Hard”负样本)</h3>
<p>        不同于CTR场景的推荐业务，微视短视频业务的负样本定义较为清晰：刷到但是快划的的视频，通常是用户不感兴趣的。所以我们在构建损失函数时，也加入了这一用户负向行为，构成了除随机负采样之外的“Hard”负样本。“Hard”负样本能提供额外的用户反馈信息，增加模型的信息量。由此我们在构建最终损失函数时，采用三类样本：正样本、“Hard”负样本和随机负采样样本。</p>
<p>        值得注意的是"Hard"负反馈行为序列与随机负采样的items不同，随机负采样的items是从整个items库中随机采样(不指定用户和行为反馈类型)，"Hard"负反馈样本是指定某个特定的用户随机采样其负向行为的items(在微视短视频中特指用户快滑操作对应的items)。</p>
<h3>2.3.4 训练与预测的兴趣向量一致性</h3>
<p>        由于训练MIND模型时，采用的动态K来建模不同长度的用户行为序列的兴趣点，例如对于较短的用户行为序列，构建的兴趣点较少(具体查看2.2章的第二部分)。 在Mind模型原文的Serving过程中，默认采用用户全部兴趣的表征来召回Items，会导致置信度低的兴趣向量参与召回流程，召回不相关的items。因为在训练时会Mask大于动态兴趣数量K对应的兴趣向量，导致这部分兴趣表征未充分学习到，从而降低召回的准确性。为解决上述训练与预测的兴趣向量不一致性的问题，我们在Serving时，采用与训练流程一致的方法，只使用动态K范围内的兴趣向量进行召回。</p>
<h2>2.4 训练与在线服务</h2>
<h3>2.4.1 模型的训练</h3>
<p>        模型训练是首先通过构建用户向量u和目标item向量e进行交互的概率值，具体计算方式如下:</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b2f3df09a9f4c6f0e1da.png"/></p>
<p>        之后构建模型整体的损失函数如下所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2ea820e148d5eb6a97e2.png"/></p>
<p>       其中，D是所有用户与item之间的交互行为数据。</p>
<h3>2.4.2 模型部署为在线服务</h3>
<p>        MIND在在线落地时，是作为u2i召回通路来提供召回的。部署时，我们采用了固定初始化、非累积的动态路由参数，以及动态的兴趣个数来进行召回。</p>
<p>三、实验结果与分析</p>
<h2>3.1 实验数据</h2>
<p>本节介绍训练Mind模型的实验数据样本构成形式，具体成分如下所示:</p>
<ol><li>
<p>一条样本由(user_feat, sequence, targets)构成，其中user_feat为用户侧的特征，sequence为用户行为序列，targets为训练所需的三类items，具体见(2)和(3)。</p>
</li>
<li>
<p>sequence由多个item构成，每个item有相同个数的item_feat。</p>
</li>
<li>
<p>target由三部分构成：行为正向item、行为负向item 和 随机负采样item。这些item和sequence同样，有相同个数的item_feat。</p>
</li>
<li>
<p>样本生成时进行shuffle。</p>
</li>
</ol><h2>3.2 离线实验结果与分析</h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/5b00733e994b172211d1.png"/></p>
<ol><li>
<p>从实验1发现优化“动态路由”中初始兴趣向量在Hit@10和NDCG@10上均优于原始的Mind模型，可能原因是通过取消batch之间的累积来排除训练阶段batch之间的干扰和固定每次batch的初始化来保证Serving时保证产出用户向量的唯一性。</p>
</li>
<li>
<p>从实验2中发现，通过修正Attention中的权重为相乘的形式能提升推荐性能，说明将计算相似度从指数修改为乘法时，既满足attention平滑度的调整，p的奇偶性也完全不影响结果的单调性。</p>
</li>
<li>
<p>从实验3表明在loss中加入负向用户行为一方面能考虑增加模型训练的难度，另一方面能为模型提供更多用户的偏好信息，能进一步提升召回的准确性。</p>
</li>
<li>
<p>从实验4中发现在Serving过程中屏蔽冗余的兴趣向量能提升模型的推荐效果，说明保持训练和Serving阶段一致性保证了两者不产生偏差，防止Serving时利用到不置信的兴趣向量，导致模型推荐的精度下降。</p>
</li>
</ol><h2>3.3 在线效果</h2>
<p>MIND在上线后，为取得了如下收益：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a9a766c35b946053d0de.png"/></p>
<p>四、结论与未来方向</p>
<h2>4.1 结论</h2>
<p>        由于现有主流的方法是通过复杂网络模型为用户生成单一的向量，而在微视短视频业务中，用户的兴趣点是多样的，因此单一向量构成的用户表征无法准确建模用户的多兴趣。为解决上述问题，我们引入MIND模型来建模用户的多兴趣，且针对MIND模型的一些问题做了一系列优化。</p>
<h2>4.2 未来方向</h2>
<ul><li>
<p>缓解用户兴趣向量同质化问题。</p>
</li>
<li>
<p>真实兴趣点个数决定动态K。</p>
</li>
<li>
<p>引入多目标，提供更精细化的召回;</p>
</li>
</ul>五、参考文献<br/><ol><li>
<p>Deep interest network for click-through rate prediction.</p>
</li>
<li>
<p>Multi-Interest Network with Dynamic Routing for Recommendation at Tmall</p>
</li>
<li>
<p>Diversity Regularized Interests Modeling for Recommender Systems</p>
</li>
<li>
<p>Sequential Recommendation with User Memory Networks</p>
</li>
</ol><p></p>
<p></p>
</div> 
{% endraw %}
