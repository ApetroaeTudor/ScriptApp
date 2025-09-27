package my.group

import kotlinx.coroutines.*
import io.ktor.network.selector.*
import io.ktor.network.sockets.*
import io.ktor.utils.io.*

suspend fun launch_sv(scope: CoroutineScope)
{
    val selector_manager = SelectorManager(Dispatchers.IO)
    val server_socket = aSocket(selector_manager).tcp().bind("127.0.0.1", 8080)
    println("Server is listening..")
    while (true) {
        val cl_socket = server_socket.accept()
        println("Accepted $cl_socket")
        scope.launch {
            val cl_receive_ch = cl_socket.openReadChannel()
            val cl_send_ch = cl_socket.openWriteChannel(autoFlush = true)
            try{ // suspending
                while(!cl_receive_ch.isClosedForRead)
                {
                    val received_val = cl_receive_ch.readUTF8Line()?:"?"
                    println(received_val)
                    if(received_val == "woof"){
//                        cl_send_ch.writeStringUtf8("hello from sv\n")
                    }
                }
                cl_socket.close()
            }
            catch (e: Throwable){
                cl_socket.close()
            }
        }
    }

}
