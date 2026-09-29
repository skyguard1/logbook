---
title: "DeepFM模型-模型实践篇"
date: 2022-04-15 11:38:24
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<p>先上代码传送门：[内部或本地链接已移除]</p>
<div>
<p><strong>第一部分：FM算法介绍</strong></p>
<p>Logistic Regression是CTR预估中最常用的算法。但LR有一个大前提，即假设特征之间是相互独立的，没有考虑特征之间的相互关系。换句话说，LR在模型侧忽略了feature pair等高阶信息。比如，在一些场景下，我们发现用户年龄和性别是十分重要的特征，但LR只能单独处理这2个特征，比如女性比男性点击率高，年纪越小点击率高。如果需要得到20-30岁的女性，15-20岁男性点击率高这样更精确的组合特征，需要人工对两个特征进行交叉。两个特征尚能做人工的交叉，但几十维的特征两两交叉起来，特征工程将会十分巨大。所以FM算法在CTR预估中才会比较重要。FM简要思路参考：</p>
<p>假设LR算法决定追加考虑任意两个特征之间的关系，则模型改写成：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/9a24df8790c751994592.png"/>   (1)</p>
<p>其中 <img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/757f7c78ae0b2b2fe322.png"/>是feature pair  <img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/825a72684be9aaadef28.png"/>的交叉权重。相对于lr模型，（1）会有如下问题：</p>
<p>1）  参数空间大幅增加，由线性增加至平方级；</p>
<p>2）  样本比较稀疏。</p>
<p>因此，我们需要一种在模型侧计算高阶信息的低复杂度方法。Factorization Machine就是其中一种方法，它把<img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/757f7c78ae0b2b2fe322.png"/>分解成2个向量<img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/68a8a683a57c9413635e.png"/>：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/8130e2e767967f16e5ea.png"/> （2）</p>
<p>直观来看，FM认为当一个特征 <img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/53d4cd20aa87af22cc57.png"/>需要与其它特征<img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/f89789b44a33b5809877.png"/>考虑组合特性的时候，只需要一组k维向量 <img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/597fb53ff5857e442d6b.png"/>即可代表 <img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/53d4cd20aa87af22cc57.png"/> ，而不需针对所特征分别计算出不同的组合参数 <img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/757f7c78ae0b2b2fe322.png"/>。这相当于将特征映射到一个k维空间，用向量关系表示特征关系。这种思想与矩阵分解（SVD）一致。</p>
<p><strong>第二部分：DeepFM算法介绍</strong></p>
<p>FM算法考虑到了低阶特征的组合问题，但是无法解决高阶特征的挖掘问题，所以才有引入<strong>DeepFM</strong>的必要性。</p>
<p>DeepFM是一个集成了FM和DNN的神经网络框架，思路和的Wide&amp;Deep有相似的地方，Wide&amp;Deep都包括wide和deep两部分。W&amp;D模型的wide部分是高维线性模型，DeepFM的wide部分则是FM模型；两者的deep部分是一致的，都是dnn层。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/d272d5942e61f93bc78b.jpg"/></p>
<p>图：网络左边为fm层，右边为dnn层</p>
<p>W&amp;D模型的输入向量维度很大，因为wide部分的特征包括了手工提取的pairwise特征组合，大大提高计算复杂度。和W&amp;D模型相比，<b>DeepFM</b><b>的wide</b><b>和deep</b><b>部分共享相同的输入，可以提高训练效率，不需要额外的特征工程</b>，用FM建模low-order的特征组合，用DNN建模high-order的特征组合，因此可以同时从raw feature中学习到low-和high-order的feature interactions。在真实应用市场的数据和criteo的数据集上实验验证，DeepFM在CTR预估的计算效率和AUC、LogLoss上超越了现有的模型（LR、FM、FNN、PNN、W&amp;D）。</p>
<p><strong>第三部分：撸代码</strong></p>
<p>前面两部分简单介绍了deepfm算法，理论归理论，对于业务侧的同学，可能更加重要的是如何实现。上文提到W&amp;D模型在tensorflow的高阶api中已经有了很完善的封装接口（可参考https://www.tensorflow.org/versions/r1.6/api_docs/python/tf/estimator/DNNLinearCombinedClassifier）。但deepfm还没有比较完善的api，所以还需要自己动手实现他，不过这也意味着有更强的扩展性。其实使用tensorflow写deepfm的网络结构写起来并不复杂，下面开始正式撸代码，加了详细的注释。</p>
<p>1）  实现fm中的一阶部分：</p>
<p>Fm中一阶部分很简单，和lr类似，主要是将特征分别乘上对应的系数：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/49742efb22ea7541a81e.png"/></p>
<p>对应下面网络图中红框部分：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/e6ca2f84604502d77961.png"/></p>
<p>网络结构代码实现：</p>
<div>
<pre>        # ---------- first order term ----------
        ##初始化wij
        feature_bias = tf.Variable(tf.random_uniform([feature_size, 1], 0.0, 1.0), name="feature_bias_0")  # feature_size * 1
        y_first_order = feature_bias
        ## wij * xij 
        y_first_order = tf.reduce_sum(tf.multiply(y_first_order, feat_value), 2)  # None * F
        ## 增加dropout，防止过拟合
        y_first_order = tf.nn.dropout(y_first_order, dropout_keep_fm[0]) # None * F</pre>
