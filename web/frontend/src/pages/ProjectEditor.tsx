import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Play, Plus, Box, Layers, Link, Zap, ChevronRight } from 'lucide-react'
import GeometryViewer from '../components/GeometryViewer'
import api from '../utils/api'

interface ProjectEditorProps {
  projectId: string | null
  onNavigate: (id: string | null) => void
}

interface System {
  id: number
  name: string
  element_type?: string
  dimensions?: Record<string, number>
}

interface Junction {
  name: string
  junction_type: string
  systems: number[]
  area?: number
  length?: number
}

function ProjectEditor({ projectId, onNavigate }: ProjectEditorProps) {
  const params = useParams()
  const navigate = useNavigate()
  const pid = projectId || params.projectId
  
  const [activeTab, setActiveTab] = useState('systems')
  const [systems, setSystems] = useState<System[]>([])
  const [junctions, setJunctions] = useState<Junction[]>([])
  const [geometry, setGeometry] = useState<{ systems: any[], junctions: any[] }>({ systems: [], junctions: [] })
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  
  // Form states
  const [showAddSystem, setShowAddSystem] = useState(false)
  const [showAddJunction, setShowAddJunction] = useState(false)
  const [systemType, setSystemType] = useState('plate')
  const [sysName, setSysName] = useState('')
  const [sysLx, setSysLx] = useState(1)
  const [sysLy, setSysLy] = useState(1)
  const [sysThickness, setSysThickness] = useState(0.01)
  const [sysMaterial, setSysMaterial] = useState('concrete')

  useEffect(() => {
    if (pid) {
      loadProjectData()
    }
  }, [pid])

  const loadProjectData = async () => {
    if (!pid) return
    // Load geometry for 3D viewer
    try {
      const geoResponse = await fetch(`/api/projects/${pid}/geometry`)
      const geoData = await geoResponse.json()
      setGeometry(geoData)
    } catch (error) {
      console.error('Failed to load geometry:', error)
    }
  }

  const handleAnalyze = async () => {
    if (!pid) return
    setAnalyzing(true)
    try {
      const response = await fetch(`/api/projects/${pid}/analyze`, {
        method: 'POST'
      })
      const result = await response.json()
      setAnalysisResult(result)
      if (result.success) {
        navigate(`/results/${pid}`)
      }
    } catch (error) {
      console.error('Analysis failed:', error)
    }
    setAnalyzing(false)
  }

  const handleAddSystem = async () => {
    if (!pid || !sysName.trim()) return
    
    try {
      await fetch(`/api/projects/${pid}/structures`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: sysName,
          element_type: systemType,
          dimensions: {
            Lx: sysLx,
            Ly: sysLy,
            thickness: sysThickness
          },
          material_name: sysMaterial,
          damping_loss_factor: 0.01
        })
      })
      setShowAddSystem(false)
      setSysName('')
      loadProjectData()
    } catch (error) {
      console.error('Failed to add system:', error)
    }
  }

  if (!pid) {
    return <div className="empty-state">No project selected</div>
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Project Editor</h1>
          <p className="text-secondary">ID: {pid}</p>
        </div>
        <button 
          className="btn btn-success analyze-btn"
          onClick={handleAnalyze}
          disabled={analyzing}
        >
          {analyzing ? (
            <>
              <span className="spinner" style={{ width: 16, height: 16 }}></span>
              Analyzing...
            </>
          ) : (
            <>
              <Play size={16} />
              Run Analysis
            </>
          )}
        </button>
      </div>

      <div className="editor-layout">
        <div className="editor-main">
          {/* 3D Geometry Viewer */}
          <div className="card">
            <div className="card-header">
              <Box size={18} />
              <span>3D Geometry</span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              <GeometryViewer geometry={geometry} />
            </div>
          </div>

          {/* Systems Panel */}
          <div className="card">
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Layers size={18} />
                <span>Systems</span>
              </div>
              <button className="btn btn-sm btn-secondary" onClick={() => setShowAddSystem(true)}>
                <Plus size={14} />
                Add
              </button>
            </div>
            <div className="card-body">
              {geometry.systems.length === 0 ? (
                <p className="text-secondary">No systems added yet</p>
              ) : (
                <div>
                  {geometry.systems.map((sys: any) => (
                    <div key={sys.id} className="system-item">
                      <div className="system-item-info">
                        <div className="system-item-icon">
                          {sys.type.includes('Plate') ? '📦' : '🏠'}
                        </div>
                        <div>
                          <div className="system-item-name">System {sys.id}</div>
                          <div className="system-item-type">{sys.type}</div>
                        </div>
                      </div>
                      {sys.Lx && (
                        <span className="badge badge-primary">
                          {sys.Lx}×{sys.Ly}m
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Junctions Panel */}
          <div className="card">
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Link size={18} />
                <span>Junctions</span>
              </div>
              <button className="btn btn-sm btn-secondary" onClick={() => setShowAddJunction(true)}>
                <Plus size={14} />
                Add
              </button>
            </div>
            <div className="card-body">
              {geometry.junctions.length === 0 ? (
                <p className="text-secondary">No junctions added yet</p>
              ) : (
                <div>
                  {geometry.junctions.map((junc: any) => (
                    <div key={junc.name} className="system-item">
                      <div className="system-item-info">
                        <div className="system-item-icon" style={{ background: '#f59e0b' }}>
                          <Link size={14} />
                        </div>
                        <div>
                          <div className="system-item-name">{junc.name}</div>
                          <div className="system-item-type">{junc.type}</div>
                        </div>
                      </div>
                      <span className="badge badge-warning">
                        {junc.systems?.join(' ↔ ')}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="editor-sidebar">
          {/* Quick Actions */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Quick Actions</span>
            </div>
            <div className="panel-body">
              <button className="btn btn-secondary" style={{ width: '100%', marginBottom: 8 }}>
                <Plus size={14} /> Add Plate
              </button>
              <button className="btn btn-secondary" style={{ width: '100%', marginBottom: 8 }}>
                <Plus size={14} /> Add Room
              </button>
              <button className="btn btn-secondary" style={{ width: '100%', marginBottom: 8 }}>
                <Link size={14} /> Add Junction
              </button>
              <button className="btn btn-secondary" style={{ width: '100%' }}>
                <Zap size={14} /> Add Load
              </button>
            </div>
          </div>

          {/* Templates */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Templates</span>
            </div>
            <div className="panel-body">
              <select className="form-select" style={{ marginBottom: 8 }}>
                <option value="">Select template...</option>
                <option value="wall_room">Wall-Room</option>
                <option value="double_wall">Double Wall</option>
                <option value="box_enclosure">Box Enclosure</option>
                <option value="car_model">Car Interior</option>
              </select>
              <button className="btn btn-primary" style={{ width: '100%' }}>
                Apply Template
              </button>
            </div>
          </div>

          {/* Analysis Status */}
          {analysisResult && (
            <div className="panel">
              <div className="panel-header">
                <span className="panel-title">Analysis Result</span>
              </div>
              <div className="panel-body">
                <div className={`badge ${analysisResult.success ? 'badge-success' : 'badge-error'}`}>
                  {analysisResult.success ? 'Success' : 'Failed'}
                </div>
                {analysisResult.energy_shape && (
                  <p style={{ marginTop: 8, fontSize: 13 }}>
                    Energy shape: {analysisResult.energy_shape.join(' × ')}
                  </p>
                )}
                <p style={{ marginTop: 8, fontSize: 13 }}>{analysisResult.message}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add System Modal */}
      {showAddSystem && (
        <div className="modal-overlay" onClick={() => setShowAddSystem(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Add Structural Element</h3>
              <button onClick={() => setShowAddSystem(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={sysName}
                  onChange={(e) => setSysName(e.target.value)}
                  placeholder="wall_1"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Type</label>
                <select 
                  className="form-select"
                  value={systemType}
                  onChange={(e) => setSystemType(e.target.value)}
                >
                  <option value="plate">Plate</option>
                  <option value="beam">Beam</option>
                </select>
              </div>
              <div className="grid grid-3">
                <div className="form-group">
                  <label className="form-label">Length X (m)</label>
                  <input type="number" className="form-input" value={sysLx} onChange={(e) => setSysLx(parseFloat(e.target.value))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Length Y (m)</label>
                  <input type="number" className="form-input" value={sysLy} onChange={(e) => setSysLy(parseFloat(e.target.value))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Thickness (m)</label>
                  <input type="number" className="form-input" value={sysThickness} onChange={(e) => setSysThickness(parseFloat(e.target.value))} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Material</label>
                <select className="form-select" value={sysMaterial} onChange={(e) => setSysMaterial(e.target.value)}>
                  <option value="steel">Steel</option>
                  <option value="aluminum">Aluminum</option>
                  <option value="concrete">Concrete</option>
                  <option value="glass">Glass</option>
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowAddSystem(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleAddSystem}>Add</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectEditor
