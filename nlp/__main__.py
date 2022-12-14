import fasttext as ft
import os
from pprint import pprint
import gensim
import wakati as wakati
import firebase_admin
from firebase_admin import credentials, initialize_app, storage
from firebase_admin import firestore
from wordcloud import WordCloud

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

_gcp_json = "data/hackukosen-firebase-adminsdk.json"

# firebase周り
cred = credentials.Certificate(_gcp_json)
firebase_admin.initialize_app(cred, {"storageBucket": "gs://hackukosen.appspot.com"})
db = firestore.client()

bucket = storage.bucket("hackukosen.appspot.com")

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
    _vector_max_num = 70

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
                    words_vectors[words[0]] = sorted(words[1], key=lambda x: x[1], reverse=True)
            analytics = topic.document("analytics")
            for words in words_vectors.items():
                words_vectors[words[0]] = words[1][-int(_vector_max_num / len(words_vectors)) :]
            ids = []
            # 画像生成用
            vecs = {}
            for words in words_vectors.items():
                ids.append(words[0])
                for word in words[1]:
                    vecs[word[0]] = word[1]
                    # analytics.collection(words[0]).document(word[0]).set({"vector": word[1]})

            wc = WordCloud(
                font_path="data/NotoSansJP-Medium.otf",
                width=1920,
                height=1080,
                prefer_horizontal=1,
                background_color="white",
                include_numbers=True,
                colormap="tab20",
            ).generate_from_frequencies(vecs)

            photo_path = f"out_img/{uid.id}.png"
            wc.to_file(photo_path)
            storage_path = f"img/{uid.id}.png"

            blob = bucket.blob(storage_path)
            blob.upload_from_filename(photo_path)

            blob.make_public()

            analytics.set({"id": ids, "wordcloudUrl": blob.public_url})


save_vector()
