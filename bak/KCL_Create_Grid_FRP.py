
#--------------------------------Import Libraries needed-----------------------------------

# import related library, if not installed, use 'pip install xxx' in a terminal to install them
import h5py,os,sys
import numpy as np
import pdb
import glob
import pandas as pd
import time

#--------------------------------End of Libraries---------------------------------------------


#--------------------------------Define Global Variables---------------------------------------------

# Define the scope of the mesh of interest, these variables can be read in from the configuration 
# file in the future so that
# each dataset can be processed different, if needed.
Start_lon = -20
End_lon = 50
Step_lon = 5
Start_lat = -45
End_lat = 45
Step_lat = 5

#define working dir
curr_workdir = '/notebooks/KCL_test'

#define list product file dir
list_product_dir = '/data'
list_product_dir = '/data_201606'

#define output file name
Grid_FRP_file = 'grid_FRP.csv'



#--------------------------------End of Global Variables---------------------------------------------


#-------------------------------------Define-Functions---------------------------------------------

# Get the data vale of channel dsname from an openned hdf5 file handle f
def get_h5_dataset(f, dsname):
    ds = dsname in f
    if ds:
        ds = f[dsname]
        d = ds[:]
        missing = ds.attrs.get("MISSING_VALUE")
        if missing is not None:
            mask = (d == missing)
        scale = ds.attrs.get("SCALING_FACTOR")
        offset = ds.attrs.get("OFFSET")
        
        #This uses the equation: real_value = Stored value /Scale_factor (10 for FRP)
        if (scale is not None) and (offset is not None):
            d = d/scale + offset
        if missing is not None:
            d[mask] = np.nan
        return d
    else:
        f.close()
        print('can not find dataset: %s in hdf5 file' % (dsname) )
        sys.exit('UNABLE_TO_PROCESS')

# Read Lon, Lat, FRP, etc from many FRP-PIXEL list product files
def read_lsasaf_h5(inputfiles):
    # define return data
    data = {}
    
    print( '-'*80)
    
    for f in inputfiles: 
        #parse the inputfile name to get the time and product type information
        path, filename = os.path.split(f)
        info = filename.split('_')
        #print(filename)
        t = info[5]  #time
        k = info[3]  #product type information
        
        #pdb.set_trace()
        
        try:
            # open a file and return a file handle fh
            fh = h5py.File(f, "r")
        except:
            print('not a valid hdf5 file:%s', sys.exit('INPUT_NOT_FOUND'))
        else:
            if k == 'FRP-PIXEL-ListProduct':
                ds = ['LONGITUDE', 'LATITUDE', 'FRP', 'ACQTIME', 'PIXEL_VZA', 'PIXEL_SIZE']
            elif k == 'FRP-PIXEL-QualityProduct':
                ds = ['QUALITYFLAG']
            elif k == 'FTA-FRP':
                ds = ['GFRP','LATITUDE','LONGITUDE']
            elif k == 'LAT' or k == 'LON':
                t='static'
                ds = [k]
            else:
                continue
                
            if t not in data:
                data[t] = {}
                
            for d in ds:
                # get the data in channel d (LATITUDE, LONGITUDE, FRP, etc)
                data[t][d] = get_h5_dataset(fh, d)
            fh.close()
            
    return data

# Create Grid mesh based on the grid boundaries
def CreateMesh(Start_lon, End_lon, Step_lon, Start_lat, End_lat, Step_lat):
    
    # Make sure the steps fit exactly in the lon/lat range
    if (End_lon - Start_lon) % Step_lon > 0 or (End_lat - Start_lat) % Step_lat > 0:
        return Lat, Lon
    
    range_lat = (int) ((End_lat - Start_lat)/Step_lat)
    range_lon = (int) ((End_lon - Start_lon)/Step_lon)
    
    Center_lon= []
    Center_lat= []
    Grid_FRP = []
    for i in range(range_lon):
        inner_lon=[]
        inner_lat=[]
        inner_FRP=[]
        for j in range(range_lat):
            tmp_lon = Start_lon + i*Step_lon + Step_lon/2.0
            tmp_lat = Start_lat + j*Step_lat + Step_lat/2.0
            tmp_FRP = 0.0
            inner_lon.append(tmp_lon)
            inner_lat.append(tmp_lat)
            inner_FRP.append(tmp_FRP)
        Center_lon.append(inner_lon)
        Center_lat.append(inner_lat)
        Grid_FRP.append(inner_FRP)
    return pd.DataFrame(Center_lon), pd.DataFrame(Center_lat), pd.DataFrame(Grid_FRP)

