---
title: "基于ModelZoo快速开发高效无量推荐模型"
date: 2022-04-18 17:15:27
categories:
  - deep-learning
---

<div data-inline-code-theme="red" data-code-block-theme="default"><h1 data-lines="1" data-sign="21b0c3487733c9d1ecf26668326da95f" id="1-%E6%97%A0%E9%87%8F%E5%92%8Cmodelzoo%E7%9A%84%E7%AE%80%E5%8D%95%E4%BB%8B%E7%BB%8D" class="toc-enable">1 无量和ModelZoo的简单介绍</h1><h2 data-lines="2" data-sign="37f3b026a4995c4fe54f07a71e7717a4" id="11-%E6%97%A0%E9%87%8F%E4%B8%8Emodelzoo" class="toc-enable">1.1 无量与ModelZoo</h2><ol start="1" class="cherry-list__default" data-lines="3" data-sign="e4d81b5ff1492eb001a5496bdfd08eadlist3"><li>在线编码：在线编码是机器学习平台部Venus团队开发的一套容器化的Web Based在线服务，主要目标是助力机器学习领域全流程的降本提效，让用户可以一站式完成从数据获取，清洗处理，特征提取加工，代码编写，模型调试训练，模型发布注册，打分等流程</li><li>VenusFlow：VenusFlow是面向开发者提供调度和管理Venus工作流的SDK。提供代码操作Venus平台工作流的能力</li><li>Vtools：Vtools 是提供给算法科学家在Venus中快速提交训练任务的一种命令行交互工具，简化训练任务依赖的共享存储、计算资源、镜像、程序等的配置及程序调整需要反复上传的工作</li></ol><h2 data-lines="2" data-sign="e554bc9f9880ea4eff1afb52d37ed016" id="22-modelzoo%E5%BF%AB%E9%80%9F%E5%BC%80%E5%8F%91" class="toc-enable">2.2 ModelZoo快速开发</h2><h2 data-lines="2" data-sign="cf74ce4ccd78885d35b87bc1c00e4a11" id="31-%E7%89%B9%E5%BE%81%E4%BC%98%E9%80%89%E5%92%8C%E8%87%AA%E5%8A%A8%E4%BA%A4%E5%8F%89" class="toc-enable">3.1 特征优选和自动交叉</h2><div data-lines="6" data-type="div" data-sign="ae5430f0f14e2845c3239398d8dc711f"><center>
	<table>
		<tbody><tr><td style=""></td><td></td><td style=""></td></tr>
	</tbody></table>
</center>

<h2 data-lines="2" data-sign="a7e67254ad11691567e789878d7e14cf" id="33-double-hash" class="toc-enable">3.3 Double Hash</h2><div data-lines="3" data-type="div" data-sign="9d9d53e816773169db3ba8d0cf188e3b">Double Hash也是一个模型压缩技术，它具有效果持平，模型可复用的优势。已信息流-混排模型的应用举例，Double Hash将模型从125G降低为14G，存储减少88%，模型上线时间缩短，上限流量降低88%，模型缩小后Ronda机器成本可节省100%。在多个场景模型体积压缩平均超70%。下表展示了Double Hash在业务主场景的推广情况：
<center style=""></center>

<h2 data-lines="2" data-sign="14f0b0be38d24bf27c6b2b52b5dc30c5" id="34-%E5%85%A8%E9%93%BE%E8%B7%AF%E4%B8%80%E8%87%B4%E6%80%A7" class="toc-enable">3.4 全链路一致性</h2><div data-lines="3" data-type="div" data-sign="4e9c98ad9e3f3cc1329da27525ba602c">全链路一致性通过联合建模精排、粗排和召回模型提高粗排、召回与精排模型的排序一致性，进而提升推荐链路的整体效果。该方案能够大幅减少排序训练资源开销（~40%），同时一致性加强提升了粗排召回效果，如全民K歌某场景精粗排一致性提升29%，看点视频某场景精粗排一致性提高15%。下表展示了该方案的落地效果：
<center style=""></center>

<h2 data-lines="2" data-sign="0dc9cbc25c2ad88845dea2004e76b419" id="35-%E5%9F%BA%E4%BA%8Ememory-network%E7%9A%84%E6%8E%A8%E8%8D%90%E5%86%B7%E5%90%AF%E5%8A%A8" class="toc-enable">3.5 基于Memory Network的推荐冷启动</h2><div data-lines="3" data-type="div" data-sign="53602000c37980bdc880b78cd32056b2">以memory network来存储用户、物品的群体特征，基于用户、物品的训练充分的属性特征来查找群体特征帮助冷启。基于ModelZoo，传入属性embedding，就可以得到memory ID embedding，根据实际场景选择相加融合、拼接或者探索其它的使用方式。该方案可以同时用于用户与物品的冷启。下表展示了该方案的落地效果：
<center style=""></center>

