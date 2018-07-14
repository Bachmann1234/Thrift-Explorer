exception OMGException {
    1: required string description

}
service PingExploder {
    void ping() throws (1: OMGException omg)
}