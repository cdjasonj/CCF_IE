import json
import numpy as np
from copy import deepcopy
import io
from _data_process import do_clean_515,get_objs


def split_chupingongsi( objs ):
    cc = 0
    index = []
    count = 0
    for idx,obj in enumerate(objs):
        temp_spos = []
        for spo in obj['spo_list']:
            if '、' in spo['object'] and spo['predicate'] == '出品公司':
                new_objects = spo['object'].split('、')
                for ob in new_objects:
                    new_spo = deepcopy(spo)
                    new_spo['object'] = ob
                    temp_spos.append(new_spo)
                    count+=1
                    # print(new_spo)
                # print(obj['text'])
                # print("-")
                cc+=1
                index.append(idx)
            else:
                temp_spos.append(spo)
        obj['spo_list'] = temp_spos
    print('本次共清理错误出品公司数据{}条',cc)
    print(count)
    return index


def split_renwu( objs ):
    cc = 0
    index = []
    count = 0
    for idx,obj in enumerate(objs):
        temp_spos = []
        for spo in obj['spo_list']:
            if '、' in spo['object'] and spo['predicate'] in ['主演','创始人','嘉宾','作曲','作者','主角','作词','歌手','编剧','制片人','导演','']:
                new_objects = spo['object'].split('、')
                for ob in new_objects:
                    new_spo = deepcopy(spo)
                    new_spo['object'] = ob
                    temp_spos.append(new_spo)
                    # print(new_spo)
                    count+=1
                # print(obj['text'])
                # print('-')
                cc+=1
                index.append(idx)
                obj['spo_list'] = temp_spos
            else:
                temp_spos.append(spo)
    print('本次共清理错误人物数据{}条',cc)
    print(count)
    return index

#查看spo用 sub,obj空格开头结尾的
def find_wrong_spo1(result):
    count = 0
    index = []
    for idx,data in enumerate(result):
        spo_list = data['spo_list']
        temp_spo = []
        for spo in spo_list:
            if spo['object'] != '' and spo['subject'] != '':
                if spo['object'][0] == ' ' and spo['subject'][0] != ' ':
                    new_spo = deepcopy(spo)
                    new_spo['object'] = spo['object'][1:-1]
                    temp_spo.append(new_spo)
                    # print(new_spo)
                    # print(data['text'])
                    # print('-')
                    count+=1
                elif spo['subject'][0] == ' ' and spo['object'][0] != ' ':
                    new_spo = deepcopy(spo)
                    new_spo['subject'] = spo['subject'][1:-1]
                    temp_spo.append(new_spo)
                    # print(new_spo)
                    # print(data['text'])
                    # print('-')
                    count+=1
                elif spo['subject'][0] == ' ' and spo['object'][0] == ' ':
                    new_spo = deepcopy(spo)
                    new_spo['subject'] = spo['subject'][1:-1]
                    new_spo['object'] = spo['object'][1:-1]
                    temp_spo.append(new_spo)
                    count+=1
                    # print(new_spo)
                    # print(data['text'])
                    # print('-')
                else:
                    temp_spo.append(spo)

        if temp_spo != spo_list:
            index.append(idx)
        data['spo_list'] = temp_spo
    print('一共修复subject,object开头为空格的样本{}条,spo{}个'.format(len(index),count))
    return index

def find_wrong_spo1_(result):
    #去除尾部未空格的情况
    count = 0
    index = []
    for idx,data in enumerate(result):
        spo_list = data['spo_list']
        temp_spo = []
        for spo in spo_list:
            if spo['object'] != '' and spo['subject'] != '':
                if spo['object'][-1] == ' ' and spo['subject'][-1] != ' ':
                    new_spo = deepcopy(spo)
                    new_spo['object'] = spo['object'][0:-1]
                    temp_spo.append(new_spo)
                    # print(new_spo)
                    # print(data['text'])
                    # print('-')
                    count+=1
                elif spo['subject'][-1] == ' ' and spo['object'][-1] != ' ':
                    new_spo = deepcopy(spo)
                    new_spo['subject'] = spo['subject'][0:-1]
                    temp_spo.append(new_spo)
                    # print(new_spo)
                    # print(data['text'])
                    # print('-')
                    count+=1
                elif spo['subject'][-1] == ' ' and spo['object'][-1] == ' ':
                    new_spo = deepcopy(spo)
                    new_spo['subject'] = spo['subject'][0:-1]
                    new_spo['object'] = spo['object'][0:-1]
                    temp_spo.append(new_spo)
                    # print(new_spo)
                    # print(data['text'])
                    # print('-')
                    count+=1
                else:
                    temp_spo.append(spo)
        if temp_spo != spo_list:
            index.append(idx)
        data['spo_list'] = temp_spo
    print('一共修复subject,object结尾为空格的样本{}条,spo{}个'.format(len(index),count))
    return index

