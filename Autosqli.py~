import urllib2
import json
import time
import threading
import re
import requests
from flask import Flask
from flask import render_template,request

app=Flask(__name__)

class AutoSqli(object):
    def __init__(self,serverURL,serverPort):
        self.serverURL=serverURL
        self.serverPort=serverPort
        self.taskid_url_Dict={}
        self.taskid_log_Dict={}
        self.taskid_status_Dict={}
        self.taskid_threads_Dict={}
        self.taskid_data_Dict={}
        self.taskid_options_Dict={}
    def NewTask(self):
        url=self.serverURL+":"+self.serverPort+"/task/new"
        responseData=json.loads(requests.get(url,None).text)
        if(responseData['success']==True):
            taskid=responseData['taskid']
            self.taskid_log_Dict[taskid]=time.strftime("[*%H:%M:%S]")+\
                "Built a new task successfully,taskid is %s;<br>"\
                % (taskid)
            self.taskid_url_Dict[taskid]="empty"
            self.taskid_status_Dict[taskid]="waiting targetUrl"
            return taskid
        else:
            return False
    def StartScan(self,taskid):
        url=self.serverURL+":"+self.serverPort+"/scan/"+taskid+"/start"
        responseData=json.loads(\
            requests.post(url,None,{'Content-Type': 'application/json'}).text)
        if(responseData['success']==True):
            self.taskid_log_Dict[taskid]=self.taskid_log_Dict[taskid]+\
                time.strftime("[*%H:%M:%S]")+\
                "Started a new scan sucessfully!The engineid is %s;<br>"\
                % (responseData['engineid'])
            self.taskid_status_Dict[taskid]="scanning"
            self.taskid_threads_Dict[taskid]=threading.Thread(target=self.Thread_Handle,\
                                                              args=(taskid,))
            self.taskid_threads_Dict[taskid].start()
            return True
        else:
            self.DeleteTask(taskid)
            del self.taskid_url_Dict[taskid]
            del self.taskid_log_Dict[taskid]
            del self.taskid_status_Dict[taskid]
            return False      
    def Thread_Handle(self,taskid):#must use statusr
        url_status=self.serverURL+":"+self.serverPort+"/scan/"+taskid+"/status"
        url_log=self.serverURL+":"+self.serverPort+"/scan/"+taskid+"/log"
        url_data=self.serverURL+":"+self.serverPort+"/scan/"+taskid+"/data"
        
        response_status_data=json.loads(requests.get(url_status,None).text)
        self.taskid_status_Dict[taskid]=response_status_data['status']  
        while response_status_data['status']!="terminated":
            if self.taskid_status_Dict[taskid]=="deleted":
                return False
            time.sleep(2)
            response_status_data=json.loads(requests.get(url_status,None).text)
            self.taskid_status_Dict[taskid]=response_status_data['status']               
        response_log_data=json.loads(requests.get(url_log,None).text) 
        loglist=response_log_data["log"]
        for log in loglist:
            self.taskid_log_Dict[taskid]=self.taskid_log_Dict[taskid]+\
                "[*"+log["time"]+"]"+log["message"]+";<br>"            
            response_log_data=json.loads(requests.get(url_log,None).text) 
            loglist=response_log_data["log"]
            for log in loglist:
                self.taskid_log_Dict[taskid]=self.taskid_log_Dict[taskid]+\
                    "[*"+log["time"]+"]"+log["message"]+";<br>"            
        self.taskid_status_Dict['status']="terminated"
        #convert scan data to a html table element,too many ugly code......
        response_data=json.loads(requests.get(url_data,None).text)
        response_data=response_data['data']
        data_html=""
        for data_item in response_data:
            if type(data_item['value'])==list:
                data_html=data_html+self.list_2_html(data_item['value'])
            elif type(data_item['value'])==dict:
                data_html=data_html+self.dict_2_html(data_item['value'])
            else:
                data_html=data_html+self.str_2_html(data_item['value'])
        data_html=re.sub("u'","",data_html)
        self.taskid_data_Dict[taskid]=data_html
    def list_2_html(self,data_list):
        data_html='<table border="1">'
        for i in range(0,len(data_list)):
            if type(data_list[i])==dict:
                for item in data_list[i]:
                    data_html=data_html+'<tr><td class="item">'+str(item)+'</td><td>'+str(data_list[i][item])+'</td></tr>'
            else: 
                data_html=data_html+'<tr><td class="item">'+str(i)+'</td><td>'+data_list[i]+'</td></tr>'  
        data_html=data_html+"</table>"
        return data_html
    def dict_2_html(self,data_dict):
        data_html='<table  border="1">'
        for key in data_dict:
            data_html=data_html+'<tr><td class="item">'+str(key)+'</td><td>'+str(data_dict[key])+'</td></tr>'
        data_html=data_html+"</table>"
        return data_html
    def str_2_html(self,data_unknown):
        data_html='<table  border="1"><tr><td class="item">'+str(data_unknown)+'</td></tr></table>'
        return data_html
    def SetOptions(self,taskid,options={}):
        for k in options:
            if options[k]=="False" or options[k]=="":
                del options[k]
        url=self.serverURL+":"+self.serverPort+"/option/"+taskid+"/set"
        requests.post(url,data=json.dumps(options),\
                      headers={'Content-Type':'application/json'})        
    
    def DeleteTask(self,taskid):
        url=self.serverURL+":"+self.serverPort+"/task/"+taskid+"/delete"         
        responseData=json.loads(requests.get(url,None).text)
        #there are two status when we wants to delete a task:running and terminated
        #and whatever the status is,we should kill the thread of the task
        #by the way,when a task is running,taskid_data_Dict does not have its taskid in keys()
        if(responseData['success']==True):
            #we should stop thread at first
            if self.taskid_threads_Dict[taskid].isAlive():
                #actually this method is not perfect and can't stop threads set value 100%
                self.taskid_status_Dict[taskid]="deleted"
            del self.taskid_threads_Dict[taskid]
            del self.taskid_log_Dict[taskid]
            if taskid in self.taskid_data_Dict.keys():
                del self.taskid_data_Dict[taskid]
            del self.taskid_status_Dict[taskid]
            del self.taskid_url_Dict[taskid]
            return "True"
        else:
            return "False"
    def SeeTaskList(self):
        task_list=""
        for taskid in self.taskid_url_Dict.keys():
            task_list=task_list+taskid+"-->"+self.taskid_url_Dict[taskid]+"<br>"
        return task_list
    def URL_Dupl(self,targetURL):
        m=re.match('(http://)|(https://)',targetURL)
        if m is None:
            targetURL="http://"+targetURL
        option_list=[]
        m=re.match('(.+)\?',targetURL)
        if m is None:
            return 0         # return 0 means illegal URL 
        else:
            option_list.append(m.groups()[0])
        temp_list=re.findall('(\&\w+=)',targetURL)
        for i in temp_list:
            if i!="":
                option_list.append(i)
        temp_list=re.findall('(\?\w+=)',targetURL)
        for i in temp_list:
            if i!="":
                option_list.append(i)        
        result=[]
        for key in self.taskid_url_Dict:
            url=self.taskid_url_Dict[key]
            status=True
            for reg in option_list:
                if '&' in reg or '?' in reg:
                    m=re.search('\\'+reg,url)
                else:
                    m=re.search(reg,url)
                if m is None:
                    status=False
                    break
            if status:
                result.append(url)
        if len(result):
            return -1      #return -1 means find url is similar to targeturl
        else:
            return 1       #return 1 means no url is similar to targeturl 
    
