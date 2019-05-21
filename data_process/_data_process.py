from copy import deepcopy
import regex
from tqdm import tqdm
import json
import re
from regex import findall

from data_process_common import get_maybe_objs, add_no_sigs, get_re, save_objs, sszj_cas_func,cbs_cas_func,jc_cas_func

def check_same_so(objs):
    cc=0
    for obj in objs:
        for spo in obj['spo_list']:
            if spo['object'] == spo['subject'] and obj['text'].count(spo['object']) == 1:
                print(spo['object'],spo['predicate'],obj['text'])
                cc+=1
    print(cc)

def split_text( text , tag_str = r"[？。，]" ):
    return  re.split(tag_str, text)
##添加地址
def get_rms( postag ):
    rms = []
    cur_rm = ''
    no_kws = ['领衔','饰','导演','大公','福特']
    def filter_and_cond1( x ):
        contain = False
        for nk in no_kws:
            if nk in x:
                contain = True
        if contain:
            return False
        return True
    def filter_and_cond2( x ):
        if '·' in x:
            x = [ x for x in filter( lambda x:''!=x , x.split('·') )]
        return len(x) > 1

    def filter_and_cond3( x ):
        if '·' in x:
            for ch in x:
                if is_eng_char(ch):
                    return False
        return True

    for idx, pt in enumerate(postag):
        # if (pt['pos'] == 'nr' and postag[idx+1]['word']=='·' and idx < len(postag)-1 ) or ( idx > 0 and  postag[idx-1]['pos']=='nr' and postag[idx]['word']=='·' ) :
        #     cur_rms = cur_rms+pt['word']
        # elif pt['pos'] == 'nr':
        #     cur_rms = pt['word']
        # else:
        #     rms.append(cur_rms)
        #     cur_rms=''
        if (pt['pos'] == 'nr' or pt['word'] == '·'):
            cur_rm+=pt['word']
        if(  (idx == len(postag) -1 or  postag[idx+1]['word'] != '·') and pt['word'] != '·' and cur_rm != ''):
            result  = [ x.strip() for x in filter( lambda x: x!='' and not x.startswith('美') and not ( x.startswith('英') and '·' in x ) and filter_and_cond1(x) and filter_and_cond2(x) and filter_and_cond3(x),cur_rm.split('/')) ]

            rms.extend(result)
            cur_rm=''
    rms = list(set(rms))
    return rms