# 作词作曲 ，作曲标漏，做词标漏
def find_wrong_spo2(result):
    index = []
    count = []
    for idx, data in enumerate(result):
        flag = 0
        spo_list = data["spo_list"]
        predicate = []
        temp_spo = []
        for spo in spo_list:
            predicate.append(spo['predicate'])

        if '作词作曲' in data['text'] or '作词、作曲' in data['text'] or '作曲作词' in data['text'] or '作曲、作词' in data['text'] or '':

            if '作曲' in predicate and '作词' not in predicate:
                temp_spo = spo_list
                # 找到作曲spo的subject 和object
                for spo in spo_list:
                    if spo['predicate'] == '作词':
                        new_spo = {}
                        new_spo['object'] = spo['object']
                        new_spo['object_type'] = 'xx'
                        new_spo['predicate'] = '作词'
                        new_spo['subject'] = spo['subject']
                        new_spo['subject_type'] = 'xx'
                        # print(new_spo)
                        # print(data['text'])
                        # print('-')
                        temp_spo.append(new_spo)
                        flag = 1
                        break

            elif '作词' in predicate and '作曲' not in predicate:
                temp_spo = spo_list
                # 找到作词spo的 subject和object
                for spo in spo_list:
                    if spo['predicate'] == '作词':
                        new_spo = {}
                        new_spo['object'] = spo['object']
                        new_spo['object_type'] = 'xx'
                        new_spo['predicate'] = '作曲'
                        new_spo['subject'] = spo['subject']
                        new_spo['subject_type'] = 'xx'
                        # print(new_spo)
                        # print(data['text'])
                        # print('-')
                        temp_spo.append(new_spo)
                        flag = 1
                        break
        if flag == 1:
            index.append(idx)
    print('作词作曲修复{}条spo'.format(len(index)))
    return index
#处理每条将本，spo求set
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

#把train里面作者，连载的连载网站做成字典.
def find_dic1(train_data):
    keys = []
    for data in train_data:
        spo_list = data['spo_list']
        predicate = {}
        for spo in spo_list:
            predicate[spo[1]] = spo[2]
        if '作者' in data['text'] and '连载于' in data['text']:
            if '作者' in predicate and '连载网站' in predicate:
                keys.append(predicate['连载网站'])
    keys = list(set(keys))
    return keys

def _find_obj(keys,text):
    #用text和keys，定位文中的object
    #如果有多个key，在text中出现，取len(key)最大的那一个作为sub返回
    maxlen = 0
    obj = ''
    for key in keys:
        if key in text:
            if len(key)>maxlen:
                maxlen = len(key)
                obj = key
    return obj

#作者，连载于同时出现,但是连载网站漏标，利用作者和连载网站标记同一个
def find_wrong_spo3(result,keys):
    index = []
    for idx,data in enumerate(result):
        flag =0
        spo_list = data['spo_list']
        predicate =  [spo['predicate'] for spo in spo_list]
        if '连载于' in data['text'] and '作者' in data['text']:
            if '连载网站' not in predicate and '作者' in predicate:
                temp_spo = spo_list
                for spo in spo_list:
                    if spo['predicate'] == '作者':
                        new_spo = {}
                        obj = _find_obj(keys,data['text'])
                        if obj :
                            new_spo['object'] = obj
                            new_spo['object_type'] = 'xx'
                            new_spo['predicate'] = '连载网站'
                            new_spo['subject'] = spo['subject']
                            new_spo['subject_type'] = 'xx'
                            temp_spo.append(new_spo)
                            print(new_spo)
                            print(data['text'])
                            print('-')
                            index.append(idx)
                        break
    print('一共修复连载网站{}条'.format(len(index)))
    return index

