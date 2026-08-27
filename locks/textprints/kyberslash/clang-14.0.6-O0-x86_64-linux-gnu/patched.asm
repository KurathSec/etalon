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
  26:	89 45 f8             	mov    %eax,-0x8(%rbp)
  29:	8b 45 f8             	mov    -0x8(%rbp),%eax
  2c:	c1 e0 01             	shl    $0x1,%eax
  2f:	89 45 f8             	mov    %eax,-0x8(%rbp)
  32:	8b 45 f8             	mov    -0x8(%rbp),%eax
  35:	05 81 06 00 00       	add    $0x681,%eax
  3a:	89 45 f8             	mov    %eax,-0x8(%rbp)
  3d:	69 45 f8 fb 3a 01 00 	imul   $0x13afb,-0x8(%rbp),%eax
  44:	89 45 f8             	mov    %eax,-0x8(%rbp)
  47:	8b 45 f8             	mov    -0x8(%rbp),%eax
  4a:	c1 e8 1c             	shr    $0x1c,%eax
  4d:	89 45 f8             	mov    %eax,-0x8(%rbp)
  50:	8b 45 f8             	mov    -0x8(%rbp),%eax
  53:	83 e0 01             	and    $0x1,%eax
  56:	0f b7 c0             	movzwl %ax,%eax
  59:	5d                   	pop    %rbp
  5a:	c3                   	ret