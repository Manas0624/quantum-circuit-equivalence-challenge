OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
z q[0];
h q[0];
cx q[0], q[1];
