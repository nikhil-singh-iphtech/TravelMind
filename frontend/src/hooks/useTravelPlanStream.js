import { useCallback, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

export function useTravelPlanStream() {
  const [events, setEvents] = useState([])
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('idle') // idle | running | done | error
  const [error, setError] = useState(null)

  const start = useCallback(async (payload) => {
    setEvents([])
    setResult(null)
    setError(null)
    setStatus('running')

    try {
      const response = await fetch(`${API_BASE}/travel-plans/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok || !response.body) {
        throw new Error(`Request failed: ${response.status}`)
      }

      // EventSource can't POST a body, so we parse the SSE text
      // format by hand from the raw response stream.
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const blocks = buffer.split('\n\n')
        buffer = blocks.pop() // last block may be incomplete, keep it for next read

        for (const block of blocks) {
          const lines = block.split('\n')
          const eventLine = lines.find((l) => l.startsWith('event: '))
          const dataLine = lines.find((l) => l.startsWith('data: '))
          if (!eventLine || !dataLine) continue

          const eventType = eventLine.replace('event: ', '')
          const data = JSON.parse(dataLine.replace('data: ', ''))

          if (eventType === 'progress') {
            setEvents((prev) => [...prev, data])
          } else if (eventType === 'complete') {
            setResult(data)
            setStatus(data.status === 'completed' ? 'done' : 'error')
          }
        }
      }
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }, [])

  return { events, result, status, error, start }
}