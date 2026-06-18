---
title: "STKE---基于Kubernetes的云原生平台实践"
date: 2022-06-12 11:03:11
categories:
  - kubernetes
---

<blockquote>
<p>Author： <a href="mailto:kanesong@tencent.com" target="_blank">kanesong@tencent.com</a></p>
<p>导语： STKE作为公司内的上云容器平台，基于容器服务（Tencent Kubernetes Engine，TKE），原生 kubernetes 技术，提供容器服务。在应对内部服务上云的时候，做了很多针对性的开发，在保有云原生能力的条件下，最大程度帮助用户降低Kubernetes使用成本，提高使用效率，并且能享受使用云原生技术带来的便利。STKE正在积极参与公司k8s oteam开源协同共建。作为公司内的自研上云容器平台，本文主要介绍STKE团队，基于云原生Kubernetes在内部落地设计，以及周边生态建设的实践落地。</p>
</blockquote>

<h2 id="目录">目录</h2>
<nav class="table-of-contents"><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#%E7%9B%AE%E5%BD%95">目录</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#%E5%8D%8F%E5%90%8C%E5%85%B1%E5%BB%BA">协同共建</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#1-1%20%E4%BB%80%E4%B9%88%E6%98%AF%E4%BA%91%E5%8E%9F%E7%94%9F">1.1 什么是云原生</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#1-2%20%E4%B8%BA%E4%BB%80%E4%B9%88%E4%BA%91%E5%8E%9F%E7%94%9F">1.2 为什么云原生</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#1-3%20%E4%B8%BA%E4%BB%80%E4%B9%88Docker">1.3 为什么Docker</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#1-4%20%E4%B8%BA%E4%BB%80%E4%B9%88Kubernetes">1.4 为什么Kubernetes</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#1-5%20%E7%8E%B0%E7%8A%B6">1.5 现状</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#1-6%20%E6%8C%91%E6%88%98">1.6 挑战</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#2%20%E5%B9%B3%E5%8F%B0%E4%BB%8B%E7%BB%8D">2 平台介绍</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#2-1%20%E8%AE%BE%E8%AE%A1%E5%8E%9F%E5%88%99">2.1 设计原则</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#2-2%20%E4%BA%A7%E5%93%81%E6%9E%B6%E6%9E%84">2.2 产品架构</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-%20%E5%8A%9F%E8%83%BD%E5%8F%8A%E5%AE%9E%E7%8E%B0">3. 功能及实现</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-1%20%E7%BD%91%E7%BB%9C">3.1 网络</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-1-1%20%E5%AE%B9%E5%99%A8%E7%BD%91%E7%BB%9C">3.1.1 容器网络</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-1-1-1%20%E9%97%AE%E9%A2%98">3.1.1.1 问题</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-1-1-2%20%E8%A7%A3%E5%86%B3%E6%96%B9%E6%A1%88">3.1.1.2 解决方案</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-1-2%20%E5%9B%BA%E5%AE%9AIP%E9%97%AE%E9%A2%98">3.1.2 固定IP问题</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-1-2-1%20%E9%97%AE%E9%A2%98">3.1.2.1 问题</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-1-2-2%20%E8%A7%A3%E5%86%B3%E6%96%B9%E6%A1%88">3.1.2.2 解决方案</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-1-2-3%20%E5%85%B7%E4%BD%93%E5%AE%9E%E7%8E%B0%E4%BC%A0%E9%80%81%E9%97%A8">3.1.2.3 具体实现传送门</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-1-3%20%E5%85%AC%E5%8F%B8%E5%86%85%E7%BD%91%E7%8E%AF%E5%A2%83">3.1.3 公司内网环境</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-2%20%E4%B8%9A%E5%8A%A1%E6%9E%B6%E6%9E%84%E7%AE%A1%E7%90%86">3.2 业务架构管理</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-2-1%20%E9%97%AE%E9%A2%98">3.2.1 问题</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-2-2%20%E8%A7%A3%E5%86%B3%E6%96%B9%E6%A1%88">3.2.2 解决方案</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-2-2-1%20CMDB%E7%BB%91%E5%AE%9A">3.2.2.1 CMDB绑定</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-2-2-2%20%E4%B8%9A%E5%8A%A1%E7%AE%A1%E7%90%86">3.2.2.2 业务管理</a></li></ul></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-3%20%E8%B7%AF%E7%94%B1%E4%B8%8E%E6%9C%8D%E5%8A%A1%E5%8F%91%E7%8E%B0">3.3 路由与服务发现</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-3-1%20%E9%97%AE%E9%A2%98">3.3.1 问题</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-3-2%20L5-CL5-CMLB%E7%B1%BB%E5%9E%8BService">3.3.2 L5/CL5/CMLB类型Service</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-3-3%20CLB%E5%9B%9B%E5%B1%82%E5%86%85%E7%BD%91-%E5%A4%96%E7%BD%91%E4%BB%A3%E7%90%86">3.3.3 CLB四层内网/外网代理</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-4%20%E6%89%A9%E7%BC%A9%E5%AE%B9%E9%89%B4%E6%9D%83">3.4 扩缩容鉴权</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-4-1%20%E9%97%AE%E9%A2%98">3.4.1 问题</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-4-2%20%20InitContainer%E9%89%B4%E6%9D%83">3.4.2  InitContainer鉴权</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-5%20StatefulSetPlus">3.5 StatefulSetPlus</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-5-1%20%E9%97%AE%E9%A2%98">3.5.1 问题</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-5-2%20%E6%96%B9%E6%A1%88%E4%B8%8E%E8%A7%A3%E5%86%B3">3.5.2 方案与解决</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-5-3%20%E5%85%B7%E4%BD%93%E5%AE%9E%E7%8E%B0%E5%8F%8A%E5%BC%80%E6%BA%90%E5%9C%B0%E5%9D%80">3.5.3 具体实现及开源地址</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-6%20%E9%95%9C%E5%83%8F%E4%BB%93%E5%BA%93">3.6 镜像仓库</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-6-1%20%E9%97%AE%E9%A2%98">3.6.1 问题</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-6-2%20%E5%85%B1%E5%90%8C%E5%88%9B%E5%BB%BACSIGHUB%E4%BB%93%E5%BA%93">3.6.2 共同创建CSIGHUB仓库</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-6-2%20%E5%85%AC%E5%85%B1%E9%95%9C%E5%83%8F">3.6.2 公共镜像</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-7%20%E6%97%A5%E5%BF%97%E6%9F%A5%E7%9C%8B">3.7 日志查看</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-7-1%20%E9%97%AE%E9%A2%98">3.7.1 问题</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-7-2%20%E6%8F%90%E4%BE%9BUTA%E8%BF%9C%E7%A8%8B%E6%97%A5%E5%BF%97">3.7.2 提供UTA远程日志</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#%E5%85%B7%E4%BD%93%E5%AE%9E%E7%8E%B0%E5%8F%8A%E5%BA%94%E7%94%A8%E6%96%87%E6%A1%A3">具体实现及应用文档</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-7-3%20%E6%A0%87%E5%87%86%E8%BE%93%E5%87%BA%E6%9F%A5%E7%9C%8B">3.7.3 标准输出查看</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-8%20%E7%9B%91%E6%8E%A7-%E5%91%8A%E8%AD%A6">3.8 监控/告警</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-8-1%20%E9%97%AE%E9%A2%98">3.8.1 问题</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-8-2%20%E5%9F%BA%E7%A1%80%E6%8C%87%E6%A0%87%E7%9B%91%E6%8E%A7-%E5%91%8A%E8%AD%A6">3.8.2 基础指标监控/告警</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-8-3%20%E4%BA%8B%E4%BB%B6%E5%91%8A%E8%AD%A6">3.8.3 事件告警</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-8-3%20%E5%85%B7%E4%BD%93%E5%AE%9E%E7%8E%B0%E5%8F%8A%E5%BA%94%E7%94%A8%E6%96%87%E6%A1%A3">3.8.3 具体实现及应用文档</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-9%20%E8%BF%9C%E7%A8%8B%E7%99%BB%E5%BD%95">3.9 远程登录</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-9-1%20SSH%E7%99%BB%E5%BD%95">3.9.1 SSH登录</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-9-2%20WebConsole">3.9.2 WebConsole</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-10%20CI-CD">3.10 CI/CD</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-10-1%20OrangeCI%E6%8F%92%E4%BB%B6">3.10.1 OrangeCI插件</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-10-2%20QCI%E6%8F%92%E4%BB%B6">3.10.2 QCI插件</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#3-10-3%20%E8%93%9D%E7%9B%BE%E6%8F%92%E4%BB%B6">3.10.3 蓝盾插件</a></li></ul></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#4%20%E4%B8%9A%E5%8A%A1%E6%8E%A5%E5%85%A5%E6%A1%88%E4%BE%8B">4 业务接入案例</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#5%20%E9%97%AE%E9%A2%98%E5%8F%8A%E5%B1%95%E6%9C%9B">5 问题及展望</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#6%20%E5%BC%80%E6%BA%90%E5%8D%8F%E5%90%8C">6 开源协同</a><ul><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#6-1%20STKE%E5%BC%80%E6%BA%90%E9%A1%B9%E7%9B%AE">6.1 STKE开源项目</a></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#6-2%20%E5%85%AC%E5%8F%B8%E5%BC%80%E6%BA%90%E9%A1%B9%E7%9B%AE">6.2 公司开源项目</a></li></ul></li><li class="tocitem"><a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#7%20%E5%8F%82%E8%80%83%E6%96%87%E7%8C%AE">7 参考文献</a></li></ul></nav>

