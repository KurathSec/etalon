   0:	89 f8                	mov    %edi,%eax
   2:	66 c1 ff 0f          	sar    $0xf,%di
   6:	66 81 e7 01 0d       	and    $0xd01,%di
   b:	01 c7                	add    %eax,%edi
   d:	0f b7 ff             	movzwl %di,%edi
  10:	8d 84 3f 80 06 00 00 	lea    0x680(%rdi,%rdi,1),%eax
  17:	48 63 d0             	movslq %eax,%rdx
  1a:	48 69 d2 41 bb 7d 9d 	imul   $0xffffffff9d7dbb41,%rdx,%rdx
  21:	48 c1 ea 20          	shr    $0x20,%rdx
  25:	01 d0                	add    %edx,%eax
  27:	c1 f8 0b             	sar    $0xb,%eax
  2a:	83 e0 01             	and    $0x1,%eax
  2d:	c3                   	ret