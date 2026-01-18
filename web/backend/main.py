"""
Aero-SEA Web Backend
FastAPI server for SEA Engine web interface
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Add parent directory to path for sea_engine imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sea_engine import SEAProject
from sea_engine.core.engine import (
    MaterialDefinition, StructuralElement, AcousticSpace, Junction, Load, FrequencyRange
)
from sea_engine.templates import TemplateLibrary, JunctionFactory
from sea_engine.utils import MaterialLibrary, PostTreatment

# Store active projects in memory
projects: Dict[str, SEAProject] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ lifespan context manager for startup/shutdown """
    # Startup: ensure sea_engine is available
    print("Aero-SEA Web Backend starting...")
    yield
    # Shutdown
    projects.clear()
    print("Aero-SEA Web Backend stopped.")


# Create FastAPI app
app = FastAPI(
    title="Aero-SEA Web API",
    description="Web API for Statistical Energy Analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= Pydantic Models =============

class MaterialCreate(BaseModel):
    name: str
    material_type: str = "solid"
    density: Optional[float] = None
    youngs_modulus: Optional[float] = None
    poisson_ratio: Optional[float] = None
    loss_factor: float = 0.01
    speed_of_sound: Optional[float] = None
    bulk_modulus: Optional[float] = None


class MaterialResponse(BaseModel):
    name: str
    material_type: str
    density: Optional[float]
    youngs_modulus: Optional[float]
    poisson_ratio: Optional[float]
    loss_factor: float


class StructureCreate(BaseModel):
    name: str
    element_type: str = "plate"
    dimensions: Dict[str, float]
    material_name: str
    damping_loss_factor: float = 0.01


class StructureResponse(BaseModel):
    id: int
    name: str
    element_type: str
    dimensions: Dict[str, float]
    material_name: str
    damping_loss_factor: float


class AcousticSpaceCreate(BaseModel):
    name: str
    dimensions: Optional[List[float]] = None
    volume: Optional[float] = None
    surface_area: Optional[float] = None
    absorption_area: float = 0.0
    damping_type: List[str] = ["surface"]


class AcousticSpaceResponse(BaseModel):
    id: int
    name: str
    dimensions: Optional[List[float]]
    volume: Optional[float]
    surface_area: Optional[float]
    absorption_area: float


class JunctionCreate(BaseModel):
    name: str
    junction_type: str = "area"
    system1_id: int
    system2_id: int
    area: Optional[float] = None
    length: Optional[float] = None
    angle_degrees: float = 90.0


class JunctionResponse(BaseModel):
    name: str
    junction_type: str
    system1_id: int
    system2_id: int
    area: Optional[float]
    length: Optional[float]


class LoadCreate(BaseModel):
    name: str
    load_type: str = "power"
    system_id: int
    magnitude: float = 0.001
    spectrum: Optional[List[float]] = None


class FrequencyConfig(BaseModel):
    f_min: float = 100.0
    f_max: float = 5000.0
    band_type: str = "third_octave"


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    frequency: FrequencyConfig = FrequencyConfig()


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    frequency: Dict[str, Any]
    systems_count: int
    junctions_count: int
    loads_count: int


class AnalysisResult(BaseModel):
    success: bool
    energy_shape: Optional[List[int]] = None
    message: str


class GeometryResponse(BaseModel):
    systems: List[Dict[str, Any]]
    junctions: List[Dict[str, Any]]


class ModalResult(BaseModel):
    system_id: int
    system_type: str
    wave_type: int
    modal_density: List[float]
    modal_overlap: List[float]
    frequency: List[float]


# ============= Helper Functions =============

def get_project(project_id: str) -> SEAProject:
    """Get project by ID or raise 404"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects[project_id]


def system_to_geometry(system: Any, system_id: int) -> Dict[str, Any]:
    """Convert SEA system to 3D geometry data"""
    geom = {
        "id": system_id,
        "type": type(system).__name__,
        "faces": []
    }
    
    # Get dimensions based on system type
    if hasattr(system, 'Lx'):
        geom["Lx"] = system.Lx
        geom["Ly"] = system.Ly
        if hasattr(system, 'Lz'):
            geom["Lz"] = system.Lz
        # Create plate geometry
        geom["faces"] = [
            {
                "type": "plate",
                "center": [system.Lx/2, system.Ly/2, 0],
                "size": [system.Lx, system.Ly],
                "normal": [0, 0, 1]
            }
        ]
    elif hasattr(system, 'volume'):
        geom["volume"] = system.volume
        geom["surface_area"] = system.surface_area
        # Create room/cavity geometry
        if hasattr(system, 'Lx'):
            geom["faces"] = [
                {"type": "wall", "name": "floor", "normal": [0, 0, -1], "size": [system.Lx, system.Ly]},
                {"type": "wall", "name": "ceiling", "normal": [0, 0, 1], "size": [system.Lx, system.Ly]},
                {"type": "wall", "name": "wall_x1", "normal": [-1, 0, 0], "size": [system.Lz, system.Ly]},
                {"type": "wall", "name": "wall_x2", "normal": [1, 0, 0], "size": [system.Lz, system.Ly]},
                {"type": "wall", "name": "wall_y1", "normal": [0, -1, 0], "size": [system.Lx, system.Lz]},
                {"type": "wall", "name": "wall_y2", "normal": [0, 1, 0], "size": [system.Lx, system.Lz]},
            ]
    
    return geom


# ============= API Endpoints =============

@app.get("/")
async def root():
    """API health check"""
    return {"status": "ok", "message": "Aero-SEA Web API", "version": "1.0.0"}


# --- Projects ---

@app.post("/projects", response_model=ProjectResponse)
async def create_project(data: ProjectCreate) -> ProjectResponse:
    """Create a new SEA project"""
    import uuid
    project_id = str(uuid.uuid4())[:8]
    
    project = SEAProject()
    project.metadata.name = data.name
    project.metadata.description = data.description
    
    # Set frequency range
    project.set_frequency_range(
        f_min=data.frequency.f_min,
        f_max=data.frequency.f_max,
        band_type=data.frequency.band_type
    )
    
    projects[project_id] = project
    
    return ProjectResponse(
        id=project_id,
        name=project.metadata.name,
        description=project.metadata.description,
        frequency={
            "f_min": data.frequency.f_min,
            "f_max": data.frequency.f_max,
            "band_type": data.frequency.band_type
        },
        systems_count=0,
        junctions_count=0,
        loads_count=0
    )


@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project_info(project_id: str) -> ProjectResponse:
    """Get project information"""
    project = get_project(project_id)
    
    systems_count = len(project.systems) if hasattr(project, 'systems') else 0
    junctions_count = len(project.junctions) if hasattr(project, 'junctions') else 0
    loads_count = len(project.loads) if hasattr(project, 'loads') else 0
    
    return ProjectResponse(
        id=project_id,
        name=project.metadata.name,
        description=project.metadata.description,
        frequency={
            "f_min": 100,
            "f_max": 5000,
            "band_type": "third_octave"
        },
        systems_count=systems_count,
        junctions_count=junctions_count,
        loads_count=loads_count
    )


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    if project_id in projects:
        del projects[project_id]
        return {"status": "ok", "message": "Project deleted"}
    raise HTTPException(status_code=404, detail="Project not found")


# --- Materials ---

@app.get("/materials")
async def list_materials() -> List[MaterialResponse]:
    """List available materials from library"""
    materials = MaterialLibrary.list_materials()
    result = []
    for name in materials:
        mat = MaterialLibrary.get_material(name)
        if mat:
            result.append(MaterialResponse(
                name=name,
                material_type=mat.get("type", "solid"),
                density=mat.get("density"),
                youngs_modulus=mat.get("youngs_modulus"),
                poisson_ratio=mat.get("poisson_ratio"),
                loss_factor=mat.get("loss_factor", 0.01)
            ))
    return result


@app.post("/projects/{project_id}/materials")
async def add_material(project_id: str, data: MaterialCreate):
    """Add material to project"""
    project = get_project(project_id)
    
    material = MaterialDefinition(
        name=data.name,
        material_type=data.material_type,
        density=data.density,
        youngs_modulus=data.youngs_modulus,
        poisson_ratio=data.poisson_ratio,
        loss_factor=data.loss_factor,
        speed_of_sound=data.speed_of_sound,
        bulk_modulus=data.bulk_modulus
    )
    
    project.add_material(material)
    
    return {"status": "ok", "material_name": data.name}


# --- Structures ---

@app.get("/templates")
async def list_templates() -> Dict[str, List[str]]:
    """List available templates"""
    return {"templates": TemplateLibrary.list_templates()}


@app.post("/projects/{project_id}/structures")
async def add_structure(project_id: str, data: StructureCreate):
    """Add structural element to project"""
    project = get_project(project_id)
    
    # Get material
    material = None
    for mat in project.materials:
        if mat.name == data.material_name:
            material = mat
            break
    
    if not material:
        raise HTTPException(status_code=400, detail=f"Material {data.material_name} not found")
    
    structure = StructuralElement(
        name=data.name,
        element_type=data.element_type,
        dimensions=data.dimensions,
        material=material,
        damping_loss_factor=data.damping_loss_factor
    )
    
    system_id = project.add_structure(structure)
    
    return {"status": "ok", "system_id": system_id}


# --- Acoustic Spaces ---

@app.post("/projects/{project_id}/acoustic-spaces")
async def add_acoustic_space(project_id: str, data: AcousticSpaceCreate):
    """Add acoustic space to project"""
    project = get_project(project_id)
    
    space = AcousticSpace(
        name=data.name,
        dimensions=tuple(data.dimensions) if data.dimensions else None,
        volume=data.volume,
        surface_area=data.surface_area,
        absorption_area=data.absorption_area,
        damping_type=data.damping_type
    )
    
    system_id = project.add_acoustic_space(space)
    
    return {"status": "ok", "system_id": system_id}


# --- Junctions ---

@app.post("/projects/{project_id}/junctions")
async def add_junction(project_id: str, data: JunctionCreate):
    """Add junction to project"""
    project = get_project(project_id)
    
    # Get systems
    system1 = None
    system2 = None
    for sys in project.systems:
        if sys.system_id == data.system1_id:
            system1 = sys
        if sys.system_id == data.system2_id:
            system2 = sys
    
    if not system1 or not system2:
        raise HTTPException(status_code=400, detail="System not found")
    
    junction = JunctionFactory.create_line_junction(
        name=data.name,
        system1=system1,
        system2=system2,
        length=data.length if data.length else 1.0,
        angle_degrees=data.angle_degrees
    )
    
    # Override junction type if area
    if data.junction_type == "area":
        junction = Junction(
            name=data.name,
            junction_type="area",
            systems=(system1, system2),
            area=data.area
        )
    
    project.add_junction(junction)
    
    return {"status": "ok", "junction_name": data.name}


# --- Loads ---

@app.post("/projects/{project_id}/loads")
async def add_load(project_id: str, data: LoadCreate):
    """Add load to project"""
    project = get_project(project_id)
    
    load = Load(
        name=data.name,
        load_type=data.load_type,
        system_id=data.system_id,
        magnitude=data.magnitude,
        spectrum=np.array(data.spectrum) if data.spectrum else None
    )
    
    project.add_load(load)
    
    return {"status": "ok", "load_name": data.name}


# --- Analysis ---

@app.post("/projects/{project_id}/analyze", response_model=AnalysisResult)
async def run_analysis(project_id: str):
    """Run SEA analysis"""
    project = get_project(project_id)
    
    if project.run_analysis():
        results = project.get_results()
        energy = results.get('energy')
        
        return AnalysisResult(
            success=True,
            energy_shape=list(energy.ydata.shape) if energy else None,
            message="Analysis completed successfully"
        )
    
    return AnalysisResult(
        success=False,
        message="Analysis failed"
    )


# --- Geometry ---

@app.get("/projects/{project_id}/geometry", response_model=GeometryResponse)
async def get_geometry(project_id: str) -> GeometryResponse:
    """Get 3D geometry data for visualization"""
    project = get_project(project_id)
    
    # Get systems
    systems_data = []
    for sys in project.systems:
        geom = system_to_geometry(sys, sys.system_id)
        systems_data.append(geom)
    
    # Get junctions
    junctions_data = []
    for jname, junction in project.junctions.items():
        jdata = {
            "name": jname,
            "type": junction.junction_type,
            "systems": [s.system_id for s in junction.systems] if hasattr(junction.systems[0], 'system_id') else [1, 2]
        }
        if junction.area:
            jdata["area"] = junction.area
        if junction.length:
            jdata["length"] = junction.length
        junctions_data.append(jdata)
    
    return GeometryResponse(
        systems=systems_data,
        junctions=junctions_data
    )


# --- Results ---

@app.get("/projects/{project_id}/energy")
async def get_energy_results(project_id: str):
    """Get energy results"""
    project = get_project(project_id)
    results = project.get_results()
    energy = results.get('energy')
    
    if not energy:
        raise HTTPException(status_code=404, detail="No results found")
    
    return {
        "data": energy.ydata.tolist(),
        "dof_id": energy.dof.ID.tolist(),
        "dof_type": energy.dof.DOF.tolist()
    }


@app.get("/projects/{project_id}/modal-density", response_model=List[ModalResult])
async def get_modal_density(project_id: str) -> List[ModalResult]:
    """Get modal density for all systems"""
    project = get_project(project_id)
    
    if not project.model:
        raise HTTPException(status_code=400, detail="Model not solved")
    
    results = []
    
    # Get frequency in Hz
    freq_hz = []
    if hasattr(project.engine, 'config') and project.engine.config:
        omega = project.engine.create_frequency_axis()
        freq_hz = (np.array(omega.data.flatten()) / (2 * np.pi)).tolist()
    else:
        # Default
        freq_hz = list(range(100, 5000, 100))
    
    # Get modal density for each system
    omega_np = np.array(freq_hz) * 2 * np.pi
    for sys in project.systems:
        try:
            if hasattr(sys, 'modal_density'):
                md = sys.modal_density(omega_np)
                mo = sys.modal_overlap(omega_np)
                
                results.append(ModalResult(
                    system_id=sys.system_id,
                    system_type=type(sys).__name__,
                    wave_type=3,  # bending for plates
                    modal_density=md.tolist(),
                    modal_overlap=mo.tolist(),
                    frequency=freq_hz
                ))
        except Exception as e:
            print(f"Could not get modal density for system {sys.system_id}: {e}")
    
    return results


@app.post("/projects/{project_id}/export-results")
async def export_results(project_id: str, units: Dict[str, str] = None):
    """Export results to JSON"""
    project = get_project(project_id)
    
    if not project.model:
        raise HTTPException(status_code=400, detail="Model not solved")
    
    # Create post-treatment
    pt = PostTreatment(project_name=project.metadata.name)
    if units:
        pt.set_units(**units)
    
    result_data = pt.process_model(project.model)
    
    return result_data.to_dict()


# --- Templates ---

@app.post("/projects/{project_id}/apply-template")
async def apply_template(project_id: str, template_name: str, params: Dict[str, Any]):
    """Apply a template to the project"""
    project = get_project(project_id)
    
    template_func = TemplateLibrary.get_template(template_name)
    if not template_func:
        raise HTTPException(status_code=400, detail=f"Template {template_name} not found")
    
    try:
        result = template_func(**params)
        
        # Add materials
        for material in result.get("materials", []):
            project.add_material(material)
        
        # Add structures
        for structure in result.get("structures", []):
            project.add_structure(structure)
        
        # Add acoustic spaces
        for space in result.get("acoustic_spaces", []):
            project.add_acoustic_space(space)
        
        return {"status": "ok", "message": f"Template {template_name} applied"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
