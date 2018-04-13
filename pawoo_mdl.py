# coding: utf-8
'''
#PawooのフォローのSensitiveな画像を一括で落とすスクリプト

##挙動
- 初回起動時にアプリ認証を行います
- フョローしているアカウントのメディア欄（最新20件)を調べます
- 画像、動画があればDLします
- [オプションでオフ] Sensitiveな画像・動画のみDLします
- [オプションでオフ] DL完了したらfavotiteします（＝相手にふぁぼ爆が飛ぶ）
- すでにfavorite済のTOOTの画像はDLしません
- ファイル名は「アカウント名_メディアID.jpg/png等」
- ローカルに同名のファイルがあるとスキップします
- 実行するごとに最新の画像IDを記録し、次回実行時は続き（更新差分）からDLします

##仕様
- pawoo以外は非対応
- 設定ファイルは、スクリプトを置いたディレクトリの" mstdn_conf.xml "
- 保存先は、スクリプトを置いたディレクトリの"output"（変更可能）
- 保存先を変えたい場合は設定ファイルを書き換えてください
- TODO:新しくフォローしたアカウントは一括DLしたい
- TODO:クライアントコード生書きは良くないかしら

##注意
- フォロー数が多いと時間がかかります
- API制限(5分で300回）のため、途中でフリーズしたかのように
  止まるタイミングがありますが、待っていればそのうち再開します
- 非常にサーバー負荷の高いスクリプトのため、怒られたりブロックされる可能性があります
- TODO:1DLに3秒待つとかにしようか？

'''

import sys
import colorama
from colorama import Fore
import mastodon
from mastodon.Mastodon import MastodonError
import urllib.error
import urllib.request
import os
from xml.etree import ElementTree
import webbrowser

# オプション--------------------------------------
# DL済のTOOTをふぁぼるか(True/False)
FAVORITE_TOOT = True

# SensitiveのみDLするか(Falseで全画像対象)
SENSITIVE_ONLY = True

# ------------------------------------------------

# UserAgentの偽装
HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0"
}


def load_from_xml(xml_path, section_name):
    """
    XML input
    """
    value = None
    if os.path.exists(xml_path):
        try:
            # xmlファイルを開く。xmlじゃなければここでエラー
            tree = ElementTree.parse(xml_path)
            idtxt = tree.findtext(section_name)
            # 要素が見つからなければNoneが帰る
            if idtxt:
                value = idtxt.strip()
            else:
                print("XML Parse Error : {0} => None".format(section_name))
        except ElementTree.ParseError:
            print("XML Parse Error : {0} => None".format(section_name))

    return value


def save_to_xml(xml_path, section_name, value):
    """
    XML output
    """
    success = False
    if os.path.exists(xml_path):
        # 存在すれば上書き
        try:
            # xmlファイルを開く。xmlじゃなければここでエラー
            tree = ElementTree.parse(xml_path)
            node_root = tree.getroot()  # 保存用
            node_section = tree.find(section_name)

            # 見つからなければ追加
            if node_section is None:
                node_section = ElementTree.Element(section_name)
                node_root.append(node_section)

            # 値セット
            node_section.text = str(value)
            success = True
        except ElementTree.ParseError:
            print("XML Parse Error: create new")

    # 存在しない、あるいはパーサーエラーの時
    if not success:
        # xml生成
        node_root = ElementTree.Element('Config')
        node_section = ElementTree.SubElement(node_root, section_name)
        node_section.text = str(value)

    # 保存
    tree = ElementTree.ElementTree(element=node_root)
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)

    return True


def download(url, save_file_path):
    """
    ダウンロード
    :param url:ダウンロード対象URL
    :param save_file_path:保存先ファイルパス
    """

    print(Fore.YELLOW + "SAVING: {0}".format(save_file_path))
    try:
        request = urllib.request.Request(url=url, headers=HEADERS)
        dlfile = urllib.request.urlopen(request).read()
        with open(save_file_path, mode="wb") as file:
            file.write(dlfile)
    except urllib.error.HTTPError as err:
        print(
            Fore.RED + "Download error:{0} -> {1} {2}".format(url, err.code, err.reason))
        sys.exit(1)


def login(access_token):
    client_id = "975d3aa0fb81e731d008542ba73fa754cc59f27fd204b16a4c7a154bec43efac"
    client_secret = "3cd0619b915589ee3fdd56e608e4d2934fb781c96b6c77e4dbaf442933111eba"

    objMstdn = None
    retry = True

    while retry:
        # オブジェクト作成
        objMstdn = mastodon.Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            api_base_url="https://pawoo.net"
        )
        # ログインできてるかテスト
        try:
            objMstdn.account_verify_credentials()
            retry = False
        except MastodonError:
            # Oauth認証
            authurl = objMstdn.auth_request_url(scopes=['read', 'write'])
            webbrowser.open_new(authurl)
            auth_code = input("Input Authorization Code >>")
            access_token = objMstdn.log_in(
                code=auth_code, scopes=['read', 'write'])

        # loop

    return objMstdn


