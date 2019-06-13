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


