/* varlat driver for the ECDSA scalar-multiplication pairs.
 *
 * Same poisoning as the taint driver, but under the patched Valgrind that flags
 * variable-latency instructions on secret operands as well as branches on them.
 * The question it answers is not the same one the taint checker answers: a branch
 * on the nonce is a control-flow fact, while a variable-latency instruction fed a
 * secret operand is an arithmetic one, and a scalar multiplication over a bignum
 * layer can carry either.
 *
 * The nonce is the secret. The group, the point and the curve are public. One call,
 * because the analyser reasons about the execution rather than sampling it.
 */
#include <valgrind/memcheck.h>
#include <openssl/ec.h>
#include <openssl/bn.h>
#include <openssl/obj_mac.h>
#include <openssl/rand.h>
#include <stdio.h>
#include "scalarmul.h"

int main(void)
{
    BN_CTX *ctx = BN_CTX_new();
    EC_GROUP *group = EC_GROUP_new_by_curve_name(NID_X9_62_prime256v1);
    EC_POINT *R = EC_POINT_new(group);
    const BIGNUM *order = EC_GROUP_get0_order(group);
    unsigned char kb[32];

    RAND_bytes(kb, 32);
    /* Poison BEFORE the conversion, so anything the conversion itself does with the
     * secret is in scope too. The reduction below is public arithmetic on a poisoned
     * value, which is the point: the analyser should follow the taint through it. */
    VALGRIND_MAKE_MEM_UNDEFINED(kb, 32);
    BIGNUM *k = BN_bin2bn(kb, 32, NULL);
    BN_mod(k, k, order, ctx);
    if (BN_is_zero(k)) {
        BN_one(k);
    }

    VALGRIND_ENABLE_TIMECOP_MODE;
    scalar_mul(group, R, k, ctx);

    printf("VARLAT_DONE\n");
    return 0;
}
