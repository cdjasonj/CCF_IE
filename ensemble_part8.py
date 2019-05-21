
#! -*- coding:utf-8 -*-

# nohup python bert_so_s.py  >> bert_so_s.log 2>&1 &
## f1: 0.8038, precision: 0.8205, recall: 0.7877, best f1: 0.8038
import codecs
import json
import os
from random import choice, sample
import keras
from keras_bert.layers import *
from keras_bert import Tokenizer
from keras_bert import get_model, load_model_weights_from_checkpoint
from tqdm import tqdm
from keras.callbacks import LearningRateScheduler

model_name = 'bert_so_s'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
train_data = json.load(open('../input/train_data_me.json'))
dev_data = json.load(open('../input/dev_data_me.json'))
test_data = json.load(open('../input/test_data_me2.json'))
id2predicate, predicate2id = json.load(open('../input/all_50_schemas_me_overlap.json'))
id2predicate = {int(i): j for i, j in id2predicate.items()}
id2char, char2id = json.load(open('../input/all_chars_me.json'))
# word2id = json.load(open('input/word2id.json'))

from copy import deepcopy

char_size = 128
num_classes = len(id2predicate)
debug = False
ML = 180

config_path = '/home/ccit/tkhoon/baiduie/sujianlin/myself_model/bert/chinese_L-12_H-768_A-12/bert_config.json'
checkpoint_path = '/home/ccit/tkhoon/baiduie/sujianlin/myself_model/bert/chinese_L-12_H-768_A-12/bert_model.ckpt'
dict_path = '/home/ccit/tkhoon/baiduie/sujianlin/myself_model/bert/chinese_L-12_H-768_A-12/vocab.txt'
#
# config_path = '/home/ccit22/m_minbo/chinese_L-12_H-768_A-12/bert_config.json'
# checkpoint_path = '/home/ccit22/m_minbo/chinese_L-12_H-768_A-12/bert_model.ckpt'
# dict_path = '/home/ccit22/m_minbo/chinese_L-12_H-768_A-12/vocab.txt'


if debug:
    train_data = sample(train_data, 40000)
    dev_data = dev_data[:8000]
    test_data = test_data[:200]

def seq_padding(X):
    # L = [len(x) for x in X]
    # ML =
    return [x + [0] * (ML - len(x)) if len(x) < ML else x[:ML] for x in X]

class test_data_generator:
    def __init__(self, data, batch_size=64):
        self.data = data
        self.batch_size = batch_size
        self.steps = len(self.data) // self.batch_size
        if len(self.data) % self.batch_size != 0:
            self.steps += 1
        self.token_dict = {}
        with codecs.open(dict_path, 'r', 'utf8') as reader:
            for line in reader:
                token = line.strip()
                self.token_dict[token] = len(self.token_dict)
        self.tokenizer = Tokenizer(self.token_dict)
        self.cache_data = []
        self.vocabs = set()
        with open(dict_path, encoding='utf8') as f:
            for l in f:
                self.vocabs.add(l.replace('\n', ''))

    def __len__(self):
        return self.steps

    def encode(self, text):
        tokens = ['[CLS]'] + [ch if ch in self.vocabs else '[UNK]' for ch in text] + ['[SEP]']
        return self.tokenizer._convert_tokens_to_ids(tokens), [0] * len(tokens)

    def __iter__(self):
        while True:
            idxs = [i for i in range(len(self.data))]
            BERT_INPUT0, BERT_INPUT1, S, ORDATA = [], [], [], []
            for i in idxs:
                d = deepcopy(self.data[i])
                text = d['text']
                or_text = text
                d['text'] = '^' + text + '^'
                indices, segments = self.encode(or_text)
                BERT_INPUT0.append(indices)
                BERT_INPUT1.append(segments)
                s = [0] * len(text)
                S.append(s)
                ORDATA.append(d)
                # import ipdb
                # ipdb.set_trace()
                if len(S) == self.batch_size or i == idxs[-1]:
                    BERT_INPUT0 = np.array(seq_padding(BERT_INPUT0))
                    BERT_INPUT1 = np.array(seq_padding(BERT_INPUT1))
                    S = np.array(seq_padding(S))

                    # import ipdb
                    # ipdb.set_trace()
                    # print('~~~~~~~~~~~~~~~~~~~~~~~', BERT_INPUT0.shape, BERT_INPUT1.shape, S1.shape, S2.shape)
                    yield [BERT_INPUT0, BERT_INPUT1, S, ORDATA]
                    BERT_INPUT0, BERT_INPUT1, S, ORDATA = [], [], [], []