<h2 id="协同共建">协同共建</h2>

<p><strong>Kubernetes开源协同社区（简称k8s oteam）已于9月发布正式版<a href="http://km.oa.com/articles/show/426050?ts=1568794365" target="_blank"> tk8s-v1.1</a>。 欢迎给k8s Oteam反馈问题和提出建议：</strong><br>
<a href="https://techmap.oa.com/oteam/8486" target="_blank">技术图谱 Kubernetes Oteam主页</a></p>

<p><strong>同时也欢迎给TKE/STKE反馈问题和提出建议</strong></p>

<p>平台页面右上角点击加入STKE社区</p>

<ul>
<li>
<p><a href="http://kubernetes.oa.com/" target="_blank">STKE平台地址</a></p>
</li>
<li>
<p><a href="http://wiki.k8s.oa.com/" target="_blank">STKE使用文档</a></p>
</li>
<li>
<p><a href="https://git.code.oa.com/STKE/web/issues" target="_blank">ISSUE反馈</a></p>
</li>
</ul>

<p>##1 背景</p>

<p>作者所在团队，一直从事容器等云原生技术的研究与落地。随着容器技术、kubernetes的迅速发展，kubernetes成为了云原生中重要的组成部分。随着kubernetes在社区的成熟，逐渐成为容器调度的霸主，团队在如何将Kubernetes在内部落地做了很多尝试。</p>

<p>自9.30之后，也成为了公司的重要任务之一。然而，上云如果仅仅是从IDC机房搬迁到机房，而将可能已经"过时"的技术实现从一个机房迁移到另一个机房，便失去了意义。</p>

<p>所以我们希望能够完全利用云上的技术，为业务同学提供一个云原生的平台，为开发同学提供另一个选择，让希望利用云原生技术的同学方便落地自己的业务。同时，也向老的业务兼容，协助老的业务在尽量少的改动下，向新的技术演进。</p>

<h3 id="1-1 什么是云原生">1.1 什么是云原生</h3>

<p>云原生应用基金会(CNCF)对云原生做了以下定义：</p>

<p>Cloud native technologies empower organizations to build and run scalable applications in modern, dynamic environments such as public, private, and hybrid clouds. Containers, service meshes, microservices, immutable infrastructure, and declarative APIs exemplify this approach.</p>

<p>These techniques enable loosely coupled systems that are resilient, manageable, and observable. Combined with robust automation, they allow engineers to make high-impact changes frequently and predictably with minimal toil.</p>

<p>云原生技术有利于各组织在公有云、私有云和混合云等新型动态环境中，构建和运行可弹性扩展的应用。云原生的代表技术包括容器、服务网格、微服务、不可变基础设施和声明式API。</p>

<p>这些技术能够构建容错性好、易于管理和便于观察的松耦合系统。结合可靠的自动化手段，云原生技术使工程师能够轻松地对系统作出频繁和可预测的重大变更。</p>

<p>云原生应用程序开发通常包括DevOps，敏捷方法，微服务，云平台，Kubernetes和Docker等，以及持续交付，简而言之，每种新的和现代的应用程序部署方法。其目的就是利用云的便利，更高效稳定的开发应用。</p>

<h3 id="1-2 为什么云原生">1.2 为什么云原生</h3>

<p>Splunk的首席技术咨询Andi Mann说过，客户犯下的一个重大错误就是试图将旧的本地部署应用程序直接并迁移到云端。 “试图利用现有的应用程序，特别是单一的遗留应用程序 ，并将它们转移到云基础架构上将无法利用必要的云原生功能。”</p>

<p>相反，你应该以新的方式开展新事物，或者将新的云原生应用程序放入新的云基础架构中，或者通过拆分现有的单块应用来从头开始使用云原生原则重构它们。</p>

<p>云原生根本目的就是利用云上的便利，以及各种容器技术，更高效稳定的开发应用。</p>

<h3 id="1-3 为什么Docker">1.3 为什么Docker</h3>

<p>在云原生应用开发中，Docker因为其自身优势，在云原生中有着重要地位，同时，在微服务中，有着广泛的应用。</p>

<ul>
<li>更高效的利用系统资源</li>
<li>资源隔离</li>
<li>一致的运行环境</li>
<li>持续交付和部署</li>
<li>更轻松的迁移</li>
<li>更轻松的维护和扩展</li>
</ul>

<p>以公司的服务为例，存在着不同的tlinux版本，不同服务依赖不同的应用版本，.so等，有些业务可能还需要设置环境变量。</p>

<p>同时，公司内的制品库复杂，交付件各种各样，各种安装包，rpm，织云PKG，CC配置文件，ARS包等，很多程序在安装时，还要执行响应的前置脚本或者后置脚本执行各种配置。</p>

<p>当使用Docker时，用户可以很轻松的通过编写Dockerfile构建出一个可以直接提供服务交付件(应用+依赖环境)，只要启动容器镜像，即可提供对外服务。</p>

<p>使用镜像/Dockerfile交付，更加清晰明确了运维与开发的界限，研发构建和分发运维的过程大大简化了。当然，两者的边界也发生了变化：</p>

<ul>
<li>
<p>之前研发只需要关注功能，性能，稳定性，可扩展性，可测试性等等。引入了镜像之后，因为要自己去写 Dockerfile，要了解这个技术依赖和运行的环境倒底是什么，应用才能跑起来，原来这些都是相应运维人员负责的。研发人员自己梳理维护起来后，就会知道这些依赖是否合理，是否可以优化等等。</p>
</li>
<li>
<p>研发还需要额外关注应用的可运维性和运维成本，关注自己的应用是有状态的还是无状态的，有状态的运维成本就比较高。这个职责的转换，可以更好的让研发具备全栈的能力，思考问题涵盖运维领域后，对如何设计更好的系统会带来更深刻的理解。</p>
</li>
</ul>

<h3 id="1-4 为什么Kubernetes">1.4 为什么Kubernetes</h3>

<p>最基础的，Kubernetes 可以在物理或虚拟机集群上调度和运行应用程序容器。然而，Kubernetes 还允许开发人员从物理和虚拟机’脱离’，从以<strong>主机为中心</strong>的基础架构转移到以<strong>容器为中心</strong>的基础架构，这样可以提供容器固有的全部优点和益处。Kubernetes 提供了基础设施来构建一个真正以<strong>容器为中心</strong>的开发环境。</p>

<p>Kubernetes 满足了生产中运行应用程序的许多常见的需求，例如：</p>

<ul>
<li><a href="https://kubernetes.io/docs/user-guide/pods/" target="_blank">Pod</a> 提供复合应用并保留一个应用一个容器的容器模型</li>
<li><a href="https://kubernetes.io/docs/user-guide/volumes/" target="_blank">挂载外部存储</a></li>
<li><a href="https://kubernetes.io/docs/user-guide/secrets/" target="_blank">Secret管理</a></li>
<li><a href="https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-probes/" target="_blank">应用健康检查</a></li>
<li><a href="https://kubernetes.io/docs/user-guide/replication-controller/" target="_blank">副本应用实例</a></li>
<li><a href="https://kubernetes.io/docs/user-guide/horizontal-pod-autoscaling/" target="_blank">横向自动扩缩容</a></li>
<li><a href="https://kubernetes.io/docs/user-guide/connecting-applications/" target="_blank">服务发现</a></li>
<li><a href="https://kubernetes.io/docs/user-guide/services/" target="_blank">负载均衡</a></li>
<li><a href="https://kubernetes.io/docs/user-guide/update-demo/" target="_blank">滚动更新</a></li>
<li><a href="https://kubernetes.io/docs/user-guide/monitoring/" target="_blank">资源监测</a></li>
<li><a href="https://kubernetes.io/docs/user-guide/logging/overview/" target="_blank">日志采集和存储</a></li>
<li><a href="https://kubernetes.io/docs/user-guide/introspection-and-debugging/" target="_blank">支持自检和调试</a></li>
<li><a href="https://kubernetes.io/docs/admin/authorization/" target="_blank">认证和鉴权</a></li>
</ul>

