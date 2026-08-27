   0:	89 f8                	mov    %edi,%eax
   2:	66 c1 ff 0f          	sar    $0xf,%di
   6:	66 81 e7 01 0d       	and    $0xd01,%di
   b:	01 c7                	add    %eax,%edi
   d:	0f b7 ff             	movzwl %di,%edi
  10:	8d 84 3f 81 06 00 00 	lea    0x681(%rdi,%rdi,1),%eax
  17:	69 c0 fb 3a 01 00    	imul   $0x13afb,%eax,%eax
  1d:	c1 e8 1c             	shr    $0x1c,%eax
  20:	83 e0 01             	and    $0x1,%eax
  23:	c3                   	ret