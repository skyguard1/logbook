---
title: "GNN 社交推荐在业务的应用"
date: 2022-04-27 18:37:46
categories:
  - deep-learning
---

<div class="page">
<div class="layoutArea">
<div class="column">

<span style="font-size:11pt;font-family:&#39;等线&#39;;">GNN </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">天模型和流式训练模型都是基于 </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">PlatoDeep </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">开发，详细的 </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">PPL </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">介绍见团队的&nbsp;</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">KM <font>文章PlatoGL和PlatoGL on DKR。</font></span>
<h1><span style="font-size:11pt;font-family:&#39;等线&#39;;">三、 小结与后续 </span></h1>
<p><span style="font-size:11pt;font-family:&#39;等线&#39;;">在社交推荐的问题上，指导我们建模的基本思想是好友同质性和好友影响力。目前在底图构造和模型追加 </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">loss </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">的部分我们都使用到了传统网络科学中对网络结构的认知分析结果，这些思路都在提现在好友同质性和影响力的挖掘结果上，而学界直接利 用模型对社交影响力传播进行直接建模，我们目前还没有拿到收益。后续，我们在 </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">GNN </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">社交推荐的模型中我们会考虑更多的高阶结构，比如更多类型的 </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">motif</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">，以及社群结构表达，来增强模型对社交关系的拓扑表达，提高社交推荐的精度。 </span></p>
<p><span style="font-size:11pt;font-family:&#39;等线&#39;;">声明:本文的工作包含多位团队成员(</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">nickgu</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">，</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">joelzheng</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">，</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">danieslin</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">，</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">drolcaqiu</span><span style="font-size:11pt;font-family:&#39;等线&#39;;">)的工作 产出，由 </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">chrisyi </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">和 </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">jerrycgsong </span><span style="font-size:11pt;font-family:&#39;等线&#39;;">整理成文。同事们对文中细节有疑问，欢迎交流。 </span></p>
<p><span style="font-size:18pt;font-family:&#39;宋体&#39;;">参考资料 </span></p>
</div>
</div>
</div>
<div class="page">
<div class="layoutArea">
<div class="column">
<pre>[1] C. Gao et al. Graph Neural Networks for Recommender Systems: Chanllenges, Methods, and Directions. TIS 2021.
</pre>
<pre>[2] S. Wu et al. Graph Neural Networks in Recommender Systems: A Survey. J. ACM 2021.
</pre>
<pre>[3]  https://github.com/wusw14/GNN-in-RS
[4]  https://github.com/tsinghua-fib-lab/GNN-Recommender-Systems
</pre>
<pre>[5]  T. Kipf and M. Welling. Semi-supervised classification with graph convolutional networks. ICLR 2017.
</pre>
<pre>[6]  W. L. Hamilton et al. Inductive representation learning on large graphs. NeurIPS 2017.
</pre>
<p><span style="font-size:12pt;font-family:&#39;宋体&#39;;">[7] P. Veli</span><span style="font-size:12pt;font-family:&#39;宋体&#39;;">c</span><span style="font-size:12pt;font-family:&#39;Times New Roman&#39;;">̌</span><span style="font-size:12pt;font-family:&#39;宋体&#39;;">kovi</span><span style="font-size:12pt;font-family:&#39;宋体&#39;;">ć </span><span style="font-size:12pt;font-family:&#39;宋体&#39;;">et al. Graph attention networks. ICLR 2018. [8] J. Sun et al. Multi-graph Convolution Collaborative Filtering.&nbsp;</span><span style="font-family:&#39;宋体&#39;;font-size:12pt;">CIKM 2020.</span></p>
<pre>[9] X. Wang et al.  Disentangled Graph Collaborative Filtering. SIGIR 2020.
</pre>
<pre>[10] R. Ying et al.  Graph Convolutional Neural Networks for Web-Scale Recommender Systems. KDD 2018.
</pre>
<pre>[11]  J. Yu et al. Enhance Social Recommendation with Adversarial Graph Convolutional Networks. 2020.
</pre>
<pre>[12] C. Song et al.  Social Recommendation with Implicit Social Influence. SIGIR 2021.
</pre>
<pre>[13] L. Wu et al.  A Neural Influence Diffusion Model for Social Recommendation. SIGIR 2019.
</pre>
<pre>[14] Q. Wu et al.  Dual Graph Attention Networks for Deep Latent Representation of Multifaceted Social Effects in Recommender Systems. WWW 2019.
</pre>
<pre>[15] L. Wu et al.  Diffnet++: A neural influence and interest diffusion network for social recommendation. TKDE 2020.
</pre>
<pre>[16] C. Ma et al. Memory Augmented Graph  Neural Networks for Sequential Recommendation. AAAI 2020.
</pre>
</div>
</div>
</div>
<div class="page">
<div class="layoutArea">
<div class="column">
<pre>[17] Z. Pan et al.  Star Graph Neural Networks for Session-Based Recommendation. CIKM 2020.
</pre>
<pre>[18] J. Wang et al.  Session-based Recommendation with Hypergraph Attention Networks. ICDM 2021.
</pre>
<pre>[19]  https://en.wikipedia.org/wiki/Gated_recurrent_unit
[20] X. Wang et al.  KGAT: Knowledge Graph Attention Network for Recommendation. KDD 2019.</pre>
<pre>[21] R. Sun et al.  Multi-Modal Knowledge Graphs for Recommender Systems. CIKM 2020.
</pre>
<pre>[22] H. Wang et al.  Knowledge Graph Convolutional Networks for Recommender Systems. WWW 2019.
</pre>
</div>
</div>

<p><span style="font-size:11pt;font-family:&#39;等线&#39;;"><br></span></p>
