---
title: "开源协同：共同打造更强大的大数据平台 TianQiong(天穹)"
date: 2022-03-18 15:38:02
categories:
  - 算法
  - 数据工程与系统实践
---

{% raw %}

<h2>行业趋势</h2>
<div>自从Hadoop在2006年1月28日横空出世，大数据技术开始了飞速发展的黄金10年，它改变了企业对数据的存储、处理和分析的过程，形成了自己的蓬勃发展的技术生态圈，并得到了非常广泛的应用。</div>
<div>在行业落地快速发展过程中，大数据技术也发生着快速的演进。从计算框架来看，从传统的MapReduce进化到了DAG引擎Tez, 内存计算引擎Spark, 以及流计算框架Flink等新的计算框架；基于大数据存储/计算引擎的数仓也从Hive(on MR), 发展到Impala, SparkSQL, Presto, Hive (on Tez, LLAP)等；即使近几年开始流行的实时计算，也从早期的Storm，进化到了Spark Streaming, Flink, Kafka Streams等新型流计算框架。不仅如此，经过的多年的发展，大数据技术的内涵和外延也变的极其丰富，不仅包括上面所提到分布式存储，分布式计算，实时计算，数仓引擎，还涵盖了数据集成，NoSQL， OLAP分析，机器学习与数据科学等方向。</div>
<div>在未来的发展方向上，大数据技术有以下几点趋势：</div>
<div>
<ol><li>大数据引擎全面容器化，与Kubernetes为代表的云原生系统整合，来简化devOps和云上的部署。这方面的代表作有Kubernetes Big Data SIG社区开发的Spark Operator, 以及最近Hadoop社区的YuniKorn；</li>
<li>大数据系统会与机器学习尤其是深度学习更好的深度整合。如同Google的Sr. Fellow Jeff Dean在SysML大会上所提出的，"System for Machine Learning" 和 "Machine Learning for System"。系统（硬件或是软件系统）会持续的优化来更好的支持机器学习，例如：的Angel, Intel的BigDL, Databricks的Project Hydrogen, Berkeley RISE Lab的Ray都是在大数据计算引擎Spark的基础上，来构建更适合深度学习的框架; 机器学习的算法也会越来越多的应用在诸如系统效率的优化提升上。</li>
<li>从垂直的数据计算引擎逐渐向数据湖方向演进，即除了统一的数据存储，也会有统一的元数据管理与数据治理，支持跨不同数据引擎的统一查询，批处理和流计算引擎的整合等等。这里说的数据湖存储，可以是云上的对象存储，如S3、COS，或者大数据文件系统HDFS以及两者的结合像Hadoop社区在开发中的Ozone等。而数据湖中的元数据管理代表产品则有AWS Glue, Lake Formation等，而数据湖统一查询引擎有Azure的Data Lake Analytics等。</li>
</ol></div>
<h2><strong>开源协同背景</strong></h2>
<div>除了外部的技术日新月异，内部各BG业务大数据的场景需求也非常丰富，无论是数据量还是业务量都在极速增长。如何以有限的研发资源来应对不断增长的业务需求是摆在每个BG大数据研发团队的一大挑战。在这样的背景下，一方面为了能海纳百川，把外部开源社区好的技术、代码引入进来满足各业务线的需要；另一方面，为了能把内部研发、创造并且经过大规模验证的优秀特性与代码能够推广出去，同时更好地来践行公司内部开源协同的号召，凝聚公司内部大数据技术的开发者、维护者以及用户的力量，我们现在将内部的大数据技术开源共建。首批开源的组件项目包括：Hadoop、Spark、Flink等应用广泛、技术成熟的公共基础类项目。</div>
<h2>项目协同目标</h2>
<div>
<p>通过将平台组件开源，多团队协同共建的方式，打造具有统一技术栈的公司级大数据平台体系。打破不同团队平台之间的壁垒实现平台互通功能复用，提升数据开发及应用的效率，释放数据价值，同时降低公司整体的开发成本及运营成本。</p>
</div>
<h2><strong>开源运作方式</strong></h2>
<div>成立大数据平台<strong>协同工作小组</strong>，该小组负责大数据领域技术栈及组件的整体规划, 工作进展包括会议记录等也会透明化向外输出。</div>
<div>大数据平台中各组件作为<strong>子项目</strong>，全部子项目的运作方式将与外部开源社区方式相同，即开放式的社区治理，各个开源协同项目的路线规划由各个项目<strong>OTeam的PMC来集体决策</strong>。而项目的PMC成员则兼顾专业性和各个相关业务BG的实际需求与资源投入情况来提名和选举产生 - 项目的初始阶段建议由参与共建的部门指派1名PMC，后期也会随着项目的推进来提名选举更多的PMC（包括committer），即按照实际的项目贡献度来进行一定程度的扩充。项目发展的决策过程与最终结果由全体PMC成员负责。公司内所有员工都可作为contributor参与到组件的功能开发中来，平等的参与代码贡献。并组织定期会议（暂定双周，公开会议拨入信息）来同步项目进展。</div>
<h2><strong>协同工作小组</strong></h2>
<div>
<p>目前大数据平台的开源协同工作已得到公司各个业务BG的强力支持，当前协同工作小组和接口人信息如下。</p>
<p><strong></strong>：rli(李锐)<br/><strong>金融数据应用部</strong>：hankchen(陈少清)<br/><strong></strong>：mikezou(邹建平)<br/><strong></strong>：yorkoliu(刘天斯)<br/><strong></strong>：brucebian(边疆);kenwaychen(陈建聪)<br/><strong></strong>：pengchen(陈鹏)；paterzheng(郑礼雄)；junpingdu(堵俊平)；kendyzhao(赵重庆)；benniehu(胡奔龙)； daisyjhhe(贺菊华)<br/><strong>微信支付数据中心</strong>：easychen(陈守志)<br/><strong></strong>：hunteryu(于东海)</p>
<h2><strong>外部开源贡献规划</strong></h2>
<p>在推动内部开源协同的同时，我们也承诺将积极参与外部社区的贡献与回馈，将公司的开源文化和技术影响力辐射出去，增强的技术品牌。目前团队中有多名Apache社区的Committer和PMC，包括<strong>2位Hadoop PMC</strong>成员， <strong>1位Spark PMC</strong>成员， <strong>1位Flink Committer</strong>， 2<strong>位HBase Committer</strong>，<strong>1位Livy Committer以及1位Sentry和Sqoop Committer</strong>等。这些活跃在开源技术社区的Committer和PMC们，不仅能更好的为开源协同项目的技术先进性和开源治理的成熟度把关，也为培养更多的开源社区人才，从而有更多的力量为的技术影响力代言。</p>
</div>
<h2><strong>项目规划</strong></h2>
<div>如上所述，首批开源的组件项目包括：Hadoop、Spark、Flink、HBase、SuperSQL、TDBank、数据资产管理等公共基础类项目。各项目简介如下：</div>
<h3>Hadoop （筹建中）</h3>
<div>代码地址：[内部或本地链接已移除]</div>
<div>TAPD地址：[内部或本地链接已移除]</div>
<div>技术图谱：[内部或本地链接已移除]</div>
<h3>Spark</h3>
<div>代码地址：[内部或本地链接已移除]</div>
<div>TAPD地址：[内部或本地链接已移除]</div>
<div>技术图谱：[内部或本地链接已移除]</div>
<div>Spark项目协同召集帖：[内部或本地链接已移除]</div>
<h3>Flink</h3>
<div>代码地址: [内部或本地链接已移除]</div>
<div>TAPD地址: [内部或本地链接已移除]</div>
<div>技术图谱: [内部或本地链接已移除]</div>
<div>Flink项目协同召集帖：[内部或本地链接已移除]</div>
<h3>HBase</h3>
<div>代码地址：[内部或本地链接已移除]</div>
<div>TAPD地址：[内部或本地链接已移除]</div>
<div>技术图谱：[内部或本地链接已移除]</div>
<div>HBase项目协同召集帖: [内部或本地链接已移除]</div>
<h3>SuperSQL （筹备中）</h3>
<div>代码地址：[内部或本地链接已移除]</div>
<div>TAPD地址：[内部或本地链接已移除]</div>
<div>KM文档地址：[内部或本地链接已移除]</div>
<div>技术图谱：[内部或本地链接已移除]</div>
<h3>TDBank （筹备中）</h3>
<div>代码地址：[内部或本地链接已移除]</div>
<div>TAPD地址：[内部或本地链接已移除]</div>
<div>KM文档地址: [内部或本地链接已移除]</div>
<div>技术图谱：[内部或本地链接已移除]</div>
<h3>数据资产管理</h3>
<div>代码地址：[内部或本地链接已移除]</div>
<div>TAPD地址：[内部或本地链接已移除]</div>
<div>技术图谱：[内部或本地链接已移除]</div>
<div>数据资产管理项目协同召集帖：[内部或本地链接已移除]</div>
<div></div>
<div>我们致力于培养一流的协同研发环境与氛围，打造一流的技术平台。对大数据项目的研发和创新感兴趣，有志于参与一起开源协同的同学，或有任何疑问以及建议的同学，欢迎联系junpingdu(堵俊平), benniehu(胡奔龙), daisyjhhe(贺菊华)。</div> 
{% endraw %}
