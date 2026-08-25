"""Compatibility: `from jupyter_cadquery.animation import Animation` keeps working.

The class lives in `ocp_viewer_core.animation` since the core adoption, and
the name bound in show.py is this viewer's factory. This module re-exports it
so the historic deep import stays valid; it is the same object as
`from jupyter_cadquery import Animation`.
"""

#
# Copyright 2026 Bernhard Walter
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

from .show import Animation

__all__ = ["Animation"]
