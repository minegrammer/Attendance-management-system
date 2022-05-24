# Flaskの操作に必要なモジュールをインポート
from flask import Flask, render_template, request
import datetime
import boto3
from boto3.dynamodb.conditions import Key

# Flaskの立ち上げ
app = Flask(__name__)
app.config['KEY'] = 'key'

# Get the service resource.
dynamodb = boto3.resource('dynamodb')

'''
# ログのテーブル作成
member_log = dynamodb.create_table(
    TableName='member_log',
    KeySchema=[
        {
            'AttributeName': 'number',
            'KeyType': 'HASH'
        },
        {
            'AttributeName': 'time',
            'KeyType': 'RANGE'
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'number',
            'AttributeType': 'N'
        },
        {
            'AttributeName': 'time',
            'AttributeType': 'S'
        },
    ],
    BillingMode='PAY_PER_REQUEST'
)

# Wait until the table exists.
member_log.meta.client.get_waiter('table_exists').wait(TableName='member_log')

# メンバーのテーブル作成
member_table = dynamodb.create_table(
    TableName='member_table',
    KeySchema=[
        {
            'AttributeName': 'number',
            'KeyType': 'HASH'
        },
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'number',
            'AttributeType': 'N'
        },
    ],
    BillingMode='PAY_PER_REQUEST'
)

# Wait until the table exists.
member_table.meta.client.get_waiter('table_exists').wait(TableName='member_table')
'''

# 研究室もメンバーをmembersリストで作成
members = ["A", "B", "C", "D", "E"] 
numbers = [1,2,3,4,5]
# 人数を調べる
members_length = len(members)
# 現在の状態を格納するnow_statusリストを人数分作成
now_status = [0] * members_length
# ３種の状態を保持するsituationsリストの作成
situations = ["帰宅", "一時外出中", "在室"]

# メニューを表示
@app.route("/")
def menu(): 
    return render_template("menu.html",members_length = members_length,  members = members, situations = situations, now_status = now_status,)

# 行動を選択
@app.route("/select", methods = ["GET", "POST"])
def sel(): 

    num = request.args.get("num")

    return render_template("select_button.html",members_length = members_length, members = members ,situations = situations, num=int(num), now_status = now_status)

# 選択済みメニュー
@app.route("/a", methods = ["GET", "POST"])
def menu1():

    num = int(request.form.get("num"))
    status = int(request.form.get("status"))

    now_status[num] = status

    now_time = str(datetime.datetime.now())
    
    #ログのアイテムの作成
    member_log = dynamodb.Table('member_log')
    member_log.put_item(
        Item={
        'number': numbers[num],
        'status': status,
        'time': now_time,
        }
    )

    # 入室時の時刻を代入し、データ更新
    if status == 2:
        member_table = dynamodb.Table('member_table')
        member_table.update_item(
            Key={
                'number': numbers[num]
            },
            UpdateExpression='SET #s = :s, #i = :i ',
            ExpressionAttributeNames={
                '#s': 'status',
                '#i': 'in_time',
            },
            ExpressionAttributeValues={
                ':s': status,
                ':i': now_time,
            }
        )

    # 退室or一時退室の時刻を代入し、データ更新
    elif status == 0 or status == 1:
        member_table = dynamodb.Table('member_table')
        member_table.update_item(
            Key={
                'number': numbers[num]
            },
            UpdateExpression='SET #s = :s, #o = :o ',
            ExpressionAttributeNames={
                '#s': 'status',
                '#o': 'outtime',
            },
            ExpressionAttributeValues={
                ':s': status,
                ':o': now_time,
            }
        )

        
    return render_template("menu.html",members_length = members_length, members = members, situations = situations, status = int(status), num = int(num), now_status = now_status)
