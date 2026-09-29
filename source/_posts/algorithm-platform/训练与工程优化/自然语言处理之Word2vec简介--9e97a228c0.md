---
title: "自然语言处理之Word2vec简介"
date: 2022-04-06 14:00:14
categories:
  - 算法平台
  - 平台工程与评估
---

{% raw %}

<div>
<p>         之所以突然想到去学习相关领域的一些知识，也是因为实际工作中也的确遇到了一些需要自然语言处理技术的场景。从去年开始，因为服务器自维保和精细化运营的目标，我们陆陆续续开始去关注服务器部件信息采集和带内带外日志的收集，目前为止，积累了大量的日志数据，像SEL超过1亿条，SDR每天新增22亿，DMESG每天新增16亿条，其他还有MCE等部件日志我们也在陆续采集。这些日志中的关键字跟故障间有不小关联。例如：我们会根据dmesg输出“rejecting I/O to dead device”去判断“SCSI掉线”，运营他们根据经验认为SEL中类似“IERR”之类的关键字可能跟CPU故障有关系。但这种直接给定关键字毕竟是少数，日志中大量的关键字其实是没用上的。我们就想是不是可以自动识别更多关键字，把关键字跟故障做下相关分析，看能不能对我们的故障告警甚至预警有所启发。所以想要达到这个目的，第一步就要自动提取出关键字。这就是word2vec做的事情。</p>
<p>         自然语言处理说到底就是让机器理解人类的语言，在自然语言处理技术中，其实大量使用了编译原理相关的技术，如词法分析，语法分析，而理解层面则使用了语义理解、机器学习等技术。按照机器学习专家余凯的说法，听与看，说白了就是阿猫阿狗都会的，而只有语言才是人类独有的。如何利用机器学习进行自然语言的深度理解，一直是工业界和学术界关注的焦点。</p>
<p>        这个领域也有很多耳熟能详的应用，如文字翻译如翻译，语言识别类如苹果的siri，更牛逼的如认知计算，代表是的watson，能够让机器理解自然语言，并支持个性化分析。我们公司也很重视这一块，提供了NLP平台——文智中文语义开放平台，上面提供了很多分词、语法分析、文本聚类等很多的API，使用起来也很方便。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/6f225b1aed13057dbf27.png"/><br/><br/></p>
<p>        NLP的技术分类有很多种不同分法，这种分法相对更为被大众所接受，它主要包括三个级别：</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/e655de0813f20ef2683d.png"/></p>
<p> </p>
<p>第一层是词法分析。分词和词性标注很好理解，命名实体识别的任务是识别句子中的特定称谓，如人名、地名等，他们由一个或多个词语组成。词义消歧是根据句子上下文判断每一个或者某些词语的真实含义。</p>
<p>第二层是句法分析。它的目的是将输入句子从序列形式变成树状结构，从而可以捕捉到句子内部词语间的关系。目前研究界有两种主流的句法分析方法，一个是短语结构，一个是依存结构，其中依存结构表示简洁，很容易表示词语间关系，比如动宾关系，时间关系等，所以应用得更多。句法分析得到的句法结构可以帮助上层的语义分析，如机器翻译，文本挖掘等。</p>
<p>第三层是语义分析。它的最终目的是理解句子表达的真实语义。语义角色标注是比较成熟的浅层语义分析技术，给定句子中的一个谓词，语义角色分析的任务是从句子中标注出谓词的施事、受事、时间、地点等参数。举个例子：中午妈妈在家里打我。给定句子中的谓词打，语义角色分析从句子中标注出打这个谓词的施事人妈妈，受事人我，时间中午，地点在家里。</p>
<p> </p>
<p><b>妈妈（施事）中午（时间）在家里（地点）打（谓词）我（受事）</b><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/cf0ddaede29f9812564f.png"/></p>
<p> </p>
<p>        我们讨论的重点其实是词法分析，着重分词这一块儿。学过计算机图形学或信号处理的应该都知道，图像数据其实就是所有单个原始像素点的强度值，把他们编成高纬度丰富的向量数据集。而音频数据就是音频中功率谱密度的强度值，把他们编成向量数据集。所以对于物体或者语音识别之类的任务，我们所需的全部信息都已经存在原始数据中，无论是人还是机器都是以原始数据进行日常的物体或语音识别的。但是对于自然语言来说，通常都把词汇作为离散的单一符号。例如猫，可用id123表示，狗，可用id456表示，这些符号编码毫无规律，无法提供不同词汇间可能存在的关联关系。而且词汇量大，离散符号将进一步导致数据稀疏，使我们在训练统计模型时不得不寻求更多的数据。词汇的向量表示将解决这些问题。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/dc843230912784d22e8a.jpg"/></p>
<p> </p>
<p>        在词的向量化方面有很多工具， 其中最经典的就是word2vec了。它是在2013年年中开源出来的一款可以将词表征为实数值向量的高效工具。word2vec通过训练，可以把对文本内容的处理简化为<i>K</i>维向量空间中的向量运算，而向量空间上的相似度可以用来表示文本语义上的相似度。因此，word2vec输出的词向量可以被用来做很多NLP相关的工作，比如聚类、找同义词、词性分析等等。它主要采用了两类模型：CBOW和skip-gram。后面会详细介绍。</p>
<p>它的优点之一是向量的加法组合运算。官网上有个例子：</p>
<p> </p>
<p><b>vector('Paris') -vector('France') + vector('Italy')≈vector('Rome')</b></p>
<p><b>vector('king') -vector('man') + vector('woman')≈ vector('queen')</b><b>。</b></p>
<p> </p>
<p>另一个优点就是高效性，据作者Tomas Mikolov说在一个优化的单机版本上一天可训练上千亿词。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/c494b44572bba819290e.png"/></p>
<p> </p>
<p>        这里我们插播一点关于作者Tomas Mikolov的八卦。感觉机器学习的圈子也很小，一般都离不开这几个大牛：Hinton、Bengio、Lecun、Ng。而且除了Bengio还坚持在学术界，其他几位都加入了工业界。Hinton本是多伦多大学的教授，是的首席科学家，被誉为神经网络之父。Lecun是纽约大学终身教授，现在是人工智能实验室负责人，他也是CNN卷积神经网络的核心推动者。Bengio是蒙特利尔大学教授，也是机器学习三大神之一，连同Geoff Hinton老先生和YannLeCun燕乐存教授缔造了2006年开始的深度学习的复兴。Ng吴恩达是华裔美国人，任教于斯坦福大学，先后任职于、，现在是首席科学家。word2vec的作者Tomas Mikolov呢，也离不开这几位大神，他的工作很多都参考了Bengio的工作，而且在Bengio的实验室作为交流学者待过一段时间。后又先后在、、呆过，跟Ng做了一段时间同事。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/62fde099d96b428c7325.jpg"/></p>
<p> </p>
<p>        聊完了八卦，我们回过头来开始认真学习下word2vec的基本理论。词向量我们前面提了一下，它包括两种表示方法：</p>
<p><b>“</b><b>话筒” 表示为 [0 0 0 1 0 0 0 0 0 0 0 0 0 0 …]</b></p>
<p><b>“</b><b>麦克”表示为  [0 0 0 0 0 0 0 0 1 0 0 0 0 0 …]</b></p>
<p>第一种one-hot representation中文意思也就是单热点表征，每个词表示为一个很长的向量，维度是整个词汇库的大小，只有对应位置为1，其他都为0.比如，话筒记为3，麦克记为8（假设是从0开始计数）。实现的时候，用hash表给每个词编个号，再配合最大熵、SVM、CRF等算法基本上可以完成NLP领域的各种主流任务。但是它有一个最大的问题，词汇鸿沟，任意两个词之间是孤立的，无法看出他们是否有关联，就连上面的话筒和麦克这种同义词也不能幸免。</p>
<p>第二种方法distributed representation（中文意思是分布式表征）就没有这个问题，它不是第一种方法里面很长很长的向量，而是一个低维实数向量，一般是50、100的维度。它通过词间距离可以判断语义相似度。</p>
<p>如：<strong>[0.792, 0.177, 0.107, 0.109, 0.542, …]</strong></p>
<p>        那么词向量到底是怎么训练得到的呢？这里不得不提到语言模型。到目前为止我了解到的所有训练方法都是在训练语言模型的同时，顺便得到词向量的。</p>
<p>        Word2vec的原理主要涉及到统计语言模型（包括N-gram模型和神经网络语言模型），CBOW模型以及skip-gram模型。下面分别进行介绍：</p>
<p>l  上下文无关模型（context=null）</p>
<p>        先从简单的入手，看一下n-gram的最简单模式，是n-gram模型中n=1的特殊情形，也称unigram model（一元文法统计模型），它仅考虑当前词本身概率，不考虑该词所处上下文，仅依赖词频统计。实际应用中，常被用于一些商用语音识别系统中。</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/3f7c0a05754f4214a0d4.jpg"/></p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/bf34ec8972f789801391.jpg"/></p>
<p></p>
<p>如：<b>I see the red house near to the lake</b></p>
<p>假如词汇库只有这句话，那么N=9，则</p>
<p><b>P(I)=1/ N=1/9</b></p>
<p><b>P(the)=2/ N=2/9</b></p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/9f89078087b663ecf849.png"/></p>
<p> </p>
<p>l  N-gram模型</p>
<p>由于上下文无关模型应用比较少，所以我们再来看下考虑上下文的情况，n-gram模型。n-gram顾名思义，就是说根据前面n个单词，给出某个单词的出现概率。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/81cd0d8b06d01aa7ae5d.png"/></p>
<p> </p>
<p>如：<b>I see the red house</b></p>
<p>当N=2时</p>
<p><b>P(I,see,the,red,house)</b><b>≈P(I|&lt;s&gt;,&lt;s&gt;)*P(see|&lt;s&gt;,I)*P(the|I,see)*P(red|see,the)*P(house|the,red)</b></p>
<p>整个话的出现概率就是：每个单词概率的乘积。</p>
<p>n-gram优点：</p>
<p>（1）包含了前n个词所能提供的全部信息，这些信息对当前词具有很强约束力</p>
<p>（2）只看n个词，不是所有词，模型效率较高</p>
<p>n-gram问题：</p>
<p>（1）无法建模更远的关系：因为语料不足导致无法训练更高阶的语言模型。一般用Bigram和Trigram较多，更高阶的可信度也大打折扣。</p>
<p>（2）无法建模词之间的相似度。如：</p>
<p><b>The cat is walking in the bedroom</b></p>
<p><b>A dog was running in a room</b></p>
<p>        这两句话其实是类似的，如果有一种方法，能知道The和a相似，cat和dog相似等等，并且会给相似的词类似的语言模型概率，那么第二句话也可以得到高概率。</p>
<p>（3）训练语料里有些n元组没出现过，条件概率为0，导致计算一整句话的概率为0.</p>
<p></p>
<p>l  神经网络语言模型（NNLM）</p>
<p>        我们要介绍的第三种语言模型，是前面提到的大牛Bengio在2003年提出的神经网络语言模型NNLM，它就解决了上述问题。这个模型的目的是根据已知的n-1个词，预测下一个词Wt。</p>
<p>如图所示：</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/4b9b6b95389151436af9.png"/></p>
<p> </p>
<p>模型公式：<b>Y=b+wx+U*tanh(d+Hx)</b></p>
<p> </p>
<p>         我们先不考虑虚线，红框框里面就是个三层前向神经网络，第一层是输入层，它将n-1个向量拼接m*（n-1）维向量X；然后X作为第二层隐藏层的输入，在上面做一个线性变换，在用双曲正切作为激活函数；最后在输出层使用softmax激活函数做归一化，将概率都归一化到0到1，得到v个概率值，每个概率yi表示输出为单词i的概率。</p>
<p>         图中虚线是输入X到输出Y的直连边，bengio觉得它虽然不能提升模型的效果，但是可以少一半迭代次数。当然也可以不用直连边，将w置0即可。</p>
<p>         最后在运用随机梯度下降SGD算法把模型进行优化，得到其中的参数。这里X也是参数，也是需要优化的，优化结束之后词向量就有了，语言模型也有了。</p>
<p>缺点：</p>
<p>         NNLM的训练太慢了。即便是在百万量级的数据集上，即便是借助了40个CPU进行训练，NNLM也需要耗时数周才能给出一个稍微靠谱的解来。显然，对于现在动辄上千万甚至上亿的真实语料库，训练一个NNLM模型几乎是一个impossible mission。</p>
<p> </p>
<p>l  Word2vec</p>
<p>         看到NNLM这么慢，那个Mikolov站了出来。他注意到，原始的NNLM模型的训练其实可以拆分成两个步骤：</p>
<p>1.用一个简单模型训练出连续的词向量；</p>
<p>2.基于词向量的表达，训练一个连续的Ngram神经网络模型。</p>
<p>         而NNLM模型的计算瓶颈主要是在第二步。所以为了提高速度，mikolov去掉了隐层，将映射层和输出层直连；并且忽略上下文序列信息，不管顺序；为了更好的分词把下文的信息也考虑进去。这样做后，不仅减少了计算量，同时效果也并不差。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/fa7d5207a4bcf4e8d3e5.png"/></p>
<p> </p>
<p>         Word2vec包括两种模型，一个CBOW（全称是continuous bag of words，中文翻译为词袋模型），意思是把单词放到一个袋子里，不考虑它的顺序，因为它的顺序不影响它的映射关系。另一个是Skip-gram（全称是continuous skip gram，中文翻译为连续跳词模型），它跟cbow类似的，区别在于cbow是通过上下文预测单词，skip-gram是通过单词预测上下文。</p>
<p>例如：</p>
<p><b>the quick brown fox jumped over the lazy dog</b></p>
<p><b>CBOW</b><b>：([the, brown], quick), ([quick, fox], brown), ([brown, jumped], fox), ...</b></p>
<p><b>Skip-gram</b><b>：(quick, the), (quick, brown), (brown, quick), (brown, fox), ...</b></p>
<p> </p>
<p>         mikolov用开源词库<b>LDC</b>中的数据集把这两种模型跟NNLM，RNNLM（循环神经网络语言模型）做了对比，声称CBOW在语法精确度上是最高的，达到64%，语义精确度略高于NNLM。Skip-gram在语义精确度上远远高于其他模型，语法精确度略低于CBOW，但也高于NNLM和RNNLM。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/3f55395077eb16532e07.jpg"/></p>
<p> </p>
<p>听起来是不是很厉害，但是实践是检验真理的唯一标准。所以我们自己来动手试试看。</p>
<p> </p>
<table><tbody><tr><td>
<p>版本</p>
</td>
<td>
<p>地址</p>
</td>
<td>
<p>CBOW</p>
</td>
<td>
<p>Skip-gram</p>
</td>
</tr><tr><td>
<p>C</p>
</td>
<td>
<p>http://word2vec.googlecode.com/svn/trunk/</p>
</td>
<td>
<p>HS，NEG</p>
</td>
<td>
<p>HS，NEG</p>
</td>
</tr><tr><td>
<p>python</p>
</td>
<td>
<p>http://radimrehurek.com/gensim/</p>
</td>
<td></td>
<td>
<p>HS</p>
</td>
</tr><tr><td>
<p>java</p>
</td>
<td>
<p>https://github.com/ansjsun/Word2VEC_java</p>
</td>
<td>
<p>HS</p>
</td>
<td>
<p>HS</p>
</td>
</tr><tr><td>
<p>C++</p>
</td>
<td>
<p>https://github.com/jdeng/word2vec</p>
</td>
<td></td>
<td></td>
</tr></tbody></table><p> </p>
<p>         源代码的话最经典但还是提供的C语言版本的word2vec，支持也最好。也有对词向量感兴趣的牛人开发的python，java，c++版本的，可能支持差一些。我们先把源代码下载下来，之前官网上有下载，后来被删掉了，不过万能的上面可以找到。然后根据自己需求修改makefile，不同系统可能需要修改一下编译选项。有些系统可能还需要修改相关的C语言头文件，具体可以网上搜索。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/a4d150a8ba0636bf21da.png"/></p>
<p> </p>
<p>         这里的训练文件text8是已经分好词的文本语料（一般用空格或者tab隔开都可以），中文分词工具的话可以用jieba分词工具。将分好词的训练语料进行训练，输入命令和其中各项参数如图所示。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/b151f2a2e647c70cca82.png"/></p>
<p> </p>
<p>         训练结束，我们看下结果，训练数据集中有7万个词汇，1600多万单词。我们输入单词china测试一下，列出了cosine距离最近的一些单词和对应的距离。你可能会说为什么距离越大的越在前面，这是因为cosine距离也就是余弦相似度，是越大越相似啊。总体来说效果还是挺好的。</p>
<p>         那我们再用自己的数据试试看呢。我随机选了10W行SEL原始数据，类似下面这样的。当然它原生就是空格分隔的</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/d81a376cdc795a81aee7.png"/></p>
<p> </p>
<p>         可以看到词汇量不多，只有113个，单词总数60万个，随便输入一个单词，当然一定要是里面存在的单词，Memory，可以看到列出来了一些相关的词汇，其中相关度最高的两个甚至达到98%以上的Correctable和ECCAsserted，Correctable是表示内存可矫正，ECC表示ECC校验，他们的确跟内存有很强相关性。但是后面几个单词什么Watts之类的，其实是电源的瓦特，这些相关性就低了，分析了下，一个是因为数据量的确小而且重复率太高了，二个也是因为SEL数据本身的关系，就是系统输出的日志数据嘛，毕竟不能跟人类原生产生的语言的复杂度比，单词还是太单调了。所以我们后面还是打算一个扩大数据集，二个数据源多样性选取。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/3578e00b8ca2b3b2c84f.png"/></p>
<p> </p>
<p>         这些单词太多，难道要一个一个去查看每两个单词之间的距离或者说近似程度吗？可以一目了然吗？这就涉及到可视化工具。例如python中可以用sklearn, matplotlib,scipy这些包，然后将单词向量压缩到二维或者三维展示出现。如图所示，就可以形象看出单词间距离。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/d67cdcdbb42cb0341e00.jpg"/></p>
<p> </p>
<p>         这是一个实验图，可以看到下面he,it,she这些人称代词靠得很近。上面数字类one、two、seven、million之类的还是靠得很近的。</p>
<p> </p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/6604f4e9f98410d4054c.jpg"/></p>
<p> </p>
<p>         对于我们的应用场景来说有什么启发呢？我想目前可以有下面三类应用：</p>
<p>way1.自动分词：日志关键字提取，相似度分析</p>
<p>way2.文本聚类：关键词分类，如部件日志分类</p>
<p>way3.故障相关性分析甚至故障预测，结合文本聚类+分类算法</p>
<p>持续探索……</p>
<p> </p>
</div> 
{% endraw %}