def find_wrong_spo4(result):
    index = []
    for idx,data in enumerate(result):
        spo_list = data['spo_list']
        predicate =  [spo['predicate'] for  spo in spo_list]
        if '同名专辑' in data['text'] :
            if ('歌手' in predicate or '作曲' in predicate or '作词' in predicate) and '所属专辑' not in predicate:
                temp_spo = spo_list
                for spo in spo_list:
                    if spo['predicate'] == '歌手' or spo['predicate'] == '作词' or spo['predicate'] == '作曲':
                        new_spo = {}
                        new_spo['object'] = spo['subject']
                        new_spo['object_type'] = 'xx'
                        new_spo['predicate'] = '所属专辑'
                        new_spo['subject'] = spo['subject']
                        new_spo['subject_type'] = 'xx'
                        # print(new_spo)
                        # print(data['text'])
                        # print('-')
                        temp_spo.append(new_spo)
                        index.append(idx)
                        break
    print('一共修所属专辑{}条'.format(len(index)))
    return index


def find_dic3(train_data):
    # 得到出品公司的list
    keys = []
    for data in train_data:
        spo_list = data['spo_list']
        for spo in spo_list:
            if spo[1] == '出品公司':
                keys.append(spo[2])
    return list(set(keys))

def _get_max_len_dict(kk):
    temp_list = []
    for idx, k1 in enumerate(kk):
        max_len_str = k1
        for idx2, k2 in enumerate(kk, idx):
            if max_len_str in k2 and len(k2) > len(max_len_str):
                max_len_str = k2
        temp_list.append(max_len_str)
    return list(set(temp_list))


def _find_obj3(keys, text):
    # 根据keys得到文中可能出现的object
    objs = []
    for key in keys:
        if key in text:
            objs.append(key)

    return _get_max_len_dict(objs)

def _split_chupingongsi(objs):
    cc = 0
    index = []
    count = 0
    for idx, obj in enumerate(objs):
        temp_spos = []
        for spo in obj['spo_list']:
            if '、' in spo[2] and spo[1] == '出品公司':
                new_objects = spo[2].split('、')
                for ob in new_objects:
                    new_spo = deepcopy(spo)
                    new_spo[2] = ob
                    temp_spos.append(new_spo)
                    count += 1
                    # print(new_spo)
                    # print(obj['text'])
                    # print('-')
                cc += 1
                index.append(idx)
            else:
                temp_spos.append(spo)
        obj['spo_list'] = temp_spos
    # print('本次共清理错误出品公司数据{}条', cc)
    # print(count)
    return index

def find_wrong_spo6(result, keys):
    # 利用主演确定subject,用key确定object
    index = []
    for idx, data in enumerate(result):
        spo_list = data['spo_list']
        predicate = [spo['predicate'] for spo in spo_list]
        if '联合出品' in data['text']:
            if '出品公司' not in predicate and '主演' in predicate:
                temp_spo = spo_list
                for spo in spo_list:
                    if spo['predicate'] == '主演':
                        objs = _find_obj3(keys, data['text'])  # objs所有可能的出品公司
                        if objs:
                            for obj in objs:
                                new_spo = {}
                                new_spo['object'] = obj
                                new_spo['object_type'] = 'xx'
                                new_spo['predicate'] = '出品公司'
                                new_spo['subject'] = spo['subject']
                                new_spo['subject_type'] = 'xx'
                                temp_spo.append(new_spo)
                                print(new_spo)
                                print(data['text'])
                                print('-')
                                index.append(idx)
                        break

    print('一共修出品公司{}条'.format(len(index)))
    return index

def _find_obj4(keys,text):
    #返回最大长度的出品公司，保证截取的完整性
    maxlen = 0
    obj = ''
    for key in keys:
        if key in text:
            if len(key)>maxlen:
                maxlen = len(key)
                obj = key
    return obj

def find_wrong_spo7(result,keys):
    index = []
    for idx,data in enumerate(result):
        spo_list = data['spo_list']
        predicate =  [spo['predicate'] for  spo in spo_list]
        if '出品' in data['text']:
            if '主演' in predicate and '出品公司' not in predicate:
                temp_spo = spo_list
                for spo in spo_list:
                    if spo['predicate'] == '主演':
                        obj = _find_obj4(keys,data['text'])
                        if obj:
                            new_spo = {}
                            new_spo['object'] = obj
                            new_spo['object_type'] = 'xx'
                            new_spo['predicate'] = '出品公司'
                            new_spo['subject'] = spo['subject']
                            new_spo['subject_type'] = 'xx'
                            temp_spo.append(new_spo)
                            print(new_spo)
                            print(data['text'])
                            print('-')
                            index.append(idx)
                            break
    print('一共修复出品公司{}条'.format(len(index)))
    return index


