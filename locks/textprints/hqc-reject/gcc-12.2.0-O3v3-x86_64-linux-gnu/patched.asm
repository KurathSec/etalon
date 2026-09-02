    1630:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    1635:	49 89 d1             	mov    %rdx,%r9
    1638:	8b 12                	mov    (%rdx),%edx
    163a:	bf 00 02 00 00       	mov    $0x200,%edi
    163f:	c7 44 24 f8 00 00 00 	movl   $0x0,-0x8(%rsp)
    1646:	00 
    1647:	31 f6                	xor    %esi,%esi
    1649:	41 83 c8 01          	or     $0x1,%r8d
    164d:	0f 1f 00             	nopl   (%rax)
    1650:	89 d0                	mov    %edx,%eax
    1652:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    1659:	00 
    165a:	b9 c8 00 00 00       	mov    $0xc8,%ecx
    165f:	c1 e0 0d             	shl    $0xd,%eax
    1662:	31 d0                	xor    %edx,%eax
    1664:	89 c2                	mov    %eax,%edx
    1666:	c1 ea 11             	shr    $0x11,%edx
    1669:	31 d0                	xor    %edx,%eax
    166b:	89 c2                	mov    %eax,%edx
    166d:	c1 e2 05             	shl    $0x5,%edx
    1670:	31 c2                	xor    %eax,%edx
    1672:	41 89 d2             	mov    %edx,%r10d
    1675:	0f 1f 00             	nopl   (%rax)
    1678:	89 d0                	mov    %edx,%eax
    167a:	c1 e0 0d             	shl    $0xd,%eax
    167d:	31 d0                	xor    %edx,%eax
    167f:	89 c2                	mov    %eax,%edx
    1681:	c1 ea 11             	shr    $0x11,%edx
    1684:	31 d0                	xor    %edx,%eax
    1686:	89 c2                	mov    %eax,%edx
    1688:	c1 e2 05             	shl    $0x5,%edx
    168b:	31 c2                	xor    %eax,%edx
    168d:	8b 44 24 fc          	mov    -0x4(%rsp),%eax
    1691:	01 d0                	add    %edx,%eax
    1693:	89 44 24 fc          	mov    %eax,-0x4(%rsp)
    1697:	83 e9 01             	sub    $0x1,%ecx
    169a:	75 dc                	jne    1678 <sample_pos+0x48>
    169c:	8b 4c 24 fc          	mov    -0x4(%rsp),%ecx
    16a0:	31 c9                	xor    %ecx,%ecx
    16a2:	45 38 c2             	cmp    %r8b,%r10b
    16a5:	44 8b 54 24 f8       	mov    -0x8(%rsp),%r10d
    16aa:	0f 92 c1             	setb   %cl
    16ad:	c4 e2 48 f2 c9       	andn   %ecx,%esi,%ecx
    16b2:	09 ce                	or     %ecx,%esi
    16b4:	44 01 d1             	add    %r10d,%ecx
    16b7:	89 4c 24 f8          	mov    %ecx,-0x8(%rsp)
    16bb:	83 ef 01             	sub    $0x1,%edi
    16be:	75 90                	jne    1650 <sample_pos+0x20>
    16c0:	89 44 24 fc          	mov    %eax,-0x4(%rsp)
    16c4:	41 89 11             	mov    %edx,(%r9)
    16c7:	89 4c 24 f8          	mov    %ecx,-0x8(%rsp)
    16cb:	8b 44 24 f8          	mov    -0x8(%rsp),%eax
    16cf:	b8 00 02 00 00       	mov    $0x200,%eax
    16d4:	c3                   	ret