from __future__ import annotations
import requests
from pathlib import Path
import time
from yt_sentiment_analysis.constants import YOUTUBE_API_KEY, CATEGORIES, DATA_DIR
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import Formatter
from datetime import datetime

from yt_sentiment_analysis.utils.decorators import mapper
from yt_sentiment_analysis.utils.get_logger import get_logger
from yt_sentiment_analysis.utils.utils import print_results
from yt_sentiment_analysis.utils.dynamo_db import Dynamo


logger = get_logger(__name__)


class MyCustomFormatter(Formatter):

    def format_transcript(self, video_id: str, transcript, **kwargs):
        # Do your custom work in here, but return a string.
        fmt = {video_id: transcript}
        return self.format_transcripts([fmt], **kwargs)

    def format_transcripts(self, transcripts, **kwargs):
        print('in my formatter')
        print('formatter kwargs')
        print(kwargs)
        # Do your custom work in here to format a list of transcripts,
        # but return a string.
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

                transcript_fmt['video_id'] = id
                transcript_fmt['transcript'] = joined_tr
                # append the single transcript dict to the list of transcripts
                transcripts_fmt.append(transcript_fmt)
        if kwargs.get('as_list'):
            logger.debug('returning transcripts_fmt as list')
            # t0_type = type(transcripts_fmt[0])
            # logger.debug(f'format_transcripts - as_list=True {t0_type}')
            return transcripts_fmt
        logger.debug('returning transcripts_fmt as json str')
        return json.dumps(transcripts_fmt)


def get_top_videos_by_category(category_id: str = None,
                               save: bool = False,
                               max_results: int = 10) -> dict:
    """
    Get the top videos for the specified `category_id`.

    Category IDs for US categories are stored in constants.py CATEGORIES variable.
    Note - some return no response.

    Params
    ------
    : category_id: YouTube API videoCategoryId of videos to get.
    : max_results : Max results
    """
    print(f'>>in {__name__}')
    if category_id is not None:
        assert category_id in list(CATEGORIES.keys()), "enter a valid category_id"
    url = 'https://youtube.googleapis.com/youtube/v3/videos'
    params = {
            'part': ['snippet', 'contentDetails', 'statistics'],
            "chart": "mostPopular",
            "regionCode": "US",
            "key": YOUTUBE_API_KEY,
            "maxResults": max_results,
    }
    # add category_id if it is passed in
    if category_id:
        params["videoCategoryId"] = category_id

    # get the top videos for the category
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        if save:
            if category_id:
                fname = 'ytapiresp_get_top_videos_by_category_{category_id}.json'
                with open(Path(DATA_DIR)/fname, 'w') as fp:
                    json.dump(data, fp)[[]]
            else:
                fname = 'ytapiresp_get_top_videos_by_category.json'
            with open(Path(DATA_DIR)/fname, 'w') as fp:
                json.dump(data, fp)
        return data
    else:
        logger.error("boo!")
        print(r.status_code)
        print(r.text)
        return None


def get_transcripts(video_ids: list,
                    load_filepath: str = None,
                    save_filepath: str = None, **kwargs):
    """
    Get the transcripts for `video_ids` list

    Params:
    ------
    :video_ids : list of video_ids for the youtube video
    :load_filepath (opt): file path to load data from instead.
    :save_filepath (opt): file path to save data to.

    kwargs:
    ------
    as_list: True or False -

    Returns:
    --------
    :json_formatted
    :video_ids_not_found : list

    """

    if load_filepath:
        # If file path is specified, return
        with open(load_filepath, 'r') as f:
            loaded = json.load(f)
            loaded_ids = loaded.keys()
            return loaded, loaded_ids
    transcripts, video_ids_not_found = YouTubeTranscriptApi.get_transcripts(video_ids, continue_after_error=True)
    if save_filepath:
        args_str = '_'.join(video_ids)
        # if a save_filepath is specified, save the data there.
        with open(DATA_DIR / 'test_data' / f'YouTubeTranscriptApi_get_transcripts_{args_str}.json', 'w') as fp:
            json.dump(transcripts, fp)
    formatter = MyCustomFormatter()

    # turns the transcript into a JSON string.
    json_formatted = formatter.format_transcripts(transcripts, **kwargs)
    # Now we can write it out to a file.
    if save_filepath is not None:
        with open(save_filepath, 'w', encoding='utf-8') as json_file:
            json_file.write(json_formatted)
    return json_formatted, video_ids_not_found


@mapper
def extract_video_details(video: dict,
                          format_dynamo=True) -> list[dict]:
    """
    Extract relevant info from the /videos api response (youtube#videoListResponse)

    Params
    ------
    : json_data: API response ['items'] = list of videos returned from
        `get_top_videos_by_category`
    """
    # make sure input is the expected type
    assert video['kind'] == "youtube#video"

    # parse out required variables
    video_id = video['id']
    # the 'snippet' stores a lot of info about the video
    snip = video['snippet']
    title = snip.get('title')
    description = snip.get('description')
    channel_id = snip.get('channelId')
    channel_name = snip.get('channelTitle')
    tags = snip.get('tags')
    category_id = snip.get('categoryId')
    published_dt = snip.get('publishedAt')

    statistics = video['statistics']

    # keys that we want formatted for DDB
    extracted_fmt = {
        'video_id': video_id,
        'title': title,
        'description': description,
        'channel_id': channel_id,
        'channel_name': channel_name,
        'tags': tags,
        'statistics': statistics,
        'category_id': category_id,
        'published_dt': published_dt,
        'insert_dt': datetime.utcnow().strftime('%m-%d-%Y')
    }

    return extracted_fmt


def pipeline():
    assert YOUTUBE_API_KEY is not None
    # initialize Dynamo client
    dynamo = Dynamo()
    # Pipeline

    # 1. for each category in CATEGORIES, get the top_videos_by_category
    invalid_categories = []  # store categories that returned no data
    transc_not_found = []
    # n = 0
    # for cat_id, cat_name in CATEGORIES.items():
    for n, cat_id in enumerate(list(CATEGORIES.keys())[:2]):
        print(f'n is => {n}')
        cat_name = CATEGORIES[cat_id]
        logger.info("Category == %s", cat_name)
        data = get_top_videos_by_category(cat_id)
        if data:
            print('We have data!')
            # 2. Extract the details for each video
            logger.debug(f"2. Extract the details for each video in Category {cat_name} - {cat_id}")
            details_list = extract_video_details(data['items'])
            # 3. Insert all into DDB
            inserted_video_ids = dynamo.insert(details_list)
            logger.debug('Inserted video ids?')
            logger.debug(inserted_video_ids)
            # continue
            # 4. Get transcript for all ^ ids
            transcripts, not_found = get_transcripts(inserted_video_ids, as_list=True)
            transc_not_found.extend(not_found)
            # 5. upsert transcript into existing videos
            us = dynamo.upsert(transcripts)
            logger.debug('Upsert')
            logger.debug(us)
        else:
            logger.error(f"No data for {cat_id}")
            invalid_categories.append(cat_id)
        time.sleep(2)
        n += 1
    print_results(invalid_categories, "Invalid Categories")
    print_results(transc_not_found, "Transcripts Not Found")
    return invalid_categories


# TODO - make this into airflow pipeline
def main():
    pipeline()


if __name__ == '__main__':
    main()
