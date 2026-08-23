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
  2e:	89 45 f8             	mov    %eax,-0x8(%rbp)
  31:	69 45 f8 3b 01 00 00 	imul   $0x13b,-0x8(%rbp),%eax
  38:	c1 e8 14             	shr    $0x14,%eax
  3b:	89 45 f8             	mov    %eax,-0x8(%rbp)
  3e:	8b 45 f8             	mov    -0x8(%rbp),%eax
  41:	83 e0 01             	and    $0x1,%eax
  44:	0f b7 c0             	movzwl %ax,%eax
  47:	5d                   	pop    %rbp
  48:	c3                   	ret