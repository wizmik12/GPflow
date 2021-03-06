# Copyright 2016 James Hensman, alexggmatthews
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tensorflow as tf
import numpy as np
from .config import default_float


def gaussian(x, mu, var):
    return -0.5 * (np.log(2 * np.pi) + tf.math.log(var) +
                   tf.square(mu - x) / var)


def lognormal(x, mu, var):
    lnx = tf.math.log(x)
    return gaussian(lnx, mu, var) - lnx


def bernoulli(x, p):
    return tf.math.log(tf.where(tf.equal(x, 1), p, 1 - p))


def poisson(x, lam):
    return x * tf.math.log(lam) - lam - tf.math.lgamma(x + 1.)


def exponential(x, scale):
    return -x / scale - tf.math.log(scale)


def gamma(x, shape, scale):
    return -shape * tf.math.log(scale) - tf.math.lgamma(shape) \
        + (shape - 1.) * tf.math.log(x) - x / scale


def student_t(x, mean, scale, df):
    df = tf.cast(df, default_float())
    const = tf.math.lgamma((df + 1.) * 0.5) - tf.math.lgamma(df * 0.5) \
        - 0.5 * (tf.math.log(tf.square(scale)) + tf.math.log(df) + np.log(np.pi))
    const = tf.cast(const, default_float())
    return const - 0.5 * (df + 1.) * \
        tf.math.log(1. + (1. / df) * (tf.square((x - mean) / scale)))


def beta(x, alpha, beta):
    # need to clip x, since log of 0 is nan...
    x = tf.clip_by_value(x, 1e-6, 1 - 1e-6)
    return (alpha - 1.) * tf.math.log(x) + (beta - 1.) * tf.math.log(1. - x) \
        + tf.math.lgamma(alpha + beta)\
        - tf.math.lgamma(alpha)\
        - tf.math.lgamma(beta)


def laplace(x, mu, sigma):
    return -tf.abs(mu - x) / sigma - tf.math.log(2. * sigma)


def multivariate_normal(x, mu, L):
    """
    Computes the log-density of a multivariate normal.
    :param x  : Dx1 or DxN sample(s) for which we want the density
    :param mu : Dx1 or DxN mean(s) of the normal distribution
    :param L  : DxD Cholesky decomposition of the covariance matrix
    :return p : (1,) or (N,) vector of log densities for each of the N x's and/or mu's

    x and mu are either vectors or matrices. If both are vectors (N,1):
    p[0] = log pdf(x) where x ~ N(mu, LL^T)
    If at least one is a matrix, we assume independence over the *columns*:
    the number of rows must match the size of L. Broadcasting behaviour:
    p[n] = log pdf of:
    x[n] ~ N(mu, LL^T) or x ~ N(mu[n], LL^T) or x[n] ~ N(mu[n], LL^T)
    """

    d = x - mu
    alpha = tf.linalg.triangular_solve(L, d, lower=True)
    num_dims = tf.cast(d.shape[0], L.dtype)
    p = -0.5 * tf.reduce_sum(tf.square(alpha), 0)
    p -= 0.5 * num_dims * np.log(2 * np.pi)
    p -= tf.reduce_sum(tf.math.log(tf.linalg.diag_part(L)))
    return p
