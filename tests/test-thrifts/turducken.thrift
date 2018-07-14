enum DOG {
    GOLDEN,
    CORGI,
    BASSET
}

struct TheStruct {
    // Maps cannot be keys in a other maps in reality. but lets see if it parses
    1: required map<map<set<list<DOG>>, list<string>>, i64> myInsaneStruct;
}

service StructService {
    TheStruct getTheStruct()
}