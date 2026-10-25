"""Build the portfolio portrait in Blender. Run with Blender --background --python tools/build-avatar.py.
MakeHuman CC0 topology and fitted T-shirt; original cap and glasses. Y-up input -> Z-up Blender.
"""
import bpy, bmesh, math, json, pathlib
from mathutils import Vector, Matrix
ROOT=pathlib.Path(__file__).resolve().parent.parent
SRC=ROOT/'tools/avatar-source'; OUT=ROOT/'assets/avatar'; OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def read_obj(path):
    v=[];uv=[];faces=[];group='body'
    for line in open(path):
        a=line.split()
        if not a: continue
        if a[0]=='v': v.append(Vector(map(float,a[1:4])))
        elif a[0]=='vt': uv.append(tuple(map(float,a[1:3])))
        elif a[0]=='g': group=a[1]
        elif a[0]=='f':
            ids=[x.split('/') for x in a[1:]]
            faces.append(([int(x[0])-1 for x in ids],[int(x[1])-1 if len(x)>1 and x[1] else 0 for x in ids],group))
    return v,uv,faces
v,uv,faces=read_obj(SRC/'base.obj')
for name,weight in [('caucasian-male-young.target',.72),('asian-male-young.target',.28),('universal-male-young-averagemuscle-averageweight.target',1)]:
    for line in open(SRC/name):
        a=line.split()
        if a and not a[0].startswith('#'):v[int(a[0])]+=Vector(map(float,a[1:4]))*weight
# A small closed-mouth smile: lift the lip corners, with a soft cheek response.
# Move both lips together so there is no exaggerated grin or exposed teeth.
for p in v:
    if p.z>1.0 and 6.8<p.y<7.8:
        corner=math.exp(-((abs(p.x)-.27)/.15)**2-((p.y-7.15)/.17)**2)
        cheek=math.exp(-((abs(p.x)-.43)/.23)**2-((p.y-7.43)/.24)**2)
        p.y+=.080*corner+.022*cheek
        p.x+=math.copysign(.009*corner,p.x)
skeleton=json.load(open(SRC/'default.mhskel'))
weights=json.load(open(SRC/'default_weights.mhw'))['weights']
vertexweights=[{} for _ in v]
for bone,entries in weights.items():
    for i,w in entries: vertexweights[i][bone]=w

def joint(bone,part):
    ids=skeleton['joints'][skeleton['bones'][bone][part]]
    return sum((v[i] for i in ids),Vector())/len(ids)
# Bake an anatomically relaxed A-pose. Both wrists and palms face the thighs.
transforms={}
for suffix,side in [('L',1),('R',-1)]:
    shoulder=joint('upperarm01.'+suffix,'head');elbow=joint('lowerarm01.'+suffix,'head');wrist=joint('wrist.'+suffix,'head')
    q=(elbow-shoulder).rotation_difference(Vector((side*.16,-.985,.03)))
    a=Matrix.Translation(shoulder)@q.to_matrix().to_4x4()@Matrix.Translation(-shoulder)
    newelbow=a@elbow
    q2=(wrist-elbow).rotation_difference(Vector((side*.015,-.997,.065)))
    b=Matrix.Translation(newelbow)@q2.to_matrix().to_4x4()@Matrix.Translation(-elbow)
    newwrist=b@wrist
    c=Matrix.Translation(newwrist)@Matrix.Rotation(math.radians(-side*55),4,'Y')@Matrix.Translation(-newwrist)@b
    for bn in skeleton['bones']:
        if bn.endswith('.'+suffix):
            if bn.startswith('upperarm'): transforms[bn]=a
            elif bn.startswith('lowerarm'): transforms[bn]=b
            elif bn.startswith(('wrist','finger','metacarpal')): transforms[bn]=c
    # Relax the fingers into a gentle curl instead of displaying an open palm.
    for finger in range(2,6):
        previous=c
        for segment in range(1,4):
            bn=f'finger{finger}-{segment}.{suffix}'
            h=joint(bn,'head');t=joint(bn,'tail');newh=previous@h
            direction=Vector((-side*[.035,.22,.42][segment-1],-1,.035)).normalized()
            r=(t-h).rotation_difference(direction).to_matrix().to_4x4()
            previous=Matrix.Translation(newh)@r@Matrix.Translation(-h)
            transforms[bn]=previous


def posed(p,ws):
    total=sum(ws.values())
    if not total:return p.copy()
    return sum(((transforms.get(b,Matrix.Identity(4))@p)*w for b,w in ws.items()),Vector())/total

