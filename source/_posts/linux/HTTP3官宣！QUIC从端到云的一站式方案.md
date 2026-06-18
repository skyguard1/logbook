---
title: "HTTP3官宣！QUIC从端到云的一站式方案"
date: 2022-06-17 11:24:03
categories:
  - linux
---

<h1 id="2e470045-2981-b12c-ea93-20551d5dbfdd" class="toc-enable">一、HTTP3 RFC正式官宣</h1>
<p>IETF（互联网工程任务组）宣布了 HTTP/3 标准，编号为<strong><a href="https://www.rfc-editor.org/rfc/rfc9114.html#name-introduction" target="_blank" rel="noreferrer">&nbsp;RFC 9114</a></strong>。</p>
<p>RFC Editor 页面显示，目前&nbsp;RFC 9114 处于 “提案标准 (PROPOSED STANDARD)” 状态，尚未成为正式标准；但在工业界中，根据w3techs的数据，目前已经大概有&nbsp;<strong>25.1%&nbsp;</strong>的网站使用了HTTP/3。相信不久的将来，HTTP3的时代将全面降临。</p>
<p style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(2)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p style="text-align:center;">图1-1&nbsp; 使用了HTTP/3的网站数量占比</p>
<p style="text-align:center;"><br></p>
<h1 class="toc-enable" id="mces2pawsh">二、QUIC是啥？</h1>
<h2 class="toc-enable" id="mcetjlvcnh">2.1 HTTP3是什么？QUIC是什么？</h2>
<p>QUIC 和 HTTP/3 是什么关系呢？</p>
<p>QUIC(Quick UDP Internet Connection)是谷歌推出的一套基于UDP的传输协议，QUIC 也一个传输层协议，在传输层之上还有应用层，我们熟知的应用层协议 HTTP、FTP、IMAP 等这些协议理论上都可以运行在 QUIC 之上，其中运行在 QUIC 之上的 HTTP 协议被称为 HTTP/3，这就是”HTTP over QUIC 即 HTTP/3“的含义。</p>
<p>那QUIC为什么基于UDP实现呢？</p>
<p>因为UDP是一个简单传输协议，基于UDP可以支持建立安全连接只需要一的个往返时间。另外，众所周知的UDP比TCP传输速度快，TCP是可靠协议，但是代价是双方确认数据而衍生的一系列消耗。其次TCP是系统内核实现的，如果升级TCP协议，就得让用户升级系统，这个的门槛比较高，而QUIC在UDP基础上由客户端自由发挥，只要有服务器能对接就可以。</p>
<p>QUIC还基于UDP实现了HTTP/2多路复用、头部压缩等功能，吸收并改良了HTTP/2的优点。<br></p>
<p style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(3)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p style="text-align:center;">图2-1 HTTP与QUIC</p>
<p><br></p>
<h2 class="toc-enable" id="HTTP-协议历史">2.2 HTTP 协议发展</h2>
<h3 class="toc-enable" id="mce87kts4">2.2.1 HTTP历史进程</h3>
<ol><li>
<p>HTTP/0.9（1991年）只支持get方法不支持请求头</p>
</li>
<li>
<p>HTTP/1.0（1996年）基本成型，支持请求头、富文本、状态码、缓存、连接无法复用</p>
</li>
<li>
<p>HTTP/1.1（1999年）支持连接复用、分块发送、断点续传</p>
</li>
<li>
<p>HTTP/2.0（2015年）二进制分帧传输、多路复用、头部压缩、服务器推送等</p>
</li>
<li>
<p>HTTP/3.0（2018年）QUIC 于2013年实现；2018年10月，IETF的HTTP工作组和QUIC工作组共同决定将QUIC上的HTTP映射称为 "HTTP/3<a href="https://zh.wikipedia.org/wiki/HTTP/3" title="HTTP/3"></a>"，以提前使其成为全球标准</p>
</li>
</ol><p><br></p>
<h3 class="toc-enable" id="HTTP1-0-和-HTTP1-1">2.2.2 HTTP/1.0 和 HTTP/1.1</h3>
<ol><li><strong>队头阻塞：</strong>下个请求必须在前一个请求返回后才能发出，导致带宽无法被充分利用，后续请求被阻塞（HTTP 1.1 尝试使用流水线（Pipelining）技术，但先天 FIFO（先进先出）机制导致当前请求的执行依赖于上一个请求执行的完成，容易引起队头阻塞，并没有从根本上解决问题）</li>
<li><strong>协议开销大：</strong>header里携带的内容过大，且不能压缩，增加了传输的成本</li>
<li><strong>单向请求：</strong>只能单向请求，客户端请求什么，服务器返回什么</li>
<li><strong>HTTP/1.0 和 HTTP/1.1 的区别：</strong></li>
<li><strong>HTTP/1.0</strong>：仅支持保持短暂的TCP连接（连接无法复用）；不支持断点续传；前一个请求响应到达之后下一个请求才能发送，存在队头阻塞</li>
<li><strong>HTTP/1.1</strong>：默认支持长连接（请求可复用TCP连接）；支持断点续传（通过在 Header 设置参数）；优化了缓存控制策略；管道化，可以一次发送多个请求，但是响应仍是顺序返回，仍然无法解决队头阻塞的问题；新增错误状态码通知；请求消息和响应消息都支持Host头域</li>
</ol><p><br></p>
<h3 class="toc-enable" id="HTTP2">2.2.3 HTTP/2</h3>
<p>HTTP/2 标准于2015年5月以RFC 7540正式发布。解决 HTTP/1.1 的一些问题，但是解决不了底层 TCP 协议层面上的队头阻塞问题。</p>
<ol><li>
<p><strong>二进制传输：</strong>二进制格式传输数据解析起来比文本更高效</p>
</li>
<li>
<p><strong>多路复用：</strong>重新定义底层 http 语义映射，允许同一个连接上使用请求和响应双向数据流。同一域名只需占用一个 TCP 连接，通过数据流（Stream）以帧为基本协议单位，避免了因频繁创建连接产生的延迟，减少了内存消耗，提升了使用性能，并行请求，且慢的请求或先发送的请求不会阻塞其他请求的返回</p>
</li>
<li>
<p><strong>Header压缩：</strong>减少请求中的冗余数据，降低开销</p>
</li>
<li>
<p><strong>服务端可以主动推送：</strong>提前给客户端推送必要的资源，这样就可以相对减少一点延迟时间</p>
</li>
<li>
<p><strong>流优先级：</strong>数据传输优先级可控，使网站可以实现更灵活和强大的页面控制</p>
</li>
<li>
<p><strong>可重置：</strong>能在不中断 TCP 连接的情况下停止数据的发送</p>
</li>
</ol><p><strong>缺点</strong>：HTTP/2中，多个请求在一个TCP管道中的，出现了丢包时，HTTP/2的表现反倒不如HTTP/1.1了。因为 TCP 为了保证可靠传输，有个特别的“丢包重传”机制，丢失的包必须要等待重新传输确认，HTTP/2出现丢包时，整个 TCP 都要开始等待重传，那么就会阻塞该TCP连接中的所有请求。而对于 HTTP/1.1 来说，可以开启多个 TCP 连接，出现这种情况反到只会影响其中一个连接，剩余的 TCP 连接还可以正常传输数据</p>
<p style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(4)" alt="" style="position: relative; z-index: 2;"></p>
<p style="text-align:center;">图2-2 HTTP1.1 VS HTTP2</p>
<p style="text-align:center;"><br></p>
<h3 class="toc-enable" id="HTTP3"><a title="HTTP3" class="headerlink" href="https://nolaaaaa.github.io/2019/04/11/QUIC%E5%8D%8F%E8%AE%AE-%E5%92%8C-TCP-UDP-%E5%8D%8F%E8%AE%AE/#HTTP3"></a>2.2.4 HTTP/3 —— HTTP Over QUIC</h3>
<p>HTTP 是建立在 TCP 协议之上，所有 HTTP 协议的瓶颈及其优化技巧都是基于 TCP 协议本身的特性，HTTP/2 虽然实现了多路复用，底层 TCP 协议层面上的问题并没有解决（HTTP/2 同一域名下只需要使用一个 TCP 连接。但是如果这个连接出现了丢包，会导致整个 TCP 都要开始等待重传，后面的所有数据都被阻塞了），而基于 QUIC 的 HTTP/3 就是为解决 HTTP/2 的 TCP 问题而生。</p>
<p><br></p>
<h1 class="toc-enable" id="mcecklyzp">三、QUIC的关键特性</h1>
<p class="toc-enable">我们这里列举一下 QUIC 的重要特性，这些特性是 QUIC 得以被广泛应用的关键。不同业务也可以根据业务特点利用 QUIC 的特性去做一些优化。同时，这些特性也是我们去提供 QUIC 服务的切入点。</p>
<h2 class="toc-enable" id="mcexlzscqw"><strong>3.1 连接迁移</strong></h2>
<h3 class="toc-enable" id="mcedvwxp5a"><b>3.1.1 tcp的连接重连之痛</b></h3>
<p>一条 TCP 连接是由<strong>四元组</strong>标识的（源 IP，源端口，目的 IP，目的端口）。什么叫连接迁移呢？就是当其中任何一个元素发生变化时，这条连接依然维持着，能够保持业务逻辑不中断。当然这里面主要关注的是客户端的变化，因为客户端不可控并且网络环境经常发生变化，而服务端的 IP 和端口一般都是固定的。</p>
<p>比如大家使用手机在 WIFI 和 4G 移动网络切换时，客户端的 IP 肯定会发生变化，需要重新建立和服务端的 TCP 连接。</p>
<p>又比如大家使用公共 NAT 出口时，有些连接竞争时需要重新绑定端口，导致客户端的端口发生变化，同样需要重新建立 TCP 连接。</p>
<p>所以从 TCP 连接的角度来讲，这个问题是无解的。</p>
<h3 class="toc-enable" id="mcejkrdrjl">3.1.2 基于UDP的QUIC的连接迁移实现</h3>
<p>当用户的地址发生变化时，如 WIFI 切换到 4G 场景，基于 TCP 的 HTTP 协议无法保持连接的存活。QUIC 基于连接 ID 唯一识别连接。当源地址发生改变时，QUIC 仍然可以保证连接存活和数据正常收发。</p>
<p>那 QUIC 是如何做到连接迁移呢？很简单，QUIC是基于UDP协议的，任何一条 QUIC 连接不再以 IP 及端口四元组标识，而是以一个 64 位的随机数作为 ID 来标识，这样就算 IP 或者端口发生变化时，只要 ID 不变，这条连接依然维持着，上层业务逻辑感知不到变化，不会中断，也就不需要重连。</p>
<p>由于这个 ID 是客户端随机产生的，并且长度有 64 位，所以冲突概率非常低。</p>
<p style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(5)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p style="text-align:center;">图3-1 TCP 和 QUIC 在 Wi-Fi 和 4G 网络切换时，唯一标识的不同情况</p>
<h1 class="Post-Title toc-enable" id="mcek2glsrz"><br></h1>
<h2 class="toc-enable" id="mce979heup"><strong>3.2 低连接延时</strong></h2>
<h3 class="toc-enable" id="mcehhuw79">3.2.1 TLS的连接时延问题</h3>
<p>以一次简单的浏览器访问为例，在地址栏中输入https://www.abc.com，实际会产生以下动作：</p>
<ol><li>DNS递归查询www.abc.com，获取地址解析的对应IP；</li>
<li>TCP握手，我们熟悉的TCP三次握手需要需要1.5个RTT；</li>
<li>TLS握手，以目前应用最广泛的TLS 1.2而言，需要2个RTT。对于非首次建连，可以选择启用会话重用，则可缩小握手时间到1个RTT；</li>
<li>HTTP业务数据交互，假设abc.com的数据在一次交互就能取回来。那么业务数据的交互需要1个RTT； 经过上面的过程分析可知，要完成一次简短的HTTPS业务数据交互，需要经历：新连接 <strong>4RTT + DNS</strong>；会话重用 <strong>3RTT + DNS</strong>。</li>
</ol><p>所以，对于数据量小的请求而言，单一次的请求握手就占用了大量的时间，对于用户体验的影响非常大。同时，在用户网络不佳的情况下，RTT延时会变得较高，极其影响用户体验。</p>
<p>下图对比了TLS各版本与场景下的延时对比：</p>
<p style=""><img alt="" src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(6)" style="position: relative; z-index: 2;"></p>
<p style="text-align:center;">图3-2 tls各个版本握手时延</p>
<p>从对比我们可以看到，即使用上了TLS 1.3，精简了握手过程，最快能做到0-RTT握手(首次是1-RTT)；但是对用户感知而言, 还要加上1RTT的TCP握手开销。 Google有提出Fastopen的方案来使得TCP非首次握手就能附带用户数据，但是由于TCP实现僵化，无法升级应用，相关RFC到现今都是experimental状态。这种分层设计带来的延时,有没有办法进一步降低呢? QUIC通过合并加密与连接管理解决了这个问题，我们来看看其是如何实现真正意义上的0-RTT的握手, 让与server进行第一个数据包的交互就能带上用户数据。</p>
<p><br></p>
<h3 class="toc-enable" id="mceyos4gh">3.2.2 真·0-RTT的QUIC握手</h3>
<p>QUIC 由于基于 UDP，无需 TCP 连接，在最好情况下，短连接下 QUIC 可以做到 0RTT 开启数据传输。而基于 TCP 的 HTTPS，即使在最好的 TLS1.3 的 early data 下仍然需要 1RTT 开启数据传输。而对于目前线上常见的 TLS1.2 完全握手的情况，则需要 3RTT 开启数据传输。对于 RTT 敏感的业务，QUIC 可以有效的降低连接建立延迟。</p>
<p>究其原因一方面是TCP和TLS分层设计导致的：分层的设计需要每个逻辑层次分别建立自己的连接状态。另一方面是TLS的握手阶段复杂的密钥协商机制导致的。要降低建连耗时，需要从这两方面着手。</p>
<p>QUIC具体握手过程如下：</p>
<ol><li>客户端判断本地是否已有服务器的全部配置参数（证书配置信息），如果有则直接跳转到(5)，否则继续&nbsp;</li>
<li>客户端向服务器发送inchoate client hello(CHLO)消息，请求服务器传输配置参数</li>
<li>服务器收到CHLO，回复rejection(REJ)消息，其中包含服务器的部分配置参数</li>
<li>客户端收到REJ，提取并存储服务器配置参数，跳回到(1)&nbsp;</li>
<li>客户端向服务器发送full client hello消息，开始正式握手，消息中包括客户端选择的公开数。此时客户端根据获取的服务器配置参数和自己选择的公开数，可以计算出初始密钥K1。</li>
<li>服务器收到full client hello，如果不同意连接就回复REJ，同(3)；如果同意连接，根据客户端的公开数计算出初始密钥K1，回复server hello(SHLO)消息，SHLO用初始密钥K1加密，并且其中包含服务器选择的一个临时公开数。</li>
<li>客户端收到服务器的回复，如果是REJ则情况同(4)；如果是SHLO，则尝试用初始密钥K1解密，提取出临时公开数</li>
<li>客户端和服务器根据临时公开数和初始密钥K1，各自基于SHA-256算法推导出会话密钥K2</li>
<li>双方更换为使用会话密钥K2通信，初始密钥K1此时已无用，QUIC握手过程完毕。之后会话密钥K2更新的流程与以上过程类似，只是数据包中的某些字段略有不同。</li>
</ol><p style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(7)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p style="text-align:center;">图3-3 quic 0-rtt 握手</p>
<p><br></p>
<h2 class="toc-enable" id="mcepx3q6zo"><strong>3.3 可自定义的拥塞控制</strong></h2>
<p>Quic使用可插拔的拥塞控制，相较于TCP，它能提供更丰富的拥塞控制信息。比如对于每一个包，不管是原始包还是重传包，都带有一个新的序列号(seq)，这使得Quic能够区分ACK是重传包还是原始包，从而避免了TCP重传模糊的问题。Quic同时还带有收到数据包与发出ACK之间的时延信息。这些信息能够帮助更精确的计算rtt。此外，Quic的ACK Frame 支持256个NACK 区间，相比于TCP的SACK(Selective Acknowledgment)更弹性化，更丰富的信息会让client和server 哪些包已经被对方收到。</p>
<p>QUIC 的传输控制不再依赖内核的拥塞控制算法，而是实现在应用层上，这意味着我们根据不同的业务场景，实现和配置不同的拥塞控制算法以及参数。GOOGLE 提出的 BBR 拥塞控制算法与 CUBIC 是思路完全不一样的算法，在弱网和一定丢包场景，BBR 比 CUBIC 更不敏感，性能也更好。在 QUIC 下我们可以根据业务随意指定拥塞控制算法和参数，甚至同一个业务的不同连接也可以使用不同的拥塞控制算法。</p>
<p style=""><img alt="" src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(8)" style="position: relative; z-index: 2;"></p>
<p style="text-align:center;">图3-4 BBR拥塞弱网下算法效果对比</p>
<h2 class="toc-enable" id="mcegeo9wt"><br><strong>3.4 无队头阻塞</strong></h2>
<h3 class="toc-enable" id="mcesw7jv0v">3.4.1 TCP的队头阻塞问题</h3>
<p>虽然 HTTP2 实现了多路复用，但是因为其基于面向字节流的 TCP，因此一旦丢包，将会影响多路复用下的所有请求流。QUIC 基于 UDP，在设计上就解决了队头阻塞问题。</p>
<p>TCP 队头阻塞的主要原因是数据包超时确认或丢失阻塞了当前窗口向右滑动，我们最容易想到的解决队头阻塞的方案是不让超时确认或丢失的数据包将当前窗口阻塞在原地。QUIC也正是采用上述方案来解决TCP 队头阻塞问题的。</p>
<p>TCP 为了保证可靠性，使用了基于字节序号的 Sequence Number 及 Ack 来确认消息的有序到达。</p>
<p style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(9)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p style="text-align:center;">图3-5 HTTP2队头阻塞</p>
<p><br></p>
<p>如上图，应用层可以顺利读取stream1中的内容，但由于stream2中的第三个segment发生了丢包，TCP 为了保证数据的可靠性，需要发送端重传第 3 个 segment 才能通知应用层读取接下去的数据。所以即使stream3 stream4的内容已顺利抵达，应用层仍然无法读取，只能等待stream2中丢失的包进行重传。</p>
<p>在弱网环境下，HTTP2的队头阻塞问题在用户体验上极为糟糕。</p>
<p><br></p>
<h3 class="toc-enable" id="mceqyemlq8">3.4.2 QUIC的无队头阻塞解决方案</h3>
<p>QUIC 同样是一个可靠的协议，它使用 Packet Number 代替了 TCP 的 Sequence Number，并且每个 Packet Number 都严格递增，也就是说就算 Packet N 丢失了，重传的 Packet N 的 Packet Number 已经不是 N，而是一个比 N 大的值，比如Packet N+M。</p>
<p>QUIC 使用的Packet Number 单调递增的设计，可以让数据包不再像TCP 那样必须有序确认，QUIC 支持乱序确认，当数据包Packet N 丢失后，只要有新的已接收数据包确认，当前窗口就会继续向右滑动。待发送端获知数据包Packet N 丢失后，会将需要重传的数据包放到待发送队列，重新编号比如数据包Packet N+M 后重新发送给接收端，对重传数据包的处理跟发送新的数据包类似，这样就不会因为丢包重传将当前窗口阻塞在原地，从而解决了队头阻塞问题。那么，既然重传数据包的Packet N+M 与丢失数据包的Packet N 编号并不一致，我们怎么确定这两个数据包的内容一样呢？</p>
<p>QUIC使用Stream ID 来标识当前数据流属于哪个资源请求，这同时也是数据包多路复用传输到接收端后能正常组装的依据。重传的数据包Packet N+M 和丢失的数据包Packet N 单靠Stream ID 的比对一致仍然不能判断两个数据包内容一致，还需要再新增一个字段Stream Offset，标识当前数据包在当前Stream ID 中的字节偏移量。</p>
<p>有了Stream Offset 字段信息，属于同一个Stream ID 的数据包也可以乱序传输了（HTTP/2 中仅靠Stream ID 标识，要求同属于一个Stream ID 的数据帧必须有序传输），通过两个数据包的Stream ID 与 Stream Offset 都一致，就说明这两个数据包的内容一致。</p>
<p style=""><br><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(10)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p class="toc-enable" style="text-align:center;">图3-6 QUIC无队头阻塞</p>
<p class="toc-enable"><br></p>
<h1 class="toc-enable" id="mceoboj6o">四、QUIC协议组成</h1>
<p>QUIC 的 packet 除了个别报文比如 PUBLIC_RESET 和 CHLO，所有报文头部都是经过认证的，报文 Body 都是经过加密的。这样只要对 QUIC 报文任何修改，接收端都能够及时发现，有效地降低了安全风险。</p>
<p class="toc-enable">如图3-1所示，蓝色部分是 Stream Frame 的报文头部，有认证。紫色部分是报文内容，全部经过加密。</p>
<p class="toc-enable" style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(11)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p style="text-align:center;">图4-1 QUIC的协议组成</p>
<p><br></p>
<ul><li><strong><strong>Flags：</strong></strong>用于表示Connection ID长度、Packet Number长度等信息。</li>
<li><strong>Connection ID</strong>：客户端随机选择的最大长度为64位的无符号整数。但是，长度可以协商。</li>
<li><strong>QUIC Version</strong>：QUIC协议的版本号，32位的可选字段。如果Public Flag &amp; FLAG_VERSION != 0，这个字段必填。客户端设置Public Flag中的Bit0为1，并且填写期望的版本号。如果客户端期望的版本号服务端不支持，服务端设置Public Flag中的Bit0为1，并且在该字段中列出服务端支持的协议版本（0或者多个），并且该字段后不能有任何报文。</li>
<li><strong>Packet Number</strong>：长度取决于Public Flag中Bit4及Bit5两位的值，最大长度6字节。发送端在每个普通报文中设置Packet Number。发送端发送的第一个包的序列号是1，随后的数据包中的序列号的都大于前一个包中的序列号。</li>
<li><strong>Stream ID</strong>：用于标识当前数据流属于哪个资源请求</li>
<li><strong>Offset</strong>：标识当前数据包在当前Stream ID 中的字节偏移量</li>
</ul><p>QUIC报文的大小需要满足路径MTU的大小以避免被分片。当前QUIC在IPV6下的最大报文长度为1350，IPV4下的最大报文长度为1370</p>
<p><br></p>
<h1 id="cc190208-3407-a4a4-40fc-a16dfa566c69" class="toc-enable">五、QUIC一站式解决方案</h1>
<div>
<div class="document">
<h2 class="paragraph text-align-type-left pap-line-1.7 pap-line-rule-auto pap-spacing-before-0pt pap-spacing-after-0pt toc-enable" id="af53216c-4e5e-e02f-1231-5810097a3172">5.1 全链路加速（FLA） —— 移动端解决方案</h2>
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">在移动端侧，我们提供更加便捷使用QUIC协议的SDK（FLA），可结合加速节点开启HTTP3特性，快速实现最后一公里Last Mile网络传输的优化。</p>
<div>
<div class="document">
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt">产品详细介绍页：https://cloud.tencent.com/product/fla</p>
</div>