class MaskedConv1D(keras.layers.Conv1D):

    def __init__(self, **kwargs):
        super(MaskedConv1D, self).__init__(char_size, 3, activation='relu', padding='same')
        self.supports_masking = True

    def compute_mask(self, inputs, mask=None):
        return mask

    def call(self, inputs, mask=None):
        if mask is not None:
            mask = K.cast(mask, K.floatx())
            inputs *= K.expand_dims(mask, axis=-1)
        return super(MaskedConv1D, self).call(inputs)


class MaskLSTM(keras.layers.CuDNNLSTM):

    def __init__(self, **kwargs):
        super(MaskLSTM, self).__init__(char_size, return_sequences=True)
        self.supports_masking = True

    def compute_mask(self, inputs, mask=None):
        return mask

    def call(self, inputs, mask=None, training=None, initial_state=None):
        if mask is not None:
            mask = K.cast(mask, K.floatx())
            inputs *= K.expand_dims(mask, axis=-1)
        return super(MaskLSTM, self).call(inputs)


class MaskFlatten(keras.layers.Flatten):

    def __init__(self, **kwargs):
        super(MaskFlatten, self).__init__(**kwargs)
        self.supports_masking = True

    def compute_mask(self, inputs, mask=None):
        return mask

    def call(self, inputs, mask=None):
        # if mask is not None:
        # mask = K.cast(mask, K.floatx())
        # inputs *= K.expand_dims(mask, axis=-1)
        return super(MaskFlatten, self).call(inputs)  # 调用父类的call ,然后传入inputs


class MaskRepeatVector(keras.layers.RepeatVector):

    def __init__(self, n, **kwargs):
        super(MaskRepeatVector, self).__init__(n, **kwargs)
        self.supports_masking = True

    def compute_mask(self, inputs, mask=None):
        return mask

    def call(self, inputs, mask=None):
        # if mask is not None:
        # mask = K.cast(mask, K.floatx())
        # inputs *= K.expand_dims(mask, axis=-1)
        return super(MaskRepeatVector, self).call(inputs)


class MaskPermute(keras.layers.Permute):

    def __init__(self, dims, **kwargs):
        super(MaskPermute, self).__init__(dims, **kwargs)
        self.supports_masking = True

    def compute_mask(self, inputs, mask=None):
        return mask

    def call(self, inputs, mask=None):
        # if mask is not None:
        #     mask = K.cast(mask, K.floatx())
        # inputs *= K.expand_dims(mask, axis=-1)
        return super(MaskPermute, self).call(inputs)


