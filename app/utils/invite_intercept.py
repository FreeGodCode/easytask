from anytree.importer import DictImporter
from anytree import Node, findall_by_attr
from anytree.exporter import DictExporter
from flask import current_app, g
import json

def intercept():
    """判断用户是否top_root"""
    # redis-cli
    rc = current_app.redis_cli
    root_data = json.loads(rc.hget(f"drp_relation_member_{g.user_id}", 0).decode())
    importer = DictImporter()
    root = importer.import_(root_data)
    return root.height
