---
title: "KG-BERT_ 基于BERT的知识图谱补全"
date: 2022-03-31 14:21:05
categories:
  - 算法
  - 图学习与知识图谱
---

{% raw %}

<p><strong>什么是知识图谱补全?</strong></p>
<p>知识图谱(Knowledge Graph, KG)是一种常用的知识表示形式。它将知识表示为一个多关系的图，其中实体是图中的节点，实体间的关系是图中的边。每一条边由一个三元组(head entity、relation、tail entity)表示，例如(Steve Jobs, founded, Apple Inc.)，表明实体节点"史蒂夫·乔布斯"和实体节点"苹果公司"之间具有"创建"关系，三元组可简写为(h, r, t)。尽管知识图谱在语义搜索、推荐、问答等任务中发挥了重要的作用，现有知识图谱往往不够完整，也就是缺少很多三元组。而知识图谱补全任务就是为了解决这个问题，其本质是对一个不在知识图谱中的三元组存在的可能性作出评估。</p>
<p></p>
<p><strong>现有知识图谱补全方法有什么不足？</strong></p>
<p>主流的知识图谱补全方法基于知识图谱嵌入(Knowledge Graph Embedding)技术 [1]。然而，大多数知识图谱嵌入模型仅仅考虑了图谱的结构信息，其效果受到知识图谱稀疏性的制约。近年来，一些研究工作引入文本信息以增强知识表示学习 [2, 3, 4, 5, 6, 7] 。但是，这些方法将不同三元组中的同一个实体/关系表示为相同的文本嵌入，从而忽略了上下文信息。例如，对于三元组(Steve Jobs, founded, Apple Inc.)和(Steve Jobs, isCitizenOf, United States), "Steve Jobs"的描述语句的不同单词的重要性应该是不同的。另一方面，现有文本增强的方法仅仅利用了实体描述、包含关系的句子、单词与实体的共现信息等，而大规模文本数据中的语法、句法等语言信息没有被充分利用。</p>
<p></p>
<p><strong>预训练语言模型</strong></p>
<p>最近一年来，预训练语言模型例如ELMo [8]、GPT [9]和BERT [10]在自然语言处理(NLP)领域获得了巨大的成功，这些模型能利用互联网中的大规模自然语言文本数据学得上下文相关的词嵌入表示，并在许多自然语言理解任务中取得了当前最优效果。其中，BERT是最具影响力的模型，它通过掩码语言建模(masked language model)和下一句预测任务(next sentence prediction)预训练了一个双向Transformer [11]文本编码器，Transformer编码器基于自注意力机制。预训练BERT模型既能考虑上下文信息，又能提供丰富的语言学知识，正好可以弥补现有基于文本的知识图谱嵌入模型的不足。接下来，我们以BERT为例，介绍如何利用预训练语言模型完成知识图谱补全任务。</p>
<p></p>
<p><strong>KG-BERT模型</strong></p>
<p>为了充分利用上下文信息和语言学知识，我们微调BERT模型以实现知识图谱补全。我们将实体和关系表示成它们的名字或描述，然后将名字/描述的单词序列作为BERT的输入句子。同原始的BERT模型一样，"句子"可以是任意长度的连续文字。为了对一个三元组存在的可能性建模，我们将(h, r, t)的句子连接成一个单独的序列。KG-BERT的输入可以是两个实体的名字/描述句子，也可以是(h, r, t)的三个句子的拼接。</p>
<p></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/6fd8f42a60d0a733933a.png"/></p>
<p>图1. 微调KG-BERT模型对一个三元组的合理性建模。</p>
<p></p>
<p>用于对三元组建模的KG-BERT的模型如图1所示。我们将这个KG-BERT版本命名为KG-BERT(a)。我们将头实体、关系、尾实体的句子拼接为一个序列。序列之间以特殊标记[SEP]分隔。第一个标记[CLS]将作为特殊的分类标记。对于三元组(Steve Jobs, founded, Apple Inc.)，头实体的句子是"Steven Paul Jobs was an American business magnate, entrepreneur and investor"或者"Steve Jobs"，尾实体的句子是"Apple Inc. is an American multinational technology company headquartered in Cupertino, California."或者"Apple Inc."。每个标记的输入是其词向量、位置向量和段落向量的和。两个实体句子中的标记共享一个段落向量eA, 关系句子的段落向量则是eB。相同位置的不同标记的位置向量相同。标记的输入嵌入传入多层双向Transformer模型 [11]后，会得到其上下文相关的隐层表示。我们将第一个标记[CLS]的最上层表示C作为三元组的最终表示，并传入一个sigmoid层用来计算三元组的得分。最后用三元组是否为真的标签y (取值为0或1)计算交叉熵损失。注意到在知识图谱中只能观察到标签为1(即为真)的三元组，而我们需要标签为0(即为假)的三元组。我们通过将真三元组的头实体或尾实体替换为一个随机的实体来得到假三元组(不能存在于真三元组集合中)。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/362f57928aa63a62ce57.png"/></p>
<p>图2. 微调KG-BERT模型用于预测两个实体间的关系。</p>
<p></p>
<p>用于预测实体间关系的KG-BERT模型如图2所示，我们将这个版本命名为KG-BERT(b)。我们用头实体h和尾实体t的句子预测关系r。在本文的预备实验中，我们发现直接预测关系要优于对KG-BERT(a)通过随机替换关系取负样本。我们同样使用[CLS]的最终状态C作为输入实体对的表示，并经过softmax层计算关系的得分，并用关系的标签计算交叉熵损失。</p>
<p><strong>实验</strong><br/></p>
<p>我们在三个知识图谱补全任务中评价KG-BERT的性能：</p>
<p>(1) 三元组分类：判断一个三元组(h, r, t)是否为真，以准确率为评价指标。</p>
<p>(2) 链接预测:  给定(h, r, ?)或(?, r, t), 预测缺失实体t或h及实体在所有候选实体中的排序，以平均排名(MR)和Hits@10作为评价指标。</p>
<p>(3) 关系预测，给定(h, ?, t)， 预测缺失关系r及其排序，以平均排名和Hits@1作为评价指标。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/80f77d55c1ce48ae078e.png"/></p>
<p>                                                 表1.数据集统计</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/885f3b2f8016f502db91.png"/></p>
<p>                                           表2.不同模型的三元组分类准确率</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/db25a95360f25f943d08.png"/></p>
<p>        图3.取不同训练集比例时不同模型三元组分类准确率。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f1eacc4e8d662894186a.png"/></p>
<p>                                             表3.不同模型的链接预测性能</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/309f52359b9dce1dde49.png"/>表4.不同模型的关系预测性能</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7e3fc90f8090084f0298.png"/></p>
<p>图4. KG-BERT(a)对于WN8RR数据集中三元组(__twenty_dollar_bill_NN_1, hypernym, __note_NN_6)的输入句子序列的注意力权重的可视化展示</p>
<p></p>
<p>从实验结果中我们发现KG-BERT能在三元组分类、链接预测、关系预测任务中取得最优结果。KG-BERT能在训练三元组较少的情况下仍然取得较高的分类准确率。KG-BERT能通过自注意力机制和上下文有关的表示聚焦到三元组描述语句中最重要的单词。</p>
<p> </p>
<p>KG-BERT表现好的主要原因是：(a) 我们对三元组的实体和关系描述进行了联合建模。(b) 知识图谱补全任务与BERT预训练中的下一句预测任务比较相似，下一句预测任务从海量文本中学到了句子间的关系，因此对于推断三元组(h, r, t)的句子间关系很有帮助。(c) 模型学到的隐层表示是上下文有关的表示，不同三元组中的同一个词具有不同的表示，因此KG-BERT利用了上下文信息。<br/></p>
<p></p>
<p><strong>总结</strong></p>
<p></p>
<p>本文介绍了我们利用预训练语言模型进行知识图谱补全的最新工作，更多具体细节可以阅读论文：</p>
<p></p>
<p>Yao, L., Mao, C. and Luo, Y., 2019. KG-BERT: BERT for Knowledge Graph Completion. arXiv preprint arXiv:1909.03193.</p>
<p></p>
<p>https://arxiv.org/abs/1909.03193</p>
<p></p>
<p>代码链接: https://github.com/yao8839836/kg-bert</p>
<p></p>
<p>相关的后续工作仍在继续。欢迎大家使用、交流。</p>
<p></p>
<p></p>
<p><strong>参考文献</strong></p>
<p> </p>
<p>[1] Wang, Q.; Mao, Z.;Wang, B.; and Guo, L. 2017. Knowledge graph embedding: A survey of approaches and applications. IEEE TKDE 29(12):2724–2743.</p>
<p></p>
<p>[2] Socher, R.; Chen, D.; Manning, C. D.; and Ng, A. 2013. Reasoning with neural tensor networks for knowledge base completion. In NIPS, 926–934.</p>
<p></p>
<p>[3] Xie, R.; Liu, Z.; Jia, J.; Luan, H.; and Sun, M. 2016. Representation learning of knowledge graphs with entity descriptions. In AAAI.</p>
<p></p>
<p>[4] Xiao, H.; Huang, M.; Meng, L.; and Zhu, X. 2017. SSP: semantic space projection for knowledge graph embedding with text descriptions. In AAAI.</p>
<p></p>
<p>[5] Wang, Z., and Li, J.-Z. 2016. Text-enhanced representation learning for knowledge graph. In IJCAI, 1293–1299.</p>
<p></p>
<p>[6] Xu, J.; Qiu, X.; Chen, K.; and Huang, X. 2017. Knowledge graph representation with jointly structural and textual encoding. In IJCAI, 1318–1324.</p>
<p></p>
<p>[7] An, B.; Chen, B.; Han, X.; and Sun, L. 2018. Accurate text-enhanced knowledge graph representation learning. In NAACL, 745–755.</p>
<p></p>
<p>[8] Peters, M. E.; Neumann, M.; Iyyer, M.; Gardner, M.; Clark, C.; Lee, K.; and Zettlemoyer, L. 2018. Deep contextualized word representations. In NAACL, 2227–2237.</p>
<p></p>
<p>[9] Radford, A.; Narasimhan, K.; Salimans, T.; and Sutskever, I. 2018. Improving language understanding by generative pre-training.</p>
<p></p>
<p>[10] Devlin, J.; Chang, M.-W.; Lee, K.; and Toutanova, K. 2019. Bert: Pre-training of deep bidirectional transformers for language understanding. In NAACL, 4171–4186.</p>
<p></p>
<p>[11] Vaswani, A.; Shazeer, N.; Parmar, N.; Uszkoreit, J.; Jones, L.; Gomez, A. N.; Kaiser, Ł.; and Polosukhin, I. 2017. Attention is all you need. In NIPS, 5998–6008.</p> 
{% endraw %}
