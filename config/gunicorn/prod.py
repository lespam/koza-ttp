"""Gunicorn *production* config file (systemd: deploy/systemd/koza-ttp.service)"""

# Django WSGI application path in pattern MODULE_NAME:VARIABLE_NAME
wsgi_app = "project.wsgi:application"
# The number of worker processes for handling requests (the VM is small: 1 vCPU)
workers = 2
threads = 2
# A genetic programming run happens inside the request and can take minutes
timeout = 900
# The socket to bind: only nginx talks to gunicorn
bind = "127.0.0.1:8000"
# Write access and error info to /var/log
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
# Redirect stdout/stderr to log file
capture_output = True
# systemd keeps it in the foreground and restarts it if it fails
daemon = False
