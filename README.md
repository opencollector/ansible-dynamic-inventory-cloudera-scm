## What is this?

This is a ansible dynamic inventory script that retrieves hosts from Cloudera Manager.

## Usage

Put `dicm.py` to any of your inventory path along with the configuration file `dicm.ini`.

## Dependencies

- *cm-api*
- *jinja2*

## dicm.ini

Put the settings into `[dicm]` section.  You can use `%(KEY)s` style interpolation where the value corresponding to KEY comes from either `[DEFAULT]` section or the environment variable of the same name.

| Key | Description |
| --- | --- |
| `cloudera_manager_host` | Host name / IP address of Cloudera Manager |
| `loudera_manager_port` | Port number (optional - defaults to 7180) |
| `cloudera_manager_user` | Cloudera Manager user |
| `cloudera_manager_password` | Cloudera Manager password |
| `filter` | Host filter (optional); accepts jinja2 expressions |
| `cluster_group_format` | Group name format for cluster groups (optional) |
| `service_group_format` | Group name format for service groups (optional) |
| `role_group_format` | Group name format for role groups (optional) |
