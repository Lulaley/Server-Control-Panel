#!/usr/bin/env bash
set -eu

BASE_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
CERTS_DIR="$BASE_DIR/certs"
CERT_PATH="$CERTS_DIR/cert.pem"
KEY_PATH="$CERTS_DIR/key.pem"
CSR_PATH="$CERTS_DIR/req.csr"

mkdir -p "$CERTS_DIR"

PUBLIC="${PUBLIC_HOST:-${CHIMEA_HOST:-${HOSTNAME:-}}}"
SAN="DNS:localhost,IP:127.0.0.1"
if [ -n "$PUBLIC" ]; then
  SAN="$SAN,DNS:$PUBLIC"
  # try to resolve IP
  RESOLVED_IP=$(getent hosts "$PUBLIC" | awk '{print $1}' || true)
  if [ -n "$RESOLVED_IP" ]; then
    SAN="$SAN,IP:$RESOLVED_IP"
  fi
fi

if command -v openssl >/dev/null 2>&1; then
  echo "Generating self-signed certificate (SAN=$SAN)..."
  # Try -addext first
  if openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "$KEY_PATH" -out "$CERT_PATH" -subj "/C=FR/ST=France/L=Paris/O=Local/CN=localhost" -addext "subjectAltName = $SAN" >/dev/null 2>&1; then
    chmod 600 "$KEY_PATH" || true
    echo "Created: $CERT_PATH and $KEY_PATH"
    exit 0
  fi

  # Fallback to config file
  TMP_CFG="$(mktemp)"
  cat > "$TMP_CFG" <<EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = FR
ST = France
L = Paris
O = Local
CN = localhost

[v3_req]
subjectAltName = $SAN
EOF

  openssl req -new -newkey rsa:2048 -nodes -keyout "$KEY_PATH" -out "$CSR_PATH" -config "$TMP_CFG"
  openssl x509 -req -in "$CSR_PATH" -signkey "$KEY_PATH" -out "$CERT_PATH" -days 365 -extensions v3_req -extfile "$TMP_CFG"
  chmod 600 "$KEY_PATH" || true
  rm -f "$CSR_PATH" "$TMP_CFG"
  echo "Created (fallback): $CERT_PATH and $KEY_PATH"
  exit 0
else
  echo "Error: openssl not found in PATH" >&2
  exit 1
fi
