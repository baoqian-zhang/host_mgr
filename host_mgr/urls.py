from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api_cost.views import ApiCostViewSet
from city.views import CityViewSet
from host.views import HostStatisticViewSet
from host.views import HostViewSet
from idc.views import IDCViewSet
from host_mgr.settings import REST_API_PRE_URL

router = DefaultRouter()
router.register("cities", CityViewSet, basename="city")
router.register("idcs", IDCViewSet, basename="idc")
router.register("hosts/statistics", HostStatisticViewSet, basename="host-statistic")
router.register("hosts", HostViewSet, basename="host")
router.register("api-costs", ApiCostViewSet, basename="api-cost")

urlpatterns = [
    path(f"{REST_API_PRE_URL}v1/", include(router.urls)),
]
