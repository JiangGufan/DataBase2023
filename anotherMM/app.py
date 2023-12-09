# -*- coding: utf-8 -*-
"""
Created on Sun Dec  3 18:01:04 2023

@author: Panda Jiang
"""
import os
import sys

from flask import Flask, render_template, request
import pymysql
import mysql.connector

from collections import defaultdict
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy
# 确保导入了必要的 SQLAlchemy 类
from sqlalchemy import Column, String, Integer, ForeignKey, Date, CheckConstraint
from sqlalchemy.sql.expression import cast
from sqlalchemy.orm import relationship

# 题目：电影管理系统
# 功能：电影的录入、查询、演员的查询、票房分析、票房预测。

app = Flask(__name__)

# 确保数据库 URI 使用正确的格式和驱动
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/movie100'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化 db 对象，无需调用 init_app，因为您已经在创建时传递了 app
db = SQLAlchemy(app)

class MovieInfo(db.Model):
    __tablename__ = 'movie_info'
    movie_id = db.Column(db.String(10), primary_key=True)
    movie_name = db.Column(db.String(20), nullable=False)
    box_office = db.Column(db.Numeric(10, 4))
    release_date = db.Column(db.DateTime)
    country = db.Column(db.String(20))
    douban_rating = db.Column(db.Numeric(3, 1))
    year = db.Column(db.Integer, nullable=False)

    # Relationship to the movie_actor_relation table
    actors = db.relationship('MovieActorRelation', back_populates='movie')

class MoviePersonInfo(db.Model):
    __tablename__ = 'movie_person_info'
    movie_person_id = db.Column(db.String(10), primary_key=True)
    movie_person_name = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(20))

    # Relationship to the movie_actor_relation table
    movie_relations = db.relationship('MovieActorRelation', back_populates='person')

class MovieActorRelation(db.Model):
    __tablename__ = 'movie_actor_relation'
    id = db.Column(db.String(10), primary_key=True)
    movie_id = db.Column(db.String(10), db.ForeignKey('movie_info.movie_id'))
    movie_person_id = db.Column(db.String(10), db.ForeignKey('movie_person_info.movie_person_id'))
    relation_type = db.Column(db.String(20))

    # Relationships to the other tables
    movie = db.relationship('MovieInfo', back_populates='actors')
    person = db.relationship('MoviePersonInfo', back_populates='movie_relations')

# 电影人相关联作品查询
def search_movies_by_actor(actor_name):
    return db.session.query(
        MovieInfo.movie_name,
        MovieInfo.box_office,
        MovieInfo.release_date,
        MovieInfo.country,
        MovieInfo.douban_rating,
        MovieInfo.year,
        MoviePersonInfo.movie_person_name,
        MoviePersonInfo.country.label('actor_country'),
        MovieActorRelation.relation_type
    ).join(
        MovieActorRelation, MovieInfo.movie_id == MovieActorRelation.movie_id
    ).join(
        MoviePersonInfo, MovieActorRelation.movie_person_id == MoviePersonInfo.movie_person_id
    ).filter(
        MoviePersonInfo.movie_person_name.ilike(f"%{actor_name}%")
    ).order_by(
        MovieActorRelation.relation_type,MoviePersonInfo.movie_person_name
    ).all()

# actor_movies={}
# movies = search_movies_by_actor('王')
# for movie in movies:
#     key = (movie.movie_person_name, movie.actor_country)  # 第一层 姓名 地区
#     relation_type = movie.relation_type  # 第二层 关系

#     if key not in actor_movies:
#         actor_movies[key] = {}

#     if relation_type not in actor_movies[key]:
#         actor_movies[key][relation_type] = {'count': 0, 'movies': []}

#     # 增加电影数量计数
#     actor_movies[key][relation_type]['count'] += 1
#     actor_movies[key][relation_type]['movies'].append(movie)
# print(actor_movies)


