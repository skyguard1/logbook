---
title: "Tesla上基于TF的深度模型训练与性能优化"
date: 2022-04-01 10:02:09
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<h2>前言</h2><p>深度学习以其强大的表达能力在图像处理、自然语言处理等领域取得了非常好的结果。广告CTR预估领域也逐渐从大规模稀疏LR/FM等模型向wide&amp;deep，deepFM，DIN等深度学习模型方向演进，并在工业界取得了良好的效果。本文基于资讯推荐场景，讲解了深度模型在tesla、gaiaStack平台的训练方式以及cephfs与TDW数据的互通，并结合业界使用经验和自己踩过的坑，将相关经验进行一个记录，期望其他人能够少走一些弯路。</p>
<h2>DeepOceans平台初使用</h2><p>深度模型的训练需要依赖大量的数据，由于数据存储、预处理与模型训练常常需要在不同的平台和框架下进行，如使用TDW存储原始结构化数据，使用Spark对数据进行分布式预处理，使用Tensorflow进行深度模型的训练，使用TF Serving进行深度模型的服务。<br/>Tesla平台已经集成了Spark组件与TensorFlow组件，与TDW权限互通，而且可以通过虫洞依赖的方式轻松的与LZ调度平台进行交互，因此对中小型任务的部署十分有利。</p>
<ul>
<li><strong>申请gaiaStack平台权限</strong><br/>Tesla上的TensorFlow组件依赖deepOcean平台，Deep Ocean（深度学习平台）通过Docker镜像 + Gaia调度的技术。对研究员屏蔽了对GPU硬件、驱动、资源调度的管理部分，其权限申请和使用可以参看文档：<br/>万众期待—GPU平台DeepOcean2.0(GPU On Gaiastack)正式服役</li><li><strong>手动删除文件</strong><br/>deepOcean平台使用了专门的分布式存储ceph，如果需要访问ceph，需要在接口机上操作。如果需要删除任务生成的文件，则需要在运行中的实例中右键进入gaia的terminal进行删除，为了方便，建议建立一个任务专门删除文件使用，这个任务可以是sleep函数或者空循环。<br/><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/81bd97be1948dad0c061.png"/><br/><div> [ 启动gaia平台的terminal ]</div></div></li><li><p><strong>程序中删除文件</strong><br/>如果想要在程序中自动删除文件，由于tesla上传脚本的时候不允许引入一些删除功能相关的包或函数（如shutil），因此是无法在程序中直接调用这些函数的，经过多方咨询，目前个人使用的方法是在ceph上先放置一个删除文件的shell脚本，然后在python程序中调用删除脚本对文件进行自动删除，实例代码如下：<br/><code>subprocess.check_output(['sh',delete_dir_script, to_write_path])</code></p>
<h2>从TDW获取数据</h2><p>深度模型的训练依赖大量的数据，公司内部的结构化数据一般存储在TDW集群，目前有多种方式从TDW获取深度模型需要的数据，常用方法有：</p>
</li><li><p><strong>使用TDWRecordDataset</strong><br/>TensorFlow中的数据读取方式可以认为有三种：</p>
</li></ul>
<ol>
<li>使用placeholder读内存中的数据</li><li>使用queue读硬盘中的数据</li><li>使用Dataset API从内存和硬盘读取数据<br/><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/327aeb19b61308ca2387.png"/><br/><div> [ TensorFlow中的dataset ]</div></div><br/>公司内已经有同事实现了类似标准API的DataSet接口<br/>Tensorflow与TDW共舞—Dataset数据集<br/>基于dataset的代码使用方式是：<pre>tdw_client = tf.new_tdw_client(db, user, password, group="tl")
filenames = tdw_client.get_data_paths(tdw_table)
dataset = readers.TDWRecordDataset(filenames)
if shuffle:
    dataset = dataset.shuffle(buffer_size=30000)
