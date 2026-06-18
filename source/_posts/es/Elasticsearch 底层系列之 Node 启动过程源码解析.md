---
title: "Elasticsearch 底层系列之 Node 启动过程源码解析"
date: 2022-06-16 21:36:43
categories:
  - es
---

<h1 style="box-sizing:border-box;font-size:2.25em;margin:24px 0px 16px;font-weight:600;line-height:1.25;padding-bottom:.3em;border-bottom:1px solid #eaecef;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">Elasticsearch Node 启动过程源码解析</h1>
<h2 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.75em;font-weight:600;line-height:1.25;padding-bottom:.3em;border-bottom:1px solid #eaecef;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#elasticsearch-%E7%AE%80%E4%BB%8B" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>Elasticsearch 简介</h2>
<p style="box-sizing: border-box; margin-top: 0px; margin-bottom: 16px; color: rgb(36, 41, 46); font-family: -apple-system, BlinkMacSystemFont, 微软雅黑, &quot;PingFang SC&quot;, Helvetica, Arial, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei&quot;, SimSun, 宋体, Heiti, 黑体, sans-serif; font-size: 14px; font-style: normal; font-weight: 400; letter-spacing: normal; text-indent: 0px; text-transform: none; white-space: normal; word-spacing: 0px;"></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">Elasticsearch 是一款开源的分布式搜索引擎，提供了近实时的查询能力和强大的聚合分析能力。与Elastic官方提供的其他组件（Beats、Logstash、Kibana）组合成Elastic Stack，提供了多种使用场景下数据摄入、清洗、存储、查询、可视化的完整解决方案，在搜索、日志分析、统计分析等领域有广泛应用。</p>
<p style="box-sizing: border-box; margin-top: 0px; margin-bottom: 16px; color: rgb(36, 41, 46); font-family: -apple-system, BlinkMacSystemFont, 微软雅黑, &quot;PingFang SC&quot;, Helvetica, Arial, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei&quot;, SimSun, 宋体, Heiti, 黑体, sans-serif; font-size: 14px; font-style: normal; font-weight: 400; letter-spacing: normal; text-indent: 0px; text-transform: none; white-space: normal; word-spacing: 0px;"></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">Elasticsearch由多个节点组成一个分布式集群，一个节点被称为一个Node。本文将基于 Elasticsearch v6.4.3版本着重介绍Node的启动过程，也会简要概述ES内部的主要模块、线程池等。</p>
<h2 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.75em;font-weight:600;line-height:1.25;padding-bottom:.3em;border-bottom:1px solid #eaecef;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#elasticsearch-%E5%90%AF%E5%8A%A8%E8%BF%87%E7%A8%8B" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>Elasticsearch 启动过程</h2>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">Elasticsearch的启动流程主要涉及Elasticsearch、Bootstrap和Node三个类。主要包括加载三个步骤：</p>
<ul style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">加载本地环境：读取命令行参数和配置文件，生成本地环境配置</li>
<li style="box-sizing:border-box;margin-top:.25em;">创建Node：创建节点实例，创建各种服务类对象，注入各种功能模块</li>
<li style="box-sizing:border-box;margin-top:.25em;">启动Node：启动各种服务，加入集群</li>
</ul><p style="box-sizing: border-box; margin-top: 0px; margin-bottom: 16px; color: rgb(36, 41, 46); font-family: -apple-system, BlinkMacSystemFont, 微软雅黑, &quot;PingFang SC&quot;, Helvetica, Arial, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei&quot;, SimSun, 宋体, Heiti, 黑体, sans-serif; font-size: 14px; font-style: normal; font-weight: 400; letter-spacing: normal; text-indent: 0px; text-transform: none; white-space: normal; word-spacing: 0px;"></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">在详细解读这三个步骤前，这里先介绍下Elasticsearch的主程序入口。</p>
<h3 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.5em;font-weight:600;line-height:1.25;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#%E4%B8%BB%E7%A8%8B%E5%BA%8F%E5%85%A5%E5%8F%A3" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>主程序入口</h3>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">从elasticsearch的启动脚本（bin/elastisearch）中，可以看到主程序的入口是 org.elasticsearch.bootstrap.Elasticsearch。</p>
<h4 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.25em;font-weight:600;line-height:1.25;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#%E5%90%AF%E5%8A%A8%E8%84%9A%E6%9C%AC" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>启动脚本</h4>
<pre><code>  exec \
    "$JAVA" \
    $ES_JAVA_OPTS \
    -Des.path.home="$ES_HOME" \
    -Des.path.conf="$ES_PATH_CONF" \
    -Des.distribution.flavor="$ES_DISTRIBUTION_FLAVOR" \
    -Des.distribution.type="$ES_DISTRIBUTION_TYPE" \
    -cp "$ES_CLASSPATH" \
    org.elasticsearch.bootstrap.Elasticsearch \
    "$@"
</code></pre>
<h4 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.25em;font-weight:600;line-height:1.25;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#%E4%B8%BB%E7%A8%8B%E5%BA%8F%E5%85%A5%E5%8F%A3-2" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>主程序入口</h4>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">PATH</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">org.elasticsearch.bootstrap.Elasticsearch#main</p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">CODE</strong></p>
<pre><code>    /**
     * Main entry point for starting elasticsearch
     */
    public static void main(final String[] args) throws Exception {
        // 1. 创建安全管理器，授权所有操作
        System.setSecurityManager(new SecurityManager() {
            @Override
            public void checkPermission(Permission perm) {
                // grant all permissions so that we can later set the security manager to the one that we want
            }
        });
        // 2. 注册log侦听器
        LogConfigurator.registerErrorListener();
        // 3. 创建Elasticsearch类对象
        final Elasticsearch elasticsearch = new Elasticsearch();
        int status = main(args, elasticsearch, Terminal.DEFAULT);
        if (status != ExitCodes.OK) {
            exit(status);
        }
    }

    static int main(final String[] args, final Elasticsearch elasticsearch, final Terminal terminal) throws Exception {
        return elasticsearch.main(args, terminal);
    }