<p>这提供了平台即服务 (PAAS) 的简单性以及基础架构即服务 (IAAS) 的灵活性，并促进跨基础设施供应商的可移植性。</p>

<p>Kubernetes是天然的微服务架构，随着功能的逐步完善，以及社区的快速发展，在容器管理、编排、调度等方面逐逐步甩开竞争对手Swarm、Mesos，处于领先地位。</p>

<h3 id="1-5 现状">1.5 现状</h3>

<p style="">Docker自2013年诞生已经有6年的时间，已经成为一个相对稳定成熟的产品，也越来越被开发者接受。<br>
<img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(2)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>虽然，在构建docker镜像的时候，到底以运行单个进程和多个进程，存在着争议，但都是以简洁，轻量级为目标构建。</p>

<p>在业界的应用中，也有一些公司将ssh服务构建到镜像中，更多业界开源镜像Nginx等，都是以单一进程启动，更加的Native。</p>

<p>目前，阿里，京东等企业已经做到了100%容器化，并且可以使用Kubernetes做调度，拼多多，知乎，饿了么等也将非存储类的服务容器化，网易游戏这样的场景，也做了容器化改造，并使用K8S管理。(如有不准确请联系作者修改)</p>

<p>反观内部的容器化发展，大部分还停留在虚拟机为主的时代，内部服务容器化的进展相对比较慢，容器化占比较低。内部虽然有一些如Sumeru，Gaia，TenC等优秀的容器平台， 但是相对于公司整体服务体量，也低于业界水平。</p>

<h3 id="1-6 挑战">1.6 挑战</h3>

<p>在内部使用Docker+Kubernetes，面临着许多挑战，比如你可能都无法正常的在机器上安装Docker(现在应该已经可以了)，即使安装了Docker，可能无法正常拉取依赖，去构建Dockerfile。等你发现一切OK之后，可能还需要一个镜像仓库……</p>

<p>另外在内部部署一个Kubernetes集群也是一个非常有挑战的事情，可能你在自己环境花半天就可以搞定的事情，在内部可能搞到绝望。当你一切都构建好之后，还可能发现因为操作系统(内核)版本等问题，导致一些功能无法正常使用。除此之外，业务自己维护一个K8S集群也是一个很有挑战的事情。</p>

<p>但是随着的推进，创建和使用集群相对容易了很多，可以直接从云上购买TKE(STKE,TenC,BCS等都是从TKE购买，根据BG特点做一些差异配置初始化)，这时最简单的集群就可以使用了。但是如果集群用于生产可能还要解决更多的问题……</p>

<p>其实，K8S使用过程中，涉及到的挑战有很多：</p>

<ul>
<li>容器网络</li>
<li>路由与服务发现</li>
<li>监控</li>
<li>告警</li>
<li>多集群管理</li>
<li>镜像仓库</li>
<li>依赖IP/模块鉴权的服务(权限同步)</li>
<li>远程存储</li>
<li>远程日志</li>
<li>远程登录</li>
<li>CI/CD</li>
<li>安全、审计</li>
</ul>

<p>后文会介绍平台在设计开发中如何逐步解决生产环境遇到的问题。</p>

<h2 id="2 平台介绍">2 平台介绍</h2>

<p>STKE 是公司使用的容器服务基础平台，以兼容云原生、适配自研业务、开源协同为最大特点，主要在TKE基础上提供以下能力：</p>

<ul>
<li>对接了L5/CL5/CMLB/CLB进行服务路由的自动化管理；</li>
<li>支持容器固定IP，容器漂移和销毁重建都能保持IP不变；</li>
<li>支持织云PKG转镜像发布，PKG自动转换成docker镜像进行云原生发布；</li>
<li>支持对接权限系统(oidb, cdb, vas_key权限等)；</li>
<li>支持多批次灰度发布；</li>
<li>支持分批容器原地升级，升级L5 agent等基础组件agent时不影响业务容器；</li>
<li>提供容器日志对接ULS平台;</li>
<li>提供容器监控和事件告警能力；</li>
<li>容器信息自动注册到cmdb4,公司cmdb；</li>
<li>支持为容器提供CBS/NFS存储；</li>
<li>支持铁将军/webconsole登入容器；</li>
<li>对接了蓝盾/OCI/QCI，实现CI、CD闭环；</li>
<li>开放原生API。</li>
</ul>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(3)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h3 id="2-1 设计原则">2.1 设计原则</h3>

<p>在产品开发设计过程中，我们遵循了一下原则：</p>

<ul>
<li>
<p>以云原生理念为基础</p>
<p>除了必要的管理维度限制(资源，模块)，将所有原生的操作都暴露给用户，用户可以根据自己需求编排自己的服务。</p>
</li>
<li>
<p>直接对接云上资源</p>
<p>平台希望业务使用的服务，逐渐迁移到云上的服务，所有PAAS资源对接资源，推动用户直接使用云上服务如云上数据库，中间件，负载均衡等而非内部自研服务。一方面云上服务有长期稳定的运营开发团队，另一方面，内部服务可以及时反馈云产品使用的问题，推动产品改进。</p>
</li>
<li>
<p>对内部组件支持</p>
<p>内部存在大量的服务，依赖诸如L5/CL5/CLMB等服务。首先业务很难短时间摆脱这些依赖，其次，像L5/CL5/CMLB这样的服务，能更好的解决应用在跨级群，CVM，实体机间的访问和调度。</p>
</li>
<li>
<p>增强对旧业务的支持</p>
<p>老的业务想要使用Kubernetes，面临很多改造成本，比如原生K8S对于分批灰度发布的支持就不是很完善，我们基于Statefulset做了StatefulsetPlus，支持了分批灰度发布，支持了原地重启等功能。对于依赖的公共组件，也做了分离，将他们以sidecar的形式与业务进程运行在同一个POD之中……</p>
</li>
<li>
<p>简化部署流程</p>
<p>部署/编排一个应用需要的配置项繁多，既要兼顾配置的间接性，又要提供足够的灵活性，不能严格正常的功能。</p>
</li>
<li>
<p>开源协同</p>
<p>Kubernetes的所有依赖，都是基于公司开源协同版本开发，并且不断基于该版本进行开发新功能，以及返回Bug。同时，在开发相关K8s组件时，考虑其通用性，并且将代码加入开源协同项目中。</p>
</li>
</ul>

<h3 id="2-2 产品架构">2.2 产品架构</h3>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(4)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(5)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<ul>
<li>STKE所有资源全部来自云上，拥有专有VPC，平台通过TKE生产出集群后，根据生产环境实际情况，对集群节点、Kubernetes参数等重新做了初始化，优化了部分配置。</li>
<li>除了底层依赖的部分TKE插件之外，还在集群中部署了很多拓展插件，例如CMDB-Controller去同步POD-IP到CMDB，Event-Controller采集k8s事件日志，Init-Action-Controller去同步权限，L5-Controller用来支持内部的L5/CL5/CMLB等。</li>
<li>中间层使用了开源的TKE-Apiserser做多集群转发Server，部署了监控上报组件，告警组件，业务管理组件等。</li>
<li>外围构建了镜像仓库，打通了argus监控上报，远程日志UTA，与安全部门打通了webconsole组件，铁将军远程登录等。</li>
</ul>

<h2 id="3- 功能及实现">3. 功能及实现</h2>

<p>本节对使用Kubernetes上云最常遇到的问题，探讨STKE的解决方式，提供解决思路，并且希望得到更好的建议，使平台更加完善。由于篇幅有限，本文针只对主要功能及实现做了简介，如果有兴趣，可以进入相应具体实现的链接查看内容，部分开源项目也附有源码地址，欢迎吐槽。</p>

<h3 id="3-1 网络">3.1 网络</h3>

<p>先从大家最先关心的网络问题说起，内部在上云和使用Kubernetes的时候，首先遇到的就是网络问题，具体分为三个方面：</p>