class data_generator:
    def __init__(self, data, batch_size=64):
        self.data = data
        self.batch_size = batch_size
        self.steps = len(self.data) // self.batch_size
        if len(self.data) % self.batch_size != 0:
            self.steps += 1
        self.token_dict = {}
        with codecs.open(dict_path, 'r', 'utf8') as reader:
            for line in reader:
                token = line.strip()
                self.token_dict[token] = len(self.token_dict)
        self.tokenizer = Tokenizer(self.token_dict)
        self.cache_data = []
        self.vocabs = set()
        with open(dict_path, encoding='utf8') as f:
            for l in f:
                self.vocabs.add(l.replace('\n', ''))

    def init_cache_data(self):
        cur_step = 0
        for i, t in enumerate(self.get_next()):
            if i >= self.steps:
                break
            cur_step += 1
            self.cache_data.append(t)

    def __len__(self):
        return self.steps

    def encode(self, text):
        tokens = ['[CLS]'] + [ch if ch in self.vocabs else '[UNK]' for ch in text] + ['[SEP]']
        return self.tokenizer._convert_tokens_to_ids(tokens), [0] * len(tokens)

    # def __iter__(self):
    #     while True:
    #         self.init_cache_data()
    #         for i in range(0,self.steps):
    #             yield self.cache_data[i],None
    def __iter__(self):
        while True:
            idxs = [i for i in range(len(self.data))]
            np.random.shuffle(idxs)
            BERT_INPUT0, BERT_INPUT1, S, K1, K2, O1, O2, = [], [], [], [], [], [], []
            for i in idxs:
                d = self.data[i]
                text = d['text']
                or_text = text
                text = '^' + text + '^'
                text = text
                items = {}
                for sp in d['spo_list']:
                    subjectid = text.find(sp[0])
                    objectid = text.find(sp[2])
                    # import ipdb
                    # ipdb.set_trace()
                    if subjectid != -1 and objectid != -1:
                        key = (subjectid, subjectid + len(sp[0]))
                        if key not in items:
                            items[key] = []
                        flag = True
                        if items:
                            for tmp in list(items.keys()):
                                # print(1)
                                if (tmp == key):  # 先匹配相同主语，因为宾语有多个需要循环判断
                                    # print(1)
                                    for sample in items[tmp]:
                                        if (sample[0], sample[1]) == (objectid, objectid + len(sp[2])):  # 相同实体对
                                            if id2predicate[sample[2]] + '-' + sp[1] in ['作曲-歌手', '歌手-作曲']:
                                                items[tmp].remove(sample)
                                                items[key].append((objectid,
                                                                   objectid + len(sp[2]),
                                                                   50))
                                                flag = False
                                                # import ipdb
                                                # ipdb.set_trace()
                                            elif id2predicate[sample[2]] + '-' + sp[1] in ['导演-编剧', '编剧-导演']:
                                                items[tmp].remove(sample)
                                                items[key].append((objectid,
                                                                   objectid + len(sp[2]),
                                                                   51))
                                                flag = False
                                                # import ipdb
                                                # ipdb.set_trace()
                        # 如果没有修改再添加，否则添加重复了。
                        if flag:
                            items[key].append((objectid,
                                               objectid + len(sp[2]),
                                               predicate2id[sp[1]]))
                if items:
                    indices, segments = self.encode(or_text)
                    BERT_INPUT0.append(indices)
                    BERT_INPUT1.append(segments)
                    s1, s2 = [0] * len(text), [0] * len(text)
                    for j in items:
                        s1[j[0]] = 1
                        s2[j[1] - 1] = 1
                    s = [0] * len(text)
                    for idx in range(len(s1)):
                        if s1[idx] == 1:
                            s[idx] = 1
                        if s2[idx] == 1:
                            s[idx] = 2
                    k1, k2 = choice(list(items.keys()))
                    o1, o2 = [0] * len(text), [0] * len(text)  # 0是unk类（共49+1个类）
                    for j in items[(k1, k2)]:
                        o1[j[0]] = j[2]
                        o2[j[1] - 1] = j[2]
                    S.append(s)
                    K1.append([k1])
                    K2.append([k2 - 1])
                    O1.append(o1)
                    O2.append(o2)
                    if len(S) == self.batch_size or i == idxs[-1]:
                        BERT_INPUT0 = np.array(seq_padding(BERT_INPUT0))
                        BERT_INPUT1 = np.array(seq_padding(BERT_INPUT1))
                        S = np.array(seq_padding(S))
                        O1 = np.array(seq_padding(O1))
                        O2 = np.array(seq_padding(O2))
                        K1, K2 = np.array(K1), np.array(K2)
                        yield [BERT_INPUT0, BERT_INPUT1, S, K1, K2, O1, O2], None
                        BERT_INPUT0, BERT_INPUT1, S, K1, K2, O1, O2 = [], [], [], [], [], [], []


