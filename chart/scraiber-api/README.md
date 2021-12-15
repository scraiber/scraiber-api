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
helm install scraiber-api ./chart/scraiber-api --namespace backend --set secret.postgresqlURL=$POSTGRESQL_URL
```