def add_dy( objs  ,or_test_objs ):
    ##1 2013年文章在周星驰投资的电视剧《小爸爸》中不仅与妻子再次合作担任男女主角，同时他还是该剧的导演 ['周星驰'] 周星驰
    ##23月5日，科比退役感言改拍的动画短片《亲爱的篮球》荣获奥斯卡第90届最佳动画短片奖，这次入围提名的还有《负空间》、《反叛的童谣》、《花园派对》、《失物招领》，科比之所以能获得奥斯卡金奖不仅仅源于这部短片情真意切+超级励志，更是传奇动画导演格兰-基恩以及著名配乐人约翰-汤纳-威廉姆斯亲自操刀的良心大作，格兰-基恩是迪士尼公司大师级的动画导演，曾参与过《小美人鱼》、《美女与野兽》、《泰山》、《魔发奇缘》、《阿拉丁》等数部迪士尼经典动画长片的创作，并曾获颁1992年安妮奖的最佳动画角色奖，以及2007年温瑟-麦凯奖的终身贡献奖 ['汤纳', '约翰', '科比', '威廉姆斯'] 约翰
    #3  《青春再见》是电影《怒放2013》的主题曲，由导演卢庚戌亲自操刀填词、作曲，2013快乐男声华晨宇、白举纲、张阳阳和左立献唱，于2013年11月12日正式发布，全面地向观众展示了这部正能量青春电影的全貌 ['卢庚戌', '华晨宇', '张阳阳', '左立', '白举纲'] 卢庚戌
    # 4  格特兹·斯佩曼尼(Götz Spielmann)，1961-1出生，编剧、导演、演员、制作人，主要作品《复仇》、《安塔芮丝》、《拂晓的赌博》 ['斯佩曼尼', '格特兹'] 斯佩曼尼
    #5 《从天儿降》的主题曲《青春快乐》，对于这首“喜脑歌”，其实是拍摄一场开车戏时，导演魏楠让张艺兴随便哼一个欢快好学的旋律 ['魏楠', '张艺兴'] 魏楠
    #6 《从天儿降》的主题曲《青春快乐》，对于这首“喜脑歌”，其实是拍摄一场开车戏时，导演魏楠让张艺兴随便哼一个欢快好学的旋律 ['魏楠', '张艺兴'] 魏楠
    #7 《刘老根1》之后，王晓曦便和赵本山结下了不解之缘，在接下来的《刘老根2》、《乡村爱情》等戏中出演重要角色，同时还担任了副导演的职务，虽然工作很辛苦，但是对于王晓曦来说，与赵本山的合作成为他一生中最幸运的事:&quot ['王晓曦', '赵本山'] 王晓曦
    #8 《光影言语：当代华语片导演访谈录》是 广西师范大学出版社出版的图书，ISBN是9787563376438 []
    #9 获奖记录获奖时间获奖奖项获奖方2018年第10届日剧公信奖15作品奖《刑警弓神》最佳男主角浅野忠信最佳男配角神木隆之介播出信息集数播出时间编剧导演收视率第一集2017-10-12仓光泰子西谷弘7 ['西谷弘7', '神木隆之介', '浅野忠信', '泰子'] 神木隆之介
    #10 近年，MK2合作的主要导演有伊朗导演阿巴斯(《合法副本》《如沐爱河》)、巴西导演沃尔特·塞勒斯(《中央车站》《在路上》)、美国导演格斯·范桑特(《大象》)、法国导演奥利维耶·阿萨亚斯(《五月之后》)及中国导演贾樟柯 ['阿萨亚斯', '塞勒斯', '沃尔特', '奥利维耶', '贾樟柯', '范桑特', '格斯', '阿巴斯'] 阿巴斯
    #11
    cc = 0
    re_list, _ = get_re()
    need_remove_str = ['"', "“", "”", ":", '：', '《', "》"]
    kws = ['执导','导演']
    not_kws = ['MV','导演组','他','出版']
    for idx , obj in enumerate(objs) :
        if len(obj['text']) > 100:
            continue
        isse = False
        for kw in kws:
            if kw in obj['text']:
                isse=True
                break
        if isse and '《' in obj['text']:
            ct =False
            for nkw in not_kws:
                if nkw in obj['text']:
                    ct = True
                    break
            if ct:
                continue
            or_obj = or_test_objs[idx]
            rms = get_rms( or_obj['postag'] )
            ##寻找导演
            rm_dis = {}
            min_dis = 300
            dymz = ''
            for rm in rms:
                cur_all_idx = find_all_ocrs(obj['text'], rm)
                for k in kws:
                    kid = obj['text'].find(k)
                    if kid == -1:
                        continue
                    for cid in cur_all_idx:
                        cur_min1 = abs(cid - kid)
                        cur_min2 = abs(cid + len(rm) - 1 - kid)
                        cmin = cur_min1 if cur_min1 < cur_min2 else cur_min2
                        if cmin < min_dis:
                            min_dis = cmin
                            dymz = rm
            subs = list(set(regex.findall("(?<=《).*?(?=》)", obj['text'])))
            havezy = False
            for spo in obj['spo_list']:
                if spo['predicate'] == '导演':
                    havezy = True
                    break
            if not havezy:
                # print(obj['text'],rms)
                if len(subs) == 1 and len(rms) > 0:
                    print(obj['text'],subs[0] , dymz ,'导演')
                    add_spo( obj , subs[0] , dymz ,'导演'  )
                    cc+=1
                else:
                    if '主要作品' in obj['text']:
                        for sb in subs:
                            add_spo(obj, sb, dymz, '导演')
                            cc+=1
                    else:
                        # print('~~~~~~~~~~~~~',obj['text'])
                        1
    print(cc)
