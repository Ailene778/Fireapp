from django.contrib import admin
from django.urls import include, path

from fire.views import HomePageView, ChartView,PieCountbySeverity, LineCountbyMonth, MultilineIncidentTop3Country, multipleBarbySeverity 

from fire import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', HomePageView.as_view(), name='home'),
    path('dashboard_chart', ChartView.as_view(), name='dashboard-chart'),
    path('chart/', PieCountbySeverity, name='chart'),
    path('lineChart/', LineCountbyMonth, name='chart'),
    path('multilineChart/', MultilineIncidentTop3Country, name='chart'),
    path('multiBarChart/', multipleBarbySeverity, name='chart'),
    path('stations', views.map_station, name='map-station'),
    path('fire-incidents-map/', views.fire_incidents_map, name='fire-incidents-map'),
    path('widgets.html', views.widgets, name='widgets'),
]
