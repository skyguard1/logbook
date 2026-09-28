---
title: "短视频分类进化：从LR到LSTM"
date: 2022-04-24 09:53:19
categories:
  - deep-learning
---

<div class="Section1" style="layout-grid: 15.6pt;">
<p align="center" style="text-align: center; text-indent: 36.0pt;"></p>
<h2 style="text-indent: 9.95pt;"><span style="font-family: 宋体;">前言</span></h2>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">由于深度学习近年来在图像领域的巨大成功，其他领域如语音、</span><span lang="EN-US">NLP</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">等领域的研究也逐渐被深度学习所统治，而且其结果几乎都是</span><span lang="EN-US"> "state of the art"</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。为了跟上这波趋势，我使用深度学习中的</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">网络对短视频分类进行了尝试，并与目前使用的传统分类方法（</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">）进行对比，的确取得了更好的效果。</span></p>
<h2 style="text-indent: 9.95pt;"><span style="font-family: 宋体;">短视频分类任务介绍</span></h2>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">对我们浏览器来说，短视频内容都是合作方提供，拿不到视频内容，只有视频链接和视频标题。所以如果想通过机器学习的方法对短视频进行分类，能拿到的信息只有视频的标题。幸运的是，短视频基本都是标题党，标题基本也包含了视频内的主要信息，如下图所示：</span></p>
<p align="center" style="text-align: center; text-indent: 24.0pt;"><span lang="EN-US" style=""></span></p>
<p align="center" style="text-align: center; text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">图</span><span lang="EN-US">1</span></p>
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">我们的短视频分类任务包括两部分：</span></p>
<p style="margin-left: 39.0pt; text-indent: -18.0pt;"><span lang="EN-US">1）</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">从上报的所有视频站点标题里识别出短视频，这是一个二分类的问题。</span></p>
<p style="margin-left: 39.0pt; text-indent: -18.0pt;"><span lang="EN-US">2）</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">对识别出的短视频，需要进行类别的识别。目前我们运营主推的短视频包含</span><span lang="EN-US">4</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">类：娱乐、生活、搞笑、奇闻，是一个</span><span lang="EN-US">4</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">分类的任务。</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">另一方面的问题是整个任务的训练样本构造。由于人力有限，没有专门的同事来对短视频及短视频的类别进行标注，只有合作方提供的一些带标注的样本，累计差不多</span><span lang="EN-US">200</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">条。这么少的样本量来训练机器学习模型基本上会过拟合。所以我写了个爬虫抓取了合作方之一的的站点的所有短视频及其分类信息，去除不需要的类别，剩下的就可以加入到有类别的短视频中。这样处理后，有标注的短视频总量为</span><span lang="EN-US">16519</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。在从上报的视频站点标题里抽样本部分非短视频的样本，两部分加起来样本总量为</span><span lang="EN-US">86040</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。另外，从爱奇艺、拿了最近</span><span lang="EN-US">1</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">个月内标注好的热门短视频和帅选的一些非短视频标题作为新测试集，共</span><span lang="EN-US">1000</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">条，用来测试模型的泛化能力。</span></p>
<h2 style="text-indent: 9.95pt;"><span style="font-family: 宋体;">传统机器学习方法</span></h2>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">对文本分类来说，由于维度高，特征也高度稀疏，传统机器学习方法中效果较好的就是</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">和线性</span><span lang="EN-US">SVM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。对标题的建模方法是采用经典的词袋模型，先对标题进行分词，去除停用词和其他词频较小的词，词库大小为</span><span lang="EN-US">20000</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，对词采用</span><span lang="EN-US">one-hot</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">向量化。</span></p>
<p style="margin-left: 39.0pt; text-indent: -18.0pt;"><span lang="EN-US" style="font-size: 14.0pt; font-family: 黑体;">1.<span style="font: 7.0pt &#39;Times New Roman&#39;;"> </span></span><span style="font-size: 14.0pt; font-family: 黑体;">识别短视频二分类</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">主要尝试了</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">和线性</span><span lang="EN-US">SVM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">模型，训练时按</span><span lang="EN-US">4:1</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">来切分训练集与测试集，效果如下：</span></p>
<div align="center">
<table border="1" class="GridTable1LightAccent1" style="border-collapse: collapse; border: none; width: 461px;"><tbody><tr><td style="width: 74px; border-width: 1pt 1pt 1.5pt; border-style: solid; border-color: #bdd6ee #bdd6ee #9cc2e5; border-image: initial; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">模型</span></p>
</td>
<td style="width: 201px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">样本中测试集准确率</span></p>
</td>
<td style="width: 138px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">新测试集准确率</span></p>
</td>
</tr><tr><td style="width: 74px; border-right: 1pt solid #bdd6ee; border-bottom: 1pt solid #bdd6ee; border-left: 1pt solid #bdd6ee; border-image: initial; border-top: none; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><b><span lang="EN-US">LR</span></b></p>
</td>
<td style="width: 201px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.960</span></p>
</td>
<td style="width: 138px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.876</span></p>
</td>
</tr><tr><td style="width: 74px; border-right: 1pt solid #bdd6ee; border-bottom: 1pt solid #bdd6ee; border-left: 1pt solid #bdd6ee; border-image: initial; border-top: none; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><b><span lang="EN-US">SVM</span></b></p>
</td>
<td style="width: 201px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.966</span></p>
</td>
<td style="width: 138px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.852</span></p>
</td>
</tr></tbody></table>

