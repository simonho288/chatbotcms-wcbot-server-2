
var util = {
  CloneObject: function(src) {
    console.assert(src != null)
    return Object.assign({}, src)
  },

  // Extract the currency symbol from WC current. This is to dig into the result
  // of WC result. See the result of woocommerce_currency. e.g. "HKD": "Hong Kong dollar (&#36;)",
  // https://woocommerce.github.io/woocommerce-rest-api-docs/#list-all-setting-options
  // Note: This function is called by ParseCurrencyToDisp() only.
  ExtractWcCurrecnySymbol: function (wcCurStr) {
    console.assert(typeof wcCurStr === 'string')
    var pos1 = wcCurStr.indexOf('(')
    var pos2 = wcCurStr.indexOf(')')
    if (pos1 >= 0 && pos2 >= 0 && pos1 < pos2) {
      var result = wcCurStr.substring(pos1 + 1, pos2)
      return result
    } else {
      return ''
    }
  },

  // Format the price as defined in Server Currency Settings
  // The setting usually stores in window._shoppingCart.server_settings.currency
  ParseCurrencyToDisp: function(curSts, price, isShowSymbol) {
    console.assert(typeof curSts === 'object')
    console.assert(typeof curSts.thousandSep === 'string')
    console.assert(typeof curSts.decimalSep === 'string')
    console.assert(curSts.numDecimal != null)
    console.assert(typeof curSts.symbolPos === 'string')
    console.assert(curSts.options != null)
    console.assert(typeof curSts.value === 'string')
    console.assert(typeof price === 'number')

    // Default value
    isShowSymbol = isShowSymbol == null ? true : isShowSymbol

    // First, make the format
    var fmt = '0,0[.]'
    for (var i = 0; i < curSts.numDecimal; ++i)
      fmt += '0'
    var priceRst = numeral(price).format(fmt)
    var dotpos = priceRst.lastIndexOf('.')
    priceRst = priceRst.replace(/,/g, curSts.thousandSep)
    if (dotpos >= 0) {
      priceRst = priceRst.substring(0, dotpos) + curSts.decimalSep + priceRst.substring(dotpos + 1, priceRst.length)
    }

    if (!isShowSymbol) {
      return priceRst
    }

    var cryopt = curSts.options[curSts.value]
    var symbol = this.ExtractWcCurrecnySymbol(cryopt)
    symbol = symbol.replace(/&amp;/g, '&')
    if (curSts.symbolPos === 'left') {
      return symbol + priceRst
    } else if (curSts.symbolPos === 'right') {
      return priceRst + symbol
    } else if (curSts.symbolPos === 'left_space') {
      return symbol + ' ' + priceRst
    } else if (curSts.symbolPos === 'right_space') {
      return priceRst + ' ' + symbol
    } else {
      console.assert('Unhandled currency symbol position: ' + curSts.symbolPos)
    }
  },

  WCDateToJsDate: function(dtStr) {
    var d = new Date(dtStr + '.000Z')
    return d.toLocaleString()
  },
  
  // decodeJSON: function (encodedJSON) {
  //   var decodedJSON = $('<div/>').html(encodedJSON).text();
  //   return $.parseJSON(decodedJSON);
  // },
  decodeJSON: function(encodedJSON) { // regex version of decodeJSON()
    return JSON.parse(encodedJSON.replace(/&#34;/g, '"'))
  }

}