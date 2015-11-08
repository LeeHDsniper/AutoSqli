import urllib2
import json
import threading
import time

class AutoSqli(object):
    def __init__(self,serverURL,serverPort):
        self.serverURL=serverURL
        self.serverPort=serverPort
        self.taskidDict={}
    def NewTask(self,targetURL):
        request=urllib2.Request(self.serverURL+":"+self.serverPort+
                                "/task/new")
        response=urllib2.urlopen(request)
        responseData=json.loads(response.read())
        if(responseData['success']==True):
            taskid=responseData['taskid']
            print "Built a new task successfully,taskid is %s.Try to start scan of targetURL:%s" % (taskid,targetURL)
            self.taskidDict[taskid]="empty"
            url=self.serverURL+":"+self.serverPort+"/scan/"+taskid+"/start"
            request=urllib2.Request(url,'{"url":"'+targetURL+'"}')
            request.add_header("Content-Type","application/json")
            response=urllib2.urlopen(request)
            responseData=json.loads(response.read())
            if(responseData['success']==True):
                self.taskidDict[taskid]=targetURL
                print "Started a new scan of %s sucessfully!The engineid is %s" % (targetURL,responseData['engineid'])
            else:
                print("Failed to start a new scan of %s." % targetURL)
            return taskid
        else:
            print("Failed to build a new task")
    def deletetask(self,taskid):
        request=urllib2.Request(self.serverURL+":"+self.serverPort+
                                "/task/"+taskid+"/delete")
        response=urllib2.urlopen(request)
        print response.read()
    def showlist(self):
        request=urllib2.Request(self.serverURL+":"+self.serverPort+
                                "/option/31c1c8bcf87f892d/list")#+taskid+"/delete")
        response=urllib2.urlopen(request)
        data=response.read()
        print data
        #data=json.loads(data)
        #data=data['data']
        #data=data[0]
        #data=data["value"][0]
        #temp="ssss="+\
            #data["dbms_version"][0]
        #print temp
myautosqli=AutoSqli("http://127.0.0.1","8775")
myautosqli.showlist()
