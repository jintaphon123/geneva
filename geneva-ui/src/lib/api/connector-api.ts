import type { ConnectorsResult, ConnectorStatus } from "@/types"

import { jsonFetch } from "./core"

export async function fetchConnectors(): Promise<ConnectorsResult> {
  return jsonFetch<ConnectorsResult>("/api/connectors")
}

export async function configureConnector(connector: string, secret: string): Promise<{ ok: boolean }> {
  const payload = connector === "google" ? { api_key: secret } : { token: secret }
  return jsonFetch<{ ok: boolean }>(`/api/connectors/${encodeURIComponent(connector)}/configure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export async function deleteConnector(connector: string): Promise<{ ok: boolean }> {
  return jsonFetch<{ ok: boolean }>(`/api/connectors/${encodeURIComponent(connector)}`, {
    method: "DELETE",
  })
}

export async function fetchConnectorStatus(connector: string): Promise<ConnectorStatus> {
  return jsonFetch<ConnectorStatus>(`/api/connectors/${encodeURIComponent(connector)}/status`)
}
