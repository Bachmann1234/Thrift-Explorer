service TestService {
    set<byte> setsAndLists(1: list<double> listOfDoubles, 2: set<binary> binarySet),
    map<bool, byte> maps(1: map<i16,i64> mapofI16toI64)
}