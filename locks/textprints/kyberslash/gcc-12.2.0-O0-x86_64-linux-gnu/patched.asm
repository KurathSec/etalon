   0:	55                   	push   %rbp
   1:	48 89 e5             	mov    %rsp,%rbp
   4:	89 f8                	mov    %edi,%eax
   6:	66 89 45 ec          	mov    %ax,-0x14(%rbp)
   a:	0f b7 45 ec          	movzwl -0x14(%rbp),%eax
   e:	66 c1 f8 0f          	sar    $0xf,%ax
  12:	66 25 01 0d          	and    $0xd01,%ax
  16:	66 01 45 ec          	add    %ax,-0x14(%rbp)
  1a:	0f b7 45 ec          	movzwl -0x14(%rbp),%eax
  1e:	89 45 fc             	mov    %eax,-0x4(%rbp)
  21:	d1 65 fc             	shll   -0x4(%rbp)
  24:	81 45 fc 81 06 00 00 	addl   $0x681,-0x4(%rbp)
  2b:	8b 45 fc             	mov    -0x4(%rbp),%eax
  2e:	69 c0 fb 3a 01 00    	imul   $0x13afb,%eax,%eax
  34:	89 45 fc             	mov    %eax,-0x4(%rbp)
  37:	c1 6d fc 1c          	shrl   $0x1c,-0x4(%rbp)
  3b:	8b 45 fc             	mov    -0x4(%rbp),%eax
  3e:	83 e0 01             	and    $0x1,%eax
  41:	5d                   	pop    %rbp
  42:	c3                   	ret