---
title: "游戏广告-基于Flink建设高性能实时数仓"
date: 2022-06-17 11:32:52
categories:
  - linux
---

<h1 id="7cc2d1ee-a8b6-b91e-003e-9c1dd334882d" class="toc-enable">现状分析</h1>
<p class="toc-enable">&nbsp; &nbsp; &nbsp; &nbsp;针对我们游戏广告业务，数据建设是必不可少的重要一环。如：产品运营同学需要数据去分析广告投放效果，以便合理的调整预算等；算法同学需要数据去做在线、离线的模型训练，以达到更好的推荐效果；老板们或许会去关注ROI等指标，以便上层决策。</p>
<p class="toc-enable" style="">&nbsp; &nbsp; &nbsp; &nbsp;而在多年以来数据的开发模式主要是烟囱式的开发模式，产品提需求，开发做需求，以致于会有很多重复的开发工作、代码没有统一，维护困难。以下是现在的开发架构：<br><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(2)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p class="toc-enable">如上图所示，会有很多个flink计算任务，根据产品需求开发不同的任务，期间存在这计算相同指标重复计算的情况，每个计算任务零散分布着，功能未抽离，带来了极大的维护困难：</p>
<p class="toc-enable">1、代码重复开发，耦合，数据冗余，浪费存储和计算资源。同时使用了Ocenaus平台和IEG数据平台。</p>
<p class="toc-enable">2、结果数据写入和查询方式欠佳，看板查询慢等情况。</p>
<p class="toc-enable">3、表多且复杂，甚至不同表有重复的指标，不方便产品运营同学高效使用。</p>
<p class="toc-enable">4、统计口径前后不一致，会出现统计错误的情况。</p>
<p class="toc-enable">5、缺少完善的监控系统，不能及时发现业务问题。</p>
<h1 id="e84cd043-e8ed-f888-9ab5-ea3fb40df58b" class="toc-enable">设计目标</h1>
<p>1、数据结构清晰：通过具体且详细的数据分层，让每一层都有其具体的职能，划分层次结构清晰明了。</p>
<p>2、减少重复开发：通过数据分层后，每个数据模块都能够起到复用的能力，提高开发效率，减少重复计算，节省计算资源。</p>
<p>3、统一数据口径：通过数据分层后，能够对外输出统一的口径和统一的计算规则。</p>
<p>4、提高计算/查询性能：统一底层数据处理架构，和优化每个模块的计算、存储模型，节省计算资源，将计算延迟降到最低，提高看板查询效率。</p>
<h1 id="036e2a9e-68ad-7356-8d85-b0c74c09e1ee" class="toc-enable">技术选型</h1>
<h2 id="4990e1f0-b15b-8e5d-8e3c-5f0dd4949301" class="toc-enable">数仓架构</h2>
<p><strong>选型对比：</strong></p>
<p><strong>Lambda架构</strong>：实时计算和离线计算、存储分离的架构。<strong>优势</strong>是一种业界使用最为广泛且成熟度最高的架构，容错性搞，迁移成本低。<strong>劣势</strong>是需要维护实时、离线两套代码，存在口径不一致的问题。</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(3)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p style="text-align:center;">注，<a href="https://libertydream.github.io/2020/04/12/lambda-%E5%92%8C-kappa-%E7%AE%80%E4%BB%8B/" target="_blank" rel="noreferrer">图片来自网络</a></p>
<p><strong>Kappa架构</strong>：实时和离线一套实时代码和存储的架构。<strong>优势</strong>是实时和离线为一套代码，实时离线统一口径。<strong>劣势</strong>是目前还不够成熟业界使用和成熟度不够，有些指标不适合用纯实时计算，同时迁移成本很高。</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(4)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p style="text-align:center;">注，<a href="https://libertydream.github.io/2020/04/12/lambda-%E5%92%8C-kappa-%E7%AE%80%E4%BB%8B/" target="_blank" rel="noreferrer">图片来自网络</a></p>
<p>由于我们目前现在是在过去这些年里有大量的离线历史任务在维护着，如果全量迁移至Kappa架构则需要耗费非常多的人力成本。通过综合考虑，<strong>数仓</strong>采用使用业界成熟的<strong>Lambda架构</strong>，实时和离线两套任务。同时可使用监控告警对任务和数据进行对账。</p>
<p><b>技术难点：</b></p>
<p>数仓架构，即将数据仓库分成不同的层次，如何设计模块解耦、数据复用，减少开发成本、提高开发效率、提高产品运营查询效率的效果具有一定的挑战性。<br></p>
<h2 id="72d5d17f-11ba-55ec-496e-3b26dc6f8e69" class="toc-enable">实时计算</h2>
<p><strong>选型对比：</strong></p>
<p><strong>Flink</strong>：实时流处理，具有低延迟、高吞吐、支持精确性一致性的语义、使用CheckPoint来保障数据的容错机制且业界使用高的特点。</p>
<p><strong>Spark Streaming</strong>：微批处理，延迟相对Flink高些，当然也支持高吞吐、支持精确性一致性的语义、使用CheckPoint容错机制，业界使用其作为实时处理的场景不多。</p>
<p><strong>Storm</strong>：实时流处理，低延迟、吞吐量相对Flink低些，支持至少一次的准确度语义，使用ACK每条数据确认的容错机制，现在业界使用不多。</p>
<p>于是，通过对比，<strong>实时计算</strong>采用<strong>Flink</strong>作为实时计算的框架。</p>
<p><b>技术难点：</b></p>
<p>设计至少能支持100wQPS的流量实时关联、计算的能力，高效精确去重、高效维表关联、高效指标计算。窗口1min，整个计算延迟1min左右。对于整个系统而言是一个较大的挑战。</p>
<h2 id="c15019f0-a291-60af-2e3a-635f78b0f671" class="toc-enable">实时存储</h2>
<p><strong>选型对比：</strong></p>
<p><strong>ClickHouse</strong>：具有海量数据批量写入、预聚合能力、索引能力、高性能实时精确聚合查询的特点，业界使用高。</p>
<p><strong>Elasticsearch</strong>：具有全文检索能力、无预聚合能力，在实时聚合查询性能方面也相对ck慢些，更适合日志存储检索。</p>
<p><strong>Druid</strong>：具有数据批量写入、预聚合能力、查询性能相比ck慢些，同时在计算全局TopN的时候只能取近似值。</p>
<p>于是，通过对比分析，<strong>实时存储</strong>采用了<strong>ClickHouse</strong>。</p>
<p><b>技术难点：</b></p>
<p>设计目标存储组件能够具有高性能写入、高可用分布式且高性能分布式查询能力。同时需要对存储组件在写入和查询方式上做一定的优化手段。</p>
<h1 id="27ad537d-9d73-a40c-d0ba-d3801d4ced02" class="toc-enable">数仓架构</h1>
<h2 id="b4c43f3d-52f1-ad28-f2b3-332f2dfdfaef" class="toc-enable">业务架构</h2>
<p>通过对广告业务场景进行整理分析后，从业务角度将整个实时数仓进行了多个层级划分：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(5)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p>如上图所示，从下往上分别是：</p>
<ul><li>ODS层，即源数据层：主要由SDK上报的原始数据，及O2的数据。上报在TdBank消息队列中。</li>
<li>DIM层，即维表层。主要是后台系统的一些原始配置，如：SSP、DSP平台配置，存储在Mysql、Mongodb等数据库里。</li>
<li>DWD层，即明细数据层。主要是将ODS层源数据经过清洗、字段扩展、字段翻译等加工后生成的明细数据，如：请求明细、广告行为明细、广告效果明细、竞价过程明细等。</li>
<li>DWS层：即服务数据层。主要是将DWD明细层数据按照一定维度的轻度聚合后的数据，如：请求信息汇总、竞价过程汇总、广告行为汇总、广告效果汇总。</li>
<li>ADS层：即应用数据层。主要有以下几个方面的应用：</li>
</ul><ol><li>实时看板：会将DWS层轻度聚合后的数据按照看板应用主题进行高度汇聚后生成，方便查询高效。</li>
<li>业务监控：对业务数据进行实时监控，如每分钟监控曝光量波动情况，消耗情况等。如出现异常，会进行实时电话、企业告警。</li>
<li>数据服务：提供数据接口服务，供其他团队同学使用结果数据，如：SSP后台系统实时结算页面数据。</li>
<li>在线学习：将样本拼接后的DWD层明细数据对接算法侧，为其提供可靠且实时的有效的样本数据，为实时算法在线学习分析、广告推荐提供数据支撑。</li>
</ol><h2 id="a1a20e77-b472-373a-9e15-976df087d266" class="toc-enable">技术架构</h2>
<p>在将实时数仓在在业务层面划分后，需要进行实际的落地实践。在此，需要将业务划分好的实时数仓结构从技术层面进行细化。在此消息队列中间结果缓存采用TDBank，实时计算采用Flink，结果存储采用ClickHouse，实时看板采用DataTalk。详细的技术架构如下图所示：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(6)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p>如上图从技术层面将实时数仓分为了这么几层：</p>
<ul><li><strong>接入层：</strong>这一层承接了ODS层的源数据，使用TDBank消息队列接收SDK上报过来的实时数据。</li>
<li><strong>计算层、中间结果层：</strong>这一层主要对数据进行加工和计算可以细分为：</li>
</ul><ol><li>Flink清洗转换：从ODS层的TDBank中读取源数据后，进行过滤、翻译、格式化、字段扩展、字段填充、流流JOIN合并等操作。跟DIM层的维表配置进行字段翻译转换。处理完后输出到下游TDBank消息队列作为DWD明细层数据。</li>
<li>Flink轻度聚合：从DWD层的TDBank中读取明细数据，按照业务主体进行轻度聚合，将聚合后的数据输出至下游TDBank作为DWS层数据。</li>
<li>Flink实时入库：这里主要是一个Flink任务用来消费DWS层的结果数据，并将数据进行实时入库至ClickHouse存储。</li>
<li>Flink监控告警：这部分主要为部门广告业务量身定制的且便捷灵活的七彩石配置告警规则、收敛规则的一套告警系统。实时监控业务指标的波动情况，并进行阈值告警，支持电话、短信、企业告警。</li>
</ol><ul><li><strong>存储层：</strong>这一层主要使用ClickHouse作为存储组件，存储DWS层数据，以及经过物化视图将DWS层数据进行聚合后的ADS层高度聚合的数据。</li>
<li><strong>应用层：</strong>主要将数据应用于实时看板、业务监控、数据接口服务、算法在线学习、离线数仓TDW计算等场景。其中，实时看板主要对接DWS层、ADS层的数据查询。业务监控主要对接DWS层轻度聚合后的数据。在线学习主要对接DWD层的明细数据。</li>
</ul><h1 id="ee1cb5c5-e149-364d-759a-3849cd29ae98" class="toc-enable">实时计算</h1>
<p>在设计了整体技术架构后，对Flink部分进行了详细的设计，主要分为：Flink CDC配置实时增量同步、Flink清洗转换、Flink轻度聚合、Flink实时入库、Flink监控告警四大部分。程序自监控代码埋点上报日志到CLS日志监控，方便日志排查问题，ERROR日志及时告警。同时我们的代码部署在Oceanus平台上，自监控的指标（算子量、耗时、CPU、内存）也由Oceanus采集并监控。日志监控及自监控均配置阈值告警，以便及时处理故障。</p>
<h2 id="18cc7c1f-3851-fc6d-fb86-c70ac9bab236" class="toc-enable">配置同步设计</h2>
<p>配置同步，同步维表数据至Redis。即在<strong>DIM层</strong>将配置同步任务分离成一个单独任务，跟计算任务解耦，因为配置表结构不定期会有变更或者增加配置表的情况。同时，由于配置表的更新比较频繁，比如创意、广告组、广告计划每天得新增修改好几百次。于是，采用了Flink CDC实时增量同步配置至Redis。</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(7)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p><strong>Source端：</strong>考虑到实时计算需要时效性较高的去同步更新配置，如果使用每天更新一次配置的方式，则会造成：如果当天现在了某个维度的数据，那么在那一天内都转换不出对应的Name。于是，采用Flink CDC读取DIM层的配置数据，采用监听DB Binlog的方式来实现全量+增量同步数据，不给DB本身增加额外的查询压力，每次读取到数据Flink都会以CheckPoint的形式存储读取的源和位置，于是即使Flink任务挂掉，重启恢复后也能正常的增量读取配置。将读取的配置放在状态State中存储，重启也不会丢失配置。</p>
<p><strong>Trans端：</strong>主要是筛选配置表中需要的维度，组合成Java对象。</p>
<p><strong>Sink端：</strong>使用Hset/Hmset方式写入Hash结构至redis，以便精确且快速的查询到某个ID下的某个维度值。如：根据media_app_id为1，查询 media_app_name、account_name的值等。</p>
<h2 id="b08d64ab-94d8-d337-8034-2979f4acb9fa" class="toc-enable">清洗转换设计</h2>
<p>这一层主要介绍如何设计生成<strong>DWD层明细数据</strong>，以及DWD层数据流向。DWD层旨在设计将数据进行标准化格式转换，同时又能够兼容离线、实时一套代码的流批计算一体架构。节省计算资源，方便代码维护，统一DWD层数据口径，公共功能解耦下沉。使用Flink实时计算来作为处理DWD层数据的技术框架，更具有时效性。如下图所示：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(8)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p>Flink消费来自ODS层TDBank实时数据，清洗转换后写入TDBank明细数据层，即实时DWD层。这一层的数据会每小时落库至TDW供离线Spark计算DWS层数据使用，同时也供Flink计算实时DWS层数据使用。达到DWD层在实时和离线的数据统一，使用同一份计算代码，在DWD层实现流批计算一体。</p>
<p>Flink清洗转换部分下面详细介绍：</p>
<p>这一部分主要使用Flink对数据ODS层数据进行清洗转换。如曝光、点击数据。如下图为多流场景的Flink清洗转换具体流程：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(9)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p><strong>Source端：</strong>接收数据。读取Tid-A数据源，如曝光数据。</p>
<p><strong>数据清洗：</strong>通过使用Ocenaus库表同步TDBank的Tid表结构，来管理每一张数据表，包括：字段名称、字段类型、字段描述、字段取值范围等。当TDBank Tid的字段有变化的时候，可以很方便的在Oceanus页面上导入最新的表结构，方便管理和维护，无需变更Flink程序即可更新。Flink程序通过Ocenaus接口定时读取对应的最新版本的表结构信息。根据实际业务场景，进行<strong>异常数据(字段长度、字段类型、字段取值)过滤、流流关联字段拼接、json维度字段解析扩展、维度ID-Name转换等操作</strong>。如果有异常数据则侧输出到下游TDBank消息队列，已备后续数据对账使用。</p>
<p><strong>Trans处理：</strong>数据转换。将流数据跟Redis中的配置维表进行Join操作，也就是对字段进行翻译转换，Redis存储为Hash结构，如媒体ID翻译得到媒体名称，采用批量读取Redis操作，减少对Redis的QPS压力，同时加快维表查询效率。（经压测后，60W QPS数据，每批1000条批量查询Redis，Redis的QPS也只有几百，且CPU负载为4%左右，查询效率为4ms左右。由于总DIM配置数据的大小也只有几百M，故，为了保障Flink CDC同步最新配置至Redis的时效性，这里先不将配置缓存至本地了，不然还需要额外增加本地缓存更新机制。）&nbsp; 如有 双流关联字段拼接操作在维表Join之前完成即可。</p>
<p><strong>Sink端：</strong>将转换后的数据输出至下游TDBank消息队列，作为DWD层明细数据。</p>
<p>同时，TDBank DWD层明细数据还需要落库TDW作为离线数仓Spark计算的DWD层明细数据，这样，经过Flink清洗转化后的明细数据DWD层达到了实时数仓和离线数仓的代码、口径、资源的完全统一，方便维护，节省计算成本，即在DWD层率先实现了流批计算一体。当然，TDBank DWD层明细数据还将用在在线学习等场景。</p>
<h2 id="e620b0e4-2f82-09dc-924d-1857c237f4b7" class="toc-enable">轻度聚合设计</h2>
<p>这一部分主要是使用Flink对数据进行轻度聚合，生成<strong>DWS层</strong>数据，如：广告行为汇总数据，包含了媒体ID、创意ID等维度，曝光量、点击量等指标。如下图为Flink轻度聚合具体流程：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(10)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>如上图所示：</p>
<p><strong>Source端：</strong>从TDBank消息队列明细数据的DWD层读取数据。</p>
<p><strong>Window计算：</strong>根据指定的维度进行Group By，对指标进行1分钟窗口内的聚合计算。窗口大小可以根据业务需要调整，支持将延迟的数据窗口计算，增量聚合计算。</p>
<p><strong>Sink端：</strong>将聚合后的结果数据输出至下游TDBank消息队列作为DWS层数据，这一层用作入库前解耦，避免数据丢失，同时也可以用作业务监控。</p>
<p>高度聚使用ClickHouse的物化视图实现，在下面的ClickHouse设计那一节将详细介绍。</p>
<h2 id="3f32d8b0-6407-b4e2-e4b1-7d0c94b62037" class="toc-enable">实时入库设计</h2>
<p>这一部分使用Flink进行实时入库，将TDBank消息队列中的DWS层的数据消费入库至ClickHouse。</p>
<p>如下图为Flink实时入库的详细过程：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(11)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>如上图所示，Flink实时入库主要由以下两个部分组成：</p>
<p><strong>Source端：</strong>读取TDBank轻度聚合的DWS层的数据。</p>
<p><strong>Trans处理：</strong>从Oceanus中读取对应主题的表结构，并将从Source接收到的数据生成对应结构数据。</p>
<p><strong>Sink端：</strong>根据不同主题将数据输出至Clickhouse不同的表中，即DWS层数据入库，对接实时看板。</p>
<h2 id="cd719bad-53fa-6449-abd9-c86ee98d53f7" class="toc-enable">监控告警设计</h2>
<p>这部分主要指对业务数据进行实时的监控，如：监控曝光量大于某值告警、消耗大于某值告警。为了方便产品、运营、开发同学及时发现业务指标波动情况，及时发现系统存在的线上异常问题，及时通知相关通信处理解决问题，超额消耗时为业务及时止损，低消耗时合理调整预算。如下图所示为Flink监控告警的详细流程：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(12)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>如上图所示，采用Flink监控告警主要由以下几个部分组成：</p>
<p><strong>Source端：</strong>读取TDBank轻度聚合的DWS层的数据。</p>
<p><strong>Trans处理：</strong>针对1min窗口计算的数据以及配置的告警规则，对实时数据进行告警检测。</p>
<ul><li>定时通过HTTP接口读取产品运营同学在七彩石配置系统上配置的告警规则，主要包含了如：周一大盘曝光量对比前一小时增长100%告警，周二波动80%告警，告警接收方式为电话，告警接收人对应每天的值班列表。告警半小时收敛等等。用于详细的配置告警规则、收敛规则等。</li>
<li>将数据指标达到告警阈值时，先从Redis获取告警规则ID判断当前告警规则ID是否还在收敛时间内（当前时间减去告警时间是否大于收敛时间），如果收敛，则不告警，不输出下游。否则将数据输出至Sink端，同时将此告警规则ID（RuleID）、告警时间 记录至Redis，下次根据规则ID判断是否在收敛时间范围内。</li>
</ul><p><strong>Sink端：</strong>根据告警规则配置的告警接收方式和接收人，进行电话告警。同时将告警结果的数据输出至Clickhouse存储，以便后续排查告警记录和问题排查。</p>
<p><strong>关于业务告警的详细方案设计和问题解决，详见作者另一篇KM文章总结：</strong></p>
<p><strong><a href="https://km.woa.com/group/51643/articles/show/493596" target="_blank" rel="noreferrer">基于Flink建设广告业务告警系统</a></strong></p>
<h1 id="e7b2c153-a83f-c2d6-3217-7d80ef5d77ce" class="toc-enable">实时存储</h1>
<p>实时数仓的存储模块采用了ClickHouse实时存储组件，其毫秒级的单表查询效率被业界广泛认可。采用Flink将数据写入ClickHouse，采用DataTalk看板查询数据。数据写入即使用Flink将从TDBank消费到的数据写入到ClickHouse。针对这部分主要从写入和查询两方面进行设计：</p>
<h2 id="e1b7c507-5439-3959-1b8f-aff5623ff7ac" class="toc-enable">写入设计</h2>
<h3 id="dd9542ed-1cd1-b531-872b-4f39dccad1ed" class="toc-enable"><strong>方案一</strong></h3>
<p>第一种方案采用直接写入本地表的方式，且批量写入，设置好partition key，以防止ClickHouse出现parts太多合并的问题。</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(13)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p><strong>Flink Source端：</strong>读取TDBank的数据，如读取DWS层轻度聚合的数据。</p>
<p><strong>Flink Sink端：</strong>现根据在ClickHouse建表时指定的Partition Key字段对应的数据进行Hash，写入到ClickHouse后端对应的分片上，直接写入本地表的形式，提高写入效率，不写分布式表（以免数据分发导致写放大，使得单节点磁盘IO撑爆）。比如：这一批的数据只会链接ClickHouse后端的某个节点，写入Shard-1分配里面直接存储。也就是DWS层轻度聚合后的数据入库了。</p>
<h3 id="699e596f-511d-6c69-50a3-16f64c8f6d9f" class="toc-enable"><strong>方案二</strong></h3>
<p>第二种方案采用flink写入clickhouse分布式表的方式代理写入到具体分片。具体如下图所示：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(14)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p><strong>Flink Source端：</strong>读取TDBank的数据，如读取DWS层轻度聚合的数据。</p>
<p><strong>Flink Sink端：</strong>将读取到的数据直接写入指定ClickHouse集群的分布式表里面。入库操作交给分布式表所在的分片，先将所有的数据落在Shard-1的临时目录，再根据partition key将其他数据写入到具体的分片上。注：这里会出现写放大，增加Shard-1的磁盘IO开销，非最优入库方式。</p>
<p>故，本实时数仓系统中写入方式采用<strong>方案一</strong>。</p>
<h2 id="506dcf5b-a8a3-ad5f-9b85-d2bfda82ca46" class="toc-enable">查询设计</h2>
<p>数据查询即查询ClickHouse的数据，展示在BI看板上面供数据分析使用。下图为查询ClickHouse的详细流程：</p>
<h3 id="14b84b7f-6875-5439-511a-0aeeff1963e7" class="toc-enable"><strong>方案一</strong></h3>
<p>使用proxy分布式表查询：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(15)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>DataTalk实时看板向ClickHouse的分布式表发送查询请求，查询请求会转发给所有后端分片，所有分片将查询到的结果会发送给其中一个Shard-1将结果合并后，返回给分布式表（Proxy代理，不存储数据），最终结果返回给看板。采用查询分布式表的形式可以将查询结果不遗漏，且正确，特别是对于Distinct去重指标的时候。当然，如果某个Shard分片上没有数据的话会空查询。</p>
<h3 id="abedc396-bafe-f168-829e-8cc7215cc64f" class="toc-enable"><strong>方案二</strong></h3>
<p>根据Partition Key生成规则，直接查询对应Shard：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(16)" width="435" height="392" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p>DataTalk实时看板向ClickHouse的发送查询请求，这回是直接向指定的分配进行查询，没有了proxy，指定的Shard查询到将结果返回，高效查询。避免了向其他Shard空查询。</p>
<p>考虑到我们的BI看板为产品运营同学自行个性化配置，且配置较多复杂的看板页面，查询条件也不好由开发事先设定，于是采用了<strong>方案一</strong>的查询方式，因为数据是按照日期来设定Partition Key，写入的时候Hash写入，于是也不会出现分片查询空的情况，同时，分布式查询效率也更高。</p>
<h2 id="db34f350-d197-c7d7-d8c5-c573cf523d56" class="toc-enable">整体设计</h2>
<p>在设计完ClickHouse高效写入和查询方式后，实时数仓的ClickHouse整体设计方案进行详细给出总体架构视图，包括写入、本地表、物化视图、分布式表、查询等。</p>
<p><br></p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(17)" width="753" height="268" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>如上图所示，由FlinkSource端消费TDBank数据后，在Flink Sink端将数据根据Partition key进行Hash后，路由到对应的分片上，直接落到本地表存储。也就是DWS层数据入库了。此时，使用物化物化视图，按照业务需要的维度进行高度聚合，ADS层的数据。建立分布式表查询本地表（DWS层）或者物化视图（ADS层）的数据，对接DataTalk查询分布式表展示实时看板数据。</p>
<h1 id="91275a5a-da65-c282-a89e-bdb186426ac3" class="toc-enable">问题与优化</h1>
<h2 id="9fed2489-e034-42a9-9073-0ba2376921c2" class="toc-enable">精确去重</h2>
<h3 id="3f74bcdd-4740-8bce-502e-9ae91773a717" class="toc-enable"><strong>原始方案</strong></h3>
<p>去重，顾名思义就是根据某个或者某些维度在某个时间范围内将所有数据去掉重复的。如，在广告业务有去重统计的指标如：根据requestID去重统计请求量、曝光量、点击量等。比如，对一个1min窗口内的数据进行去重，最初使用了如下的方式：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(18)" width="448" height="358" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p>Flink Source在消费到数据后，将数据根据Group By Key进行分组，进入Window算子，然后在Window算子里面使用HashSet的方式，将所有的RequestID进行去重，然后输出下游。此时很快就出现了严重的问题：当量越来越大的时候，马上出现了数据倾斜、算子反压的情况，任务僵死状态。如上图中橙色的算子的量比绿色的算子的量要大很多，橙色部分算子数据会倾斜严重，数据反压。</p>
<h3 id="2be3ffab-6303-baea-50b4-35b9c1feb680" class="toc-enable"><strong>第一次优化</strong></h3>
<p>于是进行了一次优化，先进行预聚合，也就是先将数据打散均衡到每个task上，再最终聚合的时候进行去重。</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(19)" width="532" height="414" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p>此方法看上去没有啥问题，且初步解决了算子倾斜的问题，让计算量阶段性变小（因为这个任务可能要需要计算其他指标），但是，即使是预聚合也无法在预聚合的时候进行去重，也就是还是需要到最后聚合的时候进行去重，也就是如上图所示，再跑了一段时间以后，橙色的"Flinal-Reduce"&nbsp; 算子仍然会出现数据倾斜的情况，因为仍然是所有的RequestID都需要落在同一个Task上才能去重。于是反压问题又一次要出现了。即使，10w QPS的数据量，已经使用了400核（图中为398个并行度），1.6T内存资源。</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(20)" alt="" style="position: relative; z-index: 2;"></p>
<h3 id="283c4a7f-f82a-7c3c-a618-d194c7bdf17a" class="toc-enable"><strong>第二次优化</strong></h3>
<p>从根本上分析原因：使用Flink精确去重需要解决的问题是：1、数据倾斜。 2、精确去重。要想完美的解决这两点</p>
<p>需要变化思路。之前的去重都是这样做的：将所有的RequestID放到一起去重，那么如果1min内有1000w个RequestID，而只有10条RequestID是重复的，那么仍然需要将1000w个RequestID放到一起去重（不管使用的数据结构是HashMap、HashSet、BitMap、HipLogLog等都一样的），而极大的浪费了计算资源。其实，换个思路来看这个问题，我们只需要找到这10条重复的RequestID放到一起进行去重即可，其他不重复的数据无需一起去重。于是，设计了第二次优化方案，如下图所示：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(21)" width="721" height="368" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></p>
<p>圆圈的A、B、C、D、E代表RequestID（需要去重的ID）不同的数据，橙色、绿色圆圈表示不同的Key-2类别的数据。</p>
<p>在Source端接收到数据后，Map算子将数据经过Key-1分组后，Hash均匀分发数据至下游去重算子，去重算子进行去重后，会将数据Forward给聚合算子（因为这个算子的Key分组跟上游去重算子的Key分组一样，可以进行算子Chain到一起，无需额外的网络传输数据，节省网络IO消耗），再将数据进行Key-2目标聚合维度分组后进行最终聚合，最后输出下游存储。</p>
<p><strong>Key</strong><strong>设计</strong></p>
<p>Key的设计十分的关键，分为去重预聚合的Key-1，和最终聚合的Key-2。在不同阶段根据不同的Key进行分组GroupBy，以达到高效去重和聚合的目的。具体设计如下所示：</p>
<p><b>HashID</b> = (去重ID的HashCode值)%(并行度个数*倍数)&nbsp; &nbsp; &nbsp;即：取模运算。由于我们业务的RequestID为正常情况都是每次不重复，出了异常情况或者SDK 的Bug导致重复上报，于是这里的“倍数”可以取值为1，让其均匀的分布在每个并行度上，当然，相同的RequestID一定会分布在同一个Task上的。</p>
<p><strong>Key-1&nbsp;</strong>= 目标聚合维度 + <b>HashID</b>&nbsp; &nbsp; 即：Key拼接，去重和预聚合维度</p>
<p><strong>Key-2 </strong>=<strong>&nbsp;</strong>目标聚合维度</p>
<p><strong>接收并分发数据阶段</strong></p>
<p>接收上游的数据，并根据GroupByKey-1来将数据进行Hash后，均匀分发给下游各个Task，使得不会产生数据倾斜的情况，如上图中，Source-Map阶段3个Task接收了绿色的数据5个，橙色的数据7个，在经过Key-1分组进行Hash后，分别均匀分发给下游4个算子进行去重运算，应为相同的Key-1的数据会分布到同一个Task上去，每个Task上面3条数据。</p>
<p><strong>数据去重阶段</strong></p>
<p>即通过GroupByKey-1阶段的Key-1分组，为去重和预聚合维度设计。也就是经过第一个步骤分发数据阶段，会将接收到的每条数据根据Key-1分组后Hash将数据均匀分发至各个Task。通过这样的设计可以达到目的：相同的RequestID的数据会落到同一个桶里去，于是可以在同一个Task上实现精确高效去重（无需将所有的RequestID放到一起去重）。同时，又将数据进行了均匀打散，根据Task并行度取模。这样，有效的防止了热点Key而导致的数据倾斜问题发生，不会产生Flink算子阻塞反压。使用MapState来存放RequestID，判断是否已经出现过，出现过则去重丢弃，否则保留发送给下游。MapState的过期时间视需要去重的时长而定。</p>
<p><strong>预聚合阶段</strong></p>
<p>即通过GroupByKey-1阶段的Key-1（<strong>Key-1: </strong><strong>目标聚合维度 + HashID</strong>）分组，为去重和预聚合维度设计，具体Key-1的设计思路同去重阶段的Key-1。在分组后相同的Key-1会Forward到在此阶段主要实现1min窗口的预聚合。采用Reduce增量聚合的方式，有效节省计算资源，高效聚合。</p>
<p><strong>最终聚合阶段</strong></p>
<p>即通过GroupByKey-2阶段的Key-2（<strong>Key-2: </strong><strong>目标聚合维度</strong>）分组，也就是目标聚合维度，具体Key-2的设计思路为：</p>
<p>Key-1去掉HashID，即直接使用目标聚合维度。</p>
<p>在这个阶段无需使用窗口来聚合了，因为在预聚合阶段已经使用1min窗口预聚合了，在此只需要将数据直接sum求和即可。定时器设置为2s，使用ValueState接收存储中间结果，并将最终结果数据sum后输出至下游。</p>
<h3 id="bf5d0f96-8a8f-53b9-f6a6-faf429eada6e" class="toc-enable"><strong>优化效果</strong></h3>
<p style="">以10w QPS的量为例，优化后仅使用了20核（图中并行度为19个），80G。且无算子倾斜和反压现象。下图为优化后的flink topo计算部分截图：<br><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(22)" alt="" style="position: relative; z-index: 2;"></p>
<p style="">也就是，优化后，将原任务CPU为400核节省至20核，从内存1.6T优化至80G。<br><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(23)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<h2 id="22abe5b7-c574-37a4-f5b1-bbcd544f8da8" class="toc-enable">维表关联</h2>
<p>即将配置数据放在Redis中，将流数据中的ID维度转换成Name维度的一个过程。在实际项目过程中遇到的两个问题：</p>
<p>1、配置更新为天级别，于是当天变更的配置不能实时获取，导致当天的变更的数据不能正确的根据ID翻译出Name的情况，甚至转换的Name为空。</p>
<p>2、由于目前维表关联查询的性能非常低，20核，只能承担QPS为2k左右。现在勉强用在聚合后关联维度。但远远不能满足DWD层的关联性能要求。ODS到DWD层的数据量，预计总量得几百万QPS。</p>
<p>下面从两个方面进行优化：<strong>配置同步、维表关联。</strong></p>
<h3 id="d5eb4bc0-caaf-d227-e81c-2d093287402e" class="toc-enable">配置同步</h3>
<p><strong>原始方案</strong></p>
<p>每天定时更新全量数据至Redis。我们使用Spark US任务每天凌晨定时从Mysql/mongoDB同步一次全量配置数据至Redis。基于查询的方式获取全量数据。</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(24)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p>由于，我们系统每天会新增或变更不少如推广计划、推广组等名称信息，而每天定时全量同步会出现一个问题：</p>
<p>当天新增或修改的名称没有及时同步过来，于是，当天实时任务拿到实时上报的数据后，就不能根据其ID转换出正确的Name信息。需要等到第二天配置同步了才行。</p>
<p><strong>优化前配置同步效率</strong></p>
<p>原方案使用<strong>天级别</strong>定时同步配置。</p>
<p><strong>优化方案</strong></p>
<p>为了解决配置同步不及时的问题，优化方案采用Flink CDC实时同步更新配置，基于监听数据库的BinLog日志的方式，实时捕获增量日志，不再使用查询数据库的形式，也减轻了对DB的压力。</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(25)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p>采用Flink-CDC实时增量同步配置，可以实现从以前离线的天级别更新配置缩短至毫秒级更新增量配置，大大提高了配置的更新效率和实时数据转换的准确度。</p>
<p><strong>优化后配置同步效率</strong></p>
<p>配置同步至Redis，更新频率从<span style="color:#ff0000;"><strong>天级别</strong></span>降到了<span style="color:#ff0000;"><strong>毫秒级</strong></span>。</p>
<h3 id="c1124b5c-f90b-3479-e8ee-0386ca99b0c5" class="toc-enable">维表关联</h3>
<p>维表关联 作为ODS层到DWD层重要一环，数据量最大的一层，其性能要求也是非常高，不然Flink任务很容易反压，数据计算延迟严重。针对维表关联效率低的问题主要从两个方面进行优化：<strong>Redis Value结构优化、关联方式优化</strong>。</p>
<p>这里使用的Redis为SSD Redis主要将数据存储在磁盘上，配置为16核64G。</p>
<p><strong>A）Redis Value结构优化</strong></p>
<p><b>优化前方案</b></p>
<p>Redis Value存储为Json格式，将原mysql/mongoDB中的结构化配置数据生成一个Json Value。<br></p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(26)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p>写入：set realtime_creative_id_1&nbsp; {JSON_STRING}</p>
<p><strong>优化前查询耗时</strong></p>
<p>单条获取Redis维度、Json转换成java对象、解析Json维度字段值，共计耗时<strong>100ms</strong>左右，查询步骤：</p>
<p>1、从Redis中 get&nbsp;realtime_media_app_id_1</p>
<p>2、json string转换成java对象</p>
<p>3、从java对象中获取具体维度值</p>
<p><strong>优化后方案</strong></p>
<p>Redis Value存储为Hash结构，将原msyql/mongoDB中的结构化配置数据，按照主键、其他维度的形式生成HashMap结构。查询某个维度值的时间复杂度为O(1)</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(27)" alt="" style="position: relative; z-index: 2;"></p>
<p>指定维度写入：hset&nbsp; creative_id:1&nbsp; creative_name xxxx</p>
<p>批量维度写入：hmset&nbsp;creative_id:1&nbsp; creative_name&nbsp;xxxxx creative_title xxxx material_type 2</p>
<p><strong>优化后查询耗时</strong></p>
<p>每批获取Redis维度值，耗时<span style="color:#ff0000;"><strong>4ms</strong></span>左右，查询步骤：</p>
<p>1、从Redis中 hget&nbsp; creative_id:1 creative_name</p>
<p><br></p>
<p><strong>B）关联方式优化</strong></p>
<p><strong>优化前方案</strong></p>
<p>采用异步IO的方式查询Redis，每条数据都需要查询Redis。</p>
<p>异步关联、解析Redis Value 的Json数据<br></p>
<p><strong>优化前性能</strong></p>
<p>1、20核，QPS 2000，Flink Queue随即反压（因为每条数据从redis获取value后，在解析json的时候花了100ms左右的耗时，造成了严重阻塞）。<br></p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(28)" width="524" height="217" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p><br></p>
<p>2、Redis 的查询qps跟数据量成正比，redis proxy CPU跟查询qps成正比。</p>
<p>如单独用上述方案只查询Redis，不解析json的时候，进行测试查询，qps为2w左右的时候：</p>
<p></p>
<p>Redis CPU负载：cpu负载已经到了50%+</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(29)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""></p>
<p>而要想将此方案用在DWD层进行维表关联，几百万QPS的查询压力，Redis早已扛不住。故不适合。</p>
<p><strong>优化后方案</strong></p>
<p>采用<strong>批量pipline</strong>的方式查询Redis，每批量1000条数据，每条数据10个维度，共1w条命令一批。</p>
<p>批量关联、取Redis Hash Value数据，其详细架构如下图所示：<br></p>
<p><strong>优化后计算性能</strong></p>
<p>压测至Task CPU 90+%：20核，QPS 60W，Flink Queue正常。OutQueue Max为10%，InQueue Max为0%<br>&nbsp;。</p>
<p>Redis CPU查询QPS：使用不同的数据量进行压测，每批1000条数据，每条数据10个维度（即共1w条命令一批），redis 查询qps只有几十~几百。</p>
<p></p>
<p>Redis CPU：只有4%左右。</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(30)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt=""><strong>优化效果</strong></p>
<p>在对维表关联进行了配置同步优化、维表关联优化两大改进措施之后，可以看到优化后的效果是非常明显的。如下图所示：</p>
<div class="table-wrap"><strong><strong><strong><strong><strong><strong style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(31)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" alt="" class="amplify"></strong></strong></strong></strong></strong></strong><strong><strong><strong><strong><strong><br></strong></strong></strong></strong></strong></div>
<div class="table-wrap">维表更新效率从天级别缩短到了毫秒级别，关联方式也是从每条解析Json Value的形式 优化成了每批Hash Get的形式。于是，使得维表关联程序的性能大大提升，Flink 20核能承受60WQPS的数据压力，相比之前20核跑到2WQPS(未解析Json Value的情况下，解析Json Value只能扛住2K）时的 Redis CPU从50%降到了4%，维度关联耗时也从每条数据100ms降到了每批1000条数据仅用了4ms左右。

<h2 id="6e95a419-3293-5e02-d4f1-ed428faa7366" class="toc-enable">流流关联</h2>
<p>在使用Flink计算的过程中，除了维表关联（即事实表关联维表）之外，还有一个重要的关联，就是事实表关联事实表，即流流Join。在Flink里面有不同窗口的Join：滑动窗口Join、滚动窗口Join、会话窗口Join、间接连接Join（Interval Join）。在面对我们的广告业务场景，经常会出现需要将多个流进行样本字段拼接、链路关联统计等。如 请求流关联响应流、曝光流关联点击流。请求在响应前面发生，曝光在点击前面发生，故相对合适的Join方式是Interval Join。然而，在面临业务数据量的不断增长，Interval Join的性能远不能满足要求，于是采用了一种高性能的优化方式：Union+Timer 来实现流流关联。</p>
<p><strong>关于流流关联的详细方案设计和问题解决，详见作者另一篇KM文章总结：</strong><br></p>
<p><strong><a href="https://km.woa.com/group/15716/articles/show/483752" target="_blank" rel="noreferrer">百万QPS-基于Flink的Union+Timer优化广告多流Join</a></strong></p>
<h1 id="75f16f6a-7ea4-443b-6c77-b5194b5ebcbd" class="toc-enable">数仓效果</h1>
<p>实时数仓建设后的一个效果如下图所示：</p>
<p style=""><img src="./【万字长文】游戏广告-基于Flink建设高性能实时数仓 - IEG增长中台体系 - KM平台_files/cos-file-url(32)" style="display: block; margin-left: auto; margin-right: auto; position: relative; z-index: 2;" width="431" height="105" alt=""></p>
<p>数据总体延时在1min，因为窗口为1min，中间其他链路环节耗时几十ms，极大的提高了数据计算性能。BI看板99%的查询能在3s内返回，极大的提高了产品运营同学报表分析体验。</p>
<h1 id="28094d35-6388-5629-0071-b7f79cea4834" class="toc-enable">总结与展望</h1>
<p>本文主要介绍了在游戏广告业务中进行实时数仓建设的实践，针对业务的痛点问题进行分析，并将实时数仓的设计过程进行详细描述。从数据层面来看，实时数仓分为ODS源数据层、DIM维表层、DWD明细数据层、DWS轻度聚合层、ADS数据应用层。从技术层面上来看，实时数仓主要包含两大模块：实时计算、实时存储。并详细的介绍了每个技术模块的技术细节和优化方案。同时也针对最棘手的技术难点：精确去重、维表关联、流流关联、业务监控告警等问题进行深入的分析探讨和优化，并给出了优化方案和效果，节省了几十倍的计算资源。</p>
<p>在未来：将持续探讨流批一体的架构与实现，将离线和实时统一成一套代码、计算一体及存储一体、复用资源，同时也方便了代码维护与集群运维。</p>				</div>
