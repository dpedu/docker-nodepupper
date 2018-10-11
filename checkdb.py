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
        del c.root.nodes["puppettest5.scc.net.davepedu.com"].classes["base2"]
    # for k, v in db.open().root.nodes["foo2"].classes.items():
    #     # print(k, v.name, ":", v, "\n\t", v.body, "\n")
    #     print(v.conf

if __name__ == "__main__":
    main()
