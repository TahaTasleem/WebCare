//gulpfile.js
var jsFiles = [
    'static/js/bootstrap.min.js',
    'static/js/jquery.smartmenus.min.js',
    'static/js/jquery.smartmenus.bootstrap.min.js',
    'static/js/jquery_ui.js',
    'static/js/xterm.js',
    'static/js/hotkeys.min.js',
    'static/js/bowser.min.js',
    'static/js/socket_io.js',
    'static/js/wd.min.js'
],
    jsDest = 'static/js/',
    jsFilesMin = [
        'static/js/webdirect.js'
    ];

var cssFiles = [
    'static/css/jquery_ui.css',
    'static/css/bootstrap.min.css',
    'static/css/jquery.smartmenus.bootstrap.css',
    'static/css/xterm.css',
    'static/css/webdirect.css'
],
    cssDest = "static/css/";

const { src, dest, parallel, series } = require("gulp");
const postcss = require("gulp-postcss");
const cssnano = require('cssnano');
const concat = require("gulp-concat");
const uglify = require("gulp-uglify");
const sourcemaps = require("gulp-sourcemaps");

function jsminimize() {
    return src(jsFilesMin)
        .pipe(sourcemaps.init())
        .pipe(concat("wd.min.js"))
        .pipe(uglify())
        .pipe(sourcemaps.write('.'))
        .pipe(dest(jsDest));
}

function jscombine() {
    return src(jsFiles)
        .pipe(concat("wd.min.js"))
        .pipe(dest(jsDest));
}

function cssBuild() {
    return src(cssFiles)
        .pipe(concat("wd.min.css"))
        .pipe(postcss([cssnano({
            preset: ['default', {
                discardComments: {
                    removeAll: true,
                },
            }]
        })]))
        .pipe(dest(cssDest));
}

exports.css = cssBuild;
exports.scripts = series(jsminimize, jscombine);
exports.default = exports.all = parallel(exports.scripts, cssBuild);