<p align="center" style="text-align: center; text-indent: 21.0pt;"><span style="font-size: 10.5pt; font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">表</span><span lang="EN-US" style="font-size: 10.5pt;">1</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">可以看到，</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">和</span><span lang="EN-US">SVM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">在训练集上都已达到了很高的准确率，而且相差不大。但是，在新的测试集上，准确率有明显的下降。这个主要是采用</span><span lang="EN-US">one-hot</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">建模方式的固有缺陷。新测试集上出现了不少没有在训练集上出现的新词，这些词不能映射到已有的词典里就只能丢弃，而原来的模型也没有学到这些信息，所以会降低模型的泛化能力。</span></p>
<p style="margin-left: 39.0pt; text-indent: -18.0pt;"><span lang="EN-US" style="font-size: 14.0pt; font-family: 黑体;">2.<span style="font: 7.0pt &#39;Times New Roman&#39;;"> </span></span><span style="font-size: 14.0pt; font-family: 黑体;">短视频多分类</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">短视频目前共分</span><span lang="EN-US">4</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">类，每类的数量为：奇闻</span><span lang="EN-US">: 6720</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，生活</span><span lang="EN-US">: 2520</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，搞笑</span><span lang="EN-US">: 3736</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，娱乐</span><span lang="EN-US">: 3543</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。新测试集中主要是奇闻和娱乐，其他类别太少，不参与评估。奇闻数量为</span><span lang="EN-US">694</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，娱乐数量为</span><span lang="EN-US">90</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。多分类的分类器是</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，效果如下：</span></p>
<table border="1" class="GridTable1LightAccent1" style="border-collapse: collapse; border: none; width: 646px;"><tbody><tr><td style="width: 61px; border-width: 1pt 1pt 1.5pt; border-style: solid; border-color: #bdd6ee #bdd6ee #9cc2e5; border-image: initial; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">模型</span></p>
</td>
<td style="width: 83px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">类别</span></p>
</td>
<td style="width: 117px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">样本中测试集准确率</span></p>
</td>
<td style="width: 110px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">样本中测试集召回率</span></p>
</td>
<td style="width: 94px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">新测试集准确率</span></p>
</td>
<td style="width: 85px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">新测试集召回率</span></p>
</td>
</tr><tr><td rowspan="5" style="width: 61px; border-right: 1pt solid #bdd6ee; border-bottom: 1pt solid #bdd6ee; border-left: 1pt solid #bdd6ee; border-image: initial; border-top: none; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><b><span lang="EN-US">LR</span></b></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">总体</span></p>
</td>
<td style="width: 117px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.88</span></p>
</td>
<td style="width: 110px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
<td style="width: 94px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.81</span></p>
</td>
<td style="width: 85px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
</tr><tr><td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">奇闻</span></p>
</td>
<td style="width: 117px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.89</span></p>
</td>
<td style="width: 110px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.89</span></p>
</td>
<td style="width: 94px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.96</span></p>
</td>
<td style="width: 85px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.86</span></p>
</td>
</tr><tr><td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">生活</span></p>
</td>
<td style="width: 117px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.87</span></p>
</td>
<td style="width: 110px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.94</span></p>
</td>
<td style="width: 94px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
<td style="width: 85px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
</tr><tr><td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">搞笑</span></p>
</td>
<td style="width: 117px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.81</span></p>
</td>
<td style="width: 110px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.70</span></p>
</td>
<td style="width: 94px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
<td style="width: 85px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
</tr><tr><td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">娱乐</span></p>
</td>
<td style="width: 117px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.92</span></p>
</td>
<td style="width: 110px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.97</span></p>
</td>
<td style="width: 94px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.63</span></p>
</td>
<td style="width: 85px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.79</span></p>
</td>
</tr></tbody></table><p align="center" style="text-align: center; text-indent: 18.0pt;"><span style="font-size: 9.0pt; font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">表</span><span lang="EN-US" style="font-size: 9.0pt;">2</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">可以看到，对这个多分类问题，</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的总体准确率还不错。但在新测试集中，娱乐的分类准确率很差。这个主要是新测试集中娱乐的样本出现了不少新明星（娱乐类短视频就是明星相关），所以基于词袋模型的</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">就有点无能为力了。而奇闻类的样本则取得了优于训练样本的结果。新测试集中的娱乐类样本相对有点极端，模型上线的时候每天进行一次训练能一定程度上降低这个问题的影响。</span></p>
<h2 style="text-indent: 9.95pt;"><span style="font-family: 宋体;">使用</span><span lang="EN-US">LSTM</span><span style="font-family: 宋体;">网络分类</span></h2>
<p style="text-indent: 28.0pt;"><span lang="EN-US" style="font-size: 14.0pt; font-family: 黑体;">1.LSTM</span><span style="font-size: 14.0pt; font-family: 黑体;">简介</span></p>
<p style="text-indent: 24.0pt;"><span lang="EN-US">RNN(Recurrent Neural Networks)</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">是一种包含循环结构的神经网络，主要用来处理连续的序列问题，比如股票预测、机器翻译、语音识别等。它的问题主要是当网络变深变大后会带来梯度消失或梯度爆炸的问题，非常难以训练。而</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">（</span><span lang="EN-US">Long-Short Term Memory</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">）是一种改进的</span><span lang="EN-US">RNN</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">网络结果，部分上解决了传统</span><span lang="EN-US">RNN</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">网络难以训练的问题。目前，</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">在自然语言处理等领域已经有了很多成功的应用，如文本分类、机器翻译等。关于</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">网络的具体介绍推荐看这篇文章：</span><span lang="EN-US"><a href="http://colah.github.io/posts/2015-08-Understanding-LSTMs/">http://colah.github.io/posts/2015-08-Understanding-LSTMs/</a></span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。</span></p>
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="font-size: 14.0pt; font-family: 黑体;">2.</span><span style="font-size: 14.0pt; font-family: 黑体;">训练词向量</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">由于原始样本只有</span><span lang="EN-US">86040</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">条，单纯用这么少的数据量训练词向量。由于训练词向量并不要求对样本进行标注，所以词向量的训练并不受这批样本的影响，原则上肯定是数据量越大越好。由于此向量能很好地反映词的相关性，我刷选了一天可能要预测的视频站点标题加入到原有的短视频样本中，使样本量扩展到</span><span lang="EN-US">80w+</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">（如果上分布式训练可以用更大的样本集）。由于在</span><span lang="EN-US">window 7</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">上进行开发，就用</span><span lang="EN-US">python</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">版的</span><span lang="EN-US">wrod2vec</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">工具</span><span lang="EN-US">gensim</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">来训练词向量。词向量维数设置为</span><span lang="EN-US">100</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，训练出来的词向量词典大小为</span><span lang="EN-US">38053</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。</span><span lang="EN-US">gensim</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">训练词向量的代码特别简单：</span></p>
<div class="km_insert_code">
<pre><code>model = gensim.models.Word2Vec(sentences, size=100,
        window=5, min_count=3, sg=1,  max_vocab_size=vocabulary_size)
