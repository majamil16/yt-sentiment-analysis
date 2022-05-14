import unittest
import json

from responses import upsert
from yt_sentiment_analysis.constants import DATA_DIR
from yt_sentiment_analysis.utils.dynamo_db import Dynamo
from yt_sentiment_analysis.utils.get_logger import get_logger
from datetime import datetime
from moto import mock_dynamodb

logger = get_logger(__name__)


@mock_dynamodb
class TestDynamoDB(unittest.TestCase):
    def setUp(self) -> None:
        # youtube API response for /videos endpoint sorted by top
        with open(
            DATA_DIR / "test_data" / "ytapiresp_get_top_videos_by_category.json"
        ) as fp:
            rsp = json.load(fp)
            self.videos_by_category_data = rsp["items"]
        with open(DATA_DIR / "dynamodb" / "table_schema.json") as sch:
            self.table_schema = json.load(sch)["Table"]
        self.client = Dynamo()

        # video_ids = ['EwTZ2xpQwpA', 'Ka4coAT3YQ4']
        # transcripts formatted for a few videos
        transcript_path = (
            DATA_DIR / "test_data" / "transcripts_EwTZ2xpQwpA_Ka4coAT3YQ4.json"
        )
        with open(transcript_path, "r") as f:
            self.transcript_data = json.load(f)

        self.client.dynamodb.create_table(
            TableName=self.client.tablename,
            KeySchema=self.table_schema["KeySchema"],
            AttributeDefinitions=self.table_schema["AttributeDefinitions"],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        )

        # maek sure table exists
        assert self.client.get_table().table_status == "ACTIVE"

    def tearDown(self) -> None:
        """
        Delete database resource and mock table
        """
        logger.debug("Tearing down")
        self.client.get_table().delete()
        self.client.dynamodb = None
        self.client = None
        print("Teardown complete")

    def test_get_dynamo(self):
        """
        Test get table
        """
        table = self.client.get_table()
        # <class 'boto3.resources.factory.dynamodb.Table'>
        self.assertEqual(table.__class__.__name__, "dynamodb.Table")

    def test_insert__videos(self):
        """
        Test inserting /videos endpoint data into DynamoDB
        """
        for vid in self.videos_by_category_data:
            fmt_dict = {
                "video_id": vid["id"],
                "title": vid["snippet"]["title"],
                "description": vid["snippet"]["description"],
                "channel_id": vid["snippet"]["channelId"],
                "channel_name": vid["snippet"]["channelTitle"],
                "tags": vid["snippet"].get("tags"),
                "statistics": ["statistics"],
                "category_id": vid["snippet"]["categoryId"],
                "published_dt": vid["snippet"]["publishedAt"],
                "insert_dt": datetime.utcnow().strftime("%m-%d-%Y"),
            }

            self.client.insert(fmt_dict)

            # make sure the item was inserted ...
            table = self.client.get_table()
            response = table.get_item(
                Key={
                    "video_id": vid["id"],
                }
            )
            if "Item" in response:
                item = response["Item"]

            # assert we get back the same object.
            self.assertEquals(fmt_dict, item)
            # assert all keys that should be in Item are in
            # self.assertTrue('video_id'   in item)
            # self.assertTrue('title'        in item)
            # self.assertTrue('description'  in item)
            # self.assertTrue('channel_id'   in item)
            # self.assertTrue('channel_name' in item)
            # self.assertTrue('tags' in item)
            # self.assertTrue('statistics'   in item)
            # self.assertTrue('category_id'  in item)
            # self.assertTrue('published_dt' in item)
            # self.assertTrue('insert_dt' in item)

    def test_update__transcripts(self):
        # first insert a transcript
        table = self.client.get_table()
        response = table.put_item(
            Item={"video_id": "test_id", "transcript": "Test transcript"}
        )

        # then update it
        fmt_update = {"video_id": "test_id", "transcript": "Test updated transcript"}
        self.client.update(fmt_update, src_obj="transcript")

        # make sure updated
        response = table.get_item(
            Key={
                "video_id": "test_id",
            }
        )
        if "Item" in response:
            item = response["Item"]
        # assert the updated value is present
        self.assertEquals(item, fmt_update)
        self.assertEquals(item['transcript'], "Test updated transcript")

    def test_insert__transcripts(self):
        """
        Test inserting Youtube Transcript data into DynamoDB
        """
        for vid in self.transcript_data:
            fmt_dict = {
                "video_id": vid["id"],
                "transcript": vid["transcript"],
                "insert_dt": datetime.utcnow().strftime("%m-%d-%Y"),
            }

            self.client.insert(fmt_dict)

            # make sure the item was inserted ...
            table = self.client.get_table()
            response = table.get_item(
                Key={
                    "video_id": vid["id"],
                }
            )
            if "Item" in response:
                item = response["Item"]
                print(item)
            # assert all keys that should be in Item are in
            self.assertEquals(item, fmt_dict)
            self.assertTrue("video_id" in item)
            self.assertTrue("transcript" in item)
            self.assertTrue("insert_dt" in item)

    def test_upsert__transcript_to_exising_video(self):
        """
        Test adding Transcript data by key that already exists in DDB
        """
        # insert video into DDB
        vid = self.videos_by_category_data[0]
        fmt_dict = {
            "video_id": vid["id"],
            "title": vid["snippet"]["title"],
            "description": vid["snippet"]["description"],
            "channel_id": vid["snippet"]["channelId"],
            "channel_name": vid["snippet"]["channelTitle"],
            "tags": vid["snippet"].get("tags"),
            "statistics": ["statistics"],
            "category_id": vid["snippet"]["categoryId"],
            "published_dt": vid["snippet"]["publishedAt"],
            "insert_dt": datetime.utcnow().strftime("%m-%d-%Y"),
        }

        self.client.insert(fmt_dict)

        # upsert transcript
        transc_dict = {
            "video_id": vid["id"],
            "transcript": "Test transcript",
            "update_dt": datetime.utcnow().strftime("%m-%d-%Y"),
        }

        self.client.upsert(transc_dict, src_obj="video")

        # retrieve the upserted item
        response = self.client.get_table().get_item(
            Key={
                "video_id": vid["id"],
            }
        )
        if "Item" in response:
            item = response["Item"]
            print(item)

        upsert_itm = {**fmt_dict, 'transcript':transc_dict['transcript'], 'update_dt':transc_dict['update_dt']  }

        self.assertEquals(item, upsert_itm)

    def test_upsert__video_to_exising_transcript(self):
        """
        Test adding Video data by key that already exists in DDB from Transcript
        This use case is not as relevant, because list of video is always retrieved first.
        """
        # upsert transcript into DDB
        vid = self.videos_by_category_data[0]
        # insert transcript
        transc_dict = {
            "video_id": vid["id"],
            "transcript": "Test transcript",
            "insert_dt": datetime.utcnow().strftime("%m-%d-%Y"),
        }

        self.client.insert(transc_dict)

        # upsert video details
        fmt_dict = {
            "video_id": vid["id"],
            "title": vid["snippet"]["title"],
            "description": vid["snippet"]["description"],
            "channel_id": vid["snippet"]["channelId"],
            "channel_name": vid["snippet"]["channelTitle"],
            "tags": vid["snippet"].get("tags"),
            "statistics": ["statistics"],
            "category_id": vid["snippet"]["categoryId"],
            "published_dt": vid["snippet"]["publishedAt"],
            "update_dt": datetime.utcnow().strftime("%m-%d-%Y"),
        }

        self.client.upsert(fmt_dict, src_obj="transcript")
        # retrieve the upserted item
        response = self.client.get_table().get_item(
            Key={
                "video_id": vid["id"],
            }
        )
        if "Item" in response:
            item = response["Item"]
            print(item)
        upsert_itm = {**fmt_dict, 'transcript':transc_dict['transcript'], 'insert_dt':transc_dict['insert_dt']  }
        self.assertEquals(item, upsert_itm)


if __name__ == "__main__":
    unittest.main()
