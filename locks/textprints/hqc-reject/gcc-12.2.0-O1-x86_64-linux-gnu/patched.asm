    1608:	49 89 d1             	mov    %rdx,%r9
    160b:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    1610:	41 83 c8 01          	or     $0x1,%r8d
    1614:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    161b:	00 
    161c:	8b 12                	mov    (%rdx),%edx
    161e:	bf 00 02 00 00       	mov    $0x200,%edi
    1623:	be 00 00 00 00       	mov    $0x0,%esi
    1628:	89 d0                	mov    %edx,%eax
    162a:	c1 e0 0d             	shl    $0xd,%eax
    162d:	31 d0                	xor    %edx,%eax
    162f:	89 c2                	mov    %eax,%edx
    1631:	c1 ea 11             	shr    $0x11,%edx
    1634:	31 d0                	xor    %edx,%eax
    1636:	89 c2                	mov    %eax,%edx
    1638:	c1 e2 05             	shl    $0x5,%edx
    163b:	31 c2                	xor    %eax,%edx
    163d:	41 89 d2             	mov    %edx,%r10d
    1640:	c7 44 24 f8 00 00 00 	movl   $0x0,-0x8(%rsp)
    1647:	00 
    1648:	b9 c8 00 00 00       	mov    $0xc8,%ecx
    164d:	89 d0                	mov    %edx,%eax
    164f:	c1 e0 0d             	shl    $0xd,%eax
    1652:	31 d0                	xor    %edx,%eax
    1654:	89 c2                	mov    %eax,%edx
    1656:	c1 ea 11             	shr    $0x11,%edx
    1659:	31 d0                	xor    %edx,%eax
    165b:	89 c2                	mov    %eax,%edx
    165d:	c1 e2 05             	shl    $0x5,%edx
    1660:	31 c2                	xor    %eax,%edx
    1662:	8b 44 24 f8          	mov    -0x8(%rsp),%eax
    1666:	01 d0                	add    %edx,%eax
    1668:	89 44 24 f8          	mov    %eax,-0x8(%rsp)
    166c:	83 e9 01             	sub    $0x1,%ecx
    166f:	75 dc                	jne    164d <sample_pos+0x45>
    1671:	8b 4c 24 f8          	mov    -0x8(%rsp),%ecx
    1675:	45 38 c2             	cmp    %r8b,%r10b
    1678:	41 0f 92 c2          	setb   %r10b
    167c:	85 f6                	test   %esi,%esi
    167e:	0f 94 c1             	sete   %cl
    1681:	0f b6 c9             	movzbl %cl,%ecx
    1684:	44 21 d1             	and    %r10d,%ecx
    1687:	09 ce                	or     %ecx,%esi
    1689:	44 8b 54 24 fc       	mov    -0x4(%rsp),%r10d
    168e:	44 01 d1             	add    %r10d,%ecx
    1691:	89 4c 24 fc          	mov    %ecx,-0x4(%rsp)
    1695:	83 ef 01             	sub    $0x1,%edi
    1698:	75 8e                	jne    1628 <sample_pos+0x20>
    169a:	41 89 11             	mov    %edx,(%r9)
    169d:	89 44 24 f8          	mov    %eax,-0x8(%rsp)
    16a1:	89 4c 24 fc          	mov    %ecx,-0x4(%rsp)
    16a5:	8b 44 24 fc          	mov    -0x4(%rsp),%eax
    16a9:	b8 00 02 00 00       	mov    $0x200,%eax
    16ae:	c3                   	ret