dataset = dataset.map(parse_csv, num_parallel_calls=20)
dataset = dataset.repeat(num_epochs)
dataset = dataset.batch(batch_size)
dataset = dataset.prefetch(2)
</pre></li></ol>
<ul>
<li><p><strong>使用queue风格的API</strong><br/>如果不想使用dataset API，还可以使用公司内其他同事提供的queue风格的API实现类似功能，可以参考文档：<br/>玩转TensorFlow—打通TensorFlow和TDW的任督二脉<br/>代码调用方式是：</p>
<pre>tdw_client = tf.new_tdw_client(db, user, password, group="tl")
filenames = tdw_client.get_data_paths(table, pri_parts=['p1'], sub_parts=['sp1', 'sp2'])
filename_queue = tf.train.string_input_producer(filenames)
</pre><p>此外这套API还支持直接将数据写回TDW，有相关需求的小伙伴可以直接使用这个API。</p>
</li><li><p><strong>使用generator自定义读取远程HDFS文件</strong><br/>TDW的数据底层使用HDFS文件存储，因此可以选择直接读取远程的HDFS文件的方式来实现完全透明化的控制。通过自定义数据获取方式，结合Dataset 的from_generator API，可以非常方便的实现完全透明的读取数据方式。<br/>需要注意的是，在TDW创建表的时候要创建TEXTFILE格式的表，且需要控制partition的数量。因为ORCFILE COMPRESS格式是列式压缩存储，需要pySpark解析，比较麻烦。如果保存TDW表的时候partition数量特别多将会产生大量的小文件，这对远程读取也是不利的。<br/>一个简单的demo如下：</p>
<pre>tdw_client = tf.new_tdw_client(db, user, password, group="tl")
filenames = tdw_client.get_data_paths(tdw_table, pri_parts=partitions)
  def gen_partition():
      for name in filenames:
          print('process %s file' % name)
          lines = []
          cat = subprocess.Popen(["hadoop", "fs", "-cat", name], stdout=subprocess.PIPE)
          for line in cat.stdout:
              lines.append(line)
          yield lines

def get_lines():
      for lines in gen_partition():
          for line in lines:
              yield line.strip()

  dataset = tf.data.Dataset.from_generator(get_lines, tf.string, tf.TensorShape([]))
  dataset = dataset.map(parse_csv, num_parallel_calls=40)

  if shuffle:
      dataset = dataset.shuffle(buffer_size=50000)
  dataset = dataset.repeat(num_epochs)
  dataset = dataset.batch(batch_size)
  dataset = dataset.prefetch(100000)
</pre></li><li><strong>拉取远程HDFS文件到ceph</strong><br/>为了进一步加快速度，在数据量不是很大的时候可以直接将远程的TDW数据（HDFS文件）拉取到ceph上存储，然后直接像读本地文件一样访问TDW数据。目前有两种方式可以将远程HDFS文件拉取到ceph</li></ul>
<ol>
<li><strong>直接使用tesla相关组件</strong><br/>tesla平台上已经提供了将TDW数据拉取到Ceph的组件<br/><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/3445182a527115f74799.png"/><br/><div> [ tesla上拉取远程数据的组件 ]</div></div><br/>tdw库表路径格式为：<code>tdw_rtx;password;db;table;p_1,p_2;sub_p_1,sub_p_2</code><br/>ceph文件路径格式为：<br/><code>/cephfs/group/g-xxx/rtx/tmp/table</code><br/>文件格式支持：npy（压缩率高，读取速度快）和csv（分隔符为\01），默认为csv</li><li><strong>结合API自己实现HDFS拉取</strong><br/>可以复用获取远程HDFS文件名称的API，首先得到HDFS路径，然后通过python中调用shell命令将远程HDFS文件下载到本地，相关代码如下：<pre>tdw_client = tf.new_tdw_client(db, user, password, group="tl")
filenames = tdw_client.get_data_paths(tdw_table, pri_parts=partitions)
for file in filenames:
     temp_file = file
     if ('\x00' in file):
         temp_file = file.split("\x00")[0]
