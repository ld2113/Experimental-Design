#!/bin/sh

module load python
source activate /cluster/home/jm2716/work/conda_enviroments/Python27_GPU_means

if [ $THISHOST == cuda10 ]
then
	export CUDA_DEVICE=1
fi

cd $GPUDIR/Main
#cd ~/work/Experimental-Design/Main

##gE1 (SBML input):
python main.py -a 0 -of=results -i1 rep_test_SDE.xml -i2 new_file_rep_SDE -lc 0 -if=Example_data -iT SDE 

##gE2 (local code):
#python main.py -a 1 -of=results -i1 input_file_hess1.xml -lc 1 -if=Example_data

##gE3 (SBML input):
#python main.py -a 2 -i1 p53_model.xml p53_model_exp.xml -i2 data_p53 data_p53_exp -of=results -lc 00 -if=Example_data

#&> ~/work/Testing/orig6_124e4_11_cuda10.txt


unset CUDA_DEVICE
