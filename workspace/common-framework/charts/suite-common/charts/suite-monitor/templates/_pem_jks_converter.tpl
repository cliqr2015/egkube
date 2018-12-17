{{/* vim: set filetype=mustache: */}}
{{/*
====================
PEM to JKS Converter
====================
Requirements:
- Mount private_key.pem at /cert/private_key.pem
- Mount certificate.pem at /cert/certificate.pem
- Mount certificate.pem at /ca/ca_certificate.pem
How To Use:
- Use in your initContainer block
- Mount emptydir at the /jks-secrets. truststore.jks and keystore.jks are saved to this directory
*/}}
{{- define "pem-jks-converter" -}}
image: openjdk:8
imagePullPolicy: IfNotPresent
command:
  - sh
  - -c
  - |
    openssl pkcs12 -export -out cert.p12 -inkey /cert/private_key.pem -in /cert/certificate.pem -password pass:password && \
    openssl x509 -outform der -in /ca/ca_certificate.pem -out ca.der && \
    keytool -importkeystore -srckeystore cert.p12 -srcstoretype PKCS12 -deststoretype JKS -destkeystore /jks-secrets/keystore.jks -storepass password -srcstorepass password && \
    keytool -importcert -keystore /jks-secrets/keystore.jks -storepass password -alias svc-cat-ca -file ca.der -noprompt && \
    keytool -import -alias svc-cat-ca -keystore /jks-secrets/truststore.jks -file ca.der -storepass password -noprompt
env:
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name
  - name: POD_NAMESPACE
    valueFrom:
      fieldRef:
        fieldPath: metadata.namespace
{{- end -}}
