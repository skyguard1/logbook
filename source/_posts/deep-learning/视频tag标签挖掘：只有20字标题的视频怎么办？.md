---
title: "视频tag标签挖掘：只有20字标题的视频怎么办？"
date: 2022-04-24 09:56:44
categories:
  - deep-learning
---

<h2 id="h2-u6807u7B7Eu6269u5C55"><a name="标签扩展" class="reference-link"></a><span class="header-link octicon octicon-link"></span>标签扩展</h2><h2 id="h2-demo"><a name="Demo" class="reference-link"></a><span class="header-link octicon octicon-link"></span>Demo</h2><h4 id="h4--strong-query-query-strong-"><a name="&lt;strong&gt;注：看后台日志，有同学query过“搞笑”、“狗”、“虎扑”，返回错误的结果，标签扩展建立在已知的标签基础上，直接query“搞笑”、“狗”、“虎扑”等词汇更像是找同义词，建议输入一句话，比如视频标题，文章标题等&lt;/strong&gt;" class="reference-link"></a><span class="header-link octicon octicon-link"></span><strong>注：看后台日志，有同学query过“搞笑”、“狗”、“虎扑”，返回错误的结果，标签扩展建立在已知的标签基础上，直接query“搞笑”、“狗”、“虎扑”等词汇更像是找同义词，建议输入一句话，比如视频标题，文章标题等</strong></h4><p><del>一个在线测试入口，输入标题，submit，返回相关推荐结果<br><a href="http://100.88.65.196:8080/" target="_blank">http://100.88.65.196:8080/</a></del><br></p><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ 标题：黄子韬唱《爱转角》，张杰问“谁的歌”罗志祥好尴尬！ ]</div></div><br><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ 返回结果 ]</div>

