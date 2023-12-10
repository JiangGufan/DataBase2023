# -*- coding: utf-8 -*-
"""
Created on Sun Dec  3 18:01:04 2023

@author: Panda Jiang
"""
import os
import sys

from flask import Flask, render_template, request, abort
import pymysql
import mysql.connector

from collections import defaultdict
from sqlalchemy import func, and_
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import Column, String, Integer, ForeignKey, Date, CheckConstraint, create_engine
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql.expression import cast
from sqlalchemy.orm import relationship, aliased, sessionmaker
from functools import wraps

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
import pandas as pd
import numpy as np

# 题目：电影管理系统
# 功能：电影的录入、查询、演员的查询、票房分析、票房预测。

app = Flask(__name__)

# 确保数据库 URI 使用正确的格式和驱动
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/movie100'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化 db 对象，无需调用 init_app，因为您已经在创建时传递了 app
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50))  # 如 'admin', 'editor', 'viewer'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    
class LabelTable(db.Model):
    __tablename__ = 'label_table'
    label_id = db.Column(db.Integer, primary_key=True)
    label_name = db.Column(db.String(100), nullable=False)

    # Relationship to the MovieLabelRelation table
    movie_labels = db.relationship('MovieLabelRelation', back_populates='label')

class MovieLabelRelation(db.Model):
    __tablename__ = 'movie_label_relation'
    movie_id = db.Column(db.String(10), db.ForeignKey('movie_info.movie_id'), primary_key=True)
    label_id = db.Column(db.Integer, db.ForeignKey('label_table.label_id'), primary_key=True)

    # Relationships to the other tables
    movie = db.relationship('MovieInfo', backref=db.backref('label_relations', lazy=True))
    label = db.relationship('LabelTable', back_populates='movie_labels')

# label = LabelTable.query.filter_by(label_id=1).first()
# if label:
#     movies_with_label = [relation.movie.movie_name for relation in label.movie_labels]
#     print(f"Label: {label.label_name}, Movies: {', '.join(movies_with_label)}")
# else:
#     print( "Label not found")


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

# 计算给定标签的平均票房
def movie_and_avg_boxoffice_for_label(label_name):
    # 查询包含特定标签的所有电影的完整信息
    movies = db.session.query(MovieInfo).\
        join(MovieLabelRelation, MovieLabelRelation.movie_id == MovieInfo.movie_id).\
        join(LabelTable, LabelTable.label_id == MovieLabelRelation.label_id).\
        filter(LabelTable.label_name == label_name).all()
    # 如果没有找到任何电影，返回空列表和None
    if not movies:
        return [], None
    # 计算这些电影的平均票房
    avg_box_office = sum(movie.box_office for movie in movies if movie.box_office is not None) / len(movies)

    return movies, avg_box_office

# movies, box = movie_and_avg_boxoffice_for_label('喜剧')

# print(movies,'\n',box,'（亿元）')


def train_linear_regression_model(movies, labels, label_relations):
    # 创建一个字典，将每部电影映射到其标签
    movie_labels_map = defaultdict(set)
    for relation in label_relations:
        movie_labels_map[relation.movie_id].add(relation.label.label_name)
    # 转换为 DataFrame
    data = []
    for movie in movies:
        if movie.box_office:  # 确保只考虑有票房数据的电影
            row = {
                'movie_id': movie.movie_id, 
                'box_office': movie.box_office, 
                'year': movie.year, 
                'douban_rating': movie.douban_rating
            }
            for label in labels:
                row[label.label_name] = 1 if label.label_name in movie_labels_map[movie.movie_id] else 0
            data.append(row)
    df = pd.DataFrame(data)
    # 分离特征和目标变量
    X = df.drop(columns=['movie_id', 'box_office'])
    y = df['box_office']
    # 分割数据集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=2023)
    # 训练线性回归模型
    model = LinearRegression()
    model.fit(X_train, y_train)
    # # 模型评估（可选）
    # print("Model Score:", model.score(X_test, y_test))
    # 获取系数
    coefficients = model.coef_
    intercept = model.intercept_
    # 将系数与对应的特征名组合
    feature_coefficients = dict(zip(X.columns, coefficients))

    return model, feature_coefficients, intercept

movies = MovieInfo.query.all()
labels = LabelTable.query.all()
label_relations = MovieLabelRelation.query.all()
 
model, feature_coefficients, const = train_linear_regression_model(movies, labels, label_relations)
feature_names = list(feature_coefficients.keys())
# 注意feature_names需要包含year和douban_rating
# print(feature_names)

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

@app.route('/box-office-prediction', methods=['GET', 'POST'])
def box_office_prediction():
    prediction = None
    message = None
    labels = LabelTable.query.all()
    year = None
    douban_rating = None
    selected_labels = []
    if request.method == 'POST':
        # 获取用户输入
        year = request.form.get('year')
        douban_rating = request.form.get('douban_rating')
        selected_labels = request.form.getlist('labels')
        
        # 验证输入
        try:
            year = int(year) if year else None
            douban_rating = float(douban_rating) if douban_rating else None

            if year is None or douban_rating is None:
                message = "您没有输入年份或评分。"
            elif not (1990 <= year <= 2023):
                message = "年份必须在1990到2023之间。"
            elif not (0 <= douban_rating <= 10):
                message = "评分必须在0到10之间。"
            else:
                features_dict = {label: 1 if label in selected_labels else 0 for label in feature_names}
                features_dict['year'] = year
                features_dict['douban_rating'] = douban_rating
        
                # 转换为 DataFrame
                features_df = pd.DataFrame([features_dict])
        
                # 确保所有特征都存在，即使用户没有选择任何标签
                for feature in feature_names:
                    if feature not in features_df:
                        features_df[feature] = 0
                # 进行预测
                prediction = model.predict(features_df)
                prediction = prediction[0]
                

        except ValueError:
            message = "无效的输入，请输入有效的年份和评分。"
            
        # print("Message:", message) 


    return render_template('box_office_prediction.html', labels=labels, prediction=prediction, message=message, year=year,rating=douban_rating ,selected_labels=selected_labels)
    # # 在这里添加票房预测的逻辑
    # return  render_template('base.html')

# if __name__ == '__main__':
#     app.run(debug=True)
  

# # 用户部分的电影编辑权限，待完成
# login_manager = LoginManager()
# login_manager.init_app(app)

# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))
