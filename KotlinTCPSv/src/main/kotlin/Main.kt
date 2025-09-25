package my.group


import kotlinx.coroutines.runBlocking
import kotlin.script.experimental.api.*
import kotlin.script.experimental.host.toScriptSource
import kotlin.script.experimental.jvm.dependenciesFromCurrentContext
import kotlin.script.experimental.jvm.jvm
import kotlin.script.experimental.jvmhost.BasicJvmScriptingHost

fun main()  = runBlocking{

    launch_sv(this)
//    val script = """
//        val x =1
//        println(x)
//    """
//
//    val host = BasicJvmScriptingHost()
//
//    val compilationConfiguration = ScriptCompilationConfiguration {
//        jvm {
//            dependenciesFromCurrentContext(wholeClasspath = true)
//        }
//    }
//
//    val evaluationConfiguration = ScriptEvaluationConfiguration {}
//
//    val result = host.eval(script.toScriptSource(), compilationConfiguration, evaluationConfiguration)
//
//    var hasErrors = false
//    result.reports.forEach { diagnostic ->
//        val severity = diagnostic.severity
//        val message = diagnostic.message
//        val location = diagnostic.location
//        val startLine = location?.start?.line ?: -1
//        val startCol = location?.start?.col ?: -1
//
//        println("[$severity] $message @ ($startLine:$startCol)")
//
//        if (severity == ScriptDiagnostic.Severity.ERROR) {
//            hasErrors = true
//        }
//    }
//
//    println("\n------------------\n")
//
//    if (hasErrors) {
//        println("Script evaluation failed due to compilation errors.")
//    } else {
//        val returnValue = result.valueOrNull()?.returnValue
//        when (returnValue) {
//            is ResultValue.Value -> {
//                println("Script completed successfully with return value: ${returnValue.value}")
//            }
//            is ResultValue.Unit -> {
//                println("Script completed successfully with no return value.")
//            }
//            is ResultValue.Error -> {
//                println("Script threw an exception during evaluation:")
//                returnValue.error.printStackTrace()
//            }
//            null -> {
//                println("Script evaluation resulted in an unknown state.")
//            }
//
//            else -> {
//
//            }
//        }
//    }


}