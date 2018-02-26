/**
 * This module used in orderReceived.pug
 */
'use strict'

$(document).ready(function () {
  // LoadPayment().then(function(result) {
  //   window._paymentTxn = result
  //   return LoadShoppingCart(result.userId, result.recipientId)
  // }).then(function(result) {
  //   window._shoppingCart = result
  //   return LoadWcOrder()
  // }).then(function(result) {
  //   window._wcOrder = result

    RenderScreen()
    $('.loading_wrapper').hide()
    $('.loaded_wrapper').show()
    SetupUI()
  // }).fail(function(err) {
  //   console.error(err)
  // })
})

// function LoadPayment() {
//   console.log('LoadPayment()')
//   console.assert(window._paymentId)

//   return $.ajax({
//     type: 'GET',
//     url: 'db_loadpaymenttxn',
//     data: {
//       pid: window._paymentId
//     }
//   })
// }

// function LoadShoppingCart(userId, recipientId) {
//   console.log('LoadShoppingCart()')
//   console.assert(userId)
//   console.assert(recipientId)

//   return $.ajax({
//     method: 'GET',
//     url: 'ws/db_loadcart',
//     data: {
//       uid: userId,
//       rid: recipientId
//     }
//   })
// }

// function LoadWcOrder() {
//   console.log('LoadWcOrder()')
//   console.assert(window._paymentTxn.userId)
//   console.assert(window._paymentTxn.recipientId)
//   console.assert(window._paymentTxn.orderId)

//   return $.ajax({
//     method: 'GET',
//     url: 'get_wc_order',
//     data: {
//       uid: window._paymentTxn.userId,
//       rid: window._paymentTxn.recipientId,
//       oid: window._paymentTxn.orderId
//     }
//   })
// }

function RenderScreen() {
  console.log('RenderScreen()')
  console.assert(window._shoppingCart.server_settings.currency)

  var crySts = window._shoppingCart.server_settings.currency

  // var orderDate = new Date(_wcOrder.date_created)
  var subtotal = 0
  for (var i = 0; i < _wcOrder.line_items.length; ++i) {
    var item = _wcOrder.line_items[i]
    subtotal += parseFloat(item.subtotal)
  }
  var orderDate = new Date(_shoppingCart.order_pool.created_at)

  $('#order_no').html(_wcOrder.id)
  $('#order_date').html(orderDate.toLocaleString())
  $('#order_total').html(util.ParseCurrencyToDisp(crySts, parseFloat(_wcOrder.total)))
  $('#payment_method').html(_paymentTxn.payment_method_title)
  $('#order_subtotal').html(util.ParseCurrencyToDisp(crySts, subtotal))
  if (_wcOrder.shipping_lines && _wcOrder.shipping_lines.length > 0)
    $('#order_shipping').html(_wcOrder.shipping_lines[0].method_title)
  $('#order_tax').html(util.ParseCurrencyToDisp(crySts, parseFloat(_wcOrder.total_tax)))
  $('#payment_id').html(_paymentTxn._id)
  $('#order_total2').html(util.ParseCurrencyToDisp(crySts, parseFloat(_wcOrder.total)))
}

function SetupUI() {
  console.log('SetupUI()')
}
