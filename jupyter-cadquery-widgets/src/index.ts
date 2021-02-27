import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  IJupyterWidgetRegistry
} from '@jupyter-widgets/base'

import * as widgetExports from './widgets'

/**
 * Initialization data for the jupyter_cadquery extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'jupyter_cadquery:plugin',
  requires: [IJupyterWidgetRegistry],
  autoStart: true,
  activate: (app: JupyterFrontEnd, widgets: IJupyterWidgetRegistry) => {
    console.log('JupyterLab extension jupyter_cadquery is activated!');
    widgets.registerWidget({
      name: 'jupyter_cadquery',
      version: '1.0.0',
      exports: widgetExports
    });
    console.log('jupyter_cadquery widgets registered!');
  }
};

export default extension;