def check_yixjiajiancheng( objs ):
    for obj in objs:
        if '（' in obj['text'] and '）' in obj['text']:
            print(obj['text'])
        # for spo in obj["spo_list"]:
        #     if spo['predicate'] == '简称' and  not '简称' in obj['text']:
        #         print(spo['subject'],spo['object'],obj['text'])
# def remove_sszj2(objs):
#     relist,_ = get_re()
#
#     for obj in objs:
#         text = obj['text']
#         find = False
#         for (s, end, start) in relist['所属专辑']:
#             obstr = regex.search(s, obj['text'])
#             if obstr is not None:
#                 obstr = str(obstr.group())
#                 if start in obstr:
#                     obstr = obstr[obstr.find(start) + len(start):]
#                 find = True
#                 break
#         if find:
#             for spo in obj['spo_list']:
#                 if spo['subject'] == obstr and not ('收录' in text or '同名' in text):
#                     print(text,spo)


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
                        print(spo['subject'],spo['predicate'],spo['object'], obj['text'])
                        cc+=1
                        add=False

            if add:
                temp_spo.append( spo )
        obj['spo_list'] = temp_spo
                # print(spo['object'],obj['text'])
    print('所属专辑',cc)
def add_dz( objs ):
    cc= 0
    for obj in objs:
        havezj = False
        zbc = False
        cur_ss = set()
        for spo in obj['spo_list']:
            if spo['predicate']  == '总部地点':
                havezj = True
                zbc+=1
                cur_ss.add(spo['subject'])
        if len(cur_ss) > 0:
            cur_ss = list(cur_ss)
            cur_ss = sorted( cur_ss , key=lambda x:len(x),reverse=True)
            sub = cur_ss[0]
        ##清理总部地点
        zbobj = []
        nkw = ['位于','城市','大美']
        temp_list = []
        for spo in obj['spo_list']:
            addflag = True
            if spo['predicate'] == '总部地点':
                for nk in nkw:
                    if nk in spo['object']:
                        addflag = False
                        break
                if addflag:
                    zbobj.append(spo['object'])
            else:
                temp_list.append(spo)
        # obj['spo_list'] = temp_list
        if zbc > 1:
            # print(obj['text'],print_spo( obj['spo_list'] ))
            #清理，如果有总部，则保留总部之后的那些
            if '总部' in obj['text']:
                zbidx = obj['text'].find('总部')
                temp_obs = []
                for ob in zbobj:
                    if obj['text'].rfind( ob ) > zbidx:
                        temp_obs.append(ob)
                temp_obs = sorted( temp_obs , key=lambda x:len(x) , reverse=True)
                zbob = temp_obs[0]
                add_spo( obj , sub , zbob , '总部地点' )
                cc+=1
                print(obj['text'], print_spo(obj['spo_list']))
        # elif havezj:
        #     print(obj['text'], print_spo(obj['spo_list']))
    print('本次共清理总部地点2', cc)
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

                        print(new_spo,obj['text'])
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
                    print(obj['text'], '```````',sub, ob, obj['spo_list'])
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
                print(data['text'])
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

# def guoji_fix(result,or_objs):
#     """
#     对国籍进行修复
#     :param result:
#     :return:
#     """
#     count = 0
#     for idx,data in enumerate(result):
#         or_obj = or_objs[idx]
#         temp_spos = []
#         for spo in data['spo_list']:
#             rm_flag = False
#             if spo['predicate'] == '国籍':
#                 print(data['text'])
#                 # count += 1
#                 china_ents = [x for x in
#                               filter(lambda x: x != '中国' and '中国' in x, [pos['word'] for pos in or_obj['postag']])]
#                 cur_text = data['text']
#                 for ent in china_ents:
#                     cur_text = cur_text.replace(ent, '')
#                 if '中国' not in cur_text:
#                     # print(data['text'])
#                     rm_flag =True
#                     count+=1
#             if not rm_flag:
#                 temp_spos.append(spo)
#
#         data['spo_list'] = temp_spos
#     print(count)

