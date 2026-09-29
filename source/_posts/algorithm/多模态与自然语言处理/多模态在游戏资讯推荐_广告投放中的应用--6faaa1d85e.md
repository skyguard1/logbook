---
title: "多模态在游戏资讯推荐_广告投放中的应用"
date: 2022-03-24 10:45:45
categories:
  - 算法
  - 多模态与自然语言处理
---

{% raw %}

<div>
<p>感谢游戏说同学(yuliangshen、collinsun、lokitu、wakalu等)以及算法组同学的支持，加速算法在王者营地、和平营地、广告投放的CTR预估等多个场景落地。相关工作已投稿AAAI-2022。</p>
</div>
<h1>1. 项目背景</h1>
<p>在信息流推荐、广告投放场景；物料冷启动很常见。人工标签通过标签相似性可以有效缓解这种问题，但是，人工标签往往表征能力有限(精度)、人工运营和维护成本高（耗时费力）。 近些年，算法自动打标签变得很火热。</p>
<p>算法自动打标签通常是利用典型深度结构提取物料某些角度信息，然后回归/分类到人工提供的标签树(Label Tree)。 然而，该方法难点在监督信号上，如果提供的标签树本身精度有限，那么算法本身就是有偏的。</p>
<p>现阶段视频、音频、自然语言处理领域都有较好的预训练模型，诸多论文已经验证，利用预训练的模型抽取的特征，对下游任务（如视频领域的分割、音频领域的音乐合成、NLP领域的问答）都有明显帮助。此外，随着对比学习的兴起，视频、音频、自然语言处理领域的无监督表征性能可以比肩甚至超越有监督表征。</p>
<p>目前，我们选用的多模态特征是指：从视频中抽取出的视觉特征、音频特征、文本(认知)特征；物料通过预训练模型、有监督模型、无监督对比模型都可以进行表征。</p>
<h1>2. 多模态平台综述</h1>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/5c0c03bf42ef03d6280d.png"/></p>
<p>上图所示为内容中心与增长中心共建的模型特征实验系统、以及当前覆盖的落地场景。</p>
<h3>工程上解决的问题：</h3>
<ul><li>特征版本管理：版本是指视频、音频、文本特征提取模型的多样性；采用内容中心的调度框架实时统一处理</li>
<li>历史物料重刷：新上线的模态特征提取模型，会触发历史物料自动特征重刷</li>
<li>特征选择配置：物料在每个模态上都有多个模型表征，算法同学可以通过配置，直接拉取对应的模型特征进行业务探索</li>
</ul><h3>业务上探索的方向：</h3>
<ul><li>特征有效性：我们搭建了特征双盲验证平台，分别从单模态特征-标签聚类验证单模态的有效性；多模态特征-有序召回验证多模态信息增益。</li>
<li>业务召回层：活跃用户-多模态序列召回优化； 新内容冷启动-双塔深度召回优化。</li>
<li>业务精排层：在已有的多视角推荐结构、Transformer序列推荐结构、GCN图推荐结构基础上，评估增加物料多模态理解对CTR、时长、留存的收益。</li>
</ul><h1>3. 特征提取与双盲验证</h1>
<h2>3.1 特征提取</h2>
<h2><img alt="" loading="lazy" src="/logbook/images/algorithm/e1109ce5e413b3e0f140.png"/></h2>
<ul><li>
<h3>物料形态</h3>
</li>
</ul><p>      对于信息流推荐，PGC场景（如首页、赛事、英雄等）通常由视频、图文混合推荐为主。PGC-UGC场景(如沉浸视频)只包含视频类。</p>
<p>      对于广告投放CTR预估，素材通常包含视频创意、图文创意。广告投放主要和渠道相关，如微信、手Q主要是图文创意、则都是视频创意</p>
<ul><li>
<h3>物料处理：</h3>
</li>
</ul><p>      视频物料，受限于关键帧提取(Key Frame Extraction)算法的稳定性，本文利用作者选定的封面图和关键帧；若作者并没有提供相关参考帧，则对视频进行分段，随机抽取1帧（每秒）； 音频则对原始视频音轨上的信号进行分段，分段抽取特征进行拼接；音频转文本主要是借助了同学的相关能力，进而提取特征。</p>
<p>      图文物料，本文采集了封面图和作者的正文配图；文本即正文文本；特别值得一提的是，音频特征上， 我们采用的是Padding。</p>
<p>      通过上面描述，由于推荐和投放场景的物料形态不一致，本文提出的多模态融合模型应当具备‘模态缺失’情况下，模型保持鲁棒性。后面会介绍两种方式：基于MLM的多模特征融合与对比学习处理模态缺失、跨领域语义融合。</p>
<ul><li>
<h3>模型选择</h3>
</li>
</ul><p>     模型选择上，根据前沿论文探讨的CV / Audio / NLP下游任务性能较优模型为主。这里，我们没有特别限制‘监督表征’和‘非监督表征’。因为两种方式本身都可以改成'监督表征模型'进行Fune-tuning。</p>
<p>    特征提取上，我们尝试过将特征提取模块与排序模块融合在一起，从而进行End-to-End训练。然而考虑到线上Inference的压力，本文选择了Two-Phase的模式：即相同的监督信号(如CTR、时长)， 分别给多模态特征提取同学和推荐算法同学。 经过测试，该种方式明显优于直接利用预训练模型直接提取物料多模态特征。 后文如无特殊说明，均采用Two-Phase模式。</p>
<h2>3.2 双盲特征验证</h2>
<p>生成的特征直接进行算法实验，明显会加重算法同学的负担，为此我们增加了‘双盲验证’环节，一方面，特征生成同学可以直接利用测试数据评估模型的有效性；算法同学也可以利用测试数据直观感受特征的倾向性。这里，主要关注单模态有效性(聚类)、多模态分别进行有序召回的信息增益。针对对比学习类表征模型，内容中心同学也采用一致性(alignment)、均匀性(uniformity)进行更加客观的评估。</p>
<ul><li>单模态有效性示例</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/d874dc970e31550bf522.png"/></p>
<p>Detail ：王者首页候选内容文本特征提取；降维方法-LDA；模型-有监督Bert；评价信号：多维度标签</p>
<ul><li>多模态有序召回信息增益示例</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/462256b98983498ff1f5.png"/></p>
<p>Detail ：召回-余弦相似度；</p>
<p>在单模态表征能力有效，多模态直接存在信息增益前提下，多模态融合工作才值得进行探索。</p>
<h1>4. 特征有/无监督降维探索</h1>
<p>在业务实践中，为了兼顾线上模型推理和特征有效性，我们尝试了两种方法控制多模态特征的维度：预训练模型-无监督降维、有监督降维。以王者首页候选内容库、文本特征抽取为例，我们采用3中的方法评估了降维后的特征性能：</p>
<ul><li>预训练模型与无监督降维性能评价</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/ba5eb6fe8647e37c2fce.png"/></p>
<ul><li>有监督降维性能评价</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/4a0a99c0eecbb295eee1.png"/></p>
<h1>5. 多模态特征融合方法</h1>
<p>在单模态特征有效、多模态之间存在信息增益基础上，探索了多模态特征融合技巧，旨在处理跨领域语义融合以及增强模态缺失情况下模型的鲁棒性。</p>
<h2>5.1 基于MLM的模态特征融合</h2>
<p>参考KM : “【算法研究】EMNLP21:Mask-TRF融合知识图谱优化对话任务”[内部或本地链接已移除]</p>
<p>我们关注的四种掩码语言模型（Masked Language Model， MLM）为：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/c6e8a843dcf2fa46a595.png"/></p>
<p>该方法主要应用于基于序列召回模型以及基于序列精排模型</p>
<h2>5.2 基于对比学习的模态特征融合</h2>
<p>采用对比学习范式处理跨模态语义融合、模态缺失。在今年的很多顶会(ACL2021/EMNLP2021/KDD2021等)频繁出现，探索中，我们也提出了相关结构:</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/d781cd76f809fdbb97ca.png"/></p>
<p><br/></p>
<p>该方法主要应用于多视角精排模型以及图推荐精排模型</p>
<h1>6.召回层：mm-Faiss 和 mm-NN</h1>
<p>召回层目前优化了序列召回和深度召回。序列召回主要针对活跃用户设计，通过感知用户历史点击列表的兴趣变化进行内容召回；深度召回主要针对内容冷启动和用户冷启动设计(用户冷启动侧特征为自然人和游戏大盘画像，内容侧为多模态特征)。</p>
<h2>6.1 mmFaiss</h2>
<ul><li>
<h3>模型与工程优化</h3>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/a50f92f5c7e7132faff9.png"/></p>
<p>Detail: 序列模型-Transformer； Faiss用于相似向量索引加速，借助了Venus的能力。</p>
<ul><li>
<h3>业务探索</h3>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/37422c772d0be6f7a8c9.png"/></p>
<p>选用的Baseline分别是作者召回、标签画像召回、序列标签Faiss召回。从特征融合效果上看，多模态融合召回在PVCTR、UVCTR上一致性优于单模态；与点击标签Faiss对比，多模态融合策略在PVCTR上具有优势，在UVCTR上处于劣势。</p>
<h2>6.2 mm-NN</h2>
<ul><li>
<h3>模型与工程优化</h3>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/cfce02a19d8d09173527.png"/></p>
<p>Detail ： 用户侧-自然人与游戏大盘画像； 内容侧-内容多模态特征；双塔结构-YoutubeDNN、W&amp;D等均可；工程优化上主要借助Faiss进行向量相似性召回加速，然后线上采用大规模Softmax进行处理。</p>
<ul><li>
<h3>业务探索</h3>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/ae5f1484920c1c66e5f3.png"/></p>
<p>Baseline：用户侧-自然人与游戏大盘画像； 内容侧-文章号</p>
<p>从特征融合效果上看，多模态融合深度召回模型的AUC一致优于单模态和Baseline；线上效果多模态在PVCTR上优于Baseline，在UVCTR上略占优势。额外的，多模态模型也能有效缓解推荐中常遇到的“Long-tail”现象，是的物料消费的更充分。</p>
<h1>7. 精排层：多视角结构、序列结构、图推荐结构</h1>
<p>根据业务需要，精排层目前开发了三种结构：1. 基于层次注意力(Hierarchical Attention)的多视角精排模型； 2. 基于用户历史兴趣的Transformer/Bert序列推荐模型； 3. 基于渠道/场景CTR/CVR二分图的图推荐结构。这里，主要交流我们将多模态模块融入三种模型结构的方法以及经验结果。</p>
<h2>7.1 多模态与多视角推荐</h2>
<ul><li>
<h3>多视角推荐结构</h3>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/70d0c964c67e7ef1dee4.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/6e259efb43ab79c2088d.png"/></p>
<p>其中，CL是5.2中介绍的，采用对比学习进行多模态特征融合。目标函数根据业务需要，调整为CTR或时长<strong>(消费百分比)</strong>。</p>
<ul><li>
<h3>业务探索</h3>
</li>
</ul><p>进行业务实验时，我们主要关心两个问题： 1. 多模态特征引入是否具有明显收益； 2. 多模态融合方式是否能有效处理模态缺失，稳定模型性能（王者首页音频缺失~45%+， 视频~5%  | 和平首页音频缺失~12%）； </p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2410cf210c3f0e4909fe.png"/></p>
<p>对于PVCTR, 多模态模型优于Baseline(DeepFM), 与点击/时长多视角模型效果相当； 对于UVCTR，多模态模型取得了最好的效果。此外，周数据上，模型性能稳定。</p>
<h2>7.2 多模态与序列推荐</h2>
<ul><li>
<h3>序列推荐结构</h3>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/f00b311a9596e92ab0d1.png"/></p>
<p>其中，MLM是5.1中提到的掩码语言模型，用于控制多模态直接进行交互，并维护Item全局特征。关于绝对位置编码以及相对位置编码对模型的分析，可以参考文章：[内部或本地链接已移除]（序列推荐:异质特征融合与对比学习泛化）</p>
<ul><li>
<h3>业务探索</h3>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/f6aa786421e403a65cad.png"/></p>
<p>在业务效果上，融合模态较单模态序列推荐模型(Text)在PVCTR、UVCTR上均有明显提升。与Baseline相比，多模态在PVCTR上性能略占优势，UVCTR上，取得了明显效果提升。</p>
<h2>7.3 多模态与图推荐</h2>
<ul><li>
<h3>图推荐结构</h3>
</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/c4d8809785993d15e245.png"/></p>
<p>其中，CL是5.2中介绍的，采用对比学习进行多模态特征融合。监督信号目前已经尝试单业务/渠道内的点击二分图(非加权图)，时长/物料消费百分比（加权图）。</p>
<p><br/></p>
<p>基础模型参考：</p>
<p>多视角推荐结构: Wu C, Wu F, An M, et al. Npa: Neural news recommendation with personalized attention[C]//Proceedings of the 25th ACM SIGKDD international conference on knowledge discovery &amp; data mining. 2019: 2576-2584.</p>
<p>序列推荐结构: de Souza Pereira Moreira G, Rabhi S, Lee J M, et al. Transformers4Rec: Bridging the Gap between NLP and Sequential/Session-Based Recommendation[C]//Fifteenth ACM Conference on Recommender Systems. 2021: 143-153.</p>
<p>聚合图推荐结构: Xiangnan He, Kuan Deng, Xiang Wang, Yan Li, YongDong Zhang, and Meng Wang. 2020. LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation. In Proceedings of the 43rd International ACM SIGIR Conference on Research and Development in Information Retrieval (SIGIR '20). Association for Computing Machinery, New York, NY, USA, 639–648. DOI:https://doi.org/10.1145/3397271.3401063</p> 
{% endraw %}
