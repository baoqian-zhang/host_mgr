from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api_cost.views import ApiCostViewSet
from city.views import CityViewSet
from host.views import HostStatisticViewSet
from host.views import HostPasswordViewSet
from host.views import HostViewSet
from idc.views import IDCViewSet

router = DefaultRouter()
router.register("cities", CityViewSet, basename="city")
router.register("idcs", IDCViewSet, basename="idc")
router.register("hosts/passwords", HostPasswordViewSet, basename="host-password")
router.register("hosts/statistics", HostStatisticViewSet, basename="host-statistic")
router.register("hosts", HostViewSet, basename="host")
router.register("api-costs", ApiCostViewSet, basename="api-cost")

urlpatterns = [
    path("api/v1/", include(router.urls)),
]
