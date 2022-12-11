import gensim
from pprint import pprint
import collections

model_path = "data/cc.ja.300.vec.gz"
wv = gensim.models.KeyedVectors.load_word2vec_format(model_path, binary=False)


def get_similar_words(word: str) -> list[str, float]:
    """類似した単語を返す"""
    words = []
    # それぞれの単語の取得数
    _topn = 10
    for m in wv.most_similar(word, topn=_topn):
        word, vec = m
        words.append(m)
        for n in wv.most_similar(word, topn=_topn):
            word, vec = n
            words.append(n)

    return words


pprint(get_similar_words("こんにちは"))
