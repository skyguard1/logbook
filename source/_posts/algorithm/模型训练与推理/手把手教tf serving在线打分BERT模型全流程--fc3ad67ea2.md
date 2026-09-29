---
title: "手把手教tf serving在线打分BERT模型全流程"
date: 2022-03-31 10:53:45
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<p>先介绍下整个流程，以及通过venus怎么做到配置作业将Tensorflow模型上线</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b8065186d7cac0dd0a9e.png"/></p>
<p>对模型训练有疑问的参考BERT在Venus上训练。模型训练后的checkpoint文件在ceph上，可通过tf作业模型导出和预测，导出的文件在ceph上，然后同步到hdfs,之后通过taf.wsd.com发布到sumeru。服务启动后用户通过python脚本调http协议获取返回结果。</p>
<p>一.模型导出部分</p>
<p>Tensorflow serving对Tensorflow模型的打分最好将checkpoint模型导出pb(protocol buffer)文件。导出过程需要将BERT模型的输入和输出指定。比如：</p>
<div>
<pre>model_signature = tf.saved_model.signature_def_utils.build_signature_def(
          inputs={                  #输入格式
              "input_ids": tf.saved_model.utils.build_tensor_info(features['input_ids']),
              "input_mask": tf.saved_model.utils.build_tensor_info(features['input_mask']),
              "segment_ids": tf.saved_model.utils.build_tensor_info(features['segment_ids']),
              "label_ids": tf.saved_model.utils.build_tensor_info(features['label_ids'])
          },
          outputs={               #输出格式
              "probabilities": tf.saved_model.utils.build_tensor_info(probabilities)
          },
          method_name=tf.saved_model.signature_constants.PREDICT_METHOD_NAME
      )</pre>
</div>
<p>BERT模型输入需要指定网络输入的tensors，输出属于垃圾或者非垃圾数据的概率。模型导出之后有一个variables的文件夹用于存储模型中参数变量的值，以及一个.pb文件用于保存模型结构。假设保存到 /data/tf-serving/new/serving/saved_cpu_model/ 目录下，新建目录 201901，然后copy上述模型导出文件到该目录下。取名模型名称:10659,模型版本：201901</p>
<p>二，ceph同步hdfs</p>
<p>使用组件文件导入到hdfs文件。具体配置详见 <a href="http://doc.venus.wsd.com/datasets/sync-clusters.html">文件导入到hdfs文件</a></p>
<p>三，模型从hdfs导出sumeru</p>
<p>此步骤使用发布数据到sumeru组件，组件配置之前需要先用taf + tensorflow serving部署服务。</p>
<p>Tensorflow serving的安装环境比较复杂，安装完之后将其保存成一个镜像，这里保存成：tafimage/venus_tfserving_cuda9_predict:20180802175634      在sumeru上部署taf + tensorflow serving服务和部署taf服务类似，部署taf方法参考 部署taf step by step 。</p>
<p>步骤一：taf开发及配置</p>
<p>本文使用taf框架的java-httpwebservice 开发，代码上传到git用于发布，核心是要通过 函数调起tensorflow serving服务</p>
<div>
<pre>nohup ${TF_SERVING_BIN} --port=${TF_SERV_PORT} --rest_api_port=${TF_SERV_HTTP_PORT} --model_config_file=${TF_SERVING_CONF} &gt;&gt;${TF_SERVING_LOG} 2&gt;&amp;1 &amp;
</pre>
</div>
<p> 以下截图是手把手教怎么从taf发布一个BERT在线服务（测试环境 147.taf.wsd.com-&gt;流程工具-&gt;taf服务上线-&gt;docker服务上线），配置虚拟OBJ：TFServingHTTPObj用于http服务请求。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/c8e6dff5f2707f609e65.png"/></p>
<p>将代码发布git地址填上，用于编译和发布</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/7c0c43959026e780bc58.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/691cc3c3516d8ade00b3.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/520448bc70f00d5c05cf.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2a3e72091e6c5a537f12.png"/></p>
<p>服务配置</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2504fe91dfed26b32610.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4653894820da7ba63db3.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a6d10e44ac6cd6ab82b7.png"/></p>
<p>数据、模块配置</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e807a4a445cd2591925b.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/b2a39ffca2dc9f90031b.png"/></p>
<p>点数据文件上传和修改模块配置还可继续改，改完点发布按钮。此时测试环境的bert服务开始启动了。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/da5d97266d0b9f1fc9cf.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2ecabfe2f3aef0a8de3b.png"/></p>
<p>可./go -d 容器名，到~/taf/app_log/TFCommonServing/bertServing]$ cat tensorflow_serving.log，查看服务运行日志</p>
<p>步骤二：使用restful接口，可以用sparta配置域名或者配置名字服务访问，一般调用类域名不允许走sparta</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/c0c511aebb293680d673.png"/></p>
<p>名字服务可参考名字发现服务</p>
<p>四. 脚本调用</p>
<p>可以用taf服务或者python脚本用来调起http协议，下面讲一下怎用python脚本调服务。脚本有两种服务调取方式，grpc和restful两种接口。附件提供两种调用的脚本代码，这里介绍下</p>
<div>
<pre>POST http://host:port/&lt;URI&gt;:&lt;VERB&gt;     #host 宿主机IP port 端口号  
URI: /v1/models/${MODEL_NAME}[/versions/${MODEL_VERSION}]  #MODEL_NAME 模型名称  MODEL_VERSION 模型版本
VERB: classify|regress|predict            #serving_default使用python脚本post请求，请求的url为 http://host:port/&lt;URI&gt;:&lt;VERB&gt;
使用脚本处理预测数据写入json</pre>
<div>
<pre>data_json = {"signature_name": 'serving_default', "instances": [{"input_ids": predict_input_fn["input_ids"], "input_mask": predict_input_fn["input_mask"], "segment_ids":predict_input_fn["segment_ids"], "label_ids":predict_input_fn["label_ids"]}]}BERT垃圾过滤服务耗时：
        打分速度平均60ms/条，并发调用每秒可处理&gt;100条。</pre>
</div>
<p> </p>
</div> 
{% endraw %}
