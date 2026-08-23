    1588:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    158d:	41 83 c8 01          	or     $0x1,%r8d
    1591:	8b 32                	mov    (%rdx),%esi
    1593:	31 c0                	xor    %eax,%eax
    1595:	89 f1                	mov    %esi,%ecx
    1597:	c1 e1 0d             	shl    $0xd,%ecx
    159a:	31 f1                	xor    %esi,%ecx
    159c:	89 ce                	mov    %ecx,%esi
    159e:	c1 ee 11             	shr    $0x11,%esi
    15a1:	31 ce                	xor    %ecx,%esi
    15a3:	41 89 f1             	mov    %esi,%r9d
    15a6:	41 c1 e1 05          	shl    $0x5,%r9d
    15aa:	41 31 f1             	xor    %esi,%r9d
    15ad:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    15b4:	00 
    15b5:	41 ba c8 00 00 00    	mov    $0xc8,%r10d
    15bb:	44 89 ce             	mov    %r9d,%esi
    15be:	89 f7                	mov    %esi,%edi
    15c0:	c1 e7 0d             	shl    $0xd,%edi
    15c3:	31 f7                	xor    %esi,%edi
    15c5:	89 f9                	mov    %edi,%ecx
    15c7:	c1 e9 11             	shr    $0x11,%ecx
    15ca:	31 f9                	xor    %edi,%ecx
    15cc:	89 ce                	mov    %ecx,%esi
    15ce:	c1 e6 05             	shl    $0x5,%esi
    15d1:	31 ce                	xor    %ecx,%esi
    15d3:	89 32                	mov    %esi,(%rdx)
    15d5:	01 74 24 fc          	add    %esi,-0x4(%rsp)
    15d9:	41 ff ca             	dec    %r10d
    15dc:	75 e0                	jne    15be <sample_pos+0x36>
    15de:	ff c0                	inc    %eax
    15e0:	8b 4c 24 fc          	mov    -0x4(%rsp),%ecx
    15e4:	41 0f b6 c9          	movzbl %r9b,%ecx
    15e8:	44 39 c1             	cmp    %r8d,%ecx
    15eb:	73 a8                	jae    1595 <sample_pos+0xd>
    15ed:	c3                   	ret