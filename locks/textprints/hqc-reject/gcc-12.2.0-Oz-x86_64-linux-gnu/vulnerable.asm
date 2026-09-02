    1549:	8a 0c 37             	mov    (%rdi,%rsi,1),%cl
    154c:	66 0f 6e 02          	movd   (%rdx),%xmm0
    1550:	31 c0                	xor    %eax,%eax
    1552:	83 c9 01             	or     $0x1,%ecx
    1555:	0f 28 d0             	movaps %xmm0,%xmm2
    1558:	ff c0                	inc    %eax
    155a:	83 64 24 f4 00       	andl   $0x0,-0xc(%rsp)
    155f:	bf c8 00 00 00       	mov    $0xc8,%edi
    1564:	66 0f 72 f2 0d       	pslld  $0xd,%xmm2
    1569:	0f 28 ca             	movaps %xmm2,%xmm1
    156c:	0f 57 c8             	xorps  %xmm0,%xmm1
    156f:	0f 28 d9             	movaps %xmm1,%xmm3
    1572:	66 0f 72 d3 11       	psrld  $0x11,%xmm3
    1577:	0f 57 cb             	xorps  %xmm3,%xmm1
    157a:	0f 28 e1             	movaps %xmm1,%xmm4
    157d:	66 0f 72 f4 05       	pslld  $0x5,%xmm4
    1582:	0f 28 c4             	movaps %xmm4,%xmm0
    1585:	0f 57 c1             	xorps  %xmm1,%xmm0
    1588:	66 0f 7e c6          	movd   %xmm0,%esi
    158c:	0f 28 e8             	movaps %xmm0,%xmm5
    158f:	66 0f 72 f5 0d       	pslld  $0xd,%xmm5
    1594:	0f 28 cd             	movaps %xmm5,%xmm1
    1597:	0f 57 c8             	xorps  %xmm0,%xmm1
    159a:	0f 28 f1             	movaps %xmm1,%xmm6
    159d:	66 0f 72 d6 11       	psrld  $0x11,%xmm6
    15a2:	0f 57 ce             	xorps  %xmm6,%xmm1
    15a5:	0f 28 f9             	movaps %xmm1,%xmm7
    15a8:	66 0f 72 f7 05       	pslld  $0x5,%xmm7
    15ad:	0f 28 c7             	movaps %xmm7,%xmm0
    15b0:	0f 57 c1             	xorps  %xmm1,%xmm0
    15b3:	66 0f 6e 4c 24 f4    	movd   -0xc(%rsp),%xmm1
    15b9:	66 0f fe c8          	paddd  %xmm0,%xmm1
    15bd:	66 0f 7e 4c 24 f4    	movd   %xmm1,-0xc(%rsp)
    15c3:	ff cf                	dec    %edi
    15c5:	75 c5                	jne    158c <sample_pos+0x43>
    15c7:	8b 7c 24 f4          	mov    -0xc(%rsp),%edi
    15cb:	40 38 ce             	cmp    %cl,%sil
    15ce:	73 85                	jae    1555 <sample_pos+0xc>
    15d0:	66 0f 7e 02          	movd   %xmm0,(%rdx)
    15d4:	66 0f 7e 4c 24 f4    	movd   %xmm1,-0xc(%rsp)
    15da:	c3                   	ret