def add_spo( obj , sub ,  ob , pred ):
    newspo = {}
    newspo['subject'] = sub
    newspo['object'] = ob
    newspo['predicate'] = pred
    newspo['subject_type'] = 0
    newspo['object_type'] = 0
    obj['spo_list'].append(newspo)


def find_dic4(train_data):
    keys = []
    for data in train_data:
        for spo in data['spo_list']:
            if spo[1] == '总部地点':
                keys.append(spo[2])
    return keys


def _find_obj5(keys, text):
    # 测评地点类粒度可以任意
    maxlen = 0
    obj = ''
    for key in keys:
        if key in text:
            if len(key) > maxlen:
                maxlen = len(key)
                obj = key
    if obj=='中国':
        obj = ''
    return obj


def find_wrong_spo8(result, keys):
    index = []
    for idx, data in enumerate(result):
        spo_list = data['spo_list']
        predicate = [spo['predicate'] for spo in spo_list]
        if '公司' in data['text'] and (
                '总部设立于' in data['text'] or '总部位于' in data['text'] or '总部在' in data['text'] or '坐落于' in data[
            'text'] or '位于' in data['text']):
            if ('成立日期' in predicate or '注册资本' in predicate) and '总部地点' not in predicate:
                temp_spo = spo_list
                for spo in spo_list:
                    if spo['predicate'] == '成立日期' or spo['predicate'] == '注册资本':
                        obj = _find_obj5(keys, data['text'])
                        if obj:
                            new_spo = {}
                            new_spo['object'] = obj
                            new_spo['object_type'] = 'xx'
                            new_spo['predicate'] = '总部地点'
                            new_spo['subject'] = spo['subject']
                            new_spo['subject_type'] = 'xx'
                            temp_spo.append(new_spo)
                            print(new_spo)
                            print(data['text'])
                            print('-')
                            index.append(idx)
                            break
    print('总部地点修复{}条'.format(len(index)))
    return index

def _adj_sub_string(values):
    """
    传入的是字符串的list,判断是否有某个元素为另外一个元素的子串
    从而判断是否存在没截全的情况发生
    :param string_list:
    :return: boolean
    """
    flag = 0
    for i,value in enumerate(values):
        for j ,_value in enumerate(values):
            if value != _value:
                if value in _value:
                    flag = 1
    return flag

def publishing_fix(result):
    """
    处理出版社没有被截取全的情况
    :param result:
    :return:
    """
    count = 0
    for data in result:
        for spo in data['spo_list']:
            if '出版社' == spo['predicate'] and '出版社' not in spo['object']:
                if spo['object'] + '出版社' in data['text']:
                    spo['object'] = spo['object'] + '出版社'
                    count+=1
                    # print(spo)
    print('出版社一共修复{}条'.format(count))

def time_fix(result):
    """
    对data类型的时间结果进行修复
    :param result:
    :return:
    """
    count = 0
    for data in result:
        for spo in data['spo_list']:
            if '上映时间' == spo['predicate'] or '出生日期' == spo['predicate'] or '成立日期' == spo['predicate']:
                if '年' not in spo['object'] and spo['object'] + '年' in data['text']:
                    spo['object'] += '年'
                    # print(spo)
                    count+=1
    print('时间一共修复{}条'.format(count))

