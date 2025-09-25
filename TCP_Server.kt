package kotlintcpsv

import io.ktor.network.selector.*
import io.ktor.network.sockets.*
import io.ktor.utils.io.*
import kotlinx.coroutines.*

fun main() = runBlocking{
    val selector_manager = SelectorManager(Dispathers.IO)
    val server_socket = aSocket(selector_manager).tcp().bind("127.0.0.1",8080)
    println("Server is listening..")
    while(true)
    {
        
    }

}
