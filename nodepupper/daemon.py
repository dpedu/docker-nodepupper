import os
import cherrypy
import logging
from nodepupper.nodeops import NodeOps, NObject, NClass, NClassAttachment
from jinja2 import Environment, FileSystemLoader, select_autoescape
from nodepupper.common import pwhash
import math
from urllib.parse import urlparse
import yaml


APPROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))


def auth():
    """
    Return the currently authorized username (per request) or None
    """
    return cherrypy.session.get('authed', None)


def require_auth(func):
    """
    Decorator: raise 403 unless session is authed
    """
    def wrapped(*args, **kwargs):
        if not auth():
            raise cherrypy.HTTPError(403)
        return func(*args, **kwargs)
    return wrapped


def slugify(words):
    return ''.join(letter for letter in '-'.join(words.lower().split())
                   if ('a' <= letter <= 'z') or ('0' <= letter <= '9') or letter == '-')


def recurse_params(node):
    params = yaml.load(node.body)
    for item in node.parents:
        for k, v in recurse_params(item).items():
            if k not in params:
                params[k] = v
    return params


def recurse_classes(node):
    classes = {c.cls: c.conf for _, c in node.classes.items()}
    for item in node.parents:
        for cls, conf in recurse_classes(item).items():
            if cls not in classes:
                classes[cls] = conf
    return classes


class AppWeb(object):
    def __init__(self, nodedb, template_dir):
        self.nodes = nodedb
        self.tpl = Environment(loader=FileSystemLoader(template_dir),
                               autoescape=select_autoescape(['html', 'xml']))
        self.tpl.filters.update(basename=os.path.basename,
                                ceil=math.ceil,
                                statusstr=lambda x: str(x).split(".")[-1])
        self.node = NodesWeb(self)
        self.classes = ClassWeb(self)

    def render(self, template, **kwargs):
        """
        Render a template
        """
        return self.tpl.get_template(template).render(**kwargs, **self.get_default_vars())

    def get_default_vars(self):
        """
        Return a dict containing variables expected to be on every page
        """
        with self.nodes.db.transaction() as c:
            ret = {
                "classnames": c.root.classes.keys(),
                "nodenames": c.root.nodes.keys(),
                # "all_albums": [],
                "path": cherrypy.request.path_info,
                "auth": True or auth()
            }
        return ret

    @cherrypy.expose
    def node_edit(self, node=None, op=None, body=None, fqdn=None, parent=None):
        if op in ("Edit", "Create") and body and fqdn:
            with self.nodes.db.transaction() as c:
                obj = c.root.nodes[fqdn] if fqdn in c.root.nodes else NObject(fqdn, body)
                obj.body = body
                obj.parents.clear()
                parent = parent or []
                for name in [parent] if isinstance(parent, str) else parent:
                    obj.parents.append(c.root.nodes[name])
                c.root.nodes[fqdn] = obj

            raise cherrypy.HTTPRedirect("node/{}".format(fqdn), 302)
        with self.nodes.db.transaction() as c:
            yield self.render("node_edit.html", node=c.root.nodes.get(node, None))

    @cherrypy.expose
    def index(self):
        """
        """
        with self.nodes.db.transaction() as c:
            yield self.render("nodes.html", nodes=c.root.nodes.values())
        # raise cherrypy.HTTPRedirect('feed', 302)

    @cherrypy.expose
    def puppet(self, fqdn, preview=False):
        with self.nodes.db.transaction() as c:
            node = c.root.nodes[fqdn]
            doc = {"environment": "production",
                   "classes": {cls.name: yaml.load(conf) or {} for cls, conf in recurse_classes(node).items()},
                   "parameters": recurse_params(node)}
            if preview:
                yield "<plaintext>"
            yield "---\n"
            yield yaml.dump(doc, default_flow_style=False)

    @cherrypy.expose
    def login(self):
        """
        /login - enable super features by logging into the app
        """
        cherrypy.session['authed'] = cherrypy.request.login
        dest = "/feed" if "Referer" not in cherrypy.request.headers \
            else urlparse(cherrypy.request.headers["Referer"]).path
        raise cherrypy.HTTPRedirect(dest, 302)

    @cherrypy.expose
    def logout(self):
        """
        /logout
        """
        cherrypy.session.clear()
        dest = "/feed" if "Referer" not in cherrypy.request.headers \
            else urlparse(cherrypy.request.headers["Referer"]).path
        raise cherrypy.HTTPRedirect(dest, 302)

    @cherrypy.expose
    def error(self, status, message, traceback, version):
        yield self.render("error.html", status=status, message=message, traceback=traceback)


