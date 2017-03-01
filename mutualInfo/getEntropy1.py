from numpy import *

from pycuda import compiler, driver
from pycuda import autoinit

import launch


def getEntropy1(data,theta,N1,N2,sigma,scale):
	# Kernel declaration
	mod = compiler.SourceModule("""
	__device__ unsigned int idx3d(int i, int k, int l, int M, int P)
	{
		return k*P + i*M*P + l;
	}

	__device__ unsigned int idx2d(int i, int j, int M)
	{
		return i*M + j;
	}

	__global__ void distance1(int Ni, int Nj, int M, int P, float sigma, double scale, double *d1, double *d2, double *res1)
	{
	int i = threadIdx.x + blockDim.x * blockIdx.x;
	int j = threadIdx.y + blockDim.y * blockIdx.y;

	if((i>=Ni)||(j>=Nj)) return;

	double x1;
	x1 = 0.0;
	for(int k=0; k<M; k++){
		for(int l=0; l<P; l++){
			x1 = x1 + log(scale) - ( d2[idx3d(j,k,l,M,P)]-d1[idx3d(i,k,l,M,P)])*( d2[idx3d(j,k,l,M,P)]-d1[idx3d(i,k,l,M,P)])/(2.0*sigma*sigma);
		}
	}
	
	res1[idx2d(i,j,Nj)] = exp(x1);
	}
	""")

	# Assigning main kernel function to a variable
	dist_gpu1 = mod.get_function("distance1")

	block = launch.optimal_blocksize(autoinit.device, dist_gpu1)
	block_i = launch.factor_partial(block) # Maximum threads per block
	block_j = block / block_i
	print "block, BLOCK_I and _j",block, block_i, block_j

	grid = launch.optimise_gridsize(8.59)
	##should be defined as an int, can then clean up formulas further down
	grid_prelim_i = launch.round_down(sqrt(grid),block_i) # Define square root of maximum threads per grid
	grid_prelim_j = launch.round_down(grid/grid_prelim_i,block_j)
	print "PRELIM: grid, GRID_i and _j", grid, grid_prelim_i, grid_prelim_j

	if N1 < grid_prelim_i:
		grid_i = float(min(autoinit.device.max_grid_dim_x,N1))
		grid_j = float(min(autoinit.device.max_grid_dim_y, launch.round_down(grid/grid_i,block_j)))
	elif N2 < grid_prelim_j:
		grid_j = float(min(autoinit.device.max_grid_dim_y,N2))
		grid_i = float(min(autoinit.device.max_grid_dim_x, launch.round_down(grid/grid_j,block_i)))
	else:
		grid_i = float(min(autoinit.device.max_grid_dim_x, grid_prelim_i))
		grid_j = float(min(autoinit.device.max_grid_dim_y, grid_prelim_j))

	print "grid, GRID_i and _j", grid, grid_i, grid_j

	# Determine required number of runs for i and j
	##need float here?
	numRuns_i = int(ceil(N1/grid_i))
	numRuns_j = int(ceil(N2/grid_j))

	result = zeros([N1,numRuns_j])

	# Prepare data
	d1 = data.astype(float64)
	d2 = array(theta)[N1:(N1+N2),:,:].astype(float64)

	M = d1.shape[1] # number of timepoints
	P = d1.shape[2] # number of species

	Ni = int(grid_i)


	for i in range(numRuns_i):
		print "Runs left:", numRuns_i - i
		if((int(grid_i)*(i+1)) > N1): # If last run with less that max remaining trajectories
			Ni = int(N1 - grid_i*i) # Set Ni to remaining number of particels

		if(Ni<block_i):
			gi = 1  # Grid size in dim i
			bi = Ni # Block size in dim i
		else:
			gi = ceil(Ni/block_i)
			bi = block_i

		data1 = d1[(i*int(grid_i)):(i*int(grid_i)+Ni),:,:] # d1 subunit for the next j runs

		Nj = int(grid_j)


		for j in range(numRuns_j):
			if((int(grid_j)*(j+1)) > N2): # If last run with less that max remaining trajectories
				Nj = int(N2 - grid_j*j) # Set Nj to remaining number of particels

			data2 = d2[(j*int(grid_j)):(j*int(grid_j)+Nj),:,:] # d2 subunit for this run

			##could move into if statements (only if ni or nj change)
			res1 = zeros([Ni,Nj]).astype(float64) # results vector [shape(data1)*shape(data2)]

			if(Nj<block_j):
				gj = 1  # Grid size in dim j
				bj = Nj # Block size in dim j
			else:
				gj = ceil(Nj/block_j)
				bj = block_j

			# Invoke GPU calculations (takes data1 and data2 as input, outputs res1)
			dist_gpu1(int32(Ni),int32(Nj), int32(M), int32(P), float32(sigma), float64(scale), driver.In(data1), driver.In(data2),  driver.Out(res1), block=(int(bi),int(bj),1), grid=(int(gi),int(gj)))

			# First summation (could be done on GPU?)
			for k in range(Ni):
				result[(i*int(grid_i)+k),j] = sum(res1[k,:])

	sum1 = 0.0
	count_na = 0
	count_inf = 0

	for i in range(N1):
		if(isnan(sum(result[i,:]))): count_na += 1
		elif(isinf(log(sum(result[i,:])))): count_inf += 1
		else:
			sum1 -= log(sum(result[i,:])) - log(float(N2)) - M*P*log(scale) -  M*P*log(2.0*pi*sigma*sigma)
	print "COUNTER", count_na, count_inf
	Info = (sum1 / float(N1 - count_na - count_inf)) - M*P/2.0*(log(2.0*pi*sigma*sigma)+1)

	return(Info)

def run_getEntropy1(model_obj):
	MutInfo1 = []
	for experiment in range(model_obj.nmodels):

		#pos = model_obj.pairParamsICS.values()[cudaorder.index(cudafile)].index([x[1] for x in model_obj.x0prior[model]])
		if model_obj.initialprior == False:
			pos = model_obj.pairParamsICS[model_obj.cuda[experiment]].index([x[1] for x in model_obj.x0prior[experiment]])
			N1 = model_obj.cudaout_structure[model_obj.cuda[experiment]][pos][0]
			N2 = model_obj.cudaout_structure[model_obj.cuda[experiment]][pos][1]
		else:
			pos = model_obj.cudaout_structure[model_obj.cuda[experiment]][0]
			N1 = pos[0]
			N2 = pos[1]

		print "-----Calculating Mutual Information-----", experiment
		#print N1, N2

		MutInfo1.append(getEntropy1(model_obj.trajectories[experiment],model_obj.cudaout[experiment],N1,N2,model_obj.sigma,model_obj.scale[experiment]))
		print "Mutual Information:", MutInfo1[experiment]

	return MutInfo1
