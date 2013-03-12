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
import subprocess
import tempfile
import os


class PandocCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_quick_panel(
            self._setting('formats').keys(), self.transform)

    def transform(self, format_to):
        # to format
        formats = self._setting('formats')
        if format_to == -1:
            return
        format_to = formats[formats.keys()[format_to]]

        view = self.window.active_view()

        # string to work with
        region = sublime.Region(0, view.size())
        contents = view.substr(region)

        # from format
        format_from = self._from(view)
        if format_from is None:
            sublime.message_dialog('Current scope "' +
                view.scope_name(view.sel()[0].end()).strip() +
                '"not configured as a format Pandoc can convert.')
            return

        # pandoc params
        cmd = [self.find_binary('pandoc')]
        # configured options
        if 'from' in format_from:
            cmd.extend(format_from['from'])
        if 'to' in format_to:
            cmd.extend(format_to['to'])
        # if -o required, write to temp file
        tf = False
        if format_to['pandoc'] in ['docx', 'epub']:
            if not ('to' in format_to and '-o' in format_to['to']):
                tf = tempfile.NamedTemporaryFile().name
                tfname =  tf + "." + format_to['pandoc']
                cmd.extend(['-o', tfname])
        cmd.extend(['-f', format_from['pandoc'], '-t', format_to['pandoc']])

        # run pandoc
        process = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result, error = process.communicate(contents.encode('utf-8'))

        # replace buffer and set syntax
        if tf:
            if format_to['pandoc'] == 'docx' and sublime.platform() == 'osx':
                subprocess.call(["open", tfname])
            else:
                sublime.message_dialog('Wrote to file ' + tfname)
        if result:
            edit = view.begin_edit()
            view.replace(edit, region, result.decode('utf8'))
            if 'syntax_file' in format_to:
                view.set_syntax_file(format_to['syntax_file'])
            view.end_edit(edit)
        if error:
            sublime.error_message(error)

    def _from(self, view):
        max_key = None
        max_score = 0
        for key, form in self._setting('formats').iteritems():
            if 'scope' in form and form['scope'] != '':
                score = view.score_selector(0, form['scope'])
                if score > max_score:
                    max_score = score
                    max_key = key
        return self._setting('formats')[max_key]

    def _setting(self, key):
        return sublime.load_settings('Pandoc.sublime-settings').get(key)

    def find_binary(self, name):
        if self._setting('pandoc-path') is not None:
            return os.path.join(self._setting('pandoc-path'), name)

        # Try the path first
        for dir in os.environ['PATH'].split(os.pathsep):
            path = os.path.join(dir, name)
            if os.path.exists(path):
                return path

        dirs = ['/usr/local/bin']

        for dir in dirs:
            path = os.path.join(dir, name)
            if os.path.exists(path):
                return path

        return None

