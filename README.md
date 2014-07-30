Jenkins XML pipeline extractor
=============

This dumps all jobs from a jenkins master into xml representation for local use.

Installation
-------

    virtualenv .jenkins_venv
    source .jenkins_venv/bin/activate
    pip install -r requirements.txt

Usage
-----------------

    usage: sync_jenkins_config.py [-h] [--debug] [--url JENKINS_URL]
                                  [--username USERNAME] [--password PASSWORD]
                                  [--conf-dir CONF_DIR]

Example
------------

    source ~/.jenkins_venv/bin/activate
    ./sync_jenkins_config.py --url https://jenkins.myservice.com --username mattusername --conf-dir confs

    Password for mattusername: 
    Processing job 'build-app-deps'...
    ...
    Done!
