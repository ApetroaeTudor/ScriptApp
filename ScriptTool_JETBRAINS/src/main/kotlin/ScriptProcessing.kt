package my.group

import kotlin.script.experimental.api.*
import kotlin.script.experimental.jvm.dependenciesFromCurrentContext
import kotlin.script.experimental.jvm.jvm
import kotlin.script.experimental.jvmhost.BasicJvmScriptingHost
import kotlinx.serialization.*
import kotlinx.serialization.json.*
import java.io.ByteArrayOutputStream
import java.io.OutputStream
import java.io.PrintStream
import java.nio.charset.StandardCharsets
import java.util.concurrent.BlockingQueue


class ByteForwardingOutputStream(
    private val outputQueue: BlockingQueue<String>
) : OutputStream() {
    private val fullOutputStream = ByteArrayOutputStream()
    private val lineBuffer = ByteArrayOutputStream()

    @Synchronized
    override fun write(b: Int) {
        fullOutputStream.write(b)

        if (b.toChar() == '\n') {
            outputQueue.put(lineBuffer.toString(StandardCharsets.UTF_8.name()))
            lineBuffer.reset()
        } else {
            lineBuffer.write(b)
        }
    }

    @Synchronized
    override fun write(b: ByteArray, off: Int, len: Int) {
        fullOutputStream.write(b, off, len)

        // 2. Process the chunk for real-time line forwarding.
        for (i in off until off + len) {
            val currentByte = b[i].toInt()
            if (currentByte.toChar() == '\n') {
                outputQueue.put(lineBuffer.toString(StandardCharsets.UTF_8.name()))
                lineBuffer.reset()
            } else {
                lineBuffer.write(currentByte)
            }
        }
    }

    @Synchronized
    override fun flush() {
        fullOutputStream.flush()
        // If there is any remaining data in the line buffer, send it.
        if (lineBuffer.size() > 0) {
            outputQueue.put(lineBuffer.toString(StandardCharsets.UTF_8.name()))
            lineBuffer.reset()
        }
    }

    fun toString(charsetName: String): String {
        return fullOutputStream.toString(charsetName)
    }

    override fun toString(): String {
        return fullOutputStream.toString()
    }
}


class ScriptProcessing(val msg_queue: BlockingQueue<String>) {
    val host = BasicJvmScriptingHost()

    val compilationConfiguration = ScriptCompilationConfiguration {
        jvm {
            dependenciesFromCurrentContext(wholeClasspath = true)
        }
    }
    private val originalConsoleOut: PrintStream = System.out

    fun printToOriginalConsole(message: String) {
        originalConsoleOut.println(message)
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

        val out_capture_stream = ByteForwardingOutputStream(msg_queue)
        val err_capture_stream = ByteForwardingOutputStream(msg_queue)
        val out_print_stream = PrintStream(out_capture_stream, true, StandardCharsets.UTF_8.name())
        val err_print_stream = PrintStream(err_capture_stream, true, StandardCharsets.UTF_8.name())

        val flusher = Thread {
            try {
                while (!Thread.currentThread().isInterrupted) {
                    out_print_stream.flush()
                    err_print_stream.flush()
                    Thread.sleep(50)
                }
            } catch (e: InterruptedException) {
                Thread.currentThread().interrupt()
            }
        }

        try {
            System.setOut(out_print_stream)
            System.setErr(err_print_stream)

            flusher.start()

            val result = host.eval(namedScriptSource, compilationConfiguration, evaluationConfiguration)
            out_print_stream.flush()
            err_print_stream.flush()
            msg_queue.put("QUIT")

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

            val msg_to_send = Message(
                hasErrors, type, diagnosticMessage.toString(), returnVal, console = "Output: ${
                    out_capture_stream.toString(
                        StandardCharsets.UTF_8.name()
                    )
                }\nError Output: ${err_capture_stream.toString(StandardCharsets.UTF_8.name())}"
            )
            return Json.encodeToString(msg_to_send)


        } finally {
            flusher.interrupt()
            flusher.join()

            out_print_stream.flush()
            err_print_stream.flush()
            System.setOut(originalOut)
            System.setErr(originalErr)
        }

    }

}