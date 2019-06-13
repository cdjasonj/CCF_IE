from copy import deepcopy
import regex
from tqdm import tqdm
import json
import re
from regex import findall

from data_process_common import get_maybe_objs, add_no_sigs, get_re, save_objs, sszj_cas_func,cbs_cas_func,jc_cas_func

def split_text( text , tag_str = r"[？。，]" ):
    return  re.split(tag_str, text)

def remove_sszj( objs ):
    cc = 0
    ## 添加毕业院校
    for obj in objs:
        haveyx = False
        tmzj = False
        zhuanjiset = set()
        for spo in obj['spo_list']:
            if spo['predicate'] =='所属专辑' :
                zhuanjiset.add( spo['object'] )
                if spo['subject'] == spo['object']:
                    tmzj=True
        temp_spo = []
        for spo in obj['spo_list']:
            add = True
            if spo['predicate'] =='歌手' or spo['predicate'] =='作词' or spo['predicate'] =='作曲' :
                for zj in zhuanjiset :
                    if spo['subject'] == zj  and not tmzj:
                        # print(spo['subject'],spo['predicate'],spo['object'], obj['text'])
                        cc+=1
                        add=False

            if add:
                temp_spo.append( spo )
        obj['spo_list'] = temp_spo
                # print(spo['object'],obj['text'])
    print('所属专辑',cc)

def add_jiancheng2( objs ):
    cc = 0
    re_list,_ = get_re()
    need_remove_str = ['"',"“","”",":",'：','《',"》",'）']
    add_type( objs )
    for obj in objs:
        cur_s = set()
        if '简称' in obj['text']:
            havejc = False
            for spo in obj['spo_list']:
                if spo['predicate'] == '简称':
                    havejc = True
                    break
                if spo['subject_type'] != '人物':
                    cur_s.add( spo['subject'] )
            if not havejc:
                isfind = False
                tempobstr='0'*100
                for rst in re_list['简称']:
                    obstr = regex.search(rst[0], obj['text'])
                    if obstr is not None:
                        if len(tempobstr) > len(str( obstr.group() )):
                            tempobstr = str( obstr.group())
                        isfind=True

                if not isfind:
                    1
                    # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',obj['text'])
                else:
                    for nds in need_remove_str:
                        tempobstr = tempobstr.replace(nds,"")
                    # print(most_min_len_str,'!!                                ',obj['text'])
                    if len(tempobstr) > 10:
                        continue
                    subject = ''
                    if len( cur_s ) == 1:
                        subject = list(cur_s)[0]
                    else:
                        ##选择最长的
                        for s in cur_s:
                            if len(s) > len(subject):
                                subject = s
                    if subject !='' and tempobstr!='' and len(subject) > len(tempobstr)  and tempobstr !='公司' and tempobstr !='集团':
                        cc+=1
                        new_spo = {}
                        new_spo['subject'] = subject
                        new_spo['object'] = tempobstr
                        new_spo['subject_type'] = 0
                        new_spo['object_type'] = 0
                        new_spo['predicate'] = '简称'

                        # print(new_spo,obj['text'])
                        obj['spo_list'].append(new_spo)
                    # print(obj)
    print('修复简称{}'.format(cc))
def add_dz2( objs ):
    cc=0
    no_kws = ['的','-']
    no_kws = ['的','全国','古都','省级','-','—']
    relist,re_sourcelist = get_re()
    re_sourcelist =re_sourcelist['总部地点'][0]
    for idx, obj in enumerate(objs):
        sub = ''
        if ('坐落' in obj['text'] or '总部' in obj['text'] ) and '公司' in obj['text']:
        # if '公司' in obj['text']:
            havedd = False
            for spo in obj['spo_list']:
                if spo['predicate'] == '总部地点':
                    havedd = True
                if '公司' in spo['subject']:
                    sub = spo['subject']
            if not havedd:
                ob = ''
                for s in re_sourcelist:
                    if s in obj['text']:
                        ob = obj['text'][obj['text'].find(s)+len(s):]

                        if '，' in ob:
                            ob = ob[ :ob.find('，')]
                        cflag = True
                        for nk in no_kws:
                            if nk in ob:
                                cflag = False
                        if not cflag:
                            # print(ob)
                            ob = ''
                            continue
                        # if '的' in ob:
                        #     ob = ob[ob.find('的')+1:]
                        if '”' in ob:
                            ob = ob[ob.find('”')+1:]
                if ob!= '' and sub != '':
                    ob = ob.strip('内')
                    add_spo( obj , sub , ob , '总部地点'  )
                    # print(obj['text'], '```````',sub, ob, obj['spo_list'])
                    cc+=1
    print('本次共清理总部地点1',cc)

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
            if spo['predicate'] == '国籍' and spo['object'] == '中国':
                # print(data['text'])
                # count += 1
                china_ents = [x for x in
                              filter(lambda x: x != '中国' and '中国' in x, [pos['word'] for pos in or_obj['postag']])]
                cur_text = data['text']
                for ent in china_ents:
                    cur_text = cur_text.replace(ent, '')
                if '中国' not in cur_text:
                    # print(data['text'])
                    rm_flag =True
                    count+=1
            if not rm_flag:
                temp_spos.append(spo)

        data['spo_list'] = temp_spos
    print(count)


