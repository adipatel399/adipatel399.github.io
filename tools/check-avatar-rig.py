"""Regression check: facial landmarks must retain their spacing during head turns."""
import bpy, pathlib, itertools
from mathutils import Vector
root=pathlib.Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(root/'tools/portrait.blend'))
body=bpy.data.objects['Human'];bone=bpy.data.objects['PortraitRig'].pose.bones['Head']
def coord(p):return Vector((p[0]*.4,-p[2]*.4,(p[1]-3.7)*.4))
landmarks={'chin':(0,6.68,1.18),'mouth':(0,7.18,1.55),'nose':(0,7.63,1.65),'temple':(.65,7.9,.9),'forehead':(0,8.2,1.5)}
ids={k:min(body.data.vertices,key=lambda v:(v.co-coord(p)).length_squared).index for k,p in landmarks.items()}
shoulder=min(body.data.vertices,key=lambda v:(v.co-coord((1.75,5.4,.5))).length_squared).index
pairs=list(itertools.combinations(ids,2))
rest={k:body.data.vertices[i].co.copy() for k,i in ids.items()}
for pitch,yaw in [(0,.38),(0,-.38),(.16,0),(-.16,0),(.16,.38)]:
    bone.rotation_mode='XYZ';bone.rotation_euler=(pitch,yaw,0);bpy.context.view_layer.update()
    evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    for a,b in pairs:
        delta=abs((evaluated.vertices[ids[a]].co-evaluated.vertices[ids[b]].co).length-(rest[a]-rest[b]).length)
        assert delta<1e-5,(pitch,yaw,a,b,delta)
    assert (evaluated.vertices[shoulder].co-body.data.vertices[shoulder].co).length<1e-5
print('PASS: chin, mouth, nose, temple and forehead move rigidly together in five poses; shoulder stays fixed.')