def coord(p):return Vector((p.x*.40,-p.z*.40,(p.y-3.7)*.40))

def mat(name,color,rough=.6,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m

def texture(m,path,normal=False,size=2048):
    img=bpy.data.images.load(str(path),check_existing=True)
    if max(img.size)>size:img.scale(size,size)
    img.pack();n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=img
    bs=m.node_tree.nodes.get('Principled BSDF')
    if normal:
        img.colorspace_settings.name='Non-Color';nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.42
        m.node_tree.links.new(n.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    else:m.node_tree.links.new(n.outputs['Color'],bs.inputs['Base Color'])
    return n
skin=mat('Fair skin — clean shaven',(.69,.43,.30),.58)
texture(skin,SRC/'optimized/skin.jpg')
skin.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=.08
cloth=mat('Powder blue polo pique',(.22,.40,.56),.90)
texture(cloth,SRC/'optimized/cotton-normal.png',True)
capmat=mat('Midnight cotton twill',(.006,.009,.014),.91)
texture(capmat,SRC/'optimized/cap-twill.png',True,size=128)
seammat=mat('Tonal cap stitching',(.009,.013,.019),.93)
frame=mat('Brushed bronze sunglasses',(.11,.095,.073),.32,.82)
lens=mat('Smoked sunglasses lenses',(.012,.017,.015),.20,0)
lens.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.25
lens.node_tree.nodes.get('Principled BSDF').inputs['Coat Roughness'].default_value=.12
hairmat=mat('Short dark hair',(.013,.009,.008),.92)
hardware=mat('Brushed cap hardware',(.16,.18,.20),.4,.75)
capmat.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.18
capmat.node_tree.nodes.get('Principled BSDF').inputs['Sheen Weight'].default_value=.28
white=mat('Embroidery',(.69,.59,.87),.8)

def make_mesh(name,verts,tex,fs,material,ws=None,filter_fn=None,sub=1):
    keep=[f for f in fs if filter_fn is None or filter_fn(f)]
    ids=sorted({i for f,_,_ in keep for i in f});mapping={old:new for new,old in enumerate(ids)}
    points=[coord(posed(verts[i],ws[i]) if ws else verts[i]) for i in ids]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(points,[],[[mapping[i] for i in f] for f,_,_ in keep]);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(material)
    if tex:
        layer=mesh.uv_layers.new(name='UVMap')
        for poly,(_,uvs,_) in zip(mesh.polygons,keep):
            for li,ui in zip(poly.loop_indices,uvs):layer.data[li].uv=tex[ui]
    for p in mesh.polygons:p.use_smooth=True
    if sub:
        mod=obj.modifiers.new('Subdivision surface','SUBSURF');mod.levels=sub;mod.render_levels=sub
        bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj

body=make_mesh('Human',v,uv,faces,skin,vertexweights,lambda f:f[2]=='body' and (min(v[i].y for i in f[0])>1.0 or min(abs(v[i].x) for i in f[0])>2.6),1)

def proxy(name,objfile,mhclo,material,filter_fn=None,sub=1):
    vv,uu,ff=read_obj(objfile);pv=[];pw=[];scales=Vector((1,1,1));reading=False
    if name=='TShirt':
        # Keep the complete shirt component, including its hem; discard the jeans.
        parents=list(range(len(vv)))
        def root(i):
            while parents[i]!=i:
                parents[i]=parents[parents[i]];i=parents[i]
            return i
        for f,_,_ in ff:
            for i in f[1:]:parents[root(i)]=root(f[0])
        groups={}
        for i in range(len(vv)):groups.setdefault(root(i),[]).append(i)
        shirt_ids=set(max(groups.values(),key=len))
        ff=[f for f in ff if f[0][0] in shirt_ids]
    if name=='Eyes':
        # The supplied atlas has a transparent cornea region. Omit that outer
        # shell rather than turning its transparent blue texels into opaque eyes.
        ff=[f for f in ff if not all(uu[i][0]>.8 and uu[i][1]<.2 for i in f[1])]

    for line in open(mhclo):
        a=line.split()
        if not a or a[0].startswith('#'):continue
        if a[0] in ('x_scale','y_scale','z_scale'):
            axis={'x_scale':0,'y_scale':1,'z_scale':2}[a[0]];scales[axis]=abs(v[int(a[1])][axis]-v[int(a[2])][axis])/float(a[3])
        elif a[0]=='material':continue
        elif a[0]=='verts':reading=True
        elif reading:
            try:ids=list(map(int,a[:3]));w=list(map(float,a[3:6]));off=Vector(map(float,a[6:9]))
            except (ValueError,IndexError):break
            if len(a)<9:break
            pv.append(sum((v[i]*ww for i,ww in zip(ids,w)),Vector())+Vector(off[k]*scales[k] for k in range(3)))
            weights0={}
            for i,ww in zip(ids,w):
                for bn,bw in vertexweights[i].items():weights0[bn]=weights0.get(bn,0)+ww*bw
            pw.append(weights0)
    assert len(pv)==len(vv),(name,len(pv),len(vv))
    obj=make_mesh(name,pv,uu,ff,material,pw,lambda f:filter_fn(f,pv) if filter_fn else True,sub)
    return obj
shirt=proxy('TShirt',SRC/'clothes/male_casualsuit06/male_casualsuit06.obj',SRC/'clothes/male_casualsuit06/male_casualsuit06.mhclo',cloth)
eyemat=mat('Brown eyes',(.8,.8,.8),.28);texture(eyemat,SRC/'optimized/eyes.jpg',size=1024)
eyes=proxy('Eyes',SRC/'high-poly.obj',SRC/'high-poly.mhclo',eyemat,sub=0)
browmat=mat('Natural eyebrows',(.018,.012,.01),.9)
node=texture(browmat,SRC/'eyebrows/eyebrow002/eyebrow002.png',size=1024)
browmat.node_tree.links.new(node.outputs['Alpha'],browmat.node_tree.nodes.get('Principled BSDF').inputs['Alpha']);browmat.surface_render_method='DITHERED'
brows=proxy('Eyebrows',SRC/'eyebrows/eyebrow002/eyebrow002.obj',SRC/'eyebrows/eyebrow002/eyebrow002.mhclo',browmat)
# Remove everything below the abdomen from the exported model, including forearms.
# Bisect cleanly through polygons instead of deleting whole rows of faces.
for ob in [body,shirt]:
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
        dist=.00001,plane_co=(0,0,-.44),plane_no=(0,0,1),clear_inner=True)
    bm.to_mesh(ob.data);bm.free();ob.data.update()
hairmat=mat('Textured dark hair',(.03,.02,.018),.78)
hairtex=texture(hairmat,SRC/'optimized/hair.png',size=1024)
hairmat.node_tree.links.new(hairtex.outputs['Alpha'],hairmat.node_tree.nodes.get('Principled BSDF').inputs['Alpha'])
hairmat.surface_render_method='DITHERED'
texture(hairmat,SRC/'optimized/hair-normal.png',True,size=1024)
hair=proxy('Textured short hairstyle',SRC/'hair/short01/short01.obj',SRC/'hair/short01/short01.mhclo',hairmat,sub=1)
# Compress the covered top beneath the cap, retaining the fringe and sides.
for p in hair.data.vertices:
    x=p.co.x/.4;y=p.co.z/.4+3.7;z=-p.co.y/.4
    if y>8.29 and z<1.15:
        q=Vector((x/.753,(y-8.29)/.80,(z-.53)/1.068))
        if q.length>1:
            q.normalize();p.co=coord(Vector((q.x*.753,8.29+q.y*.80,.53+q.z*1.068)))
# Head pivot with blended neck weights; accessories follow the same skeleton.
bpy.ops.object.armature_add();rig=bpy.context.object;rig.name='PortraitRig'
bpy.ops.object.mode_set(mode='EDIT');root=rig.data.edit_bones[0];root.name='Root';root.head=(0,0,-1.8);root.tail=(0,0,-1.4)
head=rig.data.edit_bones.new('Head');head.head=coord(Vector((0,6.85,.22)));head.tail=head.head+Vector((0,0,.5));head.parent=root
bpy.ops.object.mode_set(mode='OBJECT')

def bind(obj,headonly=False):
    rootgrp=obj.vertex_groups.new(name='Root');headgrp=obj.vertex_groups.new(name='Head')
    for vert in obj.data.vertices:
        y=vert.co.z/.4+3.7
        # Blend only the neck. The entire facial surface, including the chin
        # and underside of the jaw, belongs rigidly to the head bone.
        front=-vert.co.y/.4
        head_start=6.80-.35*max(0,min(1,(front-.45)/.5))
        w=1 if headonly else max(0,min(1,(y-6.30)/(head_start-6.30)))
        if obj==shirt or obj.get('body_attachment',False):w=0
        w=w*w*(3-2*w)
        if w>0:headgrp.add([vert.index],w,'REPLACE')
        if w<1:rootgrp.add([vert.index],1-w,'REPLACE')
    mod=obj.modifiers.new('Head tracking rig','ARMATURE');mod.object=rig;obj.parent=rig
for obj in [body,eyes,brows,hair]:bind(obj,obj!=body)
bind(shirt)
# Original fitted cap and glasses, modeled in the same coordinate system as the head.
accessories=[]
def mesh_native(name,verts,fs,material):
    me=bpy.data.meshes.new(name);me.from_pydata([coord(Vector(p)) for p in verts],[],fs);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(material)
    for p in me.polygons:p.use_smooth=True
    accessories.append(ob);return ob

def curve(name,pts,r,material,closed=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=r*.4;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts):p.co=(*coord(Vector(co)),1)
    sp.use_cyclic_u=closed;ob=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(ob);ob.data.materials.append(material)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);accessories.append(ob);return ob
