#!/usr/bin/env python
from const import *
import nfc

############################################################
# Felicaカード読込処理
############################################################
def read_felica():
    # for debug
    clf = nfc.ContactlessFrontend('usb')
    target = nfc.clf.RemoteTarget('212F')   # Felica
    res = clf.sense(target)

    # Felicaカード読込成功
    if not res is None:
        tag = nfc.tag.activate(clf, res)
        idm = tag.idm.hex()
    else:
        idm = INVALID_IDM

    clf.close()
    # for debug
    # idm = INVALID_IDM            # for debug
    #print('IDm : ' + idm)       # for debug
    return idm