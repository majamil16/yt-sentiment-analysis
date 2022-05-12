from tkinter.tix import Tree
import boto3
import argparse
import os
import sys
# import time
# import uuid
# from datetime import datetime
# from decimal import Decimal
from dynamodb_json import json_util as ddb_json

class Dynamo():
    """
    Simple class to handle creating / dropping dynamodb table as needed
    (for easy dropping data after testing, etc)
    """
    def __init__(self, tablename=os.getenv('TABLE')):
        """
        Initialize Dynamo class.

        params
        ------
        : tablename[str] - will default to environment variable TABLE if none passed
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.tablename = tablename
        assert self.tablename is not None, 'Initialize `tablename` or env variable `TABLE` must be present.'

    def get_table(self):
        return self.dynamodb.Table(self.tablename)


    def drop_ddb_table(self):
        # table = self.dynamodb.Table(os.getenv('TABLE'))
        table = self.get_table()
        table.delete()

    def check_table_status(self):
        try :
          table = self.dynamodb.Table(self.tablename)
          status = table.table_status
          return status

        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException as exc :
          print(exc)
          print('Table does not exist')
          raise exc

    def create_ddb_table(self, attributes:dict, partition_key_nm:str, sort_key_nm=None, rcu=1, wcu=1):
      """
      To generate DynamoDB create table API call based on input attributes, partition, sort key.

      Params:
      -------
      :attributes - dict[str, str] where { ATTR_NAME : ATTR_TYPE }
      :partition_key - required. Partition key for the table
      :sort_key - optional. Sort (range) key for the table
      :rcu - read capacity units. default to 1
      :wcu - write capacity units. default to 1
      """
      attrs = [{"AttributeName": k, "AttributeType": v} for k, v in attributes.items()]
      keys = [{"AttributeName": partition_key_nm, "KeyType": "HASH"} ]
      if sort_key_nm is not None : 
        keys.append({"AttributeName": partition_key_nm, "KeyType": "RANGE"})

      schema_def = {
          "AttributeDefinitions": attrs,
          "KeySchema": keys,
          "ProvisionedThroughput": {"ReadCapacityUnits": rcu, "WriteCapacityUnits": wcu},
      }  
                          
      table = self.dynamodb.create_table(
        TableName=os.getenv('TABLE'),
        KeySchema=keys,
        AttributeDefinitions=attrs,
        ProvisionedThroughput={"ReadCapacityUnits": rcu, "WriteCapacityUnits": wcu},
      )
      return table

    @classmethod
    def format(cls, data:dict) -> dict:
        """
        format dict as DynamoDB-format json data for DDB insert

        Params
        ------
        data : dict object of {K:V}

        Returns
        -------
        """
        dynamodb_json = ddb_json.dumps(data, as_dict=True)
        print(dynamodb_json)
        return dynamodb_json

    def insert(self, formatted_data:dict):
        """
        DDB insert of formatted_data

        Params
        ------
        formatted_data : 
        """
        # dynamodb_json = ddb_json.dumps(formatted_data, as_dict=True)
        print('tyep of ddb json:')
        # print(type(formatted_data))
        tbl = self.get_table()
        print('table')
        print('type of table : ')
        print(type(tbl))

        print(tbl)
        resp = tbl.put_item(Item=formatted_data)
        print('type of resp : ')
        print(type(resp))
        return resp

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--drop', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    client = Dynamo()
    if len(sys.argv) != 2: # we want 2 args (the 2nd is the flag)
        print('Flags must be exactly ONE OF : --create, --drop, --check')
        
    elif args.create and args.drop:
        print('both')
    elif args.create:
        attributes = { "video_id" : "S", "transcript" : "S", "category_id":"S", "category_nm" : "S"}
        dynamo_table = client.create_ddb_table(attributes=attributes, partition_key_nm='video_id')
        print("Table status:", dynamo_table.table_status)
    elif args.drop:
        client.drop_ddb_table()
        print("Table status: dropped" )
    elif args.check:
        status = client.check_table_status()
        print(status)