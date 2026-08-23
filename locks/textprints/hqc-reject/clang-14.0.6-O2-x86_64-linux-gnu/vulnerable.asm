    15b0:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    15b5:	41 83 c8 01          	or     $0x1,%r8d
    15b9:	8b 32                	mov    (%rdx),%esi
    15bb:	31 c0                	xor    %eax,%eax
    15bd:	0f 1f 00             	nopl   (%rax)
    15c0:	89 f1                	mov    %esi,%ecx
    15c2:	c1 e1 0d             	shl    $0xd,%ecx
    15c5:	31 f1                	xor    %esi,%ecx
    15c7:	89 ce                	mov    %ecx,%esi
    15c9:	c1 ee 11             	shr    $0x11,%esi
    15cc:	31 ce                	xor    %ecx,%esi
    15ce:	41 89 f1             	mov    %esi,%r9d
    15d1:	41 c1 e1 05          	shl    $0x5,%r9d
    15d5:	41 31 f1             	xor    %esi,%r9d
    15d8:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    15df:	00 
    15e0:	bf c8 00 00 00       	mov    $0xc8,%edi
    15e5:	44 89 ce             	mov    %r9d,%esi
    15e8:	0f 1f 84 00 00 00 00 	nopl   0x0(%rax,%rax,1)
    15ef:	00 
    15f0:	89 f1                	mov    %esi,%ecx
    15f2:	c1 e1 0d             	shl    $0xd,%ecx
    15f5:	31 f1                	xor    %esi,%ecx
    15f7:	89 ce                	mov    %ecx,%esi
    15f9:	c1 ee 11             	shr    $0x11,%esi
    15fc:	31 ce                	xor    %ecx,%esi
    15fe:	89 f1                	mov    %esi,%ecx
    1600:	c1 e1 05             	shl    $0x5,%ecx
    1603:	31 f1                	xor    %esi,%ecx
    1605:	89 0a                	mov    %ecx,(%rdx)
    1607:	01 4c 24 fc          	add    %ecx,-0x4(%rsp)
    160b:	89 ce                	mov    %ecx,%esi
    160d:	c1 e6 0d             	shl    $0xd,%esi
    1610:	31 ce                	xor    %ecx,%esi
    1612:	89 f1                	mov    %esi,%ecx
    1614:	c1 e9 11             	shr    $0x11,%ecx
    1617:	31 f1                	xor    %esi,%ecx
    1619:	89 ce                	mov    %ecx,%esi
    161b:	c1 e6 05             	shl    $0x5,%esi
    161e:	31 ce                	xor    %ecx,%esi
    1620:	89 32                	mov    %esi,(%rdx)
    1622:	01 74 24 fc          	add    %esi,-0x4(%rsp)
    1626:	83 c7 fe             	add    $0xfffffffe,%edi
    1629:	75 c5                	jne    15f0 <sample_pos+0x40>
    162b:	83 c0 01             	add    $0x1,%eax
    162e:	8b 7c 24 fc          	mov    -0x4(%rsp),%edi
    1632:	41 0f b6 c9          	movzbl %r9b,%ecx
    1636:	44 39 c1             	cmp    %r8d,%ecx
    1639:	73 85                	jae    15c0 <sample_pos+0x10>
    163b:	c3                   	ret