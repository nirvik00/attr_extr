import rhinoscriptsyntax as rs
import operator
import math
import random
import Nirvik_UI_Utility
import Rhino
import scriptcontext
import math
import Nirvik_UI_Utility
import System.Windows.Forms.DialogResult

class Main(object):
    
    def __init__(self):
        self.destroy()
        self.site_srf=rs.GetObjects("pick the topological surface")
        self.site_crvs=rs.GetObjects("pick the curves to subdivide")
        self.subdivX=rs.GetInteger("Enter X subdivisions : ",2, 1, 10)
        self.subdivY=rs.GetInteger("Enter Y subdivisions : ",2, 1, 10)
        self.attr_pts=rs.GetPoints("Pick attractor Points")
        
        
        rs.EnableRedraw(False)
        self.gen_crvs=[]
        self.gen_base_srfs=[]
        self.req_srf=[]
        self.type=[]
        self.num_grps=3

        ####    expensive   ####
        self.construct()
        ####   end construction   ####
        
        for i in self.gen_crvs:
            x=random.randint(0,10)
            if(x<3):
                self.type.append(1)
            elif(x>3 and x<7):
                self.type.append(2)
            else:
                self.type.append(3)
        
        #### GENERATE HT FUNCTION   ####
        try:
            self.attrObj()
        except:
            pass
        #### END FUNCTION   ####
        rs.EnableRedraw(True)
        rs.MessageBox("All Done")
        
    def attrObj(self):
        k=0
        for i in self.gen_base_srfs:
            if(self.type[k]==1):
                rs.ObjectColor(i,(255,255,100))
            elif(self.type[k]==2):
                rs.ObjectColor(i,(100,100,200))
                self.incHt(k)
            else:
                rs.ObjectColor(i,(255,100,100))
            k+=1
    
    def incHt(self, counter):
        pts=rs.CurvePoints(self.gen_crvs[counter])
        cen=rs.CurveAreaCentroid(self.gen_crvs[counter])[0]
        p0=pts[0]
        p1=pts[1]
        p2=pts[2]
        p3=pts[3]
        D=rs.Distance(p0,p3)
        d=0
        if(self.attr_pts==None):
            d=10
        else:
            for i in self.attr_pts:
                d+=(rs.Distance(i,cen))
                print(d)
        X=300*D/d
        print('ht : ' ,X)
        L=rs.AddLine([0,0,0],[0,0,X])
        srf=rs.ExtrudeCurve(self.gen_crvs[counter],L)
        f_srf=rs.CapPlanarHoles(srf)
        rs.ObjectColor(srf, (0,0,255))
        rs.ObjectLayer(srf,"output_geometry_srf")
        rs.DeleteObject(L)
        self.req_srf.append(srf)
    
    def construct(self):
        for i in self.site_crvs:
            rs.EnableRedraw(False)
            self.grp_crvs=self.subdivide(i)
            for j in self.grp_crvs:
                try:
                    self.constructTopoPoly(j)
                except:
                    rs.DeleteObjects(j)
            rs.EnableRedraw(True)
    
    def subdivide(self,poly):
        #subdivide the input poly into smaller poly grp_crvs
        pl_srf=rs.AddPlanarSrf(poly)
        srfUdom=rs.SurfaceDomain(pl_srf,0)
        srfVdom=rs.SurfaceDomain(pl_srf,1)
        umin=srfUdom[0]
        umax=srfUdom[1]
        ustep=(umax-umin)/self.subdivX
        vmin=srfVdom[0]
        vmax=srfVdom[1]
        vstep=(vmax-vmin)/self.subdivY
        req_poly_li=[]
        i=umin
        while(i<umax):
            j=vmin
            while(j<vmax):
                p0=rs.EvaluateSurface(pl_srf,i,j)
                p1=rs.EvaluateSurface(pl_srf,i+ustep,j)
                p2=rs.EvaluateSurface(pl_srf,i+ustep,j+vstep)
                p3=rs.EvaluateSurface(pl_srf,i,j+vstep)
                t0=rs.PointInPlanarClosedCurve(p0,poly)
                t1=rs.PointInPlanarClosedCurve(p1,poly)
                t2=rs.PointInPlanarClosedCurve(p2,poly)
                t3=rs.PointInPlanarClosedCurve(p3,poly)
                if(t0!=0 and t1!=0 and t2!=0 and t3!=0):
                    req_poly=rs.AddPolyline([p0,p1,p2,p3,p0])
                    rs.ObjectLayer(req_poly,"output_geometry_curves")
                    req_poly_li.append(req_poly)
                else:
                    this_poly=rs.AddPolyline([p0,p1,p2,p3,p0])
                    intx=rs.CurveBooleanIntersection(poly,this_poly)
                    rs.ObjectLayer(intx,"output_geometry_curves")
                    req_poly_li.append(intx)
                    rs.DeleteObject(this_poly)
                j+=vstep
            i+=ustep
        rs.DeleteObject(pl_srf)
        return req_poly_li
    
    def constructTopoPoly(self,poly):
        srf=self.site_srf
        poly_pts=rs.CurvePoints(poly)
        pts=poly_pts
        req_pts=[]
        req_pts_dup=[]
        for i in pts:
            pt2=rs.AddPoint([i[0],i[1],i[2]-1000])
            L=rs.AddLine(i,pt2)
            intx=rs.CurveSurfaceIntersection(L,srf)
            if(intx and len(intx)>0):
                pt=[intx[0][1][0],intx[0][1][1],intx[0][1][2]]
                rs.DeleteObject(L)
                rs.DeleteObject(pt2)
                req_pts.append([pt[0],pt[1],pt[2]])
                req_pts_dup.append([pt[0],pt[1],pt[2]])
            rs.DeleteObject(L)
            rs.DeleteObject(pt2)
        req_pts_dup.sort(key=operator.itemgetter(2))
        max_z=req_pts_dup[len(req_pts_dup)-1][2]+1# higher
        min_z=req_pts_dup[0][2]# higher
        high_pts=[]
        low_pts=[]
        for i in req_pts:
            high_pt=[i[0],i[1],max_z]
            high_pts.append(high_pt)
            low_pt=[i[0],i[1],min_z]
            low_pts.append(low_pt)
        high_pl=rs.AddPolyline(high_pts)
        low_pl=rs.AddPolyline(low_pts)
        this_srf=rs.AddLoftSrf([high_pl,low_pl])
        rs.DeleteObjects([low_pl,poly])
        f_srf=rs.CapPlanarHoles(this_srf)
        self.gen_base_srfs.append(this_srf)
        self.gen_crvs.append(high_pl)
        rs.ObjectLayer(this_srf,"output_geometry_srf")
        rs.ObjectLayer(high_pl,"output_geometry_curves")
        return high_pl
    
    def getGenCrvs(self):
        return self.gen_crvs
    
    def getGenBaseSrf(self):
        return self.gen_base_srfs
        
    def destroy(self):
        try:
            rs.DeleteObjects(self.gen_crvs)
        except:
            pass
        try:
            rs.DeleteObjects(self.gen_base_srfs)
        except:
            pass
        try:
            rs.DeleteObjects(self.req_srf)
        except:
            pass
        try:
            rs.DeleteObjects(rs.ObjectsByLayer("output_geometry_srf", True))
        except:
            pass
        try:
            rs.DeleteObjects(rs.ObjectsByLayer("output_geometry_curves",True))
        except:
            pass


rs.AddLayer("ns_boundary_curve")
rs.AddLayer("ns_topo_srf")
rs.AddLayer("output_geometry_srf")
rs.AddLayer("output_geometry_curves")

"""
global_poly_list=rs.GetObjects("pick the curves to subdivide")
global_topo_srf=rs.GetObjects("pick the topological surface")
global_attr_pt_li=rs.GetPoints("Pick attractor Points")
temp_global_intensity=rs.GetString("Enter the Intensity(number)")
"""


rs.Command('_SetDisplayMode _Shaded')

c=rs.GetString('Run Code ? (Y/N)','Y')
while(c=="Y" or c=="y"):
    try:
        rs.DeleteObjects(rs.ObjectsByLayer("output_geometry_srf", True))
    except:
        pass
    try:
        rs.DeleteObjects(rs.ObjectsByLayer("output_geometry_curves",True))
    except:
        pass
    m=Main()
    c=rs.GetString('Run Code ? (Y/N)','Y')
