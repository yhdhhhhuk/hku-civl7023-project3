"""Exact CSG solid + matching convex partition, in millimetres for CAD.

Simulation meshes are written in metres. Bottom-centred origin, NOT centre of
mass. No convex-hull approximation of the complete concave component is used.
"""
from pathlib import Path
import json
import struct
import hashlib
import numpy as np
import manifold3d as m

HERE = Path(__file__).resolve().parent
MODEL = HERE / "构件模型"
VERSION = "P3-GrooveKey-v2"
PARAMS = {
    "version": VERSION, "units": "mm", "origin": "bottom plane centre, +Z upward",
    "envelope_xyz": [50, 30, 25], "body_height": 22, "stack_pitch": 22,
    "notch_length_x": 38, "notch_depth_each_y": 4, "notch_floor_z": 10,
    "notch_top_z": 22, "grip_face_separation": 22,
    "boss_centres_x": [-20, 20], "boss_base_xy": [4, 8],
    "boss_top_xy": [2, 6], "boss_z": [22, 25],
    "socket_xy": [6, 10], "socket_depth": 3.5,
    "socket_entry_xy": [8, 12], "socket_chamfer_height": 0.5,
    "nominal_lateral_mating_gap_each": 1, "nominal_roof_gap": 0.5,
    "tcp_from_bottom_xyz": [0, 0, 14], "grip_depth_below_body_top": 8,
    "dynamics": "static geometry only; mass, centre of mass and inertia to be provided by A",
}


def loft_rect(x0, x1, y0, y1, z0, X0, X1, Y0, Y1, z1):
    return m.Manifold.hull_points(np.array([
        [x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],
        [X0,Y0,z1],[X1,Y0,z1],[X1,Y1,z1],[X0,Y1,z1]], dtype=float))


def box(x0,x1,y0,y1,z0,z1):
    return m.Manifold.cube((x1-x0,y1-y0,z1-z0)).translate((x0,y0,z0))


def write_stl(path, solid, scale):
    mesh = solid.to_mesh()
    vertices = np.asarray(mesh.vert_properties)[:, :3] * scale
    triangles = vertices[np.asarray(mesh.tri_verts)]
    with path.open("wb") as f:
        f.write((VERSION + "; " + ("metres" if scale == .001 else "millimetres")).encode().ljust(80,b" "))
        f.write(struct.pack("<I",len(triangles)))
        for tri in triangles:
            normal=np.cross(tri[1]-tri[0],tri[2]-tri[0])
            normal/=np.linalg.norm(normal)
            f.write(struct.pack("<12fH",*normal,*tri.flatten(),0))
    return len(triangles)


def build():
    MODEL.mkdir(parents=True,exist_ok=True)
    (MODEL/"convex").mkdir(exist_ok=True)
    pieces=[]
    # The rectangular grid is expanded at the socket mouth, forming a 0.5 mm
    # chamfer. Every retained loft is convex; the two socket cells remain empty.
    xb=[-25,-24,-16,16,24,25]; xt=[-25,-23,-17,17,23,25]
    yb=[-15,-6,6,15]; yt=[-15,-5,5,15]
    for i in range(5):
        for j in range(3):
            if i in (1,3) and j==1:
                continue
            pieces.append((f"socket_mouth_{i}_{j}",loft_rect(
                xb[i],xb[i+1],yb[j],yb[j+1],0,
                xt[i],xt[i+1],yt[j],yt[j+1],.5)))
            pieces.append((f"socket_wall_{i}_{j}",box(xt[i],xt[i+1],yt[j],yt[j+1],.5,3.5)))
    pieces.append(("lower_body",box(-25,25,-15,15,3.5,10)))
    pieces.append(("grip_core",box(-25,25,-11,11,10,22)))
    for i,(x0,x1) in enumerate(((-25,-19),(19,25))):
        for j,(y0,y1) in enumerate(((-15,-11),(11,15))):
            pieces.append((f"end_land_{i}_{j}",box(x0,x1,y0,y1,10,22)))
    for i,x in enumerate((-20,20)):
        pieces.append((f"guide_boss_{i}",loft_rect(x-2,x+2,-4,4,22,x-1,x+1,-3,3,25)))
    solid=m.Manifold.batch_boolean([s for _,s in pieces],m.OpType.Add)
    # Independently express the same part by subtraction, then compare solids.
    reference=box(-25,25,-15,15,0,22)
    for y0,y1 in ((-15,-11),(11,15)):
        reference=reference-box(-19,19,y0,y1,10,23)
    for x in (-20,20):
        pocket=loft_rect(x-4,x+4,-6,6,0,x-3,x+3,-5,5,.5)+box(x-3,x+3,-5,5,.5,3.5)
        reference=reference-pocket
        reference=reference+loft_rect(x-2,x+2,-4,4,22,x-1,x+1,-3,3,25)
    difference=(solid-reference).volume()+(reference-solid).volume()
    assert difference < 1e-5, difference
    # Use the subtraction model for the display/export shell; a partition union
    # can retain zero-volume seam fragments at coplanar cell boundaries.
    solid=reference
    assert str(solid.status()).endswith("NoError"),solid.status()
    assert len(solid.decompose())==1,"Part must be connected"
    n=write_stl(MODEL/"groove_key_block_m.stl",solid,.001)
    write_stl(MODEL/"groove_key_block_mm.stl",solid,1)
    files=[]
    for label,s in pieces:
        path=MODEL/"convex"/(label+".stl")
        write_stl(path,s,.001)
        files.append(path.relative_to(MODEL).as_posix())
    # A direct-shape loader is supplied in component_model.py. URDF import wraps
    # mesh shapes in extra compounds whose child margins cannot be adjusted with
    # changeDynamics; that would inflate the sockets and falsely report clashes.
    # Editable CSG CAD source uses mm, including the two lofted lead-in sockets.
    scad='''// P3-GrooveKey-v2; mm; origin = bottom plane centre.
// Dimensional reference is parameters.json; total envelope 50 x 30 x 25.
module rect_loft(cx,z,h,bottom,top) {
  bx=bottom[0]/2; by=bottom[1]/2; tx=top[0]/2; ty=top[1]/2;
  polyhedron(points=[[cx-bx,-by,z],[cx+bx,-by,z],[cx+bx,by,z],[cx-bx,by,z],
                     [cx-tx,-ty,z+h],[cx+tx,-ty,z+h],[cx+tx,ty,z+h],[cx-tx,ty,z+h]],
             faces=[[3,2,1,0],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]);
}
union() {
  difference() {
    translate([-25,-15,0]) cube([50,30,22]);
    for (y=[-15,11]) translate([-19,y,10]) cube([38,4,12.01]);
    for (x=[-20,20]) {
      rect_loft(x,-0.001,0.501,[8.004,12.004],[6,10]);
      translate([x-3,-5,0.499]) cube([6,10,3.002]);
    }
  }
  for (x=[-20,20]) rect_loft(x,22,3,[4,8],[2,6]);
}
'''
    (MODEL/"groove_key_block.scad").write_text(scad)
    result={**PARAMS,"volume_mm3":solid.volume(),"surface_triangles":n,
            "collision_convex_parts":len(pieces),"csg_partition_symmetric_difference_mm3":difference,
            "solid_connected_components":len(solid.decompose()),"solid_status":str(solid.status()),
            "collision_parts":files,
            "file_sha256":{p.relative_to(MODEL).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(MODEL.rglob('*')) if p.is_file() and p.suffix!='.json'}}
    (MODEL/"parameters.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('version','volume_mm3','surface_triangles','collision_convex_parts','solid_status')},indent=2))
    return result


if __name__=='__main__':
    build()