<p></p>
<h2 id="h2-background"><a name="Background" class="reference-link"></a><span class="header-link octicon octicon-link"></span>Background</h2><p><strong>keyphrases extraction</strong>(<em>关键词提取</em>)通过算法模型从文本中抽取，如tf-idf,textrank等un-supervised算法，也有根据标注数据将问题分解为分类、回归问题的supervised方法。<br>对视频打标签难度大于文本，视频相关的text通常只有一个标题，字数一般小于20。难以概括整个视频的所有关键信息。</p>
<p></p><div style="text-align: left;"></div><br>如视频 <a href="http://post.mp.qq.com/kan/video/1900763186-6005ade2954417ah-u0636i1byjv.html?_wv=2281701505&amp;sig=a84ceea993cc5771b471dce2c3145411&amp;time=1524509013" target="_blank"><strong>黄子韬唱《爱转角》，张杰问“谁的歌”罗志祥好尴尬！</strong></a>从视频标题里，直观感受，可以做tag的词有“<strong>黄子韬</strong>”，“<strong>爱转角</strong>”，“<strong>张杰</strong>”，看完视频后，可以知道视频讲的是“<strong>创造101</strong>”的“<strong>综艺片段</strong>”，而这两个tag是从视频标题本身无法抽取出来的。需要借助其他数据，如知识图谱，word embedding等，背后其实是大量非结构化的数据中提取出的一些结构化数据，知识图谱过于复杂，涉及分词，关系提取，需要大量人工辅助。<p></p>
<h2 id="h2-plan"><a name="Plan" class="reference-link"></a><span class="header-link octicon octicon-link"></span>Plan</h2><p>由于没有大量的标注数据，标签拓展主要依靠un-supervised方法，从知识图谱、关联关系、word embedding等多种技术。</p>
<ol>
<li>知识图谱 - 知识图谱是一个高成本、费人力的project。从大量的文本内容中，挖掘实体，关系，首先就是一个很难的挑战，需要介入不少人力来维护。</li><li>关联关系 - 关联关系与word embedding的区别在于，关联关系更容易挖掘<strong>“实体”-“属性”</strong>之间的关系，如何理解这一问题，见后续单独的文章介绍。</li><li>word embedding - embedding的问题在于词与词之间的关系倾向于同级别，如<strong>“北京”-“上海”</strong>；<strong>“张杰”-“谢娜”</strong>，另一个问题在于时效性问题，由于embedding非实时更新，出现了新的关系时，需要重新训练embedding。</li></ol>
<p>当经过一段时间的线上人工介入后，将人工选取的推荐标签作为正样本可以做supervised learning得到更好的结果。</p>
<h2 id="h2-details"><a name="Details" class="reference-link"></a><span class="header-link octicon octicon-link"></span>Details</h2><h4 id="h4--strong-tag-topic-strong-"><a name="&lt;strong&gt;注：本文重点描述如何进行tag的扩展，即挖掘出非标题中出现的标签。如何提取已知文本中的标签，属于另一个topic了，不在本文介绍范围之内&lt;/strong&gt;" class="reference-link"></a><span class="header-link octicon octicon-link"></span><strong>注：本文重点描述如何进行tag的扩展，即挖掘出非标题中出现的标签。如何提取已知文本中的标签，属于另一个topic了，不在本文介绍范围之内</strong></h4><p>举个例子，一篇讲<strong>“张杰”</strong>的文章，很大概率会出现<strong>“谢娜”</strong>，<strong>张杰的歌</strong>等等，其实都是张杰的<strong>属性</strong><br><em>张杰 -&gt; 老婆 -&gt; 谢娜</em><br><em>张杰 -&gt; 歌曲 -&gt; xxx</em><br>他们是大概率共现的，而word embedding虽然也是一种共现关系，但是word2vec会更倾向于找到“北京”- ”上海“这种关系，或者 v(北京) - v(中国) = v(东京) - v(日本)的关系。这里的共现关系是 <strong>“上海” - “黄浦区”</strong> 这样的关系。因为上海，黄浦区经常出现在同一篇文章里；张杰，谢娜经常出现在一篇文章里，正是因为这个现象，才可以考虑用关联关系的方法来做。<br>但这里我们用到的关联关系并非apriori等严格意义的关联关系算法，这里采用类似<strong>协同过滤</strong>的方式去求解。回想标准user-based cf在推荐场景下，基于users点过的items的行为数据，来分析出当前用户在点击了某些item的情况下，会倾向于点击其他的哪些item？<br>其实这里每篇文章可以类比为user本身，文章里的词就是item本身，正因为这里的“张杰”与“谢娜”的共现关系才会讲张杰的时候把谢娜推荐出来。<br>例如：</p>
<ul>
<li>文章a 张杰 谢娜 创造101</li><li>文章b 张杰 谢娜 女儿</li><li>文章c 张杰 谢娜 快乐大本营</li></ul>
<p>假设文章d讲的是“张杰”，大概率也会去讲“谢娜”，这里就是用的这个思想。回到上面的case，<strong>黄子韬唱《爱转角》，张杰问“谁的歌”罗志祥好尴尬！</strong>，在已知tag为<strong>黄子韬，爱转角，张杰，罗志祥</strong>的背景下，会去相关文章里捞取到很多相关内容，而<strong>近期</strong>有大量《创造101》的文章包含了这些tag，所以会推出<strong>创造101</strong>。</p>
<h2 id="h2-case"><a name="Case" class="reference-link"></a><span class="header-link octicon octicon-link"></span>Case</h2><h4 id="h4--strong-case-strong-"><a name="&lt;strong&gt;注：以下case返回的推荐标签结果都抹去了出现在标题内的内容，主要体现从标题本身引申出来推断的集合&lt;/strong&gt;" class="reference-link"></a><span class="header-link octicon octicon-link"></span><strong>注：以下case返回的推荐标签结果都抹去了出现在标题内的内容，主要体现从标题本身引申出来推断的集合</strong></h4><p>通过关联关系生成的推荐标签效果非常不错，分析原因如下：</p>
<ol>
<li>本身历史文章已经通过了标签抽取的技术生成了大量历史文章关键词的集合。</li><li>多篇相关文章同时对相关事件的多方面描述，最终更好的找出关联的关系</li></ol>
<p>以下列出一些case供参考</p>
<hr>
<p></p><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ yaoyaoyu-远大前程 ]</div></div><br><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ 某鹅号-远大前程 ]</div></div><br><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ 标签索引-远大前程（部分） ]</div></div><br>标题中最关键的tag莫非<strong>“远大前程”</strong>，我们根据这个词去相关图文中去获取到了大量关联的tag，最终通过类似于关联分析的办法，对所有相关tag进行一个打分，得到了一个排名，从结果来看，可以提取出<strong>“齐林”，“洪三元”，“于梦竹”</strong>等角色名，也可以提出相关的演员名字，对比于word2vec更容易得到“平级”关系，关联关系的方法更容易获取<strong>“实体”-“属性”</strong>的关系。<p></p>
<hr>
<p></p><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ yaoyaoyu-战神纪 ]</div></div><br><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ 某鹅号-战神纪 ]</div></div><br>这个视频<a href="http://post.mp.qq.com/kan/video/201218848-6705ade02fe188ah-h0636542fup.html?_wv=2281701505&amp;sig=cf4c96b8adc103ce5d040a496ca65b1b&amp;time=1524499295" target="_blank"><strong>“林允同陈伟霆出席活动！这CP感真的好强大呀”</strong></a>本身标题信息只有林允，陈伟霆，视频本身是12秒的发布会内容，我们可以推荐出<strong>“胡军”（主演），“《战神纪》”（片名），“铁木真”（主要角色）</strong><p></p>
<hr>
<p></p><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ yaoyaoyu-创造101 ]</div></div><br><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ 某鹅号-创造101 ]</div></div><br>如上文所说，视频为<strong>“创造101”</strong>的<strong>综艺片段</strong>，标题中并未出现“创造101”，可以顺利的推荐出这个tag。<p></p>
<hr>
<p></p><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ yaoyaoyu-下一站，别离 ]</div></div><br><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ 某鹅号-下一站，别离 ]</div>

<p></p>
<hr>
<p></p><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ yaoyaoyu-绝地求生 ]</div></div><br><div style="text-align: center;"><br><div style="border-bottom: 1px solid #d9d9d9;display: inline-block;text-align:center;color: #999;padding: 10px;"> [ 某鹅号-绝地求生 ]</div>

<p></p>
<p>从以上case可以看出，对于视频内容打标签的问题，由于文本内容过少，视频本身又难以提出标签，可以通过“知识”作为背景去尝试扩展标签，如知识图谱，关联关系，word embedding的方法，本文主要通过<strong>关联关系</strong>的方法，成功选出一批相关候选集，作为人工审核、mp号主、流量主可以选择的集合，进一步改善用户体验和提高人工审核进度。</p>
