#!/usr/bin/env python

import difflib
import getpass
import os
import sys
import urllib

import cli_tools
import jenkins


class Output(object):
    def __init__(self):
        self.last_status = ''

    def _prefix(self):
        backspace = '\b' * len(self.last_status)
        space = ' ' * len(self.last_status)
        return backspace + space + backspace

    def status(self, text):
        if len(text) > 80:
            text = text[:80]
        sys.stdout.write(self._prefix() + text)
        sys.stdout.flush()
        self.last_status = text

    def emit(self, text):
        sys.stdout.write(self._prefix() + text + '\n')
        sys.stdout.flush()
        self.last_status = ''


class JobConf(object):
    def __init__(self, conf_dir, job_name):
        self.job_name = job_name
        self.job_conf = os.path.join(conf_dir, '%s.xml' %
                                     urllib.quote(job_name, safe=''))

    def update(self, config):
        with open(self.job_conf, 'w') as f:
            f.write(config)

    def delete(self):
        os.unlink(self.job_conf)

    def diff(self, config):
        return difflib.unified_diff(self.config.split('\n'),
                                    config.split('\n'))

    @property
    def exists(self):
        return os.path.exists(self.job_conf)

    @property
    def config(self):
        with open(self.job_conf) as f:
            return f.read()

    @classmethod
    def from_conf(cls, conf_file):
        # Skip non-XML files
        if not conf_file.endswith('.xml'):
            return None

        # Start by canonicalizing...
        conf_dir = os.path.dirname(conf_file)
        conf_file = os.path.basename(conf_file)

        # Decode the filename into the job name
        job_name = urllib.unquote(conf_file[:-len('.xml')])

        return cls(conf_dir, job_name)

    @classmethod
    def from_dir(cls, conf_dir):
        for conf_file in os.listdir(conf_dir):
            # Skip non-XML files
            if not conf_file.endswith('.xml'):
                continue

            # Decode the filename into the job name
            job_name = urllib.unquote(conf_file[:-len('.xml')])

            yield cls(conf_dir, job_name)


_prompt_for_password = object()


@cli_tools.argument('--debug', action='store_true')
@cli_tools.argument('--url', '-U',
                    dest='jenkins_url',
                    default='https://jenkins.ohthree.com/',
                    help="The URL for Jenkins.")
@cli_tools.argument('--username', '-u',
                    default=os.environ['USER'],
                    help="The username to use for accessing Jenkins.")
@cli_tools.argument('--password', '-P',
                    default=_prompt_for_password,
                    help="The password to use for accessing Jenkins.  "
                    "If not provided, the user will be prompted for it.")
@cli_tools.argument('--conf-dir', '-c',
                    default='~/jenkins_config',
                    help="The directory in which Jenkins job configuration "
                    "will be kept.")
def sync_conf(jenkins_url, username, password, conf_dir):
    # Prompt for the password, if necessary
    if password is _prompt_for_password:
        password = getpass.getpass('Password for %s: ' % username)

    # Tilde-expand the config directory and make sure it exists
    conf_dir = os.path.expanduser(conf_dir)
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    elif not os.path.isdir(conf_dir):
        return "Config directory '%s' is not a directory" % conf_dir

    # Get a Jenkins handle
    jenks = jenkins.Jenkins(jenkins_url, username, password)

    # Loop through all jobs
    seen = set()
    out = Output()
    for job in jenks.get_jobs():
        job_name = job['name']

        # Emit a status line
        out.status("Processing job '%s'..." % job_name)

        conf = JobConf(conf_dir, job_name)

        # Get the configuration from Jenkins
        config = jenks.get_job_config(job_name)

        # If the config is None, the job went away before we could get
        # the configuration; loop now so we treat it as not seen, and
        # thus deleted
        if not config:
            continue

        # Remark that we've seen this job
        seen.add(job_name)

        # Does it exist?
        if not conf.exists:
            out.emit("Discovered new job '%s'" % job_name)
            conf.update(config)
            continue

        # Check if there are any differences
        diff = list(conf.diff(config))
        if diff:
            out.emit("Job '%s' has been updated" % job_name)
            out.emit('\n'.join('    %s' % line.rstrip('\n') for line in diff))
            conf.update(config)

    # Now discover any deleted jobs
    for conf in JobConf.from_dir(conf_dir):
        if conf.job_name not in seen:
            out.emit("Job '%s' has been deleted" % conf.job_name)
            conf.delete()

    out.emit("Done!")


if __name__ == '__main__':
    sys.exit(sync_conf.console())
