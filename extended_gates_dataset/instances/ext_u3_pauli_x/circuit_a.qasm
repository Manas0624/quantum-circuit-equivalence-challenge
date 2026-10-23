OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
u3(pi, 0, pi) q[0];
