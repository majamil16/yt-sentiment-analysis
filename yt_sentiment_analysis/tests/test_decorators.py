import unittest
# import json

# from yt_sentiment_analysis.constants import DATA_DIR
# from yt_sentiment_analysis.utils.dynamo_db import Dynamo
from yt_sentiment_analysis.utils.get_logger import get_logger
# from datetime import datetime
# from moto import mock_dynamodb
from yt_sentiment_analysis.utils.decorators import mapper2
logger = get_logger(__name__)


class MappedObject(object):

    def __init__(self) -> None:
        self.name = "Tester"

    @mapper2
    def len_of_stuff(stuff, more_stuff='2'):
        """ returns len of `stuff`."""
        print('in len_of_stuff')
        print('stuff:')
        print(stuff)
        return len(stuff.keys())


@mapper2
def print_dict_keys(d: dict):
  """
  pass in d. if d is a singleton, print its keys.
  if d is a list of dicts, return list of printed keys.
  """
  joined_str = "_".join([k for k in d.keys()])
  print(joined_str)
  return joined_str


@unittest.skip("Skip these tests")
class TestDecorator(unittest.TestCase):
    def setUp(self) -> None:
        print('setting up')

    def test_mapper_with_list(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"c": 1, "d": 2, "e": 3}

        mapped_result = print_dict_keys([d1, d2])
        self.assertEqual(mapped_result, ["a_b", "c_d_e"])

    def test_mapper_with_single(self):
        d1 = {"a": 1, "b": 2}

        mapped_result = print_dict_keys(d1)
        self.assertEqual(mapped_result, "a_b")

    def test_mapper_with_instance_method(self):
        mo = MappedObject()
        d1 = {"a": 1, "b": 2}
        mapped_result = mo.len_of_stuff(d1, 99)
        self.assertEqual(mapped_result, 2)

