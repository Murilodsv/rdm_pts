#----------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------- RANDOM POINTS -----------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------

#--- Description:
#----       After the zoning process for VR customers, Precision Agronomists (PA) in Brazil needs 
#----       to define the number of samples and their corresponding locations for each zone, which 
#----       in turn, will be used to drive the soil sampler in the field aided by an GPS and the points map.
#----       Nowadays (Jul-2018), the points creation is done manually taking a considerable time of PAs
#----       with the increasing new customers areas for VR. Therefore, to increase the work efficiency,
#----       reduce subjectivity and possible human errors an algorithm is proposed to create the points
#----       for each zone automatically.

#--- Goal:
#----       Place "n" number of points randomly within the FarmersEdge Zoning Areas

#--- Usage:
#----       Run the zoning on the PrecisionEdge application
#----       Rename the shapefiles for the pattern you are working (e. g. 'BRA_SUGARCANE_RAIZEN_FARM1_T01_2018JUL16.shp')
#----       Place all the zoning shapefiles in the same directory (e.g. 'C:/FarmersEdge/Zoning')
#----       Setup how the sampling points algorithm will be performed by changing the below variables:
#----           wd_z:               Working directory where all zonning shapefiles are placed (WARNING: only place zoning shapefiles and all shapes MUST the have the ZoneID)
#----           wd_p:               Working directory where the points will be saved by the algorithm (we recommended to be different from the wd_z)
#----           init_buf:           Initial distance from zone area border [meters] to avoid the "border effect" (points will not fall within this distance from the border)
#----           red_t:              Is the zone area reduction threshold [0-1] (e.g. red_t = 0.75: if the init_buf reduce the original zone area to more than 25%, a lower distance is used)
#----           min_buf:            Is the minimum distance from zone area border [meters] after the reduction due to red_t
#----           n_points_zone:      Fixed number of points that will be randomly placed in each zone
#----           pdist_red:          Final reduction on distance among points [0-1]
#----           p_min_dist:         Minimum distance among points [meters] (If the zone area is too small, the number of points will reduced to fit the p_min_dist)
#----           T_ID:               Is the number index of where the field name is in the shapefile name (e.g. for file 'BRA_SUGARCANE_RAIZEN_FARM1_T01_2018JUL16.shp' the T_ID = 5)
#----           utm_code:           Is the UTM projection code in QGIS (e.g. 'EPSG:32722' = UTM_22_S; 'EPSG:4326' = WGS84)
#----       After Setting up parameters press 'Run Script'

#--- Contact:
#--- Murilo Vianna   (murilo.vianna@farmersedge.ca)
#--- Murillo Grespan (murillo.grespan@farmersedge.ca)
#--------------------------------------------------------------------------------------------------------------------------------------

#--- RANDOM POINTS SETUP

#--- Working directories:
wd_z                = "C:/Murilo/GIS/Zoning/batatais"			#All zoning shapefiles dir
wd_p                = "C:/Murilo/GIS/Zoning/Sampling Points"			#Sampling points directory

#--- Parameters:
init_buf            = 10                    #[METERS]
red_t               = 0.75                  #[0-1]
min_buf             = 0.5                   #[METERS]
n_points_zone       = 15                    #[#]
pdist_red           = 0.5                   #[0-1]
p_min_dist          = 10                    #[METERS]
T_ID                = 5                     #[#]
utm_code            = 'EPSG:32722'          #[Projection Code]

#--- Ready to Run? 
#--- Please press 'Run Script'
#-----------------------------------------------------------------------------------------------------------------------------------------












#------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
#---- RANDOM POINTS SOURCE CODE
#---- WARNING: DO NOT CHANGE WITHOUT HAVING PYTHON BACKGROUND
#---- FOR ANY QUESTION, ERRORS, SUGESTIONS OR BUGS PLEASE CONTACT: murilo.vianna@farmersedge.ca
#-------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------

#--- Load modules
import os, gc, ogr, processing,math,subprocess,sys

#--- Check parameters
wrong_par = False
msg = ''
if not os.path.isdir(wd_z):
    msg = 'Zoning directory do not exist. Please check directory folder path (wd_z)'
    wrong_par = True

