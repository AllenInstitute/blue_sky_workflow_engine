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

def _route_task(name, args, kwargs,
              options, task=None, **kw):
    return {
        'queue': 'workflow@at_em_imaging_workflow',
    }


if __name__ == "__main__":
    app = Celery('workflow_engine_ui')
    configure_worker_app(app, 'workflow_engine_ui')
    app.conf.task_routes = (_route_task,)

    DjangoApplication().run()
