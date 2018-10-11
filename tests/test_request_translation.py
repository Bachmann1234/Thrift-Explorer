from testing_utils import load_thrift_from_testdir
from thrift_explorer.thrift_manager import parse_service_specs, translate_request_body


def _parse_services_for_thrift(thrift_file):
    thrift_module = load_thrift_from_testdir(thrift_file)
    service_specs = parse_service_specs({thrift_file: thrift_module})
    return thrift_module, service_specs[thrift_file]


def test_pass():
    thrift_module, service_specs = _parse_services_for_thrift("simpleType.thrift")
    test_service = service_specs["TestService"]
    assert {} == translate_request_body(
        test_service.endpoints["voidMethod"], {}, thrift_module
    )


def test_basic_args():
    thrift_module, service_specs = _parse_services_for_thrift("simpleType.thrift")
    test_service = service_specs["TestService"]
    assert {"intParameter": 2, "stringParameter": "batman"} == translate_request_body(
        test_service.endpoints["returnInt"],
        {"intParameter": 2, "stringParameter": "batman"},
        getattr(thrift_module, "TestService"),
    )


def test_basic_args_skipping_missing_ones():
    thrift_module, service_specs = _parse_services_for_thrift("simpleType.thrift")
    test_service = service_specs["TestService"]
    assert {"intParameter": 2} == translate_request_body(
        test_service.endpoints["returnInt"],
        {"intParameter": 2},
        getattr(thrift_module, "TestService"),
    )


def test_enum():
    enum_thrift, services = _parse_services_for_thrift("enum.thrift")
    hero_service = services["HeroService"]
    assert {"hero": enum_thrift.Superhero.BATMAN} == translate_request_body(
        hero_service.endpoints["saveHero"],
        {"hero": "BATMAN"},
        getattr(enum_thrift, "HeroService"),
    )


def test_map():
    collections_thrift, services = _parse_services_for_thrift("collections.thrift")
    test_service = services["TestService"]
    assert {"mapofI16toI64": {4: 5}} == translate_request_body(
        test_service.endpoints["maps"],
        {"mapofI16toI64": {4: 5}},
        getattr(collections_thrift, "TestService"),
    )


def test_collections():
    collections_thrift, services = _parse_services_for_thrift("collections.thrift")
    test_service = services["TestService"]
    assert {
        "listOfDoubles": [float(1), 1.4, 9.323],
        "binarySet": {b"sdas", b"4232", b"bs"},
    } == translate_request_body(
        test_service.endpoints["setsAndLists"],
        {"listOfDoubles": [1.0, 1.4, 9.323], "binarySet": {b"sdas", b"4232", b"bs"}},
        getattr(collections_thrift, "TestService"),
    )


def test_struct():
    struct_thrift, services = _parse_services_for_thrift("structThrift.thrift")
    struct_service = services["StructService"]
    assert {
        "myStruct": struct_thrift.MyStruct(
            myIntStruct=4,
            myOtherStruct=struct_thrift.MyOtherStruct(id="4", ints=[1, 2, 3]),
        )
    } == translate_request_body(
        struct_service.endpoints["sendMyStruct"],
        {
            "myStruct": {
                "myIntStruct": 4,
                "myOtherStruct": {"id": "4", "ints": [1, 2, 3]},
            }
        },
        getattr(struct_thrift, "StructService"),
    )
