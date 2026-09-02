    1700:	55                   	push   %rbp
    1701:	41 56                	push   %r14
    1703:	53                   	push   %rbx
    1704:	48 89 f3             	mov    %rsi,%rbx
    1707:	48 89 fd             	mov    %rdi,%rbp
    170a:	0f b6 3f             	movzbl (%rdi),%edi
    170d:	0f b6 36             	movzbl (%rsi),%esi
    1710:	e8 6b ff ff ff       	call   1680 <byte_work>
    1715:	8a 45 00             	mov    0x0(%rbp),%al
    1718:	45 31 f6             	xor    %r14d,%r14d
    171b:	3a 03                	cmp    (%rbx),%al
    171d:	0f 85 64 01 00 00    	jne    1887 <check_tag+0x187>
    1723:	0f b6 7d 01          	movzbl 0x1(%rbp),%edi
    1727:	0f b6 73 01          	movzbl 0x1(%rbx),%esi
    172b:	e8 50 ff ff ff       	call   1680 <byte_work>
    1730:	8a 45 01             	mov    0x1(%rbp),%al
    1733:	3a 43 01             	cmp    0x1(%rbx),%al
    1736:	0f 85 4b 01 00 00    	jne    1887 <check_tag+0x187>
    173c:	0f b6 7d 02          	movzbl 0x2(%rbp),%edi
    1740:	0f b6 73 02          	movzbl 0x2(%rbx),%esi
    1744:	e8 37 ff ff ff       	call   1680 <byte_work>
    1749:	8a 45 02             	mov    0x2(%rbp),%al
    174c:	3a 43 02             	cmp    0x2(%rbx),%al
    174f:	0f 85 32 01 00 00    	jne    1887 <check_tag+0x187>
    1755:	0f b6 7d 03          	movzbl 0x3(%rbp),%edi
    1759:	0f b6 73 03          	movzbl 0x3(%rbx),%esi
    175d:	e8 1e ff ff ff       	call   1680 <byte_work>
    1762:	8a 45 03             	mov    0x3(%rbp),%al
    1765:	3a 43 03             	cmp    0x3(%rbx),%al
    1768:	0f 85 19 01 00 00    	jne    1887 <check_tag+0x187>
    176e:	0f b6 7d 04          	movzbl 0x4(%rbp),%edi
    1772:	0f b6 73 04          	movzbl 0x4(%rbx),%esi
    1776:	e8 05 ff ff ff       	call   1680 <byte_work>
    177b:	8a 45 04             	mov    0x4(%rbp),%al
    177e:	3a 43 04             	cmp    0x4(%rbx),%al
    1781:	0f 85 00 01 00 00    	jne    1887 <check_tag+0x187>
    1787:	0f b6 7d 05          	movzbl 0x5(%rbp),%edi
    178b:	0f b6 73 05          	movzbl 0x5(%rbx),%esi
    178f:	e8 ec fe ff ff       	call   1680 <byte_work>
    1794:	8a 45 05             	mov    0x5(%rbp),%al
    1797:	3a 43 05             	cmp    0x5(%rbx),%al
    179a:	0f 85 e7 00 00 00    	jne    1887 <check_tag+0x187>
    17a0:	0f b6 7d 06          	movzbl 0x6(%rbp),%edi
    17a4:	0f b6 73 06          	movzbl 0x6(%rbx),%esi
    17a8:	e8 d3 fe ff ff       	call   1680 <byte_work>
    17ad:	8a 45 06             	mov    0x6(%rbp),%al
    17b0:	3a 43 06             	cmp    0x6(%rbx),%al
    17b3:	0f 85 ce 00 00 00    	jne    1887 <check_tag+0x187>
    17b9:	0f b6 7d 07          	movzbl 0x7(%rbp),%edi
    17bd:	0f b6 73 07          	movzbl 0x7(%rbx),%esi
    17c1:	e8 ba fe ff ff       	call   1680 <byte_work>
    17c6:	8a 45 07             	mov    0x7(%rbp),%al
    17c9:	3a 43 07             	cmp    0x7(%rbx),%al
    17cc:	0f 85 b5 00 00 00    	jne    1887 <check_tag+0x187>
    17d2:	0f b6 7d 08          	movzbl 0x8(%rbp),%edi
    17d6:	0f b6 73 08          	movzbl 0x8(%rbx),%esi
    17da:	e8 a1 fe ff ff       	call   1680 <byte_work>
    17df:	8a 45 08             	mov    0x8(%rbp),%al
    17e2:	3a 43 08             	cmp    0x8(%rbx),%al
    17e5:	0f 85 9c 00 00 00    	jne    1887 <check_tag+0x187>
    17eb:	0f b6 7d 09          	movzbl 0x9(%rbp),%edi
    17ef:	0f b6 73 09          	movzbl 0x9(%rbx),%esi
    17f3:	e8 88 fe ff ff       	call   1680 <byte_work>
    17f8:	8a 45 09             	mov    0x9(%rbp),%al
    17fb:	3a 43 09             	cmp    0x9(%rbx),%al
    17fe:	0f 85 83 00 00 00    	jne    1887 <check_tag+0x187>
    1804:	0f b6 7d 0a          	movzbl 0xa(%rbp),%edi
    1808:	0f b6 73 0a          	movzbl 0xa(%rbx),%esi
    180c:	e8 6f fe ff ff       	call   1680 <byte_work>
    1811:	8a 45 0a             	mov    0xa(%rbp),%al
    1814:	3a 43 0a             	cmp    0xa(%rbx),%al
    1817:	75 6e                	jne    1887 <check_tag+0x187>
    1819:	0f b6 7d 0b          	movzbl 0xb(%rbp),%edi
    181d:	0f b6 73 0b          	movzbl 0xb(%rbx),%esi
    1821:	e8 5a fe ff ff       	call   1680 <byte_work>
    1826:	8a 45 0b             	mov    0xb(%rbp),%al
    1829:	3a 43 0b             	cmp    0xb(%rbx),%al
    182c:	75 59                	jne    1887 <check_tag+0x187>
    182e:	0f b6 7d 0c          	movzbl 0xc(%rbp),%edi
    1832:	0f b6 73 0c          	movzbl 0xc(%rbx),%esi
    1836:	e8 45 fe ff ff       	call   1680 <byte_work>
    183b:	8a 45 0c             	mov    0xc(%rbp),%al
    183e:	3a 43 0c             	cmp    0xc(%rbx),%al
    1841:	75 44                	jne    1887 <check_tag+0x187>
    1843:	0f b6 7d 0d          	movzbl 0xd(%rbp),%edi
    1847:	0f b6 73 0d          	movzbl 0xd(%rbx),%esi
    184b:	e8 30 fe ff ff       	call   1680 <byte_work>
    1850:	8a 45 0d             	mov    0xd(%rbp),%al
    1853:	3a 43 0d             	cmp    0xd(%rbx),%al
    1856:	75 2f                	jne    1887 <check_tag+0x187>
    1858:	0f b6 7d 0e          	movzbl 0xe(%rbp),%edi
    185c:	0f b6 73 0e          	movzbl 0xe(%rbx),%esi
    1860:	e8 1b fe ff ff       	call   1680 <byte_work>
    1865:	8a 45 0e             	mov    0xe(%rbp),%al
    1868:	3a 43 0e             	cmp    0xe(%rbx),%al
    186b:	75 1a                	jne    1887 <check_tag+0x187>
    186d:	0f b6 7d 0f          	movzbl 0xf(%rbp),%edi
    1871:	0f b6 73 0f          	movzbl 0xf(%rbx),%esi
    1875:	e8 06 fe ff ff       	call   1680 <byte_work>
    187a:	8a 45 0f             	mov    0xf(%rbp),%al
    187d:	45 31 f6             	xor    %r14d,%r14d
    1880:	3a 43 0f             	cmp    0xf(%rbx),%al
    1883:	41 0f 94 c6          	sete   %r14b
    1887:	44 89 f0             	mov    %r14d,%eax
    188a:	5b                   	pop    %rbx
    188b:	41 5e                	pop    %r14
    188d:	5d                   	pop    %rbp
    188e:	c3                   	ret