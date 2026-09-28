---
title: "VENUS算法平台——TDW数据导入VENUS"
date: 2022-03-31 10:09:28
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<h2>一、预先准备</h2>
<p>1、TDW应用组、TDW库表路径及权限申请：<strong>[内部或本地链接已移除]</strong></p>
<p>2、VENUS应用组申请加入或创建：<strong>请联系Venus_Helper(维纳斯助手)</strong></p>
<h2>二、TDW接口机权限申请</h2>
<p>TDW接口机权限查看及申请地址：[内部或本地链接已移除]</p>
<p>1、查看TDW应用组是否具有“同乐--hdfs_ss-mig--hdfs接口机集群”权限</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4c58285cae3f5033e1e9.png"/></p>
<p>2、如没有“同乐--hdfs_ss-mig--hdfs接口机集群”权限，申请加入接口机集群权限</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/cd95b6a4e89d0371de4c.png"/></p>
<p>3、查看TDW应用组是否具有“同乐--tdw_tl tdw计算集群”权限</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/99a34a5b14da3bd9f997.png"/></p>
<p>4、如没有“同乐--tdw_tl tdw计算集群”权限，申请加入计算集群权限</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/fc95a9d66e0c6af22fe5.png"/></p>
<p></p>
<h2>三、VENUS平台配置TDW资源</h2>
<p>操作地址：venus.wsd.com</p>
<p>1、选择需要配置TDW资源的应用组</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/07a9820892aaf9528971.png"/></p>
<p>2、配置TDW资源（新建TDW资源）</p>
<p>洛子BG ID、产品ID查询：[内部或本地链接已移除]</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/f0c63bc4bd2872d30a3f.png"/></p>
<p></p>
<h2>四、数据导出作业配置</h2>
<p>1、使用"TDW导出"组件，将TDW数据导出到中间接口集群</p>
<p>目标集群路径创建方法：联系 TDBank_TDW_TRC_Helper，将tdw应用组名和路径发给他进行创建。</p>
<p>注意：目标集群路径需要提前创建好，否则可能没有权限创建文件夹</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e72172bbb788ca8bdbee.png"/></p>
<p>2、使用"集群间同步"组件，将中间接口集群同步到venus集群</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/ccddf78aec1ed971fb11.png"/></p>
<p>3、调试好作业后，设置定时器任务，即可完成TDW数据定时导出</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/bc0b1d81d83b12767ce3.png"/></p>
<p><strong>定时器说明</strong>：上图为小时级周期任务，每小时的第10分钟触发任务，生成的参数为上一小时的周期。例如：2019-03-21 17:10将触发作业，生成周期为2019032116，定时器后面连接的作业使用%YYYYMMDDHH%即可捕获2019032116周期参数。</p>
<h2>五、TDW数据导出速度</h2>
<p>TDW数据导出速度和数据大小、数据文件数、目标集群、同步时集群状态都有关系，下面列出三个真实作业的同步情况，以作参考。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/640b9bc025fd5926e281.png"/></p> 
{% endraw %}
