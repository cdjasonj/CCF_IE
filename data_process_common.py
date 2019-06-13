
import codecs
import json
import sys
from copy import deepcopy

from tqdm import tqdm

def zczb_cas_func( text , spo ):
    return not spo['object'] == '人民币'

def cbs_cas_func( text , spo ):
    cbs_id = text.find(spo['object'])
    if text[cbs_id-3:cbs_id] == '作者是' or text[cbs_id-4:cbs_id] == '作者是《':
        return False
    return True

def jc_cas_func( text , spo ):
    if spo['object'] == '集团' or spo['object'] == '公司':
        return False
    return True

def sszj_cas_func( text , spo ):
    #收录，同名
    if '收录' in text or '同名' in text:
        if spo['object'] == spo['subject'] and text.count(spo['object']) == 1:
            return False
        else:
            return  True
    else:
        return False

def is_lsrw(spo_list):
    for spo in spo_list:
        if spo['subject_type'] == '历史人物' or spo['object_type'] == '历史人物':
            return True
    return False
def contain_zh( obj ):
    if obj['text'].count('号') == 1 and '谥号' not in obj['text'] and obj['text'].count('字') == 1 and '、' not in obj['text'] and '文件' not in obj[
        'text'] and is_lsrw(obj['spo_list']):
        return False
    return True

def contain_zhuanji( obj ):
    if obj['text'].count('》') > 1  and obj['text'].count('《') > 1  and '专辑'  in obj['text']:
        return False
    return True

# data_path = sys.argv[1]
# data_path = "E:/competionfile/信息抽取/new/sujianlin/datasets/"
def get_objs( f_input ):
    objs = []
    with open(f_input, encoding="utf8") as f:
        for l in tqdm(f):
            a = json.loads(l)
            objs.append(a)
    return objs

import regex
def check_is_all_in_shuminghao( text , shuminghao_tags , ent ):
    last_id = -1
    flag = True
    while True:
        ent_idx = text.find( ent , last_id+1  )
        if ent_idx == -1:
            break
        if shuminghao_tags[ent_idx] == 0:
            return False
        last_id =ent_idx
    return flag

def create_shuming_tags( shuminghao_start_ids , shuminghao_end_ids ,text):
    shuminghao_tags = [0] * len(text)
    for idx, i in enumerate(shuminghao_start_ids):
        j = shuminghao_end_ids[idx]
        shuminghao_tags[i+1:j] = [1]*( j-i-1 )
    return shuminghao_tags

def clean_shuminghao(objs  ):
    not_change = set(['国家','人物','Text','城市'])
    change = set(['音乐专辑', '作品', '影视作品', '电视综艺','歌曲','图书作品','网络小说','书籍',''])
    clean_count = 0
    for obj in tqdm(objs):
        ##第一步，将书名号中的空格去掉。
        temp_spos = []
        text = obj["text"]
        # text = text.replace("《《","《")
        shumings = regex.findall("(?<=《).*?(?=》)",text)
        # for sm in shumings:
        #     if ' ' in sm:
        #         text = text.replace(sm,sm.replace(" ",""))
        #         clean_count+=1
        obj["text"] = text
        shuminghao_start_ids = []
        shuminghao_end_ids = []
        for idx, c in enumerate(text):
            if c == '《':
                shuminghao_start_ids.append(idx)
            elif c == '》':
                shuminghao_end_ids.append(idx)
        shuminghao_end_ids=shuminghao_end_ids[:len(shuminghao_start_ids)]
        shuminghao_start_ids = shuminghao_start_ids[:len(shuminghao_end_ids)]
        shuminghao_tags = create_shuming_tags( shuminghao_start_ids,shuminghao_end_ids , text )
        ##对于每一个实体，判断他是否在书名号内，如果在，那么久将他替换为书名号中的内容
        for spo in obj['spo_list']:
            subject = spo["subject"]
            object  = spo["object"]
            edit=False
            if subject not in shumings and  spo["subject_type"]  in change and check_is_all_in_shuminghao(text,shuminghao_tags,subject):
                ##判断是否以被包含在其中
                for sm in shumings  :
                    if sm.find(subject) != -1 :
                        spo["subject"] = sm
                        print("s~~~~~~~", text, "\n", spo, '\n', sm, subject)
                        # clean_count += 1
                        edit=True
            if object not in shumings and  spo["object_type"] in change and check_is_all_in_shuminghao(text,shuminghao_tags,object):
                ##判断是否以被包含在其中
                for sm in shumings:
                    if sm.find(object) != -1 :
                        spo["object"] = sm
                        print("0~~~~~~~", text, "\n", spo, '\n', sm, object)
                        # clean_count += 1
                        edit=True
            if edit:
                clean_count+=1
            # scheck_result = check_is_in_shuminghao( text , shuminghao_start_ids , shuminghao_end_ids , subject  )
            # ocheck_result = check_is_in_shuminghao(text, shuminghao_start_ids, shuminghao_end_ids, object)
            # if scheck_result is not None and scheck_result != spo["subject"] and  spo["subject_type"] not in not_change :
            #     spo["subject"] = scheck_result
            #     print("s~~~~~~~", text, "\n", spo, '\n',scheck_result,subject)
            #     clean_count += 1
            # if ocheck_result is not None and  ocheck_result != spo["object"] and  spo["object_type"] not in not_change:
            #     spo["object"] = ocheck_result
            #     print("o~~~~~~~",text,"\n", spo,'\n', ocheck_result, object)
            #     clean_count+=1
            ##先找一下有没有和书名号全匹配的，如果有就跳过

            ##如果没有，
    print("~~~~~clean count",clean_count)

