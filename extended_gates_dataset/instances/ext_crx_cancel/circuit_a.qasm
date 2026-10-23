OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
crx(pi/2) q[0], q[1];
crx(-pi/2) q[0], q[1];
