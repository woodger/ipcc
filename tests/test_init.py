import app.init as compatibility
import app.ipcc as ipcc_module


def test_compatibility_exports():

    assert compatibility.parse_networks is ipcc_module.parse_stream
    assert compatibility.collapse_networks is ipcc_module.collapse_networks
    assert compatibility.fetch_data is ipcc_module.fetch_networks
    assert compatibility.count_to_prefix_v4 is ipcc_module.prefix_v4
