    1608:	49 89 d0             	mov    %rdx,%r8
    160b:	0f b6 3c 37          	movzbl (%rdi,%rsi,1),%edi
    160f:	83 cf 01             	or     $0x1,%edi
    1612:	8b 12                	mov    (%rdx),%edx
    1614:	be 00 00 00 00       	mov    $0x0,%esi
    1619:	83 c6 01             	add    $0x1,%esi
    161c:	89 d0                	mov    %edx,%eax
    161e:	c1 e0 0d             	shl    $0xd,%eax
    1621:	31 d0                	xor    %edx,%eax
    1623:	89 c2                	mov    %eax,%edx
    1625:	c1 ea 11             	shr    $0x11,%edx
    1628:	31 d0                	xor    %edx,%eax
    162a:	89 c2                	mov    %eax,%edx
    162c:	c1 e2 05             	shl    $0x5,%edx
    162f:	31 c2                	xor    %eax,%edx
    1631:	41 89 d1             	mov    %edx,%r9d
    1634:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    163b:	00 
    163c:	b9 c8 00 00 00       	mov    $0xc8,%ecx
    1641:	89 d0                	mov    %edx,%eax
    1643:	c1 e0 0d             	shl    $0xd,%eax
    1646:	31 d0                	xor    %edx,%eax
    1648:	89 c2                	mov    %eax,%edx
    164a:	c1 ea 11             	shr    $0x11,%edx
    164d:	31 d0                	xor    %edx,%eax
    164f:	89 c2                	mov    %eax,%edx
    1651:	c1 e2 05             	shl    $0x5,%edx
    1654:	31 c2                	xor    %eax,%edx
    1656:	8b 44 24 fc          	mov    -0x4(%rsp),%eax
    165a:	01 d0                	add    %edx,%eax
    165c:	89 44 24 fc          	mov    %eax,-0x4(%rsp)
    1660:	83 e9 01             	sub    $0x1,%ecx
    1663:	75 dc                	jne    1641 <sample_pos+0x39>
    1665:	8b 4c 24 fc          	mov    -0x4(%rsp),%ecx
    1669:	41 38 f9             	cmp    %dil,%r9b
    166c:	73 ab                	jae    1619 <sample_pos+0x11>
    166e:	41 89 10             	mov    %edx,(%r8)
    1671:	89 44 24 fc          	mov    %eax,-0x4(%rsp)
    1675:	89 f0                	mov    %esi,%eax
    1677:	c3                   	ret