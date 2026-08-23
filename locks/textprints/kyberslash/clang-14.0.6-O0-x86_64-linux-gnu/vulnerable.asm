   0:	55                   	push   %rbp
   1:	48 89 e5             	mov    %rsp,%rbp
   4:	66 89 f8             	mov    %di,%ax
   7:	66 89 45 fe          	mov    %ax,-0x2(%rbp)
   b:	0f bf 4d fe          	movswl -0x2(%rbp),%ecx
   f:	c1 f9 0f             	sar    $0xf,%ecx
  12:	81 e1 01 0d 00 00    	and    $0xd01,%ecx
  18:	0f b7 45 fe          	movzwl -0x2(%rbp),%eax
  1c:	01 c8                	add    %ecx,%eax
  1e:	66 89 45 fe          	mov    %ax,-0x2(%rbp)
  22:	0f b7 45 fe          	movzwl -0x2(%rbp),%eax
  26:	c1 e0 01             	shl    $0x1,%eax
  29:	05 80 06 00 00       	add    $0x680,%eax
  2e:	b9 01 0d 00 00       	mov    $0xd01,%ecx
  33:	99                   	cltd
  34:	f7 f9                	idiv   %ecx
  36:	83 e0 01             	and    $0x1,%eax
  39:	66 89 45 fe          	mov    %ax,-0x2(%rbp)
  3d:	0f b7 45 fe          	movzwl -0x2(%rbp),%eax
  41:	5d                   	pop    %rbp
  42:	c3                   	ret