# def guoji_fix2(result,or_objs):
#     """
#     对国籍进行修复
#     :param result:
#     :return:
#     """
#     count = 0
#     for idx,data in enumerate(result):
#         or_obj = or_objs[idx]
#         temp_spos = []
#         for spo in data['spo_list']:
#             rm_flag = False
#             if spo['predicate'] == '国籍':
#                 gj = spo['object']
#                 if gj == '中国':
#                     continue
#                 print(data['text'])
#                 # count += 1
#                 china_ents = [x for x in
#                               filter(lambda x: x != gj and gj in x, [pos['word'] for pos in or_obj['postag']])]
#                 cur_text = data['text']
#                 for ent in china_ents:
#                     cur_text = cur_text.replace(ent, '')
#                 if gj not in cur_text:
#                     # print(data['text'])
#                     rm_flag =True
#                     count+=1
#             if not rm_flag:
#                 temp_spos.append(spo)
#
#         data['spo_list'] = temp_spos
#     print(count)

def add_cpgs(objs):
    sp_cc = 0
    cc=0
    ## todo 把和传媒改了
    forbid_kws = ['》','制作','投资','在','担任','联手','怎么','摄制','电视剧','和传媒','旗下','庆祝','和平','自家','主演','台湾联合','和文化','佘诗曼', '刘松仁', '赵雅芝', '张智霖','五年前于正']
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
# def get_re():
#     re_souce_dict = {}
#     re_dict = {}
#     re_souce_dict['毕业院校'] = [['毕业于'], ["大学",'学院','中学','大专','初中','学校','小学']]
#     re_souce_dict['祖籍'] = [['祖籍'], [ '（',"，", '。']]
#     re_souce_dict['注册资本'] = [['注册资本增加到,','注册资本金为','注册资金为','注册资本为','注册资本：','注册资本金','注册资金','注册资本'], ['，','。']]
#     re_souce_dict['字'] = [['）字','，字'],
#                              [' ', '，', '。']]
#     re_souce_dict['号'] = [['）号','谥号','，号'],
#                           [' ', '，', '。']]
#     re_souce_dict['所属专辑'] = [ ('专辑《','》'),('《','》专辑'),('专辑：《','》') ]
#     re_souce_dict['简称'] = [['简称，','简称','简称为'], ["，",'）','或“','、','》']]
#     re_souce_dict['总部地点'] = [['坐落于', '总部位于','总部设立在','总部迁至','总部：','总部在','坐落在','总部设在'], ["，"]]
#     re_souce_dict['出品公司'] = [['是'], ["出品"]]
#
#     ##todo )?
#     def get_dika_list(re_list_source,):
#         re_list = []
#         for start in re_list_source[0]:
#             for end in re_list_source[1]:
#                 re_list.append(('(?<={}).*?(?={})'.format(start, end),end,start))
#         return re_list
#     def just_fill_re(  re_list_source):
#         re_list = []
#         for start,end in re_list_source:
#                 re_list.append(('(?<={}).*?(?={})'.format(start, end), end,start))
#         return re_list
#     for k , i in re_souce_dict.items():
#         if type(i[0]) is tuple:
#             re_dict[k] = just_fill_re(i)
#         else:
#             re_dict[k] = get_dika_list(i)
#     return re_dict,re_souce_dict
def get_ent_type(  ):
    type_dict = {}
    with open('D:/data/IE/all_50_schemas','r',encoding='utf8') as f:
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
                print(spo['subject'],spo['object'],spo['predicate'])
        else:
            print(spo['subject'], spo['object'], spo['predicate'])

def union_spo( objs , newobjs ):
    def trans( spo_list):
        return [ ( spo['subject'],spo['predicate'],spo['object'] ) for spo in spo_list ]
    def retrans( spo_list ):
        return [{'subject':spo[0], 'predicate':spo[1],'object':spo[2]}for spo in spo_list]
    for idx,obj in enumerate(objs):
        spo_list = set(trans( obj['spo_list'] ))
        new_spo_list = set(trans( newobjs[idx]['spo_list'] )) | spo_list
        obj['spo_list'] = retrans(new_spo_list)
