# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import traceback
import datetime
import os
import copy
import re

import pymysql.cursors
from database.DB_Base import MyDB_Base

__metaclass__ = type

#class database
class MyDB_MySQL(MyDB_Base):
    #重载的函数
    
    def __init__(self):
        MyDB_Base.__init__()
        
        
    def DB_MySql_Connect(self, db_entry):
        config = {'host':db_entry['server_ip'],\
                  'port':db_entry['port'],\
                  'user':db_entry['user'],\
                  'password':db_entry['password'],\
                  'db':db_entry['db_name'],\
                  'charset':'utf8mb4',\
                  'cursorclass':pymysql.cursors.DictCursor}
        
        # Connect to the database
        self.db_conn = pymysql.connect(**config)
        self.db_curs = self.db_conn.cursor()

        return


    def DB_MySql_CreateDB(self, db_entry):
        config = {'host':db_entry['server_ip'],\
                  'port':db_entry['port'],\
                  'user':db_entry['user'],\
                  'password':db_entry['password'],\
                  'charset':'utf8mb4',\
                  'cursorclass':pymysql.cursors.DictCursor}
        # Connect to the database
        conn = pymysql.connect(**config)        
        curs = conn.cursor()
        
        # create a database
        try:
            curs.execute('create database '+db_entry['db_name'])
        except:
            print('Database '+db_entry['db_name']+' exists!')
            
        conn.select_db(db_entry['db_name'])   
                
        conn.commit()
        curs.close()
        conn.close()
        return
        
    def DB_MySql_DropDB(self, db_entry):
        config = {'host':db_entry['server_ip'],\
                  'port':db_entry['port'],\
                  'user':db_entry['user'],\
                  'password':db_entry['password'],\
                  'charset':'utf8mb4',\
                  'cursorclass':pymysql.cursors.DictCursor}
        # Connect to the database
        conn = pymysql.connect(**config)        
        curs = conn.cursor()
        
        # drop the database
        try:
            curs.execute('drop database if exists '+db_entry['db_name'])
        except:
            print('Drop Database '+db_entry['db_name']+' Fail!')
            
        conn.commit()
        curs.close()
        conn.close()         
        return
    
    def DB_MySql_Create_SqlCmd_INSERT(self, tb_name, titleNameList, data):
        insert='INSERT INTO '+self.__DbEx_TransSockNo2SockName__(tb_name)+' SET '
        for title_value in zip(titleNameList, data):
            para1=title_value[1]
            if type(para1)==str:
                para1='"'+para1+'"'
            insert+=title_value[0]+'='+str(para1)+','
        insert=insert.rstrip(',')
        
        return insert
        
     
