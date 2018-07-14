struct MyOtherStruct {
    1: required string id;
    2: required list<i64> ints;
}

struct MyStruct {
    1: required i64 myIntStruct;
    2: optional MyOtherStruct myOtherStruct;
}

service StructService {
    MyStruct getMyStruct()
}