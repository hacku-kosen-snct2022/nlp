import MeCab


tagger = MeCab.Tagger()
# node.surface が取得できない時があるので、対策のおまじない
tagger.parseToNode("")


def text_to_word_by_conditions(text: str, select_conditions: list[str]) -> list[str]:
    """文章から特定の品詞の単語を取り出す"""
    node = tagger.parseToNode(text)
    words = []
    while node:
        # 品詞
        pos = node.feature.split(",")[0]
        # もし品詞が条件と一致してたら
        if pos in select_conditions:
            words.append(node.surface)

        node = node.next
    return words
