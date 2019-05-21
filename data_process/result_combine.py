"""
在这里,把new_model和result的导演，演员，作曲，作词，结合。
"""
import json
import numpy as np
import io

def final_processing(result):
    final_result = []
    index = []
    for idx,data in enumerate(result):
        temp_spo= []
        spo_list = data['spo_list']
        for spo in spo_list:
            temp_spo.append((spo['object'],spo['predicate'],spo['subject']))
        if len(data['spo_list']) != len(list(set(temp_spo))): #spo中有重复得出现
            new_data = {}
            new_data['text']  = data['text']
            temp_spo_list = []
            for spo in list(set(temp_spo)):
                dic = {}
                dic['object'] = spo[0]
                dic['object_type'] = 'xx'
                dic['predicate'] = spo[1]
                dic['subject'] = spo[2]
                dic['subject_type'] = 'xx'
                temp_spo_list.append(dic)
            new_data['spo_list'] = temp_spo_list
            final_result.append(new_data)
            index.append(idx)
        else:
            final_result.append(data)
    return index,final_result

# 比较二者作曲-歌手 编剧-导演的差异
import sys
def compareZB(source, target,file_name):
    s = open(source, 'r', encoding='utf-8')
    t = open(target, 'r', encoding='utf-8')
    # s = source
    # t = target
    new_f = open(file_name, 'w', encoding='utf-8')
    s_lines = s.readlines()
    t_lines = t.readlines()
    count = 0
    for s_sample, t_sample in zip(s_lines, t_lines):
        _s, _t = json.loads(s_sample), json.loads(t_sample)
        s_spo = _s['spo_list']
        t_spo = _t['spo_list']
#         print (s_spo)
#         print(t_spo)
#         sys.exit(0)
        # 不管源文件是否存在 作曲、歌手、编剧、导演，都将目标中的该部分内容加入到其中（去重）。
        tmp = []
        for t_s in t_spo:
            if t_s['predicate'] in ['作曲', '歌手', '编剧', '导演','作词']:
                tmp.append(t_s)
        for t_s in tmp:
            if t_s not in s_spo:
                count += 1
                s_spo.append(t_s)
        new_dict = {'text':_s['text'], 'spo_list':s_spo}
        new_f.write(json.dumps(new_dict, ensure_ascii=False)+'\n')
    print ('最终添加了{}个'.format(str(count)))
    new_f.close()

    # 比较二者作曲-歌手 编剧-导演的差异
# file_name = 'D:/combine_data.json'
# source = 'D:/final_result_5_13_8votes_45_fix23960.json'
# target = 'D:/new_model_29_7votes_fix_23988.json'
# compareZB(source, target)