from keras.layers import *
import keras.backend as K
from keras.callbacks import Callback


def seq_gather(x):
    """seq是[None, seq_len, s_size]的格式，
    idxs是[None, 1]的格式，在seq的第i个序列中选出第idxs[i]个向量，
    最终输出[None, s_size]的向量。
    """
    seq, idxs = x
    idxs = K.cast(idxs, 'int32')
    batch_idxs = K.arange(0, K.shape(seq)[0])
    batch_idxs = K.expand_dims(batch_idxs, 1)
    idxs = K.concatenate([batch_idxs, idxs], 1)
    return K.tf.gather_nd(seq, idxs)


def seq_and_vec(x):
    """seq是[None, seq_len, s_size]的格式，
    vec是[None, v_size]的格式，将vec重复seq_len次，拼到seq上，
    得到[None, seq_len, s_size+v_size]的向量。
    """
    seq, vec = x
    vec = K.expand_dims(vec, 1)
    vec = K.zeros_like(seq[:, :, :1]) + vec
    return K.concatenate([seq, vec], 2)


def seq_maxpool(x):
    """seq是[None, seq_len, s_size]的格式，
    mask是[None, seq_len, 1]的格式，先除去mask部分，
    然后再做maxpooling。
    """
    seq, mask = x
    seq -= (1 - mask) * 1e10
    return K.max(seq, 1)


