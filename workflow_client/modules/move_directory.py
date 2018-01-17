# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Redistributions for commercial purposes are not permitted without the
# Allen Institute's written permission.
# For purposes of this license, commercial purposes is the incorporation of the
# Allen Institute's software into anything for which you will charge fees or
# other compensation. Contact terms@alleninstitute.org for commercial licensing
# opportunities.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import simplejson as json

import subprocess
import argparse
import sys
import logging
from matplotlib.compat.subprocess import CalledProcessError


if __name__ == "__main__" and __package__ is None:
    __package__ = "workflow_client.modules.move_tile_set"

example = {
    'from': '/source/path',
    'to': '/destination/path'
}

class MoveDirectory(object):
    log = logging.getLogger('workflow_client.modules.move_directory')

    def __init__(self, cmd):
        self.cmd = cmd

    def move(self, frm, to, extra_flags=None):
        executable_command = []
        executable_command.extend(self.cmd.split(' '))

        if extra_flags is not None:
            executable_command.extend(extra_flags.split(' '))

        executable_command.extend([frm, to])

        print("RUNNING: " + ' '.join(executable_command)) 

        try: 
            console_txt = subprocess.check_output(
                executable_command,
                stderr=subprocess.STDOUT)
            print(console_txt)
        except CalledProcessError as e:
            print(e.output)
            return e.returncode

        return 0

    @classmethod
    def parse_json(cls, json_string):
        return json.loads(json_string)

    @classmethod
    def parse_json_file(cls, json_file):
        with open(json_file, 'r') as f:
            return MoveDirectory.parse_json(f.read())

    @classmethod
    def parse_args(cls, args):
        parser = argparse.ArgumentParser(
            description='move tile set files to long term storage')
        parser.add_argument('--input_json', help='input arguments')
        parser.add_argument('--output_json', help='output results')

        return vars(parser.parse_args(args))
    
    @classmethod
    def main(cls, args):
        parsed_args = MoveDirectory.parse_args(args[1:])
        inp = MoveDirectory.parse_json_file(parsed_args['input_json'])

        extra_args = inp.get('extra', '')

        cmd = '/bin/rsync -ravL'

        mts = MoveDirectory(cmd)
        result = mts.move(inp['from'], inp['to'], extra_args)

        with open(parsed_args['output_json'], 'w') as f:
            f.write(json.dumps(inp))
        
        return result


if '__main__' == __name__:
    sys.exit(MoveDirectory.main(sys.argv))
