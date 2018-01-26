import logging
import inspect
import mod_misc

from inspect import currentframe, getframeinfo

logger = mod_misc.initLogger(__name__)
APP_NAME = "WCBOT"

def server_entry(request):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  # print(request.host_url)
  global SERVER_URL
  # will produce https://..../dev
  url = request.url
  if url[:len(url)] == "/": # eliminate last "/"" if exists
    url = url[:len(url) - 1]
  url = url[:url.rfind('/')] # remove /***
  SERVER_URL = url + "/"
  # SERVER_URL = request.host_url # produce  https://.../ only
  if (SERVER_URL == "http://127.0.0.1:5000/"): SERVER_URL = "https://dev-5000.simonho.net/" # Messenger API friendly
  logger.info("SERVER_URL=" + SERVER_URL)