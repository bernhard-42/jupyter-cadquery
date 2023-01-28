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

from ocp_tessellate.convert import to_assembly
from ocp_tessellate.ocp_utils import write_stl_file

# write_stl_file


def exportSTL(*cad_objs, filename="export.stl", tolerance=0.01, angular_tolerance=0.2):
    pg = to_assembly(*cad_objs)

    write_stl_file(
        pg.compound(),
        filename,
        tolerance=tolerance,
        angular_tolerance=angular_tolerance,
    )
