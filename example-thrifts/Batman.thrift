include "basethrifts/Core.thrift"

enum CrimeType {
    MURDER,
    ROBBERY,
    OTHER
}

struct Villain {
    1: required i32 villainId;
    2: required string name;
    3: required string description;
    5: optional Core.Location hideoutLocation;
}

struct Case {
    2: required string caseName;
    3: required CrimeType CrimeType;
    4: optional Villain mainSuspect;
    5: optional list<string> notes;
}

service BatPuter {
   void ping(),
   Villain getVillain(1: i32 villainId)
   Villain addVillain(
       1: string name, 
       2: string description, 
       3: Core.Location hideoutLocation
   )
   bool saveCase(1: Case caseToSave)
}