def clean_husband( objs ):
    for obj in tqdm(objs):
        temp_spos = []
        for spo in obj['spo_list']:
            if spo['predicate'] == '丈夫':
                temp_spo = {}
                temp_spo['predicate'] = '妻子'
                temp_spo['subject'] = spo['object']
                temp_spo['object'] = spo['subject']
                temp_spo['object_type'] = '人物'
                temp_spo['subject_type'] = '人物'
                addFlag=True
                for spo in obj['spo_list']:
                    if temp_spo['predicate'] == spo['predicate'] and temp_spo['subject'] == spo['subject'] and  temp_spo['object'] == spo['object']:
                        addFlag=False
                        break
                if addFlag:
                    temp_spos.append( temp_spo )
            else:
                temp_spos.append( spo )
        obj['spo_list'] = temp_spos

def save_objs( objs , f_out ):
    with codecs.open(f_out, 'w', encoding='utf-8') as f:
        for obj in objs:
            f.write(json.dumps(obj, ensure_ascii=False)+"\n")

def clean_schemas():
    schemas = []
    with open('inputs/all_50_schemas', encoding="utf8") as f:
        for l in tqdm(f):
            a = json.loads(l)
            if a['predicate'] != '丈夫':
                schemas.append(a)
    with open('inputs/all_50_schemas','w', encoding="utf8") as f:
        for sc in schemas:
            f.write(json.dumps(sc, ensure_ascii=False)+'\n')

def clean_empty_spo_list(objs):
    af_objs = []
    clean_count = 0
    for obj in objs:
        if len(obj["spo_list"]) != 0:
            af_objs.append( obj )
        else:
            clean_count+=1
    print( "clean_empty_spo_list",clean_count )
    return af_objs

