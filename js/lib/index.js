// Export widget models and views, and the npm package version number.

var image_button = require('./image_button.js');
var tree_view = require('./tree_view.js');

module.exports = Object.assign({}, image_button, tree_view);
module.exports.version = require('../package.json').version;

