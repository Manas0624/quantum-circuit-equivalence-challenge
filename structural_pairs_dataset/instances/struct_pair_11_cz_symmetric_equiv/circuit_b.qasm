OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
cz q[1], q[0];
h q[1];