def add_cpgs(objs):
    sp_cc = 0
    cc=0
    ##  这里是给出了由训练集得出的一些明显不可能是出品公司的关键字，其中和文化、和传媒等关键字因为其中的和会被当成连接字符给且分开所以也屏蔽掉
    forbid_kws = ['》', '制作', '投资', '在', '担任', '联手', '怎么', ]
    forbid_kws+=['摄制', '电视剧', '和传媒', '旗下', '庆祝', '和平', '自家', '主演','和文化']
    relist,_ = get_re()
    relist = relist['出品公司']
    strip_kw = ['一部','一部由','由','联合','共同','独家','合作','著','创作']
    for obj in objs:
        havecp = False
        for spo in obj['spo_list']:
            if spo['predicate'] == '出品公司':
                havecp = True
        if havecp or '出品' in obj['text']:
            # print_spo(obj['spo_list'],'出品公司')
            # print( obj['text'] )
            texts = split_text(obj['text'],r"[？。，]")
            for text in texts:
                text = text[text.find('》')+1:]
                for restr in relist:
                    reresult = regex.search(restr[0], text)
                    if reresult != None:
                        reresult = str(reresult.group())
                        ##等后面就不要了
                        if '等' in reresult:
                            reresult = reresult[:reresult.find('等')]
                        cflag = True
                        for fkw in forbid_kws:
                            if fkw in reresult:
                                cflag=False
                                break
                        if not cflag:
                            break
                        for rss in   [r'\d{4}年\d{1,2}月\d{1,2}日',r'\d{4}年\d{1,2}月',r'\d{4}年']:
                            yearresult = re.search(rss, reresult)
                            if yearresult is not None:
                                yearresult  = yearresult.group()
                                if '于'+yearresult in reresult:
                                    reresult = reresult[ :reresult.find('于'+yearresult) ]
                                reresult = reresult.replace(yearresult,'')
                                break
                        ##去掉
                        for skw in strip_kw:
                            if skw in reresult:
                                reresult = reresult.strip(skw)
                        reresult = reresult.rstrip('于')
                        if reresult != '':
                            reresult = set(split_text(reresult, r"[、与和及]"))
                            temp_set = []
                            for rst in reresult:
                                ##如果是一个数字
                                if '' != rst and not rst[0].isdigit():
                                    if '联合' in rst:
                                        temp_set.extend(rst.split('联合'))
                                    else:
                                        temp_set.append(rst)
                            reresult = set(temp_set)
                            # print('!!!!!',reresult)
                            ents = set()
                            for spo in obj['spo_list']:
                                if spo['predicate'] == '出品公司':
                                    ents.add(spo['object'])
                            dif = reresult - ents
                            if len(dif) > 0 :
                                cc+=len(dif)
                                # print(dif ,reresult,obj['text'])
                                ## 处理那些有same的
                                same = reresult & ents
                                if len(same) > 0:
                                    sp_set = set()
                                    for sm in same:
                                        for spo in obj['spo_list']:
                                            if sm == spo['object']:
                                                sp_set.add( (spo['subject'],spo['predicate']) )
                                    for df in dif:
                                        for sp in sp_set:
                                            add_spo( obj , sp[0],df, sp[1] )
                                            sp_cc +=1
                                    # print('!!! sp',sp_set)
                                else:
                                    ##如果只有一个书名号，就取书名号中的内容
                                    shumings = list(set(regex.findall("(?<=《).*?(?=》)", obj['text'])))
                                    if len(shumings) == 1:
                                        for df in dif:
                                            add_spo(obj, shumings[0], df, '出品公司')
                                            # print(shumings[0],df)
                                        print(shumings, dif  , obj['text'])
                                        sp_cc+=len(dif)
    print('sss',cc,sp_cc)

