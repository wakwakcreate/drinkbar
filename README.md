# 騙し合いはドリンクバーで

## 隠しコマンド

グループ内で以下の文字列を書き込むと、説明の通りの動作をした後にゲームがリセットされます。

* `debug one`: 1人でゲーム進行可（2人ダミーを追加）
* `debug two`: 2人でゲーム進行可（1人ダミーを追加）
* `debug three`: 2人でゲーム進行可（1人ダミーを追加）
* `debug reload`: セリフやお題を https://github.com/wakwakcreate/drink_scripts から再読込する

## ローカルでの開発方法

### Python 環境構築

python3 をインストールし、`requirements.txt` を使って必要なライブラリを pip でインストール。

例

```sh
$ pip install -r `requirements.txt`
```

### yusha_no_koushin 起動例

TOKEN や SECRET は LINE Developers 

```sh
#!/bin/bash

export YOUR_CHANNEL_ACCESS_TOKEN="****************************************************************************************************************************************************************************"
export YOUR_CHANNEL_SECRET="********************************"
export FLASK_APP="./main.py"
flask run --debugger --reload
```

### webhook として使えるようにする方法

yusha_no_koushin をグローバルへ出すには [ngrok](https://ngrok.com/) を使うと楽。
上記 flask run が 5000 番ポートを開けた場合の例。

```sh
$ ./ngrok http 5000
```

上記を実行すると webhook に指定するべき URL が表示される。
その URL を LINE Developers Console で、チャンネルの Webhook URL に設定すれば OK。
`/callback` を URL の最後に追記することを忘れずに。

## Heroku への移動

ローカルでの開発が済んだら Heroku に push する。これにより、アプリが24時間動くようになる（要確認）。

TBD

現時点での webhook URL は https://yuusha-no-koushin.herokuapp.com/callback になる。