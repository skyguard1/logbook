---
title: "重排混排LTR算法"
date: 2022-04-01 14:34:45
categories:
  - 算法
  - 推荐与排序
---

{% raw %}

<div>
<h3>FPSA + PRM算法</h3>
<br/><p>离线训练阶段</p>
<p>1个user点击历史形成一个list，对于 ，优化的是</p>
<p>1user vs 1item ctr pointwise算法</p>
<p>1user vs 1list ndcg listwise算法</p>
<p>目前实验方案，</p>
<p>一个list以分隔符连接形式，把一个list的样本塞到一行，大部分业务实验的是等长list</p>
<p>插件解析后的格式：</p>
<p>query1 pointwise样本1</p>
<p>query1 pointwise样本2</p>
<p>query1 pointwise样本3</p>
<p>query1 pointwise样本4</p>
<p>query1 pointwise样本5 5为list_size</p>
<p>query2 pointwise样本1</p>
<p>对于输入: [batch_size * list_size, embedding_size]</p>
<p>在网络中: [batch_size, list_size, embedding_size]</p>
<p>对于简单dnn: [batch_size, list_size, 1] #输出维度</p>
<p>将 list_size*1 算一个list的ndcg，计算lambda loss</p>
<p><br/></p>
<p>线上infer阶段：</p>
<p>混排阶段数据量不同业务不同情况，大部分是</p>
<p>1user vs 100item ctr</p>
<p>而如果上述list_size &lt;= 5, 那就有C_100 ^5=75287520种组合, 那哪种组合是更好的呢？</p>
<p>DPWN算法把infer阶段分成两个阶段： PMatch阶段 和Prank阶段</p>
<p>Pmatch阶段用了FPSA算法，贪心的学习PNEXT</p>
<p>Prank阶段用了PRM算法或者DPWN里的attention-RNN算法，目前大部分业务用的还是PRM, 对应离线训练阶段也只需要PRM。</p>
<p><br/></p>
<h3>Pmatch阶段改进</h3>
<ol><li>
<h5>暴力搜索 基于多目标搜参融合的方式</h5>
</li>
<li>
<h5>FPSA算法</h5>
</li>
</ol><p> <img alt="" loading="lazy" src="/logbook/images/algorithm/c6aeb7594526ae06b3cf.png"/></p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm/d7e68c0eefb7e73935de.png"/></p>
<p><br/></p>
<h3>Prank阶段的改进</h3>
<p>DQN算法用于排序, 解决小视频不同刷之间时间序列的最优化问题。</p>
<p>从PRM -&gt; DPWN</p>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm/c4405bcc4a5265658c92.png"/></p>
<h5>Personalized Re-ranking for Recommendation 阿里 2019</h5>
<p> <img alt="" loading="lazy" src="/logbook/images/algorithm/c8fbb0069f14b6a0ff09.png"/></p>
<h5>Revisit Recommender System in the Permutation Prospective 阿里淘宝 2021</h5>
</div> 
{% endraw %}