count = 0
def clean_not_sig( objs , key_word , types , predicate ,maybe_dict , re_list , fname=None ,
                   sub_from_key_word = False,cat_end=True,re_souce_dict=None,filter_func=None,
                   cat_start=False,s_dic=None,nkws =[],stripkws=[],cas_func=None):
    global count
    wait_write=[]
    wait_force_write=[]
    errcount = 0
    tpps =set()
    filter_func = filter_func.get(predicate) if filter_func is not None else None
    for idx, obj in tqdm(enumerate(objs)):
        fg = False
        if filter_func is not None:
            if filter_func(obj) == True:
                fg = False
            else:
                fg = True
        elif type(key_word) is set:
            for k in key_word:
                if k in obj['text']:
                    fg = True
                    break
        elif key_word in obj['text']  :
            fg = True
        if fg == True:
            err = True
            subs = set()
            sub_type = ''
            for spo in obj['spo_list']:
                if spo['predicate'] == predicate:
                    err = False
                if spo['subject_type'] in types[predicate]:
                    subs.add( spo['subject'] )
                    sub_type = spo['subject_type']
                if spo['object_type'] in types[predicate]:
                    subs.add( spo['object'] )
                    sub_type = spo['object_type']
            if err:
                errcount+=1
            else:
                continue
            ##如果没找到主语并且s_dict不为空，就采用s_dict的东西
            if len( subs ) == 0 and s_dic!=None and len(s_dic.get(str(idx),[])) == 1:
                subs.add( s_dic[str(idx)][0] )
            find = False
            if err and len(subs) == 1:
                ##不仅要找到，而且还要找到匹配长度最大的
                max_sim_len = 0
                max_sim_wp = ''
                max_sim_wp_tp = ''
                for wp in maybe_dict[predicate]:
                    if wp[0] in obj['text'] and len(wp[0]) > max_sim_len :
                        max_sim_wp =wp[0]
                        max_sim_wp_tp = wp[1]
                        max_sim_len = len(wp[0])
                        find=True

                if find :
                    new_spo = {}
                    new_spo['subject'] = list(subs)[0]
                    new_spo['object'] = max_sim_wp
                    new_spo['predicate'] = predicate
                    new_spo['subject_type'] = sub_type
                    new_spo['object_type'] = max_sim_wp_tp
                    if True if cas_func is None else cas_func( obj['text'] , new_spo):
                        obj['spo_list'].append(new_spo)
                        print(obj['text'], new_spo)
                        wait_write.append(str([obj['text'], obj['spo_list'], new_spo]) + '\n')
                        count += 1
                else:
                    ##用硬匹配
                    for (s,end,start) in re_list.get(predicate,set()):
                        obstr = regex.search( s,  obj['text'] )
                        if obstr is not None:
                            obstr = str(obstr.group())
                            if start in obstr:
                                obstr = obstr[obstr.find(start) + len(start):]
                            find = True
                            break
                    if not find  and sub_from_key_word ==True:
                        min_len = 2000
                        min_str = ''
                        for s in re_souce_dict[predicate][0]:
                            cstr  = obj['text'][ obj['text'].find(s)+len(s): ]
                            if len(cstr) < min_len:
                                min_len = len(cstr)
                                min_str = cstr
                            obstr = min_str
                        find = True
                    if find == True :
                        aflag = True
                        for kw in nkws:
                            if kw in obstr:
                                aflag = False
                                break
                        for skw in stripkws:
                            obstr = obstr.strip(skw)
                        if aflag:
                            new_spo = {}
                            new_spo['subject'] = list(subs)[0]
                            if not cat_end:
                                new_spo['object'] = obstr.replace(end,'')
                            if not cat_start:
                                new_spo['object'] = obstr.replace(start,'')
                            if cat_end:
                                new_spo['object'] = obstr + end

                            else:
                                new_spo['object'] = obstr
                            if new_spo['object'].strip() != '' and ( True if cas_func is None else cas_func( obj['text'] , new_spo ) ) :
                                new_spo['predicate'] = predicate
                                new_spo['subject_type'] = sub_type
                                new_spo['object_type'] = '学校'
                                obj['spo_list'].append(new_spo)
                                print( obj['text'] , new_spo )
                                wait_force_write.append(str([obj['text'], obj['spo_list'], new_spo]) + '\n')
                                count += 1
            if not find:
                for spo in obj['spo_list']:
                    tpps.add(spo['subject_type'])
                    tpps.add(spo['object_type'])
                # print( obj['text'],obj['spo_list'],s_dic.get(str(idx))  )
    if fname == None:
        fname=key_word
    with open( fname+'.txt','w' ,encoding='utf8') as f:
        f.writelines(wait_write)
    with open(fname + 're.txt', 'w',encoding='utf8') as f:
        f.writelines(wait_force_write)
    print('clean count',count,errcount,tpps)

