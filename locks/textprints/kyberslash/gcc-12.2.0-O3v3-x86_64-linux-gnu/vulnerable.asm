   0:	89 f8                	mov    %edi,%eax
   2:	66 c1 ff 0f          	sar    $0xf,%di
   6:	66 81 e7 01 0d       	and    $0xd01,%di
   b:	01 c7                	add    %eax,%edi
   d:	0f b7 ff             	movzwl %di,%edi
  10:	8d 8c 3f 80 06 00 00 	lea    0x680(%rdi,%rdi,1),%ecx
  17:	48 89 ca             	mov    %rcx,%rdx
  1a:	48 69 c9 81 76 fb 3a 	imul   $0x3afb7681,%rcx,%rcx
  21:	89 d0                	mov    %edx,%eax
  23:	48 c1 e9 20          	shr    $0x20,%rcx
  27:	29 c8                	sub    %ecx,%eax
  29:	d1 e8                	shr    %eax
  2b:	01 c8                	add    %ecx,%eax
  2d:	c1 e8 0b             	shr    $0xb,%eax
  30:	83 e0 01             	and    $0x1,%eax
  33:	c3                   	ret