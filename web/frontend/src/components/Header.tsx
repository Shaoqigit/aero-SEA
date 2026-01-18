import React from 'react'
import { Menu, Database, ChevronRight } from 'lucide-react'

interface HeaderProps {
  projectId: string | null
  onToggleSidebar: () => void
}

function Header({ projectId, onToggleSidebar }: HeaderProps) {
  return (
    <header className="header">
      <div className="header-left">
        <button className="header-menu-btn" onClick={onToggleSidebar}>
          <Menu size={20} />
        </button>
        <div className="header-logo">
          <Database size={24} />
          <span>Aero-SEA</span>
        </div>
      </div>
      
      <div className="header-center">
        {projectId && (
          <div className="header-breadcrumb">
            <span>Project</span>
            <ChevronRight size={16} />
            <span className="breadcrumb-id">{projectId}</span>
          </div>
        )}
      </div>
      
      <div className="header-right">
        <div className="header-status">
          <span className="status-dot"></span>
          <span>Connected</span>
        </div>
      </div>
    </header>
  )
}

export default Header
