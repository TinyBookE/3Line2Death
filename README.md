# 3Line2Death
三行遗书
### 环境
- python 3.6
- mysql 8.0
- flask
- requests
- flask
- flask_sqlalchemy

## 前端对接
#### 点赞
POST 202.114.205.217:2333/3Line2Death/praise

Headers:
Content-Type:application/json
Body:
{
    "noteId":"遗书id"
    "openId":"用户id"
}

Responds:
{
    code:结果编码
    msg:结果详细信息
}

#### 上传
POST 202.114.205.217:2333/3Line2Death/upload

Headers:
Content-Type:application/json
Body:
{
    "content":"内容"
    "name":"用户名称"
    "head":"用户头像url"
    "openid":"用户id"
}

Responds:
{
    "code":结果编码
    "msg":"结果详细信息"
    "data":{若有完全重复, 则会返回已收录的遗书记录}
}

#### 查询全部作品
POST 202.114.205.217:2333/3Line2Death/searchall

Headers:
Content-Type:application/json
Body:
{
    "sortWay": 0(按投票数从高到低)/1(按时间从前往后)
    "openid":"用户id"  用来判断是否点过赞
}

Responds:
{
    "code":结果编码
    "msg":"结果详细信息"
    "data":{
              "0"
              {
                "noteId":作品id
                "content":"内容"
                "name":"作者姓名"
                "head":"作者头像url"
                "flag": True/False     点过赞?
              }
              "1"
              {
                "noteId":作品id
                "content":"内容"
                "name":"作者姓名"
                "head":"作者头像url"
                "flag": True/False     点过赞?
              }
           }
}

#### 查询单个作品
POST 202.114.205.217:2333/3Line2Death/searchone

Headers:
Content-Type:application/json
Body:
{
    "sender":"writer"(自己作品)/"reader"(他人作品)
    "openid":"用户openid"
    "noteid":查询他人作品需要的遗书id
}

Responds:
{
    "code":结果编码
    "msg":结果详细信息
    "data":结果数据
        {
            "noteId":作品id
            "content":"内容"
            "name":"作者姓名"
            "head":"作者头像url"
            "flag":True/False
        }
}
