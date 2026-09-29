---
title: "Label Smoothing和Mixup：两种提高图像分类准确率的方法"
date: 2022-04-18 14:31:44
categories:
  - deep-learning
---

{% raw %}

<div><h1>摘要</h1>
</div><div><p>内平每日需对百万级别的短小视频进行分类，而图片特征是分类模型的一个重要模态，因此需要用视频帧训练图像分类模型。本文介绍了两种有助于提高图像分类准确率的方法：Label Smoothing（标签平滑）和Mixup，这两种方法分别立足于模型正则化和数据增强。本文通过一系列离线的对比实验，验证上述方法的有效性，并在线上运用Mixup方法，将短视频一级分类准确率从83%提高到90.6%，二级分类准确率从70%提高到82.6%；小视频一级分类准确率从78%提高到88.6%，二级分类准确率从60%提高到74.7%。</p>
</div><div><h1>一、问题背景及意义</h1>
</div><div><p>内平每日需对百万级别的微视小视频和企鹅号短视频进行分类，并基于视频embedding做近似视频召回和标签打底，从而实现视频在推荐系统中的冷启动。因此，提高分类准确率，以及中间产物embedding的表征能力，对精准推荐、改善用户体验、提高用户粘性和留存率，具有重要意义。</p>
</div><div><p>视频分类不可避免会用到视频的帧，而视频帧分类则可归结为图像分类的问题。我们的第一版模型<sup>1</sup>采用ImageNet预训练过的Inception-v3模型抽取图像特征。然而ImageNet数据集的图片内容、类目分布与我们业务的短小视频帧是有一定差别的，采用ImageNet预训练过的模型抽取短小视频帧的特征，会将该特征限制在ImageNet的空间上，从而制约接下来NetVLAD视频分类模型的上限。因此，用我们的业务数据重训图像分类模型，可以将图像分类模型的特征转移到我们业务数据的空间上，这对提高后续短小视频分类模型的表现，具有重要意义。</p>
</div><div><p>在研究过程中，我们发现了两种有助于提高图像分类准确率的方法：Label Smoothing（标签平滑）和Mixup，本文将对这两种方法进行介绍，并展示相关实验结果和分析，验证其有效性。</p>
</div><div><h1>二、Label Smoothing （标签平滑）</h1>
</div><div><p>Label Smoothing的方法于2016年由Szegedy等人与Inception-v3模型一并提出<sup>2</sup>。通常的分类算法，ground truth是一个one-hot向量，模型的输出经过Softmax函数之后，与该向量求交叉熵，计算损失函数。但one-hot向量这种非黑即白的特性，容易使得模型在训练过程中梯度过大，过快拟合训练集上的样本，从而增大过拟合的风险，降低模型在验证集、测试集上的泛化能力。为此，作者提出了Label Smoothing的方法，在ground truth向量的正确类目对应的值仍保持绝对主导的前提下，将少量概率分配给其他类目，从而平滑标签，平滑训练过程中的梯度。这种方法实质上也是在训练过程中引入少量噪声，从而对模型起到正则化的作用，有助于提高模型的泛化能力。</p>
</div><div><p>具体地，设类目数为CCC，某个样本属于第iii类，平滑系数为ϵ\epsilonϵ，则该样本的ground truth向量是一个CCC维向量，其第iii个元素为1−ϵ1-\epsilon1−ϵ，其余元素为ϵC−1\frac{\epsilon}{C-1}C−1ϵ​。该向量在训练过程中同样会与模型的Softmax输出求交叉熵，并计算损失函数的值，回传梯度，更新参数。</p>
</div><div><p>在实践中，我们发现，视频之间有一些类目是模糊的，比如小视频一级类目的“亲子”、“生活”，二级类目的“亲子_萌娃”和“亲子_正常儿童”，体现在混淆矩阵上，就是这些类会互相占据错得最多的那几个。为了反映这种模糊性，我们探索了一种基于混淆矩阵的Label Smoothing的方法，它与原始的Label Smoothing方法的区别体现在，平滑系数ϵ\epsilonϵ不再均分到所有的错误类目，而是将稍微大的权重分配给较模糊的若干个类目，将更小的权重分配给其他类目。</p>
</div><div><p>具体地，设原始模型经训练后，在测试集上，类目iii的混淆向量为[ci,0,ci,1,...,ci,i,...,ci,C−2,ci,C−1[c_{i, 0},c_{i, 1},...,c_{i, i},...,c_{i, C-2},c_{i, C-1}[ci,0​,ci,1​,...,ci,i​,...,ci,C−2​,ci,C−1​]。除去ci,ic_{i, i}ci,i​以外，最大的NNN个值，其下标集合为I\mathcal{I}I，则基于混淆矩阵的Label Smoothing方法，会将ϵ2\frac{\epsilon}{2}2ϵ​的概率平均分配给I\mathcal{I}I中包含的类目，将剩余的ϵ2\frac{\epsilon}{2}2ϵ​概率分配给剩余的类目。当然，N&lt;C−12N&lt;\frac{C-1}{2}N&lt;2C−1​，上述方法才有意义。</p>
</div><div><p>引入模糊性，实质上是将原始模型中得到的后验信息，转化为后续模型的先验信息，引入到训练过程中，这对提升模型的训练质量是有帮助的。</p>
</div><div><h1>三、Mixup</h1>
</div><div><p>图像训练算法用到的深度神经网络，通常具有大量的参数，且随着计算能力的迅速增长，模型在不断地加深加宽。文献<sup>3</sup>对这种趋势做了一个很好的综述。但网络的参数越多，在有限的训练集上，过拟合的风险就越大，为此，多种数据增强的方法被提了出来，如翻转、旋转、局部裁剪等。2018年，Zhang等人提出了一种强有力的数据增强算法——Mixup<sup>4</sup>。该算法基于输入的线性组合导致输出的线性组合的假设，采用邻域风险最小化的思路，将训练集中两张不同类目的图片按一定比例混合在一起，将其ground truth向量也按该比例混合，从而达到大幅度扩充训练样本的目的，在ImageNet、CIFAR-10、CIFAR-100等多个数据集上，均取得了SOTA（State-Of-The-Art）的结果。</p>
</div><div><p>具体地，记混合系数为λ\lambdaλ，其服从Beta分布，即λ∼Beta(α,α),α∈(0,∞)\lambda\sim \mathrm{Beta}(\alpha, \alpha), \alpha\in(0,\infty)λ∼Beta(α,α),α∈(0,∞)。记有两张图片iii和jjj，其输入分别是xix_ixi​和xjx_jxj​，ground truth向量分别为yiy_iyi​和yjy_jyj​，则以λ\lambdaλ的混合系数做Mixup之后，其输入和ground truth向量分别变为：<br/>
x~=λxi+(1−λ)xj,(3.1)\widetilde{x}=\lambda x_i + (1 - \lambda)x_j, \tag{3.1}x<svg height="0.26em" preserveAspectRatio="none" viewBox="0 0 600 260" width="100%"><path d="M200 55.538c-77 0-168 73.953-177 73.953-3 0-7
-2.175-9-5.437L2 97c-1-2-2-4-2-6 0-4 2-7 5-9l20-12C116 12 171 0 207 0c86 0
 114 68 191 68 78 0 168-68 177-68 4 0 7 2 9 5l12 19c1 2.175 2 4.35 2 6.525 0
 4.35-2 7.613-5 9.788l-19 13.05c-92 63.077-116.937 75.308-183 76.128
-68.267.847-113-73.952-191-73.952z"></path></svg>=λxi​+(1−λ)xj​,(3.1)<br/>
y~=λyi+(1−λ)yj.(3.2)\widetilde{y}=\lambda y_i + (1 - \lambda)y_j. \tag{3.2}y<svg height="0.26em" preserveAspectRatio="none" viewBox="0 0 600 260" width="100%"><path d="M200 55.538c-77 0-168 73.953-177 73.953-3 0-7
-2.175-9-5.437L2 97c-1-2-2-4-2-6 0-4 2-7 5-9l20-12C116 12 171 0 207 0c86 0
 114 68 191 68 78 0 168-68 177-68 4 0 7 2 9 5l12 19c1 2.175 2 4.35 2 6.525 0
 4.35-2 7.613-5 9.788l-19 13.05c-92 63.077-116.937 75.308-183 76.128
-68.267.847-113-73.952-191-73.952z"></path></svg>​=λyi​+(1−λ)yj​.(3.2)<br/>
图1展示了从我们的小视频数据集中任意抽出两帧，进行Mixup之后的效果。第一张图片的混合系数是0.8，第二张图片的混合系数是0.2。<br/>
<img alt="" loading="lazy" src="/logbook/images/deep-learning/87813603fccea3aa6dad.png"/><br/>
图1Mixup的效果展示\mathrm{图1\qquad Mixup的效果展示}图1Mixup的效果展示<br/>
原论文建议：</p>
</div><div><ul>
<li>以两张图片混合为宜，混三张或更多的图片，对提高训练效果基本没有帮助，反而增加了计算量。</li>
<li>混相同类目的图片是没有用的，混不同类目的图片才有用。</li>
<li>模型容量越大，跑越久，Mixup越有用。</li>
</ul>
</div><div><h1>四、实验结果与分析</h1>
</div><div><p>我们分别在短小视频的数据集上，验证上述方法的有效性。该数据集的训练集对头部类目做了降权，并确保每个尾部类目在训练集中至少出现1次，验证集和测试集则服从大盘分布。对每个视频，我们一秒抽一帧，并随机抽两帧进入图片数据集（若只有一帧，则用这一帧），并将该视频的类目指定为帧的类目。短小视频数据集的一二级类目数、训练集条目数、验证集条目数、测试集条目数分别如表1所示。</p>
</div><div><p>表1数据集的情况\mathrm{表1\qquad 数据集的情况}表1数据集的情况</p>
</div><div><div><table>
<thead>
<tr>
<th>集合</th>
<th>一级类目数</th>
<th>二级类目数</th>
<th>训练集条目数</th>
<th>验证集条目数</th>
<th>测试集条目数</th>
</tr>
</thead>
<tbody>
<tr>
<td>短视频</td>
<td>28</td>
<td>166</td>
<td>3,834,685</td>
<td>575,016</td>
<td>574,870</td>
</tr>
<tr>
<td>小视频</td>
<td>24</td>
<td>197</td>
<td>4,001,614</td>
<td>598,824</td>
<td>598,904</td>
</tr>
</tbody>
</table>
</div></div><div><p>相比第一版的Inception-v3模型，在第二版，我们将模型更换成了效果更好的EfficientNet-B3<sup>5</sup>，因此，下面的实验都是基于EfficientNet-B3模型展开的。</p>
</div><div><p>我们的算法基于Python 3.6实现，使用了PyTorch深度学习框架。在PyTorch实现Label Smoothing和Mixup的核心代码分别如下所示：</p>
</div><div><pre>N = true_label_array.size(0) # true_label_array为原始的one-hot向量，N为样本数
smoothed_labels = torch.full(size=(N, args.num_classes), fill_value=epsilon / (args.num_classes - 1)) # epsilon为平滑系数
smoothed_labels.scatter_(dim=1, index=torch.unsqueeze(true_label_array, dim=1), value=1 - epsilon)
</pre>
</div><div><pre>beta_distribution = torch.distributions.beta.Beta(alpha, alpha) # alpha为beta分布的系数
lambda_ = beta_distribution.sample([]).item() # lambda_为混合系数
index = torch.randperm(input_array.size(0))
mixed_images = lambda_ * input_array + (1 - lambda_) * input_array[index, :]
outputs = model(mixed_images)
loss = lambda_ * F.cross_entropy(outputs, true_label_array) + (1 - lambda_) * F.cross_entropy(outputs, true_label_array[index])
</pre>
</div><div><p>我们使用在ImageNet上预训练过的EfficientNet-B3模型，用我们的数据集微调参数，从而充分利用预训练模型已经学习到的点、线、边等通用特征，加快收敛速度。算法的一些重要参数如下：</p>
</div><div><p>对Label Smoothing，平滑系数ϵ\epsilonϵ为0.1；对基于混淆矩阵的Label Smoothing，平滑系数ϵ\epsilonϵ为0.2，重点分配的类目数NNN为4。</p>
</div><div><p>对Mixup，Beta分布的参数α\alphaα为0.2。</p>
</div><div><p>训练方面，我们的初始学习率设为0.0001，每过2个epoch，学习率减半。优化器采用Adam<sup>6</sup>，并限制梯度的最大模长为2。此外，对Mixup，我们还根据原论文的建议，做了学习率先增后减的实验，具体地，从第1到第5个epoch，学习率从0.0001线性增加到0.0005，随后每过两个epoch，学习率减半。实验的评测指标为分类的Hits@1准确率，短小视频的实验结果分别如表2和表3所示。<br/>
表2短视频在测试集上的Hits@1准确率（%）\mathrm{表2\qquad 短视频在测试集上的Hits@1准确率（\%）}表2短视频在测试集上的Hits@1准确率（%）</p>
</div><div><div><table>
<thead>
<tr>
<th>方法</th>
<th>一级准确率</th>
<th>二级准确率</th>
</tr>
</thead>
<tbody>
<tr>
<td>原始模型</td>
<td>76.83</td>
<td>68.08</td>
</tr>
<tr>
<td>Label Smoothing</td>
<td>77.03</td>
<td>68.27</td>
</tr>
<tr>
<td>基于混淆矩阵的Label Smoothing</td>
<td>77.15</td>
<td>68.34</td>
</tr>
<tr>
<td>Mixup</td>
<td>76.77</td>
<td>68.01</td>
</tr>
<tr>
<td>学习率先增后减的Mixup</td>
<td>77.96</td>
<td>69.75</td>
</tr>
</tbody>
</table>
</div></div><div><p>表3小视频在测试集上的Hits@1准确率（%）\mathrm{表3\qquad 小视频在测试集上的Hits@1准确率（\%）}表3小视频在测试集上的Hits@1准确率（%）</p>
</div><div><div><table>
<thead>
<tr>
<th>方法</th>
<th>一级准确率</th>
<th>二级准确率</th>
</tr>
</thead>
<tbody>
<tr>
<td>原始模型</td>
<td>75.34</td>
<td>61.87</td>
</tr>
<tr>
<td>Label Smoothing</td>
<td>75.38</td>
<td>62.12</td>
</tr>
<tr>
<td>基于混淆矩阵的Label Smoothing</td>
<td>75.68</td>
<td>62.41</td>
</tr>
<tr>
<td>Mixup</td>
<td>75.56</td>
<td>62.01</td>
</tr>
<tr>
<td>学习率先增后减的Mixup</td>
<td>76.17</td>
<td>62.95</td>
</tr>
</tbody>
</table>
</div></div><div><p>可见，相比原始模型，Label Smoothing和基于混淆矩阵的Label Smoothing均能略微提升模型的表现。但单纯的Mixup并不总是带来效果的增益，而学习率先增后减的Mixup，可以显著提升模型在测试集上的准确率。</p>
</div><div><p>图2展示了单纯的Mixup和学习率先增后减的Mixup，训练过程中在短视频验证集上的二级准确率变化趋势。可见，即使在初始的几个epoch，单纯的Mixup在验证集上稍占优势，但学习率先增后减的Mixup在进入学习率下降阶段以后，后劲更足，很快就能超越前者。<br/>
<img alt="" loading="lazy" src="/logbook/images/deep-learning/03e6b97f66b6b4d509aa.png"/><br/>
图2两种Mixup训练过程中在短视频验证集上的二级准确率\mathrm{图2\qquad 两种Mixup训练过程中在短视频验证集上的二级准确率}图2两种Mixup训练过程中在短视频验证集上的二级准确率</p>
</div><div><p>用我们业务的数据集微调基于ImageNet预训练的图像分类模型，对后续的视频分类模型准确率的提升意义重大。微调Inception-v3之后，与没有微调相比，小视频测试集一级分类的Hits@1准确率从71.55%提高到80.96%，二级则从55.64%提高到67.48%。将图像分类模型替换成EfficientNet-B3，用学习率先增后减的Mixup训练，以及做了其他各方面的改进之后，我们短视频一级分类线上准确率从83%提高到90.6%，二级分类线上准确率从70%提高到82.6%；小视频一级分类线上准确率从78%提高到88.6%，二级分类线上准确率从60%提高到74.7%，并取得了视频embedding能力打榜比赛<sup>7</sup>公榜第一、私榜第二的成绩。如今，我们的模型在线上，为每日百万量级的短小视频提供分类、embedding、标签打底等服务。</p>
</div><div><h1>五、总结与展望</h1>
</div><div><p>本文介绍了两种提高图像分类准确率的方法：Label Smoothing和Mixup，并相应介绍了两种进一步的改进策略：基于混淆矩阵的Label Smoothing和学习率先增后减的Mixup，通过离线实验和线上效果验证上述方法的有效性。</p>
</div><div><p>后续我们会尝试将Mixup运用到音频的频谱图上，对音频做数据增强，提升音频模态分类的准确率。我们还会尝试将封面图、关键帧的信息引入训练。我们也将尝试做一些视频垂类标签分类、迁移的工作。</p>
</div><div><h1>参考文献</h1>
<hr/>
<section>
<ol>
<li><p>叶振旭. [内部或本地链接已移除] [DB/OL]. : 深圳, 2019. ↩︎</p>
</li>
<li><p>Szegedy C, Vanhoucke V, Ioffe S, et al. Rethinking the inception architecture for computer vision[C]. Proceedings of the CVPR 2016. 2016: 2818-2826. ↩︎</p>
</li>
<li><p>陈琳. [内部或本地链接已移除] [DB/OL]. : 深圳, 2019. ↩︎</p>
</li>
<li><p>Zhang H, Cisse M, Dauphin Y N, et al. mixup: Beyond empirical risk minimization[C]. Proceedings of the ICLR 2018. 2018. ↩︎</p>
</li>
<li><p>Tan M, Le Q V. EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks[C]. Proceedings of the ICML 2019. 2019. ↩︎</p>
</li>
<li><p>Kingma D P, Ba J. Adam: A method for stochastic optimization[C]. Proceedings of the ICLR 2015. 2015. ↩︎</p>
</li>
<li><p>[内部或本地链接已移除] [EB/OL]. ↩︎</p>
</li>
</ol>
</section>
</div> 
{% endraw %}