model.wv.save_word2vec_format(wrod2vec,
                 "word2vec/vocabulary",binary=False)
</code></pre>

<p>&nbsp;<span lang="EN-US">3.<span style="font: 7.0pt &#39;Times New Roman&#39;;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </span></span><span style="font-size: 14.0pt; font-family: 黑体;">识别短视频二分类</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">从上面的实践可以看到，使用线性模型（</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">）就能对短视频分类取得比较好的效果，复杂的非线性模型（如</span><span lang="EN-US">GBDT</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">、</span><span lang="EN-US">SVM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">）效果可能还不如</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。因此对短视频分类来说，由于特征是高维稀疏的，所以是一个偏线性的模型。在异乡文献中对文本分类的实践也一般都是简单模型反而能取得比较好的效果。所以我在使用</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">网络对短视频进行分类时，也只设计了一个隐含层，输入层就是标题分词后</span><span lang="EN-US">word embedding</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的结果，输出层采用全连接的</span><span lang="EN-US">softmax</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">回归进行分类。另一方面也是由于样本量特别少，设计过于复杂的网络结果也很容易造成过拟合。网络结构如下：</span></p>
<p style="text-indent: 21pt;"></p>
<p align="center" style="text-align: center;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">图</span><span lang="EN-US">3</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">由于数据量较少，直接用公司办公机进行训练，训练框架采用</span><span lang="EN-US">TensorFlow 1.2 GPU</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">版本。公司的办公机配置还可以，</span><span lang="EN-US">GPU</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">是</span><span lang="EN-US">GTX660,2G</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">显存。</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">对于上述</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">网络结构，隐含层设置为</span><span lang="EN-US">128</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，序列长度设置为</span><span lang="EN-US">15</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">层</span><span lang="EN-US">dropout</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的值设置为</span><span lang="EN-US">0.5</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。其中序列长度原则上应该选分词后的标题的最大词数。经统计发现，词数最大是</span><span lang="EN-US">33</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，词数小于</span><span lang="EN-US">15</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的达到了</span><span lang="EN-US">0.99</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。但是，随着序列长度的增大，训练时间会变得越长，而且由于样本量较少，过大的序列长度也容易引起过拟合。所以，综合上述考虑就选择序列长度为</span><span lang="EN-US">15.</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">相关代码如下：</span></p>
<div class="km_insert_code">
<pre><code># Network Parameters
n_input = 100
n_steps = seq_len# timesteps
n_hidden = 128 # hidden layer num of features
n_classes = 2 #
#tf Graph input
x = tf.placeholder(tf.float32, [None, n_steps, n_input])
y = tf.placeholder(tf.float32, [None, n_classes])
# Define weights
weights = {
'out' : tf.Variable(tf.random_normal([n_hidden, n_classes]))
}
biases = {
'out': tf.Variable(tf.random_normal([n_classes]))
}

