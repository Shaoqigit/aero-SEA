import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'

interface GeometryData {
  systems: Array<{
    id: number
    type: string
    Lx?: number
    Ly?: number
    Lz?: number
    volume?: number
    faces?: Array<{
      type: string
      name?: string
      normal?: number[]
      size?: number[]
    }>
  }>
  junctions: Array<{
    name: string
    type: string
    systems: number[]
  }>
}

interface GeometryViewerProps {
  geometry: GeometryData
}

function GeometryViewer({ geometry }: GeometryViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const [hoveredSystem, setHoveredSystem] = useState<number | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Scene setup
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0xf0f4f8)
    sceneRef.current = scene

    // Camera
    const camera = new THREE.PerspectiveCamera(
      50,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    )
    camera.position.set(5, 5, 5)
    camera.lookAt(0, 0, 0)
    cameraRef.current = camera

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight)
    renderer.setPixelRatio(window.devicePixelRatio)
    containerRef.current.appendChild(renderer.domElement)
    rendererRef.current = renderer

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
    directionalLight.position.set(5, 10, 7)
    scene.add(directionalLight)

    // Grid helper
    const gridHelper = new THREE.GridHelper(10, 10, 0xcccccc, 0xe0e0e0)
    scene.add(gridHelper)

    // Create geometry from data
    createGeometry()

    // Animation
    let animationId: number
    const animate = () => {
      animationId = requestAnimationFrame(animate)
      renderer.render(scene, camera)
    }
    animate()

    // Mouse controls (simple orbit)
    let isDragging = false
    let previousMousePosition = { x: 0, y: 0 }
    let cameraAngle = { theta: Math.PI / 4, phi: Math.PI / 4 }
    let cameraDistance = 8

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true
      previousMousePosition = { x: e.clientX, y: e.clientY }
    }

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return

      const deltaX = e.clientX - previousMousePosition.x
      const deltaY = e.clientY - previousMousePosition.y

      cameraAngle.theta -= deltaX * 0.01
      cameraAngle.phi = Math.max(0.1, Math.min(Math.PI - 0.1, cameraAngle.phi + deltaY * 0.01))

      camera.position.x = cameraDistance * Math.sin(cameraAngle.phi) * Math.cos(cameraAngle.theta)
      camera.position.y = cameraDistance * Math.cos(cameraAngle.phi)
      camera.position.z = cameraDistance * Math.sin(cameraAngle.phi) * Math.sin(cameraAngle.theta)
      camera.lookAt(0, 0, 0)

      previousMousePosition = { x: e.clientX, y: e.clientY }
    }

    const onMouseUp = () => {
      isDragging = false
    }

    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      cameraDistance = Math.max(2, Math.min(20, cameraDistance + e.deltaY * 0.01))
      camera.position.x = cameraDistance * Math.sin(cameraAngle.phi) * Math.cos(cameraAngle.theta)
      camera.position.y = cameraDistance * Math.cos(cameraAngle.phi)
      camera.position.z = cameraDistance * Math.sin(cameraAngle.phi) * Math.sin(cameraAngle.theta)
      camera.lookAt(0, 0, 0)
    }

    containerRef.current.addEventListener('mousedown', onMouseDown)
    containerRef.current.addEventListener('mousemove', onMouseMove)
    containerRef.current.addEventListener('mouseup', onMouseUp)
    containerRef.current.addEventListener('wheel', onWheel, { passive: false })

    // Cleanup
    return () => {
      cancelAnimationFrame(animationId)
      containerRef.current?.removeEventListener('mousedown', onMouseDown)
      containerRef.current?.removeEventListener('mousemove', onMouseMove)
      containerRef.current?.removeEventListener('mouseup', onMouseUp)
      containerRef.current?.removeEventListener('wheel', onWheel)
      if (containerRef.current && renderer.domElement) {
        containerRef.current.removeChild(renderer.domElement)
      }
      renderer.dispose()
    }
  }, [])

  // Update geometry when data changes
  useEffect(() => {
    if (!sceneRef.current) return
    
    // Remove existing meshes (except lights and grid)
    const toRemove: THREE.Object3D[] = []
    sceneRef.current.traverse((obj) => {
      if (obj.userData.isGeometry) {
        toRemove.push(obj)
      }
    })
    toRemove.forEach((obj) => sceneRef.current?.remove(obj))

    createGeometry()
  }, [geometry])

  const createGeometry = () => {
    if (!sceneRef.current) return

    const scene = sceneRef.current

    geometry.systems.forEach((sys, index) => {
      const color = index === 0 ? 0x3b82f6 : index === 1 ? 0x22c55e : 0xf59e0b
      const material = new THREE.MeshPhongMaterial({
        color,
        transparent: true,
        opacity: 0.7,
        side: THREE.DoubleSide
      })

      if (sys.Lx && sys.Ly) {
        // Plate geometry
        const geometry = new THREE.BoxGeometry(sys.Lx, sys.Ly, 0.05)
        const mesh = new THREE.Mesh(geometry, material)
        mesh.position.set(sys.Lx / 2, sys.Ly / 2, 0)
        mesh.userData = { isGeometry: true, systemId: sys.id }
        scene.add(mesh)

        // Add label
        addLabel(sys.id.toString(), sys.Lx / 2, sys.Ly / 2, 0.1)
      } else if (sys.faces && sys.Lx && sys.Ly && sys.Lz) {
        // Room/cavity geometry (wireframe box)
        const boxGeometry = new THREE.BoxGeometry(sys.Lx, sys.Ly, sys.Lz)
        const wireframe = new THREE.WireframeGeometry(boxGeometry)
        const line = new THREE.LineSegments(wireframe)
        line.material.color.setHex(0x666666)
        line.position.set(sys.Lx / 2, sys.Ly / 2, sys.Lz / 2)
        line.userData = { isGeometry: true, systemId: sys.id }
        scene.add(line)

        // Semi-transparent inner box
        const innerMaterial = new THREE.MeshPhongMaterial({
          color: 0x22c55e,
          transparent: true,
          opacity: 0.2,
          side: THREE.BackSide
        })
        const innerMesh = new THREE.Mesh(boxGeometry, innerMaterial)
        innerMesh.position.set(sys.Lx / 2, sys.Ly / 2, sys.Lz / 2)
        innerMesh.userData = { isGeometry: true, systemId: sys.id }
        scene.add(innerMesh)
      }
    })

    // Add junction lines
    geometry.junctions.forEach((junc) => {
      if (junc.systems.length === 2) {
        const sys1 = geometry.systems.find((s) => s.id === junc.systems[0])
        const sys2 = geometry.systems.find((s) => s.id === junc.systems[1])
        
        if (sys1 && sys2) {
          const pos1 = new THREE.Vector3(
            (sys1.Lx || 1) / 2,
            (sys1.Ly || 1) / 2,
            0.05
          )
          const pos2 = new THREE.Vector3(
            (sys2.Lx || 1) / 2,
            (sys2.Ly || 1) / 2,
            0.05
          )
          
          const points = [pos1, pos2]
          const lineGeometry = new THREE.BufferGeometry().setFromPoints(points)
          const lineMaterial = new THREE.LineBasicMaterial({ color: 0xef4444, linewidth: 2 })
          const line = new THREE.Line(lineGeometry, lineMaterial)
          line.userData = { isGeometry: true }
          scene.add(line)
        }
      }
    })
  }

  const addLabel = (text: string, x: number, y: number, z: number) => {
    // Labels would require HTML overlay or sprite
    // For simplicity, we'll skip detailed labels in this version
  }

  return (
    <div style={{ position: 'relative', width: '100%', height: 400 }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      <div style={{
        position: 'absolute',
        bottom: 10,
        left: 10,
        fontSize: 12,
        color: '#64748b',
        background: 'rgba(255,255,255,0.9)',
        padding: '8px 12px',
        borderRadius: 4
      }}>
        Drag to rotate • Scroll to zoom
      </div>
      {geometry.systems.length > 0 && (
        <div style={{
          position: 'absolute',
          top: 10,
          right: 10,
          fontSize: 12,
          color: '#64748b',
          background: 'rgba(255,255,255,0.9)',
          padding: '8px 12px',
          borderRadius: 4
        }}>
          {geometry.systems.length} system(s) • {geometry.junctions.length} junction(s)
        </div>
      )}
    </div>
  )
}

export default GeometryViewer
