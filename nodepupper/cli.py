from appdirs import user_config_dir
import os
import json
import yaml
import argparse
import requests
import tempfile
import subprocess


APPNAME = "npcli"
CONFDIR = user_config_dir(APPNAME)
CONFPATH = os.path.join(CONFDIR, "conf.json")  # ~/Library/Application Support/npcli/conf.json


def editorloop(fpath, validator):
    """
    Open the editor until the user provides valid yaml.
    Raises if we fail to edit the file.
    """
    content = ""
    while True:
        subprocess.check_call([os.environ["EDITOR"], fpath])  # XXX commented for testing
        with open(fpath) as f:
            content = f.read()
            try:
                yaml.load(content)
                break
            except Exception as e:
                print(e)
                if input("Reopen editor? Y/n: ").lower() in ["", "y"]:
                    continue
                else:
                    raise
    return content


def main():
    conf = {"host": "", "username": "", "password": ""}
    if os.path.exists(CONFPATH):
        with open(CONFPATH) as cf:
            conf = json.load(cf)
    else:
        os.makedirs(CONFDIR, exist_ok=True)
        with open(CONFPATH, "w") as cf:
            json.dump(conf, cf)

    parser = argparse.ArgumentParser(description="Nodepupper cli",
                                     epilog="host/username/password will be saved to {} "
                                            "after first use.".format(CONFPATH))

    parser.add_argument("--host", help="http/s host to connect to",
                        default=os.environ.get('NPCLI_HOST', None) or conf["host"])
    parser.add_argument("-u", "--username", help="username",
                        default=os.environ.get('NPCLI_USERNAME', None) or conf["username"])
    parser.add_argument("-p", "--password", help="password",
                        default=os.environ.get('NPCLI_PASSWORD', None) or conf["password"])

    spr_action = parser.add_subparsers(dest="action", help="action to take")
    spr_action.add_parser("classlist", help="show list of classes")
    spr_action.add_parser("nodelist", help="show list of nodes")

    spr_new = spr_action.add_parser("new", help="create a node")
    spr_new.add_argument("--parents", nargs="+", help="parent nodes")
    spr_new.add_argument("node", help="name of node to create")

    spr_edit = spr_action.add_parser("edit", help="edit a node")
    spr_edit.add_argument("node", help="name of node to edit")

    spr_del = spr_action.add_parser("del", help="delete a node")
    spr_del.add_argument("node", help="name of node to delete")

    spr_addc = spr_action.add_parser("addclass", help="add a class")
    spr_addc.add_argument("cls", help="name of class to add")

    spr_delc = spr_action.add_parser("delclass", help="delete a class")
    spr_delc.add_argument("cls", help="name of class to delete")

    spr_dump = spr_action.add_parser("dump", help="dump the database")

    spr_import = spr_action.add_parser("import", help="import a database dump")
    spr_import.add_argument("fname", help="db dump yaml file to import")

    args = parser.parse_args()
    r = requests.session()

    if args.username and args.password:
        r.auth = (args.username, args.password)

    if not args.host:
        parser.error('--host, $NPCLI_HOST, or config file is required')

    def getnode(nodename):
        req = r.get(args.host.rstrip("/") + "/api/node/" + nodename)
        req.raise_for_status()
        return req.text

    def putnode(nodename, body):
        return r.put(args.host.rstrip("/") + "/api/node/" + nodename, data=body)

    if args.action == "new":
        putnode(args.node, yaml.dump({"body": {},
                                      "classes": {},
                                      "parents": args.parents or []})).raise_for_status()
    elif args.action == "del":
        r.delete(args.host.rstrip("/") + "/api/node/" + args.node).raise_for_status()
    elif args.action == "edit":
        # TODO refuse if editor is unset
        body = getnode(args.node)
        newbody = None
        with tempfile.TemporaryDirectory() as d:
            tmppath = os.path.join(d, args.node)
            with open(tmppath, "w") as f:
                f.write(body)
            newbody = editorloop(tmppath, lambda content: yaml.load(content))
        if newbody != body:
            try:
                putnode(args.node, newbody).raise_for_status()
            except Exception:
                print("Your edits:\n")
                print(newbody, "\n\n")
                raise
        else:
            print("No changes, exiting")

    elif args.action == "nodelist":
        print(r.get(args.host.rstrip("/") + "/api/node").text)

    elif args.action == "classlist":
        print(r.get(args.host.rstrip("/") + "/api/class").text)

    elif args.action == "addclass":
        r.put(args.host.rstrip("/") + "/api/class/" + args.cls).raise_for_status()

    elif args.action == "delclass":
        r.delete(args.host.rstrip("/") + "/api/class/" + args.cls).raise_for_status()

    elif args.action == "dump":
        nodes = yaml.load(r.get(args.host.rstrip("/") + "/api/node").text)["nodes"]

        dump = {"classes": yaml.load(r.get(args.host.rstrip("/") + "/api/class").text)["classes"],
                "nodes": {}}

        for nodename in nodes:
            dump["nodes"][nodename] = yaml.load(getnode(nodename))

        print(yaml.dump(dump, default_flow_style=False))

    elif args.action == "import":
        with open(args.fname) as f:
            dump = yaml.load(f)

        for clsname in dump["classes"]:
            r.put(args.host.rstrip("/") + "/api/class/" + clsname).raise_for_status()

        # just make the nodes first
        for nodename, nodebody in dump["nodes"].items():
            putnode(nodename, yaml.dump({"body": {}, "classes": {}, "parents": []})).raise_for_status()

        # then fill out node bodies to avoid missing parent ordering issues
        for nodename, nodebody in dump["nodes"].items():
            putnode(nodename, yaml.dump(nodebody)).raise_for_status()


if __name__ == "__main__":
    main()
