/**
 * This module used in orderInfoInput.pug
 */
'use strict'

$(document).ready(function () {
  // $.when(LoadShoppingCart(), LoadWcOrder(), LoadWcShipSetting())
  // .done(function(rstCart, rstOrder, rstShipStgs) {
  //   window._shoppingCart = rstCart[0]
    // window._wcOrder = rstOrder[0]
    // window._shipSettings = rstShipStgs[0]

    renderShipInfo()
    CalculateTotal()

    // Hide the loader
    $('.loading_wrapper').hide()
    $('.loaded_wrapper').show()
    SetupUI()
  // }).fail(function(err) {
  //   console.error(err)
  // })
})

function SetupUI() {
  console.log('SetupUI()')

  var $form = $('#shipping_fee_form')
  $form.form({
    on: 'blur',
    inline: true,
    fields: {
      ship_method: ['empty']
    }
  })
  $form.submit(function(evt) {
    evt.preventDefault()
    return false
  })
  $('#btn_proceed').click(onBtnProceed)
  $('#btn_back').click(onBtnBack)
  // $('.dropdown').dropdown()
}

function LoadShoppingCart() {
  console.log('LoadShoppingCart()')
  console.assert(window._userId) // this assigned in shoppingCart.pug
  console.assert(window._recipientId) // this assigned in shoppingCart.pug

  return $.ajax({
    method: 'GET',
    url: 'ws/db_loadcart',
    data: {
      uid: window._userId,
      rid: window._recipientId
    }
  })
}

function LoadWcShipSetting() {
  console.log('LoadWcShipSetting()')
  console.assert(window._userId) // this assigned in shoppingCart.pug
  console.assert(window._recipientId) // this assigned in shoppingCart.pug

  return $.ajax({
    method: 'GET',
    url: 'ws/get_wc_ship_setting',
    timeout: 15000, // 15 sec timeout since its long operation in wc
    data: {
      uid: window._userId,
      rid: window._recipientId
    }
  })
}

// function LoadWcOrder() {
//   console.log('LoadWcOrder()')
//   console.assert(window._orderId)

//   return $.ajax({
//     method: 'GET',
//     url: '/ws/get_wc_order',
//     data: {
//       uid: window._userId,
//       rid: window._recipientId,
//       oid: window._orderId
//     }
//   })
// }

function renderShipInfo() {
  console.log('renderShipInfo()')
  console.assert(window._wcOrder)

  function _appplyNA(val) {
    if (val && val.length > 0)
      return val
    else
      return '--'
  }

  $('#first_name').html(_appplyNA(window._wcOrder.shipping.first_name))
  $('#last_name').html(_appplyNA(window._wcOrder.shipping.last_name))
  $('#address1').html(_appplyNA(window._wcOrder.shipping.address_1))
  $('#address2').html(window._wcOrder.shipping.address_2)
  $('#city').html(_appplyNA(window._wcOrder.shipping.city))
  $('#state').html(_appplyNA(window._wcOrder.shipping.state))
  $('#postcode').html(_appplyNA(window._wcOrder.shipping.postcode))
  $('#country').html(_appplyNA(window._wcOrder.shipping.country))
}

