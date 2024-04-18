echo "
  <VirtualHost *:80>
      ServerName 13.236.44.123
      Redirect / https://13.236.44.123
  </VirtualHost> 
      
  <VirtualHost  *:443>
      
      ServerName 13.236.44.123
      SSLEngine on
      SSLProxyEngine On
      SSLCertificateFile      /etc/ssl/certs/ssl-cert-snakeoil.pem
      SSLCertificateKeyFile /etc/ssl/private/ssl-cert-snakeoil.key
      
      ProxyRequests     Off
      ProxyPreserveHost On
      #AllowEncodedSlashes NoDecode
      <Proxy *>
          Order deny,allow
          Allow from all
      </Proxy>
      
      ProxyPass         /_stcore        ws://localhost:5000/_stcore
      ProxyPassReverse  /_stcore        ws://localhost:5000/_stcore
      
      # The order is important here
      ProxyPass         /        http://localhost:5000/
      ProxyPassReverse  /        http://localhost:5000/
      
  </VirtualHost>>" > /etc/apache2/sites-available/deploy_healthcare_app.conf
