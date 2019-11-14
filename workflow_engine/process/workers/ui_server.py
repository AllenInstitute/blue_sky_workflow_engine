import cherrypy
from django.conf import settings
from celery import Celery
from workflow_engine.client_settings import configure_worker_app
import django; django.setup()
from django.core.handlers.wsgi import WSGIHandler


class DjangoApplication(object):
    HOST = "0.0.0.0"
    PORT = 8000

    def mount_static(self, url, root):
        config = {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': root,
            'tools.expires.on': True,
            'tools.expires.secs': 86400
        }
        cherrypy.tree.mount(None, url, {'/': config})

    def run(self):
        cherrypy.config.update({
            'server.socket_host': self.HOST,
            'server.socket_port': self.PORT,
            'engine.autoreload_on': False,
            'log.screen': True
        })

        # use python -m workflow_engine.management.manage collectstatic to populate static files
        self.mount_static(
            settings.STATIC_URL,
            settings.STATIC_ROOT)
        cherrypy.tree.graft(WSGIHandler())
        cherrypy.engine.start()
        cherrypy.engine.block()


if __name__ == "__main__":
    app = Celery(settings.APP_PACKAGE)
    configure_worker_app(app, settings.APP_PACKAGE)

    DjangoApplication().run()
