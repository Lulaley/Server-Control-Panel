# Installer acme.sh
curl https://get.acme.sh | sh
source ~/.bashrc

# Obtenir le certificat (Nginx doit être en marche)
acme.sh --issue -d chimea.fr -d www.chimea.fr --nginx

# Installer le certificat dans Nginx
acme.sh --install-cert -d chimea.fr \
  --key-file /etc/nginx/ssl/chimea. fr.key \
  --fullchain-file /etc/nginx/ssl/chimea.fr.crt \
  --reloadcmd "systemctl reload nginx"