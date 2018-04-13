# Pawoo のフォローの Sensitive な画像を一括で落とすスクリプト

# 動作確認環境

Python 3.6.3
Windows10 64bit


# 動かすには

* Python3用のスクリプトなので、無いならインストールする必要があります。

> Download Python | Python.org  
> https://www.python.org/downloads/

* 外部サードパーティモジュール(Mastodon.py / colorama)を使っています。まとめてpipしておきます。

> pip install -r requirements.txt


* 次に、以下のページにアクセスして client_id/client_secret を取得する必要があります(ソースに書けないですし）

> Access Token Generator for Mastodon API  
> https://takahashim.github.io/mastodon-access-token/

* Mastodon URL -> https://pawoo.net
* Client Name -> 適当(例: pawoo_mdl )
* Web site -> 適当(例: http://chomstudio.sblo.jp/ )
* Scopes -> read write
* client_id と client_secret を SHOW を押して表示させたらスクリプトの「必須項目」に貼り付けます
* access_token は必要に応じて認証しますがあらかじめ入れておくと楽

# 挙動

* 初回起動時にアプリ認証を行います
* フョローしているアカウントのメディア欄（最新 20 件)を調べます
* 画像、動画があれば DL します
* [オプションでオフ] Sensitive な画像・動画のみ DL します
* [オプションでオフ] DL 完了したら favotite します（＝相手にふぁぼ爆が飛ぶ）
* すでに favorite 済の TOOT の画像は DL しません
* ファイル名は「アカウント名\_メディア ID.jpg/png 等」
* ローカルに同名のファイルがあるとスキップします
* 実行するごとに最新の画像 ID を記録し、次回実行時は続き（更新差分）から DL します

# 仕様

* pawoo 以外は非対応
* 設定ファイルは、スクリプトを置いたディレクトリの" pmdl_conf.xml "
* 保存先は、スクリプトを置いたディレクトリの"output"（変更可能）
* 保存先を変えたい場合は設定ファイルを書き換えてください
* TODO:新しくフォローしたアカウントは一括 DL したい

# 注意

* 負荷軽減のため１アカウントにつき３秒(デフォルト)待つようにしています
* フォロー数が多いと時間がかかります
* API 制限(5 分で 300 回）のため、途中でフリーズしたかのように止まるタイミングがありますが、待っていればそのうち再開します
* 将来的に怒られたりブロックされる可能性も否定できない

2018 Chom P.  
https://twitter.com/chom  
http://chomstudio.com  
http://chomstudio.sblo.jp/
