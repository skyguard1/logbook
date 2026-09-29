---
title: "深度学习在CTR中的应用"
date: 2022-04-06 09:49:06
categories:
  - 算法平台
  - 排序与预估模型
---

{% raw %}

<h1>前言</h1>
<p>在计算广告和推荐系统中，点击率（Click Through Rate，以下简称CTR）预估是一个重要问题。CTR预估任务（以下简称CTR任务）是根据user信息、item信息和context信息来预测user对item的CTR。</p>
<p>随着深度学习的发展，近些年深度模型被越来越多的用在了CTR任务中来，并公开数据集上取得了SOTA的效果。</p>
<p>本文下面将这样组织，首先介绍CTR模型的结构，再介绍目前主流的深度模型，最后给benchmark。</p>
<p>本文工作由tinkleguo和kimmyzhang共同完成。</p>
<h1>模型结构</h1>
<p>典型的深度CTR模型结构为：输入、特征嵌入（feature embedding）、特征提取、输出。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/35b0bb2322630cd331fa.png"/></p>
<h2>输入</h2>
<p>输入的每条样本是一个包含特征ID（通常用uint64表示）和特征值（通常用float表示）的序列。</p>
<p>在工业级CTR任务中，特征空间是开放、高维的（特征总数通常上亿，多则千亿），样本是稀疏的（每条样本包含的特征数少，通常是几百，多则上千）。<strong>这是非常重要的性质，也是CTR任务相比其它深度学习任务的特点和难点。</strong></p>
<p>特征组织上，将特征分组，叫“特征组”，也有的文献叫“特征域（field）”。典型的特征组例如：user age、user tag、item tag。对每个特征组来说，每条样本可以包含任意数量的特征。</p>
<p>特征来源上，传统上有三部分，分别是user、item、context。近几年，有一些工作将特征来源拓展到user、candidate item、history item、context，比如的DIN和DIEN。我们把这两种模式分别叫ui和uch，本文的内容只覆盖ui。uch的工作我们也在积极实验中，目前离线取得了不错的效果。</p>
<h2>特征嵌入</h2>
<p>如上所说，样本的特点是<strong>高维、稀疏、分组</strong>。特征嵌入的功能是将高维稀疏特征转换成低维稠密向量，进而利用传统的深度学习技术。</p>
<p>特征嵌入采用<strong>分组嵌入</strong><strong>，</strong>即对每个特征组维护一个或者多个嵌入矩阵（embedding matrix），对样本中每个特征组中的特征在对应的嵌入矩阵中做嵌入查找（embedding lookup）操作，得到该特征组的向量（mini-batch时是矩阵），再将这些向量（矩阵）拼（concat）成一个更宽的向量（矩阵）。</p>
<h2>特征提取</h2>
<p>特征嵌入输出了稠密向量，特征提取部分利用传统的深度学习技术将稠密向量转换成标量。作为模型的核心模块，特征提取模块设计的合理性直接决定模型的好坏。这也是本文剩下部分要展开描述的内容。</p>
<h2>输出</h2>
<p>将上面输出的标量用sigmoid函数映射到[0, 1]，即表示CTR。</p>
<h1>深度CTR模型</h1>
<p>如上文所说，深度CTR模型结构包含了四部分：输入、特征嵌入、特征提取、输出。</p>
<p>输入是高维、稀疏、分组的，特征嵌入使用分组嵌入的方式，输出用sigmoid激活函数。本部分只描述模型的“特征提取”部分。</p>
<h2>LR</h2>
<p>CTR任务本质上是一个二分类问题，逻辑回归（Logistic Regression, LR）是对二分类建模的一个经典模型，也通常是各种benchmark的baseline。算法原理无需介绍。</p>
<p>唯一不同的是，采用了分组嵌入后，LR的嵌入矩阵的列均为1，我们要对分组嵌入的结果做reduce_sum。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8762809032f603bb8c50.png"/></p>
<p>为提高LR效果，需要人工挖掘特征的高阶组合。然而对高维稀疏特征的CTR任务，这个过程变得越来越困难。因此，人工特征工程加上LR模型处理CTR任务费时、费力。</p>
<p>在深度CTR模型中，通常会将LR（不带输出sigmoid激活函数，下文类似描述也做此理解）作为一个组成部分。此外，<strong>LR部分的嵌入矩阵是单独训练的</strong>，不会和其模型组成部分共享嵌入矩阵。</p>
<h2>FM</h2>
<p>Rendle等在2010年提出的因子分解机（Factorization Machines，FM）<sup>[1]</sup>。在FM模型中，除了原始特征和对应权重，还将原始特征两两组合构成新的二阶特征，并对每个新特征分配权重。假设原始特征数为n，则二阶特征的权重矩阵参数高达O(n^2) 。</p>
<p>在FM模型中，权重矩阵通过因子分解表示成两个低维（如n*k， k表示嵌入矩阵的维度）矩阵相乘的形式，矩阵参数可降低到 O(nk)。通常n&gt;&gt;k ，所以nn&gt;&gt;nk 。</p>
<p>在CTR模型中的FM均采用对特征分组嵌入的方式，对m个dense embedding两两组合（m表示特征组个数），对应图中的FM Layer v1。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/508792a39e6cedd2c7f2.png"/></p>
<p>在深度CTR模型中，FM通常也不会单独使用，而是将它的核心部分FM Layer作为一个组成部分，这要引出它的两个版本。</p>
<h3>FM Layer v1</h3>
<p>即上图中的FM Layer v1，输入tensor shape是（batch，m，k），输出tensor shape是（batch，1）。</p>
<p>直接show you the code，参考实现：</p>
<p>[内部或本地链接已移除]</p>
<h3>FM Layer v2</h3>
<p>输入tensor shape是（batch，m，k），输出tensor shape是（batch，k）。和v1的区别是v1在embedding的维度k上做了求和（reduce_sum），v2保留了原始embedding维度k，保留了更多信息。</p>
<p>参考实现：</p>
<p>[内部或本地链接已移除]code.[内部链接已移除]</p>
<h2>MLP</h2>
<p>MLP的本质是堆叠若干个全连接层（Stacked Fully Connected Layer），注意：全连接层之间的激活函数（ReLU）在图中被省略了。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/dd9ab7787da34ccb7ae8.png"/></p>
<p>同样的，MLP通常也不会单独使用，它是深度CTR模型最重要的积木。</p>
<h2>NFM</h2>
<p>Xiangnan He等在2017年提出了神经网络因子分解机（Neural Factorization Machines, NFM）<sup>[2]</sup>。NFM仅仅将FM Layer v2和MLP串联起来，并无太大创新。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/482d3ffe8143e55c5143.png"/></p>
<h2>AFM</h2>
<p>Jun Xiao等人于2017年提出注意力因子分解机（Attentional Factorization Machines，AFM）<sup>[3]</sup>。AFM是在FM的基础上进行改进，其特点是通过注意力网络学习二阶组合特征的重要性。将FM中的FM layer v1替换成Attention Net便可得到AFM。</p>
<p>AFM Attention Net在m个dense embedding两两组合过程中，还通过注意力机制学习到二阶组合特征的注意力分数作为权重，最后将所有的二阶组合特征向量进行加权求和作为Attention Net部分的输出。</p>
<p>与FM Layer类似，Attention Net也有两个版本。Attention Net v1的输出tensor shape是（batch，1），Attention Net v2的输出tensor shape是（batch, k）。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ca9c1f2fea1d64e844cd.png"/></p>
<p>参考实现</p>
<p>[内部或本地链接已移除]</p>
<p>AFM使用的是Attention Net v1。</p>
<h3>DeepAFM</h3>
<p>将Attention Net v2并联一个MLP，即得到DeepAFM。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/3f371cac8da20e70fa23.png"/></p>
<h2>IAFM</h2>
<p>Fuxing Hong等人于2019年提出的交互感知因子分解机（Interaction-aware Factorization Machines，IAFM）<sup>[4]</sup>从特征层面和特征组层面共同影响二阶组合特征的重要性。</p>
<p>在特征层面上与AFM类似，同样采用注意力网络学习二阶组合特征的重要性；在特征组层面，通过网络学习特征所在特征组之间的重要性向量。将组合特征的embedding与重要性向量按位相乘，再和组合特征的注意力分数加权求和作为Attention Net部分的输出。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/fc3383592bd1e7dfabff.png"/></p>
<p>参考实现：</p>
<p>[内部或本地链接已移除]</p>
<h3>DeepIAFM</h3>
<p>将Attention Net v2并联一个MLP，即得到DeepIAFM。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b5fe72f544a7a0c55998.png"/></p>
<h2>WND</h2>
<p>在2016年提出宽度与深度模型（Wide&amp;Deep,，WND）<sup>[5]</sup>。WND模型分成wide和deep部分，wide可以看成是一个不带sigmoid的LR，deep可以看成是一个不带sigmoid的MLP。最终将wide和deep的结果求和输出，其网络结构如下图：</p>
<p>WND模型在在深度CTR模型中占有举足轻重的位置，下面介绍的DeepFM、DCN、xDeepFM都可以看成是WND的变种。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e5316cf2d969783c9220.png"/></p>
<h2>DeepFM</h2>
<p>Huifeng Guo等在2017年提出深度因子分解机模型（Deep Factorization Machine, DeepFM）<sup>[6]</sup>用FM替换了WND模型Wide部分的LR，且FM Layer与MLP共享Embedding。DeepFM有两种版本，DeepFM v1和DeepFM v2。</p>
<h3>DeepFM v1</h3>
<p>DeepFM v2直接将FM Layer v1、MLP、LR输出加起来。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/88c57045ee571e152968.png"/></p>
<h3>DeepFM v2</h3>
<p>DeepFM v2将FM Layer v2、MLP、LR输出并联（Concat），再叠加一层FC。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/5b7d031476d119b1d9b9.png"/></p>
<h2>DCN</h2>
<p>Ruoxi Wang等在2017年提出深度与交叉神经网络（Deep&amp;Cross Network，DCN）<sup>[7]</sup>将FM构造二阶组合特征的过程推广到高阶。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/67a5886f306285c44913.png"/></p>
<p>Cross Net是DCN的创新部分，它与MLP共享Embedding，将特征经嵌入后得到m个dense embedding拼成的宽向量作为初始向量送入Cross Net中。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/78001d0563b9c2e28871.png"/></p>
<p>Cross Net是一个堆叠型网络，每层输出（y）构建过程是将上一层输出向量（x）与初始向量（x0）做笛卡尔积，并将得到的矩阵重新投影成与初始向量同维度向量，再加入上一层输出向量和偏置一起作为该层的输出向量。</p>
<p>Cross Net的每一层输出都包含上一层的输出信息，因此搭建N层Cross Net，最后一层输出直接包括第1阶、第2阶…第N+1阶的特征信息。</p>
<h2>xDeepFM</h2>
<p>Jianxun Lian等人在2019年提出了极端深度因子分解机（eXtreme Deep Factorization Machine, xDeepFM）<sup>[8]</sup>。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/bafb5f4730dce4e1bd92.png"/></p>
<p>CIN是xDeepFM的创新部分，它与MLP共享Embedding。与MLP将特征经嵌入后得到m个dense embedding拼成的宽向量作为初始向量不同，CIN将m个dense embedding拼成m*k的初始矩阵，矩阵的每一行表示一个特征向量。</p>
<p>CIN也是一个堆叠型网络，每层输出矩阵的每一个特征向量都是由上层输出矩阵的特征向量和初始矩阵中的特征向量两两组合并加权求和得到。</p>
<p>CIN和DCN的Cross Layer存在以下区别：</p>
<p>Cross Layer网络每层输入/输出都是向量，CIN网络每层输入/输出都是矩阵。Cross Layer每层输出维度固定，CIN每层输出矩阵的列固定，特征个数不固定（是可变参数）。</p>
<p>Cross Layer每层输出都包含上一层输出信息，CIN没有，CIN第N层只包含N+1阶特征信息。因此CIN每层都需要通过一个sum pooling连接到最后的输出层。</p>
<h2>AutoInt</h2>
<p>Weiping Song等人在2019年提出通过自注意力神经网络自动化特征交互学习方法（Automatic Feature Interaction Learning via Self-Attentive Neural Networks，AutoInt）<sup>[9]</sup>。AutoInt通过过多头（Multi-head）注意力机制将特征投射到多个子空间中，并在不同的子空间中捕获不同的特征组合形式。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/749c37402201d9f1780e.png"/></p>
<p>在每个注意力子空间中，首先会计算特征向量和其他特征向量在该注意力空间的中相似程度，其次通过加权求和方法获得该特征向量在该注意力空间的相关特征向量，并将所有注意力空间的相关特征向量拼起来作为该特征最终的相关特征向量。再引入残差网络以保留一些原始特征信息。最后将所有特征的相关特征向量拼接起来作为该层的最终输出。</p>
<h2>FGCNN</h2>
<p>Bin Liu等人在2019年提出基于卷积神经网络的CTR特征生成方法（Feature Generation by Convolutional Neural Network，FGCNN）<sup>[10]</sup>包含特征生成（Feature Generation）和深度分类器（Deep Classifier）两部分。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/0bf9821894bc48680238.png"/></p>
<p>特征生成部分采用的结构是CNN+Recombination，原始特征经分组嵌入后得到的嵌入向量分别经过卷积、池化、重组（将池化后的Feature Maps展成一个向量，再使用tanh激活函数的FC层）得到的特征向量与原始特征嵌入向量拼接，再送入到深度分类器部分。为避免梯度耦合问题，特征生成部分的Embedding和原始特征Embedding需要分开训练。FGCNN实际上是一种特征生成方法，可以和任意模型进行组合，如上图深度分类器部分采用的是IPNN<sup>[11]</sup>。</p>
<h1>实验及结果分析</h1>
<h2>数据集</h2>
<p>本文使用五个数据集，包括四个公开数据集（avazu、criteo、kdd2012t2、movielens1m）和看一看视频流数据集（video2）。数据集的具体描述如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b5095b862960e5253fb1.png"/></p>
<h2>实验平台</h2>
<p>我们基于tensorflow实现了deepx_rank_tf（[内部或本地链接已移除]），用C++实现了deepx_rank（[内部或本地链接已移除]code.[内部链接已移除]）。前者提供了一个benchmark和实验平台，后者为高效的离线训练和在线服务提供了整套的解决方案，目前看一看和搜一搜中的很多排序业务均使用了我们的工具。</p>
<p>下面的实验结果均基于deepx_rank_tf完成。</p>
<h2>实验结果</h2>
<p>在上述5个数据集上进行实验（具体实验过程可参考benchmark：[内部或本地链接已移除]）并收集测试集AUC、测试集logloss和训练速度。</p>
<p>测试集AUC</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/12721c67e4d9f834d1c4.png"/></p>
<p>测试集logloss</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/9df6a4c0d7b387cd49a3.png"/></p>
<p>训练速度（每秒每线程训练千个样本数）</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/476e07a80cbf1081c417.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/3534ed0d29362d7ace0d.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/74fc236775492f1b940b.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/0e2e26329f14019d1ec3.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/697f6245baeef7831cab.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/b8dd87534aa2b93914ab.png"/></p>
<p>总体来说，随着模型复杂度提升，AUC提升，logloss降低，逐渐趋向饱和。显然，随着模型复杂度提升，性能变差。</p>
<p>xdeep_fm和auto_int的性能受特征组数量影响严重，随着特征组数增加，性能变差。</p>
<p>模型选择是一个trade off的过程。</p>
<p>首先抛弃“低效低能”的模型，比如group_afm、group_iafm。</p>
<p>效果优先时，优先尝试xdeep_fm、auto_int、fgcnn。</p>
<p>性能优先时，优先尝试dcn、deep_fm 、deep_fm2。</p>
<p>其余模型效果不佳，不推荐使用。</p>
<h1>总结</h1>
<p>在提高CTR正确率的探索过程中，国内外学者和研究人提出了很多模型，也借鉴了注意力机制、残差网络、图像处理等方法。本文研究了CTR任务中的主流模型。</p>
<p>深度CTR模型的核心目标是找出那些对CTR预测有帮助的特征（组合），从这个目标延伸出两个方向，一个是扩充信息量，如历史行为数据<sup>[12]</sup><sup>[13]</sup>、文本信息<sup>[14]</sup>、图片信息<sup>[15]</sup>等，本文并未展开，感兴趣的读者可以阅读相关论文；还有一个是利用现有user、item的特征来构造更多的特征，也就是本文介绍的相关模型。</p>
<p>深度CTR模型说白了就是一个“搭积木”的过程，然而不是每块“积木”都是有效的（如Attention Net），“积木”之间的拼接方式也会影响模型的好坏（如FM Layer和MLP的连接方式）。</p>
<p>本文介绍的模型和提供相关对比实验结果，一方面是希望大家通过实验结果能对当前热门深度CTR模型的性能、效果有一定的认知，进而按需选择合适的模型。另一方面也是希望能够利用现成的“积木”组合出更优秀的模型，把那些对预测有帮助的、隐匿在茫茫特征海洋的组合找出来。当然，授人以鱼不如授人以渔，也希望通过以上模型的分析读者能有所启发，设计出更优秀的“积木”。</p>
<p>我们基于tensorflow实现了deepx_rank_tf（[内部或本地链接已移除]code.[内部链接已移除]），用C++实现了deepx_core（[内部或本地链接已移除]code.[内部链接已移除]）。前者提供了一个benchmark和实验平台，后者为高效的离线训练和在线服务提供了整套的解决方案，目前看一看和搜一搜中的很多排序业务均使用了我们的工具。两个项目均内部开源，希望帮助到大家。</p>
<h1>参考文献</h1>
<ol><li>Factorization Machines</li>
<li>Neural Factorization Machines for Sparse Predictive Analytics</li>
<li>Attentional Factorization Machines: Learning the Weight of Feature Interactions via Attention Networks</li>
<li>Interaction-aware Factorization Machines for Recommender Systems</li>
<li>Wide &amp; Deep Learning for Recommender Systems</li>
<li>DeepFM: A Factorization-Machine based Neural Network for CTR Prediction</li>
<li>Deep &amp; Cross Network for Ad Click Predictions</li>
<li>xDeepFM: Combining Explicit and Implicit Feature Interactions for Recommender Systems</li>
<li>AutoInt: Automatic Feature Interaction Learning via Self-Attentive Neural Networks</li>
<li>Feature Generation by Convolutional Neural Network for Click-Through Rate Prediction</li>
<li>Product-based Neural Networks for User Response Prediction</li>
<li>Deep Interest Network for Click-Through Rate Prediction</li>
<li>Deep Neural Networks for YouTube Recommendations</li>
<li>Deep CTR Prediction in Display Advertising</li>
<li>Deep Crossing: Web-Scale Modeling without Manually Crafted Combinatorial Features</li>
</ol> 
{% endraw %}
