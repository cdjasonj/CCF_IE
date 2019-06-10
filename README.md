Environment:
-----
python 3+ tensorflow 1.10+ keras 2.2.4+ Keras-bert:0.39.0

Install
-----

```python
pip install keras-bert
pip install tqdm
```

Usage
-----
run ``` python main.py gpu_num1 gpu_num2 gpu_num3 gpu_num4 gpu_num5``` <br>
The test datasets predictions will be saved into a file called ```final_data.json ```in the``` outputs```, and the models be trained will be saved into ```ensemble_part_x.weights``` in the ```models```.

We used multiple GPUs for training and prediction, so we also specified multiple GPUS for training and forecasting in this program.  

Requirements
----
requirements.txt records the dependency packages that we run locally.
