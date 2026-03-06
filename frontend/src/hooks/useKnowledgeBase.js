import { useState, useEffect } from 'react'
import axios from 'axios'
import { API_URL, API_KEY } from '../config'

export function useKnowledgeBase(isBackendReady, isIndexing, serverVersion) {
    const [documents, setDocuments] = useState([])
    const [config, setConfig] = useState(null)
    const [docsLoading, setDocsLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [lastFetchVersion, setLastFetchVersion] = useState(0)

    // Grouping state
    const [expandedGroups, setExpandedGroups] = useState({})
    const [searchQuery, setSearchQuery] = useState('')

    // Initial Fetch
    useEffect(() => {
        if (isBackendReady) {
            fetchDocuments()
        }
    }, [isBackendReady])

    const [wasIndexing, setWasIndexing] = useState(false)

    // Sync Logic
    useEffect(() => {
        // Update local refreshing state based on backend status
        setIsRefreshing(isIndexing)

        if (isIndexing) {
            setWasIndexing(true)
        } else {
            let shouldFetch = false

            // Trigger 1: State transition from indexing to idle
            if (wasIndexing) {
                console.log("Indexing finished! Triggering refresh...")
                shouldFetch = true
                setWasIndexing(false)
            }
            // Trigger 2: Server got new data silently (version incremented)
            else if (lastFetchVersion > 0 && serverVersion > lastFetchVersion) {
                console.log(`New data version detected! Server: ${serverVersion} > Local: ${lastFetchVersion}`)
                shouldFetch = true
            }

            if (shouldFetch) {
                fetchDocuments()
            }
        }
    }, [isIndexing, serverVersion, lastFetchVersion, wasIndexing])

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
                const version = docsRes.data.docs_version || 1
                setLastFetchVersion(version)
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
