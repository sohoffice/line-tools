import argparse
import json
import logging
import os
import sys
from typing import Dict

import urllib3

http = urllib3.PoolManager()
logging.basicConfig()
logger = logging.getLogger("tools")


def get_config(config_path) -> Dict[str, str]:
    config: Dict[str, str] = {
        "_configPath": os.path.normpath(config_path),
        "_configDir": os.path.dirname(os.path.normpath(config_path))
    }
    try:
        with(open(config_path)) as f:
            for line in f.readlines():
                try:
                    idx = line.index("=")
                    (key, val) = (line[0:idx].strip(), line[(idx + 1):].strip())
                    config[key] = val
                except ValueError:
                    pass
        return config
    except FileNotFoundError:
        msg = "Config file {0} not found. Please use --config to specify the path.".format(config_path)
        print(msg)
        raise Exception()


def write_config(config_path, config: Dict[str, str]):
    with(open(config_path.strip(), 'w')) as f:
        for it in config.items():
            if not it[0].startswith("_"):
                f.write("{0} = {1}\n".format(it[0], it[1]))


def _read_config(config: Dict[str, str]):
    config_dir = config['_configDir']
    token = config['token']
    if token is None:
        raise Exception("Token not defined.\n\nPlease add token = xxx in config.txt.")

    menu = None
    if 'menu' in config:
        raw = config['menu']
        menu = os.path.join(config_dir, raw)
    if menu is None:
        raise Exception("Menu not defined. Please add menu = xxx.json in config.txt.")

    image = None
    if 'image' in config:
        image = os.path.join(config_dir, config['image'])
    if image is None:
        raise Exception("Image not defined. Please add image = xxx in config.txt.")
    return token, menu, image, config_dir


def _read_line_user_id(config: Dict[str, str], profile: str):
    """
    Read link user id by looking config with the specified profile.
    :return:
    """
    x = "profile.{0}".format(profile)
    if x not in config:
        raise Exception("Try to use profile {0}, but profile.{0} doesn't exist in config.".format(profile))
    return config[x]


def _guess_media_type(filename: str):
    if filename.lower().endswith("png"):
        return "image/png"
    elif filename.lower().endswith("jpg") or filename.lower().endswith("jpeg"):
        return "image/jpeg"
    return None


def do_list(config: Dict[str, str]):
    from linetools.line_richmenu import RichMenus
    token = config['token']
    if token is None:
        raise Exception("Token not defined.\n\nPlease add token = xxx in config.txt.")

    resp = http.request("GET", "https://api.line.me/v2/bot/richmenu/list", headers={
        "Authorization": "Bearer {0}".format(token)
    })

    if resp.status != 200:
        logger.error("Error reading richmenu: {0}".format(resp.reason))
    else:
        js = json.loads(resp.data)
        rm = RichMenus(js)
        print("Current rich menus: \n" + "\n".join([" - {0}".format(m.id) for m in rm]))


def do_delete(menu_id: str, config: Dict[str, str]):
    token = config['token']
    if token is None:
        raise Exception("Token not defined.\n\nPlease add token = xxx in config.txt.")
    resp = http.request("DELETE", "https://api.line.me/v2/bot/richmenu/{0}".format(menu_id), headers={
        "Authorization": "Bearer {0}".format(token)
    })
    if resp.status != 200:
        logger.error("Error deleting menu id: {0}".format(resp.reason))
    else:
        print("rich menu {0} was deleted.".format(menu_id))