defRNN(x, weights, biases, keep_prob):
    # Unstack to get a list of 'n_steps' tensors of shape (batch_size, n_input)
    x = tf.unstack(x, n_steps, 1)
    # Define a lstm cell with tensorflow
    lstm_cell = rnn.BasicLSTMCell(n_hidden, forget_bias=1.0)
    # Get lstm cell output
    outputs, states = rnn.static_rnn(lstm_cell, x, dtype=tf.float32)
    # Linear activation, using rnn inner loop last output
    lstm_out = tf.matmul(outputs[-1], weights['out']) + biases['out']
    out_drop = tf.nn.dropout(lstm_out, keep_prob)
    return out_drop

keep_prob = tf.placeholder(tf.float32)
pred = RNN(x, weights, biases, keep_prob)
# Define loss and optimizer
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
# Evaluate model
correct_pred = tf.equal(tf.argmax(pred,1), tf.argmax(y,1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))&nbsp;</code></pre>

<p style="text-indent: 0cm;"><span lang="EN-US">&nbsp; &nbsp; &nbsp;&nbsp;</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">训练结果与</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">做了对比如下：</span></p>
<div align="center">
<table border="1" class="PlainTable1" style="border-collapse: collapse; border: none; width: 461px;"><tbody><tr><td style="width: 79px; border: 1pt solid #bfbfbf; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">模型</span></p>
</td>
<td style="width: 196px; border-top: 1pt solid #bfbfbf; border-right: 1pt solid #bfbfbf; border-bottom: 1pt solid #bfbfbf; border-image: initial; border-left: none; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">样本中测试集准确率</span></p>
</td>
<td style="width: 138px; border-top: 1pt solid #bfbfbf; border-right: 1pt solid #bfbfbf; border-bottom: 1pt solid #bfbfbf; border-image: initial; border-left: none; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">新测试集准确率</span></p>
</td>
</tr><tr><td style="width: 79px; border-right: 1pt solid #bfbfbf; border-bottom: 1pt solid #bfbfbf; border-left: 1pt solid #bfbfbf; border-image: initial; border-top: none; background: #f2f2f2; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><b><span lang="EN-US">LR</span></b></p>
</td>
<td style="width: 196px; border-top: none; border-left: none; border-bottom: 1pt solid #bfbfbf; border-right: 1pt solid #bfbfbf; background: #f2f2f2; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.960</span></p>
</td>
<td style="width: 138px; border-top: none; border-left: none; border-bottom: 1pt solid #bfbfbf; border-right: 1pt solid #bfbfbf; background: #f2f2f2; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.876</span></p>
</td>
</tr><tr><td style="width: 79px; border-right: 1pt solid #bfbfbf; border-bottom: 1pt solid #bfbfbf; border-left: 1pt solid #bfbfbf; border-image: initial; border-top: none; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><b><span lang="EN-US">LSTM</span></b></p>
</td>
<td style="width: 196px; border-top: none; border-left: none; border-bottom: 1pt solid #bfbfbf; border-right: 1pt solid #bfbfbf; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.974</span></p>
</td>
<td style="width: 138px; border-top: none; border-left: none; border-bottom: 1pt solid #bfbfbf; border-right: 1pt solid #bfbfbf; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.929</span></p>
</td>
</tr></tbody></table>