</code></pre>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">解析</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">入参 args 为命令行参数，该函数执行以下三个步骤：</p>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">设置安全管理器，授权所有操作：SecurityManager在Java中被用来检查应用程序是否能访问一些有限的资源，例如文件、套接字(socket)等。这里的checkPermission函数授权了所有操作。</li>
<li style="box-sizing:border-box;margin-top:.25em;">注册log侦听器：这里尽早启用日志侦听，防止有些日志无法被记录。</li>
<li style="box-sizing:border-box;margin-top:.25em;">创建Elasticsearch类对象，如下图所示，Elasticsearch的顺序继承至EnvironmentAwareCommand，Command。Elasticsearch()会调用父类构造函数，注册命令行的解析规则，后续解析命令行参数时使用。</li>
</ol><p style="box-sizing: border-box; margin-top: 0px; margin-bottom: 16px; color: rgb(36, 41, 46); font-family: -apple-system, BlinkMacSystemFont, 微软雅黑, &quot;PingFang SC&quot;, Helvetica, Arial, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei&quot;, SimSun, 宋体, Heiti, 黑体, sans-serif; font-size: 14px; font-style: normal; font-weight: 400; letter-spacing: normal; text-indent: 0px; text-transform: none; white-space: normal; word-spacing: 0px;"></p>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">调用elasticsearch.main()来做进一步的初始化操作（实际是Command#main）。如果初始化报错，则退出进程。</li>
</ol><h3 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.5em;font-weight:600;line-height:1.25;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#%E7%AC%AC%E4%B8%80%E6%AD%A5%E5%8A%A0%E8%BD%BD%E6%9C%AC%E5%9C%B0%E7%8E%AF%E5%A2%83elasticserach%E5%88%9D%E5%A7%8B%E5%8C%96" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>第一步：加载本地环境：Elasticserach初始化</h3>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">PATH</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">elasticsearch\libs\cli\src\main\java\org\elasticsearch\cli\Command.java</p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">CODE</strong></p>
<pre><code>
   /** Parses options for this command from args and executes it. */
    public final int main(String[] args, Terminal terminal) throws Exception {
        if (addShutdownHook()) {

            shutdownHookThread = new Thread(() -&gt; {
                try {
                    // Elasticsearch#close
                    this.close();
                } catch (final IOException e) {
                    try (
                        StringWriter sw = new StringWriter();
                        PrintWriter pw = new PrintWriter(sw)) {
                        // 异常关闭打印堆栈信息
                        e.printStackTrace(pw);
                        terminal.println(sw.toString());
                    }
                }
            });
            // 1. 增加shutdown时的hook线程，在进程退出时调用
            Runtime.getRuntime().addShutdownHook(shutdownHookThread);
        }

        try {
            // 2. 解析命令行参数
            mainWithoutErrorHandling(args, terminal);
        } catch (OptionException e) {
            printHelp(terminal);
            terminal.println(Terminal.Verbosity.SILENT, "ERROR: " + e.getMessage());
            return ExitCodes.USAGE;
        }
        return ExitCodes.OK;
    }
</code></pre>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">解析</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">Command#main的主要步骤两个：</p>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">addShutdownHook：向runtime增加进程退出时的回调线程，在进程退出时调用Elasticsearch#close，如果异常关闭则打印堆栈信息</li>
<li style="box-sizing:border-box;margin-top:.25em;">mainWithoutErrorHandling：解析部分命令行参数（-h，-v，-s）后，调用EnvironmentAwareCommand#execute：</li>
</ol><pre><code>    protected void execute(Terminal terminal, OptionSet options) throws Exception {
        final Map&lt;String, String&gt; settings = new HashMap&lt;&gt;();
        putSystemPropertyIfSettingIsMissing(settings, "path.data", "es.path.data");
        putSystemPropertyIfSettingIsMissing(settings, "path.home", "es.path.home");
        putSystemPropertyIfSettingIsMissing(settings, "path.logs", "es.path.logs");
        execute(terminal, options, createEnv(terminal, settings));
    }
</code></pre>
<ul style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">获取vm options指定的参数，放入settings中，如下图所示。</li>
</ul><p style="box-sizing: border-box; margin-top: 0px; margin-bottom: 16px; color: rgb(36, 41, 46); font-family: -apple-system, BlinkMacSystemFont, 微软雅黑, &quot;PingFang SC&quot;, Helvetica, Arial, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei&quot;, SimSun, 宋体, Heiti, 黑体, sans-serif; font-size: 14px; font-style: normal; font-weight: 400; letter-spacing: normal; text-indent: 0px; text-transform: none; white-space: normal; word-spacing: 0px;"></p>
<ul style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">调用createEnv，通过prepareEnvironment读取es的配置文件（conf/elasticsearch.yml），生成Environment，存储一些路径及ES配置信息。</li>
</ul><pre><code>    public static Environment prepareEnvironment(Settings input, Terminal terminal, Map&lt;String, String&gt; properties, Path configPath) {
        Settings.Builder output = Settings.builder();
        Path path = environment.configFile().resolve("elasticsearch.yml");
        if (Files.exists(path)) {
            try {
                output.loadFromPath(path);
            } catch (IOException e) {
                throw new SettingsException("Failed to load settings from " + path.toString(), e);
            }
        }
        return new Environment(output.build(), configPath);
    }
</code></pre>
<p style="box-sizing: border-box; margin-top: 0px; margin-bottom: 16px; color: rgb(36, 41, 46); font-family: -apple-system, BlinkMacSystemFont, 微软雅黑, &quot;PingFang SC&quot;, Helvetica, Arial, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei&quot;, SimSun, 宋体, Heiti, 黑体, sans-serif; font-size: 14px; font-style: normal; font-weight: 400; letter-spacing: normal; text-indent: 0px; text-transform: none; white-space: normal; word-spacing: 0px;"></p>
<ul style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">调用Elasticsearch#execute，读取daemonize/pidFile/quiet值，而后调用Elasticsearch#init -&gt; Bootstrap.init，初始化Bootstrap。</li>
</ul><pre><code>    protected void execute(Terminal terminal, OptionSet options, Environment env) throws UserException {
        final boolean daemonize = options.has(daemonizeOption);
        final Path pidFile = pidfileOption.value(options);
        final boolean quiet = options.has(quietOption);
        try {
            init(daemonize, pidFile, quiet, env);
        } catch (NodeValidationException e) {
            throw new UserException(ExitCodes.CONFIG, e.getMessage());
        }
    }

