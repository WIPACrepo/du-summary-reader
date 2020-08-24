import os
import random
import webbrowser
from urllib.parse import urlencode
from collections import namedtuple
import functools

import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, data):
        self.data = data

    def get(self):
        path = self.get_argument('path', self.data.default_path)
        print('path:',path)

        try:
            data = self.data.find(path)
        except Exception:
            raise tornado.web.HTTPError(400, 'bad path')

        output = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Du """+path+"""</title>
    <style>
        section.action article {
            margin: .5em;
        }
        article div.text, article div.select {
            margin: .5em 0;
            display: flex;
            align-items: center;
        }
        article span.label {
            margin-right: 0.5em;
        }
        article div.select div.selectize-control, article select {
            width: 100%;
        }
        article div.text, article div.select {
            margin: .5em 0;
            display: flex;
            align-items: center;
        }
        article>div {
            margin: 1em 1em;
        }
        article div.entry {
            display: flex;
            margin: .5em 0;
        }
        article div.entry div {
            display: inline-block;
            margin-left: .5em;
        }
        article div.entry div.name {
            width: 20em;
        }
        article div.entry div.value {
            width: 7em;
            text-align: right;
        }
        article div.entry div.graph {
            width: 7em;
            text-align: right;
            margin-right: 1em;
            position: relative;
        }
        article div.entry div.graph .text, article div.entry div.graph .text_small {
            position: absolute;
            width: 100%;
            margin: 0;
            z-index: 1;
        }
        article div.entry div.graph .text {
            right: 0;
            color: white;
        }
        article div.entry div.graph .fill {
            background-color: green;
            margin:0;
            padding:0;
            height: 100%;
            z-index: 0;
        }
        article div.header {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <header><h1>Du Summary File Browser</h1></header>
    <main>
        <article>"""
        output += f'<h3>Path: { path }</h3><div class="grid">'
        if path != self.data.default_path:
            output += f'<a href="/?{ urlencode({"path":os.path.dirname(path)}) }">&lt;&lt; Up</a><div>'
        output += '<div class="entry header"><div class="name">Name</div><div class="value">Size (GB)</div><div class="graph">Size %</div></div>'
        for row in data.children:
            output += f'<div class="entry"><div class="name">{ row.name }</div><div class="value">{ (row.size/10**9) :.2f}</div><div class="graph"><'
            percent_size = row.size*100//data.entry.size 
            if percent_size < 20:
                output += f'div class="text_small" style="right:{ percent_size+5 }%">{ percent_size }</div>'
            else:
                output += f'div class="text">{ percent_size }</div>'
            output += f'<div class="fill" style="width: { percent_size }%"></div></div>'
            if row.num > 1:
                output += f'<div class="details"><a href="/?{ urlencode({"path":row.path}) }">Details</a></div>'
            output += '</div>'
        output += f'<div class="entry header"><div class="name">Total</div><div class="value">{ data.entry.size/10**9 :.2f}</div></div>'
        output += """</div></article>
    </main>
</body>
</html>
"""
        self.write(output)

Row = namedtuple('Row', ['name', 'path', 'size', 'num'])
CacheEntry = namedtuple('CacheEntry', ['entry', 'children'])

class DuSummary:
    def __init__(self, filename):
        self.filename = filename
        self.default_path = '/'
        with open(self.filename) as f:
            for line in f:
                if line.startswith('/'):
                    self.default_path = line.split()[0]
                    break
            else:
                raise Exception('.du_summary file appears to be empty')

    @functools.lru_cache(maxsize=10000)
    def find(self, path):
        entry = None
        children = []
        with open(self.filename) as f:
            for line in f:
                if line.startswith(path):
                    parts = line.split()
                    if parts[0] == path:
                        entry = Row(parts[0].split('/')[-1], parts[0], int(parts[1]), int(parts[2]))
                    elif os.path.dirname(parts[0]) == path:
                        children.append(Row(parts[0].split('/')[-1], parts[0], int(parts[1]), int(parts[2])))
            else:
                if entry == None:
                    raise Exception()
        return CacheEntry(entry, children)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='.du_summary html browser')
    parser.add_argument('infile',help='input .du_summary file')

    args = parser.parse_args()

    data = DuSummary(args.infile)

    kwargs = {'data': data}
    app = tornado.web.Application([
        (r'/', MainHandler, kwargs),
    ], debug=True, autoescape=None)

    while True: # find an unused port we can bind to
        port = random.randint(10000,64000)
        try:
            app.listen(port)
        except Exception:
            continue
        break

    webbrowser.open('http://localhost:{}/'.format(port))
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()
