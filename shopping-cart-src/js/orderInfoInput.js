/**
 * This module used in orderInfoInput.pug
 */
'use strict'

$(document).ready(function () {
  // LoadShoppingCart().done(function(result) {
  //   window._shoppingCart = result
    CalcOrderTotal()
    ExtractCountries()
    SetupBillingForm()
    SetupShippingForm()
    // LoadWcOrderIfExists()
    SetupInputInfo()
    SetupUI()
  // }).fail(function(err) {
  //   alert(err.statusText)
  // })
})

function SetupInputInfo() {
  console.log('SetupInputInfo()')

  // No customer info input before?
  if (window._shoppingCart.input_info == null) {
    return
  }

  var $billing = $('#billing_form')
  var $shipping = $('#shipping_form')

  var billing = window._shoppingCart.input_info.billing
  $billing.find('[name="first_name"]').val(billing.first_name)
  $billing.find('[name="last_name"]').val(billing.last_name)
  $billing.find('[name="email"]').val(billing.email)
  $billing.find('[name="phone"]').val(billing.phone)
  $billing.find('[name="address1"]').val(billing.address1)
  $billing.find('[name="address2"]').val(billing.address2)
  $billing.find('[name="city"]').val(billing.city)
  $billing.find('[name="state"]').val(billing.state)
  $billing.find('[name="postal"]').val(billing.postal)
  $billing.find('[name="country"]').dropdown('set selected', billing.country)
  OnFormCountryChanged($billing, billing.country)
  $billing.find('[name="state"]').dropdown('set selected', billing.state)

  var shipping = window._shoppingCart.input_info.shipping
  $shipping.find('[name="first_name"]').val(shipping.first_name)
  $shipping.find('[name="last_name"]').val(shipping.last_name)
  $shipping.find('[name="address1"]').val(shipping.address1)
  $shipping.find('[name="address2"]').val(shipping.address2)
  $shipping.find('[name="city"]').val(shipping.city)
  $shipping.find('[name="postal"]').val(shipping.postal)
  $shipping.find('[name="country"]').dropdown('set selected', shipping.country)
  OnFormCountryChanged($shipping, shipping.country)
  $shipping.find('[name="state"]').dropdown('set selected', shipping.state)

  if (billing.first_name === shipping.first_name
    && billing.last_name === shipping.last_name
    && billing.address1 === shipping.address1
    && billing.address2 === shipping.address2
    && billing.city === shipping.city
    && billing.state === shipping.state
    && billing.postal === shipping.postal
    && billing.country === shipping.country)
  {
    $('[name="same_as_billing"]').prop('checked', 'checked')
    $shipping.find('input').each(function (elem) {
      $(this).prop('disabled', true)
    })
    $shipping.find('.dropdown').each(function (elem) {
      $(this).addClass('disabled')
    })
  }
}