def get_maybe_objs(train_objs, dev_objs, maybe_sub_dict_save_path=None,maybe_obj_dict_save_path=None):
    maybe_dict = {}
    maybe_sub_dict ={}
    maybe_obj_dict ={}
    entity_dict = {}
    maybe_type_dict ={}
    maybe_dict_without_tp = {}
    objs = train_objs+dev_objs
    for i,obj in tqdm(enumerate(objs)):
        for spo in obj['spo_list']:
            try:
                if '出版社' in obj['text']:
                    if '出版社' not in spo['object'] and spo['predicate'] == '出版社':
                        if spo['object'].endswith('出版'):
                            spo['object'] = spo['object'] + '社'
                        else:
                            spo['object'] = spo['object'] + '出版社'
            except:
                print(obj,i)
                raise
            predicate = spo['predicate']
            object = spo['object']
            maybe_predicate_set = maybe_dict.get( predicate , set() )
            maybe_type_set = maybe_type_dict.get(predicate, set())
            maybe_predicate_set.add((object,spo['object_type']))
            maybe_type_set.add(spo['subject_type'])
            maybe_dict[predicate] = maybe_predicate_set
            maybe_type_dict[predicate] = maybe_type_set

            maybe_sub_set = maybe_sub_dict.get(predicate, set())
            maybe_sub_set.add(spo['subject'])
            maybe_sub_dict[predicate] = maybe_sub_set

            maybe_obj_set =  maybe_obj_dict.get( predicate , set() )
            maybe_obj_set.add( spo['object'] )
            maybe_obj_dict[predicate] = maybe_obj_set
    for k , i in maybe_dict.items():
        maybe_dict_without_tp[k] = set([i0  for ( i0 , i1  ) in i  ])

    removes = {}
    removes['毕业院校'] = (['电影学院','交通大学','大学','研究','医科大学','戏剧','省委党校研究生','省委党校研','省委党校经济管理','师范学院','云南省委党校函授学院','云南省委党校','四川省委党校函授学院',
                        '大专','师范','私塾','煤校','初中','函大','研究生','太学','省艺校','中国共产党','中国人民解放军','省委党校','中央党校','西安美院国画系'],'学校')
    removes['出版社'] = (['第1版 (2004年9月1日)出版社', '北京', 'エンターブレイン'],'出版社')
    removes['民族'] = (['匈人','陕西','四川武胜','中国','男','穿青'
                         ,'氐族','爱尔兰','英国奥金莱克人','英国','意大利','日裔','科特迪瓦'
                         ,'彝族阿细支','波兰','韩国','西班牙','古希腊','朝鲜','法国','犹太',
                      '欧亚混血儿','华人','美国','德','英格兰','七夜一族','北京','德国',
                      '尼玛','中加混血','族','菲律宾','阿拉伯','穆斯林',',汉族','汉','格鲁吉亚人',
                      '罗马尼亚','鲁国','苏格兰','日本','壮','藏','华夏族','龙族','捷克','黑龙江','汉族，','8种少数民族'], 'Text')

    removes['连载网站'] = (['中'], '网站')
    adds = {}
    type_adds = {}
    type_adds['连载网站'] = ['图书作品']
    type_adds['出版社'] = ['图书作品','书籍']
    type_adds['注册资本'] = ['机构']
    type_adds['祖籍'] = ['历史人物']
    type_adds['民族'] = ['历史人物']
    type_adds['字'] = ['历史人物']
    for k,i in type_adds.items():
        for tpadd in i:
            maybe_type_dict[k].add(tpadd)
    for k in ['系','专业']:
        temp_set = set()
        for k2 in maybe_dict['毕业院校']:
            if k not in k2[0]:
                temp_set.add(k2)
        maybe_dict['毕业院校'] = temp_set
    for k in ['出版社']:
        temp_set = set()
        for k2 in maybe_dict['出版社']:
            if k  in k2[0]:
                temp_set.add(k2)
        maybe_dict['出版社'] = temp_set
    for k,i in removes.items():
        for rm in i[0]:
            try:
                maybe_dict_without_tp[k].remove(rm)
                maybe_dict[k].remove((rm, i[1]))
                maybe_obj_dict[k].remove(rm)
            except:
                continue
    import pickle as pk
    maybe_obj_dict['民族'] = set(filter(lambda x: '族' in x and x != '族', maybe_obj_dict['民族']))
    for i in maybe_obj_dict:
        maybe_obj_dict[i] = list(maybe_obj_dict[i])
    return maybe_dict,maybe_type_dict,maybe_dict_without_tp