def clean_spo_maunl( objs ):
    # return
    del_spo = [ ( '负空间','迪士尼','出品公司' ),
                ('东京爱情故事', '吕至杰', '作曲'),
                ('东京爱情故事', '葛大为', '作词'),
                ('最红', '张国荣', '歌手'),
                ('文艺心理学概论', '金老阅读了像《楚辞》这样承载着华夏文明精华的一本又一本巨著,创作了《文艺心理学概论》、《金开诚', '作者'),
                ( '金开诚学术文化随笔','刘宁','作者' ),( '文艺心理学概论','刘宁','作者' ),( '拂晓的赌博','格特兹·斯佩曼尼','导演' ) ]
    for obj in objs:
        temp_spos = []
        for spo in obj['spo_list']:
            flag = True
            for delspo in del_spo:
                if delspo[0] == spo['subject'] and delspo[1] == spo['object'] and delspo[2] == spo['predicate']:
                    print(spo,obj['text'])
                    flag=False
            if flag:
                temp_spos.append(spo)
        obj['spo_list'] = temp_spos
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

def get_part_result( part_file_base_path ,match_pat ):
    import os
    part_ids = os.listdir( part_file_base_path  )
    part_ids = [ x for x in filter( lambda x : match_pat in x , part_ids ) ]
    total_objs = None
    for id in part_ids:
        new_obsj = get_objs(part_file_base_path+id)
        clean_spo_maunl( new_obsj )
        if total_objs == None:
            total_objs =  new_obsj
        else:
            union_spo( total_objs , new_obsj  )
    return total_objs


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
        # rms = set([ t for t in filter( lambda x : '·' in x, get_rms( or_objs[idx]['postag'] ))])
        # eng_names = [ x.strip() for x in eng_names | rms ]
        # print(rms)
        for spo in obj['spo_list']:
            ents = [spo['object']]
            for en in eng_names:
                for ent in ents:
                    if ent in en and ent.strip() != en:
                        print(ent,'!!!',en,'!!!!',spo['object'],spo['predicate'],obj['text'])
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
    # if idx in [9741.333,1354,1731,2395,3292,3368,4202,3089,4368,4441,4792,5119,6099,7041,7358,7735,7981,8729,9741,9547,9414]:
    #     return ''
    rms_with_dun_hao = ''
    cur_rm = ''
    cond_set = set(['nr','nz'])
    # replace_dict = {'海娜':'海娜传媒','胡颖':'胡颖之','Johnny':'Johnny Yim','田雷领衔':'田雷','靖央':'井下靖央','乔舒亚·杰克逊领衔主演':'乔舒亚·杰克逊','铃木勇':'铃木勇马','柳善领':'柳善'
    #                 ,'芝崎弘':'芝崎弘记','Shelly':'Shelly佳','娜杰日达·米哈尔':'娜杰日达·米哈尔科娃','村上茉爱领衔主演':'村上茉爱'}
    replace_dict = {}
    no_kw = [ '故宫博物院','分别带来','孙悟空' ,'学报']
    no_ent_kw = set(['主演','领衔','光希','组','编','和','-','格律'])

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
                        print(1,e, '     ', obj['text'])
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
                                print(21, e, '     ', shumings, obj['text'])
                                havefix = True
                            else:
                                print('err', e, '     ', shumings, obj['text'])
                        elif text[eidx+len(e):eidx+len(e)+2] == '》》':
                            e =  e + '》'
                            if not shuming_count_is_match(e):
                                spo[k] = e
                                print(21, e, '     ', shumings, obj['text'])
                                havefix = True
                            else:
                                print('err', e, '     ', shumings, obj['text'])
                        if not havefix:
                            afg=False
                            print(23,e,'     ',shumings,obj['text'])
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
            # if idx in [9741.333, 1354, 1731, 2395, 3292, 3368, 4202, 3089, 4368, 4441, 4792, 5119, 6099, 7041, 7358,
            #            7735, 7981, 8729, 9741, 9547, 9414]:
            #     print(name_with_dunhao,'~~~~~~~~~~~~~~~~~~~',obj['text'])
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
                        cc += len(dif)
                        if addFlag:
                            for difent in dif:
                                    # if '领' in difent:
                                    #     print(difent)
                                    ## ['作者','主演','歌手','毕业院校','创始人','主角']
                                    if tp == 'sub'  and pred in ['毕业院校','创始人','主角'] :
                                        add_spo(obj, difent, another_ent, pred)
                                    elif tp == 'ob' and len( cur_subs ) == 1 :
                                        add_spo(obj, another_ent, difent, pred)
                            print_spo(obj['spo_list'])
                            print(idx, dif, obj['text'])
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
    kws = ['主演','爱情','：','国家','》',':','地区','类型','午夜','悬疑','5日','上映','豆瓣']
    text_nokws = ['/中国','bilibili','pan.baidu','豆瓣',']']
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

