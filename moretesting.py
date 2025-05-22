import requests
from pydantic import BaseModel

class Model1(BaseModel):
    a:str
    b:int
    c:str

class Model2(BaseModel):
    d:str
    e:int
    f:str

response=requests.get("http://84.16.230.94:80010",json=Model1)
print(response.json())

response2=requests.get("http://84.16.230.94:80010",json=Model2)
print(response2.json())