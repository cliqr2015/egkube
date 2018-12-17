{{/* vim: set filetype=mustache: */}}
{{/*

# PG Init Client

Create database

## Requirements:

Postgres server has to be runnning; otherwise it fails.

## How To Use:

(1) Include this template into your chart

```yaml
initContainers:
  - name: pem-jks-converter
{{ include "pem-jks-converter" . | indent 2 }}
```

(2) Add following configuration block to your values.yaml

```yaml
- database:
  host: "host"
  username: "username"
  password: "password"
  dbname: "dbname"
```

*/}}

{{- define "pg-init-client" -}}
image: "postgres"
imagePullPolicy: IfNotPresent
command:
  - sh
  - -c
  - |
    ls /tmp/secrets
    ls /tmp/secrets/postgres-password
    if !($(PGPASSWORD=$(cat /tmp/secrets/postgres-password) psql --host=$POSTGRES_HOST --username=$POSTGRES_USER -tc "SELECT 1 FROM pg_database WHERE datname='{{ .Values.database.dbname | default .Chart.Name }}';" | grep -q 1))
    then
      PGPASSWORD=$(cat /tmp/secrets/postgres-password) psql --host=$POSTGRES_HOST --username=$POSTGRES_USER -c 'CREATE DATABASE "{{ .Values.database.dbname | default .Chart.Name }}";'
    fi
env:
  - name: POSTGRES_HOST
    value: {{ default "suite-postgresql" .Values.database.host | quote }}
  - name: POSTGRES_USER
    value: {{ default "postgres" .Values.database.username | quote }}
volumeMounts:
  - name: postgres-password
    mountPath: /tmp/secrets
    readOnly: true
{{- end -}}
