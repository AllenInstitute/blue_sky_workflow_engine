#!/usr/bin/env python
# -*- coding: utf-8 -*-

#os.environ["DJANGO_SETTINGS_MODULE"] = "webapp.settings"

import cherrypy
from django.conf import settings
import django; django.setup()
from django.core.handlers.wsgi import WSGIHandler


class DjangoApplication(object):
    HOST = "0.0.0.0"
    PORT = 8000

    def mount_static(self, url, root):
        """
        :param url: Relative url
        :param root: Path to static files root
        """
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
        self.mount_static(
            settings.STATIC_URL,
            '/blue_sky_workflow_engine/workflow_engine/static')
            #settings.STATIC_ROOT)

        cherrypy.log("Loading and serving Django application")
        cherrypy.tree.graft(WSGIHandler())
        cherrypy.engine.start()

        cherrypy.engine.block()


if __name__ == "__main__":
    DjangoApplication().run()
