println("Starting long-running script...")
// A simple loop that simulates work
for (i in 1..10) {
    println("Working... step $i")
    Thread.sleep(2000) // sleep 2 seconds per step
}
// Compute something intensive
fun fibonacci(n: Int): Long {
    return if (n <= 1) n.toLong() else fibonacci(n - 1) + fibonacci(n - 2)
}
val result = fibonacci(35) // intensive recursive computation
println("Fibonacci(35) = $result")
println("Script finished!")