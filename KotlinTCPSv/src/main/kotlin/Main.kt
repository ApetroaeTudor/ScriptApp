package my.group


import kotlinx.coroutines.runBlocking
import java.io.File
import java.io.InputStream


fun main() = runBlocking {

//    launch_sv(this)
    val inputStream = File("MyScript.kts").inputStream()
    val inputString = inputStream.reader().use{it.readText()}

    val myScriptProcessor = ScriptProcessing()
    val result = myScriptProcessor.get_eval(inputString)
    println(result)
}