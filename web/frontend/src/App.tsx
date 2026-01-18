import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ProjectList from './pages/ProjectList'
import ProjectEditor from './pages/ProjectEditor'
import ResultsViewer from './pages/ResultsViewer'
import './styles/App.css'

function App() {
  const [currentProject, setCurrentProject] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <BrowserRouter>
      <div className="app">
        <Header 
          projectId={currentProject}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        />
        <div className="app-body">
          <Sidebar isOpen={sidebarOpen} />
          <main className={`main-content ${sidebarOpen ? '' : 'sidebar-collapsed'}`}>
            <Routes>
              <Route path="/" element={<ProjectList onSelectProject={setCurrentProject} />} />
              <Route 
                path="/project/:projectId" 
                element={<ProjectEditor projectId={currentProject} onNavigate={setCurrentProject} />}
              />
              <Route 
                path="/results/:projectId" 
                element={<ResultsViewer projectId={currentProject} />}
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App
