# Process Name: Update LINZ Datasets
# Author: Gareth Palmer
#
# Description:
# Download and process LINZ updates

import pandas as pd
import geopandas as gpd
import psycopg2 as pg
from sqlalchemy import create_engine
import postgis
from owslib.wfs import WebFeatureService as wfs
import xml.etree.ElementTree as et
import codecs
from datetime import datetime as dt
from pyproj import Transformer
import requests
import json

# Classes

class datasetUpdate:
    def create_metadata_conn(self):
        self.mtdt_pg = pg.connect(
            dbname = 'metadata'
            ,user = 'postgres'
            ,password = 'votum123'
            ,host = 'thoth'
            ,port = 5433
        )

    def create_transformer(self):
        self.transformer = Transformer.from_crs(
            4167
            ,2193
        )

    def __init__(self, dataset):
        self.create_metadata_conn()
        self.create_transformer()

        self.dataset = dataset
        self.dataset_id = self.dataset.dataset_id.values[0]
        self.item_no = self.dataset.item_no.values[0]
        self.src_name = self.dataset.source_name.values[0]
        self.src_id = self.dataset.source_id.values[0]
        self.db_name = self.dataset.db_name.values[0]
        self.dataset_type = self.dataset.relation_type.values[0]
        self.geometry = None
        self.to_date = dt.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        self.from_date = '2000-01-01T00:00:00.000Z'
        self.update_data = {}

        self.get_last_update()
        self.get_api()

        self.download_updates()
        self.process_update()

        self.data = self.update_data
        del self.update_data

    def get_api(self):
        '''
        Collects API key needed to access source
        '''
        with self.mtdt_pg.cursor() as conn:
            conn.execute(f'select api_key from public.api_keys where source_id = {self.src_id}')
            self.api_key = conn.fetchone()[0]

        # Check for date of last update
    def get_last_update(self):
        '''
        Gets date of last update. Leaves date as 2000 if no values exist.
        '''
        update_query = f'select max(start_time) from public.dataset_updates where success = True and dataset_id = {self.dataset_id}'

        with self.mtdt_pg.cursor() as conn:
            conn.execute(update_query)
            if conn.rowcount == 1:
                conn_val = conn.fetchone()[0]
                if conn_val is not None:
                    self.from_date == conn_val.strftime('%Y-%m-%dT%H:%M:%S.%fZ')                

    # Download updates from source
    def download_updates(self):
        '''
        Downloads the data needed to perform the update
        '''
        url = ''.join([
            'https://data.linz.govt.nz/services;key='
            ,self.api_key
            ,r'/wfs/'
            ,self.dataset_type
            ,'-'
            ,str(int(self.item_no))
            ,'-changeset?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&typeNames='
            ,self.dataset_type
            ,'-'
            ,str(int(self.item_no))
            ,'-changeset&viewparams=from:'
            ,self.from_date
            ,';to:'
            ,self.to_date
            ,'&outputFormat=json'
            ])
        self.re = requests.get(url)
        re_text = self.re.text
        self.data = json.loads(re_text)


    # Process wfs into useable dataset
    def get_shape(self, subset):
        for child in subset[-1]:
            self.geometry = child.tag[32:]
            if self.geometry == 'Point' and child[0] is not None:
                posList = child[0].text
                vertex_string = self.reproject_coord(posList)
                return self.geometry, f'{self.geometry} ({vertex_string})'
            else:
                break
        for child in subset[-1][0][0]:
            self.geometry = child.tag[32:]
            if self.geometry == 'Polygon' and child[0][0][0] is not None:
                posList = child[0][0][0].text
                vertex_string = self.reproject_coord(posList)
            
            elif self.geometry == 'LineString' and child[0] is not None:
                self.geometry = 'MultiLineString'
                for subchild in child:
                    posList = child[0].text
                    vertex_string = self.reproject_coord(posList)
            
        return self.geometry, f'{self.geometry} (({vertex_string}))'

    ## Possibly use a geopandas gdf to eliminate need to run * lines
    def process_update(self):
        for i, child in enumerate(self.data):
            for subset in child:
                self.update_data[i] = {subchild:subset[subchild] for subchild in subset}
                self.columns = [subchild.tag[26:] for subchild in subset]
                if 'shape' in self.columns:
                    self.geometry, self.update_data[i]['shape'] = self.get_shape(subset)
        
        if len(self.update_data) > 0:
            try:
                df = gpd.GeoDataFrame.from_dict(self.update_data, orient='index')
                for column in list(df.columns):
                    df[column] = df.apply(lambda row: self.check_numeric(row[column]))
            except Exception as e:
                print(e)
    
    def check_numeric(self, val):
        if pd.isnull(val) or type(val) is int:
            return val
        elif re.match(r'^\d*-\d\d-\d\d', val):
            if re.match(r'^\d*-\d\d-\d\dZ', val):
                val = val[:-1] + 'T00:00:00.000000Z'
            return pd.to_datetime(val, yearfirst=True, infer_datetime_format=True)
        test_val = val.replace('.', '').replace('-','')
        if test_val.isnumeric():
            return int(float(val)) if float(val) % 1 == 0 else float(val)
        else:
            return val

    #* Reproject data into NZTM from NZGD2000
    def reproject_coord(self, posList):
        vertexes = []
        for ind, coord in enumerate(posList.split()):
            coord = float(coord)
            if ind % 2 == 0:
                vertex = [coord]
            else:
                vertex.append(coord)
                if coord < 1000:
                    vertex[1], vertex[0] = self.transformer.transform(vertex[0], vertex[1])
                vertex = [str(vert) for vert in vertex]
                vertexes.append(' '.join(vertex))
        return ', '.join(vertexes)
        

    # Write data into postgres database

    #* Add/populate geometry column

    # Update main dataset




# Processing
query_statement = 'select * from public.datasets;'

mtdt_conn = 'postgresql+psycopg2://postgres:votum123@localhost:5433/metadata'

mtdt_pg = pg.connect(
    database='metadata',
    user='postgres',
    password='votum123',
    host='localhost',
    port=5433,
)

mtdt_engine = create_engine(mtdt_conn)

datasets = pd.read_sql(
    query_statement, 
    mtdt_engine
)

# print(datasets.head())

## TESTING RUN
# for ind, dataset in datasets.iterrows():
    # break
dataset = datasets.query('dataset_id == 16')

dataset = datasetUpdate(dataset)
print(len(dict(dataset.data)['features']))

feature_count = 0
for val in dataset.data['features']:
    print(val)
    print('>>', val['geometry'])
    if feature_count > 9:
        break
    else:
        feature_count += 1
