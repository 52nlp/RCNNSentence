import numpy as np

import theano
import theano.tensor as T
from theano.tensor.nnet import conv
from theano.tensor.signal import downsample

class ConvPool(object):

	def __init__(self, rng, input,shape,filters,pool):
		'''
		>>>type rng: numpy.random.RandomState
		>>>para rng: initalize weight randomly

		>>>type input: T.dtensor4
		>>>para input: image

		>>>type shape: tuple or list of length 4
		>>>para shape: (batch size, num of input feature maps, image height, image width)

		>>>type filters: tuple or list of length 4
		>>>para filters: (num of filters, num of input feature maps, filter height, filter width)

		>>>type pool: tuple or list of length 2
		>>>para pool: pooling size
		'''

		assert filters[1]==shape[1]
		self.input=input

		#num of input to each hidden unit
		inflow=np.prod(filters[1:])

		#num of gradients from the upper layer
		outflow=filters[0]*np.prod(filters[2:])/np.prod(pool)

		w_bound=np.sqrt(6./(inflow+outflow))

		self.w=theano.shared(
			np.asarray(
				rng.uniform(low=-w_bound,high=w_bound,size=filters),
				dtype=theano.config.floatX
				),
			borrow=True
			)

		#bias
		self.b=theano.shared(
			value=np.zeros((filters[0]),dtype=theano.config.floatX),
			borrow=True
			)

		#build up convolutional layer
		conv_out=conv.conv2d(
			input=input,
			filters=self.w,
			filter_shape=filters,
			image_shape=shape
			)

		#build up pooling layer
		pool_out=downsample.max_pool_2d(
			input=conv_out,
			ds=pool,
			ignore_border=True
			)

		self.output=T.tanh(pool_out+self.b.dimshuffle('x',0,'x','x'))

		self.param=[self.w,self.b]
