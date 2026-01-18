import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Download, ArrowLeft } from 'lucide-react'
import GeometryViewer from '../components/GeometryViewer'

interface ResultsViewerProps {
  projectId: string | null
}

interface EnergyResult {
  data: number[][]
  dof_id: number[]
  dof_type: number[]
}

interface ModalResult {
  system_id: number
  system_type: string
  wave_type: number
  modal_density: number[]
  modal_overlap: number[]
  frequency: number[]
}

function ResultsViewer({ projectId }: ResultsViewerProps) {
  const params = useParams()
  const pid = projectId || params.projectId

  const [energy, setEnergy] = useState<EnergyResult | null>(null)
  const [modalData, setModalData] = useState<ModalResult[]>([])
  const [geometry, setGeometry] = useState<{ systems: any[], junctions: any[] }>({ systems: [], junctions: [] })
  const [activeTab, setActiveTab] = useState('energy')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!pid) return
    loadResults()
  }, [pid])

  const loadResults = async () => {
    setLoading(true)
    try {
      // Load energy results
      const energyRes = await fetch(`/api/projects/${pid}/energy`)
      if (energyRes.ok) {
        setEnergy(await energyRes.json())
      }

      // Load modal density
      const modalRes = await fetch(`/api/projects/${pid}/modal-density`)
      if (modalRes.ok) {
        setModalData(await modalRes.json())
      }

      // Load geometry
      const geoRes = await fetch(`/api/projects/${pid}/geometry`)
      if (geoRes.ok) {
        setGeometry(await geoRes.json())
      }
    } catch (error) {
      console.error('Failed to load results:', error)
    }
    setLoading(false)
  }

  const handleExport = async () => {
    try {
      const response = await fetch(`/api/projects/${pid}/export-results`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ energy: 'mJ', power: 'mW' })
      })
      const data = await response.json()
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `sea_results_${pid}.json`
      a.click()
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  if (!pid) {
    return <div className="empty-state">No project selected</div>
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading results...</p>
      </div>
    )
  }

  // Prepare chart data
  const energyChartData = energy?.data ? energy.data[0].map((_, i) => ({
    freq: i + 1,
    energy: energy.data[0][i],
    ...energy.data.slice(1).reduce((acc, row, idx) => {
      acc[`energy_${idx + 1}`] = row[i]
      return acc
    }, {} as Record<string, number>)
  })) : []

  const modalChartData = modalData[0] ? modalData[0].frequency.map((freq, i) => ({
    freq,
    modal_density: modalData[0].modal_density[i],
    modal_overlap: modalData[0].modal_overlap[i]
  })) : []

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Results Viewer</h1>
          <p className="text-secondary">Project: {pid}</p>
        </div>
        <button className="btn btn-primary" onClick={handleExport}>
          <Download size={16} />
          Export JSON
        </button>
      </div>

      <div className="grid grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-header">
            <span>3D Model</span>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            <GeometryViewer geometry={geometry} />
          </div>
        </div>

        <div>
          <div className="tabs">
            <button 
              className={`tab ${activeTab === 'energy' ? 'active' : ''}`}
              onClick={() => setActiveTab('energy')}
            >
              Energy
            </button>
            <button 
              className={`tab ${activeTab === 'modal' ? 'active' : ''}`}
              onClick={() => setActiveTab('modal')}
            >
              Modal Density
            </button>
            <button 
              className={`tab ${activeTab === 'sea' ? 'active' : ''}`}
              onClick={() => setActiveTab('sea')}
            >
              SEA Matrix
            </button>
          </div>

          <div className="card">
            <div className="card-body">
              {activeTab === 'energy' && (
                <>
                  <h4 style={{ marginBottom: 16 }}>Vibrational Energy</h4>
                  {energy && energy.data.length > 0 ? (
                    <div className="chart-container">
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={energyChartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="freq" label={{ value: 'Frequency Band', position: 'insideBottom', offset: -5 }} />
                          <YAxis label={{ value: 'Energy (J)', angle: -90, position: 'insideLeft' }} />
                          <Tooltip />
                          <Legend />
                          {energy.dof_id.map((dofId, idx) => (
                            <Line 
                              key={idx}
                              type="monotone" 
                              dataKey={`energy_${idx}`} 
                              name={`System ${dofId} (DOF ${energy.dof_type[idx]})`}
                              stroke={['#3b82f6', '#22c55e', '#f59e0b'][idx % 3]}
                            />
                          ))}
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <p className="text-secondary">No energy data available</p>
                  )}
                </>
              )}

              {activeTab === 'modal' && (
                <>
                  <h4 style={{ marginBottom: 16 }}>Modal Properties</h4>
                  {modalData.length > 0 ? (
                    <>
                      <div className="chart-container">
                        <ResponsiveContainer width="100%" height={250}>
                          <LineChart data={modalChartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="freq" 
                              label={{ value: 'Frequency (Hz)', position: 'insideBottom', offset: -5 }}
                              tickFormatter={(v) => `${v}`}
                            />
                            <YAxis label={{ value: 'Modes/Hz', angle: -90, position: 'insideLeft' }} />
                            <Tooltip />
                            <Legend />
                            <Line 
                              type="monotone" 
                              dataKey="modal_density" 
                              name="Modal Density"
                              stroke="#3b82f6"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="chart-container" style={{ marginTop: 20 }}>
                        <ResponsiveContainer width="100%" height={250}>
                          <LineChart data={modalChartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="freq" 
                              label={{ value: 'Frequency (Hz)', position: 'insideBottom', offset: -5 }}
                              tickFormatter={(v) => `${v}`}
                            />
                            <YAxis label={{ value: 'Modal Overlap', angle: -90, position: 'insideLeft' }} />
                            <Tooltip />
                            <Legend />
                            <Line 
                              type="monotone" 
                              dataKey="modal_overlap" 
                              name="Modal Overlap"
                              stroke="#22c55e"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </>
                  ) : (
                    <p className="text-secondary">No modal data available</p>
                  )}
                </>
              )}

              {activeTab === 'sea' && (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <p className="text-secondary">SEA Matrix visualization coming soon</p>
                  <p style={{ fontSize: 12, color: '#94a3b8', marginTop: 8 }}>
                    Export JSON to view full matrix data
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="result-summary">
        <div className="result-stat">
          <div className="result-stat-value">
            {energy?.data[0]?.length || 0}
          </div>
          <div className="result-stat-label">Frequency Bands</div>
        </div>
        <div className="result-stat">
          <div className="result-stat-value">
            {energy?.data.length || 0}
          </div>
          <div className="result-stat-label">Energy Channels</div>
        </div>
        <div className="result-stat">
          <div className="result-stat-value">
            {modalData.length}
          </div>
          <div className="result-stat-label">Modal Datasets</div>
        </div>
      </div>
    </div>
  )
}

export default ResultsViewer
