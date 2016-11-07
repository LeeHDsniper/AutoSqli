#!/usr/bin/env python
#!-*- coding:utf-8 -*-

import json
import time
import threading
import re
import requests
import sys
import os
import sqlite3
import string
import random
import datetime
from urlparse import urlparse
from bs4 import BeautifulSoup
from flask import Flask,render_template,request,session

SERVER_List=["http://127.0.0.1:8775"]
HEADER={'Content-Type': 'application/json'} #post to sqlmapapi,we should declare http header
taskid_thread_Dict={}          #this dictionary will store all task's thread id,it will be use at Delete_Handle
app=Flask(__name__)
lock = threading.Lock()
#---------------------SQLITE initial start------------------------
app.config.update(dict(
    DATABASE=os.path.join(app.root_path+'/DATABASE', 'Autosqli.db'),
    DEBUG=True,
    SECRET_KEY='546sdafwerxcvSERds549fwe8rdxfsaf98we1r2',
    USERNAME='leehdautosqli',
    PASSWORD='lifeisshort'
))
app.config.from_envvar('AUTOSQLI_SETTINGS', silent=True)

#---------------------this secret key is for session
app.secret_key = "34$#4564dsfaWEERds/*-()^=sadfWE89SA"
#---------------------------------------------------
def connect_Db():#connect database
    rv=sqlite3.connect(app.config['DATABASE'])
    rv.row_factory=sqlite3.Row
    return rv
def get_Db():    #equals to connect_Db()
    sqlite_db=connect_Db()
    return sqlite_db
