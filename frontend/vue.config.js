const webpack = require("webpack");
module.exports = {
  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({
        '__VUE_OPTIONS_API__': JSON.stringify(true),
        '__VUE_PROD_DEVTOOLS__': JSON.stringify(false),
        '__VUE_PROD_HYDRATION_MISMATCH_DETAILS__': JSON.stringify(false) // 添加这行
      })
    ]
  },
  devServer: {
    host: '0.0.0.0',  // 允许外部访问
    port: 8080,        // 指定端口
    open: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8008",  // 后端服务地址
        secure: false, // 允许证书无效
        changeOrigin: true,
        pathRewrite: { "^/api": "" },  // 去掉 /api 前缀
        onProxyRes: (proxyRes) => {
          proxyRes.headers['X-Accel-Buffering'] = 'no'
        },
        xfwd: true, // 添加X-Forwarded头
        proxyReqWriteStream: {
          // 禁用内部缓冲
          unbuffered: true
        }
      }
    },
    compress: false,
  }
}