def get_ent_type(  ):
    type_dict = {}
    with open('inputs/all_50_schemas','r',encoding='utf8') as f:
        for l in f:
            a = json.loads(l)
            t = {}
            t['subject_type']  = a['subject_type']
            t['object_type'] = a['object_type']
            type_dict[a['predicate']] = t
    return type_dict
def add_type( objs ):
    type_dict = get_ent_type()
    for obj in objs:
        for spo in obj['spo_list']:
            spo['subject_type'] = type_dict[spo['predicate']]['subject_type']
            spo['object_type'] = type_dict[spo['predicate']]['object_type']
def print_spo( spo_list , pred=None):
    for spo in spo_list:
        if pred != None:
            if spo['predicate'] == pred:
                pass
                # print(spo['subject'],spo['object'],spo['predicate'])
        else:
            # print(spo['subject'], spo['object'], spo['predicate'])
            pass
def get_objs( f_input ):
    objs = []
    with open(f_input, encoding="utf8") as f:
        for l in tqdm(f):
            a = json.loads(l)
            objs.append(a)
    return objs
type_dict = get_ent_type()
def add_spo( obj , sub ,  ob , pred ):

    newspo = {}
    newspo['subject'] = sub
    newspo['object'] = ob
    newspo['predicate'] = pred
    newspo['subject_type'] = type_dict[pred]['subject_type']
    newspo['object_type'] = type_dict[pred]['object_type']
    add_flag = True
    for spo in obj['spo_list']:
        if spo['object'] == newspo['object'] and spo['subject'] == newspo['subject'] and spo['predicate'] == newspo['predicate']:
            add_flag = False
    if add_flag:
        obj['spo_list'].append(newspo)
        return True
    return False
def is_eng_char(ch):
    return (ch >= 'a' and ch <='z') or (ch >= 'A' and ch <='Z')




def clean_english_name_with_space( objs):
    ## todo 还有一点问题  这里还有一点问题
    cc=0
    def _clean_english_name_with_space( text ):
        eng_names = []

        def is_space_in_name(text,idx,tag):
            return idx < len(text) -1 and ch == tag and is_eng_char(text[idx+1])
        flag = False
        cur_text = ''
        for idx,ch in enumerate(text):
            if is_eng_char(ch) or  is_space_in_name( text ,idx , ' ')   :
                cur_text += ch
            else:
                if ' ' in cur_text :
                    eng_names.append( cur_text.strip() )
                    cur_text = ''
                else:
                    cur_text = ''
        return set(eng_names)
    for idx,obj in enumerate(objs):
        eng_names = _clean_english_name_with_space( obj['text'] )
        for spo in obj['spo_list']:
            ents = [spo['object']]
            for en in eng_names:
                for ent in ents:
                    if ent in en and ent.strip() != en:
                        # print(ent,'!!!',en,'!!!!',spo['object'],spo['predicate'],obj['text'])
                        add_spo( obj , spo['subject'] ,en ,spo['predicate'] )
                        cc+=1
    print('共清理带空格的英文名字',cc)


def get_mutis_shuminghao2(text):
    cur_text = ''
    flag = False

    muti_shuminghaos = []
    if '分别带来' in text or '已分别交由' in text:
        return []
    for idx, ch in enumerate(text):
        if ch == '《':
            flag = True
        # if ch == '、' and idx < len(text) - 1 and text[idx + 1] != '《':
        #     flag = False
        #     cur_text = ''
        if flag:
            cur_text += ch
        if ch == '》' and (idx == len(text) - 1 or text[idx + 1] != '《'):
            if '》《' in cur_text and cur_text.count('《') > 1:
                spresult = cur_text.split('》《')
                tempsps = set()
                for sp in spresult:
                    tempsps.add( sp.strip('《').strip('》') )
                muti_shuminghaos.append(tempsps)
                cur_text = ''
                flag = False
            else:
                cur_text = ''
                flag = False
    return muti_shuminghaos
def get_mutis_shuminghao(  text  ):
    cur_text = ''
    flag = False

    muti_shuminghaos = []
    if '分别带来' in text or '已分别交由' in text:
        return []
    for idx ,ch in enumerate(text):
        if ch == '《':
            flag = True
        if ch == '、' and  idx < len(text) -1 and text[idx+1] != '《':
            flag = False
            cur_text = ''
        if flag:
            cur_text+=ch
        if ch == '》'   and ( idx == len(text) -1 or text[idx+1] !='、') :
            if '、' in cur_text and cur_text.count('《') > 1 :
                muti_shuminghaos.append(set(cur_text.replace('《','').replace('》','').split('、')))
                cur_text = ''
                flag=False
            else:
                cur_text=''
                flag = False
    return muti_shuminghaos
