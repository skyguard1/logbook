---
title: "tensorflow模型训练到上线全流程"
date: 2022-03-31 10:04:52
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<p>一.tensorflow模型的训练</p>
<p>以mnist手写字体数据集为例，使用dnn模型训练tensorflow模型。</p>
<p>代码中有两部分是为后续服务的：</p>
<p>1.保存tensorflow serving所需的pb格式</p>
<div>
<div>builder = tf.saved_model.builder.SavedModelBuilder(modelpath)</div>
<div> builder.add_meta_graph_and_variables(</div>
<div> sess, </div>
<div> [tf.saved_model.tag_constants.SERVING], </div>
<div> signature_def_map = {tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY:model_signature}</div>
<div> )</div>
<div> builder.save()</div>
</div>
<p>2.保存训练过程中的指标数据，常用的有准确率，AUC等用一个json文件保存到ceph</p>
<div>
<div>with tf.gfile.GFile(modelpath+"metrics_info.json", "w") as f:</div>
<div> f.write(json.dumps([{"name":"acc", "type":"float", "value":str(acc)}, {"name":"loss", "type":"float", "value":str(loss)}]))</div>
</div>
<p>二，模型注册和上线</p>
<p>为了把tensorflow的模型管理起来，venus上通过简单的配置，把模型对应的信息记录下来。下面是示例项目的配置</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/5422ada347bca38c90cf.png"/></p>
<p>模型注册组件参数含义：</p>
<p>1) 模型名称用于唯一标识模型的id</p>
<p>2) 算法类型可选择NLP或者推荐模型，目前对于caffe的模型也在接入中</p>
<p>3) 训练框架目前支持tensorflow和无量，caffe的框架也在接入中</p>
<p>4) 训练方式根据实际情况选择实时还是离线，实时的模型一般可指定20分钟左右更新一次模型</p>
<p>5) 根据需要选择离线模型和在线模型保存的最大版本数，这里默认是10和2.</p>
<p>在模型上线之前，需要在所在应用组申请服务组和服务，venus.oa.com 训练管理栏找到你所在应用组，在左下角的位置找到服务那里，新建服务组，然后新建服务。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/99fd332de01ef9ab7efd.png"/></p>
<p>服务有了之后可以用模型上线组件上线模型到你注册的服务中去</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/fa46c631638f9abb01f6.png"/></p>
<p>模型上线组件参数含义：</p>
<p>1) 选择要上线的服务组和服务名称，有下拉框提示</p>
<p>2) 上线标准可过滤掉一些低于上线指标的模型，上线那些表现力好的模型</p>
<p>3)例行化之后，如果是实时模型训练，最好配置自动上线。</p>
<p>4)启用abtest，这里和abtest组件的功能一致，后续介绍。</p>
<p>三，abtest多个模型</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/543307011d1909d29c9a.png"/></p>
<p>这里只是做个示例，可以对其他模块做个abtest.选择本模型的信息，以及abtest对应的业务和模块。对比线上的效果。</p> 
{% endraw %}
