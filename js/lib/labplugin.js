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

