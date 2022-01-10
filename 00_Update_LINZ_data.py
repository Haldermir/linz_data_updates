#!/usr/bin/env python
# coding: utf-8

# # Download updates from LINZ
# 
# Creating a script that would download the updates from the LINZ data portal on a regular basis using the LINZ Changeset API. Most changes come through in frequently so needed to create a script that would only load the changes if any were found. 
# 
# The list of datasets that need to be checked are contained in a spreadsheet in the same directory as the initial downloads. New datasets and updates are able to be added to this spreadsheet moving forward.

import requests
import pandas as pd
import psycopg2 as pg
import postgis
from sqlalchemy import create_engine
from owslib.wfs import WebFeatureService
import xml.etree.ElementTree as et
import codecs
import datetime as dt
from pyproj import Transformer
import re

today = dt.datetime.now()
to_date = today.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

week = dt.timedelta(weeks=1)
then = today - week
from_date = then.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

transformer = Transformer.from_crs(4167, 2193)

# Setting up logfile for process

log = r"G:\GIS DataBase\Updates\update_log.txt"

with open(log, 'w') as log_writer:
    log_writer.write('#######################################\n')
    log_date = today.strftime('%d-%m-%Y')
    log_writer.write(f'Log file for {log_date}\n')
    log_writer.write('#######################################\n')
    log_writer.write('\n\n')

def log_write(message):
    with open(log, 'a') as log_writer:
        log_writer.write(f'{message}\n')

def check_numeric(val):
    if pd.isnull(val) or type(val) is int:
        return val
    elif re.match(r'^\d*-\d\d-\d\d', val):
        if re.match(r'^\d*-\d\d-\d\dZ', val):
            val = val[:-1] + 'T00:00:00.000000Z'
        return pd.to_datetime(val, yearfirst=True, infer_datetime_format=True)
    test_val = val.replace('.', '').replace('-','')
    if test_val.isnumeric():
        if float(val) % 1 == 0:
            return int(float(val))
        else:
            return float(val)
    else:
        return val

def get_shape(subset):
    for child in subset[-1]:
        geometry = child.tag[32:]
        if geometry == 'Point' and child[0] is not None:
            posList = child[0].text
            vertexes = []
            for ind, coord in enumerate(posList.split()):
                coord = float(coord)
                if ind % 2 == 0:
                    vertex = [coord]
                else:
                    vertex.append(coord)
                    if coord < 1000:
                        vertex[1], vertex[0] = transformer.transform(vertex[0], vertex[1])
                    vertex = [str(vert) for vert in vertex]
                    vertexes.append(' '.join(vertex))
            vertex_string = ', '.join(vertexes)
            return geometry, f'{geometry} ({vertex_string})'
        else:
            break
    for child in subset[-1][0][0]:
        geometry = child.tag[32:]
        if geometry == 'Polygon' and child[0][0][0] is not None:
            posList = child[0][0][0].text
            vertexes = []
            for ind, coord in enumerate(posList.split()):
                coord = float(coord)
                if ind % 2 == 0:
                    vertex = [coord]
                else:
                    vertex.append(coord)
                    if coord < 1000:
                        vertex[1], vertex[0] = transformer.transform(vertex[0], vertex[1])
                    vertex = [str(vert) for vert in vertex]
                    vertexes.append(' '.join(vertex))
            vertex_string = ', '.join(vertexes)
        
        elif geometry == 'LineString' and child[0] is not None:
            geometry = 'MultiLineString'
            for subchild in child:
                posList = child[0].text
                vertexes = []
                for ind, coord in enumerate(posList.split()):
                    coord = float(coord)
                    if ind % 2 == 0:
                        vertex = [coord]
                    else:
                        vertex.append(coord)
                        if coord < 1000:
                            vertex[1], vertex[0] = transformer.transform(vertex[0], vertex[1])
                        vertex = [str(vert) for vert in vertex]
                        vertexes.append(' '.join(vertex))
                vertex_string = ', '.join(vertexes)
        return geometry, f'{geometry} (({vertex_string}))'

def get_updates(layer_id, table_type, api_key, from_date=from_date, to_date=to_date):
    url = f'https://data.linz.govt.nz/services;key={api_key}/wfs/{table_type}-{layer_id}-changeset?SERVICE=WFS&REQUEST=GetFeature&viewparams=from:{from_date};to:{to_date}&TYPENAMES=data.linz.govt.nz%3A{table_type}-{layer_id}-changeset&NAMESPACES=xmlns%28data.linz.govt.nz%2Chttp%3A%2F%2Fdata.linz.govt.nz%29&OUTPUTFORMAT=application%2Fgml%2Bxml%3B%20version%3D3.2'
    re = requests.get(url)
    return re.status_code, re.text

def main(test_update, dataset, id_val):
    log_write('\n')
    log_write(dataset)
    with codecs.open(r"G:\GIS DataBase\Updates\update_data.txt", "w", "utf-8") as writer:
        writer.writelines(test_update)

    tree = et.fromstring(test_update)
    geometry = None
    data = {}

    for i, child in enumerate(tree):
        for subset in child:
            data[i] = {subchild.tag[26:]:subchild.text for subchild in subset}
            new_cols = [subchild.tag[26:] for subchild in subset]
            if 'shape' in new_cols:
                geometry, data[i]['shape'] = get_shape(subset)

    # Checking that the data frame has values present to allow uploads
    if len(data) > 0:
        try:
            df = pd.DataFrame.from_dict(data,orient='index')
            for column in list(df.columns):
                df[column] = df.apply(lambda row: check_numeric(row[column]), axis=1)
            df.convert_dtypes()
            df.to_sql('data_updates', engine, 'updates', if_exists='replace', index=False)
        except Exception as e:
            log_write('Failed to upload')
            log_write(e)
            return
    else:
        log_write('No data')
    
    if geometry:
        with psy_con.cursor() as conn:
            try:
                conn.execute(f"alter table updates.data_updates add column geom Geometry('{geometry}', 2193);")
                conn.execute("update updates.data_updates set geom = ST_GeomFromText(shape, 2193);")
                psy_con.commit()
            except Exception as e:
                log_write('Table not able to update')
                log_write(e)
                psy_con.rollback()
        
    if len(data) > 0:
        fields = list(df.columns)
        if '__change__' in fields:
            fields.remove('__change__')
        if 'shape' in fields:
            fields.remove('shape')
        
        field_list = ','.join(fields).lower()
        
        with  psy_con.cursor() as conn:
            try:
                conn.execute(f"delete from {dataset} where {id_val} in (select {id_val} from updates.data_updates)")
                if 'shape' in list(df.columns):
                    if geometry == 'Polygon':
                        conn.execute(f"insert into {dataset} (geom, {field_list}) select ST_Multi(geom), {field_list} from updates.data_updates where __change__ != 'DELETE'")
                    else:
                        conn.execute(f"insert into {dataset} (geom, {field_list}) select geom, {field_list} from updates.data_updates where __change__ != 'DELETE'")
                else:
                    print('Updating without geom')
                    conn.execute(f"insert into {dataset} ({field_list}) select {field_list} from updates.data_updates where __change__ != 'DELETE'")
                psy_con.commit()
            except Exception as e:
                log_write('Updates not successful')
                log_write(e)
                psy_con.rollback()
            finally:
                conn.execute('drop table updates.data_updates;')
                psy_con.commit()

services = r"G:\GIS DataBase\Updates\update_datasets.csv"

services_df = pd.read_csv(services)
# services_df

api_key = 'Put your key in here'

psy_con = pg.connect(database='postgres', user='postgres', password='votum123', host='localhost', port=5432)
postgis.register(psy_con)

pg_con = 'postgresql+psycopg2://postgres:votum123@localhost:5432/postgres'
engine = create_engine(pg_con)

for row in services_df.iterrows():
    layer_id = row[1]['item_no']
    layer_type = row[1]['Data_type']
    status_code, updates = get_updates(layer_id, layer_type, api_key)
    if status_code == 200:
        main(updates, row[1]['Table_Names'], row[1]['id_value'])

