from typing import Any, Dict


class RichMenu(object):
    def __init__(self, d: Dict[str, Any]):
        if 'richMenuId' in d:
            self.id = d['richMenuId']
            self.raw = d


class RichMenus(object):
    def __init__(self, d: Dict[str, Any]):
        if 'richmenus' in d:
            self.menus = [RichMenu(rm) for rm in d['richmenus']]

    def __iter__(self):
        for m in self.menus:
            yield m
