import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const root = new URL('../', import.meta.url)
const read = (path) => readFileSync(new URL(path, root), 'utf8')

const types = read('dashboard/src/lib/types.ts')
const data = read('dashboard/src/hooks/useData.ts')
const today = read('dashboard/src/views/TodayView.tsx')
const detail = read('dashboard/src/components/BookingDetailPanel.tsx')
const app = read('dashboard/src/App.tsx')

assert.match(types, /export interface AccessPrepTask/)
for (const status of [
  'pending_dispatch',
  'waiting_ack',
  'acknowledged',
  'in_progress',
  'blocked',
  'completed',
  'delivery_failed',
  'no_ack',
  'canceled',
]) {
  assert.match(types, new RegExp(`\\b${status}:`), `missing cleaning label: ${status}`)
}
assert.match(types, /accessPrepTaskStatusLabel/)
assert.match(types, /ownerOverrideWarning/)

assert.match(data, /accessPrepTasks:\s*AccessPrepTask\[\]/)
assert.match(data, /\.from\('access_prep_tasks'\)/)
assert.match(data, /\.not\('status', 'in', '\("done","canceled"\)'\)/)
assert.match(data, /table: 'access_prep_tasks'/)
assert.match(data, /setAccessPrepTasks/)

assert.match(today, /title="งาน Access Prep"/)
assert.match(today, /function AccessPrepRow/)
assert.match(today, /accessPrepTaskStatusLabel/)
assert.match(today, /ownerOverrideWarning/)
assert.match(today, /linkedCleaning/)

assert.match(detail, /accessPrepTasks:\s*AccessPrepTask\[\]/)
assert.match(detail, /งาน Access Prep/)
assert.match(detail, /ownerOverrideWarning/)
assert.match(detail, /linkedCleaning/)

assert.match(app, /accessPrepTasks=\{accessPrepTasks\}/)

console.log('phase6 dashboard read model contract passed')