<ul>
<li>容器网络</li>
<li>公司网络</li>
<li>固定IP问题</li>
</ul>

<h4 id="3-1-1 容器网络">3.1.1 容器网络</h4>

<p>实现容器网络通信的方案有很多，Kubernetes支持通过标准的CNI(Container Network Interface)接入开发者的网络插件，Kubernetes中的网络通信主要有以下几种情况：</p>

<ul>
<li>
<p>同Pod中间通信</p>
</li>
<li>
<p>Pod之间的通信（同一个Node和不同Node上）</p>
<p>同一个集群中，Pod之间可以通过Pod IP互相访问。</p>
</li>
<li>
<p>Pod与Service之间通信</p>
<p>对于Kubernetes来讲，为了保证服务的健壮性，通过健康检查，动态的销毁重建Pod来保证服务的可用性。换句话说，用户部署了一个工作负载(workload)，应当保证他有多个副本(Pods)，当其中有Pod无法工作时，通过销毁重建来恢复。</p>
<p>在Kubernetes之中，外部访问Workload不是直接通过访问某个Pod，而是通过Service的方式去访问服务，不管服务对应的Pods有多少，状态是怎么样，都会通过一个固定的ClusterIP:Port访问到后端处于ready状态的Pod，保证服务的可用性。</p>
</li>
<li>
<p>集群外与集群内服务的通</p>
<p>通常需要运营商提供LoadBalancer类型Service，或者通过Ingress进行访问。</p>
</li>
</ul>

<h5 id="3-1-1-1 问题">3.1.1.1 问题</h5>

<p>默认情况下Pod，Node，及Service都处于不同的网段，Pod和Service通常是一个虚拟网段(如172.0.0.1/16)，这些IP在集群外是无法访问的。因此在内部使用上带来了一定的困难。</p>

<ol>
<li>
<p>Pod IP如果是集群外不可访问IP(如172.0.0.1这种)，那么可能遇到的问题有</p>
<ul>
<li>原有的运维体系不兼容。</li>
<li>基础组件都可能无法正常使用和通信。</li>
<li>服务访问方式改变，原来通过IP调用的，都要改造成调用LoadBalancer Service或者NodePort Serivce+Ingress。</li>
<li>网络开销可能增大。</li>
</ul>
</li>
<li>
<p>在多集群，多机型（CVM，实体机，容器）容灾，负载均衡时，将变得十分困难。</p>
</li>
</ol>

<h5 id="3-1-1-2 解决方案">3.1.1.2 解决方案</h5>

<p>通过使用TKE的CNI插件，针对每一个 Pod，我们会给他分配一个**弹性网卡(EIP)**的辅助 IP，并通过设置主机路由和容器网络协议栈，以使达到：</p>

<ul>
<li>同主机的 Pod 可以互相通信</li>
<li>跨主机的 Pod 可以互相通信</li>
<li>Pod可与VPC其他IP互相通信</li>
<li>Pod 可以访问互联网</li>
<li>不经过 NAT 转换</li>
</ul>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(6)" alt="" style="position: relative; z-index: 2;" class="amplify"><br>
简单来说，每个Pod绑定了一个弹性网卡，弹性网卡的IP为VPC内的网段的IP，因此，既能实现跨主机间的通信，又可以与云VPC内其他服务的IP互相通信。</p>

<p>对于问题2，我们会在<a href="https://km.woa.com/group/31235/articles/show/395767?kmref=search&amp;from_page=1&amp;no=1#router">路由与服务发现</a>一节具体介绍。</p>

<h4 id="3-1-2 固定IP问题">3.1.2 固定IP问题</h4>

<h5 id="3-1-2-1 问题">3.1.2.1 问题</h5>

<p>由于刚刚提到的Kubernetes服务访问方式，通过Service是可以无须关心后端Pod实际IP的，但实际情况用户还是要基于IP去访问和管理，比如很多老的服务都是基于IP鉴权……</p>

<p>由于原生Kubernetes Pod的销毁重建，会导致Pod IP改变，在内部使用上还是有很多的不方便，因此，对于StatefulsetPlus，Statefulset，需要支持固定IP，即在容器销毁重建之后，不能改变IP，还可以让服务访问旧的Pod IP。</p>

<h5 id="3-1-2-2 解决方案">3.1.2.2 解决方案</h5>

<p>此时，就需要IPAMD支持这类情景：</p>

<p>当有 StatefulsetPlus/Statefulset 新建/更新/删除，IPAMD 会监听到该事件，为该 StatefulsetPlus/Statefulset 预留/解预留 IP。<br>
以下为 IPAMD 实现 StatefulsetPlus/Statefulset Pod 固定 IP 原理图：</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(7)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h5 id="3-1-2-3 具体实现传送门">3.1.2.3 具体实现传送门</h5>

<p>以上两个问题的相关文档，有兴趣的同学可以继续深入研究。</p>

<ul>
<li><a href="http://km.oa.com/group/31235/articles/show/395393" target="_blank">TKE 网络方案介绍 - VPC 全局路由</a></li>
<li><a href="http://km.oa.com/group/31235/articles/show/385219?kmref=discovery_page" target="_blank">POD固定IP实现原理</a></li>
<li><a href="https://git.code.oa.com/tke/eni-cni-static-ipamd" target="_blank">eni-cni-static-ipamd内部开源地址</a></li>
</ul>

<h4 id="3-1-3 公司内网环境">3.1.3 公司内网环境</h4>

<p>自研上云过程中，会有人担心公司各个网络区域之间的通讯问题，自研团队从去年开始，就与公司各基础团队打通云VPC与IDC的专线，目前已经实现IDC，云支撑与云VPC（自研上云的区域）的网络互通。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(8)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<ol>
<li>
<p>云VPC互通（跨城区）：经过 PVGW 2.0 然后进入到 云支撑大网 进行互通；</p>
</li>
<li>
<p>云VPC互通（同城区，包括同园区和跨园区）：不经过 PVGW2.0，通过 母机 的网络直接互通；</p>
</li>
<li>
<p>云VPC和自研互通（跨园区）：内部优先走云跨园区链路，到最近点有直通车互通就走直通车，没有直通车直接走SMAN绕行；</p>
</li>
<li>
<p>云VPC和自研互通（同园区）：通过直通车互通；</p>
</li>
<li>
<p>云VPC和自研互通（跨城区）：通过SMAN互通；</p>
</li>
</ol>

<p>通过以上改造各地网络延迟也有明显下降。网络延迟拓扑：</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(9)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<ul>
<li>
<p><a href="http://aim.isd.com/exp/delay" target="_blank">各地机房延时</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/35679/articles/show/380986?kmref=search&amp;from_page=1&amp;no=1" target="_blank"> - 网络互通介绍</a></p>
</li>
</ul>

<h3 id="3-2 业务架构管理">3.2 业务架构管理</h3>

<p>STKE平台也一直在探索如何适配基于Kubernetes的云原生应用的组织形式。对于小型企业或者小型服务，无需考虑太多组织架构，用户直接以集群管理员维度操作一个或者少量Kubernetes集群即可，用户成本不高。</p>

<p>比如Kubernetes的Dashboard，开源的Openshift，Rancher，阿里的ACK，公司公有云的TKE，IEG的BCS，都是以集群维度去管理的，这种方式一方面非常自由灵活，另一方面，在服务数量越来越多的情况下，管理，权限等问题就比较难以解决。</p>

<h4 id="3-2-1 问题">3.2.1 问题</h4>

<p>用户实际需求的场景中：</p>

<ul>
<li>服务有多地域多集群容灾要求，需要同时操作多个集群，需要做多集群的管理;</li>
<li>目前用户量及其服务数量上千个，每个需要对用户做权限隔离;</li>
<li>同一类型或功能的服务(微服务、服务编排等情况)可能需要统一管理 ;</li>
</ul>

<h4 id="3-2-2 解决方案">3.2.2 解决方案</h4>

<p>首先，因为业务场景不通，其实没有一个绝对合理的组织形式，每个服务都可能根据自己的实际状况组织不同的形式。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(10)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>STKE用户在进入后，首先需要创建一个业务，通过业务这个集合的概念，去管理下面的服务。</p>

<p>通常情况下，一个最简单的服务，应该由一个Workload(如，包含一个Mysql进程的镜像)和一个Service(外部访问的IP+端口)组成，如果是七层代理的访问，还需要Ingress，上图没有画出Ingres。</p>