</code></pre>
<h3 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.5em;font-weight:600;line-height:1.25;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#bootstrap%E5%88%9D%E5%A7%8B%E5%8C%96" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>Bootstrap初始化</h3>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">PATH</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">elasticsearch\bootstrap\Bootstrap.java</p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">CODE</strong></p>
<pre><code>    /**
     * This method is invoked by {@link Elasticsearch#main(String[])} to startup elasticsearch.
     */
    static void init(
            final boolean foreground,
            final Path pidFile,
            final boolean quiet,
            final Environment initialEnv) throws BootstrapException, NodeValidationException, UserException {

        // 1. 创建 Bootstrap 类对象, 启动keepAlive线程
        INSTANCE = new Bootstrap();

        // 2. 加载安全、日志配置信息,创建pidFile
        final SecureSettings keystore = loadSecureSettings(initialEnv);
        try {
            LogConfigurator.configure(environment);
        } catch (IOException e) {
            throw new BootstrapException(e);
        }
        if (environment.pidFile() != null) {
            try {
                PidFile.create(environment.pidFile(), true);
            } catch (IOException e) {
                throw new BootstrapException(e);
            }
        }
        try {
            // 检测Lucene Jar版本
            checkLucene();
            // 3. 创建Node
            INSTANCE.setup(true, environment);
            // 4. 启动Node
            INSTANCE.start();

        } catch (NodeValidationException | RuntimeException e) {

        }
    }

</code></pre>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">解析</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">Bootstrap#init 顺序执行以下步骤：</p>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">创建 Bootstrap 类对象，创建keepAliveThread，等待keepAliveLatch降为0时，该线程退出。同时向runtime添加一个ShutdownHook，当进程退出时，keepAliveLatch降为0，keepAliveThread退出。<code style="box-sizing:border-box;font-family:&#39;SFMono-Regular&#39;, Consolas, &#39;Liberation Mono&#39;, Menlo, Courier, monospace;font-size:11.9px;padding:.2em 0px;margin:0px;background-color:rgba(27,31,35,.05);border-radius:3px;">The Java Virtual Machine exits when the only threads running are all daemon threads.</code><span>&nbsp;</span>当唯一的非Deamon线程，keepAliveThread退出时，JVM关闭。</li>
</ol><pre><code>    /** creates a new instance */
    Bootstrap() {
        keepAliveThread = new Thread(new Runnable() {
            public void run() {
                try {
                    // 等待进程退出，等待keepAliveLatch降为0时，退出当前线程。
                    keepAliveLatch.await();
                }
            }
        }, "elasticsearch[keepAlive/" + Version.CURRENT + "]");
        keepAliveThread.setDaemon(false);
        // keep this thread alive (non daemon thread) until we shutdown
        Runtime.getRuntime().addShutdownHook(new Thread() {
            public void run() {
                // 进程退出时，keepAliveLatch降为0，keepAliveThread退出。
                keepAliveLatch.countDown();
            }
        });
    }
</code></pre>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">设定安全、日志配置信息，创建pidFile。pidFile为es的进程ID，防止多个ES进程读写同一路径。</li>
<li style="box-sizing:border-box;margin-top:.25em;">创建Node：ES的一个节点被封装为一个Node实例，由Node调用ES的各个模块，完成集群管理、写入、查询等功能。</li>
</ol><pre><code>    private void setup(boolean addShutdownHook, Environment environment) throws BootstrapException {

        try {
            // 遍历modules目录，读取各模块信息，为其生成控制类，这些控制类将通过stdin, stdout 和 stderr 与JVM保持连接
            spawner.spawnNativeControllers(environment);
        } catch (IOException e) {
            throw new BootstrapException(e);
        }
        // 本地环境的检测、设置（user/thread/VirtualMemory/fileSize等）
        initializeNatives(
                environment.tmpFile(),
                BootstrapSettings.MEMORY_LOCK_SETTING.get(settings),
                BootstrapSettings.SYSTEM_CALL_FILTER_SETTING.get(settings),
                BootstrapSettings.CTRLHANDLER_SETTING.get(settings));

        // 创建Node节点，后节详述
        node = new Node(environment) {
            @Override
            protected void validateNodeBeforeAcceptingRequests(
                final BootstrapContext context,
                final BoundTransportAddress boundTransportAddress, List&lt;BootstrapCheck&gt; checks) throws NodeValidationException {
                BootstrapChecks.check(context, boundTransportAddress, checks);
            }
        };
    }
</code></pre>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">启动Node</li>
</ol><pre><code>    private void start() throws NodeValidationException {
        // 启动Node，后节详述
        node.start();
        // 启动前台keepAliveThread线程，等待进程关闭时，关闭JVM
        keepAliveThread.start();
    }
