Environment:
-----
python 3+ tensorflow 1.10+ keras 2.2.4+ 

Install
-----
我们将所使用的依赖环境已打包为 requirements.txt 
keras-bert from here https://github.com/CyberZHG/keras-bert

```python
pip install keras-bert
conda install --yes --file requirements.txt
```
Datas
----
请将以下文件放入对应文件夹<br>
1,
./inputs (原始数据存放路径) <br>
应包含以下文件：
train_data.json, dev_data.json, all_50_chemas, test_data_postag.json<br>

2,
./bert (存放预训练模型权重路径)
应包含一下文件：<br>
./bert/chinese_L-12_H-768_A-12/bert_config.json;<br>
./bert/chinese_L-12_H-768_A-12/bert_model.ckpt;<br>
./bert/chinese_L-12_H-768_A-12/vocab.txt<br>

以下是预训练权重下载地址<br>
chinese_L-12_H-768_A-12 ：https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip

Usage
-----
run ``` python main.py gpu_num1 gpu_num2 gpu_num3 gpu_num4 gpu_num5``` <br>
The test datasets predictions will be saved into a file called ```final_data.json ```in the``` outputs```, and the models be trained will be saved into ```ensemble_part_x.weights``` in the ```models```.

We used multiple GPUs for training and prediction, so we also specified multiple GPUS for training and forecasting in this program.  


baseline: https://github.com/bojone/kg-2019-baseline
----
我们在苏神baseline上的工作:<br>
1, BERT<br>
2，优化了标注方式，针对重叠关系的重新设定了多信息的标注方式<br>
3，简化了下游模型结构，尝试了self-attention和普通点乘attention<br>
4，投票方式简单集成<br>
5，规则数据后处理和预处理。<br>

参考文献：
Global Normalization of Convolutional Neural Networks for Joint Entity and Relation Classification<br>
One for All Neural Joint Modeling of Entities and Even<br>
Table ﬁlling multi-task recurrent neural network for joint entity and relation extraction<br
Joint Extraction of Entities and Relations Based on a Novel Tagging Scheme<br>
End-to-End Neural Relation Extraction with Global Optimization<br
结果
---
A榜：0.889， B榜：0.8872 , 最终B榜第五（原本第六，第四名放弃）。<br>
ps: A,B榜有差距差距的原因，是因为我不小心把几个用来集成的模型权重给用debug数据跑的模型覆盖了。。。。重新跑全部EPOCH时间又不够，就以重新跑了几个更少EPOCH的模型替代，导致重新预测效果变差，坑了。。。。
