#
# Copyright 2019 Bernhard Walter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from IPython.display import display, HTML

LATEST = None

base_css = """
.scroll-area {
    overflow: scroll !important;
    border: unset !important;
}

.mac-scrollbar::-webkit-scrollbar {
    width: 5px !important;
    height: 5px !important;
}

.mac-scrollbar::-webkit-scrollbar-track {
    background-color: transparent !important;
}

.mac-scrollbar .widget-html-content {
    overflow-x: visible;
    overflow-y: visible;
}

.tab-content-no-padding .widget-tab-contents {
    overflow-x: visible !important;
    overflow-y: visible !important;
    padding-bottom: 0px !important;
}

.view_renderer {
    border: 1px solid var(--jp-border-color1);
    margin-top: 3px;
    margin-left: 2px;
}

.view_tree {
    padding: 0px !important;
}

.view_axes {
    width: 60px !important;
    margin-left: 5px !important;
}

.view_zero {
    width: 55px !important;
}

.view_grid {
    width: 56px !important;
}

.view_ortho {
    width: 64px !important;
}

.view_transparent {
    width: 125px !important;
}

.view_black_edges {
    width: 105px !important;
}

.view_button {
    padding: 0px !important;
}

.view_button>img {
    height: 28px;
    width: 36px;
}

.node_entry_wrap {
    white-space: pre;
}

.node_entry {
    white-space: nowrap;
    padding-top: 4px;
}

.t-caret {
    cursor: pointer;
    -webkit-user-select: none;
    /* Safari 3.1+ */
    -moz-user-select: none;
    /* Firefox 2+ */
    -ms-user-select: none;
    /* IE 10+ */
    user-select: none;
}

.t-caret-down::before {
    -ms-transform: rotate(90deg);
    /* IE 9 */
    -webkit-transform: rotate(90deg);
    /* Safari */
    transform: rotate(90deg);
}

.toplevel {
    list-style-type: none;
    padding-inline-start: 0px;
}

.nested {
    display: none;
    list-style-type: none;
    padding-inline-start: 16px;
}

.active {
    display: block;
}

.icon {
    width: 28px !important;
    height: 22px !important;
    padding-right: 2px;
    vertical-align: middle;
}

.indent {
    margin-left: 12px;
}

.tree_label {
    padding-left: 2px;
    font-size: 14px;
}

.scroll_down {
    display: flex;
    flex-direction: column-reverse;
}

.small_table {
    line-height: 14px;
}

.monospace select {
    font-family: monospace;
}
"""

css = {
    "light": base_css
    + """
        .t-caret::before {
            content: u"\u25B6";
            font-size: 12px;
            color: "#080808";
            display: inline-block;
            margin-right: 2px;
        }

        .mac-scrollbar::-webkit-scrollbar-thumb {
            background-color: rgba(0, 0, 0, 0.2) !important;
            border-radius: 100px !important;
        }

        .mac-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 0, 0, 0.4) !important;
        }

        .mac-scrollbar::-webkit-scrollbar-thumb:active {
            background: #181818 !important;
        }

        .mac-scrollbar::-webkit-scrollbar-corner {
            background: white;
        }

        .view_output {
            border: 1px solid var(--jp-border-color1);
            margin: 2px 2px 2px 2px !important;
            padding-right: 1px !important;
            background-color: white;
        }
    """,
    "dark": base_css
    + """
        .t-caret::before {
            content: u"\u25B6";
            font-size: 12px;
            color: #e0e0e0;
            display: inline-block;
            margin-right: 2px;
        }

        .mac-scrollbar::-webkit-scrollbar-thumb {
            background-color: rgba(255, 255, 255, 0.3) !important;
            border-radius: 100px !important;
        }

        .mac-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5) !important;
        }

        .mac-scrollbar::-webkit-scrollbar-thumb:active {
            background: #e0e0e0 !important;
        }

        .mac-scrollbar::-webkit-scrollbar-corner {
            background: #212121;
        }

        .view_output {
            border: 1px solid var(--jp-border-color1);
            margin: 2px 2px 2px 2px !important;
            padding-right: 1px !important;
            background-color: #212121;
        }
    """,
}


def set_css(theme, force=False):
    global LATEST

    if force or theme != LATEST:
        display(HTML(f"""<style>{css[theme]}</style>"""))
        LATEST = theme
