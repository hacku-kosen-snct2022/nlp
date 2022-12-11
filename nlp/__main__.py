import fasttext as ft
import os
from pprint import pprint
import gensim

_model_gz_path = "data/cc.ja.300.vec.gz"
_model_path = "data/model.bin"

# モデルのDL
if not os.path.isfile(_model_gz_path):
    ft.download_model(_model_gz_path)

# モデルの解凍
if not os.path.isfile(_model_path):
    ft.save_model_from_gz(_model_path, _model_gz_path)

# モデルの読み込み
wv = gensim.models.KeyedVectors.load(_model_path)

# 類似した単語の取得
pprint(ft.get_vector_from_words(ft.get_similar_words(wv, "おはよう")))
