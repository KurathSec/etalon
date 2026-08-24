
/tmp/v_Os.o:     file format elf64-littleaarch64


Disassembly of section .text:

0000000000000000 <coeff_to_bit>:
   0:	934f3c01 	sbfx	x1, x0, #15, #1
   4:	5281a022 	mov	w2, #0xd01                 	// #3329
   8:	0a020021 	and	w1, w1, w2
   c:	0b000020 	add	w0, w1, w0
  10:	531f3c00 	ubfiz	w0, w0, #1, #16
  14:	111a0000 	add	w0, w0, #0x680
  18:	1ac20800 	udiv	w0, w0, w2
  1c:	12000000 	and	w0, w0, #0x1
  20:	d65f03c0 	ret
