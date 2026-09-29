---
title: "玩转TensorFlow--在TeslaML与1.0共舞"
date: 2022-04-01 10:04:07
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<p>从2015年11月宣布开源，到现在短短一年多的时间里，TensorFlow的发展迅猛，促进了各种DNN算法的蓬勃生长，也成就了DeepGO的辉煌战果。在业界，越来越多的研究人员以及工程师利用TensorFlow来构造深层次的网络，解决语言翻译、皮肤癌早期诊断、黄瓜……等各种现实中面临的新问题，取得了非常不错的效果。</p>
<p>关于1.0的新功能，网上已经很多文章了，这张图很好的概括了1.0的全景</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/2664b8e7ae67f9fc04f8.jpg"/></p>
<ul><li><strong>更快</strong>：超乎想象的快！它引入了JIT、XLA等编译优化技术，将单机训练速度优化到芯片级别；同时使用jemalloc替代linux原生的malloc，优化内存碎片管理等。</li><li><strong>更好用</strong>：引进tf.layers, tf.metrics 和 tf.losses等高级API，同时宣布即将引进完全兼容 Keras 的新 tf.keras 模块</li><li><strong>更强大</strong>：TensorBoard 可视化更强，集成内置了Embedding Projector，支持高纬度数据可视化和分析</li></ul><p><img alt="" loading="lazy" src="/logbook/images/algorithm/f42daf521b846bfe5be7.png"/><br/>（任务详见Tesla样例任务流：TF-embedding，点击运行后选择TensorBoard控制台可见，渲染会使用浏览器所在机器的GPU或者CPU资源，小心发烫 ）</p>
<p>整体上，TensorFlow在往一个更加开放和强大的巨型平台发展中，具体细节可以看<a href="https://www.youtube.com/watch?v=mWl45NkFBOc&amp;list=PLOU2XLYxmsIKGc_NBoIhTn2Qhraji53cv">Dev Summit视频</a>，一切尽在其中。</p>
<hr/><p>早在0.8.0版本，TeslaML平台早就支持TensorFlow了，提供了方便的一键式部署运行方式。伴随着TensorFlow 1.0的发布，我们也与时俱进，升级到了最新版本，并做了如下的几个小工作，让小伙伴们能够更好的与1.0共舞。</p>
<h2>主要工作</h2><ol><li><p><strong>代码升级</strong></p>
<p>Tesla的TensorFlow，上一个版本是0.11，如果用户代码是基于0.11版本开发的，而希望切换到1.0版本运行的话，那么api不兼容很可能导致运行失败，这时就需要用户手动升级代码了，建议用户尽可能升级到1.0，从这个版本开始API开始稳定，后续版本会兼容前面的版本。</p>
<p>为此，有两种升级方式（自动升级失败时，需要用手工升级的方式）</p>
<ol><li><p>借助社区提供的一个工具<a href="https://github.com/tensorflow/tensorflow/blob/master/tensorflow/tools/compatibility/tf_upgrade.py"><code>tensorflow/tools/compatibility/tf_upgrade.py</code></a>，自动升级代码</p>
<ul><li><p><strong>升级单个文件</strong></p>
<pre>      tf_upgrade.py --infile foo.py --outfile foo-upgraded.py
</pre>
</li><li><p><strong>升级整个目录</strong></p>
<pre>      tf_upgrade.py --intree coolcode --outtree coolcode-upgraded
</pre>
</li></ul></li><li><p>TensorFlow-1.0 的内部pip安装包，用户可以下载下来安装到自己的开发机上，手工升级代码</p>
</li></ol></li></ol><ol><li><p><strong>动态安装依赖库</strong></p>
<p> 在之前文章介绍中，数平DeepOcean平台的TensorFlow，是运行在Docker容器中。为了保持镜像的轻量性，没有安装很多库，但是默认的库，应该能满足小伙伴们的需求了，包括：</p>
<ul><li>matplotlib</li><li>numpy</li><li>scipy</li><li>scikit-learn</li><li>pandas</li><li>tensorflow</li><li><p><strong>keras，keras，keras（重要的事情说三遍）</strong></p>
<p>假如你想要用keras，那么像以下代码这样既可：</p>
<pre>from keras.models import Sequential
</pre>
<p>然后就可以开撸了……</p>
<p>那如果想用其他的依赖库，怎么办呢？需要我们提供新的镜像吗？No. No. No. 那样就太原始了……我们的方案是：</p>
<blockquote>
<p>相关pip源以及ubuntu源已经配置妥当，用户可以自行在代码中动态安装依赖库</p>
</blockquote>
<p>这样既没有增加镜像的大小，也可以满足了用户对库使用千变万化的需求，例如：</p>
<pre>import os

# Install python package
try:
  import redis
except:
  os.system('pip install redis')
import redis