def check_birthday( objs ):
    cc = 0
    ## 检查电影上映时间
    temp_objs = []
    mask_kws = ['广播', '的播', '数播', '传播', '热播', '周五播']
    for obj in tqdm(objs):
        fg = False
        havebirth = False
        for spo in obj['spo_list']:
            if spo['subject_type'] == '影视作品':
                fg = True
            if spo['predicate'] == '制片人':
                havebirth = True
                # print( spo['subject'], spo['object'],obj['text'])
        if  fg and not havebirth  and  ( '制片' in obj['text'] ) :
            print(obj['text'])

        # print(obj['text'])

def check_mv_onshelf_date( objs ):
    cc=0
    ## 检查电影上映时间
    mask_kws =['广播','的播','数播','传播','热播','周五播','点播']
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
                            print(yearresult, cur_onshelf_date, subs, ctext)
                        else:
                            1
                            # if cur_onshelf_date != yearresult:
                            #     print(yearresult,cur_onshelf_date, subs, obj['text'])
                            #     cc+=1
                            # cc+=1
                        # print(yearresult,subs,obj['text'])
                        # yearresult = yearresult.group()
                        # if '于' + yearresult in reresult:
                        #     reresult = reresult[:reresult.find('于' + yearresult)]
                        # reresult = reresult.replace(yearresult, '')


                break
    print(cc)
# def sfind_ents_concat_by_tag( objs ,tag ):
#     for obj in objs:
#         rt = find_ents_concat_by_tag(obj,tag)
#         if len(rt) > 0:
#             print(rt,obj['text'])

# def check_name_with_dunhao( objs , orobjs ):
#     ## 处理人名被多个顿号连在一起，但是结果没有没有包含虽有被顿号连在一起的情况
#     cc=0
#     for idx, obj in enumerate(objs):
#         if '、' in obj['text']:
#             name_with_dunhao = get_name_contain_dunhao( idx  , obj['text'], orobjs[idx]['postag'] )


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
                    print_spo( obj['spo_list'] )
                    print(dif, sub_muti_shuminghao, curs, obj['text'])
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
                                print(difent, pred , ob , obj['text'])
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
                    print('&&', data['text'] ,'~' ,or_ent ,'~', ent_list )
                    # raise Exception('muti match')
                    continue
                temp_ent = ent
        if temp_ent == '':
            print(data['text'], or_ent, ent_list)
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

