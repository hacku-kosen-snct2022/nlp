import os
import gensim
from pprint import pprint
import collections
import requests
from tqdm import tqdm

model_path = "data/cc.ja.300.vec.gz"


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


if not os.path.isfile(model_path):
    download_model(model_path)

wv = gensim.models.KeyedVectors.load_word2vec_format(model_path, binary=False)

pprint(get_similar_words("こんにちは"))
