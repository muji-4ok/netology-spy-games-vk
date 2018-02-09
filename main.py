import requests
import sys
from urllib.parse import urlencode
from time import time, sleep
from json import dump


def time_calls(f):
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        delta = end - start

        if delta < 0.35:
            sleep(0.35 - delta)

        return result

    return wrapper


class VkApi:
    def __init__(self, stoken, cid, user_name_or_id):
        self.cid = cid
        self.stoken = stoken
        self.uid = self.get_uid(user_name_or_id)
        self.token = self.get_token()

    def write_json(self, filename, max_count=None):
        friends = []

        for name, gid, members, left in self.lone_groups():
            if len(friends) == max_count:
                break

            print(f'{left}'.zfill(3), end='\r')

            if name is not None:
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
        params = dict(kwargs)

        params['access_token'] = token
        params['v'] = '5.71'

        response = requests.get(f'https://api.vk.com/method/{method}', params)

        return response.json()['response']

    def groups(self):
        response = self.call('groups.get', count=1000, user_id=self.uid,
                             extended=1, fields=['members_count'])

        return response['count'], response['items']

    def friends_in_group(self, gid):
        response = self.call('groups.getMembers', group_id=gid,
                             filter='friends')

        return response['count']

    def lone_groups(self):
        count, groups = self.groups()

        for i, group in enumerate(groups):
            name = group['name']
            gid = group['id']
            members = group['members_count']
            left = count - i

            if not self.friends_in_group(gid):
                yield name, gid, members, left
            else:
                yield None, None, None, left


if __name__ == '__main__':
    service_token = ('46e917ae46e917ae46e917ae894689f0ca44'
                     '6e946e917ae1c873bfc58765bb68405d900')
    client_id = 6350692
    user_name_or_id = sys.argv[1]

    api = VkApi(service_token, client_id, user_name_or_id)
    max_count = None

    api.write_json('groups.json', max_count)
    print('Created groups.json')
