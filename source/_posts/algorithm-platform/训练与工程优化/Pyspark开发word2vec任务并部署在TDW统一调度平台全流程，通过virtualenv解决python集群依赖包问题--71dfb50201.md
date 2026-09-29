---
title: "Pyspark开发word2vec任务并部署在TDW统一调度平台全流程，通过virtualenv解决python集群依赖包问题"
date: 2022-04-06 13:59:14
categories:
  - 算法平台
  - 训练与工程优化
---

{% raw %}

<h3>1.背景</h3>
<p>Lookalike特征工程部分需要对百万量级的标签（搜索、资讯等）进行处理，而通过one-hot获得百万维特征的方法不可取，其中一个解决思路就是利用word2vec将标签转换为向量以达到降维的效果，本文将会就pyspark实现word2vec并部署到“统一调度平台”（[内部或本地链接已移除]）分享一些踩过的坑作为一个通俗易懂的部署word2vec任务手册；</p>
<p>文本力求使刚刚接触TDW或者pyspark的同学也可以根据本文实现整个word2vec任务开发配置的全流程，尽量以通俗的语言来描述每个步骤，使刚刚接触TDW平台与pyspark的同学有一个可以参考的流程，如有不严谨之处，还望指正；</p>
<h3>2.平台工具描述</h3>
<p>        “统一调度平台”提供任务的部署与周期运行，通过任务视图可以很清晰的了解任务脉络并进行配置依赖，界面如图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c48b7b6e9a8f3f1807af.png"/></p>
<p>我们可以依次部署语料清洗分词任务、word2vec模型训练任务、关键词标签生成任务、词向量预测任务以及将数据转换成模型需要格式的任务；</p>
<p>       “Idex”([内部或本地链接已移除])是使用TDW数据库非常方便的一个在线代码编辑平台，界面如下图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ea00eaaf7d25a38ec9b7.png"/></p>
<p>常用到的sql、pysql以及ipynb文件均可以在该平台上创建使用，其中ipynb也就是jupyter notebook已经配置好pyspark环境，如下图可以快速上手练习并调试语法逻辑；</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/cc0768ccb9a2715220bd.png"/></p>
<p>       本篇文章主要基于idex平台的jupyter notebook开发word2vec程序主体，介绍如何将写好的pyspark程序部署在统一调度平台运行并解决计算节点上缺少python依赖包的问题；</p>
<h3>3.Word2vec程序开发简介</h3>
<p>本文的应用场景针对于“搜索”以及“资讯”类标签数量庞大，标签的类别数有百万量级，这种规模的数据作为模型的特征显然是不合适的，我们需要对其进行降维，于是我们想到使用word2vec将词句标签转化为向量的方式(词向量维度100维)，然而我们尝试使用现有的word2vec模型转换时发现成功转换的比例很低，不足50%，因此为了能覆盖到业务场景下的标签，我们需要基于自己的语料库来训练word2vec模型；</p>
<p></p>
<p>程序主要包括语料清洗分词、模型训练、文本预测三个步骤，全流程的代码开源在工蜂git项目上：</p>
<p>[内部或本地链接已移除]</p>
<p>关于pyspark调用TDW库表的操作可以参见TDW的文档：</p>
<p>[内部或本地链接已移除]</p>
<p></p>
<p>实际使用中的任务结构如图所示：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ce0e6c2946d935d7837a.png"/></p>
<p>这里分为给出语料清洗、模型训练、向量预测三个任务统一调度平台的任务id，供感兴趣的同学参考配置信息；</p>
<p>              语料清洗：20200723194104715</p>
<p>              模型训练：20200724112241362</p>
<p>              向量预测：20200727143324270</p>
<p>这里列举程序的部分代码：</p>
<div>
<pre># pyspark相关工具初始化
spark_session = SparkSession.builder.appName("word2vec").getOrCreate()
tdw = TDWSQLProvider(spark_session, db="nfa")
tdw_util = TDWUtil(dbName='nfa')</pre>
</div>
<p> </p>
<div>
<pre># 读入语料数据
df = tdw.table(tblName="nfa_lkl_info_corpus", priParts=[train_pri])</pre>
</div>
<p> </p>
<div>
<pre># 语料分词
dic = tdw.table(tblName="jizhe_tag_name")
seg_udf = udf(seg, ArrayType(StringType()))
dic_pd = dic.toPandas()
dic_pd.to_csv('dict.txt', sep='\t', index=False, encoding='utf-8')
spark_session.sparkContext.addFile('dict.txt')
t = df.withColumn('seg', seg_udf(df['txt']))</pre>
</div>
<p> </p>
<div>
<pre># 去除停用词
stop = tdw.table(tblName="nfa_lkl_stop_words")
stop_words = [i[0] for i in stop.select("stopword").collect()]
remover = StopWordsRemover(inputCol="seg",   outputCol="words_after_stop", stopWords=stop_words)
t = remover.transform(t)</pre>
<div>
<pre># 数据清洗，去除特殊符号与英文：
remove_punctuation_udf = udf(remove_punctuation, ArrayType(StringType()))
df_clean = t.withColumn('words_after_clean',remove_punctuation_udf(t['words_after_stop']))
getterUDF = udf(getter, StringType())
df_clean = df_clean.withColumn('words_after_clean_str', getterUDF(df_clean['words_after_clean']))</pre>
</div>
<p> </p>
<div>
<pre># word2vec模型训练
w2v = Word2Vec(vectorSize=100,
			   minCount=3,
			   seed=,
			   numPartitions=128,
			   inputCol="words_after_clean",
			   outputCol="words_vec")
