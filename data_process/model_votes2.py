import json

result1 = []
result2 = []
result3 = []
result4 = []
result5 = []
result6 = []
result7 = []
result8 = []
result9 = []
result10 = []
result11 = []
result12 = []
result13 = []
result14 = []
result15 = []
result16 = []
result17 = []
result18 =[]
result19 = []
result20 = []
result21 = []
result22 = []
result23 = []
result24 = []
result25 = []
result26 = []
result27 = []
result28 = []
result29 = []

result  = [result1,result2,result3,result4,result5,result6,result7,result8,
           result9,result10,result11,result12,result13,result14,result15,result16,result17
           ,result18,result19,result20,result21,result22,result23,result24,result25,result26,result27,result28,result29]

for i in range(1,30):
    result_file_name = 'version1_'+str(i)+'_2.json'
    _result = result[i-1]
    with open(result_file_name,encoding='utf-8') as fr:
        for line in fr:
            _result.append(json.loads(line))

final_result = []
final_spo = []

for idx in range(len(result2)):

    spo = []
    spo_ = []
    for idx2, result_ in enumerate(result):
        spo_list = result_[idx]['spo_list']
        for _spo in spo_list:
            spo.append((_spo['object'], _spo['predicate'], _spo['subject']))
    final_spo.append(spo)

weights_spo = []
for spo in final_spo :
    temp_spo= []
    dic={}
    for _spo in spo:
        if _spo not in dic:
            dic[_spo] = 1
        else:
            dic[_spo] +=1
    for key,value in dic.items():
        if value >=7:
            temp_spo.append(key)
    weights_spo.append(temp_spo)
count = 0
for spo in weights_spo:
        count+=len(spo)
print('一共有spo{}条'.format(count))

final_result = []

for idx,spo in enumerate(weights_spo):
    dic={}
    text = result2[idx]['text']
    dic['text'] = text
    spo_list = []
    for _spo in spo:
        spo_dic = {}
        spo_dic['object'] = _spo[0]
        spo_dic['object_type'] = 'xx'
        spo_dic['predicate'] = _spo[1]
        spo_dic['subject'] = _spo[2]
        spo_dic['subject_type'] = 'xx'
        spo_list.append(spo_dic)
    dic['spo_list'] = spo_list
    final_result.append(dic)

import io
f = io.open('new_model_29_7votes_{}.json'.format(count),'w',encoding='utf-8')
for data in final_result:
    f.write(json.dumps(data,ensure_ascii=False)+'\n')