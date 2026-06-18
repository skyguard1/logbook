---
title: "基于Flink广告在线学习"
date: 2022-06-17 11:33:15
categories:
  - linux
---

<h1 class="toc-enable" id="061275b1-99d3-c624-f3c4-3372972f60af">前言</h1>
<p>CTR（Click-Through-Rate）即点击通过率，是互联网广告常用术语，指网络广告（图文广告/文字广告/视频广告等）的点击到达率，即广告的实际点击量/广告的展示量。</p>
<p>CVR（Conversion Rate）即转化率。是一个衡量CPA广告效果的指标，简言之就是用户点击广告到成为一个有效激活或者注册甚至付费的转换率。（本文主要探讨的转化为 注册、付费）</p>
<p>本文后续的CTR和CVR不具体计算比率输出，只计算公式中分子和分母的具体数据，由算法侧消费来学习分析。</p>
<p>针对目前在线学习场景，需要在线拼接样本特征（正样本、负样本）数据 供 算法侧学习分析在线广告曝光、点击、转化的详细情况。需要处理海量的广告数据，于是对数据处理平台也有了相应的要求：</p>
<p>高时效性：竞价响应数据（qps 3k）跟精排特征数据（qps 30w）需要100ms~1s内的窗口匹配，需要极高数据处理性能，极低的数据处理延迟。</p>
<p>数据准确性/可用性：在面临海量实时数据、需要高效的正确的计算出结果。不然很容易出现数据堆积，数据反压等性能问题。导致当前时间点输出不了准确结果甚至整个系统面临崩溃。</p>
<p>数据完整性/可靠性：数据在计算过程中和计算完成后都不应该产生丢失的情况，即使系统偶尔故障也能及时恢复数据。</p>
<p>Flink强大的计算性能、天生支持的横向扩展能力、checkpoint和savepoint可以保存数据的状态，以免异常而丢失数据，可以完整恢复。同时上下游均为tdbank消息队列系统，有效存储和记录offset。</p>
<p>面临着海量数据量带来的挑战，选择了Flink流计算框架，首选使用公司的Oceanus大数据处理平台。</p>
<h1 class="toc-enable" id="e0845125-4e11-fc5a-c1a9-9f46392ce56c">系统方案对比</h1>
<h3 id="62286c11-699d-0f93-b947-4e5c6d505dcc" class="toc-enable">方案一：Flink计算结果输出至TDBank</h3>
<p>数据源（TDBank）的数据经Flink消费计算后输出到下游TDBank，算法侧实时消费结果数据并进行在线训练。同时下游TDBank会按小时级别定时落库到tdw，供离线分析和对账。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(2)" width="712" height="192" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<h3 class="toc-enable" id="ee936a80-b228-0b15-20be-64cfb8c27e6f">方案二：Flink计算结果输出至HDFS</h3>
<p>数据源（TDBank）的数据经Flink消费计算后，按分钟级输出到下游HDFS存储，算法侧读取对应目录文件进行在线训练。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(3)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>调研发现，两种方案均具有可行性。方案一较方案二更具时效性，和离线分析对账的方便性，同时又不需要额外的共享存储资源，共享数据源的tdbank的topic资源，故本次在线特征学习采用方案一。</p>
<h1 class="toc-enable" id="a2de5443-5d7f-fa28-3429-952b9d470125">CTR样本拼接方案对比</h1>
<p>目前请求回传日志数据在qps 约30w，如果随着流量扩容10倍，召回扩大一倍之后流量会特别恐怖，实时消费会出现阻塞并且消费不过来，导致计算延迟，和不准确等问题。</p>
<h3 id="d94a7a29-4d07-c6b9-3cbd-2db78a75b428" class="toc-enable"><strong>方案一、曝光数据 join 请求回传数据之后，再落库redis</strong></h3>
<p class="toc-enable">经过试验，由于请求回传数据量太大，请求等待曝光2min的窗口都会出现计算延迟，并且一般曝光和请求会有很长时间的时间gap，所以需要再state中保存很久请求数据，造成任务checkpoint时间过长，任务积压严重；<br>结论：不可行</p>
<h3 id="64c32745-1cc4-94a5-d1f3-48922ec56f56" class="toc-enable"><strong>方案二、后台曝光回传的时候，重新计算特征数据，回传至曝光</strong></h3>
<p class="toc-enable">优点：解决请求数据过大导致的数据处理问题，不用处理99%的冗余数据<br>缺点：目前特征存储在redis中，最小更新频率为1小时，所以会造成部分特征的不一致问题<br>隐患：后续上实时特征的话，这部分特征会偏差</p>
<h3 id="0f43234f-4844-3080-7793-bce615617408" class="toc-enable"><strong>方案三、竞价返回数据&nbsp; join 请求回传数据，再落库redis</strong></h3>
<p class="toc-enable">与方案一的区别：竞价响应数据比曝光多10倍，但是和请求数据时延很小，经过统计平均延迟在15ms，而曝光和请求则在10min钟以上，所以不用缓存很久的请求数据，可解决redis资源问题。经测试需flink 仅需cpu 400核。<br>优点:&nbsp; 数据链路和方案验证可行，流程无问题<br>问题：目前集群资源池总共就900+核，后续10倍量的资源问题将持续解决。</p>
<h1 class="toc-enable" id="d7c0e260-1321-8193-da40-fc526d3ff0a2">CTR实时样本拼接方案</h1>
<h3 id="184439e7-4a2e-8ee2-fa64-4f3853e2eca2" class="toc-enable">一、拼接流程</h3>
<p>下图为多个实时流join的过程，Flink 均开启CheckPoint，每10min CheckPoint一次。Flink流主要分为两大部分：</p>
<p>1、竞价Response流 跟 精排特征回传流 进行interval join，精排回传数据等待竞价响应数据1s窗口（因为两条流同一个requestID数据正常相差时间在100ms以内），1s内匹配上则拿到特征数据，输出结果到Redis中，Redis设置3小时过期。</p>
<p>2、曝光流跟点击流interval join，曝光数据等待点击数据10min，10min以内曝光匹配上点击的为正样本数据，否则为负样本。</p>
<p>点击流跟曝光流interval join，曝光数据等待点击数据10min~30min，点击数据匹配上曝光数据的为延迟正样本。</p>
<p>3、延迟和非延迟样本（包含正、负样本）结果数据汇总后，跟已经缓存在Redis的特征数据进行匹配，拼接成带有特征数据的CTR数据，最后将拼接后的结果输出到下游TDBank。供CVR消费计算和算法侧消费计算。当然TDBank也会定时1h输出数据到TDW，供离线分析和对账。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(4)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p><br></p>
<h3 id="c569329a-cf5c-e61a-72ff-506871067334" class="toc-enable">二、Flink Topo图</h3>
<p>由此可知，Flink Topo图，也将分为两大部分，即两个作业，第一部分为特征存redis过程，第二部分为曝光点击拼接redis特征过程。其中第一个作业需要比第二个作业早启动30min，以保证redis里面有足够多的的数据给ctr从redis拿特征数据做拼接。</p>
<p>集群使用资源为500核，1T内存。</p>
<p>1、竞价Response、精排特征回传数据双流Join，将特征缓存至redis，其flink topo图为：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(5)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>上图可以看出，source端的并行度为164，跟上游tdbank的topic的并行度一致，window join算子并行度和sink输出并行度均为1000。为了加快计算效率和sink输出效率</p>
<p>两条流根据requestID和创意ID进行拼接。</p>
<p>2、曝光、点击双流join，计算得到正样本、负样本、延迟正样本，然后再跟步骤1的redis数据根据Key（RequestID+"|"+CreativeID）进行匹配拿到对应的特征，最后输出ctr拼接特征后的数据至tdbank，其Flink的topo流图为：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(6)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>上图可以看出，source端、window join算子、计算汇聚算子、输出算子的并行度均为50，已经足够满足当前的点击曝光流量。其中，曝光流跟点击流匹配上的正样本立马输出下游，负样本要等窗口过期后才输出（如：曝光流等了10min还是没有等到点击流的数据过来匹配，则视为负样本输出至下游。）</p>
<h1 class="toc-enable" id="ed8bc415-f490-d8f7-dae2-5c5972af83b7">CTR拼接效果</h1>
<p>通过对代码、集群优化后，CTR两个flink作业已稳定运行。经统计，CTR实时样本特征拼接成功率达99.89%，超过了预期95%的拼接成功率。剩下0.11%未拼接成功的样本将持续排查和代码优化。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(7)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<h1 class="toc-enable" id="e8cfb52b-1e26-76b3-b6a0-8b42f21f071b">CVR样本拼接方案对比</h1>
<h3 id="7ccc1650-1fd0-4a35-f9db-ba7ef881939b" class="toc-enable"><strong>方案一、将CTR的输出一份到redis，再join转化数据</strong></h3>
<p>预想将CTR数据输出一份到redis，存储时间为4h，然后去join转化数据。这样能够方便的得到正负样本、减少CVR代码中再次计算CTR数据的复杂度和减少资源。经过试验，Oceanus不支持将Redis维表数据作为左表来join，只支持作为右表映射用。<br>结论：不可行</p>
<h3 id="6afbc6c8-581e-d4c8-d6a5-a53d9d020089" class="toc-enable"><strong>方案二、CTR数据FULL JOIN+INTERVAL JOIN转化数据</strong></h3>
<p>由于转化数据必须先经过曝光、点击，于是，CTR数据是可以复用的，且已经通过CTR的计算后数据里包含了特征。由于CTR数据计算后是输出到TDBank，此时可以从TDBank中获取CTR的数据，通过FULL JOIN+INTERVAL JOIN，时间窗口4h，即CTR数据等待转化数据（注册、回流）4h，（注：非两条流在同一个4h窗口内的数据）。同时拼接成功的为非延迟正样本，4h内没有拼接成功的为非延迟负样本，4h的转化数据为延迟正样本。并将计算后的结果数据实时输出至下游TDBank。</p>
<p>经过试验，方案二可行。于是，采用方案二。</p>
<h1 class="toc-enable" id="52d7b19c-dd6e-d267-73af-e79638feef69">CVR样本拼接方案</h1>
<h3 id="7e8b8bcc-97a3-4abb-1eb6-20be907b01f4" class="toc-enable">一、拼接流程</h3>
<p>通过上面的CTR样本拼接完成后，CVR是计算转化率，相同的requestID必须先经过CTR流，再留下来转化（目前只考虑 注册和回流），故，CVR实时样板拼接可以为以下的流程：</p>
<p>由于转化比曝光点击要晚到，这里窗口时间为4h，即CTR等待转化数据4h内进行匹配即可，否则视为延迟样本。</p>
<p>1、注册数据流跟CTR特征数据流进行 interval join 后，得到注册特征数据。</p>
<p>2、回流数据流跟CTR特征数据流进行 interval join 后，得到回流特征数据。</p>
<p>3、4h窗口内CTR特征数据匹配上转化数据的视为非延迟正样本，没匹配上的视为非延迟负样本。4h窗口外的转化数据到达视为延迟正样本。最后，注册特征数据跟回流特征数据进行汇总后形成最终的CVR特征数据，通过sink输出到下游TDBank供算法侧消费学习使用。当然TDBank也会定时1h输出数据到TDW，供离线分析和对账。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(8)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<h3 id="aa8e1bf6-1ed5-279d-ffd6-4aad5ab79457" class="toc-enable">二、Flink Topo图</h3>
<p>通过上面的流程模块图可以得知，在Flink CVR Topo图也将有各个模块与之对应，注册数据流、回流数据流 和 CTR数据流作为source输入，并且注册回流分别跟CTR数据流进行interval join后得到4h内的正、负样本，4h外的转化为延迟正样本。最后将结果拼接后输出至下游tdbnak供算法侧实时消费分析。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(9)" alt="" style="position: relative; z-index: 2;"></p>
<p>从Topo流图中可以看出给每个算子的并行度为50，因为转化的qps不高，足以支撑整个系统稳定运行。</p>
<h1 class="toc-enable" id="810a3b3b-7f08-e746-af1b-ff0eddb52c47">CVR拼接效果</h1>
<p>经过代码和集群优化后，CVR作业已稳定运行，并能正常拼接上的注册、转化数据直接输出，但负样本需要等4h窗口过期后再sink输出。输出量符合预期。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(10)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<h1 class="toc-enable" id="e81aefff-bd69-31cf-ed30-e5b9c451decd">问题与优化</h1>
<h3 id="ccad4ca2-1da9-5de0-a47d-7b6b1c50d0fd" class="toc-enable"><strong>1、CTR没有拼接上Redis中的特征数据问题</strong></h3>
<div style="text-align: left; float: none;"><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(11)" alt="" style="position: relative; z-index: 2;" class="amplify"></div>
<div style="text-align:left;float:none;">如上图可以看出，window join后没有send输出到下游算子了（155个CTR样本未send输出）。在保证曝光点击流生成的key（requestID+“|”+creativeID）&nbsp; 跟&nbsp; 特征数据流写入redis的 key一致的前提下，双流join的时候还是没有匹配上redis中的key，导致拿不到对应的特征数据。经排查，存在以下两种情况：</div>
<div style="text-align:left;float:none;"><strong>1）曝光和点击客户端存在重复上报的问题，导致曝光跟点击根本就没有匹配上。如：</strong></div>
<div style="text-align:left;float:none;">
<p>第一次曝光时间 09:59</p>
<p>点击时间 10:00</p>
<p>第二次曝光时间 10:01</p>
<p>join的时候，可能出现点击时间 在 第二次曝光时间前面，于是不满足 “曝光时间比点击时间早10min内” 的窗口约束</p>
<p>针对此问题提出的解决方案：</p>
<p>a、使用全局redis，流在接收到数据的时候将requestID从redis中取出比较，判断若有重复得丢弃此条数据，否则将requestID存至redis。</p>

