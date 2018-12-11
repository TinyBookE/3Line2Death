from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests

# 数据库信息
duser = '3Line2Death'
dpwd = 'u5fkR8YIHHvSrumQ'
daddr = 'localhost'
dport = 3306
dname = '3Line2Death'

# app信息
port = 2333
host = '202.114.205.217'

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
        l = self.content.split('|')
        if flag == 0:
            return {'noteId':self.noteId, 'first':l[0], 'second':l[1],
                    'third':l[2],'name':self.name, 'numOfPraise':self.numOfPraise,
                    'head':self.head}
        if flag is None:
            return {'noteId':self.noteId,'first':l[0], 'second':l[1],
                    'third':l[2],'name':self.name, 'numOfPraise':self.numOfPraise,
                    'flag':False, 'head':self.head}
        return {'noteId': self.noteId,'first':l[0], 'second':l[1],
                'third':l[2],'writer': self.writer, 'numOfPraise': self.numOfPraise,
                'flag': True, 'head':self.head}


class Record(db.Model):
    key = db.Column(db.Integer, primary_key = True)
    noteId = db.Column(db.Integer)
    openid = db.Column(db.String(20))

    def __init__(self, noteId, openid):
        self.noteId = noteId
        self.openid = openid


# 点赞功能
"""
输入 json:
{
    noteId:被投票作品id
    openid:用户id
}
返回 json:
{
    code:结果代码
    msg:结果详细信息
}
"""
@app.route('/3Line2Death/praise', methods=['POST'])
def Praise():
    Content_Type = request.headers['Content-Type'].split(';')
    if 'application/json' not in Content_Type:
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
"""
输入 json:
{
    first: 第一行
    second: 第二行
    third: 第三行
    name:用户名称
    head:用户头像url
    openid:用户id
}
返回 json:
{
    code:结果代码
    msg:结果详细信息
    data:若有完全重复, 则会返回已收录的遗书记录
}
"""
@app.route('/3Line2Death/upload', methods=['POST'])
def Upload():
    Content_Type = request.headers['Content-Type'].split(';')
    if 'application/json' not in Content_Type:
        return jsonify({'code':10001, 'msg': '格式出错，需求json'})
    form = request.json
    if 'first' not in form or 'name' not in form\
            or 'head' not in form or 'openid' not in form\
            or 'second' not in form or 'third' not in form:
        return jsonify({'code': 10002, 'msg': '信息出错'})

    content = form['first']+'|'+form['second']+'|'+form['third']
    name = form['name']
    head = form['head']
    openid = form['openid']
    if not Check(openid):
        return jsonify({'code': 10003, 'msg': '用户未绑定'})
    note = Note.query.filter_by(content=content).first()
    if not note is None:
        return jsonify({'code':1, 'msg':'已收录该遗书','data': note.todict()})
    note = Note.query.filter_by(openid= openid).first()
    if note is None:
        db.session.add(Note(content,name,head,openid))
        db.session.commit()
        return jsonify({'code': 0, 'msg': '成功'})

    return jsonify({'code': 10005, 'msg': '已有提交作品'})


# 查询全部作品
"""
输入 json:
{
    sortWay:排序方式
            可选参数 0(按投票数从高到低)/1(按时间从前往后)
    openid:用户id
}
返回 json:
{
    code:结果代码
    msg:结果详细信息
    data:结果数据
        {
            noteId:作品id
            first:
            second:
            third:
            name:作者姓名
            head:作者头像url
            flag:是否投过票
        }
}
"""
@app.route('/3Line2Death/search/all', methods=['POST'])
def SearchAll():
    Content_Type = request.headers['Content-Type'].split(';')
    if 'application/json' not in Content_Type:
        return jsonify({'code':10001, 'msg': '格式出错，需求json'})
    sortWay = request.json['sortWay']
    openid = request.json['openid']
    page = request.json['page']
    # 投票数排序
    if sortWay == 0:
        if page == 0:
            note = Note.query.order_by(db.desc(Note.numOfPraise)).all()
        else:
            note = Note.query.order_by(db.desc(Note.numOfPraise)).paginate(page,10,False).items
        t = {'code': 0, 'msg': '成功', 'data':{}}
        for i in range(len(note)):
            flag = Record.query.filter_by(noteId=note[i].noteId, openid=openid).first()
            t['data'][str(i)] = note[i].todict(flag)
        return jsonify(t)
    # 发布时间排序
    elif sortWay == 1:
        if page == 0:
            note = Note.query.order_by(Note.noteId).all()
        else:
            note = Note.query.order_by(Note.noteId).paginate(page,10,False).items
        t = {'code': 0, 'msg': '成功', 'data':{}}
        for i in range(len(note)):
            flag = Record.query.filter_by(noteId=note[i].noteId, openid=openid).first()
            t['data'][str(i)] = note[i].todict(flag)
        return jsonify(t)
    return jsonify({'code': 10006, 'msg':'排序方式出错'})


# 查询单个作品
"""
输入 json:
{
    sender:查询自己作品或指定他人作品
           可选参数 writer/reader
    openid:用户openid
    noteid:查询他人作品需要的遗书id
}
返回 json:
{
    code:结果代码
    msg:结果详细信息
    data:结果数据
        {
            noteId:作品id
            first:
            second:
            third:
            name:作者姓名
            head:作者头像url
            flag:是否投过票
        }
}
"""
@app.route('/3Line2Death/search/one', methods=['POST'])
def SearchOne():
    Content_Type = request.headers['Content-Type'].split(';')
    if 'application/json' not in Content_Type:
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
