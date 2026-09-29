---
title: "召回框架在线Service结构设计(v1.0版本)"
date: 2022-04-02 11:47:37
categories:
  - 算法平台
  - 召回排序与特征
---

{% raw %}

<p></p><div><ul><li>11. 模块结构<ul><li>1.11.1. Manager</li><li>1.21.2. Trigger</li><li>1.31.3. OP</li><li>1.41.4. Plugin</li></ul></li><li>22. 配置结构设计说明<ul><li>2.12.1. Manger configure</li><li>2.22.2. Trigger Configure</li><li>2.32.3. OP Configure</li><li>2.42.4. 补充说明</li></ul></li><li>33. 使用说明<ul><li>3.13.1. 如何管理配置</li><li>3.23.2. 如何跟TAB联通进行实验</li><li>3.33.3. 如何使用框架上线和管理召回</li></ul></li><li>44. 工程说明<ul><li>4.14.1. 技术框架</li><li>4.24.2. 开发现状</li></ul></li></ul></div>
<p></p><h2>1. 模块结构</h2><h3>1.1. Manager</h3><p>用于管理和调用Trigger，通过解析ManagerConfig来对线上生效的召回列表进行管理，以及每一路召回的逻辑、参数的管理。</p><h3>1.2. Trigger</h3><p>召回服务实体，内核由DAG串联一系列OP组成，算法在线部分策略的完整逻辑，按OP来切分执行步骤。Trigger入口数据包括：UI请求信息，用户画像(长短实时)，正排索引数据.</p><p>召回候选部分可以抽象成几个步骤，比如OP:recall,filter,prerank,rerange, 以DAG配置形式来定义不同Trigger; 不同Trigger之间的差异由自定义OP来实现.</p><h3>1.3. OP</h3><p>召回策略的基础部件，作为Trigger的子模块，用于实现具体的步骤逻辑细节，并且能够被不同Trigger复用。</p><p>包括比如 recall(召回候选)，filter(各种过滤)，prerank(单路召回粗排)，rerange(类似rerank，包括打散重排一些操作) 等，亦可以自己自己开发具体业务逻辑的算子。</p><p>算子接口统一， 便于OP<strong>自由组合</strong>以及算法<strong>自定义</strong>算子.</p><h3>1.4. Plugin</h3><p>一些主要由工程实现好的基础工具类，比如RedisWrapper，AnnWrapper，TFService等。Plugin是通用工具类，Trigger和OP的配置中都可以有Plugin的配置项.</p><p><br/></p><p>
</p><div>
<div> <svg><defs><filter id="dropShadow"><fegaussianblur></fegaussianblur><feoffset></feoffset><feflood></feflood><fecomposite></fecomposite><feblend></feblend></filter></defs><g transform="scale(0.97,0.97)translate(408,48)"><g></g><g><g transform="translate(0.5,0.5)"><rect fill="none" height="600" stroke="white" stroke-width="9" width="750" x="-400" y="-40"></rect><rect fill="none" height="600" stroke="#007fff" width="750" x="-400" y="-40"></rect></g><g transform="translate(0.5,0.5)"><rect fill="none" height="470" stroke="white" stroke-width="9" width="730" x="-390" y="-20"></rect><rect fill="none" height="470" stroke="#000000" width="730" x="-390" y="-20"></rect><rect fill="none" height="466" stroke="white" stroke-width="9" width="726" x="-388" y="-18"></rect><rect fill="none" height="466" stroke="#000000" width="726" x="-388" y="-18"></rect></g><g transform="translate(0.5,0.5)"><path d="M -370 13 L -370 -10 L -210 -10 L -210 13" fill="#007fff" stroke="#000000"></path><path d="M -370 13 L -370 90 L -210 90 L -210 13" fill="none" stroke="white" stroke-width="9"></path><path d="M -370 13 L -370 90 L -210 90 L -210 13" fill="none" stroke="#000000"></path><path d="M -370 13 L -210 13" fill="none" stroke="white" stroke-width="9"></path><path d="M -370 13 L -210 13" fill="none" stroke="#000000"></path></g><g><g fill="#000000"><text x="-290" y="6.5">MANAGER</text></g></g><g><image height="9" preserveAspectRatio="none" width="9" x="-365" y="-5"/></g><g transform="translate(0.5,0.5)"><rect fill="none" height="20" stroke="white" stroke-width="9" width="70" x="-332" y="39"></rect><rect fill="none" height="20" stroke="none" width="70" x="-332" y="39"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>管理Triiger</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M -178.75 13 L -178.75 -10 L 21.25 -10 L 21.25 13" fill="#ff6666" stroke="#000000"></path><path d="M -178.75 13 L -178.75 230 L 21.25 230 L 21.25 13" fill="none" stroke="white" stroke-width="9"></path><path d="M -178.75 13 L -178.75 230 L 21.25 230 L 21.25 13" fill="none" stroke="#000000"></path><path d="M -178.75 13 L 21.25 13" fill="none" stroke="white" stroke-width="9"></path><path d="M -178.75 13 L 21.25 13" fill="none" stroke="#000000"></path></g><g><g fill="#000000"><text x="-78.75" y="6.5">BaseTrigger</text></g></g><g><image height="9" preserveAspectRatio="none" width="9" x="-174" y="-5"/></g><g transform="translate(0.5,0.5)"><rect fill="#ffcccc" height="30" rx="4.5" ry="4.5" stroke="#000000" width="170" x="-163.75" y="20"></rect><rect fill="#ffcccc" height="26" rx="3.9" ry="3.9" stroke="#000000" width="166" x="-161.75" y="22"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>U2IOffLineCommonTrigger</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#ffcccc" height="30" rx="4.5" ry="4.5" stroke="#000000" width="170" x="-161.25" y="100"></rect><rect fill="#ffcccc" height="26" rx="3.9" ry="3.9" stroke="#000000" width="166" x="-159.25" y="102"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>InsCommonTrigger</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#ffcccc" height="30" rx="4.5" ry="4.5" stroke="#000000" width="170" x="-161.25" y="140"></rect><rect fill="#ffcccc" height="26" rx="3.9" ry="3.9" stroke="#000000" width="166" x="-159.25" y="142"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>HotCommonTrigger</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#ffcccc" height="30" rx="4.5" ry="4.5" stroke="#000000" width="170" x="-161.25" y="180"></rect><rect fill="#ffcccc" height="26" rx="3.9" ry="3.9" stroke="#000000" width="166" x="-159.25" y="182"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>用户自定义Trigger</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#ffcccc" height="30" rx="4.5" ry="4.5" stroke="#000000" width="170" x="-161.25" y="60"></rect><rect fill="#ffcccc" height="26" rx="3.9" ry="3.9" stroke="#000000" width="166" x="-159.25" y="62"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>I2ICommonTrigger</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M 60 13 L 60 -10 L 320 -10 L 320 13" fill="#666666" stroke="#000000"></path><path d="M 60 13 L 60 380 L 320 380 L 320 13" fill="none" stroke="white" stroke-width="9"></path><path d="M 60 13 L 60 380 L 320 380 L 320 13" fill="none" stroke="#000000"></path><path d="M 60 13 L 320 13" fill="none" stroke="white" stroke-width="9"></path><path d="M 60 13 L 320 13" fill="none" stroke="#000000"></path></g><g><g fill="#000000"><text x="190" y="6.5">BaseOp</text></g></g><g><image height="9" preserveAspectRatio="none" width="9" x="65" y="-5"/></g><g transform="translate(0.5,0.5)"><path d="M 70 123 L 70 100 L 310 100 L 310 123" fill="#d5e8d4" stroke="#000000"></path><path d="M 70 123 L 70 160 L 310 160 L 310 123" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 123 L 70 160 L 310 160 L 310 123" fill="none" stroke="#000000"></path><path d="M 70 123 L 310 123" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 123 L 310 123" fill="none" stroke="#000000"></path></g><g><g fill="#000000"><text x="190" y="116.5">BaseFilterOp</text></g></g><g><image height="9" preserveAspectRatio="none" width="9" x="75" y="105"/></g><g transform="translate(0.5,0.5)"><rect fill="#b9e0a5" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="80" y="126.5"></rect><rect fill="#b9e0a5" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="82" y="128.5"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>FilterOpXX1</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#b9e0a5" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="200" y="128.25"></rect><rect fill="#b9e0a5" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="202" y="130.25"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>FilterOpXX1</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M 70 193 L 70 170 L 310 170 L 310 193" fill="#d5e8d4" stroke="#000000"></path><path d="M 70 193 L 70 230 L 310 230 L 310 193" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 193 L 70 230 L 310 230 L 310 193" fill="none" stroke="#000000"></path><path d="M 70 193 L 310 193" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 193 L 310 193" fill="none" stroke="#000000"></path></g><g><g fill="#000000"><text x="190" y="186.5">BasePreRankOp</text></g></g><g><image height="9" preserveAspectRatio="none" width="9" x="75" y="175"/></g><g transform="translate(0.5,0.5)"><rect fill="#ffe599" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="80" y="199"></rect><rect fill="#ffe599" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="82" y="201"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>PrerankOpXX1</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#ffe599" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="200" y="199"></rect><rect fill="#ffe599" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="202" y="201"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>PrerankOpXXN</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M 70 263 L 70 240 L 310 240 L 310 263" fill="#d5e8d4" stroke="#000000"></path><path d="M 70 263 L 70 300 L 310 300 L 310 263" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 263 L 70 300 L 310 300 L 310 263" fill="none" stroke="#000000"></path><path d="M 70 263 L 310 263" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 263 L 310 263" fill="none" stroke="#000000"></path></g><g><g fill="#000000"><text x="190" y="256.5">BaseRerangeOp</text></g></g><g><image height="9" preserveAspectRatio="none" width="9" x="75" y="245"/></g><g transform="translate(0.5,0.5)"><rect fill="#ff99cc" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="80" y="267"></rect><rect fill="#ff99cc" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="82" y="269"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>RerangeOpXX1</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#ff99cc" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="200" y="270"></rect><rect fill="#ff99cc" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="202" y="272"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>RerangeOpXXN</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M 70 333 L 70 310 L 310 310 L 310 333" fill="#d5e8d4" stroke="#000000"></path><path d="M 70 333 L 70 370 L 310 370 L 310 333" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 333 L 70 370 L 310 370 L 310 333" fill="none" stroke="#000000"></path><path d="M 70 333 L 310 333" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 333 L 310 333" fill="none" stroke="#000000"></path></g><g><g fill="#000000"><text x="190" y="326.5">用户自定义OP</text></g></g><g><image height="9" preserveAspectRatio="none" width="9" x="75" y="315"/></g><g transform="translate(0.5,0.5)"><rect fill="#cccccc" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="80" y="336"></rect><rect fill="#cccccc" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="82" y="338"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>自定义OP1</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#cccccc" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="200" y="336"></rect><rect fill="#cccccc" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="202" y="338"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>自定义OPN</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M 70 46 L 70 23 L 310 23 L 310 46" fill="#d5e8d4" stroke="#000000"></path><path d="M 70 46 L 70 90 L 310 90 L 310 46" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 46 L 70 90 L 310 90 L 310 46" fill="none" stroke="#000000"></path><path d="M 70 46 L 310 46" fill="none" stroke="white" stroke-width="9"></path><path d="M 70 46 L 310 46" fill="none" stroke="#000000"></path></g><g><g fill="#000000"><text x="190" y="39.5">BaseRecallOp</text></g></g><g><image height="9" preserveAspectRatio="none" width="9" x="75" y="28"/></g><g transform="translate(0.5,0.5)"><rect fill="#66b2ff" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="80" y="55"></rect><rect fill="#66b2ff" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="82" y="57"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>RecallOpXX1</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#66b2ff" height="25" rx="3.75" ry="3.75" stroke="#000000" width="100" x="200" y="55"></rect><rect fill="#66b2ff" height="21" rx="3.15" ry="3.15" stroke="#000000" width="96" x="202" y="57"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>RecallOpXXN</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#ff9999" height="40" rx="6" ry="6" stroke="#000000" width="157.5" x="-157.5" y="260"></rect><rect fill="#ff9999" height="36" rx="5.4" ry="5.4" stroke="#000000" width="153.5" x="-155.5" y="262"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>TRIGGER_CONFIGS</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M -78.75 260 L -78.9 260 L -78.98 256.47 L -78.89 252.94 L -78.63 249.41 L -78.62 245.88 L -78.75 242.35" fill="none" stroke="white" stroke-width="11"></path><path d="M -78.75 260 L -78.9 260 L -78.98 256.47 L -78.89 252.94 L -78.63 249.41 L -78.62 245.88 L -78.75 242.35" fill="none" stroke="#000000" stroke-width="3"></path><path d="M -78.75 233.35 L -78.76 233.35 L -77.97 235.22 L -77.31 237.03 L -76.93 238.76 L -76.53 240.49 L -75.75 242.35 L -75.75 242.28 L -76.95 242.42 L -78.15 242.31 L -79.35 242.13 L -80.55 242.32 L -81.75 242.35 L -81.84 242.32 L -81.2 240.54 L -80.33 238.83 L -79.96 236.95 L -79.44 235.12 L -78.75 233.35 Z Z" fill="#000000" stroke="#000000" stroke-width="3"></path></g><g transform="translate(0.5,0.5)"><rect fill="#808080" height="40" rx="6" ry="6" stroke="#000000" width="157.5" x="120" y="400"></rect><rect fill="#808080" height="36" rx="5.4" ry="5.4" stroke="#000000" width="153.5" x="122" y="402"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>OP_CONFIGS</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M -347 480 L -370 480 L -370 550 L -347 550" fill="#b9e0a5" stroke="#000000"></path><path d="M -347 480 L 320 480 L 320 550 L -347 550" fill="none" stroke="white" stroke-width="9"></path><path d="M -347 480 L 320 480 L 320 550 L -347 550" fill="none" stroke="#000000"></path><path d="M -347 480 L -347 550" fill="none" stroke="white" stroke-width="9"></path><path d="M -347 480 L -347 550" fill="none" stroke="#000000"></path></g><g><g fill="#000000" transform="rotate(-90,-358.5,515)"><text x="-358.5" y="520">PLUGINS</text></g></g><g><image height="9" preserveAspectRatio="none" width="9" x="-365" y="485"/></g><g transform="translate(0.5,0.5)"><rect fill="#b9e0a5" height="45" rx="6.75" ry="6.75" stroke="#000000" width="120" x="-320" y="495"></rect><rect fill="#b9e0a5" height="41" rx="6.15" ry="6.15" stroke="#000000" width="116" x="-318" y="497"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>RedisWrapper</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#b9e0a5" height="45" rx="6.75" ry="6.75" stroke="#000000" width="120" x="-163.75" y="495"></rect><rect fill="#b9e0a5" height="41" rx="6.15" ry="6.15" stroke="#000000" width="116" x="-161.75" y="497"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>ANNWrapper</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#b9e0a5" height="45" rx="6.75" ry="6.75" stroke="#000000" width="120" x="-10" y="495"></rect><rect fill="#b9e0a5" height="41" rx="6.15" ry="6.15" stroke="#000000" width="116" x="-8" y="497"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>TFSerWrapper</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><rect fill="#b9e0a5" height="45" rx="6.75" ry="6.75" stroke="#000000" width="120" x="140" y="495"></rect><rect fill="#b9e0a5" height="41" rx="6.15" ry="6.15" stroke="#000000" width="116" x="142" y="497"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>XXWrapper</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M -180 40 L -199.9 40" fill="none" stroke="white" stroke-width="11"></path><path d="M -180 40 L -199.9 40" fill="none" stroke="#000000" stroke-width="3"></path><path d="M -206.65 40 L -197.65 35.5 L -199.9 40 L -197.65 44.5 Z" fill="#000000" stroke="#000000" stroke-width="3"></path></g><g transform="translate(0.5,0.5)"><path d="M 60 140 L 30.1 140" fill="none" stroke="white" stroke-width="11"></path><path d="M 60 140 L 30.1 140" fill="none" stroke="#000000" stroke-width="3"></path><path d="M 23.35 140 L 32.35 135.5 L 30.1 140 L 32.35 144.5 Z" fill="#000000" stroke="#000000" stroke-width="3"></path></g><g><path d="M 198.75 400 L 198.9 388.24" fill="none" stroke="white" stroke-width="10"></path><path d="M 198.75 400 L 198.9 388.24" fill="none" stroke="#000000" stroke-width="2"></path><path d="M 198.97 382.24 L 202.87 390.29 L 198.9 388.24 L 194.87 390.19 Z" fill="#000000" stroke="#000000" stroke-width="2"></path></g><g transform="translate(0.5,0.5)"><path d="M -25 480 L -25 460.1" fill="none" stroke="white" stroke-width="11"></path><path d="M -25 480 L -25 460.1" fill="none" stroke="#000000" stroke-width="3"></path><path d="M -25 453.35 L -20.5 462.35 L -25 460.1 L -29.5 462.35 Z" fill="#000000" stroke="#000000" stroke-width="3"></path></g><g transform="translate(0.5,0.5)"><rect fill="#007fff" height="210" rx="21" ry="21" stroke="#000000" width="140" x="-360" y="130"></rect><rect fill="#007fff" height="206" rx="20.4" ry="20.4" stroke="#000000" width="136" x="-358" y="132"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>ManagerConfigs</div></div></div></foreignobject></g></g><g transform="translate(0.5,0.5)"><path d="M -290 130 L -290 100.1" fill="none" stroke="white" stroke-width="11"></path><path d="M -290 130 L -290 100.1" fill="none" stroke="#000000" stroke-width="3"></path><path d="M -290 93.35 L -285.5 102.35 L -290 100.1 L -294.5 102.35 Z" fill="#000000" stroke="#000000" stroke-width="3"></path></g><g transform="translate(0.5,0.5)"><rect fill="#f5f5f5" height="110" stroke="#666666" width="80" x="-330" y="180"></rect></g><g><g><foreignobject height="100%" width="100%"><div><div><div>- 召回列表<br/>     - 框架类型<br/>     - 逻辑DAG<br/>     - 算法参数</div></div></div></foreignobject></g></g></g><g></g><g></g></g></svg><div><div><div></div></div><div><div></div></div></div>[图片未保存到本地]</div>

