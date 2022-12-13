import gensim
import requests
from tqdm import tqdm
from typing import Any


def download_model(model_path: str):
    """指定したパスにfasttextのモデルをダウンロードする"""
    print("Download model")
    # fasttextのurl
    _download_file_url = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ja.300.vec.gz"

    file_size = int(requests.head(_download_file_url).headers["content-length"])
    pbar = tqdm(total=file_size, unit="B", unit_scale=True)

    data = requests.get(_download_file_url, stream=True)
    with open(model_path, mode="wb") as fs:  # wb でバイト型を書き込める
        for chunk in data.iter_content(chunk_size=1024):
            fs.write(chunk)
            pbar.update(len(chunk))
        pbar.close()


def save_model_from_gz(model_path: str, model_gz_path: str):
    """指定したパスに圧縮されたモデルを解凍して保存する"""
    print("Save model")
    model = gensim.models.KeyedVectors.load_word2vec_format(model_gz_path, binary=False)
    print("load")
    model.save(model_path)


def get_similar_words(wv: Any, word: str) -> list[tuple[str, float]]:
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


def get_vector_from_words(words: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """単語のリストをベクトルに加工して返す"""
    # 被った際の重み定数
    _word_weight = 0.1

    ret: dict[str, float] = {}
    counters: dict[str, int] = {}
    for ww in words:
        word, vec = ww
        if word not in counters.keys():
            counters[word] = 1
        else:
            counters[word] += 1
        if word not in ret.keys():
            ret[word] = vec
        else:
            ret[word] += vec
    for word in counters.keys():
        num = counters[word]
        ret[word] = ret[word] / num * (1 + _word_weight * num)

    return list(ret.items())