# A fitted six-panel baseball cap worn backward. The visor is behind the head;
# the rear opening, adjustment strap and buckle face the viewer.
cx,cy,cz=0,8.29,.53
rx,ry,rz=.77,.83,1.085
nr,ns=26,144
verts=[];fs=[]
def opening_height(a):
    d=math.atan2(math.sin(a-math.pi/2),math.cos(a-math.pi/2))
    return .35*math.sqrt(max(0,1-(d/.46)**2)) if abs(d)<.46 else 0
for r in range(nr+1):
    for i in range(ns):
        a=i/ns*math.tau
        phi=r/nr*math.acos(opening_height(a)/ry)
        panel=.0045*math.cos(a*6)*math.sin(phi)**2
        wrinkle=.003*math.sin(a*29)*math.exp(-((phi-1.40)/.15)**2)
        radial=math.sin(phi)+panel+wrinkle
        verts.append((rx*radial*math.cos(a),cy+ry*math.cos(phi),cz+rz*radial*math.sin(a)))
        if r:
            k=r*ns+i;last=r*ns+(i+1)%ns;fs.append((k,k-ns,last-ns,last))
crown=mesh_native('Backward baseball cap crown',verts,fs,capmat)
uvs=crown.data.uv_layers.new(name='Cotton weave')
for polygon in crown.data.polygons:
    columns=[crown.data.loops[i].vertex_index%ns for i in polygon.loop_indices]
    wrap=max(columns)-min(columns)>ns/2
    for li in polygon.loop_indices:
        vi=crown.data.loops[li].vertex_index;r,i=divmod(vi,ns)
        u=i/ns+(1 if wrap and i==0 else 0)
        uvs.data[li].uv=(u*24,r/nr*10)

