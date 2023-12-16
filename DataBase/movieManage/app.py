# -*- coding: utf-8 -*-
"""
Created on Sun Nov 12 13:44:44 2023

@author: Panda Jiang
"""

from flask import Flask, render_template, request
import pymysql
import mysql.connector

# 题目：电影管理系统
# 功能：电影的录入、查询、演员的查询、票房分析、票房预测。

app = Flask(__name__)

# 数据库连接信息
def get_db_connection():
    db = pymysql.connect(host="localhost", user="root", passwd="", port=3306, database="movieDB")
    return db

def search_movie(movie_name):
    db = get_db_connection()
    cursor = db.cursor()
    exact_movie_query = """
    SELECT movie_info.*, move_box.box 
    FROM movie_info 
    JOIN move_box ON movie_info.movie_id = move_box.movie_id 
    WHERE movie_info.movie_name = %s
    """
    # 尝试精确匹配
    cursor.execute(exact_movie_query, (movie_name,))
    exact_matches = cursor.fetchall()

    if len(exact_matches) > 0:
        # 如果找到精确匹配
        movies = exact_matches
        message = "搜索结果如下："
    else:
        # 如果没有精确匹配，尝试模糊匹配
        fuzzy_movie_query = """
        SELECT movie_info.*, move_box.box 
        FROM movie_info 
        JOIN move_box ON movie_info.movie_id = move_box.movie_id 
        WHERE movie_info.movie_name LIKE %s
        """
        cursor.execute(fuzzy_movie_query, ('%' + movie_name + '%',))
        fuzzy_matches = cursor.fetchall()
        movies=fuzzy_matches
        if len(fuzzy_matches) > 0:
            message = f"没有搜到名称为‘{movie_name}’的电影，猜您感兴趣："
        else:
            message = f"没有搜到名称为‘{movie_name}’的电影，您可以尝试其他关键词。"
        
    cursor.close()
    db.close()
    return movies,message

def search_actor(actor_name):
    db = get_db_connection()
    cursor = db.cursor()

    # 定义精确匹配查询
    exact_actor_query = """
    SELECT actor_info.actor_name, actor_info.gender, actor_info.country, 
           movie_actor_relation.relation_type, movie_info.*, move_box.box
    FROM actor_info
    JOIN movie_actor_relation ON actor_info.actor_id = movie_actor_relation.actor_id
    JOIN movie_info ON movie_actor_relation.movie_id = movie_info.movie_id
    JOIN move_box ON movie_info.movie_id = move_box.movie_id
    WHERE actor_info.actor_name = %s
    ORDER BY actor_info.actor_name
    """

    # 尝试精确匹配
    cursor.execute(exact_actor_query, (actor_name,))
    exact_matches = cursor.fetchall()

    if len(exact_matches) > 0:
        # 如果找到精确匹配
        actors = exact_matches
        message = "搜索结果如下："
    else:
        # 如果没有精确匹配，尝试模糊匹配
        fuzzy_actor_query = """
        SELECT actor_info.actor_name, actor_info.gender, actor_info.country, 
               movie_actor_relation.relation_type, movie_info.*, move_box.box
        FROM actor_info
        JOIN movie_actor_relation ON actor_info.actor_id = movie_actor_relation.actor_id
        JOIN movie_info ON movie_actor_relation.movie_id = movie_info.movie_id
        JOIN move_box ON movie_info.movie_id = move_box.movie_id
        WHERE actor_info.actor_name LIKE %s
        ORDER BY actor_info.actor_name

        """
        cursor.execute(fuzzy_actor_query, ('%' + actor_name + '%',))
        fuzzy_matches = cursor.fetchall()
        actors = fuzzy_matches
        if len(fuzzy_matches) > 0:
            message = f"没有搜到名称为‘{actor_name}’的演员，猜您感兴趣："
        else:
            message = f"没有搜到名称为‘{actor_name}’的演员，您可以尝试其他关键词。"
        
    cursor.close()
    db.close()
    return actors, message


# def search_actor(actor_name):
#     db = get_db_connection()
#     cursor = db.cursor()

#     # 尝试精确匹配
#     cursor.execute(exact_actor_query, (actor_name,))
#     exact_matches = cursor.fetchall()

#     if len(exact_matches) > 0:
#         # 如果找到精确匹配
#         return exact_matches
#     else:
#         # 如果没有精确匹配，尝试模糊匹配
#         cursor.execute(fuzzy_actor_query, ('%' + actor_name + '%',))
#         fuzzy_matches = cursor.fetchall()
#         return fuzzy_matches

#     cursor.close()
#     db.close()

# db = pymysql.connect(host="localhost", user="root", passwd="", port=3306, database="movieDB")
# db = mysql.connector.connect(host="localhost", user="root", passwd="", port=3306, database="movieDB")

# @app.route('/')
# def show_tables():
#     cursor = db.cursor()
#     cursor.execute("SHOW TABLES")
#     tables = cursor.fetchall()
#     return render_template('tables.html', tables=tables)

# @app.route('/table/<table_name>')
# def show_table_contents(table_name):
#     cursor = db.cursor()
#     cursor.execute(f"SELECT * FROM {table_name}")
#     data = cursor.fetchall()
#     return render_template('table_contents.html', data=data, table_name=table_name)



# @app.route('/', methods=['GET', 'POST'])
# def index():
#     # ```
#     message = ""
#     movies = [] 
#     # search_performed = False  # 新增变量来跟踪是否执行了搜索
#     # ```
#     if request.method == 'POST':
#         movie_name = request.form['movie_name']
#         movies,message =search_movie(movie_name)
        
       

#     return render_template('index.html', message=message, movies=movies)



@app.route('/')
def index():
    return render_template('index1.html')

@app.route('/search_movie', methods=['GET', 'POST'])
def search_movie_results():
    message = ""
    movies = []

    if request.method == 'POST':
        movie_name = request.form['movie_name']
        movies, message = search_movie(movie_name)

    return render_template('search_movie.html', message=message, movies=movies)

@app.route('/search_actor', methods=['GET', 'POST'])
def search_actor_results():
    message = ""
    actors = []

    if request.method == 'POST':
        actor_name = request.form['actor_name']
        actors, message = search_actor(actor_name)

    return render_template('search_actor.html', message=message, actors=actors)



# if __name__ == '__main__':
#     app.run(debug=True)
