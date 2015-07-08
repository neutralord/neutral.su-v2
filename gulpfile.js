var path = require('path'),
    gulp = require('gulp'),
    csso = require('gulp-csso'),
    gzip = require('gulp-gzip'),
    bundle = require('jspm/api').bundle,
    Builder = require('systemjs-builder');


var CONFIG = {
    babel: {sourceMap: true, modules: 'system'},
    bundleName: 'main',
    cssSrc: './web/css/*.css',
    cssDest: './web/build/css/',
    devBuild: './web/build/js/app-dev.js',
    prodBuild: './web/build/js/app-prod.js',
    vendorBuild: './web/build/js/vendor.js',
    package: require('./package.json')
};

var getBuilder = (function (cfg) {
    cfg = cfg || {};
    var _builder = null;
    return function() {
        if (_builder === null) {
            _builder = new Builder();
            _builder.loadConfigSync(path.join(CONFIG.package.jspm.directories.baseURL, 'config.js'));
            _builder.config({ baseURL: 'file:' + CONFIG.package.jspm.directories.baseURL });
            _builder.config(cfg);
        }
        return _builder;
    }
})();

gulp.task('default', function() {});

gulp.task('build:css', function() {
    return gulp
        .src(CONFIG.cssSrc)
        .pipe(csso())
        .pipe(gzip({ gzipOptions: { level: 9 } }))
        .pipe(gulp.dest(CONFIG.cssDest));
});

gulp.task('build:vendor', function () {
    var dependencies = Object.keys(CONFIG.package.jspm.dependencies);
    return bundle(dependencies.join(' + '), CONFIG.vendorBuild, {inject: true, minify: true, sourceMaps: true})
        .then(function() {
            console.log('Build complete');
        })
        .catch(function(err) {
            console.log('Build error');
            console.log(err);
        });
});

gulp.task('build:prod', function () {
    var dependencies = Object.keys(CONFIG.package.jspm.dependencies);
    return bundle('app-prod - ' + dependencies.join(' - '), CONFIG.prodBuild, {inject: true, sourceMaps: true}).then(function() {
        console.log('Build complete');
    })
    .catch(function(err) {
        console.log('Build error');
        console.log(err);
        console.log(err.stack);
    });
});

gulp.task('watch', function() {
    gulp.watch(CONFIG.jsSrc, ['build:app']);
});