def check_no_pre_kw( text , ent ):
    no_pre_kw = set(['演', '的', '版'])
    for kw in no_pre_kw:
        if text[text.find(ent) - 1] == kw:
            return False
    return True
def get_name_concat_with_tag( idx ,obj , postag ,tag ):
    text = obj['text']
    rms_with_dun_hao = ''
    cur_rm = ''
    cond_set = set(['nr','nz'])
    replace_dict = {}
    no_kw = ['学报']
    no_ent_kw = set(['主演','领衔','组','编','和','-'])

    for kw in no_kw:
        if kw in text:
            return ''
    for idx, pt in enumerate(postag):
        # if (pt['pos'] == 'nr' and postag[idx+1]['word']=='·' and idx < len(postag)-1 ) or ( idx > 0 and  postag[idx-1]['pos']=='nr' and postag[idx]['word']=='·' ) :
        #     cur_rms = cur_rms+pt['word']
        # elif pt['pos'] == 'nr':
        #     cur_rms = pt['word']
        # else:
        #     rms.append(cur_rms)
        #     cur_rms=''
        if pt['word'] == '莫罗尼':
            pt['pos'] = 'nr'
        if pt['word'] ==tag and idx < len(postag)-1 and postag[idx+1]['pos'] not in cond_set:
            return  ''
        if pt['pos'] == 'nr' or pt['word'] == '·' or pt['pos'] == 'nz' :
            cur_rm += pt['word']
        if ((idx == len(postag) - 1 or postag[idx + 1]['word'] != '·') and pt['word'] != '·' and cur_rm != ''):
            rms_with_dun_hao += cur_rm
            if idx < len(postag) - 1 and  postag[idx+1]['word'] == tag:
                rms_with_dun_hao+=tag
            else:
                if tag in rms_with_dun_hao :
                    if not rms_with_dun_hao in text:
                        return ''
                    split_result = rms_with_dun_hao.split(tag)
                    temp_result = []
                    for s in split_result:
                        s = s.strip(' ')
                        if s in replace_dict:
                            s = replace_dict[s]
                        if s !='' and  check_no_pre_kw(text,s):
                            af = True
                            for kw in no_ent_kw:
                                if kw in s:
                                    # print(text, s)
                                    af = False
                                    break
                            s = s.rstrip('领')
                            if af:
                                temp_result.append(s)
                    split_result = temp_result

                    if len(split_result) >1:
                        return set(split_result)
                rms_with_dun_hao = ''
            cur_rm = ''
    return ''

def chekc_is_zuozhe( text , ent ):
    cbs_id = text.find(ent)
    if cbs_id > 2 and text[cbs_id-3:cbs_id] == '作者是' or text[cbs_id-4:cbs_id] == '作者是《':
    # if text[cbs_id-3:cbs_id] == '作者是' or text[cbs_id-4:cbs_id] == '作者是《':
        return False
    return True

def shuming_count_is_match( e ):
    return (e.count('》')%2 == 1 and e.count('《')%2 == 0) or (e.count('《')%2 == 1 and e.count('》')%2 == 0)

def check_inner_shuminghao( objs ):
    cc=0

    cset = set(['编辑部','编委会','栏目组','委员会'])
    for obj in objs:
        temp_spo = []
        text = obj['text']
        ct = True
        shumings = get_shuminghaos2(obj['text'])
        # for shuming in shumings:
        #     if '《' in shuming:
        #         ct = False
        #         break
        # if not ct:
        #     continue
        for spo in obj['spo_list']:
            afg = True
            ent = [ spo['subject'] , spo['object'] ]
            for k in [ 'subject','object' ]:
                e = spo[k]
                if ('《' in e or '》' in e) and  check_nkw( cset , e )  and chekc_is_zuozhe( obj['text'], e ):
                    if e.startswith('《') and not e.endswith('》') or e.startswith('》') and not e.endswith('《') :
                        # print(1, e, '     ', obj['text'])
                        e = e.strip('《')
                        e = e.strip('》')
                        spo[k] = e
                        # print(1,e, '     ', obj['text'])
                        cc+=1
                    elif  shuming_count_is_match(e):
                        # obj['spo_list'].remove(spo)
                        ##尝试去修复
                        eidx = text.find(e)
                        havefix = False
                        if text[eidx-2:eidx] == '《《':
                            e = '《'+e
                            if not shuming_count_is_match(e):
                                spo[k] = e
                                # print(21, e, '     ', shumings, obj['text'])
                                havefix = True
                            else:
                                pass
                                # print('err', e, '     ', shumings, obj['text'])
                        elif text[eidx+len(e):eidx+len(e)+2] == '》》':
                            e =  e + '》'
                            if not shuming_count_is_match(e):
                                spo[k] = e
                                # print(21, e, '     ', shumings, obj['text'])
                                havefix = True
                            else:
                                pass
                                # print('err', e, '     ', shumings, obj['text'])
                        if not havefix:
                            afg=False
                            # print(23,e,'     ',shumings,obj['text'])
                        cc+=1
                    else:
                        e = e.strip('《').strip('》')
                        fg = False
                        for sm in shumings:
                            # if e in sm and '《' not in sm :
                            if e in sm :
                                fg=True
                                break
                        if not fg:
                            print(3,e, '     ', shumings, obj['text'])
                            cc += 1
                            afg=False
                        # else:
                        #     temp_spo.append(spo)
                            # obj['spo_list'].remove(spo)
                    # shumings = get_shuminghaos(obj['text'])
                    # print(e, '     ', shumings, obj['text'])
            if afg:
                temp_spo.append(spo)
        obj['spo_list'] = temp_spo
    print(cc)

