import json

def vote_result(save_result_path):
    result0 = []
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
    result18 = []
    result19 = []
    result20 = []
    result21 = []
    result22 = []
    result23 = []
    result24= []
    result25 = []
    result26 = []
    result27 = []
    result28 = []
    result29 = []
    result30 = []
    result31 = []
    result32 = []
    result33 = []
    result34 = []
    result35 = []
    result36 = []
    result37 = []
    result38 = []
    result39 = []
    result40 = []
    result41 = []
    result42 = []
    result43 = []
    result44 = []

    result = [result0,result1,result2,result3,result4,result5,result6,result7,result8,result9,result10,result11,result12,result13,result14,result15,result16
             ,result17,result18,result19,result20,result21,result22,result23,result24,result25,result26,result27,result28,result29,result30,
             result31,result32,result33,result34,result35,result36,result37,result38,result39,result40,result41,result42,result43,result44]


    for i in range(45):
        # i : 0  - 44
        result_file_name = 'outputs/test_2_'+str(i)+'.json'
        _result = result[i]
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
            if value >= 9:
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
    f = io.open(save_result_path,'w',encoding='utf-8')
    for data in final_result:
        f.write(json.dumps(data,ensure_ascii=False)+'\n')

    return final_result