function SetupUI() {
  console.log('SetupUI()')
  // setup semnatic-ui search dropdown
  $('.ui.search.dropdown').dropdown()
  // $('.ui.search.dropdown').dropdown({
  //   fullTextSearch: true
  // })
  $('.ui.checkbox').checkbox()

  $('#btn_proceed').click(onBtnProceed)
  $('#btn_back').click(onBtnBack)

  $('[name="same_as_billing"]').change(onCbSameAsBilling)

  $('#billing_form [name="country"]').on('change', function (evt) {
    OnFormCountryChanged($('#billing_form'), evt.target.value)
  })

  $('#shipping_form [name="country"]').on('change', function (evt) {
    OnFormCountryChanged($('#shipping_form'), evt.target.value)
  })

  // Hide the loading screen
  $('.loading_wrapper').hide()
  $('.loaded_wrapper').show()
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

function CalcOrderTotal() {
  console.log('CalcOrderTotal()')

  var total = 0
  $.each(window._shoppingCart.cart_items, function (index, item) {
    total += item._qty * item._unitPrice
  })
  var disp = util.ParseCurrencyToDisp(window._shoppingCart.server_settings.currency, total)
  $('#order_total').html(disp)
  $('#total_div').show()
}

// function LoadWcOrderIfExists() {
//   console.log('LoadWcOrderIfExists()')

//   if (window._orderId == null || window._orderId == '') {
//     $('.loading_wrapper').hide()
//     $('.loaded_wrapper').show()
//     return
//   }

//   $.ajax({
//     method: 'GET',
//     url: '/ws/get_wc_order',
//     data: {
//       oid: window._orderId,
//       uid: window._userId,
//       rid: window._recipientId
//     }
//   }).done(function(result) {
//     // oppsite to onBtnProceed()
//     var $form = $('#billing_form')
//     $form.find('[name="first_name"]').val(result.billing.first_name)
//     $form.find('[name="last_name"]').val(result.billing.last_name)
//     $form.find('[name="email"]').val(result.billing.email)
//     $form.find('[name="phone"]').val(result.billing.phone)
//     $form.find('[name="address1"]').val(result.billing.address_1)
//     $form.find('[name="address2"]').val(result.billing.address_2)
//     $form.find('[name="city"]').val(result.billing.city)
//     $form.find('[name="postal"]').val(result.billing.postcode)
//     $form.find('[name="country"]').dropdown('set selected', result.billing.country)
//     OnFormCountryChanged($form, result.billing.country)
//     $form.find('[name="state"]').dropdown('set selected', result.billing.state)

//     var $form = $('#shipping_form')
//     $form.find('[name="first_name"]').val(result.shipping.first_name)
//     $form.find('[name="last_name"]').val(result.shipping.last_name)
//     $form.find('[name="address1"]').val(result.shipping.address_1)
//     $form.find('[name="address2"]').val(result.shipping.address_2)
//     $form.find('[name="city"]').val(result.shipping.city)
//     $form.find('[name="postal"]').val(result.shipping.postcode)
//     $form.find('[name="country"]').dropdown('set selected', result.shipping.country)
//     OnFormCountryChanged($form, result.shipping.country)
//     $form.find('[name="state"]').dropdown('set selected', result.shipping.state)

//     if (result.billing.first_name === result.shipping.first_name
//         && result.billing.last_name === result.shipping.last_name
//         && result.billing.address_1 === result.shipping.address_1
//         && result.billing.address_2 === result.shipping.address_2
//         && result.billing.city === result.shipping.city
//         && result.billing.state === result.shipping.state
//         && result.billing.postcode === result.shipping.postcode
//         && result.billing.country === result.shipping.country) {
//       $('[name="same_as_billing"]').prop('checked', 'checked')
//       $form.find('input').each(function (elem) {
//         $(this).prop('disabled', true)
//       })
//       $form.find('.dropdown').each(function (elem) {
//         $(this).addClass('disabled')
//       })
//     }

//     $('.loading_wrapper').hide()
//     $('.loaded_wrapper').show()
//   })
// }

// Extract country & state structure from WooCommerce to this webpage
function ExtractCountries() {
  console.log('ExtractCountries()')
  console.assert(window._shoppingCart)
  console.assert(window._shoppingCart.server_settings)
  console.assert(window._shoppingCart.server_settings.country)
  console.assert(window._shoppingCart.server_settings.country.options)

  var countries = {}
  var states = []

  $.each(window._shoppingCart.server_settings.country.options, function(code, name) {
    // e.g.: { "AO:BGO": "Angola - Bengo" }
    var cparts = code.split(':')
    var ccode = cparts[0]
    var nparts = name.split(' - ')
    var cname = nparts[0]

    if (countries[ccode] == null) {
      countries[ccode] = { name: cname }
      if (cparts.length > 1) {
        countries[ccode].states = {}
        countries[ccode].states[cparts[1]] = nparts[1]
      }
    } else {
      countries[ccode].states[cparts[1]] = nparts[1]
    }
  })
  window._countries = countries
}

function onCbSameAsBilling(evt) {
  console.log('onCbSameAsBilling()', this.checked)

  var isDisabled = this.checked
  var $formBilling = $('#billing_form')
  var $formShipping = $('#shipping_form')

  // Copy state options
  if ($formBilling.find('[name="country"]').val() != $formShipping.find('[name="country"]').val()) {
    var $options = $formBilling.find('[name="state"] > option').clone()
    var $select2 = $formShipping.find('[name="state"]')
    $select2.dropdown('clear')
    $select2.empty().append($options)
  }
  
  // Copy the values of every input
  $formShipping.find('input, select').each(function(elem) {
    var name = $(this).prop('name')
    if (name.length > 0) {
      if (isDisabled) {
        console.log('name', name)
        var val = $formBilling.find('[name="' + name + '"]').val()
        if (this.tagName === 'SELECT') {
          // Not working below!!!
          // $(this).val(val)
          $(this).dropdown('setup select')
          $(this).dropdown('set selected', val)
          $(this).dropdown('refresh')
        } else {
          $(this).val(val)
        }
      }

      if (this.tagName === 'INPUT') {
        $(this).prop('disabled', isDisabled)
      } else if (this.tagName === 'SELECT') {
        if (isDisabled) {
          $(this).parent().addClass('disabled')
        } else {
          $(this).parent().removeClass('disabled')
        }
      }
    }
  })
  // $('#shipping_form :input').prop('disabled', isDisabled)
}

// Share codes for two form (billing & shipping)
function CountryCommonBehavior($form) {
  console.log('CountryCommonBehavior()')
  console.assert($form)

  var markup = '<option value="">Type to search</option>'
  var $select = $form.find('[name="country"]')
  $.each(window._countries, function(index, country) {
    markup += '<option value="' + index + '">' + country.name + '</option>'
  })
  $select.html(markup)
  $select.dropdown('refresh')
}

function SetupBillingForm() {
  console.log('SetupBillingForm()')

  var $form = $('#billing_form')
  CountryCommonBehavior($form) // Setup country

  // Semantic-ui form validation
  $form.form({
    on: 'blur',
    inline: true,
    fields: {
      first_name: {
        identifier: 'first_name',
        rules: [{
          type: 'empty'
        }]
      },
      last_name: {
        identifier: 'last_name',
        rules: [{
          type: 'empty'
        }]
      },
      email: {
        identifier: 'email',
        rules: [{
          type: 'email'
        }]
      },
      phone: {
        identifier: 'phone',
        rules: [{
          type: 'empty'
        }]
      },
      address1: {
        identifier: 'address1',
        rules: [{
          type: 'empty'
        }]
      },
      postal: {
        identifier: 'postal',
        rules: [
          {
            type: 'regExp',
            value: '/^[a-zA-Z0-9]*$/',
            prompt: 'Alphanumeric characters only'
          }
        ]
      },
      country: {
        identifier: 'country',
        rules: [{
          type: 'empty'
        }]
      }
    }
  })

  $form.submit(function(evt) {
    if (!$(this).form('is valid')) {
      evt.preventDefault()
      return false
    }

    var fieldStr = '<input type="hidden" name="payment_gateway" value="' + window.payment_gateway + '" />'
    $(this).append(fieldStr)
    return true
  })
} // SetupBillingForm()

function SetupShippingForm() {
  console.log('SetupShippingForm()')

  var $form = $('#shipping_form')
  CountryCommonBehavior($form) // Setup country

  // $form.form({
  // 	on: 'blur',
  // 	inline: true,
  // 	fields: {
  // 		first_name: ['empty'],
  // 		last_name: ['empty'],
  // 		address1: ['empty'],
  // 		// state: ['empty'],
  // 		postcode: [/^(?!-)(?!.*-)[A-Za-z0-9-]+(?<!-)$/],
  // 		country: ['empty']
  // 	}
  // })
  $form.form({
    on: 'blur',
    inline: true,
    fields: {
      first_name: {
        identifier: 'first_name',
        rules: [{
          type: 'empty'
        }]
      },
      last_name: {
        identifier: 'last_name',
        rules: [{
          type: 'empty'
        }]
      },
      address1: {
        identifier: 'address1',
        rules: [{
          type: 'empty'
        }]
      },
      postal: {
        identifier: 'postal',
        rules: [
          {
            type: 'regExp',
            value: '/^[a-zA-Z0-9]*$/',
            prompt: 'Can\'t contains hypen'
          }
        ]
      },
      country: {
        identifier: 'country',
        rules: [{
          type: 'empty'
        }]
      }
    }
  })

  $form.submit(function(evt) {
    if (!$(this).form('is valid')) {
      evt.preventDefault()
      return false
    }

    var fieldStr = '<input type="hidden" name="payment_gateway" value="' + window.payment_gateway + '" />'
    $(this).append(fieldStr)
    return true
  })
} // SetupShippingForm()

function OnFormCountryChanged($form, val) {
  console.log('OnFormCountryChanged()')
  
  var $select2 = $form.find('[name="state"]')
  var states = window._countries[val].states
  var markup
  if (states == null) {
    markup = '<option value="">Type to search</option>'
  } else {
    markup = '<option value="">Type to search</option>'
    $.each(states, function (index, state) {
      markup += '<option value="' + index + '">' + state + '</option>'
    })
  }
  $select2.html(markup)
  // $select2.dropdown('set value', '')
  $select2.dropdown('clear')
  $select2.dropdown('refresh')
  $select2.dropdown('setup select')
}

function onBtnProceed(evt) {
  console.log('onBtnProceed()')

  // evt.preventDefault()

  // First, validate billing form
  if ($('#billing_form').form('validate form')) {
    var isSameAsBill = $('[name="same_as_billing"]').prop('checked')
    console.log('isSameAsBill', isSameAsBill)
    var country = null
    if (isSameAsBill) {
      country = $('#billing_form [name="country"]').val()
    } else {
      // Second, validate shipping form
      if ($('#shipping_form').form('validate form')) {
        country = $('#shipping_form [name="country"]').val()
      }
    }

    if (country) {
      var $form = $('#billing_form')
      var data = {
        billing: {
          first_name: $form.find('[name="first_name"]').val(),
          last_name: $form.find('[name="last_name"]').val(),
          email: $form.find('[name="email"]').val(),
          phone: $form.find('[name="phone"]').val(),
          address1: $form.find('[name="address1"]').val(),
          address2: $form.find('[name="address2"]').val(),
          city: $form.find('[name="city"]').val(),
          state: $form.find('[name="state"]').val(),
          postal: $form.find('[name="postal"]').val(),
          country: $form.find('[name="country"]').val()
        }
      }
      if (isSameAsBill) {
        var s = JSON.stringify(data.billing) // duplicate it to shipInfo
        data.shipping = JSON.parse(s)
      } else {
        $form = $('shipping_form')
        data.shipping = {
          first_name: $form.find('[name="first_name"]').val(),
          last_name: $form.find('[name="last_name"]').val(),
          address1: $form.find('[name="address1"]').val(),
          address2: $form.find('[name="address2"]').val(),
          city: $form.find('[name="city"]').val(),
          state: $form.find('[name="state"]').val(),
          postal: $form.find('[name="postal"]').val(),
          country: $form.find('[name="country"]').val()
        }
      }

      EnableAllButtons(false)
      window._shoppingCart.input_info = data

      SaveCart().done(function(result) {
        console.log(result)
        if (result === 'ok') {
          window.location.href = 'mwp?page=orderShipping&uid=' + window._userId + '&rid=' + window._recipientId
        }
      }).fail(function(err, result, xhr) {
        console.error(result)
        EnableAllButtons(true)
      })
      // CreateOrUpdateWcOrder(data)
    }
    // return false
  }
}

function onBtnBack(evt) {
  console.log('onBtnBack()')

  var dlg = $('#dlg_discardwarn')
  dlg.modal('show')
  dlg.find('#btn_ok').click(function(evt) {
    EnableAllButtons(false)
    var url = 'mwp?page=shopCart&uid=' + window._userId + '&rid=' + window._recipientId
    window.location.href = url
  })
  dlg.find('#btn_cancel').click(function (evt) {
    $('#dlg_discardwarn').modal('hide')
  })
}

function SaveCart() {
  console.log('SaveCart()')
  console.assert(window._userId)
  console.assert(window._recipientId)
  console.assert(window._shoppingCart)

  // No need to save these props
  delete window._shoppingCart.cart_items
  delete window._shoppingCart.server_settings
  delete window._shoppingCart.order_pool

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

function EnableAllButtons(isEnable) {
  if (isEnable) {
    $('#btn_proceed').removeClass('disabled loading')
    $('#btn_back').removeClass('disabled loading')
  } else {
    $('#btn_proceed').addClass('disabled loading')
    $('#btn_back').addClass('disabled loading')
  }
}
