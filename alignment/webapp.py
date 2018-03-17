class WebappHandler:
    def __init__(self):
        with open('build/index.html') as idx:
            self.react_template = idx.read()

    def setup(self, app):
        app.router.add_get('/app', self.app_page)
        app.router.add_static('/static', 'build/static')

    async def app_page(request):
        return web.Response(text=self.react_template, content_type='text/html')