cmd = 'hadoop fs -get ' + temp_file + ' ' + to_write_path
subprocess.call(shlex.split(cmd))
</pre>需要注意的是，使用 <code>tdw_client.get_data_paths</code>这个API获取到的文件列表的最后一个文件名含有一个终止符\x00，需要提前处理掉否则拉取会失败。</li></ol>
<h2>TensorFlow训练速度优化</h2><p>TensorFlow目前推行的训练方案是feature column+dataset+estimator API组合，这套方案需要很多优化的才能满足工业界使用需求，其中最重要的就是训练速度优化。在这个过程中，有一些个人经验如下：</p>
<ol>
<li><strong> 减少使用feature column等高级API</strong><br/><code>tf.feature_column</code>可以非常方便的对特征进行加载和转换，诸如hash，cross等常用特征变换操作都有对应的API可以直接使用，非常适合快速实验。但是在训练和serving中发现，feature column对性能损害是比较严重的。<br/>可以使用TensorFlow提供的profile工具对整个过程的耗时进行分析，具体方式只需要加入一行代码即可：<pre>with tf.contrib.tfprof.ProfileContext('./logs/') as pctx:
             model.train(input_fn=lambda: input_fn(train_files,param_dict))
</pre>profile工具组件非常丰富，如果只需要进行耗时分析，也可以使用工具timeline，其相关代码如下：<pre>from tensorflow.python.client import timeline
run_options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
run_metadata = tf.RunMetadata()
predictions = use_sess.run(**，options=run_options, run_metadata=run_metadata)
line = timeline.Timeline(run_metadata.step_stats)
chrome_line= tl.generate_chrome_trace_format()
with open('timeline.json', 'w') as f:
 f.write(chrome_line)
</pre>对使用feature column和TFrecord的TF程序进行分析，可以得到下图的耗时分布，可以看出数据预处理部分的耗时是占比很大的。<br/><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/a6969a3193cea4c6f2ea.png"/><br/><div> [ 模型训练过程耗时分析 ]</div></div><br/>为了加快训练和预测速度，最好在外置Spark任务中先对数据进行转换，然后以稀疏的形式输入到模型中，线上服务时候，也可以使用服务端的特征变换组件对特征进行转换后再喂给模型，这样可以大大加快infer速度。</li><li><p><strong>优先使用TFRecord并辅助压缩节约存储空间</strong><br/>tfrecord文件中的数据是通过Protocol Buffer的格式存储的，也是TF官方推荐的数据存储格式，很多API都针对TFRecord进行过对应的优化，在tensorflow的graph中更快地复制、移动、读取。多篇文章都提到使用TFRecord输入相比原生数据可以有2-4倍的数据提升。但是生成TFRecord也需要消耗一定的时间，因此使用时需要进行权衡。<br/>生成TFRecord后文件的大小普遍会变得比原始文件更大，如果对存储比较敏感可以加上压缩参数，相关代码如下：</p>
<pre>options = tf.python_io.TFRecordOptions(tf.python_io.TFRecordCompressionType.GZIP)
 with tf.python_io.TFRecordWriter(tfrecord_name, options=options) as writer:
_CSV_COLUMNS,_CSV_COLUMN_DEFAULTS)
     for line in feature_rows:
         dense_feature_sample = row_process(line, data_yaml, has_label=True)
         tfexample = _convert_features_to_tfexample(dense_feature_sample, data_yaml.feature_type_dict)
         writer.write(tfexample.SerializeToString())
</pre><p>在读取时也一定要指定压缩配置，否则读取数据会出现错误：</p>
<pre>filename_queue = tf.train.string_input_producer(filenames, num_epochs=num_epochs, shuffle=False)
 reader = tf.TFRecordReader(options=tf.python_io.TFRecordOptions(tf.python_io.TFRecordCompressionType.GZIP))
 _, serialized_example = reader.read_up_to(
     filename_queue, shuffle_size + 10)
