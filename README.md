
This is to explain the files being submitted:

1.There are two sets of source code, one has the type of ipynb which can be opened in the jupyter notebook, 
  the other has the type of py which can be run from the (linux) terminal's command line, like:
       python ./*KCL_Create_Grid_FRP_py.py

2. In each set, the file '*KCL_Create_Grid_FRP*' is to create the Grid level FRP and Fire Count (FC) data based on the pixel level FRP 
list product data, the file '*KCL_plot_Grid_FRP*' is to plot and output the FRP and FC PNG files.

3. There are two sets of PNG files being generated, the one inculding '20160601' was generated from the list product file 
sent to me. Since there is only one list product file, the mean grid FRP (temporal average) does not make a lot 
of sense, and the area-weighted average of FRP in one grid leads to FRP per united area which is irrelated to this test. 
Moreover, To test if the code can process multi-files, I downloaded the whole June month's list product files and generate 
the other set of PNG files having '201606'. The switch to which set of PNG files can be made by changing the global variable
 'list_product_dir' and 'PNG_file_name' which are put at the beginning of each of the source code files.

4. The whole project is in github here: https://github.com/honggangwang1979/KCL_Test.git
   please use:
      git clone https://github.com/honggangwang1979/KCL_Test.git
   to clone it and run it.

   I will keep this repository public for 1 week.

5. Thank you!