<p align="center" style="text-align: center; text-indent: 0cm;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">表</span><span lang="EN-US">3</span></p>
<p style="text-indent: 21.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">从对比可以看到，</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">在样本测试集中准确率提高了</span><span lang="EN-US">0.014</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，而且在新测试集中仍然表现了较好的性能，比</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">具有更好的泛化能力，准确率提高了</span><span lang="EN-US">0.053</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">。这个提升个人觉得除了</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">模型本身的能力外，还有就是因为训练词向量时采用了更大的数据集，词库也更大。这就使得原来没有在有标注的样本中出现过的词但是在词向量训练集中出现的词的信息没有丢失，这些词在新测试集中出现时能对分类发挥作用，但是原来使用基于词袋模型的建模方法就只能丢弃这个词。举个例子，词向量结果中“李易峰”相似度最高的前三个词为：</span></p>
<p style="text-indent: 0cm;"><span lang="EN-US">('</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">陈伟霆</span><span lang="EN-US">', 0.816763162612915), ('</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">赵丽颖</span><span lang="EN-US">', 0.8164128661155701), ('</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">杨洋</span><span lang="EN-US">', 0.7692270874977112)</span></p>
<p style="text-indent: 0cm;"><span lang="EN-US">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">如果</span><span lang="EN-US">“</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">陈伟霆</span><span lang="EN-US">”</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">并没有出现在有标注的短视频标题中，但是出现在新测试集里，它会发挥与原来</span><span lang="EN-US">“</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">李易峰</span><span lang="EN-US">”</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">在有标注的短视频标题中类似的作用。</span></p>
<p style="margin-left: 39.0pt; text-indent: -18.0pt;"><span lang="EN-US" style="font-size: 14.0pt; font-family: 黑体;">4.<span style="font: 7.0pt &#39;Times New Roman&#39;;"> </span></span><span style="font-size: 14.0pt; font-family: 黑体;">短视频多分类</span></p>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">对于</span><span lang="EN-US">4</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">分类的短视频问题，</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的网络结构跟上述二分类的一样。开始时直接对样本进行训练。整体准确率为</span><span lang="EN-US">0.86</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，比</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的效果（</span><span lang="EN-US">0.88</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">）还差。后来发现</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">进行多分类时对类别平衡具有一定的敏感性，于是对样本中类别少的类进行过采样再进行训练，分类效果就有了很大的提升：</span><span lang="EN-US">&nbsp;</span></p>
<table border="1" class="GridTable1LightAccent1" style="border-collapse: collapse; border: none; width: 646px;"><tbody><tr><td style="width: 88px; border-width: 1pt 1pt 1.5pt; border-style: solid; border-color: #bdd6ee #bdd6ee #9cc2e5; border-image: initial; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">模型</span></p>
</td>
<td style="width: 81px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">类别</span></p>
</td>
<td style="width: 108px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">样本中测试集准确率</span></p>
</td>
<td style="width: 101px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">样本中测试集召回率</span></p>
</td>
<td style="width: 89px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">新测试集准确率</span></p>
</td>
<td style="width: 83px; border-top: 1pt solid #bdd6ee; border-left: none; border-bottom: 1.5pt solid #9cc2e5; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p class="a"><span style="font-family: 宋体;">新测试集召回率</span></p>
</td>
</tr><tr><td rowspan="5" style="width: 88px; border-right: 1pt solid #bdd6ee; border-bottom: 1pt solid #bdd6ee; border-left: 1pt solid #bdd6ee; border-image: initial; border-top: none; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><b><span lang="EN-US">LR</span></b></p>
</td>
<td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">总体</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.88</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.81</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
</tr><tr><td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">奇闻</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.89</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.89</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.96</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.86</span></p>
</td>
</tr><tr><td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">生活</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.87</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.94</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
</tr><tr><td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">搞笑</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.81</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.70</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
</tr><tr><td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">娱乐</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.92</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.97</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.63</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">0.79</span></p>
</td>
</tr><tr><td rowspan="5" style="width: 88px; border-right: 1pt solid #bdd6ee; border-bottom: 1pt solid #bdd6ee; border-left: 1pt solid #bdd6ee; border-image: initial; border-top: none; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><b><span lang="EN-US">LSTM</span></b></p>
</td>
<td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">总体</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.95</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.84</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US">&nbsp;</span></p>
</td>
</tr><tr><td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">奇闻</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.93</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.92</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.96</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.87</span></p>
</td>
</tr><tr><td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">生活</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.96</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.98</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">&nbsp;</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">&nbsp;</span></p>
</td>
</tr><tr><td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">搞笑</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.92</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.92</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">&nbsp;</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">&nbsp;</span></p>
</td>
</tr><tr><td style="width: 81px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">娱乐</span></p>
</td>
<td style="width: 108px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.97</span></p>
</td>
<td style="width: 101px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.97</span></p>
</td>
<td style="width: 89px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.75</span></p>
</td>
<td style="width: 83px; border-top: none; border-left: none; border-bottom: 1pt solid #bdd6ee; border-right: 1pt solid #bdd6ee; padding: 0cm 5.4pt;">
<p style="text-indent: 24.0pt;"><span lang="EN-US" style="color: red;">0.89</span></p>
</td>
</tr></tbody></table><p align="center" style="text-align: center; text-indent: 0cm;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">表</span><span lang="EN-US">4</span></p>
<p style="text-indent: 0cm;"><span lang="EN-US">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">跟二分类的结果一样，</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的效果对比</span><span lang="EN-US">LR</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的结果也有了一定的提升。从对比可以看到，</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">在样本测试集中准确率提高了</span><span lang="EN-US">0.07</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，而且在新测试集中仍然表现了较好的性能，总体准确率提升了</span><span lang="EN-US">0.03</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，其中娱乐类提升较大，从</span><span lang="EN-US">0.66</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">提升到了</span><span lang="EN-US">0.75</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，而且也提升了召回率。新测试集中总体准确率看起来提升不大明显是因为新测试集的样本分布太不均衡（奇闻数量为</span><span lang="EN-US">694</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，娱乐数量为</span><span lang="EN-US">90</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">），在实际数据中的类别分布并没有这么不平衡，所以实际效果肯定有更大的提升。这个提升的原因分析与二分类的结果类似。</span></p>
<h2 style="text-indent: 9.95pt;"><span style="font-family: 宋体;">总结</span></h2>
<p style="text-indent: 24.0pt;"><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">从短视频分类的实践中，可以看到</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">在文本分类中的确能取得比传统分类模型更好的效果。虽然在应用中的</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">网络的深度都不太深（只有</span><span lang="EN-US">1</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">层隐层），但是取得的效果也已经非常不错。当然，如果有更多有标注的样本，设计更复杂的网络肯定能取得更好的效果。另一方面，由于深度学习的黑盒特性，调参的确是个苦力活，比如</span><span lang="EN-US">LSTM</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">网络的层数、序列长度、</span><span lang="EN-US">dropout</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的设置、训练事</span><span lang="EN-US">batch_size</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">的大小等等，这些参数都有可能对结果产生很大的影响。对应深度学习调参，需要多看</span><span lang="EN-US">paper</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">，多实践，目前还是缺乏有效理论指导。</span></p>
<p style="text-indent: 0cm;"><span lang="EN-US">PS</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">：感谢</span><span lang="EN-US">calvinlai</span><span style="font-family: &#39;微软雅黑&#39;,&#39;sans-serif&#39;;">对本文工作的指导</span><span lang="EN-US">~<a name="_GoBack"></a></span></p>
<p style="text-indent: 0cm;"><span lang="EN-US">&nbsp;</span></p>
<p style="text-indent: 0cm;"><span lang="EN-US">&nbsp;</span></p>