solid=crown.modifiers.new('Cotton panel thickness','SOLIDIFY');solid.thickness=.009
bpy.context.view_layer.objects.active=crown;bpy.ops.object.modifier_apply(modifier=solid.name)
# Quiet, closely matched double stitching, rather than bright lines across the cap.
for k in range(6):
    a=k*math.tau/6
    for offset in [-.009,.009]:
        aa=a+offset;end=math.acos(opening_height(aa)/ry);pts=[]
        for j in range(2,30):
            p=j/29*end
            pts.append(((rx+.004)*math.sin(p)*math.cos(aa),cy+(ry+.004)*math.cos(p),cz+(rz+.004)*math.sin(p)*math.sin(aa)))
        curve('Tonal panel stitching',pts,.0035,seammat)
# The opening follows a smooth arch; the fabric band is continuous around the back.
edge=[]
for i in range(ns):
    a=i/ns*math.tau;phi=math.acos(opening_height(a)/ry)
    edge.append(((rx+.003)*math.sin(phi)*math.cos(a),cy+opening_height(a),cz+(rz+.003)*math.sin(phi)*math.sin(a)))
curve('Bound adjustment opening',edge,.018,capmat,True)
# Rear-facing visor follows the cap's elliptical edge and has a gently curved tip.
verts=[];fs=[]
for j in range(9):
    t=j/8
    for i in range(49):
        u=-1+2*i/48;x=u*.77
        inner=rz*math.sqrt(max(0,1-(x/rx)**2))
        z=cz-inner-t*.80*math.sqrt(max(0,1-u*u))
        y=cy-.025-.08*t-.09*(1-u*u)*t
        verts.append((x,y,z))
        if i and j:
            k=j*49+i;fs.append((k,k-1,k-50,k-49))
