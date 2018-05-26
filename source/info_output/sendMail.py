# -*- coding: utf-8 -*-

#Python 3.5.x

#V0.01

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.application import MIMEApplication

import json
import datetime
import time

import config

__metaclass__ = type


class MySendMail():
    def sendRes_ByMail(self, plain_msg, attachFiles):
        
        temp_email_info = json.loads(config.decryptInfo(config.email_info, config.cryptoKey))
        
        # 第三方 SMTP 服务
        mail_host=temp_email_info['mail_host']  #设置服务器
        mail_port=temp_email_info['mail_port']  #设置服务器
        mail_user=temp_email_info['mail_user']  #用户名
        mail_pass=temp_email_info['mail_pass']  #口令
        sender = temp_email_info['sender']
        receivers = temp_email_info['receivers'].split(',')  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
    
        for receiver in receivers:
            message = MIMEMultipart()
            message['From'] = Header(sender, 'utf-8')
            message['To'] =  Header(';'.join([receiver]), 'utf-8')
            subject = 'Tipster Result('+str(datetime.datetime.now())+')'
            message['Subject'] = Header(subject, 'utf-8')
            
            #正文的纯文本部分
            puretext = MIMEText(plain_msg, 'plain', 'utf-8')
            message.attach(puretext)
            
            #增加文件附件
            for attachFile in attachFiles:
                filepart=MIMEApplication(open(attachFile, 'rb').read())
                filepart.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachFile))
                message.attach(filepart)
        
        
            try:
                smtpObj = smtplib.SMTP_SSL() 
                smtpObj.connect(mail_host, mail_port)    # 25 为 SMTP 端口号
                smtpObj.login(mail_user,mail_pass)  
                smtpObj.sendmail(sender, [receiver], message.as_string())
                print("邮件发送成功<to %s>" % receiver)
            except Exception as err:
                print (err)
                print("Error: 无法发送邮件<to %s>" % receiver)
                
            time.sleep(30)
    
        