if not os.path.isdir(wd_p):
    msg = 'Random points directory do not exist. Please check directory folder path (wd_p)'
    wrong_par = True

#--- functions:
def UIerrorSwitch(supress_win_promp):
    filename_reg = wd_p+'/'+'UIon_off.reg'
    file_reg = open(filename_reg,"w")
    file_reg.write('Windows Registry Editor Version 5.00\n')
    file_reg.write('[HKEY_CURRENT_USER\Software\Microsoft\Windows\Windows Error Reporting]\n')
    if supress_win_promp:
        file_reg.write(('"%s"' % 'DontShowUI')+'=dword:00000001')
    else:
        file_reg.write(('"%s"' % 'DontShowUI')+'=dword:00000000')
    file_reg.close()
    subprocess.call(['reg', 'import', filename_reg])
    os.remove(filename_reg)
    return

#--- list of all zoning shapefiles within (wd_z)
input_zon = []
filename = []
for  r, d, f in os.walk(wd_z):
    for file in f:
        if file[len(file)-4:len(file)] == ".shp":
            input_zon.append(os.path.join(r,file))
            filename.append(os.path.join(file))

if wrong_par:
    print('----------------------------------------------------------------------------')
    print('WRONG PARAMETERS ERROR:')
    print(msg)
    print('----------------------------------------------------------------------------')

