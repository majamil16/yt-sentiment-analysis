
from __future__ import annotations

from unittest import mock
import requests
import os
from pathlib import Path, PurePath
import logging
import time
from yt_sentiment_analysis.constants  import YOUTUBE_API_KEY, CATEGORIES, DATA_DIR 
import json
from youtube_transcript_api  import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter, Formatter
import time
from datetime import datetime
from decimal import Decimal

from yt_sentiment_analysis.utils.dynamo_db import Dynamo

FORMAT = '%(asctime)s %(levelname)s %(name)s:%(funcName)s %(message)s'

logging.basicConfig(format=FORMAT)
logger = logging.getLogger("get_data" )

class MyCustomFormatter(Formatter):

    def format_transcript(self, video_id:str, transcript, **kwargs):
        # Do your custom work in here, but return a string.
        fmt = {video_id : transcript}
        return self.format_transcripts([fmt])

    def format_transcripts(self, transcripts, **kwargs):
        # Do your custom work in here to format a list of transcripts, but return a string.
        transcripts_fmt = []
        # transcripts_fmt = {}
        print(transcripts)
        for id, transcript in transcripts.items(): 
            transcript_fmt = {}
            print('id' + id)
            print(transcript)
            if isinstance(transcript, list):
                print('transc')

                joined_tr = " ".join([t['text'] for t in transcript])
                print(joined_tr)
                # transcripts_fmt[id] = joined_tr

                transcript_fmt['id'] = id
                transcript_fmt['transcript'] = joined_tr
                # append the single transcript dict to the list of transcripts
                transcripts_fmt.append(transcript_fmt)
        return json.dumps(transcripts_fmt)


def get_top_videos_by_category(category_id:str=None, save:bool=False, max_results:int=50) -> dict:
    """
    Get the top videos for the specified `category_id`.

    Category IDs for US categories are stored in constants.py CATEGORIES variable. Note - some return no response.

    Params
    ------
    : category_id: YouTube API videoCategoryId of videos to get. 
    : max_results : Max results 
    """
    if category_id is not None:
        assert category_id in list(CATEGORIES.keys()) , "enter a valid category_id"
    url = 'https://youtube.googleapis.com/youtube/v3/videos'
    params = {
    'part': ['snippet','contentDetails','statistics'],
    "chart" : "mostPopular",
    "regionCode": "US",
    "key" : YOUTUBE_API_KEY,
    "maxResults" : max_results,
    # "videoCategoryId" : category_id
    }
    # add category_id if it is passed in
    if category_id : 
        params["videoCategoryId"] = category_id

    # get the top videos for the category
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        print("JSON KEYS")
        if save:
            if category_id : 
                fname = 'ytapiresp_get_top_videos_by_category_{category_id}.json'
                with open(Path(DATA_DIR)/fname, 'w') as fp:
                    json.dump(data, fp)[[]]
            else : 
                fname = 'ytapiresp_get_top_videos_by_category.json'
            with open(Path(DATA_DIR)/fname, 'w') as fp:
                json.dump(data, fp)
        return data
    else : 
        logger.error("boo!")
        print(r.status_code)
        print(r.text)
        return None


def get_transcripts(video_ids:list, load_filepath:str=None, save_filepath:str=None):
    """
    Get the transcripts for `video_ids` list

    Params:
    ------
    :video_ids : list of video_ids for the youtube video
    :load_filepath (opt): file path to load data from instead.
    :save_filepath (opt): file path to save data to.

    """
    if load_filepath:
        # If file path is specified, return 
        with open(load_filepath, 'r') as f:
            loaded = json.load(f)
            loaded_ids = loaded.keys()
            return loaded, loaded_ids
    transcripts, video_ids_not_found = YouTubeTranscriptApi.get_transcripts(video_ids)

    formatter = MyCustomFormatter()

    # turns the transcript into a JSON string.
    json_formatted = formatter.format_transcripts(transcripts)
    # Now we can write it out to a file.
    if save_filepath is not None:
        with open(save_filepath, 'w', encoding='utf-8') as json_file:
            json_file.write(json_formatted)
    return json



def extract_video_details(videos:list, format_dynamo=True) -> list[dict]:
    """
    Extract relevant info from the /videos api response (youtube#videoListResponse)

    Params
    ------
    : json_data: API response ['items'] = list of videos returned from `get_top_videos_by_category`
    """
    extracted_video_details = []
    for vid in videos : 
        video_id = vid['id']
        # the 'snippet' stores a lot of info about the video
        snip = vid['snippet'] 
        title = snip.get('title')
        description = snip.get('description')
        channel_id = snip.get('channelId')
        channel_name = snip.get('channelTitle')
        tags = snip.get('tags')
        category_id = snip.get('categoryId')
        published_dt = snip.get('publishedAt')

        statistics = vid['statistics']

        # keys that we want formatted for DDB
        extracted_fmt = {
            'video_id' : video_id,
            'title' : title,
            'description' : description,
            'channel_id' : channel_id,
            'channel_name' : channel_name,
            'tags' : tags,
            'statistics' : statistics,
            'category_id' : category_id,
            'published_dt' : published_dt,
            'insert_dt': datetime.utcnow().strftime('%m-%d-%Y')
        }

        extracted_video_details.append(extracted_fmt) #, fmt_ddb
    return extracted_video_details



# TODO - make this into airflow pipeline
def main():
    assert YOUTUBE_API_KEY is not None
    print(YOUTUBE_API_KEY)
    # get transcripts for all categories.
    for cat_id, cat_name in CATEGORIES.items() : 
        logger.info("Category == %s", cat_name)
        data = get_top_videos_by_category(cat_id)
        if data :
            print('Data')
            print(data)
            details_list = extract_video_details(data['items'])
            print(details_list)
        time.sleep(5)




if __name__ == '__main__':
    main()