# create Grid FRP data
def CreateGridFRP(dt, files):
    
    C_lon, C_lat, Grid_FRP = CreateMesh(Start_lon, End_lon, Step_lon, Start_lat, End_lat, Step_lat)
   
    print('Starting to create Grid FRP file from pixel FRP list product files located in %s' % os.getcwd()+':\n' )
    
    for f in files:       
        #pdb.set_trace()
        MismatchedFRP = 0.0
        tmp_total_FRP = 0.0
        path, filename = os.path.split(f)
        info = filename.split('_')
        print(filename)
        t = info[5]  #time
        FRP= dt[t]['FRP']
        Lat= dt[t]['LATITUDE']
        Lon= dt[t]['LONGITUDE']
        Pixel_size = dt[t]['PIXEL_SIZE']        
        # place each fire pixel from the above List Product file into the correct 5-deg grid cell
        # and calculate the mean FRP of all fire pixels present in each grid cell
        for i in range(len(FRP)):
            #pdb.set_trace()
            if (Start_lon <= Lon[i] <= End_lon) and (Start_lat <= Lat[i] <= End_lon):       

                lon_loc = (int)((Lon[i]-Start_lon)/Step_lon)
                lat_loc = (int)((Lat[i]-Start_lat)/Step_lat)  
            
                # note that we only have one time-stamp FRP data, and the average of FRP over the grid area
                # has different physical meaning, which is FRP per unit area. so we do not average over area
                Grid_FRP.iloc[lon_loc][lat_loc] += FRP[i]
                tmp_total_FRP += FRP[i]
            else:
                MismatchedFRP += FRP[i]         
        print( "FRP error=%lf" % (sum(FRP) - tmp_total_FRP - MismatchedFRP ))
                   
    
    # Get the temporal average of grid FRP if there are HDF5 files from different time
    Grid_FRP = Grid_FRP / len(files)
    df_grid_data = pd.DataFrame(columns =['Lon','Lat','FRP'])
    df_grid_data['Lon']=C_lon.to_numpy().flatten()
    df_grid_data['Lat']=C_lat.to_numpy().flatten()
    df_grid_data['FRP']=Grid_FRP.to_numpy().flatten()
    
    return df_grid_data
    
# main body of creating Grid FRP data
def main():
    
    
    
    #step 1: get the files ready for processed
    
    data_dir = curr_workdir + list_product_dir    
    os.chdir(data_dir)    
    
    files = glob.glob("HDF5*")
    #print(files)
    
     
    #step 2: Read in the latitude, longitude and Fire Radiative Power (FRP) 
    # for each detected fire pixel present in the FRP Pixel List Product files  
        
    dt = read_lsasaf_h5(files)   
    
    start_time = time.time()
    
    #step 3: Create the grid FRP data from the pixel list product file
    df_grid_data = CreateGridFRP(dt, files)
    
    end_time = time.time()
    print('Time used to generate the grid RFP data:%s' % str(end_time - start_time) )
    
    #pdb.set_trace()
  
    #step 4: write Grid FRP data to dist file
    df_grid_data.to_csv(Grid_FRP_file, index=False)
    print( 'Grid data written to %s s' % os.getcwd()+'/'+Grid_FRP_file )
   
    
#-------------------------------End of Functions---------------------------------------------
    
    
#-------------------------------------Running the main function--------------------------

if __name__ == "__main__":
    main()
    
    
#-------------------------------------End of the Program--------------------------------
