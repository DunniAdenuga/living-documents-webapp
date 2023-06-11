# first we declare our upstream server, which is our Gunicorn application
upstream living_document_server {
    # docker will automatically resolve this to the correct address
    # because we use the same name as the service: "djangoapp"
    server djangoapp:8000;
}

# declare the upstream node stuff
upstream node_front_end {
    # docker will automatically resolve this to the correct address
    # because we use the same name as the service: "nodeapp"
    server nodeapp:9080;
}

# now we declare our main server
server {

    listen 80;
    server_name localhost;


    # everything is passed to Gunicorn for the documents api
    location /documents/ {
        proxy_pass http://living_document_server;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
	proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_redirect off;
	proxy_ignore_client_abort on;
	proxy_socket_keepalive on;
	proxy_connect_timeout 10080;
	proxy_read_timeout 10080;
	keepalive_timeout 10080;
	proxy_send_timeout 10080;
	proxy_buffer_size 64k;
	proxy_buffers 16 32k;
	proxy_busy_buffers_size 64k;

    }

    location /static/ {
        alias /opt/services/djangoapp/static/;
    }

    location /media/ {
        alias /opt/services/djangoapp/media/;
    }

    location / {
        proxy_pass http://node_front_end;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_redirect off;
	proxy_ignore_client_abort on;
	proxy_socket_keepalive on;
	proxy_read_timeout 9999;
	proxy_connect_timeout 9999;
	keepalive_timeout 9999;
	proxy_send_timeout 9999;
    }
}
