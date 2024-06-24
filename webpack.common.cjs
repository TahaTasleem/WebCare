const path = require('path');

module.exports = {
  entry: './src/index.js',
  output: {
    filename: 'wdcomponents.js',
    path: path.resolve(__dirname, 'static/js'),
    library: 'WDC'
  },
  module:{
      rules:[{
          loader: 'babel-loader',
          test: /\.js$|jsx/,
          exclude: /node_modules/
      }]
  },
};