<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt" style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(12)" width="601" height="222" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt" style="text-align:center;">图5-1&nbsp; FLA</p>
<p class="paragraph text-align-type-left pap-line-1.3 pap-line-rule-auto pap-spacing-before-3pt pap-spacing-after-3pt"><br></p>
</div>

<h2 id="e5c30c12-ef43-5d68-9667-a11d535d1c4b" class="toc-enable">5.2 QUIC在CDN上的实践</h2>
<p>QUIC具有众多优点，它融合了UDP协议的速度、性能与TCP的安全与可靠，同时也解决了HTTP1、HTTP1.1、HTTP2中引入的一些缺点，大大优化了互联网传输体验。</p>
<p>CDN已全面支持开启QUIC访问。另外众所周知，quic的实现有多个版本，CDN也同时支持了多个版本的quic协议，可以最大化地满足不同业务类型的需求。</p>
<p>登录&nbsp;<a href="https://console.cloud.tencent.com/cdn" target="_blank" rel="noreferrer">CDN 控制台</a>&nbsp;成功添加域名后，可进入域名管理，切换 Tab 至&nbsp;<strong>HTTPS 配置</strong>，即可找到&nbsp;<strong>QUIC</strong>&nbsp;配置。</p>
<p style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(13)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p style="text-align:center;">图5-2 CDN QUIC配置</p>
<p>详细可以戳这个链接：<a href="https://cloud.tencent.com/document/product/228/51800" target="_blank" rel="noreferrer">https://cloud.tencent.com/document/product/228/51800</a></p>
<p><br></p>
<h2 class="toc-enable" id="74df4bd8-88e4-27aa-a51c-ad4f455f2351">5.3 QUIC效果对比</h2>
<p>QUIC协议的核心思想是将<strong>TCP协议在内核实现的诸如可靠传输、流量控制、拥塞控制等功能转移到用户态来实现</strong>，同时在加密传输方向的尝试也推动了TLS1.3的发展。</p>
<p>但是TCP协议的势力过于强大，很多网络设备甚至对于UDP数据包做了很多不友好的策略，进行拦截从而导致成功连接率下降。</p>
<p>主导者谷歌在自家产品做了很多尝试，国内公司也做了很多关于QUIC协议的尝试。对QUIC协议表现了很大的兴趣，并做了一些<strong>优化处理</strong>，在一些重点产品中对连接迁移、QUIC成功率、弱网环境耗时等进行了实验，给出了来自生产环境的诸多宝贵数据。</p>
<p>简单看一组在移动互联网场景下的不同丢包率下的请求耗时分布：</p>
<p style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(14)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p style="text-align:center;">图5-3 QUIC弱网络下的性能提升率</p>
<p style=""><img src="./HTTP3官宣！QUIC从端到云的一站式方案 -  CDN 团队 - KM平台_files/cos-file-url(15)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
<p style="text-align:center;">图5-4 QUIC弱网络下的性能提升率2</p>
<h2 id="f6cbdf36-dd75-e6dd-2450-421503f22ac8" class="toc-enable"><br>5.4 QUIC未来应用</h2>
<p>任何新生事物的推动都是需要时间的，出现多年的HTTP/2和HTTPS协议的普及度都没有预想高，IPv6也是如此，不过QUIC已经展现了强大的生命力，让我们看看它可能的应用场景都有哪些。</p>
<h3 id="04bac5cb-1ab3-0332-acdb-8204e7a57891" class="toc-enable">5.4.1 物联网（IoT)</h3>
<p>在物联网场景中，通信主要发生在设备和物联网平台之间，由于大部分物联网设备都是<strong>资源受限型设备</strong>，它们的物理资源和网络资源都非常有限，因此，物联网场景中主要使用的通信协议都是轻量级的，为资源受限环境而设计的通信协议，例如 CoAP/LWM2M 协议和 MQTT 协议。由于其局限性，HTTP可能不是IoT的首选协议，但是在某些应用程序中，基于HTTP的通信将会非常适合。对于从附属传感器收集数据的移动设备，QUIC-HTTP/3可以<strong>解决无线连接丢失的问题</strong>， 这种优势同样也很适合安装在汽车或其它移动设施上的物联网设备。&nbsp;</p>
<p><br></p>
<h3 id="874e9c24-11cf-3a7b-f762-3e4b23e96ba5" class="toc-enable">5.4.2 Web VR</h3>
<p>伴随浏览器功能的不断增强完善，内容格局与交互体验也随之发生变化，这种变化之一是<strong>基于Web的VR（虚拟现实）</strong>。当前VR仍处于起步阶段，VR在增强协作中发挥了举足轻重的作用，在VR丰富的交互流程和体验中，网络是至关重要的环节，所有信息都需要基于网络传导。<strong>VR应用程序需要依赖更多的带宽资源和更文档的网络连接</strong>，来呈现虚拟场景的复杂细节，这将受益于QUIC的演进和普及。</p>
<p><br></p>
<h3 id="8f4ccdd4-231d-7298-381d-4965f0a3edc7" class="toc-enable">5.4.3 移动直播</h3>
<p>随着互联网的发展和互联网应用类型的丰富, 移动直播相关产业也在高速发展。移动直播这一特殊应用场景<strong>对网络传输性能要求极高</strong>，因此应用开发和调优都较为困难。使用 QUIC 改善直播体验，在丢包和网络延迟严重的情况下仍可提供可用的服务，并优化卡顿率、请求失败率、秒开率、提高连接成功率等传输指标; 连接可靠性强，支持页面资源数较多、并发连接数较多情况下的访问速率提升。</p>
<p><br></p>
<h1 class="toc-enable" id="mcelp6qyo">参考</h1>
<ul><li><a href="https://mp.weixin.qq.com/s?__biz=MzIzNjUxMzk2NQ==&amp;mid=2247501925&amp;idx=1&amp;sn=5bec81739040f0c6bf844e2ab877048c&amp;chksm=e8d437a7dfa3beb19cccca6dddaa7a9ed6d2395576702b52c21cdc3100f29617c215d99b4fca&amp;mpshare=1&amp;scene=1&amp;srcid=0303jyzNPWUpyKn4s8fZj6eW&amp;sharer_sharetime=1614737763782&amp;sharer_shareid=0cd65f7f398401a991092e2cd18a8b64&amp;version=3.1.0.2353&amp;platform=mac#rd" target="_blank" rel="noreferrer">QUIC 在 Facebook 是如何部署的？</a></li>
<li><a href="https://mp.weixin.qq.com/s?__biz=MjM5ODYwMjI2MA==&amp;mid=2649756393&amp;idx=1&amp;sn=1202bd71cfa837395b48f43d0943c484&amp;chksm=becc819289bb088441f2f65c6e98ebc6816e10318ae1ec13d43cc999656989efe919cc47753e&amp;mpshare=1&amp;scene=1&amp;srcid=0302NNKNLSd3dP1KkjHlO2jl&amp;sharer_sharetime=1614737748553&amp;sharer_shareid=0cd65f7f398401a991092e2cd18a8b64&amp;version=3.1.0.2353&amp;platform=mac#rdhttps://cloud.tencent.com/developer/article/1594468" target="_blank" rel="noreferrer">STGW 下一代互联网标准传输协议QUIC大规模运营之路</a></li>
<li><a href="https://cloud.tencent.com/developer/article/1594468" target="_blank" rel="noreferrer">QUIC 0-RTT实现简析及一种分布式的0-RTT实现方案</a></li>
<li><a href="https://zhuanlan.zhihu.com/p/32553477" target="_blank" rel="noreferrer">科普：QUIC协议原理分析</a></li>
<li><a href="https://atoonk.medium.com/tcp-bbr-exploring-tcp-congestion-control-84c9c11dc3a9" target="_blank" rel="noreferrer">TCP BBR - Exploring TCP congestion control</a></li>
<li><a href="https://zhuanlan.zhihu.com/p/146473513" target="_blank" rel="noreferrer">浅谈QUIC协议原理与性能分析及部署方案</a></li>
<li><a href="https://blog.csdn.net/m0_37621078/article/details/106506532" target="_blank" rel="noreferrer">QUIC 是如何解决TCP 性能瓶颈的？</a></li>
<li><a href="https://nolaaaaa.github.io/2019/04/11/QUIC%E5%8D%8F%E8%AE%AE-%E5%92%8C-TCP-UDP-%E5%8D%8F%E8%AE%AE/" target="_blank" rel="noreferrer">QUIC协议 和 TCP/UDP 协议</a></li>
<li><a href="https://blog.csdn.net/u014023993/article/details/86432341" target="_blank" rel="noreferrer">QUIC的那些事 | 包类型及格式</a></li>
<li><a href="https://zhuanlan.zhihu.com/p/311221111" target="_blank" rel="noreferrer">跟坚哥学QUIC系列：连接迁移（Connection Migration)</a></li>
</ul>				</div>
