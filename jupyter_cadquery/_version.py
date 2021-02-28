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

from collections import namedtuple
import re

VersionInfo = namedtuple("VersionInfo", ["major", "minor", "patch", "release", "build"])


def get_version(version):
    r = re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)\-{0,1}(?P<release>\D*)(?P<build>\d*)")
    major, minor, patch, release, build = r.match(version).groups()
    return VersionInfo(major, minor, patch, release, build)


__version__ = "2.0.0-rc1"  # DO NOT EDIT THIS DIRECTLY!  It is managed by bumpversion
__version_info__ = get_version(__version__)
