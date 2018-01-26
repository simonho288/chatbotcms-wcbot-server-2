/**
 * This module mainly handles the WooCommerce shipping method parsing.
 */

var REGEX_SPACE = /\s+/ // one or more space(s)
var REGEX_NUM = /[0-9]+(?:\.[0-9]+)?\b/ // number constant
// var REGEX_NUM = /^\d+$/ // number constant
// var REGEX_NUM = /\d+\s*$/
var REGEX_QTY = /\[\s*(qty)\s*\]/ // [qty]
var REGEX_FEE = /\[\s*(fee) \s*(.+?)\s*\]/ // [fee percent="10" min_fee="4"]

function CreateLexer() {
  console.log('CreateLexer()')

  // Regex Ref:
  // https://users.cs.cf.ac.uk/Dave.Marshall/PERL/node79.html
  // Tool:
  // https://regex101.com/

  var lexer = new Lexer
  lexer.addRule(REGEX_SPACE, function () {
    // skip whitespace
  })

  lexer.addRule(REGEX_FEE, function (lexeme) {
    return lexeme; // [fee percent="10" min_fee="4"]
  })

  // lexer.addRule(/\[(.+?)\]/, function (lexeme) {
  lexer.addRule(REGEX_QTY, function (lexeme) {
    return lexeme;
  })

  // lexer.addRule(/[0-9]+(?:\.[0-9]+)?\b/, function (lexeme) {
  lexer.addRule(REGEX_NUM, function (lexeme) {
    return lexeme; // number
  });

  lexer.addRule(/[\(\+\-\*\/\)]/, function (lexeme) {
    return lexeme; // punctuation (i.e. "(", "+", "-", "*", "/", ")")
  })

  return lexer
} // CreateLexer()

function ParseWithLexer(expression) {
  console.log('ParseWithLexer()')
  
  var factor = {
    precedence: 2,
    associativity: 'left'
  }
  var term = {
    precedence: 1,
    associativity: 'left'
  }

  var lexer = CreateLexer()
  var parser = new Parser({
    '+': term,
    '-': term,
    '*': factor,
    '/': factor
  })

  function parse(input) {
    lexer.setInput(input)
    var tokens = [], token
    while (token = lexer.lex())
      tokens.push(token)
    return parser.parse(tokens)
  }

  // Perform arithmetic
  var stack = []

  var operator = {
    '+': function (a, b) { return a + b },
    '-': function (a, b) { return a - b },
    '*': function (a, b) { return a * b },
    '/': function (a, b) { return a / b }
  }

  // parse('[qty]*2').forEach(function (c) {
  $.each(parse(expression), function (idx, c) {
    // parse(expression).forEach(function (c) {
    switch (c) {
      case '+':
      case '-':
      case '*':
      case '/':
        var b = + stack.pop()
        var a = + stack.pop()
        stack.push(operator[c](a, b))
        break
      default:
        if (/^\d+/.test(c)) { // is it a constant number?
          stack.push(parseFloat(c))
        } else if (REGEX_QTY.test(c)) {
          var tQty = CalcOrderTotalQty() // Get total qty in order
          stack.push(tQty)
        } else if (REGEX_FEE.test(c)) {
          var rr = REGEX_FEE.exec(c)
          var expression2 = rr[2] // percent="10" min_fee="4"
          var percent, min_fee
          var rr2 = /^.*percent\s*\=\s*"*(\s*[0-9]+)"*\s*/.exec(expression2)
          if (rr2 && rr2.length === 2) {
            percent = parseFloat(rr2[1])
          }
          rr2 = /^.*min_fee\s*\=\s*"*(\s*[0-9]+)"*\s*/.exec(expression2)
          if (rr2 && rr2.length === 2) {
            min_fee = parseFloat(rr2[1])
          }
          var fee = CalcFee(percent, min_fee)
          stack.push(fee)
        } else {
          console.warn('Unknown context:', c)
        }
    }
  })

  var output = stack.pop()
  console.log('output:', output)
  return output
} // ParseWithLexer()

function CalcFee(percent, minFee) {
  console.log('CalcFee()')

  var total = CalcOrderTotalAmount()
  if (percent != null) {
    total = total * percent / 100
  }
  if (minFee != null) {
    total = (total < minFee) ? minFee : total
  }
  return total
} // CalcFee()

function CalcOrderTotalAmount() {
  console.log('CalcOrderTotalAmount()')

  var totalAmt = 0
  $.each(window._wcOrder.line_items, function (index, item) {
    totalAmt += parseFloat(item.subtotal)
  })
  return totalAmt
} // CalcOrderTotalAmount()

function CalcOrderTotalQty() {
  console.log('CalcOrderTotalQty()')

  var totalQty = 0
  $.each(window._wcOrder.line_items, function(index, item) {
    totalQty += item.quantity
  })
  return totalQty
} // CalcOrderTotalQty()

// Object Parser
function Parser(table) {
  this.table = table;
}
Parser.prototype.parse = function (input) {
  var length = input.length,
    table = this.table,
    output = [],
    stack = [],
    index = 0;

  while (index < length) {
    var token = input[index++];

    switch (token) {
    case "(":
      stack.unshift(token);
      break;
    case ")":
      while (stack.length) {
        var token = stack.shift();
        if (token === "(") break;
        else output.push(token);
      }

      if (token !== "(")
        throw new Error("Mismatched parentheses.");
      break;
    default:
      if (table.hasOwnProperty(token)) {
        while (stack.length) {
          var punctuator = stack[0];

          if (punctuator === "(") break;

          var operator = table[token],
            precedence = operator.precedence,
            antecedence = table[punctuator].precedence;

          if (precedence > antecedence ||
            precedence === antecedence &&
            operator.associativity === "right") break;
          else output.push(stack.shift());
        }

        stack.unshift(token);
      } else output.push(token);
    }
  }

  while (stack.length) {
    var token = stack.shift();
    if (token !== "(") output.push(token);
    else throw new Error("Mismatched parentheses.");
  }

  return output
} // Parser.prototype.parse()
