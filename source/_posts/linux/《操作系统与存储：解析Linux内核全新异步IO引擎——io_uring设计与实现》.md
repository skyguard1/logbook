---
title: "《操作系统与存储：解析Linux内核全新异步IO引擎——io_uring设计与实现》"
date: 2022-06-17 08:30:33
categories:
  - linux
---

<h1 id="引言">引言</h1>

<p>存储场景中，我们对性能的要求非常高。在存储引擎底层的IO技术选型时，可能会有如下讨论关于IO的讨论。</p>

<blockquote>
<p>A consideration of linux native aio/POSIX aio in a conversation:<br>
<a href="http://davmac.org/davpage/linux/async-io.html" target="_blank">http://davmac.org/davpage/linux/async-io.html</a><br>
So from the above documentation, it seems that Linux doesn’t have a true async file I/O that is not blocking (AIO, Epoll or POSIX AIO are all broken in some ways). I wonder if tlinux has any remedy. We should reach out to tlinux experts to get their opinions.</p>
</blockquote>

<ol>
<li>这是在讨论什么，为何会有此番考虑？</li>
<li>有没有更好的解决方案？</li>
<li>更好的解决方案是通过怎样的设计和实现解决问题？</li>
<li>…</li>
</ol>

<p>2019年，Linux Kernel正式进入5.x时代，众多新特性中与存储最密切相关的就是最新的IO引擎——io_uring。从一些性能测试来看，得出来的结论是性能远高于AIO方式，带来了巨大的性能提升，这对当前异步IO领域是一个big news。</p>

<ol>
<li>对于问题1，本文简述了Linux过往的的IO发展历程，同步IO接口、原生异步IO接口AIO的缺陷，为何原有方式存在缺陷。</li>
<li>对于问题2，本文从设计出发，介绍了最新的IO引擎io_uring的相关内容。</li>
<li>对于问题3，本文深入最新版内核linux-5.10中解析了io_uring的设计与大体实现（关键数据结构、流程、特性实现等）。</li>
<li>…</li>
</ol>

<h1 id="一切过往-皆为序章">一切过往，皆为序章</h1>

<p>以史为镜，可以知兴替。我们先看看现存过往IO接口的缺陷。</p>

<h2 id="过往同步IO接口">过往同步IO接口</h2>

<p>当前Linux对文件的操作有很多种方式，过往同步IO接口，从功能上划分，大体分为以下几种。</p>

<ul>
<li>原始版本</li>
<li>offset版本</li>
<li>向量版本</li>
<li>offset+向量版本</li>
</ul>

<h3 id="read-write">read，write</h3>

<p>最原始的文件IO系统调用就是read，write</p>

<p>read系统调用从文件描述符所指代的打开文件中读取数据。</p>

<p>read简单介绍：</p>

<pre class="  language-txt" style="position: relative; z-index: 2;"><code class="prism  language-txt">NAME
    read - read from a file descriptor
SYNOPSIS
    #include &lt;unistd.h&gt;

    ssize_t read(int fd, void *buf, size_t count);
DESCRIPTION
    read() attempts to read up to count bytes from file descriptor fd
    into the buffer starting at buf.

    On files that support seeking, the read operation commences at the
    file offset, and the file offset is incremented by the number of
    bytes read.  If the file offset is at or past the end of file, no
    bytes are read, and read() returns zero.

    If count is zero, read() may detect the errors described below.  In
    the absence of any errors, or if read() does not check for errors, a
    read() with a count of 0 returns zero and has no other effects.

    According to POSIX.1, if count is greater than SSIZE_MAX, the result
    is implementation-defined; see NOTES for the upper limit on Linux.
</code></pre>

<p>write系统调用将数据写入一个已打开的文件中。</p>

<p>write简单介绍：</p>

<pre class="  language-txt" style="position: relative; z-index: 2;"><code class="prism  language-txt">NAME
    write - write to a file descriptor
SYNOPSIS
    #include &lt;unistd.h&gt;

    ssize_t write(int fd, const void *buf, size_t count);
DESCRIPTION
    write() writes up to count bytes from the buffer starting at buf to
    the file referred to by the file descriptor fd.

    The number of bytes written may be less than count if, for example,
    there is insufficient space on the underlying physical medium, or the
    RLIMIT_FSIZE resource limit is encountered (see setrlimit(2)), or the
    call was interrupted by a signal handler after having written less
    than count bytes.  (See also pipe(7).)

    For a seekable file (i.e., one to which lseek(2) may be applied, for
    example, a regular file) writing takes place at the file offset, and
    the file offset is incremented by the number of bytes actually
    written.  If the file was open(2)ed with O_APPEND, the file offset is
    first set to the end of the file before writing.  The adjustment of
    the file offset and the write operation are performed as an atomic
    step.

    POSIX requires that a read(2) that can be proved to occur after a
    write() has returned will return the new data.  Note that not all
    filesystems are POSIX conforming.

    According to POSIX.1, if count is greater than SSIZE_MAX, the result
    is implementation-defined; see NOTES for the upper limit on Linux.
</code></pre>

<h3 id="在文件特定偏移处的IO-pread-pwrite">在文件特定偏移处的IO：pread，pwrite</h3>