brim=mesh_native('Rear baseball visor',verts,fs,capmat)
solid=brim.modifiers.new('Visor sandwich','SOLIDIFY');solid.thickness=.016
bpy.context.view_layer.objects.active=brim;bpy.ops.object.modifier_apply(modifier=solid.name)
for t in [.83,.94]:
    pts=[]
    for i in range(1,48):
        u=-1+2*i/48;x=u*.77;inner=rz*math.sqrt(max(0,1-(x/rx)**2))
        pts.append((x,cy-.019-.08*t-.09*(1-u*u)*t,cz-inner-t*.80*math.sqrt(max(0,1-u*u))))
    curve('Visor stitch',pts,.003,seammat)
# Fabric adjustment strap across the forehead, with a small metal slide buckle.
strap=[]
for y in [cy+.015,cy+.095]:
    for i in range(25):
        x=-.365+i/24*.73;z=cz+rz*math.sqrt(1-(x/rx)**2)+.018
        strap.append((x,y,z))
mesh_native('Back adjustment strap',strap,[(i,i+1,i+26,i+25) for i in range(24)],capmat)
for yy in [cy+.025,cy+.085]:
    curve('Strap edge stitching',[(x,yy,cz+rz*math.sqrt(1-(x/rx)**2)+.023) for x in [-.34+i*.68/30 for i in range(31)]],.003,seammat)
buckle_x=-.225;buckle_z=cz+rz*math.sqrt(1-(buckle_x/rx)**2)+.028
curve('Adjustment buckle',[(buckle_x-.045,cy+.005,buckle_z),(buckle_x+.045,cy+.005,buckle_z),(buckle_x+.045,cy+.105,buckle_z),(buckle_x-.045,cy+.105,buckle_z)],.009,hardware,True)
# Small covered button on the crown.
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=coord(Vector((0,cy+ry+.015,cz))))
button=bpy.context.object;button.name='Covered crown button';button.scale=(.027,.027,.014);button.data.materials.append(capmat)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
for poly in button.data.polygons:poly.use_smooth=True
accessories.append(button)
# Tip the backward cap slightly toward the nape to reveal the swept front.
cap_pivot=coord(Vector((0,8.29,.53)))
cap_tilt=Matrix.Translation(cap_pivot)@Matrix.Rotation(-.34,4,'X')@Matrix.Translation(-cap_pivot)
for ob in accessories:
    for vertex in ob.data.vertices:vertex.co=cap_tilt@vertex.co
# Let the swept front sit below the raised band while the crown contains the top.
for vertex in hair.data.vertices:
    y=vertex.co.z/.4+3.7;z=-vertex.co.y/.4
    if z>1.0:
        fringe=math.exp(-((y-8.42)/.34)**2)*min(1,(z-1.0)/.35)
        vertex.co.z-=.045*fringe
        vertex.co.y-=.035*fringe
# Polo construction: folded collar, collar stand, and a short three-button placket.
from mathutils.bvhtree import BVHTree
surface=BVHTree.FromObject(shirt,bpy.context.evaluated_depsgraph_get())
collar_mat=mat('Polo collar knit',(.22,.40,.56),.94)
placket_mat=mat('Polo placket',(.19,.36,.51),.93)
button_mat=mat('Polo mother of pearl buttons',(.68,.76,.80),.36)
def front_surface(x,y,z):
    hit,normal,index,dist=surface.ray_cast(Vector((x*.4,-5,(y-3.7)*.4)),Vector((0,1,0)))
    return max(z,-hit.y/.4+.035) if hit else z

def garment(ob):ob['body_attachment']=True;return ob
# One continuous folded knit collar wraps the neck and lies against the shoulders.
# The front ends taper toward the open placket, with a soft rolled fold.
vertices=[];quads=[];steps=96;rows=8
for row in range(rows+1):
    t=row/rows
    for i in range(steps+1):
        u=i/steps;a=.20+u*(math.tau-.40)
        outer_a=.52+u*(math.tau-1.04)
        inner=Vector((.63*math.sin(a),6.38-.16*max(0,math.cos(a))**4,.18+.77*math.cos(a)))
        outer=Vector((.88*math.sin(outer_a),6.10-.32*max(0,math.cos(a))**5,.18+1.23*math.cos(outer_a)))
        q=inner.lerp(outer,t)
        if q.z>.65:q.z=front_surface(q.x,q.y,q.z)
        q.y+=.055*math.sin(math.pi*t)
        vertices.append(tuple(q))
        if row and i:
            k=row*(steps+1)+i;quads.append((k,k-1,k-steps-2,k-steps-1))
