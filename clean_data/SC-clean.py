# encoding: UTF-8
import re
import jieba
from tqdm import tqdm
from html.parser import HTMLParser
en_punctuation_set = [',', '.', '?', '!', '\"', '\"']
import sys
print('目前系统的编码为：',sys.getdefaultencoding())
stop_word_list = []
def load_stop_word(stop_word_path = 'stopword.txt'):
    """加载停用词表,停用词可以用df统计出来"""
    global stop_word_list
    with open(stop_word_path, 'r',encoding='utf-8') as f:
        lines = f.readlines()
        lines = [line for line in lines]
        for line in lines:
            line = line.strip()
            stop_word_list.append(line)
        stop_word_list = list(set(stop_word_list))
        print(stop_word_list)

synonym_dict = {}
def load_self_dict(self_define_dict_path = 'dictionary.txt'):
    """加载自定义词典,自定义词表用于jieba分词"""
    jieba.load_userdict(self_define_dict_path)

def semi_angle_to_sbc(uchar):
    """半角转全角"""
    inside_code = ord(uchar)
    if inside_code < 0x0020 or inside_code > 0x7e:
        return uchar
    if inside_code == 0x0020:
        inside_code = 0x3000
    else:
        inside_code += 0xfee0
    return chr(inside_code)


def sbc_to_semi_angle(uchar):
    """全角转半角"""
    inside_code = ord(uchar)
    if inside_code == 0x3000:
        inside_code = 0x0020
    else:
        inside_code -= 0xfee0
    if inside_code < 0x0020 or inside_code > 0x7e:
        return uchar
    return chr(inside_code)

def is_chinese(uchar):
    """is chinese"""
    if u'\u4e00' <= uchar <= u'\u9fa5':
        return True
    else:
        return False


def is_number(uchar):
    """is number"""
    if u'\u0030' <= uchar <= u'\u0039':
        return True
    else:
        return False

def is_alphabet(uchar):
    """is alphabet"""
    if (u'\u0041' <= uchar <= u'\u005a') or (u'\u0061' <= uchar <= u'\u007a'):
        return True
    else:
        return False

def clean_str(string):
    # 去除html标签
    dr = re.compile(r'<[^>]+>', re.S)
    string = dr.sub('', string)
    # 统一全角标点
    for c in en_punctuation_set:
        if c in string:
            string = string.replace(c,semi_angle_to_sbc(c))
    # 去除html中的特殊字符
    string = HTMLParser().unescape(string)
    # 将字母统一转成小写
    string = string.lower()
    string=string.replace(' ','')
    return string.strip()

def seperate_line(line):
    """分词的同时去除停用词"""
    words = jieba.cut(line)
    dealed_words = []
    for word in words:
        if word not in stop_word_list:
            dealed_words.append(word)
    line = " ".join(dealed_words)
    return line

def is_validate(sentence):
    """去除太长或太短的句子"""
    if len(sentence)<4 or len(sentence)>20:
        return False
    """去除含有数字的句子 去除@的句子"""
    for c in sentence:
        if c.isdigit() or c is '@':
            return False
    """去除标点或英语太多的句子"""
    cn_sentence = []
    for c in sentence:
        if is_chinese(c):
            cn_sentence.append(c)
    if len(cn_sentence)/float(len(sentence)) < 0.4:
        return False
    """检查是否含有URL"""
    pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')  # 匹配模式
    url = re.findall(pattern, sentence)
    if len(url)>0:
        return False
    """根据关键词筛选"""
    return True

# 按行读取，可以处理大文件
def clear_data(input_path='zhihu_reply.csv', output_cleaned_file='zhihu.csv'):
    with open(input_path, 'r',encoding='utf-8') as in_file:
        with open(output_cleaned_file, 'w',encoding='utf-8') as out_file:
            for line in tqdm(in_file):
                QA = line.split('\t')
                if len(QA) == 2:
                    Q = QA[0]
                    A = QA[1]
                    if is_validate(Q) and is_validate(A):
                        Q = seperate_line(clean_str(Q))
                        A = seperate_line(clean_str(A))
                        QA = Q + ',' + A+'\n'
                        out_file.write(QA)

if __name__ == '__main__':
    load_self_dict()
    #load_stop_word()
    clear_data()