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
    _model_module_version: '0.1.0',
    _view_module_version: '0.1.0',
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
