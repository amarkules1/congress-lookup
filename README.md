# congress-lookup

## Description

Shows some information about congress members.

## Development

Install dependencies: `pipenv install --dev`    

run app: `pipenv run flask --app main:app run`

regen requirements.txt after adding a dependency: `pipenv requirements > requirements.txt`

regenerate frontend assets (from `/congress-lookup-frontend`): `npm i && npm run build`