def build_model_from_config(config_file,
                            checkpoint_file,
                            training=False,
                            trainable=False,
                            seq_len=None,
                            ):
    """Build the model from config file.

    :param config_file: The path to the JSON configuration file.
    :param training: If training, the whole model will be returned.
    :param trainable: Whether the model is trainable.
    :param seq_len: If it is not None and it is shorter than the value in the config file, the weights in
                    position embeddings will be sliced to fit the new length.
    :return: model and config
    """
    with open(config_file, 'r') as reader:
        config = json.loads(reader.read())
    if seq_len is not None:
        config['max_position_embeddings'] = min(seq_len, config['max_position_embeddings'])
    if trainable is None:
        trainable = training
    model = get_model(
        token_num=config['vocab_size'],
        pos_num=config['max_position_embeddings'],
        seq_len=config['max_position_embeddings'],
        embed_dim=config['hidden_size'],
        # transformer_num= 8 ,
        transformer_num=config['num_hidden_layers'],
        head_num=config['num_attention_heads'],
        feed_forward_dim=config['intermediate_size'],
        training=False,
        trainable=True,
    )

    # SetLearningRate(model,0.00001,True)
    inputs, outputs = model
    t_in = Input(shape=(None,))
    s_in = Input(shape=(None,))
    k1_in = Input(shape=(1,))
    k2_in = Input(shape=(1,))
    o1_in = Input(shape=(None,))
    o2_in = Input(shape=(None,))

    t, s, k1, k2, o1, o2 = t_in, s_in, k1_in, k2_in, o1_in, o2_in

    mask = Lambda(lambda x: K.cast(K.greater(K.expand_dims(x, 2), 0), 'float32'))(inputs[0])
    outputs = Dropout(0.5)(outputs)

    # lstm1 = MaskLSTM()(outputs)
    # # lstm1 = BatchNormalization()(lstm1)
    # lstm2 = MaskLSTM()(lstm1)
    # lstm2 = BatchNormalization()(lstm2)

    attention = TimeDistributed(Dense(1, activation='tanh'))(outputs)
    attention = MaskFlatten()(attention)
    attention = Activation('softmax')(attention)
    attention = MaskRepeatVector(config['hidden_size'])(attention)
    attention = MaskPermute([2, 1])(attention)
    sent_representation = multiply([outputs, attention])
    attention = Lambda(lambda xin: K.sum(xin, axis=1))(sent_representation)
    # import ipdb
    # ipdb.set_trace()
    # max_pool = MaskedGlobalMaxPool1D()(outputs) #[batch_size,sequence_length,]
    t_dim = K.int_shape(outputs)[-1]

    h = Lambda(seq_and_vec, output_shape=(None, t_dim * 2))([outputs, attention])
    # h = Conv1D(char_size, 3, activation='relu', padding='same')(h)
    conv1 = MaskedConv1D()(h)
    ps = Dense(3, activation='softmax')(conv1)
    subject_model = keras.models.Model([inputs[0], inputs[1]], [ps])  # 预测subject的模型
    ##预测o1,o2
    k1 = Lambda(seq_gather, output_shape=(t_dim,))([outputs, k1])
    k2 = Lambda(seq_gather, output_shape=(t_dim,))([outputs, k2])
    k = Concatenate()([k1, k2])

    h = Lambda(seq_and_vec, output_shape=(None, t_dim * 2))([outputs, attention])
    h = Lambda(seq_and_vec, output_shape=(None, t_dim * 4))([h, k])
    h = Concatenate(axis=-1)([h, conv1])
    h = MaskedConv1D()(h)
    po1 = Dense(num_classes + 1, activation='softmax')(h)
    po2 = Dense(num_classes + 1, activation='softmax')(h)

    object_model = keras.models.Model([inputs[0], inputs[1], k1_in, k2_in], [po1, po2])  # 输入text和subject，预测object及其关系

    train_model = keras.models.Model(inputs=[inputs[0], inputs[1], s_in, k1_in, k2_in, o1_in, o2_in],
                                     outputs=[ps, po1, po2])

    s_loss = K.sparse_categorical_crossentropy(s, ps)
    s_loss = K.sum(s_loss * mask[:, :, 0]) / K.sum(mask)

    o1_loss = K.sparse_categorical_crossentropy(o1, po1)
    o1_loss = K.sum(o1_loss * mask[:, :, 0]) / K.sum(mask)
    o2_loss = K.sparse_categorical_crossentropy(o2, po2)
    o2_loss = K.sum(o2_loss * mask[:, :, 0]) / K.sum(mask)
    train_model.add_loss(s_loss + o1_loss + o2_loss)
    train_model.summary()
    train_model.compile(
        optimizer=keras.optimizers.Adam(lr=3e-5),
        # loss=(s1_loss + s2_loss)
    )

    load_model_weights_from_checkpoint(train_model, config, checkpoint_file, training)
    return train_model, subject_model, object_model


