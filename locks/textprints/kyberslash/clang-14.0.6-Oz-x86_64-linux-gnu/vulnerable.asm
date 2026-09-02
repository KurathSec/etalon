   0:	0f bf c7             	movswl %di,%eax
   3:	c1 e8 0f             	shr    $0xf,%eax
   6:	b9 01 0d 00 00       	mov    $0xd01,%ecx
   b:	21 c8                	and    %ecx,%eax
   d:	01 f8                	add    %edi,%eax
   f:	0f b7 c0             	movzwl %ax,%eax
  12:	01 c0                	add    %eax,%eax
  14:	05 80 06 00 00       	add    $0x680,%eax
  19:	31 d2                	xor    %edx,%edx
  1b:	f7 f1                	div    %ecx
  1d:	83 e0 01             	and    $0x1,%eax
  20:	c3                   	ret