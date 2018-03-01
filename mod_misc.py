import os
import re
import logging
import numbers
import decimal
import babel
import json
import datetime
import random
import time

import mod_global

from babel.numbers import format_number, format_decimal, format_percent, format_currency
from boltons.iterutils import remap

class DecimalEncoder(json.JSONEncoder):
  def default(self, o):
    if isinstance(o, decimal.Decimal):
      if o % 1 > 0:
        return float(o)
      else:
        return int(o)
    return super(DecimalEncoder, self).default(o)

# create logger
# On every function 1st line:
# logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
def initLogger(name):
  logger = logging.getLogger(name)
  # logger.setLevel(logging.DEBUG)
  if mod_global.IS_DEBUG:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.WARN)

  # create console handler and set level to debug
  ch = logging.StreamHandler()
  # ch.setLevel(logging.DEBUG)
  # create formatter
  formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
  # add formatter to ch
  ch.setFormatter(formatter)
  # add ch to logger
  logger.addHandler(ch)
  # func_name = lambda: inspect.stack()[0][3]
  return logger

def rreplace(s, old, new, occurrence):
  """
  Right string replace.
  """
  li = s.rsplit(old, occurrence)
  return new.join(li)

def wcGeneralSettingLookup(gSettings, sid):
  """
  Lookup an ID in WooCommerce general settings.
  """
  assert gSettings is not None
  assert isinstance(sid, str)
  for settings in gSettings:
    if settings["id"] == sid:
      return settings
  return None

def wcMakeCurrencyStr(cur_sts, price, is_show_symb=True):
  """
  Make WooCommerce friendly price with currency defined in Settings.
  """
  assert cur_sts is not None
  assert isinstance(price, numbers.Number)

  # First, make the format
  fmt = "{:,." + cur_sts["num_decimal"] + "f}"
  result = fmt.format(price)
  if cur_sts["thousand_sep"] != ",":
    result = result.replace(",", cur_sts["thousand_sep"])
  if cur_sts["decimal_sep"] != ".":
    result = rreplace(result, ",", cur_sts["thousand_sep"], 1)

  if not is_show_symb:
    return result

  # symbol = currency_symbol_map(cur_sts["value"])
  currency = cur_sts["value"]
  cnum = format_currency(0, currency, locale="en")
  symbol = cnum[:cnum.find('0')] # first char of $0.00
  
  if cur_sts["position"] == "left":
    return symbol + result
  elif cur_sts["position"] == "right":
    return result + symbol
  elif cur_sts["position"] == "left_space":
    return symbol + " " + result
  elif cur_sts["position"] == "right_space":
    return result + " " + symbol
  else:
    raise Exception("Unhandled currency symbol position: " + cur_sts["position"])

def wcCorrectResp(jstr):
  """
  Elinamte all console.log which generate in the WcBot plugin development mode from WooCommerce rest api.
  """
  import mod_global
  if mod_global.IS_DEBUG:
    pos = jstr.rfind("</script>")
    if pos >= 0:
      return jstr[pos + 9:]
  return jstr

def strMakeComma(categories):
  """
  Make comma seperate string i.e: a, b, c
  """
  result = ""
  for catg in categories:
    result += catg["name"] + ", "
  if len(result) > 0:
    result = result[:len(result) - 2]
  return result

def strRemoveMarkup(html):
  """
  Remove all markup tags in a string.
  """
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', html)
  return cleantext

def dumpJsonToFile(obj, fname="temp.json"):
  """
  Dump dictionary to file for debugging.
  Example: mod_misc.dumpJsonToFile(cart_rec)
  """
  with open(fname, 'w') as fp:
    json.dump(obj, fp)
  
def delKeysInDict(obj, keys):
  bad_keys = set(keys)
  drop_keys = lambda path, key, value: key not in bad_keys
  return remap(obj, visit=drop_keys)

def dictToJsonStr(obj):
  s = json.dumps(obj, separators=(",", ":"), cls=DecimalEncoder)
  return re.sub(r'\\"', "'", s) # replace \" -> '

def getPaypalUrlsByMode(mode):
  assert isinstance(mode, str)
  if mode == "sandbox":
    return {
      "nvp_url": "https://api-3t.sandbox.paypal.com/nvp",
      "pp_url": "https://www.sandbox.paypal.com/cgi-bin/webscr"
    }
  else:
    return {
      "nvp_url": "https://api-3t.paypal.com/nvp",
      "pp_url": "https://www.paypal.com/cgi-bin/webscr"
    }

def timestampToString(timestamp):
  assert timestamp is not None
  return datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M")

# Used to remove empty string before save the dictionary to DynamoDb
def remove_empty_string(d):
  if type(d) is dict:
    return dict((k, remove_empty_string(v)) for k, v in d.items() if v and remove_empty_string(v))
  elif type(d) is list:
    return [remove_empty_string(v) for v in d if v and remove_empty_string(v)]
  else:
    return d

def genRandomId():
  return str(round(time.time() * random.randint(1, 1000)))

def isNumeric(s):
  return s.lstrip("-").replace(".", "", 1).isdigit()