def add_gbz( objs ):
    cc = 0
    re_list, _ = get_re()
    need_remove_str = ['"', "“", "”", ":", '：', '《', "》"]
    for obj in objs:
        cur_s = set()
        if '改编' in obj['text']:
            havegbz = False
            for spo in obj['spo_list']:
                if spo['predicate'] == '改编自':
                    havegbz = True
                    break
                cur_s.add(spo['subject'])
            if not havegbz:
                1
                # print(obj['text'])
                subs = list(set(regex.findall("(?<=《).*?(?=》)", obj['text'])))
                if '同名' in obj['text'] or '原著' in obj['text'] or '原作' in obj['text'] :
                    if len(subs) == 1 and obj['text'].count(subs[0]) > 1 :
                        # if '改编自' in obj['text']:
                        #     print( subs[0], subs[0], obj['text'])
                        # else:
                        #     print('!',subs[0], subs[0], obj['text'])
                        add_spo(obj,subs[0],subs[0],'改编自')
                        print( subs[0] ,'~~~~~~~~~~~~~~~~~~~' , obj['text'] )
                        cc+=1
                # else:
                #     print(obj['text'])
    print('改编自清理了',cc)
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

# def cgetsm2(objs):
#     for obj in objs:
#         s = get_shuminghaos2(obj['text'])
#         if len(s) > 0:
#             print(s,obj['text'])

# ##添加地址
# def add_dz( objs ):
#     cc= 0
#     for obj in objs:
#         havezj = False
#         zbc = False
#         cur_ss = set()
#         for spo in obj['spo_list']:
#             if spo['predicate']  == '总部地点':
#                 havezj = True
#                 zbc+=1
#                 cur_ss.add(spo['subject'])
#         if len(cur_ss) > 0:
#             cur_ss = list(cur_ss)
#             cur_ss = sorted( cur_ss , key=lambda x:len(x),reverse=True)
#             sub = cur_ss[0]
#         ##清理总部地点
#         zbobj = []
#         nkw = ['位于','城市','大美']
#         temp_list = []
#         for spo in obj['spo_list']:
#             addflag = True
#             if spo['predicate'] == '总部地点':
#                 for nk in nkw:
#                     if nk in spo['object']:
#                         addflag = False
#                         break
#                 if addflag:
#                     zbobj.append(spo['object'])
#             else:
#                 temp_list.append(spo)
#         # obj['spo_list'] = temp_list
#         if zbc > 1:
#             # print(obj['text'],print_spo( obj['spo_list'] ))
#             #清理，如果有总部，则保留总部之后的那些
#             if '总部' in obj['text']:
#                 zbidx = obj['text'].find('总部')
#                 temp_obs = []
#                 for ob in zbobj:
#                     if obj['text'].rfind( ob ) > zbidx:
#                         temp_obs.append(ob)
#                 temp_obs = sorted( temp_obs , key=lambda x:len(x) , reverse=True)
#                 zbob = temp_obs[0]
#                 if add_spo( obj , sub , zbob , '总部地点' ):
#                     cc+=1
#                 print(obj['text'], print_spo(obj['spo_list']))
#         # elif havezj:
#         #     print(obj['text'], print_spo(obj['spo_list']))
#     print('本次共清理总部地点2', cc)
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
                        print("s~~~~~~~", text, "\n", spo, '\n', sm, subject)
                        clean_count += 1
                        edit=True
            if object not in shumings and  spo["object_type"] in change and check_is_all_in_shuminghao(text,shuminghao_tags,object):
                ##判断是否以被包含在其中
                for sm in shumings:
                    if sm.find(object) != -1 :
                        spo["object"] = sm
                        print("0~~~~~~~", text, "\n", spo, '\n', sm, object)
                        clean_count += 1
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
# def find_xx( objs ):
#     for obj in objs:
#         if 'x' in obj['text']:
#             print(obj['text'])
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
    maybe_dict,maybe_type_dict,maybe_dict_without_tp = get_maybe_objs(train_objs,dev_objs,'')
    add_no_sigs( objs , maybe_dict, maybe_type_dict, maybe_dict_without_tp, {})
    #
    # ## 书名号
    clean_shuminghao(objs)
    # # # ## 清理书名号错乱
    check_inner_shuminghao(objs)
    # # # # 简称
    add_jiancheng2( objs )
    # # # # # 总部地点
    add_dz2( objs )
    # # ## 清理没有被预测完整的带空格的英文名
    clean_english_name_with_space( objs )
    # # ## 补全出品公司
    add_cpgs(objs)
    # # # # 清理国籍
    guoji_fix(objs, or_test_objs)

    # # # ## 上述清理完之后，会存在一些重复或者有子串包含的spo，调用最长子串匹配清理一下
    check_mv_onshelf_date( objs )
    # # # ## 清理被顿号连起来但是没被预测出来的书名号，par2
    check_shuming_with_dunhao2(objs, get_mutis_shuminghao)
    check_shuming_with_dunhao2(objs, get_mutis_shuminghao2)
    # # # # ## 清理被顿号连起来但是没被预测出来的姓名 这里面硬编码比较多，新数据可能出错较多
    check_name_concat_with_tag(objs, or_test_objs, '、', get_name_concat_with_tag)
    check_name_concat_with_tag(objs, or_test_objs, '/', find_ents_concat_by_tag)
    find_max_len_ent( objs )





