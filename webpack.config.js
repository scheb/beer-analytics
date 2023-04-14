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
        devMiddleware: {
            writeToDisk: true,
        }
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
                test: /\.(png|jpe?g|gif|svg|woff|woff2)$/,
                type: 'asset'
            },
            {
                test: /\.scss$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    "css-loader",
                    {
                        loader: "sass-loader",
                        options: {
                            sassOptions: {
                                indentWidth: 4,
                                includePaths: ["node_modules/@syncfusion"]
                            },
                        },
                    },
                ]
            }
        ],
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js'],
        fallback: {
            "assert": false,
            "buffer": false,
            "fs": false,
            "path": false,
            "stream": require.resolve("stream-browserify")
        }
    }
};
