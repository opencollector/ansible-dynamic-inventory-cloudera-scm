## What is this?

This is a ansible dynamic inventory script that retrieves hosts from Cloudera Manager.

## Usage

Put `scm.py` to any of your inventory path along with the configuration file `dicm.ini`.

## Dependencies

- *cm-api*
- *six*
- *jinja2*

## scm.ini

Put the settings into `[scm-di]` section.  `scm_host`, `scm_port`, `scm_user` and `scm_password` are also allowed in `[scm]` section. You can use `%(KEY)s` style interpolation where the value corresponding to KEY comes from either `[DEFAULT]` section or the environment variable of the same name.

| Key | Description |
| --- | --- |
| `scm_host` | Host name / IP address of Cloudera Manager |
| `scm_port` | Port number (optional - defaults to 7180) |
| `scm_user` | Cloudera Manager user |
| `scm_password` | Cloudera Manager password |
| `filter` | Host filter (optional); accepts jinja2 expressions |
| `cluster_group_format` | Group name format for cluster groups (optional) |
| `service_group_format` | Group name format for service groups (optional) |
| `role_group_format` | Group name format for role groups (optional) |
