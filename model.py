#! -*- coding:utf-8 -*-
# nohup python bert_so_s.py  >> bert_so_s.log 2>&1 &
import codecs
import json
import os
from random import choice, sample
import keras
from keras_bert import Tokenizer
from keras_bert import get_model, load_model_weights_from_checkpoint
from tqdm import tqdm
from keras.callbacks import LearningRateScheduler
from copy import deepcopy
import keras.backend as K
from keras.layers import *
from keras.callbacks import Callback

train_data = json.load(open('inputs/train_data_me.json'))
dev_data = json.load(open('inputs/dev_data_me.json'))
test_data = json.load(open('inputs/test_data_me2.json'))
id2predicate, predicate2id = json.load(open('inputs/all_50_schemas_me.json'))
id2predicate = {int(i): j for i, j in id2predicate.items()}
id2char, char2id = json.load(open('inputs/all_chars_me.json'))

char_size = 128
num_classes = len(id2predicate)
debug = False
ML = 180

config_path = 'bert/chinese_L-12_H-768_A-12/bert_config.json'
checkpoint_path = 'bert/chinese_L-12_H-768_A-12/bert_model.ckpt'
dict_path = 'bert/chinese_L-12_H-768_A-12/vocab.txt'

if debug:
    train_data = sample(train_data, 200)
    dev_data = dev_data[:200]
    test_data = test_data[:200]

def train(gpu_num,ensemble_num,last_ensemble_num):

    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_num)

    def seq_padding(X):
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
            with open(dict_path,
                      encoding='utf8') as f:
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
            with open(dict_path,
                      encoding='utf8') as f:
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
                        if subjectid != -1 and objectid != -1:
                            key = (subjectid, subjectid + len(sp[0]))
                            if key not in items:
                                items[key] = []
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

        attention = TimeDistributed(Dense(1, activation='tanh'))(outputs)
        attention = MaskFlatten()(attention)
        attention = Activation('softmax')(attention)
        attention = MaskRepeatVector(config['hidden_size'])(attention)
        attention = MaskPermute([2, 1])(attention)
        sent_representation = multiply([outputs, attention])
        attention = Lambda(lambda xin: K.sum(xin, axis=1))(sent_representation)

        t_dim = K.int_shape(outputs)[-1]
        h = Lambda(seq_and_vec, output_shape=(None, t_dim * 2))([outputs, attention])
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
        for idx in range(0, len(datas[0])):
            text_in.append(datas[3][idx]['text'])
            _b1.append(datas[0][idx])
            _b2.append(datas[1][idx])
            _s1.append(datas[1][idx])
            _s2.append(datas[2][idx])
            _slen.append(len(datas[3][idx]['text']))
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
                            R.add((_subjects[sidxs[idx]], _predicate, _object, batch_start_idx + idxs[idx]))
                            pre_spo_list = total_r.get(batch_start_idx + idxs[idx], set())
                            pre_spo_list.add((_subjects[sidxs[idx]], _predicate, _object))
                            total_r[batch_start_idx + idxs[idx]] = pre_spo_list
                            break
        return R, cur_subjects

    class Evaluate(Callback):
        def __init__(self,part):
            self.F1 = []
            self.best = 0.
            self.part = part

        def on_epoch_end(self, epoch, logs=None):
            f1, precision, recall, _, _, _ = self.evaluate2()
            self.F1.append(f1)
            if f1 > self.best:
                self.best = f1
                train_model.save_weights('models/ensemble_model{}.weights'.format(self.part))
            print('f1: %.4f, precision: %.4f, recall: %.4f, best f1: %.4f\n' % (f1, precision, recall, self.best))

        def evaluate2(self):
            A, B, C = 1e-10, 1e-10, 1e-10
            result_dict = {}
            A_subs, B_subs, C_subs = 1e-10, 1e-10, 1e-10
            total_t = {}
            total_r = {}

            def get_batch_T(batch_data, start_idx):
                T = list()

                for idx in range(0, len(batch_data[0])):
                    total_t[start_idx + idx] = [(i[0], i[1], i[2]) for i in batch_data[3][idx]['spo_list']]
                    T.extend([(i[0], i[1], i[2], start_idx + idx) for i in batch_data[3][idx]['spo_list']])
                return set(T)

            batch_size = 1000
            dev_data_gen = test_data_generator(dev_data, batch_size)

            for batch_id, batch_data in tqdm(enumerate(dev_data_gen)):
                if batch_id > dev_data_gen.steps:
                    break
                batch_start_idx = batch_id * batch_size
                R, R_cur_subs = extract_items_batch2(batch_data, batch_start_idx, total_r)
                T = get_batch_T(batch_data, batch_start_idx)
                A += len(R & T)
                B += len(R)
                C += len(T)

                ##按id顺序存储起来
            result_dict = (total_r, total_t)

            return 2 * A / (B + C), A / B, A / C, 2 * A_subs / (
                    B_subs + C_subs), A_subs / B_subs, A_subs / C_subs

    def predict_test_batch(part):
        weight_file = "models/ensemble_model{}.weights".format(part)
        train_model.load_weights(weight_file)
        batch_size = 1000
        test_data_gen = test_data_generator(test_data, batch_size)
        total_r = {}
        for batch_id, batch_data in tqdm(enumerate(test_data_gen)):
            if batch_id > test_data_gen.steps:
                break
            batch_start_idx = batch_id * batch_size
            R, R_cur_subs = extract_items_batch2(batch_data, batch_start_idx, total_r)

        with open("outputs/test_2_{}.json".format(part), "w", encoding="utf8") as f:
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

    def scheduler(epoch):
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

    for i in range(ensemble_num):
        part = i+last_ensemble_num
        reduce_lr = LearningRateScheduler(scheduler, verbose=1)
        train_model, subject_model, object_model = build_model_from_config(config_path, checkpoint_path, seq_len=180)
        train_D = data_generator(train_data, 32)
        evaluator = Evaluate(part)
        train_model.fit_generator(train_D.__iter__(),
                                 steps_per_epoch=len(train_D),
                                 epochs=7,
                                 callbacks=[evaluator,reduce_lr]
                                 )
        predict_test_batch(part)
        K.clear_session()