model = w2v.fit(df_clean)</pre>
</div>
<p> </p>
</div>
<h3>4.Virtualenv</h3>
<p>现在我们已经有了pyspark训练word2vec全流程的代码，接下来就是在统一调度平台配置部署任务了，在这个环节，分享一个我踩过的坑：计算节点无相关依赖库（numpy,pandas,jieba等）的问题，这里的节点配置与所选的计算集群有很大关系，有的节点已经配置常见的依赖库，但是像这里用到的jieba分词在很多节点上并未预装，这里需要用Virtualenv来配置环境依赖；</p>
<p>简单来说virtualenv就是用来创建一套"隔离"的Python运行环境的工具，我们可以在服务器上通过指令：</p>
<div>
<pre>pip install virtualenv</pre>
</div>
<p>来安装virtualenv，安装完毕之后运行</p>
<div>
<pre>virtualenv --no-site-packages py_env</pre>
</div>
<p>创建一个新的虚拟环境，其中--no-site-packages参数可选，意味着新建的python环境中没有任务第三方包；</p>
<p>现在可以进入虚拟环境，运行指令：</p>
<div>
<pre>source py_env/bin/activate</pre>
</div>
<p>可以看到用户前面出现了（py_env）:</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/957c4e46439cc3842545.png"/></p>
<p>此时我们已经进入了虚拟的python环境中，这个时候我们就可以根据需要安装各类依赖包，例如pip install pyspark ，pip install jieba 等；</p>
<p>可以通过pip list指令查看虚拟环境中安装的包，如下图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/20e041d818217551b976.png"/></p>
<p></p>
<p>当我们安装完所需要的依赖包之后，使用</p>
<div>
<pre>deactivate</pre>
</div>
<p>指令退出虚拟环境，现在就可以使用zip指令打包环境：</p>
<div>
<pre>zip -r py_env.zip py_env</pre>
</div>
<p>接下来将文件py_env.zip通过hadoop指令上传到HDFS上（由于个人服务器一般不具有HDFS访问权限，需要存储到具有权限的应用组服务器中再调用Hadoop指令），服务器和本地文件传输推荐使用iFt工具，之后就可以供后续集群计算的时候调用了；</p>
<p>该项目中，这个包含pyspark、jieba等库的环境包保存在hdfs目录：</p>
<p>hdfs://ss-mig-1-v2/stage/interface//g__nfa_nfa/jizhe/py_env.zip</p>
<p>后文参数配置的环节将用到这个路径；</p>
<p>至此我们已经完成了虚拟环境的配置并保存在hdfs上，接下来我们就来看如何在统一调度平台上配置该任务；</p>
<h3>5.Pyspark参数配置</h3>
<p>首先我们新建视图并新建任务，任务类型为数据计算，任务子类型为PySpark计算，如下图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f5fdeea270d144702976.png"/></p>
<p>上传pyspark脚本时需要指定任务id，在脚本管理中上传脚本如下图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/124ef64e2086c2313a48.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f3ba6250358e4ff444b7.png"/></p>
<p>这里需要特别注意“拓展参数”的配置，我们在这里指定虚拟环境的位置以及python运行的路径，如下图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1f941aeb14cf86bf12e5.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/25b85ce4ee78b787a264.png"/></p>
<p>spark.yarn.dist.archives后面指定压缩包所在hdfs路径，最后的#py_env代表将压缩文件解压缩并命名为py_env；</p>
<p>spark.pyspark.python为python的运行路径，注意，这里也有一个坑！ 很多的文章中的路径是型如：</p>
<div>
<p>. /py_env/bin/python</p>
</div>
<p> 这样的路径，但是实际运行中会报错显示找不到python，这里我猜想是由于压缩以及解压的时候多出了一层目录导致的，实际使用的路径为：</p>
<div>
<p>./py_env/py_env/bin/python</p>
</div>
<p>如果没有注意到的话这个小问题也可能会很，这里可以两种路径都尝试一下；</p>
<p>spark.driver.maxResultSize参数默认的设置为1G，在训练模型的时候很容易会超出并报错(报错示例：Job aborted due to stage failure: Total size of serialized results of 928 tasks (1024.5 MB) is bigger than spark.driver.maxResultSize (1024.0 MB)；)，这里设置成10G之后不再出现这个问题；</p>
<h3>6.TDW统一调度平台集群选择</h3>
<p>由于各集群的机器配置是不完全相同的，配置Virtualenv环境的机器型号(CPU架构)需要与计算节点的相同，也即是同样是x86或者同样是ppc机器；如果型号不匹配会出现“无法打开二进制python文件”的报错；</p>
<p>这里给出具体的例子：TDW深汕狮子座集群使用的是ppc的机器作为节点，这时使用x86服务器配置的python虚拟环境将无法在这个集群上运行，而我们选择“天秤(2.7)”这个集群可以正常工作，如果想要在ppc的机器上运行，需要在ppc的服务器上安装Virtualenv并配置打包python虚拟环境；</p>
<h3>7.实用链接</h3>
<p>如果开发机器是windows的同学需要申请一台Linux的云服务器，公司的云产品“DevCloud”为大家免费提供一台可以使用的Linux系统服务器，申请链接为：[内部或本地链接已移除]；</p>
<p>服务器上配置好的虚拟环境需要上传到HDFS使用，需要用到有访问权限并配置Hadoop的服务器，需要在“铁将军”申请所在应用组或者部门的服务器权限，地址为：[内部或本地链接已移除]</p>
<p>TDW提供pyspark相关文档：[内部或本地链接已移除]</p>
<p>Hadoop shell命令：<a href="http://hadoop.apache.org/docs/r1.0.4/cn/hdfs_shell.html">http://hadoop.apache.org/docs/r1.0.4/cn/hdfs_shell.html</a></p>
<p>Pyspark官方文档：<a href="https://spark.apache.org/docs/latest/api/python/index.html">https://spark.apache.org/docs/latest/api/python/index.html</a></p>
<p>统一调度平台：[内部或本地链接已移除]</p>
<p>Idex：[内部或本地链接已移除]</p>
<p>iFT wiki：[内部或本地链接已移除]</p>
<p>词向量可视化工具：<a href="https://projector.tensorflow.org/">https://projector.tensorflow.org/</a></p> 
{% endraw %}
