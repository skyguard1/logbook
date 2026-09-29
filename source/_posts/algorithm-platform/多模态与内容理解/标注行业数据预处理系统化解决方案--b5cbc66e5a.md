---
title: "标注行业数据预处理系统化解决方案"
date: 2022-04-07 10:19:23
categories:
  - 算法平台
  - 多模态与内容理解
---

{% raw %}

<section><section><p><strong>特别说明：以下内容仅供内部学习使用，严禁外传。</strong></p>
<section><section><p><br/></p>
</section></section><section><section><section><section><section><p><strong>研究员介绍</strong></p>
</section></section></section></section><section></section></section><p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/de4008a710eacc6f5c4a.png"/></p>
<section><section><section><section><p><b>1.背景介绍</b></p>
</section></section></section></section><p>      在机器学习中建模数据的质量，直接决定了模型的预测和泛化能力的好坏。数据质量涉及很多因素，包括：准确性、完整性、一致性、时效性、可信性和解释性。而我们真实拿到的原始数据中可能包含了大量的缺失值和噪音，非常不利于数据标注，从而导致标注效率慢，直接影响到模型的喂养。数据预处理则是对各种脏数据进行对应方式的处理，得到标准的、干净的、连续的数据，合理的预处理方式能提升人工标注的效率和质量。</p>
<p>      本文主要梳理了数据标注行业过往在数据处理环节遇到的常见问题及对应的解决方案。</p>
<p><br/></p>
<section><section><section><section><p><b>2.存在问题</b></p>
</section></section></section></section><p>       在标注生产链条中各环节均有不同类型的数据问题，分三个阶段来分析：</p>
<p>1、标注前：主要存在<strong>数据重复与无效数据</strong>（图片，音频，文字，视频）以及<strong>数据格式异常</strong>（图片，音频需要转码）。</p>
<p>2、标注中：主要涉及<strong>转换预识别结果格式</strong>，导入平台辅助标注<strong>，</strong>如：将ASR，OCR的预识别结果导入AOP。</p>
<p>3、标注后：主要涉及<strong>标注结果的格式检查</strong>，如ASR标注结果需要对KALDI数据进行格式检查；OCR结果需要对框的顺序检查等。</p>
<p>       因此，数据问题的表现形式大致分为重复数据、无效数据、数据格式不符及标注结果检查四种类型。以下是对各问题的详细描述及对应示例。</p>
<h3><strong>2.1 重复数据</strong></h3>
<p>      在待标注数据中存在较多的相同数据和相似数据导致重复标注。主要包含类型为图片重复，图片相似，音频、视频、文本重复。</p>
<p><strong>2.1.1 相同数据：</strong>数据MD5一致，示例如下<img alt="" loading="lazy" src="/logbook/images/algorithm-platform/814c526b85b8770caf4a.png"/></p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1f00f338e3789032b1ee.png"/></strong></p>
<p><strong>2.1.2 </strong><strong>相似数据</strong>：MD5不同，肉眼相似，示例如下</p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f773197b5235dac1d727.png"/></strong></p>
<p><strong><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/3f2289ff2f441dbb28b4.png"/></strong></p>
<p><strong><br/></strong></p>
<h3><strong>2.2 无效数据</strong></h3>
<p>      在待标注数据中存在不合理的数据，不符合标注相关的标准。无效数据主要包含失效数据、乱码数据、与需求无关的数据三大类。</p>
<p><strong>2.2.1 </strong><strong>失效数据</strong>：因服务器迁移或文件删除，导致链接无法访问的文件</p>
<p><strong>2.2.2 </strong><strong>乱码数据</strong>：文本文件中，影响训练或标注的无意义字符，如下图，蒙语数据清洗前包含了汉语、英语等各类噪音数据。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/390a4e0cd4b47a0bd829.png"/></p>
<p><strong>2.2.3 </strong><strong>与需求无关的数据：</strong>与需求标准不相符的数据，如粤语OCR标注中的非粤语数据</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/46c3ecaa16a6d04a0ee0.png"/></p>
<p><br/></p>
<h3><strong>2.3 数据格式不符</strong></h3>
<p>在待标注数据中，区别与标准格式的数据。包含文件格式不符和内容格式不符两种情况：</p>
<p><strong>2.3.1 </strong><strong>文件格式不符</strong></p>
<p>如图片类需求：当原始数据中同时存在多种图片格式（如.jpeg .png等）时，需要将其转化为目标格式。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/f4cbeaf221f542a9b44a.png"/></p>
<p>音频类需求：将音频类数据转换为标准格式，16K，16BIT，单声道的wav文件。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c06fcc9f7fb9a96f733a.png"/></p>
<p><strong>2.3.2 </strong><strong>内容格式不符</strong></p>
<p>1、需要将目标文件的内容提取出来转换成另外一种格式，如将XML里面需要的信息提取至EXCEL表格中展示。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1ba8626ab2f32fcaf42d.png"/></p>
<p>2、需要将服务识别结果转换为XML等AOP平台能够导入的文件格式。如将ASR模型的识别结果中json格式转换为XML格式。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/79b3e7987faa630d4e0d.png"/></p>
<p><br/></p>
<h3><strong>2.4 标注结果检查</strong></h3>
<p>      将人工标注的数据结果进行格式检查，如音频ASR数据需要检查KALDI格式文件的对应关系、图片OCR标注结果需要检查坐标顺序等。</p>
<p>      以ASR标注结果为例：ASR交付结果为KALDI格式包含wav.scp、text、segments三个文件，三个文件ID相互对应，异常表现为段数不一致。示例如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ba737e7fb166fdfade7b.png"/></p>
<p><br/></p>
<section><section><section><section><p><b>3.处理方案</b></p>
</section></section></section></section><p>      我们通过历史沉淀的经验对上述问题提出了对应的解决方案，提升了标注质量并节省了人力成本。因此数据处理环节在整个标注生产链条中也都会涉及，主要包括<strong>重复数据清洗、无效数据剔除、数据格式转换、标注结果检查</strong>四大类。</p>
<h3><strong>3.1 重复数据清洗</strong></h3>
<p>      标注前的数据去重主要包含相似度去重和历史数据去重两类，下面针对每一个类别，将单独描述去重的方案以及实现逻辑。</p>
<p><strong>3.1.1 相似数据去重</strong></p>
<p>适用范围：主要适用于图片文件，文字数据由于相差一个字会导致语义发生变化，所以不推荐使用。</p>
<p>实现方案：使用感知哈希算法，对比汉明距离， 距离越近越相似。将一定阈值下的图片进行聚类，保留其中一个数据，完成相似度去重。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a7fbb10adeaf44934af7.png"/></p>
<p>我们可以看到不同链接的图片通过 phash 完成聚类后，效果如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ee1b29e552254505f898.png"/></p>
<p><strong>3.1.2 相同数据去重</strong></p>
<p>适用范围：图片，音频，视频，文档文件。</p>
<p>实现方案：通过获取文件的MD5存储于数据库，后续的待标注文件将抽取MD5与历史库进行对比，包含在历史库的数据则标记为已有，新数据则标记为新增，并将新增的数据MD5写入历史库。完成历史去重。（每一类需求需要建立不同的历史库）</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/da12cd6ec78f745d00b9.png"/></p>
<h3><strong>3.2 无效数据剔除</strong></h3>
<p>      无效数据主要包含失效数据、乱码数据及与需求无关的数据三大类，每一类的清洗方案有所差异，以下将针对各类无效数据的通用方案进行描述。</p>
<p><strong>3.2.1 失效数据</strong></p>
<p>适用范围：URL链接类型数据，非实体数据。</p>
<p>实现方案：通过request模拟访问URL是否成功，对URL进行失效判断。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/871ff65827a78d9de6d8.png"/></p>
<p>方案结果：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/109e3c97d75249238395.png"/></p>
<p><strong>3.2.2 乱码数据</strong></p>
<p>适用范围：文本类数据</p>
<p>实现方案：通过正则表达式编写乱码规则形成规则池，包含【空行】【乱码】【网址】【emoji表情】【表情】【汉语】【英语】【符号】等规则，数据根据不同的情况，选择不同的规则进行数据清洗。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/ce1f166057cedf35362f.png"/></p>
<p>方案效果：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/47f42987be6c9b2e62ef.png"/></p>
<p><strong>3.2.3 与需求无关的数据</strong></p>
<p>适用范围：图片，音频，文字，视频</p>
<p>实现方案：由于需求类型不同，此清洗方案无通用方案，需要根据需求标准进行适配。</p>
<p>案例：粤语OCR样本自动清洗，从视频中截取样本帧，利用图片OCR识别结果与粤语词库的匹配，剔除非粤语数据。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/dc5dfec9e24ed32a4210.png"/></p>
<p>方案流程：</p>
<p>1）对视频数据进行关键帧截取，获取视频中文字变化的帧，然后通过图片OCR识别获取关键帧中的文字信息。通过关键帧+坐标+内容的形式进行存储，如下图：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/fee8e6abe993c539036f.png"/></p>
<p>2）将所有关键帧的文本内容与粤语词库进行匹配，判断图片中的文字信息是否包含粤语词</p>
<p>3）最后通过计算粤语占比捞取一定阈值下的数据，并将关键帧实体文件（jpg格式）存储于服务器，对应的图片识别结果以xml格式文件存储于服务器中。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/e53bc23469eb7434a952.png"/></p>
<p><br/></p>
<h3><strong>3.3 数据格式转换</strong></h3>
<p>数据格式转换主要包含<strong>文件格式转换、内容格式转换</strong>两类，由于格式之间的差异较大，通用方案设计方面覆盖不够全面。目前需持续优化。</p>
<p><strong>3.3.1 文件格式转换</strong></p>
<p>常见的文件格式转换：图片格式/音频格式异常，将导致需求方无法使用</p>
<p>实现方案<strong>：</strong>获取图片/音频源格式信息，通过对应的方法修改文件编码（音频主要是采样率，比特率，位宽，声道，图片主要是格式）信息达到转码的目的。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/747ffc1481c04c1e9d86.png"/></p>
<p>案例：图片格式转换，将bmp文件格式转为jpg格式</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/58ddd4c0c3a842252b49.png"/></p>
<p><strong>3.3.2 内容格式转换</strong></p>
<p>内容格式不符主要出现为<strong>特定信息提取</strong>和<strong>预标注结果转换</strong>两类：</p>
<p>1）特定信息提取：主要存在于运营分析的工作中，包括xml与json类的格式，人工分析较为困难，通过提取有效信息生成excel便于进行数据整理分析。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/a7009004b6c02e124c70.png"/></p>
<p>案例：xml转excel</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/1ba8626ab2f32fcaf42d.png"/></p>
<p>2）预标注结果转换：数据信息一般通过调用对应服务，生成平台所对应的xml信息，用于在标注台展示预识别结果。</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/c21440ce8c08a300424e.png"/></p>
<p>案例：OCR模型结果转XML</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/79b3e7987faa630d4e0d.png"/></p>
<p><br/></p>
<h3><strong>3.4 标注结果检查</strong></h3>
<p>      由于标注过程中数据、人员或平台的问题可能导致标注后的部分结果不符合标准，当前我们已经在ASR和OCR的标注结果上形成了完备的检查方案，流程如下：</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/4db57ee15ce261580b3d.png"/></p>
<p>案例：在OCR标注结果中坐标框的顺序为从左到右、从上到下，因此OCR结果检查方案中需要对非标准顺序的数据进行提示，以确保标注数据的质量，以下为检查结果示例</p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/8f3e0da4682ca550b13f.png"/></p>
<p><br/></p>
<section><section><section><section><p><b>4.结语</b></p>
</section></section></section></section><p>      以上处理方案来源于对过往经验的总结，然而在数据标注行业中不同的需求所需的数据处理都有自己的特点，需要结合实际情况采取不同的应对措施。本文通过对过往经验进行沉淀输出，总结出数据处理中的共性问题，并给出一些已有的解决方案，希望能给刚入门的同学和我们自己有一些方向的指导，文章中出现的解决方案可能并非最优解，我们也在持续对各类数据处理方案进行优化，也欢迎大家相互交流。</p>
<p><br/></p>
<p><br/></p>
<p><img alt="" loading="lazy" src="/logbook/images/algorithm-platform/19cdb202013e00bf9624.png"/></p>
<p><br/></p>
</section></section> 
{% endraw %}
