// module.exports = {
//   // devServer Options don't belong into `configureWebpack`
//   devServer: {
//     host: '0.0.0.0',
//     port: '9080',
//     public: '192.168.99.100:9080',
//     //hot: true,
//     //disableHostCheck: true,
//   },
// };

module.exports = {
  publicPath: '/',
  devServer: {
    disableHostCheck: true,
    port: 9080,
    public: '0.0.0.0:9080'
  }
}
