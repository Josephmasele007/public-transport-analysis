# Generated by Django 5.1.6 on 2025-03-16 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_alter_transportationdata_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransportData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('road_name', models.CharField(max_length=255)),
                ('road_distance', models.FloatField()),
                ('route_name', models.CharField(max_length=255)),
                ('bus_station', models.CharField(max_length=255)),
                ('brt_station', models.CharField(max_length=255)),
                ('peak_hours', models.CharField(max_length=50)),
                ('average_speed', models.FloatField()),
                ('travel_time', models.FloatField()),
                ('fare', models.FloatField()),
                ('landmark_nearby', models.CharField(max_length=255)),
                ('road_type', models.CharField(max_length=50)),
                ('traffic_lights_count', models.IntegerField()),
                ('route_type', models.CharField(max_length=50)),
                ('congestion_level', models.CharField(max_length=50)),
                ('passenger_capacity', models.IntegerField()),
                ('alternative_routes', models.CharField(max_length=255)),
                ('bus_station_location', models.CharField(max_length=255)),
                ('brt_station_location', models.CharField(max_length=255)),
                ('geojson_data', models.TextField()),
            ],
            options={
                'verbose_name_plural': 'Transport Data',
            },
        ),
        migrations.DeleteModel(
            name='TransportationData',
        ),
    ]
