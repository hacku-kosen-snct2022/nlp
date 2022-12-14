import fasttext as ft
import os
from pprint import pprint
import gensim
import wakati as wakati
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

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

# firebase周り
cred = credentials.Certificate("data/hackukosen-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

_select_conditions = ["動詞", "名詞"]


def text_to_vectors(text: str) -> dict[str, list[tuple[str, float]]]:
    """文章から特定の品詞を取り出し、それの類似単語をベクトルで返す"""
    # 単語の分解
    words = list(set(wakati.text_to_word_by_conditions(text, _select_conditions)))
    ret: dict[str, list[tuple[str, float]]] = {}
    for word in words:
        # 類似した単語の取得
        try:
            ret[word] = ft.get_vector_from_words(ft.get_similar_words(wv, word))
        except:
            print(f"{word} はfasttextにありません")
    return ret


def save_vector():
    # ベクトル表示件数
    _vector_num = 5

    # 投稿取得件数
    _get_post_num = 3
    for uid in db.collections():
        topics = uid.document("topics").collections()
        for topic in topics:
            words_vectors = {}
            posts = topic.document("timeLine").collections()
            # postはcollectionReference
            for post in list(posts)[-_get_post_num:]:
                text = list(post.stream())[-1].to_dict()["memo"]
                for words in text_to_vectors(text).items():
                    words_vectors[words[0]] = sorted(words[1], key=lambda x: x[1], reverse=True)[-_vector_num:]
            analytics = topic.document("analytics")
            ids = []
            for words in words_vectors.items():
                ids.append(words[0])
                for word in words[1]:
                    analytics.collection(words[0]).document(word[0]).set({"vector": word[1]})
            analytics.set({"id": ids})


# save_vector()
text_to_vectors("こんにちは！たくさんのalphabetや123を含みます。また😀も含みますよ！https://github.com/hacku-kosen-snct2022/nlp/issues/16")
