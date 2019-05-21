import json
from data_process import result_process
from result_combine import compareZB

source_result = []
with open('D:/final_result_B_5_16_251226_9votes_45.json', 'r', encoding='utf-8') as fr:
    for line in fr:
        source_result.append(json.loads(line))

tartget_result = []
with open('D:/new_model_29_7votes_249278.json','r',encoding='utf-8') as fr:
    for line in fr:
        tartget_result.append(json.loads(line))

source_file = 'D:/result1.json'
tartget_file = 'D:/result2.json'

source_result = result_process(source_result,source_file)
tartget_result = result_process(tartget_result,tartget_file)

compareZB(source_file,tartget_file,'D:/combine_data.json')

combine_data = []
with open('D:/combine_data.json','r',encoding='utf-8') as fr:
    for line in fr:
        combine_data.append(json.loads(line))

combine_data = result_process(combine_data,'D:/combine_data.json')

count = 0
for data in combine_data:
    count += len(data['spo_list'])
print('总spo得个数为{}'.format(count))
print(len(combine_data))

import io
f = io.open('D:/final_test_B_{}_.json'.format(count), 'w', encoding='utf-8')
for data in combine_data:
    f.write(json.dumps(data, ensure_ascii=False) + '\n')