def init_Db():   #initial database ,this function will rebuild database--Autosqli.db
    with app.app_context():
        db=get_Db()
        with app.open_resource('DATABASE/schema.sql',mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
def query_db(query, args=(), one=False): #execute a sql select command parameter 'one' means return one record or all
    db=get_Db()
    cur = db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv
@app.teardown_appcontext
def close_Db(error):#close database
    db=get_Db()
    db.close()

#---------------------SQLITE initial end------------------------ 

#---------------------Random String ----------------------------
def get_RandomStr(length=1):
    source="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    if length>0:
        return string.join(random.sample(source,length), sep='')
    else:
        return '0'
#---------------------Random String end-------------------------

#---------------------Set SESSION for user----------------------
def set_Session():
    if 'username' not in session:
        session['username'] = datetime.datetime.now().strftime("%Y-%m-%d")
#---------------------Set SESSION end --------------------------

#-------------Functions to write data to database---------------
def write_Log(taskid,message={}):
    log = query_db('select log from Autosqli where taskid = ?',
                   [taskid], one=True)['log']
    log=eval(log)  #convert str to a list
    log.append(message)#append message at end of log list
    db=get_Db()#write log to database
    db.execute('update Autosqli set log = ? where taskid = ?',
                        [str(log),taskid])
    db.commit()
    return True
def write_Data(taskid,data=""):
    db=get_Db()
    db.execute('update Autosqli set data = ? where taskid = ?',
               [data,taskid])
    db.commit()
    return True
def write_Status(taskid,status=""):
    db=get_Db()
    db.execute('update Autosqli set status = ? where taskid = ?',
               [status,taskid])
    db.commit()
    return True
def write_Url(taskid,url=""):
    db=get_Db()
    db.execute('update Autosqli set url = ? where taskid = ?',
               [url,taskid])
    db.commit()
    return True
def write_UrlParameters(taskid,url_paramters_list=[]):
    db=get_Db()
    db.execute('update Autosqli set url_parameters = ? where taskid = ?',
               [str(url_paramters_list),taskid])
    db.commit()
    return True
#-------------Functions to write data to database end------------

#-------------Functions to get parameters in URL-----------------
def get_UrlParamters(URL):
    m=re.match('(http://)|(https://)',URL)
    if m is None:
        URL="http://"+URL
    option_list=[]
    m=re.match('(.+)\?',URL)
    if m is None:
        option_list.append(URL)
        return option_list
    temp_list=re.findall('\?(\w+)=',URL)
    for i in temp_list:
        if i!="":
            option_list.append(i)    
    temp_list=re.findall('\&(\w+)=',URL)
    for i in temp_list:
        if i!="":
            option_list.append(i)
    for i in range(len(option_list)):
        option_list[i]=option_list[i].encode('utf-8')
    return option_list   
#-------------Functions to get parameters in URL end-------------
def get_Server():
    tasklist = query_db('select * from Autosqli where status = ?',["running"])
    server_runningNum_dict={}
    for server in SERVER_List:
        server_runningNum_dict[server]=0
    if len(tasklist)!=0:
        for task in tasklist:
            server_runningNum_dict[task['server']]+=1
        return sorted(server_runningNum_dict.iteritems(),key=lambda t:t[1],reverse=False)[0][0]
    else:
        return SERVER_List[0]
def new_Taskid():
    '''get a new taskid'''
    server=get_Server()
    url=server+"/task/new"    
    responseData=json.loads(requests.get(url,None).text)
    if(responseData['success']==True):
        taskid=responseData['taskid']
        log=str([{time.strftime("[*%H:%M:%S]"):"Built a new task successfully"}])
        db=get_Db() #insert a new record into database
        db.execute('insert into Autosqli (taskid, log,user,server) values (?, ?, ? ,?)',
                     [taskid,log,session['username'],server])
        db.commit()
        write_Status(taskid, status="not running")
        return taskid
    else:
        return False 

def set_Options(taskid,options={}):
    if options is None:
        return False
    server=query_db('select server from Autosqli where taskid = ?',[taskid],one=True)['server']
    url=server+"/option/"+taskid+"/set"
    for k in options:
        if options[k]=="False" or options[k]=="":
            del options[k]
    if 'url' in options.keys():
        write_Url(taskid, url=options['url'])
        write_UrlParameters(taskid, url_paramters_list=get_UrlParamters(options['url']))
    data=json.dumps(options)
    responseData=json.loads(requests.post(url,data=data,headers=HEADER).text)
    if(responseData['success']==True):
        log={time.strftime("[*%H:%M:%S]"):"Set Options successfully"}
        write_Log(taskid,log)
        db=get_Db()
        db.execute('update Autosqli set options = ? where taskid = ?',
                            [data,taskid])
        db.commit()
        return True
    else:
        return False
            
def Thread_Handle(taskid):
    lock.acquire()
    server=query_db('select server from Autosqli where taskid = ?',[taskid],one=True)['server']
    url_status=server+"/scan/"+taskid+"/status"
    url_log=server+"/scan/"+taskid+"/log"
    url_data=server+"/scan/"+taskid+"/data"
    db=get_Db()
    response_status=json.loads(requests.get(url_status,None).text)['status']
    db.execute('update Autosqli set status = ? where taskid = ?',
               [response_status,taskid]) 
    db.commit() 
    while response_status!="terminated" and response_status!="deleting":
        time.sleep(2)
        response_status=json.loads(requests.get(url_status,None).text)['status']             
    response_loglist=json.loads(requests.get(url_log,None).text)['log']
    for log in response_loglist:
        write_Log(taskid, {"[*"+log['time']+"]":log['message']})
    write_Status(taskid, response_status)
    response_data=requests.get(url_data,None).text
    if response_data==None:
        return False
    write_Data(taskid, response_data)  
    lock.release()
    return True
    
def start_Scan(taskid):
    server=query_db('select server from Autosqli where taskid = ?',[taskid],one=True)['server']
    url=server+"/scan/"+taskid+"/start"
    responseData=json.loads(requests.post(url,None,{'Content-Type': 'application/json'}).text)
    if(responseData['success']==True):
        write_Log(taskid,{time.strftime("[*%H:%M:%S]"):"Started a new scan successfully"})
        write_Status(taskid, status="scaning")
        t=threading.Thread(target=Thread_Handle,args=(taskid,))
        taskid_thread_Dict[taskid]=t
        t.start()
        return True
    else:
        return False   
def stop_Scan(taskid):
    server=query_db('select server from Autosqli where taskid = ?',[taskid],one=True)['server']
    url=server+"/scan/"+taskid+"/stop"
    responseData=json.loads(requests.get(url,None).text)
    if(responseData['success']==True):
        write_log(taskid,{time.strftime("[*%H:%M:%S]"):"Task was stopped by user"})
        return True
    else:
        return False
def Delete_Handle(taskid):
    write_Status(taskid, status="deleting")
    server=query_db('select server from Autosqli where taskid = ?',[taskid],one=True)['server']
    url=server+"/task/"+taskid+"/delete"
    if(taskid in taskid_thread_Dict.keys()):
        while(taskid_thread_Dict[taskid].isAlive()):
            time.sleep(2)
    json.loads(requests.get(url,None).text)
    db=get_Db()
    db.execute('delete from Autosqli where taskid = ?',
               [taskid])
    db.commit()
    return True

def delete_Task(taskid):
    t=threading.Thread(target=Delete_Handle,args=(taskid,))
    t.start()
    return True

def save_successresult(options):
    rebeat = query_db("select url from SuccessTarget where user = ?", [session['username']])
    if len(rebeat) >0 :
        return None
    db=get_Db() #insert a new record into database
    db.execute('insert into SuccessTarget (url, data,user) values (?, ?, ?)',
                    [options['url'],options['data'],session['username']])
    db.commit()

def getsuccessresult():
    tasklist = query_db('select * from SuccessTarget where user = ?',[session['username']])
    if len(tasklist)>0:
        for task in tasklist:
            for key in task.keys():
                if task[key]=="" or task[key]==None:
                    task[key]="Empty"
    return tasklist

def get_TaskList():
    if session['username']=="":
        return False
    tasklist = query_db('select * from Autosqli where user = ?',[session['username']])
    if len(tasklist)>0:
        for task in tasklist:
            for key in task.keys():
                if task[key]=="" or task[key]==None:
                    task[key]="Empty"
    return tasklist
def get_TaskLog(taskid):
    loglist=query_db('select log from Autosqli where taskid = ?',[taskid],one=True)['log']
    loglist=eval(loglist)
    return_html='<p class="close_button" onclick="close_log()">CLOSE</p>'
    for log in loglist:
        time=log.keys()[0]
        return_html=return_html+"<p>"+time+log[time]+"</p>"
    return return_html
def get_TaskData(taskid):
    data=query_db('select data from Autosqli where taskid = ?',[taskid],one=True)['data']
    return data

def task_Dup(Options={}):
    options=Options.copy()
    tasklist=query_db('select url_parameters,options from Autosqli where user = ?',[session['username']])
    if len(tasklist)==0:
        return 1
    urlparamters=get_UrlParamters(options['url'])
    del options['url']
    for task in tasklist:
        templist_UrlParam=eval(task['url_parameters'])
        tempdic_Options=json.loads(task['options'])
        if 'url' in tempdic_Options.keys():
            del tempdic_Options['url']
        if sorted(urlparamters)==sorted(templist_UrlParam) and options==tempdic_Options:
            return -1
    return 1

#------------------new Feature-------------------------------
def gethref(url):
    def sp(urls):
        print urls
        alist = set()
        headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:47.0) Gecko/20100101 Firefox/47.0"}
        req = requests.get(url, headers=headers)
        domain = "{0}://{1}".format(urlparse(url).scheme, urlparse(url).netloc)
        soup = BeautifulSoup(req.text, "lxml")
        # import ipdb;ipdb.set_trace()
        if len(soup.find_all('a')) == 0:
            alist.add(urls)
            return 
        for a in soup.find_all('a'):
            if a.has_attr('href') == False:
                continue
            if a['href'].startswith(domain):
                alist.add(a['href'])
            elif a['href'].startswith('http') == False:
                us = "{0}/{1}/{2}".format(domain, urlparse(url).path, a['href'])
                alist.add(us)
        return alist
    tmp1 = tmp2 = sp(url)
    if(tmp2!=None):
        for u in tmp2:
            tmp1 = tmp1 | sp(u)
        return tmp1
    else:
        return set([url])