@cherrypy.popargs("node")
class NodesWeb(object):
    def __init__(self, root):
        # self.base = root
        self.nodes = root.nodes
        self.render = root.render

    @cherrypy.expose
    def index(self, node):
        with self.nodes.db.transaction() as c:
            yield self.render("node.html", node=c.root.nodes[node])

    @cherrypy.expose
    def op(self, node, op, clsname=None, config=None, parent=None):
        with self.nodes.db.transaction() as c:
            if op == "Attach" and clsname and config:
                # TODO validate yaml
                c.root.nodes[node].classes[clsname] = NClassAttachment(c.root.classes[clsname], config)
            elif op == "Add Parent" and parent:
                c.root.nodes[node].parents.append(c.root.nodes[parent])
            elif op == "detach" and clsname:
                del c.root.nodes[node].classes[clsname]
            else:
                raise Exception("F")
        raise cherrypy.HTTPRedirect("/node/{}".format(node), 302)


@cherrypy.popargs("cls")
class ClassWeb(object):
    def __init__(self, root):
        self.root = root
        self.nodes = root.nodes
        self.render = root.render

    @cherrypy.expose
    def index(self, cls=None):
        # with self.nodes.db.transaction() as c:
        yield self.render("classes.html")

    @cherrypy.expose
    def op(self, cls, op=None, name=None):
        # with self.nodes.db.transaction() as c:
        yield self.render("classes.html")

    @cherrypy.expose
    def add(self, op, name):
        with self.nodes.db.transaction() as c:
            if op == "Create":
                if name not in c.root.classes:
                    c.root.classes[name] = NClass(name)
        raise cherrypy.HTTPRedirect("/classes/{}".format(name), 302)


def main():
    import argparse
    import signal

    parser = argparse.ArgumentParser(description="Photod photo server")

    parser.add_argument('-p', '--port', default=8080, type=int, help="tcp port to listen on")
    # parser.add_argument('-l', '--library', default="./library", help="library path")
    # parser.add_argument('-c', '--cache', default="./cache", help="cache path")
    parser.add_argument('-s', '--database', default="./pupper.db", help="path to persistent sqlite database")
    parser.add_argument('--debug', action="store_true", help="enable development options")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.debug else logging.WARNING,
                        format="%(asctime)-15s %(levelname)-8s %(filename)s:%(lineno)d %(message)s")

    library = NodeOps(args.database)

    tpl_dir = os.path.join(APPROOT, "templates") if not args.debug else "templates"

    web = AppWeb(library, tpl_dir)

    def validate_password(realm, username, password):
        s = library.session()
        if s.query(User).filter(User.name == username, User.password == pwhash(password)).first():
            return True
        return False

    cherrypy.tree.mount(web, '/', {'/': {'tools.trailing_slash.on': False,
                                         'error_page.403': web.error,
                                         'error_page.404': web.error},
                                   '/static': {"tools.staticdir.on": True,
                                               "tools.staticdir.dir": os.path.join(APPROOT, "styles/dist")
                                               if not args.debug else os.path.abspath("styles/dist")},
                                   '/login': {'tools.auth_basic.on': True,
                                              'tools.auth_basic.realm': 'webapp',
                                              'tools.auth_basic.checkpassword': validate_password}})

    cherrypy.config.update({
        'tools.sessions.on': True,
        'tools.sessions.locking': 'explicit',
        'tools.sessions.timeout': 525600,
        'request.show_tracebacks': True,
        'server.socket_port': args.port,
        'server.thread_pool': 25,
        'server.socket_host': '0.0.0.0',
        'server.show_tracebacks': True,
        'log.screen': False,
        'engine.autoreload.on': args.debug
    })

    def signal_handler(signum, stack):
        logging.critical('Got sig {}, exiting...'.format(signum))
        cherrypy.engine.exit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        cherrypy.engine.start()
        cherrypy.engine.block()
    finally:
        logging.info("API has shut down")
        cherrypy.engine.exit()


if __name__ == '__main__':
    main()