def extract_items_batch2(datas, batch_start_idx, total_r):
    R = set()
    text_in = []
    _b1 = []
    _b2 = []
    _s1 = []
    _s2 = []
    _slen = []
    # import ipdb
    # ipdb.set_trace()
    for idx in range(0, len(datas[0])):
        text_in.append(datas[3][idx]['text'])
        _b1.append(datas[0][idx])
        _b2.append(datas[1][idx])
        _s1.append(datas[1][idx])
        _s2.append(datas[2][idx])
        _slen.append(len(datas[3][idx]['text']))
    # _s = np.array([_b1,_b2,_s1,_s2])
    _b1 = np.array(_b1)
    _b2 = np.array(_b2)
    _s1 = np.array(_s1)
    _s2 = np.array(_s2)

    _ks = subject_model.predict([_b1, _b2])
    _sk1, _sk2 = [], []
    _2b1, _2b2 = [], []
    _subjects = []
    sidxs = []
    idxs = []
    cur_subjects = set()
    for idx in range(len(_ks)):
        _k = _ks[idx]
        _k = np.argmax(_k, axis=-1)
        for i, s1 in enumerate(_k):
            if i >= _slen[idx]:
                break
            if s1 == 1:
                _subject = ''
                for j, s2 in enumerate(_k[i + 1:]):
                    if s2 == 2:
                        _subject = text_in[idx][i: i + j + 2]
                        _2b1.append(_b1[idx])
                        _2b2.append(_b2[idx])
                        _sk1.append(i)
                        _sk2.append(i + j + 1)
                        sidxs.append(len(_subjects))
                        _subjects.append(_subject)
                        idxs.append(idx)
                        break
    _sk1 = np.array(_sk1)
    _sk2 = np.array(_sk2)
    _2b1 = np.array(_2b1)
    _2b2 = np.array(_2b2)
    if len(_2b1) == 0:
        return set(), set()
    _o1s, _o2s = object_model.predict([_2b1, _2b2, _sk1, _sk2])
    for idx in range(0, len(_o1s)):
        _o1 = _o1s[idx]
        _o2 = _o2s[idx]
        _o1, _o2 = np.argmax(_o1, 1), np.argmax(_o2, 1)
        for i, _oo1 in enumerate(_o1):
            if _oo1 > 0:
                for j, _oo2 in enumerate(_o2[i:]):
                    if _oo2 == _oo1:
                        _object = text_in[idxs[idx]][i: i + j + 1]
                        _predicate = id2predicate[_oo1]
                        # 修改的部分
                        pre_spo_list = total_r.get(batch_start_idx + idxs[idx], set())
                        if _predicate in ['作曲-歌手', '歌手-作曲']:
                            R.add((_subjects[sidxs[idx]], '作曲', batch_start_idx + idxs[idx]))
                            R.add((_subjects[sidxs[idx]], '歌手', batch_start_idx + idxs[idx]))
                            pre_spo_list.add((_subjects[sidxs[idx]], '作曲', _object))
                            pre_spo_list.add((_subjects[sidxs[idx]], '歌手', _object))
                        elif _predicate in ['编剧-导演', '导演-编剧']:
                            R.add((_subjects[sidxs[idx]], '编剧', batch_start_idx + idxs[idx]))
                            R.add((_subjects[sidxs[idx]], '导演', batch_start_idx + idxs[idx]))
                            pre_spo_list.add((_subjects[sidxs[idx]], '编剧', _object))
                            pre_spo_list.add((_subjects[sidxs[idx]], '导演', _object))
                        else:
                            R.add((_subjects[sidxs[idx]], _predicate, batch_start_idx + idxs[idx]))
                            pre_spo_list.add((_subjects[sidxs[idx]], _predicate, _object))

                        # R.add((_subjects[sidxs[idx]], _predicate, _object, batch_start_idx + idxs[idx]))
                        # pre_spo_list.add((_subjects[sidxs[idx]], _predicate, _object))
                        total_r[batch_start_idx + idxs[idx]] = pre_spo_list
                        break
    return R, cur_subjects

def comput_f1(dev_file):
    """
    对dev进行测评
    P_all = right_num_all / pred_num_all  # 准确率
    R_all = right_num_all / true_num_all  # 召回率
    F_all = 2 * P_all * R_all / (P_all + R_all)  # F值
    :param dev_file:
    :return:
    """
    right = 1e-10
    pred = 1e-10
    true = 1e-10
    dev_pred = []
    with open(dev_file,'r',encoding='utf-8') as fr:
        for line in fr:
            dev_pred.append(json.loads(line))
    for idx in range(len(dev_data)):
        pred_data = dev_pred[idx]
        true_data = dev_data[idx]
        true_spo = []
        pred_spo = []
        for spo in true_data['spo_list']:
            true_spo.append((spo[0],spo[1],spo[2]))
        for spo in pred_data['spo_list']:
            pred_spo.append((spo['subject'],spo['predicate'],spo['object']))
        true+= len(list(set(true_spo)))
        pred+= len(list(set(pred_spo)))
        right+= len((set(true_spo))&(set(pred_spo)))
    P = right/pred
    R = right / true
    F = 2*P*R/(R+P)
    return P,R,F