#Instantiates the AutoSqli class.    
autosqli=AutoSqli("http://127.0.0.1","8775")

@app.route('/',methods=['GET'])
def handle_root(): 
    return render_template("index.html")

@app.route('/index.html',methods=['GET'])
def handle_index(): 
    return render_template("index.html")

@app.route('/quickbuild.html',methods=['GET'])
def handle_quickbuild():
    return render_template("quickbuild.html")
@app.route('/quickbuild.html',methods=['POST'])
def handle_post_quickbuild():
    if 'url' in request.json:
        targetURL=request.json['url']
        m=re.match('(http://)|(https://)',targetURL) #add http:// for targetURL
        if m is None:
            targetURL="http://"+targetURL        
        repeated=autosqli.URL_Dupl(targetURL)     #check whether targetURL has been added
        if repeated != 1:
            return "False" 
        else:
            taskid=autosqli.NewTask()
            if taskid:
                autosqli.SetOptions(taskid,{"url": targetURL})
                log=autosqli.StartScan(taskid)
                autosqli.taskid_url_Dict[taskid]=targetURL
                return str(log)
            else:
                return "False"
    else:
        return "False"
    
@app.route('/customtask.html',methods=['GET'])
def handle_customtask():
    return render_template("customtask.html")

@app.route('/customtask.html',methods=['POST'])
def handle_post_customtask():
    if 'url' not in request.form.keys():
        return render_template("customtask.html",result="Error:Please input URL.")
    targetURL=request.form['url']
    m=re.match('(http://)|(https://)',targetURL) #add http:// for targetURL
    if m is None:
        targetURL="http://"+targetURL    
    if autosqli.URL_Dupl(targetURL)!=1:
        return render_template("customtask.html",result="Error:This url has been establised.")    
    taskid=autosqli.NewTask()
    options={}
    if taskid:
        for k in request.form:
            if request.form[k] and request.form[k] != "False" and request.form[k]!= "":
                options[k]=request.form[k]
        autosqli.SetOptions(taskid,options)
        log=autosqli.StartScan(taskid)
        autosqli.taskid_url_Dict[taskid]=targetURL
        if log:
            return render_template("tasklist.html")
    else:
        return render_template("customtask.html",result="Failed:can not establish task.")
