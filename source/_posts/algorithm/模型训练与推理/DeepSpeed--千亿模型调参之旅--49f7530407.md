---
title: "DeepSpeed--千亿模型调参之旅"
date: 2022-03-31 10:15:44
categories:
  - 算法
  - 模型训练与推理
---

{% raw %}

<h2>一、DeepSpeed简介</h2>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4756f0e61c0e5874dbaa.png"/></p>
<p>DeepSpeed为推出的超大模型优化库，其利用ZeRO技术对显存进行优化，使得NVIDIA V100 32G GPU从容纳13亿参数提升到130亿参数，并且使千亿参数的GPT3训练成为现实。DeepSpeed具有以下四点创新：</p>
<ul><li><strong>使用 ZeRO-Offload，在单 GPU 上进行 10 倍的模型训练：</strong>DeepSpeed扩展到ZeRO-3，利用 CPU 和 GPU 内存来训练大型模型。使用一台 <strong>NVIDIA V100 GPU </strong>机器，用户可以在不耗尽内存的情况下运行<strong>多达 130 亿个参数模型</strong>，比现有方法大 10 倍，同时获得具有竞争力的吞吐量。</li>
<li><strong>具有 3D 并行性的万亿参数模型训练：</strong>DeepSpeed 支持三种并行方法的灵活组合——ZeRO 支持的数据并行、流水线并行和张量切片模型并行。3D 并行可适应工作负载需求的变化，为具有超过<strong>一万亿</strong>个参数的<strong>超大型模型</strong>提供支持，同时实现近乎完美的内存扩展和吞吐量扩展效率。此外，其改进的通信效率允许用户在网络带宽有限的常规集群上将数十亿参数模型的训练速度提高 2~7 倍。</li>
<li><strong>通过 DeepSpeed 稀疏注意力机制，提供 10 倍长序列和 6 倍快的执行速度：</strong>DeepSpeed 提供了稀疏注意力内核，这是一种支持长序列模型输入的工具性技术，无论是文本、图像还是声音。与经典的密集 Transformer 相比，它提供了一个<strong>数量级更长的输入序列</strong>，并以相当的正确率获得高达 6 倍的执行速度。它的执行速度也比最先进的稀疏实现快 1.5~3 倍。此外，DeepSpeed的稀疏内核支持高效执行灵活的稀疏格式，并赋予用户对其定制的稀疏结构进行创新的能力。</li>
<li><strong>1 位 Adam，通信量最多可减少 5 倍：</strong>Adam 是训练许多大规模深度学习模型的有效（且可能是利用最充分的）优化器。然而，Adam 通常与通信高效的优化算法不兼容。因此，在跨分布式设备扩展时，通信成本可能会成为瓶颈。DeepSpeed引入了一种新的算法，具有高效实现的 1 位 Adam，在达到与 Adam 相似的收敛效率的同时，<strong>通信量降低了 5 倍</strong>。在通信受限的场景中，分布式训练的速度最高可提高 3.5 倍，从而可以扩展到不同类型的 GPU 集群和网络。</li>
</ul><h2>二、从3亿到千亿的模型训练</h2>
<h3>2.1、DeepSpeed vs PyTorch</h3>
<p>DeepSpeed优化库目前主要与PyTorch框架结合使用，而PyTorch框架本身有<a href="https://pytorch.org/docs/stable/nn.html#torch.nn.parallel.DistributedDataParallel">DistributedDataParallel</a> (DDP) 来支持多机多卡任务，为了体现DeepSpeed的易用性，此对比实验在一个可用的PyTorch任务基础上，几乎无代码层面的修改，直接新增DeepSpeed配置参数（使用ZeRO2+fp16优化）实现DeepSpeed任务。此对比实验在单机8卡到十六机128卡实现3亿及10亿参数量的bert模型训练。<strong>3亿bert实验结果如下</strong>：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/833261fbc66b133eb642.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e63b02ae36c1d625da0c.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/a9b70bb91c0db0f98f37.png"/></p>
<p>由上图可以看出：</p>
<ul><li> 在单卡能放下的<strong>小模型场景</strong>，DeepSpeed相比PyTorch的<strong>加速效果不明显</strong></li>
<li><strong>fp16</strong>能够<strong>提高</strong>单卡装载的<strong>batch_size</strong></li>
<li>DeepSpeed 使用<strong>ZeRO显存优化</strong>，相比PyTorch能放下<strong>更大的batch_size</strong></li>
<li><strong>小模型场景</strong>，从单机扩展<strong>多机加速明显</strong>，PyTorch<strong>十六机加速比达到13.6</strong></li>
</ul><p><strong>10亿bert实验结果如下：</strong></p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm/14084f2f26c41d3ee81d.png"/></strong></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4a65a1e82f278d6998aa.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/55a758a7d3151f523af2.png"/></p>
<p>由上图可以看出：</p>
<ul><li> 当接近PyTorch单卡装载参数上限（13亿）时，DeepSpeed相比PyTorch的<strong>加速效果十分明显</strong></li>
<li>DeepSpeed从单机拓展到多机时，<strong>接近线性加速</strong>（十六机提供了13倍的加速）</li>
<li>当接近PyTorch单卡装载参数上限（13亿）时，DeepSpeed 使用<strong>ZeRO显存优化的效果更加明显，</strong>单机batch_size装载量达到PyTorch的<strong>6倍</strong></li>
</ul><h3>2.2、26亿 Bert vs 110亿 Bert</h3>
<p>继续增加bert的hidden_size和head_size，将模型的参数量提升到26亿，此时全用GPU还是能够装载下的，当参数量提升到110亿时，发现纯用GPU放不下，所以是开启ZeRO优化offload到CPU来实现的，下面直接看下实验结果吧。</p>
<p><strong>26亿bert实验结果如下：</strong></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/fc766d710c702b16f223.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/e54807b6b9d7961cfdd6.png"/></p>
<p>由上图可以看出：</p>
<ul><li>相比10亿参数模型，<strong>26亿参数模型的多机加速比有所降低</strong>，10亿时，八机加速比达到<strong>6.85</strong>，而26亿时，八机加速比为<strong>5.1</strong></li>
<li>随着机器数量的增长，加速效果越好，例如四机相比双机的加速比是<strong>1.73</strong>，而八机相比四机的加速比是<strong>1.96；随机器数量增长</strong>，机器间<strong>通信量增长对训练时长的影响越来越小</strong></li>
</ul><p><strong>110亿bert实验结果如下：</strong></p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm/b6e695e630209c21fbb6.png"/></strong></p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm/79bcdae58853e3744d3e.png"/></strong></p>
<p><strong>由上图可以看出：</strong></p>
<ul><li><strong>使用<strong>CPU offload</strong>能运行<strong>更大的模型</strong>，但是<strong>运行速度慢</strong>很多。例如不使用CPU offload的10亿模型，十六机处理速度达到<strong>815245.53 tokens/s，</strong></strong>而使用CPU offload的110亿模型，十六机处理速度为<strong>1132.56</strong> <strong>tokens/s，</strong>这里除了模型变大、CPU offload使得训练变慢以外，另一个重要原因是<strong>batch_size变小了，</strong>10亿时batch_zise为72,110亿时batch_zise为1，感兴趣的同学可以调整batch_size和模型大小，比较一下offload到底慢多少</li>
<li>对于<strong>CPU offload场景，扩展机器数带来的计算效果特别好，超出线性加速</strong></li>
</ul><h3>2.3、100亿 GPT2 vs 1000亿 GPT2</h3>
<p>在进行GPT2 模型对比时，主要进行了100亿参数模型和1000亿模型的实验，其中100亿使用数据并行 + ZeRO2实现，1000亿使用模型并行 + ZeRO3 + <strong>CPU offload实现，下面看一下实验数据。</strong></p>
<table><tbody><tr><td>参数</td>
<td colspan="10" rowspan="1">layers=50<br/>hidden size=4096<br/>attention head=32<br/>sequence_length=1024<br/>vocabulary_size= 50258→50304<br/>max-position-embeddings=1024<br/><strong>参数量：10279239680</strong><br/>TFlop/GPU = approx_parameters_in_billions * batch_size * seq_length * 2.0 * 4.0 / 1000</td>
</tr><tr><td colspan="1" rowspan="2">实验结果</td>
<td>batch_size</td>
<td>global_batch_size</td>
<td>model_parallel_size</td>
<td>forward(ms)</td>
<td>backward(ms)</td>
<td>optimizer_allgather(ms)</td>
<td>iteration(ms)</td>
<td>TFlop/GPU</td>
<td>TFlops/GPU</td>
<td>SamplesPerSec</td>
</tr><tr><td>6</td>
<td>64*6</td>
<td>1</td>
<td>2436.62</td>
<td>7622.04</td>
<td>2583.01</td>
<td>12722.4</td>
<td>505.2</td>
<td>505.2/12.7=<strong>39.78</strong></td>
<td>32.33429813</td>
</tr></tbody></table><h2><strong>由上表可以看出：</strong></h2>
<ul><li><strong>100亿参数的GPT2每块V100的计算效率很高，达到<strong>39.78 TFlops/GPU</strong></strong></li>
<li><strong>从成本上考虑，<strong>100亿参数的GPT2</strong>作为预训练模型，是<strong>比较好在业务场景落地的一个大模型</strong></strong></li>
</ul><p><strong><strong>千亿GPT2实验结果如下：</strong></strong></p>
<table><tbody><tr><td>参数</td>
<td colspan="10">layers=480<br/> hidden size=4096<br/> attention head=32<br/> sequence_length=1024<br/> vocabulary_size= 50258→51200<br/><strong>参数量：96988233728</strong><br/> TFlop/GPU = approx_parameters_in_billions * batch_size * seq_length * 2.0 * 4.0 / 1000</td>
</tr><tr><td rowspan="3">实验结果</td>
<td>batch_size</td>
<td>global_batch_size</td>
<td>model_parallel_size</td>
<td>forward(ms)</td>
<td>backward(ms)</td>
<td>optimizer_allgather(ms)</td>
<td>iteration(ms)</td>
<td>TFlop/GPU</td>
<td>TFlops/GPU</td>
<td>offload</td>
</tr><tr><td>6</td>
<td>64*6</td>
<td>8</td>
<td>973334.76</td>
<td>2444435.74</td>
<td>507.81</td>
<td>3418327.2</td>
<td>595.9</td>
<td>595.9/3418.3=0.17</td>
<td>yes</td>
</tr><tr><td>1</td>
<td>64</td>
<td>8</td>
<td>516441.22</td>
<td>1131882.99</td>
<td>204.85</td>
<td>1648574.8</td>
<td>99.3</td>
<td>99.3/1648.6=0.06</td>
<td>no</td>
</tr></tbody></table><h2><strong>由上表可以看出：</strong></h2>
<ul><li><strong>1000亿参数的GPT2每块V100的计算效率很低，在不启用CPU offload时，勉强能装下batch_size为1的数据，计算速度只有<strong>0.06 TFlops/GPU，</strong></strong>此数据有很大的优化空间，Venus还在优化中</li>
<li>在启用<strong>CPU offload后，虽然计算速度会比纯GPU的慢，但是可以通过提高batch_size来提高整体训练速度，计算速度反而提升到<strong>0.17 TFlops/GPU</strong></strong></li>
</ul><h2>三、DeepSpeed调参途中问题收集</h2>
<p>3.1、机器节点是否处在<strong>同一modules</strong>？</p>
<p>答：机器节点处于不同modules时，多机间通信时间会长很多，<strong>已从平台层面增加调度到同一modules的策略。</strong>可在运行实例处查看机器ip，在pms.wsd.com查看机器的机房位置，处于同一位置的即在同一modules。</p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm/6d91100a9b7d11e6f46b.png"/></strong></p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm/f44349e242ceea8f7390.png"/></strong></p>
<p></p>
<p>3.2、多机时是否<strong>启用RDMA</strong>？</p>
<p>答：<strong>启用RDMA对多机间通信特别有效。</strong>在26亿参数bert实验中，启用RDMA比为未启动的<strong>提速1倍多</strong>。通过设置<strong>export NCCL_DEBUG=INFO</strong>，查看日志中是否出现<strong>[receive] via NET/IB/0 和 [send] via NET/IB/0</strong>，出现则说明启用RDMA成功，否则失败。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/4c92ccf46ce2110f608c.png"/></p>
<p></p>
<p>3.3、多机时是否<strong>启用GDRDMA</strong>？</p>
<p>答：能否启用<strong>GDRDMA和NCCL版本有关</strong>，经测试，使用PyTorch1.7（自带NCCL2.7.8）时，启动GDRDMA失败，和Nvidia的人沟通后确定是NCCL高版本的bug，暂时还未修复；使用PyTorch1.6（自带NCCL2.4.8）时，能够启用GDRDMA。经测试，“NCCL2.4.8 + 启用GDRDMA ” 比 “NCCL2.7.8 + 未启用GDRDMA”<strong>提升4%。通过设置export NCCL_DEBUG=INFO，查看日志中是否出现[receive] via NET/IB/0/GDRDMA 和 [send] via NET/IB/0/GDRDMA，出现则说明启用GDRDMA成功，否则失败。</strong></p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm/3e85181ea39720388497.png"/></strong></p>
<p><strong></strong></p>
<p>3.4、PyTorch版本如何选择？</p>
<p>答：经业务反馈，DeepSpeed在PyTorch1.8和PyTorch1.9上面上面会出现各种奇奇怪怪的问题，而PyTorch1.6能够启动的GDRDMA收益也不是很大，属于正常波动范围，<strong>建议使用PyTorch1.7</strong>，此文中对比实验都是在PyTorch1.7上进行。</p>
<p></p>
<p>3.5、机器节点数如何选择？</p>
<p>答：建议使用<strong>2的n次幂个机器节点</strong>，例如2、4、8、16。在实验中，发现三机的效果比双机差多了，多机间通信时间陡增，而四机时又正常了，和Nvidia的人沟通，猜测是NCCL的采用的二叉树allreduce算法，对于非2的n次幂个机器节点情况容易解析错通信拓扑图。</p>
<p></p>
<p>3.6、是否采用NVLink？</p>
<p>答：所有GPU机器都使用了NVLink，用户无需配置。</p>
<p></p>
<p>3.7、关于机器间通信带宽？</p>
<p>答：100Gbps</p>
<p></p>
<p>3.8、如何开启fp 16？</p>
<p>答：推荐使用apex工具包，安装时有坑，直接pip install apex安装遇到“TypeError: Class advice impossible in Python3”报错，源码安装后跑GPT2又遇到“ModuleNotFoundError: No module named ‘fused_layer_norm_cuda’”，推荐安装方式如下：</p>
<div>
<pre># 升级GCC
yum install centos-release-scl -y \
  &amp;&amp; yum install devtoolset-7 -y  --skip-broken \
  &amp;&amp; scl enable devtoolset-7 bash \
  &amp;&amp; gcc --version  &amp;&amp; source /opt/rh/devtoolset-7/enable \
 
