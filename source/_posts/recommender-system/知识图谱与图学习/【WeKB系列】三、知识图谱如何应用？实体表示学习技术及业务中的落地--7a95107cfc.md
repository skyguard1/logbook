---
title: "【WeKB系列】三、知识图谱如何应用？实体表示学习技术及业务中的落地"
date: 2022-03-16 14:20:15
categories:
  - 推荐系统
  - 知识图谱与图学习
---

{% raw %}

<h1>▌一、实体表示学习技术简介</h1>
<p><strong>实体表示学习（Entity Representation Learning</strong><strong>）</strong>，或称实体的向量表示学习，即为对知识图谱（Knowledge Graph, KG）中的实体（Entity），学习其向量表示（Entity Embedding）的技术方法。</p>
<p>为什么要学习实体的向量表示呢？本质上，知识图谱是一种建模实体与实体之间关系的<strong>离散</strong>表示形式（图结构）。然而，基于离散表示的KG在应用过程中存在局限性，尤其在需要利用实体相关性的搜索、推荐等场景中，<strong>连续</strong>的向量表示往往更易于应用。例如，在<strong>搜索</strong>场景中：对于用户的搜索query，我们发现其中的实体后，可以对文档集中的内容做相同或相关Entity的匹配；在<strong>推荐</strong>场景中：对于用户感兴趣的实体，我们可以在推荐池中匹配具有相同或相关Entity的内容来推荐给用户。在上述两个场景下，相同实体的匹配往往限制性太强，相关实体的度量又很难去定义。如果依赖KG里的特定关系或关系路径（Metapath），一定程度上可以描述实体的相关性，但往往很难枚举这些关系或路径，需要case by case地开发，成本较高，且对KG的完整性有很高的要求。</p>
<p>怎么解决实体相关性检索的难点呢？如果我们可以把KG的每一个实体表示为一个实体向量（Entity Embedding），在向量空间中通过近邻检索，找到向量距离近的其他实体，就可以发现相关的实体了。这一方法要求实体向量的语义空间对于具体业务的“相关性”具有好的刻画能力，即：向量距离近的实体倾向于相关，向量距离远的实体倾向于不相关。</p>
<p>除了实体相关性问题，实体表示对链路预测（Link Prediction）、知识库补全、实体对齐（Entity Alignment）、语言模型、实体分类（Entity Typing）、智能问答、文本理解等应用场景都有着关键的作用。以上应用对Entity Embedding如何获取，有着很高的要求。</p>
<p>下面，我们将介绍几种主要的实体表示学习方法，来获取高质量的Entity Embedding：</p>
<p>1）基于<strong>图结构</strong>的实体表示学习，及其局限性；</p>
<p>2）基于<strong>语境文本</strong>的实体表示学习，以及我们取得的相关学术成果；</p>
<p>3）基于<strong>多模态数据</strong>的实体表示学习，以及在这一方向的创新性探索。</p>
<p><br/></p>
<h1>▌二、背景：基于图结构的实体表示学习</h1>
<p>2013年-2017年左右，以TransE为开端，产生了很多基于图结构的实体表示学习方法。其核心思想是基于知识图谱中的<strong>结构相似性</strong>，学习KG实体的向量表示。</p>
<p>TransE的基本思想是对于三元组(h, r, t)，学习每个实体和关系的向量，使头实体h与关系向量r的和尽可能靠近尾实体t：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/7249a66b7ea3c13faa61.png"/></p>
<p>我们举两个例子：<br/> (h=巴拉克奥巴马, r=妻子, t=米歇尔奥巴马)<br/> (h=邓超, r=妻子, t=孙俪)</p>
<p>TransE习得的关系向量表示为实体向量空间中的平移，如头实体经过“妻子”关系平移后的向量即得到尾实体。多跳关系即为在空间中多次平移，如：<br/> h + r_妻子 + r_丈夫 = h<br/> h + r_妻子 + r_父亲 = h的岳父</p>
<p> </p>
<p>这一方法的一个主要问题是，不适于一对多或多对多关系、以及对称关系的学习，而我们的KG往往有很多这样的关系，影响学习效果。因此产生了TransH方法，用超平面内的转换思想处理KG上的多对多关系。后续也产生了其他的方法：TransR、TransD等，解决不同方面的局限性。 </p>
<p>然而，基于图结构的实体表示学习方法（Trans系列方法），仍有几个主要的不足：</p>
<p>1）对知识图谱的<strong>完整性</strong>有很强的依赖。</p>
<p>2）不能对<strong>新增的实体</strong>、变化的KG进行有效的推理。</p>
<p>3）不能有效应对<strong>巨大的知识图谱</strong>，如亿级别实体的知识图谱需要的模型计算量巨大。</p>
<p>4）除了知识图谱本身的结构，未能有效<strong>融合其他信息</strong>，如实体在语料中的关联文本。</p>
<p>为了解决这些问题，从而获得更易用的实体表示，笔者近年来参与研究了基于语境文本的实体表示学习方法，下面将展开介绍。</p>
<p> </p>
<h1>▌三、基于语境文本的实体表示学习</h1>
<p>针对上述局限性，我们希望实体表示学习方法可以减轻对知识图谱完整性的依赖，并有效融合实体所在语料的文本信息。</p>
<p>传统的基于文本的表示学习方法，如Word2Vec和GloVE，基于语料中词之间的共现关系学习词向量，然而其学习的单元为词汇 (word) 而非实体 (entity)，无法解决消歧义问题，这里不加赘述。</p>
<p>2018年出现的BERT，在NLP领域的一系列任务上刷新了最好成绩。BERT的成功得益于几个方面：</p>
<p>（1）巧妙地设计Masked Language Model (MLM)、Next Sentence Prediction (NSP) 两个自监督任务； </p>
<p>（2）得以运用大规模无标注语料，构造海量训练数据；</p>
<p>（3）基于语境的词向量Contextualized word representation思想的进一步深化；</p>
<p>（4）提出了广泛适用的pretrain-finetune范式。</p>
<p>那么我们能否将BERT的思想迁移到实体向量表示学习的过程中呢？这里要提到我们在2019年的一篇工作 [<a href="https://arxiv.org/abs/2001.03765">1</a>]：RELIC。</p>
<p>我们类比BERT的两个预训练任务：第一个是MLM（遮蔽语言模型），即随机掩盖15%文本让模型预测； 第二个是NSP（上下句预测），即随机打乱50%的句子让模型预测两个句子是否上下句关系。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/b530273de4baf7d662be.png"/></p>
<p>图1：BERT的预训练任务</p>
<p> </p>
<p>在实体表示学习的任务中，如何使用维基百科语料来“预训练”实体表示呢？ 我们可以修改BERT的预训练任务为Entity Linking (EL) 任务，即直接根据上下句语境，预测出当前位置的实体ID。与MLM类似，我们可以设置一个遮蔽率 K%，在K%的概率下遮蔽实体对应的文本（mention），1-K%的概率下不遮蔽实体对应的文本。 文本及其对应的实体ID数据可以通过预处理维基百科内链数据来得到。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/3593cd9ff1658da937d4.png"/></p>
<p>图2：改造BERT的预训练任务用于实体表示学习</p>
<p> </p>
<p>在这个设计中，我们使用两个特殊的token来环绕带有内链的实体词，如上图中“[E1] valentina [/E1]”，并有概率把文中的实体词valentina替换为一个[MASK] token，来增加模型预测的难度。让一个BERT模型去阅读该段上下文 “[E1] valentina [/E1] 是第一个登上太空的女性” 或 “[E1] [MASK] [/E1]是第一个登上太空的女性”，直接预测对应实体的ID。可以想到，模型为了完成这一任务，<strong>需要学好每个实体的</strong><strong>ID</strong><strong>向量表示。</strong></p>
<p>在训练方法上，我们使用一个双塔模型，命名为<strong>RELIC</strong>，意为“语境中学习的实体表示”。训练采用batch softmax loss，即基于批内其他样本作为负样本的对比学习方法。训练的产出是一个基于BERT的mention encoder （语境编码器） 和entity embeddings（每个实体的向量）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/b5b2e6a7ac15c02ad9c8.png"/></p>
<p>图3：RELIC实体表示的训练方法</p>
<p> </p>
<p>那么这样学习到的RELIC实体表示，效果如何呢？为了说明其效果，我们验证了3个下游任务：实体链接、实体分类、智能问答。</p>
<p>在<strong>实体链接</strong>任务上，RELIC基本追平了实体链接任务上当时的SOTA：（在CONLL数据集上追平，在 KBP2010上差1个点）</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/97d61e6f7456310726ad.png"/></p>
<p>图4：RELIC在实体链接上的效果</p>
<p> </p>
<p>在<strong>实体分类</strong>任务上，我们采用预训练的RELIC entity embedding，添加一个额外的分类层，在实体分类数据集FIGMENT上finetune。RELIC比传统方法的F1 score从82.3提升到87.9，而且我们看到只用5%的FIGMENT训练数据来finetune，效果已经比传统方法更优。在TypeNet数据集上也有类似效果（5%的训练数据已经远超之前的SOTA）。可见RELIC预训练实体表示<strong>经过少量样本</strong><strong>finetune</strong><strong>就可以较好地适配下游任务</strong>：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/31f9b4f062482e61f0bf.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/973673c31afc40a03ac6.png"/></p>
<p>图5：RELIC在实体分类上的效果</p>
<p> </p>
<p>RELIC还可以用作<strong>智能问答</strong>：我们使用训练的mention encoder直接编码query，在实体向量空间中检索最近的实体作为答案。这一方法达到了SOTA的QA方法的80%效果（45.0 vs 35.7），且是第一个“闭卷QA”（Closed-book QA）的方法，即不参考额外语料即可回答问题： </p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/e1f4b34979abf5654211.png"/></p>
<p>图6：RELIC在智能问答上的效果</p>
<p> </p>
<p>我们发现通过设置不同的遮蔽率（mask rate）K%，习得的实体表示可以达到不同的效果。当遮蔽率较低时，模型可以更好地看到实体词本身作为参考，因此实体链接效果更好；当遮蔽率较高时，模型学会更多地依赖上下文语境来进行分类判断，因此实体分类效果更好。实际应用场景中，可以根据下游任务来选择合适的遮蔽率：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/7cb7c8707a8cb9ebb852.png"/></p>
<p>图7：RELIC的mask rate对下游任务的影响</p>
<p> </p>
<p>RELIC有如下的优势：（1）模型架构简洁，便于训练。（2）可以利用大规模预训练语言模型BERT，较好地适配训练语料，习得语境中每个entity独特的向量表示。 （3）在一系列下游任务，包括实体链接、分类、问答等系统中，都获得了比较突出的效果。</p>
<p>当然，RELIC也有一些不足，主要包括：（1）比较依赖实体所在语境的准确映射，即带内链文本或实体链接系统；（2）对于纯新实体（zero-shot）以及在训练语料中较少出现的实体（few-shot）难以习得足够好的表示。（3）对于超大规模的KB需要学习每个实体的独立embedding，对硬件要求较高、学习效率较低。</p>
<p>为改进这些不足，我们后续也研究了基于实体特征的实体表示方法，可以参考笔者的另一篇工作 [2] Entity Linking in 100 Languages，该方法使用了实体文本特征进行泛化，习得一个可对任意实体生效的语义编码器，从而不再限制实体在语料当中的出现频率，对于大规模KG、新实体冷启动场景、多语言KG的场景表现更佳，在多语言实体链接中取得了最好的效果。此处不再赘述。</p>
<p> </p>
<h1>▌四、多模态实体表示学习技术探索</h1>
<p>以上的方法主要依赖知识图谱的现有结构以及实体的文本语境，来学习实体的表示。然而在的实际应用场景中，这些方法仍有其局限性：的推荐、搜索等场景蕴含了视频、音频、文本等<strong>多模态</strong>数据，在这些多模态场景中，仅用图谱结构或文本信息习得的实体表示，往往不能涵盖实体所包含的准确语义和兴趣点。我们是否能够融合多模态的数据，来进一步丰富实体的向量表示？</p>
<p>我们团队基于多模态数据场景，创新性地设计了一种基于多模态语境编码器到实体表示的学习机制。与之前的RELIC思路类似，我们通过融合多模态数据（包括视频、音频、描述文本、hashtag等），结合WeKB实体链接系统，获取视频号到WeKB实体的对齐语料，使用该语料训练每个实体的多模态表示，从而将实体与视频的多模态信息映射到同一个语义空间：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/98d71f10e999aeda4a96.png"/></p>
<p>图8：多模态实体表示学习架构</p>
<p> </p>
<p>Multimodal Encoder的具体结构如下，由数据中心自研的MMCore框架支持：[内部或本地链接已移除]</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/ca2a12d4e031d898a99e.png"/></p>
<p>图9：MMCore多模态视频Encoder结构</p>
<p> </p>
<p>通过这一方法，我们获得了知识图谱WeKB中每个实体的<strong>多模态实体向量（</strong><strong>MEE， Multimodal Entity Embedding）</strong>。该方法的效果也比较突出，在内部相关实体检索、关键词扩展乃至视频推荐等任务上都有直接的应用场景，我们将在下一个部分中详细阐述。</p>
<h1>▌五、实体表示的应用</h1>
<p>如前所述，在我们获得了良好的实体向量表示后，可以支持一系列下游应用。下面简述几个中具体的落地场景。</p>
<h2>▌5.1 用于相关实体检索</h2>
<p>在的推荐与投放等场景中，我们往往要基于特定的关键词，扩散出一系列相关的概念，来支持下游业务。如：如何把一个关于“布偶猫”的视频推荐给可能喜欢这个视频的用户？除了推荐系统的域内数据本身，我们可以基于知识图谱扩散出一系列兴趣相关的实体，来推荐给有这些相关兴趣的用户。在这个场景中，<strong>相关实体的检索</strong>便成为了一个核心的部分。</p>
<p>我们基于前述的多模态实体向量（MEE），结合近年来基于 Faiss,  ScaNN等向量近似检索（Approximate Nearest Neighbor Search , ANN）系统方法（我们采用了自研向量检索引擎SimSvr），可以实现向量空间内次线性复杂度的高效检索。以实体之间的余弦相似度为度量： </p>
<p>Sim(e1, e2) = Cosine(Emb_e1, Emb_e2)</p>
<p>实体检索方法：给定实体e1，返回向量空间内最近的实体e2的列表，下游可以通过打分模型、人工审核等方法使用。如图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/bf4caef8359e7627a275.png"/></p>
<p>图10：实体相似度扩散方法</p>
<p>与实体向量检索互为补充的是基于KG图结构的Metapath挖掘方法：通过挖掘给定的图谱路径，获取准确、不依赖于语料的相关实体，如：通过“钓鱼”扩散出所有渔具，通过“健身”扩散出健身方法，通过“猫”扩散出所有猫的品种。如图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/89da24ed97f4ad1a2992.png"/></p>
<p>图11：Metapath扩散方法 </p>
<p>这两种方法互为补充，值得一提的是多模态实体向量（MEE）在检索中的效果是比较令人惊喜的：可以捕获内容风格相似、字面有很大差异的一些实体，如“新裤子乐队”可以扩散出相似风格的乐队，“邓紫棋“可以扩散相似风格的歌手等。在实际项目的评估中，基于Metapath的扩展方法具有很高的准确率（96%），而基于多模态实体向量相似度的扩展具有较好的准确率（85%）、更高的覆盖率和下游应用中的贡献占比（61%）：</p>
<p><img alt="" loading="lazy" src="/logbook/images/recommender-system/f64d0cf24502ad568595.png"/></p>
<p>图12：相关实体扩散的业务效果</p>
<p> </p>
<p>这一技术被我们应用于：视频号红点投放、用户兴趣画像的扩展推理、推荐系统的特征等场景，并在视频号的运营投放平台中，支持了运营人员的交互选词、灵活投放。</p>
<p>相关实体检索也可以被用于搜索场景中相似文档的检索、语义匹配中内容之间匹配度的计算等。本质上，实体向量可以支撑我们计算任意实体之间的语义相似度，从而支持基于实体理解的广泛应用。</p>
<h2>▌5.2 用作推荐系统特征</h2>
<p>基于行为的推荐系统往往在行为足够时有很好的表现，而面对用户与内容的<strong>冷启动</strong>场景时，则有较大的提升空间。获取实体向量表示后，我们通过基于WeKB的实体链接系统，获取内容当中的实体标注。通过得到实体对应的Entity Embedding，可以添加到推荐系统中作为用户侧或物品侧特征（直接添加或聚类使用等）。也可以通过实体相似度打分，构造User-Item相关性特征或Item-Item相关性特征等，从而把一些场景下的硬匹配特征转化为一个平滑的相似度计算过程。基于实体向量的推荐特征也在数个推荐场景下得到了落地。</p>
<h2>▌5.3 其他应用</h2>
<p>除了推荐系统的应用，实体表示对链路预测（Link Prediction）、知识库补全、实体对齐（Entity Alignment）、实体链接、语言模型、实体分类（Entity Typing）、智能问答、文本理解等应用场景都有着关键的作用。</p>
<p><strong>链路预测/知识库补全</strong>，是在已有的图谱中补全缺失的关系。在链路预测中，传统的Trans*系列方法可以直接通过实体向量的偏置来推理实体之间可能存在的关系。</p>
<p><strong>实体对齐</strong>，是发现不同的知识库中可能重复的实体。在实体对齐场景中，两个实体是否一致的判断可以通过实体相似度来完成，或者通过实体检索来生成实体对齐的候选项。</p>
<p><strong>实体链接</strong>，是判断文本当中出现了哪些KG中的实体，并对应到一个无歧义ID的过程，如：判断“苹果安卓哪个好用”、 “苹果CEO库克”、“苹果多少钱一斤”中的“苹果”分别对应KG里的哪些实体。这是打通文本世界与语义世界的关键步骤。除了本文中我们的相关工作 [1] [2]，也请期待我们的后续文章对于实体链接方法的详细介绍。</p>
<p><strong>语言模型</strong>：近年来也有通过KG的实体表示增强语言模型的研究，代表性的有[6][7]等。虽然现在的NLP模型本质仍然离不开基于语料的统计，但相信KG会逐渐将结构化知识与推理能力带给我们的语言模型，拓宽通用AI的可能性。</p>
<p><strong>实体分类、智能问答、文本理解：</strong>正如前面介绍的RELIC模型，好的实体向量表示可以帮助我们对新发现的实体进行有效的细分类、直接找到问题的实体答案等。与实体链接相结合后，也可以辅助文本的理解、分类、检索、生成等。</p>
<p><br/></p>
<h1>▌六、其他相关工作</h1>
<p><br/></p>
<p>这里我们也简要列举一些文中未覆盖到的、近年来有代表性的实体表示学习工作。至于实体链接、信息抽取等方向相关研究广泛，就不再一一枚举：</p>
<ul><li>LUKE [8]：基于上下文语境的实体表示，与BERT/ElMo类似，考虑实体的表示不是独立的embedding，而是基于不同上下文语境变化的contextualized representation。</li>
<li>Global Entity Disambiguation with Pretrained Contextualized Embeddings of Words and Entities [9]: 对LUKE进行改进，将entity embedding与mention上下文语境进行结合来改进实体链接效果，取得了CoNLL、ACE2004等实体链接测试集上的最佳效果。</li>
<li>Entities As Experts [7]: 将实体链接任务作为语言模型训练的中间层联合训练，通过融合实体表示到语言模型中，来提升语言模型在一系列下游任务上的效果。</li>
<li>Matching the Blanks [10]: 本文考虑关系表示而非实体表示的学习问题。通过改进BERT任务对维基百科进行监督，对KG的关系进行表示学习，并达到了关系分类、少样本关系分类等任务上的最佳效果。</li>
</ul><h1>▌七、未来展望</h1>
<p><br/></p>
<p>在未来，数据中心依托于知识图谱WeKB与海量多模态数据，将会进一步研究实体和关系的表示学习方法及其应用。几个我们感兴趣的研究方向：</p>
<ul><li>1）如何<strong>融合</strong>图结构、语境文本、多模态数据，进行综合的实体表示学习？</li>
<li>2）如何进行有效的<strong>领域迁移</strong>，将实体表示学习模型迁移到新的KG、新的下游应用上？</li>
<li>3）如何进行<strong>零样本、少样本</strong>实体表示学习，尤其是对新实体的有效表示方法？</li>
<li>4）如何<strong>组件化、服务化</strong>地提供实体表示学习能力，支持公司内其他应用场景？</li>
</ul><p>我们也将探索开放实体表示学习服务的可能性，将我们的方法迁移到公司内的通用、垂类知识图谱中，提供简单易用的实体表示来创造更多的业务价值。</p>
<p> </p>
<h1>▌部分参考文献</h1>
<p><br/></p>
<p>[1] <a href="https://arxiv.org/abs/2001.03765">https://arxiv.org/abs/2001.03765</a> Learning Cross-Context Entity Representations from Text (RELIC). Ling, J., FitzGerald, N., <strong>Shan, Z.</strong>, Soares, L.B., Févry, T., Weiss, D. and Kwiatkowski, T., 2020.</p>
<p>[2] <a href="https://arxiv.org/abs/2011.02690">https://arxiv.org/abs/2011.02690</a> Entity Linking in 100 Languages. Botha, J.A., <strong>Shan, Z.</strong> and Gillick, D., 2020.</p>
<p>[3] <a href="https://zhuanlan.zhihu.com/p/147542008">https://zhuanlan.zhihu.com/p/147542008</a></p>
<p>[4] <a href="https://github.com/thunlp/TensorFlow-TransX">https://github.com/thunlp/TensorFlow-TransX</a></p>
<p>[5] [内部或本地链接已移除] 数据中心多模态训练框架MMCore</p>
<p>[6] <a href="https://arxiv.org/abs/1909.07606">https://arxiv.org/abs/1909.07606</a> K-BERT: Enabling Language Representation with Knowledge Graph. Liu, W., Zhou, P., Zhao, Z., Wang, Z., Ju, Q., Deng, H. and Wang, P., 2020.</p>
<p>[7] <a href="https://arxiv.org/abs/2004.07202">https://arxiv.org/abs/2004.07202</a> Entities as Experts: Sparse Memory Access with Entity Supervision. Févry, T., Soares, L.B., FitzGerald, N., Choi, E. and Kwiatkowski, T., 2020.</p>
<p>[8] <a href="https://arxiv.org/abs/2010.01057">https://arxiv.org/abs/2010.01057</a> LUKE: Deep Contextualized Entity Representations with Entity-aware Self-attention. Yamada, I., Asai, A., Shindo, H., Takeda, H. and Matsumoto, Y., 2020.</p>
<p>[9] <a href="https://arxiv.org/abs/1909.00426">https://arxiv.org/abs/1909.00426</a> Global Entity Disambiguation with Pretrained Contextualized Embeddings of Words and Entities. Yamada, I., Washio, K., Shindo, H. and Matsumoto, Y., 2021.</p>
<p>[10] <a href="https://arxiv.org/abs/1906.03158">https://arxiv.org/abs/1906.03158</a> Matching the Blanks: Distributional Similarity for Relation Learning. Soares, L.B., FitzGerald, N., Ling, J. and Kwiatkowski, T., 2019.</p> 
{% endraw %}
