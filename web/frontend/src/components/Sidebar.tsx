import React from 'react'
import { Home, FolderKanban, Settings, HelpCircle, Book } from 'lucide-react'
import './Sidebar.css'

interface SidebarProps {
  isOpen: boolean
}

function Sidebar({ isOpen }: SidebarProps) {
  const menuItems = [
    { icon: Home, label: 'Dashboard', href: '/' },
    { icon: FolderKanban, label: 'Projects', href: '/' },
    { icon: Book, label: 'Templates', href: '/' },
    { icon: Settings, label: 'Settings', href: '/' },
    { icon: HelpCircle, label: 'Help', href: '/' },
  ]
  
  return (
    <aside className={`sidebar ${isOpen ? '' : 'sidebar-collapsed'}`}>
      <nav className="sidebar-nav">
        {menuItems.map((item, index) => (
          <a key={index} href={item.href} className="sidebar-item">
            <item.icon size={20} />
            <span className="sidebar-label">{item.label}</span>
          </a>
        ))}
      </nav>
      
      <div className="sidebar-footer">
        <div className="sidebar-version">v1.0.0</div>
      </div>
    </aside>
  )
}

export default Sidebar