#源码安装apex
cd /data \
  &amp;&amp; wget [内部链接已移除] \
  &amp;&amp; unzip apex-master.zip \
  &amp;&amp; cd apex-master  \
  &amp;&amp; cd /data/apex-master \
  &amp;&amp; pip install -v --disable-pip-version-check --no-cache-dir --global-option="--cpp_ext" --global-option="--cuda_ext" ./</pre>
</div>
<p> </p>
<p>3.9、多机场景optimizer_allgather耗时太长如何优化？</p>
<p>答：1）<strong>如何确定optimizer_allgather耗时太长</strong>：经过大量的实验，总结出多机optimizer_allgather耗时基本比forward大一点点，是backward的1/4～1/2。如果出现optimizer_allgather接近backward或者比backward耗时还大，基本可以判定为optimizer_allgather耗时过长，需要优化。而单机optimizer_allgather是走机器内多GPU通信，耗时很少，通常比forward要小。</p>
<p>       2）上文提到的机器节点是否处在<strong>同一modules、多机时是否启用RDMA、是否使用2的n次幂个机器节点数</strong>都会对optimizer_allgather有很大影响，请依次确认<strong>。</strong></p>
<p><strong>     </strong>  3） 调整DeepSpeed<strong> </strong>ZeRO的<strong>allgather_bucket_size参数 ：</strong>该参数表示一次收集的通信元素数，需要根据具体通信量、机器带宽、模型大小、batch_size调整。<strong>不是越大越好，也不是越小越好</strong>。设置太大时，一次收集的元素多，通信次数变少，通信总时间变少，但是<strong>allgather操作会占用显存</strong>，如果模型太大容易oom，而且容易压缩batch_size的优化空间，造成batch_size太小，整体速度上不去。设置太小时，收集通信信息的轮数太多，通信时间会用的更多。</p>
<p></p>
<p>3.10、batch_size该如何优化？</p>
<p>答：结合<strong>显存利用率和allgather_bucket_size</strong>进行调参，建议先在单机上根据显存利用率调整batch_size，尽量占满显存利用率，根据optimizer_allgather耗时调整allgather_bucket_size参数，如果allgather_bucket_size需调高但会oom，可适当减小batch_size。单机调好后，扩展到<strong>多机</strong>时一般可以<strong>调大一点batch_size</strong>，例如26亿的bert模型，在单机时能放下batch_size为24，到双机时能放下batch_size为28。</p>
<p></p>
<p>3.11、什么情况下该使用offload？</p>
<p>答：1）offload 分为CPU offload和NVMe offload，既将需要装载在显存中的信息装载到内存或者磁盘中，本文实验<strong>使用的是CPU offload</strong>，经测试Venus GPU机器<strong>单机内存能到360G</strong>，千亿模型GPT2 使用CPU offload，内存大概占用220G。NVMe offload没测试过，但理论速度是会比CPU offload慢不少的。</p>
<p>       2）当模型太大，在单机内做完模型并行还放不下时，可以使用offload技术，放下更大的模型。</p>
<p>       3）当使用offload技术，能够提升batch_size，使得整体训练速度更快的时候。</p>
<p></p>
<p>3.12、参数gradient_accumulation_steps有什么用？</p>
<p>答：gradient_accumulation_steps释义：在累积多少step的梯度后再传递。此参数可以减少梯度通信的次数，能够降低显存的使用。</p>
<h2>四、千亿模型Demo使用</h2>
<p>百亿GPT2和千亿GPT2的运行Demo都已经放到Venus平台首页了，感兴趣的同学可以直接复制Demo进行使用。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/bf26dc3b82cac5be1dd2.png"/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm/0294a03d792fcd978213.png"/></p>
<p>DeepSpeed Demo工作流：[内部或本地链接已移除]</p>
<p>DeepSpeed 使用文档：[内部或本地链接已移除]</p>
<p>DeepSpeed 组件Demo Git：[内部或本地链接已移除]</p>
<h2>五、致谢</h2>
<p>感谢lshzhang(张路生)、andreasyang(杨震)、orchardwen(温泉)、pengmeng(孟朋) 等同学提供的demo支持，感谢orlandochen(陈凯钿)、ryuan(袁成瑞)等同学提供的技术支持。</p>
<p></p> 
{% endraw %}
