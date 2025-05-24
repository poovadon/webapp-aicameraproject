from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# สร้าง router สำหรับ ViewSets
router = DefaultRouter()
router.register(r'api/cameras', views.CameraViewSet, basename='camera')
router.register(r'api/edge_devices', views.EdgeDevicesViewSet, basename='edge_devices')
router.register(r'api/checkpoints', views.CheckpointViewSet, basename='checkpoint')
router.register(r'api/aggregation_detections', views.AggregationDetectionsViewSet, basename='aggregation_detections')

urlpatterns = [
    path('', views.home, name='home'),
    path('camera_data/', views.get_camera_data, name='camera_data'),
    path('map/', views.search_license_plate, name='map'),
    path('map_check/', views.map_check, name='map_check'),
    path('about/', views.about, name='about'),
    path('data_table/', views.data_table, name='data_table'),
    path('contact/', views.contact, name='contact'),
    path('camera/', views.camera, name='camera'),
    path('check/', views.check, name='check'),
    path('detections/', views.detections, name='detections'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# รวม URL จาก router
urlpatterns += router.urls
