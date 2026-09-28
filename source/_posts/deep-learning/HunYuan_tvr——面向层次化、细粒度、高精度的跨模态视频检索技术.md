---
title: "HunYuan_tvr——面向层次化、细粒度、高精度的跨模态视频检索技术"
date: 2022-05-08 08:19:39
categories:
  - deep-learning
---

{% raw %}

<div>
<div>
<ol><li>
<h2>引言</h2>
</li>
</ol><p>近年来，随着大规模视觉-语言预训练（Vision-Language Pretraining，VLP）模型的出现，CV和NLP等多模态信息进一步有效融合，使得多模态内容理解的性能步入新台阶。大量研究工作表明，大规模预训练模型对于加速下游任务的学习及部署具有重要意义。其中，跨模态检索技术作为重要的下游任务之一，在多模态视频理解中发挥着重要作用，受到广泛的关注。依托于“混元”AI大模型的建设，广告多媒体AI中心算法团队，基于构建层次化、细粒度、高精度的跨模态视频检索技术的目标，提出了HunYuan_tvr模型（链接：<a href="https://arxiv.org/pdf/2204.03382.pdf">https://arxiv.org/pdf/2204.03382.pdf</a>），在MSR-VTT，MSVD，LSMDA，DiDeMO和ActivityNet 5大跨模态视频检索数据集上取得SOTA性能，并超过阿里、、等团队的模型性能，实现了该领域的大满贯。目前，该技术已经服务于广告，应用到包括广告智能创作、广告检索、广告推荐等诸多业务场景中，更好地提升了广告主与用户的体验。</p>
<ol><li>
<h2>背景介绍</h2>
</li>
</ol><p>近年来视频广告爆发式增长，并且在各流量产品中得到了广泛的应用。视频相比图文广告效果好的重要原因是多视角拍摄，情景真实感，语音BGM等元素可以蕴含更真实可信的信息，具有更强的说服力，从而快速崛起成为了广告投放最重要的创意形式[1]。</p>
<p>随着视频内容消费的日益增长，视频内容的理解、推荐和搜索能力对于广告内容的投放、审核、推荐等环节至关重要。在海量广告数据中，自然语言文本-视频跨模态检索技术作为最符合人类认知的交互方式之一，也是提高计算机对视频内容理解的重要手段之一。然而不同于单模态（图片、视频、文本）检索任务，不同模态的数据分布存在天然的异质鸿沟问题（heterogeneity gap）[2]，因此跨模态检索任务需要模型不仅能捕捉模态内部的细粒度语义信息，还需要捕捉跨模态数据之间的内容关联性。</p>
<p>最近，大量基于视觉-语言预训练模型的方法占据了文本-视频检索的排行榜。总的来说，这些方法可以大致分为两类：基于Video-Sentence交互和基于Frame-Word交互的方法，如图1所示。</p>
<h3>(1) 基于Video-Sentence交互的方法</h3>
<p>对于基于Video-Sentence交互的方法[2-15]，其检索过程非常简洁和高效。通常首先采用单独的文本和视频特征提取器提取各自的Embedding；然后将文本和视频Embedding学习映射到一个共同的嵌入空间中，使得正pair对之间尽可能的近，负pair对尽可能的远；最后根据它们Embedding间的余弦相似度直接进行检索任务。</p>
<p>常见的方法例如FROZEN[6]，将图像视为单帧视频，并设计课程学习方式，在文本-图像+视频的数据集上预训练模型，在保证模型性能的同时极大地缩短训练时间，后续的一些方法[13-15]在FROZEN基础上引入Region信息，更好地学习视觉与文本的细粒度对应关系。与 FROZEN 预训练一个新的文本-视频检索模型不同，之前的SOTA方法CLIP4Clip[3]从图像文本预训练模型CLIP[16]中知识迁移，来解决视频文本检索任务。同样基于预训练的 CLIP 模型，CAMoE [2]提出了一种具有单门专家混合(CAMoE) 和新颖的Dual Softmax损失 (DSL) 的多流语料库对齐网络，以进一步提高检索性能。</p>
<h3>(2) 基于Frame-Word交互的方法</h3>
<p>基于Video-Sentence交互的方法，为每个模态提取单一维度的全局向量，往往缺乏足够的信息来进行跨模态信息交互，因此，基于Frame-Word交互的方法可以更好地实现该目标。首先利用特征提取器，将每个Word/Frame转换为一系列Token/Frame嵌入，然后使用交互模块来捕获Token和Frame Embedding之间的细粒度线索。当前的SOTA方法DRL[17]基于此思想，提出了加权Token-wise Interaction(WTI) 来探索Token和Frame Embedding之间的细粒度线索，以及Channel DeCorrelation Regularization (CDCR) 来最小化所比较向量之间的冗余，以便学习层级化表征。</p>
<p>然而，几乎所有现有的方法都只考虑来自Video-Sentence或Frame-Word的单个形式的跨模态交互，很少有工作探索视频和文本数据中内在的层次语义结构。 因此，在本文中，我们提出了一种名为 HunYuan_tvr的新方法，该方法探索包含Video-Sentence、Clip-Phrase和Frame-Word多层级交互，以全面理解文本-视频细粒度内容。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/896c95ad4bdaab93dfa8.png"/></p>
<p>图1：跨模态视频检索目前常见模型方案示意图</p>
<ol><li>
<h2>Hunyuan_tvr模型介绍</h2>
</li>
</ol><h3>3.1 算法框架</h3>
<p>HunYuan_tvr模型的推理框架如图2所示。输入一段文本，模型需要从对应视频库中返回和对应文本最符合的视频内容。为此，模型不仅需要理解视频和文本中的语义信息，同时还要将两种模态的特征在同一潜空间进行匹配对齐。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/6e55a401a3e3ac3e57ca.png"/></p>
<p>图2：HunYuan_tvr推理框架示意图</p>
<p>针对上述问题，HunYuan_tvr模型的训练框架图如图3所示。给定一段视频  <img alt="" loading="lazy" src="/logbook/images/deep-learning/0ad99db9169bc735f2f6.svg"/>和对应的文本描述  <img alt="" loading="lazy" src="/logbook/images/deep-learning/cd14dfb7c723a4038898.svg"/>，我们希望视觉编码器  <img alt="" loading="lazy" src="/logbook/images/deep-learning/f11514babed92c5c5921.svg"/>和文本编码器  <img alt="" loading="lazy" src="/logbook/images/deep-learning/3b9bbef5377b49b76c0d.svg"/>捕捉到视频和文本数据中的语义知识。其主要包含三个技术点：(1) 层级化跨模态交互技术；(2) 自适应标签去噪技术；(3) 边缘样本增强技术。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/ad900150fba106427bd0.png"/></p>
<p>图3：HunYuan_tvr技术框架图</p>
<ol><li>
<p>层级化跨模态交互： </p>
</li>
</ol><p>视频  <img alt="" loading="lazy" src="/logbook/images/deep-learning/0ad99db9169bc735f2f6.svg"/>和文本  <img alt="" loading="lazy" src="/logbook/images/deep-learning/cd14dfb7c723a4038898.svg"/>都包含层级化的结构信息。如图4所示，视频由不同的片段组成，而片段由不同的帧组成。同样的，文本由短语以及单词组成。在人的感知系统中，我们不仅会提取视频中的关键帧和文本里的关键词进行分析匹配，同时还会整体分析视频内容和文本描述的内容是否一致。为此，我们提出了层级化跨模态交互技术，通过自注意力机制将单帧特征聚合成帧-片段-视频的层级化视觉特征，同时针对文本模态得到单词-短语-句子的层级化文本特征。最后通过层级化的对比学习，综合分析两种模态数据的相似程度。</p>
<p>具体来说，  <img alt="" loading="lazy" src="/logbook/images/deep-learning/f11514babed92c5c5921.svg"/>和  <img alt="" loading="lazy" src="/logbook/images/deep-learning/3b9bbef5377b49b76c0d.svg"/>首先利用CLIP预训练模型的视觉和文本编码器分别提取每一帧图像的视觉特征  <img alt="" loading="lazy" src="/logbook/images/deep-learning/d8d1c5a3b91b2bbb314a.svg"/>和每个单词对应的特征   <img alt="" loading="lazy" src="/logbook/images/deep-learning/156a5da2ab363870d03c.svg"/>，其中  <img alt="" loading="lazy" src="/logbook/images/deep-learning/20769473d38eb0d3111d.svg"/>和  <img alt="" loading="lazy" src="/logbook/images/deep-learning/c8a99a0965e83d6e1ffb.svg"/>分别表示帧数目和单词数目。随后，通过aggregation layer（聚合层）将不同的帧或单词特征进行自适应聚合。如图4所示，aggregation layer通过自注意力机制将具有相近语义信息的input tokens进行聚合，并利用Feed-Forward层将特征在高维空间进行非线性变化，最终将  <img alt="" loading="lazy" src="/logbook/images/deep-learning/7437ca17e7462510083e.svg"/>帧的视觉特征重组成  <img alt="" loading="lazy" src="/logbook/images/deep-learning/0100814c31205c11a649.svg"/>个片段特征  <img alt="" loading="lazy" src="/logbook/images/deep-learning/37fb2b5d350b78fa7baf.svg"/>，其中  <img alt="" loading="lazy" src="/logbook/images/deep-learning/0e332afc1caab5037fd9.svg"/>。用相似的方式，我们可以将  <img alt="" loading="lazy" src="/logbook/images/deep-learning/c1c5b24b5b1bd69fd1ff.svg"/>聚合成一个全局的视频特征  <img alt="" loading="lazy" src="/logbook/images/deep-learning/7df0595a9be309f9a2e8.svg"/>，以及  <img alt="" loading="lazy" src="/logbook/images/deep-learning/0547277dad30d12e8979.svg"/>自适应地聚合成短语特征  <img alt="" loading="lazy" src="/logbook/images/deep-learning/f18d7bfb553de5c184f3.svg"/>和句子特征  <img alt="" loading="lazy" src="/logbook/images/deep-learning/d2d89cb7f9c938dbe2a7.svg"/>。最终，有了层级化的视觉特征  <img alt="" loading="lazy" src="/logbook/images/deep-learning/874d1e43ec320e4a39b6.svg"/>和层级化的文本特征  <img alt="" loading="lazy" src="/logbook/images/deep-learning/0d6d3ee4e9b863872c36.svg"/>后，我们分别对  <img alt="" loading="lazy" src="/logbook/images/deep-learning/5e714a8319b39674f07e.svg"/>，  <img alt="" loading="lazy" src="/logbook/images/deep-learning/4bf068d5f43ed6ba0c44.svg"/>，以及  <img alt="" loading="lazy" src="/logbook/images/deep-learning/e9150b8745752310de8d.svg"/>进行对比学习，实现层级化的跨模态交互方式。</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/f6f2a47701748b630fd8.png"/></p>
<p>图4：层级化跨模态交互技术</p>
<ol><li>
<p>自适应标签去噪：</p>
</li>
</ol><p>跨模态对比学习通常假设具有不同ID的样本为负样本。比如对于某一视频来说，其对应的文本描述被视为正样本对，而所有其他视频的描述被视为负样本。而在真实的样本分布中，视频-文本之间应该存在某种复杂的多对多关系。当我们将相似视频的文本描述视为负样本对将会产生噪声梯度，从而影响网络的正常收敛。因此我们提出自适应标签去噪技术来挖掘样本中潜在的正样本对，避免训练过程中的噪声梯度带来的负面影响。对于某一个视频，我们将其均匀划分成N个片段，然后在每个片段随机采样一帧，最后N帧组在一起表示该视频。我们将上述操作重复两次，得到了该视频了两个视角  <img alt="" loading="lazy" src="/logbook/images/deep-learning/64a47b32fc21e2f679fc.svg"/>和  <img alt="" loading="lazy" src="/logbook/images/deep-learning/fed5ed7cb72faa33eb7a.svg"/>。显然，  <img alt="" loading="lazy" src="/logbook/images/deep-learning/64a47b32fc21e2f679fc.svg"/>和  <img alt="" loading="lazy" src="/logbook/images/deep-learning/fed5ed7cb72faa33eb7a.svg"/>来自于同一视频，属于正样本对，那么当不同的两个视频  <img alt="" loading="lazy" src="/logbook/images/deep-learning/64a47b32fc21e2f679fc.svg"/>和  <img alt="" loading="lazy" src="/logbook/images/deep-learning/107026a43af0b9332f4e.svg"/>的相似度大于  <img alt="" loading="lazy" src="/logbook/images/deep-learning/64a47b32fc21e2f679fc.svg"/>和  <img alt="" loading="lazy" src="/logbook/images/deep-learning/fed5ed7cb72faa33eb7a.svg"/>时，我们即认为  <img alt="" loading="lazy" src="/logbook/images/deep-learning/64a47b32fc21e2f679fc.svg"/>和  <img alt="" loading="lazy" src="/logbook/images/deep-learning/107026a43af0b9332f4e.svg"/>属于正样本对：</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/b68edebf3931093cb68a.svg"/></p>
<p>        最终，我们在层级化跨模态对比学习中会同时考虑真实正样本对和潜在正样本对。</p>
<ol><li>
<p>边缘样本增强：</p>
</li>
</ol><p>训练数据集中最具有信息量的数据往往是一些边缘样本（难样本）。这些边缘样本具有容易混淆的纹理或内容，难以被模型准确的识别。因此，我们提出了边缘样本增强技术，进一步提高模型的检索精度。对于一个视频  <img alt="" loading="lazy" src="/logbook/images/deep-learning/c1c5b24b5b1bd69fd1ff.svg"/>，我们选取在当前数据批次中最容易被误匹配上的负样本文本  <img alt="" loading="lazy" src="/logbook/images/deep-learning/a57f60237ed0516d7e0d.svg"/>作为边缘样本，并得到三元数据组  <img alt="" loading="lazy" src="/logbook/images/deep-learning/6e04aa911551d0f97104.svg"/>。同样地，我们对文本  <img alt="" loading="lazy" src="/logbook/images/deep-learning/5ae5538cf60e628b0b2a.svg"/>也生成对应的三元组  <img alt="" loading="lazy" src="/logbook/images/deep-learning/729bc16ba524103930d5.svg"/>。最终，我们设计对称的三元组损失去增强网络对边缘样本的检索能力：</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/1e034c0e74678f06ce98.svg"/></p>
<p>        其中  <img alt="" loading="lazy" src="/logbook/images/deep-learning/585d56ef5790d90d53ef.svg"/>是一个超参数。</p>
<h3>3.2 实验结果</h3>
<p>Text-video retrieval最权威的五个数据集榜单分别为MSR-VTT, MSVD, LSMDC, DiDeMo和ActivityNet，其主办单位包括，UC berkeley，和阿卜杜拉国王科技大学。我们的HunYuan_tvr大模型在这五个数据榜单上都取得了text-to-video rank@1 Top 1的成绩，并分别领先第二名1.7%, 1.0%, 2.8%, 3.1%, 和11.1%。具体数值如下：</p>
<p>表1：各方法在5个公开数据集上T2V Recall@1指标对比</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/340b2c439787a912fea3.png"/></p>
<p><br/></p>
<p>        具体排行榜结果如下，红色混元是HunYuan_tvr模型：</p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/cd5ac45289645abed059.png"/></p>
<p>图5：HunYuan_tvr在MSR-VTT-1kA上的取得了SOTA的结果</p>
<p>（见https://paperswithcode.com/sota/video-retrieval-on-msr-vtt-1ka）</p>
<p><br/></p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/ea52241dc2a9a83015e6.png"/></p>
<p>图6：HunYuan_tvr在MSVD上的取得了SOTA的结果</p>
<p>（见https://paperswithcode.com/sota/video-retrieval-on-msvd）</p>
<p><br/></p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/014f0f6ba3857dd74e90.png"/></p>
<p>图7：HunYuan_tvr在MSR-VTT-1kA上的取得了SOTA的结果</p>
<p>（见https://paperswithcode.com/sota/video-retrieval-on-lsmdc）</p>
<p><br/></p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/5f990ec51ed9413b1399.png"/></p>
<p>图8：HunYuan_tvr在MSR-VTT-1kA上的取得了SOTA的结果</p>
<p>（见https://paperswithcode.com/sota/video-retrieval-on-didemo）</p>
<p><br/></p>
<p> <img alt="" loading="lazy" src="/logbook/images/deep-learning/4be354c7ae6ca7934d3a.png"/></p>
<p>图9：HunYuan_tvr在MSR-VTT-1kA上的取得了SOTA的结果</p>
<p>（见https://paperswithcode.com/sota/video-retrieval-on-activitynet）</p>
<div>
<div>
<h2>参考文献</h2>
<ol><li>
<p>【赛题解析】广告算法新"视"界：多模态视频广告秒级解析</p>
</li>
<li>
<p>Cheng, X., Lin, H., Wu, X., Yang, F., Shen, D.: Improving video-text retrieval by multi-stream corpus alignment and dual softmax loss. arXiv preprint arXiv:2109.04290 (2021)</p>
</li>
<li>
<p>Luo, H., Ji, L., Zhong, M., Chen, Y., Lei, W., Duan, N., Li, T.: Clip4clip: An empirical study of clip for end to end video clip retrieval. arXiv preprint arXiv:2104.08860 (2021)</p>
</li>
<li>
<p>Liu, Y., Albanie, S., Nagrani, A., Zisserman, A.: Use what you have: Video retrieval using representations from collaborative experts. arXiv preprint arXiv:1907.13487 (2019)</p>
</li>
<li>
<p>Portillo-Quintero, J.A., Ortiz-Bayliss, J.C., Terashima-Marín, H.: A straightforward framework for video retrieval using clip. In: Mexican Conference on Pattern Recognition. pp. 3–12. Springer (2021)</p>
</li>
<li>
<p>Bain, M., Nagrani, A., Varol, G., Zisserman, A.: Frozen in time: A joint video and image encoder for end-to-end retrieval. In: Proceedings of the IEEE/CVF International Conference on Computer Vision. pp. 1728–1738 (2021)</p>
</li>
<li>
<p>Croitoru, I., Bogolin, S.V., Leordeanu, M., Jin, H., Zisserman, A., Albanie, S., Liu, Y.: Teachtext: Crossmodal generalized distillation for text-video retrieval. In: Proceedings of the IEEE/CVF International Conference on Computer Vision. pp. 11583–11593 (2021)</p>
</li>
<li>
<p>Gabeur, V., Sun, C., Alahari, K., Schmid, C.: Multi-modal transformer for video retrieval. In: European Conference on Computer Vision. pp. 214–229. Springer (2020)</p>
</li>
<li>
<p>Liu, S., Fan, H., Qian, S., Chen, Y., Ding, W., Wang, Z.: Hit: Hierarchical transformer with momentum contrast for video-text retrieval. In: Proceedings of the IEEE/CVF International Conference on Computer Vision. pp. 11915–11925 (2021)</p>
</li>
<li>
<p>Liu, Y., Albanie, S., Nagrani, A., Zisserman, A.: Use what you have: Video retrieval using representations from collaborative experts. arXiv preprint arXiv:1907.13487 (2019)</p>
</li>
<li>
<p>Khattab, O., Zaharia, M.: Colbert: Efficient and effective passage search via contextualized late interaction over bert. In: Proceedings of the 43rd International ACM SIGIR conference on research and development in Information Retrieval. pp. 39–48 (2020)</p>
</li>
<li>
<p>Kim, W., Son, B., Kim, I.: Vilt: Vision-and-language transformer without convolution or region supervision. In: International Conference on Machine Learning. pp. 5583–5594. PMLR (2021)</p>
</li>
<li>
<p>Yan, Rui, et al. "Video-Text Pre-training with Learned Regions." arXiv preprint arXiv:2112.01194 (2021).</p>
</li>
<li>
<p>Li, Dongxu, et al. "Align and Prompt: Video-and-Language Pre-training with Entity Prompts." arXiv preprint arXiv:2112.09583 (2021).</p>
</li>
<li>
<p>Cai, Guanyu, et al. "Revitalize Region Feature for Democratizing Video-Language Pre-training." arXiv preprint arXiv:2203.07720 (2022).</p>
</li>
<li>
<p>Radford, A., Kim, J.W., Hallacy, C., Ramesh, A., Goh, G., Agarwal, S., Sastry, G., Askell, A., Mishkin, P., Clark, J., et al.: Learning transferable visual models from natural language supervision. In: International Conference on Machine Learning. pp. 8748–8763. PMLR (2021)</p>
</li>
<li>
<p>Wang, Q., Zhang, Y., Zheng, Y., Pan, P., Hua, X.S.: Disentangled representation learning for text-video retrieval. arXiv preprint arXiv:2203.07111 (2022)</p>
</li>
</ol><p><br/></p>
</div>
</div>
<p><br/></p>
</div>
</div> 
{% endraw %}
