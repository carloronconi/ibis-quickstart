import os
import shutil
from unittest import TestLoader

from codegen import ROOT_DIR
from test.test_operators import TestNullableOperators, TestNonNullableOperators
from test.test_nexmark import TestNexmark


def update_all_expected_sources():
    """
    Updates all expected sources of tests with whatever the tests currently produce
    Useful when made a change that changes expected noir code of all tests and already ensured output similarity
    """
    suite = []
    suite.extend(
        list(TestLoader().loadTestsFromTestCase(TestNullableOperators)))
    suite.extend(
        list(TestLoader().loadTestsFromTestCase(TestNonNullableOperators)))
    suite.extend(
        list(TestLoader().loadTestsFromTestCase(TestNexmark)))

    tests = [(t._testMethodName + ".rs", t) for t in suite]
    for file, t in tests:
        file = ROOT_DIR + "/test/expected/" + file
        t.run()

        # replace old expected file with file produced by test
        try:
            os.remove(file)
        except FileNotFoundError:
            pass  # ignore: create new file
        shutil.copyfile(ROOT_DIR + "/noir_template/src/main.rs", file)


if __name__ == "__main__":
    update_all_expected_sources()