def GetSuccessTarget():
    slist = {}
    flag = re.compile(r'payload":\s+"(.*?)"')
    tasklist = get_TaskList()
    for task in tasklist:
        try:
            data = flag.search(task['data']).groups()[0]
            slist['url'] = task['url']
            slist['data'] = data
            save_successresult(slist)
        except:
            pass
    return slist


#-------------------A test page----------------------------------   
#@app.route('/sqlshow.html')
#def show_entries():
    #db=get_Db()
    #cur = db.execute("select * from Autosqli")
    #entry=cur.fetchall()
    #tasklist=query_db('select user from Autosqli where taskid = ?',['7abc8e899783367a'],one=True)
    #return render_template('sqlshow.html', entries=entry,data=str(request.remote_addr))
#-------------------A test page end------------------------------ 
@app.route('/',methods=['GET'])
def handle_root():
    set_Session()    
    return render_template("index.html")

@app.route('/index.html',methods=['GET'])
def handle_index(): 
    set_Session()   
    return render_template("index.html")

@app.route('/quickbuild.html',methods=['GET'])
def handle_quickbuild():
    set_Session()
    return render_template("quickbuild.html")
@app.route('/quickbuild.html',methods=['POST'])
def handle_post_quickbuild():
    options={}
    if 'url' in request.json and request.json['url']!="":
        options['url']=request.json['url']
        m=re.match('(http://)|(https://)',options['url']) #add http:// for targetURL
        if m is None:
            options['url']="http://"+options['url']        
        if task_Dup(options)!= 1:
            return "False" 
        else:
            taskid=new_Taskid()
            if taskid:
                result=set_Options(taskid,options)
                return str(result)
            else:
                return "False"
    else:
        return "False"
    
