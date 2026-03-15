const path = require('path');

module.exports = {
  mode: 'production',
  entry: {
    'e2e': './tests/e2e.ts',
    'ramping-arrival-notes-crud': './ai-performance/tests/ramping-arrival-notes-crud.ts',
  },
  output: {
    path: path.resolve(__dirname, 'dist'),
    libraryTarget: 'commonjs',
    filename: '[name].js',
  },
  resolve: {
    extensions: ['.ts', '.js'],
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: 'babel-loader',
        exclude: /node_modules/,
      },
    ],
  },
  target: 'web',
  externals: /^(k6|https?:\/\/(cdn\.jsdelivr\.net|jslib\.k6\.io))/,
  performance: {
    hints: false,
  },
  optimization: {
    minimize: false,
  },
};
