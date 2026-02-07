import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { API_URL, API_KEY } from '../config'

export function useChat(currentSessionId, onLoadSessions) {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am docBrain. How can I help you today?' }
    ])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)

    // Load messages when session changes
    useEffect(() => {
        if (!currentSessionId) {
            // Reset to welcome if no session (or we can keep it empty)
            setMessages([{ role: 'assistant', content: 'Hello! I am docBrain. How can I help you today?' }])
            return
        }

        const loadMessages = async () => {
            try {
                const res = await axios.get(`${API_URL}/sessions/${currentSessionId}/messages`, {
                    headers: { 'Authorization': `Bearer ${API_KEY}` }
                })
                if (res.data.messages) {
                    if (res.data.messages.length > 0) {
                        setMessages(res.data.messages)
                    } else {
                        // New session
                        setMessages([{ role: 'assistant', content: 'Hello! I am docBrain. How can I help you today?' }])
                    }
                }
            } catch (e) {
                console.error("Failed to load messages", e)
                setMessages([])
            }
        }
        loadMessages()
    }, [currentSessionId])

    const handleSend = async () => {
        if (!input.trim() || isLoading) return

        const userMessage = input
        setMessages(prev => [...prev, { role: 'user', content: userMessage }])
        setInput('')
        setIsLoading(true)

        try {
            // Refresh session title locally if it's the first message
            // We trigger the callback to let parent know it might want to refresh sessions
            const isNewSession = messages.length <= 2

            const response = await axios.post(`${API_URL}/query?session_id=${currentSessionId || ''}`, {
                query: userMessage,
                quality_mode: false,
                force_crew: false
            }, {
                headers: {
                    'Authorization': `Bearer ${API_KEY}`,
                    'Content-Type': 'application/json'
                }
            })

            if (response.data && response.data.status === 'success') {
                setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }])
                if (isNewSession && onLoadSessions) {
                    onLoadSessions()
                }
            } else {
                setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Received unexpected response from server.' }])
            }

        } catch (error) {
            console.error("API Error:", error)
            let errorMsg = "Sorry, I couldn't connect to the server. Please check if the backend is running."
            if (error.response) {
                errorMsg = `Server Error: ${error.response.data.detail || error.response.statusText}`
            }
            setMessages(prev => [...prev, { role: 'assistant', content: errorMsg }])
        } finally {
            setIsLoading(false)
        }
    }

    return {
        messages,
        input,
        setInput,
        isLoading,
        handleSend,
        setMessages
    }
}
