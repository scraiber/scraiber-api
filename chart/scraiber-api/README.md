# Setup for Helm chart

First you have to create a namespace like

```
kubectl create ns backend
```

If the database access string looks like

```
postgresql://USERNAME:PASSWORD@CLUSTER_ADRESS:PORT/DATABASE
```

you can run

```
export POSTGRESQL_URL="postgresql://USERNAME:PASSWORD@CLUSTER_ADRESS:PORT/DATABASE"
export FASTAPI_SECRET=(openssl rand -base64 100)
export SENDINBLUE_API_KEY=<Your Sendinblue key>
export CLUSTER_DICT='{"US1": "CLUSTER_LINK_US1", "EU1": "CLUSTER_LINK_EU1"}'

helm install scraiber-api ./chart/scraiber-api --namespace backend --set secret.postgresqlURL=$POSTGRESQL_URL --set secret.scraiberAPISecret=$FASTAPI_SECRET --set secret.sendinblueAPIKey=$SENDINBLUE_API_KEY --set secret.clusterDict=$CLUSTER_DICT 
```