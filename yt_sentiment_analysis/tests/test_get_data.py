import unittest
import json
from unittest.mock import patch
from yt_sentiment_analysis.constants import DATA_DIR
from yt_sentiment_analysis.src.get_data import extract_video_details, get_transcripts
from yt_sentiment_analysis.src.get_data import get_top_videos_by_category
from yt_sentiment_analysis.utils.get_logger import get_logger

from youtube_transcript_api._errors import NoTranscriptFound

logger = get_logger(__name__)


class MockResponse:
    """
    This method will be used by the mock to replace requests.get
    https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
    """

    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def mocked_youtube_transcript_api(*args, **kwargs):
    args_str = '_'.join(args[0])
    fpath = DATA_DIR / 'test_data' / f'YouTubeTranscriptApi_get_transcripts_{args_str}.json'
    with open(fpath, 'r') as fp:
        transcripts_resp = json.load(fp)
        print('tyep of transcript_resp')
        print(type(transcripts_resp))
        print("keys:")
        print(transcripts_resp.keys())
        not_found = []
        return transcripts_resp, not_found

def mocked_youtube_transcript_api__not_found(*args, **kwargs):
    """ Mock the Youtube Transcript API with a 'not found' list reunred. """
    args_str = '_'.join(args[0])
    fpath = DATA_DIR / 'test_data' / f'YouTubeTranscriptApi_get_transcripts_{args_str}.json'
    with open(fpath, 'r') as fp:
        transcripts_resp = json.load(fp)
        print('tyep of transcript_resp')
        not_found = ['testid_000']
        return transcripts_resp, not_found


def mocked_requests_get_youtuberesp(*args, **kwargs):
    params = kwargs['params']
    # Mock out all the YT API Responses expected
    # No params passed (get all videoCategoryId)
    if args[0] == 'https://youtube.googleapis.com/youtube/v3/videos':
        if 'videoCategoryId' in params:
            datapath = DATA_DIR / 'test_data' / 'ytapiresp_get_top_videos_by_category.json'
            with open(datapath, 'r') as fp:
                rsp = json.load(fp)
                return MockResponse(rsp, 200)
        else:
            datapath = DATA_DIR / 'test_data' / 'ytapiresp_wo_cat.json'
            with open(datapath, 'r') as fp:
                rsp = json.load(fp)
                return MockResponse(rsp, 200)
    elif args[0] == 'https://youtube.googleapis.com/youtube/v3/transcripts':
        return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)


def mocked_yttranscriptapi_NoTranscriptFound(*args, **kwargs):
    """ Mock response - when no transcript exists for a video. """
    print('ARGS:')
    print(args)
    # raise NoTranscriptFound(video_id=)


class TestGetData(unittest.TestCase):
    def setUp(self) -> None:
        # youtube API response for /videos endpoint sorted by top
        with open(
            DATA_DIR / "test_data" / "ytapiresp_get_top_videos_by_category.json"
        ) as fp:
            rsp = json.load(fp)
            self.full_videos_by_category_data = rsp
            self.videos_by_category_data = rsp["items"]

        # transcripts formatted for a few videos
        self.video_ids = ['EwTZ2xpQwpA', 'Ka4coAT3YQ4']
        transcript_path = (
            DATA_DIR / "test_data" / "transcripts_EwTZ2xpQwpA_Ka4coAT3YQ4.json"
        )
        with open(transcript_path, "r") as f:
            self.transcript_data = json.load(f)

    # TODO - build out this test more.
    @patch('requests.get', side_effect=mocked_requests_get_youtuberesp)
    def test_get_top_videos_by_category__with_category_id(self, mock_get):
        """ videos from specific `category_id` """
        json_data = get_top_videos_by_category(category_id='1')
        # the mocked yt api response
        self.assertEqual(json_data, self.full_videos_by_category_data)

    # TODO - build out this test more.
    @patch('requests.get', side_effect=mocked_requests_get_youtuberesp)
    def test_get_top_videos_by_category__bad_category_id(self, mock_get):
        """ `category_id` not valid """
        with self.assertRaises(AssertionError):
            get_top_videos_by_category(category_id='9171')

    @patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcripts',
           side_effect=mocked_youtube_transcript_api)
    def test_get_transcripts(self, mock_get):
        """ get transcripts for `self.video_ids` """
        kwargs = {'as_list': True}
        transcripts, ids_not_found = get_transcripts(self.video_ids, **kwargs)

        t0 = transcripts[0]
        t1 = transcripts[1]
        print(t0)
        # make sure formatting is ok
        print('to keys?')
        print(set(list(t0.keys())))

        self.assertEqual(set(list(t0.keys())), set(['transcript', 'video_id']))
        self.assertEqual(set(list(t1.keys())), set(['transcript', 'video_id']))

    @patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcripts',
           side_effect=mocked_youtube_transcript_api__not_found)
    def test_get_transcripts__with_ids_not_found(self, mock_get):
        """ get transcripts for `self.video_ids` """
        kwargs = {'as_list': True}
        transcripts, ids_not_found = get_transcripts(self.video_ids, **kwargs)

        t0 = transcripts[0]
        t1 = transcripts[1]

        self.assertEqual(set(list(t0.keys())), set(['transcript', 'video_id']))
        self.assertEqual(set(list(t1.keys())), set(['transcript', 'video_id']))
        self.assertIn('testid_000', ids_not_found)

    # TODO - build out this test more.
    @patch('requests.get', side_effect=mocked_requests_get_youtuberesp)
    def test_get_top_videos_by_category__none_category_id(self, mock_get):
        json_data = get_top_videos_by_category()
        # the mocked yt api response
        self.assertEqual(json_data, self.full_videos_by_category_data)

    def test_extract_video_details(self):
        # expected input obj
        extracts = extract_video_details(self.videos_by_category_data)
        print(extracts)
        # make sure all extracted
        self.assertEqual(len(extracts), len(self.videos_by_category_data))
        # make sure all details extracted
        test_in = self.videos_by_category_data[0]
        test_out = extracts[0]
        print('test_in')
        print(test_in)
        print('test_out')
        print(test_out)
        # make sure all keys are in output
        self.assertTrue('video_id' in test_out)
        self.assertTrue('title' in test_out)
        self.assertTrue('description' in test_out)
        self.assertTrue('channel_id' in test_out)
        self.assertTrue('channel_name' in test_out)
        self.assertTrue('tags' in test_out)
        self.assertTrue('statistics' in test_out)
        self.assertTrue('category_id' in test_out)
        self.assertTrue('published_dt' in test_out)
        self.assertTrue('insert_dt' in test_out)

    @unittest.skip("skip this test.")
    @patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcripts',
           side_effect=mocked_yttranscriptapi_NoTranscriptFound)
    def test_get_transcripts__raises_NoTranscriptFound(self, mock_get):
        """ get transcripts for `self.video_ids` """
        kwargs = {'as_list': True}
        transcripts, ids_not_found = get_transcripts(self.video_ids, **kwargs)

        t0 = transcripts[0]
        t1 = transcripts[1]
        print(t0)
        # make sure formatting is ok
        self.assertEqual(set(list(t0.keys())), set(['transcript', 'video_id']))
        self.assertEqual(set(list(t1.keys())), set(['transcript', 'video_id']))



if __name__ == "__main__":
    unittest.main()
