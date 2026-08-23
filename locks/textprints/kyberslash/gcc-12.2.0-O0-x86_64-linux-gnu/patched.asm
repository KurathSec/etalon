   0:	55                   	push   %rbp
   1:	48 89 e5             	mov    %rsp,%rbp
   4:	89 f8                	mov    %edi,%eax
   6:	66 89 45 ec          	mov    %ax,-0x14(%rbp)
   a:	0f b7 45 ec          	movzwl -0x14(%rbp),%eax
   e:	66 c1 f8 0f          	sar    $0xf,%ax
  12:	66 25 01 0d          	and    $0xd01,%ax
  16:	66 01 45 ec          	add    %ax,-0x14(%rbp)
  1a:	0f b7 45 ec          	movzwl -0x14(%rbp),%eax
  1e:	01 c0                	add    %eax,%eax
  20:	05 80 06 00 00       	add    $0x680,%eax
  25:	89 45 fc             	mov    %eax,-0x4(%rbp)
  28:	8b 45 fc             	mov    -0x4(%rbp),%eax
  2b:	69 c0 3b 01 00 00    	imul   $0x13b,%eax,%eax
  31:	c1 e8 14             	shr    $0x14,%eax
  34:	89 45 fc             	mov    %eax,-0x4(%rbp)
  37:	8b 45 fc             	mov    -0x4(%rbp),%eax
  3a:	83 e0 01             	and    $0x1,%eax
  3d:	5d                   	pop    %rbp
  3e:	c3                   	ret