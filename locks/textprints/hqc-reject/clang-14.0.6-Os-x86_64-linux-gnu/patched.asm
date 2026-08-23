    1588:	44 0f b6 04 37       	movzbl (%rdi,%rsi,1),%r8d
    158d:	41 83 c8 01          	or     $0x1,%r8d
    1591:	c7 44 24 fc 00 00 00 	movl   $0x0,-0x4(%rsp)
    1598:	00 
    1599:	8b 3a                	mov    (%rdx),%edi
    159b:	45 31 c9             	xor    %r9d,%r9d
    159e:	45 31 d2             	xor    %r10d,%r10d
    15a1:	89 f8                	mov    %edi,%eax
    15a3:	c1 e0 0d             	shl    $0xd,%eax
    15a6:	31 f8                	xor    %edi,%eax
    15a8:	89 c1                	mov    %eax,%ecx
    15aa:	c1 e9 11             	shr    $0x11,%ecx
    15ad:	31 c1                	xor    %eax,%ecx
    15af:	41 89 cb             	mov    %ecx,%r11d
    15b2:	41 c1 e3 05          	shl    $0x5,%r11d
    15b6:	41 31 cb             	xor    %ecx,%r11d
    15b9:	c7 44 24 f8 00 00 00 	movl   $0x0,-0x8(%rsp)
    15c0:	00 
    15c1:	b9 c8 00 00 00       	mov    $0xc8,%ecx
    15c6:	44 89 df             	mov    %r11d,%edi
    15c9:	89 fe                	mov    %edi,%esi
    15cb:	c1 e6 0d             	shl    $0xd,%esi
    15ce:	31 fe                	xor    %edi,%esi
    15d0:	89 f0                	mov    %esi,%eax
    15d2:	c1 e8 11             	shr    $0x11,%eax
    15d5:	31 f0                	xor    %esi,%eax
    15d7:	89 c7                	mov    %eax,%edi
    15d9:	c1 e7 05             	shl    $0x5,%edi
    15dc:	31 c7                	xor    %eax,%edi
    15de:	89 3a                	mov    %edi,(%rdx)
    15e0:	01 7c 24 f8          	add    %edi,-0x8(%rsp)
    15e4:	ff c9                	dec    %ecx
    15e6:	75 e1                	jne    15c9 <sample_pos+0x41>
    15e8:	8b 4c 24 f8          	mov    -0x8(%rsp),%ecx
    15ec:	41 0f b6 c3          	movzbl %r11b,%eax
    15f0:	44 39 c0             	cmp    %r8d,%eax
    15f3:	0f 92 c0             	setb   %al
    15f6:	45 85 c9             	test   %r9d,%r9d
    15f9:	0f 94 c1             	sete   %cl
    15fc:	20 c1                	and    %al,%cl
    15fe:	0f b6 c1             	movzbl %cl,%eax
    1601:	01 44 24 fc          	add    %eax,-0x4(%rsp)
    1605:	41 09 c1             	or     %eax,%r9d
    1608:	41 ff c2             	inc    %r10d
    160b:	41 81 fa 00 02 00 00 	cmp    $0x200,%r10d
    1612:	75 8d                	jne    15a1 <sample_pos+0x19>
    1614:	8b 44 24 fc          	mov    -0x4(%rsp),%eax
    1618:	b8 00 02 00 00       	mov    $0x200,%eax
    161d:	c3                   	ret