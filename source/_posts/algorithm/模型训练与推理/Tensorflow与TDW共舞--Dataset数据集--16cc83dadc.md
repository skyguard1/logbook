---
title: "Tensorflow与TDW共舞--Dataset数据集"
date: 2022-04-01 10:06:01
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<div>
<p>TDW是公司级的结构化数据的存储系统，里面存储了大量的结构化数据。随着业务的发展在GPU中的应用越来越多，为了让深度学习和TDW的更进一步的融合，本文详细介绍了一种新方法Dataset来访问TDW的数据。</p>
<h2>1 数据集TDWRecordDataset简介</h2>
<p>首先我们大概介绍一下什么是数据集（Dataset）。社区在TensorFlow1.3版本引入了这以重要功能，在Tensorflow 1.4 版本这部分API正式移动到核心中。数据集是一种为TensorFlow模型创建输入管道的新方式，使用Dataset API 的性能要比使用feed_dict或队列式管道的性能高得多，而且更简洁，使用起来更容易。所以我们也尝试在Tensorflow支持以数据集的方式来访问TDW的数据，所以我们增加了一种新类TDWRecordDataset，从层次而言属于和TextLineDataset同一层次，如下图所示： <img alt="图示" loading="lazy" src="/logbook/images/algorithm/c796dc8196a97ae7c8cd.png"/></p>
<p> 其中：</p>
<ul><li>数据集：基类，包含用于创建和转换数据集的函数。允许您从内存中的数据或从 Python 生成器初始化数据集。</li>
<li>TextLineDataset：从文本文件中读取各行内容。</li>
<li> TFRecordDataset：从TFRecord文件中读取记录。</li>
<li>FixedLengthRecordDataset：从二进制文件中读取固定大小的记录。</li>
<li> TDWRecordDataset：从TDW的结构化数据读取记录。</li>
<li>迭代器：提供了一种一次获取一个数据集元素的方法。</li>
</ul><p>从上面的关系和说明看TDWRecordDataset实现了类似TFRecordDataset的功能，它可以有效的从TDW获取数据用于Tensorflow的训练使用。</p>
<h2>2 数据集的使用</h2>
<p>上面介绍了TDWRecordDataset在Dataset的位置和功能，下面我们来看看如何使用这个API接口。</p>
<p> <b>1.    </b><b>Import </b><b>TDWRecordDataset数据集的op。</b></p>
<p>TDWRecordDataset存在于tensorflow.python.data.ops下面，所以可以和使用TFRecordDataset等一样的操作使用TDWRecordDataset数据集，例如：</p>
<div>
<pre>from tensorflow.python.data.ops import readers</pre>
</div>
<p> <b>2.    </b><b>获取TDW上存储数据的文件</b> </p>
<p>a)     初始化 TDW Client对象 </p>
<div>
<pre># First new a tdw client
tdw_client = tf.new_tdw_client(db, user, password, group="tl")</pre>
</div>
<ul><li> <strong>db</strong>：str类型，TDW库名</li>
<li><strong>user和password</strong>：str类型，表示TDW用户名和密码</li>
<li><strong>group</strong>：str类型(可选)，所在集群，默认为同乐，财付通需指定”cft” </li>
</ul><p>b)      获得文件列表 </p>
<p>获取所有文件列表名，再用TensorFlow内置Reader的风格，初始化一个文件队列</p>
<div>
<pre># New a filename queue
filenames = tdw_client.get_data_paths(table, pri_parts=['p1'], sub_parts=['sp1', 'sp2'])</pre>
</div>
<ul><li> <strong>table</strong>：str类型，表示要读的表名</li>
<li><strong>pri_parts和sub_parts</strong>：list类型(可选)，表示一级分区和二级分区名，不指定表示读取所有分区数据 </li>
</ul><p><b>3.  </b><b>定义解析函数</b></p>
<p>对于获取的TDW数据进行一些清洗和处理等参数。例如：</p>
<div>
<pre>record_defaults = [[1], [1], [1],[1],["false"],[0.],[0.],["null"]]
def decode_csv(line):
    parsed_line = tf.decode_csv(line, record_defaults,  "\01")
    return parsed_line </pre>
</div>
<p> <b>4.  </b><b>构建TDWRecordDataset数据集</b></p>
<p>根据获取的文件以及数据解析函数构建TDWRecordDataset数据集，同时设置相关参数。这个用法和TFRecordDataset等数据集一致。 </p>
<div>
<pre>dataset = readers.TDWRecordDataset(filenames).map(decode_csv) # Read TDW DB file
dataset = dataset.repeat(100) # Repeats dataset this # times
dataset = dataset.batch(32)  # Batch size to use 
iterator = dataset.make_one_shot_iterator()
batch_features = iterator.get_next() </pre>
</div>
<p> <b>5.  </b><b>训练任务</b></p>
<p>训练相关任务的操作与TFRecordDataset等数据集的使用没有任何区别。</p>
<p>例如：</p>
<div>
<pre>with tf.Session() as sess:
  tf.initialize_all_variables().run()
  for i in range(10):
     print(sess.run(batch_features))</pre>
</div>
<strong><strong>  </strong></strong>
<h2>3 结论</h2>
<p>目前只在Tensorflow 1.4版本支持数据集访问TDW的方式，目前是整条数据读取，然后通过map来进行数据的清洗和转换。当然对于大数据量可以采用spark进行一次清洗后，然后在用Tensorflow进行访问和读取。目前TDWRecordDataset为第一个版本，欢迎试用和提出您的宝贵建议和意见。 </p>
<p>如需队列式管道方式可以参考小刚的文章《玩转TensorFlow--打通TensorFlow和TDW的任督二脉》。</p>
<p> 注：目前该特性支持Tensorflow 1.4以上版本，只有最新的gaiastack集群支持。</p>
<p></p>
<p><strong>参考：</strong></p>
<p><em>http://developers.googleblog.cn/2017/09/tensorflow.html</em></p>
</div> 
{% endraw %}
