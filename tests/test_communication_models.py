import json

import pytest

from thrift_explorer.communication_models import CommunicationModelEncoder


def test_encoder_explodes_on_new_thing():
    with pytest.raises(TypeError):
        json.dumps(json, cls=CommunicationModelEncoder)
