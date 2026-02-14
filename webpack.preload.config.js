export default {
  target: 'electron-preload',
  mode: 'development',
  devtool: false,
  module: {
    rules: [],
  },
  resolve: {
    extensions: ['.js', '.ts', '.json'],
  },
  // External electron - don't bundle it
  externals: {
    'electron': 'commonjs2 electron'
  },
};
