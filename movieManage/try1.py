# -*- coding: utf-8 -*-
"""
Created on Sun Dec  3 09:03:20 2023

@author: Panda Jiang
"""

from flask import Flask, render_template, request
import pymysql
import mysql.connector

# app = Flask(__name__)

# 数据库连接信息
def get_db_connection():
    db = pymysql.connect(host="localhost", user="root", passwd="", port=3306, database="movieDB")
    return db

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

name='王'
actors, message =search_actor(name)
print(actors, message)