def check_name_concat_with_tag( objs , orobjs ,tag,concat_spilit_func):
    ## 处理人名被多个顿号连在一起，但是结果没有没有包含虽有被顿号连在一起的情况
    cc=0
    allow_preds = set(['作者','主演','歌手','毕业院校','创始人','主角'])
    # allow_preds = set([ '朝代'])
    pred_no_kw = { '毕业院校':['指导','聘请','教授','导师','观看'] }
    for idx, obj in enumerate(objs):
        if tag in obj['text']:
            name_with_dunhao = concat_spilit_func( idx  , obj, orobjs[idx]['postag'] ,tag )
            contain_mu = False
            ents = set()
            cur_subs = set()
            if len(name_with_dunhao) > 0:
                for spo in obj['spo_list']:
                    cur_subs.add( spo['subject'] )
                    ents.add(spo['object'])
                    ents.add(spo['subject'])
                    if spo['predicate'] == '目':
                        contain_mu = True
                dif = set()
                for name in name_with_dunhao:
                    afg = False
                    for ent in ents:
                        if name  in ent:
                            afg =True
                            break
                    if not afg:
                        dif.add(name)
                same = name_with_dunhao & ents
                another_ent = None
                tp = None
                pred = None
                sps = set()
                for spo in obj['spo_list']:
                    if spo['object'] in same and spo['predicate'] in allow_preds and obj['text'].count(spo['object']) == 1:
                        tp = 'ob'
                        another_ent = spo['subject']
                        pred = spo['predicate']
                        sps.add( ( tp ,another_ent , pred ) )
                    if spo['subject'] in same and spo['predicate'] in allow_preds and obj['text'].count(spo['subject']) == 1:
                        tp = 'sub'
                        pred = spo['predicate']
                        another_ent = spo['object']
                        sps.add((tp, another_ent, pred))
                if len(dif) > 0 and len(dif) < len(name_with_dunhao) and not contain_mu and len(sps) > 0 :
                    for sp in sps:
                        addFlag = True
                        pred = sp[2]
                        another_ent = sp[1]
                        tp = sp[0]
                        for k in pred_no_kw:
                            klist = pred_no_kw[k]
                            if k == pred:
                                for kl in klist:
                                    if kl in obj['text']:
                                        addFlag = False
                                        # print(obj['text'])
                                        break
                        # cc += len(dif)
                        if addFlag:
                            for difent in dif:
                                    if tp == 'sub'  and pred in ['毕业院校','创始人','主角'] :
                                        add_spo(obj, difent, another_ent, pred)
                                        cc+=1
                                    elif tp == 'ob' and len( cur_subs ) == 1 :
                                        add_spo(obj, another_ent, difent, pred)
                                        cc+=1
                            # print_spo(obj['spo_list'])
                            # print(idx, dif, obj['text'])
    print('共处理',cc)
def find_all_ocrs( text ,ent ):
    last_idx = -1
    all_idx = []
    while True:
        cur_idx = text.find(ent,last_idx+1)
        if cur_idx == -1:
            return all_idx
        last_idx = cur_idx
        all_idx.append(cur_idx)
def check_nkw( kws ,text ):
    # return True
    for kw in kws:
        if kw in text:
            return False
    return True

