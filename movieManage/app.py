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



@app.route('/', methods=['GET', 'POST'])
def index():
    # ```
    message = ""
    movies = [] 
    # search_performed = False  # 新增变量来跟踪是否执行了搜索
    # ```
    if request.method == 'POST':
        movie_name = request.form['movie_name']
        db = get_db_connection()
        cursor = db.cursor()
        
        # 先尝试精确匹配
        exact_query = "SELECT * FROM movie_info WHERE movie_name = %s"
        cursor.execute(exact_query, (movie_name,))
        exact_matches = cursor.fetchall()

        if len(exact_matches) == 0:
            # 如果没有精确匹配，进行模糊匹配
            fuzzy_query = "SELECT * FROM movie_info WHERE movie_name LIKE %s"
            cursor.execute(fuzzy_query, ('%' + movie_name + '%',))
            movies = cursor.fetchall()
            if len(movies) > 0:
                message = f"没有搜到名称为‘{movie_name}’的电影，猜您感兴趣："
            else:
                message = f"没有搜到名称为‘{movie_name}’的电影，您可以尝试其他关键词。"
            # message = f"没有搜到名称为‘{movie_name}’的电影，猜您感兴趣："
        else:
            movies = exact_matches

        cursor.close()
        db.close()

    return render_template('index.html', message=message, movies=movies)
        
        
        
    #     query = "SELECT * FROM movie_info WHERE movie_name LIKE %s"
    #     cursor.execute(query, ('%' + movie_name + '%',))
    #     movies = cursor.fetchall()
    #     cursor.close()
    #     db.close()
    #     return render_template('index.html', movies=movies)
    # return render_template('index.html', movies=[])

# if __name__ == '__main__':
#     app.run(debug=True)