</pre></li><li><p><strong>使用read_up_to方法提高输入并发度</strong><br/>如果要使用queue风格的API，其原理如下图所示：<br/></p><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/bf996ad713a95db30e5f.png"/><br/><div> [ TensorFlow的queue输入pipline ]</div></div><br/>其调用过程涉及到两个队列的配合，filename 队列是文件名的队列，确定要读取哪一个文件。example队列则存储了处理后的数据记录，供其他线程对其进行消费。理想情况下，应该是example队列充满数据，计算队列随时都可以从数据队列中拉取数据，如果消费队列长期处于饥饿状态，则会大大降低并行度和训练速度。<br/>为了充分利用多线程优势，保证数据队列始终充满数据，需要使用read_up_to方法并在batch过程中加上<code>enqueue_many=True</code>参数，这个技巧在的深度学习工程实践的文章中有提到，在我们自己的测试中确实有非常明显的速度提升。<br/><a href="https://tech.meituan.com/2018/06/07/searchads-dnn.html">深度学习在搜索广告排序的应用实践</a><br/>其代码如下：<p></p>
<pre>filename_queue = tf.train.string_input_producer(filenames,num_epochs=3,shuffle=True)
reader = tf.TFRecordReader()
 _, serialized_example = reader.read_up_to(
     filename_queue, 10240)

 batch_serialized_example = tf.train.shuffle_batch(
     [serialized_example], batch_size=batch_size, capacity=10240, enqueue_many=True,
     min_after_dequeue=5120, num_threads=40)

 features = tf.parse_example(
     batch_serialized_example,
     features=feature_shape
 )
 features, labels = parse_features(features)
</pre></li><li><strong> 使用prefetch提高输入并发度</strong><br/>queue风格的API将逐渐在未来的版本中淘汰，Dataset和Data是推荐的数据输入方式，因此TF官方对dataset性能推出了一系列优化措施。详细文档可以参考其官方文档：<br/><a href="https://tensorflow.google.cn/guide/performance/datasets">数据输入流水线性能</a><br/>优化训练速度的重要前提就是避免计算线程空置等待，希望计算线程和数据准备能够以pipline的方式进行完美的配合。<br/><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/541ec14929a276120a35.png"/><br/><div> [ 数据准备和计算的pipline配合 ]</div></div><br/>下面列举一些基于dataset的常用的优化策略，在实践中需要根据机器环境和需求进行灵活调整。<pre># tf.data.Dataset.prefetch 使用prefetch将生成数据的时间和使用数据的时间分离开
dataset = dataset.prefetch(buffer_size=FLAGS.prefetch_buffer_size)
#使用map 转换的 num_parallel_calls 参数来指定并行处理级别
dataset = dataset.map(map_func=parse_fn, num_parallel_calls=FLAGS.num_parallel_calls)
#需要反序列化操作使用 parallel_interleave 转换来并行
dataset = files.apply(tf.contrib.data.parallel_interleave(
tf.data.TFRecordDataset, cycle_length=FLAGS.num_parallel_readers))
</pre></li><li><strong>选择合适的TF版本和运行环境</strong><br/>TF版本迭代是很快的，不同版本的TF对不同API的支持程度有区别。在实践中发现，TF 1.12版本（gaiaStack平台目前最新的版本）下使用queue的API辅助上述优化方法CPU利用率可以到4000%已上，使用dataset API则速度显著低于queue方法。但是在1.11版本下，使用dataset相关的API相比queue方法有3-4倍的提升。实践中可以将两种数据输入方法分别尝试和优化，选择更高效的版本使用。<br/>使用GPU一般会加速计算，因为GPU相对CPU可以提供更高的并行度，但由于推荐模型相对CV/NLP领域的模型其复杂度低很多，因此实践只使用CPU而不使用GPU，训练速度反而会更快，因为GPU带来的速度提升不足以覆盖增加的CPU与GPU之间数据传输的开销，因此反而没有加速效果。<br/>如果只使用CPU，还可以在程序中使用intel提供的MKL（Math Kernel Library）优化。具体可以通过两个参数进行控制，如果都没有设置或设置为 0，则会默认使用逻辑 CPU 核心的数目：<pre>intra_op_parallelism_threads： 使用多线程来并行化计算的结点会将不同的计算单元分配到该池中的线程上
inter_op_parallelism_threads： 所有待计算结点都由此线程池来调度
</pre>可以通过 tf.ConfigProto对相关参数进行传递：<pre>config = tf.estimator.RunConfig().replace(
     session_config=tf.ConfigProto(device_count={'GPU': 0}),
      intra_op_parallelism_threads = 64,inter_op_parallelism_threads=64))
     keep_checkpoint_max=4, save_checkpoints_steps=save_checkpoints_steps,
     save_summary_steps=100
 )