def get_re():
    re_souce_dict = {}
    re_dict = {}
    re_souce_dict['毕业院校'] = [['毕业于'], ["大学",'学院','中学','大专','初中','学校','小学','院','校',',']]
    re_souce_dict['祖籍'] = [['祖籍'], [ '（',"，", '。']]
    re_souce_dict['注册资本'] = [['注册资本增加到,','注册资本金为','注册资金为','注册资本为','注册资本：','注册资本金','注册资金','注册资本'], ['人民币','元','万','，','。']]
    re_souce_dict['字'] = [['）字','，字'],
                             [' ', '，', '。']]
    re_souce_dict['号'] = [['）号','谥号','，号'],
                          [' ', '，', '。']]
    re_souce_dict['所属专辑'] = [ ('专辑《','》'),('《','》专辑'),('专辑：《','》') ]
    re_souce_dict['简称'] = [['简称','简称为'], ["，",'）','或“','、','》']]
    re_souce_dict['总部地点'] = [['坐落于', '总部位于','总部设立在','总部迁至','总部：','总部在','坐落在','总部设在'], ["，"]]
    re_souce_dict['出品公司'] = [['是'], ["出品"]]

    ##todo )?
    def get_dika_list(re_list_source,):
        re_list = []
        for start in re_list_source[0]:
            for end in re_list_source[1]:
                re_list.append(('(?<={}).*?(?={})'.format(start, end),end,start))
        return re_list
    def just_fill_re(  re_list_source):
        re_list = []
        for start,end in re_list_source:
                re_list.append(('(?<={}).*?(?={})'.format(start, end), end,start))
        return re_list
    for k , i in re_souce_dict.items():
        if type(i[0]) is tuple:
            re_dict[k] = just_fill_re(i)
        else:
            re_dict[k] = get_dika_list(i)
    return re_dict,re_souce_dict

def split_chupingongsi( objs ):
    cc = 0
    for obj in objs:
        temp_spos = []
        for spo in obj['spo_list']:
            if '、' in spo['object'] and spo['predicate'] == '出品公司':
                new_objects = spo['object'].split('、')
                for ob in new_objects:
                    new_spo = deepcopy(spo)
                    new_spo['object'] = ob
                    temp_spos.append(new_spo)
                cc+=1
            else:
                temp_spos.append(spo)
        obj['spo_list'] = temp_spos
    print('本次共清理错误出品公司数据{}条',cc)

def get_filter_func():
    filter_func = {}
    filter_func['字'] = contain_zh
    filter_func['号'] = contain_zh
    filter_func['所属专辑'] = contain_zhuanji
    return filter_func

def add_no_sigs(objs,maybe_dict,maybe_type_dict,maybe_dict_without_tp,s_dic=None):
    filter_func = get_filter_func()
    re_list,re_souce_dict = get_re()
    #
    clean_not_sig( objs,'毕业于',maybe_type_dict,'毕业院校',maybe_dict , re_list,s_dic=s_dic , nkws=['，'])
    clean_not_sig(objs, '出版', maybe_type_dict, '出版社', maybe_dict, re_list,s_dic=s_dic , cas_func=cbs_cas_func)
    clean_not_sig(objs, '连载于', maybe_type_dict, '连载网站', maybe_dict, re_list,s_dic=s_dic )
    maybe_dict['祖籍'] = set()
    clean_not_sig(objs, '祖籍', maybe_type_dict, '祖籍', maybe_dict, re_list, '祖籍',True,False,re_souce_dict,filter_func,s_dic=s_dic , nkws=['，','、','星座','的'],stripkws=['人','）','清代'] )
    maybe_dict['字'] = set()
    clean_not_sig(objs, None, maybe_type_dict, '字', maybe_dict, re_list, '字', False, False, re_souce_dict, filter_func,s_dic=s_dic,nkws=['（'] )
    maybe_dict['号'] = set()
    clean_not_sig(objs, None, maybe_type_dict, '号', maybe_dict, re_list, '号', False, False, re_souce_dict, filter_func,s_dic=s_dic )
    maybe_dict['注册资本'] = set()
    clean_not_sig(objs, set(['注册资金','注册资本']), maybe_type_dict, '注册资本', maybe_dict, re_list, '注册资本', False, True,re_souce_dict,s_dic=s_dic,stripkws=['，','。'] ,nkws=['，','仅'],cas_func=zczb_cas_func)
    maybe_dict['所属专辑'] = set()
    clean_not_sig(objs, None, maybe_type_dict, '所属专辑', maybe_dict, re_list, '所属专辑', False, False,
                  re_souce_dict,filter_func,s_dic=s_dic , cas_func=sszj_cas_func )