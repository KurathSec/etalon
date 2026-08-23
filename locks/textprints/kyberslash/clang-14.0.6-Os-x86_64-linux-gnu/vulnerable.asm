   0:	0f bf c7             	movswl %di,%eax
   3:	c1 e8 0f             	shr    $0xf,%eax
   6:	25 01 0d 00 00       	and    $0xd01,%eax
   b:	01 f8                	add    %edi,%eax
   d:	0f b7 c0             	movzwl %ax,%eax
  10:	01 c0                	add    %eax,%eax
  12:	05 80 06 00 00       	add    $0x680,%eax
  17:	48 69 c8 81 76 fb 3a 	imul   $0x3afb7681,%rax,%rcx
  1e:	48 c1 e9 20          	shr    $0x20,%rcx
  22:	29 c8                	sub    %ecx,%eax
  24:	d1 e8                	shr    %eax
  26:	01 c8                	add    %ecx,%eax
  28:	c1 e8 0b             	shr    $0xb,%eax
  2b:	83 e0 01             	and    $0x1,%eax
  2e:	c3                   	ret