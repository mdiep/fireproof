#!/usr/bin/env python3

import codecs
from datetime import datetime, time
from operator import attrgetter
import optparse
import os
import shutil

import jinja2
import markdown2
import yaml

VERSION = '0.1.0'

from html.entities import codepoint2name

# register a codec to handle escaping non-ASCII characters
def named_entities(text):
    if isinstance(text, (UnicodeEncodeError, UnicodeTranslateError)):
        s = []
        for c in text.object[text.start:text.end]:
            if ord(c) in codepoint2name:
                s.append(u'&%s;' % codepoint2name[ord(c)])
            else:
                s.append(u'&#%s;' % ord(c))
        return ''.join(s), text.end
    else:
        raise TypeError("Can't handle %s" % text.__name__)
codecs.register_error('named_entities', named_entities)

def splittype(path):
    name, ext = os.path.splitext(path)
    if ext == ".md":
        name, ext = os.path.splitext(name)
    return (name, ext[1:])
  

class Page(object):
    def __init__(self, site, path):
        self.site = site
        self.path = path

        root, type = splittype(self.path)
        self.type = type
        self.file = root + site.page_exts[self.type]
        self.url  = os.path.normpath(os.path.join('/', self.file))
        if self.url.endswith('index.html'):
            self.url = self.url[:-10]


        contents = open(os.path.join(self.site.directory, self.path)).read()
        idx = contents.find('\n\n')
        if idx != -1:
            data, text = contents[:idx], contents[idx:]

            for key, value in yaml.safe_load(data).items():
                setattr(self, key, value)

            self.text = markdown2.markdown(text, extras=["fenced-code-blocks", "footnotes"])
        else:
            data = yaml.safe_load(contents)
            if data:
                for key, value in data.items():
                    setattr(self, key, value)

    def __str__(self):
        try:
            template = '_' + self.type + self.site.page_exts[self.site.current_page.type]
            template = self.site.template_env.get_template(template)
            return self.site.render(self, template)
        except jinja2.TemplateNotFound:
            return self.text

    @property
    def absolute_url(self):
        if self.site.url[-1] == '/':
            return self.site.url + self.url[1:]
        else:
            return self.site.url + self.url

    @property
    def directory(self):
        return os.path.split(self.url)[0]

    @property
    def tag(self):
        url = self.absolute_url

        # discard everything before the domain name
        idx = url.index('://') + 3
        tag = url[idx:]

        # change all #s to /s
        tag.replace('#', '/')

        # insert ,year-mm-dd:
        idx  = url.index('/')
        date = self.date.strftime('%Y-%m-%d')
        tag  = tag[:idx] + ',' + date + ':' + tag[idx:]

        # add tag: at the beginning
        tag = 'tag:' + tag

        return tag