def space_and_superscript_process(result):
    """
    把括号里面的上标1，和空格删去
    :param result:
    :return:
    """
    special_sampls= ['+1','01','舌尖1','1-1','教师1','ko1','记1','加1','11','传说1']
    index = []
    count = 0
    for idx,data in enumerate(result):
        spo_list = data['spo_list']
        for spo in spo_list:
            object_flag = 0
            subject_flag = 0
            #清除spo里面前后的括号。
            if spo['object'] and spo['subject']:
                if spo['object'][0] == ' ':
                    spo['object'] = spo['object'][1:]
                    count+=1
                elif spo['subject'][0] == ' ':
                    spo['subject'] = spo['subject'][1:]
                    count+=1
                elif spo['object'][-1] == ' ':
                    spo['object'] = spo['object'][:-1]
                    count+=1
                elif spo['subject'][-1] == ' ':
                    spo['subject'] = spo['subject'][:-1]
                    count+=1
                #清除括号的下标
                for samples in special_sampls:
                    if samples in spo['object']:
                        object_flag = 1
                        break
                if spo['predicate'] != '成立日期' and spo['predicate'] != '上映日期' and spo['predicate'] != '出生日期' :  # object是日期类的时候不做清洗
                    if object_flag == 0 and spo['object'][-1] == '1': #object 不包含special_samples里面的内容
                        spo['object'] = spo['object'][:-1]
                        count+=1
                for samples in special_sampls:
                    if samples in spo['subject']:
                        subject_flag = 1
                        break
                if subject_flag == 0 and spo['subject'][-1] == '1': #subject 不包含
                    spo['subject'] = spo['subject'][:-1]
                    count+=1
    print('括号，上标处理{}条'.format(count))


def gongsi_fix(result):
    """
    对公司后缀进行修复
    1,有限责任公司
    2，实业有限公司
    3，股份有限公司
    4，投资有限公司
    5，有限公司
    6，投资发展有限公司
    :param result:
    :return:
    """
    count = 0
    name_list = ['有限责任公司','实业有限公司','股份有限公司','投资有限公司','有限公司','投资发展有限公司']
    for data in result:
        for spo in data['spo_list']:
            if spo['predicate'] in ['董事长','成立日期','创始人']:
                for name in name_list:
                    if spo['subject'] + name in data['text']:
                        spo['subject']+= name
                        count+=1
                        print(spo)
                        print(data['text'])
                        print('-')
                        break
            elif spo['predicate'] == '出品公司':
                for name in name_list:
                    if spo['object'] + name in data['text']:
                        spo['object'] += name
                        print(spo)
                        print(data['text'])
                        print('-')
                        count+=1
                        break
    print(count)

def didian_fix(result):
    """
    1，地点截取到人
    2，地点没截取全 （市，县，区）
    :param result:
    :return:
    """
    count = 0
    for data in result:
        for spo in data['spo_list']:
            if spo['predicate'] in ['祖籍','出生地']:
                if spo['object'][-1] == '人':
                    spo['object'] = spo['object'][:-1]
                    count+=1
    for data in result:
        flag = 1
        for spo in data['spo_list']:
            if spo['predicate'] in ['祖籍','总部地点','出生地']:
                if spo['object']+'省' in data['text']:
                    spo['object']+='省'
                    count+=1
                    flag=  0
                elif spo['object']+'市' in data['text']:
                    spo['object']+='市'
                    count+=1
                    flag = 0
                elif spo['object']+'县' in data['text']:
                    spo['object']+='县'
                    count+=1
                    flag=  0
                elif spo['object']+'区' in data['text']:
                    spo['object']+='区'
                    count+=1
                    flag=0
                elif spo['object']+'镇' in data['text']:
                    spo['object']+='镇'
                    count+=1
                    flag =0
    for data in result:
        flag = 1
        for spo in data['spo_list']:
            if spo['predicate'] in ['首都','所在城市']:
                if spo['object']+'市' in data['text']:
                    spo['object']+='市'
                    count+=1
                    flag = 0
                elif spo['object']+'县' in data['text']:
                    spo['object']+='县'
                    count+=1
                    flag=  0
                elif spo['object']+'区' in data['text']:
                    spo['object']+='区'
                    count+=1
                    flag=0
                elif spo['object']+'镇' in data['text']:
                    spo['object']+='镇'
                    count+=1
                    flag =0

def renkou_fix(result):
    """
    按照官方的说法，人口数量不能带单位’人‘，这里做修复
    :param result:
    :return:
    """
    count = 0
    for data in result:
        for spo in data['spo_list']:
            if spo['predicate'] == '人口数量':
                if spo['object'][-1] == '人':
                    spo['object'] = spo['object'][:-1]
                    count+=1
                    print(data['text'])
                    print(spo)
    # print('修复')