def do_new(user: str, config: Dict[str, str]):
    (token, menu, image, config_dir) = _read_config(config)

    # First create the rich menu itself.
    with open(menu, 'r') as f:
        data = f.read().encode("utf-8")
    resp = http.request("POST", "https://api.line.me/v2/bot/richmenu", headers={
        "Authorization": "Bearer {0}".format(token),
        'Content-Type': 'application/json'
    }, body=data)
    if resp.status != 200:
        logger.error("Error creating menu: {0}".format(resp.reason))
    else:
        menu_id = json.loads(resp.data)['richMenuId']
        print("rich menu {0} was created.".format(menu_id))

    # Second, upload image
    with open(image, 'rb') as f2:
        image_data = f2.read()
    resp = http.request("POST", "https://api.line.me/v2/bot/richmenu/{0}/content".format(menu_id), headers={
        "Authorization": "Bearer {0}".format(token),
        'Content-Type': _guess_media_type(image)
    }, body=image_data)
    if resp.status != 200:
        logger.error("Error uploading menu image {0}: {1}".format(image, resp.reason))
    else:
        print("rich menu image was uploaded.")

    if user is not None:
        do_link(user, menu_id, config)


def do_info(menu_id: str, config: Dict[str, str]):
    from linetools.line_richmenu import RichMenus
    token, *_ = _read_config(config)
    resp = http.request("GET", "https://api.line.me/v2/bot/richmenu/list", headers={
        "Authorization": "Bearer {0}".format(token)
    })
    if resp.status != 200:
        logger.error("Error reading rich menus: {0}".format(resp.reason))
    else:
        js = json.loads(resp.data)
        rm = RichMenus(js)
        for it in rm:
            if it.id == menu_id:
                print(json.dumps(it.raw, indent=2, ensure_ascii=False))


def do_link(profile: str, menu_id: str, config: Dict[str, str]):
    token, *_ = _read_config(config)
    user_id = _read_line_user_id(config, profile)
    resp = http.request("POST", "https://api.line.me/v2/bot/user/{0}/richmenu/{1}".format(user_id, menu_id), headers={
        "Authorization": "Bearer {0}".format(token)
    })
    if resp.status != 200:
        logger.error("Error linking menu to user {0}: {1}".format(user_id, resp.reason))
    else:
        print("rich menu linked to user.")


def process(the_args):
    try:
        if 'command' not in the_args:
            raise Exception("No command is given. Use rhythm --help to see help.")
        if 'config' in the_args:
            config_path = the_args.config
            config = get_config(config_path)
        else:
            raise Exception("Config not found.")

        if 'command' in the_args:
            command = the_args.command
            if command == "list":
                do_list(config)
            elif command == 'delete':
                do_delete(the_args.menuId, config)
            elif command == 'new':
                do_new(the_args.user, config)
            elif command == 'info':
                do_info(the_args.menuId, config)
            elif command == 'link':
                do_link(the_args.user, the_args.menuId, config)

        write_config(config_path + "\n", config)
    except Exception as e:
        logger.error(e)


def main():
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('--config', action='store', default='./config.txt',
                             help='The path to config file, default to ./config.txt')

    parser = argparse.ArgumentParser(description='Build and update LINE rich menu.', prog="rhythm")

    subparsers = parser.add_subparsers(title="commands")
    parser_list = subparsers.add_parser("list", parents=[base_parser])
    parser_list.set_defaults(command='list')

    parser_new = subparsers.add_parser("new", parents=[base_parser])
    parser_new.set_defaults(command='new')
    parser_new.add_argument('--user', action='store',
                            default=None,
                            help='Optionally specify the user profile to link to when creating richmenu. The value will be used to look up '
                                 'profile.[user] in config.txt')

    parser_delete = subparsers.add_parser("delete", parents=[base_parser])
    parser_delete.set_defaults(command='delete')
    parser_delete.add_argument('menuId', action='store',
                               help='The rich menu id to be deleted.')

    parser_info = subparsers.add_parser("info", parents=[base_parser])
    parser_info.set_defaults(command='info')
    parser_info.add_argument('menuId', action='store',
                             help='The rich menu id to be displayed.')

    parser_link = subparsers.add_parser("link", parents=[base_parser])
    parser_link.set_defaults(command='link')
    parser_link.add_argument('user', action='store',
                             help='The user profile to perform the linking. The value will be used to look up profile.[user] in config.txt')
    parser_link.add_argument('menuId', action='store',
                             help='The rich menu id to be linked to.')

    args = parser.parse_args()
    logger.debug("argument list: " + str(args))


if __name__ == "__main__":
    sys.exit(main())
