import unittest
import json

from yt_sentiment_analysis.constants import DATA_DIR

# from yt_sentiment_analysis.utils.dynamo_db import Dynamo
from yt_sentiment_analysis.utils.get_logger import get_logger
from datetime import datetime

# from moto import mock_dynamodb

logger = get_logger(__name__)


class TestGetData(unittest.TestCase):
    def setUp(self) -> None:
        # youtube API response for /videos endpoint sorted by top
        with open(
            DATA_DIR / "test_data" / "ytapiresp_get_top_videos_by_category.json"
        ) as fp:
            rsp = json.load(fp)
            self.videos_by_category_data = rsp["items"]
        # with open(DATA_DIR / "dynamodb" / "table_schema.json") as sch:
        #     self.table_schema = json.load(sch)["Table"]
        # self.client = Dynamo()

        # transcripts formatted for a few videos
        transcript_path = (
            DATA_DIR / "test_data" / "transcripts_EwTZ2xpQwpA_Ka4coAT3YQ4.json"
        )
        with open(transcript_path, "r") as f:
            self.transcript_data = json.load(f)

        # self.client.dynamodb.create_table(
        #     TableName=self.client.tablename,
        #     KeySchema=self.table_schema["KeySchema"],
        #     AttributeDefinitions=self.table_schema["AttributeDefinitions"],
        #     ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        # )

        # maek sure table exists
        # assert self.client.get_table().table_status == "ACTIVE"

    def test_get_top_videos_by_category(self):
        pass

    def test_get_transcripts(self):
        pass

    def test_extract_video_details(self):
        pass


if __name__ == "__main__":
    unittest.main()
