import threading
import fasttext as ft
import os
from pprint import pprint
import gensim
import wakati as wakati
import firebase_admin
from firebase_admin import credentials, initialize_app, storage, auth
from firebase_admin import firestore
from wordcloud import WordCloud
import schedule
from time import sleep
import secrets
import datetime
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

# モデルのダウンロード先
_model_gz_path = "data/cc.ja.300.vec.gz"
# モデルの保存先
_model_path = "data/model.bin"
# 取り出す品詞リスト
_select_conditions = ["動詞", "名詞"]
# フォント
_font_path = "fonts/NotoSansJP-Medium.otf"
_font_family = "Yu Mincho"

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
callback_done = threading.Event()


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


def make_network_graph(text_vectors: dict[str, list[tuple[str, float]]], path: str):
    G = nx.Graph()

    vec_list: list[tuple[float, str]] = []

    for vecs in text_vectors.items():
        word, vectors = vecs
        for vec in vectors:
            vec_list.append((vec[1], vec[0]))

    # NetworkのRoot数
    _network_root_num = 5
    # Networkの各Node数
    _network_node_num = 5

    vec_list = sorted(vec_list)[-_network_root_num:]
    pprint(vec_list)

    node_size_list: list[float] = []
    edge_wight_list = []

    root_list = []

    for vector in vec_list:
        _, word = vector
        root_list.append(word)
        vectors = sorted(ft.get_vector_from_words(ft.get_similar_words(wv, word)), key=lambda x: x[1])[
            -_network_node_num:
        ]
        if word not in G.nodes:
            G.add_node(word)
            node_size_list.append(4000)

        for vec in vectors:
            w, v = vec
            if w not in G.nodes:
                node_size_list.append(pow(v, 10) * 40000)
                G.add_node(w)
            edge_wight_list.append(pow(v, 5) * 20)
            G.add_edge(word, w)

    plt.figure(figsize=(23, 23))  # 12
    pos = nx.spring_layout(G, k=0.5)

    nx.draw_networkx_nodes(G, pos, alpha=0.2, node_size=node_size_list)
    nx.draw_networkx_labels(G, pos, font_size=44, font_family=_font_family)
    nx.draw_networkx_edges(G, pos, edge_color="c", width=edge_wight_list, alpha=0.5)

    plt.axis("off")
    plt.savefig(path)


# 各uidのトピックのリスト
known_users_topics: dict[str, list[str]] = {}


def on_topic_snapshot(topic_snapshot, changes, read_time):
    """各トピックの更新からベクトルを生成し保存する"""
    for topic_doc in topic_snapshot:
        # ベクトルを取得し、保存する

        print(topic_doc.id)

        # 投稿取得件数
        _get_post_num = 3

        topic = topic_doc.reference.parent

        posts = list(topic.document("timeLine").collections())
        texts = []
        posts = sorted(posts, key=lambda x: int(x.id))

        if posts.__len__() <= 0:
            callback_done.set()
            continue

        for post in posts[-_get_post_num:]:
            post_list = sorted(list(post.stream()), key=lambda x: x.id)
            texts.append(post_list[-1].to_dict()["memo"])

        # ベクトル表示件数
        _vector_max_num = 70
        words_vectors = {}
        analytics = topic.document("analytics")
        for text in texts:
            for words in text_to_vectors(text).items():
                words_vectors[words[0]] = sorted(words[1], key=lambda x: x[1], reverse=True)
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
            font_path=_font_path,
            width=1920,
            height=1080,
            prefer_horizontal=1,
            background_color="white",
            include_numbers=True,
            colormap="tab20",
        ).generate_from_frequencies(vecs)

        token = secrets.token_hex(16)

        photo_path = f"out_img/{token}_wordcloud.png"
        wc.to_file(photo_path)
        storage_path = f"img/{token}_wordcloud.png"

        blob = bucket.blob(storage_path)
        blob.upload_from_filename(photo_path)

        blob.make_public()

        wordcloud_url = blob.public_url

        # ネットワークグラフ生成
        network_graph_path = f"out_img/{token}_network.png"
        network_storage_path = f"img/{token}_network.png"
        make_network_graph(words_vectors, network_graph_path)
        blob = bucket.blob(network_storage_path)
        blob.upload_from_filename(network_graph_path)
        blob.make_public()
        network_url = blob.public_url
        analytics.set({"ids": ids, "wordcloudUrl": wordcloud_url, "networkGraphUrl": network_url})

        print(datetime.datetime.now())
    callback_done.set()


def on_uid_snapshot(uid_snapshot, changes, read_time):
    """uidの更新からtopicにスナップショットを設定する"""
    for topics in uid_snapshot:
        if topics.id == "topics":
            parent_id = topics.reference.parent.id
            for topic in topics.reference.collections():
                if topic.id not in known_users_topics[parent_id]:
                    known_users_topics[parent_id].append(topic.id)
                    topic.document("timeLine").on_snapshot(on_topic_snapshot)
                    on_topic_snapshot([topic.document("timeLine").get()], None, None)

    callback_done.set()


def check_new_users():
    """新しいユーザーを探し、そのユーザーに対してスナップショットを設定する"""
    print("check new users")
    for user in auth.list_users().users:
        if user.uid not in known_users_topics.keys():
            known_users_topics[user.uid] = []
            db.collection(user.uid).on_snapshot(on_uid_snapshot)
            on_uid_snapshot(db.collection(user.uid).stream(), None, None)


# デバッグ用
# known_users_topics["uid"] = []
# db.collection("uid").on_snapshot(on_uid_snapshot)
# on_uid_snapshot(db.collection("uid").stream(), None, None)

# 三分ごとに実行
schedule.every(60 * 3).seconds.do(check_new_users)
check_new_users()

# Keep the app running
while True:
    schedule.run_pending()
    sleep(1)