model = tf.estimator.Estimator(model_fn=model_fn, model_dir=model_dir, params=model_params, config=config)
</pre>如果不使用estimator，可以直接对session进行设置：<pre>config = tf.ConfigProto()
config.intra_op_parallelism_threads = 64
config.inter_op_parallelism_threads = 64
tf.session(config=config)
</pre></li></ol>
<h2>解决特殊输入格式</h2><p>特征决定了模型的上限，而模型只是不断的逼近这个上限。在实践中，我们总会构造各种各样的特征期望带来更好的数据表示。因此不可避免的会有很多特殊格式的输入。</p>
<ul>
<li><strong>multi-hot 格式输入</strong><br/>对于multi-hot特征大家都比较熟悉，比如一篇新闻可能既属于财经，又属于时政，假设现在有一个multi-hot特征工作类型以feature column形式输入到模型：<pre>workclass = tf.feature_column.indicator_column(tf.feature_column.categorical_column_with_vocabulary_list(
  'workclass', [ 'Self-emp-not-inc', 'Private', 'State-gov', 'Federal-gov', 'Local-gov', '?', 'Self-emp-inc', 'Without-pay', 'Never-worked']))
</pre>可以先通过indicator column将这个特征转化为one hot编码。<br/>在原始数据中，你可以将多个取值使用某种分割符进行表示，如写成<code>State-gov:Private:Private</code>，接下来就是使用合适的方式将其转换为模型能够接受的tensor输入：<pre>def process_list_column(list_column, dtype):
  sparse_strings = tf.string_split([list_column], ':')
  print('sparse string is'+'*'*100)
  print(sparse_strings.indices)
  print(sparse_strings.values)
  return tf.SparseTensor(indices=sparse_strings.indices,
                          values=sparse_strings.values,
                          #values =string_strip(sparse_strings.values),
                          dense_shape=sparse_strings.dense_shape)
</pre>配合上其他函数就可以转换为模型可以接受的形式。<pre>def parse_csv(value):
  columns = tf.decode_csv(value, record_defaults=_CSV_COLUMN_DEFAULTS)   
  columns[muilti_index] = process_list_column(columns[muilti_index], dtype=tf.string)
  features = dict(zip(_CSV_COLUMNS, columns))
  labels = features.pop('income_bracket')
  return features, tf.equal(labels, '&gt;50K')
</pre><pre>dataset = tf.data.TextLineDataset(filename)
dataset = dataset.map(parse_csv, num_parallel_calls=1)
dataset = dataset.repeat(1)
dataset = dataset.batch(1)
</pre>输入输出的示例结果<pre>data = dataset.make_one_shot_iterator().get_next()
layer_test = tf.feature_column.input_layer(data[0], workclass)
sess = tf.Session()    
sess.run(tf.global_variables_initializer())
sess.run(tf.tables_initializer())
print(sess.run(layer_test))
print(sess.run(layer_test))
print(sess.run(layer_test))
print(sess.run(layer_test))
</pre><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/fab8c2d0148acab7d53b.png"/><br/><div> [ 输入输出结果样例 ]</div></div></li><li><strong>weight multi-hot 格式输入</strong><br/>实践中可能还有更多更复杂的特征，比如一篇新闻既属于财经又属于时政，属于财经的得分是0.7，属于时政的得分是0.3，那你就需要两个特征去表示这些信息，其中一个特征是表征这篇新闻属于的类别，另一个特征表征这个新闻的类别权重。TensorFlow官方支持这种特征的输入，可以使用<code>tf.feature_column.weighted_categorical_column</code>对其进行包装，然后将其变成一个特征输入到模型：</li></ul>
<pre>workclass = tf.feature_column.indicator_column(tf.feature_column.categorical_column_with_vocabulary_list(
    'workclass', [
        'Self-emp-not-inc', 'Private', 'State-gov', 'Federal-gov',
        'Local-gov', '?', 'Self-emp-inc', 'Without-pay', 'Never-worked']))
