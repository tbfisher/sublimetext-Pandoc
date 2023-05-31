# Copyright (c) 2012 Brian Fisher
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import sublime
import sublime_plugin
from collections import OrderedDict
import pprint
import re
import subprocess
import tempfile
import os
import threading

from .thread_progress import ThreadProgress
from .edit import Edit


class PromptPandocCommand(sublime_plugin.WindowCommand):

    '''Defines the plugin command palette item.

    @see Default.sublime-commands'''

    options = []
    last_selected = 0

    def run(self):
        if self.window.active_view():
            self.window.show_quick_panel(
                self.transformations(),
                self.transform,
                selected_index=self.last_selected)

    def transformations(self):
        '''Generates a ranked list of available transformations.'''
        view = self.window.active_view()

        # hash of transformation ranks
        ranked = {}
        for label, settings in _s('transformations').items():
            for scope in settings['scope'].keys():
                score = view.score_selector(0, scope)
                if not score:
                    continue
                if label not in ranked or ranked[label] < score:
                    ranked[label] = score

        if not len(ranked):
            sublime.error_message(
                'No transformations configured for the syntax '
                + view.settings().get('syntax'))
            return

        # reverse sort
        self.options = list(OrderedDict(sorted(
            ranked.items(), key=lambda t: t[1])).keys())
        self.options.reverse()

        return self.options

    def transform(self, i):
        if i == -1:
            return
        self.last_selected = i
        transformation = _s('transformations')[self.options[i]]
        self.window.active_view().run_command('pandoc', {
            'transformation': transformation
        })


class PandocCommand(sublime_plugin.TextCommand):

    '''Transforms using Pandoc.'''

    def run(self, edit, transformation):

        # string to work with
        region = sublime.Region(0, self.view.size())
        contents = self.view.substr(region)

        # pandoc executable
        binary_name = 'pandoc.exe' if sublime.platform() == 'windows' else 'pandoc'
        pandoc = _find_binary(binary_name, _s('pandoc-path'))
        if pandoc is None:
            return
        cmd = [pandoc]

        # from format
        score = 0
        for scope, c_iformat in transformation['scope'].items():
            c_score = self.view.score_selector(0, scope)
            if c_score <= score:
                continue
            score = c_score
            iformat = c_iformat
        cmd.extend(['-f', iformat])

        # configured parameters
        args = Args(transformation['pandoc-arguments'])
        # Use pandoc output format name as file extension unless specified by out-ext in transformation
        try:
            transformation['out-ext']
        except:
            argsext = None
        else:
            argsext = transformation['out-ext']
        # output format
        oformat = args.get(short=['t', 'w'], long=['to', 'write'])
        oext = argsext

        # pandoc doesn't actually take 'pdf' as an output format
        # see https://github.com/jgm/pandoc/issues/571
        if oformat == 'pdf':
            args = args.remove(
                short=['t', 'w'], long=['to', 'write'], values=['pdf'])

        # output file locally
        try:
            transformation['out-local']
        except:
            argslocal = None
        else:
            argslocal = transformation['out-local']

        # get current file path
        current_file_path = self.view.file_name()
        if current_file_path:
            working_dir = os.path.dirname(current_file_path)
            file_name = os.path.splitext(current_file_path)[0]
        else:
            working_dir = None
            file_name = None

        # if write to file, add -o if necessary, set file path to output_path
        output_path = None
        if oformat is not None and oformat in _s('pandoc-format-file'):
            output_path = args.get(short=['o'], long=['output'])
            if output_path is None:
                # note the file extension matches the pandoc format name
                if argslocal and file_name:
                    output_path = file_name
                else:
                    output_path = tempfile.NamedTemporaryFile().name
                # If a specific output format not specified in transformation, default to pandoc format name
                if oext is None:
                    output_path += "." + oformat
                else:
                    output_path += "." + oext
                args.extend(['-o', output_path])

        cmd.extend(args)

        # write pandoc command to console
        print(' '.join(cmd))

        thread = PandocThread(
            cmd, working_dir, contents, oformat, output_path, transformation,
            self.view)
        thread.start()
        ThreadProgress(thread, 'Running Pandoc', 'Done!')


