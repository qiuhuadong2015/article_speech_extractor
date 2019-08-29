# 根据下载模型存放位置修改
LTP_DATA_PATH = '/Users/qiuhuadong/ltp_data_v3.4.0'

def read_list(file_name):
    with open(file_name) as f:
        words = f.read().split()
        return words

def split_by_sentence_end(article: str) -> list:
    '''
    基于pyltp的SentenceSplitter。根据句号、问号、感叹号等句子结束标点判断
    '''
    from pyltp import SentenceSplitter
    sentences = SentenceSplitter.split(article) # 分句 得到可迭代对象
    sentences = [s for s in sentences if len(s) != 0] # 剔除分句结果列表中的空句子
    return sentences

def segmentor(line: str, segmentor_model=None) -> list:
    '''
    line：确保先经过清洗
    segmentor_model: 重复调用函数时，需外部传入模型以减少开销，并在外部释放
    '''
    inner_release = False
    if segmentor_model == None:
        from pyltp import Segmentor
        segmentor_model = Segmentor()
        segmentor_model.load(f'{LTP_DATA_PATH}/cws.model')
        inner_release = True
    
    tokens = segmentor_model.segment(line) # 分词 得到可迭代对象
    tokens = list(tokens)
    
    if inner_release:
        segmentor_model.release() # 释放模型
    return tokens

def postagger(tokens, postagger_model=None):
    '''
    postagger_model: 重复调用函数时，需外部传入模型以减少开销，并在外部释放
    '''
    inner_release = False
    if postagger_model == None:
        from pyltp import Postagger
        postagger_model = Postagger()
        postagger_model.load(f'{LTP_DATA_PATH}/pos.model')
        inner_release = True
        
    postags = postagger_model.postag(tokens)  # 词性标注 获得可迭代对象
    postags = list(postags)
    
    if inner_release:
        postagger_model.release()  # 释放模型
    return postags

def ner(tokens, postags, ner_model=None):
    '''
    ner_model: 重复调用函数时，需外部传入模型以减少开销，并在外部释放
    '''
    inner_release = False
    if ner_model == None:
        from pyltp import NamedEntityRecognizer
        ner_model = NamedEntityRecognizer()
        ner_model.load(f'{LTP_DATA_PATH}/ner.model')
        inner_release = True
        
    netags = ner_model.recognize(tokens, postags)  # 命名实体识别
    netags = list(netags)
    
    if inner_release:
        ner_model.release()  # 释放模型
    return netags

def parse(tokens, postags, parser_model=None, get_origin=False):
    '''
    paser_model: 重复调用函数时，需外部传入模型以减少开销，并在外部释放
    '''
    inner_release = False
    if parser_model == None:
        from pyltp import Parser
        parser_model = Parser()
        parser_model.load(f'{LTP_DATA_PATH}/parser.model') 
        inner_release = True
    
    arcs_origin = parser_model.parse(tokens, postags)  # 句法分析
    arcs=[[arc.head,arc.relation] for arc in arcs_origin]
    
    if inner_release:
        parser_model.release()  # 释放模型
    
    if get_origin:
        return arcs_origin
    else:
        return arcs

def load_LTP_models():
    models = {}
    from pyltp import Segmentor
    segmentor_model = Segmentor()
    segmentor_model.load(f'{LTP_DATA_PATH}/cws.model')
    from pyltp import Postagger
    postagger_model = Postagger()
    postagger_model.load(f'{LTP_DATA_PATH}/pos.model')
    from pyltp import NamedEntityRecognizer
    ner_model = NamedEntityRecognizer()
    ner_model.load(f'{LTP_DATA_PATH}/ner.model')
    from pyltp import Parser
    parser_model = Parser()
    parser_model.load(f'{LTP_DATA_PATH}/parser.model')

    models['seg'] = segmentor_model
    models['pos'] = postagger_model
    models['ner'] = ner_model
    models['parser'] = parser_model

    return models

def release_LTP_models(models: dict):
    models['seg'].release()
    models['pos'].release()
    models['ner'].release()
    models['parser'].release()

def extract_SBV_of_say_in_lines(article_lines, say_words):

    # 一次加载模型，避免重复开销导致运行慢
    models = load_LTP_models()

    s_SBVs_of_say = []
    for article_line in article_lines:
        line_sentences = split_by_sentence_end(article_line)
        for sentence in line_sentences:
            s_tokens = segmentor(sentence, segmentor_model=models['seg'])
            s_postags = postagger(s_tokens, postagger_model=models['pos'])
            s_netags = ner(s_tokens, s_postags, ner_model=models['ner'])
            # 跳过不含实体的行
            if ('S-Ns' not in s_netags) and ('S-Ni' not in s_netags) and ('S-Nh' not in s_netags):
                continue
            s_arcs = parse(s_tokens, s_postags, parser_model=models['parser'])

            # 留下主谓关系，记录主语token idx
            s_SBVs = [(s_token_idx, s_arc) for s_token_idx,
                      s_arc in enumerate(s_arcs) if s_arc[1] == 'SBV']

            for s_SBV in s_SBVs:
                s_V_idx = s_SBV[1][0] - 1  # 取arc.head，也就是主谓关系中谓语Verb的token idx
                s_SB_idx = s_SBV[0]  # 取主谓关系中主语Subject的token idx
                # 留下谓语是说的的主谓关系
                if s_tokens[s_V_idx] not in say_words:
                    continue
                # 符合「该行包含实体、主谓关系、谓语是说」条件的，构造结果
                s_SBVs_of_say.append(
                    (s_tokens[s_SB_idx], s_tokens[s_V_idx], ''.join(s_tokens[s_V_idx+1:])))

    # 释放所有模型
    release_LTP_models(models)

    return s_SBVs_of_say

from flask import Flask,jsonify,Response,request
import simplejson

app = Flask(__name__)
from flask_cors import CORS
CORS(app, supports_credentials=True)

import json
@app.route("/api/get",methods=['POST'])
def get_result():
    data = request.get_json()
    article = data['article']
    article_lines = article.split('\n')
    print(article_lines)
    SBVs_of_say = extract_SBV_of_say_in_lines(article_lines, load_say_words)
    print(SBVs_of_say)
    result = {'result':[
        {'subject':subj,'predicate':pred,'object':obj}
        for subj,pred,obj in SBVs_of_say
    ]}
    return jsonify(result)

@app.route("/api")
def hello():
    return "hello api"

load_say_words = read_list('say_words.txt')

if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False#避免中文乱码
    app.run(port=5000)
    #app.run(debug=True)# 免重新运行，代码的修改会自动更新到运行环境


