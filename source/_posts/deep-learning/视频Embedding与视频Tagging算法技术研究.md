---
title: "视频Embedding与视频Tagging算法技术研究"
date: 2022-04-18 14:33:26
categories:
  - deep-learning
---

<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<div style="margin:0px 0px 0px 10px;padding:0px;vertical-align:middle;display:inline-block;color:#8091a5;font-size:15px;line-height:1.3;position:relative;height:20px;width:22px;"></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">视频Embeding的目的是将视频表示为一个定长的向量，该向量需要满足以下两个特性：</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<ol style="margin:10px 0px 10px 25px;padding:0px;text-indent:0px;"><li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">表示性：Embedding向量能够抽象表达视频的完整信息，不出现明显的遗漏；</p>
</li>
<li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">平滑性：Embedding向量之间的距离和视频之间的相似度呈正相关（最好是线性相关）。</p>
</li>
</ol></div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">通常可以通过改进模型结构来增强Embedding向量对视频的标示性，通过改进训练方式和改善训练数据集来提高Embedding的平滑性。视频Embedding的难点在于如何将多帧的信息有效的融合成整个视频的信息（Video Aggregation）。当前常见的Video Aggregation算法大体可归为两类：</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<ol style="margin:10px 0px 10px 25px;padding:0px;text-indent:0px;"><li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">时间序列融合模型（如RNN、LSTM、GRU等）</p>
</li>
<li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">基于可训练的池化模型（Learnable Pooling）包含NetVLAD、ActionVLAD等算法。</p>
</li>
</ol></div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin: 0px 0px 1em; padding: 0px; line-height: 1.3;"></p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">  基于Learnable Pooling的模型无法区分不同输入帧的发生时序，所以理论上具有较弱的动作识别能力，但是实验表明，至少在现有的模型复杂度的条件下，视频帧顺序并不能给动作识别带来明显的性能增益（参见<a href="https://arxiv.org/abs/1803.10628https://arxiv.org/abs/1803.10628" style="text-decoration:none;color:#6293e2;">Video Representation Learning Using Discriminative Pooling</a>）。这类模型的最大优势就是能够通过学习的方式判断视频中重要的帧和次要的帧，从而能够更好地表示视频的内容。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin: 0px 0px 1em; padding: 0px; line-height: 1.3;"></p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h2 style="margin:10px 0px;padding:0px;font:bold 24px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">Embedding模型的训练</h2>
<div style="margin:0px 0px 0px 10px;padding:0px;vertical-align:middle;display:inline-block;color:#8091a5;font-size:15px;line-height:1.3;position:relative;height:20px;width:22px;">