@app.route('/tasklist.html',methods=['GET'])
def handle_tasklist():
    if "action" in request.args and request.args["action"]=="refresh":
        return_html=""
        for taskid in autosqli.taskid_url_Dict:
            return_html=return_html+'<div class="task_box">'+\
                '<p><span><strong>TargetURL:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                autosqli.taskid_url_Dict[taskid]+\
                '</span></p><p><span><strong>Status:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                autosqli.taskid_status_Dict[taskid]+'</span></p>'+\
                '<a class="button" href="/tasklog.html?taskid='+taskid+'">'+\
                '<strong>Log</strong></a>'+\
                '<a class="button" href="/taskdata.html?taskid='+taskid+'">'+\
                '<strong>Data</strong></a>'+\
                '<p class="button" onclick="del_task(\''+taskid+'\')">'+\
                '<strong>Delete</strong></p></div>'            
        return return_html
    elif "action" in request.args and request.args["action"]=="delete" \
         and "taskid" in request.args and request.args["taskid"]!="":
        return autosqli.DeleteTask(str(request.args["taskid"]))
    elif "action" in request.args and request.args["action"]=="seelog"\
         and "taskid" in request.args and request.args["taskid"]!="":
        taskid=str(request.args["taskid"])
        return autosqli.taskid_log_Dict[taskid];
    else:
        return_html=""
        for taskid in autosqli.taskid_url_Dict:
            return_html=return_html+'<div class="task_box">'+\
                '<p><span><strong>TargetURL:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                autosqli.taskid_url_Dict[taskid]+\
                '</span></p><p><span><strong>Status:&nbsp;&nbsp;&nbsp;&nbsp;</strong>'+\
                autosqli.taskid_status_Dict[taskid]+'</span></p>'+\
                '<a class="button" href="/tasklog.html?taskid='+taskid+'">'+\
                '<strong>Log</strong></a>'+\
                '<a class="button" href="/taskdata.html?taskid='+taskid+'">'+\
                '<strong>Data</strong></a>'+\
                '<p class="button" onclick="delete(\''+taskid+'\')">'+\
                '<strong>Delete</strong></p></div>'            
        return render_template("tasklist.html",html=return_html)

@app.route('/instructions.html',methods=['GET'])
def handle_instructions():
    return render_template("instructions.html")

@app.route('/tasklog.html',methods=['GET'])
def handle_tasklog():
    if "action" in request.args and request.args["action"]=="refresh"\
       and "taskid" in request.args\
       and request.args["taskid"] in autosqli.taskid_log_Dict.keys():
        taskid=str(request.args["taskid"])
        if autosqli.taskid_status_Dict[taskid]!="terminated":
            return autosqli.taskid_log_Dict[taskid]
        else:
            return "terminated"
    elif "taskid" in request.args and \
       request.args["taskid"] in autosqli.taskid_log_Dict.keys():
        taskid=str(request.args["taskid"])
        return render_template("tasklog.html",Log=autosqli.taskid_log_Dict[taskid],\
                               TaskID=taskid,TargetURL=autosqli.taskid_url_Dict[taskid])
    else:
        return '<script>window.location="/index.html"</script>'
    
@app.route('/taskdata.html',methods=['GET'])
def handle_taskdata():
    if "taskid" in request.args and \
       request.args["taskid"] in autosqli.taskid_data_Dict.keys():
        taskid=str(request.args["taskid"])
        return render_template("taskdata.html",Data=autosqli.taskid_data_Dict[taskid],\
                               TaskID=taskid,TargetURL=autosqli.taskid_url_Dict[taskid])
    else:
        return '<script>window.location="/index.html"</script>'

def returnlist():
    return autosqli.SeeTaskList()
    
if __name__=='__main__':
    app.run(host="0.0.0.0",port=80,debug=True)