</div>
         <p></p><p><br/></p><p>附工程侧设计图：</p><p> <img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/6614f1cf427e34fea5c9.png"/></p><h2>2. 配置结构设计说明</h2><h3>2.1. Manger configure</h3><p>1.管理多个trigger，Trigger的启用和停用，以及多种版本(实验)的配置的切换。</p><p>2.【暂缓】多个召回Triiger结果聚合, Rerange操作.（这里可以接OP算子）</p><p>配置项模版如下：</p><div><div><p><strong>global</strong>：</p><p>-- version：1.0.1</p><p>-- comment：ab_xxx_config</p><p><strong>triggers/DAGs</strong>:</p><p>-- trigger_1:                                                 //trigger id，具体召回配置的id标识</p><ul><li>type : [I2I/U2I ....]                               //召回框架类型</li><li>name: [ICF/SLIM/TwoTower..]           //召回名，可选</li><li>policy_id: 1000001                            //对应召回算法管理平台里的算法id</li><li>version: 1.0.0</li><li>req_num: 100                                   //返回数</li><li>config: xxx.yaml/xxx.json                  // Trigger详细配置分离出单独的多个版本的配置文件,  可以再这里自由切换</li><li>status: [ON/OFF]                              //开启or禁用 </li></ul><p>-- trigger_2:</p><ul><li>type: --</li><li>name: --</li><li>policy_id: --</li><li>config: --</li><li>version: --</li><li>req_num: 100</li><li>config: xxx.yaml/xxx.json</li><li>status:[ON/OFF]</li></ul><p><strong>plugins</strong>:（工程配置，算法通常不需要关注）</p><p>-- storages/dataaccess:</p><ul><li>redis_his_offline:<ul><li>namespace: Production</li><li>target: <a href="http://sz2837.xxx.redis.com/">sz2837.xxx.redis.com</a></li><li>prefix: xx_</li><li>auth: xxxx</li><li>timeout: xxxx</li></ul></li></ul><ul><li>service_tf:<ul><li>service_name: xxxx   </li></ul></li></ul></div></div><p>   </p><h3>2.2. Trigger Configure</h3><p>Trigger 由多个算子(OP)构成，统一输入和输出接口.</p><p>(不同算子之间可以按照配置的先后顺序依次执行，也可以添加类似index配置，来定义op执行的顺序)</p><p>配置项框架如下：</p><div><div><p><strong>global</strong>:  </p><p>-- version: 1.0.0</p><p>-- comment: xxxxx</p><p>-- type: I2I/U2I ...</p><p>-- name: xxxxx</p><p>-- policy_id: 1000001  //对应召回算法管理平台里的算法id</p><p>-- req_num: 100 // 召回截断条目</p><p><strong>ops</strong>:</p><p>-- op_recall_xx:</p><ul><li>op_type: recall/rerange/prerank ..</li><li>op_version: 1.0.0</li><li>op_name: xxxxx</li><li>op_config: op_confs/recall/op_recall_v1.json // OP详细配置分离出单独多版本的配置文件单独管理，在这里切换不同配置.</li><li>topn: 500</li></ul><p>-- op_filter_xx1:</p><ul><li>op_type:filter</li><li>op_version: 1.0.0</li><li>op_name: expo_filter_v1</li><li>op_config: op_confs/filter/op_filter_expo_v1.json</li></ul><p>-- op_filter_xx2:</p><p>.......</p><p>-- op_rerange_xx1:</p><p>.....</p><p>-- <strong>op_prerank_xx1</strong>:    //单召回粗排模型截断OP</p><ul><li>..</li><li>..</li><li>topn:200</li></ul><p>.....</p><p>-- op_filter_xx3:</p><p>.....</p><p><strong>plugins</strong>:</p><p>同Manager</p></div></div><p><br/></p><h3>2.3. <strong>OP Configure</strong></h3><p>算子(OP)配置根据不同算子自由定义，算法直接的差异由不同OP来体现，现有逻辑不满足的，可以自定义OP。</p><p>OP的configure为具体的算法、策略相关的参数配置，参考2.2节中的ops内的op具体节点。</p><h3>2.4. 补充说明</h3><p>文档中属性，分类以及配置文件格式根据实际实现时自由调整，文档中只描述大体的结构和配置形式.</p><h2>3. 使用说明</h2><h3>3.1. 如何管理配置</h3><p>上述的配置可以有两个层次的接口方式，需要看下工程侧的支持能力。</p><ol><li>朴素的config文件，修改后需要TriggerManager服务重新加载config才能生效。</li><li>平台后台对ManagerConfig和TriggerConfigs提供UI接口进行调整，并推送更新到TriggerManager服务。类似现在用的灵犀后台原来的召回模块管理。</li></ol><h3>3.2. 如何跟TAB联通进行实验</h3><ol><li>Manager和Trigger以及算子的配置作为基线配置</li><li>需要实验都Diff部分在TAB实验上进行定义</li><li>TriggerManger根据流量实验拿到都diff部分跟base配置进行merge。</li></ol><h3>3.3. 如何使用框架上线和管理召回</h3><p>常用的Trigger先抽象出来比如I2I召回框架，画像召回框架，热门召回框架，ANN召回框架，只需要新建配置、修改配置就能实现召回服务上线。也提供自定义OP用来实现一些业务策略相关的trigger。</p><p>也即可以提供两个层次的使用方式：</p><ol><li>初阶用户，在现有预置框架上，通过增加TriggerConfig和修改ManagerConfig来实现召回上线和修改。</li><li>高阶用户，除了修改配置外，还会对Trigger内的DAG的重新定义，DAG的算子Node的重新开发，来形成更具自由度的算法策略。</li></ol><h2>4. 工程说明</h2><h3>4.1. 技术框架</h3><p>工程侧采用的是golang来开发，采用微服务架构。</p><p>召回服务整体由TriggerManager服务和一组TriggerService构成。</p><p>TriggerManger跟Logic调度服务交互作为召回的整体出入口，且并发请求一组TriggerService获取多路召回结果，汇总返回给调度服务。</p><h3>4.2. 开发现状</h3><p>已有：目前已经有I2ITrigger。可以参考：[内部或本地链接已移除]，以及附件“基于DAG框架的召回模式开发.pptx”</p><p>待开发：TriggerManager服务，以及I2I以外的服务框架。</p><p>期望时间节点：</p><ul><li>11.2~11.6  线上框架、召回服务OP，线下召回数据同时开发，完成i2i、u2i倒排式、通用式召回；</li><li>11.9~11.13 线上线下联调开发，支持MVP版本打通上线；</li><li>11.16~11.30 u2i predictor+ann类召回完成开发。</li></ul><p><br/></p><p>
