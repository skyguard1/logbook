---
title: "让AI精准匹配新闻标题：详解语义匹配算法与建模细节"
date: 2022-04-27 14:25:46
categories:
  - deep-learning
---

{% raw %}

<h2>一、研究背景</h2>
<h3>1.1 任务定义</h3>
<p>        语义匹配是指，给定两段文本，判断是否同义。具体来说，在我们的场景中，给定两篇新闻的标题ta, tb，判断ta和tb是否同义。产品在新闻推荐时，同义的新闻，不会重复推荐给用户。下图展示了两组同义标题：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/f19cebadb358f30ef888.png"/></p>
<h3>1.2 挑战</h3>
<p>挑战主要来自两个方面：任务层面和数据层面。</p>
<p><strong>任务层面的挑战</strong>：自然语言理解按照深浅层次，可以分为词法分析、句法分析和语义分析。如下图所示，颜色越深，表示难度越大。语义匹配属于最后一个层次。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/56dda42e82bf1d7dc574.png"/></p>
<p>下图展示了两类典型的困难case。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/662ecc2f39913cc0fd04.png"/></p>
<p>        第一个例子中，两个标题描述的事件虽然相同，但处于不同阶段：标题1表述的是“周末将迎来中考”，而标题2描述的是开考的场景。第二个例子中，字面差异很大，但描述的内容相同。其中，句2中的“一个动作惹人心疼”指的是句1中的“不慎摔倒”，需要深度理解+推理才能解决。</p>
<p><strong>数据层面的挑战</strong>：数据的构造是语义匹配面临的另一个挑战。主要体现在两个方面：</p>
<ul><li>候选数据的构造：如何保证多样性</li>
</ul><ul><li>候选数据标注：标注难度大；需要标注的数据规模大</li>
</ul><h3>1.3 小结</h3>
<p>      本文主要介绍我们在基于交互特征的语义匹配模型上的探索。所谓交互特征模型，是指计算标题向量时，需要同时考虑两个标题的信息。目前模型已在快报标题去重项目中应用。交互特征的匹配模型需要对pair中的句子联合计算表示向量，计算量大，并且无法预先计算，不适用需要密集计算匹配的场景，例如信息检索。我们还探索了基于编码的匹配模型，在该框架下，可以预先计算出所有标题的表示向量，后续只需要基于标题的表示向量做简单运算即可判断是否能够匹配。后续将在下一篇文章中进行介绍，欢迎关注。相关能力已上线博通平台（体验链接），欢迎体验接入。</p>
<h2>二、数据构造</h2>
<h3>2.1 训练数据</h3>
<p>        由于pair的标注难度和规模都很大，因此尝试自动构造训练集。我们内部有一个事件挖掘服务，该服务依据文章的关键实体、关键词等信息对快报文章进行聚类，将相同事件的新闻聚合到同一个簇下。我们基于事件事件挖掘服务产生的事件库构造训练集，流程如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/10af7c7853abbabbbd80.png"/></p>
<p>        值得注意的是，为了保证构造的负例具有一定的难度，我们将同一簇下相似度小于一定阈值的pair作为负例。这里的相似度通过无监督的SIF模型计算。该流程共构造170w pair，其中正例62w，负例108w。抽样评估准确率，正例准确率90%，负例准确率86%。</p>
<p>        自动构造的数据冗余性较大，我们通过实验发现，随机选择其中的30w pair，可以达到和170w数据相近的效果（详情见下表）。为了加快后续模型训练的速度，我们随机选择其中的30w作为训练集。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/a6d8f2b57b29cf3f80b9.png"/></p>
<p>        事件挖掘流程是基于实体进行的，因此事件库中所有新闻标题中至少包含一个实体。因此，上述流程抽样出的数据全部包含实体，缺乏没有实体的数据，多样性差。因此，我们还将WSDM2019上谣言匹配评测的数据集加入到训练集中（下图展示了该数据集的pair示例），增加训练数据的多样性。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/4bde95fb2609d142aaa0.png"/></p>
<p>最终，我们的训练集如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1feeaf38dcb60b0c312b.png"/></p>
<h3>2.2 测试集</h3>
<p>测试集需要尽可能反映真实场景，并且标注准确，评估的结果才可信。为了实现上述目标，我们构造测试集的策略如下：</p>
<ul><li>随机选择一批新闻标题，两两组合，构成候选pair （保证数据真实性）；</li>
<li>根据标题是否包含实体，分四类分别抽样满足条件的pair（共1w条）（多样性）；</li>
<li>WSDM谣言匹配语料中，抽样4000条加入到测试集 （多样性）；</li>
<li>人工对上述1.4w条进行标注（准确性）</li>
</ul><p>下表展示了测试集的统计信息：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/ce21967941123b79a07a.png"/></p>
<h3>2.3 数据集对比</h3>
<p>        LCQMC和BQ是中文语义匹配学术研究中比较常用的公开数据集。前者是知道的问题对，后者是银行客服的问题对。我们从如下两个维度对测试数据集进行评估：</p>
<ul><li><strong>标题多样度</strong>：标题多样度反映测试集中标题的多样性。标题多样度=测试集不重复的标题数/测试集总标题数；</li>
<li><strong>标题特异度</strong>：标题特异度反映了测试集中标题和训练集不重合的程度。标题特异度=测试集独有的标题数/测试集不重复的标题数；</li>
</ul><p>        上述两个指标都是越大越好。为了便于表示，本文将我们构造的数据集取名为“<em><strong>TitleMatch</strong></em>”，下表展示了不同数据集在上述指标上的统计信息：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/e2f09d6dba5178dc59de.png"/></p>
<p>        由上表可见，LCQMC和BQ存在不同的问题。我们还用BERT实验了不同数据集上的效果，用于验证各个数据集的难度，结果见下表：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/fbbc1f4c104fa3af73e5.png"/></p>
<p>        由表可见，由于BQ和LCQMC各自存在的问题，导致任务过于简单，模型取得很好的效果。而我们的数据集更符合真实场景，难度更大。</p>
<h2>三、算法与模型</h2>
<h3>3.1 评价指标</h3>
<p>        由于测试集正负例分布不均（正:负=1:6），因此acc不能很好的衡量模型的效果。实际应用中，我们只关心模型在正例（匹配上的pair）上的效果，因此采用正例上的P，R，F作为评价指标，定义如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/5ed5e3ea41e722a79e00.png"/></p>
<p><strong>3.2 Baselines</strong></p>
<p>我们实现了如下几组Baseline模型：</p>
<ul><li><strong>无监督模型</strong></li>
</ul><ol><li>VSM：词袋模型，基于词是否出现构建高维稀疏向量</li>
<li>W2V：基于word2vector模型训练词向量，并将句子中所有词词向量的平均向量作为句子的表示向量</li>
<li>SIF：W2V没考虑词的权重，SIF首先为每个词计算权重，然后将加权平均的词向量作为句子表示向量</li>
</ol><ul><li><strong>有监督模型</strong></li>
</ul><ol><li>BIMPM：建模多维度交互信息</li>
<li>BERT：12层BERT</li>
</ol><p>各模型效果如下表所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/ac84c61ce64fdfda8fe4.png"/></p>
<p>其中，BIMPM和BERT表示在58w语料上训练，BIMPM+在58w+140w（最初构造的语料剩余部分）语料上训练。</p>
<p>由表可见：</p>
<p>a). BiMPM模型对训练数据量的要求更大。在数据构造章节已经证明，BERT在30w和170w数据训练结果相差不大，而BIMPM则有较大差异，说明BIMPM需要更多的训练数据。</p>
<p>b). BERT的效果显著比其它方法好。</p>
<p><strong>3.3 Pooling or no Pooling</strong></p>
<p>下图展示了BERT做语义匹配的网络结构：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/900e0c4acd00734d3ad7.png"/></p>
<p>        最后一层Transformer输出的CLS表示，会经过一个pooler层（全连接层），然后进入softmax分类层。我们对比了pooling之前的向量和之后的向量分别作为分类层的输入，模型效果上的差异，结果见下表：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/11d7574d286d7c8af04c.png"/></p>
<p>        实验证明，经过pooler层的向量效果更好。这是因为该层在BERT预训练阶段建模了句子之间的关系信息，因此对语义匹配任务具有正向作用。</p>
<h3>3.4 调整学习率</h3>
<p>        多篇相关工作指出，学习率对BERT的效果影响很大。上面的实验，学习率采用了Google发布代码中默认的学习率，lr=5e-5。利用网格搜索策略，我们尝试了不同学习率下模型的效果，详情见下表：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/7216d49b04123858f770.png"/></p>
<p>由表可见，和默认学习率5e-5相比，调整后的学习率6e-6对应的F值提升了4.2个点，提升幅度巨大。</p>
<h3>3.5 建模细节信息</h3>
<p>BERT模型层次很深，能够建模深层语义，但对浅层的细节信息把握不准。典型case如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/fcf9ab3339235b395c2d.png"/></p>
<p>为了显示建模细节特征，我们在模型中引入浅层特征（shallow feature）模块。如下图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/087414485b4edc49653d.png"/></p>
<p>其中，浅层特征模块使用的特征集合如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/8465693021ba28e6fdc3.png"/></p>
<p>首先，对pair进行特征抽取，得到原始稀疏特征向量，然后特征组合模块对特征向量作笛卡尔积运算，建模二阶组合特征。最后，将得到的浅层特征向量和BERT输出的深层特征向量进行拼接，经过softmax分类得到匹配结果。实验效果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/3ff5d9c55bcd884b0d72.png"/></p>
<p>由表可见，加入浅层特征模块，模型匹配效果取得了一定的提升，但幅度不大。分析数据发现，由于测试集规模有限（1.4w），能够有效反映该策略的case不多。因此，我们构造了1000条针对性的负例加入测试集，基本思想是随机替换句子中的实体、地域、时间或英文数字，组成pair，作为负例。下面展示了四类替换策略产生的负例：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/6642133cfbfb7c63b9a2.png"/></p>
<p>新测试集（1.4w + 1k）,模型效果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/330f57cbad2d04f2a17a.png"/></p>
<p>新测试集上，我们的模型比BERT取得了显著的提升。这表明，加入浅层特征模块后，模型能够更好地区分细节信息。</p>
<h3>3.6 拆分数据，分别训练</h3>
<p>        分析bad case发现，有很多字面差异较大的pair，被错误匹配。主要原因是，对于事件性的pair，少数关键信息相同即表示它们同义，而非事件性pair则需要更多的相同成分才表示同义。下图展示了一个例子：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/e93fedcbc0d4d1ebc73c.png"/></p>
<p>        第一个是非事件性标题，两句词汇重合度低，语义不同；而第二句是事件性标题，虽然重合度不高，但描述了相同的事件（魅族16s发布）。这两类数据混在一起，导致模型容易误将低重合度的非事件pair误匹配。为了解决该问题，我们尝试针对事件性pair和非事件性pair，分别训练匹配模型。我们调用事件识别服务（该服务详情参考[内部或本地链接已移除]）将训练数据拆分为事件类数据和非事件类数据。拆分标准及处理流程如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/820ff4b9cb3cdefd0bb4.png"/></p>
<p>        训练阶段，分别基于事件性pair和非事件性pair训练匹配模型，得到model1（事件性pair匹配模型）和model2（非事件性pair匹配模型）；预测阶段，每个待测试pair，首先调用事件识别服务，判断应该走哪个匹配模型。下表展示了实验结果：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/570207bf5989692b5af6.png"/></p>
<p>由表可见：</p>
<p>a). 拆分训练模型后，event类数据效果降低，主要是准确率下降，主要原因是：no-event相似pair对重合度要求更为严格，训练集去除这些数据，导致准确率大幅下降。</p>
<p>b). no-event数据准召都有提升, 证明event类数据对no-event的负面影响很大，符合我们之前的观察。</p>
<p>为了进一步提升总体效果，我们让请求的非事件pair过no_event模型，事件pair则过所有数据训练的模型，最终结果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/6afcdc999fff756a921b.png"/></p>
<p>由表可见，经过对请求策略的调整，总体结果进一步取得了1.8个点提升。</p>
<p>对badcase分析发现，采用新策略后，低重合度误召回的样本数量显著降低。下面展示了具体数据：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/cd396fb93db678f74867.png"/></p>
<p>该结果进一步证明了我们前面假设的正确性：事件性pair会导致低重合度的非事件pair误召回，需要分别进行建模。</p>
<p><strong>3.7 扩充数据多样性</strong></p>
<p>为了进一步扩充训练数据的多样性，我们融合开源数据集LCQMC和BQ数据集到训练数据中。融合后的数据集统计信息如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/42edf94c7dbd12c896b6.png"/></p>
<p>下表展示了不同数据集训练模型的效果：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/7e7899c26ce94387ebe8.png"/></p>
<p>        值得注意的是，融合数据之后，模型准确率取得大幅提升。主要原因是，原始训练集，有30w数据是自动构造的，包含噪声，新增的两个数据集都是人工标注数据集，质量更高，因此提升了模型的效果。我们尝试过去除自动构造的数据，结果发现模型召回大幅降低（因为只有自动构造的数据和测试数据是同源的）。</p>
<p><strong>Domain Weighting</strong></p>
<p>        不同领域的数据直接合并的方式比较粗糙，不同领域的数据对目标领域的相关程度不同。因此，训练时尝试为不同领域的数据设置不同的权重，具体实施方式为：计算loss时，不同领域的样本损失值乘以改领域权重之后作为最终的损失，公式如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/0040936d0dba73b628ae.png"/></p>
<p>实现时，同一领域的所有样本赋值相同的权重。不同权重的实验效果如下</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/cc9ed0ef544f6894ede4.png"/></p>
<p>当TitleMatch：LCQMC：BQ =1:0.5:1时效果最好，F值进一步提高0.8个点。</p> 
{% endraw %}
