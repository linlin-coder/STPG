version 1.0

struct Parameter {
    Map[String, String] parameter
    Map[String, String] environment
    Map[String, String] software
    Map[String, String] database
    Map[String, String] script
}

struct ModuleConfig {
    Map[String , Parameter] module
}