def guoji_fix(result,or_objs):
    """
    对国籍进行修复
    :param result:
    :return:
    """
    count = 0
    for idx,data in enumerate(result):
        or_obj = or_objs[idx]
        temp_spos = []
        for spo in data['spo_list']:
            rm_flag = False
            if spo['predicate'] == '国籍' and spo['object'] =='中国':
                china_ents = [x for x in
                              filter(lambda x: x != '中国' and '中国' in x, [pos['word'] for pos in or_obj['postag']])]
                cur_text = data['text']
                for ent in china_ents:
                    cur_text = cur_text.replace(ent, '')
                if '中国' not in cur_text:
                    print(data['text'])
                    rm_flag =True
                    count+=1
            if not rm_flag:
                temp_spos.append(spo)

        data['spo_list'] = temp_spos
    print(count)

def get_ent_type(  ):
    type_dict = {}
    with open('../inputs/all_50_schemas','r',encoding='utf8') as f:
        for l in f:
            a = json.loads(l)
            t = {}
            t['subject_type']  = a['subject_type']
            t['object_type'] = a['object_type']
            type_dict[a['predicate']] = t
    return type_dict


def trans_spo_list( spo_list ):
    return [ (spo['subject'],spo['predicate'],spo['object']) for spo in spo_list ]

def retrans_spo_list( spo_list ):
    return [ { 'subject':spo[0] , 'predicate':spo[1] , 'object':spo[2] , 'subject_type':0,'bbject_type':0 } for spo in spo_list ]


def find_max_len_ent( result ):
    edit_cc = 0
    clean_cc = 0
    type_dict = get_ent_type()
    """
        针对同一对sub-predicate,多个object,并且存在字串的情况，进行清洗
        针对同一对obj-predicate,多个subject,并且存在子串的情况，进行清洗
        :param result:
        :return:index:
    """
    def find_match_ent( or_ent , ent_list ):
        temp_ent = ''
        match_cnt = 0
        for ent in ent_list:
            if or_ent in ent:
                match_cnt += 1
                if match_cnt > 1:
                    print( data['text'] , or_ent , ent_list )
                    # raise
                temp_ent = ent
        if temp_ent == '':
            # raise
            pass

        return temp_ent

    for idx,data in enumerate(result):
        ##todo 记着这里是排除了简称的
        spo_list = data['spo_list']
        ent_dict = {}
        ##查看当前有没有子串
        for spo in spo_list:
            sub_type = type_dict[spo['predicate']]['subject_type']
            ob_type = type_dict[spo['predicate']]['object_type']

            temp_sub_list = ent_dict.get(sub_type,[])
            temp_sub_list.append(spo['subject'])
            ent_dict[sub_type] = temp_sub_list

            temp_ob_list = ent_dict.get(ob_type, [])
            temp_ob_list.append( spo['object'] )
            ent_dict[ ob_type] = temp_ob_list

        spo_list = trans_spo_list(spo_list)
        or_spo_list = deepcopy(spo_list)
        for k in ent_dict:
            ent_dict[k] = _get_max_len_dict( ent_dict[k] )
        for idx,spo in enumerate(spo_list):
            sub_type = type_dict[spo[1]]['subject_type']
            ob_type = type_dict[spo[1]]['object_type']
            or_sub = spo[0]
            newsub = find_match_ent( spo[0] ,ent_dict[sub_type] )
            or_ob  = spo[2]
            newob = find_match_ent(spo[2], ent_dict[ob_type])
            if or_sub != newsub or or_ob != newob:
                edit_cc+=1
            spo_list[idx] = ( newsub,spo[1] ,newob )
        spo_list = set( spo_list )
        ##跟原来不一样的条数
        difset = set(or_spo_list) - set(spo_list)
        # for spo in difset:
            # print( spo,data['text'] , or_spo_list )
        clean_cc+=len( difset )
        data['spo_list'] = retrans_spo_list( spo_list )
    print( '当前编辑了 ',edit_cc )
    print('当前删除了 ', clean_cc)

def jy_fix(result):
    count = 0
    for data in result:
        for spo in data['spo_list']:
            if spo['predicate'] == '编剧' and spo['object'] == '金庸':
                spo['predicate'] = '作者'
                count+=1
    print(count)

def find_zj_dic(train_data,predicate):
    zj_dic = {}
    for data in train_data:
        for spo in data['spo_list']:
            if spo[1] == predicate:
                if spo[0] not in zj_dic :
                    zj_dic[spo[0]] = []
                    zj_dic[spo[0]].append(spo[2])
                else :
                    zj_dic[spo[0]].append(spo[2])

    for key,value in zj_dic.items():
        zj_dic[key] = list(set(value))
    return zj_dic

