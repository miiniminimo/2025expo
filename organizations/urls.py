# organizations/urls.py
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, EmployeeViewSet

router = DefaultRouter()
router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"employees", EmployeeViewSet, basename="employee")

urlpatterns = router.urls