</div>
<p> </p>
<p><strong>2）  实现fm中的二阶部分：</strong></p>
<p>Fm中二阶部分，主要是对<img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/53d4cd20aa87af22cc57.png"/>和<img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/37bebb91845ec0bf7584.png"/>两两组合，并且找到他们分别对应的特征向量。</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/766ab84c09354ac32a01.png"/></p>
<p>对应下面网络图的红框部分：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/04f73b0ca40ea4d7933e.png"/></p>
<p>为了更方便实现二阶部分，我们进一步进行推导：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/74942c1662199d9a98fe.png"/></p>
<p>最后转化为和平方与平方和两部分</p>
<p>网络结构代码实现：</p>
<div>
<pre>        # ---------- second order term ---------------
        #vi*xi
        embeddings = tf.multiply(embeddings, feat_value)
        # 和平方
        summed_features_emb = tf.reduce_sum(embeddings, 1)  # None * K
        summed_features_emb_square = tf.square(summed_features_emb)  # None * K

        # 平方和
        squared_features_emb = tf.square(embeddings)
        squared_sum_features_emb = tf.reduce_sum(squared_features_emb, 1)  # None * K

        # 和平方与平方和按公式组合
        y_second_order = 0.5 * tf.subtract(summed_features_emb_square, squared_sum_features_emb)  # None * K
        y_second_order = tf.nn.dropout(y_second_order, dropout_keep_fm[1])  # None * K</pre>
</div>
<p> </p>
<p><strong>3）  实现DNN：</strong></p>
<p>传统的多层感知机，增加dropout防止过拟合。</p>
<div>
<pre>    with tf.name_scope("deep"):
        
        # ---------- Deep component ----------
        y_deep = tf.reshape(embeddings, shape=[-1, feature_size*embedding_size]) # None * (F*K)
        y_deep = tf.nn.dropout(y_deep, dropout_keep_deep[0])
        
        weights = dict()
        ##初始化各层的权重
        input_size = feature_size * embedding_size
        glorot = np.sqrt(2.0 / (input_size + deep_layers[0]))
        weights["layer_0"] = tf.Variable(
            np.random.normal(loc=0, scale=glorot, size=(input_size, deep_layers[0])), dtype=np.float32, name="weights_layer0")
        weights["bias_0"] = tf.Variable(np.random.normal(loc=0, scale=glorot, size=(1, deep_layers[0])),
                                                        dtype=np.float32,name="weights_bias0")

        num_layer = len(deep_layers)
        for i in range(1, num_layer): 
            glorot = np.sqrt(2.0 / (deep_layers[i-1] + deep_layers[i]))
            weights["layer_%d" % i] = tf.Variable(
                np.random.normal(loc=0, scale=glorot, size=(deep_layers[i-1], deep_layers[i])),
                dtype=np.float32 ,name="weights_layer"+str(i))  # layers[i-1] * layers[i]
            weights["bias_%d" % i] = tf.Variable(
                np.random.normal(loc=0, scale=glorot, size=(1, deep_layers[i])),
                dtype=np.float32 ,name="weights_bias"+str(i))  # 1 * layer[i]
        ##对dnn的各层进行连接        
        for i in range(0, len(deep_layers)):           
            y_deep = tf.add(tf.matmul(y_deep, weights["layer_%d" %i]), weights["bias_%d"%i]) # None * layer[i] * 1
                #if self.batch_norm:
                #    self.y_deep = self.batch_norm_layer(self.y_deep, train_phase=self.train_phase, scope_bn="bn_%d" %i) # None * layer[i] * 1
            y_deep = tf.nn.relu(y_deep)
            y_deep = tf.nn.dropout(y_deep, dropout_keep_deep[1+i]) # dropout at each Deep layer</pre>
