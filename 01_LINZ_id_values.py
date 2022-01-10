#!/usr/bin/env python
# coding: utf-8

# # Extract LINZ Layer ID Values
# Extracts the layer ids from the LINZ readme documents. uses pandas to process the data and export to csv file

# In[1]:


import pandas as pd
import os


# In[2]:


update_dir = r'G:\GIS DataBase\Updates'


# In[3]:


def get_id(txt):
    with open(txt, 'r') as open_text:
        line = None
        while_count = 0
        while line is None and while_count < 500:
            test_line = open_text.readline()
            if test_line[:5] == ' http':
                return test_line[:-1]
            while_count += 1
        #return line[:-1]


# In[30]:


def get_name(val):
    try:
        return val.split('/')[-2]
    except Exception:
        return val

def get_id_no(val):
    return val.split('-')[0]

def get_type(val):
    try:
        return val.split('/')[-3]
    except Exception:
        return val


# In[9]:


files = []

for root, dirname, filenames in os.walk(update_dir):
    for filename in filenames:
        if filename[-3:] == 'txt' and filename != 'update_data.txt':
            print(filename)
            #print(os.path.join(root,filename))
            #print(os.path.exists(os.path.join(root, filename)))
            try:
                line = get_id(os.path.join(root, filename))
            except Exception:
                line = '!! Could not read file'
            print(line)
            files.append([filename, line])
            
file_df = pd.DataFrame(data = files, columns=['Source_File','Path'])


# In[28]:


file_df['Name'] = file_df.apply(lambda row: get_name(row['Path']), axis=1)
file_df['item_no'] = file_df.apply(lambda row: get_id_no(row['Name']), axis=1)


# In[31]:


file_df['Data_type'] = file_df.apply(lambda row: get_type(row['Path']), axis=1)


# In[32]:


file_df


# In[34]:


file_df.to_csv(os.path.join(update_dir, 'update_datasets_new.csv'))

