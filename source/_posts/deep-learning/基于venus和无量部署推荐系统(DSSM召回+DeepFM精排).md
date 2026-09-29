---
title: "基于venus和无量部署推荐系统(DSSM召回+DeepFM精排)"
date: 2022-04-18 15:18:29
categories:
  - deep-learning
---

{% raw %}

<h1><img alt="" loading="lazy" src="/logbook/images/deep-learning/2484b397c2003ac962cb.png"/></h1>
<p>推荐系统主要分为召回和排序两大阶段。在实际生产环境中需要部署召回模型和排序模型。venus是公司内部较为成熟的机器学习平台，且能较好地支持模型部署。鉴于km上现有文章零散不全，本文将介绍使用venus部署DSSM双塔召回模型和DeepFM精排模型的完整推荐系统流程，希望能帮助大家快速地搭建出一个简单的推荐系统。文末附件提供模型代码和客户端示例代码。</p>
<table><tbody><tr><td></td>
<td>
<p><b>在线学习</b></p>
</td>
<td>
<p><b>运维现状</b></p>
</td>
<td>
<p><b>已接入业务</b></p>
</td>
<td>
<p><b>数据接入</b></p>
</td>
</tr><tr><td>
<p>venus</p>
</td>
<td>
<p>支持</p>
</td>
<td>
<p>成熟运维</p>
</td>
<td>
<p>大规模使用</p>
</td>
<td>
<p>支持hdfs,kafka,cdmq,atta等</p>
</td>
</tr><tr><td>
<p>太极</p>
</td>
<td>
<p>支持</p>
</td>
<td>
<p>不成熟</p>
</td>
<td>
<p>广告推荐</p>
</td>
<td>
<p>支持hdfs, tdw等</p>
</td>
</tr><tr><td>
<p>Oceanus-ml</p>
</td>
<td>
<p>支持</p>
</td>
<td>
<p>不成熟</p>
</td>
<td>
<p>未大规模使用</p>
</td>
<td>
<p>支持hdfs,kafka,Mysql,Hbase等</p>
</td>
</tr></tbody></table><h1></h1>
<h1><img alt="" loading="lazy" src="/logbook/images/deep-learning/65265ddd8b0a058f30c3.png"/></h1>
<p>update：附件中的dssm.py和DeepFM.py都已经支持无量0.5.0哦</p>
<h1>1.准备数据</h1>
<p>本文使用MovieLens-1M公开数据集，可前往<a href="https://files.grouplens.org/datasets/movielens/ml-1m.zip">https://files.grouplens.org/datasets/movielens/ml-1m.zip</a>下载。MovieLens-1M数据集包含约6000个用户对约4000部电影的1百万条评分记录。并提供了用户的如下信息：用户id、性别、年龄、职业、邮政编码，以及电影的如下信息：电影id、电影标题、电影类型。</p>
<p>为简单起见，我们将用户的id、性别、年龄、职业、邮政编码输入双塔模型的用户塔，用来生成user vector; 将电影id输入双塔模型的物品塔，用来生成item vector。</p>
<p>首先，我们需要对原始数据进行处理，生成符合无量输入格式的数据。</p>
<div>
<div>
<div>
<div>
<table><tbody><tr><td>
<div>
<div><code>additional_Info|label|key:slotid:value;key:slotid:value;...key:slotid:value</code></div>
</div>
</td>
</tr></tbody></table></div>
</div>
</div>
</div>
<p>1) 其中additional_Info是样本描述信息，可以是一串数字或者字符，建议填入item_id，便于后续生成item vector；</p>
<p>2) label是样本的标签值；</p>
<p>3) 在key:slotid:value中，slotid代表特征，是特征的数字化表示（即不同的slotid代表不同的特征），key代表特征值的位置，value代表特征值的大小。key定义为int64整型，目前默认只用低48位表示key的大小，高16位是保留位，作为其他用途。</p>
<p>[图片未保存到本地]</p>
<p></p>
<p>若一条样本有两个特征，label为0，slotid为1的特征用dense的表示方式（假设有5维，值为1到5），slotid为3的特征用sparse的表示方式（假设只有第10和11的位置有值，值为1），那么这个样本表示为：</p>
<p>additional_Info|0|0:1:1;1:1:2;2:1:3;3:1:4;4:1:5;10+3×2^32:3:1;11+3×2^32:3:1</p>
<p>这里可能感到疑惑的地方在于slotid为3的特征的sparse表示为什么不是10:3:1;11:3:1，而是10+3×2^32:3:1;11+3×2^32:3:1。这样做的原因是为了保证不同特征的取值是唯一的，对于sparse表示方式的特征，key值通过下图方式得到，图示中的subkey指的是特征的取值（如这里的10和11），也就是说key值会由slotid的取值和特征取值共同决定。可以看到，key是包含了slotid的信息的，之所以显式地将slotid表示出来（key:slotid:value），是为了算法人员能更加直接地获取slotid信息并用于分析。Note: 高16位是保留位，暂时没有用到。</p>
<p></p>
<p>代码见文末附件gen_hdfs_data.py, 我们为各特征设置slot_id如下：</p>
<p>1:user_id; 2:movie_id; 3:gender; 4:age; 5:occupation; 6:zip</p>
<p></p>
<p>数据需按照如下格式存放。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/656c482025d0c6d62ce9.png"/></p>
<p>笔者将数据存放到了cfs上，接下来我们把cfs上的数据同步到hdfs上，该步骤可使用venus提供的”文件同步到集群”组件(位于venus的ETL目录下)。</p>
<p>请先做好以下准备：</p>
<ul><li>CFS资源申请及在venus使用</li>
<li>在此处创建自己的hdfs路径</li>
</ul><p>组件填写示例：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/fb2c549d13961069d794.png"/></p>
<p></p>
<h1>2.训练DSSM模型</h1>
<p>dssm双塔模型是目前工业界广泛应用的召回模型，网络结构图如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/9cbbf640d954094fce59.png"/></p>
<p>我们选择“推荐中台”目录下的“无量2.0”组件。在传入的python文件中，我们需要指定slot_id,这样venus才能正确读取数据。</p>
<p>1:user_id; 2:movie_id; 3:gender; 4:age; 5:occupation; 6:zip</p>
<p>在召回阶段，面对海量的数据，我们需要快速地挑选出用户感兴趣的item, 因此我们需要使用较简单的模型，输入较少的特征。因此，我们选择1，3，4，5，6这5个特征输入user塔， 2这个特征输入item塔。</p>
<div>
<pre>user_slots = ['1', '3', '4', '5', '6'] //

