import logging

def get_logger(name=__name__, level=logging.DEBUG):
  # Create a custom logger
  logger = logging.getLogger(name)
  logger.setLevel(level)

  # Create handlers
  c_handler = logging.StreamHandler()
  f_handler = logging.FileHandler('log.log')
  c_handler.setLevel(logging.DEBUG)
  f_handler.setLevel(logging.DEBUG)

  # Create formatters and add it to handlers
  c_format = logging.Formatter('%(asctime)s %(filename)-18s %(name)-8s %(levelname)-8s: %(message)s')
  f_format = logging.Formatter('%(asctime)s %(filename)-18s %(levelname)-8s: %(message)s')
  c_handler.setFormatter(c_format)
  f_handler.setFormatter(f_format)

  # Add handlers to the logger
  logger.addHandler(c_handler)
  logger.addHandler(f_handler)

  return logger