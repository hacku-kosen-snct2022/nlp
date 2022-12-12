import fasttext as ft
import os
from pprint import pprint
import gensim
import wakati as wakati

# モデルのダウンロード先
_model_gz_path = "data/cc.ja.300.vec.gz"
# モデルの保存先
_model_path = "data/model.bin"
# 取り出す品詞リスト
_select_conditions = ["動詞", "名詞"]

# モデルのDL
if not os.path.isfile(_model_gz_path):
    ft.download_model(_model_gz_path)

# モデルの解凍
if not os.path.isfile(_model_path):
    ft.save_model_from_gz(_model_path, _model_gz_path)

# モデルの読み込み
wv = gensim.models.KeyedVectors.load(_model_path)

_select_conditions = ["動詞", "名詞"]


def text_to_vectors(text: str) -> dict[str, list[str, float]]:
    """文章から特定の品詞を取り出し、それの類似単語をベクトルで返す"""
    # 単語の分解
    words = list(set(wakati.text_to_word_by_conditions(text, _select_conditions)))
    ret: dict[str, list[str, float]] = {}
    for word in words:
        # 類似した単語の取得
        try:
            ret[word] = ft.get_vector_from_words(ft.get_similar_words(wv, word))
        except:
            print(f"{word} はfasttextにありません")
    return ret
