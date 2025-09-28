package my.group

import kotlinx.serialization.Serializable

@Serializable
data class Message(val error: Boolean, val type: String, val message: String, val result: String, val console: String)
