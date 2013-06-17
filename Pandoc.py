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

    def transform(self, format_dest):
        formats = {'src': None, 'dest': None}

        # dest format
        if format_dest == -1:
            return
        format_dest = self._setting('formats').keys()[format_dest]
        formats['dest'] = self._format_conf(format_dest)

        view = self.window.active_view()

        # string to work with
        region = sublime.Region(0, view.size())
        contents = view.substr(region)

        # source format
        formats['src'] = self._src_format(view)
        if formats['src'] is None:
            sublime.message_dialog(
                'Current scope "' +
                view.scope_name(view.sel()[0].end()).strip() +
                '"not configured as a format Pandoc can convert.')
            return

        # pandoc params
        cmd = [self._find_binary('pandoc')]
        # configured options
        if 'from' in formats['src']:
            cmd.extend(formats['src']['from'])
        if 'to' in formats['dest']:
            cmd.extend(formats['dest']['to'])
        # if -o required, write to temp file
        tf = False
        if formats['dest']['key'] in ['docx', 'epub', 'pdf']:
            if not ('to' in formats['dest'] and '-o' in formats['dest']['to']):
                tf = tempfile.NamedTemporaryFile().name
                tfname = tf + "." + formats['dest']['key']
                cmd.extend(['-o', tfname])
        # PDF output
        if formats['dest']['key'] == 'pdf':
            # pandoc assumes pdf from destination file extension
            cmd.extend(['-f', formats['src']['key']])
        else:
            cmd.extend(['-f', formats['src']['key'], '-t', formats['dest']['key']])

        # run pandoc
        process = subprocess.Popen(
            cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        result, error = process.communicate(contents.encode('utf-8'))

        # write some formats to tmp file and possibly open
        if tf:
            try:
                if sublime.platform() == 'osx':
                    subprocess.call(["open", tfname])
                elif sublime.platform() == 'windows':
                    os.startfile(tfname)
            except:
                sublime.message_dialog('Wrote to file ' + tfname)

        if result:

            # write to new buffer and set syntax
            if self._setting('new-buffer'):
                w = view.window()
                w.new_file()
                edit = w.active_view().begin_edit()
                w.active_view().replace(edit, region, result.decode('utf8'))
                if 'syntax_file' in formats['dest']:
                    w.active_view().set_syntax_file(formats['dest']['syntax_file'])
                w.active_view().end_edit(edit)

            # replace buffer and set syntax
            else:
                edit = view.begin_edit()
                view.replace(edit, region, result.decode('utf8'))
                if 'syntax_file' in formats['dest']:
                    view.set_syntax_file(formats['dest']['syntax_file'])
                view.end_edit(edit)

        if error:
            sublime.error_message(error)

    def _src_format(self, view):
        '''
        use sublime.score_selector() to determine the current Pandoc format from
        the current document syntax.
        '''
        max_label = None
        max_score = 0
        for label in self._setting('formats').iterkeys():
            conf = self._format_conf(label)
            # scope implies pandoc can accept the format as input
            if 'scope' in conf and conf['scope'] != '':
                score = view.score_selector(0, conf['scope'])
                if score > max_score:
                    max_score = score
                    max_label = label
        return self._format_conf(max_label)

    def _setting(self, key):
        return sublime.load_settings('Pandoc.sublime-settings').get(key)

    def _format_conf(self, label):
        '''
        Generate a hash of format configuration.
        @see Pandoc.sublime-settings

        Keyword arguments:
        label -- format label used in settings

        Returns:
        hash of any configured settings, plus "key" which is the pandoc format
        (-f or -t values)
        '''
        key = self._setting('formats')[label]
        conf = self._setting('format_' + key)
        conf['key'] = key
        return conf

    def _find_binary(self, name):
        path = self._setting(name + '-path')
        if path is not None:
            if os.path.exists(path):
                return path
            msg = 'configured path for {0} {1} not found.'.format(name, path)
            sublime.error_message(msg)
            return None

        # Try the path first
        for dirname in os.environ['PATH'].split(os.pathsep):
            path = os.path.join(dirname, name)
            if os.path.exists(path):
                return path

        dirnames = ['/usr/local/bin']

        for dirname in dirnames:
            path = os.path.join(dirname, name)
            if os.path.exists(path):
                return path

        return None
