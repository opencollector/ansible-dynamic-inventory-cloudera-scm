#!/usr/bin/env python
#
# Copyright (c) 2018 Moriyoshi Koizumi <mozo@mozo.jp>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
import errno
import io
import os
import json
import sys
import six
import jinja2.sandbox
from cm_api.api_client import ApiResource
from six.moves.configparser import ConfigParser
from ansible.template import safe_eval


if six.PY2:
    FileNotFoundError = lambda f: IOError(errno.ENOENT, '%s: %s' % (os.strerror(errno.ENOENT), f))


class ConfigurationError(Exception):
    pass


def read_config(config_file):
    parser = ConfigParser(os.environ)
    parser.read(config_file)
    all_items = parser.items('scm')
    if parser.has_section('scm-di'):
        all_items.extend(parser.items('scm-di'))
    return dict(all_items)


def main():
    config_file = os.environ.get('SCM_INI_FILE', 'scm.ini')
    if not os.path.isabs(config_file):
        dirname = os.path.dirname(sys.argv[0])
        basename = os.path.basename(config_file)
        dirs = [dirname]
        try:
            dirs.append(os.path.dirname(os.path.join(dirname, os.readlink(sys.argv[0]))))
        except:
            pass
        for dir_ in dirs:
            _config_file = os.path.join(dir_, basename)
            if os.path.exists(_config_file):
                config_file = _config_file
                break
        else:
            raise FileNotFoundError(config_file)
    config = read_config(config_file)

    def get(key, default=None, as_=str, required=True, empty_as_none=True):
        rv = config.get(key)
        if rv is not None:
            rv = rv.strip()
        if empty_as_none and not rv:
            rv = None
        if rv is None:
            rv = default
            if rv is None and required:
                raise ConfigurationError('setting {} does not exist'.format(key))
        if as_ and rv is not None:
            try:
                v = as_(rv)
            except (TypeError, ValueError):
                raise ConfigurationError('invalid value for setting {}: {}'.format(key, rv))
        else:
            v = rv
        return v


    cm_host = get('scm_host', 'localhost', required=True)
    cm_port = get('scm_port', None, as_=int, required=False)
    cm_user = get('scm_user', required=True)
    cm_password = get('scm_password', required=True)
    cluster_group_format = get('cluster_group_format', '{}', required=True) 
    service_group_format = get('service_group_format', '{}', required=True) 
    role_group_format = get('role_group_format', '{}', required=True) 
    filter_ = get('filter')

    if filter_:
        je = jinja2.sandbox.SandboxedEnvironment()
        filter_pred = lambda **args: je.from_string('{%%if (%s) %%}True{%%endif%%}' % filter_).render(**args) == 'True'
    else:
        filter_pred = lambda **args: True

    api = ApiResource(cm_host, cm_port or None, cm_user, cm_password)

    hosts = api.get_all_hosts('full')

    hostvars = {}
    hosts_for_clusters = {}
    hosts_for_services = {}
    hosts_for_roles = {}

    for host in hosts:
        host_id = host.hostId
        host_name = host.hostname
        ip_address = host.ipAddress
        cluster_name = host.clusterRef.clusterName
        role_names = ['-'.join(roleRef.roleName.split('-')[:2]) for roleRef in host.roleRefs]
        service_names = [roleRef.serviceName for roleRef in host.roleRefs]
        vars_ = dict(
            host_id=host_id,
            host_name=host_name,
            ip_address=ip_address,
            cluster_name=cluster_name,
            role_names=role_names,
            service_names=service_names
        )
        pred_value = filter_pred(**vars_)
        if pred_value:
            hostvars[host_name] = {
                'ansible_ssh_host': ip_address,
                'ip_address': ip_address,
                'scm_host_id': host_id,
                'scm_cluster_name': cluster_name,
                'scm_role_names': role_names,
                'scm_service_names': service_names,
            }

            hosts_for_clusters.setdefault(cluster_group_format.format(cluster_name, **vars_), set()).add(host_name)
            for service_name in service_names:
                hosts_for_services.setdefault(service_group_format.format(service_name, **vars_), set()).add(host_name)
            for role_name in role_names:
                hosts_for_roles.setdefault(role_group_format.format(role_name, **vars_), set()).add(host_name)

    resp = {
        '_meta': {
            'hostvars': hostvars,
        },
    }
    def hosts_sorted(d):
        return {
            k: list(sorted(v))
            for k, v in d.items()
        }
    resp.update(hosts_sorted(hosts_for_clusters))
    resp.update(hosts_sorted(hosts_for_services))
    resp.update(hosts_sorted(hosts_for_roles))
    if six.PY2:
        json.dump(resp, sys.stdout, ensure_ascii=False, indent=2, encoding='UTF-8')
    else:
        json.dump(resp, io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8'), ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