</code></pre>
<h3 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.5em;font-weight:600;line-height:1.25;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#%E7%AC%AC%E4%BA%8C%E6%AD%A5%E5%88%9B%E5%BB%BAnode" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>第二步：创建Node</h3>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">PATH</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">elasticsearch\node\Node.java</p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">CODE</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">代码较长，做了大量精简：</p>
<pre><code>    protected Node(final Environment environment, Collection&lt;Class&lt;? extends Plugin&gt;&gt; classpathPlugins) {

        try {
            // 1. 创建节点环境，包括nodeId/nodePaths/logger等；创建tmpSettings，主要是一些节点配置信息
            // create the node environment as soon as possible, to recover the node id and enable logging
            try {
                nodeEnvironment = new NodeEnvironment(tmpSettings, environment);
            } catch (IOException ex) {
                throw new IllegalStateException("Failed to create node environment", ex);
            }
            final boolean hadPredefinedNodeName = NODE_NAME_SETTING.exists(tmpSettings);
            final String nodeId = nodeEnvironment.nodeId();
            tmpSettings = addNodeNameIfNeeded(tmpSettings, nodeId);
            final Logger logger = Loggers.getLogger(Node.class, tmpSettings);
            // this must be captured after the node name is possibly added to the settings
            final String nodeName = NODE_NAME_SETTING.get(tmpSettings);
            if (hadPredefinedNodeName == false) {
                logger.info("node name derived from node ID [{}]; set [{}] to override", nodeId, NODE_NAME_SETTING.getKey());
            } else {
                logger.info("node name [{}], node ID [{}]", nodeName, nodeId);
            }
            // 2. 打印 jvm 信息
            final JvmInfo jvmInfo = JvmInfo.jvmInfo();
            logger.info("JVM arguments {}", Arrays.toString(jvmInfo.getInputArguments()));

            // 3. 创建PluginsService，加载modules目录下的所有模块和plugins目录下的所有插件
            this.pluginsService = new PluginsService(tmpSettings, environment.configFile(), environment.modulesFile(), environment.pluginsFile(), classpathPlugins);

            // 4. 创建Node.environment
             this.environment = new Environment(this.settings, environment.configFile());

            // 5. 调用各插件的getExecutorBuilders，获取ExecutorBuilder/thread pool
            final List&lt;ExecutorBuilder&lt;?&gt;&gt; executorBuilders = pluginsService.getExecutorBuilders(settings);

            // 6. 创建线程池
            final ThreadPool threadPool = new ThreadPool(settings, executorBuilders.toArray(new ExecutorBuilder[0]));

            // 7. 创建NodeClient
            client = new NodeClient(settings, threadPool);

            // 8. 创建各种服务类对象***Service和各种模块对象***Module
            final ResourceWatcherService resourceWatcherService = new ResourceWatcherService(settings, threadPool);
            final ScriptModule scriptModule = new ScriptModule(settings, pluginsService.filterPlugins(ScriptPlugin.class));
            AnalysisModule analysisModule = new AnalysisModule(this.environment, pluginsService.filterPlugins(AnalysisPlugin.class));
            ...
            final PersistentTasksService persistentTasksService = new PersistentTasksService(settings, clusterService, threadPool, client);

            // 绑定各种服务模块的实例
            modules.add(b -&gt; {
                    b.bind(Node.class).toInstance(this);
                    b.bind(NodeService.class).toInstance(nodeService);
                    ...
                    b.bind(GatewayMetaState.class).toInstance(gatewayMetaState);
                    b.bind(PersistentTasksExecutorRegistry.class).toInstance(registry);
                }
            );
            injector = modules.createInjector();

            // 9. 初始化rest handler，用于后续接收 http rest 请求
            if (NetworkModule.HTTP_ENABLED.get(settings)) {
                logger.debug("initializing HTTP handlers ...");
                actionModule.initRestHandlers(() -&gt; clusterService.state().nodes());
            }

            // node初始化完成
            logger.info("initialized");
            success = true;
        } catch (IOException ex) {
            throw new ElasticsearchException("failed to bind service", ex);
        } finally {
            if (!success) {
                IOUtils.closeWhileHandlingException(resourcesToClose);
            }
        }
    }
</code></pre>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">解析</strong></p>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">创建节点环境，包括nodeId/nodePaths/logger等；创建tmpSettings，主要是一些节点配置信息。lock data目录。</li>
</ol><p style="box-sizing: border-box; margin-top: 0px; margin-bottom: 16px; color: rgb(36, 41, 46); font-family: -apple-system, BlinkMacSystemFont, 微软雅黑, &quot;PingFang SC&quot;, Helvetica, Arial, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei&quot;, SimSun, 宋体, Heiti, 黑体, sans-serif; font-size: 14px; font-style: normal; font-weight: 400; letter-spacing: normal; text-indent: 0px; text-transform: none; white-space: normal; word-spacing: 0px;"></p>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">打印 JVM 信息</li>
<li style="box-sizing:border-box;margin-top:.25em;">创建PluginsService，加载classpath、modules目录和plugins目录下的所有模块</li>
</ol><p style="box-sizing: border-box; margin-top: 0px; margin-bottom: 16px; color: rgb(36, 41, 46); font-family: -apple-system, BlinkMacSystemFont, 微软雅黑, &quot;PingFang SC&quot;, Helvetica, Arial, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei&quot;, SimSun, 宋体, Heiti, 黑体, sans-serif; font-size: 14px; font-style: normal; font-weight: 400; letter-spacing: normal; text-indent: 0px; text-transform: none; white-space: normal; word-spacing: 0px;"></p>
<pre><code>    public PluginsService(Settings settings, Path configPath, Path modulesDirectory, Path pluginsDirectory, Collection&lt;Class&lt;? extends Plugin&gt;&gt; classpathPlugins) {

        List&lt;Tuple&lt;PluginInfo, Plugin&gt;&gt; pluginsLoaded = new ArrayList&lt;&gt;();
        List&lt;PluginInfo&gt; pluginsList = new ArrayList&lt;&gt;();
        final List&lt;String&gt; pluginsNames = new ArrayList&lt;&gt;();

        // 加载 classpath 中的plugins， 供 tests 和 transport clients 使用
        for (Class&lt;? extends Plugin&gt; pluginClass : classpathPlugins) {
            pluginsLoaded.add(new Tuple&lt;&gt;(pluginInfo, plugin));
            pluginsList.add(pluginInfo);
        }

        Set&lt;Bundle&gt; seenBundles = new LinkedHashSet&lt;&gt;();
        List&lt;PluginInfo&gt; modulesList = new ArrayList&lt;&gt;();

        // 加载 modules
        if (modulesDirectory != null) {
            Set&lt;Bundle&gt; modules = getModuleBundles(modulesDirectory);
            for (Bundle bundle : modules) {
                ...
            }
            seenBundles.addAll(modules);
        }

        // 加载 plugins/ 目录下的 plugins
        if (pluginsDirectory != null) {
            Set&lt;Bundle&gt; plugins = getPluginBundles(pluginsDirectory);
            for (final Bundle bundle : plugins) {
                pluginsList.add(bundle.plugin);
            }
            seenBundles.addAll(plugins);
        }

        // 前面装载的每个module和plugin都是一个bundle, a "bundle" is a group of jars in a single classloader
        // 因此这里可以将modules和plugins统一封装为Plugin
        List&lt;Tuple&lt;PluginInfo, Plugin&gt;&gt; loaded = loadBundles(seenBundles);
        pluginsLoaded.addAll(loaded);

        // 将plugins和modules的元信息保存至PluginsAndModules info
        this.info = new PluginsAndModules(pluginsList, modulesList);

        // 将Plugin放入List&lt;Tuple&lt;PluginInfo, Plugin&gt;&gt; plugins
        this.plugins = Collections.unmodifiableList(pluginsLoaded);

    }

