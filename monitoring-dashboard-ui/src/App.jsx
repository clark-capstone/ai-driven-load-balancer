import React, { useEffect, useMemo, useState } from 'react'
import { Activity, Clock3, Cpu, RefreshCcw, Server, ShieldCheck } from 'lucide-react'
import './App.css'
import SimulationView from './components/SimulationView'
import LogFeed from './components/LogFeed'

const CPU_THRESHOLD = 75
const POLL_INTERVAL_MS = 3000

const SERVERS = [
  {
    id: 'server-1',
    name: 'Server-1',
    baseUrl: 'http://localhost:8080',
    region: 'Localhost',
    enabled: true,
  },
  {
    id: 'server-2',
    name: 'Server-2',
    baseUrl: 'https://a5a3-2600-6c64-623f-76f6-e955-1de0-2335-545e.ngrok-free.app',
    region: 'Remote ngrok',
    enabled: true,
  },
  {
    id: 'server-3',
    name: 'Server-3',
    baseUrl: null,
    region: 'Disabled',
    enabled: false,
  },
]

const formatPercent = value => (typeof value === 'number' ? `${value.toFixed(1)}%` : 'n/a')

const formatClock = value => {
  if (!value) return 'waiting'
  return new Date(value).toLocaleTimeString()
}

const normalizeServerState = async server => {
  if (!server.enabled || !server.baseUrl) {
    return {
      ...server,
      active: false,
      cpuUsage: null,
      memoryUsage: null,
      requestCount: 0,
      hostname: server.name,
      metrics: null,
      error: 'Disabled',
    }
  }

  try {
    const response = await fetch(`${server.baseUrl}/metrics`)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const metrics = await response.json()

    return {
      ...server,
      active: true,
      cpuUsage: typeof metrics.cpuUsage === 'number' ? metrics.cpuUsage : null,
      memoryUsage: typeof metrics.memoryUsage === 'number' ? metrics.memoryUsage : null,
      requestCount: typeof metrics.requestCount === 'number' ? metrics.requestCount : 0,
      hostname: metrics.hostname ?? server.name,
      metrics,
      error: null,
    }
  } catch (error) {
    return {
      ...server,
      active: false,
      cpuUsage: null,
      memoryUsage: null,
      requestCount: 0,
      hostname: server.name,
      metrics: null,
      error: error.message,
    }
  }
}

const pickBestServer = servers => {
  const activeServers = servers.filter(server => server.active)

  if (activeServers.length === 0) {
    return {
      selectedServer: null,
      decision: 'No active server available',
    }
  }

  const underThreshold = activeServers.filter(server => typeof server.cpuUsage === 'number' && server.cpuUsage < CPU_THRESHOLD)
  const pool = underThreshold.length > 0 ? underThreshold : activeServers

  const ranked = [...pool].sort((left, right) => {
    const leftCpu = typeof left.cpuUsage === 'number' ? left.cpuUsage : Number.POSITIVE_INFINITY
    const rightCpu = typeof right.cpuUsage === 'number' ? right.cpuUsage : Number.POSITIVE_INFINITY
    if (leftCpu !== rightCpu) {
      return leftCpu - rightCpu
    }
    return left.id.localeCompare(right.id)
  })

  const selectedServer = ranked[0]

  return {
    selectedServer,
    decision: underThreshold.length > 0
      ? `${selectedServer.name} chosen under ${CPU_THRESHOLD}% CPU threshold`
      : `${selectedServer.name} chosen as lowest active CPU fallback`,
  }
}