def find_ents_concat_by_tag( idx  , obj, postag ,splittag):
    result = []
    ents = [ spo['subject'] for spo in obj['spo_list'] ]
    ents+=[ spo['object'] for spo in obj['spo_list'] ]
    text = obj['text']
    kws = []
    text_nokws = []
    for tnk in text_nokws:
        if tnk in obj['text']:
            return []
    tags = [0]*len(text)
    tt = [ch for ch in text]

    for ent in ents:
        ##找到所在位置，打上标记
        ocrs = find_all_ocrs( text , ent )
        for ocr in ocrs:
            tags[ ocr:ocr+len(ent) ] = [1]*len(ent)
    ##插入顿号、所在的、位置
    split_result = split_text(text,tag_str = r"[？。，:：]")
    cur_len = 0
    for sr in split_result:
        dunhaoocrs = find_all_ocrs(sr, splittag)
        for idx,ocr in enumerate(dunhaoocrs):
            if idx < len(dunhaoocrs) -1 :
                start_idx = ocr + cur_len
                end_idx = dunhaoocrs[idx + 1] + cur_len
                tags[ start_idx:end_idx+1 ] = [2]*( end_idx+1 - start_idx )
        cur_len+=(len(sr)+1)
    cur_text = ''
    for idx,tag in enumerate( tags ):
        if tag == 2 or tag == 1:
            cur_text+=text[idx]
        else:
            if splittag in cur_text  :
                temp_set = set([ x  for x in filter( lambda x: x != '' and check_nkw(kws,x) and len(x) > 1 and not x.strip().isdigit() , cur_text.split(splittag) ) ])
                return set([ x.strip() for x in  temp_set ])
            else:
                cur_text =''
    return ''


def check_mv_onshelf_date( objs ):
    cc=0
    ## 检查电影上映时间，根据训练集得出的一些不可能是上映时间的关键字
    mask_kws =['广播','的播','数播','传播','热播','点播']
    nk_kws = ['有消息']
    for obj in tqdm(objs):
        for spo in obj['spo_list']:
            if spo['predicate'] == '主演':
                if not  check_nkw( nk_kws , obj['text'] ):
                    continue
                # print(obj['text'])
                subs = set()
                for spo in obj['spo_list']:
                    if spo['subject_type'] == '影视作品':
                        subs.add(spo['subject'])
                if len(subs) != 1:
                    break
                cf = False
                cur_onshelf_date = None
                for spo in obj['spo_list']:
                    if spo['predicate'] == '上映时间':
                        cf = True
                        cur_onshelf_date = spo['object']
                        break
                # if cf:
                #     print(obj['text'])
                #     # cc+=1
                # yearresults = []
                #
                ctext = obj['text']
                for mask in mask_kws:
                    ctext = ctext.replace(mask,'xx')
                bo_idx = ctext.find('播')
                min_len = 99
                yearresult = None
                for rss in [r'\d{4}年\d{1,2}月\d{1,2}日', r'\d{4}年\d{1,2}月', r'\d{4}年',r'\d{4}-\d{1,2}-\d{1,2}', r'\d{4}-\d{1,2}']:
                    cyearresults = re.findall(rss, obj['text'])
                    for cyearresult in cyearresults:
                        if cyearresult is not None:
                            # yearresults.append( yearresult.group() )
                            # cyearresult = cyearresult.group()
                            year_idx = ctext.find(cyearresult)
                            if abs(year_idx - bo_idx) < min_len:
                                min_len = abs(year_idx - bo_idx)
                                yearresult = cyearresult
                if yearresult is not None:
                    if ctext.count('播') > 0:
                        # print_spo(obj['spo_list'])
                        if not cf:
                            cc+=1
                            add_spo( obj , list(subs)[0],yearresult , '上映时间' )
                            # print(yearresult, cur_onshelf_date, subs, ctext)
                        else:
                            1
                break
    print(cc)


def check_shuming_with_dunhao1( objs,union_results ):
    def get_spo_from_union(obj,spo_list,dif):
        for spo in spo_list:
            if spo['subject'] == dif:
                add_spo( obj , spo['subject'] , spo['object'] , spo['predicate'] )
                return True
        return False
    ##80多可以处理的情况。80多个一个顿号都没有出现过的情况，从原始的融合文件里面找
    cc = 0
    for idx, obj in enumerate(objs):
        muti_shuminghao = get_mutis_shuminghao( obj['text'] )
        curs = set()
        union_obj = union_results[idx]
        for spo in obj['spo_list']:
            curs.add( spo['subject'] )
        if len(muti_shuminghao) > 0 :

            for sub_muti_shuminghao in muti_shuminghao:
                dif = []
                for m in sub_muti_shuminghao:
                    if m not in curs:
                        dif.append(m)

                if len(dif) > 0 and len(dif) == len(sub_muti_shuminghao):
                    for d in dif:
                        if get_spo_from_union( obj ,union_obj['spo_list'] , d  ):
                            cc+=1
                    # print_spo( obj['spo_list'] )
                    # print(dif, sub_muti_shuminghao, curs, obj['text'])
    print('多主语数量',cc)


def check_shuming_with_dunhao2( objs  ,split_func):
    ##80多可以处理的情况。80多个一个顿号都没有出现过的情况，从原始的融合文件里面找
    cc = 0
    for idx, obj in enumerate(objs):
        muti_shuminghao = split_func( obj['text'] )
        curs = set()
        curo = {}
        for spo in obj['spo_list']:
            curs.add( spo['subject'] )
            temp_set = curo.get( (spo['subject'],spo['predicate']) ,set() )
            temp_set.add(spo['object'])
            curo[(spo['subject'],spo['predicate'])] = temp_set
        if len(muti_shuminghao) > 0  :
            for sub_muti_shuminghao in muti_shuminghao:
                dif = []
                for m in sub_muti_shuminghao:
                    if m not in curs:
                        dif.append(m)
                # dif = muti_shuminghao - curs

                if len(dif) > 0 and len( dif) < len(sub_muti_shuminghao) :
                    same = sub_muti_shuminghao & curs
                    sps = set()
                    mmfg = False
                    for spo in obj['spo_list']:
                        if spo['subject'] in same and  len(curo[( spo['subject'],spo['predicate'] )]) > 1:
                            mmfg = True
                    if mmfg:
                        continue
                    for spo in obj['spo_list']:
                        if spo['subject'] in same and obj['text'].count(spo['subject']) == 1 :
                            sps.add((spo['predicate'],spo['object']))
                        # if spo['subject'] in same and obj['text'].count(spo['subject']) == 1:
                        #     if spo['predicate'] not in preds:
                        #         # preds.append(spo['predicate'])
                        #         # obs.append(spo['object'])
                    # cc+=len(dif)
                    sps = list(sps)
                    if len(sps)>0 :
                        for difent in dif:
                            for idx in range(0, len(sps)):
                                sp = sps[idx]
                                pred = sp[0]
                                ob = sp[1]
                                # print(difent, pred , ob , obj['text'])
                                cc += 1
                                add_spo(obj, difent, ob, pred)
                    # print_spo(obj['spo_list'])
                    # print(dif, sub_muti_shuminghao, curs, obj['text'])
    print('多主语数量',cc)

def trans_spo_list( spo_list ):
    return [ (spo['subject'],spo['predicate'],spo['object']) for spo in spo_list ]

def retrans_spo_list( spo_list ):
    type_dict = get_ent_type()
    return [ { 'subject':spo[0] , 'predicate':spo[1] , 'object':spo[2] , 'subject_type':type_dict[spo[1]]['subject_type'],'object_type':type_dict[spo[1]]['object_type'] } for spo in spo_list ]
def _get_max_len_dict(kk):
    temp_list = []
    for idx, k1 in enumerate(kk):
        max_len_str = k1
        for idx2, k2 in enumerate(kk, idx):
            if max_len_str in k2 and len(k2) > len(max_len_str):
                max_len_str = k2
        temp_list.append(max_len_str)
    return list(set(temp_list))
def find_max_len_ent( result ):
    add_type( result )
    edit_cc = 0
    clean_cc = 0
    type_dict = get_ent_type()
    miss_ent = set(['过把瘾'])
    """
        针对同一对sub-predicate,多个object,并且存在字串的情况，进行清洗
        针对同一对obj-predicate,多个subject,并且存在子串的情况，进行清洗
        :param result:
        :return:index:
    """
    def find_match_ent( or_ent , ent_list ):
        if or_ent in miss_ent:
            return or_ent
        temp_ent = ''
        match_cnt = 0
        for ent in ent_list:
            if or_ent in ent:
                match_cnt += 1
                if match_cnt > 1:
                    # print('&&', data['text'] ,'~' ,or_ent ,'~', ent_list )
                    # raise Exception('muti match')
                    continue
                temp_ent = ent
        if temp_ent == '':
            # print(data['text'], or_ent, ent_list)
            ## todo 这里有bug
            return or_ent
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
            ent_dict[ob_type] = temp_ob_list

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
        #     print( spo,data['text'] , or_spo_list )
        clean_cc+=len( difset )
        data['spo_list'] = retrans_spo_list( spo_list )
    print( '当前编辑了 ',edit_cc )
    print('当前删除了 ', clean_cc)

