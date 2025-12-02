import React, { useState, useEffect, useRef } from 'react'
import { adminAPI } from '../services/api'
import { toast } from 'sonner'
import { 
  Server, 
  Users, 
  HardDrive, 
  Activity, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Clock,
  User,
  Database,
  Wifi,
  WifiOff
} from 'lucide-react'

const AdminPage = () => {
  const [status, setStatus] = useState(null)
  const [users, setUsers] = useState([])
  const [nodes, setNodes] = useState([])
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const eventSourceRef = useRef(null)

  useEffect(() => {
    loadAdminData()
    connectToEvents()
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  const loadAdminData = async () => {
    try {
      setLoading(true)
      
      // Load system status
      const statusResponse = await adminAPI.getStatus()
      if (statusResponse.data.success) {
        setStatus(statusResponse.data.data)
      }

      // Load users
      const usersResponse = await adminAPI.getUsers()
      if (usersResponse.data.success) {
        setUsers(usersResponse.data.data)
      }

      // Load nodes
      const nodesResponse = await adminAPI.getNodes()
      if (nodesResponse.data.success) {
        setNodes(nodesResponse.data.data)
      }
    } catch (error) {
      toast.error('Failed to load admin data')
      console.error('Error loading admin data:', error)
    } finally {
      setLoading(false)
    }
  }

  const connectToEvents = () => {
    try {
      eventSourceRef.current = adminAPI.getEvents()
      
      eventSourceRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setEvents((prev) => [data, ...prev].slice(0, 50)) // Keep last 50 events
      }

      eventSourceRef.current.onerror = (error) => {
        console.error('SSE error:', error)
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (eventSourceRef.current) {
            eventSourceRef.current.close()
            connectToEvents()
          }
        }, 5000)
      }
    } catch (error) {
      console.error('Failed to connect to events:', error)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-500'
      case 'warning': return 'text-yellow-500'
      case 'error': return 'text-red-500'
      default: return 'text-gray-500'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5" />
      case 'warning': return <AlertCircle className="w-5 h-5" />
      case 'error': return <XCircle className="w-5 h-5" />
      default: return <Clock className="w-5 h-5" />
    }
  }

  const formatEventTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  const getEventIcon = (type) => {
    switch (type) {
      case 'user_login': return <User className="w-4 h-4" />
      case 'file_upload': return <Database className="w-4 h-4" />
      case 'node_status': return <Server className="w-4 h-4" />
      case 'system_alert': return <AlertCircle className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="h-8 bg-muted rounded w-1/4 mb-6 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="h-32 bg-muted rounded animate-pulse"></div>
          <div className="h-32 bg-muted rounded animate-pulse"></div>
          <div className="h-32 bg-muted rounded animate-pulse"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold mb-2">Admin Panel</h1>
        <p className="text-muted-foreground">
          Monitor system status, users, and real-time events
        </p>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">System Status</h3>
            <Server className="w-5 h-5 text-muted-foreground" />
          </div>
          <div className="flex items-center space-x-2">
            <div className={getStatusColor(status?.system || 'healthy')}>
              {getStatusIcon(status?.system || 'healthy')}
            </div>
            <span className="font-medium capitalize">{status?.system || 'healthy'}</span>
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Database</h3>
            <Database className="w-5 h-5 text-muted-foreground" />
          </div>
          <div className="flex items-center space-x-2">
            <div className={getStatusColor(status?.database || 'healthy')}>
              {getStatusIcon(status?.database || 'healthy')}
            </div>
            <span className="font-medium capitalize">{status?.database || 'healthy'}</span>
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Storage</h3>
            <HardDrive className="w-5 h-5 text-muted-foreground" />
          </div>
          <div className="flex items-center space-x-2">
            <div className={getStatusColor(status?.storage || 'healthy')}>
              {getStatusIcon(status?.storage || 'healthy')}
            </div>
            <span className="font-medium capitalize">{status?.storage || 'healthy'}</span>
          </div>
        </div>

        <div className="bg-card border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Active Users</h3>
            <Users className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-2xl font-bold">{users.length}</p>
          <p className="text-sm text-muted-foreground">Total registered</p>
        </div>
      </div>

      {/* Nodes and Users */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Storage Nodes */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="font-medium mb-4">Storage Nodes</h3>
          <div className="space-y-3">
            {nodes.map((node) => (
              <div key={node.id} className="flex items-center justify-between p-3 bg-accent rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={node.status === 'online' ? 'text-green-500' : 'text-red-500'}>
                    {node.status === 'online' ? <Wifi className="w-5 h-5" /> : <WifiOff className="w-5 h-5" />}
                  </div>
                  <div>
                    <p className="font-medium">{node.name}</p>
                    <p className="text-sm text-muted-foreground">{node.endpoint}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{node.used_space}/{node.total_space}</p>
                  <p className="text-xs text-muted-foreground capitalize">{node.status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="font-medium mb-4">Recent Users</h3>
          <div className="space-y-3">
            {users.slice(0, 8).map((user) => (
              <div key={user.id} className="flex items-center justify-between p-3 bg-accent rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-medium">
                    {user.name ? user.name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="font-medium">{user.name || user.email}</p>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{user.storage_used || '0 GB'}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(user.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Real-time Events */}
      <div className="bg-card border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Real-time Events</h3>
          <Activity className="w-5 h-5 text-muted-foreground animate-pulse" />
        </div>
        
        <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
          {events.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Waiting for events...</p>
            </div>
          ) : (
            events.map((event, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-accent rounded-lg">
                <div className="flex-shrink-0">
                  {getEventIcon(event.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{event.message}</p>
                  <p className="text-xs text-muted-foreground">
                    {event.user} • {formatEventTime(event.timestamp)}
                  </p>
                </div>
                <div className="text-xs text-muted-foreground">
                  {event.type}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminPage