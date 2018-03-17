from aioauth_client import OAuth2Client

class DiscordClient(OAuth2Client):
    access_token_url = 'https://discordapp.com/api/oauth2/token'
    authorize_url = 'https://discordapp.com/api/oauth2/authorize'
    base_url = 'https://discordapp.com/api/v6/'
    name = 'discord'
    user_info_url = 'https://discordapp.com/api/v6/users/@me'

    @staticmethod
    def user_parse(data):
        yield 'id', data.get('id')
        yield 'username', data.get('username')
        yield 'discriminator', data.get('discriminator')
        yield 'picture', "https://cdn.discordapp.com/avatars/{}/{}.png".format(
            data.get('id'), data.get('avatar'))

    def request(self, method, url, headers=None, **aio_kwargs):
        """Request OAuth2 resource."""
        url = self._get_url(url)
        headers = headers or {'Accept': 'application/json'}
        if self.access_token:
            headers['Authorization'] = "Bearer {}".format(self.access_token)

        return self._request(method, url, headers=headers, **aio_kwargs)
