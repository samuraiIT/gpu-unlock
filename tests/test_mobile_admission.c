// SPDX-License-Identifier: GPL-2.0-only
/* Host-only tests of the production recipe selector. No GPU access. */
#include <stdio.h>
#include <stdlib.h>
#include "recipes.h"

#define CHECK(condition) do { \
	if (!(condition)) { \
		fprintf(stderr, "FAIL at line %d: %s\n", __LINE__, #condition); \
		return EXIT_FAILURE; \
	} \
} while (0)

int main(void)
{
	const struct gu_card *candidate, *desktop;
	unsigned int id, opt_in, exact;
	const char *bdf = "0000:01:00.0";

	CHECK(!gu_target_listed(NULL, bdf));
	CHECK(!gu_target_listed("", bdf));
	CHECK(!gu_target_listed("all", bdf));
	CHECK(!gu_target_listed("0000:01", bdf));
	CHECK(!gu_target_listed("01:00.0", bdf));
	CHECK(!gu_target_listed("0000:01:00.00", bdf));
	CHECK(!gu_target_listed(" 0000:01:00.0", bdf));
	CHECK(gu_target_listed(bdf, bdf));
	CHECK(gu_target_listed(",0000:02:00.0,0000:01:00.0,", bdf));
	CHECK(gu_target_listed("0000:0A:00.0", "0000:0a:00.0"));

	/* A standard install or targets=all cannot discover the mobile candidate. */
	CHECK(gu_card_find(0x2820) == NULL);
	for (opt_in = 0; opt_in < 2; opt_in++)
		for (exact = 0; exact < 2; exact++)
			CHECK(!!gu_card_select(0x2820, 0x1558, 0x0157, 0xa1,
					       opt_in, exact) == (opt_in && exact));

	candidate = gu_card_select(0x2820, 0x1558, 0x0157, 0xa1, true, true);
	CHECK(candidate && candidate->chip == 0x196);
	CHECK(!gu_card_can_resume(candidate));
	CHECK(!gu_card_can_resume(NULL));
	CHECK(!gu_card_select(0x2820, 0x17aa, 0x0157, 0xa1, true, true));
	CHECK(!gu_card_select(0x2820, 0x1558, 0x3cf3, 0xa1, true, true));
	CHECK(!gu_card_select(0x2820, 0x1558, 0x0157, 0xa0, true, true));
	CHECK(!gu_card_select(0x2860, 0x17aa, 0x3cf3, 0xa1, true, true));

	/* All other IDs retain upstream selection behavior for every flag pair. */
	for (id = 0; id <= 0xffff; id++) {
		if (id == 0x2820)
			continue;
		for (opt_in = 0; opt_in < 2; opt_in++)
			for (exact = 0; exact < 2; exact++)
				CHECK(gu_card_select(id, 0x1558, 0x0157, 0xa1,
						     opt_in, exact) == gu_card_find(id));
	}
	desktop = gu_card_find(0x2803);
	CHECK(desktop && gu_card_can_resume(desktop));
	CHECK(candidate->family == desktop->family);
	puts("PASS: explicit opt-in, exact target, board/revision isolation, no resume, upstream ID behavior");
	return EXIT_SUCCESS;
}
