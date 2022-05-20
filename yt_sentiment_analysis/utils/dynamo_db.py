import boto3
import argparse
import os
import sys
from botocore.exceptions import ClientError
# import time
# import uuid
# from datetime import datetime
# from decimal import Decimal
from dynamodb_json import json_util as ddb_json
from yt_sentiment_analysis.utils.get_logger import get_logger
from functools import wraps

logger = get_logger(__name__)


def map_insert(f):
    print('wrapper')
    print(f'in {__name__}')

    @wraps(f)
    def inner(self, map, *args, **kwargs):
        print(f'>>in {__name__}')

        # if list of args videos passed:
        if isinstance(map, dict):
            return f(self, map, *args, **kwargs)
        # if just 1 passed
        elif isinstance(map, list):
            return [f(self, m, *args, **kwargs) for m in map]
        else:
            raise ValueError("unsupported")
    return inner


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
        self._pk = 'video_id' # partition key
        assert self.tablename is not None, 'Initialize `tablename` or env variable `TABLE` must be present.'

    def get_table(self):
        return self.dynamodb.Table(self.tablename)

    def drop_ddb_table(self):
        # table = self.dynamodb.Table(os.getenv('TABLE'))
        table = self.get_table()
        table.delete()

    def check_table_status(self):
        try:
            table = self.dynamodb.Table(self.tablename)
            status = table.table_status
            return status

        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException as exc:
            print(exc)
            print('Table does not exist')
            raise exc

    def create_ddb_table(self, attributes: dict, partition_key_nm: str,
                         sort_key_nm=None, rcu=1, wcu=1):
        """
        To generate DynamoDB create table API call based on input attributes,
        partition, sort key.

        Params:
        -------
        :attributes - dict[str, str] where { ATTR_NAME : ATTR_TYPE }
        :partition_key - required. Partition key for the table
        :sort_key - optional. Sort (range) key for the table
        :rcu - read capacity units. default to 1
        :wcu - write capacity units. default to 1
        """
        attrs = [{"AttributeName": k, "AttributeType": v} for k, v in attributes.items()]
        keys = [{"AttributeName": partition_key_nm, "KeyType": "HASH"}]
        if sort_key_nm is not None:
            keys.append({"AttributeName": sort_key_nm, "KeyType": "RANGE"})

        schema_def = {
            "AttributeDefinitions": attrs,
            "KeySchema": keys,
            "ProvisionedThroughput": {"ReadCapacityUnits": rcu,
                                      "WriteCapacityUnits": wcu
                                      },
        }
        table = self.dynamodb.create_table(
            TableName=os.getenv('TABLE'),
            KeySchema=keys,
            AttributeDefinitions=attrs,
            ProvisionedThroughput={"ReadCapacityUnits": rcu, "WriteCapacityUnits": wcu},
        )
        return table

    @classmethod
    def format(cls, data: dict) -> dict:
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

    @map_insert
    def insert(self, formatted_data: dict, return_id=True):
        """
        DDB insert of formatted_data

        Params
        ------
        formatted_data :
        """
        tbl = self.get_table()
        resp = tbl.put_item(Item=formatted_data, ReturnValues='ALL_OLD')

        if return_id:
            return formatted_data[self._pk]
        return resp

    def update(self, formatted_data: dict, src_obj: str):
        """
        DDB update existing item based on formatted_data[`video_id`]

        Params
        ------
        :param dict formatted_data: {video_id, ...rest}
        :param str src_obj: specify ['transcript', 'video']
        """
        partition_key = 'video_id'
        sort_key = None
        if src_obj not in ['transcript', 'video']:
            logger.error("results: status must be one of %r, %r."
                         % ['transcript', 'video'])
            raise ValueError("results: status must be one of %r, %r."
                             % ['transcript', 'video'])

        try:
            # update expression will differ depending on src
            update_exp_map = ','.join([f'{k}=:{k}' for k in formatted_data.keys()
                                      if k not in [partition_key, sort_key]])
            update_exp_map = f"set {update_exp_map}"
            logger.debug("Update expression : ")
            logger.debug(update_exp_map)

            # exp_att_map = ','.join([f':{k}={v}' for k, v in formatted_data.items()])

            exp_att_map = {f':{k}': v for k, v in formatted_data.items()
                           if k not in [partition_key, sort_key]}

            # exp_att_map = f"set {exp_att_map}"
            logger.debug("Expression Attribute Map:")
            logger.debug(exp_att_map)

            response = self.get_table().update_item(
                Key={'video_id': formatted_data['video_id']},
                UpdateExpression=update_exp_map,
                ExpressionAttributeValues=exp_att_map,
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            logger.error(
                "Couldn't update video %s in table %s. Here's why: %s: %s",
                formatted_data['video_id'], self.tablename,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']

    @map_insert
    def upsert(self, formatted_data: dict, src_obj: str):
        """
        Update or insert.
        """
        # try get_item
        item = self.get_table().get_item(Key={'video_id': formatted_data['video_id']})
        # if found, update
        if 'Item' in item:
            return self.update(formatted_data, src_obj)
        # else insert
        else:
            return self.insert(formatted_data)


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--drop', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()

    client = Dynamo()
    if len(sys.argv) != 2:  # we want 2 args (the 2nd is the flag)
        print('Flags must be exactly ONE OF : --create, --drop, --check')
    elif args.create and args.drop:
        print('both')
    elif args.create:
        attributes = {"video_id": "S", "transcript": "S", "category_id": "S", "category_nm": "S"}
        dynamo_table = client.create_ddb_table(attributes=attributes, partition_key_nm='video_id')
        print("Table status:", dynamo_table.table_status)
    elif args.drop:
        client.drop_ddb_table()
        print("Table status: dropped")
    elif args.check:
        status = client.check_table_status()
        print(status)