## 获取原始被预测文件
# mode = 'test1'
# if mode == 'test1':
#     # part_file_base_path = 'E:/competionfile/信息抽取/new/sujianlin/result/'
#     # # 获取原始33份part预测结/
#     # union_results = get_part_result(part_file_base_path,'test_1')
#     # data_path = '../datasets'
#     # train_objs = get_objs(data_path+'/train_data.json')
#     # dev_objs = get_objs(data_path+'/dev_data.json')
#     or_test_objs = get_objs('E:/competionfile/信息抽取/new/sujianlin/datasets/test1_data_postag.json')
#     # objs = get_objs('E:/competionfile/信息抽取/new/sujianlin/result/final_result_5_13_9votes_45_models_fix_23934.json')
#     # objs = get_objs('E:/competionfile/信息抽取/new/sujianlin/result/final_result_5_4_fix_23373_23445.json')
#     # final_result_5_13_24477_8_45
#     objs = get_objs('E:/competionfile/信息抽取/new/sujianlin/result/final_result_5_13_24477_8_45.json')
#
# else:
#     # part_file_base_path = 'E:/competionfile/信息抽取/new/sujianlin/result/testb/'
#     # # 获取原始33份part预测结/
#     # union_results = get_part_result(part_file_base_path,'test_2')
#     # data_path = '../datasets'
#     # train_objs = get_objs(data_path+'/train_data.json')
#     # dev_objs = get_objs(data_path+'/dev_data.json')
#     or_test_objs = get_objs('E:/competionfile/信息抽取/new/sujianlin/datasets/test_data_postag.json')
#     objs = get_objs('E:/competionfile/信息抽取/new/sujianlin/result/final_result_B_5_16_251226_9votes_45.json')
#
# do_clean_515( objs , or_test_objs ,None,None )
# test_do_clean_515( objs , or_test_objs ,None,None )
# do_clean_515( objs , or_test_objs ,train_objs,dev_objs )



# add_dy( objs , or_test_objs )
# add_dz(objs)
# add_dz2(objs)
# add_jiancheng2( objs )
# find_wrong_spo8(objs)
# add_type(objs)
# ## 改编自
# add_gbz(objs)
# ## 手动清理一些错误的spo，
# clean_spo_maunl(objs)
# ## 清理被顿号连起来但是没被预测出来的书名号，par1 ， and 这里利用到了原始33份未融合预测结果，对预测结果进行了一定的手动清理，在新数据上会有一些错误
# ## 清理被顿号连起来但是没被预测出来的书名号，par2
# check_shuming_with_dunhao1(objs,union_results)
# check_shuming_with_dunhao2(objs)
# ## 清理被顿号连起来但是没被预测出来的姓名 这里面硬编码比较多，新数据可能出错较多
# check_name_with_dunhao(objs, or_test_objs)
# check_inner_shuminghao(objs)
# ## 清理没有被预测完整的带空格的英文名
# clean_english_name_with_space( objs )
# guoji_fix( objs , or_test_objs )
# ## 补全出品公司
# add_cpgs(objs)
# ## 上述清理完之后，会存在一些重复或者有子串包含的spo，调用最长子串匹配清理一下
# find_max_len_ent(objs)


# do_clean_515()