item_slots = ['2'] //

user_embedding_sum_layers = {}
for slot_id in user_slots:
    embedding_w, x_data = numerous.framework.SparseEmbedding(
        embedding_dim=embedding_size,
        optimizer=Adam(rho1=0.99, rho2=0.999, eps=0.0001, time_thresh=5000),
        distribution=numerous.distributions.Uniform(left=-0.001, right=0.001),
        slot_ids=[str(slot_id)],
        use_sparse_placeholder=False)

    embedding = tf.matmul(x_data, embedding_w)
    user_embedding_sum_layers[slot_id] = embedding
user_merge_layers = tf.concat(user_embedding_sum_layers.values(), axis=1)

item_embedding_sum_layers = {}
for slot_id in item_slots:
    embedding_w, x_data = numerous.framework.SparseEmbedding(
        embedding_dim=embedding_size,
        optimizer=Adam(rho1=0.99, rho2=0.999, eps=0.0001, time_thresh=5000),
        distribution=numerous.distributions.Uniform(left=-0.001, right=0.001),
        slot_ids=[str(slot_id)],
        use_sparse_placeholder=False)

    embedding = tf.matmul(x_data, embedding_w)
    item_embedding_sum_layers[slot_id] = embedding
item_merge_layers = tf.concat(item_embedding_sum_layers.values(), axis=1)</pre>
</div>
<p> 在请求服务时，我们需要模型分别返回user vector和item vector, 因此我们可以在模型定义时给相应变量命名，在请求时模型会根据我们传入的name返回相应的变量。</p>
<div>
<pre>u_y_dnn_norm = norm_tensor(u_y_dnn, name="user_vector")
i_y_dnn_norm = norm_tensor(i_y_dnn, name="item_vector")</pre>
</div>
<p>dssm.py见文末附件</p>
<p></p>
<h1>3.生成item vector并写入elasticfaiss集群(即刷库)</h1>
<p>我们使用user vector作为查询向量，寻找与其最接近的N个item vector, 这样就完成了召回。在venus中，我们可以使用“推荐中台”目录下的"召回上线(新)"组件，该组件和旧版的区别在于新版支持trpc。</p>
<p>使用该组件前，需先做好以下准备:</p>
<p>在此处申请trpc服务:[内部或本地链接已移除](需申请两个，一个用于user vector， 一个用于item vector),将申请到的服务id填入即可；</p>
<p>EF集群中填写的64674945:65536为公共测试集群，在测试结束后需要自己申请正式集群。</p>
<p>该组件执行成功后，64674945:65536集群中已经写入了item vector。</p>
<p>我们可以查看集群中写入了多少个item vector, 以验证执行是否成功。</p>
<p>参考EF命令行操作快速上手</p>
<p>运行以下命令：./ef_cli --l5 64674945:65536 info_index --index recall_online_dssm_movie1m</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/55d24da4b02ac5bbaca2.png"/></p>
<p>其中的size即为写入的item vector数量。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/92748c8dc80f861c6703.png"/><img alt="" loading="lazy" src="/logbook/images/deep-learning/cd7494d1b14d93169973.png"/></p>
<p></p>
<h1>4.训练DeepFM模型</h1>
<p>DeepFM模型是工业界比较经典的一个精排算法。该算法将FM算法和神经网络结合，通过FM获取低阶组合特征，DNN获取高阶组合特征并将这些特征融合从而取得了超越前人的效果。</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/be00414e0a9ad6506d3c.png"/></p>
<p>在精排阶段，我们追求的是推荐的准确性，因此可以使用较复杂的模型，输入较多的特征来精准的命中用户的兴趣点。本文为简单起见，仍然使用以下6个特征：1:user_id; 2:movie_id; 3:gender; 4:age; 5:occupation; 6:zip。</p>
<div>
<pre>model_slots = (1,2,3,4,5,6)
# embedding
embedding_sum_layers = {}
for slot_id in model_slots:
    embedding_w, slots1 = numerous.framework.SparseEmbedding(
        slot_ids=[str(slot_id)],
        embedding_dim=embedding_size)
    embedding = tf.matmul(slots1, embedding_w)
    embedding_sum_layers[slot_id] = embedding</pre>
</div>
<p>我们请求服务时，需要模型返回score, 因此我们将我们想要获得的变量y_pred(即score)命名为“prob",在请求服务时传入"prob"即可获得模型返回的score.</p>
<div>
<pre>y_pred = tf.sigmoid(logits, name = "prob")</pre>
</div>
<p>  deepfm.py见文末附件。</p>
<h1>5.客户端调用</h1>
<p>在客户端代码中，我们编写如下流程：</p>
<p>读取特征-&gt;请求召回模型服务返回user vector-&gt;从elasticfaiss中查询距离最近的100个item vector-&gt;请求精排模型打分服务-&gt;返回打分最高的10个item; </p>
<p>代码见</p>
<p>[内部或本地链接已移除]</p>
<p>[内部或本地链接已移除]</p>
<p><img alt="" loading="lazy" src="/logbook/images/deep-learning/1fca834730620b5ef9d9.png"/></p>
<p></p>
<p>至此，一个完整而简单的推荐系统就搭建完成了。</p> 
{% endraw %}
