#!/usr/bin/env python3

import ZODB
import ZODB.FileStorage

# def main():
#     storage = ZODB.FileStorage.FileStorage("pupper.db")
#     db = ZODB.DB(storage)
#     for k, v in db.open().root.nodes.items():
#         print(k, v.name, ":", v, "\n\t", v.body, "\n")

# def main():
#     storage = ZODB.FileStorage.FileStorage("pupper.db")
#     db = ZODB.DB(storage)
#     for k, v in db.open().root.nodes["foo2"].classes.items():
#         # print(k, v.name, ":", v, "\n\t", v.body, "\n")
#         print(v.conf)


def main():
    storage = ZODB.FileStorage.FileStorage("pupper.db")
    db = ZODB.DB(storage)
    with db.transaction() as c:
        for host in ("scc", "root", "puppettest5.scc.net.davepedu.com"):
            if "foo2" in c.root.nodes[host].classes:
                del c.root.nodes[host].classes["foo2"]
        # del c.root.nodes["scc"].classes["foo2"]

# def main():
#     storage = ZODB.FileStorage.FileStorage("pupper.db")
#     db = ZODB.DB(storage)
#     with db.transaction() as c:
#         print(c.root.nodes["puppettest5.scc.net.davepedu.com"].parents)


if __name__ == "__main__":
    main()
