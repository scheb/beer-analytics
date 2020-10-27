const path = require("path");
const {CleanWebpackPlugin} = require("clean-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
    entry: {
        app: "./web_app/static/ts/application.ts",
        style: "./web_app/static/scss/beer_analytics.scss"
    },
    output: {
        path: path.resolve(__dirname, "./bundles"),
        publicPath: "/static/",
        filename: "[name].js",
        chunkFilename: "[id]-[chunkhash].js",
    },
    devServer: {
        port: 8081,
        writeToDisk: true,
    },
    plugins: [
        new MiniCssExtractPlugin(),
        new CleanWebpackPlugin(),
    ],
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: 'ts-loader',
                exclude: /node_modules/,
            },
            {
                test: /\.(svg)$/,
                use: {
                    loader: "url-loader",
                    options: {
                        limit: 5120,
                    },
                },
            },
            {
                test: /\.(woff|woff2)/,
                use: {
                    loader: "file-loader",
                    options: {
                        name: "[name].[ext]",
                        outputPath: "fonts"
                    }
                }
            },
            {
                test: /\.scss$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: '[name].css',
                        }
                    },
                    'extract-loader',
                    "css-loader",
                    "sass-loader"
                ]
            }
        ],
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js'],
    },
};
