import os
from dotenv import load_dotenv
from pathlib import Path

ENV_FILE_PATH = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=ENV_FILE_PATH)


# directory definitions
ROOT_DIR = Path(__file__).parent
DATA_DIR = Path(ROOT_DIR / 'data') # os.path.join(ROOT_DIR, 'data')

FEATURES_DIR = Path(ROOT_DIR / 'features') # os.path.join(ROOT_DIR, 'features')
MODELS_DIR = Path(ROOT_DIR / 'models') # os.path.join(ROOT_DIR, 'models')
SRC_DIR = Path(ROOT_DIR / 'src') # os.path.join(ROOT_DIR, 'src')
TESTS_DIR = Path(ROOT_DIR / 'tests') # os.path.join(ROOT_DIR, 'tests')

# secrets
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

#Youtube API Categories
# CATEGORIES = ['', 'Film & Animation', 'Autos & Vehicles', '', '', '', '', '', '', '', 'Music', '', '', '', '', 'Pets & Animals', '', 'Sports', 'Short Movies', 'Travel & Events', 'Gaming', 'Videoblogging', 'People & Blogs', 'Comedy', 'Entertainment', 'News & Politics', 'Howto & Style', 'Education', 'Science & Technology', 'Nonprofits & Activism', 'Movies', 'Anime/Animation', 'Action/Adventure', 'Classics', 'Comedy', 'Documentary', 'Drama', 'Family', 'Foreign', 'Horror', 'Sci-Fi/Fantasy', 'Thriller', 'Shorts', 'Shows', 'Trailers']
CATEGORIES = {
  '1' : "Film & Animation",
  '2' : "Autos & Vehicles",
  '10' : "Music",
  '15' : "Pets & Animals",
  '17' : "Sports",
  '18' : "Short Movies",
  '19' : "Travel & Events",
  '20' : "Gaming",
  '21' : "Videoblogging",
  '22' : "People & Blogs",
  '23' : "Comedy",
  '24' : "Entertainment",
  '25' : "News & Politics",
  '26' : "Howto & Style",
  '27' : "Education",
  '28' : "Science & Technology",
  '29' : "Nonprofits & Activism",
  '30' : "Movies",
  '31' : "Anime/Animation",
  '32' : "Action/Adventure",
  '33' : "Classics",
  '34' : "Comedy",
  '35' : "Documentary",
  '36' : "Drama",
  '37' : "Family",
  '38' : "Foreign",
  '39' : "Horror",
  '40' : "Sci-Fi/Fantasy",
  '41' : "Thriller",
  '42' : "Shorts",
  '43' : "Shows",
  '44' : "Trailers",
}