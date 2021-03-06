from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.client.user import User
from lampost.context.resource import m_requires, requires
from lampost.model.player import Player
from lampost.util.lmutil import DataError, StateError

m_requires('datastore', 'user_manager', 'perm', __name__)


class SettingsResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('get', SettingsGet())
        self.putChild("create_account", AccountCreate())
        self.putChild('update_account', AccountUpdate())
        self.putChild('delete_account', AccountDelete())
        self.putChild('create_player', PlayerCreate())
        self.putChild('get_players', GetPlayers())
        self.putChild('delete_player', PlayerDelete())


class SettingsGet(Resource):
    @request
    def render_POST(self, content, session):
        if session.user.dbo_id != content.user_id:
            check_perm(session, 'admin')
        user = load_object(User, content.user_id)
        user_json = user.json_obj
        user_json['password'] = ''
        return user_json


class AccountCreate(Resource):
    @request
    def render_POST(self, content, session):
        account_name = content.account_name.lower()
        if get_index("user_name_index", account_name) or object_exists('player', account_name):
            raise DataError(content.account_name + " is in use.")
        user = user_manager.create_user(account_name, content.password, content.email)
        session.connect_user(user)
        return {'user_id': user.dbo_id}


class AccountUpdate(Resource):
    @request
    def render_POST(self, content, session):
        user_json = content.user
        user_id = content.user_id
        if session.user.dbo_id != content.user_id:
            check_perm(session, 'admin')

        old_user = None
        if user_id:
            old_user = datastore.load_object(User, user_id)
            if not old_user:
                raise StateError(user_id + " does not exist!")

        if user_manager.check_name(user_json['user_name'], old_user) != "ok":
            raise DataError(user_id + " is in use")
        user = User(user_id)
        if not user_json['password']:
            user_json['password'] = old_user.password

        update_object(user, user_json)
        if old_user:
            delete_index("user_name_index", old_user.user_name.lower())
        set_index("user_name_index", user.user_name.lower(), user_id)


@requires('sm')
class AccountDelete(Resource):
    @request
    def render_POST(self, content, session):
        user = session.user
        if user.player_ids and content.password != user.password:
            raise StateError("Incorrect password.")
        response = self.sm.logout(session)
        user_manager.delete_user(user)
        return response


@requires('cls_registry')
class PlayerCreate(Resource):
    @request
    def render_POST(self, content, session):
        user = load_object(User, content.user_id)
        if not user:
            raise DataError("User {0} does not exist".format([content.user_id]))
        player_name = content.player_name.lower()
        if player_name != user.user_name and get_index("user_name_index", player_name):
            raise DataError(content.player_name + " is in use.")
        if object_exists('player', player_name):
            raise DataError(content.player_name + " is in use.")
        player = self.cls_registry(Player)(player_name)
        load_json(player, content.player_data)
        user_manager.attach_player(user, player)


class GetPlayers(Resource):
    @request
    def render_POST(self, content, session):
        user = load_object(User, content.user_id)
        if not user:
            raise StateError("User {0} does not exist".format([content.user_id]))
        return player_list(user.player_ids)


class PlayerDelete(Resource):
    @request
    def render_POST(self, content, session):
        user = session.user
        if content.password != user.password:
            raise DataError("Incorrect account password")
        if not content.player_id in user.player_ids:
            raise StateError("Player not longer associated with user")
        player = load_object(Player, content.player_id)
        user_manager.delete_player(user, player)
        return player_list(user.player_ids)


def player_list(player_ids):
    players = []
    for player_id in player_ids:
        player = load_object(Player, player_id)
        players.append({'name': player.name, 'dbo_id': player.dbo_id})
        if not getattr(player, 'session', None):
            evict_object(player)
    return players





