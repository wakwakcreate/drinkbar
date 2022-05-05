# 騙し合いはドリンクバーで

https://github.com/line/line-bot-sdk-python を使用して開発。

## 隠しコマンド

グループ内で以下の文字列を書き込むと、説明の通りの動作をした後にゲームがリセットされます。

* `d`: 1人でゲーム進行可（2人ダミーを追加）
* `i`: ゲームを初期化
* `スタート`: ゲームを初期化

## ローカルでの開発方法

### Python 環境構築

python3 をインストールし、`requirements.txt` を使って必要なライブラリを pip でインストール。

例

```sh
$ pip install -r `requirements.txt`
```

### 起動例

TOKEN や SECRET は LINE Developers にログインして確認。

```sh
#!/bin/bash

export YOUR_CHANNEL_ACCESS_TOKEN="****************************************************************************************************************************************************************************"
export YOUR_CHANNEL_SECRET="********************************"
export FLASK_APP="./main.py"
flask run --debugger --reload
```

### テスト

```sh
$ pytest test
```

### webhook として使えるようにする方法

yusha_no_koushin をグローバルへ出すには [ngrok](https://ngrok.com/) を使うと楽。
上記 flask run が 5000 番ポートを開けた場合の例。

```sh
$ ./ngrok http 5000
```

上記を実行すると webhook に指定するべき URL が表示される。
その URL を [LINE Developers Console](https://developers.line.biz/console/channel/1656404948/messaging-api) で、チャンネルの Webhook URL に設定すれば OK。
`/callback` を URL の最後に追記することを忘れずに。

<!-- ## Heroku への移動

ローカルでの開発が済んだら Heroku に push する。これにより、アプリが24時間動くようになる（要確認）。

TBD

現時点での webhook URL は https://yuusha-no-koushin.herokuapp.com/callback になる。 -->