<p>业务下面通过不同的Namepace去隔离用户的的环境，如测试环境，预发布，生产环境，为了避免命名空间冲突等问题，会由平台统一约束，用户可以将一套服务完整的部署在某个命名空间当中，测试，预发布，生产环境的网络环境完全一致，服务在上线前，可以快速的在测试或预发布环境中部署测试，通过后在生产环境中升级（如更新Workload镜像版本）。</p>

<p>在规划业务时，经常遇到一些关于业务维度的疑惑，多大/多少的服务可以组成一个业务？根据目前遇到的场景，大致分为两种：</p>

<ol>
<li>有些应用，由几个关联的服务组合而成，开发也是由一两个小组组成，这些服务部署之后，应用即可使用，这种就可以放到一个业务下面。例如Hadoop（datanode，namenode，zookeeper，resourcemanager, dashboard）。</li>
<li>另外有些应用，规模比较大，其实是有多个子应用组成，每个应用又由一些服务组成，子应用之间有独立的小组开发，可以独立部署测试，那么，这个子应用中的服务，变可以组成一个业务模块。例如Kuberntes中使用的prometheus监控就可以以一个业务形式部署。</li>
</ol>

<p>由于Kubernetes的设计理念，本身就符合微服务的架构，STKE在此基础强化业务维度管理，环境管理，多集群管理，使用更加方便。</p>

<p>同时，将相同相似服务部署在同一个Namespace当中，还可以对服务拓扑，调用关系，问题处理上更加方便。尤其是今后在服务环境治理时，比如STKE与文档、Service Mesh（Istio）实现测试环境治理时，这样的管理形式会比较简洁清晰。</p>

<p>下图是基于STKE + Serice Mesh在base命名空间的服务调用拓扑。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(11)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h5 id="3-2-2-1 CMDB绑定">3.2.2.1 CMDB绑定</h5>

<p>虽然原生应用中与CMDB没有业务跟公司的三级模块（对应原SNG CMDB4，现在PCG，CISG CMDB4的四级模块）绑定。用于</p>

<ul>
<li>公司合规要求，将生产的Pod IP落地CMDB</li>
<li>适配基于CMDB、IP鉴权/管理的服务</li>
<li>基础组件依赖(tnm2等)</li>
</ul>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(12)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(13)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>如上图所示：</p>

<ul>
<li>在当用户首次部署服务和服务扩容的时候，STKE会增加InitContainer去主动发起CMDB注册;</li>
<li>在运行时如果发现业务有Pod变更，CMDB-Controller也会动态的发现，并与CMDB对账；</li>
</ul>

<p>开源协同地址</p>

<ul>
<li><a href="http://git.code.oa.com/k8s/cmdb4-controller.git" target="_blank">CMDB4-Controller</a></li>
<li><a href="http://git.code.oa.com/k8s/cmdb2.git" target="_blank">CMDB2-Controller</a></li>
</ul>

<h5 id="3-2-2-2 业务管理">3.2.2.2 业务管理</h5>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(14)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>为了实现以业务级别的管理，STKE在开源TKE的基础上进行了二次开发。</p>

<p>由于需要基于业务维度的多集群控制，所以使用了NamespaceSet的概念，通过NamespaceSet Controller去管理NamespaceSet，简称NsSet，它是一个在集群之上的资源，每个NsSet去监听每个集群中的Ns，用于创建，删除，变更对应集群的Ns。</p>