def get_media_list(objMstdn, user_id, user_name, limit_media_id, save_path):
    """
    ユーザーIDを元にメディア一覧を取得し、ダウンロードする

    objMstdn -- マストドンオブジェクト
    user_id  -- 取得対象のユーザーID
    user_name  -- 取得対象のユーザーアカウント名
    limit_media_id -- このmedia ID以下はダウンロードしない
    save_path -- 保存先ディレクトリ(バックスラッシュ終わり)
    favorite_toot -- ダウンロードしたTOOTをふぁぼるか否か

    return -- ダウンロード完了のうち最大のmedia id
    """

    last_media_id = limit_media_id

    # TOOTのリスト
    toots = objMstdn.account_statuses(user_id, only_media=True)
    for tootinfo in toots:
        # TOOT ID 取得
        toot_id = tootinfo["id"]

        # Sensitiveのみ取得
        if SENSITIVE_ONLY and (not tootinfo["sensitive"]):
            print(Fore.BLUE +
                  "TOOT ID ={0} - not Sensitive. skip".format(toot_id))
            continue

        # ふぁぼ済のTOOTはDLしない
        if tootinfo["favourited"]:
            print(Fore.BLUE +
                  "TOOT ID ={0} - already favorited. skip".format(toot_id))
            continue

        # ふぁぼるかフラグ
        favtoot = False

        # 添付メディアのリスト
        medialist = tootinfo["media_attachments"]
        for media in medialist:
            # メディアURLとID
            media_url = media["url"]
            media_id = media["id"]

            # IDチェック（比較対象はlast_media_idではない）
            if media_id < limit_media_id:
                print(Fore.BLUE +
                      "MEDIA ID={0} - old media. skip".format(media_id))
                continue

            # ファイルパス生成
            filename = media_url.rsplit('/', 1)[1].split('?')[0]
            fbody, fext = os.path.splitext(filename)
            filePath = save_path + user_name + "_" + str(media_id) + fext

            # ダウンロード済チェック
            if os.path.exists(filePath):
                print(Fore.BLUE +
                      "FILE {0} - already exists. skip".format(filePath))
                continue

            # ダウンロード
            download(media_url, filePath)

            # ダウンロード済のIDを記録
            last_media_id = media_id

            favtoot = True

        # （ひとつでも）ダウンロード完了したTooTはふぁぼる
        if FAVORITE_TOOT and favtoot:
            print(Fore.YELLOW +
                  "TOOT ID ={0} - favorited.".format(toot_id))
            objMstdn.status_favourite(toot_id)

    return last_media_id


def main():
    # メッセージに色付
    colorama.init(autoreset=True)

    # config保存場所(実行スクリプトのディレクトリ)
    run_dir = os.path.dirname(os.path.abspath(__file__)) + "\\"
    config_path = run_dir + "mstdn_conf.xml"

    # configからlimit IDの取得
    limit_media_id = int(load_from_xml(config_path, "limit_media_id"))
    if limit_media_id is None:
        limit_media_id = 0
    print("Limit Media ID = {}".format(limit_media_id))
    last_media_id = limit_media_id

    # configからsave pathの取得
    save_path = load_from_xml(config_path, "save_path")
    # 一応パスが存在するか調べます
    if not save_path or (not os.path.exists(save_path)):
        # なかったら作ります
        print(Fore.RED + "save_path not exists :{0}".format(save_path))
        save_path = run_dir + "output\\"
        os.makedirs(save_path)
    print("save_path = {}".format(save_path))

    # configからaccess_tokenの取得
    access_token = load_from_xml(config_path, "access_token")

    # ログイン
    objMstdn = login(access_token)

    # 自分自身のアカウント情報を取得
    my_user_info = objMstdn.account_verify_credentials()
    my_user_id = my_user_info["id"]
    my_username = my_user_info["username"]
    my_display_name = my_user_info["display_name"]
    print(Fore.YELLOW + "Now Logged in as [{0}] - {1} @{2}".format(
        my_user_id, my_display_name, my_username))

    # フォローリスト取得(最初の1回)
    followlist = objMstdn.account_following(my_user_id)

    # ループ継続条件
    # ・listに１個以上アイテムがある (followlist != False)
    # ・ページネーションで次がある (max_id != False)
    # max_id はループ内で上書きされます

    max_id = 1  # False判定されなければなんでも
    page = 1
    while (followlist and max_id):
        max_id = None  # 安全装置

        for userinfo in followlist:
            # ユーザー情報の取得
            user_id = userinfo["id"]
            username = userinfo["username"]
            display_name = userinfo["display_name"]
            print("[{0}] - {1} @{2}".format(user_id, display_name, username))

            # メディアの一覧を取得してダウンロード
            mid = get_media_list(
                objMstdn, user_id, username, limit_media_id, save_path)
            # mid = 0

            # 最大IDを更新
            if mid > last_media_id:
                last_media_id = mid

            # ページ送り用情報（最後のアイテムに含まれる）
            if "_pagination_next" in userinfo:
                pagination_prev = userinfo["_pagination_next"]
                max_id = pagination_prev["max_id"]
                # print("pagination found:{0}".format(max_id))

        # ページ送り
        if max_id:
            followlist = objMstdn.account_following(my_user_id, max_id=max_id)
            page = page + 1
        else:
            break

    # 新しいlimit ID/savepathの保存
    save_to_xml(config_path, "limit_media_id", last_media_id)
    save_to_xml(config_path, "save_path", save_path)
    save_to_xml(config_path, "access_token", access_token)

    # 終了メッセージ
    print("Download Finished.")
    print("last_media_id:{0}".format(last_media_id))


if __name__ == '__main__':
    main()
