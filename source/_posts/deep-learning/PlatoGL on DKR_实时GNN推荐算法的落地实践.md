---
title: "PlatoGL on DKR_实时GNN推荐算法的落地实践"
date: 2022-04-19 19:07:01
categories:
  - deep-learning
---

{% raw %}

<h2>一、背景</h2>
<p>图作为一种数据结构，相比二维矩阵数据能蕴含更丰富更高阶的信息，然而图数据的处理（图特征表达）算法也更为复杂。我们团队尝试将用户行为数据表达为一张多源异构图，并利用GNN模型进行图特征的表达，从而进行用户行为预测。目前我们在跨域推荐的任务上取得不错的效果，跨域推荐问题上GNN算法的设计可参考文章[1]。文章[2]介绍了PlatoGL工程系统的设计理念。本文将从算法工作者的角度来介绍，怎么利用PlatoGL和笛卡尔平台（下文简称DKR）来落地实现推荐业务上的GNN模型服务的全流程pipline（简称PPL）：包括数据准备、模型训练、模型上线推理和模型运维。本文分为三个部分：第一部分主要介绍实时GNN推荐算法落地PPL的概貌，并且给出PlatoGL on DKR的框架示意图。第二部分对实时GNN推荐算法PPL进行详细的介绍，分为数据准备、模型训练、模型上线和模型运维四小节。第三部分总结当前落地PPL的优点及后续的改进点。</p>
<p>本文由chrisyi、drolcaqiu和nickgu共同撰写，特别感谢chuanchen提供修改意见。</p>
<h2><strong>二、DKR 的全流程作业PPL</strong></h2>
<p>DKR是微信数据中心为算法同学打造的高效作业平台，基于DKR平台算法同学可以完成多种类型的作业。PlatoGL on DKR为团队同学提供一个高效的图深度学习作业平台，其基本框架图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/286a0cf0866e07d8068f.png"/></p>
<p>图1  PlatoGL on DKR基本框架图</p>
<p>本文的第二部分以一个实时的GNN推荐算法的落地为例，对全流程PPL即数据准备、模型训练、模型上线及模型运维进行详细展开<strong>。</strong>全流程PPL的示意图如下：<br/><img alt="" loading="lazy" src="/logbook/images/deep-learning/66aebc0f4b79211c2346.png"/></p>
<p>图2  PlatoGL on DKR全流程PPL</p>
<h2><strong>三、PlatoGL on DKR：实时GNN算法落地实践</strong></h2>
<h3><strong>图数据准备</strong></h3>
<p>对于实时推荐系统的数据准备来说，我们会使用到spark、puslar，Flink组件。对于S实时GNN模型的基础数据，我们需要做到特征数据的实时性和训练样本的实时性。同时，需要防止出现两个问题，一是防止线上线下不一致，二是防止数据穿越。对于图数据存储，如文章[2]中所介绍，我们使用了mkvGraph。其数据流如下：原始数据会按格式分别经过实时流处理或离线批处理成图结构数据，随后调用图存储接口最终写入mkvGraph，这份KV数据会提供给线上服务查询使用（直播精排、召回模块等）。 </p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/435eaca56156333f5c70.png"/></p>
<p>图 3 mkvGraph数据处理流程</p>
<p>mkvGraph支持多种时间粒度的更新。对于离线批处理数据：按天/周/月粒度准备topo数据&amp;节点feature数据，离线批量导入mkv集群，方便历史数据回溯&amp;大批量数据更新。对于实时流处理数据：行为log接入pulsar流，flink实时抽取交互行为数据，构造成图topo数据/图节点特征后写入mkv集群。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/c4944a814f63fe9620e8.png"/></p>
<p>图 4 实时数据流写入流程</p>
<p>常用的mkvGraph接口包括全量或者增量新增/删除节点和边，批量查询Neighnors等多种算法，详情见[内部或本地链接已移除]</p>
<p>把数据存储到mkvGraph时，在训练GNN模型的时候，基于mkvgraph的原始数据加入了保证线上线下一致性和防止数据穿越的逻辑：</p>
<ul><li><strong>线上线下一致性：</strong>实时训练和实时推荐的GNN模型同时访问同一mkvGraph存储，保证一致性。</li>
<li><strong>防穿越逻辑</strong>：由于实时数据的写入，训练任务针对当前样本学习时有可能采样到当前样本时间之后的数据，所以mkvGraph内会保存topo数据的行为时间（create_timestamp），训练时仅抽取数据行为时间小于当前样本时间的topo数据防止特征穿越。</li>
</ul><h3><strong>GNN模型训练</strong><em><br/></em></h3>
<p>GNN模型的训练环境由数据中心的PlatoGL和DKR平台构成，其中PlatoGL提供实时的图存储和模型训练框架，DKR平台提供模型训练任务调度的能力。基于<strong>PlatoGL on DKR</strong>，算法同学可以直接通过编写tensorflow代码完成一个GNN模型的开发到最终上线，整个实时GNN模型训练流程如下：</p>
<p><em><img alt="" loading="lazy" src="/logbook/images/deep-learning/50281231543e141774b2.png"/></em></p>
<p>图 5 实时模型训练流程图</p>
<p>模型训练的时候，我们先从实时样本流（pulsar）中取出一个batch的实时样本，过滤拿到对应的user_id和item_id，再去实时图存储mkvGraph中查询需要的实时图数据（包括邻居、点特征和边特征），将实时样本流中的特征和实时查询得到的图数据一起输送给模型，进行接下来的计算。我们将读取实时样本和实时查询图数据的部分放入tf.dataset中，将GNN模型的卷积计算+模型逻辑放入model_fn中，将整个训练流程丝滑嵌入到tensorflow的estimator训练框架中；我们将公共部分抽取出来在DKR平台上沉淀为算法节点，算法同学在开发过程中只需要补充部分tensorflow代码即可拉起一个实时GNN模型的训练流程。</p>
<p>对于GNN模型，计算所需要的数据主要包括邻居节点、节点特征、边信息和边特征，为了方便计算，我们直接将所需要的全部数据全部封装在egoGraph结构类中，给到模型使用，接下来简单介绍一下。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/29e7406297d9a9682d6e.png"/></p>
<p>图 6 egoGraph结构类示意图</p>
<ul><li><strong>邻居采样：</strong>GNN计算需要的数据采用按层采样的方式被处理成一个一个的egoGraph结构，每一层的采样根据算法设计的不同，支持放回和不放回采样，最终将全部的egoGraph组合成为egoGraphGroup结构，作为tf.dataset的输出给到模型进行计算，如图所示，每一个egoGraph结构包括了每一层的节点id、特征和每两层节点之间的边信息、特征。考虑到GNN计算的二维稀疏性，PlatoGL支持使用Attributed CSR/COO两种格式来存储边数据，并且提供两种格式相互转换的算子，满足大部分计算场景。</li>
</ul><p><img alt="" loading="lazy" src="/logbook/images/deep-learning/eb5c3d4945e13a53a147.png"/>图 7  CSR/COO数据格式</p>
<ul><li><strong> 邻居聚合和更新：</strong>针对稀疏边的格式，PlatoGL提供高性能的聚合算子来帮助实现GNN的聚合函数。比如reduce_mean卷积算子和reduce_sum卷积算子需要用到的u_gather_v、u_gather_v_reduce_sum和attention卷积算子需要用到的u_gather_v_mul_e_reduce_sum带权聚合，利用这些算子可以轻松的实现GNN算法中各种各样的卷积函数。</li>
</ul><p>目前，PlatoGL上实现一些学术界较常用的GNN算法作为baseline提供给大家，后续我们会将文章[1]中提到的在业务上取得收益的算法进行开源，在下面的地址开源：[内部或本地链接已移除]。其次，算法同学也可以基于PlatoGL的采样算子和聚合算子自行设计开发更加适合自己业务的图算法。</p>
<h3><strong>GNN模型上线</strong></h3>
<p>GNN模型的上线使用到了DKR原有的模型发布功能。首先PlatoGL将所有的图采样和对应的卷积计算操作封装成为了tensorflow的算子，所以可以直接利用tf直接封装好的的serving能力，我们直接将训练好的GNN模型导出为SavedModel格式，SavedModel 格式是tensorflow 2.0 推荐的格式，它很好地支持了tf-serving部署。一个 SavedModel 包含了一个完整的 TensorFlow program, 包含了全部变量以及模型的计算图. 它不需要原本的模型代码就可以加载并进行预测。所以，模型所需要的图数据的采样过程以及GNN相关算子的计算也全部会作为计算图的一部分，封装保留在savedmodel文件中，我们在预测的时候，只需要保证mkvGraph的稳定服务，对于每一个线上请求，模型会按照训练定义好的计算图执行路径，从mkvGraph拿到对应节点的egoGraphGroup数据，并进行预测打分。目前实时GNN模型运行在DKR上，上线方式采用直接页面交互式操作，非常便捷。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/7297934ae76d464daa54.png"/></p>
<p>图 8  实时GNN精排模型的线上serving流程</p>
<p>上图给出了一个实时GNN精排模型的线上serving流程，可以看到，整个流程和在推荐系统中已经广泛应用的实时DNN类型模型上线方式基本一致，可以上线任何支持在线tf-serving的模块。</p>
<p>对于召回模型的上线方式，可以分为两部分，第一部分，模型会定时拉取全量推荐池中的item，对这些item进行预测，产出item_emb，写入到微信高性能特征检索SimSvr服务中，当一个用户的请求过来时，通过模型serving得到user_emb，再去simsvr检索服务中检索出top N，作为一路召回提供给精排模型。<br/><img alt="" loading="lazy" src="/logbook/images/deep-learning/6aa46866096176dcd2cd.png"/></p>
<p>图 9  实时GNN召回模型的线上serving流程<br/></p>
<h3><strong>模型运维</strong></h3>
<p>对算法工作者而言，模型上线之后，如何高效地保证模型服务的稳定性也是一大挑战。我们主要由DKR平台和全景视图来完成。DKR平台结合全景视图对特征数据的运行时间、运行结果进行了监控，并且算法同学可以根据任务的实际情况开启告警功能。对于模型的运行，算法人员也可以对其输入数据，比如特征的pk数，有效sk数进行监控，对模型训练的结果auc、gauc进行监控告警，形成一整套高效的运维工具，保证模型服务的稳定性。</p>
<h2><strong>四、小结</strong></h2>
<p>本文主要介绍算法同学基于PlatoGL on DKR 来完成一个在实时推荐GNN算法的落地。包括数据准备、模型训练、模型推荐、和模型运维这一整条操作PPL。整个PPL使用到了的组件，包括数据中心的Pulsar组件，Flink组件，DKR调度平台、PlatoGL训练引擎、基础架构中心的存储组件mkvGraph和Weps、和测试中心的全景监控视图。</p>
<p>对于算法同学来说PlatoGL on DKR这整套PPL也具备几个非常显著的优点：</p>
<ol><li>首先是支持直接实时训练和实时推荐的图推荐算法平台，其优秀的高性能已经在直播、订阅号等业务上上线，完全满足线上的性能要求。</li>
<li>可快速复用的数据准备节点极大地提高了算法同学的工作效率，多元丰富的大数据组件，也支持算法同学进行更复杂的、定制化的数据准备工作。</li>
<li>内置了经典的GNN算法训练节点，同时算法同学也可以基于基础算子灵活编写图算法。</li>
<li>内置了评测节点，并且提供了基准的图数据集用于算法评测。</li>
<li>提供了模型上线服务的诸多周边功能，包括训练监控、效果评测、版本管理等。</li>
</ol><p>最后，非常感谢上述组件团队对PlatoGL on DKR的支持，也欢迎业务团队的算法同学接入PlatoGL on DKR试用。</p>
<p><strong>参考资料</strong></p>
<p>1. 跨域推荐：异构GNN推荐算法：[内部或本地链接已移除]</p>
<p>2.PlatoGL：主攻GNN实时推荐的新一代图深度学习框架：[内部或本地链接已移除]</p> 
{% endraw %}