function CalculateTotal() {
  console.log('CalculateTotal()')
  console.assert(window._shoppingCart)

  // Calculate order items total cost & tax
  var total = 0, taxes = 0
  window._wcOrder.line_items.forEach(function(item) {
    total += parseFloat(item.subtotal)
    taxes += parseFloat(item.total_tax)
  })
  window._totalAmount = total
  var disp = util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency, total)
  $('#order_totalamt').html(disp)

  // Find shipping location which matches with order
  var matchedCountry = []
  var locNotCover = null
  for (var i = 0, len = _shipSettings.length; i < len; i++) {
    var shipSts = _shipSettings[i]
    if (shipSts.locations.length === 0) { // when not specify location, it is 'loc not covered by your zone...'
      locNotCover = shipSts
    } else {
      // verify the location
      var isCountryMatch = false, isPostcodeExist = false, isPostcodeMatch = false
      for (var j = 0, len2 = shipSts.locations.length; j < len2; j++) {
        var loc = shipSts.locations[j]
        if (loc.type === 'country') {
          if (loc.code === _wcOrder.shipping.country) {
            isCountryMatch = true
          }
        } else if (loc.type === 'postcode') {
          isPostcodeExist = true
          if (IsPostcodeMatch(loc.code, _wcOrder.shipping.postcode)) {
            isPostcodeMatch = true
          }
        }
      }
      if (isCountryMatch) {
        if (!isPostcodeExist) {
          matchedCountry.push(shipSts)
        } else {
          if (isPostcodeMatch) {
            matchedCountry.push(shipSts)
          }
        }
      }
    }
  }
  console.assert(locNotCover != null) // 'locations not covered' object must exist. If else, check WooCommerce->Settings->Shipping->Shipping Zones->Locations not covered by your other zones

  var markup = '<option value="">Please select</option>'
  if (matchedCountry.length === 0) {
    // No matched country, use 'location not cover'
    // var zoneName = locNotCover.zone.name
    var zoneName = 'Locations not covered'
    markup += MethodsToSelectOptionsMarkup(zoneName, locNotCover.methods)
  } else {
    // Make shipping methods as select option(s)
    for (var i = 0, len = matchedCountry.length; i < len; ++i) {
      var country = matchedCountry[i]
      var zoneName = country.zone.name
      markup += MethodsToSelectOptionsMarkup(zoneName, country.methods)
    }
  }
  var $select = $('[name="ship_method"]')
  $select.html(markup)
  
  var disp = util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency, taxes)
  $('#order_totaltax').html(disp)
} // CalculateTotal()

function MethodsToSelectOptionsMarkup(zoneName, methods) {
  console.log('MethodsToSelectOptionsMarkup()')
  console.assert(window._shoppingCart.server_settings.currency)

  var crySts = window._shoppingCart.server_settings.currency
  var markup = ''
  for (var i = 0; i < methods.length; ++i) {
    var method = methods[i]
    var cost, title
    title = zoneName + ': '
    switch (method.method_id) {
      case 'free_shipping':
        // Parsing the min. requirement
        cost = 0 // suppose cost is zero initially
        if (method.settings.requires.value === 'min_amount') {
          var minAmount = parseFloat(method.settings.min_amount.value)
          if (window._totalAmount < minAmount) {
            continue // not eligible for free-shipping
          }
        }
        title += method.method_title
        title += ': Fee ' + util.ParseCurrencyToDisp(crySts, 0)
        break
      case 'flat_rate':
        cost = ParseAndCalcShipCost(method.settings.cost.value)
        title += method.method_title + ': Fee ' + util.ParseCurrencyToDisp(crySts, cost)
        break
      case 'local_pickup':
        cost = ParseAndCalcShipCost(method.settings.cost.value)
        title += method.method_title + ': Fee ' + util.ParseCurrencyToDisp(crySts, cost)
        break
      default:
        $.alert({
          type: 'red',
          useBootstrap: false,
          title: "Error",
          content: 'Unhandled shipping method: ' + method.method_id
        })
    }
    markup += '<option '
    markup += 'value="' + method.method_id + '"'
    markup += 'data-title="' + method.method_title + '"'
    markup += 'data-cost="' + cost + '">'
    markup += title
    markup += '</option>'
  }

  return markup
}

function IsPostcodeMatch(wcPostcode, userPostcode) {
  console.log('IsPostcodeMatch()')
  var upc = userPostcode.toLowerCase().trim()
  var wpcs = wcPostcode.toLowerCase().split('-')
  if (wpcs.length === 1) {
    return wpcs[0].trim() === upc
  } else if (wpcs.length === 2) {
    var nwpcs0 = parseInt(wpcs[0].trim())
    var nwpcs1 = parseInt(wpcs[1].trim())
    if (nwpcs0 > nwpcs1) {
      var t = nwpcs1
      nwpcs1 = nwpcs0
      nwpcs0 = t
    }
    upc = parseInt(upc)
    return (upc >= nwpcs0) && (upc <= nwpcs1)
  } else {
    $.alert({
      type: 'red',
      useBootstrap: false,
      title: 'Error',
      content: 'Invalid WC Postcode: ' + wcPostcode
    })
  }
  return false
}

