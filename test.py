import urllib2
import json
import threading
import time
import re

def URL_Dedu(urldic,targetURL):
    #if not len(self.taskid_url_Dict):
        #return 1
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
    print option_list
    result=[]
    for key in urldic:
        url=urldic[key]
        status=True
        for reg in option_list:
            print reg
            print url
            if '&' in reg or '?' in reg:
                print "yes"
                m=re.search('\\'+reg,url)
            else:
                m=re.search(reg,url)
            if m is None:
                status=False
                break
        if status:
            result.append(url)
    print result
    if len(result):
        return -1      #return -1 means find url is similar to targeturl
    else:
        return 1
dict1={"1":"http://www.baidu.com?id=1"}
print URL_Dedu(dict1,"www.baidu.com?id=1")