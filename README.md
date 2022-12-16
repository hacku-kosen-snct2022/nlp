# nlp
Server-side repository for natural language processing in "Hack U KOSEN 2022".

## 実行方法
1. `./data`ディレクトリを作成
2. [ここから](https://console.firebase.google.com/u/2/project/hackukosen/settings/serviceaccounts/adminsdk?hl=ja)サービスアカウントのjsonを取得し`hackukosen-firebase-adminsdk.json`にリネーム
3. `./data`ディレクトリにDLしたサービスアカウントの`hackukosen-firebase-adminsdk.json`を配置
4. [ここから](https://console.cloud.google.com/iam-admin/iam?authuser=2&project=hackukosen)生成したサービスアカウントに**ストレージ管理者**の権限を付与
5. PCに`MeCab`をインストール
6. `pip install -r requirements.txt`を実行
7. プロジェクトルートで`python3 nlp`を実行
