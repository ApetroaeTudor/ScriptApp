package my.group

import kotlinx.coroutines.*
import io.ktor.network.selector.*
import io.ktor.network.sockets.*
import io.ktor.utils.io.*


suspend fun launch_sv(scope: CoroutineScope) {
    val myScriptProcessor = ScriptProcessing()


    val selector_manager = SelectorManager(Dispatchers.IO)
    val server_socket = aSocket(selector_manager).tcp().bind("127.0.0.1", 8080)
    println("Server is listening..")
    while (true) {
        val cl_socket = server_socket.accept()
        println("Accepted $cl_socket")
        scope.launch {
            val cl_receive_ch = cl_socket.openReadChannel()
            val cl_send_ch = cl_socket.openWriteChannel(autoFlush = true)
            try { // suspending
                while (true) {
                    val received_val = cl_receive_ch.readUTF8Line() ?: break
                    val tokenized_received_val = received_val.split('`')
                    val script_txt = tokenized_received_val[3].replace("@@@", "\n")
                    println(script_txt)




                    val result = myScriptProcessor.get_eval(script_txt)
                    cl_send_ch.writeStringUtf8(result+"\n")

                    when (tokenized_received_val[1]) {
                        "COMPILE" -> {
                            println("COMPILATION RESULT DUMP: $result")
                        }

                        "EXECUTE" -> {
                            println("EXECUTE RESULT DUMP: $result")
                        }

                    }

                }
                cl_socket.close()
            } catch (e: Throwable) {
                cl_socket.close()
            }
        }
    }

}
