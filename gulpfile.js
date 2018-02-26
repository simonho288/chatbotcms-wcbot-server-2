const gulp = require('gulp')
const uglify = require('gulp-uglify') // for client-side JS minify
const minify = require('gulp-minify') // for server-side JS minify (ES6)
const pump = require('pump')
const cleanCSS = require('gulp-clean-css')
const gzip = require('gulp-gzip')
const util = require('gulp-util')
const runSequence = require('run-sequence')
const gulpAwsS3 = require('gulp-s3-publish')

const CLIENTJS_MINIFY_OPTS = {
  compress: {
    drop_console: true
  }
}

const CLIENTCSS_MINIFY_OPTS = {
  compatibility: '*'
}

/************************************************************************
Shopping Cart build
************************************************************************/

// Minify JS files: using Uglify: https://github.com/terinjokes/gulp-uglify
gulp.task('shopcart-js', () => {
  return pump([gulp.src('shopping-cart-src/js/**/*.js'),
    uglify(CLIENTJS_MINIFY_OPTS),
    gulp.dest('shopping-cart/js')
  ])
})

// Minify CSS files: using https://github.com/scniro/gulp-clean-css
gulp.task('shopcart-css', () => {
  return pump([gulp.src('shopping-cart-src/css/**/*.css'),
    cleanCSS(CLIENTCSS_MINIFY_OPTS),
    gulp.dest('shopping-cart/css')
  ])
})

// public folder contains shopping cart which has JS, CSS and Semantic UI themes assets
gulp.task('build-shopcart', ['shopcart-js', 'shopcart-css'])

/************************************************************************
Deployment
************************************************************************/

// IMPORTANT: Must define environment varables before run this task.
function initAWS() {
  if (process.env.AMZBUCKET == null)
    throw new Error("Environment AMZBUCKET not defined!")
  if (process.env.AMZACCESSSECRET == null)
    throw new Error("Environment AMZACCESSSECRET not defined!")
  if (process.env.AMZACCESSKEY == null)
    throw new Error("Environment AMZACCESSKEY not defined!")
  if (process.env.AMZREGION == null)
    throw new Error("Environment AMZREGION not defined!")

  return {
    config: {
      key: process.env.AMZACCESSKEY,
      secret: process.env.AMZACCESSSECRET,
      bucket: process.env.AMZBUCKET,
      region: process.env.AMZREGION
    },
    options: {
      acl: 'public-read',
      headers: {'CacheControl': 'max-age=315360000, no-transform, public'},
      gzippedOnly: true,
      uploadPath: 'wcbot/'
    }
  }
}

// For production: Upload the Shopping Cart to S3.
gulp.task('upload-s3', () => {
  aws = initAWS();  
  util.log('Uploading shopping-cart to bucket: ' + process.env.AMZBUCKET)
  return gulp.src('shopping-cart/**/*')
    .pipe(gzip()) // upload gzipped content to reduce download size
    .pipe(gulpAwsS3(aws.config, aws.options))
})

// For development: Upload the Shopping Cart to S3.
gulp.task('upload-s3-dev', () => {
  aws = initAWS();  
  util.log('Uploading shopping-cart to bucket: ' + process.env.AMZBUCKET)
  return gulp.src('shopping-cart-src/**/*')
    .pipe(gzip()) // upload gzipped content to reduce download size
    .pipe(gulpAwsS3(aws.config, aws.options))
})
