    1700:	55                   	push   %rbp
    1701:	41 57                	push   %r15
    1703:	41 56                	push   %r14
    1705:	53                   	push   %rbx
    1706:	48 83 ec 28          	sub    $0x28,%rsp
    170a:	49 89 f6             	mov    %rsi,%r14
    170d:	48 89 fb             	mov    %rdi,%rbx
    1710:	0f b6 3f             	movzbl (%rdi),%edi
    1713:	0f b6 36             	movzbl (%rsi),%esi
    1716:	e8 65 ff ff ff       	call   1680 <byte_work>
    171b:	0f b6 7b 01          	movzbl 0x1(%rbx),%edi
    171f:	41 0f b6 76 01       	movzbl 0x1(%r14),%esi
    1724:	41 0f b6 2e          	movzbl (%r14),%ebp
    1728:	44 0f b6 3b          	movzbl (%rbx),%r15d
    172c:	e8 4f ff ff ff       	call   1680 <byte_work>
    1731:	0f b6 7b 02          	movzbl 0x2(%rbx),%edi
    1735:	c5 f9 6e c5          	vmovd  %ebp,%xmm0
    1739:	c4 c3 79 20 46 01 01 	vpinsrb $0x1,0x1(%r14),%xmm0,%xmm0
    1740:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1746:	41 0f b6 76 02       	movzbl 0x2(%r14),%esi
    174b:	c4 c1 79 6e c7       	vmovd  %r15d,%xmm0
    1750:	c4 e3 79 20 43 01 01 	vpinsrb $0x1,0x1(%rbx),%xmm0,%xmm0
    1757:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    175c:	e8 1f ff ff ff       	call   1680 <byte_work>
    1761:	0f b6 7b 03          	movzbl 0x3(%rbx),%edi
    1765:	41 0f b6 76 03       	movzbl 0x3(%r14),%esi
    176a:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1770:	c4 c3 79 20 46 02 02 	vpinsrb $0x2,0x2(%r14),%xmm0,%xmm0
    1777:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    177d:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1782:	c4 e3 79 20 43 02 02 	vpinsrb $0x2,0x2(%rbx),%xmm0,%xmm0
    1789:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    178e:	e8 ed fe ff ff       	call   1680 <byte_work>
    1793:	0f b6 7b 04          	movzbl 0x4(%rbx),%edi
    1797:	41 0f b6 76 04       	movzbl 0x4(%r14),%esi
    179c:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    17a2:	c4 c3 79 20 46 03 03 	vpinsrb $0x3,0x3(%r14),%xmm0,%xmm0
    17a9:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    17af:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    17b4:	c4 e3 79 20 43 03 03 	vpinsrb $0x3,0x3(%rbx),%xmm0,%xmm0
    17bb:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    17c0:	e8 bb fe ff ff       	call   1680 <byte_work>
    17c5:	0f b6 7b 05          	movzbl 0x5(%rbx),%edi
    17c9:	41 0f b6 76 05       	movzbl 0x5(%r14),%esi
    17ce:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    17d4:	c4 c3 79 20 46 04 04 	vpinsrb $0x4,0x4(%r14),%xmm0,%xmm0
    17db:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    17e1:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    17e6:	c4 e3 79 20 43 04 04 	vpinsrb $0x4,0x4(%rbx),%xmm0,%xmm0
    17ed:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    17f2:	e8 89 fe ff ff       	call   1680 <byte_work>
    17f7:	0f b6 7b 06          	movzbl 0x6(%rbx),%edi
    17fb:	41 0f b6 76 06       	movzbl 0x6(%r14),%esi
    1800:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1806:	c4 c3 79 20 46 05 05 	vpinsrb $0x5,0x5(%r14),%xmm0,%xmm0
    180d:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1813:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1818:	c4 e3 79 20 43 05 05 	vpinsrb $0x5,0x5(%rbx),%xmm0,%xmm0
    181f:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1824:	e8 57 fe ff ff       	call   1680 <byte_work>
    1829:	0f b6 7b 07          	movzbl 0x7(%rbx),%edi
    182d:	41 0f b6 76 07       	movzbl 0x7(%r14),%esi
    1832:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1838:	c4 c3 79 20 46 06 06 	vpinsrb $0x6,0x6(%r14),%xmm0,%xmm0
    183f:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1845:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    184a:	c4 e3 79 20 43 06 06 	vpinsrb $0x6,0x6(%rbx),%xmm0,%xmm0
    1851:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1856:	e8 25 fe ff ff       	call   1680 <byte_work>
    185b:	0f b6 7b 08          	movzbl 0x8(%rbx),%edi
    185f:	41 0f b6 76 08       	movzbl 0x8(%r14),%esi
    1864:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    186a:	c4 c3 79 20 46 07 07 	vpinsrb $0x7,0x7(%r14),%xmm0,%xmm0
    1871:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1877:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    187c:	c4 e3 79 20 43 07 07 	vpinsrb $0x7,0x7(%rbx),%xmm0,%xmm0
    1883:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1888:	e8 f3 fd ff ff       	call   1680 <byte_work>
    188d:	0f b6 7b 09          	movzbl 0x9(%rbx),%edi
    1891:	41 0f b6 76 09       	movzbl 0x9(%r14),%esi
    1896:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    189c:	c4 c3 79 20 46 08 08 	vpinsrb $0x8,0x8(%r14),%xmm0,%xmm0
    18a3:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    18a9:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    18ae:	c4 e3 79 20 43 08 08 	vpinsrb $0x8,0x8(%rbx),%xmm0,%xmm0
    18b5:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    18ba:	e8 c1 fd ff ff       	call   1680 <byte_work>
    18bf:	0f b6 7b 0a          	movzbl 0xa(%rbx),%edi
    18c3:	41 0f b6 76 0a       	movzbl 0xa(%r14),%esi
    18c8:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    18ce:	c4 c3 79 20 46 09 09 	vpinsrb $0x9,0x9(%r14),%xmm0,%xmm0
    18d5:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    18db:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    18e0:	c4 e3 79 20 43 09 09 	vpinsrb $0x9,0x9(%rbx),%xmm0,%xmm0
    18e7:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    18ec:	e8 8f fd ff ff       	call   1680 <byte_work>
    18f1:	0f b6 7b 0b          	movzbl 0xb(%rbx),%edi
    18f5:	41 0f b6 76 0b       	movzbl 0xb(%r14),%esi
    18fa:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1900:	c4 c3 79 20 46 0a 0a 	vpinsrb $0xa,0xa(%r14),%xmm0,%xmm0
    1907:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    190d:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1912:	c4 e3 79 20 43 0a 0a 	vpinsrb $0xa,0xa(%rbx),%xmm0,%xmm0
    1919:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    191e:	e8 5d fd ff ff       	call   1680 <byte_work>
    1923:	0f b6 7b 0c          	movzbl 0xc(%rbx),%edi
    1927:	41 0f b6 76 0c       	movzbl 0xc(%r14),%esi
    192c:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1932:	c4 c3 79 20 46 0b 0b 	vpinsrb $0xb,0xb(%r14),%xmm0,%xmm0
    1939:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    193f:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1944:	c4 e3 79 20 43 0b 0b 	vpinsrb $0xb,0xb(%rbx),%xmm0,%xmm0
    194b:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1950:	e8 2b fd ff ff       	call   1680 <byte_work>
    1955:	0f b6 7b 0d          	movzbl 0xd(%rbx),%edi
    1959:	41 0f b6 76 0d       	movzbl 0xd(%r14),%esi
    195e:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1964:	c4 c3 79 20 46 0c 0c 	vpinsrb $0xc,0xc(%r14),%xmm0,%xmm0
    196b:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    1971:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    1976:	c4 e3 79 20 43 0c 0c 	vpinsrb $0xc,0xc(%rbx),%xmm0,%xmm0
    197d:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    1982:	e8 f9 fc ff ff       	call   1680 <byte_work>
    1987:	0f b6 7b 0e          	movzbl 0xe(%rbx),%edi
    198b:	41 0f b6 76 0e       	movzbl 0xe(%r14),%esi
    1990:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    1996:	c4 c3 79 20 46 0d 0d 	vpinsrb $0xd,0xd(%r14),%xmm0,%xmm0
    199d:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    19a3:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    19a8:	c4 e3 79 20 43 0d 0d 	vpinsrb $0xd,0xd(%rbx),%xmm0,%xmm0
    19af:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    19b4:	e8 c7 fc ff ff       	call   1680 <byte_work>
    19b9:	0f b6 7b 0f          	movzbl 0xf(%rbx),%edi
    19bd:	41 0f b6 76 0f       	movzbl 0xf(%r14),%esi
    19c2:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    19c8:	c4 c3 79 20 46 0e 0e 	vpinsrb $0xe,0xe(%r14),%xmm0,%xmm0
    19cf:	c5 f9 7f 44 24 10    	vmovdqa %xmm0,0x10(%rsp)
    19d5:	c5 f9 6f 04 24       	vmovdqa (%rsp),%xmm0
    19da:	c4 e3 79 20 43 0e 0e 	vpinsrb $0xe,0xe(%rbx),%xmm0,%xmm0
    19e1:	c5 f9 7f 04 24       	vmovdqa %xmm0,(%rsp)
    19e6:	e8 95 fc ff ff       	call   1680 <byte_work>
    19eb:	c5 f9 6f 44 24 10    	vmovdqa 0x10(%rsp),%xmm0
    19f1:	c4 c3 79 20 46 0f 0f 	vpinsrb $0xf,0xf(%r14),%xmm0,%xmm0
    19f8:	c5 f9 6f 0c 24       	vmovdqa (%rsp),%xmm1
    19fd:	c4 e3 71 20 4b 0f 0f 	vpinsrb $0xf,0xf(%rbx),%xmm1,%xmm1
    1a04:	c5 f9 ef c1          	vpxor  %xmm1,%xmm0,%xmm0
    1a08:	c5 f9 70 c8 ee       	vpshufd $0xee,%xmm0,%xmm1
    1a0d:	c5 f9 eb c1          	vpor   %xmm1,%xmm0,%xmm0
    1a11:	c5 f9 70 c8 55       	vpshufd $0x55,%xmm0,%xmm1
    1a16:	c5 f9 eb c1          	vpor   %xmm1,%xmm0,%xmm0
    1a1a:	c5 f1 72 d0 10       	vpsrld $0x10,%xmm0,%xmm1
    1a1f:	c5 f9 eb c1          	vpor   %xmm1,%xmm0,%xmm0
    1a23:	c5 f1 71 d0 08       	vpsrlw $0x8,%xmm0,%xmm1
    1a28:	c5 f9 eb c1          	vpor   %xmm1,%xmm0,%xmm0
    1a2c:	c4 e3 79 14 c0 00    	vpextrb $0x0,%xmm0,%eax
    1a32:	ff c8                	dec    %eax
    1a34:	c1 e8 08             	shr    $0x8,%eax
    1a37:	83 e0 01             	and    $0x1,%eax
    1a3a:	48 83 c4 28          	add    $0x28,%rsp
    1a3e:	5b                   	pop    %rbx
    1a3f:	41 5e                	pop    %r14
    1a41:	41 5f                	pop    %r15
    1a43:	5d                   	pop    %rbp
    1a44:	c3                   	ret