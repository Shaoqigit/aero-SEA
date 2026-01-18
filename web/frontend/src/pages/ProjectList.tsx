import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, Search } from 'lucide-react'
import api from '../utils/api'

interface ProjectListProps {
  onSelectProject: (id: string) => void
}

interface Project {
  id: string
  name: string
  description?: string
  systems_count: number
  junctions_count: number
  loads_count: number
}

function ProjectList({ onSelectProject }: ProjectListProps) {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return
    
    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newProjectName })
      })
      const project = await response.json()
      setProjects([...projects, project])
      setShowCreateModal(false)
      setNewProjectName('')
      onSelectProject(project.id)
      navigate(`/project/${project.id}`)
    } catch (error) {
      console.error('Failed to create project:', error)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Projects</h1>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          <Plus size={16} />
          New Project
        </button>
      </div>

      <div className="search-bar">
        <Search size={20} />
        <input
          type="text"
          placeholder="Search projects..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="form-input"
        />
      </div>

      {projects.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📁</div>
          <h3 className="empty-state-title">No projects yet</h3>
          <p>Create your first SEA project to get started</p>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            <Plus size={16} />
            Create Project
          </button>
        </div>
      ) : (
        <div className="grid grid-3">
          {projects.filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase())).map((project) => (
            <div
              key={project.id}
              className="project-card"
              onClick={() => {
                onSelectProject(project.id)
                navigate(`/project/${project.id}`)
              }}
            >
              <div className="project-card-header">
                <h3 className="project-card-title">{project.name}</h3>
                <FolderOpen size={20} color="var(--text-secondary)" />
              </div>
              <p className="project-card-description">
                {project.description || 'No description'}
              </p>
              <div className="project-card-meta">
                <span>{project.systems_count} systems</span>
                <span>{project.junctions_count} junctions</span>
                <span>{project.loads_count} loads</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Create New Project</h3>
              <button onClick={() => setShowCreateModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Project Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="My SEA Project"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleCreateProject}>
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectList
