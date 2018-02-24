import requests
import sys
from urllib.parse import urlencode
from json import dump, load


UNKNOWN_ERROR = 1
TOO_MANY_REQUESTS = 6
INTERNAL_ERROR = 10
NOT_ENOUGH_PERMISSIONS = 7
BANNED_OR_DELETED = 18


def time_calls(f):
    def wrapper(*args, **kwargs):
        while True:
            result = f(*args, **kwargs)

            if 'error' in result:
                error_code = result['error']['error_code']

                if error_code in (NOT_ENOUGH_PERMISSIONS, BANNED_OR_DELETED):
                    return None
                elif error_code in (UNKNOWN_ERROR, TOO_MANY_REQUESTS,
                                    INTERNAL_ERROR):
                    continue
                else:
                    print(result['error'])
                    raise NotImplementedError
            else:
                break

        return result['response']

    return wrapper


class VkApi:
    def __init__(self, stoken, cid, user_name_or_id):
        self.cid = cid
        self.stoken = stoken
        self.uid = self.get_uid(user_name_or_id)
        self.token = self.get_token()

    def write_json(self, filename, max_count=None):
        friends = []

        for name, gid, members in self.lone_groups():
            if len(friends) == max_count:
                break

            friends.append({'name': name,
                            'gid': gid,
                            'members_count': members})

        with open(filename, 'w') as f:
            dump(friends, f, indent=2)

    def get_uid(self, user_name_or_id):
        response = self.call('utils.resolveScreenName', self.stoken,
                             screen_name=user_name_or_id)

        try:
            return response['object_id']
        except TypeError:
            return user_name_or_id

    def get_token(self):
        params = {
            'client_id': self.cid,
            'redirect_uri': 'https://oauth.vk.com/blank.html',
            'scope': 262146,
            'response_type': 'token'
        }

        url = '?'.join(('https://oauth.vk.com/authorize', urlencode(params)))

        print(url)

        return input('token >>> ')

    @time_calls
    def call(self, method, token=None, **kwargs):
        token = token or self.token

        kwargs['access_token'] = token
        kwargs['v'] = '5.71'

        response = requests.get(f'https://api.vk.com/method/{method}', kwargs)

        return response.json()

    def groups(self, uid):
        response = self.call('groups.get', count=1000, user_id=uid,
                             extended=1, fields=['members_count'])

        if response is not None:
            return {(x['name'], x['id'], x['members_count'])
                    for x in response['items'] if 'members_count' in x}
        else:
            return set()

    def friends(self):
        response = self.call('friends.get', user_id=self.uid)

        return response['items']

    def lone_groups(self):
        user_groups = self.groups(self.uid)
        friends = self.friends()
        left = len(friends)

        for fid in friends:
            user_groups -= self.groups(fid)
            print(f'{left}'.zfill(3), end='\r')
            left -= 1

        for group in user_groups:
            yield group


if __name__ == '__main__':
    with open('config.json') as f:
        config = load(f)
        service_token = config['service_token']
        client_id = config['client_id']

    user_name_or_id = sys.argv[1]

    api = VkApi(service_token, client_id, user_name_or_id)
    max_count = None

    api.write_json('groups.json', max_count)
    print('Created groups.json')