</code></pre>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">创建Node.environment</li>
<li style="box-sizing:border-box;margin-top:.25em;">调用各插件的getExecutorBuilders，获取ExecutorBuilder</li>
<li style="box-sizing:border-box;margin-top:.25em;">创建ThreadPool</li>
</ol><pre><code>    // ThreadPool构造函数：
    public ThreadPool(final Settings settings, final ExecutorBuilder&lt;?&gt;... customBuilders) {

        final Map&lt;String, ExecutorBuilder&gt; builders = new HashMap&lt;&gt;();
        // 获取本机cpu核数，假设cpu核数为8
        final int availableProcessors = EsExecutors.numberOfProcessors(settings);
        // (cpu+1)/2 在区间 [1,5] 中的取值，此处(8+1)/2 = 4, 在[1,5]区间内取值为4
        final int halfProcMaxAt5 = halfNumberOfProcessorsMaxFive(availableProcessors);
        // (cpu+1)/2 在区间 [1,10] 中的取值，此处(8+1)/2 = 4, 在[1,5]区间内取值为4
        final int halfProcMaxAt10 = halfNumberOfProcessorsMaxTen(availableProcessors);
        // 4*8=32，genericThreadPoolMax在区间[128,512]中的取值为128
        final int genericThreadPoolMax = boundedBy(4 * availableProcessors, 128, 512);

        // 创建各种线程池的builder
        builders.put(Names.GENERIC, new ScalingExecutorBuilder(Names.GENERIC, 4, genericThreadPoolMax, TimeValue.timeValueSeconds(30)));
        builders.put(Names.INDEX, new FixedExecutorBuilder(settings, Names.INDEX, availableProcessors, 200, true));
        builders.put(Names.WRITE, new FixedExecutorBuilder(settings, Names.WRITE, "bulk", availableProcessors, 200));
        ...

        threadContext = new ThreadContext(settings);

        // 创建各种线程池
        final Map&lt;String, ExecutorHolder&gt; executors = new HashMap&lt;&gt;();
        for (@SuppressWarnings("unchecked") final Map.Entry&lt;String, ExecutorBuilder&gt; entry : builders.entrySet()) {
            final ExecutorHolder executorHolder = entry.getValue().build(executorSettings, threadContext);
            executors.put(entry.getKey(), executorHolder);
        }
        executors.put(Names.SAME, new ExecutorHolder(DIRECT_EXECUTOR, new Info(Names.SAME, ThreadPoolType.DIRECT)));
        this.executors = unmodifiableMap(executors);
    }