<p>在多线程环境下，为了保证线程安全，需要保证下列操作的原子性。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">    off_t orig<span class="token punctuation">;</span>
    orig <span class="token operator">=</span> lseek<span class="token punctuation">(</span>fd<span class="token punctuation">,</span> <span class="token number">0</span><span class="token punctuation">,</span> SEEK_CUR<span class="token punctuation">)</span><span class="token punctuation">;</span> <span class="token operator">//</span> Save current offset
    lseek<span class="token punctuation">(</span>fd<span class="token punctuation">,</span> offset<span class="token punctuation">,</span> SEEK_SET<span class="token punctuation">)</span><span class="token punctuation">;</span>
    s <span class="token operator">=</span> read<span class="token punctuation">(</span>fd<span class="token punctuation">,</span> buf<span class="token punctuation">,</span> <span class="token builtin">len</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
    lseek<span class="token punctuation">(</span>fd<span class="token punctuation">,</span> orig<span class="token punctuation">,</span> SEEK_SET<span class="token punctuation">)</span><span class="token punctuation">;</span> <span class="token operator">//</span> Restore original <span class="token builtin">file</span> offset
</code></pre>

<p>让使用者来保证原子性较繁，从接口上就有保证是一个好的选择，后来出现的pread实现了这一点。</p>

<p>与read, write类似，pread, pwrite调用时可以指定位置进行文件IO操作，而非始于文件的当前偏移处，且他们不会改变文件的当前偏移量。这种方式，减少了编码，并提高了代码的健壮性。</p>

<pre class="  language-txt" style="position: relative; z-index: 2;"><code class="prism  language-txt">NAME
       pread,  pwrite  -  read from or write to a file descriptor at a given
       offset
SYNOPSIS
       #include &lt;unistd.h&gt;

       ssize_t pread(int fd, void *buf, size_t count, off_t offset);

       ssize_t pwrite(int fd, const void *buf, size_t count, off_t offset);

DESCRIPTION
       pread() reads up to count bytes from file descriptor fd at offset
       offset (from the start of the file) into the buffer starting at buf.
       The file offset is not changed.

       pwrite() writes up to count bytes from the buffer starting at buf to
       the file descriptor fd at offset offset.  The file offset is not
       changed.

       The file referenced by fd must be capable of seeking.
</code></pre>

<p>当然，往read，write接口参数的标志位集合中加入新标志，用以表征新逻辑，可能达到相同的效果，但是这可能不够优雅——如果某个参数有多种可能的值，而函数内又以条件表达式检查这些参数值，并根据不同参数值做出不同的行为，那么以明确函数取代参数（Replace Parameter with Explicit Methods）也是一种合适的重构手法。</p>

<p>如果需要反复执行lseek，并伴之以文件IO，那么pread和pwrite系统调用在某些情况下是具有性能优势的。这是因为执行单个pread或pwrite系统调用的成本要低于执行lseek和read/write两个系统调用（当然，相对地，执行实际IO的开销通常要远大于执行系统调用，系统调用的性能优势作用有限）。历史上，一些数据库，通过使用kernel的这一新接口，获得了不菲的收益。如PostgreSQL：<a href="https://www.postgresql-archive.org/PATCH-Using-pread-instead-of-lseek-with-analysis-td2215257.html" target="_blank"><em>[PATCH] Using pread instead of lseek (with analysis)</em></a></p>

<h3 id="分散输入和集中输出-Scatter-Gather-IO--readv--writev">分散输入和集中输出（Scatter-Gather IO）：readv, writev</h3>

<p>“物质的组成与结构决定物质的性质，性质决定用途，用途体现性质。”是自然科学的重要思想，在计算机科学中也是如此。现有计算机体系结构下，数据存储由一个或多个基本单元组成，物理、逻辑上的结构，决定了数据存储的性质——可能是连续的，也可能是不连续的。</p>

<p>对于不连续的数据的处理相对较繁，例如，使用read将数据读到不连续的内存，使用write将不连续的内存发送出去。<br>
更具体地看，如果要从文件中读一片连续的数据至进程的不同区域，有两种方案：</p>

<ol>
<li>使用read一次将它们读至一个较大的缓冲区中，然后将它们分成若干部分复制到不同的区域。</li>
<li>调用read若干次分批将它们读至不同区域。</li>
</ol>

<p>同样地，如果想将程序中不同区域的数据块连续地写至文件，也必须进行类似的处理。而且这种方案需要多次调用read、write系统调用，有损性能。</p>

<p>那么如何简化编程，如何解决这种开销呢？可以使用特定的数据结构对非连续的数据进行管理，批量传输数据，这样就能解决上述问题。从接口上就有此保证是一个好的选择，后来出现的readv，writev实现了这一点。</p>

<p>这种基于向量的，分散输入和集中输出的系统调用并非只对单个缓冲区进行读写操作，而是一次即可传输多个缓冲区的数据，免除了多次系统调用的开销。数组iov定义了一组用来传输数据的缓冲区。整形数iovcnt则指定了iov的成员个数。iov中的每个成员都是如下形式的数据结构。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">struct iovec <span class="token punctuation">{</span>
   void  <span class="token operator">*</span>iov_base<span class="token punctuation">;</span>    <span class="token operator">/</span><span class="token operator">*</span> Starting address <span class="token operator">*</span><span class="token operator">/</span>
   size_t iov_len<span class="token punctuation">;</span>     <span class="token operator">/</span><span class="token operator">*</span> Number of <span class="token builtin">bytes</span> to transfer <span class="token operator">*</span><span class="token operator">/</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<h4 id="功能交集-preadv-pwritev">功能交集：preadv，pwritev</h4>

<p>上述两种功能都是一种进步，不过似乎没有合二为一。那么是否能进两步呢？</p>

<p>数学上，集合是指具有某种特定性质的具体的或抽象的对象汇总而成的集体。其中，构成集合的这些对象则称为该集合的元素。我这里将接口定义成一种集合，一种特定功能就是其中的一个元素。根据已知有限集构造一个子集，该子集对于每一个元素要么包含要么不包含，那么根据乘法原理，这个子集共有2^N 种构造方式，即有2^N个子集。这么多可能的集合，显然较繁。基于场景对于功能子集的需求、元素之间的容斥、集合中元素是否需要有序（接口层面对功能的表现）、简约性等因素，我们会确立一些优雅的接口，这也是函数接口设计的一个哲学话题。</p>

<p>后来出现的preadv，pwritev，是偏移和向量的交集，不仅支持向量的，而且支持offset。</p>

<h4 id="带标志位集合的IO-preadv2-pwritev2">带标志位集合的IO：preadv2，pwritev2</h4>

<p>后来还出现了变种函数preadv2和pwritev2，相比较preadv，pwritev，v2版本还能设置本次IO的标志，比如RWF_DSYNC、RWF_HIPRI、RWF_SYNC、RWF_NOWAIT、RWF_APPEND。</p>

<pre class="  language-txt" style="position: relative; z-index: 2;"><code class="prism  language-txt">NAME
    readv,  writev,  preadv,  pwritev,  preadv2, pwritev2 - read or write
       data into multiple buffers

SYNOPSIS
    #include &lt;sys/uio.h&gt;

   ssize_t readv(int fd, const struct iovec *iov, int iovcnt);

   ssize_t writev(int fd, const struct iovec *iov, int iovcnt);

   ssize_t preadv(int fd, const struct iovec *iov, int iovcnt,
                  off_t offset);

   ssize_t pwritev(int fd, const struct iovec *iov, int iovcnt,
                   off_t offset);

   ssize_t preadv2(int fd, const struct iovec *iov, int iovcnt,
                   off_t offset, int flags);

   ssize_t pwritev2(int fd, const struct iovec *iov, int iovcnt,
                    off_t offset, int flags);

DESCRIPTION
   The readv() system call reads iovcnt buffers from the file associated
       with the file descriptor fd into the buffers described by iov
       ("scatter input").

       The writev() system call writes iovcnt buffers of data described by
       iov to the file associated with the file descriptor fd ("gather
       output").

       The pointer iov points to an array of iovec structures, defined in
       &lt;sys/uio.h&gt; as:

           struct iovec {
               void  *iov_base;    /* Starting address */
               size_t iov_len;     /* Number of bytes to transfer */
           };

       The readv() system call works just like read(2) except that multiple
       buffers are filled.

       The writev() system call works just like write(2) except that multi‐
       ple buffers are written out.

       Buffers are processed in array order.  This means that readv() com‐
       pletely fills iov[0] before proceeding to iov[1], and so on.  (If
       there is insufficient data, then not all buffers pointed to by iov
       may be filled.)  Similarly, writev() writes out the entire contents
       of iov[0] before proceeding to iov[1], and so on.

       The data transfers performed by readv() and writev() are atomic: the
       data written by writev() is written as a single block that is not in‐
       termingled with output from writes in other processes (but see
       pipe(7) for an exception); analogously, readv() is guaranteed to read
       a contiguous block of data from the file, regardless of read opera‐
       tions performed in other threads or processes that have file descrip‐
       tors referring to the same open file description (see open(2)).

   preadv() and pwritev()
       The preadv() system call combines the functionality of readv() and
       pread(2).  It performs the same task as readv(), but adds a fourth
       argument, offset, which specifies the file offset at which the input
       operation is to be performed.

       The pwritev() system call combines the functionality of writev() and
       pwrite(2).  It performs the same task as writev(), but adds a fourth
       argument, offset, which specifies the file offset at which the output
       operation is to be performed.

       The file offset is not changed by these system calls.  The file re‐
       ferred to by fd must be capable of seeking.

   preadv2() and pwritev2()
       These system calls are similar to preadv() and pwritev() calls, but
       add a fifth argument, flags, which modifies the behavior on a per-
       call basis.

       Unlike preadv() and pwritev(), if the offset argument is -1, then the
       current file offset is used and updated.

       The flags argument contains a bitwise OR of zero or more of the fol‐
       lowing flags:

       RWF_DSYNC (since Linux 4.7)
              Provide a per-write equivalent of the O_DSYNC open(2) flag.
              This flag is meaningful only for pwritev2(), and its effect
              applies only to the data range written by the system call.

       RWF_HIPRI (since Linux 4.6)
              High priority read/write.  Allows block-based filesystems to
              use polling of the device, which provides lower latency, but
              may use additional resources.  (Currently, this feature is us‐
              able only on a file descriptor opened using the O_DIRECT
              flag.)

       RWF_SYNC (since Linux 4.7)
              Provide a per-write equivalent of the O_SYNC open(2) flag.
              This flag is meaningful only for pwritev2(), and its effect
              applies only to the data range written by the system call.

       RWF_NOWAIT (since Linux 4.14)
              Do not wait for data which is not immediately available.  If
              this flag is specified, the preadv2() system call will return
              instantly if it would have to read data from the backing stor‐
              age or wait for a lock.  If some data was successfully read,
              it will return the number of bytes read.  If no bytes were
              read, it will return -1 and set errno to EAGAIN.  Currently,
              this flag is meaningful only for preadv2().

       RWF_APPEND (since Linux 4.16)
              Provide a per-write equivalent of the O_APPEND open(2) flag.
              This flag is meaningful only for pwritev2(), and its effect
              applies only to the data range written by the system call.
              The offset argument does not affect the write operation; the
              data is always appended to the end of the file.  However, if
              the offset argument is -1, the current file offset is updated.
</code></pre>

<h2 id="同步IO接口的缺陷">同步IO接口的缺陷</h2>

<p>这类接口，尽管形式多种多样，但它们都有一个共同的特征，就是同步，即在读写IO时，系统调用会阻塞住等待，在数据读取或写入后才返回结果。</p>

<p>对于传统的普通的编程模型，这类同步接口编程简单，且结果可以预测，倒也无妨。但是在要求高效的场景下，同步导致的后果就是caller 在阻塞的同时无法继续执行其他的操作，只能等待IO结果返回，其实caller本可以利用这段时间继续往后执行。例如，一个 ftp 服务器，当接收到客户机上传的文件，然后将文件写入到本机的过程中，若ftp服务程序忙于等待文件读写结果的返回，则会拒绝其他此刻正需要连接的客户机请求。显然，在这种场景下，更好的方式是采用异步编程模型，如在上述例子中，当服务器接收到某个客户机上传文件后，直接、无阻塞地将写入IO的buffer 提交给内核，然后caller继续接受下一个客户请求，内核处理完IO之后，主动调用某种通知机制，告诉caller该IO已完成，完成状态保存在某位置，请查看。</p>

<p>所以，我们需要异步IO。</p>

<h2 id="AIO">AIO</h2>

<p>由上可见，仅同步IO有一定的局限性，我们还需要异步IO。后来应这类场景的诉求，产生了异步IO接口，即Linux Native异步IO——AIO。</p>

<p>历史上，一些项目通过使用kernel的这一新接口，获得了不菲的收益。</p>

<p>高性能服务器nginx就使用了这样的机制，nginx把读取文件的操作异步地提交给内核后，内核会通知IO设备独立地执行操作，这样，nginx进程可以继续充分地占用CPU。而且，当大量读事件堆积到IO设备的队列中时，将会发挥出内核中“电梯算法”的优势，从而降低随机读取磁盘扇区的成本。</p>

<h2 id="AIO的缺陷">AIO的缺陷</h2>

<p>但是它仍然不够完美，同样存在很多缺陷，还是以nginx为例，目前，nginx仅支持在读取文件时使用AIO，因为正常写入文件往往是写入内存就立刻返回，效率很高，如果替换成AIO写入速度会明显下降。</p>

<p>这是因为AIO不支持缓存操作，即使需要操作的文件块在linux文件缓存中存在，也不会通过操作缓存中的文件块来代替实际对磁盘的操作，这可能降低实际处理的性能。需要看具体的使用场景，如果大部分用户请求对文件操作都会落到文件缓存中，那么使用AIO可能不是一个好的选择，需要实际测试。</p>

<p style=""><img src="./《操作系统与存储：解析Linux内核全新异步IO引擎——io_uring设计与实现》 - 社交平台产品部 - KM平台_files/cos-file-url(2)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>以上是AIO的不足之一，分析AIO缘何不足，需要较大的篇幅，这里按下不表直接总结结论。</p>

<ul>
<li><strong>仅支持direct IO</strong>。在采用AIO的时候，只能使用O_DIRECT，不能借助文件系统缓存来缓存当前的IO请求，还存在size对齐（直接操作磁盘，所有写入内存块数量必须是文件系统块大小的倍数，而且要与内存页大小对齐。）等限制，直接影响了aio在很多场景的使用。</li>
<li><strong>仍然可能被阻塞。语义不完备</strong>。即使应用层主观上，希望系统层采用异步IO，但是客观上，有时候还是可能会被阻塞。io_getevents(2)调用read_events读取AIO的完成events，read_events中的wait_event_interruptible_hrtimeout等待aio_read_events，如果条件不成立（events未完成）则调用__wait_event_hrtimeout进入睡眠（当然，支持用户态设置最大等待时间）。</li>
<li><strong>拷贝开销大</strong>。每个IO提交需要拷贝64+8字节，每个IO完成需要拷贝32字节，总共104字节的拷贝。这个拷贝开销是否可以承受，和单次IO大小有关：如果需要发送的IO本身就很大，相较之下，这点消耗可以忽略，而在大量小IO的场景下，这样的拷贝影响比较大。</li>
<li><strong>API不友好</strong>。每一个IO至少需要两次系统调用才能完成（submit和wait-for-completion)，需要非常小心地使用完成事件以避免丢事件。</li>
<li><strong>系统调用开销大</strong>。也正是因为上一条，io_submit/io_getevents造成了较大的系统调用开销，在存在spectre/meltdown（CPU熔断幽灵漏洞，CVE-2017-5754）的机器上，若如果要避免漏洞问题，系统调用性能则会大幅下降。在存储场景下，高频系统调用的性能影响较大。</li>
</ul>

<p>软件工程中，在现有接口基础上改进，相比新开发一套接口，往往有着更多的优势，然而在过去的数年间，针对上述限制的很多改进努力都未尽如人意。</p>

<p>终于，全新的异步IO引擎io_uring就在这样的环境下诞生了。</p>

<h1 id="设计--应该是什么样子">设计——应该是什么样子</h1>

<p>我曾听志超兄说过如此一句：“Linux应该是什么样子，它现在就是什么样子。”，它并不是类似于“存在即合理”这样的谬传，而是对Linux系统优雅哲学的高度概括，同时也是对开源自由软件精神的肯定——因为自始至终都是自由的，所以大家觉得应该是什么样子（哪里有缺陷，哪里不够优雅），大家就会自由地去修改它，所以，经过时代的发展，它的面貌与大家所期望的最相符，即众人拾柴，众望所归。</p>

<p>以后世上可能会有无数文章讲述io_uring是什么样子，我们先看看它应该是什么样子。</p>

<h2 id="设计原则">设计原则</h2>

<p>既然是全新实现，那么一个好的设计很重要。我们甚至可以不囿于问题，思考应该是什么样子。</p>

<p>如上所述，历史实现在一定场景下，会有一定问题，新实现理应解决这些问题。反思既往问题，可知新实现需要遵循一定原则。</p>

<ul>
<li>简单：接口需要足够简单，这一点不言自明。</li>
<li>易用：同时需要足够克制，保持易于理解。对于使用者来说，就不容易误用，是一种有效的助推。（之所以如上没有采用“简单易用”这样的惯用语，是因为简单并不一定意味着易用。我们尽量避免这种不合逻辑的隐喻。）</li>
<li>可扩展：接口要有足够的扩展性，尽管某个接口是为了某种场景（如存储）而建立，但是我们需要面向未来，若有朝一日需要支持非阻塞设备（非块存储）以及网络I/O时，这里不应是桎梏。</li>
<li>特性丰富：当然，接口需要支持足够丰富的功能。</li>
<li>高效：在存储场景下，高效率始终是关键目标。</li>
<li>可伸缩性：满足峰值场景的性能需要（高效和低延迟很重要，但是峰值速率对于存储设备来讲也很重要。）底层软件是基于硬件建构的，为了适应新硬件的要求，接口还需要考虑到伸缩性。</li>
</ul>

<p>另外，因为我们的部分目标之间，本质上往往是存在一定互斥性的（如可伸缩与足够简单互斥、特性丰富与高效互斥）很难同时满足，所以，我们设计时也需要权衡。其中，io_uring始终需要围绕高效进行设计。</p>

<h2 id="实现思路">实现思路</h2>

<h3 id="解决-系统调用开销大-的问题">解决“系统调用开销大”的问题</h3>

<p>针对这个问题，考虑是否每次都需要系统调用。如果能将多次系统调用中的逻辑放到有限次数中来，就能将消耗降为常数时间复杂度。</p>

<h3 id="解决-拷贝开销大-的问题">解决“拷贝开销大”的问题</h3>

<p>之所以在提交和完成事件中存在内存拷贝，是因为应用程序和内核之间的通信需要拷贝数据，所以为了避免这个问题，需要重新考量应用与内核间的通信方式。我们发现，两者通信，不是必须要拷贝，通过现有技术，可以让应用与内核共享内存，用于彼此通信，需要生产者-消费者模型。</p>

<p>要实现核外与内核的一个零拷贝，最佳的方式就是实现一块内存映射区域，两者共享一段内存，核外往这段内存写数据，然后通知内核使用这段内存数据，或者内核填写这段数据，核外使用这部分数据。因此我们需要一对共享的ring buffer用于应用程序和内核之间的通信。</p>

<p>共享ring buffer的设计主要带来以下几个好处：</p>

<ul>
<li>提交、完成请求时节省应用和内核之间的内存拷贝</li>
<li>使用 SQPOLL 高级特性时，应用程序无需调用系统调用</li>
<li>无锁操作，用memory ordering实现同步，通过几个简单的头尾指针的移动就可以实现快速交互。</li>
</ul>

<p>一块用于核外传递数据给内核，一块是内核传递数据给核外，一方只读，一方只写。</p>

<ul>
<li>提交队列SQ(submission queue)中，应用是IO提交的生产者（producer），内核是消费者（consumer）。</li>
<li>完成队列CQ(completion queue)中，内核是完成事件的生产者，应用是消费者。</li>
</ul>

<p>内核控制SQ ring的head和CQ ring的tail，应用程序控制SQ ring的tail和CQ ring的head</p>

<p style=""><img src="./《操作系统与存储：解析Linux内核全新异步IO引擎——io_uring设计与实现》 - 社交平台产品部 - KM平台_files/cos-file-url(3)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>那么他们分别需要保存的是什么数据呢？<br>
假设A缓存区为核外写，内核读，就是将IO数据写到这个缓存区，然后通知内核来读；再假设B缓存区为内核写，核外读，他所承担的责任就是返回完成状态，标记A缓存区的其中一个entry的完成状态为成功或者失败等信息。</p>

<h3 id="解决-API不友好-的问题">解决“API不友好”的问题</h3>

<p>问题在于需要多个系统调用才能完成，考虑是否可以把多个系统调用合而为一。</p>

<p>你可能会想到，这与上文所说的重构手法相悖，即以明确函数取代参数（Replace Parameter with Explicit Methods）——如果某个参数有多种可能的值，而函数内又以条件表达式检查这些参数值，并根据不同参数值做出不同的行为。</p>

<p>然而，手法只是手法，选择具体的重构手法需要遵循重构原则。在不同场景下，相反地，令函数携带参数（Parameterize Method）可能是一个好的选择。</p>

<p>话说天下大势，分久必合，合久必分。你可能会发现这样的两个函数，它们做着类似的工作，但因少数几个值致使行为略有不同。在这种情况下，你可以将这些各自分离的函数统一起来，并通过参数来处理那些变化情况，用以简化问题。这样的修改可以去除重复代码，并提高灵活性，因为你可以用这个参数处理更多的变化情况。</p>

<p>也许你会发现，你无法用这种办法处理整个函数，但可以处理函数中的一部分代码。这种情况下，你应该首先将这部分代码提炼到一个独立函数中，然后再对那个提炼所得的函数使用令函数携带参数（Parameterize Method）。</p>

<h1 id="实现--现在是什么样子">实现——现在是什么样子</h1>

<p>推导完了应该是什么样子，解析一下现在是什么样子。</p>

<h2 id="关键数据结构">关键数据结构</h2>

<p>程序等于数据结构加算法，这里先解析io_uring有哪些关键数据结构。</p>

<h3 id="io_uring-io_rings结构">io_uring、io_rings结构</h3>

<p>结构前面是一些标志位集合和掩码，尾部是一个柔性数组。这两个数据在前面使用mmap分配内存的时候，对应到了不同的offset，即前面IORING_OFF_SQ_RING、IORING_OFF_CQ_RING和IORING_OFF_SQES的预定于的值。</p>

<p>其中io_rings结构中sq, cq成员，分别代表了提交的请求的ring和已经完成的请求返回结构的ring。io_uring结构中是head和tail，用于控制队列中的头尾索引。即前文提到的，内核控制SQ ring的head和CQ ring的tail，应用程序控制SQ ring的tail和CQ ring的head。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token punctuation">{</span>
	u32 head ____cacheline_aligned_in_smp<span class="token punctuation">;</span>
	u32 tail ____cacheline_aligned_in_smp<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>

<span class="token comment">/*
 * This data is shared with the application through the mmap at offsets
 * IORING_OFF_SQ_RING and IORING_OFF_CQ_RING.
 *
 * The offsets to the member fields are published through struct
 * io_sqring_offsets when calling io_uring_setup.
 */</span>
<span class="token keyword">struct</span> <span class="token class-name">io_rings</span> <span class="token punctuation">{</span>
	<span class="token comment">/*
	 * Head and tail offsets into the ring; the offsets need to be
	 * masked to get valid indices.
	 *
	 * The kernel controls head of the sq ring and the tail of the cq ring,
	 * and the application controls tail of the sq ring and the head of the
	 * cq ring.
	 */</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_uring</span>		sq<span class="token punctuation">,</span> cq<span class="token punctuation">;</span>
	<span class="token comment">/*
	 * Bitmasks to apply to head and tail offsets (constant, equals
	 * ring_entries - 1)
	 */</span>
	u32			sq_ring_mask<span class="token punctuation">,</span> cq_ring_mask<span class="token punctuation">;</span>
	<span class="token comment">/* Ring sizes (constant, power of 2) */</span>
	u32			sq_ring_entries<span class="token punctuation">,</span> cq_ring_entries<span class="token punctuation">;</span>
	<span class="token comment">/*
	 * Number of invalid entries dropped by the kernel due to
	 * invalid index stored in array
	 *
	 * Written by the kernel, shouldn't be modified by the
	 * application (i.e. get number of "new events" by comparing to
	 * cached value).
	 *
	 * After a new SQ head value was read by the application this
	 * counter includes all submissions that were dropped reaching
	 * the new SQ head (and possibly more).
	 */</span>
	u32			sq_dropped<span class="token punctuation">;</span>
	<span class="token comment">/*
	 * Runtime SQ flags
	 *
	 * Written by the kernel, shouldn't be modified by the
	 * application.
	 *
	 * The application needs a full memory barrier before checking
	 * for IORING_SQ_NEED_WAKEUP after updating the sq tail.
	 */</span>
	u32			sq_flags<span class="token punctuation">;</span>
	<span class="token comment">/*
	 * Runtime CQ flags
	 *
	 * Written by the application, shouldn't be modified by the
	 * kernel.
	 */</span>
	u32                     cq_flags<span class="token punctuation">;</span>
	<span class="token comment">/*
	 * Number of completion events lost because the queue was full;
	 * this should be avoided by the application by making sure
	 * there are not more requests pending than there is space in
	 * the completion queue.
	 *
	 * Written by the kernel, shouldn't be modified by the
	 * application (i.e. get number of "new events" by comparing to
	 * cached value).
	 *
	 * As completion events come in out of order this counter is not
	 * ordered with any other data.
	 */</span>
	u32			cq_overflow<span class="token punctuation">;</span>
	<span class="token comment">/*
	 * Ring buffer of completion events.
	 *
	 * The kernel writes completion events fresh every time they are
	 * produced, so the application is allowed to modify pending
	 * entries.
	 */</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_uring_cqe</span>	cqes<span class="token punctuation">[</span><span class="token punctuation">]</span> ____cacheline_aligned_in_smp<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<h3 id="Submission-Queue-Entry单元数据结构">Submission Queue Entry单元数据结构</h3>

<p>Submission Queue（下称SQ）是提交队列，核外写内核读的地方。Submission Queue Entry（下称SQE），即提交队列中的条目，队列由一个个条目组成。</p>

<p>描述一个SQE会复杂很多，不仅是因为要描述更多的信息，也是因为可扩展性这一设计原则。</p>

<p>我们需要操作码、标志集合、关联文件描述符、地址、偏移量，另外地，可能还需要表示优先级。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token comment">/*
 * IO submission data structure (Submission Queue Entry)
 */</span>
<span class="token keyword">struct</span> <span class="token class-name">io_uring_sqe</span> <span class="token punctuation">{</span>
	__u8	opcode<span class="token punctuation">;</span>		<span class="token comment">/* type of operation for this sqe */</span>
	__u8	flags<span class="token punctuation">;</span>		<span class="token comment">/* IOSQE_ flags */</span>
	__u16	ioprio<span class="token punctuation">;</span>		<span class="token comment">/* ioprio for the request */</span>
	__s32	fd<span class="token punctuation">;</span>		<span class="token comment">/* file descriptor to do IO on */</span>
	<span class="token keyword">union</span> <span class="token punctuation">{</span>
		__u64	off<span class="token punctuation">;</span>	<span class="token comment">/* offset into file */</span>
		__u64	addr2<span class="token punctuation">;</span>
	<span class="token punctuation">}</span><span class="token punctuation">;</span>
	<span class="token keyword">union</span> <span class="token punctuation">{</span>
		__u64	addr<span class="token punctuation">;</span>	<span class="token comment">/* pointer to buffer or iovecs */</span>
		__u64	splice_off_in<span class="token punctuation">;</span>
	<span class="token punctuation">}</span><span class="token punctuation">;</span>
	__u32	len<span class="token punctuation">;</span>		<span class="token comment">/* buffer size or number of iovecs */</span>
	<span class="token keyword">union</span> <span class="token punctuation">{</span>
		__kernel_rwf_t	rw_flags<span class="token punctuation">;</span>
		__u32		fsync_flags<span class="token punctuation">;</span>
		__u16		poll_events<span class="token punctuation">;</span>	<span class="token comment">/* compatibility */</span>
		__u32		poll32_events<span class="token punctuation">;</span>	<span class="token comment">/* word-reversed for BE */</span>
		__u32		sync_range_flags<span class="token punctuation">;</span>
		__u32		msg_flags<span class="token punctuation">;</span>
		__u32		timeout_flags<span class="token punctuation">;</span>
		__u32		accept_flags<span class="token punctuation">;</span>
		__u32		cancel_flags<span class="token punctuation">;</span>
		__u32		open_flags<span class="token punctuation">;</span>
		__u32		statx_flags<span class="token punctuation">;</span>
		__u32		fadvise_advice<span class="token punctuation">;</span>
		__u32		splice_flags<span class="token punctuation">;</span>
	<span class="token punctuation">}</span><span class="token punctuation">;</span>
	__u64	user_data<span class="token punctuation">;</span>	<span class="token comment">/* data to be passed back at completion time */</span>
	<span class="token keyword">union</span> <span class="token punctuation">{</span>
		<span class="token keyword">struct</span> <span class="token punctuation">{</span>
			<span class="token comment">/* pack this to avoid bogus arm OABI complaints */</span>
			<span class="token keyword">union</span> <span class="token punctuation">{</span>
				<span class="token comment">/* index into fixed buffers, if used */</span>
				__u16	buf_index<span class="token punctuation">;</span>
				<span class="token comment">/* for grouped buffer selection */</span>
				__u16	buf_group<span class="token punctuation">;</span>
			<span class="token punctuation">}</span> <span class="token function">__attribute__</span><span class="token punctuation">(</span><span class="token punctuation">(</span>packed<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token comment">/* personality to use, if used */</span>
			__u16	personality<span class="token punctuation">;</span>
			__s32	splice_fd_in<span class="token punctuation">;</span>
		<span class="token punctuation">}</span><span class="token punctuation">;</span>
		__u64	__pad2<span class="token punctuation">[</span><span class="token number">3</span><span class="token punctuation">]</span><span class="token punctuation">;</span>
	<span class="token punctuation">}</span><span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<ul>
<li>opcode是操作码，例如IORING_OP_READV，代表向量读。</li>
<li>flags是标志位集合。</li>
<li>ioprio是请求的优先级，对于普通的读写，具体定义可以参照ioprio_set(2)，</li>
<li>fd是这个请求相关的文件描述符</li>
<li>off是操作的偏移量</li>
<li>addr表示这次IO操作执行的地址，如果操作码opcode描述了一个传输数据的操作，这个操作是基于向量的，addr就指向struct iovec的数组首地址，这和前文所说的preadv系统调用是一样的用法；如果不是基于向量的，那么addr必须直接包含一个地址，len这里（非向量场景）就表示这段buffer的长度，而向量场景就表示iovec的数量。</li>
<li>接下来的是一个union，表示一系列针对特定操作码opcode的一些flag。例如，对于上文所提的IORING_OP_READV，随后的flags就遵循preadv2系统调用。</li>
<li>user_data是各操作码opcode通用的，内核并未染指，仅仅只是拷贝给完成事件completion event</li>
<li>结构的最后用于内存对齐，对齐到64字节，为了更丰富的特性，未来这个请求结构应该会包含更多的内容。</li>
</ul>

<p>这就是核外往内核填写的Submission Queue Entry的数据结构，准备好这样的一个数据结构，将它写到对应的sqes所在的内存位置，然后再通知内核去对应的位置取数据，这样就完成了一次数据交接。</p>

<h3 id="Completion-Queue-Entry单元数据结构">Completion Queue Entry单元数据结构</h3>

<p>Completion Queue（下称CQ）是完成队列，内核写核外读的地方。Completion Queue Entry（下称CQE），即完成队列中的条目，队列由一个个条目组成。</p>

<p>描述一个CQE就简单得多。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token comment">/*
 * IO completion data structure (Completion Queue Entry)
 */</span>
<span class="token keyword">struct</span> <span class="token class-name">io_uring_cqe</span> <span class="token punctuation">{</span>
	__u64	user_data<span class="token punctuation">;</span>	<span class="token comment">/* sqe-&gt;data submission passed back */</span>
	__s32	res<span class="token punctuation">;</span>		<span class="token comment">/* result code for this event */</span>
	__u32	flags<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<ul>
<li>user_data就是sqe发送时核外填写的，只不过在完成时回传而已，一个常见的用例就是作为一个指针，指向原始请求。从submission queue到completion queue，内核不会动这里面的数据</li>
<li>res用来保存最终的这个sqe的执行结果，就是这个event的返回码，可以认为是系统调用的返回值，表示成功或失败等。如果接口成功的话返回传输的字节数，如果失败的话，就是错误码。如果错误发生，res就等于-EIO</li>
<li>flags是标志位集合。如果flags设置为IORING_CQE_F_BUFFER，则前16位是buffer ID（调用链：io_uring_enter -&gt; io_iopoll_check -&gt; io_iopoll_getevents -&gt; io_do_iopoll -&gt; io_iopoll_complete -&gt; io_put_rw_kbuf -&gt; io_put_kbuf，最终会调用io_put_kbuf，如代码所示）。</li>
</ul>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> cqe<span class="token operator">-</span><span class="token operator">&gt;</span>flags
 <span class="token operator">*</span>
 <span class="token operator">*</span> IORING_CQE_F_BUFFER	If <span class="token builtin">set</span><span class="token punctuation">,</span> the upper <span class="token number">16</span> bits are the <span class="token builtin">buffer</span> ID
 <span class="token operator">*</span><span class="token operator">/</span>
<span class="token comment">#define IORING_CQE_F_BUFFER		(1U &lt;&lt; 0)</span>

enum <span class="token punctuation">{</span>
	IORING_CQE_BUFFER_SHIFT		<span class="token operator">=</span> <span class="token number">16</span><span class="token punctuation">,</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">static unsigned <span class="token builtin">int</span> io_put_kbuf<span class="token punctuation">(</span>struct io_kiocb <span class="token operator">*</span>req<span class="token punctuation">,</span> struct io_buffer <span class="token operator">*</span>kbuf<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	unsigned <span class="token builtin">int</span> cflags<span class="token punctuation">;</span>

	cflags <span class="token operator">=</span> kbuf<span class="token operator">-</span><span class="token operator">&gt;</span>bid <span class="token operator">&lt;&lt;</span> IORING_CQE_BUFFER_SHIFT<span class="token punctuation">;</span>
	cflags <span class="token operator">|</span><span class="token operator">=</span> IORING_CQE_F_BUFFER<span class="token punctuation">;</span>
	req<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span><span class="token operator">=</span> <span class="token operator">~</span>REQ_F_BUFFER_SELECTED<span class="token punctuation">;</span>
	kfree<span class="token punctuation">(</span>kbuf<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> cflags<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="上下文结构io_ring_ctx">上下文结构io_ring_ctx</h3>

<p>前面介绍了SQE/CQE等关键的数据结构，他们是用来承载数据流的关键部分，有了数据流的关键数据结构我们还需要一个上下文数据结构，用于整个io_uring控制流。这就是io_ring_ctx，贯穿整个io_uring所有过程的数据结构，基本上在任何位置只需要你能持有该结构就可以找到任何数据所在的位置，例如，sq_sqes就是指向io_uring_sqe结构的指针，指向SQEs的首地址。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">struct io_ring_ctx <span class="token punctuation">{</span>
	struct <span class="token punctuation">{</span>
		struct percpu_ref	refs<span class="token punctuation">;</span>
	<span class="token punctuation">}</span> ____cacheline_aligned_in_smp<span class="token punctuation">;</span>

	struct <span class="token punctuation">{</span>
		unsigned <span class="token builtin">int</span>		flags<span class="token punctuation">;</span>
		unsigned <span class="token builtin">int</span>		compat<span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">;</span>
		unsigned <span class="token builtin">int</span>		limit_mem<span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">;</span>
		unsigned <span class="token builtin">int</span>		cq_overflow_flushed<span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">;</span>
		unsigned <span class="token builtin">int</span>		drain_next<span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">;</span>
		unsigned <span class="token builtin">int</span>		eventfd_async<span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">;</span>
		unsigned <span class="token builtin">int</span>		restricted<span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">;</span>

		<span class="token operator">/</span><span class="token operator">*</span>
		 <span class="token operator">*</span> Ring <span class="token builtin">buffer</span> of indices into array of io_uring_sqe<span class="token punctuation">,</span> which <span class="token keyword">is</span>
		 <span class="token operator">*</span> mmapped by the application using the IORING_OFF_SQES offset<span class="token punctuation">.</span>
		 <span class="token operator">*</span>
		 <span class="token operator">*</span> This indirection could e<span class="token punctuation">.</span>g<span class="token punctuation">.</span> be used to assign fixed
		 <span class="token operator">*</span> io_uring_sqe entries to operations <span class="token keyword">and</span> only submit them to
		 <span class="token operator">*</span> the queue when needed<span class="token punctuation">.</span>
		 <span class="token operator">*</span>
		 <span class="token operator">*</span> The kernel modifies neither the indices array nor the entries
		 <span class="token operator">*</span> array<span class="token punctuation">.</span>
		 <span class="token operator">*</span><span class="token operator">/</span>
		u32			<span class="token operator">*</span>sq_array<span class="token punctuation">;</span>
		unsigned		cached_sq_head<span class="token punctuation">;</span>
		unsigned		sq_entries<span class="token punctuation">;</span>
		unsigned		sq_mask<span class="token punctuation">;</span>
		unsigned		sq_thread_idle<span class="token punctuation">;</span>
		unsigned		cached_sq_dropped<span class="token punctuation">;</span>
		unsigned		cached_cq_overflow<span class="token punctuation">;</span>
		unsigned <span class="token builtin">long</span>		sq_check_overflow<span class="token punctuation">;</span>

		struct list_head	defer_list<span class="token punctuation">;</span>
		struct list_head	timeout_list<span class="token punctuation">;</span>
		struct list_head	cq_overflow_list<span class="token punctuation">;</span>

		wait_queue_head_t	inflight_wait<span class="token punctuation">;</span>
		struct io_uring_sqe	<span class="token operator">*</span>sq_sqes<span class="token punctuation">;</span>
	<span class="token punctuation">}</span> ____cacheline_aligned_in_smp<span class="token punctuation">;</span>

	struct io_rings	<span class="token operator">*</span>rings<span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span> IO offload <span class="token operator">*</span><span class="token operator">/</span>
	struct io_wq		<span class="token operator">*</span>io_wq<span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span>
	 <span class="token operator">*</span> For SQPOLL usage <span class="token operator">-</span> we hold a reference to the parent task<span class="token punctuation">,</span> so we
	 <span class="token operator">*</span> have access to the <span class="token operator">-</span><span class="token operator">&gt;</span>files
	 <span class="token operator">*</span><span class="token operator">/</span>
	struct task_struct	<span class="token operator">*</span>sqo_task<span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span> Only used <span class="token keyword">for</span> accounting purposes <span class="token operator">*</span><span class="token operator">/</span>
	struct mm_struct	<span class="token operator">*</span>mm_account<span class="token punctuation">;</span>

<span class="token comment">#ifdef CONFIG_BLK_CGROUP</span>
	struct cgroup_subsys_state	<span class="token operator">*</span>sqo_blkcg_css<span class="token punctuation">;</span>
<span class="token comment">#endif</span>

	struct io_sq_data	<span class="token operator">*</span>sq_data<span class="token punctuation">;</span>	<span class="token operator">/</span><span class="token operator">*</span> <span class="token keyword">if</span> using sq thread polling <span class="token operator">*</span><span class="token operator">/</span>

	struct wait_queue_head	sqo_sq_wait<span class="token punctuation">;</span>
	struct wait_queue_entry	sqo_wait_entry<span class="token punctuation">;</span>
	struct list_head	sqd_list<span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span>
	 <span class="token operator">*</span> If used<span class="token punctuation">,</span> fixed <span class="token builtin">file</span> <span class="token builtin">set</span><span class="token punctuation">.</span> Writers must ensure that <span class="token operator">-</span><span class="token operator">&gt;</span>refs <span class="token keyword">is</span> dead<span class="token punctuation">,</span>
	 <span class="token operator">*</span> readers must ensure that <span class="token operator">-</span><span class="token operator">&gt;</span>refs <span class="token keyword">is</span> alive <span class="token keyword">as</span> <span class="token builtin">long</span> <span class="token keyword">as</span> the <span class="token builtin">file</span><span class="token operator">*</span> <span class="token keyword">is</span>
	 <span class="token operator">*</span> used<span class="token punctuation">.</span> Only updated through io_uring_register<span class="token punctuation">(</span><span class="token number">2</span><span class="token punctuation">)</span><span class="token punctuation">.</span>
	 <span class="token operator">*</span><span class="token operator">/</span>
	struct fixed_file_data	<span class="token operator">*</span>file_data<span class="token punctuation">;</span>
	unsigned		nr_user_files<span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span> <span class="token keyword">if</span> used<span class="token punctuation">,</span> fixed mapped user buffers <span class="token operator">*</span><span class="token operator">/</span>
	unsigned		nr_user_bufs<span class="token punctuation">;</span>
	struct io_mapped_ubuf	<span class="token operator">*</span>user_bufs<span class="token punctuation">;</span>

	struct user_struct	<span class="token operator">*</span>user<span class="token punctuation">;</span>

	const struct cred	<span class="token operator">*</span>creds<span class="token punctuation">;</span>

<span class="token comment">#ifdef CONFIG_AUDIT</span>
	kuid_t			loginuid<span class="token punctuation">;</span>
	unsigned <span class="token builtin">int</span>		sessionid<span class="token punctuation">;</span>
<span class="token comment">#endif</span>

	struct completion	ref_comp<span class="token punctuation">;</span>
	struct completion	sq_thread_comp<span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span> <span class="token keyword">if</span> <span class="token builtin">all</span> <span class="token keyword">else</span> fails<span class="token punctuation">.</span><span class="token punctuation">.</span><span class="token punctuation">.</span> <span class="token operator">*</span><span class="token operator">/</span>
	struct io_kiocb		<span class="token operator">*</span>fallback_req<span class="token punctuation">;</span>

<span class="token comment">#if defined(CONFIG_UNIX)</span>
	struct socket		<span class="token operator">*</span>ring_sock<span class="token punctuation">;</span>
<span class="token comment">#endif</span>

	struct idr		io_buffer_idr<span class="token punctuation">;</span>

	struct idr		personality_idr<span class="token punctuation">;</span>

	struct <span class="token punctuation">{</span>
		unsigned		cached_cq_tail<span class="token punctuation">;</span>
		unsigned		cq_entries<span class="token punctuation">;</span>
		unsigned		cq_mask<span class="token punctuation">;</span>
		atomic_t		cq_timeouts<span class="token punctuation">;</span>
		unsigned <span class="token builtin">long</span>		cq_check_overflow<span class="token punctuation">;</span>
		struct wait_queue_head	cq_wait<span class="token punctuation">;</span>
		struct fasync_struct	<span class="token operator">*</span>cq_fasync<span class="token punctuation">;</span>
		struct eventfd_ctx	<span class="token operator">*</span>cq_ev_fd<span class="token punctuation">;</span>
	<span class="token punctuation">}</span> ____cacheline_aligned_in_smp<span class="token punctuation">;</span>

	struct <span class="token punctuation">{</span>
		struct mutex		uring_lock<span class="token punctuation">;</span>
		wait_queue_head_t	wait<span class="token punctuation">;</span>
	<span class="token punctuation">}</span> ____cacheline_aligned_in_smp<span class="token punctuation">;</span>

	struct <span class="token punctuation">{</span>
		spinlock_t		completion_lock<span class="token punctuation">;</span>

		<span class="token operator">/</span><span class="token operator">*</span>
		 <span class="token operator">*</span> <span class="token operator">-</span><span class="token operator">&gt;</span>iopoll_list <span class="token keyword">is</span> protected by the ctx<span class="token operator">-</span><span class="token operator">&gt;</span>uring_lock <span class="token keyword">for</span>
		 <span class="token operator">*</span> io_uring instances that don't use IORING_SETUP_SQPOLL<span class="token punctuation">.</span>
		 <span class="token operator">*</span> For SQPOLL<span class="token punctuation">,</span> only the single threaded io_sq_thread<span class="token punctuation">(</span><span class="token punctuation">)</span> will
		 <span class="token operator">*</span> manipulate the <span class="token builtin">list</span><span class="token punctuation">,</span> hence no extra locking <span class="token keyword">is</span> needed there<span class="token punctuation">.</span>
		 <span class="token operator">*</span><span class="token operator">/</span>
		struct list_head	iopoll_list<span class="token punctuation">;</span>
		struct hlist_head	<span class="token operator">*</span>cancel_hash<span class="token punctuation">;</span>
		unsigned		cancel_hash_bits<span class="token punctuation">;</span>
		<span class="token builtin">bool</span>			poll_multi_file<span class="token punctuation">;</span>

		spinlock_t		inflight_lock<span class="token punctuation">;</span>
		struct list_head	inflight_list<span class="token punctuation">;</span>
	<span class="token punctuation">}</span> ____cacheline_aligned_in_smp<span class="token punctuation">;</span>

	struct delayed_work		file_put_work<span class="token punctuation">;</span>
	struct llist_head		file_put_llist<span class="token punctuation">;</span>

	struct work_struct		exit_work<span class="token punctuation">;</span>
	struct io_restriction		restrictions<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<h2 id="关键流程">关键流程</h2>

<p>数据结构定义好了，逻辑实现具体是如何驱动这些数据结构的呢？使用上，大体分为准备、提交、收割过程。</p>

<p>有几个io_uring相关的系统调用：</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token macro property">#<span class="token directive keyword">include</span> <span class="token string">&lt;linux/io_uring.h&gt;</span></span>

<span class="token keyword">int</span> <span class="token function">io_uring_setup</span><span class="token punctuation">(</span>u32 entries<span class="token punctuation">,</span> <span class="token keyword">struct</span> <span class="token class-name">io_uring_params</span> <span class="token operator">*</span>p<span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token keyword">int</span> <span class="token function">io_uring_enter</span><span class="token punctuation">(</span><span class="token keyword">unsigned</span> <span class="token keyword">int</span> fd<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> <span class="token keyword">int</span> to_submit<span class="token punctuation">,</span>
                   <span class="token keyword">unsigned</span> <span class="token keyword">int</span> min_complete<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> <span class="token keyword">int</span> flags<span class="token punctuation">,</span>
                   sigset_t <span class="token operator">*</span>sig<span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token keyword">int</span> <span class="token function">io_uring_register</span><span class="token punctuation">(</span><span class="token keyword">unsigned</span> <span class="token keyword">int</span> fd<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> <span class="token keyword">int</span> opcode<span class="token punctuation">,</span>
                      <span class="token keyword">void</span> <span class="token operator">*</span>arg<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> <span class="token keyword">int</span> nr_args<span class="token punctuation">)</span><span class="token punctuation">;</span>
</code></pre>

<p>下面分析关键流程。</p>

<h3 id="io_uring准备阶段">io_uring准备阶段</h3>

<p>io_uring通过io_uring_setup完成准备阶段。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token keyword">int</span> <span class="token function">io_uring_setup</span><span class="token punctuation">(</span>u32 entries<span class="token punctuation">,</span> <span class="token keyword">struct</span> <span class="token class-name">io_uring_params</span> <span class="token operator">*</span>p<span class="token punctuation">)</span><span class="token punctuation">;</span>
</code></pre>

<p>io_uring_setup系统调用的过程就是初始化相关数据结构，建立好对应的缓存区，然后通过系统调用的参数io_uring_params结构传递回去，告诉核外环内存地址在哪，起始指针的地址在哪等关键的信息。</p>

<p>需要初始化内存的内存分为三个区域，分别是SQ，CQ，SQEs。内核初始化SQ和CQ，此外，提交请求在SQ，CQ之间有一个间接数组，即内核提供了一个Submission Queue Entries（SQEs）数组。之所以额外采用了一个数组保存SQEs，是为了方便通过环形缓冲区提交内存上不连续的请求。SQ和CQ中每个节点保存的都是SQEs数组的索引，而不是实际的请求，实际的请求只保存在SQEs数组中。这样在提交请求时，就可以批量提交一组SQEs上不连续的请求。</p>

<p>通常，SQE被独立地使用，意味着它的执行不影响在ring中的连续SQE条目。它允许全面、灵活的操作，并且使它们最高性能地并行执行完成。一个顺序的使用案例就是数据的整体写入。它的一个通常的例子就是一系列写，随之的是fsync/fdatasync，应用通常转变成程序同步-等待操作。</p>

<p style=""><img src="./《操作系统与存储：解析Linux内核全新异步IO引擎——io_uring设计与实现》 - 社交平台产品部 - KM平台_files/cos-file-url(4)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>先从参数上来解析</p>

<ul>
<li>核外需要告诉io_uring_setup提交的整个缓存区数组的大小。（代表 queue depth？），这里就是entries参数。</li>
<li>params这个参数从IO的角度看有两种，一种是输入参数，一种是输出参数。
<ul>
<li>一部分属于输入参数，是用户设置、核外传递给核外的，用于定义io_uring在内核中的行为，这些都是在创建阶段就决定了的。
<ul>
<li>比如params-&gt;flags，这个成员变量是用来设置当前整个io_uring 的标志的，它将决定是否启动sq_thread，是否采用iopoll模式等等</li>
<li>sq_thread_cpu、sq_thread_idle也由用户设置，用来指定io_sq_thread内核线程CPU、idle时间。</li>
</ul>
</li>
<li>还有一部分属于输出参数，由内核设置（io_uring_create）、传递数据到核外的，核外根据这些数据来使用mmap分配内存，初始化一些数据结构。
<ul>
<li>sq_entries是输出参数，由内核填充，让应用程序知道这个ring支持多少SQE。</li>
<li>类似地，cq_entries告诉应用程序，CQ ring有多大。</li>
<li>sq_off和cq_off分别是io_sqring_offsets和io_cqring_offsets结构，是内核与核外的约定，分别描述了SQ和CQ的指针在mmap中的offset</li>
<li>其他的结构成员涉及到高级用法，暂时按下不表。</li>
</ul>
</li>
</ul>
</li>
</ul>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token comment">/*
 * Passed in for io_uring_setup(2). Copied back with updated info on success
 */</span>
<span class="token keyword">struct</span> <span class="token class-name">io_uring_params</span> <span class="token punctuation">{</span>
	__u32 sq_entries<span class="token punctuation">;</span>
	__u32 cq_entries<span class="token punctuation">;</span>
	__u32 flags<span class="token punctuation">;</span>
	__u32 sq_thread_cpu<span class="token punctuation">;</span>
	__u32 sq_thread_idle<span class="token punctuation">;</span>
	__u32 features<span class="token punctuation">;</span>
	__u32 wq_fd<span class="token punctuation">;</span>
	__u32 resv<span class="token punctuation">[</span><span class="token number">3</span><span class="token punctuation">]</span><span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_sqring_offsets</span> sq_off<span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_cqring_offsets</span> cq_off<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>

<span class="token comment">/*
 * io_uring_params-&gt;features flags
 */</span>
<span class="token macro property">#<span class="token directive keyword">define</span> IORING_FEAT_SINGLE_MMAP		(1U &lt;&lt; 0)</span>
<span class="token macro property">#<span class="token directive keyword">define</span> IORING_FEAT_NODROP		(1U &lt;&lt; 1)</span>
<span class="token macro property">#<span class="token directive keyword">define</span> IORING_FEAT_SUBMIT_STABLE	(1U &lt;&lt; 2)</span>
<span class="token macro property">#<span class="token directive keyword">define</span> IORING_FEAT_RW_CUR_POS		(1U &lt;&lt; 3)</span>
<span class="token macro property">#<span class="token directive keyword">define</span> IORING_FEAT_CUR_PERSONALITY	(1U &lt;&lt; 4)</span>
<span class="token macro property">#<span class="token directive keyword">define</span> IORING_FEAT_FAST_POLL		(1U &lt;&lt; 5)</span>
<span class="token macro property">#<span class="token directive keyword">define</span> IORING_FEAT_POLL_32BITS 	(1U &lt;&lt; 6)</span>
</code></pre>

<p>再从实现上来解析，如下为io_uring_setup代码。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> Sets up an aio uring context<span class="token punctuation">,</span> <span class="token keyword">and</span> returns the fd<span class="token punctuation">.</span> Applications asks <span class="token keyword">for</span> a
 <span class="token operator">*</span> ring size<span class="token punctuation">,</span> we <span class="token keyword">return</span> the actual sq<span class="token operator">/</span>cq ring sizes <span class="token punctuation">(</span>among other things<span class="token punctuation">)</span> <span class="token keyword">in</span> the
 <span class="token operator">*</span> params structure passed <span class="token keyword">in</span><span class="token punctuation">.</span>
 <span class="token operator">*</span><span class="token operator">/</span>
static <span class="token builtin">long</span> io_uring_setup<span class="token punctuation">(</span>u32 entries<span class="token punctuation">,</span> struct io_uring_params __user <span class="token operator">*</span>params<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	struct io_uring_params p<span class="token punctuation">;</span>
	<span class="token builtin">int</span> i<span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span>copy_from_user<span class="token punctuation">(</span><span class="token operator">&amp;</span>p<span class="token punctuation">,</span> params<span class="token punctuation">,</span> sizeof<span class="token punctuation">(</span>p<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EFAULT<span class="token punctuation">;</span>
	<span class="token keyword">for</span> <span class="token punctuation">(</span>i <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span> i <span class="token operator">&lt;</span> ARRAY_SIZE<span class="token punctuation">(</span>p<span class="token punctuation">.</span>resv<span class="token punctuation">)</span><span class="token punctuation">;</span> i<span class="token operator">+</span><span class="token operator">+</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>p<span class="token punctuation">.</span>resv<span class="token punctuation">[</span>i<span class="token punctuation">]</span><span class="token punctuation">)</span>
			<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span>p<span class="token punctuation">.</span>flags <span class="token operator">&amp;</span> <span class="token operator">~</span><span class="token punctuation">(</span>IORING_SETUP_IOPOLL <span class="token operator">|</span> IORING_SETUP_SQPOLL <span class="token operator">|</span>
			IORING_SETUP_SQ_AFF <span class="token operator">|</span> IORING_SETUP_CQSIZE <span class="token operator">|</span>
			IORING_SETUP_CLAMP <span class="token operator">|</span> IORING_SETUP_ATTACH_WQ <span class="token operator">|</span>
			IORING_SETUP_R_DISABLED<span class="token punctuation">)</span><span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>

	<span class="token keyword">return</span>  io_uring_create<span class="token punctuation">(</span>entries<span class="token punctuation">,</span> <span class="token operator">&amp;</span>p<span class="token punctuation">,</span> params<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>经过标志位非法检查之后，关键是调用内部函数io_uring_create实现实例创建过程。</p>

<ul>
<li>首先需要创建一个上下文结构io_ring_ctx用来管理整个会话。</li>
<li>随后实现SQ和CQ内存区的映射，使用IORING_OFF_CQ_RING偏移量，使用io_cqring_offsets结构的实例，即io_uring_params中cq_off这个成员，SQ使用IORING_OFF_SQES这个偏移量。</li>
<li>其余的是一些错误检查、权限检查、资源配额检查等检查逻辑。</li>
</ul>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token keyword">static</span> <span class="token keyword">int</span> <span class="token function">io_uring_create</span><span class="token punctuation">(</span><span class="token keyword">unsigned</span> entriesstatic <span class="token keyword">int</span> <span class="token function">io_uring_create</span><span class="token punctuation">(</span><span class="token keyword">unsigned</span> entries<span class="token punctuation">,</span> <span class="token keyword">struct</span> <span class="token class-name">io_uring_params</span> <span class="token operator">*</span>p<span class="token punctuation">,</span>
			   <span class="token keyword">struct</span> <span class="token class-name">io_uring_params</span> __user <span class="token operator">*</span>params<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	<span class="token keyword">struct</span> <span class="token class-name">user_struct</span> <span class="token operator">*</span>user <span class="token operator">=</span> <span class="token constant">NULL</span><span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_ring_ctx</span> <span class="token operator">*</span>ctx<span class="token punctuation">;</span>
	<span class="token keyword">bool</span> limit_mem<span class="token punctuation">;</span>
	<span class="token keyword">int</span> ret<span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>entries<span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>entries <span class="token operator">&gt;</span> IORING_MAX_ENTRIES<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span><span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_CLAMP<span class="token punctuation">)</span><span class="token punctuation">)</span>
			<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>
		entries <span class="token operator">=</span> IORING_MAX_ENTRIES<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	<span class="token comment">/*
	 * Use twice as many entries for the CQ ring. It's possible for the
	 * application to drive a higher depth than the size of the SQ ring,
	 * since the sqes are only used at submission time. This allows for
	 * some flexibility in overcommitting a bit. If the application has
	 * set IORING_SETUP_CQSIZE, it will have passed in the desired number
	 * of CQ ring entries manually.
	 */</span>
	p<span class="token operator">-&gt;</span>sq_entries <span class="token operator">=</span> <span class="token function">roundup_pow_of_two</span><span class="token punctuation">(</span>entries<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_CQSIZE<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token comment">/*
		 * If IORING_SETUP_CQSIZE is set, we do the same roundup
		 * to a power-of-two, if it isn't already. We do NOT impose
		 * any cq vs sq ring sizing.
		 */</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>p<span class="token operator">-&gt;</span>cq_entries<span class="token punctuation">)</span>
			<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>cq_entries <span class="token operator">&gt;</span> IORING_MAX_CQ_ENTRIES<span class="token punctuation">)</span> <span class="token punctuation">{</span>
			<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span><span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_CLAMP<span class="token punctuation">)</span><span class="token punctuation">)</span>
				<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>
			p<span class="token operator">-&gt;</span>cq_entries <span class="token operator">=</span> IORING_MAX_CQ_ENTRIES<span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
		p<span class="token operator">-&gt;</span>cq_entries <span class="token operator">=</span> <span class="token function">roundup_pow_of_two</span><span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>cq_entries<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>cq_entries <span class="token operator">&lt;</span> p<span class="token operator">-&gt;</span>sq_entries<span class="token punctuation">)</span>
			<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>
	<span class="token punctuation">}</span> <span class="token keyword">else</span> <span class="token punctuation">{</span>
		p<span class="token operator">-&gt;</span>cq_entries <span class="token operator">=</span> <span class="token number">2</span> <span class="token operator">*</span> p<span class="token operator">-&gt;</span>sq_entries<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	user <span class="token operator">=</span> <span class="token function">get_uid</span><span class="token punctuation">(</span><span class="token function">current_user</span><span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	limit_mem <span class="token operator">=</span> <span class="token operator">!</span><span class="token function">capable</span><span class="token punctuation">(</span>CAP_IPC_LOCK<span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span>limit_mem<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		ret <span class="token operator">=</span> <span class="token function">__io_account_mem</span><span class="token punctuation">(</span>user<span class="token punctuation">,</span>
				<span class="token function">ring_pages</span><span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>sq_entries<span class="token punctuation">,</span> p<span class="token operator">-&gt;</span>cq_entries<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>ret<span class="token punctuation">)</span> <span class="token punctuation">{</span>
			<span class="token function">free_uid</span><span class="token punctuation">(</span>user<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
	<span class="token punctuation">}</span>

	ctx <span class="token operator">=</span> <span class="token function">io_ring_ctx_alloc</span><span class="token punctuation">(</span>p<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>ctx<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>limit_mem<span class="token punctuation">)</span>
			<span class="token function">__io_unaccount_mem</span><span class="token punctuation">(</span>user<span class="token punctuation">,</span> <span class="token function">ring_pages</span><span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>sq_entries<span class="token punctuation">,</span>
								p<span class="token operator">-&gt;</span>cq_entries<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token function">free_uid</span><span class="token punctuation">(</span>user<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>ENOMEM<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>
	ctx<span class="token operator">-&gt;</span>compat <span class="token operator">=</span> <span class="token function">in_compat_syscall</span><span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	ctx<span class="token operator">-&gt;</span>user <span class="token operator">=</span> user<span class="token punctuation">;</span>
	ctx<span class="token operator">-&gt;</span>creds <span class="token operator">=</span> <span class="token function">get_current_cred</span><span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token macro property">#<span class="token directive keyword">ifdef</span> CONFIG_AUDIT</span>
	ctx<span class="token operator">-&gt;</span>loginuid <span class="token operator">=</span> current<span class="token operator">-&gt;</span>loginuid<span class="token punctuation">;</span>
	ctx<span class="token operator">-&gt;</span>sessionid <span class="token operator">=</span> current<span class="token operator">-&gt;</span>sessionid<span class="token punctuation">;</span>
<span class="token macro property">#<span class="token directive keyword">endif</span></span>
	ctx<span class="token operator">-&gt;</span>sqo_task <span class="token operator">=</span> <span class="token function">get_task_struct</span><span class="token punctuation">(</span>current<span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token comment">/*
	 * This is just grabbed for accounting purposes. When a process exits,
	 * the mm is exited and dropped before the files, hence we need to hang
	 * on to this mm purely for the purposes of being able to unaccount
	 * memory (locked/pinned vm). It's not used for anything else.
	 */</span>
	<span class="token function">mmgrab</span><span class="token punctuation">(</span>current<span class="token operator">-&gt;</span>mm<span class="token punctuation">)</span><span class="token punctuation">;</span>
	ctx<span class="token operator">-&gt;</span>mm_account <span class="token operator">=</span> current<span class="token operator">-&gt;</span>mm<span class="token punctuation">;</span>

<span class="token macro property">#<span class="token directive keyword">ifdef</span> CONFIG_BLK_CGROUP</span>
	<span class="token comment">/*
	 * The sq thread will belong to the original cgroup it was inited in.
	 * If the cgroup goes offline (e.g. disabling the io controller), then
	 * issued bios will be associated with the closest cgroup later in the
	 * block layer.
	 */</span>
	<span class="token function">rcu_read_lock</span><span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	ctx<span class="token operator">-&gt;</span>sqo_blkcg_css <span class="token operator">=</span> <span class="token function">blkcg_css</span><span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	ret <span class="token operator">=</span> <span class="token function">css_tryget_online</span><span class="token punctuation">(</span>ctx<span class="token operator">-&gt;</span>sqo_blkcg_css<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">rcu_read_unlock</span><span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>ret<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token comment">/* don't init against a dying cgroup, have the user try again */</span>
		ctx<span class="token operator">-&gt;</span>sqo_blkcg_css <span class="token operator">=</span> <span class="token constant">NULL</span><span class="token punctuation">;</span>
		ret <span class="token operator">=</span> <span class="token operator">-</span>ENODEV<span class="token punctuation">;</span>
		<span class="token keyword">goto</span> err<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>
<span class="token macro property">#<span class="token directive keyword">endif</span></span>

	<span class="token comment">/*
	 * Account memory _before_ installing the file descriptor. Once
	 * the descriptor is installed, it can get closed at any time. Also
	 * do this before hitting the general error path, as ring freeing
	 * will un-account as well.
	 */</span>
	<span class="token function">io_account_mem</span><span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> <span class="token function">ring_pages</span><span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>sq_entries<span class="token punctuation">,</span> p<span class="token operator">-&gt;</span>cq_entries<span class="token punctuation">)</span><span class="token punctuation">,</span>
		       ACCT_LOCKED<span class="token punctuation">)</span><span class="token punctuation">;</span>
	ctx<span class="token operator">-&gt;</span>limit_mem <span class="token operator">=</span> limit_mem<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token function">io_allocate_scq_urings</span><span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> p<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ret<span class="token punctuation">)</span>
		<span class="token keyword">goto</span> err<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token function">io_sq_offload_create</span><span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> p<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ret<span class="token punctuation">)</span>
		<span class="token keyword">goto</span> err<span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span><span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_R_DISABLED<span class="token punctuation">)</span><span class="token punctuation">)</span>
		<span class="token function">io_sq_offload_start</span><span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token function">memset</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>p<span class="token operator">-&gt;</span>sq_off<span class="token punctuation">,</span> <span class="token number">0</span><span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>sq_off<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>sq_off<span class="token punctuation">.</span>head <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> sq<span class="token punctuation">.</span>head<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>sq_off<span class="token punctuation">.</span>tail <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> sq<span class="token punctuation">.</span>tail<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>sq_off<span class="token punctuation">.</span>ring_mask <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> sq_ring_mask<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>sq_off<span class="token punctuation">.</span>ring_entries <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> sq_ring_entries<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>sq_off<span class="token punctuation">.</span>flags <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> sq_flags<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>sq_off<span class="token punctuation">.</span>dropped <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> sq_dropped<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>sq_off<span class="token punctuation">.</span>array <span class="token operator">=</span> <span class="token punctuation">(</span><span class="token keyword">char</span> <span class="token operator">*</span><span class="token punctuation">)</span>ctx<span class="token operator">-&gt;</span>sq_array <span class="token operator">-</span> <span class="token punctuation">(</span><span class="token keyword">char</span> <span class="token operator">*</span><span class="token punctuation">)</span>ctx<span class="token operator">-&gt;</span>rings<span class="token punctuation">;</span>

	<span class="token function">memset</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>p<span class="token operator">-&gt;</span>cq_off<span class="token punctuation">,</span> <span class="token number">0</span><span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span>p<span class="token operator">-&gt;</span>cq_off<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>cq_off<span class="token punctuation">.</span>head <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> cq<span class="token punctuation">.</span>head<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>cq_off<span class="token punctuation">.</span>tail <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> cq<span class="token punctuation">.</span>tail<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>cq_off<span class="token punctuation">.</span>ring_mask <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> cq_ring_mask<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>cq_off<span class="token punctuation">.</span>ring_entries <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> cq_ring_entries<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>cq_off<span class="token punctuation">.</span>overflow <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> cq_overflow<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>cq_off<span class="token punctuation">.</span>cqes <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> cqes<span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token operator">-&gt;</span>cq_off<span class="token punctuation">.</span>flags <span class="token operator">=</span> <span class="token function">offsetof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_rings</span><span class="token punctuation">,</span> cq_flags<span class="token punctuation">)</span><span class="token punctuation">;</span>

	p<span class="token operator">-&gt;</span>features <span class="token operator">=</span> IORING_FEAT_SINGLE_MMAP <span class="token operator">|</span> IORING_FEAT_NODROP <span class="token operator">|</span>
			IORING_FEAT_SUBMIT_STABLE <span class="token operator">|</span> IORING_FEAT_RW_CUR_POS <span class="token operator">|</span>
			IORING_FEAT_CUR_PERSONALITY <span class="token operator">|</span> IORING_FEAT_FAST_POLL <span class="token operator">|</span>
			IORING_FEAT_POLL_32BITS<span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token function">copy_to_user</span><span class="token punctuation">(</span>params<span class="token punctuation">,</span> p<span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span><span class="token operator">*</span>p<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
		ret <span class="token operator">=</span> <span class="token operator">-</span>EFAULT<span class="token punctuation">;</span>
		<span class="token keyword">goto</span> err<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	<span class="token comment">/*
	 * Install ring fd as the very last thing, so we don't risk someone
	 * having closed it before we finish setup
	 */</span>
	ret <span class="token operator">=</span> <span class="token function">io_uring_get_fd</span><span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ret <span class="token operator">&lt;</span> <span class="token number">0</span><span class="token punctuation">)</span>
		<span class="token keyword">goto</span> err<span class="token punctuation">;</span>

	<span class="token function">trace_io_uring_create</span><span class="token punctuation">(</span>ret<span class="token punctuation">,</span> ctx<span class="token punctuation">,</span> p<span class="token operator">-&gt;</span>sq_entries<span class="token punctuation">,</span> p<span class="token operator">-&gt;</span>cq_entries<span class="token punctuation">,</span> p<span class="token operator">-&gt;</span>flags<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
err<span class="token operator">:</span>
	<span class="token function">io_ring_ctx_wait_and_kill</span><span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>io_sqring_offsets、io_cqring_offsets等相关结构、标志位集合。</p>

<p>预定义offset<br>
如果要表征分配的是io uring相关的一些内存，就需要预定义一些offset，如IORING_OFF_SQ_RING、IORING_OFF_SQES和IORING_OFF_CQ_RING，这些offset值定义了保存到这个三个结构保存到位置。这里mmap的时候，就使用了这些offset。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> Magic offsets <span class="token keyword">for</span> the application to mmap the data it needs
 <span class="token operator">*</span><span class="token operator">/</span>
<span class="token comment">#define IORING_OFF_SQ_RING		0ULL</span>
<span class="token comment">#define IORING_OFF_CQ_RING		0x8000000ULL</span>
<span class="token comment">#define IORING_OFF_SQES			0x10000000ULL</span>

<span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> Filled <span class="token keyword">with</span> the offset <span class="token keyword">for</span> mmap<span class="token punctuation">(</span><span class="token number">2</span><span class="token punctuation">)</span>
 <span class="token operator">*</span><span class="token operator">/</span>
struct io_sqring_offsets <span class="token punctuation">{</span>
	__u32 head<span class="token punctuation">;</span>
	__u32 tail<span class="token punctuation">;</span>
	__u32 ring_mask<span class="token punctuation">;</span>
	__u32 ring_entries<span class="token punctuation">;</span>
	__u32 flags<span class="token punctuation">;</span>
	__u32 dropped<span class="token punctuation">;</span>
	__u32 array<span class="token punctuation">;</span>
	__u32 resv1<span class="token punctuation">;</span>
	__u64 resv2<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>

<span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> sq_ring<span class="token operator">-</span><span class="token operator">&gt;</span>flags
 <span class="token operator">*</span><span class="token operator">/</span>
<span class="token comment">#define IORING_SQ_NEED_WAKEUP	(1U &lt;&lt; 0) /* needs io_uring_enter wakeup */</span>
<span class="token comment">#define IORING_SQ_CQ_OVERFLOW	(1U &lt;&lt; 1) /* CQ ring is overflown */</span>

struct io_cqring_offsets <span class="token punctuation">{</span>
	__u32 head<span class="token punctuation">;</span>
	__u32 tail<span class="token punctuation">;</span>
	__u32 ring_mask<span class="token punctuation">;</span>
	__u32 ring_entries<span class="token punctuation">;</span>
	__u32 overflow<span class="token punctuation">;</span>
	__u32 cqes<span class="token punctuation">;</span>
	__u32 flags<span class="token punctuation">;</span>
	__u32 resv1<span class="token punctuation">;</span>
	__u64 resv2<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>

<span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> cq_ring<span class="token operator">-</span><span class="token operator">&gt;</span>flags
 <span class="token operator">*</span><span class="token operator">/</span>

<span class="token operator">/</span><span class="token operator">*</span> disable eventfd notifications <span class="token operator">*</span><span class="token operator">/</span>
<span class="token comment">#define IORING_CQ_EVENTFD_DISABLED	(1U &lt;&lt; 0)</span>

<span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> io_uring_enter<span class="token punctuation">(</span><span class="token number">2</span><span class="token punctuation">)</span> flags
 <span class="token operator">*</span><span class="token operator">/</span>
<span class="token comment">#define IORING_ENTER_GETEVENTS	(1U &lt;&lt; 0)</span>
<span class="token comment">#define IORING_ENTER_SQ_WAKEUP	(1U &lt;&lt; 1)</span>
<span class="token comment">#define IORING_ENTER_SQ_WAIT	(1U &lt;&lt; 2)</span>

<span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> io_uring_register<span class="token punctuation">(</span><span class="token number">2</span><span class="token punctuation">)</span> opcodes <span class="token keyword">and</span> arguments
 <span class="token operator">*</span><span class="token operator">/</span>
enum <span class="token punctuation">{</span>
	IORING_REGISTER_BUFFERS			<span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">,</span>
	IORING_UNREGISTER_BUFFERS		<span class="token operator">=</span> <span class="token number">1</span><span class="token punctuation">,</span>
	IORING_REGISTER_FILES			<span class="token operator">=</span> <span class="token number">2</span><span class="token punctuation">,</span>
	IORING_UNREGISTER_FILES			<span class="token operator">=</span> <span class="token number">3</span><span class="token punctuation">,</span>
	IORING_REGISTER_EVENTFD			<span class="token operator">=</span> <span class="token number">4</span><span class="token punctuation">,</span>
	IORING_UNREGISTER_EVENTFD		<span class="token operator">=</span> <span class="token number">5</span><span class="token punctuation">,</span>
	IORING_REGISTER_FILES_UPDATE		<span class="token operator">=</span> <span class="token number">6</span><span class="token punctuation">,</span>
	IORING_REGISTER_EVENTFD_ASYNC		<span class="token operator">=</span> <span class="token number">7</span><span class="token punctuation">,</span>
	IORING_REGISTER_PROBE			<span class="token operator">=</span> <span class="token number">8</span><span class="token punctuation">,</span>
	IORING_REGISTER_PERSONALITY		<span class="token operator">=</span> <span class="token number">9</span><span class="token punctuation">,</span>
	IORING_UNREGISTER_PERSONALITY		<span class="token operator">=</span> <span class="token number">10</span><span class="token punctuation">,</span>
	IORING_REGISTER_RESTRICTIONS		<span class="token operator">=</span> <span class="token number">11</span><span class="token punctuation">,</span>
	IORING_REGISTER_ENABLE_RINGS		<span class="token operator">=</span> <span class="token number">12</span><span class="token punctuation">,</span>

	<span class="token operator">/</span><span class="token operator">*</span> this goes last <span class="token operator">*</span><span class="token operator">/</span>
	IORING_REGISTER_LAST
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<p>具体的实践，可以参考如下liburing中的初始化函数io_uring_queue_init中对io_uring_setup的使用（<a href="http://git.kernel.dk/cgit/liburing/tree/src/setup.c%EF%BC%89%E3%80%82" target="_blank">http://git.kernel.dk/cgit/liburing/tree/src/setup.c）。</a></p>

<p>liburing中使用io_uring_setup的部分代码</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token comment">/*
 * Returns -1 on error, or zero on success. On success, 'ring'
 * contains the necessary information to read/write to the rings.
 */</span>
<span class="token keyword">int</span> <span class="token function">io_uring_queue_init</span><span class="token punctuation">(</span><span class="token keyword">unsigned</span> entries<span class="token punctuation">,</span> <span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token operator">*</span>ring<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> flags<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_uring_params</span> p<span class="token punctuation">;</span>
	<span class="token keyword">int</span> fd<span class="token punctuation">,</span> ret<span class="token punctuation">;</span>

	<span class="token function">memset</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>p<span class="token punctuation">,</span> <span class="token number">0</span><span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span>p<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token punctuation">.</span>flags <span class="token operator">=</span> flags<span class="token punctuation">;</span>

	fd <span class="token operator">=</span> <span class="token function">io_uring_setup</span><span class="token punctuation">(</span>entries<span class="token punctuation">,</span> <span class="token operator">&amp;</span>p<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>fd <span class="token operator">&lt;</span> <span class="token number">0</span><span class="token punctuation">)</span>
		<span class="token keyword">return</span> fd<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token function">io_uring_queue_mmap</span><span class="token punctuation">(</span>fd<span class="token punctuation">,</span> <span class="token operator">&amp;</span>p<span class="token punctuation">,</span> ring<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ret<span class="token punctuation">)</span>
		<span class="token function">close</span><span class="token punctuation">(</span>fd<span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>注意mmap的时候需要传入MAP_POPULATE参数，为文件映射通过预读的方式准备好页表，随后对映射区的访问不会被page fault。</p>

<h3 id="IO提交">IO提交</h3>

<p>在初始化完成之后，应用程序就可以使用这些队列来添加IO请求，即填充SQE。当请求都加入SQ后，应用程序还需要某种方式告诉内核，生产的请求待消费，这就是提交IO请求，可以通过io_uring_enter系统调用。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token keyword">int</span> <span class="token function">io_uring_enter</span><span class="token punctuation">(</span><span class="token keyword">unsigned</span> <span class="token keyword">int</span> fd<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> <span class="token keyword">int</span> to_submit<span class="token punctuation">,</span>
                   <span class="token keyword">unsigned</span> <span class="token keyword">int</span> min_complete<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> <span class="token keyword">int</span> flags<span class="token punctuation">,</span>
                   sigset_t <span class="token operator">*</span>sig<span class="token punctuation">)</span><span class="token punctuation">;</span>
</code></pre>

<p>内核将SQ中的请求提交给Block层。这个系统调用既能提交，也能等待。</p>

<p>具体的实现是找到一个空闲的SQE，根据请求设置SQE，并将这个SQE的索引放到SQ中。SQ是一个典型的ring buffer，有head，tail两个成员，如果head == tail，意味着队列为空。SQE设置完成后，需要修改SQ的tail，以表示向ring buffer中插入了一个请求。</p>

<p>先从参数上来解析</p>

<ul>
<li>fd即由io_uring_setup(2)返回的文件描述符，</li>
<li>to_submit告诉内核待消费和提交的SQE的数量，表示一次提交多少个 IO，</li>
<li>min_complete请求完成请求的个数。</li>
<li>flags是修饰接口行为的标志集合，这里主要例举两个flags
<ul>
<li>如果在io_uring_setup的时候flag设置了IORING_SETUP_SQPOLL，内核会额外启动一个特定的内核线程来执行轮询的操作，称作SQ线程，这里使用的轮询结构会最终对应到struct file_operations中的iopoll操作，这个操作作为一个新的接口在最近才添加到这里，Linux native aio的新功能也使用了这个iopoll。这里io _uring实际上只有vfs层的改动，其它的都是使用已经存在的东西，而且几个核心的东西和aio使用的相同/类似。直接通过访问相关的队列就可以获取到执行完的任务，不需要经过系统调用。关于这个线程，通过io_uring_params结构中的sq_thread_cpu配置，这个内核线程可以运行在某个指定的 CPU核心 上。这个内核线程会不停的 Poll SQ，直到在通过sq_thread_idle配置的时间内没有Poll到任何请求为止。</li>
<li>如果flags中设置了IORING_ENTER_GETEVENTS，并且min_complete &gt; 0，这个系统调用会一直 block，直到 min_complete 个 IO 已经完成才返回。这个系统调用会同时处理 IO 收割。</li>
<li>另外的，IORING_SQ_NEED_WAKEUP可以表示在一些时候唤醒休眠中的轮询线程。</li>
</ul>
</li>
</ul>

<p>static int io_sq_thread(void *data)即内核轮询线程。</p>

<p style=""><img src="./《操作系统与存储：解析Linux内核全新异步IO引擎——io_uring设计与实现》 - 社交平台产品部 - KM平台_files/cos-file-url(5)" alt="" style="position: relative; z-index: 2;"></p>

<p>同样地，可以用这个系统调用等待完成。除非应用程序，内核会直接修改CQ，因此调用io_uring_enter系统调用时不必使用IORING_ENTER_GETEVENTS，完成就可以被应用程序消费。</p>

<p>io_uring提供了submission offload模式，使得提交过程完全不需要进行系统调用。当程序在用户态设置完SQE，并通过修改SQ的tail完成一次插入时，如果此时SQ线程处于唤醒状态，那么可以立刻捕获到这次提交，这样就避免了用户程序调用io_uring_enter。如上所说，如果SQ线程处于休眠状态，则需要通过使用IORING_SQ_NEED_WAKEUP标志位调用io_uring_enter来唤醒SQ线程。</p>

<p>以io_iopoll_check为例，正常情况下执行路线是io_iopoll_check -&gt; io_iopoll_getevents -&gt; io_do_iopoll -&gt; (kiocb-&gt;ki_filp-&gt;f_op-&gt;iopoll). 在完成请求的操作之后，会调用下面这个函数提交结果到cqe数组中，这样应用就能看到结果了。这里的io_cqring_fill_event就是获取一个目前可以写入到cqe，写入数据。这里最终调用的会是io_get_cqring，可以见就是返回目前tail的后面的一个。</p>

<p>更详细的内容可以直接参考io_uring_enter(2)的man page。</p>

<p>内核中io_uring_enter的相关代码如下。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">SYSCALL_DEFINE6<span class="token punctuation">(</span>io_uring_enter<span class="token punctuation">,</span> unsigned <span class="token builtin">int</span><span class="token punctuation">,</span> fd<span class="token punctuation">,</span> u32<span class="token punctuation">,</span> to_submit<span class="token punctuation">,</span>
		u32<span class="token punctuation">,</span> min_complete<span class="token punctuation">,</span> u32<span class="token punctuation">,</span> flags<span class="token punctuation">,</span> const sigset_t __user <span class="token operator">*</span><span class="token punctuation">,</span> sig<span class="token punctuation">,</span>
		size_t<span class="token punctuation">,</span> sigsz<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	struct io_ring_ctx <span class="token operator">*</span>ctx<span class="token punctuation">;</span>
	<span class="token builtin">long</span> ret <span class="token operator">=</span> <span class="token operator">-</span>EBADF<span class="token punctuation">;</span>
	<span class="token builtin">int</span> submitted <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
	struct fd f<span class="token punctuation">;</span>

	io_run_task_work<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span>flags <span class="token operator">&amp;</span> <span class="token operator">~</span><span class="token punctuation">(</span>IORING_ENTER_GETEVENTS <span class="token operator">|</span> IORING_ENTER_SQ_WAKEUP <span class="token operator">|</span>
			IORING_ENTER_SQ_WAIT<span class="token punctuation">)</span><span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>

	f <span class="token operator">=</span> fdget<span class="token punctuation">(</span>fd<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>!f<span class="token punctuation">.</span><span class="token builtin">file</span><span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EBADF<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token operator">-</span>EOPNOTSUPP<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>f<span class="token punctuation">.</span><span class="token builtin">file</span><span class="token operator">-</span><span class="token operator">&gt;</span>f_op <span class="token operator">!=</span> <span class="token operator">&amp;</span>io_uring_fops<span class="token punctuation">)</span>
		goto out_fput<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token operator">-</span>ENXIO<span class="token punctuation">;</span>
	ctx <span class="token operator">=</span> f<span class="token punctuation">.</span><span class="token builtin">file</span><span class="token operator">-</span><span class="token operator">&gt;</span>private_data<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>!percpu_ref_tryget<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>refs<span class="token punctuation">)</span><span class="token punctuation">)</span>
		goto out_fput<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token operator">-</span>EBADFD<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_R_DISABLED<span class="token punctuation">)</span>
		goto out<span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span>
	 <span class="token operator">*</span> For SQ polling<span class="token punctuation">,</span> the thread will do <span class="token builtin">all</span> submissions <span class="token keyword">and</span> completions<span class="token punctuation">.</span>
	 <span class="token operator">*</span> Just <span class="token keyword">return</span> the requested submit count<span class="token punctuation">,</span> <span class="token keyword">and</span> wake the thread <span class="token keyword">if</span>
	 <span class="token operator">*</span> we were asked to<span class="token punctuation">.</span>
	 <span class="token operator">*</span><span class="token operator">/</span>
	ret <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_SQPOLL<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>!list_empty_careful<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>cq_overflow_list<span class="token punctuation">)</span><span class="token punctuation">)</span>
			io_cqring_overflow_flush<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> false<span class="token punctuation">,</span> NULL<span class="token punctuation">,</span> NULL<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>flags <span class="token operator">&amp;</span> IORING_ENTER_SQ_WAKEUP<span class="token punctuation">)</span>
			wake_up<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>sq_data<span class="token operator">-</span><span class="token operator">&gt;</span>wait<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>flags <span class="token operator">&amp;</span> IORING_ENTER_SQ_WAIT<span class="token punctuation">)</span>
			io_sqpoll_wait_sq<span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
		submitted <span class="token operator">=</span> to_submit<span class="token punctuation">;</span>
	<span class="token punctuation">}</span> <span class="token keyword">else</span> <span class="token keyword">if</span> <span class="token punctuation">(</span>to_submit<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		ret <span class="token operator">=</span> io_uring_add_task_file<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> f<span class="token punctuation">.</span><span class="token builtin">file</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>unlikely<span class="token punctuation">(</span>ret<span class="token punctuation">)</span><span class="token punctuation">)</span>
			goto out<span class="token punctuation">;</span>
		mutex_lock<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>uring_lock<span class="token punctuation">)</span><span class="token punctuation">;</span>
		submitted <span class="token operator">=</span> io_submit_sqes<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> to_submit<span class="token punctuation">)</span><span class="token punctuation">;</span>
		mutex_unlock<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>uring_lock<span class="token punctuation">)</span><span class="token punctuation">;</span>

		<span class="token keyword">if</span> <span class="token punctuation">(</span>submitted <span class="token operator">!=</span> to_submit<span class="token punctuation">)</span>
			goto out<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>flags <span class="token operator">&amp;</span> IORING_ENTER_GETEVENTS<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		min_complete <span class="token operator">=</span> <span class="token builtin">min</span><span class="token punctuation">(</span>min_complete<span class="token punctuation">,</span> ctx<span class="token operator">-</span><span class="token operator">&gt;</span>cq_entries<span class="token punctuation">)</span><span class="token punctuation">;</span>

		<span class="token operator">/</span><span class="token operator">*</span>
		 <span class="token operator">*</span> When SETUP_IOPOLL <span class="token keyword">and</span> SETUP_SQPOLL are both enabled<span class="token punctuation">,</span> user
		 <span class="token operator">*</span> space applications don't need to do io completion events
		 <span class="token operator">*</span> polling again<span class="token punctuation">,</span> they can rely on io_sq_thread to do polling
		 <span class="token operator">*</span> work<span class="token punctuation">,</span> which can <span class="token builtin">reduce</span> cpu usage <span class="token keyword">and</span> uring_lock contention<span class="token punctuation">.</span>
		 <span class="token operator">*</span><span class="token operator">/</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_IOPOLL <span class="token operator">&amp;</span><span class="token operator">&amp;</span>
		    !<span class="token punctuation">(</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_SQPOLL<span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
			ret <span class="token operator">=</span> io_iopoll_check<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> min_complete<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token punctuation">}</span> <span class="token keyword">else</span> <span class="token punctuation">{</span>
			ret <span class="token operator">=</span> io_cqring_wait<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> min_complete<span class="token punctuation">,</span> sig<span class="token punctuation">,</span> sigsz<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
	<span class="token punctuation">}</span>

out<span class="token punctuation">:</span>
	percpu_ref_put<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>refs<span class="token punctuation">)</span><span class="token punctuation">;</span>
out_fput<span class="token punctuation">:</span>
	fdput<span class="token punctuation">(</span>f<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> submitted ? submitted <span class="token punctuation">:</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>io_iopoll_complete实现</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> Find <span class="token keyword">and</span> free completed poll iocbs
 <span class="token operator">*</span><span class="token operator">/</span>
static void io_iopoll_complete<span class="token punctuation">(</span>struct io_ring_ctx <span class="token operator">*</span>ctx<span class="token punctuation">,</span> unsigned <span class="token builtin">int</span> <span class="token operator">*</span>nr_events<span class="token punctuation">,</span>
			       struct list_head <span class="token operator">*</span>done<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	struct req_batch rb<span class="token punctuation">;</span>
	struct io_kiocb <span class="token operator">*</span>req<span class="token punctuation">;</span>
	LIST_HEAD<span class="token punctuation">(</span>again<span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span> order <span class="token keyword">with</span> <span class="token operator">-</span><span class="token operator">&gt;</span>result store <span class="token keyword">in</span> io_complete_rw_iopoll<span class="token punctuation">(</span><span class="token punctuation">)</span> <span class="token operator">*</span><span class="token operator">/</span>
	smp_rmb<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>

	io_init_req_batch<span class="token punctuation">(</span><span class="token operator">&amp;</span>rb<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">while</span> <span class="token punctuation">(</span>!list_empty<span class="token punctuation">(</span>done<span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token builtin">int</span> cflags <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>

		req <span class="token operator">=</span> list_first_entry<span class="token punctuation">(</span>done<span class="token punctuation">,</span> struct io_kiocb<span class="token punctuation">,</span> inflight_entry<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>READ_ONCE<span class="token punctuation">(</span>req<span class="token operator">-</span><span class="token operator">&gt;</span>result<span class="token punctuation">)</span> <span class="token operator">==</span> <span class="token operator">-</span>EAGAIN<span class="token punctuation">)</span> <span class="token punctuation">{</span>
			req<span class="token operator">-</span><span class="token operator">&gt;</span>result <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
			req<span class="token operator">-</span><span class="token operator">&gt;</span>iopoll_completed <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
			list_move_tail<span class="token punctuation">(</span><span class="token operator">&amp;</span>req<span class="token operator">-</span><span class="token operator">&gt;</span>inflight_entry<span class="token punctuation">,</span> <span class="token operator">&amp;</span>again<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token keyword">continue</span><span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
		list_del<span class="token punctuation">(</span><span class="token operator">&amp;</span>req<span class="token operator">-</span><span class="token operator">&gt;</span>inflight_entry<span class="token punctuation">)</span><span class="token punctuation">;</span>

		<span class="token keyword">if</span> <span class="token punctuation">(</span>req<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> REQ_F_BUFFER_SELECTED<span class="token punctuation">)</span>
			cflags <span class="token operator">=</span> io_put_rw_kbuf<span class="token punctuation">(</span>req<span class="token punctuation">)</span><span class="token punctuation">;</span>

		__io_cqring_fill_event<span class="token punctuation">(</span>req<span class="token punctuation">,</span> req<span class="token operator">-</span><span class="token operator">&gt;</span>result<span class="token punctuation">,</span> cflags<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token punctuation">(</span><span class="token operator">*</span>nr_events<span class="token punctuation">)</span><span class="token operator">+</span><span class="token operator">+</span><span class="token punctuation">;</span>

		<span class="token keyword">if</span> <span class="token punctuation">(</span>refcount_dec_and_test<span class="token punctuation">(</span><span class="token operator">&amp;</span>req<span class="token operator">-</span><span class="token operator">&gt;</span>refs<span class="token punctuation">)</span><span class="token punctuation">)</span>
			io_req_free_batch<span class="token punctuation">(</span><span class="token operator">&amp;</span>rb<span class="token punctuation">,</span> req<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	io_commit_cqring<span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_SQPOLL<span class="token punctuation">)</span>
		io_cqring_ev_posted<span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
	io_req_free_batch_finish<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> <span class="token operator">&amp;</span>rb<span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span>!list_empty<span class="token punctuation">(</span><span class="token operator">&amp;</span>again<span class="token punctuation">)</span><span class="token punctuation">)</span>
		io_iopoll_queue<span class="token punctuation">(</span><span class="token operator">&amp;</span>again<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>io_get_cqring实现</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">static struct io_uring_cqe <span class="token operator">*</span>io_get_cqring<span class="token punctuation">(</span>struct io_ring_ctx <span class="token operator">*</span>ctx<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	struct io_rings <span class="token operator">*</span>rings <span class="token operator">=</span> ctx<span class="token operator">-</span><span class="token operator">&gt;</span>rings<span class="token punctuation">;</span>
	unsigned tail<span class="token punctuation">;</span>

	tail <span class="token operator">=</span> ctx<span class="token operator">-</span><span class="token operator">&gt;</span>cached_cq_tail<span class="token punctuation">;</span>
	<span class="token operator">/</span><span class="token operator">*</span>
	 <span class="token operator">*</span> writes to the cq entry need to come after reading head<span class="token punctuation">;</span> the
	 <span class="token operator">*</span> control dependency <span class="token keyword">is</span> enough <span class="token keyword">as</span> we're using WRITE_ONCE to
	 <span class="token operator">*</span> fill the cq entry
	 <span class="token operator">*</span><span class="token operator">/</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>tail <span class="token operator">-</span> READ_ONCE<span class="token punctuation">(</span>rings<span class="token operator">-</span><span class="token operator">&gt;</span>cq<span class="token punctuation">.</span>head<span class="token punctuation">)</span> <span class="token operator">==</span> rings<span class="token operator">-</span><span class="token operator">&gt;</span>cq_ring_entries<span class="token punctuation">)</span>
		<span class="token keyword">return</span> NULL<span class="token punctuation">;</span>

	ctx<span class="token operator">-</span><span class="token operator">&gt;</span>cached_cq_tail<span class="token operator">+</span><span class="token operator">+</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> <span class="token operator">&amp;</span>rings<span class="token operator">-</span><span class="token operator">&gt;</span>cqes<span class="token punctuation">[</span>tail <span class="token operator">&amp;</span> ctx<span class="token operator">-</span><span class="token operator">&gt;</span>cq_mask<span class="token punctuation">]</span><span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="IO收割">IO收割</h3>

<p>来都来了，搞点事情吧，在我们提交IO的同时，使用同一个io_uring_enter系统调用就可以回收完成状态，这样的好处就是一次系统调用接口就完成了原本需要两次系统调用的工作，大大的减少了系统调用的次数，也就是减少了内核核外的切换，这是一个很明显的优化，内核与核外的切换极其耗时。</p>

<p>当IO完成时，内核负责将完成IO在SQEs中的index放到CQ中。由于IO在提交的时候可以顺便返回完成的IO，所以收割IO不需要额外系统调用。</p>

<p>如果使用了IORING_SETUP_SQPOLL参数，IO收割也不需要系统调用的参与。由于内核和用户态共享内存，所以收割的时候，用户态遍历[cring-&gt;head, cring-&gt;tail)区间，即已经完成的IO队列，然后找到相应的CQE并进行处理，最后移动head指针到tail，IO收割至此而终。</p>

<p>所以，在最理想的情况下，IO提交和收割都不需要使用系统调用。</p>

<h2 id="高级特性">高级特性</h2>

<p>此外，我们可以使用一些优化思想，进行更进一步的优化，这些优化，以一种可选的方式成为io_uring的其它一些高级特性。</p>

<h3 id="Fixed-Files模式">Fixed Files模式</h3>

<h4 id="优化思想">优化思想</h4>

<p>非关键逻辑上提至循环外，简化关键路径。</p>

<h4 id="优化实现">优化实现</h4>

<p>可以调用io_uring_register系统调用，使用IORING_REGISTER_FILES操作码，将一组file注册到内核，最终调用io_sqe_files_register，这样内核在注册阶段就批量完成文件的一些基本操作（对于这组文件填充相应的数据结构fixed_file_data，其中fixed_file_table是维护的file表。内核态下，如何获得文件描述符获取相关的信息呢，就需要通过fget，根据fd号获得指向文件的struct file），之后的再次批量IO时就不需要重复地进行此类基本信息设置（更具体地，例如对文件进行fget/fput操作）。如果需要进行IO操作的文件相对固定（比如数据库日志），这会节省一定量的IO时间。</p>

<h4 id="fixed_file_data结构">fixed_file_data结构</h4>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token keyword">struct</span> <span class="token class-name">fixed_file_data</span> <span class="token punctuation">{</span>
	<span class="token keyword">struct</span> <span class="token class-name">fixed_file_table</span>		<span class="token operator">*</span>table<span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_ring_ctx</span>		<span class="token operator">*</span>ctx<span class="token punctuation">;</span>

	<span class="token keyword">struct</span> <span class="token class-name">fixed_file_ref_node</span>	<span class="token operator">*</span>node<span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">percpu_ref</span>		refs<span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">completion</span>		done<span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">list_head</span>		ref_list<span class="token punctuation">;</span>
	spinlock_t			lock<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<h4 id="io_sqe_files_register实现Fixed-Files操作">io_sqe_files_register实现Fixed Files操作</h4>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token keyword">static</span> <span class="token keyword">int</span> <span class="token function">io_sqe_files_register</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_ring_ctx</span> <span class="token operator">*</span>ctx<span class="token punctuation">,</span> <span class="token keyword">void</span> __user <span class="token operator">*</span>arg<span class="token punctuation">,</span>
				 <span class="token keyword">unsigned</span> nr_args<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	__s32 __user <span class="token operator">*</span>fds <span class="token operator">=</span> <span class="token punctuation">(</span>__s32 __user <span class="token operator">*</span><span class="token punctuation">)</span> arg<span class="token punctuation">;</span>
	<span class="token keyword">unsigned</span> nr_tables<span class="token punctuation">,</span> i<span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">file</span> <span class="token operator">*</span>file<span class="token punctuation">;</span>
	<span class="token keyword">int</span> fd<span class="token punctuation">,</span> ret <span class="token operator">=</span> <span class="token operator">-</span>ENOMEM<span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">fixed_file_ref_node</span> <span class="token operator">*</span>ref_node<span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">fixed_file_data</span> <span class="token operator">*</span>file_data<span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span>ctx<span class="token operator">-&gt;</span>file_data<span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EBUSY<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>nr_args<span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>nr_args <span class="token operator">&gt;</span> IORING_MAX_FIXED_FILES<span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EMFILE<span class="token punctuation">;</span>

	file_data <span class="token operator">=</span> <span class="token function">kzalloc</span><span class="token punctuation">(</span><span class="token keyword">sizeof</span><span class="token punctuation">(</span><span class="token operator">*</span>ctx<span class="token operator">-&gt;</span>file_data<span class="token punctuation">)</span><span class="token punctuation">,</span> GFP_KERNEL<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>file_data<span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>ENOMEM<span class="token punctuation">;</span>
	file_data<span class="token operator">-&gt;</span>ctx <span class="token operator">=</span> ctx<span class="token punctuation">;</span>
	<span class="token function">init_completion</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>done<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">INIT_LIST_HEAD</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>ref_list<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">spin_lock_init</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>lock<span class="token punctuation">)</span><span class="token punctuation">;</span>

	nr_tables <span class="token operator">=</span> <span class="token function">DIV_ROUND_UP</span><span class="token punctuation">(</span>nr_args<span class="token punctuation">,</span> IORING_MAX_FILES_TABLE<span class="token punctuation">)</span><span class="token punctuation">;</span>
	file_data<span class="token operator">-&gt;</span>table <span class="token operator">=</span> <span class="token function">kcalloc</span><span class="token punctuation">(</span>nr_tables<span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span><span class="token operator">*</span>file_data<span class="token operator">-&gt;</span>table<span class="token punctuation">)</span><span class="token punctuation">,</span>
				   GFP_KERNEL<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>file_data<span class="token operator">-&gt;</span>table<span class="token punctuation">)</span>
		<span class="token keyword">goto</span> out_free<span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token function">percpu_ref_init</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>refs<span class="token punctuation">,</span> io_file_ref_kill<span class="token punctuation">,</span>
				PERCPU_REF_ALLOW_REINIT<span class="token punctuation">,</span> GFP_KERNEL<span class="token punctuation">)</span><span class="token punctuation">)</span>
		<span class="token keyword">goto</span> out_free<span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token function">io_sqe_alloc_file_tables</span><span class="token punctuation">(</span>file_data<span class="token punctuation">,</span> nr_tables<span class="token punctuation">,</span> nr_args<span class="token punctuation">)</span><span class="token punctuation">)</span>
		<span class="token keyword">goto</span> out_ref<span class="token punctuation">;</span>
	ctx<span class="token operator">-&gt;</span>file_data <span class="token operator">=</span> file_data<span class="token punctuation">;</span>

	<span class="token keyword">for</span> <span class="token punctuation">(</span>i <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span> i <span class="token operator">&lt;</span> nr_args<span class="token punctuation">;</span> i<span class="token operator">++</span><span class="token punctuation">,</span> ctx<span class="token operator">-&gt;</span>nr_user_files<span class="token operator">++</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token keyword">struct</span> <span class="token class-name">fixed_file_table</span> <span class="token operator">*</span>table<span class="token punctuation">;</span>
		<span class="token keyword">unsigned</span> index<span class="token punctuation">;</span>

		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token function">copy_from_user</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>fd<span class="token punctuation">,</span> <span class="token operator">&amp;</span>fds<span class="token punctuation">[</span>i<span class="token punctuation">]</span><span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span>fd<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
			ret <span class="token operator">=</span> <span class="token operator">-</span>EFAULT<span class="token punctuation">;</span>
			<span class="token keyword">goto</span> out_fput<span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
		<span class="token comment">/* allow sparse sets */</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>fd <span class="token operator">==</span> <span class="token operator">-</span><span class="token number">1</span><span class="token punctuation">)</span>
			<span class="token keyword">continue</span><span class="token punctuation">;</span>

		file <span class="token operator">=</span> <span class="token function">fget</span><span class="token punctuation">(</span>fd<span class="token punctuation">)</span><span class="token punctuation">;</span>
		ret <span class="token operator">=</span> <span class="token operator">-</span>EBADF<span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>file<span class="token punctuation">)</span>
			<span class="token keyword">goto</span> out_fput<span class="token punctuation">;</span>

		<span class="token comment">/*
		 * Don't allow io_uring instances to be registered. If UNIX
		 * isn't enabled, then this causes a reference cycle and this
		 * instance can never get freed. If UNIX is enabled we'll
		 * handle it just fine, but there's still no point in allowing
		 * a ring fd as it doesn't support regular read/write anyway.
		 */</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>file<span class="token operator">-&gt;</span>f_op <span class="token operator">==</span> <span class="token operator">&amp;</span>io_uring_fops<span class="token punctuation">)</span> <span class="token punctuation">{</span>
			<span class="token function">fput</span><span class="token punctuation">(</span>file<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token keyword">goto</span> out_fput<span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
		table <span class="token operator">=</span> <span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>table<span class="token punctuation">[</span>i <span class="token operator">&gt;&gt;</span> IORING_FILE_TABLE_SHIFT<span class="token punctuation">]</span><span class="token punctuation">;</span>
		index <span class="token operator">=</span> i <span class="token operator">&amp;</span> IORING_FILE_TABLE_MASK<span class="token punctuation">;</span>
		table<span class="token operator">-&gt;</span>files<span class="token punctuation">[</span>index<span class="token punctuation">]</span> <span class="token operator">=</span> file<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	ret <span class="token operator">=</span> <span class="token function">io_sqe_files_scm</span><span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ret<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token function">io_sqe_files_unregister</span><span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	ref_node <span class="token operator">=</span> <span class="token function">alloc_fixed_file_ref_node</span><span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token function">IS_ERR</span><span class="token punctuation">(</span>ref_node<span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token function">io_sqe_files_unregister</span><span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">return</span> <span class="token function">PTR_ERR</span><span class="token punctuation">(</span>ref_node<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	file_data<span class="token operator">-&gt;</span>node <span class="token operator">=</span> ref_node<span class="token punctuation">;</span>
	<span class="token function">spin_lock</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>lock<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">list_add_tail</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>ref_node<span class="token operator">-&gt;</span>node<span class="token punctuation">,</span> <span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>ref_list<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">spin_unlock</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>lock<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">percpu_ref_get</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>refs<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
out_fput<span class="token operator">:</span>
	<span class="token keyword">for</span> <span class="token punctuation">(</span>i <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span> i <span class="token operator">&lt;</span> ctx<span class="token operator">-&gt;</span>nr_user_files<span class="token punctuation">;</span> i<span class="token operator">++</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
		file <span class="token operator">=</span> <span class="token function">io_file_from_index</span><span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> i<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>file<span class="token punctuation">)</span>
			<span class="token function">fput</span><span class="token punctuation">(</span>file<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token punctuation">}</span>
	<span class="token keyword">for</span> <span class="token punctuation">(</span>i <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span> i <span class="token operator">&lt;</span> nr_tables<span class="token punctuation">;</span> i<span class="token operator">++</span><span class="token punctuation">)</span>
		<span class="token function">kfree</span><span class="token punctuation">(</span>file_data<span class="token operator">-&gt;</span>table<span class="token punctuation">[</span>i<span class="token punctuation">]</span><span class="token punctuation">.</span>files<span class="token punctuation">)</span><span class="token punctuation">;</span>
	ctx<span class="token operator">-&gt;</span>nr_user_files <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
out_ref<span class="token operator">:</span>
	<span class="token function">percpu_ref_exit</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>file_data<span class="token operator">-&gt;</span>refs<span class="token punctuation">)</span><span class="token punctuation">;</span>
out_free<span class="token operator">:</span>
	<span class="token function">kfree</span><span class="token punctuation">(</span>file_data<span class="token operator">-&gt;</span>table<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">kfree</span><span class="token punctuation">(</span>file_data<span class="token punctuation">)</span><span class="token punctuation">;</span>
	ctx<span class="token operator">-&gt;</span>file_data <span class="token operator">=</span> <span class="token constant">NULL</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="Fixed-Buffers模式">Fixed Buffers模式</h3>

<h4 id="优化思想">优化思想</h4>

<p>优化思想也是将非关键逻辑上提至循环外，简化关键路径。</p>

<h4 id="优化实现">优化实现</h4>

<p>如果应用提交到内核的虚拟内存地址是固定的，那么可以提前完成虚拟地址到物理pages的映射，将这个并不是每次都要做的非关键路径从关键的IO 路径中剥离，避免每次I/O都进行转换，从而优化性能。可以在io_uring_setup之后，调用io_uring_register，使用IORING_REGISTER_BUFFERS 操作码，将一组buffer注册到内核（参数是一个指向iovec的数组，表示这些地址需要map到内核），最终调用io_sqe_buffer_register，这样内核在注册阶段就批量完成buffer的一些基本操作（减小get_user_pages、put_page开销，提前使用get_user_pages来获得userspace虚拟地址对应的物理pages，初始化在io_ring_ctx上下文中用于管理用户态buffer的io_mapped_ubuf数据结构，map/unmap，传递IOV的地址和长度等），之后的再次批量IO时就不需要重复地进行此类内存拷贝和基础信息检测。在操作IO的时，如果需要进行IO操作的buffer相对固定，提交的虚拟地址曾经被注册过，那么可以使用带FIXED系列的opcode（IORING_OP_READ_FIXED/IORING_OP_WRITE_FIXED）IO，可以看到底层调用链：io_issue_sqe-&gt;io_read-&gt;io_import_iovec-&gt;__io_import_iovec-&gt;io_import_fixed，会直接使用已经完成的“成果”，如此就免去了虚拟地址到pages的转换，这会节省一定量的IO时间。</p>

<h4 id="io_mapped_ubuf结构">io_mapped_ubuf结构</h4>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token keyword">struct</span> <span class="token class-name">io_mapped_ubuf</span> <span class="token punctuation">{</span>
	u64		ubuf<span class="token punctuation">;</span>
	size_t		len<span class="token punctuation">;</span>
	<span class="token keyword">struct</span>		<span class="token class-name">bio_vec</span> <span class="token operator">*</span>bvec<span class="token punctuation">;</span>
	<span class="token keyword">unsigned</span> <span class="token keyword">int</span>	nr_bvecs<span class="token punctuation">;</span>
	<span class="token keyword">unsigned</span> <span class="token keyword">long</span>	acct_pages<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<h4 id="io_sqe_buffer_register实现Fixed-Buffers操作">io_sqe_buffer_register实现Fixed Buffers操作</h4>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token keyword">static</span> <span class="token keyword">int</span> <span class="token function">io_sqe_buffer_register</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_ring_ctx</span> <span class="token operator">*</span>ctx<span class="token punctuation">,</span> <span class="token keyword">void</span> __user <span class="token operator">*</span>arg<span class="token punctuation">,</span>
				  <span class="token keyword">unsigned</span> nr_args<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	<span class="token keyword">struct</span> <span class="token class-name">vm_area_struct</span> <span class="token operator">*</span><span class="token operator">*</span>vmas <span class="token operator">=</span> <span class="token constant">NULL</span><span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">page</span> <span class="token operator">*</span><span class="token operator">*</span>pages <span class="token operator">=</span> <span class="token constant">NULL</span><span class="token punctuation">;</span>
	<span class="token keyword">struct</span> <span class="token class-name">page</span> <span class="token operator">*</span>last_hpage <span class="token operator">=</span> <span class="token constant">NULL</span><span class="token punctuation">;</span>
	<span class="token keyword">int</span> i<span class="token punctuation">,</span> j<span class="token punctuation">,</span> got_pages <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
	<span class="token keyword">int</span> ret <span class="token operator">=</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span>ctx<span class="token operator">-&gt;</span>user_bufs<span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EBUSY<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>nr_args <span class="token operator">||</span> nr_args <span class="token operator">&gt;</span> UIO_MAXIOV<span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>

	ctx<span class="token operator">-&gt;</span>user_bufs <span class="token operator">=</span> <span class="token function">kcalloc</span><span class="token punctuation">(</span>nr_args<span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_mapped_ubuf</span><span class="token punctuation">)</span><span class="token punctuation">,</span>
					GFP_KERNEL<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>ctx<span class="token operator">-&gt;</span>user_bufs<span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>ENOMEM<span class="token punctuation">;</span>

	<span class="token keyword">for</span> <span class="token punctuation">(</span>i <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span> i <span class="token operator">&lt;</span> nr_args<span class="token punctuation">;</span> i<span class="token operator">++</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token keyword">struct</span> <span class="token class-name">io_mapped_ubuf</span> <span class="token operator">*</span>imu <span class="token operator">=</span> <span class="token operator">&amp;</span>ctx<span class="token operator">-&gt;</span>user_bufs<span class="token punctuation">[</span>i<span class="token punctuation">]</span><span class="token punctuation">;</span>
		<span class="token keyword">unsigned</span> <span class="token keyword">long</span> off<span class="token punctuation">,</span> start<span class="token punctuation">,</span> end<span class="token punctuation">,</span> ubuf<span class="token punctuation">;</span>
		<span class="token keyword">int</span> pret<span class="token punctuation">,</span> nr_pages<span class="token punctuation">;</span>
		<span class="token keyword">struct</span> <span class="token class-name">iovec</span> iov<span class="token punctuation">;</span>
		size_t size<span class="token punctuation">;</span>

		ret <span class="token operator">=</span> <span class="token function">io_copy_iov</span><span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> <span class="token operator">&amp;</span>iov<span class="token punctuation">,</span> arg<span class="token punctuation">,</span> i<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>ret<span class="token punctuation">)</span>
			<span class="token keyword">goto</span> err<span class="token punctuation">;</span>

		<span class="token comment">/*
		 * Don't impose further limits on the size and buffer
		 * constraints here, we'll -EINVAL later when IO is
		 * submitted if they are wrong.
		 */</span>
		ret <span class="token operator">=</span> <span class="token operator">-</span>EFAULT<span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>iov<span class="token punctuation">.</span>iov_base <span class="token operator">||</span> <span class="token operator">!</span>iov<span class="token punctuation">.</span>iov_len<span class="token punctuation">)</span>
			<span class="token keyword">goto</span> err<span class="token punctuation">;</span>

		<span class="token comment">/* arbitrary limit, but we need something */</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>iov<span class="token punctuation">.</span>iov_len <span class="token operator">&gt;</span> SZ_1G<span class="token punctuation">)</span>
			<span class="token keyword">goto</span> err<span class="token punctuation">;</span>

		ubuf <span class="token operator">=</span> <span class="token punctuation">(</span><span class="token keyword">unsigned</span> <span class="token keyword">long</span><span class="token punctuation">)</span> iov<span class="token punctuation">.</span>iov_base<span class="token punctuation">;</span>
		end <span class="token operator">=</span> <span class="token punctuation">(</span>ubuf <span class="token operator">+</span> iov<span class="token punctuation">.</span>iov_len <span class="token operator">+</span> PAGE_SIZE <span class="token operator">-</span> <span class="token number">1</span><span class="token punctuation">)</span> <span class="token operator">&gt;&gt;</span> PAGE_SHIFT<span class="token punctuation">;</span>
		start <span class="token operator">=</span> ubuf <span class="token operator">&gt;&gt;</span> PAGE_SHIFT<span class="token punctuation">;</span>
		nr_pages <span class="token operator">=</span> end <span class="token operator">-</span> start<span class="token punctuation">;</span>

		ret <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>pages <span class="token operator">||</span> nr_pages <span class="token operator">&gt;</span> got_pages<span class="token punctuation">)</span> <span class="token punctuation">{</span>
			<span class="token function">kvfree</span><span class="token punctuation">(</span>vmas<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token function">kvfree</span><span class="token punctuation">(</span>pages<span class="token punctuation">)</span><span class="token punctuation">;</span>
			pages <span class="token operator">=</span> <span class="token function">kvmalloc_array</span><span class="token punctuation">(</span>nr_pages<span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">page</span> <span class="token operator">*</span><span class="token punctuation">)</span><span class="token punctuation">,</span>
						GFP_KERNEL<span class="token punctuation">)</span><span class="token punctuation">;</span>
			vmas <span class="token operator">=</span> <span class="token function">kvmalloc_array</span><span class="token punctuation">(</span>nr_pages<span class="token punctuation">,</span>
					<span class="token keyword">sizeof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">vm_area_struct</span> <span class="token operator">*</span><span class="token punctuation">)</span><span class="token punctuation">,</span>
					GFP_KERNEL<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>pages <span class="token operator">||</span> <span class="token operator">!</span>vmas<span class="token punctuation">)</span> <span class="token punctuation">{</span>
				ret <span class="token operator">=</span> <span class="token operator">-</span>ENOMEM<span class="token punctuation">;</span>
				<span class="token keyword">goto</span> err<span class="token punctuation">;</span>
			<span class="token punctuation">}</span>
			got_pages <span class="token operator">=</span> nr_pages<span class="token punctuation">;</span>
		<span class="token punctuation">}</span>

		imu<span class="token operator">-&gt;</span>bvec <span class="token operator">=</span> <span class="token function">kvmalloc_array</span><span class="token punctuation">(</span>nr_pages<span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">bio_vec</span><span class="token punctuation">)</span><span class="token punctuation">,</span>
						GFP_KERNEL<span class="token punctuation">)</span><span class="token punctuation">;</span>
		ret <span class="token operator">=</span> <span class="token operator">-</span>ENOMEM<span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>imu<span class="token operator">-&gt;</span>bvec<span class="token punctuation">)</span>
			<span class="token keyword">goto</span> err<span class="token punctuation">;</span>

		ret <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
		<span class="token function">mmap_read_lock</span><span class="token punctuation">(</span>current<span class="token operator">-&gt;</span>mm<span class="token punctuation">)</span><span class="token punctuation">;</span>
		pret <span class="token operator">=</span> <span class="token function">pin_user_pages</span><span class="token punctuation">(</span>ubuf<span class="token punctuation">,</span> nr_pages<span class="token punctuation">,</span>
				      FOLL_WRITE <span class="token operator">|</span> FOLL_LONGTERM<span class="token punctuation">,</span>
				      pages<span class="token punctuation">,</span> vmas<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>pret <span class="token operator">==</span> nr_pages<span class="token punctuation">)</span> <span class="token punctuation">{</span>
			<span class="token comment">/* don't support file backed memory */</span>
			<span class="token keyword">for</span> <span class="token punctuation">(</span>j <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span> j <span class="token operator">&lt;</span> nr_pages<span class="token punctuation">;</span> j<span class="token operator">++</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
				<span class="token keyword">struct</span> <span class="token class-name">vm_area_struct</span> <span class="token operator">*</span>vma <span class="token operator">=</span> vmas<span class="token punctuation">[</span>j<span class="token punctuation">]</span><span class="token punctuation">;</span>

				<span class="token keyword">if</span> <span class="token punctuation">(</span>vma<span class="token operator">-&gt;</span>vm_file <span class="token operator">&amp;&amp;</span>
				    <span class="token operator">!</span><span class="token function">is_file_hugepages</span><span class="token punctuation">(</span>vma<span class="token operator">-&gt;</span>vm_file<span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
					ret <span class="token operator">=</span> <span class="token operator">-</span>EOPNOTSUPP<span class="token punctuation">;</span>
					<span class="token keyword">break</span><span class="token punctuation">;</span>
				<span class="token punctuation">}</span>
			<span class="token punctuation">}</span>
		<span class="token punctuation">}</span> <span class="token keyword">else</span> <span class="token punctuation">{</span>
			ret <span class="token operator">=</span> pret <span class="token operator">&lt;</span> <span class="token number">0</span> <span class="token operator">?</span> pret <span class="token operator">:</span> <span class="token operator">-</span>EFAULT<span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
		<span class="token function">mmap_read_unlock</span><span class="token punctuation">(</span>current<span class="token operator">-&gt;</span>mm<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>ret<span class="token punctuation">)</span> <span class="token punctuation">{</span>
			<span class="token comment">/*
			 * if we did partial map, or found file backed vmas,
			 * release any pages we did get
			 */</span>
			<span class="token keyword">if</span> <span class="token punctuation">(</span>pret <span class="token operator">&gt;</span> <span class="token number">0</span><span class="token punctuation">)</span>
				<span class="token function">unpin_user_pages</span><span class="token punctuation">(</span>pages<span class="token punctuation">,</span> pret<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token function">kvfree</span><span class="token punctuation">(</span>imu<span class="token operator">-&gt;</span>bvec<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token keyword">goto</span> err<span class="token punctuation">;</span>
		<span class="token punctuation">}</span>

		ret <span class="token operator">=</span> <span class="token function">io_buffer_account_pin</span><span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> pages<span class="token punctuation">,</span> pret<span class="token punctuation">,</span> imu<span class="token punctuation">,</span> <span class="token operator">&amp;</span>last_hpage<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>ret<span class="token punctuation">)</span> <span class="token punctuation">{</span>
			<span class="token function">unpin_user_pages</span><span class="token punctuation">(</span>pages<span class="token punctuation">,</span> pret<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token function">kvfree</span><span class="token punctuation">(</span>imu<span class="token operator">-&gt;</span>bvec<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token keyword">goto</span> err<span class="token punctuation">;</span>
		<span class="token punctuation">}</span>

		off <span class="token operator">=</span> ubuf <span class="token operator">&amp;</span> <span class="token operator">~</span>PAGE_MASK<span class="token punctuation">;</span>
		size <span class="token operator">=</span> iov<span class="token punctuation">.</span>iov_len<span class="token punctuation">;</span>
		<span class="token keyword">for</span> <span class="token punctuation">(</span>j <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span> j <span class="token operator">&lt;</span> nr_pages<span class="token punctuation">;</span> j<span class="token operator">++</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
			size_t vec_len<span class="token punctuation">;</span>

			vec_len <span class="token operator">=</span> <span class="token function">min_t</span><span class="token punctuation">(</span>size_t<span class="token punctuation">,</span> size<span class="token punctuation">,</span> PAGE_SIZE <span class="token operator">-</span> off<span class="token punctuation">)</span><span class="token punctuation">;</span>
			imu<span class="token operator">-&gt;</span>bvec<span class="token punctuation">[</span>j<span class="token punctuation">]</span><span class="token punctuation">.</span>bv_page <span class="token operator">=</span> pages<span class="token punctuation">[</span>j<span class="token punctuation">]</span><span class="token punctuation">;</span>
			imu<span class="token operator">-&gt;</span>bvec<span class="token punctuation">[</span>j<span class="token punctuation">]</span><span class="token punctuation">.</span>bv_len <span class="token operator">=</span> vec_len<span class="token punctuation">;</span>
			imu<span class="token operator">-&gt;</span>bvec<span class="token punctuation">[</span>j<span class="token punctuation">]</span><span class="token punctuation">.</span>bv_offset <span class="token operator">=</span> off<span class="token punctuation">;</span>
			off <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
			size <span class="token operator">-=</span> vec_len<span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
		<span class="token comment">/* store original address for later verification */</span>
		imu<span class="token operator">-&gt;</span>ubuf <span class="token operator">=</span> ubuf<span class="token punctuation">;</span>
		imu<span class="token operator">-&gt;</span>len <span class="token operator">=</span> iov<span class="token punctuation">.</span>iov_len<span class="token punctuation">;</span>
		imu<span class="token operator">-&gt;</span>nr_bvecs <span class="token operator">=</span> nr_pages<span class="token punctuation">;</span>

		ctx<span class="token operator">-&gt;</span>nr_user_bufs<span class="token operator">++</span><span class="token punctuation">;</span>
	<span class="token punctuation">}</span>
	<span class="token function">kvfree</span><span class="token punctuation">(</span>pages<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">kvfree</span><span class="token punctuation">(</span>vmas<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> <span class="token number">0</span><span class="token punctuation">;</span>
err<span class="token operator">:</span>
	<span class="token function">kvfree</span><span class="token punctuation">(</span>pages<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">kvfree</span><span class="token punctuation">(</span>vmas<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token function">io_sqe_buffer_unregister</span><span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="Polled-IO模式">Polled IO模式</h3>

<h4 id="优化思想">优化思想</h4>

<p>将较多的CPU时间放到重要的事情上，全速完成关键路径。</p>

<p>状态从未完成变成已完成，就需要对完成状态进行探测，很多时候，可以使用中断模型，也就是等待后端数据处理完毕之后，内核会发起一个SIGIO或eventfd的EPOLLIN状态提醒核外有数据已经完成了，可以开始处理。但是，中断其实是比较耗时的，如果是高IOPS的场景，就会不停地中断，中断开销就得不偿失。</p>

<p>我们可以更激进一些，让内核采用Polled IO模式收割块设备层请求。这在一定的程度上加速了IO，这在追求低延时和高IOPS的应用场景非常有用。</p>

<h4 id="优化实现">优化实现</h4>

<p>io_uring_enter通过正确设置IORING_ENTER_GETEVENTS，IORING_SETUP_IOPOLL等flag（如下代码设置IORING_SETUP_IOPOLL并且不设置IORING_SETUP_SQPOLL，即没有使用SQ线程）调用io_iopoll_check。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">SYSCALL_DEFINE6<span class="token punctuation">(</span>io_uring_enter<span class="token punctuation">,</span> unsigned <span class="token builtin">int</span><span class="token punctuation">,</span> fd<span class="token punctuation">,</span> u32<span class="token punctuation">,</span> to_submit<span class="token punctuation">,</span>
		u32<span class="token punctuation">,</span> min_complete<span class="token punctuation">,</span> u32<span class="token punctuation">,</span> flags<span class="token punctuation">,</span> const sigset_t __user <span class="token operator">*</span><span class="token punctuation">,</span> sig<span class="token punctuation">,</span>
		size_t<span class="token punctuation">,</span> sigsz<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	struct io_ring_ctx <span class="token operator">*</span>ctx<span class="token punctuation">;</span>
	<span class="token builtin">long</span> ret <span class="token operator">=</span> <span class="token operator">-</span>EBADF<span class="token punctuation">;</span>
	<span class="token builtin">int</span> submitted <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
	struct fd f<span class="token punctuation">;</span>

	io_run_task_work<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span>flags <span class="token operator">&amp;</span> <span class="token operator">~</span><span class="token punctuation">(</span>IORING_ENTER_GETEVENTS <span class="token operator">|</span> IORING_ENTER_SQ_WAKEUP <span class="token operator">|</span>
			IORING_ENTER_SQ_WAIT<span class="token punctuation">)</span><span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EINVAL<span class="token punctuation">;</span>

	f <span class="token operator">=</span> fdget<span class="token punctuation">(</span>fd<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>!f<span class="token punctuation">.</span><span class="token builtin">file</span><span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>EBADF<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token operator">-</span>EOPNOTSUPP<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>f<span class="token punctuation">.</span><span class="token builtin">file</span><span class="token operator">-</span><span class="token operator">&gt;</span>f_op <span class="token operator">!=</span> <span class="token operator">&amp;</span>io_uring_fops<span class="token punctuation">)</span>
		goto out_fput<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token operator">-</span>ENXIO<span class="token punctuation">;</span>
	ctx <span class="token operator">=</span> f<span class="token punctuation">.</span><span class="token builtin">file</span><span class="token operator">-</span><span class="token operator">&gt;</span>private_data<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>!percpu_ref_tryget<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>refs<span class="token punctuation">)</span><span class="token punctuation">)</span>
		goto out_fput<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token operator">-</span>EBADFD<span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_R_DISABLED<span class="token punctuation">)</span>
		goto out<span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span>
	 <span class="token operator">*</span> For SQ polling<span class="token punctuation">,</span> the thread will do <span class="token builtin">all</span> submissions <span class="token keyword">and</span> completions<span class="token punctuation">.</span>
	 <span class="token operator">*</span> Just <span class="token keyword">return</span> the requested submit count<span class="token punctuation">,</span> <span class="token keyword">and</span> wake the thread <span class="token keyword">if</span>
	 <span class="token operator">*</span> we were asked to<span class="token punctuation">.</span>
	 <span class="token operator">*</span><span class="token operator">/</span>
	ret <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_SQPOLL<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>!list_empty_careful<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>cq_overflow_list<span class="token punctuation">)</span><span class="token punctuation">)</span>
			io_cqring_overflow_flush<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> false<span class="token punctuation">,</span> NULL<span class="token punctuation">,</span> NULL<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>flags <span class="token operator">&amp;</span> IORING_ENTER_SQ_WAKEUP<span class="token punctuation">)</span>
			wake_up<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>sq_data<span class="token operator">-</span><span class="token operator">&gt;</span>wait<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>flags <span class="token operator">&amp;</span> IORING_ENTER_SQ_WAIT<span class="token punctuation">)</span>
			io_sqpoll_wait_sq<span class="token punctuation">(</span>ctx<span class="token punctuation">)</span><span class="token punctuation">;</span>
		submitted <span class="token operator">=</span> to_submit<span class="token punctuation">;</span>
	<span class="token punctuation">}</span> <span class="token keyword">else</span> <span class="token keyword">if</span> <span class="token punctuation">(</span>to_submit<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		ret <span class="token operator">=</span> io_uring_add_task_file<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> f<span class="token punctuation">.</span><span class="token builtin">file</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>unlikely<span class="token punctuation">(</span>ret<span class="token punctuation">)</span><span class="token punctuation">)</span>
			goto out<span class="token punctuation">;</span>
		mutex_lock<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>uring_lock<span class="token punctuation">)</span><span class="token punctuation">;</span>
		submitted <span class="token operator">=</span> io_submit_sqes<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> to_submit<span class="token punctuation">)</span><span class="token punctuation">;</span>
		mutex_unlock<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>uring_lock<span class="token punctuation">)</span><span class="token punctuation">;</span>

		<span class="token keyword">if</span> <span class="token punctuation">(</span>submitted <span class="token operator">!=</span> to_submit<span class="token punctuation">)</span>
			goto out<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>flags <span class="token operator">&amp;</span> IORING_ENTER_GETEVENTS<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		min_complete <span class="token operator">=</span> <span class="token builtin">min</span><span class="token punctuation">(</span>min_complete<span class="token punctuation">,</span> ctx<span class="token operator">-</span><span class="token operator">&gt;</span>cq_entries<span class="token punctuation">)</span><span class="token punctuation">;</span>

		<span class="token operator">/</span><span class="token operator">*</span>
		 <span class="token operator">*</span> When SETUP_IOPOLL <span class="token keyword">and</span> SETUP_SQPOLL are both enabled<span class="token punctuation">,</span> user
		 <span class="token operator">*</span> space applications don't need to do io completion events
		 <span class="token operator">*</span> polling again<span class="token punctuation">,</span> they can rely on io_sq_thread to do polling
		 <span class="token operator">*</span> work<span class="token punctuation">,</span> which can <span class="token builtin">reduce</span> cpu usage <span class="token keyword">and</span> uring_lock contention<span class="token punctuation">.</span>
		 <span class="token operator">*</span><span class="token operator">/</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_IOPOLL <span class="token operator">&amp;</span><span class="token operator">&amp;</span>
		    !<span class="token punctuation">(</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>flags <span class="token operator">&amp;</span> IORING_SETUP_SQPOLL<span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
			ret <span class="token operator">=</span> io_iopoll_check<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> min_complete<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token punctuation">}</span> <span class="token keyword">else</span> <span class="token punctuation">{</span>
			ret <span class="token operator">=</span> io_cqring_wait<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> min_complete<span class="token punctuation">,</span> sig<span class="token punctuation">,</span> sigsz<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
	<span class="token punctuation">}</span>

out<span class="token punctuation">:</span>
	percpu_ref_put<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>refs<span class="token punctuation">)</span><span class="token punctuation">;</span>
out_fput<span class="token punctuation">:</span>
	fdput<span class="token punctuation">(</span>f<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> submitted ? submitted <span class="token punctuation">:</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>io_iopoll_check开始poll核外程序可以不停的轮询需要的完成事件数量min_complete，循环内主要调用io_iopoll_getevents。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">static <span class="token builtin">int</span> io_iopoll_check<span class="token punctuation">(</span>struct io_ring_ctx <span class="token operator">*</span>ctx<span class="token punctuation">,</span> <span class="token builtin">long</span> <span class="token builtin">min</span><span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	unsigned <span class="token builtin">int</span> nr_events <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
	<span class="token builtin">int</span> iters <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">,</span> ret <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>

	<span class="token operator">/</span><span class="token operator">*</span>
	 <span class="token operator">*</span> We disallow the app entering submit<span class="token operator">/</span>complete <span class="token keyword">with</span> polling<span class="token punctuation">,</span> but we
	 <span class="token operator">*</span> still need to lock the ring to prevent racing <span class="token keyword">with</span> polled issue
	 <span class="token operator">*</span> that got punted to a workqueue<span class="token punctuation">.</span>
	 <span class="token operator">*</span><span class="token operator">/</span>
	mutex_lock<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>uring_lock<span class="token punctuation">)</span><span class="token punctuation">;</span>
	do <span class="token punctuation">{</span>
		<span class="token operator">/</span><span class="token operator">*</span>
		 <span class="token operator">*</span> Don't enter poll loop <span class="token keyword">if</span> we already have events pending<span class="token punctuation">.</span>
		 <span class="token operator">*</span> If we do<span class="token punctuation">,</span> we can potentially be spinning <span class="token keyword">for</span> commands that
		 <span class="token operator">*</span> already triggered a CQE <span class="token punctuation">(</span>eg <span class="token keyword">in</span> error<span class="token punctuation">)</span><span class="token punctuation">.</span>
		 <span class="token operator">*</span><span class="token operator">/</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>io_cqring_events<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> false<span class="token punctuation">)</span><span class="token punctuation">)</span>
			<span class="token keyword">break</span><span class="token punctuation">;</span>

		<span class="token operator">/</span><span class="token operator">*</span>
		 <span class="token operator">*</span> If a submit got punted to a workqueue<span class="token punctuation">,</span> we can have the
		 <span class="token operator">*</span> application entering polling <span class="token keyword">for</span> a command before it gets
		 <span class="token operator">*</span> issued<span class="token punctuation">.</span> That app will hold the uring_lock <span class="token keyword">for</span> the duration
		 <span class="token operator">*</span> of the poll right here<span class="token punctuation">,</span> so we need to take a breather every
		 <span class="token operator">*</span> now <span class="token keyword">and</span> then to ensure that the issue has a chance to add
		 <span class="token operator">*</span> the poll to the issued <span class="token builtin">list</span><span class="token punctuation">.</span> Otherwise we can spin here
		 <span class="token operator">*</span> forever<span class="token punctuation">,</span> <span class="token keyword">while</span> the workqueue <span class="token keyword">is</span> stuck trying to acquire the
		 <span class="token operator">*</span> very same mutex<span class="token punctuation">.</span>
		 <span class="token operator">*</span><span class="token operator">/</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>!<span class="token punctuation">(</span><span class="token operator">+</span><span class="token operator">+</span>iters <span class="token operator">&amp;</span> <span class="token number">7</span><span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
			mutex_unlock<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>uring_lock<span class="token punctuation">)</span><span class="token punctuation">;</span>
			io_run_task_work<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
			mutex_lock<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>uring_lock<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token punctuation">}</span>

		ret <span class="token operator">=</span> io_iopoll_getevents<span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> <span class="token operator">&amp;</span>nr_events<span class="token punctuation">,</span> <span class="token builtin">min</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>ret <span class="token operator">&lt;=</span> <span class="token number">0</span><span class="token punctuation">)</span>
			<span class="token keyword">break</span><span class="token punctuation">;</span>
		ret <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
	<span class="token punctuation">}</span> <span class="token keyword">while</span> <span class="token punctuation">(</span><span class="token builtin">min</span> <span class="token operator">&amp;</span><span class="token operator">&amp;</span> !nr_events <span class="token operator">&amp;</span><span class="token operator">&amp;</span> !need_resched<span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>

	mutex_unlock<span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-</span><span class="token operator">&gt;</span>uring_lock<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>io_iopoll_getevents调用io_do_iopoll。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token comment">/*
 * Poll for a minimum of 'min' events. Note that if min == 0 we consider that a
 * non-spinning poll check - we'll still enter the driver poll loop, but only
 * as a non-spinning completion check.
 */</span>
<span class="token keyword">static</span> <span class="token keyword">int</span> <span class="token function">io_iopoll_getevents</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_ring_ctx</span> <span class="token operator">*</span>ctx<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> <span class="token keyword">int</span> <span class="token operator">*</span>nr_events<span class="token punctuation">,</span>
				<span class="token keyword">long</span> min<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	<span class="token keyword">while</span> <span class="token punctuation">(</span><span class="token operator">!</span><span class="token function">list_empty</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>ctx<span class="token operator">-&gt;</span>iopoll_list<span class="token punctuation">)</span> <span class="token operator">&amp;&amp;</span> <span class="token operator">!</span><span class="token function">need_resched</span><span class="token punctuation">(</span><span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token keyword">int</span> ret<span class="token punctuation">;</span>

		ret <span class="token operator">=</span> <span class="token function">io_do_iopoll</span><span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> nr_events<span class="token punctuation">,</span> min<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>ret <span class="token operator">&lt;</span> <span class="token number">0</span><span class="token punctuation">)</span>
			<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">*</span>nr_events <span class="token operator">&gt;=</span> min<span class="token punctuation">)</span>
			<span class="token keyword">return</span> <span class="token number">0</span><span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	<span class="token keyword">return</span> <span class="token number">1</span><span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>io_do_iopoll中的kiocb-&gt;ki_filp-&gt;f_op-&gt;iopoll，即blkdev_iopoll，不断地轮询探测确认提交给Block层的请求的完成状态，直到足够数量的IO完成。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token keyword">static</span> <span class="token keyword">int</span> <span class="token function">io_do_iopoll</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_ring_ctx</span> <span class="token operator">*</span>ctx<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> <span class="token keyword">int</span> <span class="token operator">*</span>nr_events<span class="token punctuation">,</span>
			<span class="token keyword">long</span> min<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_kiocb</span> <span class="token operator">*</span>req<span class="token punctuation">,</span> <span class="token operator">*</span>tmp<span class="token punctuation">;</span>
	<span class="token function">LIST_HEAD</span><span class="token punctuation">(</span>done<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">bool</span> spin<span class="token punctuation">;</span>
	<span class="token keyword">int</span> ret<span class="token punctuation">;</span>

	<span class="token comment">/*
	 * Only spin for completions if we don't have multiple devices hanging
	 * off our complete list, and we're under the requested amount.
	 */</span>
	spin <span class="token operator">=</span> <span class="token operator">!</span>ctx<span class="token operator">-&gt;</span>poll_multi_file <span class="token operator">&amp;&amp;</span> <span class="token operator">*</span>nr_events <span class="token operator">&lt;</span> min<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
	<span class="token function">list_for_each_entry_safe</span><span class="token punctuation">(</span>req<span class="token punctuation">,</span> tmp<span class="token punctuation">,</span> <span class="token operator">&amp;</span>ctx<span class="token operator">-&gt;</span>iopoll_list<span class="token punctuation">,</span> inflight_entry<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		<span class="token keyword">struct</span> <span class="token class-name">kiocb</span> <span class="token operator">*</span>kiocb <span class="token operator">=</span> <span class="token operator">&amp;</span>req<span class="token operator">-&gt;</span>rw<span class="token punctuation">.</span>kiocb<span class="token punctuation">;</span>

		<span class="token comment">/*
		 * Move completed and retryable entries to our local lists.
		 * If we find a request that requires polling, break out
		 * and complete those lists first, if we have entries there.
		 */</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token function">READ_ONCE</span><span class="token punctuation">(</span>req<span class="token operator">-&gt;</span>iopoll_completed<span class="token punctuation">)</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
			<span class="token function">list_move_tail</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>req<span class="token operator">-&gt;</span>inflight_entry<span class="token punctuation">,</span> <span class="token operator">&amp;</span>done<span class="token punctuation">)</span><span class="token punctuation">;</span>
			<span class="token keyword">continue</span><span class="token punctuation">;</span>
		<span class="token punctuation">}</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span><span class="token function">list_empty</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>done<span class="token punctuation">)</span><span class="token punctuation">)</span>
			<span class="token keyword">break</span><span class="token punctuation">;</span>

		ret <span class="token operator">=</span> kiocb<span class="token operator">-&gt;</span>ki_filp<span class="token operator">-&gt;</span>f_op<span class="token operator">-&gt;</span><span class="token function">iopoll</span><span class="token punctuation">(</span>kiocb<span class="token punctuation">,</span> spin<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span>ret <span class="token operator">&lt;</span> <span class="token number">0</span><span class="token punctuation">)</span>
			<span class="token keyword">break</span><span class="token punctuation">;</span>

		<span class="token comment">/* iopoll may have completed current req */</span>
		<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token function">READ_ONCE</span><span class="token punctuation">(</span>req<span class="token operator">-&gt;</span>iopoll_completed<span class="token punctuation">)</span><span class="token punctuation">)</span>
			<span class="token function">list_move_tail</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>req<span class="token operator">-&gt;</span>inflight_entry<span class="token punctuation">,</span> <span class="token operator">&amp;</span>done<span class="token punctuation">)</span><span class="token punctuation">;</span>

		<span class="token keyword">if</span> <span class="token punctuation">(</span>ret <span class="token operator">&amp;&amp;</span> spin<span class="token punctuation">)</span>
			spin <span class="token operator">=</span> <span class="token boolean">false</span><span class="token punctuation">;</span>
		ret <span class="token operator">=</span> <span class="token number">0</span><span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	<span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span><span class="token function">list_empty</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>done<span class="token punctuation">)</span><span class="token punctuation">)</span>
		<span class="token function">io_iopoll_complete</span><span class="token punctuation">(</span>ctx<span class="token punctuation">,</span> nr_events<span class="token punctuation">,</span> <span class="token operator">&amp;</span>done<span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>块设备层相关file_operations。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">const struct file_operations def_blk_fops <span class="token operator">=</span> <span class="token punctuation">{</span>
	<span class="token punctuation">.</span><span class="token builtin">open</span>		<span class="token operator">=</span> blkdev_open<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>release	<span class="token operator">=</span> blkdev_close<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>llseek		<span class="token operator">=</span> block_llseek<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>read_iter	<span class="token operator">=</span> blkdev_read_iter<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>write_iter	<span class="token operator">=</span> blkdev_write_iter<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>iopoll		<span class="token operator">=</span> blkdev_iopoll<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>mmap		<span class="token operator">=</span> generic_file_mmap<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>fsync		<span class="token operator">=</span> blkdev_fsync<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>unlocked_ioctl	<span class="token operator">=</span> block_ioctl<span class="token punctuation">,</span>
<span class="token comment">#ifdef CONFIG_COMPAT</span>
	<span class="token punctuation">.</span>compat_ioctl	<span class="token operator">=</span> compat_blkdev_ioctl<span class="token punctuation">,</span>
<span class="token comment">#endif</span>
	<span class="token punctuation">.</span>splice_read	<span class="token operator">=</span> generic_file_splice_read<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>splice_write	<span class="token operator">=</span> iter_file_splice_write<span class="token punctuation">,</span>
	<span class="token punctuation">.</span>fallocate	<span class="token operator">=</span> blkdev_fallocate<span class="token punctuation">,</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<p>当使用POLL IO时，大多数CPU时间花费在blkdev_iopoll上。即全速完成关键路径。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">static <span class="token builtin">int</span> blkdev_iopoll<span class="token punctuation">(</span>struct kiocb <span class="token operator">*</span>kiocb<span class="token punctuation">,</span> <span class="token builtin">bool</span> wait<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	struct block_device <span class="token operator">*</span>bdev <span class="token operator">=</span> I_BDEV<span class="token punctuation">(</span>kiocb<span class="token operator">-</span><span class="token operator">&gt;</span>ki_filp<span class="token operator">-</span><span class="token operator">&gt;</span>f_mapping<span class="token operator">-</span><span class="token operator">&gt;</span>host<span class="token punctuation">)</span><span class="token punctuation">;</span>
	struct request_queue <span class="token operator">*</span>q <span class="token operator">=</span> bdev_get_queue<span class="token punctuation">(</span>bdev<span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token keyword">return</span> blk_poll<span class="token punctuation">(</span>q<span class="token punctuation">,</span> READ_ONCE<span class="token punctuation">(</span>kiocb<span class="token operator">-</span><span class="token operator">&gt;</span>ki_cookie<span class="token punctuation">)</span><span class="token punctuation">,</span> wait<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<h3 id="Kernel-Side-Polling">Kernel Side Polling</h3>

<p>IORING_SETUP_SQPOLL，当前应用更新SQ并填充一个新的SQE，内核线程sq_thread会自动完成提交，这样应用无需每次调用io_uring_enter系统调用来提交IO。应用可通过IORING_SETUP_SQ_AFF和sq_thread_cpu绑定特定的CPU。</p>

<p>实际机器上，不仅有高IOPS场景，还有些场景的IOPS有些时间段会非常低。为了节省无IO场景的CPU开销，一段时间空闲，该内核线程可以自动睡眠。核外在下发新的IO时，通过IORING_ENTER_SQ_WAKEUP唤醒该内核线程。</p>

<h3 id="小结">小结</h3>

<p>如上可见，内核提供了足够多的选择，不同的方案有着不同角度的优化方向，这些优化方案可以自行组合。通过合理地使用，可以使io_uring 全速运转。</p>

<h1 id="io_uring用户态库liburing">io_uring用户态库liburing</h1>

<p>正如前文所说，简单并不一定意味着易用——io_uring的接口足够简单，但是相对于这种简单，操作上需要手动mmap来映射内存，稍显复杂。为了更方便地使用io_uring，原作者Jens Axboe还开发了一套liburing库。liburing库提供了一组辅助函数实现设置和内存映射，应用不必了解诸多io_uring的细节就可以简单地使用起来。例如，无需担心memory barrier，或者是ring buffer管理之类等。上文所提的一些高级特性，在liburing中也有封装。</p>

<h2 id="核心数据结构">核心数据结构</h2>

<p>liburing中，核心的结构有io_uring、io_uring_sq、io_uring_cq</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> Library interface to io_uring
 <span class="token operator">*</span><span class="token operator">/</span>
struct io_uring_sq <span class="token punctuation">{</span>
	unsigned <span class="token operator">*</span>khead<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>ktail<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>kring_mask<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>kring_entries<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>kflags<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>kdropped<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>array<span class="token punctuation">;</span>
	struct io_uring_sqe <span class="token operator">*</span>sqes<span class="token punctuation">;</span>

	unsigned sqe_head<span class="token punctuation">;</span>
	unsigned sqe_tail<span class="token punctuation">;</span>

	size_t ring_sz<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>

struct io_uring_cq <span class="token punctuation">{</span>
	unsigned <span class="token operator">*</span>khead<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>ktail<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>kring_mask<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>kring_entries<span class="token punctuation">;</span>
	unsigned <span class="token operator">*</span>koverflow<span class="token punctuation">;</span>
	struct io_uring_cqe <span class="token operator">*</span>cqes<span class="token punctuation">;</span>

	size_t ring_sz<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>

struct io_uring <span class="token punctuation">{</span>
	struct io_uring_sq sq<span class="token punctuation">;</span>
	struct io_uring_cq cq<span class="token punctuation">;</span>
	<span class="token builtin">int</span> ring_fd<span class="token punctuation">;</span>
<span class="token punctuation">}</span><span class="token punctuation">;</span>
</code></pre>

<h2 id="核心接口">核心接口</h2>

<p>相关接口在头文件linux/tools/io_uring/liburing.h，如果是通过标准方式安装的liburing，则在/usr/include/下。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token comment">/*
 * System calls
 */</span>
<span class="token keyword">extern</span> <span class="token keyword">int</span> <span class="token function">io_uring_setup</span><span class="token punctuation">(</span><span class="token keyword">unsigned</span> entries<span class="token punctuation">,</span> <span class="token keyword">struct</span> <span class="token class-name">io_uring_params</span> <span class="token operator">*</span>p<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token keyword">extern</span> <span class="token keyword">int</span> <span class="token function">io_uring_enter</span><span class="token punctuation">(</span><span class="token keyword">int</span> fd<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> to_submit<span class="token punctuation">,</span>
	<span class="token keyword">unsigned</span> min_complete<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> flags<span class="token punctuation">,</span> sigset_t <span class="token operator">*</span>sig<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token keyword">extern</span> <span class="token keyword">int</span> <span class="token function">io_uring_register</span><span class="token punctuation">(</span><span class="token keyword">int</span> fd<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> <span class="token keyword">int</span> opcode<span class="token punctuation">,</span> <span class="token keyword">void</span> <span class="token operator">*</span>arg<span class="token punctuation">,</span>
	<span class="token keyword">unsigned</span> <span class="token keyword">int</span> nr_args<span class="token punctuation">)</span><span class="token punctuation">;</span>

<span class="token comment">/*
 * Library interface
 */</span>
<span class="token keyword">extern</span> <span class="token keyword">int</span> <span class="token function">io_uring_queue_init</span><span class="token punctuation">(</span><span class="token keyword">unsigned</span> entries<span class="token punctuation">,</span> <span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token operator">*</span>ring<span class="token punctuation">,</span>
	<span class="token keyword">unsigned</span> flags<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token keyword">extern</span> <span class="token keyword">int</span> <span class="token function">io_uring_queue_mmap</span><span class="token punctuation">(</span><span class="token keyword">int</span> fd<span class="token punctuation">,</span> <span class="token keyword">struct</span> <span class="token class-name">io_uring_params</span> <span class="token operator">*</span>p<span class="token punctuation">,</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token operator">*</span>ring<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token keyword">extern</span> <span class="token keyword">void</span> <span class="token function">io_uring_queue_exit</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token operator">*</span>ring<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token keyword">extern</span> <span class="token keyword">int</span> <span class="token function">io_uring_peek_cqe</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token operator">*</span>ring<span class="token punctuation">,</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_uring_cqe</span> <span class="token operator">*</span><span class="token operator">*</span>cqe_ptr<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token keyword">extern</span> <span class="token keyword">int</span> <span class="token function">io_uring_wait_cqe</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token operator">*</span>ring<span class="token punctuation">,</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_uring_cqe</span> <span class="token operator">*</span><span class="token operator">*</span>cqe_ptr<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token keyword">extern</span> <span class="token keyword">int</span> <span class="token function">io_uring_submit</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token operator">*</span>ring<span class="token punctuation">)</span><span class="token punctuation">;</span>
<span class="token keyword">extern</span> <span class="token keyword">struct</span> <span class="token class-name">io_uring_sqe</span> <span class="token operator">*</span><span class="token function">io_uring_get_sqe</span><span class="token punctuation">(</span><span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token operator">*</span>ring<span class="token punctuation">)</span><span class="token punctuation">;</span>
</code></pre>

<h2 id="主要流程">主要流程</h2>

<ul>
<li>使用io_uring_queue_init，完成io_uring相关结构的初始化。在这个函数的实现中，会调用多个mmap来初始化一些内存。</li>
<li>初始化完成之后，为了提交IO请求，需要获取里面queue的一个项，使用io_uring_get_sqe。
<ul>
<li>获取到了空闲项之后，使用io_uring_prep_readv、io_uring_prep_writev初始化读、写请求。和前文所提preadv、pwritev的思想差不多，这里直接以不同的操作码委托io_uring_prep_rw，io_uring_prep_rw只是简单地初始化io_uring_sqe。</li>
</ul>
</li>
<li>准备完成之后，使用io_uring_submit提交请求。</li>
<li>提交了IO请求时，可以通过非阻塞式函数io_uring_peek_cqe、阻塞式函数io_uring_wait_cqe获取请求完成的情况。默认情况下，完成的IO请求还会存在内部的队列中，需要通过io_uring_cqe_seen表标记完成操作。</li>
<li>使用完成之后要通过io_uring_queue_exit来完成资源清理的工作。</li>
</ul>

<h2 id="核心实现">核心实现</h2>

<p>io_uring_queue_init的实现，前文已略有提及。其中的操作主要就是io_uring_setup和io_uring_queue_mmap，io_uring_setup前文已解析过，这里主要看io_uring_queue_mmap。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token comment">/*
 * Returns -1 on error, or zero on success. On success, 'ring'
 * contains the necessary information to read/write to the rings.
 */</span>
<span class="token keyword">int</span> <span class="token function">io_uring_queue_init</span><span class="token punctuation">(</span><span class="token keyword">unsigned</span> entries<span class="token punctuation">,</span> <span class="token keyword">struct</span> <span class="token class-name">io_uring</span> <span class="token operator">*</span>ring<span class="token punctuation">,</span> <span class="token keyword">unsigned</span> flags<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	<span class="token keyword">struct</span> <span class="token class-name">io_uring_params</span> p<span class="token punctuation">;</span>
	<span class="token keyword">int</span> fd<span class="token punctuation">,</span> ret<span class="token punctuation">;</span>

	<span class="token function">memset</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>p<span class="token punctuation">,</span> <span class="token number">0</span><span class="token punctuation">,</span> <span class="token keyword">sizeof</span><span class="token punctuation">(</span>p<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	p<span class="token punctuation">.</span>flags <span class="token operator">=</span> flags<span class="token punctuation">;</span>

	fd <span class="token operator">=</span> <span class="token function">io_uring_setup</span><span class="token punctuation">(</span>entries<span class="token punctuation">,</span> <span class="token operator">&amp;</span>p<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>fd <span class="token operator">&lt;</span> <span class="token number">0</span><span class="token punctuation">)</span>
		<span class="token keyword">return</span> fd<span class="token punctuation">;</span>

	ret <span class="token operator">=</span> <span class="token function">io_uring_queue_mmap</span><span class="token punctuation">(</span>fd<span class="token punctuation">,</span> <span class="token operator">&amp;</span>p<span class="token punctuation">,</span> ring<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ret<span class="token punctuation">)</span>
		<span class="token function">close</span><span class="token punctuation">(</span>fd<span class="token punctuation">)</span><span class="token punctuation">;</span>

	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>io_uring_queue_mmap初始化io_uring结构，然后主要调用io_uring_mmap。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python"><span class="token operator">/</span><span class="token operator">*</span>
 <span class="token operator">*</span> For users that want to specify sq_thread_cpu <span class="token keyword">or</span> sq_thread_idle<span class="token punctuation">,</span> this
 <span class="token operator">*</span> interface <span class="token keyword">is</span> a convenient helper <span class="token keyword">for</span> mmap<span class="token punctuation">(</span><span class="token punctuation">)</span>ing the rings<span class="token punctuation">.</span>
 <span class="token operator">*</span> Returns <span class="token operator">-</span><span class="token number">1</span> on error<span class="token punctuation">,</span> <span class="token keyword">or</span> zero on success<span class="token punctuation">.</span>  On success<span class="token punctuation">,</span> <span class="token string">'ring'</span>
 <span class="token operator">*</span> contains the necessary information to read<span class="token operator">/</span>write to the rings<span class="token punctuation">.</span>
 <span class="token operator">*</span><span class="token operator">/</span>
<span class="token builtin">int</span> io_uring_queue_mmap<span class="token punctuation">(</span><span class="token builtin">int</span> fd<span class="token punctuation">,</span> struct io_uring_params <span class="token operator">*</span>p<span class="token punctuation">,</span> struct io_uring <span class="token operator">*</span>ring<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	<span class="token builtin">int</span> ret<span class="token punctuation">;</span>

	memset<span class="token punctuation">(</span>ring<span class="token punctuation">,</span> <span class="token number">0</span><span class="token punctuation">,</span> sizeof<span class="token punctuation">(</span><span class="token operator">*</span>ring<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
	ret <span class="token operator">=</span> io_uring_mmap<span class="token punctuation">(</span>fd<span class="token punctuation">,</span> p<span class="token punctuation">,</span> <span class="token operator">&amp;</span>ring<span class="token operator">-</span><span class="token operator">&gt;</span>sq<span class="token punctuation">,</span> <span class="token operator">&amp;</span>ring<span class="token operator">-</span><span class="token operator">&gt;</span>cq<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>!ret<span class="token punctuation">)</span>
		ring<span class="token operator">-</span><span class="token operator">&gt;</span>ring_fd <span class="token operator">=</span> fd<span class="token punctuation">;</span>
	<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>io_uring_mmap初始化io_uring_sq结构和io_uring_cq结构的内存，另外还会分配一个io_uring_sqe结构的数组。</p>

<pre class="  language-python" style="position: relative; z-index: 2;"><code class="prism  language-python">static <span class="token builtin">int</span> io_uring_mmap<span class="token punctuation">(</span><span class="token builtin">int</span> fd<span class="token punctuation">,</span> struct io_uring_params <span class="token operator">*</span>p<span class="token punctuation">,</span>
			 struct io_uring_sq <span class="token operator">*</span>sq<span class="token punctuation">,</span> struct io_uring_cq <span class="token operator">*</span>cq<span class="token punctuation">)</span>
<span class="token punctuation">{</span>
	size_t size<span class="token punctuation">;</span>
	void <span class="token operator">*</span>ptr<span class="token punctuation">;</span>
	<span class="token builtin">int</span> ret<span class="token punctuation">;</span>

	sq<span class="token operator">-</span><span class="token operator">&gt;</span>ring_sz <span class="token operator">=</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_off<span class="token punctuation">.</span>array <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_entries <span class="token operator">*</span> sizeof<span class="token punctuation">(</span>unsigned<span class="token punctuation">)</span><span class="token punctuation">;</span>
	ptr <span class="token operator">=</span> mmap<span class="token punctuation">(</span><span class="token number">0</span><span class="token punctuation">,</span> sq<span class="token operator">-</span><span class="token operator">&gt;</span>ring_sz<span class="token punctuation">,</span> PROT_READ <span class="token operator">|</span> PROT_WRITE<span class="token punctuation">,</span>
			MAP_SHARED <span class="token operator">|</span> MAP_POPULATE<span class="token punctuation">,</span> fd<span class="token punctuation">,</span> IORING_OFF_SQ_RING<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ptr <span class="token operator">==</span> MAP_FAILED<span class="token punctuation">)</span>
		<span class="token keyword">return</span> <span class="token operator">-</span>errno<span class="token punctuation">;</span>
	sq<span class="token operator">-</span><span class="token operator">&gt;</span>khead <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_off<span class="token punctuation">.</span>head<span class="token punctuation">;</span>
	sq<span class="token operator">-</span><span class="token operator">&gt;</span>ktail <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_off<span class="token punctuation">.</span>tail<span class="token punctuation">;</span>
	sq<span class="token operator">-</span><span class="token operator">&gt;</span>kring_mask <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_off<span class="token punctuation">.</span>ring_mask<span class="token punctuation">;</span>
	sq<span class="token operator">-</span><span class="token operator">&gt;</span>kring_entries <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_off<span class="token punctuation">.</span>ring_entries<span class="token punctuation">;</span>
	sq<span class="token operator">-</span><span class="token operator">&gt;</span>kflags <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_off<span class="token punctuation">.</span>flags<span class="token punctuation">;</span>
	sq<span class="token operator">-</span><span class="token operator">&gt;</span>kdropped <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_off<span class="token punctuation">.</span>dropped<span class="token punctuation">;</span>
	sq<span class="token operator">-</span><span class="token operator">&gt;</span>array <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_off<span class="token punctuation">.</span>array<span class="token punctuation">;</span>

	size <span class="token operator">=</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_entries <span class="token operator">*</span> sizeof<span class="token punctuation">(</span>struct io_uring_sqe<span class="token punctuation">)</span><span class="token punctuation">;</span>
	sq<span class="token operator">-</span><span class="token operator">&gt;</span>sqes <span class="token operator">=</span> mmap<span class="token punctuation">(</span><span class="token number">0</span><span class="token punctuation">,</span> size<span class="token punctuation">,</span> PROT_READ <span class="token operator">|</span> PROT_WRITE<span class="token punctuation">,</span>
				MAP_SHARED <span class="token operator">|</span> MAP_POPULATE<span class="token punctuation">,</span> fd<span class="token punctuation">,</span>
				IORING_OFF_SQES<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>sq<span class="token operator">-</span><span class="token operator">&gt;</span>sqes <span class="token operator">==</span> MAP_FAILED<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		ret <span class="token operator">=</span> <span class="token operator">-</span>errno<span class="token punctuation">;</span>
err<span class="token punctuation">:</span>
		munmap<span class="token punctuation">(</span>sq<span class="token operator">-</span><span class="token operator">&gt;</span>khead<span class="token punctuation">,</span> sq<span class="token operator">-</span><span class="token operator">&gt;</span>ring_sz<span class="token punctuation">)</span><span class="token punctuation">;</span>
		<span class="token keyword">return</span> ret<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>

	cq<span class="token operator">-</span><span class="token operator">&gt;</span>ring_sz <span class="token operator">=</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>cq_off<span class="token punctuation">.</span>cqes <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>cq_entries <span class="token operator">*</span> sizeof<span class="token punctuation">(</span>struct io_uring_cqe<span class="token punctuation">)</span><span class="token punctuation">;</span>
	ptr <span class="token operator">=</span> mmap<span class="token punctuation">(</span><span class="token number">0</span><span class="token punctuation">,</span> cq<span class="token operator">-</span><span class="token operator">&gt;</span>ring_sz<span class="token punctuation">,</span> PROT_READ <span class="token operator">|</span> PROT_WRITE<span class="token punctuation">,</span>
			MAP_SHARED <span class="token operator">|</span> MAP_POPULATE<span class="token punctuation">,</span> fd<span class="token punctuation">,</span> IORING_OFF_CQ_RING<span class="token punctuation">)</span><span class="token punctuation">;</span>
	<span class="token keyword">if</span> <span class="token punctuation">(</span>ptr <span class="token operator">==</span> MAP_FAILED<span class="token punctuation">)</span> <span class="token punctuation">{</span>
		ret <span class="token operator">=</span> <span class="token operator">-</span>errno<span class="token punctuation">;</span>
		munmap<span class="token punctuation">(</span>sq<span class="token operator">-</span><span class="token operator">&gt;</span>sqes<span class="token punctuation">,</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>sq_entries <span class="token operator">*</span> sizeof<span class="token punctuation">(</span>struct io_uring_sqe<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
		goto err<span class="token punctuation">;</span>
	<span class="token punctuation">}</span>
	cq<span class="token operator">-</span><span class="token operator">&gt;</span>khead <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>cq_off<span class="token punctuation">.</span>head<span class="token punctuation">;</span>
	cq<span class="token operator">-</span><span class="token operator">&gt;</span>ktail <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>cq_off<span class="token punctuation">.</span>tail<span class="token punctuation">;</span>
	cq<span class="token operator">-</span><span class="token operator">&gt;</span>kring_mask <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>cq_off<span class="token punctuation">.</span>ring_mask<span class="token punctuation">;</span>
	cq<span class="token operator">-</span><span class="token operator">&gt;</span>kring_entries <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>cq_off<span class="token punctuation">.</span>ring_entries<span class="token punctuation">;</span>
	cq<span class="token operator">-</span><span class="token operator">&gt;</span>koverflow <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>cq_off<span class="token punctuation">.</span>overflow<span class="token punctuation">;</span>
	cq<span class="token operator">-</span><span class="token operator">&gt;</span>cqes <span class="token operator">=</span> ptr <span class="token operator">+</span> p<span class="token operator">-</span><span class="token operator">&gt;</span>cq_off<span class="token punctuation">.</span>cqes<span class="token punctuation">;</span>
	<span class="token keyword">return</span> <span class="token number">0</span><span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<h2 id="具体例程">具体例程</h2>

<p>如下是一个基于liburing的helloworld示例。</p>

<pre class="  language-cpp" style="position: relative; z-index: 2;"><code class="prism  language-cpp"><span class="token macro property">#<span class="token directive keyword">include</span> <span class="token string">&lt;unistd.h&gt;</span></span>
<span class="token macro property">#<span class="token directive keyword">include</span> <span class="token string">&lt;fcntl.h&gt;</span></span>
<span class="token macro property">#<span class="token directive keyword">include</span> <span class="token string">&lt;string.h&gt;</span></span>
<span class="token macro property">#<span class="token directive keyword">include</span> <span class="token string">&lt;stdio.h&gt;</span></span>
<span class="token macro property">#<span class="token directive keyword">include</span> <span class="token string">&lt;liburing.h&gt;</span></span>

<span class="token macro property">#<span class="token directive keyword">define</span> ENTRIES 4</span>

<span class="token keyword">int</span> <span class="token function">main</span><span class="token punctuation">(</span><span class="token keyword">int</span> argc<span class="token punctuation">,</span> <span class="token keyword">char</span> <span class="token operator">*</span>argv<span class="token punctuation">[</span><span class="token punctuation">]</span><span class="token punctuation">)</span>
<span class="token punctuation">{</span>
    <span class="token keyword">struct</span> <span class="token class-name">io_uring</span> ring<span class="token punctuation">;</span>
    <span class="token keyword">struct</span> <span class="token class-name">io_uring_sqe</span> <span class="token operator">*</span>sqe<span class="token punctuation">;</span>
    <span class="token keyword">struct</span> <span class="token class-name">io_uring_cqe</span> <span class="token operator">*</span>cqe<span class="token punctuation">;</span>
    <span class="token keyword">struct</span> <span class="token class-name">iovec</span> iov <span class="token operator">=</span> <span class="token punctuation">{</span>
        <span class="token punctuation">.</span>iov_base <span class="token operator">=</span> <span class="token string">"Hello World"</span><span class="token punctuation">,</span>
        <span class="token punctuation">.</span>iov_len <span class="token operator">=</span> <span class="token function">strlen</span><span class="token punctuation">(</span><span class="token string">"Hello World"</span><span class="token punctuation">)</span><span class="token punctuation">,</span>
    <span class="token punctuation">}</span><span class="token punctuation">;</span>
    <span class="token keyword">int</span> fd<span class="token punctuation">,</span> ret<span class="token punctuation">;</span>
    <span class="token keyword">if</span> <span class="token punctuation">(</span>argc <span class="token operator">!=</span> <span class="token number">2</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
        <span class="token function">printf</span><span class="token punctuation">(</span><span class="token string">"%s: &lt;testfile&gt;\n"</span><span class="token punctuation">,</span> argv<span class="token punctuation">[</span><span class="token number">0</span><span class="token punctuation">]</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
        <span class="token keyword">return</span> <span class="token number">1</span><span class="token punctuation">;</span>
    <span class="token punctuation">}</span>
    <span class="token comment">/* setup io_uring and do mmap */</span>
    ret <span class="token operator">=</span> <span class="token function">io_uring_queue_init</span><span class="token punctuation">(</span>ENTRIES<span class="token punctuation">,</span> <span class="token operator">&amp;</span>ring<span class="token punctuation">,</span> <span class="token number">0</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
    <span class="token keyword">if</span> <span class="token punctuation">(</span>ret <span class="token operator">&lt;</span> <span class="token number">0</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
        <span class="token function">printf</span><span class="token punctuation">(</span><span class="token string">"io_uring_queue_init: %s\n"</span><span class="token punctuation">,</span> <span class="token function">strerror</span><span class="token punctuation">(</span><span class="token operator">-</span>ret<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
        <span class="token keyword">return</span> <span class="token number">1</span><span class="token punctuation">;</span>
    <span class="token punctuation">}</span>
    fd <span class="token operator">=</span> <span class="token function">open</span><span class="token punctuation">(</span><span class="token string">"testfile"</span><span class="token punctuation">,</span> O_WRONLY <span class="token operator">|</span> O_CREAT<span class="token punctuation">)</span><span class="token punctuation">;</span>
    <span class="token keyword">if</span> <span class="token punctuation">(</span>fd <span class="token operator">&lt;</span> <span class="token number">0</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
        <span class="token function">printf</span><span class="token punctuation">(</span><span class="token string">"open failed\n"</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
        ret <span class="token operator">=</span> <span class="token number">1</span><span class="token punctuation">;</span>
        <span class="token keyword">goto</span> exit<span class="token punctuation">;</span>
    <span class="token punctuation">}</span>
    <span class="token comment">/* get an sqe and fill in a WRITEV operation */</span>
    sqe <span class="token operator">=</span> <span class="token function">io_uring_get_sqe</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>ring<span class="token punctuation">)</span><span class="token punctuation">;</span>
    <span class="token keyword">if</span> <span class="token punctuation">(</span><span class="token operator">!</span>sqe<span class="token punctuation">)</span> <span class="token punctuation">{</span>
        <span class="token function">printf</span><span class="token punctuation">(</span><span class="token string">"io_uring_get_sqe failed\n"</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
        ret <span class="token operator">=</span> <span class="token number">1</span><span class="token punctuation">;</span>
        <span class="token keyword">goto</span> out<span class="token punctuation">;</span>
    <span class="token punctuation">}</span>
    <span class="token function">io_uring_prep_writev</span><span class="token punctuation">(</span>sqe<span class="token punctuation">,</span> fd<span class="token punctuation">,</span> <span class="token operator">&amp;</span>iov<span class="token punctuation">,</span> <span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">0</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
    <span class="token comment">/* tell the kernel we have an sqe ready for consumption */</span>
    ret <span class="token operator">=</span> <span class="token function">io_uring_submit</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>ring<span class="token punctuation">)</span><span class="token punctuation">;</span>
    <span class="token keyword">if</span> <span class="token punctuation">(</span>ret <span class="token operator">&lt;</span> <span class="token number">0</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
        <span class="token function">printf</span><span class="token punctuation">(</span><span class="token string">"io_uring_submit: %s\n"</span><span class="token punctuation">,</span> <span class="token function">strerror</span><span class="token punctuation">(</span><span class="token operator">-</span>ret<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
        <span class="token keyword">goto</span> out<span class="token punctuation">;</span>
    <span class="token punctuation">}</span>
    <span class="token comment">/* wait for the sqe to complete */</span>
    ret <span class="token operator">=</span> <span class="token function">io_uring_wait_cqe</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>ring<span class="token punctuation">,</span> <span class="token operator">&amp;</span>cqe<span class="token punctuation">)</span><span class="token punctuation">;</span>
    <span class="token keyword">if</span> <span class="token punctuation">(</span>ret <span class="token operator">&lt;</span> <span class="token number">0</span><span class="token punctuation">)</span> <span class="token punctuation">{</span>
        <span class="token function">printf</span><span class="token punctuation">(</span><span class="token string">"io_uring_wait_cqe: %s\n"</span><span class="token punctuation">,</span> <span class="token function">strerror</span><span class="token punctuation">(</span><span class="token operator">-</span>ret<span class="token punctuation">)</span><span class="token punctuation">)</span><span class="token punctuation">;</span>
        <span class="token keyword">goto</span> out<span class="token punctuation">;</span>
    <span class="token punctuation">}</span>
    <span class="token comment">/* read and process cqe event */</span>
    <span class="token function">io_uring_cqe_seen</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>ring<span class="token punctuation">,</span> cqe<span class="token punctuation">)</span><span class="token punctuation">;</span>
out<span class="token operator">:</span>
    <span class="token function">close</span><span class="token punctuation">(</span>fd<span class="token punctuation">)</span><span class="token punctuation">;</span>
exit<span class="token operator">:</span>
    <span class="token comment">/* tear down */</span>
    <span class="token function">io_uring_queue_exit</span><span class="token punctuation">(</span><span class="token operator">&amp;</span>ring<span class="token punctuation">)</span><span class="token punctuation">;</span>
    <span class="token keyword">return</span> ret<span class="token punctuation">;</span>
<span class="token punctuation">}</span>
</code></pre>

<p>更多的示例可参考：<br>
<a href="http://git.kernel.dk/cgit/liburing/tree/examples" target="_blank">http://git.kernel.dk/cgit/liburing/tree/examples</a><br>
<a href="https://git.kernel.dk/cgit/liburing/tree/test" target="_blank">https://git.kernel.dk/cgit/liburing/tree/test</a></p>

<h1 id="性能">性能</h1>

<p>如上，推演过了设计与实现，回归到存储的需求上来，io_uring子系统是否能满足我们对高性能的极致需求呢？这一切还是要profiling</p>

<h2 id="测试方法">测试方法</h2>

<p>io_uring原作者Jens Axboe在fio中提供了ioengine=io_uring的支持，可以使用fio进行测试，使用ioengine选项指定异步IO引擎。</p>

<p>可以基于不同的IO栈：</p>

<ul>
<li>libaio</li>
<li>kernel+io_uring</li>
<li>kernel+io_uring polling mode</li>
</ul>

<p>可以基于一些硬件之上：</p>

<ul>
<li>NVMe SSD</li>
<li>…</li>
</ul>

<p>测试过程中主要4k数据的顺序读、顺序写、随机读、随机写，对比几种IO引擎的性能及QoS等指标</p>

<p>io_uring polling mode测试实例：</p>

<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash">fio -name<span class="token operator">=</span>testname -filename<span class="token operator">=</span>/mnt/vdd/testfilename -iodepth<span class="token operator">=</span><span class="token number">64</span> -thread -rw<span class="token operator">=</span>randread -ioengine<span class="token operator">=</span>io_uring -sqthread_poll<span class="token operator">=</span><span class="token number">1</span> -direct<span class="token operator">=</span><span class="token number">1</span> -bs<span class="token operator">=</span>4k -size<span class="token operator">=</span>10G -numjobs<span class="token operator">=</span><span class="token number">1</span> -runtime<span class="token operator">=</span><span class="token number">600</span> -group_reporting
</code></pre>

<h2 id="测试结果">测试结果</h2>

<p>网上可以找到一些关于io uring的性能测试，这里列出部分供参考：</p>

<ul>
<li><a href="https://www.flashmemorysummit.com/Proceedings2019/08-07-Wednesday/20190807_SOFT-202-1_Verma.pdf" target="_blank"><em>Improved Flash Performance Using the New Linux Kernel I/O Interface</em></a></li>
<li><a href="https://github.com/frevib/io_uring-echo-server/blob/io-uring-feat-fast-poll/benchmarks/benchmarks.md" target="_blank"><em>io_uring echo server benchmarks</em></a></li>
<li><a href="https://lore.kernel.org/linux-block/20190116175003.17880-1-axboe@kernel.dk/" target="_blank"><em>[PATCHSET v5] io_uring IO interface</em></a></li>
<li>…</li>
</ul>

<p>主要有以下几个测试结果</p>

<ul>
<li>io_uring在非polling模式下，相比libaio，性能提升不是非常显著。</li>
<li>io_uring在polling模式下，性能提升显著，与spdk接近，在队列深度较高时性能更好。</li>
<li>在meltdown和spectre漏洞没有修复的场景下，io_uring的提升并不太高。虽然减少了大量的用户态到内核态的上下文切换，在meldown和spectre漏洞没有修复的场景下，用户态到内核态的切换开销本比较小，所以提升不太高。</li>
<li>在某些场景下使用io_uring + Kernel NVMe的驱动，效果甚至要比使用SPDK 用户态NVMe 驱动更好</li>
</ul>

<p>从测试中，我们可以得出结论，在存储中使用io_uring，相比使用libaio，应用的性能会有显著的提升。</p>

<p>在同样的硬件平台上，仅仅更换IO引擎，就可以带来较大的提升，是很难得的，对于存储这种延时敏感的应用而言十分宝贵。</p>

<h2 id="io_uring的优势">io_uring的优势</h2>

<p>综合前文和测试，io_uring有如此出众的性能，主要来源于以下几个方面：</p>

<ul>
<li>用户态和内核态共享提交队列SQ和完成队列CQ实现零拷贝。</li>
<li>IO提交和收割可以offload给Kernel，不需要经过系统调用。</li>
<li>支持块设备层的Polling模式。</li>
<li>可以提前注册用户态内存地址，从而减少地址映射的开销。</li>
<li>相比libaio，支持buffered IO</li>
</ul>

<h1 id="发展方向">发展方向</h1>

<p>事物的发展是一个哲学话题。前文阐述了io_uring作为一个新事物，发展的根本动力、内因和外因，谨此简述一些可预见的未来的发展方向。</p>

<h2 id="普及">普及</h2>

<p>应用层多使用。</p>

<p>目前主要应用在存储的场景中，这是一个不仅需要高性能，也需要稳定的场景，而一般来说，新事物并不具备“稳定”的属性。但是io_uring同样也是稳定的，因为虽然io_uring使用到了若干新概念，但是这些新的东西已经有了实践的检验，如eventfd通知机制，SIGIO信号机制，与AIO基本相似。它是一个质变的新事物。</p>

<p>就我们而言，内核使用tlinux<br>
tlinux3基于4.14.99主线（<a href="https://git.code.oa.com/tlinux/tkernel3/commit/46970e58e0a8b9437ec7c03d2a5e4e2133292311%EF%BC%89" target="_blank">https://git.code.oa.com/tlinux/tkernel3/commit/46970e58e0a8b9437ec7c03d2a5e4e2133292311）</a><br>
tlinux4基于5.4.23主线（<a href="https://git.code.oa.com/tlinux/tkernel4/commit/d3f96c44661da3b13b03b347682d71207b14c9d9%EF%BC%89" target="_blank">https://git.code.oa.com/tlinux/tkernel4/commit/d3f96c44661da3b13b03b347682d71207b14c9d9）</a></p>

<p>所以，tlinux3可以用native aio，tlinux4之后已经可以用native io_uring。</p>

<p>相信通过大家的努力，正如前文所说的PostgreSQL使用彼时新接口pread，Nginx使用彼时的新接口AIO一样，通过使用新接口，我们的工程也能获得巨大收益。</p>

<h2 id="优化方向">优化方向</h2>

<h3 id="降低本身的工作负载">降低本身的工作负载</h3>

<p>持续降低系统调用开销、拷贝开销、框架本身的负载。</p>

<h3 id="重构">重构</h3>

<blockquote>
<p>"Politics are for the moment. An equation is for eternity.<br>
　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　——Albert Einstein</p>
</blockquote>

<p>追求真理的人不可避免地追求永恒。“政治只是一时，方程却是永恒。”——爱因斯坦如是说，时值以色列的第一任总统魏兹曼于1952年逝世，继任首相古理安建议邀请爱因斯坦担任第二任总统。</p>

<p>我们折衷权衡、精益求精，字里行间都是永恒，然而软件却应该持续重构。实际上并不只是io_uring需要如此，有机会我会写一篇关于重构的文章。</p>

<h1 id="总结">总结</h1>

<p>// TODO…</p>

<h1 id="关于">关于</h1>

<p>可以通过以下网址找到本文。</p>

<ul>
<li>知乎：<a href="https://www.zhihu.com/people/linkerist-61" target="_blank">https://www.zhihu.com/people/linkerist-61</a></li>
<li>简书：<a href="https://www.jianshu.com/u/6e736fe94d97" target="_blank">https://www.jianshu.com/u/6e736fe94d97</a></li>
<li>Github: <a href="https://github.com/Linkerist/blog/issues" target="_blank">https://github.com/Linkerist/blog/issues</a></li>
</ul>

<p>内容难免纰漏，会继续更新，不过可能会忘记更新到KM。可以关注公众号“开发者技术精选”，有更多高质量技术文章。</p>

<p>开发者技术精选</p>

<p style=""><img src="./《操作系统与存储：解析Linux内核全新异步IO引擎——io_uring设计与实现》 - 社交平台产品部 - KM平台_files/cos-file-url(6)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h1 id="参考">参考</h1>

<p><a href="https://lore.kernel.org/linux-block/20190211190049.7888-14-axboe@kernel.dk/" target="_blank"><em>[PATCH 12/19]io_uring: add support for pre-mapped user IO buffers</em></a></p>

<p><a href="https://lwn.net/Articles/97178/" target="_blank"><em>Add pread/pwrite support bits to match the lseek bit</em></a></p>

<p><a href="https://lwn.net/Articles/724198/" target="_blank"><em>Toward non-blocking asynchronous I/O</em></a></p>

<p><a href="https://lwn.net/Articles/743714/" target="_blank"><em>A new kernel polling interface</em></a></p>

<p><a href="https://lwn.net/Articles/810414/" target="_blank"><em>The rapid growth of io_uring</em></a></p>

<p><a href="https://lwn.net/Articles/776703/" target="_blank"><em>Ringing in a new asynchronous I/O API</em></a></p>

<p><a href="http://kernel.dk/io_uring.pdf" target="_blank"><em>Efficient IO with io_uring</em></a></p>

<p><a href="https://lwn.net/Articles/741878" target="_blank"><em>The current state of kernel page-table isolation</em></a></p>

<p><a href="https://www.kernel.org/doc/man-pages/" target="_blank">The Linux man-pages project</a></p>

<p><em>Computer Systems: A Programmer’s Perspective, Third Edition</em></p>

<p><em>Advanced Programming in the UNIX Environment, Third Edition</em></p>

<p><em>The Linux Programming Interface: A Linux and UNIX System Programming Handbook</em></p>

<p><a href="http://kernel.taobao.org/2020/08/Introduction_to_IO_uring/" target="_blank"><em>Introduction to io_uring</em></a></p>
