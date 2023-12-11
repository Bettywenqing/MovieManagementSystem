from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from datetime import datetime
import string, random

app = Flask(__name__)  # 创建一个名为 app 的 Flask 应用程序对象

# 数据库配置
# 设置flask应用程序app的数据库连接URI，该URI描述了要连接的数据库，类型为mysql，用户名为root，密码为123，主机地址为localhost，端口号为3306，数据库名称为moviedb，编码使用utf-8
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://root:123@localhost:3306/moviedb?charset=utf8"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 禁止对模型的更改进行跟踪，可以节省资源并提高性能
db = SQLAlchemy(app)  # 创建了一个SQLAlchemy对象db，并使用之前的flask程序app进行初始化，db可用于定义数据库模型和执行数据库操作


# 将根URL‘/’与名为index的视图函数绑定，当用户用GET方法访问根URL时，flask会调用该视图函数
@app.route('/', methods=['GET'])  # 将视图函数与URL绑定
def index():  # 定义视图函数，该视图函数负责处理根URL的GET请求
    return render_template('index.html')  # 渲染名为index.html的模板文件，并将其作为响应返回给用户


# 创建两个变量，分别定义演员和电影数据结构
movieKeys = ['movieId', 'movieName', 'releaseDate', 'country', 'type', 'year']
performerKeys = ['actorId', 'actorName', 'gender', 'country']


# 定义名为 generateRandomString 的函数，用于生成随机字符串，length指定了生成字符串长度为10
def generateRandomString(length=10):
    characters = string.ascii_letters + string.digits  # 该字符集中包含所有字母和数字
    return ''.join(random.choice(characters) for i in range(length))  # 从字符集中随机选取字符并将其进行拼接后返回


# 用于处理用户发出的搜索请求的函数，ps.只能单独对电影或演员进行查询，目前无法实现关联查询的功能
@app.route('/searchParameter', methods=['POST'])  # 当收到发往 /searchParameter 路径的 POST 请求时，应该调用下面定义的函数来处理这个请求
def searchParameter():
    data = request.get_json()  # 获取POST请求中的JSON数据
    queryParam = data.get('param')  # 从JSON数据中提取param字段
    queryAction, queryData = queryParam.split('=')  # 按照=将该字段分为两个部分

    with db.engine.connect() as conn:  # 创建与数据库的连接，并使用with语句确保其执行完成后可正确关闭，并将连接对象赋值给变量conn
        if queryAction == 'moviename':  # 先处理对电影的检索部分
            sql = text("SELECT * FROM movie_info WHERE movie_name = :name")  # 执行SQL查询，查找数据库中与给定电影名称匹配的电影信息
            result = conn.execute(sql,
                                  {'name': queryData}).fetchone()  # 通过电影名称查询电影信息，执行查询并传入参数，fetchone() 返回查询结果的第一行数据。
            # print(result, '7777777777777777777777')
            if not result:  # 如果在数据库中不存在该数据
                return jsonify({'code': 400, 'message': '您要查询的电影或演员不存在，请重试'})  # 返回一个JSON响应，表示未找到相关信息
            result = dict(zip(movieKeys, result))  # 查询到了结果，将结果转换为字典格式，将查询结果与 movieKeys 列表中的键进行关联，形成字典，其中键是电影信息的属性名称
            # print(result, '6666666666666666666666')
            result['releaseDate'] = result.get('releaseDate').strftime('%Y年%m月%d日')  # 对结果中的发行日期进行了格式化处理，约定了返回的统一格式
            sql = text("SELECT box FROM move_box WHERE movie_id = :id")  # 同时查询电影的票房信息
            # print(result, result.get('movieId'), '-------------')
            box_obj = conn.execute(sql,
                                   {'id': result.get('movieId')}).fetchone()  # 通过电影id查询票房信息，返回查询结果的第一行数据，将结果储存在box_obj中
            if not box_obj:  # 如果在数据库中未查询到票房信息
                result['box'] = '插入错误//'
                result['code'] = 200
                return jsonify(result)  # 返回一个JSON相应，表示未查询到相关信息
            result['box'] = box_obj[0]
            sql = text("SELECT actor_id, relation_type FROM movie_actor_relation WHERE movie_id = :id")  # 获取相关演员信息
            data = conn.execute(sql, {'id': result.get('movieId')}).fetchall()  # 通过查询电影的id来查询演员id和联系
            sql = text("SELECT actor_name FROM actor_info WHERE actor_id = :id")  # 通过演员id查询演员姓名
            for actorId, relationType in data:
                result[relationType] = conn.execute(sql, {'id': actorId}).fetchone()[0]

            result['code'] = 200  # 将查询成功的code设置为200
            return jsonify(result)  # 返回包含该电影所有信息的JSON响应
        elif queryAction == 'performername':  # 对演员部分进行查询
            sql = text("SELECT * FROM actor_info WHERE actor_name = :name")  # 查询演员表中的演员信息
            result = conn.execute(sql, {'name': queryData}).fetchone()  # 通过演员姓名查询演员信息
            if not result:  # 如果该演员的信息不存在于演员数据库中
                return jsonify({'code': 400, 'message': f'您要查询的电影或演员不存在，请重试'})  # 返回一个JSON响应，表示未查找到相关信息
            data = dict(
                zip(performerKeys, result))  # 查询到了结果，将结果转换为字典格式，将查询结果与performerKeys列表中的键进行关联，形成字典，其中键是表演者信息的属性名称
            data['code'] = 200  # 将code设置为200表示成功
    return jsonify(data)  # 将检索到的信息返回


