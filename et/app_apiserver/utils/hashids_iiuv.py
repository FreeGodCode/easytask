import hashids
from flask import current_app

def hashids_iivu_encode(iiuv):
    """加密uuid生成iiuv"""
    hasher = hashids.Hashids(salt=current_app.config['HASHIDS_SECRET'], min_length=4)
    res = hasher.encode(iiuv)
    return res

def hashids_iivu_decode(iiuv):
    """解密iiuv"""
    hasher = hashids.Hashids(salt=current_app.config['HASHIDS_SECRET'])
    res = hasher.decode(iiuv)
    return res