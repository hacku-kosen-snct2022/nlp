import types
import typing


def get_post_memo(db: typing.Any, uid: str) -> list[str]:
    """ユーザーの投稿の最新3件を取得する"""
    # 投稿取得件数
    _get_post_num = 3
    topics = db.collection(uid).document("topics").collections()
    for topic in topics:
        posts = topic.document("timeLine").collections()
        ret = []
        # postはcollectionReference
        for post in list(posts)[-_get_post_num:]:
            # docsはdocumentReference
            ret.append(list(post.stream())[-1].to_dict()["memo"])

        return ret
    return []