collar=garment(mesh_native('Folded polo collar',vertices,quads,collar_mat))
solid=collar.modifiers.new('Soft knit thickness','SOLIDIFY');solid.thickness=.003
bpy.context.view_layer.objects.active=collar;bpy.ops.object.modifier_apply(modifier=solid.name)
# Placket follows the actual draped shirt, avoiding a floating button strip.
vertices=[];quads=[]
for row in range(25):
    y=6.02-row/24*1.10
    for x in [-.08,.08]:vertices.append((x,y,front_surface(x,y,1.10)+.008))
    if row:k=row*2;quads.append((k,k+1,k-1,k-2))
garment(mesh_native('Polo button placket',vertices,quads,placket_mat))
for y in [5.80,5.45,5.10]:
    z=front_surface(0,y,1.10)+.037
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=coord(Vector((0,y,z))))
    ob=bpy.context.object;ob.name='Polo button';ob.scale=(.013,.006,.013);ob.data.materials.append(button_mat)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);accessories.append(garment(ob))

# Light metal rectangular sunglasses with physically curved smoked lenses.

for side in [-1,1]:
    ex=side*.34;ey=7.89;ez=1.58;pts=[]
    for i in range(96):
        a=i*math.tau/96
        x=math.copysign(abs(math.cos(a))**.55,math.cos(a))*.285*(1+.08*math.sin(a))
        y=math.copysign(abs(math.sin(a))**.55,math.sin(a))*.168
        pts.append((ex+x,ey+y,ez-abs(x)*.12))
    curve('Thin metal sunglasses rim',pts,.011,frame,True)
    # A gently convex optical surface gives continuous softbox reflections.
    vv=[(ex,ey,ez+.015)];ff=[];segments=len(pts);rings=12
    for ring in range(1,rings+1):
        r=ring/rings
        for x,y,z in pts:
            vv.append((ex+(x-ex)*r,ey+(y-ey)*r,ez-.018+(z-ez)*r+.033*(1-r*r)))
    for i in range(segments):ff.append((0,1+i,1+(i+1)%segments))
    for ring in range(1,rings):
        for i in range(segments):
            a=1+(ring-1)*segments+i;b=1+(ring-1)*segments+(i+1)%segments
            ff.append((a,a+segments,b+segments,b))
    glass=mesh_native('Curved smoked optical lens',vv,ff,lens)
    curve('Sunglasses temple',[(side*.68,ey+.07,1.54),(side*.81,ey+.06,1.17),(side*.84,ey,.36),(side*.80,ey-.10,.28)],.010,frame)
    curve('Temple pin',[(side*.66,ey+.10,1.562),(side*.69,ey+.10,1.55)],.007,hardware)
curve('Sunglasses bridge',[(-.055,7.97,1.58),(0,8.00,1.66),(.055,7.97,1.58)],.012,frame)
for obj in accessories:bind(obj,not obj.get('body_attachment',False))
# Studio lighting for source-file rendering; lights are not exported to the website.
world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.045,.04,.065,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45

def area(name,loc,power,color,size):
    bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.name=name;ob.data.energy=power;ob.data.color=color;ob.data.shape='DISK';ob.data.size=size;ob.rotation_euler=(Vector((0,0,.6))-ob.location).to_track_quat('-Z','Y').to_euler()
area('Warm key',(-3,-5,5),500,(1,.88,.78),4)
area('Soft fill',(3,-3,2),300,(.75,.81,1),4)
area('Lavender rim',(2,2,3),650,(.65,.48,1),3)
bpy.ops.object.camera_add(location=(0,-9,.87));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.87))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.9;bpy.context.scene.camera=cam
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
# Export only the posed, clothed portrait and its head rig.
bpy.ops.object.select_all(action='DESELECT')
for ob in [rig,body,shirt,eyes,brows,hair]+accessories:ob.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(OUT/'portrait.glb'),export_format='GLB',use_selection=True,export_animations=False,export_image_format='AUTO',export_yup=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'tools/portrait.blend'))
scene.render.filepath=str(OUT/'blender-preview.png');bpy.ops.render.render(write_still=True)
print('Portrait exported and rendered')
