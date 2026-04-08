import React, { useEffect, useMemo, useState } from 'react'
import { Activity, Clock3, RefreshCcw, Server, ShieldCheck } from 'lucide-react'
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
    metricsUrl: '/metrics',
    routeToken: 'LOCAL',
    region: 'Localhost',
    enabled: true,
  },
  {
    id: 'server-2',
    name: 'Server-2',
    baseUrl: 'https://a5a3-2600-6c64-623f-76f6-e955-1de0-2335-545e.ngrok-free.app',
    metricsUrl: '/server-2-metrics',
    routeToken: 'a5a3-2600-6c64-623f-76f6-e955-1de0-2335-545e.ngrok-free.app',
    region: 'Remote ngrok',
    enabled: true,
  },
  {
    id: 'server-3',
    name: 'Server-3',
    baseUrl: null,
    routeToken: null,
    region: 'Disabled',
    enabled: false,
  },
]

const formatClock = value => {
  if (!value) return 'waiting'
  return new Date(value).toLocaleTimeString()
}

const buildDemoPayload = tick => {
  const attackPulse = tick % 6 === 5

  return attackPulse
    ? { payload_size: 120, request_rate: 25, path: '/api/burst-demo' }
    : { payload_size: 120, request_rate: 4, path: '/api/steady-demo' }
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
    const response = await fetch(server.metricsUrl ?? `${server.baseUrl}/metrics`)
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

const predictBestServer = servers => {
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
  <div className="glass-card p-5 transition-all duration-300 hover:scale-[1.02]">
    <div className="mb-4 flex items-center justify-between">
      <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900/50 ${tone}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="h-1.5 w-1.5 rounded-full bg-slate-700" />
    </div>
    <div className="text-[11px] font-bold uppercase tracking-[0.15em] text-slate-400">{title}</div>
    <div className="mt-1 flex items-baseline gap-2">
      <div className="truncate text-2xl font-black tracking-tight text-white">{value}</div>
    </div>
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
  const [decision, setDecision] = useState('Initializing...')
  const [aiVerdict, setAiVerdict] = useState('WAITING')
  const [history, setHistory] = useState([])
  const [simulatedRequests, setSimulatedRequests] = useState([])
  const [lastUpdatedAt, setLastUpdatedAt] = useState(null)
  const [status, setStatus] = useState('CONNECTING')

  useEffect(() => {
    let cancelled = false
    let tick = 0

    const loadLiveState = async () => {
      const payload = buildDemoPayload(tick)
      tick += 1

      const nextServers = await Promise.all(SERVERS.map(normalizeServerState))
      const { selectedServer: predictedServer, decision: predictedDecision } = predictBestServer(nextServers)

      let chosenServer = predictedServer
      let nextDecision = predictedDecision
      let nextAiVerdict = 'ALLOW'

      try {
        const routeResponse = await fetch('/route', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        })

        const routeText = await routeResponse.text()

        if (routeText.includes('BLOCKED_BY_AI_SENTINEL')) {
          chosenServer = null
          nextAiVerdict = 'BLOCKED'
          nextDecision = 'AI Sentinel blocked the current request before routing'
        } else {
          const routeMatchedServer = nextServers.find(server => server.routeToken && routeText.includes(server.routeToken))
          if (routeMatchedServer) {
            chosenServer = routeMatchedServer
          }
        }
      } catch (error) {
        nextAiVerdict = 'UNAVAILABLE'
        nextDecision = 'AI route check unavailable, showing metric-based fallback'
      }

      if (cancelled) return

      setServers(nextServers)
      setChosenServerId(chosenServer?.id ?? null)
      setDecision(nextDecision)
      setAiVerdict(nextAiVerdict)
      setLastUpdatedAt(Date.now())
      setStatus(chosenServer || nextAiVerdict === 'BLOCKED' ? 'LIVE' : 'DEGRADED')

      setSimulatedRequests(current => {
        const nextRequest = {
          id: `${Date.now()}-${chosenServer?.id ?? nextAiVerdict}`,
          targetServerId: nextAiVerdict === 'BLOCKED' ? null : chosenServer?.id ?? null,
          status: nextAiVerdict === 'BLOCKED' ? 'AI_BLOCKED' : chosenServer ? 'ROUTED' : 'NO_SERVER',
        }
        return [...current, nextRequest].slice(-8)
      })

      setHistory(current => {
        const entry = {
          id: `${Date.now()}-${chosenServer?.id ?? nextAiVerdict}`,
          timestamp: new Date().toISOString(),
          chosenServer: chosenServer?.name ?? 'None',
          status: nextAiVerdict === 'BLOCKED' ? 'AI_BLOCKED' : chosenServer ? 'ROUTED' : 'NO_SERVER',
          aiVerdict: nextAiVerdict,
          requestRate: payload.request_rate,
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
        return [entry, ...current].slice(0, 15)
      })
    }

    loadLiveState()
    const intervalId = window.setInterval(loadLiveState, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [])

  const chosenServer = useMemo(
    () => servers.find(server => server.id === chosenServerId) ?? null,
    [servers, chosenServerId],
  )

  const metrics = useMemo(() => {
    const activeServers = servers.filter(server => server.active)

    return {
      chosenServer: chosenServer?.name ?? 'None',
      aiVerdict,
      activeServers: activeServers.length,
      lastUpdated: formatClock(lastUpdatedAt),
    }
  }, [aiVerdict, chosenServer, lastUpdatedAt, servers])

  return (
    <div className="h-screen overflow-hidden bg-[#020617] bg-[radial-gradient(ellipse_at_top,_rgba(30,58,138,0.15),_transparent_60%)] px-6 py-6 text-slate-100">
      <main className="mx-auto grid h-full max-w-[1600px] grid-cols-1 gap-6 xl:grid-cols-[1.6fr_1fr]">
        <div className="flex min-h-0 flex-col gap-6">
          <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
            <StatsCard title="Current Target" value={metrics.chosenServer} icon={Server} tone="text-cyan-400" />
            <StatsCard title="AI Verdict" value={metrics.aiVerdict} icon={ShieldCheck} tone={metrics.aiVerdict === 'BLOCKED' ? 'text-rose-400' : 'text-emerald-400'} />
            <StatsCard title="Nodes Online" value={String(metrics.activeServers)} icon={Activity} tone="text-emerald-400" />
            <StatsCard title="Last Pulse" value={metrics.lastUpdated} icon={Clock3} tone="text-indigo-400" />
          </div>

          <section className="glass-card flex min-h-0 flex-1 flex-col overflow-hidden p-6">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="flex items-center gap-2.5 text-sm font-bold tracking-tight text-white">
                  <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
                    <RefreshCcw className="h-3.5 w-3.5" />
                  </div>
                  Simulation Environment
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  {decision}
                </p>
              </div>
              <div className="rounded-full bg-slate-900/50 px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Poll Cycle: 3s
              </div>
            </div>

            <div className="flex min-h-0 flex-1 items-center justify-center">
              <div className="w-full">
                <SimulationView
                  servers={servers}
                  chosenServerId={chosenServerId}
                  cpuThreshold={CPU_THRESHOLD}
                  requests={simulatedRequests}
                />
              </div>
            </div>
          </section>
        </div>

        <div className="min-h-0 pb-2">
          <LogFeed history={history} />
        </div>
      </main>
    </div>
  )
}

export default App
