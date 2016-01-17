import json
import requests
responseData=json.loads(requests.get("http://223.129.28.59:8775/download/de5206c019a75259",None).text)
print responseData