import json
from data_process import result_process
from result_combine import compareZB

source_result = []
with open('../outputs/final_result_B_8votes_45.json.json', 'r', encoding='utf-8') as fr:
    for line in fr:
        source_result.append(json.loads(line))

tartget_result = []
with open('../outputs/new_model_30_7votes.json','r',encoding='utf-8') as fr:
    for line in fr:
        tartget_result.append(json.loads(line))

source_file = '../outputs/result1.json'
tartget_file = '../outputs/result2.json'

source_result = result_process(source_result,source_file)
tartget_result = result_process(tartget_result,tartget_file)

compareZB(source_file,tartget_file,'../outputs/combine_data.json')

combine_data = []
with open('../outputs/combine_data.json','r',encoding='utf-8') as fr:
    for line in fr:
        combine_data.append(json.loads(line))

combine_data = result_process(combine_data,'../outputs/combine_data.json')

count = 0
for data in combine_data:
    count += len(data['spo_list'])
print('总spo得个数为{}'.format(count))
print(len(combine_data))

import io
f = io.open('../outputs/final_test_B_{}_.json'.format(count), 'w', encoding='utf-8')
for data in combine_data:
    f.write(json.dumps(data, ensure_ascii=False) + '\n')
