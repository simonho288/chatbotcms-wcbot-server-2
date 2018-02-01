import os
import requests
import time
import logging
import json
import inspect
import traceback
import re

import mod_misc
import mod_database

from requests.auth import HTTPBasicAuth
from requests.utils import quote
from inspect import currentframe, getframeinfo
from woocommerce import API

logger = mod_misc.initLogger(__name__)

class Wc:
  def __init__(self, url, consumer_key, consumer_secret):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(url, str)
    assert isinstance(consumer_key, str)
    assert isinstance(consumer_secret, str)
    # self.url = url
    # self.consumer_key = consumer_key
    # self.consumer_secret = consumer_secret
    self.wcapi = API(
      url=url,
      consumer_key=consumer_key,
      consumer_secret=consumer_secret,
      wp_api=True,
      version="wc/v2",
      timeout=30, # requires especially for WooCommerce connects with Jetpack
      query_string_auth=True
    )
  
  def getGeneralSetting(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    try:
      r = self.wcapi.get("settings/general")
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(str(exp))
      logger.error(traceback.format_exc())
      raise exp

  def getProductsList(self, items_per_page, page_no, category_id=None, tag_id=None):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(items_per_page, int)
    assert isinstance(page_no, int)
    url = "products?per_page={0}&page={1}".format(items_per_page, page_no)
    if category_id is not None:
      url += "&category=" + str(category_id)
    if tag_id is not None:
      url += "&tag=" + str(tag_id)
    try:
      r = self.wcapi.get(url)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(str(exp))
      logger.error(traceback.format_exc())
      raise exp

  def getTagBySlug(self, tag_name):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(tag_name, str)
    url = "products/tags?slug={0}".format(tag_name)
    try:
      r = self.wcapi.get(url)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(str(exp))
      logger.error(traceback.format_exc())
      raise exp

  def getProductDetail(self, product_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(product_id, str)
    url = "products/{0}".format(product_id)
    try:
      r = self.wcapi.get(url)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(traceback.format_exc())
      raise exp

  def getProductCategoriesList(self, items_per_page, page_no):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(items_per_page, int)
    assert isinstance(page_no, int)
    url = "products/categories?per_page={0}&page={1}".format(items_per_page, page_no)
    try:
      r = self.wcapi.get(url)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(traceback.format_exc())
      raise exp

  def searchProductsByName(self, items_per_page, page_no, name):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(items_per_page, int)
    assert isinstance(page_no, int)
    kw_url = quote(name)
    # print("kw_url=" + kw_url)
    url = "products?search={0}&status=publish&per_page={1}&page={2}".format(kw_url, items_per_page, page_no)
    try:
      r = self.wcapi.get(url)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(traceback.format_exc())
      raise exp

  def searchProductsByPriceRange(self, items_per_page, page_no, min_price, max_price):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(items_per_page, int)
    assert isinstance(page_no, int)
    assert min_price is not None or max_price is not None
    # print("kw_url=" + kw_url)
    # url = "products?search={0}&status=publish&per_page={1}&page={2}".format(kw_url, items_per_page, page_no)
    url = "products?"
    if min_price is not None:
      url += "min_price=" + min_price + "&"
    if max_price is not None:
      url += "max_price=" + max_price + "&"
    url += "status=publish&per_page={0}&page={1}".format(items_per_page, page_no)
    try:
      r = self.wcapi.get(url)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(traceback.format_exc())
      raise exp

  def createOrder(self, iinfo, items):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert iinfo is not None
    assert items is not None
    assert iinfo["billing"] is not None
    assert iinfo["billing"]["first_name"] is not None
    assert iinfo["billing"]["last_name"] is not None
    assert iinfo["billing"]["email"] is not None
    assert iinfo["billing"]["phone"] is not None
    assert iinfo["billing"]["address1"] is not None
    # assert iinfo["billing"]["address2"] is not None
    assert iinfo["billing"]["city"] is not None
    assert iinfo["billing"]["state"] is not None
    assert iinfo["billing"]["postal"] is not None
    assert iinfo["billing"]["country"] is not None
    assert iinfo["shipping"] is not None
    assert iinfo["shipping"]["first_name"] is not None
    assert iinfo["shipping"]["last_name"] is not None
    assert iinfo["shipping"]["address1"] is not None
    # assert iinfo["shipping"]["address2"] is not None
    assert iinfo["shipping"]["city"] is not None
    assert iinfo["shipping"]["state"] is not None
    assert iinfo["shipping"]["postal"] is not None
    assert iinfo["shipping"]["country"] is not None
    assert isinstance(items, list)
    for item in items:
      assert item["product_id"] is not None
      assert item["qty"] is not None
      assert item["unit_price"] is not None

    # map to WooCommerce order properties
    # http://woocommerce.github.io/woocommerce-rest-api-docs/#create-an-order
    postData = {
      "set_paid": False,
      "prices_include_tax": False,
      "billing": {
        "first_name": iinfo["billing"]["first_name"],
        "last_name": iinfo["billing"]["last_name"],
        "address_1": iinfo["billing"]["address1"],
        # "address_2": iinfo["billing"]["address2"],
        "city": iinfo["billing"]["city"],
        "state": iinfo["billing"]["state"],
        "postcode": iinfo["billing"]["postal"],
        "country": iinfo["billing"]["country"],
        "email": iinfo["billing"]["email"],
        "phone": iinfo["billing"]["phone"]
      },
      "shipping": {
        "first_name": iinfo["shipping"]["first_name"],
        "last_name": iinfo["shipping"]["last_name"],
        "address_1": iinfo["shipping"]["address1"],
        # "address_2": iinfo["shipping"]["address2"],
        "city": iinfo["shipping"]["city"],
        "state": iinfo["shipping"]["state"],
        "postcode": iinfo["shipping"]["postal"],
        "country": iinfo["shipping"]["country"],
        "email": iinfo["shipping"]["email"],
        "phone": iinfo["shipping"]["phone"]
      },
      "line_items": []
    }
    if "address2" in iinfo["billing"]:
      postData["billing"]["address_2"] = iinfo["billing"]["address2"]
    if "address2" in iinfo["shipping"]:
      postData["shipping"]["address_2"] = iinfo["shipping"]["address2"]
    for item in items:
      postData["line_items"].append({
        "product_id": item["product_id"],
        "quantity": int(item["qty"]),
        "price": float(item["unit_price"])
      })
    url = "orders"
    try:
      r = self.wcapi.post(url, postData)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(traceback.format_exc())
      raise exp

  def getShippingSettings(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    result = []
    r = self.wcapi.get("shipping/zones")
    ship_zones = json.loads(mod_misc.wcCorrectResp(r.text))
    for zone in ship_zones:
      if "_links" in zone: del zone["_links"]
      r = self.wcapi.get("shipping/zones/" + str(zone["id"]) + "/locations")
      locations = json.loads(mod_misc.wcCorrectResp(r.text))
      for loc in locations:
        if "_links" in loc: del loc["_links"]
      r = self.wcapi.get("shipping/zones/" + str(zone["id"]) + "/methods")
      methods = json.loads(mod_misc.wcCorrectResp(r.text))
      methods2 = []
      for method in methods:
        # print("method")
        # print(method)
        if method["enabled"]:
          methods2.append({
            "id": method["id"],
            "title": method["title"],
            "method_id": method["method_id"],
            "method_title": method["method_title"],
            "settings": method["settings"]
          })
      result.append({
        "zone": zone,
        "locations": locations,
        "methods": methods2
      })
    return result

  def updateOrder(self, order_id, update_props):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert order_id is not None
    assert update_props is not None
    url = "orders/" + str(order_id)
    try:
      r = self.wcapi.put(url, update_props)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(traceback.format_exc())
      raise exp

  def getOrder(self, order_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert order_id is not None
    url = "orders/" + str(order_id)
    try:
      r = self.wcapi.get(url)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(traceback.format_exc())
      raise exp

  def deleteOrder(self, order_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(order_id, str)
    url = "orders/" + order_id
    try:
      r = self.wcapi.delete(url)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(traceback.format_exc())
      raise exp

  def getPaymentGateways(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    url = "payment_gateways"
    try:
      r = self.wcapi.get(url)
      return json.loads(mod_misc.wcCorrectResp(r.text))
    except Exception as exp:
      logger.error(traceback.format_exc())
      raise exp

def handleAuthenicate(params):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  this_host = "https://" + SERVER_URL
  store_url = param["wp_host"]
  endpoint = "/wc-auth/v1/authorize"
  params = {
    "app_name": param["app_name"],
    "scope": "read_write",
    "user_id": param["_id"],
    "return_url": param["wp_return_url"],
    "callback_url": this_host + "/authenticate_wc_callback" # wc requires HTTPS
  }
  query_string = json.dumps(params)
  query_string = re.sub(r"%20", "+", query_string)
  auth_url = store_url + endpoint + '?' + query_string
  return auth_url

def handleAuthenicateCallback(params):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  assert isinstance(params["user_id"], str)
  assert isinstance(params["consumer_key"], str)
  assert isinstance(params["consumer_secret"], str)
  fb_page_id = params["user_id"]
  m_db = mod_database.Mdb()
  client_rec = m_db.findClientByFbPageId(fb_page_id)
  client_rec["woocommerce"]["consumer_key"] = params["consumer_key"]
  client_rec["woocommerce"]["consumer_secret"] = params["consumer_secret"]
  client_id = client_rec["client_id"]
  return m_db.replaceClientRecord(client_id, client_rec)
