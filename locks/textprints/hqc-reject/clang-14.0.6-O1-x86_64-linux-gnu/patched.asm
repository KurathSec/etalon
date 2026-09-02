    15b0:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    15b5:	41 83 c8 01          	or     $0x1,%r8d
    15b9:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    15c0:	00 
    15c1:	45 31 c9             	xor    %r9d,%r9d
    15c4:	45 31 d2             	xor    %r10d,%r10d
    15c7:	66 0f 1f 84 00 00 00 	nopw   0x0(%rax,%rax,1)
    15ce:	00 00 
    15d0:	8b 02                	mov    (%rdx),%eax
    15d2:	89 c7                	mov    %eax,%edi
    15d4:	c1 e7 0d             	shl    $0xd,%edi
    15d7:	31 c7                	xor    %eax,%edi
    15d9:	89 f8                	mov    %edi,%eax
    15db:	c1 e8 11             	shr    $0x11,%eax
    15de:	31 f8                	xor    %edi,%eax
    15e0:	89 c7                	mov    %eax,%edi
    15e2:	c1 e7 05             	shl    $0x5,%edi
    15e5:	31 c7                	xor    %eax,%edi
    15e7:	89 3a                	mov    %edi,(%rdx)
    15e9:	c7 44 24 f8 00 00 00 	movl   $0x0,-0x8(%rsp)
    15f0:	00 
    15f1:	b8 c8 00 00 00       	mov    $0xc8,%eax
    15f6:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
    15fd:	00 00 00 
    1600:	8b 32                	mov    (%rdx),%esi
    1602:	89 f1                	mov    %esi,%ecx
    1604:	c1 e1 0d             	shl    $0xd,%ecx
    1607:	31 f1                	xor    %esi,%ecx
    1609:	89 ce                	mov    %ecx,%esi
    160b:	c1 ee 11             	shr    $0x11,%esi
    160e:	31 ce                	xor    %ecx,%esi
    1610:	89 f1                	mov    %esi,%ecx
    1612:	c1 e1 05             	shl    $0x5,%ecx
    1615:	31 f1                	xor    %esi,%ecx
    1617:	89 0a                	mov    %ecx,(%rdx)
    1619:	01 4c 24 f8          	add    %ecx,-0x8(%rsp)
    161d:	83 c0 ff             	add    $0xffffffff,%eax
    1620:	75 de                	jne    1600 <sample_pos+0x50>
    1622:	8b 44 24 f8          	mov    -0x8(%rsp),%eax
    1626:	40 0f b6 c7          	movzbl %dil,%eax
    162a:	44 39 c0             	cmp    %r8d,%eax
    162d:	40 0f 92 c7          	setb   %dil
    1631:	45 85 c9             	test   %r9d,%r9d
    1634:	0f 94 c0             	sete   %al
    1637:	40 20 f8             	and    %dil,%al
    163a:	0f b6 c0             	movzbl %al,%eax
    163d:	01 44 24 fc          	add    %eax,-0x4(%rsp)
    1641:	41 09 c1             	or     %eax,%r9d
    1644:	41 83 c2 01          	add    $0x1,%r10d
    1648:	41 81 fa 00 02 00 00 	cmp    $0x200,%r10d
    164f:	0f 85 7b ff ff ff    	jne    15d0 <sample_pos+0x20>
    1655:	8b 44 24 fc          	mov    -0x4(%rsp),%eax
    1659:	b8 00 02 00 00       	mov    $0x200,%eax
    165e:	c3                   	ret