import ZODB
import ZODB.FileStorage
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


class NClass(persistent.Persistent):
    def __init__(self, name):
        self.name = name


class NClassAttachment(persistent.Persistent):
    def __init__(self, cls, conf):
        self.cls = cls
        self.conf = conf


class NodeOps(object):
    def __init__(self, db_path):
        self.storage = ZODB.FileStorage.FileStorage(db_path)
        self.db = ZODB.DB(self.storage)

        with self.db.transaction() as c:
            if "nodes" not in c.root():
                c.root.nodes = BTrees.OOBTree.BTree()
            if "classes" not in c.root():
                c.root.classes = BTrees.OOBTree.BTree()