</p><div>
<div>
<fieldset>




</fieldset>
<table>
<thead>
<tr>
<th> </th>
<th> 文件
</th>
<th> 已修改
</th>
</tr>
</thead>
<tbody>
<tr>
<td>
 
</td>
<td>
 Powerpoint 文件 
                        基于DAG框架的召回模式开发.pptx
                    
</td>
<td>
十月 29, 2020
by
wimguo(郭卫敏)<i></i> </td>
</tr>
<tr>
<td> </td>
<td colspan="2">
<div> </div>
<p>标签</p>
<div>
<div>
<ul>
<li>
            无标签
        </li>
<li>

编辑标签

</li>
</ul>
</div>
</div>
<div>
Preview
查看
在 Office 中编辑
属性
删除
</div>
</td>
</tr>
<tr>
<td>
 
</td>
<td>
文件 
                        召回service结构设计
                    
draw.io diagram
</td>
<td>
十月 30, 2020
by
wimguo(郭卫敏)<i></i> </td>
</tr>
<tr>
<td> </td>
<td colspan="2">
<p>标签</p>
<div>
<div>
<ul>
<li>drawio</li>
<li>

编辑标签

</li>
</ul>
</div>
</div>
<div>
Preview
View
属性
删除
</div>
</td>
</tr>
<tr>
<td>
 