</code></pre>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">线程池类型：</p>
<ul style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">
<p style="box-sizing:border-box;margin-top:16px;margin-bottom:16px;">DIRECT：即<code style="box-sizing:border-box;font-family:&#39;SFMono-Regular&#39;, Consolas, &#39;Liberation Mono&#39;, Menlo, Courier, monospace;font-size:11.9px;padding:.2em 0px;margin:0px;background-color:rgba(27,31,35,.05);border-radius:3px;">elasticsearch.common.util.concurrent.EsExecutors#DIRECT_EXECUTOR_SERVICE</code>。通过调用方的当前线程，执行一个Runnable.run()过程，运行过程中该线程不允许被关闭。<code style="box-sizing:border-box;font-family:&#39;SFMono-Regular&#39;, Consolas, &#39;Liberation Mono&#39;, Menlo, Courier, monospace;font-size:11.9px;padding:.2em 0px;margin:0px;background-color:rgba(27,31,35,.05);border-radius:3px;">an {@link ExecutorService} that executes submitted tasks on the current thread. This executor service does not support being shutdown.</code></p>
</li>
<li style="box-sizing:border-box;margin-top:.25em;">
<p style="box-sizing:border-box;margin-top:16px;margin-bottom:16px;">FIXED: 线程数量固定，有队列，队列长度为固定值。无空闲线程时，请求被放入队列中。参数：</p>
</li>
</ul><pre><code>size      the fixed number of threads
queueSize the size of the backing queue, -1 for unbounded
</code></pre>
<ul style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">SCALING: 线程数量不固定，在core和max之间动态变化。参数：</li>
</ul><pre><code>core      the minimum number of threads in the pool
max       the maximum number of threads in the pool
keepAlive the time that spare threads above {@code core} threads will be kept alive
</code></pre>
<ul style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">FIXED_AUTO_QUEUE_SIZE: 线程数量固定，有队列，队列长度为不固定。参数：</li>
</ul><pre><code>size             the fixed number of threads
initialQueueSize initial size of the backing queue
minQueueSize     the minimum size of the backing queue
maxQueueSize     the maximum size of the backing queue
</code></pre>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">ES中的线程池：</p>
<table style="box-sizing:border-box;border-spacing:0px;border-collapse:collapse;margin-top:0px;margin-bottom:16px;display:table;width:auto;overflow:auto;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><thead style="box-sizing:border-box;"><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><th style="box-sizing:border-box;padding:6px 13px;font-weight:600;border:1px solid #dfe2e5;">线程池名称</th>
<th style="box-sizing:border-box;padding:6px 13px;font-weight:600;border:1px solid #dfe2e5;">类型</th>
<th style="box-sizing:border-box;padding:6px 13px;font-weight:600;border:1px solid #dfe2e5;">介绍</th>
<th style="box-sizing:border-box;padding:6px 13px;font-weight:600;border:1px solid #dfe2e5;">参数默认值</th>
</tr></thead><tbody style="box-sizing:border-box;"><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SAME</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">DIRECT</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">通过当前线程直接执行某些逻辑</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;"></td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">LISTENER</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FIXED</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于java client得到响应时执行某些逻辑</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">size：min((availableProcessors + 1) / 2, 10)，queueSize：10</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">GET</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FIXED</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于get请求</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">size：availableProcessors， queueSize：200</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">ANALYZE</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FIXED</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于analyze（分词）操作</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">size：1， queueSize：16</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">WRITE</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FIXED</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于put/bulk请求</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">size：availableProcessors， queueSize：200</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FORCE_MERGE</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FIXED</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于segment force-merge操作</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">size：1， queueSize：-1</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">GENERIC</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SCALING</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">通用的线程，如NodeDiscovery等</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">core：4，max：availableProcessors*4 在区间[128，512]中的取值，keepAlive：30s</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">MANAGEMENT</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SCALING</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于集群管理等</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">core：1，max：5，keepAlive：5m</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FLUSH</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SCALING</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于flush操作</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">core：1，max：min((availableProcessors + 1) / 2, 5)，keepAlive：5m</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">REFRESH</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SCALING</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于refresh操作</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">core：1，max：min((availableProcessors + 1) / 2, 10)，keepAlive：5m</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">WARMER</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SCALING</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于segment warm-up操作</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">core：1，max：min((availableProcessors + 1) / 2, 5)，keepAlive：5m</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SNAPSHOT</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SCALING</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于snapshot操作</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">core：1，max：min((availableProcessors + 1) / 2, 5)，keepAlive：5m</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FETCH_SHARD_STARTED</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SCALING</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于fetch shard开始操作</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">core：1，max：availableProcessors * 2，keepAlive：5m</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FETCH_SHARD_STORE</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SCALING</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于fetch shard存储操作</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">core：1，max：availableProcessors * 2，keepAlive：5m</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SEARCH</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">FIXED_AUTO_QUEUE_SIZE</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于search/count/suggest请求</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">size:((availableProcessors * 3) / 2) + 1，initialQueueSize：1000，minQueueSize：1000，maxQueueSize：1000</td>
</tr></tbody></table><ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">创建客户端NodeClient</li>
<li style="box-sizing:border-box;margin-top:.25em;">创建各种服务类对象xxxService，利用Guice注册各种服务使用的模块xxxModule</li>
</ol><ul style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">Service：</li>
</ul><table style="box-sizing:border-box;border-spacing:0px;border-collapse:collapse;margin-top:0px;margin-bottom:16px;display:table;width:auto;overflow:auto;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><thead style="box-sizing:border-box;"><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><th style="box-sizing:border-box;padding:6px 13px;font-weight:600;border:1px solid #dfe2e5;">服务</th>
<th style="box-sizing:border-box;padding:6px 13px;font-weight:600;border:1px solid #dfe2e5;">简介</th>
</tr></thead><tbody style="box-sizing:border-box;"><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">ResourceWatcherService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">监控统计各种服务使用的资源</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">NetworkService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">TCP/IP/PORT等网络配置管理</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">ClusterService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">集群管理，集群状态发布、更新等</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">IngestService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">Ingest Node的写入数据预处理服务</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">ClusterInfoService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">用于获取最新的集群信息</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">UsageService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">监视Elasticsearch各种功能的使用情况</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">MonitorService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">JVM、进程、系统的监控服务</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">CircuitBreakerService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">熔断服务，资源使用超限时阻止任务执行</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">MetaStateService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">读写Metadata和IndexMetadata</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">IndicesService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">索引管理，索引的创建、删除等操作</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">IndicesClusterStateService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">集群状态更新时，处理索引相关的操作</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">MetaDataIndexUpgradeService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">更新IndexMetadata至最新版本</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">TemplateUpgradeService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">节点加入集群时，升级其plugins相关的template</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">TransportService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">Transport层网络服务</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">HttpServerTransport</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">Http层网络服务，提供REST接口服务</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">ResponseCollectorService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">收集每个节点上执行任务的队列大小，响应时间和服务时间的统计信息</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">NodeService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">一个节点的实例，负责调用各种服务</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SearchService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">处理查询任务</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">SnapshotsService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">快照服务</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">Discovery</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">集群发现服务</td>
</tr><tr style="box-sizing:border-box;background-color:#ffffff;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">RoutingService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">路由表管理</td>
</tr><tr style="box-sizing:border-box;background-color:#f6f8fa;border-top:1px solid #c6cbd1;"><td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">GatewayService</td>
<td style="box-sizing:border-box;padding:6px 13px;border:1px solid #dfe2e5;">集群、索引的元数据的持久化及恢复</td>
</tr></tbody></table><ul style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">Module：ScriptModule、AnalysisModule、SettingsModule、PluginModule、ClusterModule、IndicesModule、SearchModule、GatewayModule、RepositoriesModule、ActionModule、NetworkModule、DiscoveryModule。各模块功能可以参照上面的同名Service。</li>
</ul><h3 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.5em;font-weight:600;line-height:1.25;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#%E7%AC%AC%E4%B8%89%E6%AD%A5%E5%90%AF%E5%8A%A8node" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>第三步：启动Node</h3>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">PATH</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">elasticsearch\node\Node.java</p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">CODE</strong></p>
<pre><code>    /**
     * Start the node. If the node is already started, this method is no-op.
     */
    public Node start() throws NodeValidationException {
        // 1. 状态机，将local node的state设为STARTED状态
        if (!lifecycle.moveToStarted()) {
            return this;
        }

        logger.info("starting ...");

        // LifecycleComponent in modules and plugins start
        pluginLifecycleComponents.forEach(LifecycleComponent::start);

        // 2. 获取创建Node时各种模块及服务绑定的实例，启动这些实例
        // AbstractLifecycleComponent.start() -&gt; class.doStart()

        injector.getInstance(MappingUpdatedAction.class).setClient(client);
        injector.getInstance(IndicesService.class).start();
        injector.getInstance(IndicesClusterStateService.class).start();
        injector.getInstance(SnapshotsService.class).start();
        injector.getInstance(SnapshotShardsService.class).start();
        injector.getInstance(RoutingService.class).start();
        injector.getInstance(SearchService.class).start();
        nodeService.getMonitorService().start();
        ...
        Discovery discovery = injector.getInstance(Discovery.class);
        clusterService.getMasterService().setClusterStatePublisher(discovery::publish);

        // 启动 transport service
        TransportService transportService = injector.getInstance(TransportService.class);
        transportService.getTaskManager().setTaskResultsService(injector.getInstance(TaskResultsService.class));
        transportService.start();

        // 加载本地的MeteData信息
        final MetaData onDiskMetadata;
        try {
            if (DiscoveryNode.isMasterNode(settings) || DiscoveryNode.isDataNode(settings)) {
                onDiskMetadata = injector.getInstance(GatewayMetaState.class).loadMetaState();
            } else {
                onDiskMetadata = MetaData.EMPTY_META_DATA;
            }

        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }

        // bootstrap的各项检测：BootstrapChecks.check
        validateNodeBeforeAcceptingRequests(new BootstrapContext(settings, onDiskMetadata), transportService.boundAddress(), pluginsService
            .filterPlugins(Plugin
            .class)
            .stream()
            .flatMap(p -&gt; p.getBootstrapChecks().stream()).collect(Collectors.toList()));

        // 初始化ClusterState，启动Discovery
        discovery.start();
        // 启动clusterServeice、clusterApplierService、masterService
        clusterService.start();

        // transport层启动，开始接受请求
        transportService.acceptIncomingRequests();
        // initial discovery -&gt; ZenDiscovery.java innerJoinCluster（），加入集群
        discovery.startInitialJoin();

        // Http层启动，开始接受请求
        injector.getInstance(HttpServerTransport.class).start();

        // 节点启动成功
        logger.info("started");

        pluginsService.filterPlugins(ClusterPlugin.class).forEach(ClusterPlugin::onNodeStarted);

        return this;
    }
