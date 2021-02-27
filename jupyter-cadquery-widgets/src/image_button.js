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


import {
  ButtonView,
  ButtonModel
} from '@jupyter-widgets/controls';

import {
  extend
} from 'lodash';


// Custom Model. Custom widgets models must at least provide default values
var ImageButtonModel = ButtonModel.extend({
  defaults: extend(ButtonModel.prototype.defaults(), {
    _model_name: 'ImageButtonModel',
    _view_name: 'ImageButtonView',
    _model_module: 'jupyter_cadquery',
    _view_module: 'jupyter_cadquery',
    _model_module_version: "v1.0.0",
    _view_module_version: "v1.0.0",
    value: null
  })
});


// Custom View. Renders the widget model.
var ImageButtonView = ButtonView.extend({
  render: function () {
    var width = this.model.get('width');
    var height = this.model.get('height');
    var blob = new Blob([this.model.get("value")], {
      type: 'image/png'
    });
    var tooltip = this.model.get('tooltip');
    this.el.classList.add('jupyter-widgets');
    this.el.classList.add('jupyter-button');
    this.el.setAttribute('width', width + 4);
    this.el.setAttribute('height', height + 4);
    this.el.setAttribute('title', tooltip);
    var img = document.createElement('img');
    img.setAttribute('width', width);
    img.setAttribute('height', height);
    img.src = URL.createObjectURL(blob);
    this.el.appendChild(img);
  },
});

export { ImageButtonModel, ImageButtonView }
