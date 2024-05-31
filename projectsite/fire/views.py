from django.shortcuts import render
from django.views.generic.list import ListView
from fire.models import Locations, Incident, FireStation
from django.db import connection
from django.http import JsonResponse
from django.db.models.functions import ExtractMonth
from django.db.models import Count
from datetime import datetime

def widgets(request):
    return render(request, 'widgets.html')

class HomePageView(ListView):
    model = Locations
    context_object_name = 'home'
    template_name = "home.html"

class ChartView(ListView):
    template_name = 'chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self, *args, **kwargs):
        pass

def PieCountbySeverity(request):
    query = '''
    SELECT severity_level, COUNT(*) as count
    FROM fire_incident
    GROUP BY severity_level
    '''
    data = {}
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            data = {severity: count for severity, count in rows}
    
    return JsonResponse(data)

def LineCountbyMonth(request):
    current_year = datetime.now().year
    result = {month: 0 for month in range(1, 13)}

    incidents_per_month = Incident.objects.filter(date_time__year=current_year).values_list('date_time', flat=True)

    for date_time in incidents_per_month:
        month = date_time.month
        result[month] += 1

    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }

    result_with_month_names = {month_names[month]: count for month, count in result.items()}
    return JsonResponse(result_with_month_names)

def MultilineIncidentTop3Country(request):
    query = '''
        SELECT 
            fl.country,
            strftime('%m', fi.date_time) AS month,
            COUNT(fi.id) AS incident_count
        FROM 
            fire_incident fi
        JOIN 
            fire_locations fl ON fi.location_id = fl.id
        WHERE 
            fl.country IN (
                SELECT 
                    fl_top.country
                FROM 
                    fire_incident fi_top
                JOIN 
                    fire_locations fl_top ON fi_top.location_id = fl_top.id
                WHERE 
                    strftime('%Y', fi_top.date_time) = strftime('%Y', 'now')
                GROUP BY 
                    fl_top.country
                ORDER BY 
                    COUNT(fi_top.id) DESC
                LIMIT 3
            )
            AND strftime('%Y', fi.date_time) = strftime('%Y', 'now')
        GROUP BY 
            fl.country, month
        ORDER BY 
            fl.country, month;
    '''

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    result = {}
    months = set(str(i).zfill(2) for i in range(1, 13))

    for row in rows:
        country, month, total_incidents = row
        if country not in result:
            result[country] = {month: 0 for month in months}
        result[country][month] = total_incidents

    while len(result) < 3:
        missing_country = f"Country {len(result) + 1}"
        result[missing_country] = {month: 0 for month in months}

    for country in result:
        result[country] = dict(sorted(result[country].items()))

    return JsonResponse(result)

def multipleBarbySeverity(request):
    query = '''
    SELECT 
        fi.severity_level,
        strftime('%m', fi.date_time) AS month,
        COUNT(fi.id) AS incident_count
    FROM 
        fire_incident fi
    GROUP BY fi.severity_level, month
    '''

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    result = {}
    months = set(str(i).zfill(2) for i in range(1, 13))

    for row in rows:
        level, month, total_incidents = row
        if level not in result:
            result[level] = {month: 0 for month in months}
        result[level][month] = total_incidents

    for level in result:
        result[level] = dict(sorted(result[level].items()))

    return JsonResponse(result)

def map_station(request):
    fireStations = FireStation.objects.values('name', 'latitude', 'longitude')
    for fs in fireStations:
        fs['latitude'] = float(fs['latitude'])
        fs['longitude'] = float(fs['longitude'])

    fireStations_list = list(fireStations)

    context = {
        'fireStations': fireStations_list,
    }

    return render(request, 'map_station.html', context)

def fire_incidents_map(request):
    city = request.GET.get('city', '')

    query = """
        SELECT
            fire_locations.latitude AS latitude,
            fire_locations.longitude AS longitude,
            fire_locations.address AS address,
            fire_incident.severity_level AS severity_level,
            fire_incident.description AS description
        FROM
            fire_incident
        INNER JOIN  
            fire_locations ON fire_incident.location_id = fire_locations.id
        WHERE
            fire_locations.city = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [city])
        rows = cursor.fetchall()

    incident_data = []
    for row in rows:
        latitude, longitude, address, severity_level, description = row
        incident_data.append({
            'latitude': latitude,
            'longitude': longitude,
            'address': address,
            'severity_level': severity_level,
            'description': description
        })

    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT city FROM fire_locations")
        cities = cursor.fetchall()
        cities_list = [city[0] for city in cities]

    context = {
        'incident_data': incident_data,
        'cities': cities_list,
    }

    return render(request, 'fire_incidents_map.html', context)