for shp in range(0,len(input_zon)):
    print('--------------------------------------------------------------------------------------------')
    print('Running Random Points for '+filename[shp])
    log_msg = ''
    loc = input_zon[shp]
    lnm= filename[shp]
    
    #--- Read shapefile internaly
    vlayer = QgsVectorLayer(loc, lnm,"ogr")
    
    #--- Read shapefile attribute table
    zones           = []
    zones_area   = []
    poly_area      = []
    field_id          = []
    field_op  = []
    
    for feature in vlayer.getFeatures():
        zones.append(feature["ZoneID"])
        zones_area.append(feature["ZoneArea"])
        poly_area.append(feature["PolyArea"])
        field_id.append(feature["FieldID"])
        field_op.append(feature["FieldOpID"])
    
    #--- check size
    nfeatures = len(zones)
    if nfeatures == 0:
        print("No Zones attributes in "+ filename[shp] + " (Skipped to next).")
        continue
    
    #--- Unique zones
    unique_zones = set(zones)
    print(filename[shp]+' has '+str(len(unique_zones))+' Zones')
    
    #------ loop over zones
    for zn in unique_zones:
        skip_zone = False
        #--- Select Zone 1 f(ZoneID)
        #--- add to object
        print('Running Random Points in Zone '+str(zn))
        z_lyr =QgsVectorLayer(processing.runalg("qgis:extractbyattribute",      #Algorithm
        vlayer,                                             #Input Zone
        "ZoneID",											    #Field
        0,
        zn,
        None)['OUTPUT'], ('zon_'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- Separate single polygons to multipolygons (To correct geometries)
        z_lyr_mpsp =QgsVectorLayer(processing.runalg("qgis:multiparttosingleparts",      #Algorithm
        z_lyr,
        None)['OUTPUT'], ('zon_mpsp'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- Buffer with distance = 0 to correct geometries
        #--- Refer to https://anitagraser.com/2017/08/29/fixing-invalid-polygon-geometries/
        z_lyr_corr =QgsVectorLayer(processing.runalg("gdalogr:buffervectors",      #Algorithm
        z_lyr_mpsp,
        'geometry',
        0.0,
        0,
        None,
        0,
        None,
        None)['OUTPUT_LAYER'],('zon_corr'+str(zn)+'_'+filename[shp]),"ogr")
        
        z_lyr_smo = QgsVectorLayer(processing.runalg("qgis:smoothgeometry",      #Algorithm
        z_lyr_corr,
        1,
        0.25,
        None)['OUTPUT_LAYER'],('zon_smo_'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- Recompute polyarea
        formula = "area(transform($geometry,'EPSG:4326','"+utm_code+"')) * 0.000247105"
        z_lyr_cor_pa = QgsVectorLayer(processing.runalg("qgis:fieldcalculator",
        z_lyr_smo,
        'PolyArea',
        0,
        15,
        2,
        0,
        formula, #IN ACRES
        None)['OUTPUT_LAYER'], ('zon_polyarea'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- recompute ZoneArea (needed because correction may created/deleted polygons)
        z_lyr_cor_za = QgsVectorLayer(processing.runalg("qgis:fieldcalculator",
        z_lyr_cor_pa,
        'ZoneArea',
        0,
        15,
        2,
        0,
        'sum( "PolyArea")', #IN ACRES
        None)['OUTPUT_LAYER'], ('zon_zonearea'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- Read shapefile zonearea
        zones_area   = []
        for feature in z_lyr_cor_za.getFeatures():
            zones_area.append(feature["ZoneArea"])
        z_area = zones_area[0]
        
        #--- check if the zonning area has signinficant size
        print('Zone '+str(zn)+' Area: '+str(round(z_area,2))+' Acres')
        if z_area < 0.00001:
            print('Area of Zone '+str(zn)+ ' is lower than 1 square meter')
            print('Skipping Zone'+str(zn)+ ' for file '+filename[shp])
            log_msg = 'Skipped Zone'+str(zn)+ ' for file '+filename[shp]
            continue
        
        #--- reproject vector to UTM
        z_lyr_utm = QgsVectorLayer(processing.runalg("qgis:reprojectlayer",
        z_lyr_cor_za,
        utm_code,
        None)['OUTPUT'],('zon_utm_'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- try the first inner buffer with initial distance
        distbuf = init_buf
        file_exist = False
        
        #--- Reduce buffer distance if "saga:shapesbufferfixeddistance" fails
        ##TRY TO MAKE THIS AN ERROR OR SUPPRESS WINDOWS ERROR
        while not file_exist:
            UIerrorSwitch(True)
            outnm_del = 'init_buf_'+str(round(distbuf,2))+'_Zone_'+str(zn)+'_'+filename[shp]
            init_buf_str = processing.runalg("saga:shapesbufferfixeddistance",
            z_lyr_utm,
            distbuf,
            1,
            5,
            0,
            1,
            None)['BUFFER']
            UIerrorSwitch(False)
            #--- Check whether the file was created
            z_lyr_buf_1 = QgsVectorLayer(init_buf_str, "BUFFER", "ogr")
            
            if z_lyr_buf_1.isValid():
                file_exist = True
            
            if not file_exist:
                distbuf = distbuf * 0.75 # reduce the inital buffer into 25% for this first assessment
                print('Initial Buffer distance is too high for this Zone')
                print('Buffer distance reduced to: '+str(round(distbuf,2))+' meters')
        
        print('Buffer distance used: '+str(round(distbuf,2))+' meters')
        
        #--- Separate single polygons to multipolygons (To correct geometries)
        z_lyr_buf1_mpsp =QgsVectorLayer(processing.runalg("qgis:multiparttosingleparts",      #Algorithm
        z_lyr_buf_1,
        None)['OUTPUT'], ('zon_buf1_mpsp'+str(zn)+'_'+filename[shp]),"ogr")
        
        z_lyr_buf_1_corr =QgsVectorLayer(processing.runalg("gdalogr:buffervectors",      #Algorithm
        z_lyr_buf1_mpsp,
        'geometry',
        0.0,
        0,
        None,
        0,
        None,
        None)['OUTPUT_LAYER'],('zon_buf1_corr'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- dissolve the result because some features might be ruled out
        z_lyr_buf_1_diss = QgsVectorLayer(processing.runalg("qgis:dissolve",
        z_lyr_buf_1_corr,
        1,
        'ZoneID',
        None)['OUTPUT'], ('zon_initbuf_dissolve_'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- Recompute polyArea (needed because correction may created/deleted polygons)
        z_lyr_buf_pa = QgsVectorLayer(processing.runalg("qgis:fieldcalculator",
        z_lyr_buf_1_diss,
        'PolyArea',
        0,
        15,
        4,
        1,
        "$area * 0.000247105", #IN ACRES
        None)['OUTPUT_LAYER'], ('zon_bf1_diss_pa_'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- Read buffer area
        buf_area   = []
        for feature in z_lyr_buf_pa.getFeatures():
            buf_area.append(feature["PolyArea"])
        buf_area = sum(buf_area)
        
        #--- Check If new area was not reduced more than red_threshold from original Zone area
        bufdif_area = max(0, z_area - buf_area)
        if distbuf == 0 or z_area == 0:
            print('Distance buffer or Zone area equal to zero, skiping this zone')
            skip_zone = True
            continue
        bf_rate = (z_area - bufdif_area) / (0 - distbuf)
        bf_fac = (bufdif_area / z_area)
        red_threshold = red_t
        print('New Reduced area is: '+str(round(bufdif_area,2))+' Acres')
        n_it = 0
        while(round(bf_fac,2) < red_threshold):
            #--- Reduce buffer distance
            distbuf = -(z_area * (1-red_threshold)) / bf_rate
            
            if(distbuf < min_buf):
                if n_it == 0:
                    #--- This zone is too small
                    print('Zone '+str(zn)+' is too small: Skipped!')
                    skip_zone = True
                    break
                
                print('Minimum buffer distance reached ('+str(min_buf)+'m): Proceed to Random Points')
                log_msg = 'Minimum buffer distance reached ('+str(min_buf)+'m) in Zone '+str(zn)+' file: '+filename[shp]
                distbuf = min_buf
                #--- Buffer with reduced distance
                z_lyr_buf_it = QgsVectorLayer(processing.runalg("saga:shapesbufferfixeddistance",
                z_lyr_utm,
                distbuf,
                1,
                5,
                0,
                1,
                None)['BUFFER'], ('zon_buf2_reduced_to_'+str(round(distbuf,2))+'_Zone_'+str(zn)+'_'+filename[shp]),"ogr")
                
                #--- Separate single polygons to multipolygons (To correct geometries)
                z_lyr_buf_it_mpsp =QgsVectorLayer(processing.runalg("qgis:multiparttosingleparts",      #Algorithm
                z_lyr_buf_it,
                None)['OUTPUT'], ('zon_buf_it_mpsp'+str(zn)+'_'+filename[shp]),"ogr")
                
                z_lyr_buf_it_corr =QgsVectorLayer(processing.runalg("gdalogr:buffervectors",      #Algorithm
                z_lyr_buf_it_mpsp,
                'geometry',
                0.0,
                0,
                None,
                0,
                None,
                None)['OUTPUT_LAYER'],('zon_buf1_corr'+str(zn)+'_'+filename[shp]),"ogr")
                
                #--- dissolve the result because some features might be ruled out
                z_lyr_buf_it_diss = QgsVectorLayer(processing.runalg("qgis:dissolve",
                z_lyr_buf_it_corr,
                1,
                'ZoneID',
                None)['OUTPUT'], ('zon_initbuf_dissolve_'+str(zn)+'_'+filename[shp]),"ogr")
                
                #--- recompute polyArea (needed because correction may created/deleted polygons)
                z_lyr_buf_pa = QgsVectorLayer(processing.runalg("qgis:fieldcalculator",
                z_lyr_buf_it_diss,
                'PolyArea',
                0,
                15,
                4,
                1,
                "$area * 0.000247105", #IN ACRES
                None)['OUTPUT_LAYER'], ('zon_parea_reduced_to_'+str(round(distbuf,2))+'_Zone_'+str(zn)+'_'+filename[shp]),"ogr")
                
                #--- Read difference area
                buf_area   = []
                for feature in z_lyr_buf_pa.getFeatures():
                    buf_area.append(feature["PolyArea"])
                buf_area = sum(buf_area)
                bufdif_area = max(0, z_area - buf_area)
                if distbuf == 0 or z_area == 0:
                    print('Distance buffer or Zone area equal to zero, skiping this zone')
                    skip_zone = True
                    continue
                bf_rate = (z_area - bufdif_area) / (0 - distbuf)
                bf_fac = (bufdif_area / z_area)                
                break
            
            #--- Buffer with reduced distance
            z_lyr_buf_it = QgsVectorLayer(processing.runalg("saga:shapesbufferfixeddistance",
            z_lyr_utm,
            round(distbuf,2),
            1,
            5,
            0,
            1,
            None)['BUFFER'], ('zon_buf2_reduced_to_'+str(round(distbuf,2))+'_Zone_'+str(zn)+'_'+filename[shp]),"ogr")
            
            #--- Separate single polygons to multipolygons (To correct geometries)
            z_lyr_buf_it_mpsp =QgsVectorLayer(processing.runalg("qgis:multiparttosingleparts",      #Algorithm
            z_lyr_buf_it,
            None)['OUTPUT'], ('zon_buf_it_mpsp'+str(zn)+'_'+filename[shp]),"ogr")
            
            z_lyr_buf_it_corr =QgsVectorLayer(processing.runalg("gdalogr:buffervectors",      #Algorithm
            z_lyr_buf_it_mpsp,
            'geometry',
            0.0,
            0,
            None,
            0,
            None,
            None)['OUTPUT_LAYER'],('zon_buf1_corr'+str(zn)+'_'+filename[shp]),"ogr")
            
            #--- dissolve the result because some features might be ruled out
            z_lyr_buf_it_diss = QgsVectorLayer(processing.runalg("qgis:dissolve",
            z_lyr_buf_it_corr,
            1,
            'ZoneID',
            None)['OUTPUT'], ('zon_initbuf_dissolve_'+str(zn)+'_'+filename[shp]),"ogr")
            
            #--- recompute polyArea (needed because correction may created/deleted polygons)
            z_lyr_buf_pa = QgsVectorLayer(processing.runalg("qgis:fieldcalculator",
            z_lyr_buf_it_diss,
            'PolyArea',
            0,
            15,
            4,
            1,
            "$area * 0.000247105", #IN ACRES
            None)['OUTPUT_LAYER'], ('zon_parea_reduced_to_'+str(round(distbuf,2))+'_Zone_'+str(zn)+'_'+filename[shp]),"ogr")
            
            #--- Read difference area
            buf_area   = []
            for feature in z_lyr_buf_pa.getFeatures():
                buf_area.append(feature["PolyArea"])
            buf_area = sum(buf_area)
            bufdif_area = max(0, z_area - buf_area)
            
            print('Area reduced to more than ' +str(round((1.-red_threshold)*100,1))+ '% of original Zone Area ')
            print('Distance Buffer Reduced to:'+str(round(distbuf,2))+' meters')
            print('New Reduced area is: '+str(round(bufdif_area,2))+' Acres')
            print('Target is:'+str(round(z_area * red_threshold,2))+' Acres')
            if distbuf == 0 or z_area == 0:
                print('Distance buffer or Zone area equal to zero, skiping this zone')
                skip_zone = True
                continue
            bf_rate = (z_area - bufdif_area) / (0 - distbuf)
            bf_fac = (bufdif_area / z_area)
            n_it = n_it + 1
        
        if skip_zone:
            #---skip to next zone
            continue
        print('Buffer distance used: '+str(round(distbuf,2))+' meters')
        #--- Compute the difference between buffer and original vector (Not necessary)
        buf_dif = QgsVectorLayer(processing.runalg("qgis:difference",
        z_lyr_utm,
        z_lyr_buf_pa,
        1,        
        None)['OUTPUT'], ('zon_reduced_shp_Zone_'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- Separate single polygons to multipolygons (To correct any geometries)
        buf_dif_mpsp =QgsVectorLayer(processing.runalg("qgis:multiparttosingleparts",      #Algorithm
        buf_dif,
        None)['OUTPUT'], ('buf_dif_mpsp'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- Buffer with distance = 0 to correct geometries
        #--- Refer to https://anitagraser.com/2017/08/29/fixing-invalid-polygon-geometries/
        buf_dif_corr =QgsVectorLayer(processing.runalg("gdalogr:buffervectors",      #Algorithm
        buf_dif_mpsp,
        'geometry',
        0.0,
        0,
        None,
        0,
        None,
        None)['OUTPUT_LAYER'],('buf_dif_corr'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- dissolve the result to points be included only in a single feature and not by polygon
        buf_dif_diss = QgsVectorLayer(processing.runalg("qgis:dissolve",
        buf_dif_corr,
        1,
        'ZoneID',
        None)['OUTPUT'], ('buf_dif_dissolve_'+str(zn)+'_'+filename[shp]),"ogr")
        
        #--- run the random points for this reduced zone
        #--- Estimate an initial distance among points
        ext = buf_dif_diss.extent()
        x_dist = ext.xMaximum() - ext.xMinimum()
        y_dist = ext.yMaximum() - ext.yMinimum()
        
        if y_dist == 0 or x_dist == 0:
            print('Zone '+str(zn)+' is too small, skipping to next Zone')
            print('Zone '+str(zn)+' of file '+filename[shp]+' has no points')
            continue
        
        px = math.ceil(math.sqrt(n_points_zone*x_dist/y_dist))
        if math.floor(px*y_dist/x_dist)*px < n_points_zone:
            sx = y_dist/math.ceil(px*y_dist/x_dist)
        else:
            sx = x_dist/px
        
        py = math.ceil(math.sqrt(n_points_zone*y_dist/x_dist))
        if math.floor(py*x_dist/y_dist)*py < n_points_zone:
            sy = x_dist/math.ceil(x_dist*py/y_dist)
        else:
            sy = y_dist/py
        
        #--- Estimated poitns distance
        dist_init = max(sx,sy)
        fixed_npoints = True
        npoints = n_points_zone
        pdist = dist_init
        rp_try_red = 5
        if fixed_npoints:
            npoints_zn = 0
            rp_try = 0
            r_points_z = QgsVectorLayer(processing.runalg("qgis:randompointsinsidepolygonsfixed",
            buf_dif_diss,
            0,
            npoints,
            pdist,
            None)['OUTPUT'], ('rpoints'+str(zn)+'_try'+str(rp_try)+'_dist_'+str(pdist)+filename[shp]),"ogr")
            
            npoints_zn   = []
            for feature in r_points_z.getFeatures():
                npoints_zn.append(feature["id"])
            npoints_zn = len(npoints_zn)
            
            force_rep = False
            while(npoints_zn < npoints):
                if force_rep:
                    pdist = pdist
                    print('Points distance reduced to minimum: '+str(round(pdist,1))+' meters')
                    rp_try = rp_try + 1                    
                    if rp_try > rp_try_red:
                        print('Number of points was reduced to '+str(npoints_zn)+' to fit in zone area')
                        break 
                    print('Retry fitting '+str(rp_try)+'/'+str(rp_try_red))
                else:
                    pdist = pdist * 0.80
                    print('Points distance reduced to: '+str(round(pdist,1))+' meters')                
                if pdist < p_min_dist:
                    print('Distance between points lower than minimum: '+str(p_min_dist)+' meters')
                    pdist = p_min_dist
                    force_rep = True
                r_points_z = QgsVectorLayer(processing.runalg("qgis:randompointsinsidepolygonsfixed",
                buf_dif_diss,
                0,
                npoints,
                pdist,
                None)['OUTPUT'], ('rpoints'+str(zn)+'_try'+str(rp_try)+'_dist_'+str(pdist)+filename[shp]),"ogr")
                
                npoints_zn   = []
                for feature in r_points_z.getFeatures():
                    npoints_zn.append(feature["id"])
                npoints_zn = len(npoints_zn)
            #else:
                #implemented variable number of points per layer (points density npoints/acres)
        
        #Reduce the points distance to better distribute on polygon area
        pdist = max(pdist * pdist_red,p_min_dist)
        r_points_z = QgsVectorLayer(processing.runalg("qgis:randompointsinsidepolygonsfixed",
        buf_dif_diss,
        0,
        npoints,
        pdist,
        None)['OUTPUT'], ('rpoints'+str(zn)+'_try'+str(rp_try)+'_dist_'+str(pdist)+filename[shp]),"ogr")
        npoints_zn   = []
        for feature in r_points_z.getFeatures():
            npoints_zn.append(feature["id"])
        npoints_zn = len(npoints_zn)
        print('Final points distance is: '+str(round(pdist,1))+' meters')
        
        rp_try = 0
        rp_try_red = 5
        while(npoints_zn < npoints):
            if rp_try > rp_try_red:
                print('Number of points was reduced to: '+str(npoints_zn))
                break
            print('Trying to fit points with final distance: '+str(round(pdist,1))+' meters')
            print('Attempt '+str(rp_try)+'/'+str(rp_try_red))
            r_points_z = QgsVectorLayer(processing.runalg("qgis:randompointsinsidepolygonsfixed",
            buf_dif_diss,
            0,
            npoints,
            pdist,
            None)['OUTPUT'], ('rpoints'+str(zn)+'_try'+str(rp_try)+'_dist_'+str(pdist)+filename[shp]),"ogr")
            npoints_zn   = []
            for feature in r_points_z.getFeatures():
                npoints_zn.append(feature["id"])
            npoints_zn = len(npoints_zn)
            rp_try = rp_try + 1
        
        #--- reproject points back to WGS84 
        r_points_z_WGS84 = QgsVectorLayer(processing.runalg("qgis:reprojectlayer",
        r_points_z,###################################################WARNING
        'EPSG:4326',
        None)['OUTPUT'], ('rpoints'+str(zn)+'_WGS84_'+filename[shp]),"ogr")
        
        #--- Sample ID
        t = filename[shp].split('_')[T_ID]
        formula = "concat('"+t+"','_Z"+str(zn)+"')"
        r_pts_samp_id = QgsVectorLayer(processing.runalg("qgis:fieldcalculator",
        r_points_z_WGS84,
        'Sample_ID',
        2,
        10,
        0,
        1,
        formula,
        None)['OUTPUT_LAYER'], ('rpoints_sid_'+str(zn)+'_WGS84_'+filename[shp]),"ogr")
        
        #--- retrieve lat/lon        
        r_points_zn_xc = QgsVectorLayer(processing.runalg("qgis:fieldcalculator",
        r_pts_samp_id,
        'Lat',
        0,
        15,
        7,
        1,
        "$y", #IN ACRES
        None)['OUTPUT_LAYER'], ('rpoints_lat'+str(zn)+'_WGS84_'+filename[shp]),"ogr")
        r_points_zn_xc = QgsVectorLayer(processing.runalg("qgis:fieldcalculator",
        r_points_zn_xc,
        'Lon',
        0,
        15,
        7,
        1,
        "$x", #IN ACRES
        None)['OUTPUT_LAYER'], ('rpoints_lon'+str(zn)+'_WGS84_'+filename[shp]),"ogr")
        
        #--- Points ID
        formula = '"id" +1'
        r_points_pid = QgsVectorLayer(processing.runalg("qgis:fieldcalculator",
        r_points_zn_xc,
        'Point_ID',
        1,
        2,
        0,
        1,
        formula, #IN ACRES
        None)['OUTPUT_LAYER'], ('rpoints_pid_'+str(zn)+'_WGS84_att_xcoord'+filename[shp]),"ogr")
        r_points_zn = QgsVectorLayer(processing.runalg("qgis:deletecolumn",
        r_points_pid,
        'id',        
        None)['OUTPUT'], 'Zone_'+str(zn)+'_'+filename[shp].replace('.shp','')+'_PTS'+'.shp',"ogr")
        
        #--- Merge points to single shapefile
        if zn ==1:
            r_points = r_points_zn
        else:
            r_points = QgsVectorLayer(processing.runalg("qgis:mergevectorlayers",
            [r_points,r_points_zn],
            None)['OUTPUT'], filename[shp].replace('.shp','')+'_PTS'+'.shp',"ogr")
    
    #--- Write Random points as filename_PTS
    _writer = QgsVectorFileWriter.writeAsVectorFormat(r_points,wd_p+'/'+r_points.name(),"utf-8",None,"ESRI Shapefile")
    print('Random Points for '+filename[shp]+' is completed')
print('Random Points for all shapefiles are completed')
#-------------------------------------------------------------
