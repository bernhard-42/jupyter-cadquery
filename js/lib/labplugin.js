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

var jupyter_cadquery = require('./index');
var base = require('@jupyter-widgets/base');

module.exports = {
  id: 'jupyter_cadquery',
  requires: [base.IJupyterWidgetRegistry],
  activate: function(app, widgets) {
      widgets.registerWidget({
          name: 'jupyter_cadquery',
          version: jupyter_cadquery.version,
          exports: jupyter_cadquery
      });
  },
  autoStart: true
};

