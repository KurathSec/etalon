    1559:	8a 0c 37             	mov    (%rdi,%rsi,1),%cl
    155c:	66 0f 6e 02          	movd   (%rdx),%xmm0
    1560:	31 c0                	xor    %eax,%eax
    1562:	83 c9 01             	or     $0x1,%ecx
    1565:	0f 28 d0             	movaps %xmm0,%xmm2
    1568:	31 ff                	xor    %edi,%edi
    156a:	ff c0                	inc    %eax
    156c:	66 0f 72 f2 0d       	pslld  $0xd,%xmm2
    1571:	89 7c 24 f4          	mov    %edi,-0xc(%rsp)
    1575:	bf c8 00 00 00       	mov    $0xc8,%edi
    157a:	0f 28 ca             	movaps %xmm2,%xmm1
    157d:	0f 57 c8             	xorps  %xmm0,%xmm1
    1580:	0f 28 d9             	movaps %xmm1,%xmm3
    1583:	66 0f 72 d3 11       	psrld  $0x11,%xmm3
    1588:	0f 57 cb             	xorps  %xmm3,%xmm1
    158b:	0f 28 e1             	movaps %xmm1,%xmm4
    158e:	66 0f 72 f4 05       	pslld  $0x5,%xmm4
    1593:	0f 28 c4             	movaps %xmm4,%xmm0
    1596:	0f 57 c1             	xorps  %xmm1,%xmm0
    1599:	66 0f 7e c6          	movd   %xmm0,%esi
    159d:	0f 28 e8             	movaps %xmm0,%xmm5
    15a0:	66 0f 72 f5 0d       	pslld  $0xd,%xmm5
    15a5:	0f 28 cd             	movaps %xmm5,%xmm1
    15a8:	0f 57 c8             	xorps  %xmm0,%xmm1
    15ab:	0f 28 f1             	movaps %xmm1,%xmm6
    15ae:	66 0f 72 d6 11       	psrld  $0x11,%xmm6
    15b3:	0f 57 ce             	xorps  %xmm6,%xmm1
    15b6:	0f 28 f9             	movaps %xmm1,%xmm7
    15b9:	66 0f 72 f7 05       	pslld  $0x5,%xmm7
    15be:	0f 28 c7             	movaps %xmm7,%xmm0
    15c1:	0f 57 c1             	xorps  %xmm1,%xmm0
    15c4:	66 0f 6e 4c 24 f4    	movd   -0xc(%rsp),%xmm1
    15ca:	66 0f fe c8          	paddd  %xmm0,%xmm1
    15ce:	66 0f 7e 4c 24 f4    	movd   %xmm1,-0xc(%rsp)
    15d4:	ff cf                	dec    %edi
    15d6:	75 c5                	jne    159d <sample_pos+0x44>
    15d8:	8b 7c 24 f4          	mov    -0xc(%rsp),%edi
    15dc:	40 38 ce             	cmp    %cl,%sil
    15df:	73 84                	jae    1565 <sample_pos+0xc>
    15e1:	66 0f 7e 02          	movd   %xmm0,(%rdx)
    15e5:	66 0f 7e 4c 24 f4    	movd   %xmm1,-0xc(%rsp)
    15eb:	c3                   	ret