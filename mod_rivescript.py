import re
import os
import logging
import inspect
import rivescript

import mod_misc

from inspect import currentframe, getframeinfo

logger = mod_misc.initLogger(__name__)

logger.debug("rivescript module loaded")

class Nls:
  def __init__(self, user_id, fb_page_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    rsbot = rivescript.RiveScript(utf8=True)
    rsbot.unicode_punctuation = re.compile(r'[,!?;:]') # re.compile(r'[.,!?;:]')
    rsbot.load_directory("./rsBrainFiles")
    rsbot.sort_replies()
    rsbot.set_uservar(user_id, "fb_page_id", fb_page_id)
    self.rsbot = rsbot

  def getReply(self, userId, message=None, sticker_id=None):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(userId, str)
    if sticker_id is not None:
      return self.replySticker(sticker_id)
    elif message is not None:
      return self.rsbot.reply(userId, message)

  def replySticker(self, sticker_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(sticker_id, int)
    if sticker_id == 369239263222822:
      return ":)"
    else:
      return "?"
    
  def getUserVars(self, userId):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(userId, str)
    return self.rsbot.get_uservars(userId)

  def setUserVar(self, userId, name, value):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(userId, str)
    assert isinstance(name, str)
    self.rsbot.set_uservar(userId, name, value)

  def setUserVars(self, userId, usr_vars):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(userId, str)
    assert usr_vars is not None
    self.rsbot.set_uservars(userId, usr_vars)

  def setSubroutines(self, wc_bot):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert wc_bot is not None
    self.rsbot.set_subroutine("rs_find_products", wc_bot.rsSubFindProducts)
    self.rsbot.set_subroutine("rs_list_product_price_under", wc_bot.rsSubProductsPriceBelow)
    self.rsbot.set_subroutine("rs_list_product_price_above", wc_bot.rsSubProductsPriceAbove)
    self.rsbot.set_subroutine("rs_list_product_price_range", wc_bot.rsSubProductsPriceRange)


