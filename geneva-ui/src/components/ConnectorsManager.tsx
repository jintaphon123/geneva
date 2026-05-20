import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, Plug, RefreshCw, Trash2, XCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import { configureConnector, deleteConnector, fetchConnectors } from "@/lib/api"
import type { ConnectorStatus } from "@/types"

const CONNECTOR_LABELS: Record<string, string> = {
  google: "Google Workspace",
  notion: "Notion",
  github: "GitHub",
}

export function ConnectorsManager() {
  const [connectors, setConnectors] = useState<ConnectorStatus[]>([])
  const [trustedServers, setTrustedServers] = useState<string[]>([])
  const [secrets, setSecrets] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const result = await fetchConnectors()
      setConnectors(result.connectors)
      setTrustedServers(result.trusted_servers ?? [])
      setError(null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Connectors could not be loaded.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleConfigure(connector: string) {
    const secret = (secrets[connector] ?? "").trim()
    if (!secret) return
    setSaving(connector)
    try {
      await configureConnector(connector, secret)
      setSecrets((current) => ({ ...current, [connector]: "" }))
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : `Could not configure ${connector}.`)
    } finally {
      setSaving(null)
    }
  }

  async function handleDisconnect(connector: string) {
    setSaving(connector)
    try {
      await deleteConnector(connector)
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : `Could not disconnect ${connector}.`)
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="connectors-manager">
      <div className="connectors-manager-header">
        <div>
          <strong>Connectors</strong>
          <span>{connectors.filter((connector) => connector.configured).length} connected</span>
        </div>
        <button disabled={loading} onClick={() => void load()} type="button">
          <RefreshCw className={loading ? "size-3.5 animate-spin" : "size-3.5"} />
          Refresh
        </button>
      </div>

      {error ? <div className="connectors-error">{error}</div> : null}

      <div className="connectors-list">
        {connectors.map((connector) => {
          const label = CONNECTOR_LABELS[connector.connector] ?? titleCase(connector.connector)
          const savingThis = saving === connector.connector
          return (
            <section className="connector-row" key={connector.connector}>
              <div className="connector-row-main">
                <span className="connector-icon">
                  <Plug className="size-4" />
                </span>
                <div>
                  <strong>{label}</strong>
                  <small>{connector.capabilities.join(" · ") || "No capabilities reported"}</small>
                  {connector.oauth_required_for?.length ? (
                    <small>OAuth later: {connector.oauth_required_for.join(" · ")}</small>
                  ) : null}
                </div>
              </div>
              <span className={connector.configured ? "connector-status ok" : "connector-status"}>
                {connector.configured ? <CheckCircle2 className="size-3.5" /> : <XCircle className="size-3.5" />}
                {connector.configured ? "Connected" : "Not connected"}
              </span>
              <div className="connector-secret-row">
                <input
                  autoComplete="off"
                  onChange={(event) =>
                    setSecrets((current) => ({ ...current, [connector.connector]: event.target.value }))
                  }
                  placeholder={connector.connector === "google" ? "API key" : "Token"}
                  type="password"
                  value={secrets[connector.connector] ?? ""}
                />
                <Button
                  disabled={savingThis || !(secrets[connector.connector] ?? "").trim()}
                  onClick={() => void handleConfigure(connector.connector)}
                  type="button"
                >
                  {connector.configured ? "Replace" : "Connect"}
                </Button>
                {connector.configured ? (
                  <Button
                    disabled={savingThis}
                    onClick={() => void handleDisconnect(connector.connector)}
                    type="button"
                    variant="subtle"
                  >
                    <Trash2 className="size-4" />
                    Disconnect
                  </Button>
                ) : null}
              </div>
            </section>
          )
        })}
      </div>

      {trustedServers.length ? (
        <div className="trusted-server-list">
          <span>Trusted MCP servers</span>
          {trustedServers.map((server) => (
            <code key={server}>{server}</code>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function titleCase(value: string): string {
  return value
    .split(/[-_ ]+/)
    .filter(Boolean)
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ")
}