<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">  因为缺乏直接的训练目标,Embedding模型通常采用间接训练的方式，即如训练一个分类模型或者回归模型，训练完成后取模型的中高层隐层作为Embedding。也可以用Metric Learning的方式用pairwise或triplet损失函数直接训练Embedding。这种训练方式的优点在于可以直接定义样本之间的相似度，并且可以在构造损失函数时加入一些语义的成分，但是其缺点是缺乏已标注的大型数据集，很难训练出高质量的模型。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">  综合上述考虑，我们选用Youtube8m作为训练集，用视频分类算法训练我们的Embedding模型。考虑到Youtube8m数据集过于庞大，训练成本太高，所以在模型选择过程中我们选用较小的UCF101数据集进行实验。虽然可能和Youtube8m的实验结果存在一些偏差，但我们认为UCF101数据集的实验结果依然具有代表性。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h3 style="margin:10px 0px;padding:0px;font:bold 18px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">基准模型选择</h3>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">  首先通过实验验证Learnable Pooling和时间序列模型的Embedding效果。我们用UCF101数据集作为训练-测试集，用模型在UCF101上的预测精度来判断模型的Embedding效果。本实验基于以下两条假设：</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<ol style="margin:10px 0px 10px 25px;padding:0px;text-indent:0px;"><li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">模型在UCF101数据集和YouTube8m数据集上具有相同的性能排序</p>
</li>
<li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">更高的分类精度意味着更好的Embedding效果</p>
</li>
</ol></div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">实验中我们构建了四个模型：单层LSTM、单层LSTM Self-Attention、双层LSTM和NetVLAD。其中LSTM Self-Attention模型是用LSTM的State向量对输出的Hidden做Reweight，希望能够通过这种方式让LSTM模型能够给重要的帧更大的权重，如下图所示：</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin: 0px 0px 1em; padding: 0px; line-height: 1.3;"></p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<div style="margin:10px 0px;padding:0px;overflow-x:auto;line-height:1.3;">
<table style="border-collapse:collapse;border-spacing:0px;clear:none;width:auto;table-layout:fixed;margin:0px 0px 20px;min-width:30%;max-width:95%;"><thead><tr><th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">LSTM</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">LSTM Self-Attention</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">LSTM 2 Layers</th>
</tr></thead><tbody><tr><td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;"><strong>76.6%</strong></td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">68.1%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">67.5%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">68.6%</td>
</tr></tbody></table></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">上述实验结果表明，NetVLAD模型具有明显的优势，增加复杂度的双层LSTM无法得到性能收益，添加attention的LSTM模型也无法获得明显的精度提升。所以我们选用NetVLAD作为Embedding的基准模型。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h3 style="margin:10px 0px;padding:0px;font:bold 18px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">Gradient Accumulation</h3>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">  由于视频包含多帧图像，所以tensorflow的标准NHWC数据结构无法满足视频的batch训练（N通道被N个视频帧占用，无法放入N个视频），默认情况下batch size只能设为1。理论上batch size对于模型训练的稳定性和泛化能力都有至关重要的作用。为了实现batch训练，我们编写了Gradient Accumulation机制来模拟batch训练，通过缓存多次BP的梯度，统一平均梯度更新参数。通过这种方式将batch size设置为10，重复上述实验，结果如下：</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<div style="margin:10px 0px;padding:0px;overflow-x:auto;line-height:1.3;">
<table style="border-collapse:collapse;border-spacing:0px;clear:none;width:auto;table-layout:fixed;margin:0px 0px 20px;min-width:30%;max-width:95%;"><thead><tr><th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">LSTM</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">LSTM Self-Attention</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">LSTM 2 Layers</th>
</tr></thead><tbody><tr><td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;"><strong>80.8%</strong></td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">70.1%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">69.3%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">70.4%</td>
</tr></tbody></table></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">可以看出Gradient Accumulation可以明显提高模型的预测精度，也就能够提高模型Embedding效果。经过多次试验验证，我们发现batch size设为10是平衡模型性能和训练开销的较好选择。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h3 style="margin:10px 0px;padding:0px;font:bold 18px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">参数选择</h3>
<div style="margin:0px 0px 0px 10px;padding:0px;vertical-align:middle;display:inline-block;color:#8091a5;font-size:15px;line-height:1.3;position:relative;height:20px;width:22px;"></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">我们通过一系列的实验来调优模型参数和训练参数，我们选取两个有代表性的实验展示：</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<ol style="margin:10px 0px 10px 25px;padding:0px;text-indent:0px;"><li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">NetVLAD 500ms：用500ms的抽帧率代替1s的抽帧率，判断抽帧数量策略对模型的影响。0.812</p>
</li>
<li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">NetVLAD DA：加入帧随机翻转、随机裁剪、RGB通道变换、随机高斯噪声等预处理步骤。</p>
</li>
</ol></div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">实验结果如下：</p>
<div style="margin:10px 0px;padding:0px;overflow-x:auto;line-height:1.3;">
<table style="border-collapse:collapse;border-spacing:0px;clear:none;width:auto;table-layout:fixed;margin:0px 0px 20px;min-width:30%;max-width:95%;"><thead><tr><th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD 500ms</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD DA</th>
</tr></thead><tbody><tr><td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">80.8%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">81.2%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;"><strong>81.6%</strong></td>
</tr></tbody></table>

