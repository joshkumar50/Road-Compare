import React, { useEffect, useState } from 'react'
import axios from 'axios'
import ReactPlayer from 'react-player'

const API = import.meta.env.VITE_API || 'http://localhost:8000/api/v1'

// Configure axios defaults for better CORS handling
// Note: withCredentials removed to prevent CORS issues
// Don't set Content-Type globally - let axios handle it for FormData

// Add axios interceptor for lightweight error logging (avoid noisy console)
axios.interceptors.response.use(
  response => response,
  error => {
    const url = error.config?.url || ''
    const isPolling = url.endsWith('/jobs') && error.config?.method === 'get'
    if (!isPolling) {
      console.warn('API issue:', {
        url,
        method: error.config?.method,
        status: error.response?.status,
        message: error.message
      })
    }
    return Promise.reject(error)
  }
)

// Retry helper for failed requests
const retryRequest = async (fn, retries = 3, delay = 1000) => {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn()
    } catch (error) {
      if (i === retries - 1) throw error
      console.log(`Retry attempt ${i + 1}/${retries} after ${delay}ms...`)
      await new Promise(resolve => setTimeout(resolve, delay))
      delay *= 2 // Exponential backoff
    }
  }
}

function Upload({ onJobCreated }) {
  const [base, setBase] = useState(null)
  const [present, setPresent] = useState(null)
  const [meta, setMeta] = useState('{}')
  const [jobId, setJobId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function submit() {
    if (!base || !present) {
      setError('Please select both base and present videos')
      return
    }
    
    // Validate file sizes (100MB limit)
    const maxSize = 100 * 1024 * 1024 // 100MB
    if (base.size > maxSize) {
      setError(`Base video is too large (${(base.size / 1024 / 1024).toFixed(1)}MB). Maximum size is 100MB.`)
      return
    }
    if (present.size > maxSize) {
      setError(`Present video is too large (${(present.size / 1024 / 1024).toFixed(1)}MB). Maximum size is 100MB.`)
      return
    }
    
    try {
      setLoading(true)
      setError(null)

      // Initialize chunked upload session
      const init = await axios.post(`${API}/uploads/init`)
      const { job_id, base_key, present_key } = init.data

      const uploadFileInChunks = async (file, key) => {
        const CHUNK = 1 * 1024 * 1024 // 1MB (safer for edge)
        let idx = 0
        const total = Math.ceil(file.size / CHUNK)
        for (let offset = 0; offset < file.size; offset += CHUNK) {
          const blob = file.slice(offset, Math.min(offset + CHUNK, file.size))
          const buf = await blob.arrayBuffer()
          // Retry each chunk with exponential backoff
          await retryRequest(() => axios.post(`${API}/uploads/chunk`, new Uint8Array(buf), {
            params: { key, idx, total },
            headers: { 'Content-Type': 'application/octet-stream' },
            timeout: 30000
          }), 3, 800)
          idx++
        }
      }

      // Upload both files in PARALLEL (edge-safe per file; sequential within each file)
      await Promise.all([
        uploadFileInChunks(base, base_key),
        uploadFileInChunks(present, present_key)
      ])

      // Finalize and create job
      const complete = await axios.post(`${API}/uploads/complete`, {
        job_id,
        base_key,
        present_key,
        sample_rate: 1,
        metadata: meta ? JSON.parse(meta) : {}
      })

      setJobId(complete.data.job_id)
      onJobCreated && onJobCreated(complete.data.job_id)
      setBase(null)
      setPresent(null)
      setMeta('{}')
    } catch (err) {
      console.error('Upload error:', err)
      let errorMsg = 'Failed to upload videos'
      
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail
      } else if (err.response?.data?.message) {
        errorMsg = err.response.data.message
      } else if (err.message) {
        errorMsg = `Upload error: ${err.message}`
      }
      
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200">
      <h2 className="text-2xl font-bold mb-4 text-blue-900">📹 Upload Road Videos</h2>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="border-2 border-dashed border-blue-300 rounded-lg p-4 hover:bg-blue-100 transition">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Base Video (Before)</label>
          <input 
            type="file" 
            accept="video/*" 
            onChange={e=>setBase(e.target.files[0])}
            className="w-full"
          />
          {base && <p className="text-xs text-green-600 mt-1">✓ {base.name}</p>}
        </div>
        <div className="border-2 border-dashed border-blue-300 rounded-lg p-4 hover:bg-blue-100 transition">
          <label className="block text-sm font-semibold text-gray-700 mb-2">Present Video (After)</label>
          <input 
            type="file" 
            accept="video/*" 
            onChange={e=>setPresent(e.target.files[0])}
            className="w-full"
          />
          {present && <p className="text-xs text-green-600 mt-1">✓ {present.name}</p>}
        </div>
      </div>
      <div className="mb-4">
        <label className="block text-sm font-semibold text-gray-700 mb-2">Metadata (optional)</label>
        <textarea 
          className="w-full border border-gray-300 rounded-lg p-2 text-sm" 
          rows={2} 
          value={meta} 
          onChange={e=>setMeta(e.target.value)} 
          placeholder='{"start_gps": "10.3170, 77.9449", "end_gps": "10.3064, 77.9370", "date": "2025-02-27"}'
        />
      </div>
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-4">{error}</div>}
      <button 
        className="w-full btn bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition disabled:opacity-50"
        onClick={submit}
        disabled={loading}
      >
        {loading ? '⏳ Processing...' : '🚀 Analyze Videos'}
      </button>
      {jobId && <div className="mt-4 p-3 bg-green-100 border border-green-400 rounded text-green-800">
        ✓ Job queued! ID: <span className="font-mono font-bold">{jobId}</span>
      </div>}
    </div>
  )
}

function Jobs({ refreshTrigger }) {
  const [jobs, setJobs] = useState([])
  const [deleting, setDeleting] = useState(null)

  const fetchJobs = async () => {
    try {
      const res = await retryRequest(() => axios.get(`${API}/jobs`))
      setJobs(res.data)
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
      // Don't show error to user for polling failures
    }
  }

  useEffect(() => {
    fetchJobs()
  }, [refreshTrigger])
  
  // Separate effect for polling to avoid infinite loops
  useEffect(() => {
    // Only poll if there are processing jobs
    const hasProcessing = jobs.some(j => j.status === 'processing' || j.status === 'queued')
    if (!hasProcessing) return
    
    const iv = setInterval(fetchJobs, 10000) // Poll every 10 seconds
    return () => clearInterval(iv)
  }, [jobs.map(j => j.status).join(',')]) // Only re-run when job statuses change

  const deleteJob = async (jobId, e) => {
    e.preventDefault()
    if (!confirm('Delete this job and all associated data?')) return
    try {
      setDeleting(jobId)
      await axios.delete(`${API}/jobs/${jobId}`)
      setJobs(jobs.filter(j => j.id !== jobId))
    } catch (err) {
      alert('Failed to delete job: ' + (err.response?.data?.detail || err.message))
    } finally {
      setDeleting(null)
    }
  }

  const getStatusColor = (status) => {
    switch(status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'processing': return 'bg-blue-100 text-blue-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-yellow-100 text-yellow-800'
    }
  }

  return (
    <div className="card mt-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">📋 Analysis History</h2>
        {jobs.length > 0 && (
          <button 
            onClick={async () => {
              if (confirm('Delete ALL jobs? This cannot be undone.')) {
                try {
                  await axios.delete(`${API}/jobs`)
                  setJobs([])
                } catch (err) {
                  alert('Failed to delete all jobs')
                }
              }
            }}
            className="text-sm px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
          >
            🗑️ Clear All
          </button>
        )}
      </div>
      {jobs.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No analysis jobs yet. Upload videos to get started!</div>
      ) : (
        <div className="grid gap-3">
          {jobs.map(j => (
            <div key={j.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition">
              <a href={`#/jobs/${j.id}`} className="flex-1">
                <div className="flex items-center gap-3">
                  <div className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(j.status)}`}>
                    {j.status.toUpperCase()}
                  </div>
                  <div>
                    <div className="font-mono text-sm text-gray-600">{j.id.slice(0, 8)}...</div>
                    <div className="text-xs text-gray-500">Frames: {j.processed_frames} | Runtime: {j.summary?.time_per_min_sample || '—'}ms/min</div>
                  </div>
                </div>
              </a>
              <button
                onClick={(e) => deleteJob(j.id, e)}
                disabled={deleting === j.id}
                className="ml-4 px-3 py-1 text-red-600 hover:bg-red-50 rounded transition disabled:opacity-50"
              >
                {deleting === j.id ? '⏳' : '🗑️'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function JobViewer({jobId}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedIssue, setSelectedIssue] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const res = await retryRequest(() => axios.get(`${API}/jobs/${jobId}/results`))
        setData(res.data)
      } catch (err) {
        console.error('Failed to fetch results:', err)
        setData({ error: 'Failed to load results. Please try again.' })
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    // Only poll if job is still processing
    if (data?.summary?.status === 'processing' || data?.summary?.status === 'queued') {
      const iv = setInterval(fetchData, 5000)
      return () => clearInterval(iv)
    }
  }, [jobId, data?.summary?.status])

  if (loading) return <div className="card mt-4 text-center py-8">⏳ Loading results...</div>
  if (!data) return <div className="card mt-4 text-center py-8">❌ Failed to load results</div>
  if (data.error) return <div className="card mt-4 text-center py-8 text-red-600">❌ {data.error}</div>

  const { summary, issues } = data
  const issueStats = {
    total: issues.length,
    high: issues.filter(i => i.severity === 'HIGH').length,
    medium: issues.filter(i => i.severity === 'MEDIUM').length,
  }

  return (
    <div className="mt-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="card bg-blue-50 border-l-4 border-blue-500">
          <div className="text-xs text-gray-600">Status</div>
          <div className="text-2xl font-bold text-blue-600 capitalize">{summary.status}</div>
        </div>
        <div className="card bg-purple-50 border-l-4 border-purple-500">
          <div className="text-xs text-gray-600">Frames Processed</div>
          <div className="text-2xl font-bold text-purple-600">{summary.processed_frames}</div>
        </div>
        <div className="card bg-red-50 border-l-4 border-red-500">
          <div className="text-xs text-gray-600">🔴 High Severity</div>
          <div className="text-2xl font-bold text-red-600">{issueStats.high}</div>
        </div>
        <div className="card bg-orange-50 border-l-4 border-orange-500">
          <div className="text-xs text-gray-600">🟠 Medium Severity</div>
          <div className="text-2xl font-bold text-orange-600">{issueStats.medium}</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Issues List */}
        <div className="col-span-2 card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold">🔍 Detected Issues ({issues.length})</h3>
            <a 
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm font-semibold"
              href={`${API}/jobs/${jobId}/report.pdf`} 
              target="_blank"
            >
              📄 Download PDF
            </a>
          </div>
          
          {issues.length === 0 ? (
            <div className="text-center py-8 text-gray-500">✓ No issues detected - Road is safe!</div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {issues.map((i, idx) => (
                <div 
                  key={i.id} 
                  onClick={() => setSelectedIssue(i)}
                  className={`p-4 border rounded-lg cursor-pointer transition ${
                    selectedIssue?.id === i.id 
                      ? 'bg-blue-50 border-blue-500 border-2' 
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded text-xs font-bold text-white ${
                        i.severity === 'HIGH' ? 'bg-red-600' : 'bg-orange-600'
                      }`}>
                        {i.severity}
                      </span>
                      <span className="font-semibold text-gray-800">{i.element}</span>
                    </div>
                    <span className="text-xs text-gray-500">#{idx + 1}</span>
                  </div>
                  <div className="text-sm text-gray-700 mb-2">
                    <strong>Issue:</strong> {i.issue_type} | <strong>Confidence:</strong> {(i.confidence * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-600 mb-2">
                    Frames: {i.first_frame} - {i.last_frame}
                  </div>
                  <div className="flex gap-2">
                    <img src={i.base_crop_url} alt="base" className="h-12 w-12 object-cover rounded border" />
                    <img src={i.present_crop_url} alt="present" className="h-12 w-12 object-cover rounded border" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Issue Details */}
        <div className="card bg-gradient-to-br from-gray-50 to-gray-100">
          <h3 className="text-lg font-bold mb-4">📊 Issue Details</h3>
          {selectedIssue ? (
            <div className="space-y-4">
              <div>
                <div className="text-xs text-gray-600 font-semibold">ELEMENT</div>
                <div className="text-lg font-bold text-gray-800">{selectedIssue.element}</div>
              </div>
              <div>
                <div className="text-xs text-gray-600 font-semibold">ISSUE TYPE</div>
                <div className="text-lg font-bold text-blue-600">{selectedIssue.issue_type}</div>
              </div>
              <div>
                <div className="text-xs text-gray-600 font-semibold">SEVERITY</div>
                <div className={`text-lg font-bold ${selectedIssue.severity === 'HIGH' ? 'text-red-600' : 'text-orange-600'}`}>
                  {selectedIssue.severity}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-600 font-semibold">CONFIDENCE</div>
                <div className="text-lg font-bold text-green-600">{(selectedIssue.confidence * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-xs text-gray-600 font-semibold mb-1">REASON</div>
                <div className="text-sm text-gray-700 bg-white p-2 rounded border">{selectedIssue.reason}</div>
              </div>
              <div>
                <div className="text-xs text-gray-600 font-semibold mb-2">COMPARISON</div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Base</div>
                    <img src={selectedIssue.base_crop_url} alt="base" className="w-full rounded border" />
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Present</div>
                    <img src={selectedIssue.present_crop_url} alt="present" className="w-full rounded border" />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              Select an issue to view details
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Metrics(){
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await retryRequest(() => axios.get(`${API}/jobs`))
        const jobs = res.data
        const completed = jobs.filter(j => j.status === 'completed')
        const failed = jobs.filter(j => j.status === 'failed')
        const processing = jobs.filter(j => j.status === 'processing')
        
        let totalFrames = 0
        let totalIssues = 0
        let avgRuntime = 0
        
        for (const job of completed) {
          totalFrames += job.processed_frames || 0
          avgRuntime += job.runtime_seconds || 0
          try {
            const res2 = await retryRequest(() => axios.get(`${API}/jobs/${job.id}/results`))
            totalIssues += res2.data.issues.length
          } catch (e) {
            console.error(`Failed to fetch results for job ${job.id}:`, e)
          }
        }
        
        setStats({
          total: jobs.length,
          completed: completed.length,
          failed: failed.length,
          processing: processing.length,
          totalFrames,
          totalIssues,
          avgRuntime: completed.length > 0 ? (avgRuntime / completed.length).toFixed(2) : 0,
        })
      } catch (err) {
        console.error('Failed to fetch stats:', err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchStats()
    const iv = setInterval(fetchStats, 3000)
    return () => clearInterval(iv)
  }, [])

  if (loading) return <div className="card text-center py-8">⏳ Loading metrics...</div>

  return (
    <div className="mt-4">
      <h2 className="text-2xl font-bold mb-4">📊 System Metrics</h2>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 border-l-4 border-blue-600">
          <div className="text-sm text-gray-600 font-semibold">Total Jobs</div>
          <div className="text-4xl font-bold text-blue-600">{stats?.total || 0}</div>
          <div className="text-xs text-gray-600 mt-2">
            ✓ {stats?.completed} completed | ⏳ {stats?.processing} processing | ✗ {stats?.failed} failed
          </div>
        </div>
        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-l-4 border-green-600">
          <div className="text-sm text-gray-600 font-semibold">Total Issues Detected</div>
          <div className="text-4xl font-bold text-green-600">{stats?.totalIssues || 0}</div>
          <div className="text-xs text-gray-600 mt-2">
            Across all completed analyses
          </div>
        </div>
        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-l-4 border-purple-600">
          <div className="text-sm text-gray-600 font-semibold">Frames Processed</div>
          <div className="text-4xl font-bold text-purple-600">{stats?.totalFrames || 0}</div>
          <div className="text-xs text-gray-600 mt-2">
            Total video frames analyzed
          </div>
        </div>
        <div className="card bg-gradient-to-br from-orange-50 to-orange-100 border-l-4 border-orange-600">
          <div className="text-sm text-gray-600 font-semibold">Avg Processing Time</div>
          <div className="text-4xl font-bold text-orange-600">{stats?.avgRuntime || 0}s</div>
          <div className="text-xs text-gray-600 mt-2">
            Per job average
          </div>
        </div>
      </div>
      <div className="card bg-blue-50 border-l-4 border-blue-600 p-4">
        <h3 className="font-bold text-blue-900 mb-2">💡 About RoadCompare</h3>
        <p className="text-sm text-blue-800">
          RoadCompare uses AI-powered video analysis to detect road safety issues by comparing base and present video footage. 
          It identifies deterioration in road infrastructure including pavement defects, missing lane markings, and hazards.
        </p>
      </div>
    </div>
  )
}

export default function App(){
  const [route, setRoute] = useState(window.location.hash)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  useEffect(() => {
    const onhash = () => setRoute(window.location.hash)
    window.addEventListener('hashchange', onhash)
    return () => window.removeEventListener('hashchange', onhash)
  }, [])

  let page
  if(route === '#/metrics'){
    page = <Metrics />
  } else if(route.startsWith('#/jobs/')){
    const jobId = route.split('/')[2]
    page = <JobViewer jobId={jobId} />
  } else {
    page = (
      <>
        <Upload onJobCreated={() => setRefreshTrigger(t => t + 1)} />
        <Jobs refreshTrigger={refreshTrigger} />
      </>
    )
  }

  return (
    <div className="min-h-screen p-6 bg-gradient-to-br from-gray-50 to-gray-100">
      <header className="mb-6 flex justify-between items-center bg-white rounded-lg shadow-sm p-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🛣️ RoadCompare</h1>
          <p className="text-sm text-gray-600">Fast, explainable AI audits for road safety</p>
        </div>
        <nav className="space-x-4 text-sm font-semibold">
          <a href="#/" className={`px-4 py-2 rounded transition ${route === '' || route === '#/' ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100'}`}>
            🏠 Home
          </a>
          <a href="#/metrics" className={`px-4 py-2 rounded transition ${route === '#/metrics' ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100'}`}>
            📊 Metrics
          </a>
        </nav>
      </header>
      <div className="max-w-7xl mx-auto">
        {page}
      </div>
    </div>
  )
}