<p>平台通过Project Manager去管理业务，业务与NsSet相关联，以此达到了基于业务的多集群多环境管理的效果。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(15)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
</div><center>业务列表</center>
![](http://km.oa.com/files/photos/pictures/201909/1568689507_77_w2114_h1100.png)
</div><center>服务多集群部署</center>
![](http://km.oa.com/files/photos/pictures/201909/1568689524_2_w1530_h466.png)
</div><center>服务展示</center>
开源地址

<ul>
<li><a href="https://git.code.oa.com/tke/tke" target="_blank">tke</a></li>
</ul>

<h3 id="3-3 路由与服务发现">3.3 路由与服务发现</h3>

<h4 id="3-3-1 问题">3.3.1 问题</h4>

<p>前文中有介绍，Kubernetes中的服务发现，通过Serivce和Ingress实现。</p>

<p>Service是对一组提供相同功能的Pods的抽象，并为它们提供一个统一的入口。借助Service，应用可以方便的实现服务发现与负载均衡，并实现应用的零宕机升级。</p>

<p>Service有三种类型：</p>

<ul>
<li>
<p>ClusterIP：默认类型，自动分配一个仅cluster内部可以访问的虚拟IP</p>
</li>
<li>
<p>NodePort：在ClusterIP基础上为Service在每台机器上绑定一个端口，这样就可以通过<code>&lt;NodeIP&gt;:NodePort</code>来访问该服务</p>
</li>
<li>
<p>LoadBalancer：在NodePort的基础上，借助cloud provider创建一个外部的负载均衡器，并将请求转发到<code>&lt;NodeIP&gt;:NodePort</code></p>
</li>
</ul>

<p>Service虽然解决了服务发现和负载均衡的问题，还需要Ingress，主要用来将服务暴露到cluster外面。</p>

<p>就带了了部署服务的复杂性：</p>

<ul>
<li>
<p>如果使用Service ClusterIP，集群外无法访问，</p>
</li>
<li>
<p>使用Service NodePort类型，还需要知道NodeIP。</p>
</li>
<li>
<p>增加了路由表的复杂性，以及延迟。</p>
</li>
<li>
<p>配置Service + ingress比较复杂。</p>
</li>
</ul>

<p>除此之外，公司内大量服务是使用L5/Cl5/CMLB做服务发现，业务也不可能全部替换为Kubernetes的形式。</p>

<p>因此，平台主要通过两种方式为用户提供服务的对外方法。</p>

<ol>
<li>L5/Cl5/CMLB 类型Service</li>
<li>CLB类型Service</li>
</ol>

<h4 id="3-3-2 L5-CL5-CMLB类型Service">3.3.2 L5/CL5/CMLB类型Service</h4>

<p>STKE开发了L5-Controller，用户在部署服务时，同时可以选择L5/CL5/CMLB类型的Service与workload进行绑定，就可以实现相应的访问，主调方直接根据ID即可获取到对应Pod IP:Port，提供访问。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(16)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>
</div><center>选择L5</center>
![](http://km.oa.com/files/photos/pictures/201909/1568689567_15_w846_h400.png)
<center>L5-Service yaml</center>
![](http://km.oa.com/files/photos/pictures/201909/1568689582_90_w1029_h657.png)

<p>简单的说，l5-controller订阅etcd的servcie/endpoints/configmap事件，当有事件产生时，根据变更情况，以及配置信息（权重，就近访问等信息）与相应路由系统实时同步，实现对应注册Pod IP信息、配置同步。</p>

<p>通过这种方式，可以实现同种服务部署在实体机，虚拟机，多集群之间，通过L5的配置，实现服务发现和负载均衡。</p>

<p>具体实现传送门</p>

<ul>
<li><a href="http://km.oa.com/group/31235/articles/show/393312" target="_blank">L5-Controller实现原理详细介绍</a></li>
<li><a href="https://git.code.oa.com/k8s/l5-controller" target="_blank">L5-Controoler开源代码地址</a></li>
</ul>

<h4 id="3-3-3 CLB四层内网-外网代理">3.3.3 CLB四层内网/外网代理</h4>

<p>另外一种可以实现集群内/外访问的方式，就是是用CLB，即上文提到的LoadBalancer类型的Service，CLB是的负载均衡。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(17)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(18)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>他的实现也的与L5类似，也是通过监听绑定Service的Pod变化，将后端实际Pod IP动态的与CLB后端的RS信息同步，达到通过访问一个VIP，即可路由到后端Pod的效果。同时，STKE的公网的CLB还支持各类运营商网络，以满足业务接入需求。</p>

<p>具体实现传送门</p>

<ul>
<li><a href="http://km.oa.com/articles/show/425444" target="_blank">自研上云-STKE接入层路由Ingress/Service操作指引</a></li>
</ul>

<h3 id="3-4 扩缩容鉴权">3.4 扩缩容鉴权</h3>

<h4 id="3-4-1 问题">3.4.1 问题</h4>

<p>由于历史原因，很多公司内部系统，权限控制都是基于CMDB模块或者来源IP鉴权（数据库，OIDB等），这种方式是非常阻碍云原生的实践的。</p>

<ol>
<li>由于Pod的调度（部署，扩缩绒，迁移），本身IP就是不固定的。</li>
<li>Pod的IP经常变化。</li>
<li>CMDB同步不是实时的。</li>
<li>内部系统同步IP或CMDB信息不是实时的。</li>
</ol>

<p>就会造成隔离系统权限同步不及时，即使服务已经启动，但还是会造成调用失败。</p>

<p>在此，还是希望系统如果需要认证，还是希望通过类似签名等方式完成。如AWS<a href="https://docs.aws.amazon.com/AWSECommerceService/latest/DG/HMACSignatures.html" target="_blank">HMAC</a>。</p>

<h4 id="3-4-2  InitContainer鉴权">3.4.2  InitContainer鉴权</h4>

<p>STKE对于这种情况，使用了Kubernetes的InitContainer机制，预先在容器启动之前，先拿到Pod的IP，去各类平台进行鉴权，保证权限已经下发之后，再启动之后用户的Container。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(19)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(20)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(21)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>同时，例如OIDB，VAS_KEY这里鉴权，平台也跟响应的开发同学联合优化，使得鉴权同步时间从十几分钟缩短到5分钟以内。</p>

<h3 id="3-5 StatefulSetPlus">3.5 StatefulSetPlus</h3>

<h4 id="3-5-1 问题">3.5.1 问题</h4>

<p>在使用原生Kubernetes的时候，关于常用工作负载类型(deployment，statefulset)，总有或多或少的问题，简单列举几个：</p>

<ol>
<li>在升级上，deployment，statefulset都不能很好的控制升级进度，指定Pod升级，分批灰度升级。</li>
<li>Pod IP在扩缩容，调度时，不能够固定IP。</li>
<li>无法支持原地升级等场景。</li>
<li>升级过程中发生HPA（水平扩缩容），导致Pod重建，会默认变为新版本，在有些服务中是无法接受的。</li>
</ol>

<h4 id="3-5-2 方案与解决">3.5.2 方案与解决</h4>

<p>以上遇到的问题，不管是在阿里还是其他公司，也都会针对上述情况，开发自己的CRD支持自研业务。</p>

<p>STKE平台自研了StatefulSetPlus来实现增强功能。在保留StatefulSet的优秀能力下，支持了以下特性：</p>

<ul>
<li>
<p>支持StatefulSetPlus Pod固定IP，扩缩容、容器漂移后容器IP都能保持不变，使用IP地址进行安全配置的场景，非常友好。</p>
</li>
<li>
<p>支持弹性伸缩。</p>
</li>
<li>
<p>支持应用的多批次灰度更新，更好的兼容了传统应用的发布：</p>
</li>
</ul>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(22)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<ul>
<li>用户可选择应用分几批次进行更新。</li>
<li>用户可配置每个批次的实例列表，比如用户可根据应用服务地区，只暂时升级对应地区的实例。</li>
<li>每个批次指定的实例是并发更新的，升级效率高。</li>
<li>发布过程中，支持一键回滚到任何一个版本，简单高效。</li>
<li>升级更安全：每个批次升级完成后，除了要求应用的探针成功外，还额外要求用户确认，再触发升级下一批实例（deplyoment不会自动停止，升级直至结束，statefuset至于遇到错误才会中断）。</li>
<li>升级更省心：对于开发质量高的应用，已经经过了开发—&gt;测试—&gt;预发布的流程验证，StatefulSetPlus还支持每个批次升级成功后，暂停一定时间（可配置），然后自动触发升级下一批实例，整个流程完全自动。（即将发布）</li>
<li>支持手动扩缩容，也支持基于应用基础指标(Cpu, Mem, Network I/O)的弹性伸缩。基于Argus应用自定义监控指标的弹性伸缩也即将发布。</li>
</ul>

<p>通过上述方式，解决了大部分内部升级的问题。同时，STKE也在开发自动分批升级、回滚，以及更多升级策略，来保证满足多种升级需求。</p>

<h4 id="3-5-3 具体实现及开源地址">3.5.3 具体实现及开源地址</h4>

<p><a href="http://km.oa.com/group/25898/articles/show/367845?kmref=search&amp;from_page=1&amp;no=1" target="_blank">更适合的Kubernetes Workload - StatefulSetPlus</a></p>

<p><a href="https://git.code.oa.com/k8s/statefulsetplus-operator" target="_blank">statefulsetplus-operator</a></p>

<h3 id="3-6 镜像仓库">3.6 镜像仓库</h3>

<p>镜像仓库是应用Docker/Kubernetes的关键组件。其服务质量也影响到后续的整个流程。</p>

<h4 id="3-6-1 问题">3.6.1 问题</h4>

<p>在平台建设过程中，我们遇到了不少问题：</p>

<ol>
<li>公司没有一个统一的镜像仓库，都是各个容器相关的团队独立维护，维护成本高。</li>
<li>内部仓库大部分是http访问，都需要用户手动配置INSECURE_REGISTRY。</li>
<li>内部使用Https访问，又会遭遇没有公网证书的尴尬，需要用户手动下载ca证书配置。</li>
<li>多台服务器访问镜像仓库时，下载速度非常慢，即使使用P2P，效果也不太理想。(内网大部分机型，网卡带宽只有1G)。</li>
<li>仓库无法基于项目组织管理。</li>
</ol>

<h4 id="3-6-2 共同创建CSIGHUB仓库">3.6.2 共同创建CSIGHUB仓库</h4>

<p>基于上述问题，在TencentHub团队帮助下，建立了csighub.oa.com镜像仓库。一方面可以将内部使用问题反馈给开发团队，另一方面也得到了运营上的支持，遇到问题能够更加高效的解决。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(23)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<ol>
<li>为了解决Https及证书问题，我们签发了公网证书，为了能够保证访问，浏览器端使用csighub.oa.com登录，<a href="http://xn--csighub-oc6k521zscmtjk892blx1a.tencentyun.com/" target="_blank">终端访问使用csighub.tencentyun.com</a>。</li>
<li>用户登录直接可以使用RTX+密码的方式进行登录。</li>
<li>镜像可以通过组织管理，授予不同角色。</li>
<li>底层使用了COS存储，不仅镜像下载速度快，并且几乎没有网络瓶颈，在上千节点同时拉取镜像时，不会减缓下载速度。</li>
<li>为了保证公司各种网络下可以使用镜像仓库，在非云环境下，也配置了响应的代理，并与企业IT的同学积极协调，尽量减少devnet/office wifi的访问成本(比如不在需要手动开通443端口策略等)。</li>
</ol>

<p><a href="http://wiki.k8s.oa.com/quickstart/csighub.html" target="_blank">CSIGHUB仓库说明</a></p>

<h4 id="3-6-2 公共镜像">3.6.2 公共镜像</h4>

<p>于此同时，STKE也为大家提供了公司tlinux的基础镜像，即tlinux的镜像版本</p>

<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash">csighub.tencentyun.com/admin/tlinux2.2-bridge-tcloud-underlay:latest
</code></pre>

<p>对于通用的公共组件，STKE平台还提供了l5_protocol_32os，monitor_agent，tjg_agent等镜像，可以作为sidecar与主镜像共同编排在同一个Pod中提供服务。</p>

<h3 id="3-7 日志查看">3.7 日志查看</h3>

<h4 id="3-7-1 问题">3.7.1 问题</h4>

<p>一般情况下，有些日志会通过响应系统上报，有些会保留在本地，但是在使用容器时，就会遇到问题。容器在销毁重建之后，对应的数据就会消失，这对于业务排查问题就带了不便。</p>

<h4 id="3-7-2 提供UTA远程日志">3.7.2 提供UTA远程日志</h4>

<p>用户在配置文件的时候，可以选择对应的容器日志采集目录+文件</p>

<ol>
<li>首先STKE默认为用户在UTA上创建日志主题；</li>
<li>创建日志文件共享目录，使日志组件可以读取用户日志；</li>
<li>挂载Filebeat SideCar为用户上报日志；</li>
</ol>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(24)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>用户可以通过平台连接，直接跳转到<a href="http://uta.oa.com/" target="_blank">UTA</a>查看自己的日志流水</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(25)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(26)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h5 id="具体实现及应用文档">具体实现及应用文档</h5>

<p><a href="http://km.oa.com/group/39547/articles/show/390797" target="_blank">STKE 业务日志上报方案介绍</a></p>

<h4 id="3-7-3 标准输出查看">3.7.3 标准输出查看</h4>

<p>对于常规日志，平台还提供了原生支持的标准输出查看，将常级别日志打到标准输出，平台会提供查看功能。</p>

<p></p>

<h3 id="3-8 监控-告警">3.8 监控/告警</h3>

<h4 id="3-8-1 问题">3.8.1 问题</h4>

<p>监控告警在Kubernetes场景下也是一个较难解决的问题，由于Docker隔离性问题，在容器内获取的监控指标如CPU、内存相关指标，传统的监控比如monitor或者网管agent的数据便不准确。</p>

<p>同时，Kubernetes又有独特的事件(event)信息，比如Pod销毁重建，扩缩绒，健康检查类的事件，这些事件不仅要采集持久化，还要进行事件告警。这部公司也没有任何的监控告警系统支持。</p>

<p>平台通过基础上报组件，与监控告警平台打通，支持了用户自定义指标告警。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(27)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h4 id="3-8-2 基础指标监控-告警">3.8.2 基础指标监控/告警</h4>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(28)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p>关于基础指标，平台使用prometheus作为基础监控，并对Kubelet做了改进，修正了部分上报参数（<a href="http://km.oa.com/articles/show/423025" target="_blank">kubernetes上报Pod已用内存不准问题分析</a>）。</p>

<p>于此同时，我们将基础指标转换为标准指标，上报到CMS（argus）监控中心，通过arugs处理监控告警指标，触发告警，发送到业务的负责人。</p>

<p>不得不承认，相对云传统情况下的监控，现在的监控指标相对于传统的指标还不够全面，这也是平台在努力补齐的方向，可以支持更加完全的监控数据。</p>

<h4 id="3-8-3 事件告警">3.8.3 事件告警</h4>

<p>STKE开发了事件采集器Event-Controller，实时的将事件采集到消息队里。一方面将数据持久化存储，另一方面将事件处理为监控指标的标准格式，上报到CMS（arugs），通过处理后发送给负责人。</p>

<p>由于K8S相关的事件类型上百个，平台经过筛选，将最常用的告警及产生原因梳理，把用户相关性最大的告警发送给用户（比如Pod异常销毁重建，发生自动扩缩绒等）。</p>

<h4 id="3-8-3 具体实现及应用文档">3.8.3 具体实现及应用文档</h4>

<p><a href="http://km.oa.com/articles/show/414609" target="_blank">STKE事件监控系统说明</a></p>

<p><a href="http://wiki.k8s.oa.com/quickstart/alarm.html" target="_blank">STKE自定义监控告警</a></p>

<h3 id="3-9 远程登录">3.9 远程登录</h3>

<p>为了能够适配容器场景的登录，STKE提供了两种方式。</p>

<h4 id="3-9-1 SSH登录">3.9.1 SSH登录</h4>

<p>平台提供的Tlinux_base镜像中，默认集成了铁将军模块，用户部署服务后，默认拥有机器权限，可以通过实名免密的方式，直接登录到容器中，无需输入密码。</p>

<pre class="  language-bash" style="position: relative; z-index: 2;"><code class="prism  language-bash"><span class="token function">ssh</span> rtx@PodIP
</code></pre>

<h4 id="3-9-2 WebConsole">3.9.2 WebConsole</h4>

<p>由于第一种方式不能适应所有场景，比如：</p>

<ul>
<li>
<p>权限同步需要时间，无法立刻登录；</p>
</li>
<li>
<p>用户自定义镜像无铁将军；</p>
</li>
<li>
<p>无ssh服务；</p>
</li>
</ul>

<p>因此基于这写场景，经过安全部门同学的协助与评估，逐渐开放了内部合规的Webconsole登录的功能，方便用户直接登录容器。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(29)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(30)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(31)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h3 id="3-10 CI-CD">3.10 CI/CD</h3>

<p>STKE也积极的跟公司主流CI系统合作，打通了自动发布的流程，在OrangeCI，蓝盾，QCI上，都集成了STKE的组件，用户经过GIT构建，镜像构建，推送仓库后，都可以直接更新STKE上的服务（当然一般是直接更新测试和预发布环境）。</p>

<p>同时，也将之前的zhiyun服务，可以保有原来构建PKG的流程，再将这些织云PKG组合构建出相应的镜像，发布到STKE（长尾服务迁移困难，最好的办法还是直接构建为镜像）。</p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(32)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(33)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<h4 id="3-10-1 OrangeCI插件">3.10.1 OrangeCI插件</h4>

<pre class="  language-yaml" style="position: relative; z-index: 2;"><code class="prism  language-yaml"><span class="token key atrule">master</span><span class="token punctuation">:</span>
  <span class="token key atrule">push</span><span class="token punctuation">:</span>
    <span class="token punctuation">-</span>
      <span class="token key atrule">stages</span><span class="token punctuation">:</span>
        <span class="token comment"># ...省略中间构建docker的部分</span>
        <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> stke update
          <span class="token key atrule">type</span><span class="token punctuation">:</span> stke<span class="token punctuation">:</span>update
          <span class="token key atrule">options</span><span class="token punctuation">:</span>
            <span class="token key atrule">kind</span><span class="token punctuation">:</span> statefulsetplus
            <span class="token key atrule">projectName</span><span class="token punctuation">:</span> prj<span class="token punctuation">-</span>3e6ckrwpkoyy
            <span class="token key atrule">namespaces</span><span class="token punctuation">:</span> prj<span class="token punctuation">-</span>3e6ckrwpkoyy
            <span class="token key atrule">clusterId</span><span class="token punctuation">:</span> cls<span class="token punctuation">-</span>98zz20xk
            <span class="token key atrule">resourceIns</span><span class="token punctuation">:</span>  deployment<span class="token punctuation">-</span>runner
            <span class="token key atrule">name</span><span class="token punctuation">:</span>  demo<span class="token punctuation">-</span>container
            <span class="token key atrule">image</span><span class="token punctuation">:</span> csighub.tencentyun.com/demo/demo<span class="token punctuation">:</span>$<span class="token punctuation">{</span>ORANGE_BUILD_ID<span class="token punctuation">}</span>
</code></pre>

<p><a href="http://doc.orange-ci.oa.com/internal-steps/stke/update.html#%E8%BE%93%E5%87%BA" target="_blank">OrangeCI STKE Update</a></p>

<h4 id="3-10-2 QCI插件">3.10.2 QCI插件</h4>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(34)" alt="" style="position: relative; z-index: 2;"></p>

<p><a href="http://qci.oa.com/#/plugins_market/STKE_update" target="_blank">QCI STKE Update</a></p>

<h4 id="3-10-3 蓝盾插件">3.10.3 蓝盾插件</h4>

<p style=""><img src="./【k8s 开源协同】STKE---基于Kubernetes的云原生平台实践 - Kubernetes - KM平台_files/cos-file-url(35)" alt="" style="position: relative; z-index: 2;" class="amplify"></p>

<p><a href="http://devops.oa.com/console/store/atomStore/detail/atom/stkeAtom" target="_blank">蓝盾 STKE Update</a></p>

<h2 id="4 业务接入案例">4 业务接入案例</h2>

<p>目前平台已经有超过2000+业务，很多业务也积极的反馈了问题，并且提供各自业务接入的文档，提供给大家参考。</p>

<ul>
<li>
<p><a href="http://km.oa.com/group/35679/articles/show/393588?kmref=home_headline" target="_blank">自动驾驶自研上云经验分享</a></p>
</li>
<li>
<p><a href="http://km.oa.com/articles/show/422035?kmref=search&amp;from_page=1&amp;no=1" target="_blank">stke接入流程</a></p>
</li>
<li>
<p><a href="http://km.oa.com/articles/show/420165?kmref=search&amp;from_page=1&amp;no=4" target="_blank">画眉TTS使用OCI,STKE发布</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/578/articles/show/390969?kmref=search&amp;from_page=1&amp;no=3" target="_blank">STKE + 织云 + ULS 搭建内部上云服务实践</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/18297/articles/show/390468?kmref=search&amp;from_page=1&amp;no=6" target="_blank">STKE + Orange-ci + TSW 30 分钟弹射起步</a></p>
</li>
<li>
<p><a href="http://km.oa.com/base/attachments/attachment_view/203547" target="_blank">点石STKE自研上云之路</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/22373/articles/show/371763" target="_blank">用 Docker STKE 容器三分钟创建一个内网管理后台系统</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/18055/articles/show/379083?kmref=home_recommend_read" target="_blank">【优图数据中台】分布式计算容器化之路前传–kubernetes接入</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/11800/articles/show/376112?kmref=search&amp;from_page=1&amp;no=10" target="_blank">orange-ci 构建 going 项目 &amp;&amp; stke 部署实践</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/764/articles/show/379229?kmref=search&amp;from_page=2&amp;no=10" target="_blank">QQ web stke编排实践</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/36485/articles/show/378595?kmref=search&amp;from_page=3&amp;no=1" target="_blank">CapMock平台后台蓝盾&amp;stke部署&amp;内网上云探索</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/14568/articles/show/381471" target="_blank">STKE上云踩坑指南</a></p>
</li>
<li>
<p><a href="http://km.oa.com/articles/show/418099?ts=1564067970" target="_blank">企点营销server基础镜像制作</a></p>
</li>
<li>
<p><a href="http://km.oa.com/articles/show/418100?ts=1564069772" target="_blank">企点营销server 蓝盾+STKE上云流程</a></p>
</li>
<li>
<p><a href="http://km.oa.com/group/29048/articles/show/370009?kmref=knowledge" target="_blank">【自研上云】基于蓝盾和TKE实践CI/CD流水线之路</a></p>
</li>
<li>
<p><a href="http://km.oa.com/articles/show/399246" target="_blank">123</a></p>
</li>
<li>
<p><a href="http://km.oa.com/knowledge/4662" target="_blank">在线教育上云文集</a></p>
</li>
</ul>

<h2 id="5 问题及展望">5 问题及展望</h2>

<p>在平台建设中，发现有很多问题还需要平台和用户，以及周边团队共同解决。比如</p>

<ul>
<li>
<p>平台与其他产品、研发流程之前还是相对独立的，不利于研发流程闭环。</p>
</li>
<li>
<p>用户创建部署好服务后，有些参数变更需要修改yaml，非常复杂，需要更优雅的转换为UI可视化。</p>
</li>
<li>
<p>在为用户创建UTA远程日志的时候，还需要调用第三方接口创建UTA主题，创建CLB和Ingress的时候，需要预先调用运管接口在创建yaml，使得用户无法直接通过编写yaml直接实现相应功能，这些我们也在推动优化。</p>
</li>
<li>
<p>对于相关监控和告警的支持不足，需要逐步完善。</p>
</li>
<li>
<p>针对集群负载，调度，亲和性等问题，也需要持续优化。</p>
</li>
<li>
<p>很多开发对Kuberetes等技术的了解不足，并不是所有开发都有兴趣去了解新的技术，并为之改进程序。</p>
</li>
<li>
<p>涉及到底层操作系统或内核问题，修复周期就会很长，可能运行在开源操作系统上正常的功能 ，在公司的版本下就可能无法支持，对此tlinux团队也在在帮助解决新技术引来的问题，在底层帮助用户更好的使用云原生技术。</p>
</li>
<li>
<p>容器技术让开发可以自由的构建镜像或者使用开源的镜像，这对安全也产生了新的挑战。平台也积极的向安全部门需求帮助，在安全合规的条件下，给用户最大的自由。</p>
</li>
<li>
<p>在未来发展中，基于Kubernetes、istio的环境治理也是产品演进的方向，也已经有产品在测试，生产环境下使用。</p>
</li>
<li>
<p>随着云原生技术的发展Serverless又回归大众视野，也有可能再次焕发光彩。</p>
</li>
</ul>

<p>总之，目前和方向是明朗的，路途是艰辛的，还需要小伙伴们共同努力。</p>

<h2 id="6 开源协同">6 开源协同</h2>

<h3 id="6-1 STKE开源项目">6.1 STKE开源项目</h3>

<p>目前，STKE为支持开发了公共组件。当前虽然公开了实现代码，有些在文档说明和代码实现上还有很多不足，希望大家批评指正。</p>

<p>| 组件                     | 简介                                                         | 开源地址                                             |<br>
| : ------------------------ | :--------------------------------------------- | : ---------------------------------------------------- |<br>
| statefulsetplus-operator | 基于CRD+Operator开发的一种自定义的K8S工作负债（StatefulSetPlus），核心特性包括：1. 兼容StatefulSet所有特性。   2. 支持分批灰度更新和一键回滚，每个批次更新时，Pods是并发更新的。    3. 对接了TKE Ipamd，实现了Pod固定IP;   4. 支持HPA;    5. 支持Operator高可用部署;    6.支持Node失联时，Pod的自动漂移;   7.支持容器原地升级;    8.支持在分批发布时如果触发了自动扩容，选择旧版或者新版本扩容; | <a href="https://git.code.oa.com/k8s/statefulsetplus-operator" target="_blank">https://git.code.oa.com/k8s/statefulsetplus-operator</a> |<br>
| L5-controller            | L5-controller是用于TKE  Service和公司路由系统(L5/CL5/CMLB)由对接的Kubernetes 控制器。负责监控服务的创建、更新和销毁，将路由同步更新到公司路由。目前支持l5, cmlb, cl5名字服务。 | <a href="https://git.code.oa.com/k8s/l5-controller" target="_blank">https://git.code.oa.com/k8s/l5-controller</a>            |<br>
| init-container           | 进行业务初始化工作，比如进行织云权限注册、CMDB注册等。       | <a href="https://git.code.oa.com/k8s/init-action" target="_blank">https://git.code.oa.com/k8s/init-action</a>              |<br>
| cmdb-controller          | 自动注册ip 到公司cmdb，并同步到cmdb4。                       | <a href="https://git.code.oa.com/k8s/cmdb4-controller" target="_blank">https://git.code.oa.com/k8s/cmdb4-controller</a>         |<br>
| cmdb2-controller         | 根据微服务化设计，把微服务树结构信息注册到新版本cmdb(基于微服务设计的CMDB)中。 | <a href="https://git.code.oa.com/k8s/cmdb4-controller" target="_blank">https://git.code.oa.com/k8s/cmdb4-controller</a>         |<br>
| hpaplus-controller       | 1. 独立部署，优化了性能，其资源需求可以是集群规模和HPA数量进行合理调整;  2. 支持各个HPA对象自定义伸缩响应时间，支持自动感应业务是否在变更发布并决定是否要禁用HPA;  3. 支持业务级别对负载的抖动容忍度的个性化配置;  4. 通过Extension APIServer的方式对接公司Monitor监控，保留Prometheus-Adaptor的方式来支持基于Prometheus的应用监控，满足基于多种应用监控系统的custom metrics进行HPA。 | <a href="https://git.code.oa.com/STKE/hpaplus-controller" target="_blank">https://git.code.oa.com/STKE/hpaplus-controller</a>      |</p>

<h3 id="6-2 公司开源项目">6.2 公司开源项目</h3>

<p>同时，也欢迎大家加入公司的开源协同项目 <a href="https://techmap.oa.com/oteam/8486" target="_blank">kubernetes(k8s) Oteam</a>，参与到公司开源项目中。</p>

<h2 id="7 参考文献">7 参考文献</h2>

<ol>
<li><a href="https://github.com/cncf/toc/blob/master/DEFINITION.md#%E4%B8%AD%E6%96%87%E7%89%88%E6%9C%AC" target="_blank">https://github.com/cncf/toc/blob/master/DEFINITION.md</a></li>
<li><a href="https://github.com/cncf/toc/blob/master/DEFINITION.md#%E4%B8%AD%E6%96%87%E7%89%88%E6%9C%AC" target="_blank">https://github.com/cncf/toc/blob/master/DEFINITION.md#%E4%B8%AD%E6%96%87%E7%89%88%E6%9C%AC</a></li>
<li><a href="https://www.infoworld.com/article/3281046/what-is-cloud-native-the-modern-way-to-develop-software.html" target="_blank">What is cloud-native? The modern way to develop software</a></li>
<li><a href="https://km.woa.com/group/31235/articles/show/%5Bhttps://kubernetes.io/zh/docs/concepts/overview/what-is-kubernetes/#%E4%B8%BA%E4%BB%80%E4%B9%88%E6%88%91%E4%BB%AC%E9%9C%80%E8%A6%81-kubernetes-%E5%AE%83%E8%83%BD%E5%81%9A%E4%BB%80%E4%B9%88%5D(https://kubernetes.io/zh/docs/concepts/overview/what-is-kubernetes/#%E4%B8%BA%E4%BB%80%E4%B9%88%E6%88%91%E4%BB%AC%E9%9C%80%E8%A6%81-kubernetes-%E5%AE%83%E8%83%BD%E5%81%9A%E4%BB%80%E4%B9%88)" target="_blank">Kubernetes官方文档</a></li>
<li><a href="http://km.oa.com/group/31235/articles/show/385219?kmref=discovery_page" target="_blank">POD固定IP实现原理</a></li>
</ol>