const StatsCard = ({ title, value, icon: Icon, tone }) => (
  <div className="rounded-3xl border border-white/10 bg-slate-950/70 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.35)] backdrop-blur">
    <div className="mb-4 flex items-start justify-between">
      <div className={`rounded-2xl p-3 ${tone}`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
    </div>
    <div className="text-sm font-medium text-slate-400">{title}</div>
    <div className="mt-1 text-3xl font-black tracking-tight text-white">{value}</div>
  </div>
)

function App() {
  const [servers, setServers] = useState(() => SERVERS.map(server => ({
    ...server,
    active: false,
    cpuUsage: null,
    memoryUsage: null,
    requestCount: 0,
    hostname: server.name,
    metrics: null,
    error: null,
  })))
  const [chosenServerId, setChosenServerId] = useState(null)
  const [decision, setDecision] = useState('Waiting for first poll')
  const [history, setHistory] = useState([])
  const [simulatedRequests, setSimulatedRequests] = useState([])
  const [lastUpdatedAt, setLastUpdatedAt] = useState(null)
  const [status, setStatus] = useState('CONNECTING')

  useEffect(() => {
    let cancelled = false

    const loadLiveState = async () => {
      const nextServers = await Promise.all(SERVERS.map(normalizeServerState))
      const { selectedServer, decision: nextDecision } = pickBestServer(nextServers)

      if (cancelled) {
        return
      }

      setServers(nextServers)
      setChosenServerId(selectedServer?.id ?? null)
      setDecision(nextDecision)
      setLastUpdatedAt(Date.now())
      setStatus(selectedServer ? 'LIVE' : 'DEGRADED')
      setSimulatedRequests(current => {
        const nextRequest = {
          id: `${Date.now()}-${selectedServer?.id ?? 'none'}`,
          targetServerId: selectedServer?.id ?? null,
          status: selectedServer ? 'ROUTED' : 'NO_SERVER',
        }

        return [...current, nextRequest].slice(-10)
      })

      setHistory(current => {
        const entry = {
          id: `${Date.now()}-${selectedServer?.id ?? 'none'}`,
          timestamp: new Date().toISOString(),
          chosenServer: selectedServer?.name ?? 'none',
          status: selectedServer ? 'ROUTED' : 'NO_SERVER',
          decision: nextDecision,
          servers: nextServers.map(server => ({
              name: server.name,
              enabled: server.enabled,
              active: server.active,
              cpuUsage: server.cpuUsage,
              memoryUsage: server.memoryUsage,
              error: server.error,
            })),
        }

        return [entry, ...current].slice(0, 20)
      })
    }

    loadLiveState()
    const intervalId = window.setInterval(loadLiveState, POLL_INTERVAL_MS)
    const cleanupId = window.setInterval(() => {
      setSimulatedRequests(current => current.slice(-6))
    }, 1800)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
      window.clearInterval(cleanupId)
    }
  }, [])

  const chosenServer = useMemo(
    () => servers.find(server => server.id === chosenServerId) ?? null,
    [servers, chosenServerId],
  )

  const metrics = useMemo(() => {
    const activeServers = servers.filter(server => server.active)
    const averageCpu = activeServers.length > 0
      ? activeServers.reduce((sum, server) => sum + (server.cpuUsage ?? 0), 0) / activeServers.length
      : null

    return {
      chosenServer: chosenServer?.name ?? 'None',
      activeServers: activeServers.length,
      averageCpu: averageCpu != null ? `${averageCpu.toFixed(1)}%` : 'n/a',
      lastUpdated: formatClock(lastUpdatedAt),
    }
  }, [chosenServer, lastUpdatedAt, servers])

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.2),_transparent_24%),radial-gradient(circle_at_top_right,_rgba(34,197,94,0.14),_transparent_22%),linear-gradient(180deg,_#020617_0%,_#0f172a_42%,_#111827_100%)] px-4 py-6 text-slate-100 sm:px-6">
      <header className="mx-auto flex max-w-7xl flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-3">
            <div className={`h-3 w-3 rounded-full ${status === 'LIVE' ? 'bg-emerald-400 shadow-[0_0_18px_#34d399]' : 'bg-amber-400 shadow-[0_0_18px_#f59e0b]'}`} />
            <h1 className="text-3xl font-black tracking-[-0.08em] text-white sm:text-4xl">n8n Load Balancer Monitor</h1>
          </div>
          <p className="flex items-center gap-2 text-sm font-medium uppercase tracking-[0.28em] text-slate-400">
            <ShieldCheck className="h-4 w-4" />
            Live server metrics, current routing decision, and polling history
          </p>
        </div>

        <div className="rounded-3xl border border-white/10 bg-slate-950/50 px-5 py-3 text-sm font-semibold text-slate-300 shadow-[0_20px_60px_rgba(15,23,42,0.25)] backdrop-blur">
          {status}
        </div>
      </header>

      <main className="mx-auto mt-8 grid max-w-7xl grid-cols-1 gap-6 xl:grid-cols-4">
        <div className="grid grid-cols-1 gap-6 xl:col-span-3">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 2xl:grid-cols-4">
            <StatsCard title="Chosen Server" value={metrics.chosenServer} icon={Server} tone="bg-cyan-500/80" />
            <StatsCard title="Active Servers" value={String(metrics.activeServers)} icon={Activity} tone="bg-emerald-500/80" />
            <StatsCard title="Average CPU" value={metrics.averageCpu} icon={Cpu} tone="bg-amber-500/80" />
            <StatsCard title="Last Poll" value={metrics.lastUpdated} icon={Clock3} tone="bg-indigo-500/80" />
          </div>

          <section className="rounded-[28px] border border-white/10 bg-slate-950/55 p-5 shadow-[0_24px_80px_rgba(15,23,42,0.35)] backdrop-blur">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="flex items-center gap-2 text-lg font-bold text-white">
                  <RefreshCcw className="h-5 w-5 text-cyan-300" />
                  Live Routing View
                </h2>
                <p className="mt-1 text-sm text-slate-400">{decision}</p>
              </div>
              <div className="rounded-full border border-cyan-300/30 bg-cyan-400/10 px-4 py-2 text-xs font-black uppercase tracking-[0.26em] text-cyan-200">
                Polling every 3 seconds
              </div>
            </div>

            <SimulationView
              servers={servers}
              chosenServerId={chosenServerId}
              cpuThreshold={CPU_THRESHOLD}
              requests={simulatedRequests}
            />
          </section>
        </div>

        <div className="xl:col-span-1">
          <LogFeed history={history} />
        </div>
      </main>
    </div>
  )
}

export default App
