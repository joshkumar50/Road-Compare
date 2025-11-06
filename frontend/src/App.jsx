import React, { useEffect, useState } from 'react'
import axios from 'axios'
import ReactPlayer from 'react-player'

const API = import.meta.env.VITE_API || 'http://localhost:8000/api/v1'

function Upload() {
  const [base, setBase] = useState(null)
  const [present, setPresent] = useState(null)
  const [meta, setMeta] = useState('{}')
  const [jobId, setJobId] = useState(null)

  async function submit() {
    const form = new FormData()
    if (base) form.append('base_video', base)
    if (present) form.append('present_video', present)
    form.append('metadata', meta)
    form.append('sample_rate', '1')
    const res = await axios.post(`${API}/jobs`, form)
    setJobId(res.data.job_id)
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-2">Upload videos</h2>
      <div className="grid grid-cols-2 gap-4">
        <input type="file" accept="video/*" onChange={e=>setBase(e.target.files[0])} />
        <input type="file" accept="video/*" onChange={e=>setPresent(e.target.files[0])} />
      </div>
      <textarea className="w-full border mt-2 p-2" rows={3} value={meta} onChange={e=>setMeta(e.target.value)} placeholder='{"start_gps": ..., "end_gps": ...}' />
      <button className="btn mt-2" onClick={submit}>Drop base & present videos here — or use sample data</button>
      {jobId && <div className="mt-2">Queued Job ID: <span className="font-mono">{jobId}</span></div>}
    </div>
  )
}

function Jobs() {
  const [jobs, setJobs] = useState([])
  useEffect(()=>{ const iv = setInterval(async () => {
    const res = await axios.get(`${API}/jobs`)
    setJobs(res.data)
  }, 1500); return ()=>clearInterval(iv)},[])
  return (
    <div className="card mt-4">
      <h2 className="text-xl font-semibold mb-2">Jobs</h2>
      <div className="grid gap-2">
        {jobs.map(j => (
          <a key={j.id} href={`#/jobs/${j.id}`} className="block p-3 border rounded hover:bg-gray-50">
            <div className="flex justify-between">
              <div>
                <div className="font-mono">{j.id}</div>
                <div className="text-sm">Status: {j.status} · Frames: {j.processed_frames}</div>
              </div>
              <div className="text-accent font-semibold">View</div>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}

function JobViewer({jobId}) {
  const [data, setData] = useState(null)
  useEffect(()=>{ (async ()=>{
    const res = await axios.get(`${API}/jobs/${jobId}/results`)
    setData(res.data)
  })() },[jobId])
  if(!data) return <div className="card">Loading...</div>
  const {issues} = data
  return (
    <div className="grid grid-cols-3 gap-4 mt-4">
      <div className="col-span-2 card">
        <h3 className="font-semibold">Side-by-side (demo placeholder)</h3>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-black h-48 flex items-center justify-center text-white">Base</div>
          <div className="bg-black h-48 flex items-center justify-center text-white">Present</div>
        </div>
      </div>
      <div className="card">
        <div className="flex justify-between items-center">
          <h3 className="font-semibold">Issues</h3>
          <a className="btn" href={`${API}/jobs/${jobId}/report.pdf`} target="_blank">PDF</a>
        </div>
        <div className="mt-2 space-y-2">
          {issues.map(i => (
            <div key={i.id} className="p-2 border rounded">
              <div className="text-sm">{i.element} — <span className="text-warning">{i.issue_type}</span> · conf {i.confidence.toFixed(2)}</div>
              <div className="flex gap-2 mt-1">
                <img src={i.base_crop_url} className="h-16"/>
                <img src={i.present_crop_url} className="h-16"/>
              </div>
              <div className="text-xs mt-1">{i.reason}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function App(){
  const [route, setRoute] = useState(window.location.hash)
  useEffect(()=>{ const onhash = ()=>setRoute(window.location.hash); window.addEventListener('hashchange', onhash); return ()=>window.removeEventListener('hashchange', onhash)},[])
  let page
  if(route === '#/metrics'){
    page = <Metrics />
  } else
  if(route.startsWith('#/jobs/')){
    const jobId = route.split('/')[2]
    page = <JobViewer jobId={jobId} />
  } else {
    page = (<>
      <Upload />
      <Jobs />
    </>)
  }
  return (
    <div className="min-h-screen p-6 bg-background text-primary">
      <header className="mb-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">RoadCompare — Fast, explainable AI audits for road safety.</h1>
        <nav className="space-x-3 text-sm">
          <a href="#/" className="underline">Home</a>
          <a href="#/metrics" className="underline">Metrics</a>
        </nav>
      </header>
      {page}
    </div>
  )
}

function Metrics(){
  const [summary, setSummary] = useState(null)
  const [metrics, setMetrics] = useState(null)
  useEffect(()=>{ (async ()=>{
    try {
      const res = await axios.get(`${API}/jobs`)
      const done = res.data.find(j=>j.status==='completed')
      if(done){
        const r2 = await axios.get(`${API}/jobs/${done.id}/results`)
        setSummary(r2.data.summary)
      }
    } catch(e) {}
    try {
      const m = await fetch('/artifacts_metrics.json').then(r=>r.ok?r.json():null)
      setMetrics(m)
    } catch(e) {}
  })() },[])
  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-2">Metrics dashboard</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="p-3 border rounded"><div className="text-sm text-gray-500">Processed frames</div><div className="text-2xl">{summary?.processed_frames ?? '—'}</div></div>
        <div className="p-3 border rounded"><div className="text-sm text-gray-500">Precision (change)</div><div className="text-2xl">{metrics?.precision ?? '—'}</div></div>
        <div className="p-3 border rounded"><div className="text-sm text-gray-500">Recall (change)</div><div className="text-2xl">{metrics?.recall ?? '—'}</div></div>
      </div>
    </div>
  )
}