# 电影人相关票房的查询函数
def get_top_movie_people(relation_type, top_n): 
    
        
    # 子查询: 对于每个电影人，选择他们参与的唯一电影 ID 和票房
    subquery = db.session.query(
        MovieActorRelation.movie_person_id,
        MovieActorRelation.movie_id,
        MovieInfo.box_office
    ).join(
        MovieInfo, MovieActorRelation.movie_id == MovieInfo.movie_id
    ).filter(
        MovieActorRelation.relation_type.in_(relation_type)
    ).distinct(MovieActorRelation.movie_person_id, MovieActorRelation.movie_id).subquery()

    # 主查询：根据电影人汇总票房
    return db.session.query(
        MoviePersonInfo.movie_person_name,
        MoviePersonInfo.country,
        db.func.sum(subquery.c.box_office).label('total_box_office')
    ).join(
        subquery, subquery.c.movie_person_id == MoviePersonInfo.movie_person_id
    ).group_by(
        MoviePersonInfo.movie_person_id,
        MoviePersonInfo.country
    ).order_by(
        db.desc('total_box_office')
    ).limit(top_n).all()
    
  

# # Example query to get all movies
# movies = MovieInfo.query.all()

# for movie in movies[0:5]:
#     print(movie.movie_name, movie.release_date)
# # Query for a specific actor by name
# actor = MoviePersonInfo.query.filter_by(movie_person_name='吴京').first()

# # Check if an actor is found and print details
# if actor:
#     print(f'Actor ID: {actor.movie_person_id}, Name: {actor.movie_person_name}, Country: {actor.country}')
# else:
#     print('Actor not found')



@app.route('/')
def index():
    top_movies = MovieInfo.query.order_by(cast(MovieInfo.movie_id, db.Integer)).limit(30).all()
    return render_template('index.html', top_movies=top_movies)

@app.route('/movie-search', methods=['GET', 'POST'])
def movie_search():
    top_movies = MovieInfo.query.order_by(cast(MovieInfo.movie_id, db.Integer)).limit(10).all()
    searched = False  # 添加一个标志来跟踪是否进行了搜索
    movie_results=None
    if request.method == 'POST':
        searched = True
        movie_name = request.form.get('movie_name')
        # 使用ILIKE进行不区分大小写的模糊匹配
        movie_results = MovieInfo.query.filter(MovieInfo.movie_name.ilike(f"%{movie_name}%")).all()
    return render_template('movie_search.html', movies=movie_results,top_movies=top_movies,searched=searched)


@app.route('/actor-search', methods=['GET', 'POST'])
def actor_search():
    searched = False
    actor_movies = {}
    top_people = get_top_movie_people(['主演','导演'], 10)
    if request.method == 'POST':
        searched = True
        actor_name = request.form.get('actor_name')
        movies = search_movies_by_actor(actor_name)
        for movie in movies:
            key = (movie.movie_person_name, movie.actor_country)  # 第一层 姓名 地区
            relation_type = movie.relation_type  # 第二层 关系
    
            if key not in actor_movies:
                actor_movies[key] = {}
            
            if relation_type not in actor_movies[key]:
                actor_movies[key][relation_type] = {'count': 0, 'movies': []}

            # 增加电影数量计数
            actor_movies[key][relation_type]['count'] += 1
            actor_movies[key][relation_type]['movies'].append(movie)
            
    return render_template('actor_search.html', actor_movies=actor_movies,searched=searched,top_people=top_people)


@app.route('/box-office-analysis')
def box_office_analysis():
    # 演员/导演票房总和查询       
    top_actors = get_top_movie_people(['主演'], 10)
    top_directors = get_top_movie_people(['导演'], 10)

    # 渲染网页并传递分析结果
    return render_template('box_office_analysis.html', top_actors=top_actors, top_directors=top_directors)

@app.route('/box-office-prediction')
def box_office_prediction():
    # 在这里添加票房预测的逻辑
    return '票房预测页面（待实现）'

# if __name__ == '__main__':
#     app.run(debug=True)
    
    