from chrisomatic.spec.given import GivenCube, GivenCubePlugin
from serde import from_dict


def test_looks_like_store_url():
    assert GivenCube.looks_like_store_url(
        "https://cube.chrisproject.org/api/v1/plugins/2/"
    )
    assert GivenCube.looks_like_store_url(
        "https://cube.chrisproject.org/api/v1/plugins/34/"
    )
    assert GivenCube.looks_like_store_url("http://localhost/api/v1/plugins/34/")
    assert GivenCube.looks_like_store_url(
        "http://chrisstore.local:8010/api/v1/plugins/34/"
    )
    assert not GivenCube.looks_like_store_url(
        "https://cube.chrisproject.org/api/v1/pipelines/5/"
    )
    assert not GivenCube.looks_like_store_url("https://cube.chrisproject.org/api/v1/")
    assert not GivenCube.looks_like_store_url("python")
    assert not GivenCube.looks_like_store_url("fnndsc/chris:1.2.3")
    assert not GivenCube.looks_like_store_url("pl-simpledsapp")
    assert not GivenCube.looks_like_store_url("dbg-nvidia-smi")


def test_looks_like_image_tag():
    assert GivenCube.looks_like_image_tag("fnndsc/pl-whatever")
    assert GivenCube.looks_like_image_tag("fnndsc/something:1.2.3")
    assert GivenCube.looks_like_image_tag("docker.io/library/python")
    assert not GivenCube.looks_like_image_tag(
        "http://chrisstore.local:8010/api/v1/plugins/34/"
    )
    assert not GivenCube.looks_like_image_tag(
        "https://cube.chrisproject.org/api/v1/pipelines/5/"
    )
    assert not GivenCube.looks_like_image_tag("https://cube.chrisproject.org/api/v1/")
    assert not GivenCube.looks_like_image_tag("python")
    assert not GivenCube.looks_like_image_tag("pl-simpledsapp")


def test_looks_like_public_repo():
    assert GivenCube.looks_like_public_repo("https://github.com/FNNDSC/pl-simpledsapp")
    assert GivenCube.looks_like_public_repo(
        "https://gitlab.com/jennydaman/crispy-octo-meme"
    )
    assert not GivenCube.looks_like_public_repo(
        "http://chrisstore.local:8010/api/v1/plugins/34/"
    )
    assert not GivenCube.looks_like_public_repo("pl-simpledsapp")


def test_deserialization_untagged_union():
    """
    https://github.com/yukinarit/pyserde/issues/292
    """
    data = {
        "compute_resource": [],
        "users": [],
        "pipelines": [],
        "plugins": ["fnndsc/pl-simpledsapp", {"name": "pl-complicateddsapp"}],
    }
    expected = GivenCube(
        users=[],
        pipelines=[],
        compute_resource=[],
        plugins=["fnndsc/pl-simpledsapp", GivenCubePlugin(name="pl-complicateddsapp")],
    )
    actual: GivenCube = from_dict(GivenCube, data)
    assert expected.plugins == actual.plugins
