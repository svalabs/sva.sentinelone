"""
Role unit tests
"""


def test_packages(host):
    """
    Ensure that packages are installed
    """
    os = host.ansible("setup")["ansible_facts"]["ansible_os_family"].lower()
    if os == "debian":
        pkg = 'sentinelagent'
    else:
        pkg = 'SentinelAgent'
    assert host.package(pkg).is_installed


def test_service(host):
    """
    Ensure that service is enabled and running
    """
    srv = 'sentinelone.service'
    _srv = host.service(srv)
    assert _srv.is_enabled
    assert _srv.is_running


def test_registration(host):
    """
    Ensure that registration has succeeded
    """
    with host.sudo():
        cmd = host.run(
            "sentinelctl management status"
        ).stdout.strip().split("\n")
        # check that URL and UUID are not undefined
        _url = [x for x in cmd if "URL" in x]
        _uuid = [x for x in cmd if "UUID" in x]
        _connect = [x for x in cmd if "Connectivity" in x]
        assert "undefined" not in _url[0]
        assert "undefined" not in _uuid[0]
        assert "Off" not in _connect[0]
