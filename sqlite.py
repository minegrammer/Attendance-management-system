# Flaskの操作に必要なモジュールをインポート
from flask import Flask, render_template, request
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

# DBのテーブルの型をインポート
from sqlalchemy import Column, Integer, String

# Flaskの立ち上げ
app = Flask(__name__)
app.config['KEY'] = 'key'

# DBへのパス
app.config['SQLALCHEMY_DATABASE_URI'] = 'your URI' 

# SQLAlchemyでデータベース定義
db = SQLAlchemy(app)

# SQLiteのLOGDBテーブル情報
class LOGDB(db.Model):
    __tablename__ = 'log_table'

    ID = db.Column(Integer, primary_key=True)
    NUMBER = db.Column(Integer)
    MEMBER = db.Column(Integer)
    JOUTAI = db.Column(Integer)
    NOWTIME = db.Column(Integer)

# SQLiteのMEMBERDBテーブル情報
class MEMBERDB(db.Model):
    __tablename__ = 'member_table'

    ID = db.Column(Integer, primary_key=True)
    NUMBER = db.Column(Integer)
    MEMBER = db.Column(Integer)
    JOUTAI = db.Column(Integer)
    INTIME = db.Column(Integer)
    OUTTIME = db.Column(Integer)
    DAYTIME = db.Column(String(32))
    ALLTIME = db.Column(String(32))

# DBの作成
db.create_all()

# 研究室もメンバーをmembersリストで作成
members = ["A", "B", "C", "D", "E"] 
numbers = [1,2,3,4,5]
# 人数を調べる
members_length = len(members)
# 現在の状態を格納するnowリストを人数分作成
now = [0] * members_length
# ３種の状態を保持するsituationsリストの作成
situations = ["帰宅", "一時外出中", "在室"]

# メニューを表示
@app.route("/")
def menu(): 
    #管理者用MEMBERDB作成
    '''
    for i in range(members_length):
        flask = MEMBERDB(NUMBER = numbers[i], MEMBER = i, JOUTAI = now[i])
        db.session.add(flask)
    db.session.commit()
    '''
    
    MEMBERDB_infos = db.session.query(MEMBERDB.MEMBER, MEMBERDB.JOUTAI, MEMBERDB.NUMBER).all()

    return render_template("menu.html",members_length = members_length,  members = members, situations = situations, now = now, MEMBERDB_infos = MEMBERDB_infos)

# 行動を選択
@app.route("/select", methods = ["GET", "POST"])
def sel(): 

    num = request.args.get("num")
    
    return render_template("select_button.html",members_length = members_length, members = members ,situations = situations, num=int(num), now = now)

# 選択済みメニュー
@app.route("/a", methods = ["GET", "POST"])
def menu1():
    num = int(request.form.get("num"))
    joutai = int(request.form.get("joutai"))

    now[num] = joutai

    now_time = datetime.datetime.now()

    # 誰が（num）どうだ（joutai）をログで表示
    flask = LOGDB(NUMBER = numbers[num], MEMBER = num, JOUTAI = joutai, NOWTIME = now_time)
    db.session.add(flask)
    db.session.commit()
    LOGDB_infos = db.session.query(LOGDB.MEMBER, LOGDB.JOUTAI, LOGDB.NOWTIME).all()

    # 最新のデータをLOGDBから取ってくる（ログ内検索）
    logdb = db.session.query(LOGDB).filter(LOGDB.NUMBER == numbers[num]).order_by(desc(LOGDB.NOWTIME)).first()

    # MEMBERDBの行を選択
    memberdb = db.session.query(MEMBERDB).filter(MEMBERDB.NUMBER == numbers[num]).first()
    memberdb.JOUTAI = logdb.JOUTAI 

    # 入室時の時刻をmemberdb.INTIMEに代入し、データ更新
    if joutai == 2:
        memberdb.INTIME = logdb.NOWTIME
    
    # 退室or一時退室の時刻をmemberdb.OUTTIMEに代入し、データ更新
    elif joutai == 0 or joutai == 1:
        memberdb.OUTTIME = logdb.NOWTIME

        #ここから時間の計算
        #logdbから入室した時間を取ってくる
        in_time_row = db.session.query(LOGDB).filter(LOGDB.NUMBER == numbers[num], LOGDB.JOUTAI == 2).order_by(desc(LOGDB.NOWTIME)).first()
        in_time = in_time_row.NOWTIME
        in_time = datetime.datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S.%f')

        #在室時間を計算
        day_time = now_time - in_time
        if memberdb.DAYTIME == None:
            allday_time = day_time
        else:
            allday_time = memberdb.DAYTIME
            hours, minutes, seconds = map(float, allday_time.split(":"))
            allday_time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
            allday_time += day_time
        memberdb.DAYTIME = str(allday_time)

        #退出する場合
        if joutai == 0:
            # all_timeを計算（総在室時間）
            if memberdb.ALLTIME == None:
                all_time = allday_time
            else:
                all_time = memberdb.ALLTIME
                hours, minutes, seconds = map(float, all_time.split(":"))
                all_time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
                all_time += allday_time

            memberdb.ALLTIME = str(all_time)
            #memberdb.DAYTIME = None

    db.session.commit()
    db.session.close()
    MEMBERDB_infos = db.session.query(MEMBERDB.MEMBER, MEMBERDB.JOUTAI, MEMBERDB.INTIME, MEMBERDB.OUTTIME, MEMBERDB.DAYTIME, MEMBERDB.ALLTIME).all()

    return render_template("menu.html",members_length = members_length, members = members, situations = situations, joutai = int(joutai), num = int(num), now = now, LOGDB_infos = LOGDB_infos)