def get_shuminghaos(text ):
    shumings = regex.findall("(?<=《).*?(?=》)", text)
    return  shumings

def get_shuminghaos2( text ):
    cur_zuo = 0
    cur_you = 0
    shumings = []
    cur_text =''
    cfg = False
    for idx , ch in enumerate(text):
        if ch =='《':
            cur_zuo+=1
            cfg = True
        if ch == '》':
            cur_you+=1
        if cfg:
            cur_text+=ch
        if ch == '》' and cur_zuo == cur_you:
            if cur_text != '':
                cur_text= cur_text[1:-1]
                shumings.append(cur_text)
                cur_text=''
                cfg=False
    return shumings

def create_shuming_tags( shuminghao_start_ids , shuminghao_end_ids ,text):
    shuminghao_tags = [0] * len(text)
    for idx, i in enumerate(shuminghao_start_ids):
        j = shuminghao_end_ids[idx]
        shuminghao_tags[i+1:j] = [1]*( j-i-1 )
    return shuminghao_tags
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
def clean_shuminghao(objs  ):
    not_change = set(['国家','人物','Text','城市'])
    change = set(['音乐专辑', '作品', '影视作品', '电视综艺','歌曲','图书作品','网络小说','书籍',''])
    clean_count = 0
    for obj in tqdm(objs):
        ##第一步，将书名号中的空格去掉。
        temp_spos = []
        text = obj["text"]
        # text = text.replace("《《","《")
        shumings = findall("(?<=《).*?(?=》)",text)
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
                        # print("s~~~~~~~", text, "\n", spo, '\n', sm, subject)
                        clean_count += 1
                        edit=True
            if object not in shumings and  spo["object_type"] in change and check_is_all_in_shuminghao(text,shuminghao_tags,object):
                ##判断是否以被包含在其中
                for sm in shumings:
                    if sm.find(object) != -1 :
                        spo["object"] = sm
                        # print("0~~~~~~~", text, "\n", spo, '\n', sm, object)
                        clean_count += 1
                        edit=True
            if edit:
                clean_count+=1

    print("~~~~~clean count",clean_count)
def find_dif(objs,cp_objs):
    temp_objs = []
    cc=0
    for idx,obj in enumerate(objs):
        addF = False
        spo_list = set(trans_spo_list(obj['spo_list']))
        cp_spo_list = set(trans_spo_list( cp_objs[idx]['spo_list'] ))
        dif = spo_list - cp_spo_list
        if len(dif) > 0:
            cc+=len(dif)
            dif = retrans_spo_list(dif)
            temp_objs.append( {'text':obj['text'],'spo_list':dif} )
        save_objs(temp_objs,'dif_spo.json')
    print('本次共清理',cc)
def do_clean_515(objs,or_test_objs,train_objs,dev_objs):
    # cp_objs = deepcopy(objs)
    add_type(objs)
    remove_sszj(objs)
    maybe_dict, maybe_type_dict, maybe_dict_without_tp = get_maybe_objs(train_objs, dev_objs, '')
    add_no_sigs(objs, maybe_dict, maybe_type_dict, maybe_dict_without_tp, {})
    # ## 书名号
    clean_shuminghao(objs)
    # # # ## 清理书名号错乱
    check_inner_shuminghao(objs)
    # # # # 简称
    add_jiancheng2(objs)
    # # # # # 总部地点
    add_dz2(objs)
    # # ## 清理没有被预测完整的带空格的英文名
    clean_english_name_with_space(objs)
    # # ## 补全出品公司
    add_cpgs(objs)
    # # # # 清理国籍
    guoji_fix(objs, or_test_objs)
    # # # ## 上述清理完之后，会存在一些重复或者有子串包含的spo，调用最长子串匹配清理一下
    check_mv_onshelf_date(objs)
    # # # ## 清理被顿号连起来但是没被预测出来的书名号，par2
    check_shuming_with_dunhao2(objs, get_mutis_shuminghao)
    check_shuming_with_dunhao2(objs, get_mutis_shuminghao2)
    # # # # ## 清理被顿号连起来但是没被预测出来的姓名 这里面硬编码比较多，新数据可能出错较多
    check_name_concat_with_tag(objs, or_test_objs, '、', get_name_concat_with_tag)
    check_name_concat_with_tag(objs, or_test_objs, '/', find_ents_concat_by_tag)
    find_max_len_ent(objs)
