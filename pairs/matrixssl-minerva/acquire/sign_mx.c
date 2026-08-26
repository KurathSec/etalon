/* ECDSA timing harness over real MatrixSSL (Minerva, CVE-2019-13629).
 * Signs a fixed SHA-256 digest with random per-signature nonces and times each
 * psEccDsaSign with rdtscp. Emits the Minerva trace format: line 1
 * "<pubkey_hex> <message_hex>", then "r_hex,s_hex,cycles". The signature comes
 * back DER-encoded, so r and s are parsed out of SEQUENCE{INTEGER,INTEGER}. */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>
#include "coreApi.h"
#include "cryptoApi.h"
#ifndef NSIGS
#define NSIGS 6000
#endif
static uint64_t rd(void){unsigned a;return __rdtscp(&a);}
static void puthex(const unsigned char *b, int n){ for(int i=0;i<n;i++) printf("%02x", b[i]); }

int main(void){
  const psEccCurve_t *curve; psEccKey_t *key;
  if (psCryptoOpen(PSCRYPTO_CONFIG) < 0) { fprintf(stderr,"open\n"); return 1; }
  if (getEccParamById(IANA_SECP256R1, &curve) < 0) return 1;
  if (psEccNewKey(NULL, &key, curve) < 0) return 1;
  if (psEccGenKey(NULL, key, curve, NULL) < 0) { fprintf(stderr,"genkey\n"); return 1; }

  /* public key as 0x04||X||Y */
  /* pstm_to_unsigned_bin writes big-endian significant bytes only; the _nr
     variant writes them least-significant-first and must NOT be used here. Both
     coordinates are left-padded to the 32-byte field width. */
  unsigned char X[32], Y[32], tmpb[48];
  int xl = pstm_unsigned_bin_size(&key->pubkey.x);
  int yl = pstm_unsigned_bin_size(&key->pubkey.y);
  memset(X,0,32); memset(Y,0,32);
  pstm_to_unsigned_bin(NULL, &key->pubkey.x, tmpb); memcpy(X+(32-xl), tmpb, xl);
  pstm_to_unsigned_bin(NULL, &key->pubkey.y, tmpb); memcpy(Y+(32-yl), tmpb, yl);
  printf("04"); puthex(X,32); puthex(Y,32);
  unsigned char msg[32]; memset(msg, 0x5a, 32);
  printf(" "); puthex(msg,32); printf("\n");

  { /* DIAGNOSTIC ONLY: private key on stderr so each nonce can be reconstructed
       and correlated against its timing. Never used for acquisition. */
    unsigned char db[48], dpad[32]; int dl = pstm_unsigned_bin_size(&key->k);
    pstm_to_unsigned_bin(NULL, &key->k, db);
    memset(dpad,0,32); memcpy(dpad+(32-dl), db, dl);
    fprintf(stderr, "PRIV "); for(int i=0;i<32;i++) fprintf(stderr,"%02x",dpad[i]);
    fprintf(stderr, "\n");
  }
  unsigned char h[32];
  psSha256_t sha; psSha256Init(&sha); psSha256Update(&sha, msg, 32); psSha256Final(&sha, h);

  for (int i=0;i<NSIGS;i++){
    unsigned char sig[160]; psSize_t siglen = sizeof sig;
    uint64_t t0=rd();
    int32_t ret = psEccDsaSign(NULL, key, h, 32, sig, &siglen, 0, NULL);
    uint64_t t1=rd();
    if (ret < 0) { fprintf(stderr,"sign %d\n", (int)ret); return 1; }
    /* DER: 30 len 02 rlen R 02 slen S */
    const unsigned char *p = sig; int off = 2;
    if (sig[1] & 0x80) off = 2 + (sig[1] & 0x7f);
    int rl = p[off+1]; const unsigned char *r = p+off+2;
    int sl = p[off+2+rl+1]; const unsigned char *s = p+off+2+rl+2;
    while (rl>1 && *r==0){r++;rl--;} while (sl>1 && *s==0){s++;sl--;}
    puthex(r,rl); printf(","); puthex(s,sl);
    printf(",%llu\n",(unsigned long long)(t1-t0));
  }
  return 0;
}
