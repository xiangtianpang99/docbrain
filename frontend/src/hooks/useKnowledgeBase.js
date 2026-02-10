import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_URL, API_KEY } from '../config'

export function useKnowledgeBase(isBackendReady, isIndexing, serverLastUpdate) {
    const [documents, setDocuments] = useState([])
    const [config, setConfig] = useState(null)
    const [docsLoading, setDocsLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [lastFetchTime, setLastFetchTime] = useState(0)

    // Grouping state
    const [expandedGroups, setExpandedGroups] = useState({})
    const [searchQuery, setSearchQuery] = useState('')

    // Initial Fetch
    useEffect(() => {
        if (isBackendReady) {
            fetchDocuments()
        }
    }, [isBackendReady])

    // Sync Logic
    useEffect(() => {
        // Update local refreshing state based on backend status
        if (isIndexing) {
            setIsRefreshing(true)
        } else {
            setIsRefreshing(false)
        }

        // Check if we need to fetch new data
        // If server has newer data (serverLastUpdate > lastFetchTime) AND is not currently indexing
        if (!isIndexing && serverLastUpdate > lastFetchTime) {
            console.log(`New data detected! Server: ${serverLastUpdate} > Local: ${lastFetchTime}`)
            fetchDocuments()
        }
    }, [isIndexing, serverLastUpdate, lastFetchTime])

    // Auto-expand groups when searching, collapse when cleared
    useEffect(() => {
        if (searchQuery.trim() && config && config.watch_paths) {
            const allGroups = {}
            config.watch_paths.forEach(p => allGroups[p] = true)
            allGroups['Others'] = true
            setExpandedGroups(allGroups)
        } else {
            setExpandedGroups({})
        }
    }, [searchQuery, config])

    const fetchDocuments = async () => {
        try {
            if (documents.length === 0) setDocsLoading(true)
            setIsRefreshing(true)

            const [docsRes, configRes] = await Promise.all([
                axios.get(`${API_URL}/documents`, { headers: { 'Authorization': `Bearer ${API_KEY}` } }),
                axios.get(`${API_URL}/config`, { headers: { 'Authorization': `Bearer ${API_KEY}` } })
            ])

            if (docsRes.data && docsRes.data.status === 'success') {
                setDocuments(docsRes.data.documents)
                setLastFetchTime(Date.now() / 1000)
            }
            if (configRes.data) {
                setConfig(configRes.data)
            }
        } catch (error) {
            console.error("Failed to fetch data:", error)
        } finally {
            setDocsLoading(false)
            setIsRefreshing(false)
        }
    }

    const toggleGroup = (groupName) => {
        setExpandedGroups(prev => ({
            ...prev,
            [groupName]: !prev[groupName]
        }))
    }

    return {
        documents,
        config,
        docsLoading,
        isRefreshing,
        fetchDocuments,
        searchQuery,
        setSearchQuery,
        expandedGroups,
        toggleGroup,
        setExpandedGroups
    }
}
