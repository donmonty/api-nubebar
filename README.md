# NubeBar API

NubeBar is a SaaS app that helps bars and restaurants manage their alcohol inventory with ease and maximum precision in order to avoid theft and boost revenue. For most bars and restaurants alcohol sales represent 40% or more of total sales. Alcohol also has the highest margins and is the most valuable inventory. Despite this, most businesses manage their alcohol inventory using manual, time-consuming methods that make inventory control a big challenge. NubeBar solves this problem.

## Tech Stack

I built the entire backend using the following tech stack:

- Python
- Django
- Django REST Framework
- Postgres
- Docker containers for testing

## Features

The backend allows bar managers to:

- Add new bottles to the inventory.
- Track the liquid volume of each bottle over time.
- Remove empty bottles from the inventory.
- Parse sales reports from third-party point of sale software.
- Perform daily inventory counts.
- Generate variance analysis reports to compare alcohol sales versus actual consumption.
- Load drink menus and recipes from Google Sheets files via the Google Sheets API.
- Create inventory cost reports.
- Manage multiple locations (for restaurant and bar chains).
- Manage multiple storage locations.
- Preload more than 400 spirit brands sold in Mexico via the Google Sheets API.
- Validate the legitimacy of purchased bottles by scrapping the federal government's website.

Each of these features is fully tested via unit and integration tests.