# Install system lib
os.system('apt-get update &amp;&amp; apt-get install -y libjpeg8')
</pre>
<p>那么你就可以使用你需要的库了，是不是很方便呢？</p>
</li></ul></li><li><p><strong>Hdfs &amp; TDW访问</strong></p>
<p> 在《玩转TensorFlow系列》的第5篇中，“打通TensorFlow和TDW的任督二脉”已经介绍过如何在TensorFlow中直接访问TDW，这次我们介绍一下如何访问HDFS。</p>
<p> 如果你已经了解了常规的 <a href="https://www.tensorflow.org/programmers_guide/reading_data">Reading data</a>，那么访问HDFS将非常轻松，所有TDW的Hadoop环境，在运维的协助下，在镜像中配置好，用户按如下方式初始化文件队列即可：</p>
<pre> filename_queue = tf.train.string_input_producer([
     "hdfs://namenode:9000/path/to/file1.csv",
     "hdfs://namenode:9000/path/to/file2.csv",
 ])
</pre>
<p> 只要你的Tesla账号，有对应的目录权限，那么你的TensorFlow代码，将可以畅通无阻的访问到属于你的数据。</p>
</li></ol><h2>Demo工程</h2><p>为了进一步降低用户使用门槛，我们从社区整理了几个样例代码，在公司内部的Git上新建了一个Demo工程，方便用户学习。</p>
<p>项目地址：[内部或本地链接已移除]</p>
<p>项目目录结构如下：</p>
<ul><li><code>tensorflow/pip-package</code>: 当前线上版本的pip安装包</li><li><code>tensorflow/examples</code>: 当前线上版本对应的样例</li><li><p><code>tensorflow/examples/mnist</code>目录下，其代码结构说明如下：</p>
<ul><li><code>input_data.py</code>: 读取数据的相关封装</li><li><code>mnist.py</code>: 实现模型构建，包括inference、training、loss</li><li><code>fully_connected_feed.py</code>: main入口程序，使用Feed，训练并评估模型</li></ul></li><li><p><code>tensorflow/examples/word2vec</code></p>
<ul><li><code>word2vec_ops.cc</code>: 自定义读取数据的相关Operation声明</li><li><code>word2vec_kernels.cc</code>: 自定义读取数据的相关Operation实现</li><li><code>word2vec_optimized.py</code>: main入口程序，使用自定义的Operation得到输入数据，训练并评估模型</li></ul></li></ul><p>下面简单介绍如何在Tesla上使用样例(也可以直接参考对应目录下的README.md)。首先我们介绍深度学习领域的 Hello World 样例mnist，将<code>fully_connected_feed.py</code>上传到tesla入口脚本框，将<code>input_data.py</code>和<code>mnist.py</code>打包到一个zip文件中，例如<code>dep.zip</code>，将<code>dep.zip</code>上传到依赖文件框，然后填上程序参数运行即可。注意，输入数据需要自行下载放到指定的ceph目录下，在程序参数中指定<code>--input_data_dir</code>到你的数据目录。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f7178dee442ec8ffefa0.jpg"/></p>
<p>如果你的代码有C/C++的实现，例如自己实现了Operation Kernel，那么按照下面这个样例word2vec来部署，样例代码位于<code>tensorflow/examples/word2vec</code>目录下。首先编译自定义Operator(需要本地安装tensorflow)，得到word2vec_ops.so:</p>
<pre>TF_INC=$(python -c 'import tensorflow as tf; print(tf.sysconfig.get_include())')
g++ -std=c++11 -shared word2vec_ops.cc word2vec_kernels.cc -o word2vec_ops.so -fPIC -I $TF_INC -O2 -D_GLIBCXX_USE_CXX11_ABI=0
</pre>
<p>将<code>word2vec_optimized.py</code>上传到tesla入口脚本框，编译得到的<code>word2vec_ops.so</code>上传到依赖文件框，然后填上程序参数运行即可。注意，输入数据需要自行下载放到指定的ceph目录下，在程序参数中分别指定<code>--train_data</code>(训练数据)、<code>--eval_data</code>(测试数据)以及<code>--save_path</code>(模型输出目录)。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e51ada03d8705bfe39a8.jpg"/></p>
<h2>展望</h2><p>未来我们将更加完善 TensorFlow的，增强其多机多卡的性能，并引入TensorFlow Serving来做模型Inference，支持线上应用，导入更多的业界模型和数据集，方便小伙伴们进行各种AI研究，敬请期待。</p>
<p>深度学习和人工智能的需求方兴未艾，真正蓬勃发展之中。对人工智能有兴趣的小伙伴，如果没有GPU资源的，请找 lingochen 和 rogerhuang 申请GPU资源，对TensorFlow的使用，有任何问题的，欢迎咨询高进朝和我。</p> 
{% endraw %}
