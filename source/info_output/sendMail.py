# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import smtplib
from email.mime.text import MIMEText
from email.header import Header

import json
import datetime

import config

__metaclass__ = type


class MySendMail():
    def sendRes_ByMail(self, plain_msg):
        
        temp_email_info = json.loads(config.decryptInfo(config.email_info, config.cryptoKey))
        
        # 第三方 SMTP 服务
        mail_host=temp_email_info['mail_host']  #设置服务器
        mail_port=temp_email_info['mail_port']  #设置服务器
        mail_user=temp_email_info['mail_user']  #用户名
        mail_pass=temp_email_info['mail_pass']  #口令
        sender = temp_email_info['sender']
        receivers = temp_email_info['receivers'].split(',')  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
    
    
        message = MIMEText(plain_msg, 'plain', 'utf-8')
        message['From'] = Header(sender, 'utf-8')
        message['To'] =  Header(';'.join(receivers), 'utf-8')
    
        subject = 'Tipster Result('+str(datetime.datetime.now())+')'
        message['Subject'] = Header(subject, 'utf-8')
    
    
        try:
            smtpObj = smtplib.SMTP_SSL() 
            smtpObj.connect(mail_host, mail_port)    # 25 为 SMTP 端口号
            smtpObj.login(mail_user,mail_pass)  
            smtpObj.sendmail(sender, receivers, message.as_string())
            print("邮件发送成功")
        except Exception as err:
            print (err)
            print("Error: 无法发送邮件")
    
        
