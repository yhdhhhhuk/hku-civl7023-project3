"""Rotation matrix to xyzw quaternion, without Euler-angle singularities."""
import numpy as np


def matrix_quaternion(R):
    # Eigenvector form is stable near 180 degrees (the project's top-down pose).
    R=np.asarray(R,dtype=float)
    K=np.array([[R[0,0]-R[1,1]-R[2,2],R[1,0]+R[0,1],R[2,0]+R[0,2],R[2,1]-R[1,2]],
                [R[1,0]+R[0,1],R[1,1]-R[0,0]-R[2,2],R[2,1]+R[1,2],R[0,2]-R[2,0]],
                [R[2,0]+R[0,2],R[2,1]+R[1,2],R[2,2]-R[0,0]-R[1,1],R[1,0]-R[0,1]],
                [R[2,1]-R[1,2],R[0,2]-R[2,0],R[1,0]-R[0,1],R[0,0]+R[1,1]+R[2,2]]])/3
    values,vectors=np.linalg.eigh(K);q=vectors[:,np.argmax(values)]
    return (q if q[3]>=0 else -q).tolist()
