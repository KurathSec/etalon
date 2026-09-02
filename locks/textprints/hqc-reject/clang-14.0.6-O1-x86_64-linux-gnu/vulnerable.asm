    15b0:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    15b5:	41 83 c8 01          	or     $0x1,%r8d
    15b9:	45 31 c9             	xor    %r9d,%r9d
    15bc:	0f 1f 40 00          	nopl   0x0(%rax)
    15c0:	8b 0a                	mov    (%rdx),%ecx
    15c2:	89 cf                	mov    %ecx,%edi
    15c4:	c1 e7 0d             	shl    $0xd,%edi
    15c7:	31 cf                	xor    %ecx,%edi
    15c9:	89 f9                	mov    %edi,%ecx
    15cb:	c1 e9 11             	shr    $0x11,%ecx
    15ce:	31 f9                	xor    %edi,%ecx
    15d0:	41 89 ca             	mov    %ecx,%r10d
    15d3:	41 c1 e2 05          	shl    $0x5,%r10d
    15d7:	41 31 ca             	xor    %ecx,%r10d
    15da:	44 89 12             	mov    %r10d,(%rdx)
    15dd:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    15e4:	00 
    15e5:	b9 c8 00 00 00       	mov    $0xc8,%ecx
    15ea:	66 0f 1f 44 00 00    	nopw   0x0(%rax,%rax,1)
    15f0:	8b 3a                	mov    (%rdx),%edi
    15f2:	89 fe                	mov    %edi,%esi
    15f4:	c1 e6 0d             	shl    $0xd,%esi
    15f7:	31 fe                	xor    %edi,%esi
    15f9:	89 f7                	mov    %esi,%edi
    15fb:	c1 ef 11             	shr    $0x11,%edi
    15fe:	31 f7                	xor    %esi,%edi
    1600:	89 fe                	mov    %edi,%esi
    1602:	c1 e6 05             	shl    $0x5,%esi
    1605:	31 fe                	xor    %edi,%esi
    1607:	89 32                	mov    %esi,(%rdx)
    1609:	01 74 24 fc          	add    %esi,-0x4(%rsp)
    160d:	83 c1 ff             	add    $0xffffffff,%ecx
    1610:	75 de                	jne    15f0 <sample_pos+0x40>
    1612:	41 83 c1 01          	add    $0x1,%r9d
    1616:	8b 4c 24 fc          	mov    -0x4(%rsp),%ecx
    161a:	41 0f b6 ca          	movzbl %r10b,%ecx
    161e:	44 39 c1             	cmp    %r8d,%ecx
    1621:	41 0f 42 c1          	cmovb  %r9d,%eax
    1625:	73 99                	jae    15c0 <sample_pos+0x10>
    1627:	c3                   	ret