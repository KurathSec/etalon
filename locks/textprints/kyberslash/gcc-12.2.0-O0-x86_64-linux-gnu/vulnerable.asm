   0:	55                   	push   %rbp
   1:	48 89 e5             	mov    %rsp,%rbp
   4:	89 f8                	mov    %edi,%eax
   6:	66 89 45 fc          	mov    %ax,-0x4(%rbp)
   a:	0f b7 45 fc          	movzwl -0x4(%rbp),%eax
   e:	66 c1 f8 0f          	sar    $0xf,%ax
  12:	66 25 01 0d          	and    $0xd01,%ax
  16:	66 01 45 fc          	add    %ax,-0x4(%rbp)
  1a:	0f b7 45 fc          	movzwl -0x4(%rbp),%eax
  1e:	01 c0                	add    %eax,%eax
  20:	05 80 06 00 00       	add    $0x680,%eax
  25:	48 63 d0             	movslq %eax,%rdx
  28:	48 69 d2 41 bb 7d 9d 	imul   $0xffffffff9d7dbb41,%rdx,%rdx
  2f:	48 c1 ea 20          	shr    $0x20,%rdx
  33:	01 c2                	add    %eax,%edx
  35:	c1 fa 0b             	sar    $0xb,%edx
  38:	c1 f8 1f             	sar    $0x1f,%eax
  3b:	29 c2                	sub    %eax,%edx
  3d:	89 d0                	mov    %edx,%eax
  3f:	83 e0 01             	and    $0x1,%eax
  42:	66 89 45 fc          	mov    %ax,-0x4(%rbp)
  46:	0f b7 45 fc          	movzwl -0x4(%rbp),%eax
  4a:	5d                   	pop    %rbp
  4b:	c3                   	ret