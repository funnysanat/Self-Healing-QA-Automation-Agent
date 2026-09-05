import { useState } from 'react'

function App() {
  const [version, setVersion] = useState('v1')
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [healingData, setHealingData] = useState<any>(null)
  const [metrics, setMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [generatedTests, setGeneratedTests] = useState<string[]>([])
  const [changeDesc, setChangeDesc] = useState("Developer changed checkout button ID from #checkout to #proceed-payment")

  const runTest = async () => {
    setLoading(true)
    setStatus('Running...')
    setError(null)
    setHealingData(null)
    setMetrics(null)
    
    try {
      const res = await fetch('http://127.0.0.1:8000/run-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version })
      })
      const data = await res.json()
      
      setMetrics(data.metrics)

      if (data.status === 'PASS') {
        setStatus('PASS')
      } else {
        setStatus('FAIL')
        setError(data.error)
        await healTest(data.error)
      }
    } catch (err: any) {
      setStatus('ERROR')
      setError(err.toString())
    }
    setLoading(false)
  }

  const healTest = async (errorMessage: string) => {
    setStatus('AI Healing...')
    try {
      const res = await fetch('http://127.0.0.1:8000/heal-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version, error_message: errorMessage })
      })
      const data = await res.json()
      setHealingData(data)
      setStatus(data.status)
      
      // Auto re-run test if healed
      if (data.status === 'HEALED') {
        setTimeout(() => runTest(), 2000)
      }
    } catch (err: any) {
      setError(err.toString())
    }
  }

  const generateTests = async () => {
    setGenerating(true)
    setGeneratedTests([])
    try {
      const res = await fetch('http://127.0.0.1:8000/generate-tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: changeDesc })
      })
      const data = await res.json()
      setGeneratedTests(data.tests)
    } catch (err: any) {
      console.error(err)
    }
    setGenerating(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-12">
      <div className="w-full max-w-6xl bg-white shadow-xl rounded-2xl overflow-hidden">
        
        <div className="bg-blue-600 text-white p-6">
          <h1 className="text-3xl font-bold">Autonomous QA Agent Platform</h1>
          <p className="opacity-80 mt-2">Full MVP Demo: Detection, Generation, Multi-Dimensional Testing & Intelligence</p>
        </div>
        
        <div className="p-8 grid grid-cols-3 gap-8">
          
          <div className="col-span-1 border-r pr-8">
            <h2 className="text-xl font-bold text-gray-800 mb-4">1. AI Test Generation</h2>
            <p className="text-sm text-gray-600 mb-2">Simulate a Git PR Change:</p>
            <textarea 
              value={changeDesc}
              onChange={(e) => setChangeDesc(e.target.value)}
              className="w-full p-2 border rounded text-sm mb-4 h-24"
            />
            <button 
              onClick={generateTests}
              disabled={generating}
              className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg shadow mb-6"
            >
              {generating ? 'Generating...' : 'Generate Test Cases'}
            </button>

            {generatedTests.length > 0 && (
              <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
                <h3 className="font-bold text-indigo-800 mb-2 text-sm">Generated Scenarios</h3>
                <ul className="text-sm text-indigo-900 space-y-2 list-disc pl-4">
                  {generatedTests.map((t, i) => <li key={i}>{t}</li>)}
                </ul>
              </div>
            )}
          </div>

          <div className="col-span-2 space-y-8">
            <div>
              <h2 className="text-xl font-bold text-gray-800 mb-4">2. Multi-Dimensional Execution & Healing</h2>
              
              <div className="flex gap-4 mb-4">
                <button 
                  onClick={() => setVersion('v1')}
                  className={`px-4 py-2 rounded font-semibold ${version === 'v1' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                >
                  Target: App v1 (Original)
                </button>
                <button 
                  onClick={() => setVersion('v2')}
                  className={`px-4 py-2 rounded font-semibold ${version === 'v2' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                >
                  Target: App v2 (Broken ID)
                </button>
                <button 
                  onClick={runTest}
                  disabled={loading}
                  className="px-6 py-2 bg-green-500 hover:bg-green-600 text-white font-bold rounded shadow ml-auto disabled:opacity-50"
                >
                  {loading ? 'Executing...' : 'Run Pipeline'}
                </button>
              </div>

              {metrics && (
                <div className="flex gap-4 mb-6">
                  <div className={`px-3 py-1 rounded text-sm font-bold ${metrics.ui === 'PASS' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>UI: {metrics.ui}</div>
                  <div className={`px-3 py-1 rounded text-sm font-bold ${metrics.api === 'PASS' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>API: {metrics.api}</div>
                  <div className={`px-3 py-1 rounded text-sm font-bold ${metrics.logs === 'PASS' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>Logs: {metrics.logs}</div>
                  <div className={`px-3 py-1 rounded text-sm font-bold ${metrics.security === 'PASS' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>Security: {metrics.security}</div>
                  <div className={`px-3 py-1 rounded text-sm font-bold ${metrics.accessibility === 'WARN' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>A11y: {metrics.accessibility}</div>
                  <div className={`px-3 py-1 rounded text-sm font-bold ${metrics.performance.includes('PASS') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>Perf: {metrics.performance}</div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="bg-gray-50 p-6 rounded-xl border border-gray-200">
                <h3 className="text-lg font-bold text-gray-800 mb-4">Execution Status</h3>
                {status && (
                  <div className={`p-4 rounded-lg font-bold text-lg mb-4 text-center ${
                    status === 'PASS' ? 'bg-green-100 text-green-800 border-green-300' :
                    status === 'FAIL' ? 'bg-red-100 text-red-800 border-red-300' :
                    status === 'AI Healing...' ? 'bg-yellow-100 text-yellow-800 border-yellow-300 animate-pulse' :
                    status === 'HEALED' ? 'bg-blue-100 text-blue-800 border-blue-300' :
                    status === 'DIAGNOSED' ? 'bg-purple-100 text-purple-800 border-purple-300' :
                    'bg-gray-200 text-gray-800'
                  } border`}>
                    Status: {status}
                  </div>
                )}
                {error && (
                  <div className="bg-red-50 text-red-700 p-4 rounded text-xs font-mono overflow-auto max-h-32 border border-red-200">
                    {error}
                  </div>
                )}
              </div>

              <div className="bg-gray-50 p-6 rounded-xl border border-gray-200 flex flex-col justify-between">
                <div>
                  <h3 className="text-lg font-bold text-gray-800 mb-4">3. Quality Intelligence</h3>
                  {!healingData && !metrics && (
                    <p className="text-gray-500 italic text-sm">Awaiting execution...</p>
                  )}
                  {healingData && (
                    <div className="mb-4">
                      <h4 className="font-bold text-indigo-800 text-xs uppercase">Healer Diagnosis</h4>
                      <p className="text-indigo-900 mt-1 text-sm">{healingData.diagnosis}</p>
                    </div>
                  )}
                  {metrics && !healingData && status === 'PASS' && (
                    <div className="mb-4">
                      <h4 className="font-bold text-green-800 text-xs uppercase">Diagnosis</h4>
                      <p className="text-green-900 mt-1 text-sm">All business-critical UI flows passed. API contract intact.</p>
                    </div>
                  )}
                </div>
                
                {(healingData || metrics) && (
                  <div className={`p-4 rounded-lg flex items-center justify-between border ${
                    status === 'FAIL' ? 'bg-red-50 border-red-200 text-red-900' : 'bg-green-50 border-green-200 text-green-900'
                  }`}>
                    <h4 className="font-bold">Release Decision</h4>
                    <span className="text-xl font-bold">
                      {status === 'FAIL' ? '🔴 BLOCK' : '🟢 PASS'}
                    </span>
                  </div>
                )}
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
