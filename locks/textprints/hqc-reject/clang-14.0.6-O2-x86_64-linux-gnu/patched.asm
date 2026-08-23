    15b0:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    15b5:	41 83 c8 01          	or     $0x1,%r8d
    15b9:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    15c0:	00 
    15c1:	8b 3a                	mov    (%rdx),%edi
    15c3:	45 31 c9             	xor    %r9d,%r9d
    15c6:	45 31 d2             	xor    %r10d,%r10d
    15c9:	0f 1f 80 00 00 00 00 	nopl   0x0(%rax)
    15d0:	89 f8                	mov    %edi,%eax
    15d2:	c1 e0 0d             	shl    $0xd,%eax
    15d5:	31 f8                	xor    %edi,%eax
    15d7:	89 c1                	mov    %eax,%ecx
    15d9:	c1 e9 11             	shr    $0x11,%ecx
    15dc:	31 c1                	xor    %eax,%ecx
    15de:	89 c8                	mov    %ecx,%eax
    15e0:	c1 e0 05             	shl    $0x5,%eax
    15e3:	31 c8                	xor    %ecx,%eax
    15e5:	c7 44 24 f8 00 00 00 	movl   $0x0,-0x8(%rsp)
    15ec:	00 
    15ed:	b9 c8 00 00 00       	mov    $0xc8,%ecx
    15f2:	89 c7                	mov    %eax,%edi
    15f4:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
    15fb:	00 00 00 
    15fe:	66 90                	xchg   %ax,%ax
    1600:	89 fe                	mov    %edi,%esi
    1602:	c1 e6 0d             	shl    $0xd,%esi
    1605:	31 fe                	xor    %edi,%esi
    1607:	89 f7                	mov    %esi,%edi
    1609:	c1 ef 11             	shr    $0x11,%edi
    160c:	31 f7                	xor    %esi,%edi
    160e:	89 fe                	mov    %edi,%esi
    1610:	c1 e6 05             	shl    $0x5,%esi
    1613:	31 fe                	xor    %edi,%esi
    1615:	89 32                	mov    %esi,(%rdx)
    1617:	01 74 24 f8          	add    %esi,-0x8(%rsp)
    161b:	89 f7                	mov    %esi,%edi
    161d:	c1 e7 0d             	shl    $0xd,%edi
    1620:	31 f7                	xor    %esi,%edi
    1622:	89 fe                	mov    %edi,%esi
    1624:	c1 ee 11             	shr    $0x11,%esi
    1627:	31 fe                	xor    %edi,%esi
    1629:	89 f7                	mov    %esi,%edi
    162b:	c1 e7 05             	shl    $0x5,%edi
    162e:	31 f7                	xor    %esi,%edi
    1630:	89 3a                	mov    %edi,(%rdx)
    1632:	01 7c 24 f8          	add    %edi,-0x8(%rsp)
    1636:	83 c1 fe             	add    $0xfffffffe,%ecx
    1639:	75 c5                	jne    1600 <sample_pos+0x50>
    163b:	8b 4c 24 f8          	mov    -0x8(%rsp),%ecx
    163f:	0f b6 c0             	movzbl %al,%eax
    1642:	44 39 c0             	cmp    %r8d,%eax
    1645:	0f 92 c0             	setb   %al
    1648:	45 85 c9             	test   %r9d,%r9d
    164b:	0f 94 c1             	sete   %cl
    164e:	20 c1                	and    %al,%cl
    1650:	0f b6 c1             	movzbl %cl,%eax
    1653:	01 44 24 fc          	add    %eax,-0x4(%rsp)
    1657:	41 09 c1             	or     %eax,%r9d
    165a:	41 83 c2 01          	add    $0x1,%r10d
    165e:	41 81 fa 00 02 00 00 	cmp    $0x200,%r10d
    1665:	0f 85 65 ff ff ff    	jne    15d0 <sample_pos+0x20>
    166b:	8b 44 24 fc          	mov    -0x4(%rsp),%eax
    166f:	b8 00 02 00 00       	mov    $0x200,%eax
    1674:	c3                   	ret