package my.group

import kotlin.script.experimental.api.*
import kotlin.script.experimental.host.toScriptSource
import kotlin.script.experimental.jvm.dependenciesFromCurrentContext
import kotlin.script.experimental.jvm.jvm
import kotlin.script.experimental.jvmhost.BasicJvmScriptingHost
import kotlinx.serialization.*
import kotlinx.serialization.json.*

@Serializable
data class Message(val error: Boolean, val type: String, val message: String, val result: String)

class ScriptProcessing {
    val host = BasicJvmScriptingHost()

    val compilationConfiguration = ScriptCompilationConfiguration {
        jvm {
            dependenciesFromCurrentContext(wholeClasspath = true)
        }
    }

    val evaluationConfiguration = ScriptEvaluationConfiguration {}

    suspend fun get_eval(script: String): String {
        val namedScriptSource = object : SourceCode {
            override val text: String = script
            override val name: String = "MyScript.kts"
            override val locationId: String = "MyScript.kts"
        }
        val result = host.eval(namedScriptSource, compilationConfiguration, evaluationConfiguration)
        var hasErrors = false
        var diagnosticMessage: StringBuilder = StringBuilder("")
        if (result is ResultWithDiagnostics.Failure) {
            hasErrors = true
            result.reports.forEach { diagnostic ->
                if (diagnostic.severity.toString() == "ERROR") {
                    diagnosticMessage.append("[${diagnostic.severity}] ${diagnostic.message}\n")
                }
            }
        } else {
            diagnosticMessage.append("Compiled: ")
        }

        var returnVal = "None"
        val evaluationResult = result.valueOrNull()
        if (evaluationResult != null) {
            val returnValue = evaluationResult.returnValue
            when (returnValue) {
                is ResultValue.Value -> {
                    diagnosticMessage.append("SUCCESS")
                    returnVal = returnValue.value.toString()
                }

                is ResultValue.Unit -> {
                    diagnosticMessage.append("SUCCESS")
                    returnVal = "Unit"
                }

                is ResultValue.Error -> {
                    diagnosticMessage.append("Runtime Error")
                    returnVal = "None"
                }

                else -> {
                    diagnosticMessage.append("Unknown Behavior")
                    returnVal = "None"
                }
            }
        }


        val type = when (hasErrors) {
            true -> "ERROR"; else -> "DEBUG"
        }

        val msg_to_send = Message(hasErrors, type, diagnosticMessage.toString(), returnVal)
        return Json.encodeToString(msg_to_send)
    }

}