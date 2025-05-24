# myproject/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
# You might need this if you have specific middleware for HTTP within ASGI
# from channels.http import AsgiHandler # older versions, get_asgi_application is preferred

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stream.settings')

import stream.routing

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests (including REST API)
    "http": get_asgi_application(),
    "websocket": URLRouter(
            stream.routing.websocket_urlpatterns
    ),

    # WebSocket handler
    # "websocket": AuthMiddlewareStack( # Or just URLRouter if no auth needed at WS connect time
    #     URLRouter(
    #         stream.routing.websocket_urlpatterns
    #     )
    # ),
})