# 下面对用于电影信息的录入
@app.route('/submitMovieInfo', methods=['POST'])
def submitMovieInfo():  # 当收到发往 /submitMovieInfo 路径的 POST 请求时，应该调用下面定义的函数来处理这个请求
    data = request.get_json()  # 获取POST请求中的JSON数据
    try:  # 从传入的JSON数据中提取电影名称，国家，类型，主演，导演，票房，上映时间的信息
        movieName = data.get('name')
        country = data.get('country')
        movieType = data.get('type')
        leader = data.get('leader')
        main = data.get('main')
        money = int(data.get('money')) / 10000  # 将票房的单位进行转换
        dateObj = datetime.strptime(data.get('publish_time'), '%Y年%m月%d日').strftime('%Y-%m-%d')  # 将上映时间的格式转换，方便储存和处理
        year = data.get('publish_time').split('年')[0]  # 从上映的时间中提取出年份，这里原本是希望进行票房分析
        if not year:  # 检查是否成功提取了年份，如果没有则返回一个参数错误的JSON响应
            return jsonify({'code': 400, 'message': '参数错误'})
    except Exception as e:  # 在前面的数据提取、格式转换中出现任何异常，可以捕捉该异常并将异常信息包含在返回的JSON响应中，指示参数错误
        return jsonify({'code': 400, 'message': f'参数错误 {e}'})
    if_exist_sql = text("SELECT * FROM movie_info WHERE movie_name = :movieName")  # 检查数据库中是否已经存在同名电影

    insertMovieSql = text("""
            INSERT INTO movie_info (movie_id, movie_name, release_date, country, type, year)
            VALUES (:movie_id, :movie_name, :release_date, :country, :type, :year)
        """)  # 定义SQL语句，用于向movie_info中插入电影信息
    with db.engine.connect() as conn:  # 创建与数据库的连接，并使用with语句确保其执行完成后可正确关闭，并将连接对象赋值给变量conn
        if conn.execute(if_exist_sql,
                        {'movieName': movieName}).fetchone():  # 查询数据库中是否已经存在当前录入的电影，如果存在则返回JSON响应，表示电影已经存在，状态码为400
            return jsonify({'code': 400, 'message': '电影已存在'})
        conn.execute(insertMovieSql,
                     {'movie_id': generateRandomString(), 'movie_name': movieName, 'release_date': dateObj,
                      'country': country,
                      'type': movieType,
                      'year': year})  # 执行之前定义的insertmoviesql语句，其中电影id使用随机的方式生成
        conn.commit()  # 提交了对数据库的修改，将信息电影信息写入数据库
        sql = text("SELECT * FROM actor_info WHERE actor_name = :name")  # 查询输入的演员和导演名，并将其id进行获取
        mainId = conn.execute(sql, {'name': main}).fetchone()
        leaderId = conn.execute(sql, {'name': leader}).fetchone()
        if not main or not leader:  # 如果main或leader为空，则会返回一个JSON响应，指示导演或演员不存在
            return jsonify({'code': 400, 'message': '参数错误,演员或导演不存在'})
        findMovieIdSql = text("SELECT movie_id FROM movie_info WHERE movie_name = :name")
        movieId = conn.execute(findMovieIdSql, {'name': movieName}).fetchone()[0]  # 刚才已经录入了电影信息，现在需要提取电影id，在其他表中进行信息录入
        insertRelationSql = text(
            """INSERT INTO movie_actor_relation (id, movie_id, actor_id, relation_type) 
            VALUES (:id, :movie_id, :actor_id, :relation_type)""")  # 定义向电影-演员关系表中插入数据的SQL语句
        movieBoxSql = text(
            """INSERT INTO move_box (movie_id, box) 
            VALUES (:movie_id, :box)""")  # 定义向票房表插入数据的SQL语句
        try:
            conn.execute(insertRelationSql, {'id': generateRandomString(), 'movie_id': movieId, 'actor_id': mainId[0],
                                             'relation_type': '主演'})  # 执行插入主演操作，该id随机生成
            conn.execute(insertRelationSql,
                         {'id': generateRandomString(), 'movie_id': movieId, 'actor_id': leaderId[0],
                          'relation_type': '导演'})  # 执行插入导演操作，该id随机生成
            conn.execute(movieBoxSql, {'movie_id': movieId, 'box': money})  # 执行插入票房操作
            conn.commit()  # 提交操作
        except Exception as e:  # 如果上述操作中存在异常，返回异常JSON响应
            return jsonify({'code': 400, 'message': '参数错误,演员或导演不存在'})
    return jsonify({'code': 200, 'message': '提交成功'})  # 上述操作执行结束后，返回JSON响应并显示提交成功


if __name__ == '__main__':
    app.run()  # 运行当前程序