<h2 data-lines="2" data-sign="d8f3c0ecb0db60e0850f46d194c6e1b2" id="36-%E6%A8%A1%E5%9E%8B%E9%A2%84%E8%AE%AD%E7%BB%83" class="toc-enable">3.6 模型预训练</h2><div data-lines="3" data-type="div" data-sign="53a15d736e5e56b8d2411c482e0d54bc">模型预训练方案通过在大数据量上训练一个通用模型，然后在某个场景上微调进行服务。预训练使用一个大模型提高在多个场景上的业务效果和开发效率。该方案通过引入多端流水，丰富用户端内的行为，通过不同的算法方式，对大盘和新用户均有收益，对新用户收益尤为显著。下表展示了该方案的业务落地效果：
<center style=""></center>

<h2 data-lines="2" data-sign="3b820ef7cce455d150fa015f783d29a9" id="37-gpu%E6%A8%A1%E5%9E%8B%E8%AE%AD%E7%BB%83" class="toc-enable">3.7 GPU模型训练</h2><div data-lines="4" data-type="div" data-sign="3b9937312d646ee9d6ef28f73c104f5e">GPU训练是无量新推出的功能，在性能、性价比和业务核心指标上均有显著提升。下表展示了多个业务场景GPU训练的效果：
<center style=""></center>
一般业务模型使用两张A100卡就能进行训练，训练速度能够达到原来的3倍以上，同时成本上也有很大节省。

<h2 data-lines="2" data-sign="574abb6753d40597068c85410a35ba09" id="38-learning-to-rank" class="toc-enable">3.8 Learning to Rank</h2><div data-lines="3" data-type="div" data-sign="407d6f4e272fed742734299389851aff">Learning to rank（LTR）一般在搜索和混排场景使用，主要分为pointwise、pairwise和listwise类型。一般的无量模型是pointwise类型的，即我们每次预估一个用户对一个物品的喜好。通过简单的样本改造，无量也支持pairwise和listwise的模型。下表展示了pairwise或者listwise的落地情况：
<center style=""></center>

<h2 data-lines="2" data-sign="ba48c77584084987314a0aceca8006a1" id="39-%E5%9C%BA%E6%99%AF%E8%9E%8D%E5%90%88%E5%92%8C%E8%BF%81%E7%A7%BB" class="toc-enable">3.9 场景融合和迁移</h2><div data-lines="3" data-type="div" data-sign="c58779faae5b1d5381a8b317685aa34c">场景融合与迁移就是将相似的多个场景数据和模型进行合并，达到降本增效的效果。相似的场景具有相互补充的作用，因此对于推荐效果也是有收益的。将多个模型合并为一个，也能够大大降低训练资源，从而降低训练成本。下表展示了场景融合和迁移的落地情况：
<center style=""></center></div><div data-lines="3" data-type="div" data-sign="8b7cd139a397e3678068154b0888f13f">场景融合常采用多任务学习的方式进行，比如可参考的模型结构如下图所示：
<center style=""></center>

<h1 data-lines="2" data-sign="38b97ed9379831a91fe9a49245111891" id="4-%E6%80%BB%E7%BB%93" class="toc-enable">4 总结</h1><ul class="cherry-list__square" data-lines="2" data-sign="0b064039a139b223faae185a882ffb86list2"><li>无量框架训练全流程</li><li>无量推荐模型库ModelZoo</li></ul><span data-lines="2" data-type="br" data-sign="br2"></span><p data-lines="1" data-type="p" data-sign="120385931016ebf496415289d75de628">2.无量推荐模型降本增效</p><span id="mark-markdown-toc-enable" data-toc-enable="true"></span><ul class="cherry-list__square" data-lines="10" data-sign="55f4743820adc731874e1a5e98340b06list10"><li>AutoGroup: 推荐系统中的自动特征交叉</li><li><a rel="nofollow" href="https://doc.weixin.qq.com/doc/w3_ALgAKQZ-ACca1eDlKXUSHusjmA1Q8?scode=AJEAIQdfAAoJVyu7jHALgAKQZ-ACc">无量模型压缩和加速技术</a></li><li>量化功能在无量推荐的设计与优化</li><li>推荐全链路</li><li>联合训练和无量实践</li><li>基于Memory Netowrk的推荐系统冷启动方案</li><li>搜推广meta-learning技术调研</li><li>搜推广跨场景联合层次MTL学习技术调研</li><li>使用无量框架训练learning-to-rank模型</li><li>基于梯度的特征重要度算法实践</li></ul></div>				</div>
