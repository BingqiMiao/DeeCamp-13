"""
对SequenceToSequence模型进行基本的参数组合测试
"""

import random
import itertools
from collections import OrderedDict

import pandas as pd
import numpy as np
import tensorflow as tf
from tqdm import tqdm

from sequence_to_sequence import SequenceToSequence
from data_utils import batch_flow
from fake_data import generate


def test(bidirectional, cell_type, depth,
         attention_type, use_residual, use_dropout, time_major):
    """测试不同参数在生成的假数据上的运行结果"""

    # 获取一些假数据
    x_data, y_data, ws_input, ws_target = generate(size=1000)

    # 训练部分

    split = int(len(x_data) * 0.8)
    x_train, x_test, y_train, y_test = (
        x_data[:split], x_data[split:], y_data[:split], y_data[split:])
    n_epoch = 1
    batch_size = 8
    steps = int(len(x_train) / batch_size) + 1

    config = tf.ConfigProto(
        device_count={'CPU': 1, 'GPU': 0},
        allow_soft_placement=True,
        log_device_placement=False
    )

    save_path = '/tmp/s2ss.ckpt'

    tf.reset_default_graph()
    with tf.Graph().as_default():
        random.seed(0)
        np.random.seed(0)
        tf.set_random_seed(0)

        with tf.Session(config=config) as sess:

            model = SequenceToSequence(
                input_vocab_size=len(ws_input),
                target_vocab_size=len(ws_target),
                batch_size=batch_size,
                learning_rate=0.001,
                bidirectional=bidirectional,
                cell_type=cell_type,
                depth=depth,
                attention_type=attention_type,
                use_residual=use_residual,
                use_dropout=use_dropout,
                time_major=time_major,
                hidden_units=64,
                embedding_size=64,
                parallel_iterations=1 # for test
            )
            init = tf.global_variables_initializer()
            sess.run(init)

            # print(sess.run(model.input_layer.kernel))
            # exit(1)

            for epoch in range(1, n_epoch + 1):
                costs = []
                flow = batch_flow(
                    [x_train, y_train], [ws_input, ws_target], batch_size
                )
                bar = tqdm(range(steps),
                           desc='epoch {}, loss=0.000000'.format(epoch))
                for _ in bar:
                    x, xl, y, yl = next(flow)
                    cost = model.train(sess, x, xl, y, yl)
                    costs.append(cost)
                    bar.set_description('epoch {} loss={:.6f}'.format(
                        epoch,
                        np.mean(costs)
                    ))

            model.save(sess, save_path)

    # 测试部分
    tf.reset_default_graph()
    model_pred = SequenceToSequence(
        input_vocab_size=len(ws_input),
        target_vocab_size=len(ws_target),
        batch_size=1,
        mode='decode',
        beam_width=5,
        bidirectional=bidirectional,
        cell_type=cell_type,
        depth=depth,
        attention_type=attention_type,
        use_residual=use_residual,
        use_dropout=use_dropout,
        time_major=time_major,
        hidden_units=64,
        embedding_size=64,
        parallel_iterations=1 # for test
    )
    init = tf.global_variables_initializer()

    with tf.Session(config=config) as sess:
        sess.run(init)
        model_pred.load(sess, save_path)

        bar = batch_flow([x_test, y_test], [ws_input, ws_target], 1)
        t = 0
        for x, xl, y, yl in bar:
            pred = model_pred.predict(
                sess,
                np.array(x),
                np.array(xl)
            )
            print(ws_input.inverse_transform(x[0]))
            print(ws_target.inverse_transform(y[0]))
            print(ws_target.inverse_transform(pred[0]))
            t += 1
            if t >= 3:
                break

    tf.reset_default_graph()
    model_pred = SequenceToSequence(
        input_vocab_size=len(ws_input),
        target_vocab_size=len(ws_target),
        batch_size=1,
        mode='decode',
        beam_width=0,
        bidirectional=bidirectional,
        cell_type=cell_type,
        depth=depth,
        attention_type=attention_type,
        use_residual=use_residual,
        use_dropout=use_dropout,
        time_major=time_major,
        hidden_units=64,
        embedding_size=64,
        parallel_iterations=1 # for test
    )
    init = tf.global_variables_initializer()

    with tf.Session(config=config) as sess:
        sess.run(init)
        model_pred.load(sess, save_path)

        bar = batch_flow([x_test, y_test], [ws_input, ws_target], 1)
        t = 0
        for x, xl, y, yl in bar:
            pred = model_pred.predict(
                sess,
                np.array(x),
                np.array(xl)
            )
            print(ws_input.inverse_transform(x[0]))
            print(ws_target.inverse_transform(y[0]))
            print(ws_target.inverse_transform(pred[0]))
            t += 1
            if t >= 3:
                break

    # return last train loss
    return np.mean(costs)


def main():
    """入口程序，开始测试不同参数组合"""
    random.seed(0)
    np.random.seed(0)
    tf.set_random_seed(0)

    params = OrderedDict((
        ('cell_type', ('gru', 'lstm')),
        ('attention_type', ('Luong', 'Bahdanau')),
        ('use_dropout', (True, False)),
        ('time_major', (True, False)),
        ('depth', (1, 2, 3)),
        ('bidirectional', (True, False)),
        ('use_residual', (True, False)),
    ))

    loop = itertools.product(*params.values())

    rows = []
    for param_value in loop:
        param = OrderedDict(zip(params.keys(), param_value))
        print('=' * 30)
        row = []
        for key, value in param.items():
            print(key, ':', value)
            row.append(value)
        print('-' * 30)
        cost = test(**param)
        row += [cost]
        rows.append(row)

    columns = list(params.keys()) + ['loss']
    dframe = pd.DataFrame(rows, columns=columns)
    dframe.to_excel('/tmp/s2ss_test.xlsx')


if __name__ == '__main__':
    main()
