---
title: "linux内核参数优化"
date: 2022-06-17 08:33:03
categories:
  - linux
---

<div class="Section1" style="layout-grid: 15.6pt;">
<h1 style="line-height: 150%;"><span style="font-family: 宋体;">一、需要背景</span></h1>
<p style="line-height: 150%;"><span lang="EN-US">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </span><span style="font-family: 宋体;">一台硬件资源固定的服务器，我们可以跑任何我们想跑的应用程序，只是应用场合不同，服务器的硬件性能发挥的等级也不同。内核参数直接控制着硬件性能，合适的参数可以最大程度地压榨服务器性能，具体参数值需要根据应用程序需要的性能来定，如，</span><span lang="EN-US">nginx</span><span style="font-family: 宋体;">需要大并发处理能力、数据库需要</span><span lang="EN-US">io</span><span style="font-family: 宋体;">性能较好以及快速的数据交换处理能力、转码程序需要</span><span lang="EN-US">cpu</span><span style="font-family: 宋体;">的处理能力较强……，适当的内核参数可以把固定硬件的性能发挥到极致。</span></p>
<h1 style="line-height: 150%;"><span style="font-family: 宋体;">二、查看内核参数</span></h1>
<p style="text-indent: 21.0pt; line-height: 150%;"><span lang="EN-US">Linux</span><span style="font-family: 宋体;">内核采用的是模块化技术，这样的设计使得系统内核可以保持最小化，同时确保了内核的可扩展性与可维护性，模块化设计允许我们在需要时才将模块加载至内核，实现动态内核调整。系统所加载的内核模块不同，系统所打印的内核变量也不一样。</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">可以用</span><span lang="EN-US">sysctlvariable</span><span style="font-family: 宋体;">查具体内核参数</span></p>
<p style="line-height: 150%;"><span lang="EN-US">sysctl –a </span><span style="font-family: 宋体;">查看所有参数</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="490" height="177" id="图片 3" src="/logbook/images/linux/linux内核参数优化/b77f02ab1ae6.png" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">打印出来的内核变量及参数，在</span><span lang="EN-US">/proc</span><span style="font-family: 宋体;">目录下有对应的虚拟文件保存参数，应用程序在运行过程从这些文件拉取对应参数，一个内核变量对应一个虚拟文件，如</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">文件</span><span lang="EN-US"> /proc/sys/vm/swappiness</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">对应变量</span><span lang="EN-US">vm.swappiness</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="460" height="66" src="/logbook/images/linux/linux内核参数优化/689db5824340.png" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">上面拉取变量值的的方法是等价的</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">内核相关变量命名规则</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">一般是把参数文件的完整路径，去掉</span><span lang="EN-US">/proc/sys</span><span style="font-family: 宋体;">，把“</span><span lang="EN-US">/</span><span style="font-family: 宋体;">”变成“</span><span lang="EN-US">.</span><span style="font-family: 宋体;">”，作为变量名</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">如：</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">参数文件</span><span lang="EN-US">/proc/sys/net/ipv4/tcp_fin_timeout</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">对应变量名</span><span lang="EN-US"> net.ipv4.tcp_fin_timeout</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">控制内核行为的内核参数存储在</span><span lang="EN-US">/proc</span><span style="font-family: 宋体;">中</span><span lang="EN-US">(</span><span style="font-family: 宋体;">特别是</span><span lang="EN-US">/proc/sys</span><span style="font-family: 宋体;">中</span><span lang="EN-US">)</span></p>
<p style="line-height: 150%;"><span lang="EN-US">/proc</span><span style="font-family: 宋体;">目录树有对内核参数作分类，类似的内核行为被归于同一目录下</span></p>
<table border="0" cellspacing="0" cellpadding="0" width="544" style="width: 408.0pt; border-collapse: collapse;">
<tbody>
<tr style="height: 24.0pt;">
<td width="185" style="width: 139.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><b><span style="font-family: 宋体;">目录</span></b></p>
</td>
<td width="359" style="width: 269.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><b><span style="font-family: 宋体;">说明</span></b></p>
</td>
</tr>
<tr style="height: 24.0pt;">
<td width="185" style="width: 139.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span lang="EN-US">/proc/sys/abi</span></p>
</td>
<td width="359" style="width: 269.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span style="font-family: 宋体;">包含文件与应用程序二进制信息</span></p>
</td>
</tr>
<tr style="height: 24.0pt;">
<td width="185" style="width: 139.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span lang="EN-US">/proc/sys/debug</span></p>
</td>
<td width="359" style="width: 269.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span style="font-family: 宋体;">此目录为可能空</span></p>
</td>
</tr>
<tr style="height: 24.0pt;">
<td width="185" style="width: 139.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span lang="EN-US">/proc/sys/dev</span></p>
</td>
<td width="359" style="width: 269.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span style="font-family: 宋体;">包含特定设备信息</span></p>
</td>
</tr>
<tr style="height: 24.0pt;">
<td width="185" style="width: 139.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span lang="EN-US">/proc/sys/fs</span></p>
</td>
<td width="359" style="width: 269.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span style="font-family: 宋体;">文件句柄、</span><span lang="EN-US">inode</span><span style="font-family: 宋体;">、</span><span lang="EN-US">dentry</span><span style="font-family: 宋体;">和配额调优</span></p>
</td>
</tr>
<tr style="height: 24.0pt;">
<td width="185" style="width: 139.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span lang="EN-US">/proc/sys/kernel</span></p>
</td>
<td width="359" style="width: 269.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span style="font-family: 宋体;">系统核心参数的窗口</span></p>
</td>
</tr>
<tr style="height: 24.0pt;">
<td width="185" style="width: 139.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span lang="EN-US">/proc/sys/net</span></p>
</td>
<td width="359" style="width: 269.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span style="font-family: 宋体;">网络部分内核参数调整</span></p>
</td>
</tr>
<tr style="height: 24.0pt;">
<td width="185" style="width: 139.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span lang="EN-US">/proc/sys/vm</span></p>
</td>
<td width="359" style="width: 269.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span style="font-family: 宋体;">内存、</span><span lang="EN-US">buffer</span><span style="font-family: 宋体;">和</span><span lang="EN-US">cache</span><span style="font-family: 宋体;">管理</span></p>
</td>
</tr>
<tr style="height: 24.0pt;">
<td width="185" style="width: 139.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span lang="EN-US">&nbsp;</span></p>
</td>
<td width="359" style="width: 269.0pt; padding: 3.6pt 7.2pt 3.6pt 7.2pt; height: 24.0pt;">
<p style="line-height: 150%;"><span lang="EN-US">&nbsp;</span></p>
</td>
</tr>
</tbody>
</table>
<h1 style="line-height: 150%;"><span style="font-family: 宋体;">三、内核参数调整方法</span></h1>
<p style="text-indent: 21.0pt; line-height: 150%;"><span style="font-family: 宋体;">内核参数修改的方法一般有三种：</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">方法一：修改</span><span lang="EN-US">/proc</span><span style="font-family: 宋体;">下内核参数文件内容，不能使用编辑器来修改内核参数文件，理由是由于内核随时可能更改这些文件中的任意一个，另外，这些内核参数文件都是虚拟文件，实际中不存在，因此不能使用编辑器进行编辑，而是使用</span><span lang="EN-US">echo</span><span style="font-family: 宋体;">命令，然后从命令行将输出重定向至</span><span lang="EN-US"> /proc</span><span style="font-family: 宋体;">下所选定的文件中。</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">如：将</span><span lang="EN-US">timeout_timewait</span><span style="font-family: 宋体;">参数设置为</span><span lang="EN-US">30</span><span style="font-family: 宋体;">秒：</span></p>
<p style="line-height: 150%;"><span lang="EN-US"># echo 30 &gt; /proc/sys/net/ipv4/tcp_fin_timeout</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">参数修改后立即生效，但是重启系统后，该参数又恢复成默认值。因此，想永久更改内核参数，需要修改</span><span lang="EN-US">/etc/sysctl.conf</span><span style="font-family: 宋体;">文件</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="554" height="51" src="/logbook/images/linux/linux内核参数优化/222e40278106.png" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">方法二：直接给内核变量赋值，临时改变系统内核参数值，内核参数是通过</span><span lang="EN-US">variable=value </span><span style="font-family: 宋体;">的形式来设定值，可以用</span><span lang="EN-US">sysctl -w </span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">临时调整参数，如：</span></p>
<p style="line-height: 150%;"><span lang="EN-US">#sysctl -w net.ipv4.tcp_fin_timeout = 30 </span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">这样修改是暂时的，系统重启后，内核参数将被重新加载</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="541" height="79" src="/logbook/images/linux/linux内核参数优化/e024c193a638.png" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">方法三：修改</span><span lang="EN-US">/etc/sysctl.conf</span><span style="font-family: 宋体;">文件。检查</span><span lang="EN-US">sysctl.conf</span><span style="font-family: 宋体;">文件，如果已经包含需要修改的参数，则修改该参数的值，如果没有</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">需要修改的参数，在</span><span lang="EN-US">sysctl.conf</span><span style="font-family: 宋体;">文件中添加参数。如：</span></p>
<p style="line-height: 150%;"><span lang="EN-US">&nbsp;&nbsp; net.ipv4.tcp_fin_timeout=30</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">保存退出后，可以重启机器使参数生效，如果想使参数马上生效，也可以执行如下命令：</span></p>
<p style="line-height: 150%;"><span lang="EN-US">&nbsp;&nbsp; # sysctl&nbsp; -p</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="470" height="240" src="/logbook/images/linux/linux内核参数优化/d6fcec53151d.png" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span lang="EN-US">/etc/sysctl.conf</span><span style="font-family: 宋体;">有可能是空的，即当前系统内核参数都是默认参数，把所需要的参数以</span><span lang="EN-US">variable=value </span><span style="font-family: 宋体;">的形式写进配置文件，重新加载即可。注意写内核变量的对应模块必须已加载，另外非内核变量不可出现在文件中。因为内核控制系统最核心的操作行为，在修改之前务必了解每个参数表示的含义，建议先临时修改测试效果，再写到配置文件中，以免引发故障。</span></p>
<h1 style="line-height: 150%;"><span style="font-family: 宋体;">四、具体参数优化</span></h1>
<p style="line-height: 150%;"><span lang="EN-US">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </span><span style="font-family: 宋体;">内核参数有很多，内核版本不同，加载的数量也不一样，大部分都是可以保持默认值，这里只拿了少数常用参数讲解。</span></p>
<h2 style="line-height: 150%;"><span lang="EN-US">1</span><span style="font-family: 宋体;">、网络相关参数优化</span></h2>
<p style="line-height: 150%;"><b><span lang="EN-US">tcp</span></b><b><span style="font-family: 宋体;">连接保持管理</span></b></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">（</span><span lang="EN-US">1</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.ipv4.tcp_keepalive_time = 7200 </span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">如果在该参数指定时间内某条连接处于空闲状态，则内核向远程主机发起探测</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">（</span><span lang="EN-US">2</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.ipv4.tcp_keepalive_intvl = 75&nbsp; </span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">内核向远程主机发送的保活探测的时间间隔</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">（</span><span lang="EN-US">3</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.ipv4.tcp_keepalive_probes = 9 </span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">内核发送保活探测的最大次数，如果探测次数大于这个数，则断定远程主机不可达，则关闭该连接并释放本地资源。一个连接</span><span lang="EN-US">7200s</span><span style="font-family: 宋体;">空闲后，内核会每隔</span><span lang="EN-US">75</span><span style="font-family: 宋体;">秒去重试，若连续</span><span lang="EN-US">9</span><span style="font-family: 宋体;">次则放弃。这样就导致一个连接经过</span><span lang="EN-US">2h11min</span><span style="font-family: 宋体;">的时间才能被丢弃，降低该值能够尽量减小失效连接所占用的资源，而被新的连接所使用。</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="553" height="41" id="图片 12" src="/logbook/images/linux/linux内核参数优化/af28bf8dbe3a.jpg" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">当</span><span lang="EN-US">keepalive</span><span style="font-family: 宋体;">打开的情况下</span><span lang="EN-US">,</span><span style="font-family: 宋体;">默认参数偏大，特别是</span><span lang="EN-US">web</span><span style="font-family: 宋体;">服务器容易被网络攻击，说如果</span><span lang="EN-US">2</span><span style="font-family: 宋体;">边建立了连接</span><span lang="EN-US">,</span><span style="font-family: 宋体;">然后不发送任何数据</span><span lang="EN-US">,</span><span style="font-family: 宋体;">那么持续的时间就是</span><span lang="EN-US">2</span><span style="font-family: 宋体;">小时</span><span lang="EN-US">11</span><span style="font-family: 宋体;">分钟</span><span lang="EN-US">,</span><span style="font-family: 宋体;">形成空连接攻击，上面三个参数就是预防此情形的，一般负载的</span><span lang="EN-US">web</span><span style="font-family: 宋体;">建议分别改为</span><span lang="EN-US">1800 15 5 </span><span style="font-family: 宋体;">，规避等待连接太多，及时释放资源。</span></p>
<p style="line-height: 150%;"><b><span lang="EN-US">tcp</span></b><b><span style="font-family: 宋体;">连接管理</span></b></p>
<p style="line-height: 150%;"><span lang="EN-US">1</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.ipv4.tcp_syncookies = 1</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">表示开启</span><span lang="EN-US">SYN Cookies</span><span style="font-family: 宋体;">。当出现</span><span lang="EN-US">SYN</span><span style="font-family: 宋体;">等待队列溢出时，启用</span><span lang="EN-US">cookies</span><span style="font-family: 宋体;">来处理，可防范少量</span><span lang="EN-US">SYN</span><span style="font-family: 宋体;">攻击，默认为</span><span lang="EN-US">0</span><span style="font-family: 宋体;">，表示关闭；</span></p>
<p style="line-height: 150%;"><span lang="EN-US">2</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.ipv4.tcp_tw_reuse = 1&nbsp; </span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">表示开启重用。允许将</span><span lang="EN-US">TIME-WAIT sockets</span><span style="font-family: 宋体;">重新用于新的</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">连接，默认为</span><span lang="EN-US">0</span><span style="font-family: 宋体;">，表示关闭；</span><span lang="EN-US">tw_reuse</span><span style="font-family: 宋体;">只对客户端起作用，</span><span style="font-family: 宋体;">开启后客户端在</span><span lang="EN-US">1s</span><span style="font-family: 宋体;">内回收</span></p>
<p style="line-height: 150%;"><span lang="EN-US">3</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.ipv4.tcp_tw_recycle = 1&nbsp; </span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">表示开启</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">连接中</span><span lang="EN-US">TIME-WAIT sockets</span><span style="font-family: 宋体;">的快速回收，默认为</span><span lang="EN-US">0</span><span style="font-family: 宋体;">，表示关闭。对客户端和服务器同时起作用，能够回收服务端</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">的</span><span lang="EN-US">TIME_WAIT</span><span style="font-family: 宋体;">数量</span></p>
<p style="line-height: 150%;"><span lang="EN-US">4</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.ipv4.tcp_fin_timeout = 60&nbsp; </span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">对于本端断开的</span><span lang="EN-US">socket</span><span style="font-family: 宋体;">连接，</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">保持在</span><span lang="EN-US">FIN_WAIT_2</span><span style="font-family: 宋体;">状态的时间。对方可能会断开连接或一直不结束连接或不可预料的进程死亡。默认值为</span><span lang="EN-US"> 60 </span><span style="font-family: 宋体;">秒。可以改为</span><span lang="EN-US">30</span><span style="font-family: 宋体;">﹐但需要注意﹐如果您的机器为负载很重的</span><span lang="EN-US">web</span><span style="font-family: 宋体;">服务器﹐您可能要冒内存被大量无效数据报填满的风险﹐</span><span lang="EN-US">FIN-WAIT-2 sockets </span><span style="font-family: 宋体;">的危险性低于</span><span lang="EN-US"> FIN-WAIT-1 </span><span style="font-family: 宋体;">﹐因为它们最多只吃</span><span lang="EN-US"> 1.5K </span><span style="font-family: 宋体;">的内存﹐但是它们存在时间更长。可以用命令</span><span lang="EN-US"># netstat -n | awk '/^tcp/ {++S[$NF]} END {for(a in S) print a,S[a]}'</span><span style="font-family: 宋体;">查看系统当前</span><span lang="EN-US">tcp</span><span style="font-family: 宋体;">连接状态</span><a name="_GoBack"></a></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="554" height="96" id="图片 7" src="/logbook/images/linux/linux内核参数优化/8107872823df.jpg" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">里面各种状态连接的生成原因是多种多样的，以实例可以说说</span><span lang="EN-US">CLOSE_WAIT</span><span style="font-family: 宋体;">、</span><span lang="EN-US"> FIN_WAIT_2</span><span style="font-family: 宋体;">状态的生成原因</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">如果服务器程序</span><span lang="EN-US">APACHE</span><span style="font-family: 宋体;">处于</span><span lang="EN-US">CLOSE_WAIT</span><span style="font-family: 宋体;">状态的话，说明套接字是被动关闭的！</span><span lang="EN-US"><br> </span><span style="font-family: 宋体;">假设</span><span lang="EN-US">CLIENT</span><span style="font-family: 宋体;">端主动断掉当前连接，那么双方关闭这个</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">连接共需要四个</span><span lang="EN-US">packet</span><span style="font-family: 宋体;">：</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="554" height="78" id="图片 1" src="/logbook/images/linux/linux内核参数优化/c52c4d7c0b00.jpg" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">这时候</span><span lang="EN-US">Client</span><span style="font-family: 宋体;">端处于</span><span lang="EN-US">FIN_WAIT_2</span><span style="font-family: 宋体;">状态；而</span><span lang="EN-US">Server </span><span style="font-family: 宋体;">程序处于</span><span lang="EN-US">CLOSE_WAIT</span><span style="font-family: 宋体;">状态。</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="554" height="80" src="/logbook/images/linux/linux内核参数优化/d4938d3d5968.jpg" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">这时</span><span lang="EN-US">Server </span><span style="font-family: 宋体;">发送</span><span lang="EN-US">FIN</span><span style="font-family: 宋体;">给</span><span lang="EN-US">Client</span><span style="font-family: 宋体;">，</span><span lang="EN-US">Server </span><span style="font-family: 宋体;">就置为</span><span lang="EN-US">LAST_ACK</span><span style="font-family: 宋体;">状态。</span><span lang="EN-US">Client</span><span style="font-family: 宋体;">回应了</span><span lang="EN-US">ACK</span><span style="font-family: 宋体;">，那么</span><span lang="EN-US">Server </span><span style="font-family: 宋体;">的套接字才会真正置为</span><span lang="EN-US">CLOSED</span><span style="font-family: 宋体;">状态。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">Server </span><span style="font-family: 宋体;">程序处于</span><span lang="EN-US">CLOSE_WAIT</span><span style="font-family: 宋体;">状态，而不是</span><span lang="EN-US">LAST_ACK</span><span style="font-family: 宋体;">状态，说明还没有发</span><span lang="EN-US">FIN</span><span style="font-family: 宋体;">给</span><span lang="EN-US">Client</span><span style="font-family: 宋体;">，那么可能是在关闭连接之前还有许多数据要发送或者其他事要做，导致没有发这个</span><span lang="EN-US">FIN packet</span><span style="font-family: 宋体;">。</span><span lang="EN-US"><br> </span><span style="font-family: 宋体;">通常来说，一个</span><span lang="EN-US">CLOSE_WAIT</span><span style="font-family: 宋体;">会维持至少</span><span lang="EN-US">2</span><span style="font-family: 宋体;">个小时的时间。如果有个流氓特地写了个程序，给你造成一堆的</span><span lang="EN-US">CLOSE_WAIT</span><span style="font-family: 宋体;">，消耗资源，那么通常是等不到释放那一刻，系统就已经解决崩溃了。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">5</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.ipv4.tcp_max_syn_backlog = 1024 &nbsp;</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">控制每个端口的</span><span lang="EN-US">tcpsyn</span><span style="font-family: 宋体;">的队列长度，来自客户端的连接请求需要排队，直至服务器接受，如果连接请求数大于该值，则连接请求会被丢弃，客户端无法连接服务器，一般服务器要提高此值。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">6</span><span style="font-family: 宋体;">）</span><span lang="EN-US"> net.ipv4.ip_local_port_range = 1024&nbsp;&nbsp; 65000&nbsp; </span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">表示用于向外连接的端口范围。缺省情况下很小：</span><span lang="EN-US">32768</span><span style="font-family: 宋体;">到</span><span lang="EN-US">61000</span><span style="font-family: 宋体;">，改为</span><span lang="EN-US">1024</span><span style="font-family: 宋体;">到</span><span lang="EN-US">65000</span><span style="font-family: 宋体;">。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">7</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.core.tcp_max_tw_buckets = 5000</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">表示系统同时保持</span><span lang="EN-US">TIME_WAIT</span><span style="font-family: 宋体;">套接字的最大数量，如果超过这个数字，</span><span lang="EN-US">TIME_WAIT</span><span style="font-family: 宋体;">套接字将立刻被清除并打印警告信息。默认为</span><span lang="EN-US">180000</span><span style="font-family: 宋体;">，改为</span><span lang="EN-US"> 5000</span><span style="font-family: 宋体;">。对于</span><span lang="EN-US">Apache</span><span style="font-family: 宋体;">、</span><span lang="EN-US">Nginx</span><span style="font-family: 宋体;">等服务器，上几行的参数可以很好地减少</span><span lang="EN-US">TIME_WAIT</span><span style="font-family: 宋体;">套接字数量。此项参数可以控制</span><span lang="EN-US">TIME_WAIT</span><span style="font-family: 宋体;">套接字的最大数量，避免服务器被大量的</span><span lang="EN-US">TIME_WAIT</span><span style="font-family: 宋体;">套接字拖死。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">8</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.core.wmem_max = 8388608</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">所有的队列（即系统）</span><span lang="EN-US">,</span><span style="font-family: 宋体;">最大系统发送缓存</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.core.rmem_max = 8388608</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">所有的队列（即系统）</span><span lang="EN-US">,</span><span style="font-family: 宋体;">最大系统接收缓存</span><span lang="EN-US">,</span><span style="font-family: 宋体;">单位为内存页，这里设置最大值</span><span lang="EN-US">8MB</span></p>
<p style="line-height: 150%;"><span lang="EN-US">9</span><span style="font-family: 宋体;">）</span><span lang="EN-US">net.ipv4.tcp_wmem = 4096 87380 8388608</span></p>
<p style="line-height: 150%;"><span lang="EN-US">&nbsp;&nbsp; net.ipv4.tcp_rmem = 4096 87380 8388608</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">该文件包含</span><span lang="EN-US">3</span><span style="font-family: 宋体;">个整数值，分别是：</span><span lang="EN-US">min</span><span style="font-family: 宋体;">，</span><span lang="EN-US">default</span><span style="font-family: 宋体;">，</span><span lang="EN-US">max</span></p>
<p style="line-height: 150%;"><span lang="EN-US">Min</span><span style="font-family: 宋体;">：为</span><span lang="EN-US">TCP socket</span><span style="font-family: 宋体;">预留用于发送</span><span lang="EN-US">/</span><span style="font-family: 宋体;">接收缓冲的内存数量，即使在内存出现紧张情况下</span><span lang="EN-US">TCP socket</span><span style="font-family: 宋体;">都至少会有这么多数量的内存用于</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">接收缓冲。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">Default</span><span style="font-family: 宋体;">：为</span><span lang="EN-US">TCP socket</span><span style="font-family: 宋体;">预留用于发送</span><span lang="EN-US">/</span><span style="font-family: 宋体;">接收缓冲的内存数量，默认情况下该值会影响其它协议使用的</span><span lang="EN-US">net.core.wmem</span><span style="font-family: 宋体;">中</span><span lang="EN-US">default</span><span style="font-family: 宋体;">的值，一般要低于</span><span lang="EN-US">net.core.wmem</span><span style="font-family: 宋体;">中</span><span lang="EN-US">default</span><span style="font-family: 宋体;">的值。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">Max</span><span style="font-family: 宋体;">：为</span><span lang="EN-US">TCP socket</span><span style="font-family: 宋体;">预留用于发送</span><span lang="EN-US">/</span><span style="font-family: 宋体;">接收缓冲的内存最大值，必须小于或等于</span><span lang="EN-US">wmem_max</span><span style="font-family: 宋体;">和</span><span lang="EN-US">rmem_max</span></p>
<p style="line-height: 150%;"><span lang="EN-US">10</span><span style="font-family: 宋体;">）</span><span lang="EN-US"> net.ipv4.tcp_mem = 524288 &nbsp;699050 &nbsp;1048576</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">内核分配给</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">连接的内存，单位是</span><span lang="EN-US">Page</span><span style="font-family: 宋体;">，同样有</span><span lang="EN-US">3</span><span style="font-family: 宋体;">个值</span><span lang="EN-US">,</span><span style="font-family: 宋体;">意思是</span><span lang="EN-US">:</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_mem[0]:</span><span style="font-family: 宋体;">低于此值</span><span lang="EN-US">,TCP</span><span style="font-family: 宋体;">没有内存压力，</span><span lang="EN-US">kernel </span><span style="font-family: 宋体;">不对其进行任何的干预</span><span lang="EN-US">.</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_mem[1]:</span><span style="font-family: 宋体;">在此值下</span><span lang="EN-US">, TCP</span><span style="font-family: 宋体;">试图稳定其内存使用</span><span lang="EN-US">,kernel</span><span style="font-family: 宋体;">进入内存压力阶段</span><span lang="EN-US">.</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_mem[2]:</span><span style="font-family: 宋体;">高于此值</span><span lang="EN-US">,TCP</span><span style="font-family: 宋体;">拒绝分配</span><span lang="EN-US">socket.</span></p>
<p style="line-height: 150%;"><span lang="EN-US">11</span><span style="font-family: 宋体;">）</span><span lang="EN-US"> net.ipv4.tcp_retries2 = 15</span></p>
<p style="line-height: 150%;"><span lang="EN-US">TCP</span><span style="font-family: 宋体;">失败重传次数</span><span lang="EN-US">,</span><span style="font-family: 宋体;">默认值</span><span lang="EN-US">15,</span><span style="font-family: 宋体;">意味着重传</span><span lang="EN-US">15</span><span style="font-family: 宋体;">次才彻底放弃</span><span lang="EN-US">.</span><span style="font-family: 宋体;">可减少到</span><span lang="EN-US">5,</span><span style="font-family: 宋体;">以尽早释放内核资源，尽早的检测连接失效</span></p>
<h2 style="line-height: 150%;"><span lang="EN-US">2</span><span style="font-family: 宋体;">、内存和</span><span lang="EN-US">IO</span><span style="font-family: 宋体;">参数优化</span></h2>
<p style="line-height: 150%;"><span lang="EN-US">1</span><span style="font-family: 宋体;">）</span><span lang="EN-US">vm.swappiness = 60</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">实际上，并不是等所有的物理内存都消耗完毕之后，才去使用</span><span lang="EN-US">swap</span><span style="font-family: 宋体;">的空间，什么时候使用是由</span><span lang="EN-US">swappiness</span><span style="font-family: 宋体;">参数值控制。该参数</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">表示系统进行交换行为的程度，数值（</span><span lang="EN-US">0-100</span><span style="font-family: 宋体;">）越高，越可能发生磁盘交换。控制</span><span lang="EN-US">swappiness</span><span style="font-family: 宋体;">参数，尽量减少应用的内存被交换</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">到交换分区中，默认是</span><span lang="EN-US">60</span><span style="font-family: 宋体;">。</span><span lang="EN-US">swappiness=0</span><span style="font-family: 宋体;">的时候表示最大限度使用物理内存，然后才是</span><span lang="EN-US"> swap</span><span style="font-family: 宋体;">空间，</span><span lang="EN-US">swappiness</span><span style="font-family: 宋体;">＝</span><span lang="EN-US">100</span><span style="font-family: 宋体;">的时候表示</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">积极的使用</span><span lang="EN-US">swap</span><span style="font-family: 宋体;">分区，并且把内存上的数据及时的搬运到</span><span lang="EN-US">swap</span><span style="font-family: 宋体;">空间里面。适当降低当该值，让操作系统尽可能的使用物理内存，</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">降低系统对</span><span lang="EN-US">swap</span><span style="font-family: 宋体;">的使用，对提高系统的性能，特别是提升</span><span lang="EN-US">TS</span><span style="font-family: 宋体;">类设备性能更为明显。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">2</span><span style="font-family: 宋体;">）</span><span lang="EN-US">vm.drop_caches=0</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">使内核释放</span><span lang="EN-US">page_cache</span><span style="font-family: 宋体;">，</span><span lang="EN-US">dentries</span><span style="font-family: 宋体;">和</span><span lang="EN-US">inodes</span><span style="font-family: 宋体;">缓存所占的内存。缺省值为</span><span lang="EN-US">0</span></p>
<p style="line-height: 150%;"><span lang="EN-US">1</span><span style="font-family: 宋体;">：只释放</span><span lang="EN-US">page_cache</span></p>
<p style="line-height: 150%;"><span lang="EN-US">2</span><span style="font-family: 宋体;">：只释放</span><span lang="EN-US">dentries</span><span style="font-family: 宋体;">和</span><span lang="EN-US">inodes</span><span style="font-family: 宋体;">缓存</span></p>
<p style="line-height: 150%;"><span lang="EN-US">3</span><span style="font-family: 宋体;">：释放</span><span lang="EN-US">page_cache</span><span style="font-family: 宋体;">、</span><span lang="EN-US">dentries</span><span style="font-family: 宋体;">和</span><span lang="EN-US">inodes</span><span style="font-family: 宋体;">缓存</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="554" height="119" id="图片 5" src="/logbook/images/linux/linux内核参数优化/8288ed6304c3.jpg" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">我们在查看系统内存时都会发现</span><span lang="EN-US"> cached</span><span style="font-family: 宋体;">占用的内存都比较高，其实这是为了提高文件读取效率的做法。可以通地修改参数的方法回收内存。注意这里释放</span><span lang="EN-US">cache</span><span style="font-family: 宋体;">可能会造成内存数据丢失，修改之前最好用</span><span lang="EN-US">sync</span><span style="font-family: 宋体;">命令把数据刷到硬盘。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">3</span><span style="font-family: 宋体;">）</span><span lang="EN-US">vm.dirty_ratio = 40</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">这个参数则指定了当文件系统缓存脏页数量达到系统内存百分之多少时（缺省值</span><span lang="EN-US">40%</span><span style="font-family: 宋体;">），系统必须开始处理缓存脏页。</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">该参数需要据数据流写场合情况适当修改，数据流非持续非恒定写入时，增大参数会使用更多系统内存用于磁盘写缓冲，</span><span style="font-family: 宋体;">也可以极大提高系统的写性能，但当需要持续、恒定的写入场合时，应该降低其数值。</span></p>
<table border="1" cellpadding="0" cellspacing="0">
<tbody>
<tr>
<td width="3" height="14"></td>
</tr>
<tr>
<td></td>
<td style=""><img width="554" height="71" src="/logbook/images/linux/linux内核参数优化/d6de2598ae45.jpg" style="position: relative; z-index: 2;"></td>
</tr>
</tbody>
</table>
<table border="1" cellpadding="0" cellspacing="0">
<tbody>
<tr>
<td width="0" height="1"></td>
</tr>
<tr>
<td></td>
<td style=""><img width="401" height="225" src="/logbook/images/linux/linux内核参数优化/e5293c633d31.jpg" style="position: relative; z-index: 2;"></td>
</tr>
</tbody>
</table>
<p style="line-height: 150%;"></p>
<p style="line-height: 150%;"><span lang="EN-US">4</span><span style="font-family: 宋体;">）</span><span lang="EN-US">vm.dirty_background_ratio = 5</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">个参数指定了当文件系统缓存脏页数量达到系统内存百分之多少时（如</span><span lang="EN-US">5%</span><span style="font-family: 宋体;">，低于</span><span lang="EN-US">dirty_ratio</span><span style="font-family: 宋体;">）就会触发</span><span lang="EN-US">pdflush</span><span style="font-family: 宋体;">等后台回写</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">进程运行，将一定缓存的脏页异步地刷入硬盘。应该场合跟</span><span lang="EN-US">dirty_ratio</span><span style="font-family: 宋体;">一样</span></p>
<p style="line-height: 150%;"><span lang="EN-US">dirty_ratio vs dirty_background_ratio</span><span style="font-family: 宋体;">通常系统会先达到</span><span lang="EN-US">dirty_background_ratio</span><span style="font-family: 宋体;">的条件然后触发</span><span lang="EN-US">flush</span><span style="font-family: 宋体;">进程进行异步的</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">回写操作，但是这一过程中应用进程仍然可以进行写操作，如果多个应用进程写入的量大于</span><span lang="EN-US">flush</span><span style="font-family: 宋体;">进程刷出的量那就会达到</span></p>
<p style="line-height: 150%;"><span lang="EN-US">dirty_ratio</span><span style="font-family: 宋体;">这个参数所设定的值，此时操作系统会转入同步地处理脏页的过程，阻塞应用进程。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">5</span><span style="font-family: 宋体;">）</span><span lang="EN-US">vm.dirty_writeback_centisecs = 500</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">该参数控制内核的脏数据刷新进程</span><span lang="EN-US">pdflush</span><span style="font-family: 宋体;">的运行间隔。单位是</span><span lang="EN-US"> 1/100 </span><span style="font-family: 宋体;">秒。缺省数值是</span><span lang="EN-US">500</span><span style="font-family: 宋体;">，也就是</span><span lang="EN-US"> 5 </span><span style="font-family: 宋体;">秒。如果你的系统是</span><span style="font-family: 宋体;">持续地写入动作，那么实际上还是降低这个数值比较好，这样可以把尖峰的写操作削平成多次写操作。如果你的系统是短期</span><span style="font-family: 宋体;">地尖峰式的写操作，并且写入数据不大（几十</span><span lang="EN-US">M/</span><span style="font-family: 宋体;">次）且内存有比较多富裕，那么应该增大此数值</span></p>
<p style="line-height: 150%;"><span lang="EN-US" style=""><img width="554" height="45" id="图片 2" src="/logbook/images/linux/linux内核参数优化/dba958c62393.jpg" style="position: relative; z-index: 2;"></span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">可以查</span><span lang="EN-US">io</span><span style="font-family: 宋体;">压力，如果压力大适当调小该参数</span></p>
<p style="line-height: 150%;"><span lang="EN-US">6</span><span style="font-family: 宋体;">）</span><span lang="EN-US">vm.dirty_expire_centisecs = 3000</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">该参数声明</span><span lang="EN-US">Linux</span><span style="font-family: 宋体;">内核写缓冲区里面的数据多“旧”了之后，</span><span lang="EN-US">pdflush</span><span style="font-family: 宋体;">进程就开始考虑写到磁盘中去。单位是</span><span lang="EN-US"> 1/100</span><span style="font-family: 宋体;">秒。</span><span style="font-family: 宋体;">缺省是</span><span lang="EN-US"> 30000</span><span style="font-family: 宋体;">，也就是</span><span lang="EN-US"> 30 </span><span style="font-family: 宋体;">秒的数据就算旧了，将会落地磁盘。对于特别重载的写操作来说，这个值适当缩小也是好的，</span><span style="font-family: 宋体;">但也不能缩小太多，因为缩小太多也会导致</span><span lang="EN-US">IO</span><span style="font-family: 宋体;">提交太快。当然，如果你的系统内存比较大，可以任性一些，并且写入模式是间歇式的，</span><span style="font-family: 宋体;">并且每次写入的数据不大（比如几十</span><span lang="EN-US">M</span><span style="font-family: 宋体;">），那么这个值还是大些的好。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">7</span><span style="font-family: 宋体;">）</span><span lang="EN-US">vm.min_free_kbytes = 1000</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">该文件表示强制</span><span lang="EN-US">Linux&nbsp;&nbsp; VM</span><span style="font-family: 宋体;">最低保留多少空闲内存（</span><span lang="EN-US">Kbytes</span><span style="font-family: 宋体;">）。</span><span lang="EN-US">ts80</span><span style="font-family: 宋体;">缺省值：</span><span lang="EN-US">90112</span><span style="font-family: 宋体;">（</span><span lang="EN-US">88M</span><span style="font-family: 宋体;">物理内存），</span><span style="font-family: 宋体;">目前很少场合用到，可以调小，节约内存给其他程序用</span></p>
<h1 style="line-height: 150%;"><span style="font-family: 宋体;">五、</span><span lang="EN-US"> web</span><span style="font-family: 宋体;">相关参数实例</span></h1>
<p style="line-height: 150%;"><span style="font-family: 宋体;">由于默认的</span><span lang="EN-US">Linux</span><span style="font-family: 宋体;">内核参数考虑的是最通用的场景，这明显不符合用于支持高并发访问的</span><span lang="EN-US">Web</span><span style="font-family: 宋体;">服务器的定义，</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">所以需要修改</span><span lang="EN-US">Linux</span><span style="font-family: 宋体;">内核参数，使得</span><span lang="EN-US">Nginx/Apache</span><span style="font-family: 宋体;">可以拥有更高的性能。在优化内核时，可以做的事件很多，</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">不过，我们通常会根据业务特点来进行调整，当</span><span lang="EN-US">Nginx/Apache</span><span style="font-family: 宋体;">作为静态</span><span lang="EN-US">Web</span><span style="font-family: 宋体;">内容服务器、反向代理服务器或</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">是提供图片缩略功能（实时压缩图片）的服务器时，其内核参数的调整都是不同的。这里只针对最通用的、</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">使</span><span lang="EN-US">Nginx</span><span style="font-family: 宋体;">支持更多并发请求的</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">网络参数做简单说明。</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">首先，需要修改</span><span lang="EN-US">/etc/sysctl.conf</span><span style="font-family: 宋体;">来更改内核参数，例如，最常用的配置：</span></p>
<p style="line-height: 150%;"><span lang="EN-US">#</span><span style="font-family: 宋体;">新增字段</span></p>
<p style="line-height: 150%;"><span lang="EN-US">fs.file-max = 999999&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_tw_reuse = 1&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_keepalive_time = 600&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_fin_timeout = 30&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_max_tw_buckets = 5000&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.ip_local_port_range = 1024 61000&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_rmem = 10240 87380 12582912&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_wmem = 10240 87380 12582912&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.core.netdev_max_backlog = 8096&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.core.rmem_default = 6291456&nbsp; </span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.core.wmem_default = 6291456</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">然后执行</span><span lang="EN-US">sysctl -p</span><span style="font-family: 宋体;">命令，使上述参数生效。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">fs.file-max = 999999</span><span style="font-family: 宋体;">：这个参数表示进程（比如一个</span><span lang="EN-US">worker</span><span style="font-family: 宋体;">进程）可以同时打开的最大句柄数，这个参数</span><span style="font-family: 宋体;">直线限制最大并发连接数，需根据实际情况配置。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_tw_reuse = 1</span><span style="font-family: 宋体;">：这个参数设置为</span><span lang="EN-US">1</span><span style="font-family: 宋体;">，表示允许将</span><span lang="EN-US">TIME-WAIT</span><span style="font-family: 宋体;">状态的</span><span lang="EN-US">socket</span><span style="font-family: 宋体;">重新用于新的</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">连接，</span><span style="font-family: 宋体;">这对于服务器来说很有意义，因为服务器上总会有大量</span><span lang="EN-US">TIME-WAIT</span><span style="font-family: 宋体;">状态的连接。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_keepalive_time = 600</span><span style="font-family: 宋体;">：这个参数表示当</span><span lang="EN-US">keepalive</span><span style="font-family: 宋体;">启用时，</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">发送</span><span lang="EN-US">keepalive</span><span style="font-family: 宋体;">消息的频度。</span><span style="font-family: 宋体;">默认是</span><span lang="EN-US">2</span><span style="font-family: 宋体;">小时，若将其设置的小一些，可以更快地清理无效的连接。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_fin_timeout = 30</span><span style="font-family: 宋体;">：这个参数表示当服务器主动关闭连接时，</span><span lang="EN-US">socket</span><span style="font-family: 宋体;">保持在</span><span lang="EN-US">FIN-WAIT-2</span><span style="font-family: 宋体;">状态</span><span style="font-family: 宋体;">的最大时间。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_max_tw_buckets = 5000</span><span style="font-family: 宋体;">：这个参数表示操作系统允许</span><span lang="EN-US">TIME_WAIT</span><span style="font-family: 宋体;">套接字数量的最大值，</span></p>
<p style="line-height: 150%;"><span style="font-family: 宋体;">如果超过这个数字，</span><span lang="EN-US">TIME_WAIT</span><span style="font-family: 宋体;">套接字将立刻被清除并打印警告信息。该参数默认为</span><span lang="EN-US">180000，</span><span style="font-family: 宋体;">过多的</span><span lang="EN-US">TIME_WAIT</span><span style="font-family: 宋体;">套接字会使</span><span lang="EN-US">Web</span><span style="font-family: 宋体;">服务器变慢。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_max_syn_backlog = 1024</span><span style="font-family: 宋体;">：这个参数标示</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">三次握手建立阶段接受</span><span lang="EN-US">SYN</span><span style="font-family: 宋体;">请求队列的</span><span style="font-family: 宋体;">最大长度，默认为</span><span lang="EN-US">1024</span><span style="font-family: 宋体;">，将其设置得大一些可以使出现</span><span lang="EN-US">Nginx</span><span style="font-family: 宋体;">繁忙来不及</span><span lang="EN-US">accept</span><span style="font-family: 宋体;">新连接的情况时</span><span style="font-family: 宋体;">，</span><span lang="EN-US">Linux</span><span style="font-family: 宋体;">不至于丢失客户端发起的连接请求。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.ip_local_port_range = 1024 61000</span><span style="font-family: 宋体;">：这个参数定义了在</span><span lang="EN-US">UDP</span><span style="font-family: 宋体;">和</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">连接中本地（不包括连接的远端）</span><span style="font-family: 宋体;">端口的取值范围。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_rmem = 10240 87380 12582912</span><span style="font-family: 宋体;">：这个参数定义了</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">接受缓存（用于</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">接受滑动窗口）的最小值、</span><span style="font-family: 宋体;">默认值、最大值。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_wmem = 10240 87380 12582912</span><span style="font-family: 宋体;">：这个参数定义了</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">发送缓存（用于</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">发送滑动窗口）的最小值、</span><span style="font-family: 宋体;">默认值、最大值。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.core.netdev_max_backlog = 8096</span><span style="font-family: 宋体;">：当网卡接受数据包的速度大于内核处理的速度时，会有一个队列保存这</span><span style="font-family: 宋体;">些数据包。这个参数表示该队列的最大值。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.core.rmem_default = 6291456</span><span style="font-family: 宋体;">：这个参数表示内核套接字接受缓存区默认的大小。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.core.wmem_default = 6291456</span><span style="font-family: 宋体;">：这个参数表示内核套接字发送缓存区默认的大小。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.core.rmem_max = 12582912</span><span style="font-family: 宋体;">：这个参数表示内核套接字接受缓存区的最大大小。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.core.wmem_max = 12582912</span><span style="font-family: 宋体;">：这个参数表示内核套接字发送缓存区的最大大小。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">net.ipv4.tcp_syncookies = 1</span><span style="font-family: 宋体;">：该参数与性能无关，用于解决</span><span lang="EN-US">TCP</span><span style="font-family: 宋体;">的</span><span lang="EN-US">SYN</span><span style="font-family: 宋体;">攻击。</span></p>
<p style="line-height: 150%;"><span lang="EN-US">&nbsp;</span></p>
