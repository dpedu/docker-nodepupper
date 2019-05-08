from urllib.parse import urlparse
import ZODB
from relstorage.storage import RelStorage
from relstorage.options import Options
from relstorage.adapters.mysql import MySQLAdapter
import persistent
import persistent.list
import persistent.mapping
import BTrees.OOBTree


def plist():
    return persistent.list.PersistentList()


def pmap():
    return persistent.mapping.PersistentMapping()


class NObject(persistent.Persistent):
    def __init__(self, fqdn, body):
        self.fqdn = fqdn
        self.parents = plist()
        self.classes = pmap()
        self.body = body

    def parent_names(self):
        return [n.fqdn for n in self.parents]

    def class_names(self):
        return list(self.classes.keys())


class NClass(persistent.Persistent):
    def __init__(self, name):
        self.name = name


class NClassAttachment(persistent.Persistent):
    def __init__(self, cls, conf):
        self.cls = cls
        self.conf = conf


class NodeOps(object):
    def __init__(self, db_uri):
        uri = urlparse(db_uri)

        self.mysql = MySQLAdapter(host=uri.hostname, user=uri.username, passwd=uri.password, db=uri.path[1:],
                                  options=Options(keep_history=False))
        self.storage = RelStorage(adapter=self.mysql)
        self.db = ZODB.DB(self.storage)

        with self.db.transaction() as c:
            if "nodes" not in c.root():
                c.root.nodes = BTrees.OOBTree.BTree()
            if "classes" not in c.root():
                c.root.classes = BTrees.OOBTree.BTree()

    def rename_node(self, c, node, newname):
        # check new name isnt taken
        if newname in c.root.nodes:
            raise Exception(f"{newname} already exists")

        # move in root
        del c.root.nodes[node.fqdn]
        node.fqdn = newname
        c.root.nodes[node.fqdn] = node
