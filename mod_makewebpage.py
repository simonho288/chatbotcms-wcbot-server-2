"""
Notes: Most operation of every webpage is to prefetch the data and makes it into JSON string then pass to Flask template for rendering. For instance:
m_cart = mod_shopcart.ShoppingCart(user_id, fb_page_id)
m_cart.loadFromDatabase()
cart_rec = m_cart.getRecord()
cart_str = mod_misc.dictToJson(cart_rec)
...
  return render_template(XXX, shopcart=cart_str, ...)

"""
import os
import datetime # datetime.datetime.utcnow()
import time
import pymongo
import inspect
import re
import json
import sys, traceback

import mod_misc
import mod_global
import mod_messenger
import mod_woocommerce
import mod_shopcart
import mod_database
import mod_payment

from inspect import currentframe, getframeinfo
from flask import Flask, make_response, request, jsonify, render_template
from html import escape

logger = mod_misc.initLogger(__name__)

class Mwp:
  def __init__(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")

  def mapHandler(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert request is not None
    page = request.args.get("page")
    if page == "shopCart":
      return self.doShoppingCart(request)
    elif page == "checkout":
      return self.doCheckout(request)
    elif page == "paymentFailure":
      return self.doPaymentFailure(request)
    elif page == "orderInfoInput":
      return self.doOrderInfoInput(request)
    elif page == "orderShipping":
      return self.doOrderShipping(request)
    elif page == "orderReview":
      return self.doOrderReview(request)
    elif page == "orderPayment":
      return self.doOrderPayment(request)
    # elif page == "orderReceived":
    #   rst = self.changeOrderStatus(request.args.get("pid"))
    #   return self.renderOrderReceivedHtml(request, rst["paymenttxn"], rst["shopcart"], rst["wcorder"])
    else:
      raise Exception("Unhandled page: " + page)

  # def changeOrderStatus(self, payment_id):
  #   logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  #   assert isinstance(payment_id, str)
  #   m_db = mod_database.Mdb()
  #   payment_rec = m_db.findPaymentTxnById(payment_id)
  #   # result_txn = self.callPaypalNVPGetCompleteTxn(mode, api_username, api_password, api_signature, token, payer_id, payment_rec["total"], payment_rec["currency"])
  #   # m_db.setPaymentGatewayTxn(payment_id, result_txn)
  #   client_rec = m_db.findClientByFbPageId(payment_rec["fb_page_id"])
  #   m_cart = mod_shopcart.ShoppingCart(payment_rec["user_id"], payment_rec["fb_page_id"])
  #   m_cart.loadFromDatabase()
  #   orderpool_id = payment_rec["order_id"]
  #   orderpool_rec = m_db.findOrderPoolById(orderpool_id)
  #   wcorder_id = str(orderpool_rec["order_id"])
  #   wc_rec = client_rec["woocommerce"]
  #   m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
  #   wcorder = m_wc.getOrder(wcorder_id)
  #   return {
  #     "paymenttxn": payment_rec,
  #     "shopcart": m_cart.getRecord(),
  #     "wcorder": m_wc.getOrder(wcorder_id)
  #   }

  def doShoppingCart(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.args.get("uid"), str)
    assert isinstance(request.args.get("rid"), str)
    user_id = request.args.get("uid")
    fb_page_id = request.args.get("rid")
    order_id = request.args.get("oid")
    if order_id is None: order_id = ""
    # prefetch server settings
    mDb = mod_database.Mdb()
    client_rec = mDb.findClientByFbPageId(fb_page_id)
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    json_gs = m_wc.getGeneralSetting()
    settingCountry = mod_misc.wcGeneralSettingLookup(json_gs, "woocommerce_default_country")
    settingCurrency = mod_misc.wcGeneralSettingLookup(json_gs, "woocommerce_currency")
    settingCurPos = mod_misc.wcGeneralSettingLookup(json_gs, "woocommerce_currency_pos")
    thouSep = mod_misc.wcGeneralSettingLookup(json_gs, "woocommerce_price_thousand_sep")
    decSep = mod_misc.wcGeneralSettingLookup(json_gs, "woocommerce_price_decimal_sep")
    numDec = mod_misc.wcGeneralSettingLookup(json_gs, "woocommerce_price_num_decimals")
    # Remove some useless properties
    del settingCountry["_links"]
    del settingCountry["description"]
    del settingCountry["tip"]
    del settingCurrency["description"]
    del settingCurrency["type"]
    del settingCurrency["default"]
    del settingCurrency["tip"]
    del settingCurrency["_links"]
    settingCurrency["symbolPos"] = settingCurPos["value"] # but add currency pos in there. Values maybe left, right, left_space, right_space
    settingCurrency["thousandSep"] = thouSep["value"]
    settingCurrency["decimalSep"] = decSep["value"]
    settingCurrency["numDecimal"] = numDec["value"]
    cart = mod_shopcart.ShoppingCart(user_id, fb_page_id, order_id=order_id)
    cart.loadFromDatabase()
    cart.saveServerSettings({ # Append server setting to shopping cart record
      "country": settingCountry,
      "currency": settingCurrency
    })
    cart_str = mod_misc.dictToJsonStr(cart.getRecord())
    return render_template("shoppingCart.html", userId=user_id, recipientId=fb_page_id, orderId=order_id, cart=cart_str)

  def doCheckout(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    raise Exception("Not implemented!")

  def renderOrderReceivedHtml(self, request, paymenttxn, shopcart, wcorder):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.args.get("pid"), str)
    assert paymenttxn is not None
    assert shopcart is not None
    assert wcorder is not None
    cart_str = mod_misc.dictToJsonStr(shopcart)
    paymenttxn_str = mod_misc.dictToJsonStr(paymenttxn)
    wcorder_str = mod_misc.dictToJsonStr(wcorder)
    return render_template("orderReceived.html", shopcart=cart_str, paymenttxn=paymenttxn_str, wcorder=wcorder_str)

  def doPaymentFailure(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    raise Exception("Not implemented!")

  def doOrderInfoInput(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.args.get("uid"), str)
    assert isinstance(request.args.get("rid"), str)
    user_id = request.args.get("uid")
    fb_page_id = request.args.get("rid")
    order_id = request.args.get("oid")
    m_db = mod_database.Mdb()
    if order_id is None:
      order_id = ""
    m_cart = mod_shopcart.ShoppingCart(user_id, fb_page_id)
    m_cart.loadFromDatabase()
    cart_rec = m_cart.getRecord()
    cart_str = mod_misc.dictToJsonStr(cart_rec)
    return render_template("orderInfoInput.html", userId=user_id, recipientId=fb_page_id, orderId=order_id, cart=cart_str)

  def delWcOrderShipping(self, wcshippings):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert wcshippings is not None
    wcshippings = mod_misc.delKeysInDict(wcshippings, ["description", "tip"])
    # for shipping in wcshippings:
    #   for method in shipping["methods"]:
    #     if "cost" in method["settings"]:
    #       del method["settings"]["cost"]["description"]
    #       del method["settings"]["cost"]["tip"]
    #     if "min_amount" in method["settings"]:
    #       del method["settings"]["min_amount"]["description"]
    #       del method["settings"]["min_amount"]["tip"]
    #     if "title" in method["settings"]:
    #       del method["settings"]["title"]["description"]
    #       del method["settings"]["title"]["tip"]

  def doOrderShipping(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.args.get("uid"), str)
    assert isinstance(request.args.get("rid"), str)
    user_id = request.args.get("uid")
    fb_page_id = request.args.get("rid")
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientByFbPageId(fb_page_id)
    wc_rec = client_rec["woocommerce"]
    wc_url = wc_rec["url"]
    wc_con_key = wc_rec["consumer_key"]
    wc_con_sec = wc_rec["consumer_secret"]
    m_wc = mod_woocommerce.Wc(wc_url, wc_con_key, wc_con_sec)
    m_cart = mod_shopcart.ShoppingCart(user_id, fb_page_id)
    m_cart.loadFromDatabase()
    cart_rec = m_cart.getRecord()
    cart_str = mod_misc.dictToJsonStr(cart_rec)
    wcorder = m_cart.createWcOrder(wc_url, wc_con_key, wc_con_sec)
    wcorder = mod_misc.delKeysInDict(wcorder, ["_links"])
    order_pool = m_db.saveOrderToPool(user_id, fb_page_id, wcorder)
    m_cart.saveOrderPool(order_pool)
    # direct pass the wcorder as Json string
    wcorder_str = mod_misc.dictToJsonStr(wcorder)
    wcshippings = m_wc.getShippingSettings()
    self.delWcOrderShipping(wcshippings)
    wcshipping_str = mod_misc.dictToJsonStr(wcshippings)
    return render_template("orderShipping.html", userId=user_id, recipientId=fb_page_id, orderId=order_pool["id"], shopcart=cart_str, wcorder=wcorder_str, wcshipping=wcshipping_str)

  def doOrderReview(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.args.get("uid"), str)
    assert isinstance(request.args.get("rid"), str)
    assert isinstance(request.args.get("oid"), str)
    user_id = request.args.get("uid")
    fb_page_id = request.args.get("rid")
    order_id = request.args.get("oid")
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientByFbPageId(fb_page_id)
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    m_cart = mod_shopcart.ShoppingCart(user_id, fb_page_id)
    m_cart.loadFromDatabase()
    cart_rec = m_cart.getRecord()
    cart_str = json.dumps(cart_rec, separators=(",", ":"))
    orderpool_rec = m_db.findOrderPoolById(order_id)["doc"]
    wcorder = m_wc.getOrder(orderpool_rec["order_id"])
    wcorder_str = mod_misc.dictToJsonStr(wcorder)
    return render_template("orderReview.html", userId=user_id, recipientId=fb_page_id, orderId=order_id, shopcart=cart_str, wcorder=wcorder_str)

  def doOrderPayment(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.args.get("uid"), str)
    assert isinstance(request.args.get("rid"), str)
    assert isinstance(request.args.get("oid"), str)
    user_id = request.args.get("uid")
    fb_page_id = request.args.get("rid")
    order_id = request.args.get("oid")
    return self.genPaymentScreen(user_id, fb_page_id, order_id)

  # shared by doOrderPayment() & doOrderCancelled()
  def genPaymentScreen(self, user_id, fb_page_id, order_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert request is not None
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert isinstance(order_id, str)
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientByFbPageId(fb_page_id)
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    m_cart = mod_shopcart.ShoppingCart(user_id, fb_page_id)
    m_cart.loadFromDatabase()
    cart_rec = m_cart.getRecord()
    cart_str = mod_misc.dictToJsonStr(cart_rec)
    orderpool_rec = m_db.findOrderPoolById(order_id)["doc"]
    wcorder = m_wc.getOrder(orderpool_rec["order_id"])
    wcorder_str = mod_misc.dictToJsonStr(wcorder)
    m_pg = mod_payment.Paygate()
    m_pg.initPaymentGateways(m_wc)
    wcpaygates = m_pg.getRawPaymentGateways() # Get processed of all gateways
    wcpaygates = mod_misc.delKeysInDict(wcpaygates, ["tip", "_links", "method_description", "method_title", "label"])
    wcpaygates_str = mod_misc.dictToJsonStr(wcpaygates)
    btrst = m_pg.createBraintreeClientToken()
    stripkey = m_pg.getStripePublishKey()
    return render_template("orderPayment.html", userId=user_id, recipientId=fb_page_id, orderId=order_id, stripePublishKey=stripkey, braintreeClientToken=btrst["clientToken"], braintreeMode=btrst["mode"], shopcart=cart_str, wcorder=wcorder_str, wcpaygates=wcpaygates_str)

  def doOrderCancelled(self, request, user_id, fb_page_id, order_id):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert request is not None
    assert isinstance(user_id, str)
    assert isinstance(fb_page_id, str)
    assert isinstance(order_id, str)
    return self.genPaymentScreen(user_id, fb_page_id, order_id)

