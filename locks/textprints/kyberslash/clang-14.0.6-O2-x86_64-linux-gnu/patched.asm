   0:	0f bf c7             	movswl %di,%eax
   3:	c1 e8 0f             	shr    $0xf,%eax
   6:	25 01 0d 00 00       	and    $0xd01,%eax
   b:	01 f8                	add    %edi,%eax
   d:	0f b7 c0             	movzwl %ax,%eax
  10:	69 c0 f6 75 02 00    	imul   $0x275f6,%eax,%eax
  16:	05 7b 9a 00 08       	add    $0x8009a7b,%eax
  1b:	c1 e8 1c             	shr    $0x1c,%eax
  1e:	83 e0 01             	and    $0x1,%eax
  21:	c3                   	ret