@app.route('/customtask.html',methods=['GET'])
def handle_customtask():
    set_Session()
    return render_template("customtask.html")

@app.route('/customtask.html',methods=['POST'])
def handle_post_customtask():
    options={}
    for k in request.form:
        if request.form[k] and request.form[k] != "False" and request.form[k]!= "":
            options[k]=request.form[k]    
    if 'url' not in options.keys():
        return render_template("customtask.html",result="Error:Please input URL.")
    m=re.match('(http://)|(https://)',options['url']) #add http:// for targetURL
    if m is None:
        options['url']="http://"+options['url']
    
    urls = gethref(options['url'])
    for u in urls:
        options['url']=u
        if task_Dup(options)==1:#这里去重从逻辑上来更合理，但是没多大意义
            taskid=new_Taskid()
            if taskid:
                result = set_Options(taskid,options)
            else:
                return render_template("customtask.html",result="Error:Can not establish task.")
    return render_template("tasklist.html")
@app.route('/spider',methods=['POST'])
def hander_spider():
    if 'url' in request.json and request.json['url']!="":
        url=request.json['url']
        m=re.match('(http://)|(https://)',url) #add http:// for targetURL
        if m is None:
            url="http://"+url
        try:
            result=gethref(url)
        except Exception, e:
            return "False"
        if(len(result)!=0):
            li_list=""
            for u in result:
                li_list=li_list+"<li>"+u+"</li>"
            return li_list
        else:
            return "False"
    else:
        return "False"
