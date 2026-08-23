   0:	0f bf c7             	movswl %di,%eax
   3:	c1 e8 0f             	shr    $0xf,%eax
   6:	25 01 0d 00 00       	and    $0xd01,%eax
   b:	01 f8                	add    %edi,%eax
   d:	0f b7 c0             	movzwl %ax,%eax
  10:	69 c0 76 02 00 00    	imul   $0x276,%eax,%eax
  16:	05 80 ff 07 00       	add    $0x7ff80,%eax
  1b:	c1 e8 14             	shr    $0x14,%eax
  1e:	83 e0 01             	and    $0x1,%eax
  21:	c3                   	ret