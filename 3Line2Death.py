from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests

# 数据库信息
duser = 'root'
dpwd = ''
daddr = 'localhost'
dport = 3306
dname = '3Line2Death'

# app信息
port = 2333
host = 'localhost'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(duser, dpwd, daddr, dport, dname)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class Note(db.Model):
    noteId = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.String(99))
    name = db.Column(db.String(20))
    head = db.Column(db.String(99))
    openid = db.Column(db.String(99))
    numOfPraise = db.Column(db.Integer)

    def __init__(self, content, name, head, openid, numOfPriase = 0):
        self.content = content
        self.name = name
        self.head = head
        self.openid = openid
        self.numOfPraise = numOfPriase

    def todict(self, flag = 0):
        if flag == 0:
            return {'noteId':self.noteId, 'content':self.content,
                    'name':self.name, 'numOfPraise':self.numOfPraise,
                    'head':self.head}
        if flag is None:
            return {'noteId':self.noteId, 'content':self.content,
                    'name':self.name, 'numOfPraise':self.numOfPraise,
                    'flag':False, 'head':self.head}
        return {'noteId': self.noteId, 'content': self.content,
                'writer': self.writer, 'numOfPraise': self.numOfPraise,
                'flag': True, 'head':self.head}


class Record(db.Model):
    key = db.Column(db.Integer, primary_key = True)
    noteId = db.Column(db.Integer)
    openid = db.Column(db.String(20))

    def __init__(self, noteId, openid):
        self.noteId = noteId
        self.openid = openid


# 点赞功能
@app.route('/3Line2Death/praise', methods=['POST'])
def Praise():
    if request.headers['Content-Type'] != 'application/json':
        return jsonify({'code':10001, 'msg': '格式出错，需求json'})
    form = request.json
    if 'noteId' not in form or 'openid' not in form:
        return jsonify({'code':10002, 'msg': '信息出错'})

    noteId = form['noteId']
    openid = form['openid']
    if not Check(openid):
        return jsonify({'code': 10003, 'msg': '用户未绑定'})
    record = Record.query.filter_by(noteId=noteId, openid=openid).first()
    if record is None:
        note = Note.query.filter_by(noteId=noteId).first()
        note.numOfPraise += 1
        db.session.commit()
        db.session.add(Record(noteId, openid))
        db.session.commit()

        return jsonify({'code': 0, 'msg': '成功'})

    return jsonify({'code': 10004, 'msg': '同作品多次点赞'})


# 上传作品
@app.route('/3Line2Death/upload', methods=['POST'])
def Upload():
    if request.headers['Content-Type'] != 'application/json':
        return jsonify({'code':10001, 'msg': '格式出错，需求json'})
    form = request.json
    if 'content' not in form or 'name' not in form\
            or 'head' not in form or 'openid' not in form:
        return jsonify({'code': 10002, 'msg': '信息出错'})

    content = form['content']
    name = form['name']
    head = form['head']
    openid = form['openid']
    if not Check(openid):
        return jsonify({'code': 10003, 'msg': '用户未绑定'})
    note = Note.query.filter_by(openid= openid).first()
    if note is None:
        db.session.add(Note(content,name,head,openid))
        db.session.commit()
        return jsonify({'code': 0, 'msg': '成功'})

    return jsonify({'code': 10005, 'msg': '已有提交作品'})


# 查询全部作品
@app.route('/3Line2Death/search/all', methods=['POST'])
def SearchAll():
    if request.headers['Content-Type'] != 'application/json':
        return jsonify({'code':10001, 'msg': '格式出错，需求json'})
    sortWay = request.json['sortWay']
    openid = request.json['openid']
    # 投票数排序
    if sortWay == 0:
        note = Note.query.order_by(db.desc(Note.numOfPraise)).all()
        t = {'code': 0, 'msg': '成功', 'data':{}}
        for i in range(len(note)):
            flag = Record.query.filter_by(noteId=note[i].noteId, openid=openid).first()
            t['data'][str(i)] = note[i].todict(flag)
        return jsonify(t)
    # 发布时间排序
    elif sortWay == 1:
        note = Note.query.order_by(Note.noteId).all()
        t = {'code': 0, 'msg': '成功', 'data':{}}
        for i in range(len(note)):
            flag = Record.query.filter_by(noteId=note[i].noteId, openid=openid).first()
            t['data'][str(i)] = note[i].todict(flag)
        return jsonify(t)
    return jsonify({'code': 10006, 'msg':'排序方式出错'})


# 查询单个作品
@app.route('/3Line2Death/search/one', methods=['POST'])
def SearchOne():
    if request.headers['Content-Type'] != 'application/json':
        return jsonify({'code':10001, 'msg': '格式出错，需求json'})

    sender = request.json['sender']
    openid = request.json['openid']
    if sender == 'writer':
        note = Note.query.filter_by(openid=openid).first()
        noteId = note.noteId
        if note is None:
            return jsonify({'code':10007, 'msg':'不存在作品'})

        flag = Record.query.filter_by(noteId=noteId, openid=openid).first()
        return jsonify({'code':0, 'msg': '成功', 'data':note.todict(flag)})

    elif sender == 'reader':
        noteId = request.form['noteId']
        note = Note.query.filter_by(noteId=noteId).first()
        if note is None:
            return jsonify({'code':10007, 'msg':'不存在作品'})

        flag = Record.query.filter_by(noteId =noteId,openid=openid).first()
        return jsonify({'code':0, 'msg': '成功', 'data':note.todict(flag)})

    return jsonify({'code': 10002, 'msg': '信息出错'})


def Check(openid):
    url = r'https://icug.net.cn/wechat/basic_info'
    body = {'openid': openid}
    r = requests.post(url, body).json()
    if r['code'] ==0:
        return True
    return False


if __name__ == '__main__':
    db.create_all()
    app.run(host=host,port=port)
