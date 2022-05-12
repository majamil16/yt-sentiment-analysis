import json
from tkinter.tix import Tree
from yt_sentiment_analysis.src import get_data
from dotenv import load_dotenv
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from yt_sentiment_analysis import DATA_DIR

# This method will be used by the mock to replace requests.get
# https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
def mocked_requests_get_youtuberesp(*args, **kwargs):
    class MockResponse:
        print("ARGS")
        print(args)
        print("KWARS")
        print(kwargs)
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    params = kwargs['params']
    # Mock out all the YT API Responses expected
    # No params passed (get all videoCategoryId)
    if args[0] == 'https://youtube.googleapis.com/youtube/v3/videos':
        if 'videoCategoryId' in params:
            datapath = DATA_DIR / 'test_data' / 'ytapiresp_wo_cat.json'
            with open(datapath, 'r') as fp:
                rsp = json.load(fp)
                return MockResponse(rsp, 200)
        else :
            datapath = DATA_DIR / 'test_data' / 'ytapiresp_wo_cat.json'
            with open(datapath, 'r') as fp:
                rsp = json.load(fp)
                return MockResponse(rsp, 200)
    # elif args[0] == 'http://someotherurl.com/anothertest.json':
    #     return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)

class TestSrcMethods(unittest.TestCase):

    def setUp(self):
      load_dotenv()
      os.environ['ENV'] = 'Test'
      # self.yt_api_resp = 
     
      with open(Path(DATA_DIR) / 'test_data' / 'ytapiresp_wo_cat.json', 'r') as fp:
        self.yt_api_rsp = json.load(fp)
    
    def tearDown(self):
        print('teardown')

    @patch('requests.get', side_effect=mocked_requests_get_youtuberesp)
    def test_get_top_videos_by_category__with_category_id(self, mock_get):
      json_data = get_data.get_top_videos_by_category(category_id='1')
      # the mocked yt api response
      self.assertEqual(json_data, self.yt_api_rsp)

    @patch('requests.get', side_effect=mocked_requests_get_youtuberesp)
    def test_get_top_videos_by_category__bad_category_id(self, mock_get):
        with self.assertRaises(AssertionError):
            json_data = get_data.get_top_videos_by_category(category_id='9171')


    @patch('requests.get', side_effect=mocked_requests_get_youtuberesp)
    def test_get_top_videos_by_category__none_category_id(self, mock_get):
      json_data = get_data.get_top_videos_by_category()
      # the mocked yt api response
      self.assertEqual(json_data, self.yt_api_rsp)


    @patch('requests.get', side_effect=mocked_requests_get_youtuberesp)
    def test_categories(self, mock_get):
        # get_data.get_vid_info()
        assert False, "Temporary - fail on purpose"
        # for vid in self.yt_api_rsp['items']:
        #     snippet = vid['snippet']
        #     print(vid)
        # for k, v in get_data.CATEGORIES.items():
        #     print(v)


if __name__ == '__main__':
    unittest.main()
