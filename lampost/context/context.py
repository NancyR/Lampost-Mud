from json.decoder import JSONDecoder
from json.encoder import JSONEncoder
from lampost.client.user import UserManager

from lampost.context.resource import register, provides

from lampost.client.server import WebServer
from lampost.gameops.config import Config
from lampost.gameops.event import Dispatcher
from lampost.client.session import SessionManager
from lampost.datastore.dbconn import RedisStore
from lampost.gameops.permissions import Permissions
from lampost.mud.mud import MudNature
from lampost.util.lmlog import Log

@provides('context')
class Context():
    def __init__(self, port=2500, db_host="localhost", db_port=6379, db_num=0, db_pw=None,
                 flavor='merc', config='lampost'):
        Log()
        dispatcher = Dispatcher()
        register('decode', JSONDecoder().decode)
        register('encode', JSONEncoder().encode)
        ClassRegistry()
        data_store = RedisStore(db_host, int(db_port), int(db_num), db_pw)
        Permissions()
        SessionManager()
        UserManager()
        web_server = WebServer(int(port))
        MudNature(flavor)
        data_store.load_object(Config, config)
        dispatcher._start_service()
        web_server._start_service()

@provides('cls_registry')
class ClassRegistry:
    def __init__(self):
        self.registry = dict()

    def __call__(self, cls):
        return self.registry.get(cls, cls)

    def set_class(self, base_cls, sub_cls):
        self.registry[base_cls] = sub_cls
