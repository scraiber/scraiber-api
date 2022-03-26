# Scraiber-api

[![CircleCI](https://circleci.com/gh/scraiber/scraiber-api/tree/main.svg?style=svg)](https://circleci.com/gh/scraiber/scraiber-api/tree/main)

The scraiber-api is a backend API (based on FastAPI), that enables users to access a group of Kubernetes clusters, to create namespaces there and to work together on it.

## Prerequisites for installing scraiber-api

- One or more Kubernetes clusters (our software has been tested on Digitalocean)
- A Postgresql database running (we will need an access string)
- A tenant at auth0
  - Create a `single page application` with allowed callback URL http://127.0.0.1:12345/callback
  - Create a `machine-to-machine` app and authorize `https://your-domain.auth0.com/api/v2/` such that you can `read:users`, `delete:users`, `read:user_idp_tokens`
- `kubectl` installed
- `helm` installed
- A kubeconfig file with contexts for all clusters, named `config`
- A file specifying additional information for the cluster, called `cluster_dict.json`

The file `cluster_dict.json` has to look like

```
{ 
    "EU1": {
        "Location": "Frankfurt",
        "Config-Name": <Config name for respective cluster in config file>,
        "blacklist": <a list of blacklisted namespaces for this cluster like ["default", "kube-public"]>,
        "concierge-endpoint": <your-pinniped endpoint for this cluster>,
        "certificate-authority-data": <your certifiacte for pinniped for this cluster>
    },
    "US1": {
        "Location": "New York",
        "Config-Name": <Config name for respective cluster in config file>,
        "blacklist":  <a list of blacklisted namespaces for this cluster like ["default", "kube-public"]>,
        "concierge-endpoint": <your-pinniped endpoint for this cluster>,
        "certificate-authority-data": <your certifiacte for pinniped for this cluster>
    }    
}
```

**Important:** The files `config` and `cluster_dict.json` have to be placed in `chart/scraiber-api/`.


## Installing scraiber-api via Helm chart

First you have to create a namespace in the cluster like

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
export SENDINBLUE_API_KEY=<Your Sendinblue key>
export DOMAIN_NAME=<Your Domain name, like https://scraiber.com>
export AUTH0_DOMAIN='<your-auth0-domain>.auth0.com'
export AUTH0_CLIENTID_FRONTEND=<your-auth0-frontend-client-id>
export AUTH0_CLIENTID_BACKEND=<your-auth0-backend-client-id>
export AUTH0_CLIENT_SECRET_BACKEND=<your-auth0-backend-client-secret>
export AUTH0_AUDIENCE='https://<your-auth0-domain>.eu.auth0.com/api/v2/'

helm install scraiber-api ./chart/scraiber-api --namespace backend \
    --set secret.postgresqlURL=$POSTGRESQL_URL \
    --set secret.sendinblueAPIKey=$SENDINBLUE_API_KEY \
    --set secret.domainName=$DOMAIN_NAME \
    --set secret.auth0_domain=$AUTH0_DOMAIN \
    --set secret.auth0_clientid_frontend=$AUTH0_CLIENTID_FRONTEND \
    --set secret.auth0_clientid_backend=$AUTH0_CLIENTID_BACKEND \
    --set secret.auth0_client_secret_backend=$AUTH0_CLIENT_SECRET_BACKEND \
    --set secret.auth0_audience=$AUTH0_AUDIENCE
```

## Accessing scraiber-api in the cluster

Upon running

```
export POD_NAME=$(kubectl get pods --namespace backend -l "app.kubernetes.io/name=scraiber-api,app.kubernetes.io/instance=scraiber-api" -o jsonpath="{.items[0].metadata.name}")
export CONTAINER_PORT=$(kubectl get pod --namespace backend $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
echo "Visit http://127.0.0.1:8080 to use your application"
kubectl --namespace backend port-forward $POD_NAME 8080:$CONTAINER_PORT
```

you can access scraiber-api under [http://localhost:8080](http://localhost:8080).

## Documentation

The documentation can be found at [http://localhost:8080/docs](http://localhost:8080/docs). It follows the OpenAPI standard and most of the APIs will be self-explaining, but we will extend that part of this README soon. For the user sign up/sign in/password reset/delete user etc. part, we used [FastAPI Users](https://fastapi-users.github.io/fastapi-users/usage/flow/).


## License

This project is licensed under the terms of the Apache 2.0 license.