<p>b、客户端上报一个标识，标记是否为此曝光点击数据是否为第一次上报。</p>
<p>跟客户端同学沟通后，采取了上报标识的方案。</p>
<p><strong>2）时间差问题：</strong>曝光点击流&nbsp; 跟&nbsp;特征数据流&nbsp; 两个作业差不多同时起来，于是从曝光点击流从redis中匹配不上特征数据。（特征数据还没来得及缓存进去）</p>
<p>故，需要特征数据流这个作业至少提前30min开启，因为我们最大的窗口为30min。（10min内为非延迟样本，10~30min内为延迟样本）</p>
<h3 id="58c1f8f5-911a-da99-0e4d-29a626945d76" class="toc-enable"><strong>2、CVR负样本未输出负样本问题</strong></h3>
<p>interval join 的时候 watermark没有推进到可以输出数据的时间：</p>
<p>在双流join的时候，watermark为两条流最小的那个流的watermark，如果flink定时器注册的时间为A，那么在watermark超过这个时间A后，代表左右边两流在时间A之前的数据都进来了或者已经等不到A之前的数据来匹配了。</p>
<p>由此可知：我们的场景是注册或回流数据 JOIN CTR数据，那么CTR数据的事件事件相对当前系统时间更加接近，而注册或回流数据的事件时间则到来的可能是几个小时之前的。那么watermark被设置为很早之前的时间，然后watermark再慢慢往后前进。此时，只能看到注册或回流数据到来的输出（没匹配上CTR数据为延迟正样本，匹配上为非延迟正样本），却看不到CTR负样本数据的输出。而我们的窗口为4h，只需要CTR数据等待4h即可。假设来了一条回流数据是相对系统时间是4h前甚至可能更早之前的，那么我们至少需要等待8h或者更久（转化数据的事件时间不好估量）才能看到CTR负样本的输出，这样对内存也有较大缓存压力。</p>
<p>调整前（下图只展示注册流和CTR流的拼接示例 ），window join后仅输出正样本6个，1580个负样本未输出：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(12)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>由于我们当前的场景：注册或回流需要匹配跟点击数据时间在4h之内的，点击数据时间跟系统时间一般10min之内。故可以使用数据到来系统时间来作为窗口长度，即CTR数据系统时间等待注册或回流数据系统时间4h（流刚启动的第一个4h的数据需要特殊处理，因为：第一个4h转化数据可能出现匹配不上CTR数据，当作延迟正样本，其实可能为非延迟正样本）。当然还有一种办法就是将作业拆成两个，让CTR流数据先跑4h以上。</p>
<p>调整后（这里加了注册、回流两个source来拼接CTR source）：正样本匹配上后输出，且负样本在4h窗口过期后慢慢输出中（图中window join后send的红框数量慢慢比source红框的数量大，因为CTR特征数据的source中包含了大部分的负样本数据流下来）</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(13)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p><br></p>
<h3 id="dc1a0cad-8a24-5633-456d-a65e674a532e" class="toc-enable"><strong>3、曝光点击时间戳不对问题</strong></h3>
<p>在数据跑通以后，发现点击时间和曝光时间一样，且都不是其中一个的正确时间。</p>
<p>如下图：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(14)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>经排查，发现在Oceanus上设置的事件时间，如曝光时间impression_timestamp，Oceanus这边从TDBank那边同步过来的时间字段仍然是Long类型，不是timestamp或者date类型。但不能当作Long类型进行获取。导致获取字段值的时候转换有误。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(15)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>需要对时间进行特殊转换，先转换成String类型的时间，再从String类型时间转换成时间戳：</p>
<p>UNIX_TIMESTAMP(From_unixtime(click_timestamp, 'yyyy-MM-dd HH🇲🇲ss'), 'yyyy-MM-dd HH🇲🇲ss')</p>
<p>转换后点击、曝光时间正常。如下图所示：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(16)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<h3 id="99520619-50a8-1bf3-8717-231e000af4a7" class="toc-enable"><strong>4、数据倾斜、数据反压问题</strong></h3>
<p>在线样本拼接任务偶发checkpoint超时失败告警。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(17)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>观察监控页面出现了数据反压，可想而知是window-join算子计算不过来了。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(18)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>甚至已经反压到source端，导致tdbank消费的严重延迟，如下图可以看出消费速度比生成速度低一个数量级：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(19)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>想到的第一个办法就是扩算子并行度，将join和sink算子并行度扩大到1000，有缓解，但还是会出现处理不过来的情况，没有从根本上解决问题。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(20)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>于是，再对落地tdw的数据进行分析，经过定位发现有热点数据，再经过排查这些热点requestID大多为异常数据。从而导致集群单个节点数据过多计算过不来，CheckPoint也受到影响，从而造成数据积压，反压至tdbank端。</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(21)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>最后，通过对异常数据进行过滤，（若为正常的热点数据，需要考虑：增大并发度、在source端将key人工打散，预汇聚 等操作） 问题得到解决：</p>
<p>查看flink topo算子监控正常：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(22)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>CheckPoint正常，每次CheckPoint仅需30s左右：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(23)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<h3 id="21cf5348-c876-4ed3-8de4-0507e16311ea" class="toc-enable"><strong>5、写redis速度跟不上上游算子输出的问题</strong></h3>
<p>通过特征缓存redis的作业的flink topo图可以很清晰的看出每个算子的计算量，来分析数据经过每个算子后流向下游的数据量是否符合预期。下图可以看出window join输出量比sink接收量比大了3-4万，经分析，sink下游是输出到redis，故问题出在sink写redis慢了导致sink接收上游的数据慢的一个反压现象。</p>
<p>优化前：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(24)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>再分析代码，写入redis的key是requestID+“-”+creativeID，用‘-’拼接的，value是其对应的特征值。尝试使用‘|’拼接requestID+“|”+creativeID后，实验发现几乎没有再出现反压现象了，其他拼接符号也测试过，表现均没有‘|’ 好。也就是Oceanus API底层在使用“|” 拼接redis key写入redis的效率高于用‘-’或其他符号（已反馈现象）。有效解决redis sink输出的反压性能问题。下图中可以看出，&nbsp; woindow-join算子的输出跟sink的接收到的量几乎一致。</p>
<p><strong>同时，将同步写redis的方式改成异步写，使用RedisAsyncFunction，大大提升了写的效率。</strong></p>
<p>优化后：</p>
<p style=""><img src="./基于Flink广告在线学习 - 互娱Online - KM平台_files/cos-file-url(25)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<h3 id="ac102e68-081c-a419-c164-07fcd7b02f97" class="toc-enable"><strong>6、Flink集群参数优化</strong></h3>
<p><strong>taskmanager.vcores：2</strong></p>
<p>每个TaskManager的vcore数量，默认值2，相当于增加最大并行度（Oceanus默认会给每个算子设置同样的并行度=总vcore数量=cpu核数*此值/2），另外，还需要手动调整source的并行度跟上游的tdbank或kafka的并行度保持一致，不然多的并行度分配到的资源为空闲状态。</p>
<p><strong>env.java.opts.jobmanager：-Xmx8192m -XX:+PrintGCDetails -XX:+PrintGCTimeStamps</strong></p>
<p>JobManager运行内存参数，默认2G，当任务作业太大的时候，需要适当增加内存，不然可能作业起不来，Oceanus监控页面打不开。</p>
<p><strong>checkpoint.timeout：1800000</strong></p>
<p>CheckPoint超时时间，单位s，根据时间state大小决定，同时还需要设置多久CheckPoint一次。</p>
<p><strong>slot.per.taskmanager：4</strong></p>
<p>每个taskmanger的slot个数，默认2。总taskmanger个数为最大算子并行度值/本值</p>
<p><strong>source.repartition.type：REBALANCE</strong></p>
<p>该参数主要用于消息中间件在分区数据不均匀的时候，进入Oceanus后可通过配置进行再均衡（REBALANCE），以防热点数据倾斜。参数可取值：REBALANCE、SHUFFLE、FORWARD、RESCALE</p>
<p><strong>空闲状态保存时间：1天</strong></p>
<p>此配置主要用于定期清理空闲的state数据，需要根据实际情况来保存数据。主要考虑的点有：</p>
<p>a) 当集群或作业故障需要恢复历史数据</p>
<p>b) 磁盘是否能够撑得下这么久的数据（当使用rocksdb存储的时候）</p>
<p>c) 如果state数据将全部用来计算，这么久的数据是否可以计算的过来</p>
<h1 class="toc-enable" id="01ec0e5f-3824-8fe8-aab4-3a4cac4741f2">总结</h1>
<p>本文介绍了系统整体方案，采用了Flink计算完后输出到TDBank的方案。也详细介绍了CTR和CVR样本特征拼接的方案选型和对比，给出了落地方案的具体实现过程，并取得了良好的实时拼接效果。当数据量增大时系统可支持横向扩展，也具有良好的容灾机制，集群故障数据可恢复。最后，文章中也总结了遇到的redis映射特征数据失败、cvr未输出负样本、时间戳问题、数据倾斜反压、Redis Key拼接问题、和Flink集群参数优化方法。</p>
<p>通过使用Oceanus平台，基于Flink实现了海量数据的样本拼接，CTR和CVR都正常拼接特征输出至TDBank，算法侧已正常消费进行模型训练学习。后续如果遇到其他问题将持续跟进优化和总结。</p>
<p><br></p>
<p>-----------------------</p>
<p><span style="color:#ff0000;"><strong>持续更新总结：</strong></span></p>
<p><span style="color:#ff0000;"><strong>优化篇请参考后续文章：<a href="https://km.woa.com/group/15716/articles/show/483752" target="_blank" style="color:#ff0000;" rel="noreferrer">百万QPS-基于Flink的Union+Timer优化广告多流Join</a></strong></span></p>				</div>
