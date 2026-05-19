# Introduction to gala-ragdoll

gala-ragdoll provides a unit test framework based on flask_testing and implements basic function tests on REST APIs for configuration tracing.

## flask_testing Overview

Flask-testing wraps unittest and provides a unit test tool for Flask.
Before using it, you need to use `create_app()` to return an app. You can use the `client` attribute to simulate client access.
Example: `client.get('/', headers={'Cookie':cookie})`
Example: `client.post('/', data=parama, follow_redirects=True)`
Other usage methods are similar to those of unittest.

For details about flask-testing, see <http://www.pythondoc.com/flask-testing/index.html>.

## gala-ragdoll Test Framework

gala-ragdoll provides a flask_testing unit test framework for the configuration tracing service, which is mainly used for basic function tests and developer self-tests.

### Basic Function Tests

- test_domain_controller

  Provides REST API tests for three types of domain operations. Each test module performs specific function tests, including setting, querying, and deleting a domain.

- test_host_controller

  Provides REST API tests for three types of node operations. Each test module performs specific function tests, including adding a node, querying nodes in a domain, and deleting nodes from a domain.

- test_management_controller

  Provides REST API tests for three types of management configuration operations. Each test module performs specific function tests, including adding, querying, and deleting management configurations.

- test_confs_controller

  Provides REST API tests for four types of configuration operations. Each test module performs specific function tests, including querying the actual configuration, querying the total supported configuration, verifying the configuration, and synchronizing the configuration.

### Developer Self-tests

- test_yang.py

  Tests whether the YANG model is compliant.

- test_config_model.py

  Tests whether the conversion script can convert an object.

- test_reverse_config_model.py

  Tests whether the reverse conversion script can convert data back into an object.
