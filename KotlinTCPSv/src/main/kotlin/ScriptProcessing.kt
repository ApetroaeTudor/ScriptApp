package my.group

import kotlin.script.experimental.api.*
import kotlin.script.experimental.host.toScriptSource
import kotlin.script.experimental.jvm.dependenciesFromCurrentContext
import kotlin.script.experimental.jvm.jvm
import kotlin.script.experimental.jvmhost.BasicJvmScriptingHost
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import java.io.ByteArrayOutputStream
import java.io.PrintStream
import java.nio.charset.StandardCharsets

@Serializable
data class Message(val error: Boolean, val type: String, val message: String, val result: String, val console:String)

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

        val originalOut = System.out
        val originalErr = System.err

        val out_capture_stream = ByteArrayOutputStream()
        val err_capture_stream = ByteArrayOutputStream()
        val out_print_stream = PrintStream(out_capture_stream, true, StandardCharsets.UTF_8.name())
        val err_print_stream = PrintStream(err_capture_stream, true, StandardCharsets.UTF_8.name())

        try {
            System.setOut(out_print_stream)
            System.setErr(err_print_stream)

            val result = host.eval(namedScriptSource, compilationConfiguration, evaluationConfiguration)
            var hasErrors = false
            val diagnosticMessage: StringBuilder = StringBuilder("")
            if (result is ResultWithDiagnostics.Failure) {
                hasErrors = true
                result.reports.forEach { diagnostic ->
                    if (diagnostic.severity.toString() == "ERROR") {
                        diagnosticMessage.append("[${diagnostic.severity}] ${diagnostic.message}\n")
                        diagnostic.location?.let { loc ->
                            val line = loc.start.line
                            val column = loc.start.col
                            diagnosticMessage.append(" - AT [LINE: $line, COLUMN: $column] - ")
                        }
                    }
                }
            } else
            {
                diagnosticMessage.append("Compiled: ")
            }

            var returnVal = "None"
            val evaluationResult = result.valueOrNull()
            if (evaluationResult != null)
            {
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

            val msg_to_send = Message(hasErrors, type, diagnosticMessage.toString(), returnVal, console = "Output: ${out_capture_stream.toString(
                StandardCharsets.UTF_8.name())}\nError Output: ${err_capture_stream.toString(StandardCharsets.UTF_8.name())}")
            return Json.encodeToString(msg_to_send)


        } finally {
            System.setOut(originalOut)
            System.setErr(originalErr)
        }

}

}