from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/trainer/', include('trainer.urls')),
    path('api/plan/', include('plan.urls')),
    path('api/client/', include('client.urls')),
    path('api/review/',include('review.urls')),
    path('api/section/',include('section.urls')),
    path('api/refund/',include('refund.urls')),
    path('api/nutrition/',include('nutrition.urls')),
    path('api/tickets/',include('tickets.urls')),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