@app.route('/tasklist.html',methods=['GET'])
def handle_tasklist():
    set_Session()
    GetSuccessTarget()
    if "action" in request.args and request.args["action"]=="refresh":
        tasklist=get_TaskList()
        return_html="<div class=\"task_box\"><p>Now has {0} tasks to running</p></div>".format(len(tasklist))
        if tasklist==False or len(tasklist)==0:
            return_html='<div class="task_box"><p>No task for you</p></div>'
            return return_html
        for task in tasklist:
            return_html=return_html+'<div class="task_box">'+\
                '<p><span><strong>TaskID:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                task['taskid']+\
                '</span></p><p><span><strong>Status:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                task['status']+'</span></p>'+\
                '</span></p><p><span><strong>TargetURL:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                task['url']+'</span></p>'+\
                '</span></p><p><span><strong>URL Paramters:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                task['url_parameters']+'</span></p>'+\
                '</span></p><p><span><strong>Options:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                task['options']+'</span></p>'+\
                '</span></p><p><span><strong>Server:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                task['server']+'</span></p>'+\
                '<p class="button" onclick="see_log(\''+task['taskid']+'\')">'+\
                '<strong>Log</strong></p>'+\
                '<a class="button" href="/taskdata.html?taskid='+task['taskid']+'">'+\
                '<strong>Data</strong></a>'+\
                '<p class="button" onclick="start_task(\''+task['taskid']+'\')">'+\
                '<strong>Start</strong></p>'+\
                '<p class="button" onclick="stop_task(\''+task['taskid']+'\')">'+\
                '<strong>Stop</strong></p>'+\
                '<p class="button" onclick="del_task(\''+task['taskid']+'\')">'+\
                '<strong>Delete</strong></p></div>'            
        return return_html
    elif "action" in request.args and request.args["action"]=="delete" \
         and "taskid" in request.args and request.args["taskid"]!="":
        return str(delete_Task(str(request.args["taskid"])))
    elif "action" in request.args and request.args["action"]=="seelog"\
         and "taskid" in request.args and request.args["taskid"]!="":
        taskid=str(request.args["taskid"])
        return get_TaskLog(taskid)
    elif "action" in request.args and request.args["action"]=="start"\
         and "taskid" in request.args and request.args["taskid"]!="":
         taskid=str(request.args['taskid'])
         result=start_Scan(taskid)
         return str(result)
    elif "action" in request.args and request.args["action"]=="stop"\
         and "taskid" in request.args and request.args["taskid"]!="":
         taskid=str(request.args['taskid'])
         result=stop_Scan(taskid)
         return str(result)
    else:
        tasklist=get_TaskList()
        return_html="<div class=\"task_box\"><p>Now has {0} tasks to running</p></div>".format(len(tasklist))
        if tasklist==False or len(tasklist)==0:
            return_html='<div class="task_box"><p>No task for you</p></div>'
        else:
            for task in tasklist:
                return_html=return_html+'<div class="task_box">'+\
                    '<p><span><strong>TaskID:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                    task['taskid']+\
                    '</span></p><p><span><strong>Status:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                    task['status']+'</span></p>'+\
                    '</span></p><p><span><strong>TargetURL:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                    task['url']+'</span></p>'+\
                    '</span></p><p><span><strong>URL Paramters:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                    task['url_parameters']+'</span></p>'+\
                    '</span></p><p><span><strong>Options:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                    task['options']+'</span></p>'+\
                    '</span></p><p><span><strong>Server:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                    task['server']+'</span></p>'+\
                    '<p class="button" onclick="see_log(\''+task['taskid']+'\')">'+\
                    '<strong>Log</strong></p>'+\
                    '<a class="button" href="/taskdata.html?taskid='+task['taskid']+'">'+\
                    '<strong>Data</strong></a>'+\
                    '<p class="button" onclick="start_task(\''+task['taskid']+'\')">'+\
                    '<strong>Start</strong></p>'+\
                    '<p class="button" onclick="stop_task(\''+task['taskid']+'\')">'+\
                    '<strong>Stop</strong></p>'+\
                    '<p class="button" onclick="del_task(\''+task['taskid']+'\')">'+\
                    '<strong>Delete</strong></p></div>'  
        return render_template("tasklist.html",html=return_html)

@app.route('/success.html',methods=['GET'])
def handle_instructions():
    set_Session()
    slist = getsuccessresult()  
    return_html='<div class="task_box"><p>Now has <font color="red">{0}</font> url success crack</p></div>'.format(len(slist))
    for url in slist:
        return_html=return_html+'<div class="task_box">'+\
                    '<p><span><font color="red"><strong>URL:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                    url['url']+\
                    '</span></font></p><p><span><font color="red"><strong>payload:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                    url['data']+'</font></span></p></div>'
    return render_template("success.html", html=return_html)
    
@app.route('/taskdata.html',methods=['GET'])
def handle_taskdata():
    set_Session()
    if "taskid" in request.args :
        taskid=str(request.args["taskid"])
        return render_template("taskdata.html",data=get_TaskData(taskid))
    else:
        return '<script>window.location="/index.html"</script>'
init_Db()
if __name__=='__main__':
    app.run(host="0.0.0.0",port=int(sys.argv[1]),debug=True)
