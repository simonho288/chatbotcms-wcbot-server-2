import os
import logging
import inspect
import sys
import traceback
import time

import mod_misc
import mod_messenger
import mod_rivescript
import mod_database
import mod_makewebpage
import mod_webservices
import mod_woocommerce
import mod_payment
import mod_global

from flask import Flask, make_response, Response, request, jsonify, render_template, send_from_directory, redirect
from inspect import currentframe, getframeinfo

logger = mod_misc.initLogger(__name__)
app = Flask(__name__, static_folder="static", static_url_path="/")
app = Flask(__name__)
if os.environ["DEBUG_MODE"] == "1":
  app.debug = True

@app.route("/")
def index():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  mod_global.server_entry(request)
  time.sleep(1)
  return make_response("WcBot is running\n", 200)

# static files
@app.route("/js/<path:path>")
def send_js(path):
  # return send_from_directory("static/js", path)
  path = "static/js/" + path
  print("path=" + path)
  with open(path, "r") as f:
    data = f.read()
    f.close()
    return Response(data, mimetype="application/javascript")

# static files
@app.route("/css/<path:path>")
def send_css(path):
  return send_from_directory("static/css", path)

@app.route("/ping", methods=["GET"])
def ping():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  mod_global.server_entry(request)
  if request.args.get("q") == "chatbotcms-wcbot":
    resp = make_response("pong", 200)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "X-Requested-With"
    return resp
  else:
    time.sleep(3)
    return make_response("Invalid request!\n", 500)

@app.route("/test_db", methods=["GET"])
def test_db():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  mod_global.server_entry(request)
  if request.args.get("q") == "chatbotcms-wcbot":
    try:
      m_mdb = mod_database.Mdb()
      count = m_mdb.getClientsCount()
      resp = make_response("Database connection okay.\n", 200)
      resp.headers["Access-Control-Allow-Origin"] = "*"
      resp.headers["Access-Control-Allow-Headers"] = "X-Requested-With"
      return resp
    except Exception as ex:
      return make_response("Exp: " + str(ex), 200)
  else:
    time.sleep(3)
    return make_response("Invalid request! Missing query string.\n", 500)

@app.route("/test_wc", methods=["GET"])
def test_wc():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  mod_global.server_entry(request)
  if request.args.get("subscribe_vk") is None:
    time.sleep(3)
    return make_response("Invalid request! Missing query string.\n", 500)
  client_id = request.args.get("subscribe_vk")
  m_mdb = mod_database.Mdb()
  client_rec = m_mdb.findClientByVerifyToken(client_id)
  if client_rec is None:
    return make_response("Invalid request! Invalid id", 500)
  wc_rec = client_rec["woocommerce"]
  wc_url = wc_rec["url"]
  m_wc = mod_woocommerce.Wc(wc_url, wc_rec["consumer_key"], wc_rec["consumer_secret"])
  m_wc.getGeneralSetting()
  m_wc.getProductsList(1, 1)
  resp = make_response("WooCommerce connection with '{0}' okay.\n".format(wc_url), 200)
  resp.headers["Access-Control-Allow-Origin"] = "*"
  resp.headers["Access-Control-Allow-Headers"] = "X-Requested-With"
  return resp

@app.route("/webhookfb", methods=["GET", "POST"])
def webhookfb():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  mod_global.server_entry(request)
  mMgr = mod_messenger.Messenger()
  if request.method == "GET":
    result = mMgr.webhookGet(request.args)
    if result is not None:
      return make_response(result)
    else:
      return make_response("Unkown verify token!", 500)
  elif request.method == "POST":
    try:
      result = mMgr.webhookPost(request)
      return make_response(result)
    except:
      logger.error(traceback.format_exc())
      return make_response("")

@app.route("/mwp", methods=["GET"])
def makeWebPage():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  mod_global.server_entry(request)
  m_mwp = mod_makewebpage.Mwp()
  return m_mwp.mapHandler(request)
  # jsonify(...)

# Web services
@app.route("/ws/<name>", methods=["GET", "POST", "PUT", "DELETE"])
def webServices(name):
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  cart_ws = mod_webservices.Shopcart()
  return cart_ws.handleService(name, request)

@app.route("/authenticate_wc", methods=["GET"])
def authenticate_wc():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  mod_global.server_entry(request)
  params = request.args
  redirect_url = mod_woocommerce.handleAuthenicate(params)
  return redirect(redirect_url, 305)

@app.route("/authenticate_wc_callback", methods=["POST"])
def authenticate_wc_callback():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  mod_global.server_entry(request)
  params = request.form
  if request.is_json:
    params = request.json
  if mod_woocommerce.handleAuthenicateCallback(params):
    return make_response("")

# Payment return
@app.route("/payment_return", methods=["GET"])
def paymentReturn():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  m_pg = mod_payment.Paygate()
  result = m_pg.handleReturn(request)
  m_mwp = mod_makewebpage.Mwp()
  return m_mwp.renderOrderReceivedHtml(request, result["paymenttxn"], result["shopcart"], result["wcorder"])

@app.route("/payment_cancel", methods=["GET"])
def paymentCancel():
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  m_pg = mod_payment.Paygate()
  payment_rec = m_pg.handleCancel(request)
  m_mwp = mod_makewebpage.Mwp()
  return m_mwp.doOrderCancelled(request, payment_rec["user_id"], payment_rec["fb_page_id"], payment_rec["order_id"])

@app.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == "__main__":
  logger.debug(str(currentframe().f_lineno) + ":" + inspect.stack()[0][3] + "()")
  app.run(debug=app.debug, port=443, host="127.0.0.1")
  # app.run(debug=app.debug, port=5000, host="127.0.0.1")
