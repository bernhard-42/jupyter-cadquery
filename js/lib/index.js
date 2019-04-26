// Copyright 2019 Bernhard Walter

// Licensed under the Apache License, Version 2.0(the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//    http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Export widget models and views, and the npm package version number.

var image_button = require('./image_button.js');
var tree_view = require('./tree_view.js');

module.exports = Object.assign({}, image_button, tree_view);
module.exports.version = require('../package.json').version;

