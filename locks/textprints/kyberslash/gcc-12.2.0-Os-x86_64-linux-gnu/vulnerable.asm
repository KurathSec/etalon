   0:	89 f8                	mov    %edi,%eax
   2:	66 c1 ff 0f          	sar    $0xf,%di
   6:	b9 01 0d 00 00       	mov    $0xd01,%ecx
   b:	66 81 e7 01 0d       	and    $0xd01,%di
  10:	01 c7                	add    %eax,%edi
  12:	0f b7 ff             	movzwl %di,%edi
  15:	8d 84 3f 80 06 00 00 	lea    0x680(%rdi,%rdi,1),%eax
  1c:	99                   	cltd
  1d:	f7 f9                	idiv   %ecx
  1f:	83 e0 01             	and    $0x1,%eax
  22:	c3                   	ret