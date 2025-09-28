package my.group

import kotlinx.coroutines.*
import io.ktor.network.selector.*
import io.ktor.network.sockets.*
import io.ktor.utils.io.*
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.PrintStream
import java.util.concurrent.BlockingQueue
import java.util.concurrent.LinkedBlockingQueue


suspend fun launch_sv(scope: CoroutineScope) {
    val msg_queue: BlockingQueue<String> = LinkedBlockingQueue()
    val myScriptProcessor = ScriptProcessing(msg_queue)


    val selector_manager = SelectorManager(Dispatchers.IO)
    val server_socket = aSocket(selector_manager).tcp().bind("127.0.0.1", 8080)
    println("Server is listening..")
    while (true) {
        val cl_socket = server_socket.accept()
        println("Accepted $cl_socket")
        scope.launch {
            val cl_receive_ch = cl_socket.openReadChannel()
            val cl_send_ch = cl_socket.openWriteChannel(autoFlush = true)
            try {
                while (true) {
                    val received_val = cl_receive_ch.readUTF8Line() ?: break
                    val tokenized_received_val = received_val.split('`')
                    val script_txt = tokenized_received_val[3].replace("@@@", "\n")
                    val evalJob = async(Dispatchers.IO) {
                        myScriptProcessor.get_eval(script_txt)
                    }
                    while (true) {
                        val msg = msg_queue.poll()
                        if (msg != null) {
                            if (msg == "QUIT") {
                                break
                            }
                            if (!msg.trim().isEmpty()){
                                val msg = Message(error = false, type = "REAL_TIME", message = "", result = "", console = msg)
                                cl_send_ch.writeStringUtf8(Json.encodeToString(msg) + "\n")
                            }
                        }
                        delay(50)
                    }
                    val result = evalJob.await()
                    cl_send_ch.writeStringUtf8(result + "\n")


                }
                cl_socket.close()
            } catch (e: Throwable) {
                cl_socket.close()
            }
        }
    }

}