</code></pre>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><strong style="box-sizing:border-box;font-weight:600;">解析</strong></p>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">启动node时，主要是获取各个服务模块绑定的实例，调用每个实例的start()方法（实际是 class.doStart()）来启动各项服务。这其中比较重要的几个过程有：</p>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">启动 transport service，使得后续该节点可通过discovery过程加入集群</li>
<li style="box-sizing:border-box;margin-top:.25em;">如果该节点node.master属性为true的话，加载本地的metadata，以获取原集群的信息（节点挂掉后重启的场景）</li>
<li style="box-sizing:border-box;margin-top:.25em;">bootstrap check，检测ES当前的运行环境，主要是操作系统和JVM参数，如下图所示。某些检测不通过则ES会报错退出。各项检测的具体含义可以参考<a href="https://www.elastic.co/guide/en/elasticsearch/reference/6.4/bootstrap-checks.html" target="_blank" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;" rel="noreferrer">官方文档 Bootstrap Checks</a>。</li>
</ol><p style="box-sizing: border-box; margin-top: 0px; margin-bottom: 16px; color: rgb(36, 41, 46); font-family: -apple-system, BlinkMacSystemFont, 微软雅黑, &quot;PingFang SC&quot;, Helvetica, Arial, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei&quot;, SimSun, 宋体, Heiti, 黑体, sans-serif; font-size: 14px; font-style: normal; font-weight: 400; letter-spacing: normal; text-indent: 0px; text-transform: none; white-space: normal; word-spacing: 0px;"></p>
<ol style="box-sizing:border-box;padding-left:2em;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><li style="box-sizing:border-box;">启动discovery和clusterService，初始化集群元信息ClusterState</li>
<li style="box-sizing:border-box;margin-top:.25em;">启动transport服务，用于节点间通信</li>
<li style="box-sizing:border-box;margin-top:.25em;">启动initial discovery，加入所属的Elasticsearch集群</li>
<li style="box-sizing:border-box;margin-top:.25em;">启动http服务，开始接受用户请求</li>
</ol><h2 style="box-sizing:border-box;margin-top:24px;margin-bottom:16px;font-size:1.75em;font-weight:600;line-height:1.25;padding-bottom:.3em;border-bottom:1px solid #eaecef;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-style:normal;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;"><a href="https://note.youdao.com/md/preview.html?file=%2Fyws%2Fapi%2Fpersonal%2Ffile%2F7C63765EE638477195831E83CB80CE2B%3Fmethod%3Ddownload%26read%3Dtrue%26shareKey%3D35d14b1c03d89b5088acd1b34a720a7c#%E5%90%AF%E5%8A%A8%E6%97%A5%E5%BF%97" style="box-sizing:border-box;background-color:transparent;color:#0366d6;text-decoration:none;"></a>启动日志</h2>
<p style="box-sizing:border-box;margin-top:0px;margin-bottom:16px;color:#24292e;font-family:&#39;-apple-system&#39;, BlinkMacSystemFont, &#39;微软雅黑&#39;, &#39;PingFang SC&#39;, Helvetica, Arial, &#39;Hiragino Sans GB&#39;, &#39;Microsoft YaHei&#39;, SimSun, &#39;宋体&#39;, Heiti, &#39;黑体&#39;, sans-serif;font-size:14px;font-style:normal;font-weight:400;letter-spacing:normal;text-indent:0px;text-transform:none;white-space:normal;word-spacing:0px;">最后我们通过ES节点的日志来验证下上面讲述的节点启动流程</p>
<pre><code>
# 开始创建Node
[2018-12-28T19:54:44,159][INFO ][o.e.n.Node               ] [] initializing ...
# 读取本地目录信息、JVM信息，创建NodeEnvironment
[2018-12-28T19:54:44,376][INFO ][o.e.e.NodeEnvironment    ] [V9VXhfr] using [1] data paths, mounts [[项目 (D:)]], net usable_space [271.7gb], net total_space [310gb], types [NTFS]
[2018-12-28T19:54:44,376][INFO ][o.e.e.NodeEnvironment    ] [V9VXhfr] heap size [1gb], compressed ordinary object pointers [true]
# 打印NodeName等节点信息
[2018-12-28T19:54:44,379][INFO ][o.e.n.Node               ] [V9VXhfr] node name derived from node ID [V9VXhfr9TvSyUfxyr-ZQWg]; set [node.name] to override
[2018-12-28T19:54:44,379][INFO ][o.e.n.Node               ] [V9VXhfr] version[6.4.3-SNAPSHOT], pid[19512], build[unknown/unknown/Unknown/Unknown], OS[Windows 7/6.1/amd64], JVM["Oracle Corporation"/Java HotSpot(TM) 64-Bit Server VM/10.0.1/10.0.1+10]
# 打印JVM信息
[2018-12-28T19:54:44,379][INFO ][o.e.n.Node               ] [V9VXhfr] JVM arguments [-agentlib:jdwp=transport=dt_socket,address=127.0.0.1:8831,suspend=y,server=n, -Des.path.home=D:\elasticsearch_release\elasticsearch-6.4.3, -Des.path.conf=D:\elasticsearch_release\elasticsearch-6.4.3\config, -Djava.security.policy=D:\elasticsearch_release\elasticsearch-6.4.3\config\java.policy, -Dlog4j2.disable.jmx=true, -Xms1g, -Xmx1g, -javaagent:C:\Users\morningchen\.IntelliJIdea2018.3\system\groovyHotSwap\gragent.jar, -javaagent:C:\Users\morningchen\.IntelliJIdea2018.3\system\captureAgent\debugger-agent.jar, -Dfile.encoding=UTF-8]
# 初始化各种Service和Module
# 加载各种module
[2018-12-28T19:54:53,359][INFO ][o.e.p.PluginsService     ] [V9VXhfr] loaded module [aggs-matrix-stats]
[2018-12-28T19:54:53,359][INFO ][o.e.p.PluginsService     ] [V9VXhfr] loaded module [analysis-common]
...
[2018-12-28T19:54:53,362][INFO ][o.e.p.PluginsService     ] [V9VXhfr] loaded module [x-pack-watcher]
# 加载plugin
[2018-12-28T19:54:53,362][INFO ][o.e.p.PluginsService     ] [V9VXhfr] no plugins loaded
[2018-12-28T19:54:58,078][DEBUG][o.e.a.ActionModule       ] Using REST wrapper from plugin org.elasticsearch.xpack.security.Security
[2018-12-28T19:54:58,271][INFO ][o.e.d.DiscoveryModule    ] [V9VXhfr] using discovery type [zen]
[2018-12-28T19:54:59,102][INFO ][o.e.n.Node               ] [V9VXhfr] initialized
# 开始启动Node
[2018-12-28T19:54:59,102][INFO ][o.e.n.Node               ] [V9VXhfr] starting ...
# 启动Transport服务
[2018-12-28T19:54:59,428][INFO ][o.e.t.TransportService   ] [V9VXhfr] publish_address {10.40.98.48:9300}, bound_addresses {127.0.0.1:9300}, {[::1]:9300}
# BootstrapChecks
[2018-12-28T19:54:59,442][INFO ][o.e.b.BootstrapChecks    ] [V9VXhfr] bound or publishing to a non-loopback address, enforcing bootstrap checks
# 加入集群
[2018-12-28T19:55:54,939][INFO ][o.e.c.s.MasterService    ] [V9VXhfr] zen-disco-elected-as-master ([0] nodes joined)[, ], reason: new_master {V9VXhfr}{V9VXhfr9TvSyUfxyr-ZQWg}{m7N1OuBHRSuJlyGOoIJmqw}{10.40.98.48}{10.40.98.48:9300}{ml.machine_memory=17099067392, xpack.installed=true, ml.max_open_jobs=20, ml.enabled=true}
[2018-12-28T19:55:54,945][INFO ][o.e.c.s.ClusterApplierService] [V9VXhfr] new_master {V9VXhfr}{V9VXhfr9TvSyUfxyr-ZQWg}{m7N1OuBHRSuJlyGOoIJmqw}{10.40.98.48}{10.40.98.48:9300}{ml.machine_memory=17099067392, xpack.installed=true, ml.max_open_jobs=20, ml.enabled=true}, reason: apply cluster state (from master [master {V9VXhfr}{V9VXhfr9TvSyUfxyr-ZQWg}{m7N1OuBHRSuJlyGOoIJmqw}{10.40.98.48}{10.40.98.48:9300}{ml.machine_memory=17099067392, xpack.installed=true, ml.max_open_jobs=20, ml.enabled=true} committed version [1] source [zen-disco-elected-as-master ([0] nodes joined)[, ]]])
# 启动Http服务
[2018-12-28T19:55:58,722][INFO ][o.e.x.s.t.n.SecurityNetty4HttpServerTransport] [V9VXhfr] publish_address {10.40.98.48:9200}, bound_addresses {127.0.0.1:9200}, {[::1]:9200}
# 节点启动完毕
[2018-12-28T19:55:58,723][INFO ][o.e.n.Node               ] [V9VXhfr] started
# license检测
[2018-12-28T19:55:58,902][INFO ][o.e.l.LicenseService     ] [V9VXhfr] license [a4e08819-7a8b-4017-8b85-5329bc2909b0] mode [basic] - valid
# 开始恢复本地数据
[2018-12-28T19:55:58,926][INFO ][o.e.g.GatewayService     ] [V9VXhfr] recovered [0] indices into cluster_state
</code></pre>				</div>
