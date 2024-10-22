#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import logging
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
import os
import re

header={'content-type': 'application/json',
           'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0' }
logging.captureWarnings(True)


# In[25]:




## get lot and lot name
def getLot(northing, easting):

    try:
        url = f'https://geodata.gov.hk/gs/api/v1.0.0/identify?x={easting}&y={northing}&lang=en'
        #print(url)
        response = requests.get( url , headers = header , verify = False, timeout = 10)
        jsondata = response.json()
        
        
        count = len(jsondata['results'])-1
        if count == -1: 
            lot="NAN"
            lotname = "NAN"
        while count>=0:
            try:
                lot = jsondata['results'][count]["addressInfo"][0]["LOT_FULLNAME"]
                lotname = jsondata['results'][count]["addressInfo"][0]["LOTNAME"] 
                #print(lotname)
                break
            except:
                count-=1
                if(count == -1):
                    lot="NAN"
                    lotname = "NAN"
    except:
        lot = "NAN"
        lotname = "NAN"
    
    return lot,lotname


# In[ ]:


# clean the string of building Userage
def str_clean(str1):
    str1 = str1.replace('<br/>',' ')
    str1 = str1.replace('/',' ')
    if str1.find('(') !=-1:
        str1 = str1[:str1.find('(')]+str1[str1.find(')')+1:]
    return str1.rstrip().lower()


# In[ ]:


# generate the building code
def bcode(str1):    
    
    word_list=['school','chorch','factory','petrol','data',
               'house','temple','hotel','office','industrial',
               'transitional','logistics','hostel',
               'apartment','commercial','residen'
              ]
    for i in word_list:
        if i in str1:
            return str(word_list.index(i)+1).zfill(2)
    return 0


# In[ ]:


# big jsonfile
def getjson(url):
    response = requests.get(url , headers = header, verify = False)
    try:
        jsondata = response.json()
        return jsondata
    except:
        if "scalar" in response.text:
            print("Blocked by Network Safety.")


# In[ ]:


# json to table
def table_json(url):
    print(url)
    row_table = getjson(url)

    print(row_table)

    row_table = row_table['features']



    return row_table


# In[1]:


# genereate final excel table
def generate(row_table,last_update):
    db=[]
    current = 0
    for i in row_table:
        
        store={}
        
        store = i['properties']
        store ['Last Update']=datetime.strptime(store ['Last Update'], '%Y-%m-%d %H:%M:%S').date()
        if(store['Last Update'] <= last_update):
            continue

        current+=1
        store['Building Type']=str_clean(store['Building Type']) 
        store['Applicant']=str_clean(store['Applicant'])
        store['buildingcode']=bcode(store['Building Type'])
        store['Xcoords'] = i['geometry']['coordinates'][0]
        store['Ycoords'] = i['geometry']['coordinates'][1]
        if current % 100 ==0:
            print(current)
        
        if store['buildingcode'] == 0 :
            continue
        north = int(store["Northing"])
        east =int(store["Easting"])
        store['Lot'],store['lotname']=getLot(north,east)
        
        db.append(store)

    return db


# In[ ]:


#regetlot 
def regetlot(xlsx_name):
    table = pd.read_excel(xlsx_name,index_col=0)
    suffix_number = xlsx_name.split("_")[1]
    suffix_number = suffix_number.split(".")[0]
    suffix_number = int(suffix_number) % 10

    print(f"suffix = {suffix_number}")


    left =-1
    while True:
        current = 0
        cleaned = 0
        for i in range(len(table)):
            if(table.iloc[i]['Lot'+suffix_number] == 'NAN'):
                lot,lotname= getLot(table.iloc[i]['Northing'],table.iloc[i]['Easting']) 
                table.loc[i,"Lot"]=lot
                table.loc[i,"lotname"]=lotname
                current+=1
                if lot!= 'NAN':
                    cleaned +=1
        if current-cleaned == left :
            break
        else:
            left = current -cleaned
            print(left)


    name = xlsx_name[xlsx_name.rfind("\\")+1:]
    print(f"{name} have {left} NAN lots.")
    table.to_excel(xlsx_name)


# In[ ]:


def re_region(a):
    a = a.lower()
    a = a.replace(", hong kong","")
    a = a.replace(", kowloon","")
    a = a.replace(", new territories","")    
    a = a.replace(" hong kong","")
    a = a.replace(" kowloon","")
    a = a.replace(" new territories","")
    return a


# In[ ]:


def tpu(table_name):

    table = pd.read_excel(table_name,index_col = 0)
    for i in table.index:
        tpu="-1"
        n = re.search('[\d].[\d].[\d/].?\(\d.?\)',table.loc[i,'Address'])
        if n != None:
            tpu = n.group()
        table.loc[i,'Address'] = re_region(table.loc[i,'Address'])
        table.loc[i,'Address'] = table.loc[i,'Address'].replace(tpu,"")
        table.loc[i,'Address'] = re.sub(r"[()]","",table.loc[i,'Address'])
        
        table.loc[i,'TPU'] = re.sub("[^0-9^/]","",tpu)
        
    table.to_excel(table_name)
    print(table_name," TPU Done.")

# In[3]:


#drop_duplicates
def table_drop_dupl(table_name):
    table = pd.read_excel(table_name,index_col=0)
    table.columns+='_3'
    table['id']=table['Lot_3']+"_"+table['buildingcode_3'].map(str)
    table = table.sort_values(['Address_3']).drop_duplicates( subset = 'Address_3' , keep = 'last')
    table.to_excel(table_name)

def add_suffix(path):
    for i in [4,5,6]:
        
        table = pd.read_excel(path+"\\table_5"+str(i)+'.xlsx',index_col=0)
        table.columns+='_'+str(i)
        table['id']=table['Lot_'+str(i)]+"_"+table['buildingcode_'+str(i)].map(str)
        table.to_excel(path+"\\table_5"+str(i)+'.xlsx')


# In[ ]:




