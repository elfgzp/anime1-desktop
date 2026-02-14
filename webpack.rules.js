export default [
  {
    test: /\.ts$/,
    exclude: /node_modules/,
    use: 'ts-loader',
  },
  {
    test: /\.vue$/,
    use: 'vue-loader',
  },
  {
    test: /\.css$/,
    use: ['style-loader', 'css-loader'],
  },
];
