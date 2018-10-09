#!/usr/bin/env python3

import ZODB
import ZODB.FileStorage

def main():
    storage = ZODB.FileStorage.FileStorage("pupper.db")
    db = ZODB.DB(storage)
    for k, v in db.open().root.nodes.items():
        print(k, v.name, ":", v, "\n\t", v.body, "\n")

if __name__ == "__main__":
    main()
