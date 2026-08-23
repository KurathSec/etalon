    1630:	0f b6 3c 37          	movzbl (%rdi,%rsi,1),%edi
    1634:	49 89 d0             	mov    %rdx,%r8
    1637:	8b 12                	mov    (%rdx),%edx
    1639:	31 f6                	xor    %esi,%esi
    163b:	83 cf 01             	or     $0x1,%edi
    163e:	89 d0                	mov    %edx,%eax
    1640:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    1647:	00 
    1648:	83 c6 01             	add    $0x1,%esi
    164b:	b9 c8 00 00 00       	mov    $0xc8,%ecx
    1650:	c1 e0 0d             	shl    $0xd,%eax
    1653:	31 d0                	xor    %edx,%eax
    1655:	89 c2                	mov    %eax,%edx
    1657:	c1 ea 11             	shr    $0x11,%edx
    165a:	31 d0                	xor    %edx,%eax
    165c:	89 c2                	mov    %eax,%edx
    165e:	c1 e2 05             	shl    $0x5,%edx
    1661:	31 c2                	xor    %eax,%edx
    1663:	41 89 d1             	mov    %edx,%r9d
    1666:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
    166d:	00 00 00 
    1670:	89 d0                	mov    %edx,%eax
    1672:	c1 e0 0d             	shl    $0xd,%eax
    1675:	31 d0                	xor    %edx,%eax
    1677:	89 c2                	mov    %eax,%edx
    1679:	c1 ea 11             	shr    $0x11,%edx
    167c:	31 d0                	xor    %edx,%eax
    167e:	89 c2                	mov    %eax,%edx
    1680:	c1 e2 05             	shl    $0x5,%edx
    1683:	31 c2                	xor    %eax,%edx
    1685:	8b 44 24 fc          	mov    -0x4(%rsp),%eax
    1689:	01 d0                	add    %edx,%eax
    168b:	89 44 24 fc          	mov    %eax,-0x4(%rsp)
    168f:	83 e9 01             	sub    $0x1,%ecx
    1692:	75 dc                	jne    1670 <sample_pos+0x40>
    1694:	8b 4c 24 fc          	mov    -0x4(%rsp),%ecx
    1698:	41 38 f9             	cmp    %dil,%r9b
    169b:	73 a1                	jae    163e <sample_pos+0xe>
    169d:	89 44 24 fc          	mov    %eax,-0x4(%rsp)
    16a1:	89 f0                	mov    %esi,%eax
    16a3:	41 89 10             	mov    %edx,(%r8)
    16a6:	c3                   	ret