</div>
<p> 这里对权重初始化使用了glorot根据输入与输出层的神经元个数进行分布初始化，减少梯度爆炸和梯度弥散的风险。</p>
<p><strong>4）  dnn+fm融合</strong></p>
<p>将两者的输出进行连接，并线性组合起来，通过sigmoid函数转换成最后的得分。</p>
<p>如果是deep与fm融合，则将2个部分的输出进行concat，如果只是单一的dnn或者fm则只用一部分的输出。代码中由<code>MODETYPE控制网络类型。</code></p>
<div>
<pre>    # ---------- DeepFM ----------
    with tf.name_scope("deepfm"):
        concat_input = tf.concat([y_first_order, y_second_order, y_deep], axis=1)
        if MODETYPE==0:##deepfm
            concat_input = tf.concat([y_first_order, y_second_order, y_deep], axis=1)
            input_size = feature_size + embedding_size + deep_layers[-1]
        elif MODETYPE==1:##fm only
            concat_input = tf.concat([y_first_order, y_second_order], axis=1)
            input_size = feature_size + embedding_size 
        elif MODETYPE==2:##dnn only
            concat_input = y_deep   
            input_size =  deep_layers[-1]
        
        glorot = np.sqrt(2.0 / (input_size + 1))
        weights["concat_projection"] = tf.Variable(np.random.normal(loc=0, scale=glorot, size=(input_size, 1)),
                        dtype=np.float32 ,name="concat_projection0")  # layers[i-1]*layers[i]
        weights["concat_bias"] = tf.Variable(tf.constant(0.01), dtype=np.float32 ,name="concat_bias0")    
        out = tf.add(tf.matmul(concat_input, weights["concat_projection"]), weights["concat_bias"],name='out')

    score=tf.nn.sigmoid(out,name='score')
    ##观看变量
    tf.summary.histogram("deep+fm"+"/score",score) </pre>
</div>
<p><strong>5）  评估器的设计</strong></p>
<p>自定义损失函数，常用的损失函数最小平方误差准则（MSE）和交叉熵等等：</p>
<div>
<pre>    if args.model_type==0:
        estimate_name="DeepFm_Estimate"
    elif args.model_type==1:
        estimate_name="Fm_Estimate"
    elif args.model_type==2:
        estimate_name="Deep_Estimate"
        
    with tf.name_scope(estimate_name):
        # 损失函数的定义：均方差
        loss = tf.reduce_mean(tf.reduce_sum(tf.square(y - prediction),reduction_indices=[1]))
        ##观看常量
        tf.summary.scalar('loss',loss)
        
        auc = tf.contrib.metrics.streaming_auc(prediction,tf.convert_to_tensor(y))   
        ##观看常量
        tf.summary.scalar('auc1',auc[0])
        tf.summary.scalar('auc2',auc[1])</pre>
</div>
<p> </p>
<p><strong>6）  通过tensorboard观察模型各项指标：</strong></p>
<p>在前面的模型结构构建过程中，我们已经在tf.summary中增加score、loss、auc的监控。训练迭代过程中，我们注意将每次的中间结果merge进去，即可在tensorboard中观察收敛过程。（tensorboard真的很方便~~）</p>
<div>
<pre>    with tf.Session() as sess:
        saver = tf.train.Saver()
        sess.run(init)
        sess.run(tf.local_variables_initializer())
        #合并到Summary中    
        merged = tf.summary.merge_all()    
        #选定可视化存储目录  
        writer = tf.summary.FileWriter('./tmp/deepfm',graph=tf.get_default_graph())
        
        
        for _ in range(400):
            sess.run(train_step, feed_dict={x: x_data, y: y_data})
            if _ % 5 == 0:
                #print(str(_)+":loss=")
                print("[%d]loss:%s"%(_,sess.run(loss, feed_dict={x: x_data, y: y_data})))
                result = sess.run(merged,feed_dict={x: x_data, y: y_data}) #merged也是需要run的    
                writer.add_summary(result,_) #result是summary类型的，需要放入writer中，i步数（x轴）</pre>
</div>
<p> Loss和auc的变化：可以看到deepfm比fm有显著提升，对比DNN也有一定幅度提升。使用相同数据训练，在测试集上dnn0.73,deepfm0.75,fm0.70（特征工程仍然是最重要的，特征越多，差异越明显）</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/74d7c05101a14c27e30f.png"/></p>
<p>不同迭代次数后，观察score的分布结果：</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/c400bd2cd90b24915d0d.png"/></p>
<p><strong>7）  graph结构：</strong></p>
<p>最后我们回顾一下上面创建的graph结构，短短几百行代码就构造了看起来还挺复杂的网络^^，这也是tensorflow的强大之处。</p>
<p><img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/4f0caf4db380654c468d.png"/></p>
<p></p>
<p>预告：deepfm模型—线上部署篇</p>
<p></p>
<p>参考：</p>
<p>[1] A Factorization-Machine based Neural Network for CTR Prediction<a href="https://arxiv.org/abs/1703.04247">https://arxiv.org/abs/1703.04247</a></p>
<p>[2] https://zhuanlan.zhihu.com/p/27999355</p>
</div> 
{% endraw %}