</td>
<td>
PNG文件 
                        召回service结构设计.png
                    
召回service结构设计 exported to image
</td>
<td>
十月 30, 2020
by
wimguo(郭卫敏)<i></i> </td>
</tr>
<tr>
<td> </td>
<td colspan="2">
<div> </div>
<p>标签</p>
<div>
<div>
<ul>
<li>
            无标签
        </li>
<li>

编辑标签

</li>
</ul>
</div>
</div>
<div>
Preview
属性
删除
</div>
</td>
</tr>
<tr>
<td>
 
</td>
<td>
PNG文件 
                        image2020-10-30_15-36-30.png
                    
</td>
<td>
十月 30, 2020
by
wimguo(郭卫敏)<i></i> </td>
</tr>
<tr>
<td> </td>
<td colspan="2">
<div> </div>
<p>标签</p>
<div>
<div>
<ul>
<li>
            无标签
        </li>
<li>

编辑标签

</li>
</ul>
</div>
</div>
<div>
Preview
属性
删除
</div>
</td>
</tr>
</tbody>
</table>
</div>
<div>
<div>
<li>
<div> </div>
拖放上传或 浏览文件
<img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/d3e3944d4649450dee66.gif"/>
</li>

</div>
</div>
<div>
下载全部
</div>
</div>
<p></p><p><br/></p>
<div>

<div>
<div><div><ul><li>1. 模块结构</li><li>1.1. Manager</li><li>1.2. Trigger</li><li>1.3. OP</li><li>1.4. Plugin</li><li>2. 配置结构设计说明</li><li>2.1. Manger configure</li><li>2.2. Trigger Configure</li><li>2.3. OP Configure</li><li>2.4. 补充说明</li><li>3. 使用说明</li><li>3.1. 如何管理配置</li><li>3.2. 如何跟TAB联通进行实验</li><li>3.3. 如何使用框架上线和管理召回</li><li>4. 工程说明</li><li>4.1. 技术框架</li><li>4.2. 开发现状</li></ul></div></div>
<div>
目录
<img alt="图示" loading="lazy" src="/logbook/images/algorithm-platform/184a14cd60e0997045f5.png"/>
</div>
</div>

</div>
{% endraw %}