<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">实验证明提高模型帧采样率有利于提高模型性能，但同时也明显增加了系统开销，所以相比之下做在线数据预处理是一种更廉价有效的方案。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h3 style="margin:10px 0px;padding:0px;font:bold 18px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">改进模型结构</h3>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h4 style="margin:10px 0px;padding:0px;font:bold 16px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">Hierarchical VLAD (HVLAD)</h4>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">首先我们提出层级式VLAD：Hierarchical VLAD。提出这种模型的动因是，VLAD模型最初是在图像识别中获得广泛应用的，它能够将不同区域的特征进行pooling来表示一幅图像，更有利于描述图片的局部信息。所以本模型借助这种特点，先对每一帧做图像金字塔，用VLAD对金字塔特征进行图像块级别的VLAD Pooling，最后再做帧级别的VLAD Pooling，模型简图如下：</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin: 0px 0px 1em; padding: 0px; line-height: 1.3;"></p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">实验结果如下表：</p>
<div style="margin:10px 0px;padding:0px;overflow-x:auto;line-height:1.3;">
<table style="border-collapse:collapse;border-spacing:0px;clear:none;width:auto;table-layout:fixed;margin:0px 0px 20px;min-width:30%;max-width:95%;"><thead><tr><th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">HVLAD</th>
</tr></thead><tbody><tr><td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">80.8%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">80.7%</td>
</tr></tbody></table></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">HVLAD和NetVLAD在UCF101数据集上相比没有表现出任何性能优势，可能是由于以下两点原因</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<ol style="margin:10px 0px 10px 25px;padding:0px;text-indent:0px;"><li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">HVLAD的参数要远多于NetVLAD，对UCF101数据集造成了不小的压力；</p>
</li>
<li style="margin:0px;padding:0px;list-style:decimal;line-height:1.8;white-space:normal;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">从原理上HVLAD的优势应该在对局部特征的描述，但是对于视频分类来讲很难说帧的局部特征能够起到明显的作用，毕竟视频中包含的信息量远大于图像，模型需要学习的内容也更多。</p>
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;"></p>
</li>
</ol></div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">实验表明，在视频分类的task中，过于细化的局部信息和过于复杂的模型结构很难提供良好的性能增益。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h4 style="margin:10px 0px;padding:0px;font:bold 16px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">RGB-音频Concat模型（NetVLAD+Audio）</h4>
<div style="margin:0px 0px 0px 10px;padding:0px;vertical-align:middle;display:inline-block;color:#8091a5;font-size:15px;line-height:1.3;position:relative;height:20px;width:22px;"></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">我们用VGG-16模型将视频的音频信息抽象成128维特征(参见<a href="https://arxiv.org/abs/1609.09430" style="text-decoration:none;color:#6293e2;">CNN ARCHITECTURES FOR LARGE-SCALE AUDIO CLASSIFICATION</a>)，并入Inception-V3的输出，共同输入NetVLAD模型。分类效果取得了非常明显的提升，GAP 0.861 vs GAP 0.816。实验表明音频信息作为视频的重要组成部分，能够明显增强视频的Embedding表示。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin: 0px 0px 1em; padding: 0px; line-height: 1.3;"></p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<div style="margin:10px 0px;padding:0px;overflow-x:auto;line-height:1.3;">
<table style="border-collapse:collapse;border-spacing:0px;clear:none;width:auto;table-layout:fixed;margin:0px 0px 20px;min-width:30%;max-width:95%;"><thead><tr><th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD DA</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD+Audio</th>
</tr></thead><tbody><tr><td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">81.6%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;"><strong>86.1%</strong></td>
</tr></tbody></table></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h4 style="margin:10px 0px;padding:0px;font:bold 16px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">光流-RGB双塔模型（OF-RGB VLAD）</h4>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">NetVLAD无法学习帧间的时序关系，所以我们认为加入光流应该能够明显弥补这一缺陷。我们将离线计算的光流图送入ResNet-101模型，构成一个完整的双通道模型。两个通道输出的特征向量用MoE模型融合再送入softmax分类。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin: 0px 0px 1em; padding: 0px; line-height: 1.3;"></p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<div style="margin:10px 0px;padding:0px;overflow-x:auto;line-height:1.3;">
<table style="border-collapse:collapse;border-spacing:0px;clear:none;width:auto;table-layout:fixed;margin:0px 0px 20px;min-width:30%;max-width:95%;"><thead><tr><th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD DA</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">OF-RGB VLAD</th>
</tr></thead><tbody><tr><td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">81.6%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;"><strong>88.3%</strong></td>
</tr></tbody></table></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">可以看到双通道光流模型的GAP达到0.883，可见光流信息能够极大增强模型的性能。但遗憾的是这种做法需要离线计算视频光流，该过程是非常缓慢的，所以我们又提出了一种在线光流双通道模型：Online-Hibernate VLAD（OHVLAD）模型。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h4 style="margin:10px 0px;padding:0px;font:bold 16px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">Online-Hibernate VLAD（OHVLAD）</h4>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">OHVLAD的基本原理是借助FlowNet模型，将光流计算流程融入网络框架内，从而实现高速在线预测。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin: 0px 0px 1em; padding: 0px; line-height: 1.3;"></p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<div style="margin:10px 0px;padding:0px;overflow-x:auto;line-height:1.3;">
<table style="border-collapse:collapse;border-spacing:0px;clear:none;width:auto;table-layout:fixed;margin:0px 0px 20px;min-width:30%;max-width:95%;"><thead><tr><th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">NetVLAD DA</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">OF-RGB VLAD</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">OHVLAD-FlowNet</th>
<th style="margin:0px;padding:5px;font-style:normal;font-weight:bold;font-family:inherit;text-align:left;height:18px;line-height:18px;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;background-color:#f7f7f7;color:#666666;vertical-align:top;">OHVLAD-FLowNetV2</th>
</tr></thead><tbody><tr><td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">81.6%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;"><strong>88.3%</strong></td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">87.6%</td>
<td style="margin:0px;padding:5px;height:22px;line-height:22px;text-align:left;overflow:inherit;white-space:nowrap;border:1px solid #dfdfdf;vertical-align:top;">86.0%</td>
</tr></tbody></table></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">用FlowNet在线生成光流性能十分接近于离线生成光流的做法，并且明显优于单通道VLAD模型，但其缺点就是模型复杂度较高，计算耗时是普通NetVLAD模型2-3倍。</p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin: 0px 0px 1em; padding: 0px; line-height: 1.3;"></p>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;"></div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<h2 style="margin:10px 0px;padding:0px;font:bold 24px/1.5 &#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;color:#34383e;height:auto;">小结</h2>
<div style="margin:0px 0px 0px 10px;padding:0px;vertical-align:middle;display:inline-block;color:#8091a5;font-size:15px;line-height:1.3;position:relative;height:20px;width:22px;"></div>
</div>
</div>
<div style="margin:0px;padding:0px;line-height:1.3;color:#000000;font-family:&#39;Helvetica Neue&#39;, &#39;Helvetica Neue&#39;, Helvetica, Arial, &#39;Lantinghei SC&#39;, &#39;Hiragino Sans GB&#39;, &#39;Microsoft Yahei&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-align:left;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;background-color:#ffffff;">
<div style="margin:0px;padding:0px;line-height:1.3;">
<p style="margin:0px 0px 1em;padding:0px;line-height:1.3;">训练视频Embedding基于Learnable Pooling的方法能获得比时间序列模型更好的效果。鉴于视频信息量大的特性，增加模型的复杂度不一定能够带来性能的提升。音频信息、光流信息（本质上是帧间相关性）都能够明显地提升视频Embedding的效果，这也是未来模型改进的主要方向。</p>
