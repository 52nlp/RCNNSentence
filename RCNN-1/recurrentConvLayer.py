import numpy as np

import theano
import theano.tensor as T
from theano.tensor.nnet import conv
from theano.tensor.signal import downsample

from normLayer import *

def ReLU(x):
	return theano.tensor.switch(x<0,0,x)

def TensorPadding(input,axis,width):
	'''
	>>>type input: T.tensorVariable
	>>>para input: input TensorVariable

	>>>type axis: int
	>>>para axis: which dimension to be padded

	>>>type width: int
	>>>para width: padding width
	'''
	shape=[]
	for i in xrange(input.ndim):
		shape.append(input.shape[i])
	pad_left=(width+1)/2
	pad_right=width/2
	
	if pad_left>0:
		left_shape=shape
		left_shape[axis]=pad_left
		left=T.zeros(left_shape)
		input=T.concatenate([left,input],axis=axis)

	if pad_right>0:
		right_shape=shape
		right_shape[axis]=pad_right
		right=T.zeros(right_shape)
		input=T.concatenate([input,right],axis=axis)
	return input

class RecurrentConvLayer(object):
	
	def __init__(self,rng,input,shape,filters,rfilter,alpha,beta,N,time,pool):
		'''
		>>>type rng: numpy.random.RandomState
		>>>para rng: random seed
		
		>>>type input: T.tensor4
		>>>para input: input data

		>>>type shape: tuple or list of length 4
		>>>para shape: (batch_size,num of input feature maps, image height, image width)

		>>>type filters: tuple or list of length 4
		>>>para filters: (num of filters, num of input feature maps, filter height, filter width)

		>>>type rfilter: tuple or list of length 4
		>>>para rfilter: (num of filters, num of filters, recurrent filter height, recurrent filter width)

		>>>type alpha,beta,N: int or float
		>>>para alpha,beta,N: used in the formulation of recurent state

		>>>type time: int
		>>>para time: the num of iteration in the recurrent layer

		>>>type pool: tuple or list of length 2
		>>>para pool: pooling size
		'''

		assert shape[1]==filters[1]
		assert filters[0]==rfilter[0]
		assert rfilter[0]==rfilter[1]
		self.input=input
		self.filters=filters;self.rfilter=rfilter
		self.shape=shape;self.time=time;self.pool=pool
		self.alpha=alpha;self.beta=beta;self.N=N
		layer_size=(shape[0],filters[0],shape[2]-filters[2]+1,shape[3]-filters[3]+1)

		inflow=np.prod(filters[1:])
		outflow=filters[0]*np.prod(filters[2:])/np.prod(pool)

		w_bound=np.sqrt(6./(inflow+outflow))
		rw_bound=np.sqrt(3./np.prod(rfilter))

		w_in_init=np.asarray(rng.uniform(low=-w_bound,high=w_bound,size=filters),dtype=theano.config.floatX)
		self.w_in=theano.shared(value=w_in_init,name='w_in')
		w_r_init=np.asarray(rng.uniform(low=-rw_bound,high=rw_bound,size=rfilter),dtype=theano.config.floatX)
		self.w_r=theano.shared(value=w_r_init,name='w_r')

		b_init=np.zeros(shape=filters[0],dtype=theano.config.floatX)
		self.b=theano.shared(value=b_init,name='b_in')
		b_r_init=np.zeros(shape=rfilter[0],dtype=theano.config.floatX)
		self.b_r=theano.shared(value=b_r_init,name='b_r')

		conv_input=conv.conv2d(
			input=input,
			filters=self.w_in,
			filter_shape=filters,
			image_shape=shape
			)

		print 'initialize the weight'

		state=conv_input+self.b_r.dimshuffle('x',0,'x','x')
		for i in xrange(time):
			padded_input=TensorPadding(TensorPadding(input=state,width=rfilter[2]-1,axis=2),width=rfilter[3]-1,axis=3)
			conv_recurrent=conv.conv2d(
				input=padded_input,
				filters=self.w_r,
				filter_shape=rfilter,
				image_shape=[layer_size[0],layer_size[1],layer_size[2]+rfilter[2]-1,layer_size[3]+rfilter[3]-1]
			)
			state=ReLU(conv_input+conv_recurrent)
			norm=NormLayer(
				input=state,
				shape=layer_size,
				alpha=alpha,
				beta=beta,
				N=N
			)
			state=norm.output

		pool_out=downsample.max_pool_2d(
			input=state,
			ds=pool,
			ignore_border=True
		)
		self.output=pool_out+self.b.dimshuffle('x',0,'x','x')
		self.param=[self.w_in,self.w_r,self.b,self.b_r]
		
		print 'recurrentconvlayer constructed!'

	def process(self,data,batchSize):
		'''
		>>>process new data

		>>>type data: T.tensor4
		>>>para data: newly processed data
		>>>type batchSize: int
		>>>para batchSize: batch size
		'''
		shape=(batchSize,1,self.shape[2],self.shape[3])
		layer_size=(batchSize,self.filters[0],shape[2]-self.filters[2]+1,shape[3]-self.filters[3]+1)

		conv_input=conv.conv2d(
			input=data,
			filters=self.w_in,
			filter_shape=self.filters,
			image_shape=shape
		)

		state=conv_input+self.b_r.dimshuffle('x',0,'x','x')
		for i in xrange(self.time):
			padded_input=TensorPadding(TensorPadding(input=state,width=self.rfilter[2]-1,axis=2),width=self.rfilter[3]-1,axis=3)
			conv_recurrent=conv.conv2d(
				input=padded_input,
				filters=self.w_r,
				filter_shape=self.rfilter,
				image_shape=[layer_size[0],layer_size[1],layer_size[2]+self.rfilter[2]-1,layer_size[3]+self.rfilter[3]-1]
			)
			state=ReLU(conv_input+conv_recurrent)
#			norm=NormLayer(
#				input=state,
#				shape=layer_size,
#				alpha=self.alpha,
#				beta=self.beta,
#				N=self.N
#			)
#			state=norm.output

		pool_out=downsample.max_pool_2d(
			input=state,
			ds=self.pool,
			ignore_border=True
		)
		output=pool_out+self.b.dimshuffle('x',0,'x','x')
		return output