def zhujue_fix(result,dic,predicate,subject_type,object_type):
    """
    利用字典进行远程监督，对主角进行补充
    :param result:
    :param dic:
    :return:
    """
    new_data = []
    count =0
    books = list(dic.keys())
    for data in (result):
        flag = 1
        spo_list = data['spo_list']
        temp_spo_list = []
        for book in books:
            if book in data['text']:
                roles = dic[book]
                for role in roles:
                    # book和role都出现，进行补充
                    if role in data['text']:
                            temp_spo = {}
                            temp_spo['object'] = role
                            temp_spo['object_type'] = object_type
                            temp_spo['predicate'] = predicate
                            temp_spo['subject'] = book
                            temp_spo['subject_type'] = subject_type
                            if temp_spo not in spo_list:
                                data['spo_list'].append(temp_spo)
                                count+=1
    print(count)

def cd_fix(result):
    count = 0
    for data in result:
        for spo in data['spo_list']:
            if spo['predicate'] == '朝代':
                if spo['object'] +'末年' in data['text']:
                    spo['object']+='末年'
                    count+=1
                    print(spo)
                elif spo['object'] + '时期' in data['text']:
                    spo['object'] += '时期'
                    count+=1
                    print(spo)
                elif spo['object'] + '代' in data['text']:
                    spo['object'] += '代'
                    count+=1
                    print(spo)
                elif spo['object'] + '朝' in data['text']:
                    spo['object'] += '朝'
                    count+=1
                    print(spo)
    print(count)

    """
    数据处理过程
    1，将顿号没隔开的出品公司，人物隔开，
    2，将‘1’，‘ ’为结尾的so,删去
    3，最长字符串匹配，删去投票带来的误差
    4，用规则修复明显的作词，作曲应该是同时出现的样本
    5，用字典的方式修复连载网站。
    6，利用同名专辑修复填充 专辑，歌曲
    7，利用主演修复出品公司
    8，修复总部地点
    9，曾的代码部分。简称，改编自，出版社，书名号，
    10，地点，公司，人口，单位处理
    11，
    """

def result_process(result,save_file):

    train_data = json.load(open('../inputs/train_data_me.json', encoding='utf-8'))
    dev_data = json.load(open('../inputs/dev_data_me.json', encoding='utf-8'))

    train_data += dev_data
    index0 = split_chupingongsi(result)
    _= split_renwu(result)
    # 开头为空格，结尾为空格
    index1 = find_wrong_spo1(result)
    index1_ = find_wrong_spo1_(result)

    find_max_len_ent(result) #曽的清除子串噪音
    index2 = find_wrong_spo2(result) #作词作曲同时出现
    keys1 = find_dic1(train_data)
    index3 = find_wrong_spo3(result,keys1) #这里有问题，可以用截取括号的
    index4= find_wrong_spo4(result)

    # 这个出品公司先不要了，曽给挖完了
    _ = _split_chupingongsi(train_data)
    keys2 = find_dic3(train_data) #出品公司的全部object
    index5 = find_wrong_spo6(result,keys2)
    index6 = find_wrong_spo7(result,keys2)

    keys3 = find_dic4(train_data) #总部地点
    index7 = find_wrong_spo8(result,keys3)
    # add_dz2(result) #曽与的总部地点
    # add_type(result)
    # add_jiancheng2(result) #曽的简称
    # add_gbz(result)  #曽的改编自
    publishing_fix(result)#出版社
    time_fix(result) #时间
    # clean_shuminghao( result ) #曽的书名号清洗
    # remove_sszj(result)
    didian_fix(result)
    gongsi_fix(result)
    renkou_fix(result)

    # cd_fix(result) #朝代 5/19
    do_clean_515(result,get_objs('../inputs/test_data_postag.json'),get_objs('../inputs/train_data.json'),get_objs('../inputs/dev_data.json'))
    jy_fix(result)

    space_and_superscript_process(result)
    _index,final_result = final_processing(result)

    # 最终得spo数量

    count = 0
    for data in result:
        count+=len(data['spo_list'])
    print('总spo得个数为{}'.format(count))
    print(len(final_result))

    f = io.open(save_file,'w',encoding='utf-8')
    for data in result:
        f.write(json.dumps(data,ensure_ascii=False)+'\n')
    return final_result
