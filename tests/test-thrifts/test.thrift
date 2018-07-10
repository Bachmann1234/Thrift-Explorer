struct ImAStruct {
    1: optional string optionalValue;
    2: required i32 requiredValue
}

service TestService {
    i32 returnInt(1: i32 intParameter, 2: string stringParameter)
}