def predict_test_batch(mode):
    if mode == 'test':
        weight_file = weight_name
        train_model.load_weights(weight_file)
        batch_size = 1000
        test_data_gen = test_data_generator(test_data, batch_size)
        total_r = {}
        for batch_id, batch_data in tqdm(enumerate(test_data_gen)):
            if batch_id > test_data_gen.steps:
                break
            batch_start_idx = batch_id * batch_size
            R, R_cur_subs = extract_items_batch2(batch_data, batch_start_idx, total_r)

        with open(test_result, "w", encoding="utf8") as f:
            for i, d in tqdm(enumerate(test_data)):
                text = d["text"]
                spo_list = []
                for sp in total_r.get(i, set()):
                    spo = {}
                    spo['predicate'] = sp[1]
                    spo['subject'] = sp[0]
                    spo['subject_type'] = '0'
                    spo['object_type'] = '0'
                    spo['object'] = sp[2]
                    spo_list.append(spo)
                f.write(json.dumps({"text": text, "spo_list": spo_list}, ensure_ascii=False) + "\n")

    else:
        #对dev进行测评
        batch_size = 1000
        dev_data_gen = test_data_generator(dev_data, batch_size)
        total_r = {}
        for batch_id, batch_data in tqdm(enumerate(dev_data_gen)):
            if batch_id > dev_data_gen.steps:
                break
            batch_start_idx = batch_id * batch_size
            R, R_cur_subs = extract_items_batch2(batch_data, batch_start_idx, total_r)

        with open(dev_result, "w", encoding="utf8") as f:
            for i, d in tqdm(enumerate(dev_data)):
                text = d["text"]
                spo_list = []
                for sp in total_r.get(i, set()):
                    spo = {}
                    spo['predicate'] = sp[1]
                    spo['subject'] = sp[0]
                    spo['subject_type'] = '0'
                    spo['object_type'] = '0'
                    spo['object'] = sp[2]
                    spo_list.append(spo)
                f.write(json.dumps({"text": text, "spo_list": spo_list}, ensure_ascii=False) + "\n")

        return comput_f1(dev_result)


def scheduler(epoch):
    # 每隔1个epoch，学习率减小为原来的1/2
    # if epoch % 100 == 0 and epoch != 0:
    #再epoch > 3的时候,开始学习率递减,每次递减为原来的1/2,最低为2e-6
    if epoch+1 <= 2:
        return K.get_value(train_model.optimizer.lr)
    else:
        lr = K.get_value(train_model.optimizer.lr)
        lr = lr*0.5
        if lr < 2e-6:
            return 2e-6
        else:
            return lr


for i in range(2):
    train_model, subject_model, object_model = build_model_from_config(config_path, checkpoint_path, seq_len=180)
    # train_D = data_generator(train_data, 32)
    # reduce_lr = LearningRateScheduler(scheduler, verbose=1)
    # best_f1 = 0
    if i == 0:
        weight_name = 'version1_22.weights'
        dev_result = 'version1_dev22.json'
        test_result = 'test_B/version1_22_2.json'
    else:
        weight_name = 'version1_23.weights'
        dev_result = 'version1_dev23.json'
        test_result = 'test_B/version1_23_2.json'

    # for i in range(1,7):

        # train_model.fit_generator(train_D.__iter__(),
        #                           steps_per_epoch=len(train_D),
        #                           epochs=1,
        #                           callbacks=[reduce_lr]
        #                           )
        # if (i) % 2 == 0 : #两次对dev进行一次测评,并对dev结果进行保存
        #     print('进入到这里了哟~')
            # P, R, F = predict_test_batch('dev')
            # if F > best_f1 :
            #     train_model.save_weights(weight_name)
            #     print('当前第{}个epoch，准确度为{},召回为{},f1为：{}'.format(i,P,R,F))
    predict_test_batch('test')
    K.clear_session()