const path = require('path');

module.exports = {
  entry: './src/main.js',
  target: 'electron-main',
  module: {
    rules: [
      {
        test: /\.ts$/,
        exclude: /node_modules/,
        use: 'ts-loader',
      },
    ],
  },
  resolve: {
    extensions: ['.js', '.ts', '.json'],
    alias: {
      '@shared': path.resolve(__dirname, 'src/shared'),
    },
  },
  externals: {
    // Native modules and ES modules that should not be bundled
    'electron-store': 'commonjs electron-store',
    'cheerio': 'commonjs cheerio',
    'axios': 'commonjs axios',
  },
};