// JS expression parser: https://stackoverflow.com/questions/23325832/parse-arithmetic-expression-with-javascript
// WooCommerce cost examples: https://docs.woocommerce.com/document/flat-rate-shipping/
function ParseAndCalcShipCost(val) {
  console.log('ParseAndCalcShipCost()')

  if (val == null || val == '')
    return 0

  var expression = val.toLowerCase().replace(/&#39;/g, '"')

  // var expression = '20 + [ fee percent="10" min_fee="4" ]'
  // var expression = '20 + [ qty]*10'
  // var expression = '[qty] * 10 + [fee percent="10" min_fee="4"]'
  // var expression = '10 + (1 + 2) * [qty]'

  return ParseWithLexer(expression) // see parseShipping.js
} // ParseAndCalcShipCost()

function EnableAllButtons(isEnable) {
  if (isEnable) {
    $('#btn_proceed').removeClass('disabled loading')
    $('#btn_back').removeClass('disabled loading')
  } else {
    $('#btn_proceed').addClass('disabled loading')
    $('#btn_back').addClass('disabled loading')
  }
}

function onBtnBack(evt) {
  console.log('onBtnBack()')

  evt.preventDefault()

  EnableAllButtons(false)

  $.ajax({
    type: 'DELETE',
    url: 'ws/delete_order',
    data: {
      oid: window._orderId,
      uid: window._userId,
      rid: window._recipientId
    }
    // dataType: 'json',
  }).done(function (result) {
    console.log(result)
    if (result === 'ok') {
      window.location.href = 'mwp?page=orderInfoInput&oid=' + window._orderId + '&uid=' + window._userId + '&rid=' + window._recipientId
    }
  }).fail(function(err, result, xhr) {
    EnableAllButtons(true)
    $.alert({
      type: 'red',
      useBootstrap: false,
      title: err,
      content: xhr.responseText,
    })
  })
}

function onBtnProceed(evt) {
  console.log('onBtnProceed()')
  
  if ($('#shipping_fee_form').form('validate form')) {
    EnableAllButtons(false)

    $.when(
      SaveCart(),
      UpdateWcOrder()
    ).done(function(result1, result2) {
      if (result1[1] === 'success' && result2[1] === 'success') {
        window.location.href = 'mwp?page=orderReview&oid=' + window._orderId + '&uid=' + window._userId + '&rid=' + window._recipientId
      }
    }).fail(function(xhr, status, err) {
      EnableAllButtons(true)
      $.alert({
        type: 'red',
        useBootstrap: false,
        title: err,
        content: xhr.responseText,
      })
    })
  }
}

function SaveCart() {
  console.log('SaveCart()')
  console.assert(window._wcOrder.id != null)

  // No need to save these props
  delete window._shoppingCart.input_info
  delete window._shoppingCart.cart_items
  delete window._shoppingCart.server_settings
  delete window._shoppingCart.order_pool

  // But need to save 'ship_info'
  var $select = $('[name="ship_method"]')
  console.assert($select.find(':selected').data('cost') != null)
  console.assert($select.val() != null)
  window._shoppingCart.ship_info = {
    wc_order_id: window._wcOrder.id.toString(),
    method: $select.val(),
    cost: $select.find(':selected').data('cost').toString()
  }

  return $.ajax({
    type: 'POST',
    url: 'ws/db_savecart',
    data: JSON.stringify({
      userId: window._userId,
      recipientId: window._recipientId,
      cart: window._shoppingCart
    }),
    contentType: 'application/json'
  })
}

// Update WC order to add shipping_lines
function UpdateWcOrder() {
  console.log('UpdateWcOrder()')
  console.assert(window._wcOrder.id != null)

  var $select = $('[name="ship_method"]').find(':selected')
  var props = {
    shipping_lines: [
      {
        method_id: $select.val(),
        method_title: $select.data('title'),
        total: numeral($select.data('cost')).format('0.00')
      }
    ]
  }

  return $.ajax({
    type: 'PUT',
    url: 'ws/update_order',
    // headers: { 'Content-Type': 'application/json' },
    data: {
      userId: window._userId,
      recipientId: window._recipientId,
      orderId: window._orderId,
      updateProps: JSON.stringify(props)
    }
  })
}