weight_columns = tf.feature_column.indicator_column(tf.feature_column.weighted_categorical_column(workclass, 'weights'))

def input_fn(data_file):
    def process_list_column(list_column, dtype):
        sparse_strings = tf.string_split(list_column, ':')
        if (dtype == tf.string):
            t_values = sparse_strings.values
        elif (dtype == tf.float32):
            t_values = tf.string_to_number(sparse_strings.values, out_type=tf.float32)
        return tf.SparseTensor(indices=sparse_strings.indices,
                               values=t_values,
                               dense_shape=sparse_strings.dense_shape)

    def parse_csv(value):
        columns = tf.decode_csv(value, record_defaults=_CSV_COLUMN_DEFAULTS)

        columns[1] = process_list_column([columns[1]], dtype=tf.string)
        columns[-1] = process_list_column([columns[-1]], dtype=tf.float32)
        print('after column convert columns are ' + '*' * 100)
        print(columns)
        features = dict(zip(_CSV_COLUMNS, columns))
        labels = features.pop('income_bracket')
        return features, tf.equal(labels, '&gt;50K')
</pre><ul>
<li><p><strong>非feature column的任意格式输入</strong><br/>如果不使用feature column，你可以使用更加自由的方式处理各种各样格式的输入，比如输入数据的格式是：<code>label feature_indexs feature_values</code>的稀疏数据，实际样例：<br/><code>0 1,4,7 0.5,0.3,0.6</code>，你可以充分利用TF各种API自定义解析函数将其转化成TF可以接受的格式，如下示例程序：</p>
<pre>  def decode_sparse(line):
      columns = tf.string_split(line, ' ')
      splits = tf.reshape(columns.values, columns.dense_shape)
      label_str, index_str, value_str = tf.split(splits, num_or_size_splits=3, axis=1)
      # process label
      labels = tf.string_to_number(label_str, out_type=tf.float32)
      labels = tf.reshape(labels, [-1, batch_size])[0]
      # process feature index
      index_str = tf.reshape(index_str, [-1, batch_size])[0]
      index_str = tf.string_split(index_str, ',')
      index_str = tf.reshape(index_str.values, index_str.dense_shape)
      index = tf.string_to_number(index_str, out_type=tf.int32)
      # process feature values
      value_str = tf.reshape(value_str, [-1, batch_size])[0]
      value_str = tf.string_split(value_str, ',')
      value_str = tf.reshape(value_str.values, value_str.dense_shape)
      value = tf.string_to_number(value_str, out_type=tf.float32)

      return {"index": index, "values": value}, labels
