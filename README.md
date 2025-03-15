Public Transportation Optimization in Dar es Salaam
Overview
This project aims to optimize public transportation systems in Dar es Salaam, Tanzania, through mobility data analysis. It integrates various data sources, including OpenStreetMap (OSM), WorldPop, and NBS Tanzania, to analyze and solve transportation challenges.
Features
•	Dashboard: Provides transport insights with interactive charts and reports.
•	Road & Route Explorer: Displays public roads, transport routes, and major landmarks.
•	Bus & BRT Stations: Lists all available bus and Mwendokasi (BRT) stations.
•	Traffic Congestion Analysis: Uses mobility data to analyze congestion patterns.
•	Travel Cost Calculator: Helps commuters estimate transport costs.
•	Data Insights & Reports: Provides analytical reports on transportation patterns.
•	Admin Panel: Manages transport data efficiently.
•	Map Integration: Uses Leaflet.js and GeoJSON for data visualization.
Tech Stack
•	Frontend: Django (Template-based UI)
•	Backend: Django Rest Framework (DRF) 
•	Database: SQLite (Primary)
•	Mapping Tools: Leaflet.js, Folium, GeoJSON
•	Data Sources: OpenStreetMap, WorldPop, NBS Tanzania
Installation & Setup
•	Python (>=3.9)
•	pip
•	Virtual environment (venv)
•	SQLite
•	Node.js (if using Vue.js for frontend)
Steps
1.	Clone the repository:
2.	git clone https://github.com/Josephmasele007/public-transport-analysis.git
             Create a virtual environment and activate it:
3.	python -m venv venv
                  source venv/bin/activate  # On Windows: venv\Scripts\activate
4.	Install dependencies:
               pip install -r requirements.txt
5.	Run database migrations:
               python manage.py migrate
6.	Load initial data (Optional):
               python manage.py loaddata initial_data.json
7.	Run the development server:
               python manage.py runserver
API Endpoints (If using DRF/FastAPI)
Endpoint	Method	Description
/api/routes/	GET	Get all transport routes
/api/stations/	GET	Get all bus & BRT stations
/api/traffic/	GET	Get traffic congestion data
/api/cost-calculator/	POST	Estimate travel cost
Data Visualization
•	The project utilizes Leaflet.js and Folium for displaying GeoJSON-based transport data.
•	Heatmaps and route mapping are supported for real-time analysis.


Contribution Guidelines
1.	Fork the repository.
2.	Create a new branch: feature-new-component.
3.	Commit changes and push to the branch.
4.	Open a pull request for review.
Contact
For any questions or contributions, please contact:
•	Email: josephmasele1307@gmail.com
•	GitHub: https://github.com/Josephmasele007

