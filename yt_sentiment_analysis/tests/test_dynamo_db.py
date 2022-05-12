import unittest
import json
from yt_sentiment_analysis.constants import DATA_DIR
from yt_sentiment_analysis.utils.dynamo_db import Dynamo
import boto3
from datetime import datetime
from moto import mock_dynamodb

@mock_dynamodb
class TestDynamoDB(unittest.TestCase):

  def setUp(self) -> None:
      # youtube API response for /videos endpoint sorted by top
      with open(DATA_DIR/'test_data'/'ytapiresp_get_top_videos_by_category.json') as fp:
        rsp = json.load(fp)
        self.videos_by_category_data = rsp['items']
      with open(DATA_DIR/'dynamodb'/'table_schema.json') as sch:
        self.table_schema = json.load(sch)["Table"]
      self.client = Dynamo()

      video_ids = ['EwTZ2xpQwpA', 'Ka4coAT3YQ4']
      # transcripts formatted for a few videos
      transcript_path = DATA_DIR/'test_data'/'transcripts_EwTZ2xpQwpA_Ka4coAT3YQ4.json'
      with open(transcript_path, 'r') as f : 
        self.transcript_data = json.load(f)

      # pre-format the transcript
      # from yt_sentiment_analysis.src.get_data import MyCustomFormatter, get_transcripts
      # self.fmt_transcript = get_transcripts(video_ids=video_ids, save_filepath=transcript_path)

      # create table
      # assert self.client.get_table().table_status == 'ACTIVE'

      self.client.dynamodb.create_table(
          TableName=self.client.tablename,
          KeySchema=self.table_schema['KeySchema'],
          AttributeDefinitions=self.table_schema['AttributeDefinitions'],
          ProvisionedThroughput={
              'ReadCapacityUnits': 1,
              'WriteCapacityUnits': 1
          }
      )


  def tearDown(self) -> None:
      """ 
      Delete database resource and mock table
      """
      print("Tearing down")
      self.client.get_table().delete()
      self.client.dynamodb = None
      self.client = None

      print("Teardown complete")

  # @mock_dynamodb
  def test_get_dynamo(self):
    """
    Test get table
    """
    table = self.client.get_table()
    print('table') 
    print(table)
    assert table


  # @mock_dynamodb
  def test_insert__videos(self):
    """
    Test inserting /videos endpoint data into DynamoDB
    """
    # self.client.dynamodb.create_table(
    #         TableName=self.client.tablename,
    #         KeySchema=self.table_schema['KeySchema'],
    #         AttributeDefinitions=self.table_schema['AttributeDefinitions'],
    #         ProvisionedThroughput={
    #             'ReadCapacityUnits': 1,
    #             'WriteCapacityUnits': 1
    #         }
    #     )

    for vid in self.videos_by_category_data : 
      fmt_dict = {
        'video_id'      : vid['id'],
        'title'         : vid['snippet']['title'],
        'description'   : vid['snippet']['description'],
        'channel_id'    : vid['snippet']['channelId'],
        'channel_name'  : vid['snippet']['channelTitle'],
        'tags' : vid['snippet'].get('tags'),
        'statistics'    : ['statistics'],
        'category_id'   : vid['snippet']['categoryId'],
        'published_dt'  : vid['snippet']['publishedAt'],
        'insert_dt': datetime.utcnow().strftime('%m-%d-%Y')
        }
      
      self.client.insert(fmt_dict)

      # make sure the item was inserted ...
      table = self.client.get_table()
      response = table.get_item(
          Key={
              'video_id' : vid['id'],
          }
      )
      if 'Item' in response:
        item = response['Item']
        print(item)
      # assert all keys that should be in Item are in
      self.assertTrue('video_id'   in item)
      self.assertTrue('title'        in item)
      self.assertTrue('description'  in item)
      self.assertTrue('channel_id'   in item)
      self.assertTrue('channel_name' in item)
      self.assertTrue('tags' in item)
      self.assertTrue('statistics'   in item)
      self.assertTrue('category_id'  in item)
      self.assertTrue('published_dt' in item)
      self.assertTrue('insert_dt' in item)




  # @mock_dynamodb
  def test_insert__transcripts(self):
    """
    Test inserting Youtube Transcript data into DynamoDB
    """

    # self.client.dynamodb.create_table(
    #     TableName=self.client.tablename,
    #     KeySchema=self.table_schema['KeySchema'],
    #     AttributeDefinitions=self.table_schema['AttributeDefinitions'],
    #     ProvisionedThroughput={
    #         'ReadCapacityUnits': 1,
    #         'WriteCapacityUnits': 1
    #     }
    # )

    for vid in self.transcript_data : 
      print('vid')
      print(vid)
      fmt_dict = {
        'video_id'      : vid['id'],
        'transcript'    : vid['transcript'],
        'insert_dt': datetime.utcnow().strftime('%m-%d-%Y')
        }
      
      self.client.insert(fmt_dict)

      # make sure the item was inserted ...
      table = self.client.get_table()
      response = table.get_item(
          Key={
              'video_id' : vid['id'],
          }
        )
      if 'Item' in response:
        item = response['Item']
        print(item)
      # assert all keys that should be in Item are in
      self.assertTrue('video_id'   in item)
      self.assertTrue('transcript'        in item)
      self.assertTrue('insert_dt' in item)

  # @mock_dynamodb
  def test_upsert__transcript_to_exising_video(self):
    """
    Test adding Transcript data by key that already exists in DDB
    """
    pass

  # @mock_dynamodb
  def test_upsert__video_to_exising_transcript(self):
    """
    Test adding Video data by key that already exists in DDB from Transcript
    """
    pass

if __name__ == '__main__':
  unittest.main()