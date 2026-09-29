---
title: "user embedding技术3 – SocialTrans：BERT与GNN的结合"
date: 2022-04-16 10:34:49
categories:
  - 算法平台
  - 图学习与内容理解
---

{% raw %}

<h2>1.   背景</h2>
<p>社交网络中的用户行为会受用户自身兴趣以及身边朋友的影响，在对任务进行建模的时候需要同时考虑这两种因素。本工作尝试解决的问题是，<strong>针对社交网络（如</strong><strong>QQ</strong><strong>、、豆瓣）环境，如何同时刻画用户自身兴趣以及好友对其的影响，提供高质量的推荐结果</strong>。我们之前的相关工作[4][5][6]利用了BERT对用户行为历史进行建模，其本质是利用了物品的协同信息。但对于行为稀疏的用户，其Embedding向量质量较差，在这里我们利用了GAT模型对用户的社交兴趣进行刻画，提高了冷启动用户的Embedding表达质量。本工作使用BERT（层叠Transformer）对用户历史行为进行建模，使用GAT对社交兴趣进行刻画，最后融合上述两个子模块得到user embedding，随后生成推荐结果。这里我们<strong>在</strong><strong>2</strong><strong>个离线数据集和1</strong><strong>个在线环境中，验证了本方案的有效性</strong>。</p>
<p>大规模BERT相关技术（包括本工作SocialTrans）产生的Embedding已沉淀至<strong>自研数据挖掘平台</strong><strong>-</strong><strong>笛卡尔[</strong><strong>7</strong><strong>]</strong>和<strong>自研图计算引擎</strong><strong>-</strong><strong>柏拉图[</strong><strong>8</strong><strong>]</strong>中：</p>
<ol><li><strong>的相关数据embedding</strong><strong>结果</strong>，会在<strong>笛卡尔特征库</strong>中供大家使用。</li>
<li><strong>柏拉图平台提供embedding</strong><strong>相关算法组件</strong>，供业务团队生成需要的Embedding。</li>
</ol><p>如有需求，欢迎合作！</p>
<h2>2.   社交影响力的有效性</h2>
<p>在开始本工作之前，我们对用户在中的公众号文章转发行为进行了分析。分析的结果如下图所示，具体可参考附录分析过程，结论为：</p>
<ul><li>用户的文章转发行为受好友的影响，同时也受社交网络中的高阶邻居的影响（举个例子，二阶邻居是用户好友的好友，三阶邻居是用户好友的好友的好友），影响力随阶数增加而迅速衰减；</li>
<li>在不同文章类目上，用户的行为受到好友的影响是不一致的，如在公众号文章中，用户在IT、财经类的新闻上更容易受到好友的影响，在娱乐类新闻上更不容易受到影响。<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1a9aa315d2536d86bd3f.png"/></li>
</ul><p>该<strong>分析结论验证了社交影响力的有效性</strong>，同时启发了我们在社交环境中进行推荐是需要考虑到好友因素的，同时需要考虑到不同类目对用户影响是不一致的情况。在这里我们<strong>在关系链上使用</strong><strong>GAT [</strong><strong>1</strong><strong>] </strong><strong>对社交因素进行建模</strong>，优点是：1）能将好友的信息聚合到用户身上；2）注意力机制能考虑到好友的偏好对用户影响力是不同的影响。</p>
<h2>3.   模型框架</h2>
<p>下图为本工作使用的模型架构。这里<strong>使用了</strong><strong>BERT(</strong><strong>多层的Transformer [</strong><strong>3</strong><strong>])</strong><strong>对用户自身的兴趣进行建模，使用了多层的GAT [</strong><strong>1</strong><strong>] </strong><strong>对用户的好友信息进行聚合</strong>，最后将上面获得的两个结果合并在一起，最后进行模型的预测打分。为了让读者更快的了解工作，在这里不对公式进行展开，<strong>具体公式在附录</strong><strong>-</strong><strong>建模过程中，建议大家选择性观看</strong>。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9240b777474098596d6d.png"/></p>
<h2>4.   实验结果</h2>
<p>在这里我们进行了离线测试和在线测试。其中离线测试包含一个公开数据集Yelp，以及的公众号阅读数据集（目标为预测在用户历史中未出现的公众号阅读，类似推荐未关注公众号给用户）。而在线测试为使用公众号的阅读数据生成Embedding，随后在看一看上进行推荐。</p>
<p>在离线测试上，我们对比了热度推荐（POP），时序模型算法（GRU4Rec, BERT）和图模型算法（mepath2vec、GAT），我们的方法（SocialTrans）均有较大的提升。</p>
<table><tbody><tr><td rowspan="2">
<p><strong>模型</strong></p>
</td>
<td colspan="2">
<p><strong>Yelp</strong></p>
</td>
<td colspan="2">
<p><strong>WeChat Offical Acct.</strong></p>
</td>
</tr><tr><td>
<p><strong>recall@20</strong></p>
</td>
<td>
<p><strong>NDCG</strong></p>
</td>
<td>
<p><strong>recall@10</strong></p>
</td>
<td>
<p><strong>NDCG</strong></p>
</td>
</tr><tr><td>
<p>POP</p>
</td>
<td>
<p>1.05%</p>
</td>
<td>
<p>9.39%</p>
</td>
<td>
<p>3.87%</p>
</td>
<td>
<p>12.22%</p>
</td>
</tr><tr><td>
<p>GRU4Rec</p>
</td>
<td>
<p>5.84%</p>
</td>
<td>
<p>11.68%</p>
</td>
<td>
<p>6.27%</p>
</td>
<td>
<p>13.03%</p>
</td>
</tr><tr><td>
<p>BERT</p>
</td>
<td>
<p>6.18%</p>
</td>
<td>
<p>12.83%</p>
</td>
<td>
<p>7.01%</p>
</td>
<td>
<p>13.50%</p>
</td>
</tr><tr><td>
<p>metapath2vec</p>
</td>
<td>
<p>1.06%</p>
</td>
<td>
<p>9.41%</p>
</td>
<td>
<p>5.23%</p>
</td>
<td>
<p>12.42%</p>
</td>
</tr><tr><td>
<p>GAT</p>
</td>
<td>
<p>6.27%</p>
</td>
<td>
<p>12.92%</p>
</td>
<td>
<p>8.52%</p>
</td>
<td>
<p>14.45%</p>
</td>
</tr><tr><td>
<p>SocialTrans</p>
</td>
<td>
<p>6.87%</p>
</td>
<td>
<p>13.23%</p>
</td>
<td>
<p>9.75%</p>
</td>
<td>
<p>15.19%</p>
</td>
</tr></tbody></table><p>在离线测试效果上提升后，我们将模型进行了上线。由于看一看每天能推荐的文章十分的多，这需要模型更新速度较快，计算开销也较大。为此我们采取了一种基于User-CF的间接验证的方案。具体流程为：</p>
<ol><li>使用训练数据训练模型，并生成用户的User Embedding；</li>
<li>对每个用户，根据用户的User Embedding寻找Top K_u兴趣相似的其他用户；</li>
<li>将Top K_u兴趣相似的其他用户的最近阅读文章进行召回；</li>
<li>使用统一的排序模型进行排序，并将Top K_a篇文章推荐给用户；</li>
</ol><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/904b03d82806010c1bb5.png"/></p>
<p>采取本流程进行评测的目的，一是为了解决文章更新速度较快的问题，二是我们关注的工作重点是在User Embedding上。在看一看上，我们对数据中心已有的方案对4天的CTR进行测试，具体数据为：</p>
<table><tbody><tr><td>
<p>　</p>
</td>
<td>
<p>CTR</p>
</td>
<td>
<p>相对提升</p>
</td>
</tr><tr><td>
<p>metapath2vec</p>
</td>
<td>
<p>18.96%</p>
</td>
<td>
<p>0%(基准)</p>
</td>
</tr><tr><td>
<p>BERT</p>
</td>
<td>
<p>19.72%</p>
</td>
<td>
<p>3.99%</p>
</td>
</tr><tr><td>
<p>SocialTrans</p>
</td>
<td>
<p>20.08%</p>
</td>
<td>
<p>5.89%</p>
</td>
</tr></tbody></table><p>可以看出我们的方案相比之前的方法有明显的提升。证明<strong>用户个性兴趣和社交信息结合产生的</strong><strong>Embedding</strong><strong>会有效果提升</strong>。</p>
<h2>5.   总结展望</h2>
<p>本工作我们对BERT进行了改造，增加了社交的信息，在离线和在线的效果上均有正向提升。最后，大规模BERT相关技术（包括本工作SocialTrans）产生的Embedding已沉淀至<strong>自研数据挖掘平台</strong><strong>-</strong><strong>笛卡尔[</strong><strong>7</strong><strong>]</strong>和<strong>自研图计算引擎</strong><strong>-</strong><strong>柏拉图[</strong><strong>8</strong><strong>]</strong>中：</p>
<ul><li><strong>的相关数据embedding</strong><strong>结果</strong>，会在<strong>笛卡尔特征库</strong>中供大家使用。</li>
<li><strong>柏拉图平台提供embedding</strong><strong>相关算法组件</strong>，供业务团队生成需要的Embedding。</li>
</ul><p>如有需求，欢迎合作！</p>
<h2>附录-分析过程</h2>
<p>针对公众号场景，如果一个好友（或者高阶邻居）转发了文章且该用户也转发了文章，则称该用户受到了好友的影响。本分析中我们对n度好友对用户的影响能力感兴趣，为此定义n阶好友影响力如下：</p>
<ul><li>定义用户-文章-好友-阶数的影响力 - H(u, a, v, n)，表示对文章a，当u受到n阶邻居v的影响时，H(u,a,v,n)则为1，否则为0；</li>
<li>定义用户-文章-阶数的影响力 - H(u, a, n) = AVG_{v属于u的n阶邻居} H(u, a, v, n)，代表对文章a，用户u受到n阶邻居影响的平均概率；</li>
<li>定义文章-阶数的影响力 – H(a, n) = AVG_{u为阅读a文章的用户} H(u, a, n)，代表对文章a，随机用户受到n阶邻居影响的平均概率；</li>
<li>定义阶数影响力 – H(n) = AVG_{任意文章a} H(a, n)，代表对随机文章随机用户受到n阶邻居影响的平均概率；</li>
</ul><p>针对阶数影响力，我们分析H(n)-H(0)的大小值，其中H(0)为全局阅读转发概率。直觉上，该数值可视为用户收到n阶邻居信息后对转发行为决策的改变程度。在本分析中，我们从6月份的公众号阅读数据中，针对金融财经、科技互联网、追星娱乐类目中各抽取一篇转发在[10000,11000]的文章进行分析。</p>
<h2>附录-建模过程</h2>
<h3>1)    用户兴趣建模-多层Transformer</h3>
<p>随着时间的增加，用户兴趣本身可能会发生迁移。比如热爱科技互联网的同事可能会突然对养生和金融财经感兴趣。在这里为了补抓这种时效性的迁移特点，本工作使用了单向多层Transformer进行建模，具体模型细节可以参考 [2]。在这里简要介绍一层Transformer中所含的具体模块。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a30894493036769bf919.png"/></p>
<p><strong>输入数据：</strong>第一层Transformer的输入是由，用户的物品点击序列中，每个点击的物品的embedding构成。同时为了增加位置信息，增加了position embedding。形式化为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4f68689c2660c2122055.png"/></p>
<p>其中\tau为具体点击物品下标，w为对应物品的embedding，p为对应位置的position embedding。</p>
<p><strong>多头注意力机制：本子层的作用是，每个位置对先前的信息进行聚合。</strong>在这里使用了跟文章[3]一样的注意力机制，具体地对输入数据投影至query、key、value空间后再进行注意力计算，形式化为：</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm-platform/381323b1b4b924f8d6d0.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/18d35fce59113945550b.png"/></p>
<p>上述为单个注意力机制的聚合结果，实践中往往发现多个注意力机制合并起来有更好的结果，为此需要一种多头注意力的计算以及融合机制：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4932b8ac5e171e81fa3e.png"/></p>
<p><strong>前向网络：针对多头注意力机制生成的结果仍是简单的线性聚合结果的问题，本子层的作用是进行非线性变换。</strong>在此引入了一个两层的全连接神经网络，对每个位置的聚合结果分别进行非线性变换。形式化为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/26bda91991bffec8443c.png"/></p>
<p>其中f为激活函数，在这里我们选取了Gaussian Error Linear Unit。</p>
<p><strong>残差与归一化层（Add&amp;Norm</strong><strong>）</strong>：<strong>本层是为解决深度学习中层数过深出现的梯度消失问题而引入的。</strong>残差网络是深度学习中常用的技巧，它将网络中的底层特征与高层特征直接进行相加，达到最终目标中仍可快捷访问底层特征的效果。对底层特征X与高层特征Y，形式化为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c7b0918acf1966645f93.png"/></p>
<p>而为了让学习更加的鲁棒稳定，在这里引入了Layer Normalization。形式化为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/67db0495690cb6682d71.png"/></p>
<p><strong>模块输出：此处将多层Transformer</strong><strong>中最后一层最后一个时刻的结果作为用户自身兴趣embedding</strong>，如同我们相关工作 [5] 的具体做法。</p>
<h3>2)    用户社交兴趣建模-多层GAT</h3>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/2b795e503375e51556a3.png"/></p>
<p><strong>模块输入：</strong>在用户兴趣建模的模块输出中，用户自身兴趣会被表示成为Transformer对用户阅读序列进行转换后的输出。而对于用户的好友，也采用相同的Transformer对其序列进行转换。随后将用户与好友的自身兴趣embedding输入到GAT中。</p>
<p><strong>GAT</strong>：<strong>GAT</strong><strong>的作用是，将好友的信息聚合到自己身上</strong>，这里做简要介绍，更详细的描述可参考论文 [1]。首先针对用户u和u’，根据自身兴趣embedding和边特征e_{u,u’}计算其相似性得分，形式化为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/224631264cbcfe886dea.png"/></p>
<p>上述公式代表好友对u与u’的相似性得分为自身兴趣embedding的相似性加上边特征的加权。随后将上述相似性得分进行归一化，方便后续进行信息聚合，形式化为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/630254f152f591f820af.png"/></p>
<p>最后，对用户u根据上述归一化得分聚合好友的信息：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9b018fbc44ca4e8fb196.png"/></p>
<p>在实际应用中，我们发现使用Transformer一样的多头的注意力机制能提升模型的效果，因此将上述公式全修改为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/44c026e4a613bb627698.png"/></p>
<p>随后对多头的输出进行结果合并：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/99fce6d5b637a1deef64.png"/></p>
<h3>3)    模型训练</h3>
<p>针对用户兴趣建模和社交兴趣建模出来的结果，在这里先使用一个全连接层对其进行合并：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/29c84119d7f351952ea2.png"/></p>
<p>随后使用softmax函数对用户的下一物品进行预测：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/16dbfaec7b53a26db4b3.png"/></p>
<p>模型训练的目标为最大化训练数据中出现的用户-下一物品预测概率：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a6ec0c0a4016f803c832.png"/></p>
<h3>4)    大规模实现优化</h3>
<p>上述模型在面对实际问题的时候（如数亿的用户，数百万的物品规模），会存在效率上的问题。在这里介绍我们为模型上线所做的一些优化。</p>
<p><strong>图采样</strong>：原始的GAT无法适应上的数据规模（十亿用户，千亿关系链）。在这里我们对原图进行了采样，针对每个节点，<strong>根据共同点击物品数的特征去采样</strong><strong>Top K</strong><strong>好友</strong>，并删除掉不在Top K列表中的好友。相比于随机采样的方式，我们发现这种采样策略更加有效。</p>
<p><strong>共享负样本</strong>：在预测计算的时候，由于softmax函数需要计算用户和所有物品对的得分，会大量浪费计算资源。在这里我们<strong>使用了采样的方式，对</strong><strong>softmax</strong><strong>函数进行估算</strong>。在每个batch中，采样1000个负样本集合J，这1000个负样本用于估算下一物品的预测概率：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/35adb56d9d77c9183d7a.png"/></p>
<p><strong>稀疏更新优化器：</strong>我们在训练过程中，使用Adam作为模型求解的优化器。但是应用共享负样本技术后，Adam的参数更新仍会更新到在本轮中未出现的负样本。为此需要一个稀疏更新的优化器，在这里我们修改其为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/0721fd7f7ccfe8c5c2a8.png"/></p>
<p>其中\Theta_k为在本轮batch中出现的正负样本和其他模型参数。这种更新方式实质为，<strong>对有出现的参数才进行更新，对没出现的参数则保留。</strong></p>
<p><strong>多GPU</strong><strong>实现：</strong>Transformer和GAT叠加的方式会对计算速度有较大的要求。在这里我们使用了单机4卡的方式对模型进行训练，并使用ring all reduce的机制进行参数通信。</p>
<p><strong>SparkFuel [</strong><strong>9</strong><strong>]</strong><strong>生成Embedding</strong><strong>：</strong>我们采取了多阶段生成Embedding的方案，该方案能不使用GPU的情况下，生成聚合了用户个性兴趣和社交兴趣的Embedding，具体为：</p>
<ol><li>第一阶段：使用SparkFuel生成用户个性兴趣Embedding，由于仅使用Transformer，计算压力较少；</li>
<li>第二阶段：对每个用户，检索其个性化兴趣Embedding和好友个性化兴趣Embedding，本阶段涉及IO操作较多，可通过SparkSQL实现；</li>
<li>第三阶段：对每个用户，根据第二阶段得到的Embedding，生成社交兴趣Embedding和最后融合的Embedding，本阶段是另外一个SparkFuel程序。</li>
</ol><h2>附录-重要引用</h2>
<ol><li>Petar Veličković, Guillem Cucurull, Arantxa Casanova, Adriana Romero, Pietro Lio, and Yoshua Bengio. 2018. Graph attention networks. In ICLR.</li>
<li>Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2019. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. In NAACL. 4171–4186.</li>
<li>Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. 2017. Attention is All you Need. In NIPS. 5998–6008.</li>
<li> User embedding技术应用综述. http://[内部链接已移除]</li>
<li> User embedding技术1：用户行为序列建模Bert4UserEmbedding. [内部或本地链接已移除]</li>
<li>User embedding技术2：Bert大规模预训练算法. [内部或本地链接已移除]</li>
<li>笛卡尔，[内部或本地链接已移除]</li>
<li> 2019年上半年公司级技术突破奖：高性能图计算Plato项目. [内部或本地链接已移除]</li>
<li> Spark-Fuel: 助力Spark ML腾飞. http://[内部链接已移除]</li>
</ol> 
{% endraw %}