class PandocThread(threading.Thread):
    def __init__(self, cmd, working_dir, contents, oformat, output_path,
                 transformation, view):
        super().__init__()
        self.cmd = cmd
        self.working_dir = working_dir
        self.contents = contents
        self.oformat = oformat
        self.output_path = output_path
        self.transformation = transformation
        self.view = view

    def run(self):
        # run pandoc
        process = subprocess.Popen(
            self.cmd, shell=False, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.working_dir)
        result, error = process.communicate(self.contents.encode('utf-8'))

        # handle pandoc errors
        if error:
            sublime.error_message('\n\n'.join([
                'Error when running:',
                ' '.join(self.cmd),
                error.decode('utf-8').strip()]))
            return

        # if write to file, open
        if self.oformat is not None and \
           self.oformat in _s('pandoc-format-file'):
            try:
                if sublime.platform() == 'osx':
                    subprocess.call(["open", self.output_path])
                elif sublime.platform() == 'windows':
                    os.startfile(self.output_path)
                elif os.name == 'posix':
                    subprocess.call(('xdg-open', self.output_path))
            except:
                sublime.message_dialog('Wrote to file ' + self.output_path)
            return

        # write to buffer
        if result:
            if self.transformation['new-buffer']:
                w = self.view.window()
                w.new_file()
                view = w.active_view()
                region = sublime.Region(0, view.size())
            else:
                view = self.view
                region = sublime.Region(0, view.size())

            with Edit(view) as edit:
                edit.replace(
                    region, result.decode('utf8').replace('\r\n', '\n'))

            view.set_syntax_file(self.transformation['syntax_file'])
            view.sel().clear()


def _find_binary(name, default=None):
    '''Returns a configure path or looks for an executable on the system path.
    '''

    if default is not None:
        if os.path.exists(default):
            return default
        msg = 'configured path for {0} {1} not found.'.format(name, default)
        sublime.error_message(msg)
        return None

    for dirname in os.environ['PATH'].split(os.pathsep):
        path = os.path.join(dirname, name)
        if os.path.exists(path):
            return path

    sublime.error_message('Could not find pandoc executable on PATH.')
    return None


def _s(key):
    '''Convenience function for getting the setting dict.'''
    return merge_user_settings()[key]


def merge_user_settings():
    '''Return the default settings merged with the user's settings.'''

    settings = sublime.load_settings('Pandoc.sublime-settings')
    default = settings.get('default', {})
    user = settings.get('user', {})

    if user:

        # merge each transformation
        transformations = default.pop('transformations', {})
        user_transformations = user.get('transformations', {})
        for name, data in user_transformations.items():
            if name in transformations:
                transformations[name].update(data)
            else:
                transformations[name] = data
        default['transformations'] = transformations
        user.pop('transformations', None)

        # merge all other keys
        default.update(user)

    return default


def _c(item):
    '''Pretty prints item to console.'''
    pprint.PrettyPrinter().pprint(item)


class Args(list):

    '''Process Pandoc arguments.

    "short" are of the form "-k val""".
    "long" arguments are of the form "--key=val""".'''

    def get(self, short=None, long=None):
        '''Get the first value for a argument.'''
        value = None
        for arg in self:
            if short is not None:
                if value:
                    return arg
                match = re.search('^-(' + '|'.join(short) + ')$', arg)
                if match:
                    value = True  # grab the next arg
                    continue
            if long is not None:
                match = re.search('^--(' + '|'.join(long) + ')=(.+)$', arg)
                if match:
                    return match.group(2)
        return None

    def remove(self, short=None, long=None, values=None):
        '''Remove all matching arguments.'''
        ret = Args([])
        value = None
        for arg in self:
            if short is not None:
                if value:
                    if values is not None and arg not in values:
                        ret.append(arg)
                    value = None
                    continue
                match = re.search('^-(' + '|'.join(short) + ')$', arg)
                if match:
                    value = True  # grab the next arg
                    continue
            if long is not None:
                match = re.search('^--(' + '|'.join(long) + ')=(.+)$', arg)
                if match:
                    continue
            ret.append(arg)
        return ret
