from resume import Resume
import json
import http.client 

re = Resume('1.html')
json_str = re.to_json()
data2 = json.loads(json_str)
pass


 
requrl = "http://127.0.0.1/api/upload_cv"
headerdata = {"Content-type": "application/json"}
 
conn = http.client.HTTPConnection("127.0.0.1",8000)
 
conn.request('POST', requrl, json_str ,headerdata) 
 
response = conn.getresponse()
 
res= response.read()