class Site(object):
    def __init__(self, dir):
        initpath = os.path.join(dir, '.fireproof')
        if os.path.isfile(initpath):
            data = open(initpath).read()
            for key, value in yaml.safe_load(data).items():
                setattr(self, key, value)

        self.directory      = dir
        self.subdirectories = []
        self.files          = []
        self.pages          = []
        self.static_files   = []
        self.template_dir   = os.path.join(dir, 'templates')
        self.page_exts      = {}
        self.pages          = {}

        # 1) find templates and infer page types
        self.find_templates()

        # 2) set up template environment
        loader = jinja2.FileSystemLoader(self.template_dir)
        env    = jinja2.Environment(loader=loader)
        env.filters['markdown'] = lambda x: markdown2.markdown(x) if x else ""
        env.filters['rfc3339']  = lambda x: x.strftime('%Y-%m-%dT%H:%M:%SZ')
        env.filters['strftime'] = datetime.strftime
        env.globals['pages']    = find_pages
        self.template_env = env

        # 3) make a list of all directories and files: pages, images
        for dirpath, dirs, files in os.walk(self.directory):
            self.add_dirs_and_files(dirpath, dirs, files)

    def should_ignore_dir(self, path):
        name = os.path.split(path)[1]
        if path == self.template_dir:
            return True
        if name.startswith("."):
            return True
        return False

    def should_ignore_file(self, path):
        name = os.path.split(path)[1]
        if name.startswith("."):
            return True
        return False

    def add_dirs_and_files(self, dirpath, dirs, files):
        """
        Find all the directories and files in the site.

        This function is used in conjunction with os.walk().
        """

        dirpath = os.path.relpath(dirpath, self.directory)

        dirs_to_delete = []
        for i, name in enumerate(dirs):
            path = os.path.join(dirpath, name)
            if self.should_ignore_dir(path):
                dirs_to_delete.append(i)
                continue

            self.subdirectories.append(path)
        # remove directories from dirs so that os.walk won't visit them
        for i in reversed(dirs_to_delete):
            del dirs[i]

        for name in files:
            path = os.path.join(dirpath, name)
            type = splittype(path)[1]
            if self.should_ignore_file(path):
                continue

            self.files.append(path)
            if type in self.pages:
                page = Page(self, path)
                self.pages[type].append(page)
            else:
                self.static_files.append(path)

    def find_templates(self):
        for file in os.listdir(self.template_dir):
            if os.path.isdir(file):
                continue;

            name, ext = os.path.splitext(file)
            if name[0] == '_':
                name = name[1:]

            self.page_exts[name] = ext
            self.pages[name] = []

    def render_to_dir(self, output_dir):
        # 1) make the output directory and all subdirectories
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        for dir in self.subdirectories:
            path = os.path.join(output_dir, dir)
            if not os.path.isdir(path):
                os.mkdir(path)

        # 2) copy over all static files
        for path in self.static_files:
            src_path  = os.path.join(self.directory, path)
            dest_path = os.path.join(output_dir, path)
            shutil.copyfile(src_path, dest_path)

        # 3) process all pages
        for type in self.pages:
            ext = self.page_exts[type]
            for page in self.pages[type]:
                self.current_page = page
                try:
                    template = type + self.page_exts[type]
                    template = self.template_env.get_template(template)
                except jinja2.TemplateNotFound:
                    template = 'page' + self.page_exts['page']
                    template = self.template_env.get_template(template)
                fullpath = os.path.join(output_dir, page.file)
                stream   = codecs.open(fullpath, 'w', encoding='UTF-8')
                for line in self.render(page, template):
                    if ext == '.html':
                        line = line.encode('ascii', 'named_entities').decode('UTF-8')
                    stream.write(line)
                self.current_page = None

    def render(self, page, template):
        context  = {
            'site':    self,
            'page':    page,
            page.type: page,
            'now':     datetime.utcnow(),
        }
        return template.render(**context)

def find_pages(site, types=[], directory=None, limit=None, order_by=[]):
    if not types:
        types = site.pages.keys()
    result = []
    for type in types:
        for p in site.pages[type]:
            result.append(p)

    if directory:
        result = [p for p in result if p.directory.startswith(directory)]

    for key in reversed(order_by):
        reverse = False
        if key[0] == '-':
            key = key[1:]
            reverse = True
        result = sorted(result, key=attrgetter(key), reverse=reverse)

    # enforce limit
    if limit:
        result = result[:limit]

    return result

def main():
    parser = optparse.OptionParser(usage="%prog [options] site_dir output_dir", version="%prog " + VERSION)
    parser.add_option("-f", "--force", dest="force", action="store_true", default=False,
                      help="force output to a non-empty directory")

    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.error("incorrect number of arguments")

    site_dir   = args[0]
    output_dir = args[1]

    # Check that the site and output directories meet the requirements
    if not os.path.exists(site_dir):
        parser.error("site directory '%s' doesn't exist" % site_dir)
    if not os.path.isdir(site_dir):
        parser.error("site directory '%s' isn't a directory" % site_dir)
    if os.path.exists(output_dir) and not os.path.isdir(output_dir):
        parser.error("output directory '%s' isn't a directory" % output_dir)
    if not options.force and os.path.isdir(output_dir) and len(os.listdir(output_dir)) != 0:
        parser.error("output directory '%s' must be empty" % output_dir)

    site = Site(site_dir)
    site.render_to_dir(output_dir)

if __name__ == '__main__':
    main()