</pre><p>需要注意的是这些操作都比较耗时，在实践中尽量定义标准的输入格式减少解析耗时。</p>
</li></ul>
<h2>TF Serving性能优化</h2><p>模型训练完毕后需要在线上服务，线上服务的速度和吞吐量是重要的优化指标。</p>
<ol>
<li><strong>serving方式的选取</strong><br/>TensorFlow Serving提供REST API和gRPC两种请求方式，在实践中，我们发现1000条样本在用REST方式进行请求的时候，总耗时是200 ms，网络的耗时只有50 ms，最后实际的预测耗时是50 ms，在定位源码的时候发现主要的耗时都在rapidjson中的json串解析上（只能单线程的串行去做解析），大概耗时是100 ms，相关代码片段：<br/><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/c82900caf62d14ef9ba1.png"/><br/><div> [ TF Serving代码定位 ]</div></div><br/>采用grpc的方式以后，pb的解析只需要10 ms左右的耗时，相比json解析有较大的提高。实践中可以考虑使用grpc调用方式，其采用的pb格式的解析和传输都比json有优势。</li><li><strong>使用专用指令集进行加速</strong><br/>高级矢量扩展（AVX）是英特尔在2008年3月提出的英特尔和AMD微处理器的x86指令集体系结构的扩展，AVX引入了融合乘法累加（FMA）操作，加速了线性代数计算，即点积，矩阵乘法，卷积等，因此使用AVX可以加速CPU上的计算过程。<br/>在实践中，使用AVX指令集进行编译优化，获得了10倍速度提升：<pre>bazel build -c opt --copt=-mavx --copt=-mavx2 --copt=-mfma --copt=-msse4.2 //tensorflow_serving/model_servers:tensorflow_model_server
//对部分老机型，如B6服务器因不支持avx2指令集，要用不使用avx2指令集进行编译：
bazel build -c opt --copt=-msse4.1 --copt=-msse4.2 --copt=-mavx --copt=-O3 //tensorflow_serving/model_servers:tensorflow_model_server
</pre><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/4df8288433a4157a2bb1.png"/><br/><div> [ 优化前的infer速度 ]</div></div><br/><div><img alt="图示" loading="lazy" src="/logbook/images/algorithm/136187e55467a334bea4.png"/><br/><div> [ 优化后的infer速度 ]</div></div><br/>但是公司服务器通常不提供外网连接，使用bazel编译时需要大量依赖包，因此需要进行较多本地编译工作，更详细的方法可以参考我们的记录文档：<br/>TFServing优化记录<br/>除了AVX指令集，还可以使用XLA,XKL等指令集进行优化，这些方法在TF官方文档都有提到，而且提供了相关功能，可以参考下面两篇文章：<br/><a href="https://tensorflow.juejin.im/performance/performance_guide.html">TF性能指南</a><br/><a href="https://zhuanlan.zhihu.com/p/60890267">How we improved Tensorflow Serving performance by over 70%</a></li></ol>
<h2>致谢</h2><p>深度模型训练和部署服务是一个系统性工程，在相关尝试过程离不开大家的努力，我们部分工作已经开源至：[内部或本地链接已移除] 欢迎大家一起commit<br/>感谢leocchen，brucehou，bingxu，leonqian等同事一起探讨与尝试，感谢deepOcean平台的beckyu，xiangtikong，jineyli等同事一起配合定位和修复问题。</p>
<h2>参考文献</h2><p>Tensorflow与TDW共舞—Dataset数据集<br/>玩转TensorFlow—打通TensorFlow和TDW的任督二脉<br/>万众期待—GPU平台DeepOcean2.0(GPU On Gaiastack)正式服役<br/><a href="https://tech.meituan.com/2018/06/07/searchads-dnn.html">深度学习在搜索广告排序的应用实践</a><br/><a href="https://tensorflow.google.cn/guide/performance/datasets">数据输入流水线性能</a><br/>TFServing优化记录<br/><a href="https://tensorflow.juejin.im/performance/performance_guide.html">TF性能指南</a><br/><a href="https://tech.meituan.com/2018/04/08/tensorflow-performance-bottleneck-analysis-on-hadoop.html">使用TensorFlow训练WDL模型性能问题定位与调优</a><br/><a href="https://tech.meituan.com/2018/10/25/dl-system-in-nlu-and-speech.html">深度学习系统的工程实践</a><br/><a href="https://tech.meituan.com/2018/10/11/tfserving-improve.html">基于TensorFlow Serving的深度学习在线预估</a></p>

{% endraw %}
