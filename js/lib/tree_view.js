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

import { SelectionModel, DescriptionView } from '@jupyter-widgets/controls';
import { extend } from 'lodash';

import '../style/index.css';

// Some helpers

function tag(name, classList, options) {
  var el = document.createElement(name);
  if (typeof (classList) != "undefined") {
    for (var i in classList) {
      el.classList.add(classList[i]);
    }
  }
  if (typeof (options) != "undefined") {
    for (var t in options) {
      el[t] = options[t];
    }
  }
  return el;
};

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
};

const States = {
  unselected: 0,
  selected: 1,
  mixed: 2,
  empty: 3
};

// TreeModel

var TreeModel = SelectionModel.extend({
  defaults: extend(SelectionModel.prototype.defaults(), {
    _model_name: 'TreeModel',
    _view_name: 'TreeView',
    _model_module: 'jupyter_cadquery',
    _view_module: 'jupyter_cadquery',
    _model_module_version: "v1.0.0",
    _view_module_version: "v1.0.0",
    icons: null,
    tree: null,
    state: null
  })
});


// TreeView

var TreeView = DescriptionView.extend({
  initialize: function (parameters) {
    DescriptionView.prototype.initialize.apply(this, arguments);

    this.icons = this.model.get("icons");
    // Be sure to work on deep copy, otherwise object will be updated and
    // model.set will not find any differences and nothing will be sent to python!
    this.states = clone(this.model.get("state"));
    this.treeModel = this.toModel(this.model.get("tree"));

    this.listenTo(this.model, "change:state", () => this.updateAllStates());
  },

  render: function () {
    var ul = tag("ul", ["toplevel"]);
    ul.appendChild(this.toHtml(this.treeModel));
    this.el.appendChild(ul);

    for (var icon_id in this.icons) {
      this.updateNodes(this.treeModel, icon_id);
    }

    var toggler = this.el.getElementsByClassName("caret");
    for (var i = 0; i < toggler.length; i++) {
      toggler[i].addEventListener("click", e => { // jshint ignore:line
        e.srcElement.parentElement.parentElement.querySelector(".nested").classList.toggle("active");
        e.srcElement.classList.toggle("caret-down");
      });
    }
  },

  toModel: function (tree) {
    var model = {
      id: tree.id,
      type: tree.type,
      name: tree.name,
      color: tree.color,
      imgs: [],
      states: []
    };
    var i = 0;

    if (tree.type === "node") {
      for (i in this.icons) {
        model.states.push(States.selected);
      }
      model.children = [];
      for (i in tree.children) {
        model.children.push(this.toModel(tree.children[i]));
      }
    } else if (tree.type === "leaf") {
      var state = this.model.get("state")[tree.id];
      for (i in this.icons) {
        model.states.push(state[i]);
      }
    } else {
      console.error(`Error, unknown type '${tree.type}'`);
    }
    return model;
  },

  getNode: function (node, id) {
    if (node.id == id) return node;
    for (var i in node.children) {
      var result = this.getNode(node.children[i], id);
      if (result != null) return result;
    }
    return null;
  },

  publish: function () {
    // update the model variable with the internal updated states
    // Ensure to work with a clone to keep internal states and model states
    // decoupled
    this.model.set("state", clone(this.states));
    // and send to python kernel
    this.model.save_changes();
  },

  updateState: function (node, icon_id, state) {
    if (node.states[icon_id] != States.empty) { // ignore empty
      // update internal states. This does not about the model variable
      this.states[node.id][icon_id] = state;
      // update treeModel
      node.states[icon_id] = state;
      // update icons
      this.setIcon(node.imgs[icon_id], icon_id, state);
    }
  },

  propagateChange: function (node, icon_id, state) {
    for (var i in node.children) {
      var subNode = node.children[i];
      if (subNode.type == "leaf") {
        this.updateState(subNode, icon_id, state);
      } else {
        this.propagateChange(subNode, icon_id, state);
      }
    }
  },

  updateAllStates: function () {
    var changes = false;
    this.states = clone(this.model.get("state"));
    for (var icon_id in this.icons) {
      for (var id in this.states) {
        var node = this.getNode(this.treeModel, id);
        var state = this.states[id][icon_id];
        if (node.states[icon_id] != state){
          changes = true;
          node.states[icon_id] = state;
          this.updateState(node, icon_id, state);
          this.setIcon(node.imgs[icon_id], icon_id, state);
        }
      }
      if (changes){
        this.updateNodes(this.treeModel, icon_id);
      }
    }
  },

  updateNodes: function (model, icon_id) {
    var state = 0;
    if (model.type === "node") {
      var states = [];
      for (var i in model.children) {
        states.push(this.updateNodes(model.children[i], icon_id));
      }
      var filtered_states = states.filter(e => e != 3)
      if (filtered_states.length == 0) {
        state = 3;
      } else {
        state = filtered_states.reduce((s1, s2) => (s1 == s2) ? s1 : States.mixed,
                                       filtered_states[0]);
      }
      model.states[icon_id] = state;
      this.setIcon(model.imgs[icon_id], icon_id, state);
    } else {
      state = model.states[icon_id];
    }
    return state;
  },

  getIcon: function (icon_id, state) {
    return `data:image/png;base64,${this.icons[icon_id][state]}`;
  },

  setIcon: function (img, icon_id, state) {
    img.src = this.getIcon(icon_id, state);
  },

  handle: function (type, id, icon_id) {
    var node = this.getNode(this.treeModel, id);
    var newState = (node.states[icon_id] == States.selected) ? States.unselected : States.selected;
    if (type == "leaf") {
      this.updateState(node, icon_id, newState);
      this.updateNodes(this.treeModel, icon_id);
    } else if (type == "node") {
      this.propagateChange(node, icon_id, newState);
      this.updateNodes(this.treeModel, icon_id);
    } else {
      console.error(`Error, unknown type '${type}'`);
    }
    this.publish();
  },

  toHtml: function (model) {
    var view = this;
    var icon_id = 0;
    var img;

    var li = tag("li");
    var lbl = tag("span", ["tree_label"]);
    lbl.innerHTML = model.name;
    var entry = tag("span", ["node_entry"])
    if (model.type === "node") {
      var span = tag("span", ["node_entry_wrap"])
      span.appendChild(tag("span", ["caret", "caret-down"]));
      for (icon_id in this.icons) {
        img = tag("img", ["icon"], { src: this.getIcon(icon_id, 1) });
        img.setAttribute("icon_id", icon_id);
        img.addEventListener("click", e => { // jshint ignore:line
          this.handle(model.type, model.id, e.srcElement.getAttribute("icon_id"));
        });
        entry.appendChild(img);
        model.imgs.push(img);
      }
      entry.appendChild(lbl);
      span.appendChild(entry);
      li.append(span);
      var lu = tag("ul", ["nested", "active"]);
      for (var i in model.children) {
        lu.appendChild(this.toHtml(model.children[i]));
      }
      li.appendChild(lu);

    } else {
      for (icon_id in this.icons) {
        img = tag("img", ["icon"], { src: this.getIcon(icon_id, model.states[icon_id]) });
        img.setAttribute("icon_id", icon_id);
        if (icon_id == 0) {
          img.classList.add("indent");
        }
        if (model.states[icon_id] != States.empty) { // no events on empty icon
          img.addEventListener("click", e => { // jshint ignore:line
            this.handle(model.type, model.id, e.srcElement.getAttribute("icon_id"));
          });
        }
        entry.appendChild(img);
        model.imgs.push(img);
      }
      entry.appendChild(lbl);
      li.appendChild(entry);
    }
    return li;
  }
});

export { TreeModel, TreeView };
