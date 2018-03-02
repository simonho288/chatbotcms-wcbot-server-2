import os
import datetime # datetime.datetime.utcnow()
import time
import pymongo
import inspect
import re
import sys, traceback
import json
import uuid
import ssl
import platform
import requests
# import paypalrestsdk.util as paypal_util

import mod_misc
import mod_global
import mod_messenger
import mod_woocommerce
import mod_shopcart
import mod_database
import mod_payment

from flask import Flask, make_response, request, jsonify, render_template, redirect
from inspect import currentframe, getframeinfo
# from paypalrestsdk import exceptions as paypal_exceptions
# from paypalrestsdk.config import __version__ as paypal_version
# from paypalrestsdk.config import __endpoint_map__ as paypal_endpoint

logger = mod_misc.initLogger(__name__)

class Shopcart:
  def __init__(self):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")

  def handleService(self, name, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    logger.debug("looking up service handler: " + name)
    if name == "db_loadcart":
      return self.doLoadCart(request)
    elif name == "db_savecart":
      return self.doSaveCart(request)
    elif name == "update_order":
      return self.doUpdateOrder(request)
    elif name == "delete_order":
      return self.doDeleteOrder(request)
    elif name == "checkout_submit":
      return self.doCheckoutSubmit(request)
    elif name == "db_loadclient":
      return self.doLoadClient(request)
    elif name == "db_upsertclient":
      return self.doUpsertClient(request)
    elif name == "init_msgr_profile":
      return self.doInitMsgrProfile(request)
    elif name == "send_user_directmsg":
      return self.doSendUserDirectMsg(request)
    elif name == "server_check":
      return self.doServerSideCheck(request)
    elif name == "get_item_stock":
      return self.doGetItemStock(request)
    else:
      raise Exception("Unhandled service: " + name)

  def doLoadCart(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.args["uid"], str)
    assert isinstance(request.args["rid"], str)
    raise Exception("Deprecated!")
    # mDb = mod_database.Mdb()
    # result = mDb.findShopcartByUserAndFbpageid(request.args["uid"], request.args["rid"])
    # if result is not None:
    #   record = result["record"]
    #   return jsonify(record)

  def doLoadClient(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.args["_id"], str)
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientByVerifyToken(request.args["_id"])
    resp = make_response(jsonify(client_rec), 200)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "X-Requested-With"
    return resp

  def doUpsertClient(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    form_data = request.form.to_dict()
    assert isinstance(form_data["_id"], str)
    assert isinstance(form_data["app_name"], str)
    assert isinstance(form_data["form_action"], str)
    assert isinstance(form_data["client_email"], str)
    assert isinstance(form_data["fb_page_id"], str)
    assert isinstance(form_data["fb_page_acctok"], str)
    assert isinstance(form_data["woocommerce_url"], str)
    assert isinstance(form_data["woocommerce_consumer_key"], str)
    assert isinstance(form_data["woocommerce_consumer_secret"], str)
    assert isinstance(form_data["woocommerce_site_name"], str)
    assert isinstance(form_data["version"], str)
    assert isinstance(form_data["plugin_type"], str)
    assert isinstance(form_data["shop_type"], str)
    new_clientrec = {
      "created_at": int(round(time.time() * 1000)),
      "client_id": form_data["_id"],
      "app_name": form_data["app_name"],
      "client_email": form_data["client_email"],
      "fb_page_id": form_data["fb_page_id"],
      "facebook_page": {
        "access_token": form_data["fb_page_acctok"]
      },
      "plugin_type": form_data["plugin_type"],
      "shop_type": form_data["shop_type"],
      "woocommerce": {
        "url": form_data["woocommerce_url"],
        "consumer_key": form_data["woocommerce_consumer_key"],
        "consumer_secret": form_data["woocommerce_consumer_secret"],
        "site_name": form_data["woocommerce_site_name"]
      },
      "version": form_data["version"]
    }
    if form_data["form_action"] == "create":
      new_clientrec["subscribe_date"] = form_data["subscribe_date"]
      new_clientrec["woocommerce"]["consumer_key"] = "-"
      new_clientrec["woocommerce"]["consumer_secret"] = "-"
    m_db = mod_database.Mdb()
    old_clientrec = m_db.findClientByFbPageId(form_data["fb_page_id"])
    if old_clientrec is not None:
      # Remove existing client record if exists
      m_db.deleteClientById(old_clientrec["client_id"])
    m_db.insertClient(new_clientrec)
    resp = make_response(jsonify({"status": True}), 200)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "X-Requested-With"
    return resp

  def doSaveCart(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.json["userId"], str)
    assert isinstance(request.json["recipientId"], str)
    assert request.json["cart"] is not None
    mCart = mod_shopcart.ShoppingCart(request.json["userId"], request.json["recipientId"])
    cart = request.json["cart"]
    if "cart_items" in cart:
      mCart.saveCartItems(cart["cart_items"])
    elif "input_info" in cart:
      mCart.saveCartInputinfo(cart["input_info"])
    elif "ship_info" in cart:
      mCart.saveCartShipinfo(cart["ship_info"])
    else:
      raise Exception("Nothing to be updated")
    return make_response("ok")

  def doUpdateOrder(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.values["userId"], str)
    assert isinstance(request.values["recipientId"], str)
    assert isinstance(request.values["orderId"], str)
    assert isinstance(request.values["updateProps"], str)
    fb_page_id = request.values["recipientId"]
    update_props = json.loads(request.values["updateProps"])
    # verify the "total" is only str
    for method in update_props["shipping_lines"]: assert isinstance(method["total"], str)
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientByFbPageId(fb_page_id)
    wc_rec = client_rec["woocommerce"]
    orderpool_rec = m_db.findOrderPoolById(request.values["orderId"])["doc"]
    props = [
      {
        "key": "shipping_lines",
        "value": update_props["shipping_lines"]
      }
    ]
    m_db.updateOrderPoolById(request.values["orderId"], props)
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    result = m_wc.updateOrder(orderpool_rec["order_id"], update_props)
    return make_response("ok")

  def doDeleteOrder(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    user_id = request.values["uid"]
    fb_page_id = request.values["rid"]
    order_id = request.values["oid"]
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientByFbPageId(fb_page_id)
    wc_rec = client_rec["woocommerce"]
    orderpool_rec = m_db.findOrderPoolById(order_id)["doc"]
    wcorder_id = orderpool_rec["order_id"]
    m_db.deleteOrderPoolById(order_id)
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    m_wc.deleteOrder(str(wcorder_id))
    return make_response("ok")

  def doCheckoutSubmit(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.json["user_id"], str)
    assert isinstance(request.json["recipient_id"], str)
    assert request.json["gateway_settings"] is not None
    assert isinstance(request.json["payment_method"], str)
    assert isinstance(request.json["total"], str)
    assert isinstance(request.json["currency"], str)

    # Pre-save a payment to database
    user_id = request.json["user_id"]
    fb_page_id = request.json["recipient_id"]
    gateway_sts = request.json["gateway_settings"]
    payment_method = request.json["payment_method"]
    total = request.json["total"]
    currency = request.json["currency"]
    paytxn_doc = {
      "user_id": user_id,
      "fb_page_id": fb_page_id,
      "order_id": request.json["order_id"],
      "payment_method": payment_method,
      "payment_method_title": request.json["payment_method_title"],
      "total": total,
      "status": "pending",
      "currency": currency,
      "created_at": int(round(time.time() * 1000)),
      "gateway_settings": gateway_sts
    }
    m_db = mod_database.Mdb()
    rec_id = m_db.savePaymentTransaction(paytxn_doc)
    m_payment = mod_payment.Paygate()
    if payment_method == "paypal":
      return m_payment.doPaymentPaypal(rec_id, total, currency, gateway_sts)
    elif payment_method == "braintree_credit_card":
      assert isinstance(request.json["braintree_nonce"], str)
      bt_nonce = request.json["braintree_nonce"]
      return m_payment.doPaymentBraintreeCC(rec_id, total, currency, gateway_sts, bt_nonce)
    elif payment_method == "stripe":
      assert isinstance(request.json["stripe_token"], str)
      stripe_token = request.json["stripe_token"]
      return m_payment.doPaymentStripe(rec_id, total, currency, gateway_sts, stripe_token)
    elif payment_method == "bacs":
      return m_payment.doPaymentBacs(rec_id, total, currency, gateway_sts)
    elif payment_method == "cheque":
      return m_payment.doPaymentCheque(rec_id, total, currency, gateway_sts)
    elif payment_method == "cod":
      return m_payment.doPaymentCod(rec_id, total, currency, gateway_sts)
    else:
      raise Exception("Unhandled payment_method: " + payment_method)

  def doInitMsgrProfile(self, request):
    """
    Setup Messenger Platform. Usually called by plugin. Ref:
    https://developers.facebook.com/docs/messenger-platform/reference/messenger-profile-api
    To see current whitelisted domains. Check out the curl command in README.md
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    post_data = request.form.to_dict()
    client_id = post_data["clientId"]
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientById(client_id)
    if "domain" in post_data:
      domain = post_data["domain"]
      access_token = client_rec["facebook_page"]["access_token"]
      mod_messenger.setupWhiteListDomains(access_token, [domain])
    resp = make_response("ok", 200)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "X-Requested-With"
    return resp

  def doSendUserDirectMsg(self, request):
    """
    Directly send text message to specify user
    To invoke in Javascript:
      $.ajax({
        type: 'POST',
        url: '/ws/send_user_directmsg',
        data: JSON.stringify({
          user_id: _userId,
          recipient_id: _recipientId,
          msg: 'Hello, world...'
        }),
        contentType: 'application/json'
      })
    """
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    # post_data = request.form.to_dict()
    assert request.json is not None
    post_data = request.json
    assert isinstance(post_data["user_id"], str)
    assert isinstance(post_data["recipient_id"], str)
    assert isinstance(post_data["msg"], str)
    user_id = post_data["user_id"]
    fb_page_id = post_data["recipient_id"]
    msg = post_data["msg"]
    # Retreive client record
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientByFbPageId(fb_page_id)
    acc_tok = client_rec["facebook_page"]["access_token"]
    mod_messenger.sendMessengerTextMessage(acc_tok, user_id, msg)
    resp = make_response("ok", 200)
    return resp

  def doServerSideCheck(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert request.form is not None
    post_data = request.form.to_dict()
    assert isinstance(post_data["client_id"], str)
    client_id = post_data["client_id"]
    print("client_id: " + client_id)
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientById(client_id)
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    shipping_methods = m_wc.getShippingMethods()
    result = []
    for method in shipping_methods:
      if method["id"] == "wc_services_usps":
        result.append({
          "type": "warn",
          "message": "Shipping method 'USPS (WooCommerce Services)' is not support. It will not appears in chatbot built-in shopping cart."
        })
    # Example to add an error message
    # result.append({
    #   "type": "error",
    #   "message": "An error message"
    # })
    resp = make_response(jsonify(result), 200)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "X-Requested-With"
    return resp

  def doGetItemStock(self, request):
    logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
    assert isinstance(request.args["item_id"], str)
    assert isinstance(request.args["fb_page_id"], str)
    fb_page_id = request.args["fb_page_id"]
    item_id = request.args["item_id"]
    m_db = mod_database.Mdb()
    client_rec = m_db.findClientByFbPageId(fb_page_id)
    wc_rec = client_rec["woocommerce"]
    m_wc = mod_woocommerce.Wc(wc_rec["url"], wc_rec["consumer_key"], wc_rec["consumer_secret"])
    stock = m_wc.getProductStock(item_id)
    result = {
      "manage_stock": stock["manage_stock"],
      "stock_quantity": stock["stock_quantity"],
      "in_stock": stock["in_stock"]
    }
    resp = make_response(jsonify(result), 200)
    return resp
